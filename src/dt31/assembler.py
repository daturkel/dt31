from copy import deepcopy

from dt31.exceptions import AssemblyError
from dt31.instructions import Instruction, RelativeJumpMixin
from dt31.operands import Label, Literal, MemoryReference, Operand, RegisterReference


def assemble(
    program: list[Instruction | Label] | list[Instruction],
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


def program_to_text(program: list[Instruction | Label] | list[Instruction]) -> str:
    """Convert a program to assembly text format.

    Converts a list of instructions and labels (whether created programmatically
    in Python or parsed from text) into human-readable assembly text syntax.

    Args:
        program: List of instructions and labels in source order.

    Returns:
        A string containing the assembly text representation of the program,
        with one instruction or label per line.

    Examples:
        Convert Python program to assembly text:
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
        # CP 5, R.a
        # loop:
        #     NOUT R.a, 1
        #     SUB R.a, 1
        #     JGT loop, R.a, 0
        ```

        Round-trip conversion (text → Python → text):
        ```python
        from dt31.parser import parse_program

        original = '''
        CP 5, R.a
        loop:
            NOUT R.a, 1
            SUB R.a, 1
            JGT loop, R.a, 0
        '''

        program = parse_program(original)
        reconstructed = program_to_text(program)
        # reconstructed matches original (modulo whitespace)
        ```
    """
    lines = []
    for item in program:
        if isinstance(item, Label):
            lines.append(f"{item.name}:")
        else:
            lines.append(f"    {str(item)}")
    return "\n".join(lines)


def extract_registers_from_program(program: list[Instruction | Label]) -> list[str]:
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
        if isinstance(item, Label):
            continue

        # Instructions store operands as attributes
        # Walk through all attributes to find operands
        for attr_value in item.__dict__.values():
            if isinstance(attr_value, (RegisterReference, MemoryReference)):
                extract_from_operand(attr_value)

    return sorted(registers_used)
