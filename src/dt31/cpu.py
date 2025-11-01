from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from .operands import MemoryReference, Operand, RegisterReference

if TYPE_CHECKING:
    from .instructions import Instruction  # pragma: no cover


class DT31:
    """A simple virtual CPU with registers, memory, and a stack.

    The DT31 CPU provides a basic execution environment for instructions with:
    - Configurable general-purpose registers (default: a, b, c)
    - Fixed-size memory array
    - Stack for temporary values
    - Instruction pointer (ip) register for program control flow

    Args:
        registers: List of register names to create. If None, creates registers a, b, c.
        memory_size: Size of the memory array (must be > 0).
        stack_size: Maximum size of the stack (must be > 0).
        wrap_memory: If True, memory accesses wrap around using modulo arithmetic.
            If False, out-of-bounds accesses raise IndexError.

    Raises:
        ValueError: If stack_size or memory_size <= 0, or if 'ip' is in register names.
    """

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
        self.instructions = []

    @property
    def state(self):
        """Get a dictionary representation of the CPU's current state.

        Returns:
            dict: Contains non-zero memory locations (M[addr]), all registers (R[name]),
                and the stack contents.
        """
        state = {}
        for k, v in enumerate(self.memory):
            if v != 0:
                state[f"M[{k}]"] = v
        state |= {f"R[{k}]": v for k, v in self.registers.items()}
        state["stack"] = list(self.stack)
        return state

    def pop(self) -> int:
        """Pop a value from the stack.

        Returns:
            int: The value popped from the top of the stack.

        Raises:
            RuntimeError: If the stack is empty (stack underflow).
        """
        if len(self.stack) == 0:
            raise RuntimeError("stack underflow")
        return self.stack.pop()

    def push(self, value: int):
        """Push a value onto the stack.

        Args:
            value: The integer value to push onto the stack.

        Raises:
            RuntimeError: If the stack is at maximum capacity (stack overflow).
        """
        if len(self.stack) == self.stack_size:
            raise RuntimeError("stack overflow")
        self.stack.append(value)

    def __getitem__(self, arg: Operand) -> int:
        """Get a value from memory or a register using operand syntax.

        Args:
            arg: A MemoryReference or RegisterReference operand.

        Returns:
            int: The value at the specified location.

        Raises:
            ValueError: If arg is not a MemoryReference or RegisterReference.
        """
        if isinstance(arg, (MemoryReference, RegisterReference)):
            return arg.resolve(self)
        else:
            raise ValueError(f"can't get item with type {type(arg)}")

    def __setitem__(self, arg: Operand, value: int):
        """Set a value in memory or a register using operand syntax.

        Args:
            arg: A MemoryReference or RegisterReference operand.
            value: The integer value to set.

        Raises:
            ValueError: If arg is not a MemoryReference or RegisterReference.
        """
        if isinstance(arg, MemoryReference):
            self.set_memory(arg.resolve_address(self), value)
        elif isinstance(arg, RegisterReference):
            self.set_register(arg.register, value)
        else:
            raise ValueError(f"can't get item with type {type(arg)}")

    def get_memory(self, index: int) -> int:
        """Get a value from memory at the specified index.

        Args:
            index: The memory address to read from.

        Returns:
            int: The value at the specified memory address.

        Raises:
            IndexError: If index is out of bounds and wrap_memory is False.
        """
        if self.wrap_memory:
            return self.memory[index % self.memory_size]
        elif not (0 <= index < len(self.memory)):
            raise IndexError(f"memory has no index {index}")
        return self.memory[index]

    def set_memory(self, index: int, value: int):
        """Set a value in memory at the specified index.

        Args:
            index: The memory address to write to.
            value: The integer value to store.

        Raises:
            IndexError: If index is out of bounds and wrap_memory is False.
        """
        if self.wrap_memory:
            self.memory[index % self.memory_size] = value
        elif not (0 <= index < len(self.memory)):
            raise IndexError(f"memory has no index {index}")
        else:
            self.memory[index] = value

    def get_register(self, register: str) -> int:
        """Get the value of a register.

        Args:
            register: The name of the register to read.

        Returns:
            int: The current value of the register.

        Raises:
            ValueError: If the register name is not recognized.
        """
        if register not in self.registers:
            raise ValueError(f"unknown register {register}")
        return self.registers[register]

    def set_register(self, register: str, value: int) -> int:
        """Set the value of a register.

        Args:
            register: The name of the register to write to.
            value: The integer value to store in the register.

        Returns:
            int: The value that was set (for convenience in chaining).

        Raises:
            ValueError: If the register name is not recognized.
        """
        if register not in self.registers:
            raise ValueError(f"unknown register {register}")
        self.registers[register] = value
        return value

    def run(self, instructions: list[Instruction], debug: bool = False):
        """Load and execute a list of instructions until completion.

        Args:
            instructions: The list of instructions to execute.
            debug: If True, prints each instruction result and waits for user input
                before continuing to the next instruction.

        Raises:
            EndOfProgram: When execution completes normally (caught internally).
        """
        self.load(instructions)
        while True:
            try:
                self.step(debug)
                if debug:
                    input()
            except EndOfProgram:
                break

    def load(self, instructions: list[Instruction]):
        """Load instructions into the CPU and reset the instruction pointer.

        Args:
            instructions: The list of instructions to load.
        """
        self.set_register("ip", 0)
        self.instructions = instructions

    def step(self, debug: bool = False):
        """Execute a single instruction at the current instruction pointer.

        Args:
            debug: If True, prints the instruction and resulting state after execution.

        Raises:
            EndOfProgram: If the instruction pointer is out of bounds.
        """
        if self.get_register("ip") >= len(self.instructions):
            raise EndOfProgram("No more instructions")
        if self.get_register("ip") < 0:
            raise EndOfProgram("Cannot load negative instructions")
        instruction = self.instructions[self.get_register("ip")]
        output = instruction(self)
        if debug:
            print(str(instruction) + " -> " + str(output))
            print(self.state)


class EndOfProgram(Exception):
    """Exception to throw when the end of the instructions is reached."""

    pass
