"""Exceptions used by dt31."""


class EndOfProgram(Exception):
    """Exception to throw when the end of the instructions is reached."""

    pass


class AssemblyError(Exception):
    """An exception to throw when the assembler encounters something wrong with a program."""

    pass


class ParserError(Exception):
    """Exception raised when parsing DT31 assembly text fails.

    This exception is raised for syntax errors, invalid operands,
    or other parsing issues in DT31 assembly code.
    """

    pass
