from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dt31.cpu import DT31  # pragma: no cover


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

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.__dict__ == other.__dict__


class Literal(Operand):
    """An operand representing a literal integer value.

    Literal operands resolve to their constant value regardless of CPU state.
    """

    def __init__(self, value: int, is_char: bool = False):
        """Initialize a literal operand.

        Args:
            value: The constant integer value this operand represents.
            is_char: Whether this literal represents a character (for output formatting).
        """
        self.value = value
        self.is_char = is_char

    def resolve(self, cpu: DT31) -> int:
        """Return the literal value.

        Args:
            cpu: The DT31 CPU instance (unused for literals).

        Returns:
            The constant value of this literal.
        """
        return self.value

    def __repr__(self) -> str:
        """Return Python API representation."""
        return str(self.value)

    def __str__(self) -> str:
        """Return assembly text representation."""
        if self.is_char:
            return f"'{chr(self.value)}'"
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


class _MetaCharLiteral(type):
    """Metaclass enabling bracket syntax for creating character Literal operands."""

    def __getitem__(self, arg: str) -> Literal:
        """Create a Literal operand from a character using bracket syntax.

        Args:
            arg: A single character string.

        Returns:
            A Literal operand with the character's ordinal value, marked as a character.

        Raises:
            ValueError: If arg is not a single character string.
        """
        if not isinstance(arg, str) or len(arg) != 1:
            raise ValueError(f"LC requires a single character, got: {arg}")
        return Literal(ord(arg), is_char=True)


class LC(metaclass=_MetaCharLiteral):
    """Convenience class for creating character Literal operands using bracket syntax.

    Examples:
        LC['A']  # Creates Literal(65)
        LC['z']  # Creates Literal(122)
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

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"M[{self.address!r}]"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"[{self.address}]"


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


def validate_register_name(name: str) -> None:
    """Validate that a register name is a valid Python identifier.

    Register names must be valid Python identifiers and cannot start with
    double underscores to avoid conflicts with dunder methods.

    Args:
        name: The register name to validate.

    Raises:
        ValueError: If the register name is not a valid Python identifier
            or starts with double underscores.

    Examples:
        >>> validate_register_name("a")  # Valid
        >>> validate_register_name("my_reg")  # Valid
        >>> validate_register_name("reg123")  # Valid
        >>> validate_register_name("_private")  # Valid
        >>> validate_register_name("123")  # Raises ValueError
        >>> validate_register_name("my-reg")  # Raises ValueError
        >>> validate_register_name("__dunder__")  # Raises ValueError
    """
    if not name.isidentifier():
        raise ValueError(
            f"Invalid register name '{name}'. "
            f"Register names must be valid Python identifiers "
            f"(letters, digits, underscores; cannot start with a digit)."
        )
    if name.startswith("__"):
        raise ValueError(
            f"Invalid register name '{name}'. "
            f"Register names cannot start with double underscores (reserved for dunder methods)."
        )


class RegisterReference(Operand):
    """An operand representing a CPU register reference.

    Register references resolve to the value stored in the named register.

    Register names must be valid Python identifiers (letters, digits, underscores;
    cannot start with a digit) and cannot start with double underscores (reserved
    for dunder methods).
    """

    def __init__(self, register: str):
        """Initialize a register reference operand.

        Args:
            register: The name of the register to reference. Must be a valid Python
                identifier and cannot start with double underscores.

        Raises:
            ValueError: If the register name is not a valid Python identifier or
                starts with double underscores.
        """
        validate_register_name(register)
        self.register = register

    def resolve(self, cpu: DT31) -> int:
        """Resolve the register reference to its current value.

        Args:
            cpu: The DT31 CPU instance providing register access.

        Returns:
            The value currently stored in the referenced register.
        """
        return cpu.get_register(self.register)

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"R.{self.register}"

    def __str__(self) -> str:
        """Return assembly text representation."""
        return f"R.{self.register}"


class _MetaRegister(type):
    """Metaclass enabling attribute syntax for RegisterReference operands."""

    def __getattribute__(self, arg: str):
        """Create a RegisterReference using attribute syntax.

        Args:
            arg: The name of the register.

        Returns:
            A RegisterReference operand, unless accessing special attributes.

        Raises:
            ValueError: If the register name is not a valid Python identifier.
        """
        # Don't intercept special attributes (dunder methods)
        if arg.startswith("__"):
            return super().__getattribute__(arg)
        return RegisterReference(arg)


class R(metaclass=_MetaRegister):
    """Convenience class for creating RegisterReference operands.

    Uses attribute syntax for ergonomic register references.

    Register names must be valid Python identifiers (letters, digits, underscores;
    cannot start with a digit) and cannot start with double underscores (reserved
    for dunder methods).

    Examples:
        R.a         # Creates RegisterReference("a")
        R.foo       # Creates RegisterReference("foo")
        R.my_reg    # Creates RegisterReference("my_reg")
        R._temp     # Creates RegisterReference("_temp") - valid
        R.__dunder  # Raises ValueError - double underscore prefix not allowed
        R.123       # SyntaxError - identifiers cannot start with digits
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


class Label:
    """A named label that marks a position in the program for jumps and calls.

    Labels are assembly-time constructs used to mark instruction positions in a program.
    They are removed during the assembly process and replaced with numeric instruction
    indices. Labels can only be used as destinations for jump and call instructions.

    Usage
    -----
    Labels are used in two contexts:

    1. **Definition**: Place a Label directly in the program list to mark a position:
       ```python
       program = [
           I.CP(R.a, L[0]),
           Label("loop"),      # Marks this position
           I.ADD(R.a, L[1]),
       ]
       ```

    2. **Reference**: Use a Label as the destination operand in jump/call instructions:
       ```python
       I.JMP(Label("loop"))     # Jump to the position marked by "loop"
       I.CALL(Label("func"))    # Call the function at "func"
       I.RJGT(Label("start"), R.a, L[10])  # Conditional relative jump
       ```

    Valid Instructions for Labels
    ------------------------------
    Labels can ONLY be used as the `dest` parameter in these instructions:
    - Absolute jumps: JMP, JEQ, JNE, JGT, JGE, JIF
    - Relative jumps: RJMP, RJEQ, RJNE, RJGT, RJGE, RJIF
    - Function calls: CALL, RCALL

    Invalid Usage
    -------------
    Labels cannot be used in arithmetic, logic, or other operations:
    ```python
    I.ADD(R.a, Label("x"))      # INVALID - will cause runtime error
    I.CP(Label("foo"), R.b)     # INVALID - will cause runtime error
    M[Label("addr")]            # INVALID - will cause runtime error
    ```

    Examples
    --------
    Simple loop counting from 0 to 10:
    ```python
    from dt31 import DT31, I, R, L, Label
    from dt31.assembler import assemble

    loop = Label("loop")
    program = [
        I.CP(R.a, L[0]),
        loop,                          # Mark loop start
        I.NOUT(R.a, L[1]),             # Print counter
        I.ADD(R.a, L[1]),              # Increment
        I.JGT(loop, L[10], R.a),       # Continue if a <= 10
    ]

    cpu = DT31()
    cpu.run(assemble(program))
    ```

    Function with label:
    ```python
    program = [
        I.CALL(Label("greet")),
        I.JMP(Label("end")),

        Label("greet"),
        I.OOUT(LC['H']),
        I.OOUT(LC['i']),
        I.RET(),

        Label("end"),
    ]
    ```
    """

    def __init__(self, name: str):
        """Initialize a label with a given name.

        Args:
            name: The symbolic name for this label.
        """
        self.name = name

    def resolve(self, cpu: DT31) -> int:
        """Resolve the label to an instruction position.

        This method should never be called during normal execution. Labels must be
        resolved during the assembly process before the program runs. If this method
        is called, it indicates the program was not assembled or the label was used
        incorrectly (e.g., in an arithmetic operation instead of a jump destination).

        Args:
            cpu: The DT31 CPU instance (unused).

        Raises:
            RuntimeError: Always raised, as labels must be resolved during assembly.
        """
        raise RuntimeError(
            f"Unresolved label '{self.name}' encountered at runtime. "
            "Programs containing labels must be assembled using assemble() before execution. "
            "Labels can only be used as jump/call destinations, not in arithmetic or other operations."
        )

    def __repr__(self) -> str:
        """Return Python API representation."""
        return f"{self.name}"

    def __str__(self) -> str:
        """Return assembly text representation (without colon)."""
        return f"{self.name}"

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.name == other.name


# Type alias for jump/call destination operands
Destination = Label | Operand | int
