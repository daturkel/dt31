from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cpu import DT31  # pragma: no cover


class Operand:
    """Base class for operands in DT31 assembly instructions.

    Operands can be literals, register references, or memory references.
    All operands must implement the resolve method to return their value.
    """

    def resolve(self, cpu: DT31) -> int:
        """Resolve the operand to its integer value.

        Args:
            cpu: The DT31 CPU instance providing context for resolution.

        Returns:
            The resolved integer value of this operand.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError()


class Literal(Operand):
    """An operand representing a literal integer value.

    Literal operands resolve to their constant value regardless of CPU state.
    """

    def __init__(self, value: int):
        """Initialize a literal operand.

        Args:
            value: The constant integer value this operand represents.
        """
        self.value = value

    def resolve(self, cpu: DT31) -> int:
        """Return the literal value.

        Args:
            cpu: The DT31 CPU instance (unused for literals).

        Returns:
            The constant value of this literal.
        """
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, int):
            return other == self.value
        elif isinstance(other, Literal):
            return other.value == self.value
        return False


class _MetaLiteral(type):
    """Metaclass enabling bracket syntax for creating Literal operands."""

    def __getitem__(self, arg: int) -> Literal:
        """Create a Literal operand using bracket syntax.

        Args:
            arg: The integer value for the literal.

        Returns:
            A Literal operand with the specified value.
        """
        return Literal(arg)


class L(metaclass=_MetaLiteral):
    """Convenience class for creating Literal operands using bracket syntax.

    Examples:
        L[42]  # Creates Literal(42)
        L[0]   # Creates Literal(0)
    """

    pass


class MemoryReference(Operand):
    """An operand representing a memory address reference.

    Memory references resolve to the value stored at a memory address.
    The address itself can be a constant or another operand (indirect addressing).
    """

    def __init__(self, address: int | Operand):
        """Initialize a memory reference operand.

        Args:
            address: The memory address, either as an integer literal or reference that
                resolves to an address (for indirect addressing).
        """
        self.address = as_op(address)

    def resolve(self, cpu: DT31) -> int:
        """Resolve the memory reference to the value at its address.

        Args:
            cpu: The DT31 CPU instance providing memory access.

        Returns:
            The value stored at the resolved memory address.
        """
        return cpu.get_memory(self.resolve_address(cpu))

    def resolve_address(self, cpu: DT31) -> int:
        """Resolve the address of this memory reference.

        Args:
            cpu: The DT31 CPU instance for resolving operand addresses.

        Returns:
            The integer memory address.
        """
        return self.address.resolve(cpu)

    def __str__(self) -> str:
        return f"M[{self.address}]"


class _MetaMemory(type):
    """Metaclass enabling bracket syntax for creating MemoryReference operands."""

    def __getitem__(self, arg: int | Operand) -> MemoryReference:
        """Create a MemoryReference operand using bracket syntax.

        Args:
            arg: The memory address, either as an integer or another operand.

        Returns:
            A MemoryReference operand for the specified address.
        """
        return MemoryReference(arg)


class M(metaclass=_MetaMemory):
    """Convenience class for creating MemoryReference operands using bracket syntax.

    Examples:
        M[100]      # Direct memory access at address 100
        M[R.a]      # Indirect memory access using register 'a' as address
        M[M[50]]    # Double indirect addressing
    """

    pass


class RegisterReference(Operand):
    """An operand representing a CPU register reference.

    Register references resolve to the value stored in the named register.
    """

    def __init__(self, register: str):
        """Initialize a register reference operand.

        Args:
            register: The name of the register to reference.
        """
        self.register = register

    def resolve(self, cpu: DT31) -> int:
        """Resolve the register reference to its current value.

        Args:
            cpu: The DT31 CPU instance providing register access.

        Returns:
            The value currently stored in the referenced register.
        """
        return cpu.get_register(self.register)

    def __str__(self) -> str:
        return f"R[{self.register}]"


class _MetaRegister(type):
    """Metaclass enabling bracket and attribute syntax for RegisterReference operands."""

    def __getitem__(self, arg: str) -> RegisterReference:
        """Create a RegisterReference using bracket syntax.

        Args:
            arg: The name of the register.

        Returns:
            A RegisterReference operand for the specified register.
        """
        return RegisterReference(arg)

    def __getattribute__(self, arg: str):
        """Create a RegisterReference using attribute syntax.

        Args:
            arg: The name of the register.

        Returns:
            A RegisterReference operand, unless accessing special attributes.
        """
        # Don't intercept special attributes (dunder methods)
        if arg.startswith("_"):
            return super().__getattribute__(arg)
        return RegisterReference(arg)


class R(metaclass=_MetaRegister):
    """Convenience class for creating RegisterReference operands.

    Supports both bracket and attribute syntax for ergonomic register references.

    Examples:
        R.a         # Creates RegisterReference("a")
        R["a"]      # Also creates RegisterReference("a")
    """

    pass


Reference = RegisterReference | MemoryReference


def as_op(arg: int | Operand):
    """Coerce a value into an Operand.

    Converts integers to Literal operands, while passing through existing operands.

    Args:
        arg: Either an integer to be converted or an existing Operand.

    Returns:
        An Operand instance (either the input operand or a new Literal).

    Raises:
        ValueError: If the argument cannot be coerced into an operand.
    """
    if isinstance(arg, Operand):
        return arg
    elif isinstance(arg, int):
        return Literal(arg)
    else:
        raise ValueError(f"can't coerce value {arg} into operand")
