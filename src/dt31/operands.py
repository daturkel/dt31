from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cpu import DT31  # pragma: no cover


class Operand:
    def resolve(self, cpu: DT31) -> int:
        raise NotImplementedError()


class Literal(Operand):
    def __init__(self, value: int):
        self.value = value

    def resolve(self, cpu: DT31) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)


class _MetaLiteral(type):
    def __getitem__(self, arg: int) -> Literal:
        return Literal(arg)


class L(metaclass=_MetaLiteral):
    pass


class MemoryReference(Operand):
    def __init__(self, address: int | Operand):
        self.address = address

    def resolve_address(self, cpu: DT31) -> int:
        if not isinstance(self.address, int):
            return self.address.resolve(cpu)
        else:
            return self.address

    def resolve(self, cpu: DT31) -> int:
        return cpu.get_memory(self.resolve_address(cpu))

    def __str__(self) -> str:
        return f"M[{self.address}]"


class _MetaMemory(type):
    def __getitem__(self, arg: int | Operand) -> MemoryReference:
        return MemoryReference(arg)


class M(metaclass=_MetaMemory):
    pass


class RegisterReference(Operand):
    def __init__(self, register: str):
        self.register = register

    def resolve(self, cpu: DT31) -> int:
        return cpu.get_register(self.register)

    def __str__(self) -> str:
        return f"R[{self.register}]"


class _MetaRegister(type):
    def __getitem__(self, arg: str) -> RegisterReference:
        return RegisterReference(arg)

    def __getattribute__(self, arg: str):
        # Don't intercept special attributes (dunder methods)
        if arg.startswith("_"):
            return super().__getattribute__(arg)
        return RegisterReference(arg)


class R(metaclass=_MetaRegister):
    pass


Reference = RegisterReference | MemoryReference


def as_op(arg: int | Operand):
    if isinstance(arg, Operand):
        return arg
    elif isinstance(arg, int):
        return Literal(arg)
    else:
        raise ValueError(f"can't coerce value {arg} into operand")
