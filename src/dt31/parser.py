import re

import dt31.instructions as I
from dt31.exceptions import ParserError
from dt31.instructions import Instruction
from dt31.operands import (
    L,
    LC,
    Label,
    M,
    Operand,
    R,
)


def parse_program(
    text: str,
    custom_instructions: dict[str, type[Instruction]] | None = None,
) -> list[Instruction | Label]:
    """
    Parse DT31 assembly text into a program list.

    For an overview of the text syntax, see the main documentation of `dt31`.

    For the CLI tool to directly execute programs in the text syntax, see `dt31.cli`.

    Args:
        text: Assembly code as a string
        custom_instructions: Optional dict of custom instruction names to `Instruction`
            subclasses

    Returns:
        List of Instructions and Labels ready for cpu.run()

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
        # Strip comments (everything after semicolon)
        line = line.split(";")[0].strip()
        if not line:
            continue

        # Handle label definitions
        label = None
        if ":" in line:
            label_part, line = line.split(":", 1)
            label = label_part.strip()
            line = line.strip()

            # Validate label name
            if label and not label.replace("_", "").isalnum():
                raise ParserError(
                    f"Line {line_num}: Invalid label name '{label}'. "
                    f"Labels must contain only alphanumeric characters and underscores."
                )

        if label:
            program.append(Label(label))

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
