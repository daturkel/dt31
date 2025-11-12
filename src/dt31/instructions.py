from __future__ import annotations

import random
from typing import TYPE_CHECKING

from dt31.operands import Destination, L, Label, Operand, Reference, as_op

if TYPE_CHECKING:
    from dt31.cpu import DT31  # pragma: no cover

INPUT_PROMPT = "> "


class Instruction:
    """Base class for all DT31 instructions.

    Instructions are the fundamental building blocks of DT31 programs. Each instruction
    performs a specific operation when executed by the CPU, such as arithmetic, logic,
    memory manipulation, or control flow.

    Execution Model
    ---------------
    When an instruction is executed (via `__call__`), it follows a two-phase process:

    1. **Calculation phase** (`_calc`): Computes the instruction's result value and
       performs any side effects (e.g., writing to memory, pushing to stack).
    2. **Advance phase** (`_advance`): Updates the instruction pointer (IP) to determine
       which instruction executes next. By default, increments IP by 1, but jump
       instructions override this to change control flow.

    Implementing New Instructions
    ------------------------------
    To create a new instruction, subclass `Instruction` (or, even better, a helper subclass
    like `NullaryOperation`, `UnaryOperation`, or `BinaryOperation`) and implement:

    - `__init__(self)`: Pass the instruction's args to the `__init__` method of the parent
      class.
    - `_calc(cpu)`: Perform the instruction's operation and return a result value.
      This value is available to the instruction but typically only used for operations
      that need to store results (via `NullaryOperation`,`BinaryOperation` or `UnaryOperation`
      base classes).
    - `_advance(cpu)` (optional): Override to customize how the instruction pointer moves.
      Default behavior increments IP by 1. Jump instructions override this to modify
      control flow.
    - `__str__()` (optional): Return a human-readable representation showing the
      instruction name and operands for debugging and display purposes.

    Consult the source of existing instructions as a guide.

    Examples
    --------
    Simple unary operation (square a value):
    ```python
    class SQUARE(UnaryOperation):
        \"\"\"Square a value (a * a).\"\"\"
        def __init__(self, a: Operand, out: Reference | None = None):
            super().__init__("SQUARE", a, out)

        def _calc(self, cpu: DT31) -> int:
            val = self.a.resolve(cpu)
            return val * val
    ```

    Custom instruction with multiple operands (swap two registers):
    ```python
    class SWAP(Instruction):
        \"\"\"Swap the values of two registers.\"\"\"
        def __init__(self, a: Reference, b: Reference):
            super().__init__("SWAP")
            self.a = a
            self.b = b

        def _calc(self, cpu: DT31) -> int:
            val_a = self.a.resolve(cpu)
            val_b = self.b.resolve(cpu)
            self.a.assign(cpu, val_b)
            self.b.assign(cpu, val_a)
            return 0

        def __str__(self) -> str:
            return f"{self.name}({self.a}, {self.b})"
    ```
    """

    def __init__(self, name: str):
        """Initialize an Instruction.

        Args:
            name: The name of the instruction (e.g., "ADD", "JMP", "PUSH").
        """
        self.name = name

    def _calc(self, cpu: DT31) -> int:
        """Perform the instruction's operation and return a result value.

        This method must be implemented by subclasses to define the instruction's
        behavior. It performs the core operation (arithmetic, comparison, I/O, etc.)
        and returns an integer result.

        Args:
            cpu: The DT31 CPU instance executing this instruction.

        Returns:
            The computed result value. For instructions that write to operands
            (via `BinaryOperation` or `UnaryOperation`), this value is stored
            in the output location. For other instructions, the return value
            may be unused.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError()

    def _advance(self, cpu: DT31):
        """Update the instruction pointer to determine the next instruction.

        By default, increments the instruction pointer by 1 to execute the next
        sequential instruction. Jump instructions override this method to modify
        control flow (e.g., jumping to a different location or returning from a call).

        Args:
            cpu: The DT31 CPU instance executing this instruction.
        """
        # default behavior is to increment the instruction register by 1
        cpu.set_register("ip", cpu.get_register("ip") + 1)

    def __call__(self, cpu: DT31) -> int:
        """Execute the instruction on the given CPU.

        This is the main entry point for instruction execution. It orchestrates
        the two-phase execution model by calling `_calc` followed by `_advance`.

        This function is overridden in some of the subclasses like `UnaryOperation` and
        `BinaryOperation` to handle storing results.

        Args:
            cpu: The DT31 CPU instance to execute this instruction on.

        Returns:
            The result value computed by `_calc`.
        """
        value = self._calc(cpu)
        self._advance(cpu)
        return value

    def __repr__(self) -> str:
        """Return Python API representation of the instruction.

        Returns:
            A string showing the instruction name and any operands in Python syntax.
        """
        return f"{self.name}()"

    def __str__(self) -> str:
        """Return assembly text representation of the instruction.

        Returns:
            A string showing the instruction in assembly text format.
        """
        return self.name

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.__dict__ == other.__dict__


class NOOP(Instruction):
    """Do nothing but advance instruction pointer."""

    def __init__(self):
        super().__init__("NOOP")

    def _calc(self, cpu: DT31) -> int:
        return 0


class NullaryOperation(Instruction):
    """Base class for instructions which take no input operands and write to an output
    operand."""

    out: Reference  # Always set to a Reference in __init__

    def __init__(self, name: str, out: Reference):
        """Base class for instructions which take no input operands and write to an
        output operand.

        Args:
            name: The name of the instruction (e.g., "RND").
            out: Output reference for result.
        """
        super().__init__(name)
        if not isinstance(out, Reference):
            raise ValueError("argument `out` must be a Reference")
        self.out = out

    def __call__(self, cpu: DT31) -> int:
        value = super().__call__(cpu)
        cpu[self.out] = value
        return value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.out}"


class UnaryOperation(Instruction):
    """Base class for instructions which utilize a single operand and optionally write
    to a separate operand."""

    out: Reference  # Always set to a Reference in __init__

    def __init__(self, name: str, a: Operand | int, out: Reference | None = None):
        super().__init__(name)
        self.a = as_op(a)
        if not isinstance(out, (type(None), Reference)):
            raise ValueError("argument `out` must be a Reference or None")
        if out is not None:
            self.out = out
        elif isinstance(self.a, Reference):
            self.out = self.a
        else:
            raise ValueError(
                f"{self.name} must be called with a reference as operand `out` or a reference as operand `a`"
            )

    def __call__(self, cpu: DT31) -> int:
        value = super().__call__(cpu)
        cpu[self.out] = value
        return value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(a={self.a!r}, out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.a}, {self.out}"


# ---------------------------------- bitwise and alu --------------------------------- #
class BinaryOperation(Instruction):
    """Base class for instructions which utilize two operands and optionally write
    to a separate operand."""

    out: Reference  # Always set to a Reference in __init__

    def __init__(
        self,
        name: str,
        a: Operand | int,
        b: Operand | int,
        out: Reference | None = None,
    ):
        """Base class for instructions which take two operands and optionally write to a
        separate operand."""
        super().__init__(name)
        self.a = as_op(a)
        self.b = as_op(b)
        if not isinstance(out, (type(None), Reference)):
            raise ValueError("argument `out` must be a Reference or None")
        if isinstance(out, Reference):
            self.out = out
        elif isinstance(self.a, Reference):
            self.out = self.a
        else:
            raise ValueError(
                f"{self.name} must be called with a reference as operand `out` or a reference as operand `a`"
            )

    def __call__(self, cpu: DT31) -> int:
        value = super().__call__(cpu)
        cpu[self.out] = value
        return value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(a={self.a!r}, b={self.b!r}, out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.a}, {self.b}, {self.out}"


class ADD(BinaryOperation):
    """Add operands a and b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the addition.
            b: Second operand of the addition.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("ADD", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) + self.b.resolve(cpu)


class SUB(BinaryOperation):
    """Subtracts operand b from operand a."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the subtraction.
            b: Second operand of the subtraction.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("SUB", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) - self.b.resolve(cpu)


class MUL(BinaryOperation):
    """Multiplies operands a and b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the multiplication.
            b: Second operand of the multiplication.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("MUL", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) * self.b.resolve(cpu)


class DIV(BinaryOperation):
    """Divide operand a by b (using floor division)."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the addition.
            b: Second operand of the addition.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("DIV", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) // self.b.resolve(cpu)


class MOD(BinaryOperation):
    """Calculate operand a modulo operand b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the modulus.
            b: Second operand of the modulus.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("MOD", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) % self.b.resolve(cpu)


class BSL(BinaryOperation):
    """Shift operand a left by operand b bits."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the bit shift.
            b: Second operand of the bit shift.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BSL", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) << self.b.resolve(cpu)


class BSR(BinaryOperation):
    """Shift operand a right by operand b bits."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the bit shift.
            b: Second operand of the bit shift.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BSR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) >> self.b.resolve(cpu)


class BAND(BinaryOperation):
    """Take the bitwise and of operands a and b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the bitwise and.
            b: Second operand of the bitwise and.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BAND", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) & self.b.resolve(cpu)


class BOR(BinaryOperation):
    """Take the bitwise or of operands a and b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the bitwise or.
            b: Second operand of the bitwise or.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) | self.b.resolve(cpu)


class BXOR(BinaryOperation):
    """Take the bitwise xor of operands a and b."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the bitwise xor.
            b: Second operand of the bitwise xor.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BXOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) ^ self.b.resolve(cpu)


class BNOT(UnaryOperation):
    """Take the bitwise negation operand a."""

    def __init__(self, a: Operand | int, out: Reference | None = None):
        """
        Args:
            a: Operand to be negated.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("BNOT", a, out)

    def _calc(self, cpu: DT31) -> int:
        return ~self.a.resolve(cpu)


# ------------------------------------ comparisons ----------------------------------- #
class LT(BinaryOperation):
    """Store 1 if operand a is less than operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("LT", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) < self.b.resolve(cpu))


class GT(BinaryOperation):
    """Store 1 if operand a is greater than operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("GT", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) > self.b.resolve(cpu))


class LE(BinaryOperation):
    """Store 1 if operand a is less than or equal to operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("LE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) <= self.b.resolve(cpu))


class GE(BinaryOperation):
    """Store 1 if operand a is greater than or equal to operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("GE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) >= self.b.resolve(cpu))


class EQ(BinaryOperation):
    """Store 1 if operand a is equal to operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("EQ", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) == self.b.resolve(cpu))


class NE(BinaryOperation):
    """Store 1 if operand a is not equal to operand b else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the comparison.
            b: Second operand of the comparison.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("NE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) != self.b.resolve(cpu))


# ---------------------------------- pythonic logic ---------------------------------- #
class AND(BinaryOperation):
    """Store 1 if both operands are nonzero (truthy) else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the logical and.
            b: Second operand of the logical and.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("AND", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) and self.b.resolve(cpu))


class OR(BinaryOperation):
    """Store 1 if either operand is nonzero (truthy) else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the logical or.
            b: Second operand of the logical or.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("OR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) or self.b.resolve(cpu))


class XOR(BinaryOperation):
    """Store 1 if exactly one operand is nonzero (truthy) else 0."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: First operand of the logical xor.
            b: Second operand of the logical xor.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("XOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        a = self.a.resolve(cpu)
        b = self.b.resolve(cpu)
        return int((a and not b) or (b and not a))


class NOT(UnaryOperation):
    """Store 1 if operand is zero (falsy) else 0."""

    def __init__(self, a: Operand | int, out: Reference | None = None):
        """
        Args:
            a: Operand to be negated.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("NOT", a, out)

    def _calc(self, cpu: DT31) -> int:
        return int(not self.a.resolve(cpu))


# --------------------------------------- jumps -------------------------------------- #
class Jump(Instruction):
    """Base class for various types of jump instruction."""

    def __init__(self, name: str, dest: Destination):
        """
        Args:
            name: The name of the jump instruction.
            dest: The destination to jump to (Label, Operand, or int).
        """
        super().__init__(name)
        # Handle Label separately since it's not an Operand
        if isinstance(dest, Label):
            self.dest = dest
        else:
            self.dest = as_op(dest)

    def _jump_condition(self, cpu: DT31) -> bool:
        raise NotImplementedError()

    def _jump_destination(self, cpu: DT31) -> int:
        raise NotImplementedError()

    def _calc(self, cpu: DT31) -> int:
        return 0

    def _advance(self, cpu: DT31):
        if self._jump_condition(cpu):
            cpu.set_register("ip", self._jump_destination(cpu))
        else:
            cpu.set_register("ip", cpu.get_register("ip") + 1)

    def __repr__(self) -> str:
        """Return Python API representation."""
        if isinstance(self.dest, Label):
            return f"{self.name}(dest={self.dest!r})"
        return f"{self.name}(dest={self.dest!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.dest}"


class UnaryJump(Jump):
    """Base class for conditions which use a single value to determine jumps."""

    def __init__(self, name: str, dest: Destination, a: Operand | int):
        """
        Args:
            name: The name of the jump instruction.
            dest: The destination to jump to (Label, Operand, or int).
            a: The operand used to determine if jump condition is met.
        """
        super().__init__(name, dest)
        self.a = as_op(a)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(dest={self.dest!r}, a={self.a!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.dest}, {self.a}"


class BinaryJump(Jump):
    """Base class for conditions which use two values to determine jumps."""

    def __init__(
        self, name: str, dest: Destination, a: Operand | int, b: Operand | int
    ):
        """
        Args:
            name: The name of the jump instruction.
            dest: The destination to jump to (Label, Operand, or int).
            a: The first operand used to determine if jump condition is met.
            b: The second operand used to determine if jump condition is met.
        """
        super().__init__(name, dest)
        self.a = as_op(a)
        self.b = as_op(b)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(dest={self.dest!r}, a={self.a!r}, b={self.b!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.dest}, {self.a}, {self.b}"


class ExactJumpMixin(Jump):
    """Mixin for jumps that use an exact position specified by operand.

    This mixin class defines behavior for jumps where the destination is used directly as
    the new instruction pointer value, rather than relative to the current position.
    """

    def _jump_destination(self, cpu: DT31) -> int:
        return self.dest.resolve(cpu)


class RelativeJumpMixin(Jump):
    """Mixin for jumps that are offset from current location.

    This mixin class defines behavior for jumps where the destination is used as an offset
    relative to the current instruction pointer position, rather than an exact position.
    """

    def _jump_destination(self, cpu: DT31) -> int:
        return cpu.get_register("ip") + self.dest.resolve(cpu)


class UnconditionalJumpMixin(Jump):
    """Class mixin for always taking a jump.

    This mixin class defines behavior for jumps that always occur, regardless of any conditions.
    It implements the jump_condition method to always return True. It does not utilize any
    operands.
    """

    def _jump_condition(self, cpu: DT31):
        return True


class IfEqualJumpMixin(BinaryJump):
    """Binary jump condition that triggers when operands are equal.

    This mixin class defines behavior for jumps that should occur when two specified operands
    hold equal values. It implements the jump_condition method to compare the resolved values
    of the operands. It expects an a and b operand.
    """

    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) == self.b.resolve(cpu)


class IfUnequalJumpMixin(BinaryJump):
    """Binary jump condition that triggers when operands are not equal.

    This mixin class defines behavior for jumps that should occur when two specified operands
    hold unequal values. It implements the jump_condition method to compare the resolved
    values of the operands. It expects an a and b operand.
    """

    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) != self.b.resolve(cpu)


class IfGTJumpMixin(BinaryJump):
    """Binary jump condition that triggers when first operand is greater than second operand.

    This mixin class defines behavior for jumps that should occur when the first specified
    operand is greater than the second operand. It implements the jump_condition method to
    compare the resolved values of the operands. It expects an a and b operand.
    """

    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) > self.b.resolve(cpu)


class IfGEJumpMixin(BinaryJump):
    """Binary jump condition that triggers when first operand is greater than or equal to
    the second operand.

    This mixin class defines behavior for jumps that should occur when the first specified
    operand is greater than or equal to the second operand. It implements the jump_condition
    method to compare the resolved values of the operands. It expects an a and b operand.
    """

    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) >= self.b.resolve(cpu)


class IfJumpMixin(UnaryJump):
    """Unary jump condition that triggers when operand is nonzero (truthy).

    This mixin class defines behavior for jumps that should occur when the specified operand
    holds a nonzero (truthy) value. It implements the jump_condition method to check if
    the resolved value is truthy. It expects an a operand.
    """

    def _jump_condition(self, cpu: DT31) -> bool:
        return bool(self.a.resolve(cpu))


class JMP(ExactJumpMixin, UnconditionalJumpMixin):
    """Unconditional jump instruction."""

    def __init__(self, dest: Destination):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
        """
        super().__init__("JMP", dest)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"JMP(dest={self.dest!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"JMP {self.dest}"


class RJMP(RelativeJumpMixin, UnconditionalJumpMixin):
    """Relative unconditional jump instruction."""

    def __init__(self, delta: Destination):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
        """
        super().__init__("RJMP", delta)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"RJMP(dest={self.dest!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"RJMP {self.dest}"


class JEQ(ExactJumpMixin, IfEqualJumpMixin):
    """Jump to exact destination if operands are equal."""

    def __init__(self, dest: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("JEQ", dest, a, b)


class RJEQ(RelativeJumpMixin, IfEqualJumpMixin):
    """Jump to relative destination if operands are equal."""

    def __init__(self, delta: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("RJEQ", delta, a, b)


class JNE(ExactJumpMixin, IfUnequalJumpMixin):
    """Jump to exact destination if operands are not equal."""

    def __init__(self, dest: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("JNE", dest, a, b)


class RJNE(RelativeJumpMixin, IfUnequalJumpMixin):
    """Jump to relative destination if operands are not equal."""

    def __init__(self, delta: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("RJNE", delta, a, b)


class JGT(ExactJumpMixin, IfGTJumpMixin):
    """Jump to exact destination if first operand is greater than second operand."""

    def __init__(self, dest: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("JGT", dest, a, b)


class RJGT(RelativeJumpMixin, IfGTJumpMixin):
    """Jump to relative destination if first operand is greater than second operand."""

    def __init__(self, delta: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("RJGT", delta, a, b)


class JGE(ExactJumpMixin, IfGEJumpMixin):
    """Jump to exact destination if first operand is greater than or equal to second operand."""

    def __init__(self, dest: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("JGE", dest, a, b)


class RJGE(RelativeJumpMixin, IfGEJumpMixin):
    """Jump to relative destination if first operand is greater than or equal to second operand."""

    def __init__(self, delta: Destination, a: Operand | int, b: Operand | int):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
            a: First operand to compare.
            b: Second operand to compare.
        """
        super().__init__("RJGE", delta, a, b)


class JIF(ExactJumpMixin, IfJumpMixin):
    """Jump to exact destination if operand is nonzero (truthy)."""

    def __init__(self, dest: Destination, a: Operand | int):
        """
        Args:
            dest: The destination to jump to (Label, Operand, or int).
            a: Operand to check for truthiness.
        """
        super().__init__("JIF", dest, a)


class RJIF(RelativeJumpMixin, IfJumpMixin):
    """Jump to relative destination if operand is nonzero (truthy)."""

    def __init__(self, delta: Destination, a: Operand | int):
        """
        Args:
            delta: The destination to jump to (Label, Operand, or int).
            a: Operand to check for truthiness.
        """
        super().__init__("RJIF", delta, a)


# ---------------------------------- function calls ---------------------------------- #


class CALL(ExactJumpMixin, UnconditionalJumpMixin):
    """Call function at exact destination, pushing return address to stack."""

    def __init__(self, dest: Destination):
        """
        Args:
            dest: The destination to call (Label, Operand, or int).
        """
        super().__init__("CALL", dest)

    def _calc(self, cpu: DT31) -> int:
        # Push return address (next instruction) onto stack
        cpu.push(cpu.get_register("ip") + 1)
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"CALL(dest={self.dest!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"CALL {self.dest}"


class RCALL(RelativeJumpMixin, UnconditionalJumpMixin):
    """Call function at relative destination, pushing return address to stack."""

    def __init__(self, delta: Destination):
        """
        Args:
            delta: The destination to call (Label, Operand, or int).
        """
        super().__init__("RCALL", delta)

    def _calc(self, cpu: DT31) -> int:
        # Push return address (next instruction) onto stack
        cpu.push(cpu.get_register("ip") + 1)
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"RCALL(dest={self.dest!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"RCALL {self.dest}"


class RET(Instruction):
    """Return from function by popping return address from stack and jumping to it."""

    def __init__(self):
        super().__init__("RET")

    def _calc(self, cpu: DT31) -> int:
        return 0

    def _advance(self, cpu: DT31):
        # Pop return address from stack and set IP to it
        return_address = cpu.pop()
        cpu.set_register("ip", return_address)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return "RET()"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return "RET"


# --------------------------------------- stack -------------------------------------- #


class PUSH(Instruction):
    """Push operand value onto the stack."""

    def __init__(self, a: Operand | int):
        """
        Args:
            a: Operand value to push onto the stack.
        """
        super().__init__("PUSH")
        self.a = as_op(a)

    def _calc(self, cpu: DT31) -> int:
        cpu.push(self.a.resolve(cpu))
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"PUSH(a={self.a!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"PUSH {self.a}"


class POP(Instruction):
    """Pop value from the stack."""

    def __init__(self, out: Reference | None = None):
        """
        Args:
            out: Optional output reference to store the popped value. If not provided, value
                is popped but not stored.
        """
        super().__init__("POP")
        if out is not None:
            self.out = as_op(out)
        else:
            self.out = None

    def _calc(self, cpu: DT31) -> int:
        value = as_op(cpu.pop()).resolve(cpu)
        if self.out is not None:
            cpu[self.out] = value
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"POP(out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        if self.out is not None:
            return f"POP {self.out}"
        return "POP"


class SEMP(Instruction):
    """Check if stack is empty and store result."""

    def __init__(self, out: Reference):
        """
        Args:
            out: Output reference to store the result (1 if empty, 0 if not empty).
        """
        super().__init__("SEMP")
        self.out = as_op(out)

    def _calc(self, cpu: DT31) -> int:
        if cpu.stack:
            value = 0
        else:
            value = 1
        cpu[self.out] = value
        return value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"SEMP(out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"SEMP {self.out}"


# ---------------------------------------- I/O --------------------------------------- #


class CP(Instruction):
    """Copy operand value to output reference."""

    def __init__(self, a: Operand | int, b: Reference):
        """
        Args:
            a: Source operand to copy from.
            b: Output reference to copy to.
        """
        super().__init__("CP")
        self.a = as_op(a)
        if not isinstance(b, Reference):
            raise ValueError("argument `b` must be a Reference")
        self.b = b

    def _calc(self, cpu: DT31) -> int:
        value = self.a.resolve(cpu)
        cpu[self.b] = value
        return value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}(a={self.a!r}, b={self.b!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"{self.name} {self.a}, {self.b}"


class NOUT(Instruction):
    """Output operand as a number."""

    def __init__(self, a: Operand, b: Operand | int = L[0]):
        """
        Args:
            a: Operand value to output as a number.
            b: If nonzero, append newline after output. Defaults to L[0] (no newline).
        """
        super().__init__("NOUT")
        self.a = as_op(a)
        self.b = as_op(b)

    def _calc(self, cpu: DT31) -> int:
        if self.b.resolve(cpu) != 0:
            end = "\n"
        else:
            end = ""
        print(self.a.resolve(cpu), end=end)
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"NOUT(a={self.a!r}, b={self.b!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"NOUT {self.a}, {self.b}"


class OOUT(Instruction):
    """Output operand as a character (using chr())."""

    def __init__(self, a: Operand, b: Operand | int = L[0]):
        """
        Args:
            a: Operand value to output as a character.
            b: If nonzero, append newline after output. Defaults to L[0] (no newline).
        """
        super().__init__("OOUT")
        self.a = as_op(a)
        self.b = as_op(b)

    def _calc(self, cpu: DT31) -> int:
        if self.b.resolve(cpu) != 0:
            end = "\n"
        else:
            end = ""
        print(chr(self.a.resolve(cpu)), end=end)
        return 0

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"OOUT(a={self.a!r}, b={self.b!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"OOUT {self.a}, {self.b}"


class NIN(Instruction):
    """Read number input from user."""

    def __init__(self, out: Reference):
        """
        Args:
            out: Output reference to store the input number.
        """
        super().__init__("NIN")
        self.out = as_op(out)

    def _calc(self, cpu: DT31) -> int:
        val = input(INPUT_PROMPT)
        val_int = int(val)
        cpu[self.out] = val_int
        return val_int

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"NIN(out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"NIN {self.out}"


class OIN(Instruction):
    """Read character input from user and store as ordinal value."""

    def __init__(self, out: Reference):
        """
        Args:
            out: Output reference to store the ordinal value of the input character.
        """
        super().__init__("OIN")
        self.out = as_op(out)

    def _calc(self, cpu: DT31) -> int:
        val = input("> ")
        val_ord = ord(val)
        cpu[self.out] = val_ord
        return val_ord

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"OIN(out={self.out!r})"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"OIN {self.out}"


class BRK(Instruction):
    """Breakpoint: dump CPU state and wait for Enter, then continue execution."""

    def __init__(self):
        super().__init__("BRK")

    def _calc(self, cpu: DT31) -> int:
        # Print in debug format: instruction -> result, then state
        print(f"{self.name} -> 0")
        print(cpu.state)
        input()
        return 0


class BRKD(Instruction):
    """Debug breakpoint: dump CPU state and switch to debug mode for rest of execution."""

    def __init__(self):
        super().__init__("BRKD")

    def _calc(self, cpu: DT31) -> int:
        # Print in debug format: instruction -> result, then state
        print(f"{self.name} -> 0")
        print(cpu.state)
        # Switch to debug mode - run() will handle waiting for input
        cpu.debug_mode = True
        return 0


# ------------------------------------ Randomness ------------------------------------ #


class RND(NullaryOperation):
    """Return a random bit."""

    def __init__(self, out: Reference):
        """
        Args:
            out: Output reference for result.
        """
        super().__init__("RND", out)

    def _calc(self, cpu: DT31) -> int:
        return random.getrandbits(1)


class RINT(BinaryOperation):
    """Return a random number between a and b (inclusive)."""

    def __init__(
        self, a: Operand | int, b: Operand | int, out: Reference | None = None
    ):
        """
        Args:
            a: Lowest integer value allowed
            b: Second operand of the addition.
            out: Optional output reference for result. If not provided, result stored in
                first operand.
        """
        super().__init__("ADD", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        a = self.a.resolve(cpu)
        b = self.b.resolve(cpu)
        if b < a:
            raise ValueError(f"RINT argument b must be ≥ argument a; got {a=}, {b=}")

        return random.randint(a, b)
