from copy import deepcopy

from dt31.exceptions import AssemblyError
from dt31.instructions import Instruction, RelativeJumpMixin
from dt31.operands import Label, Literal, MemoryReference, Operand, RegisterReference
from dt31.parser import Comment


def assemble(
    program: list[Instruction | Label | Comment] | list[Instruction],
) -> list[Instruction]:
    """Assemble a program by resolving labels to instruction positions.

    This function performs a two-pass assembly process:

    **Pass 1 - Symbol Table Construction:**
    - Scans through the program to find all Label definitions
    - Records each label's name and its corresponding instruction pointer (IP)
    - Removes labels from the instruction list (they're assembly-time only)
    - Validates that labels are not defined multiple times

    **Pass 2 - Label Resolution:**
    - For each jump/call instruction that references a label:
      - Replaces the label with the actual instruction position
      - For absolute jumps/calls (JMP, CALL, etc.): uses direct IP
      - For relative jumps/calls (RJMP, RCALL, etc.): calculates offset from current position
    - Validates that all referenced labels are defined

    Args:
        program: List of instructions and labels in source order.

    Returns:
        A new list of instructions with all labels removed and all label references
        resolved to numeric instruction positions (Literal operands).

    Raises:
        AssemblyError: If a label is defined multiple times or if an undefined label
            is referenced.

    Note:
        This function is run automatically when `DT31.run` is called, so it typically doesn't
        need to be invoked manually.

    Examples:
        Simple loop with label:
        ```python
        from dt31 import I, R, L, Label

        program = [
            I.CP(R.a, L[0]),
            Label("loop"),
            I.ADD(R.a, L[1]),
            I.JGT(Label("loop"), R.a, L[10]),
        ]

        assembled = assemble(program)
        # Label removed, JGT now jumps to IP 1
        ```

        Relative vs absolute jumps:
        ```python
        program = [
            Label("start"),           # IP 0
            I.NOOP(),                 # IP 0
            I.JMP(Label("start")),    # IP 1 - becomes JMP(Literal(0))
            I.RJMP(Label("start")),   # IP 2 - becomes RJMP(Literal(-2))
        ]
        ```
    """
    new_program = []
    used_labels = set()
    label_to_ip = {}

    # First pass populates label_to_ip
    ip = 0
    for inst in program:
        if isinstance(inst, Label):
            if inst.name in used_labels:
                raise AssemblyError(f"Label {inst.name} used more than once.")
            used_labels.add(inst.name)
            label_to_ip[inst.name] = ip
        elif isinstance(inst, Comment):
            continue
        else:
            new_program.append(deepcopy(inst))
            ip += 1

    # Second pass to replace label references
    for ip, inst in enumerate(new_program):
        if hasattr(inst, "dest") and isinstance(inst.dest, Label):
            try:
                target_ip = label_to_ip[inst.dest.name]
            except KeyError:
                raise AssemblyError(f"Undefined label: {inst.dest.name}")

            if isinstance(inst, RelativeJumpMixin):
                delta = target_ip - ip
                inst.dest = Literal(delta)
            else:
                inst.dest = Literal(target_ip)

    return new_program


def program_to_text(
    program: list[Instruction | Label | Comment] | list[Instruction],
    *,
    indent_size: int = 4,
    comment_spacing: int = 1,
    label_inline: bool = False,
    blank_line_before_label: bool = True,
    align_comments: bool = False,
    comment_column: int = 40,
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
        hide_default_out: If True, hide output parameters when they match the default value (default: False).

    Returns:
        A string containing the assembly text representation of the program,
        with one instruction, label, or comment per line.

    Examples:
        Default formatting:
        ```python
        from dt31 import I, R, L, Label

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
                    item, align_comments, comment_column, comment_spacing
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
                comment = (
                    item.comment
                    if item.comment
                    else (
                        pending_labels[-1].comment if pending_labels[-1].comment else ""
                    )
                )
                pending_labels = []
            else:
                label_prefix = indent
                comment = item.comment

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
        line = _format_label(lbl, align_comments, comment_column, comment_spacing)
        lines.append(line)

    return "\n".join(lines)


def _format_label(
    label: Label,
    align_comments: bool,
    comment_column: int,
    comment_spacing: int,
) -> str:
    """Format a label with optional comment alignment."""
    line = f"{label.name}:"
    if label.comment:
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


def extract_registers_from_program(
    program: list[Instruction | Label | Comment],
) -> list[str]:
    """
    Extract all register names used in a program.

    This function works on already-parsed programs, whether they were parsed from
    text or constructed programmatically in Python. Useful for determining which
    registers need to be initialized in the CPU.

    Args:
        program: List of Instructions and Labels

    Returns:
        Sorted list of register names used in the program (excluding 'ip')

    Example:
        >>> from dt31 import I, R, L
        >>> program = [
        ...     I.CP(10, R.x),
        ...     I.ADD(R.x, L[5]),
        ...     I.NOUT(R.x, L[1]),
        ... ]
        >>> extract_registers_from_program(program)
        ['x']
    """
    registers_used: set[str] = set()

    def extract_from_operand(operand: Operand) -> None:
        """Recursively extract registers from an operand."""
        if isinstance(operand, RegisterReference):
            if operand.register != "ip":
                registers_used.add(operand.register)
        elif isinstance(operand, MemoryReference):
            # Memory references can contain nested operands (e.g., M[R.a])
            extract_from_operand(operand.address)

    for item in program:
        if isinstance(item, (Label, Comment)):
            continue

        # Instructions store operands as attributes
        # Walk through all attributes to find operands
        for attr_value in item.__dict__.values():
            if isinstance(attr_value, (RegisterReference, MemoryReference)):
                extract_from_operand(attr_value)

    return sorted(registers_used)
