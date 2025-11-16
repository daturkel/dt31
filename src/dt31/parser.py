import re

import dt31.instructions as I
from dt31.exceptions import ParserError
from dt31.instructions import Instruction
from dt31.operands import (
    LC,
    L,
    Label,
    M,
    Operand,
    R,
)


class Comment:
    """A standalone comment line in a DT31 program.

    Comments are preserved when parsing assembly text and can be included in programs
    created with the Python API. They have no effect on program execution.

    Args:
        text: The comment text (without the leading semicolon).

    Example:
        >>> program = [
        ...     Comment("Initialize counter"),
        ...     I.CP(5, R.a),
        ... ]
    """

    def __init__(self, comment: str):
        """Initialize a comment with the given text.

        Args:
            text: The comment text (without the leading semicolon).
        """
        self.comment = comment

    def __str__(self) -> str:
        """Return assembly text representation of the comment.

        Returns:
            The comment formatted as "; text".
        """
        return f"; {self.comment}"

    def __repr__(self) -> str:
        """Return Python API representation of the comment.

        Returns:
            A string showing Comment construction.
        """
        return f'Comment("{self.comment}")'

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.comment == other.comment


def parse_program(
    text: str,
    custom_instructions: dict[str, type[Instruction]] | None = None,
) -> list[Instruction | Label | Comment]:
    """
    Parse DT31 assembly text into a program list.

    For an overview of the text syntax, see the main documentation of `dt31`.

    For the CLI tool to directly execute programs in the text syntax, see `dt31.cli`.

    Args:
        text: Assembly code as a string
        custom_instructions: Optional dict of custom instruction names to `Instruction`
            subclasses

    Returns:
        List of Instructions, Labels, and Comments ready for cpu.run()

    Example:
        >>> from dt31 import DT31
        >>> from dt31.assembler import extract_registers_from_program
        >>> text = '''
        ... CP 5, R.a
        ... loop:
        ...     NOUT R.a, 1
        ...     SUB R.a, 1
        ...     JGT loop, R.a, 0
        ... '''
        >>> program = parse_program(text)
        >>> registers = extract_registers_from_program(program)
        >>> cpu = DT31(registers=registers)
        >>> cpu.run(program)
        5
        4
        3
        2
        1
    """
    custom_instructions = custom_instructions or {}
    program = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        # Extract comment (everything after semicolon)
        comment_text = None
        if ";" in line:
            line, comment_part = line.split(";", 1)
            comment_text = comment_part.strip()

        line = line.strip()

        # Standalone comment line (no code, only comment)
        if not line and comment_text:
            program.append(Comment(comment_text))
            continue

        if not line:
            continue

        # Handle label definitions
        label_name = None
        if ":" in line:
            label_part, line = line.split(":", 1)
            label_name = label_part.strip()
            line = line.strip()

            # Validate label name
            if label_name and not label_name.replace("_", "").isalnum():
                raise ParserError(
                    f"Line {line_num}: Invalid label name '{label_name}'. "
                    f"Labels must contain only alphanumeric characters and underscores."
                )

        if label_name:
            label = Label(label_name)
            if comment_text:
                label.comment = comment_text
            program.append(label)

        if not line:
            continue

        # Tokenize: preserve brackets, quoted strings, R.name
        tokens = TOKEN_PATTERN.findall(line)

        if not tokens:
            continue

        inst_name = tokens[0]

        try:
            operands = [parse_operand(t) for t in tokens[1:]]
        except ParserError as e:
            raise ParserError(f"Line {line_num}: {e}") from e

        # Get instruction function
        try:
            if inst_name in custom_instructions:
                inst_func = custom_instructions[inst_name]
            else:
                inst_func = getattr(I, inst_name.upper())
        except AttributeError:
            raise ParserError(f"Line {line_num}: Unknown instruction '{inst_name}'")

        # Type checker can't verify operand types for dynamically looked up instructions.
        # Labels are valid for jump/call instructions (Destination = Label | Operand | int).
        try:
            instruction = inst_func(*operands)  # type: ignore[arg-type]
        except (TypeError, ValueError) as e:
            raise ParserError(
                f"Line {line_num}: Error creating instruction '{inst_name}': {e}"
            ) from e

        # Set comment if present
        if comment_text:
            instruction.comment = comment_text

        program.append(instruction)

    return program


def parse_operand(token: str) -> Operand | Label:
    """
    Parse a single operand token into an Operand object.

    Supports:
    - Numeric literals: 42, -5
    - Character literals: 'H', 'a'
    - Registers: R.a, R.b, R.c (must use R. prefix)
    - Memory: [100], M[100], [R.a], M[R.a]
    - Labels: loop, end, start (any bare identifier not matching above)

    Args:
        token: String token to parse

    Returns:
        An Operand object (Literal, RegisterReference, MemoryReference, or Label)

    Note:
        Registers MUST use the R. prefix syntax (e.g., R.a, R.b).
        All bare identifiers that are not numeric literals or special syntax
        are treated as labels. Register names are not validated at parse time.
    """
    match token:
        # Character literal: 'H'
        case str() if token.startswith("'") and token.endswith("'"):
            char = token[1:-1]
            if len(char) != 1:
                raise ParserError(
                    f"Invalid character literal '{token}'. "
                    f"Character literals must contain exactly one character."
                )
            return LC[char]

        # Memory reference: [100] or M[100] or [a] or M[R.a]
        case str() if m := MEMORY_PATTERN.match(token):
            inner = m.group(1)
            inner_operand = parse_operand(inner)  # Recursive
            # Labels cannot be used as memory addresses
            if isinstance(inner_operand, Label):
                raise ParserError(
                    f"Invalid memory reference: Labels cannot be used as memory addresses. "
                    f"Found label '{inner_operand.name}' in memory reference '{token}'"
                )
            return M[inner_operand]

        # Register with prefix: R.a
        case str() if m := REGISTER_PREFIX_PATTERN.match(token):
            reg_name = m.group(1)
            return getattr(R, reg_name)

        # Numeric literal: 42 or -5
        case str() if token.lstrip("-").isdigit():
            return L[int(token)]

        # Bare identifier: always treated as a label
        # Registers must use R.name syntax
        case _:
            return Label(token)


# Precompiled regex patterns for parsing
TOKEN_PATTERN = re.compile(r"'[^']+'|[^\s,]+")
MEMORY_PATTERN = re.compile(r"M?\[(.+)\]")
REGISTER_PREFIX_PATTERN = re.compile(r"R\.(\w+)")
