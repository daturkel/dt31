from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from .operands import MemoryReference, Operand, RegisterReference

if TYPE_CHECKING:
    from .instructions import Instruction  # pragma: no cover


class DT31:
    def __init__(
        self,
        registers: list[str] | None = None,
        memory_size: int = 256,
        stack_size: int = 256,
        wrap_memory: bool = False,
    ):
        if stack_size <= 0:
            raise ValueError("stack_size must be greater than 0")
        if memory_size <= 0:
            raise ValueError("memory_size must be greater than 0")
        if (registers is not None) and ("ip" in registers):
            raise ValueError("register name 'ip' is reserved")
        if registers is None:
            self.registers = {"a": 0, "b": 0, "c": 0}
        else:
            self.registers = {r: 0 for r in registers}
        self.registers["ip"] = 0
        self.memory = [0] * memory_size
        self.memory_size = memory_size
        self.stack: deque[int] = deque()
        self.stack_size = stack_size
        self.wrap_memory = wrap_memory

    def pop(self) -> int:
        if len(self.stack) == 0:
            raise RuntimeError("stack underflow")
        return self.stack.pop()

    def push(self, value: int):
        if len(self.stack) == self.stack_size:
            raise RuntimeError("stack overflow")
        self.stack.append(value)

    def __getitem__(self, arg: Operand) -> int:
        if isinstance(arg, (MemoryReference, RegisterReference)):
            return arg.resolve(self)
        else:
            raise ValueError(f"can't get item with type {type(arg)}")

    def __setitem__(self, arg: Operand, value: int):
        if isinstance(arg, MemoryReference):
            self.set_memory(arg.resolve_address(self), value)
        elif isinstance(arg, RegisterReference):
            self.set_register(arg.register, value)
        else:
            raise ValueError(f"can't get item with type {type(arg)}")

    def get_memory(self, index: int) -> int:
        if self.wrap_memory:
            return self.memory[index % self.memory_size]
        elif not (0 <= index < len(self.memory)):
            raise IndexError(f"memory has no index {index}")
        return self.memory[index]

    def set_memory(self, index: int, value: int):
        if self.wrap_memory:
            self.memory[index % self.memory_size] = value
        elif not (0 <= index < len(self.memory)):
            raise IndexError(f"memory has no index {index}")
        else:
            self.memory[index] = value

    def get_register(self, register: str) -> int:
        if register not in self.registers:
            raise ValueError(f"unknown register {register}")
        return self.registers[register]

    def set_register(self, register: str, value: int) -> int:
        if register not in self.registers:
            raise ValueError(f"unknown register {register}")
        self.registers[register] = value
        return value

    def run(self, instructions: list[Instruction]):
        self.set_register("ip", 0)
        num_instructions = len(instructions)
        while True:
            if (
                self.get_register("ip") >= num_instructions
                or self.get_register("ip") < 0
            ):
                break
            instructions[self.get_register("ip")](self)
