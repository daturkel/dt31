from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from dt31.assembler import assemble, extract_registers_from_program, program_to_text
from dt31.parser import parse_program
from dt31.exceptions import AssemblyError, EndOfProgram
from dt31.operands import (
    Label,
    MemoryReference,
    Operand,
    RegisterReference,
    validate_register_name,
)

if TYPE_CHECKING:
    from dt31.instructions import Instruction  # pragma: no cover


class DT31:
    """A simple virtual CPU with registers, memory, and a stack.

    The DT31 CPU provides a basic execution environment for instructions with:
    - Configurable general-purpose registers (default: a, b, c)
    - Fixed-size memory array
    - Stack for temporary values
    - Instruction pointer (ip) register for program control flow

    Args:
        registers: List of register names to create. If None, creates registers a, b, c.
            Register names must be valid Python identifiers and cannot start with '__'.
        memory_size: Size of the memory array (must be > 0).
        stack_size: Maximum size of the stack (must be > 0).
        wrap_memory: If True, memory accesses wrap around using modulo arithmetic.
            If False, out-of-bounds accesses raise IndexError.
        debug: If True, CPU starts in debug mode (step-by-step execution with state output).
            Defaults to False.

    Raises:
        ValueError: If stack_size or memory_size <= 0, if 'ip' is in register names,
            or if any register name is not a valid Python identifier or starts with '__'.
    """

    def __init__(
        self,
        registers: list[str] | None = None,
        memory_size: int = 256,
        stack_size: int = 256,
        wrap_memory: bool = False,
        debug: bool = False,
    ):
        if stack_size <= 0:
            raise ValueError("stack_size must be greater than 0")
        if memory_size <= 0:
            raise ValueError("memory_size must be greater than 0")
        if (registers is not None) and ("ip" in registers):
            raise ValueError("register name 'ip' is reserved")

        # Validate register names
        register_list = registers if registers is not None else ["a", "b", "c"]
        for reg_name in register_list:
            validate_register_name(reg_name)

        self.registers: dict[str, int]
        """General-purpose registers for holding variables."""
        if registers is None:
            self.registers = {"a": 0, "b": 0, "c": 0}
        else:
            self.registers = {r: 0 for r in registers}
        self.registers["ip"] = 0
        self.memory_size: int = memory_size
        """The length of the built-in memory."""
        self.memory: list[int] = [0] * self.memory_size
        """A fixed-length array of memory."""
        self.stack_size: int = stack_size
        """The max length of the stack."""
        self.stack: deque[int] = deque()
        """A stack to push or pop from."""
        self.wrap_memory: bool = wrap_memory
        """If `True`, memory wraps around using a modulo on the index."""
        self.instructions: list[Instruction] = []
        """Instructions currently loaded."""
        self.debug_mode: bool = debug
        """If `True`, the CPU is in debug mode (step-by-step execution)."""

    @property
    def state(self):
        """Get a dictionary representation of the CPU's current state.

        Returns:
            dict: Contains non-zero memory locations (M[addr]), all registers (R.name),
                and the stack contents.
        """
        state = {}
        for k, v in enumerate(self.memory):
            if v != 0:
                state[f"M[{k}]"] = v
        state |= {f"R.{k}": v for k, v in self.registers.items()}
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

    def run(self, instructions: list[Instruction | Label], debug: bool = False):
        """Load and execute a list of instructions until completion.

        Assembly happens automatically during loading.

        Args:
            instructions: The list of instructions to execute.
            debug: If True, prints each instruction result and waits for user input
                before continuing to the next instruction.

        Raises:
            EndOfProgram: When execution completes normally (caught internally).
        """
        self.load(instructions)
        self.debug_mode = debug
        while True:
            try:
                self.step()
                if self.debug_mode:
                    input()
            except EndOfProgram:
                break

    def validate_program_registers(self, program: list[Instruction | Label]) -> None:
        """Validate that all registers used in a program exist in this CPU.

        This method extracts all register references from the program and verifies
        that each register has been defined in this CPU instance. This provides
        assembly-time validation similar to real assemblers, catching register
        errors before execution begins.

        Args:
            program: List of instructions and labels to validate.

        Raises:
            AssemblyError: If the program uses registers that don't exist in this CPU,
                with a message listing the missing registers.

        Example:
            >>> from dt31 import DT31, I, R, L
            >>> cpu = DT31(registers=["a", "b"])
            >>> program = [I.CP(10, R.x)]  # 'x' not in CPU registers
            >>> cpu.validate_program_registers(program)
            Traceback (most recent call last):
                ...
            AssemblyError: Program uses registers ['x'] but CPU only has registers ['a', 'b']
            Missing registers: ['x']
        """
        registers_used = extract_registers_from_program(program)
        # Filter out 'ip' from CPU registers for comparison (it's always present)
        cpu_user_registers = [r for r in self.registers.keys() if r != "ip"]

        missing = set(registers_used) - set(self.registers.keys())
        if missing:
            raise AssemblyError(
                f"Program uses registers {registers_used} "
                f"but CPU only has registers {cpu_user_registers}\n"
                f"Missing registers: {sorted(missing)}"
            )

    def load(self, instructions: list[Instruction | Label]):
        """Assemble and load instructions into the DT31 and reset the instruction pointer.

        Args:
            instructions: The list of instructions to load.

        Raises:
            AssemblyError: If the program uses registers that don't exist in this CPU,
                or if there are issues with label resolution.
        """
        # Validate registers before assembling
        self.validate_program_registers(instructions)
        self.set_register("ip", 0)
        self.instructions = assemble(instructions)

    def step(self, debug: bool | None = None):
        """Execute a single instruction at the current instruction pointer.

        Args:
            debug: If True, prints the instruction and resulting state after execution.
                If None, uses self.debug_mode. Defaults to None.

        Raises:
            EndOfProgram: If the instruction pointer is out of bounds.
        """
        if debug is None:
            debug = self.debug_mode

        if self.get_register("ip") >= len(self.instructions):
            raise EndOfProgram("No more instructions")
        if self.get_register("ip") < 0:
            raise EndOfProgram("Cannot load negative instructions")
        instruction = self.instructions[self.get_register("ip")]
        output = instruction(self)
        if debug:
            print(repr(instruction) + " -> " + str(output))
            print(self.state)

    def dump(self) -> dict:
        """Serialize complete CPU state for later resumption.

        This method captures the entire state of the CPU including registers, memory,
        stack, and the loaded program (if any). The serialized state can be used to
        pause and resume program execution, or to save/restore CPU state.

        If a program is loaded (instructions list is non-empty), it will be converted
        to assembly text and included in the dump.

        Returns:
            Dict containing CPU state:
                - registers: Current register values (dict)
                - memory: Complete memory array (list)
                - stack: Current stack contents (list)
                - program: Assembly text (if program is loaded, otherwise None)
                - config: CPU configuration (memory_size, stack_size, wrap_memory)

        Example:
            >>> from dt31 import DT31
            >>> from dt31.parser import parse_program
            >>> cpu = DT31()
            >>> program = parse_program("CP 10, R.a\\nCP 20, R.b")
            >>> cpu.load(program)
            >>> cpu.step()  # Execute first instruction
            >>> state = cpu.dump()
            >>> state["registers"]["a"]
            10
            >>> state["registers"]["ip"]
            1
            >>> "CP 10, R.a" in state["program"]
            True
        """
        # Convert loaded program to text if present
        program_text = None
        if self.instructions:
            program_text = program_to_text(self.instructions)

        return {
            "registers": self.registers.copy(),
            "memory": self.memory.copy(),
            "stack": list(self.stack),
            "program": program_text,
            "config": {
                "memory_size": self.memory_size,
                "stack_size": self.stack_size,
                "wrap_memory": self.wrap_memory,
            },
        }

    @classmethod
    def load_from_dump(cls, state: dict) -> DT31:
        """Deserialize CPU from a dumped state.

        This method recreates a CPU instance from a previously dumped state,
        restoring all registers, memory, stack contents, and optionally the loaded program.
        If a program was saved in the dump, it is re-parsed and loaded.

        Args:
            state: Dict from dump() containing CPU state

        Returns:
            DT31 instance restored to the saved state

        Raises:
            ValueError: If state dict is missing required fields
            ParserError: If program is provided but cannot be parsed

        Example:
            >>> from dt31 import DT31
            >>> from dt31.parser import parse_program
            >>> cpu = DT31()
            >>> program = parse_program("CP 10, R.a\\nCP 20, R.b")
            >>> cpu.load(program)
            >>> cpu.step()
            >>> state = cpu.dump()
            >>> cpu2 = DT31.load_from_dump(state)
            >>> cpu2.get_register("a")
            10
            >>> cpu2.get_register("ip")
            1
        """
        # Validate state dict
        required_fields = ["registers", "memory", "stack", "config"]
        for field in required_fields:
            if field not in state:
                raise ValueError(f"State dict missing required field: {field}")

        # Extract register names (excluding 'ip')
        register_names = [r for r in state["registers"].keys() if r != "ip"]

        # Create CPU with same config
        cpu = cls(
            registers=register_names,
            memory_size=state["config"]["memory_size"],
            stack_size=state["config"]["stack_size"],
            wrap_memory=state["config"]["wrap_memory"],
        )

        # Load program if available
        if state.get("program"):
            program = parse_program(state["program"])
            cpu.load(program)

        # Restore state
        cpu.registers = state["registers"].copy()
        cpu.memory = state["memory"].copy()
        cpu.stack = deque(state["stack"], maxlen=cpu.stack_size)

        return cpu
