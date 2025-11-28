"""Program formatting utilities for converting programs to assembly text.

This module provides functionality for converting dt31 programs (lists of
instructions, labels, and comments) into human-readable assembly text format
with configurable formatting options.
"""

from dt31.instructions import Instruction
from dt31.operands import Label
from dt31.parser import Comment


def program_to_text(
    program: list[Instruction | Label | Comment] | list[Instruction],
    *,
    indent_size: int = 4,
    comment_spacing: int = 1,
    label_inline: bool = False,
    blank_line_before_label: bool = True,
    align_comments: bool = False,
    comment_column: int = 40,
    strip_comments: bool = False,
    hide_default_out: bool = False,
) -> str:
    """Convert a program to assembly text format with configurable formatting.

    Converts a list of instructions, labels, and comments (whether created programmatically
    in Python or parsed from text) into human-readable assembly text syntax.

    Args:
        program: List of instructions, labels, and comments in source order.
        indent_size: Number of spaces per indentation level (default: 4).
        comment_spacing: Number of spaces before inline comment semicolon (default: 1).
        label_inline: If True, place labels on same line as next instruction (default: False).
        blank_line_before_label: If True, add blank line before labels (default: True).
        align_comments: If True, align inline comments at comment_column (default: False).
        comment_column: Column position for aligned comments when align_comments=True (default: 40).
        strip_comments: If True, remove all comments from output. (default: False).
        hide_default_out: If True, hide output parameters when they match the default value (default: False).

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

        Custom formatting with 2-space indent and inline labels:
        ```python
        text = program_to_text(
            program,
            indent_size=2,
            label_inline=True,
            blank_line_before_label=False,
        )
        #   CP 5, R.a
        # loop: NOUT R.a, 1
        #   SUB R.a, 1, R.a
        #   JGT loop, R.a, 0
        ```

        Aligned comments:
        ```python
        program_with_comments = [
            I.CP(5, R.a).with_comment("Initialize"),
            I.ADD(R.a, L[1]).with_comment("Increment"),
        ]
        text = program_to_text(program_with_comments, align_comments=True, comment_column=30)
        #     CP 5, R.a              ; Initialize
        #     ADD R.a, 1, R.a        ; Increment
        ```

        Hide default output parameters:
        ```python
        program = [
            I.ADD(R.a, R.b),  # Default out=R.a
            I.NOUT(R.a),      # Default b=L[0] (no newline)
        ]
        text = program_to_text(program, hide_default_out=True)
        #     ADD R.a, R.b
        #     NOUT R.a
        # vs without hide_default_out:
        #     ADD R.a, R.b, R.a
        #     NOUT R.a, 0
        ```
    """
    indent = " " * indent_size
    lines = []
    pending_labels: list[Label] = []
    prev_was_label = False

    for i, item in enumerate(program):
        if isinstance(item, Comment):
            # Standalone comments are never indented or aligned
            if not strip_comments:
                lines.append(str(item))
            prev_was_label = False
        elif isinstance(item, Label):
            # Add blank line before label if requested (but not before first item or consecutive labels)
            if blank_line_before_label and lines and not prev_was_label:
                lines.append("")

            if label_inline:
                # Collect labels to put inline with next instruction
                pending_labels.append(item)
            else:
                # Labels on separate lines
                line = _format_label(
                    item,
                    align_comments,
                    comment_column,
                    comment_spacing,
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

            instruction_text = item.to_concise_str() if hide_default_out else str(item)
            line = _format_instruction_with_comment(
                label_prefix + instruction_text,
                comment,
                align_comments,
                comment_column,
                comment_spacing,
            )
            lines.append(line)

    # Handle any remaining labels at end of program
    for lbl in pending_labels:
        line = _format_label(
            lbl, align_comments, comment_column, comment_spacing, strip_comments
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
    comment_column: int,
    comment_spacing: int,
    strip_comments: bool = False,
) -> str:
    """Format a label with optional comment alignment."""
    line = f"{label.name}:"
    if label.comment and not strip_comments:
        line = _format_instruction_with_comment(
            line, label.comment, align_comments, comment_column, comment_spacing
        )
    return line


def _format_instruction_with_comment(
    instruction_text: str,
    comment: str,
    align_comments: bool,
    comment_column: int,
    comment_spacing: int,
) -> str:
    """Format an instruction with its comment, handling alignment if requested."""
    if not comment:
        return instruction_text

    if align_comments:
        current_len = len(instruction_text)
        if current_len < comment_column:
            padding = comment_column - current_len
            return f"{instruction_text}{' ' * padding}; {comment}"
        else:
            # Instruction exceeds column, fall back to spacing
            return f"{instruction_text}{' ' * comment_spacing}; {comment}"
    else:
        # No alignment, just use spacing
        return f"{instruction_text}{' ' * comment_spacing}; {comment}"
