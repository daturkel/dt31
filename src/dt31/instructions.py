from typing import TYPE_CHECKING

from .cpu import DT31
from .operands import L, Operand, Reference, as_op

if TYPE_CHECKING:
    from .cpu import DT31  # pragma: no cover


class Instruction:
    def __init__(self, name: str):
        self.name = name

    def _calc(self, cpu: DT31) -> int:
        raise NotImplementedError()

    def _advance(self, cpu: DT31, value: int):
        # default behavior is to increment the instruction register by 1
        cpu.set_register("ip", cpu.get_register("ip") + 1)

    def __call__(self, cpu: DT31) -> int:
        value = self._calc(cpu)
        self._advance(cpu, value)
        return value


class NOOP(Instruction):
    def __init__(self):
        super().__init__("NOOP")

    def _calc(self, cpu: DT31) -> int:
        return 0


class UnaryOperation(Instruction):
    def __init__(self, name: str, a: Operand | int, out: Operand | None = None):
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


# ---------------------------------- bitwise and alu --------------------------------- #
class BinaryOperation(Instruction):
    def __init__(
        self, name: str, a: Operand | int, b: Operand | int, out: Operand | None = None
    ):
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


class ADD(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("ADD", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) + self.b.resolve(cpu)


class SUB(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("SUB", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) - self.b.resolve(cpu)


class MUL(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("MUL", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) * self.b.resolve(cpu)


class DIV(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("DIV", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) // self.b.resolve(cpu)


class MOD(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("MOD", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) % self.b.resolve(cpu)


class BSL(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("BSL", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) << self.b.resolve(cpu)


class BSR(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("BSR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) >> self.b.resolve(cpu)


class BAND(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("BAND", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) & self.b.resolve(cpu)


class BOR(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("BOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) | self.b.resolve(cpu)


class BXOR(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("BXOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return self.a.resolve(cpu) ^ self.b.resolve(cpu)


class BNOT(UnaryOperation):
    def __init__(self, a: Operand | int, out: Operand | None = None):
        super().__init__("BNOT", a, out)

    def _calc(self, cpu: DT31) -> int:
        return ~self.a.resolve(cpu)


# ------------------------------------ comparisons ----------------------------------- #
class LT(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("LT", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) < self.b.resolve(cpu))


class GT(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("GT", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) > self.b.resolve(cpu))


class LE(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("LE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) <= self.b.resolve(cpu))


class GE(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("GE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) >= self.b.resolve(cpu))


class EQ(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("EQ", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) == self.b.resolve(cpu))


class NE(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("NE", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) != self.b.resolve(cpu))


# ---------------------------------- pythonic logic ---------------------------------- #
class AND(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("AND", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) and self.b.resolve(cpu))


class OR(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("OR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        return int(self.a.resolve(cpu) or self.b.resolve(cpu))


class XOR(BinaryOperation):
    def __init__(self, a: Operand | int, b: Operand | int, out: Operand | None = None):
        super().__init__("XOR", a, b, out)

    def _calc(self, cpu: DT31) -> int:
        a = self.a.resolve(cpu)
        b = self.b.resolve(cpu)
        return int((a and not b) or (b and not a))


class NOT(UnaryOperation):
    def __init__(self, a: Operand | int, out: Operand | None = None):
        super().__init__("NOT", a, out)

    def _calc(self, cpu: DT31) -> int:
        return int(not self.a.resolve(cpu))


# --------------------------------------- jumps -------------------------------------- #
class Jump(Instruction):
    def __init__(self, name: str, dest: Operand | int):
        super().__init__(name)
        self.dest = as_op(dest)

    def _jump_condition(self, cpu: DT31) -> bool:
        raise NotImplementedError()

    def _jump_destination(self, cpu: DT31) -> int:
        raise NotImplementedError()

    def _calc(self, cpu: DT31) -> int:
        return 0

    def _advance(self, cpu: DT31, value: int):
        if self._jump_condition(cpu):
            cpu.set_register("ip", self._jump_destination(cpu))
        else:
            cpu.set_register("ip", cpu.get_register("ip") + 1)


class UnaryJump(Jump):
    def __init__(self, name: str, dest: Operand | int, a: Operand | int):
        super().__init__(name, dest)
        self.a = as_op(a)


class BinaryJump(Jump):
    def __init__(
        self, name: str, dest: Operand | int, a: Operand | int, b: Operand | int
    ):
        super().__init__(name, dest)
        self.a = as_op(a)
        self.b = as_op(b)


class ExactJumpMixin(Jump):
    def _jump_destination(self, cpu: DT31) -> int:
        return self.dest.resolve(cpu)


class RelativeJumpMixin(Jump):
    def _jump_destination(self, cpu: DT31) -> int:
        return cpu.get_register("ip") + self.dest.resolve(cpu)


class UnconditionalJumpMixin(Jump):
    def _jump_condition(self, cpu: DT31):
        return True


class IfEqualJumpMixin(BinaryJump):
    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) == self.b.resolve(cpu)


class IfUnequalJumpMixin(BinaryJump):
    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) != self.b.resolve(cpu)


class IfGTJumpMixin(BinaryJump):
    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) > self.b.resolve(cpu)


class IfGEJumpMixin(BinaryJump):
    def _jump_condition(self, cpu: DT31) -> bool:
        return self.a.resolve(cpu) >= self.b.resolve(cpu)


class IfJumpMixin(UnaryJump):
    def _jump_condition(self, cpu: DT31) -> bool:
        return bool(self.a.resolve(cpu))


class JMP(ExactJumpMixin, UnconditionalJumpMixin):
    def __init__(self, dest: Operand | int):
        super().__init__("JMP", dest)


class RJMP(RelativeJumpMixin, UnconditionalJumpMixin):
    def __init__(self, delta: Operand | int):
        super().__init__("RJMP", delta)


class JEQ(ExactJumpMixin, IfEqualJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("JEQ", dest, a, b)


class RJEQ(RelativeJumpMixin, IfEqualJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("RJEQ", dest, a, b)


class JNE(ExactJumpMixin, IfUnequalJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("RNE", dest, a, b)


class RJNE(RelativeJumpMixin, IfUnequalJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("RJNE", dest, a, b)


class JGT(ExactJumpMixin, IfGTJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("JGT", dest, a, b)


class RJGT(RelativeJumpMixin, IfGTJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("RJGT", dest, a, b)


class JGE(ExactJumpMixin, IfGEJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("JGE", dest, a, b)


class RJGE(RelativeJumpMixin, IfGEJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int, b: Operand | int):
        super().__init__("RJGE", dest, a, b)


class JIF(ExactJumpMixin, IfJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int):
        super().__init__("JIF", dest, a)


class RJIF(RelativeJumpMixin, IfJumpMixin):
    def __init__(self, dest: Operand | int, a: Operand | int):
        super().__init__("RJIF", dest, a)


# --------------------------------------- stack -------------------------------------- #


class PUSH(Instruction):
    def __init__(self, a: Operand | int):
        super().__init__("PUSH")
        self.a = as_op(a)

    def _calc(self, cpu: DT31) -> int:
        cpu.push(self.a.resolve(cpu))
        return 0


class POP(Instruction):
    def __init__(self, out: Reference):
        super().__init__("POP")
        self.out = out

    def _calc(self, cpu: DT31) -> int:
        cpu[self.out] = as_op(cpu.pop()).resolve(cpu)
        return 0


# --------------------------------------- other -------------------------------------- #


class CP(Instruction):
    def __init__(self, a: Operand | int, out: Reference):
        self.a = as_op(a)
        self.out = out

    def _calc(self, cpu: DT31) -> int:
        cpu[self.out] = self.a.resolve(cpu)
        return 0


class OUT(Instruction):
    def __init__(self, a: Operand, n: Operand = L[0]):
        self.a = as_op(a)
        self.n = as_op(n)

    def _calc(self, cpu: DT31) -> int:
        if self.n.resolve(cpu) != 0:
            end = "\n"
        else:
            end = ""
        print(self.a.resolve(cpu), end=end)
        return 0


class NIN(Instruction):
    def __init__(self, out: Reference):
        self.out = as_op(out)

    def _calc(self, cpu: DT31) -> int:
        val = input()
        val_int = int(val)
        cpu[self.out] = val_int
        return val_int


class OIN(Instruction):
    def __init__(self, out: Reference):
        self.out = as_op(out)

    def _calc(self, cpu: DT31) -> int:
        val = input()
        val_ord = ord(val)
        cpu[self.out] = val_ord
        return val_ord
