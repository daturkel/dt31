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


class BlankLine:
    """A blank line in a DT31 program.

    Blank lines are preserved when parsing assembly text with the `preserve_newlines`
    option. They have no effect on program execution and are primarily used for
    formatting and readability.

    Example:
        >>> program = [
        ...     I.CP(5, R.a),
        ...     BlankLine(),
        ...     I.ADD(R.a, 1),
        ... ]
    """

    def __str__(self) -> str:
        """Return assembly text representation of the blank line.

        Returns:
            An empty string.
        """
        return ""

    def __repr__(self) -> str:
        """Return Python API representation of the blank line.

        Returns:
            A string showing BlankLine construction.
        """
        return "BlankLine()"

    def __eq__(self, other):
        return type(self) is type(other)


def _find_label_colon(line: str) -> int:
    """Find the first ':' that's not inside a quoted string.

    Args:
        line: The line to search.

    Returns:
        The position of the first label colon, or -1 if none found.
    """
    in_quote = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == "'":
            in_quote = not in_quote
        elif char == "\\" and in_quote and i + 1 < len(line):
            # Skip the next character if we're in a quote and this is a backslash
            i += 1
        elif char == ":" and not in_quote:
            return i
        i += 1
    return -1


def parse_program(
    text: str,
    custom_instructions: dict[str, type[Instruction]] | None = None,
    preserve_newlines: bool = False,
) -> list[Instruction | Label | Comment | BlankLine]:
    """
    Parse DT31 assembly text into a program list.

    For an overview of the text syntax, see the main documentation of `dt31`.

    For the CLI tool to directly execute programs in the text syntax, see `dt31.cli`.

    Args:
        text: Assembly code as a string
        custom_instructions: Optional dict of custom instruction names to `Instruction`
            subclasses
        preserve_newlines: If True, preserve blank lines as BlankLine objects (default: False)

    Returns:
        List of Instructions, Labels, Comments, and optionally BlankLines ready for cpu.run()

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

        # Blank line (no code, no comment)
        if not line:
            if preserve_newlines:
                program.append(BlankLine())
            continue

        # Handle label definitions (can be multiple labels on same line)
        # Need to respect quoted strings when looking for ':' label delimiters
        labels_found = []
        while ":" in line:
            # Find the first ':' that's not inside a quoted string
            colon_pos = _find_label_colon(line)
            if colon_pos == -1:
                break  # No label colon found (all colons are in quotes)

            label_part = line[:colon_pos]
            line = line[colon_pos + 1 :].strip()
            label_name = label_part.strip()

            # Validate label name
            if label_name and not label_name.replace("_", "").isalnum():
                raise ParserError(
                    f"Line {line_num}: Invalid label name '{label_name}'. "
                    f"Labels must contain only alphanumeric characters and underscores."
                )

            if label_name:
                labels_found.append(label_name)

        # Add all found labels to program
        for label_name in labels_found:
            label = Label(label_name)
            program.append(label)

        # Attach comment only to the last label (if any labels were found)
        if comment_text and labels_found:
            program[-1].comment = comment_text

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
            # Decode escape sequences (e.g., '\n' -> newline)
            try:
                # Use 'unicode_escape' to handle common escape sequences
                decoded_char = char.encode().decode("unicode_escape")
            except Exception as e:
                raise ParserError(
                    f"Invalid escape sequence in character literal {token}: {e}"
                )

            if len(decoded_char) != 1:
                raise ParserError(
                    f"Invalid character literal {token}. "
                    f"Character literals must contain exactly one character."
                )
            return LC[decoded_char]

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
TOKEN_PATTERN = re.compile(
    r"""
    '           # Opening quote for character literal
    (?:         # Non-capturing group for character content
        \\.     # Escaped character (backslash + any char, e.g., \', \n)
        |       # OR
        [^']    # Any non-quote character
    )
    '           # Closing quote
    |           # OR (for non-character-literal tokens)
    [^\s,]+     # Any sequence of non-whitespace, non-comma characters
    """,
    re.VERBOSE,
)
MEMORY_PATTERN = re.compile(r"M?\[(.+)\]")
REGISTER_PREFIX_PATTERN = re.compile(r"R\.(\w+)")
