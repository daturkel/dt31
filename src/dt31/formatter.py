"""Program formatting utilities for converting programs to assembly text and to
Python source.

This module provides functionality for converting dt31 programs (lists of
instructions, labels, and comments) into human-readable assembly text format
with configurable formatting options, and into standalone Python source files
using the Python API.
"""

import json
import keyword
from typing import Literal

from dt31.assembler import extract_registers_from_program
from dt31.instructions import Instruction, Jump, RelativeJumpMixin
from dt31.operands import (
    Label,
    MemoryReference,
    Offset,
    Operand,
    RegisterReference,
    validate_register_name,
)
from dt31.operands import Literal as OperandLiteral
from dt31.parser import BlankLine, Comment


def program_to_text(
    program: list[Instruction | Label | Comment | BlankLine] | list[Instruction],
    *,
    indent_size: int = 4,
    label_inline: bool = False,
    blank_lines: Literal["auto", "preserve", "none"] = "preserve",
    align_comments: bool = False,
    comment_column: int | None = None,
    comment_margin: int = 2,
    strip_comments: bool = False,
    hide_default_args: bool = True,
) -> str:
    """Convert a program to assembly text format with configurable formatting.

    Converts a list of instructions, labels, and comments (whether created programmatically
    in Python or parsed from text) into human-readable assembly text syntax.

    Args:
        program: List of instructions, labels, comments, and blank lines in source order.
        indent_size: Number of spaces per indentation level (default: 4).
        label_inline: If True, place labels on same line as next instruction (default: False).
        blank_lines: Controls blank line handling. "preserve" preserves blank lines from source,
            "auto" adds blank lines before labels, "none" removes automatic blank lines (default: "preserve").
        align_comments: If True, align inline comments at comment_column (default: False).
        comment_column: Column position for aligned comments. If None and align_comments=True,
            automatically calculated based on longest instruction + comment_margin (default: None).
        comment_margin: Spaces before inline comment semicolon. Also used when auto-calculating
            comment_column for aligned comments (default: 2).
        strip_comments: If True, remove all comments from output. (default: False).
        hide_default_args: If True, hide arguments when they match the default value (default: True).

    Returns:
        A string containing the assembly text representation of the program,
        with one instruction, label, or comment per line.

    Examples:
        Default formatting:
        ```python
        from dt31 import I, R, L, Label
        from dt31.formatter import program_to_text

        program = [
            I.CP(5, R.a),
            loop := Label("loop"),
            I.NOUT(R.a, L[1]),
            I.SUB(R.a, L[1]),
            I.JGT(loop, R.a, L[0]),
        ]

        text = program_to_text(program)
        print(text)
        #     CP 5, R.a
        #
        # loop:
        #     NOUT R.a, 1
        #     SUB R.a, 1, R.a
        #     JGT loop, R.a, 0
        ```

        Custom formatting with 2-space indent, inline labels, and no blank lines:
        ```python
        text = program_to_text(
            program,
            indent_size=2,
            label_inline=True,
            blank_lines="none",
        )
        #   CP 5, R.a
        # loop: NOUT R.a, 1
        #   SUB R.a, 1, R.a
        #   JGT loop, R.a, 0
        ```

        Auto-aligned comments:
        ```python
        program_with_comments = [
            I.CP(5, R.a).with_comment("Initialize"),
            I.ADD(R.a, L[1]).with_comment("Increment"),
        ]
        text = program_to_text(program_with_comments, align_comments=True)
        #     CP 5, R.a        ; Initialize
        #     ADD R.a, 1, R.a  ; Increment
        ```

        Aligned comments at specific column:
        ```python
        text = program_to_text(program_with_comments, align_comments=True, comment_column=30)
        #     CP 5, R.a              ; Initialize
        #     ADD R.a, 1, R.a        ; Increment
        ```

        Auto-aligned comments with custom margin:
        ```python
        text = program_to_text(program_with_comments, align_comments=True, comment_margin=4)
        #     CP 5, R.a            ; Initialize
        #     ADD R.a, 1, R.a      ; Increment
        ```

        Strip all comments:
        ```python
        text = program_to_text(program_with_comments, strip_comments=True)
        #     CP 5, R.a
        #     ADD R.a, 1, R.a
        ```

        Hide default arguments:
        ```python
        program = [
            I.ADD(R.a, R.b),  # Default out=R.a
            I.NOUT(R.a),      # Default b=L[0] (no newline)
        ]
        text = program_to_text(program, hide_default_args=True)
        #     ADD R.a, R.b
        #     NOUT R.a
        # vs without hide_default_args (hide_default_args=False):
        #     ADD R.a, R.b, R.a
        #     NOUT R.a, 0
        ```
    """
    # Auto-calculate comment column if not specified
    if align_comments and comment_column is None and not strip_comments:
        # Generate program without comments to measure instruction widths
        stripped_text = program_to_text(
            program,
            indent_size=indent_size,
            label_inline=label_inline,
            blank_lines=blank_lines,
            strip_comments=True,  # Remove comments for measurement
            hide_default_args=hide_default_args,
        )

        # Find longest line
        max_length = max((len(line) for line in stripped_text.splitlines()), default=0)

        # Calculate comment column
        comment_column = max_length + comment_margin

    indent = " " * indent_size
    lines = []
    pending_labels: list[Label] = []
    prev_was_label = False

    for item in program:
        if isinstance(item, BlankLine):
            # Preserve blank lines only if blank_lines is "preserve"
            if blank_lines == "preserve":
                lines.append("")
            prev_was_label = False
        elif isinstance(item, Comment):
            # Standalone comments are never indented or aligned
            if not strip_comments:
                lines.append(str(item))
            prev_was_label = False
        elif isinstance(item, Label):
            # Add blank line before label if blank_lines is "auto" (but not before first item or consecutive labels)
            if blank_lines == "auto" and lines and not prev_was_label:
                # Look backwards to find where to insert blank line
                # If there are comments immediately before this label, insert blank before first comment
                insert_idx = len(lines)
                while insert_idx > 0 and lines[insert_idx - 1].startswith(";"):
                    insert_idx -= 1
                lines.insert(insert_idx, "")

            if label_inline:
                # Collect labels to put inline with next instruction
                pending_labels.append(item)
            else:
                # Labels on separate lines
                line = _format_label(
                    item,
                    align_comments,
                    comment_column,
                    comment_margin,
                    strip_comments,
                )
                lines.append(line)

            prev_was_label = True
        else:
            # Instruction
            prev_was_label = False

            # Handle pending inline labels
            if pending_labels:
                label_prefix = " ".join(f"{lbl.name}:" for lbl in pending_labels) + " "
                # Comments from inline labels are handled by the instruction comment
                # (use the instruction's comment if it exists, otherwise use last label's comment)
                if strip_comments:
                    comment = ""
                else:
                    comment = item.comment or pending_labels[-1].comment or ""
                pending_labels = []
            else:
                label_prefix = indent
                comment = "" if strip_comments else item.comment

            instruction_text = item.to_concise_str() if hide_default_args else str(item)
            line = _format_instruction_with_comment(
                label_prefix + instruction_text,
                comment,
                align_comments,
                comment_column,
                comment_margin,
            )
            lines.append(line)

    # Handle any remaining labels at end of program
    for lbl in pending_labels:
        line = _format_label(
            lbl, align_comments, comment_column, comment_margin, strip_comments
        )
        lines.append(line)

    result = "\n".join(lines)

    # Ensure trailing newline (POSIX standard for text files)
    if result and not result.endswith("\n"):
        result += "\n"

    return result


def _format_label(
    label: Label,
    align_comments: bool,
    comment_column: int | None,
    comment_margin: int,
    strip_comments: bool = False,
) -> str:
    """Format a label with optional comment alignment."""
    line = f"{label.name}:"
    if label.comment and not strip_comments:
        line = _format_instruction_with_comment(
            line, label.comment, align_comments, comment_column, comment_margin
        )
    return line


def _format_instruction_with_comment(
    instruction_text: str,
    comment: str,
    align_comments: bool,
    comment_column: int | None,
    comment_margin: int,
) -> str:
    """Format an instruction with its comment, handling alignment if requested."""
    if not comment:
        return instruction_text

    if align_comments and comment_column is not None:
        current_len = len(instruction_text)
        if current_len < comment_column:
            padding = comment_column - current_len
            return f"{instruction_text}{' ' * padding}; {comment}"
        else:
            # Instruction exceeds column, fall back to margin
            return f"{instruction_text}{' ' * comment_margin}; {comment}"
    else:
        # No alignment, just use margin
        return f"{instruction_text}{' ' * comment_margin}; {comment}"


# Names the generated module binds itself: every dt31 symbol it may import, plus
# its two module-level variables. Binding a label to one of these would shadow it.
_RESERVED_NAMES = frozenset(
    {"DT31", "I", "L", "LC", "Label", "M", "R", "cpu", "program"}
)


def _label_ref(
    label: Label,
    introduced: set[str],
    comment: str = "",
    parenthesize: bool = False,
) -> str:
    """Return the Python expression to use for one occurrence of a label.

    If a label name is a valid Python variable name that doesn't collide with a
    name the generated module already binds, we'll use that. Otherwise, we can
    just use a literal `Label("1invalidname")` object.

    Args:
        label: The label occurrence being rendered (a program-list marker, or a
            jump/call instruction's `dest`).
        introduced: Names of labels whose walrus binding has already been emitted;
            mutated in place as labels are introduced.
        comment: A rendered `.with_comment(...)` call to attach, or `""`. On the
            occurrence that introduces a walrus binding it goes inside the
            binding, so the bound name and the list element are one object. A
            marker whose name was already bound by an earlier forward jump takes
            it outside, since the binding can't be amended in place.
        parenthesize: Wrap a walrus binding in parentheses. Required when the
            occurrence is a keyword argument's value, which PEP 572 won't accept
            bare; a list element takes it without.

    Returns:
        `'name := Label("name")'` on a usable identifier's first occurrence,
        `"name"` on later occurrences, or `'Label("name")'` (always, no tracking)
        if the name isn't a usable Python identifier or is in `_RESERVED_NAMES`.
    """
    name = label.name
    if not name.isidentifier() or keyword.iskeyword(name) or name in _RESERVED_NAMES:
        return f"Label({json.dumps(name, ensure_ascii=False)}){comment}"
    if name not in introduced:
        introduced.add(name)
        binding = f"{name} := Label({json.dumps(name, ensure_ascii=False)}){comment}"
        return f"({binding})" if parenthesize else binding
    return f"{name}{comment}"


def _comment_suffix(item: Instruction | Label) -> str:
    """Return a `.with_comment(...)` call for a commented item, else an empty string.

    Args:
        item: The instruction or label being rendered.

    Returns:
        `'.with_comment("text")'` if the item carries a comment, otherwise `""`.
    """
    if not item.comment:
        return ""
    return f".with_comment({json.dumps(item.comment, ensure_ascii=False)})"


def _collect_symbols(
    program: list[Instruction | Label | Comment | BlankLine] | list[Instruction],
) -> set[str]:
    """Collect the dt31 operand symbols a generated program body will reference.

    Walks the program's operands rather than the rendered source, so comment text
    can't introduce a spurious import.

    Args:
        program: List of instructions, labels, comments, and blank lines.

    Returns:
        A set drawn from `{"LC", "Label", "M", "R"}`. `DT31` and `I` are always
        needed and aren't reported here.
    """
    symbols: set[str] = set()

    def visit(operand: object) -> None:
        if isinstance(operand, MemoryReference):
            symbols.add("M")
            visit(operand.address)
        elif isinstance(operand, Offset):
            visit(operand.base)
            visit(operand.offset)
        elif isinstance(operand, RegisterReference):
            symbols.add("R")
        elif isinstance(operand, Label):
            symbols.add("Label")
        elif isinstance(operand, OperandLiteral) and operand.is_char:
            symbols.add("LC")

    for item in program:
        if isinstance(item, Label):
            symbols.add("Label")
        elif isinstance(item, Instruction):
            for value in item.__dict__.values():
                if isinstance(value, (Operand, Label)):
                    visit(value)

    return symbols


def program_to_python(
    program: list[Instruction | Label | Comment | BlankLine] | list[Instruction],
    *,
    registers: list[str] | None = None,
    memory_size: int | None = None,
    stack_size: int | None = None,
    debug: bool = False,
) -> str:
    """Convert a program to a standalone Python source file using the Python API.

    Produces the same style as the hand-written examples in `examples/*.py`: a
    module-level `program = [...]` list followed by an `if __name__ ==
    "__main__":` block that runs it. Only the `dt31` symbols the program actually
    uses are imported.

    Args:
        program: List of instructions, labels, comments, and blank lines in source
            order (e.g. from `parser.parse_program`).
        registers: Explicit register list for the generated `DT31(...)` call. If
            `None` (the default), registers are auto-detected from `program` via
            `assembler.extract_registers_from_program`. Each name is validated
            with `operands.validate_register_name` (raising `ValueError` if
            invalid), but the list is otherwise trusted as-is -- the caller is
            assumed to have already checked it covers every register the
            program uses, the same way `cli.run_command` does for `run
            --registers`.
        memory_size: Passed through as `DT31(memory_size=...)` if given; omitted
            (so `DT31`'s own default applies) otherwise.
        stack_size: Same, for `stack_size`.
        debug: Whether the generated `cpu.run(program, debug=...)` call passes
            `debug=True`.

    Returns:
        Complete Python source, ready to write to a `.py` file.

    Example:
        ```python
        from dt31.formatter import program_to_python
        from dt31.parser import parse_program

        program = parse_program("CP 5, R.a\\nNOUT R.a, 1")
        print(program_to_python(program))
        #     from dt31 import DT31, I, R
        #
        #     program = [
        #         I.CP(a=5, b=R.a),
        #         I.NOUT(a=R.a, b=1),
        #     ]
        #
        #     if __name__ == "__main__":
        #         cpu = DT31(registers=["a"])
        #         cpu.run(program, debug=False)
        ```
    """
    introduced: set[str] = set()
    body_lines = []

    for item in program:
        if isinstance(item, BlankLine):
            body_lines.append("")
        elif isinstance(item, Comment):
            body_lines.append(f"    # {item.comment}")
        elif isinstance(item, Label):
            body_lines.append(
                f"    {_label_ref(item, introduced, _comment_suffix(item))},"
            )
        else:
            line = repr(item)
            if isinstance(item, Jump) and isinstance(item.dest, Label):
                # `Jump.__repr__` renders a label destination as a bare name;
                # swap in the walrus-or-literal form. Relative jumps take the
                # destination as `delta` rather than `dest`.
                dest_kwarg = "delta" if isinstance(item, RelativeJumpMixin) else "dest"
                line = line.replace(
                    f"{dest_kwarg}={item.dest.name}",
                    f"{dest_kwarg}={_label_ref(item.dest, introduced, parenthesize=True)}",
                    1,
                )
            body_lines.append(f"    I.{line}{_comment_suffix(item)},")

    body = "\n".join(body_lines)

    needed = _collect_symbols(program)

    # Ordered to match ruff's import sort: all-caps names first (DT31, LC),
    # then the rest alphabetically (I, Label, M, R).
    symbols = ["DT31"]
    if "LC" in needed:
        symbols.append("LC")
    symbols.append("I")
    symbols.extend(name for name in ("Label", "M", "R") if name in needed)

    if registers is not None:
        for register in registers:
            validate_register_name(register)
        registers_to_use = registers
    else:
        registers_to_use = extract_registers_from_program(program)

    # Mirrors cli.run_command's own cpu_kwargs construction: only non-default
    # arguments are passed, so the common case still reads as a plain
    # `DT31(registers=[...])` (or, for a register-less program, `DT31()`).
    cpu_kwargs = []
    if registers_to_use:
        # A list's own `!r` defers to each element's `!r`, which single-quotes
        # strings; build it manually with plain double quotes instead, matching
        # ruff's convention. Safe because every name in `registers_to_use` has
        # just been validated as a plain identifier, so it can't contain a
        # quote or backslash.
        register_list = ", ".join(f'"{r}"' for r in registers_to_use)
        cpu_kwargs.append(f"registers=[{register_list}]")
    if memory_size is not None:
        cpu_kwargs.append(f"memory_size={memory_size!r}")
    if stack_size is not None:
        cpu_kwargs.append(f"stack_size={stack_size!r}")

    lines = [
        f"from dt31 import {', '.join(symbols)}",
        "",
        "program = [",
        body,
        "]",
        "",
        'if __name__ == "__main__":',
        f"    cpu = DT31({', '.join(cpu_kwargs)})",
        f"    cpu.run(program, debug={debug!r})",
        "",
    ]
    return "\n".join(lines)
