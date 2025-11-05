"""Example demonstrating custom instructions in dt31.

This shows how to define custom instructions and use them programmatically.
For CLI usage, see the cli_example/ directory.
"""

from dt31 import DT31
from dt31.instructions import BinaryOperation, UnaryOperation
from dt31.operands import Operand, Reference
from dt31.parser import parse_program


class SQUARE(UnaryOperation):
    """Square a value and store the result."""

    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("SQUARE", a, out)

    def _calc(self, cpu: DT31) -> int:
        value = self.a.resolve(cpu)
        return value * value


class CLAMP(BinaryOperation):
    """Clamp a value between 0 and maximum."""

    def __init__(self, value: Operand, maximum: Operand, out: Reference | None = None):
        super().__init__("CLAMP", value, maximum, out)

    def _calc(self, cpu: DT31) -> int:
        val = self.a.resolve(cpu)
        max_val = self.b.resolve(cpu)
        return max(0, min(val, max_val))


if __name__ == "__main__":
    cpu = DT31()

    # Define custom instructions
    custom_instructions = {
        "SQUARE": SQUARE,
        "CLAMP": CLAMP,
    }

    # Program using custom instructions
    assembly = """
        CP 5, R.a
        SQUARE R.a          ; a = 25
        NOUT R.a, 1

        CP 150, R.b
        CLAMP R.b, 100, R.c ; c = 100 (clamped)
        NOUT R.c, 1
    """

    program = parse_program(assembly, custom_instructions=custom_instructions)
    cpu.run(program)
    # Output:
    # 25
    # 100
