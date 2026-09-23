"""Exceptions used by dt31."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dt31.instructions import Instruction  # pragma: no cover


class EndOfProgram(Exception):
    """Exception to throw when the end of the instructions is reached."""


class AssemblyError(Exception):
    """An exception to throw when the assembler encounters something wrong with a program."""


class ParserError(Exception):
    """Exception raised when parsing DT31 assembly text fails.

    This exception is raised for syntax errors, invalid operands,
    or other parsing issues in DT31 assembly code.
    """


class DT31RuntimeError(Exception):
    """Base class for errors a running program can trigger during execution.

    Attributes:
        ip: The instruction pointer at the time of the error, or `None` if unknown.
        instruction: The failing `Instruction`, or `None` if unknown.
        line: The source line number of the failing instruction, or `None` if
            it wasn't parsed from assembly text.
    """

    def __init__(self, message: str = ""):
        """Initialize a DT31RuntimeError.

        Args:
            message: The error message.
        """
        super().__init__(message)
        self.ip: int | None = None
        self.instruction: Instruction | None = None
        self.line: int | None = None


class DivisionByZero(DT31RuntimeError):
    """Raised when a program divides or takes the modulo of a value by zero.

    Raised by the `DIV` and `MOD` instructions.
    """


class StackUnderflow(DT31RuntimeError):
    """Raised when a program pops from an empty stack.

    Raised by `DT31.pop()`, e.g. via the `POP` instruction.
    """


class StackOverflow(DT31RuntimeError):
    """Raised when a program pushes onto a full stack.

    Raised by `DT31.push()`, e.g. via the `PUSH` instruction.
    """


class MemoryOutOfBounds(DT31RuntimeError):
    """Raised when a program accesses a memory address outside the CPU's memory.

    Raised by `DT31.get_memory()`/`DT31.set_memory()` when `wrap_memory` is `False`.
    """


class InvalidOperand(DT31RuntimeError):
    """Raised when a program supplies an operand value an instruction can't use.

    Raised by the `RINT` instruction when its high bound is less than its low bound.
    """


class StepLimitExceeded(DT31RuntimeError):
    """Raised when a program executes more than `max_steps` instructions in a single `run()` call."""
