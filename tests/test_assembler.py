import pytest

from dt31 import instructions as I
from dt31.assembler import (
    AssemblyError,
    assemble,
    extract_registers_from_program,
    program_to_text,
)
from dt31.operands import L, LC, Label, Literal, M, R

# ============================================================================
# Basic Assembly
# ============================================================================


def test_assemble_empty_program():
    """Empty programs should return empty list."""
    result = assemble([])
    assert result == []


def test_assemble_program_without_labels():
    """Programs without labels should be returned unchanged."""
    program = [
        I.CP(L[0], R.a),
        I.ADD(L[1], L[2], R.b),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 3
    assert str(result[0]) == str(program[0])
    assert str(result[1]) == str(program[1])
    assert str(result[2]) == str(program[2])


# ============================================================================
# Label Definition
# ============================================================================


def test_single_label_at_start():
    """Label at the start should map to IP 0."""
    program = [
        Label("start"),
        I.NOOP(),
        I.JMP(Label("start")),
    ]
    result = assemble(program)
    assert len(result) == 2
    # Label should be removed
    assert not any(isinstance(inst, Label) for inst in result)
    # JMP should point to IP 0
    assert isinstance(result[1].dest, Literal)
    assert result[1].dest.value == 0


def test_single_label_in_middle():
    """Label in the middle should map to correct IP."""
    program = [
        I.NOOP(),
        I.NOOP(),
        Label("middle"),
        I.NOOP(),
        I.JMP(Label("middle")),
    ]
    result = assemble(program)
    assert len(result) == 4
    # JMP should point to IP 2 (after two NOOPs)
    assert isinstance(result[3].dest, Literal)
    assert result[3].dest.value == 2


def test_multiple_labels():
    """Multiple labels should each map to correct positions."""
    program = [
        Label("first"),
        I.NOOP(),
        Label("second"),
        I.NOOP(),
        Label("third"),
        I.JMP(Label("first")),
        I.JMP(Label("second")),
        I.JMP(Label("third")),
    ]
    result = assemble(program)
    assert len(result) == 5
    # First JMP should point to IP 0
    assert result[2].dest.value == 0
    # Second JMP should point to IP 1
    assert result[3].dest.value == 1
    # Third JMP should point to IP 2
    assert result[4].dest.value == 2


def test_consecutive_labels():
    """Consecutive labels should point to same IP."""
    program = [
        I.NOOP(),
        Label("first"),
        Label("second"),
        Label("third"),
        I.NOOP(),
        I.JMP(Label("first")),
        I.JMP(Label("second")),
        I.JMP(Label("third")),
    ]
    result = assemble(program)
    assert len(result) == 5
    # All three jumps should point to IP 1
    assert result[2].dest.value == 1
    assert result[3].dest.value == 1
    assert result[4].dest.value == 1


# ============================================================================
# Absolute Jumps
# ============================================================================


def test_jmp_with_label():
    """JMP should resolve to absolute position."""
    program = [
        I.CP(L[0], R.a),
        Label("loop"),
        I.ADD(R.a, L[1]),
        I.JMP(Label("loop")),
    ]
    result = assemble(program)
    assert len(result) == 3
    assert isinstance(result[2].dest, Literal)
    assert result[2].dest.value == 1


def test_call_with_label():
    """CALL should resolve to absolute position."""
    program = [
        I.NOOP(),
        Label("function"),
        I.ADD(L[1], L[2], R.a),
        I.RET(),
        I.CALL(Label("function")),
    ]
    result = assemble(program)
    assert len(result) == 4
    assert isinstance(result[3].dest, Literal)
    assert result[3].dest.value == 1


def test_conditional_jumps_with_labels():
    """Conditional jumps should resolve to absolute positions."""
    program = [
        Label("start"),
        I.CP(L[0], R.a),
        Label("loop"),
        I.ADD(R.a, L[1]),
        I.JNE(Label("loop"), R.a, L[10]),
        I.JGT(Label("start"), R.a, L[5]),
    ]
    result = assemble(program)
    assert len(result) == 4
    # JNE should point to "loop" at IP 1
    assert result[2].dest.value == 1
    # JGT should point to "start" at IP 0
    assert result[3].dest.value == 0


def test_forward_and_backward_jumps():
    """Both forward and backward jumps should work."""
    program = [
        I.JMP(Label("forward")),
        Label("backward"),
        I.NOOP(),
        I.JMP(Label("end")),
        Label("forward"),
        I.NOOP(),
        I.JMP(Label("backward")),
        Label("end"),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 6
    # First JMP forward to IP 3 (after backward NOOP and JMP)
    assert result[0].dest.value == 3
    # JMP at IP 2 forward to IP 5
    assert result[2].dest.value == 5
    # JMP at IP 4 backward to IP 1
    assert result[4].dest.value == 1


# ============================================================================
# Relative Jumps
# ============================================================================


def test_rjmp_forward():
    """RJMP should calculate forward offset correctly."""
    program = [
        Label("start"),
        I.NOOP(),
        I.RJMP(Label("target")),  # At IP 1, jumping to IP 3
        I.NOOP(),
        Label("target"),
        I.NOOP(),
    ]
    result = assemble(program)
    # RJMP at IP 1 to target at IP 3: offset = 3 - 1 = 2
    assert result[1].dest.value == 2


def test_rjmp_backward():
    """RJMP should calculate backward offset correctly."""
    program = [
        Label("start"),
        I.NOOP(),
        I.NOOP(),
        I.RJMP(Label("start")),  # At IP 2, jumping to IP 0
    ]
    result = assemble(program)
    # RJMP at IP 2 to start at IP 0: offset = 0 - 2 = -2
    assert result[2].dest.value == -2


def test_rjmp_to_same_position():
    """RJMP to its own position should have offset 0."""
    program = [
        I.NOOP(),
        Label("loop"),
        I.RJMP(Label("loop")),  # At IP 1, jumping to IP 1
    ]
    result = assemble(program)
    # RJMP at IP 1 to loop at IP 1: offset = 1 - 1 = 0
    assert result[1].dest.value == 0


def test_rcall_with_label():
    """RCALL should calculate relative offset."""
    program = [
        I.NOOP(),
        I.RCALL(Label("func")),  # At IP 1, calling IP 3
        I.NOOP(),
        Label("func"),
        I.RET(),
    ]
    result = assemble(program)
    # RCALL at IP 1 to func at IP 3: offset = 3 - 1 = 2
    assert result[1].dest.value == 2


def test_relative_conditional_jumps():
    """Relative conditional jumps should calculate offsets."""
    program = [
        Label("start"),
        I.NOOP(),
        I.RJEQ(Label("target"), L[1], L[1]),  # At IP 1, to IP 4
        I.NOOP(),
        Label("target"),
        I.RJGT(Label("start"), L[2], L[1]),  # At IP 3, to IP 0
    ]
    result = assemble(program)
    # RJEQ at IP 1 to target at IP 3: offset = 3 - 1 = 2
    assert result[1].dest.value == 2
    # RJGT at IP 3 to start at IP 0: offset = 0 - 3 = -3
    assert result[3].dest.value == -3


def test_mixed_absolute_and_relative_jumps():
    """Absolute and relative jumps can coexist."""
    program = [
        Label("start"),
        I.NOOP(),
        I.JMP(Label("abs_target")),  # Absolute to IP 4
        I.RJMP(Label("rel_target")),  # At IP 2, relative to IP 5
        Label("abs_target"),
        I.NOOP(),
        Label("rel_target"),
        I.NOOP(),
    ]
    result = assemble(program)
    # JMP should use absolute position
    assert result[1].dest.value == 3
    # RJMP should use relative offset: 4 - 2 = 2
    assert result[2].dest.value == 2


# ============================================================================
# Assembly Errors
# ============================================================================


def test_duplicate_label_error():
    """Defining same label twice should raise AssemblyError."""
    program = [
        Label("duplicate"),
        I.NOOP(),
        Label("duplicate"),
        I.NOOP(),
    ]
    with pytest.raises(AssemblyError) as exc_info:
        assemble(program)
    assert "duplicate" in str(exc_info.value).lower()
    assert "more than once" in str(exc_info.value).lower()


def test_undefined_label_error():
    """Referencing undefined label should raise AssemblyError."""
    program = [
        I.NOOP(),
        I.JMP(Label("nonexistent")),
    ]
    with pytest.raises(AssemblyError) as exc_info:
        assemble(program)
    assert "undefined" in str(exc_info.value).lower()
    assert "nonexistent" in str(exc_info.value)


def test_undefined_label_in_relative_jump():
    """Undefined label in relative jump should raise AssemblyError."""
    program = [
        I.NOOP(),
        I.RJMP(Label("missing")),
    ]
    with pytest.raises(AssemblyError) as exc_info:
        assemble(program)
    assert "undefined" in str(exc_info.value).lower()
    assert "missing" in str(exc_info.value)


def test_multiple_undefined_labels():
    """Should report first undefined label encountered."""
    program = [
        I.JMP(Label("first_missing")),
        I.JMP(Label("second_missing")),
    ]
    with pytest.raises(AssemblyError) as exc_info:
        assemble(program)
    assert "undefined" in str(exc_info.value).lower()
    # Should encounter first_missing first
    assert "first_missing" in str(exc_info.value)


# ============================================================================
# Complex Programs
# ============================================================================


def test_loop_program():
    """Assemble a simple loop program."""
    program = [
        I.CP(L[0], R.a),
        Label("loop"),
        I.ADD(R.a, L[1]),
        I.JNE(Label("loop"), R.a, L[10]),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 4
    # JNE should jump back to IP 1 when a != 10
    assert result[2].dest.value == 1


def test_function_with_call_and_return():
    """Assemble a program with function call."""
    program = [
        I.CALL(Label("add_one")),
        I.NOOP(),
        I.JMP(Label("end")),
        Label("add_one"),
        I.ADD(R.a, L[1]),
        I.RET(),
        Label("end"),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 6
    # CALL should point to add_one at IP 3
    assert result[0].dest.value == 3
    # JMP should point to end at IP 5
    assert result[2].dest.value == 5


def test_nested_loops():
    """Assemble nested loop structure."""
    program = [
        I.CP(L[0], R.a),
        Label("outer"),
        I.CP(L[0], R.b),
        Label("inner"),
        I.ADD(R.b, L[1]),
        I.JNE(Label("inner"), R.b, L[5]),
        I.ADD(R.a, L[1]),
        I.JNE(Label("outer"), R.a, L[3]),
    ]
    result = assemble(program)
    assert len(result) == 6
    # Inner loop jump at IP 3 to IP 2
    assert result[3].dest.value == 2
    # Outer loop jump at IP 5 to IP 1
    assert result[5].dest.value == 1


def test_branching_with_multiple_targets():
    """Assemble program with conditional branches."""
    program = [
        I.CP(L[5], R.a),
        I.JEQ(Label("equal"), R.a, L[5]),
        I.JGT(Label("greater"), R.a, L[5]),
        # If we get here, a < 5
        Label("less"),
        I.CP(L[1], R.b),
        I.JMP(Label("end")),
        Label("greater"),
        I.CP(L[2], R.b),
        I.JMP(Label("end")),
        Label("equal"),
        I.CP(L[0], R.b),
        Label("end"),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 9
    # JEQ to "equal" at IP 7
    assert result[1].dest.value == 7
    # JGT to "greater" at IP 5
    assert result[2].dest.value == 5
    # "JMP end" from less at IP 4 should point to IP 8
    assert result[4].dest.value == 8
    # "JMP end" from greater at IP 6 should point to IP 8
    assert result[6].dest.value == 8


# ============================================================================
# Deep Copy
# ============================================================================


def test_original_program_unchanged():
    """Original program should not be modified."""
    program = [
        Label("start"),
        I.NOOP(),
        I.JMP(Label("start")),
    ]
    # Keep reference to original jump instruction
    original_jump = program[2]
    original_dest = original_jump.dest

    result = assemble(program)

    # Original should still have Label, not Literal
    assert isinstance(original_dest, Label)
    assert original_dest.name == "start"
    # Result should have Literal
    assert isinstance(result[1].dest, Literal)


def test_modifying_result_does_not_affect_original():
    """Modifying assembled program should not affect original."""
    program = [
        I.CP(L[0], R.a),
        I.ADD(R.a, L[1]),
    ]
    result = assemble(program)

    # Modify result
    result[0] = I.NOOP()

    # Original should be unchanged
    assert repr(program[0]) == "CP(a=0, b=R.a)"


# ============================================================================
# Edge Cases
# ============================================================================


def test_label_at_end_of_program():
    """Label at the very end should work."""
    program = [
        I.NOOP(),
        I.NOOP(),
        Label("end"),
    ]
    result = assemble(program)
    assert len(result) == 2


def test_only_labels():
    """Program with only labels should return empty."""
    program = [
        Label("first"),
        Label("second"),
        Label("third"),
    ]
    result = assemble(program)
    assert len(result) == 0


def test_jump_to_last_instruction():
    """Jump to label at last position should work."""
    program = [
        I.JMP(Label("end")),
        Label("end"),
        I.NOOP(),
    ]
    result = assemble(program)
    assert len(result) == 2
    assert result[0].dest.value == 1


def test_many_consecutive_jumps_to_same_label():
    """Multiple jumps to same label should all resolve correctly."""
    program = [
        Label("target"),
        I.NOOP(),
        I.JMP(Label("target")),
        I.JMP(Label("target")),
        I.JMP(Label("target")),
        I.RJMP(Label("target")),
    ]
    result = assemble(program)
    # All absolute jumps to IP 0
    assert result[1].dest.value == 0
    assert result[2].dest.value == 0
    assert result[3].dest.value == 0
    # Relative jump at IP 4 to IP 0: offset = -4
    assert result[4].dest.value == -4


# ============================================================================
# Register Extraction
# ============================================================================


def test_extract_registers_single():
    """Test extracting a single register from a program."""
    program = [
        I.CP(L[10], R.x),
        I.NOUT(R.x, L[1]),
    ]
    registers = extract_registers_from_program(program)
    assert registers == ["x"]


def test_extract_registers_multiple():
    """Test extracting multiple registers from a program."""
    program = [
        I.CP(L[10], R.x),
        I.CP(L[20], R.y),
        I.ADD(R.x, R.y),
        I.NOUT(R.x, L[1]),
    ]
    registers = extract_registers_from_program(program)
    assert registers == ["x", "y"]


def test_extract_registers_with_memory():
    """Test extracting registers from memory references like M[R.a]."""
    program = [
        I.CP(L[100], R.addr),
        I.CP(L[42], M[R.addr]),
        I.CP(M[R.addr], R.value),
    ]
    registers = extract_registers_from_program(program)
    assert registers == ["addr", "value"]


def test_extract_registers_filters_ip():
    """Test that 'ip' register is filtered out."""
    program = [
        I.CP(L[10], R.x),
        I.CP(R.ip, R.y),  # Using ip register
    ]
    registers = extract_registers_from_program(program)
    # 'ip' should be filtered out
    assert registers == ["x", "y"]


def test_extract_registers_no_registers():
    """Test program with no registers."""
    program = [
        I.CP(L[10], M[50]),
        I.NOUT(M[50], L[1]),
    ]
    registers = extract_registers_from_program(program)
    assert registers == []


def test_extract_registers_ignores_labels():
    """Test that labels don't affect register extraction."""
    program = [
        Label("start"),
        I.CP(L[10], R.x),
        Label("loop"),
        I.NOUT(R.x, L[1]),
        I.JMP(Label("start")),
    ]
    registers = extract_registers_from_program(program)
    assert registers == ["x"]


def test_extract_registers_sorted():
    """Test that extracted registers are sorted."""
    program = [
        I.CP(L[1], R.z),
        I.CP(L[2], R.a),
        I.CP(L[3], R.m),
    ]
    registers = extract_registers_from_program(program)
    assert registers == ["a", "m", "z"]


# ============================================================================
# Program to Text Conversion
# ============================================================================


def test_program_to_text_simple():
    """Test converting a simple program to text."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
        I.NOUT(R.a, L[1]),
    ]
    text = program_to_text(program)
    expected = "    CP 5, R.a\n    ADD R.a, 1, R.a\n    NOUT R.a, 1"
    assert text == expected


def test_program_to_text_with_labels():
    """Test converting program with labels to text."""
    program = [
        I.CP(5, R.a),
        loop := Label("loop"),
        I.NOUT(R.a, L[1]),
        I.SUB(R.a, L[1]),
        I.JGT(loop, R.a, L[0]),
    ]
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1, R.a"
    assert lines[4] == "    JGT loop, R.a, 0"


def test_program_to_text_character_literals():
    """Test that character literals render correctly."""
    program = [
        I.OOUT(LC["H"]),
        I.OOUT(LC["i"], L[1]),
    ]
    text = program_to_text(program)
    lines = text.split("\n")
    assert lines[0] == "    OOUT 'H', 0"
    assert lines[1] == "    OOUT 'i', 1"


def test_program_to_text_memory_references():
    """Test that memory references render correctly."""
    program = [
        I.CP(100, M[50]),
        I.CP(M[50], R.a),
        I.CP(M[R.a], R.b),
    ]
    text = program_to_text(program)
    lines = text.split("\n")
    assert lines[0] == "    CP 100, [50]"
    assert lines[1] == "    CP [50], R.a"
    assert lines[2] == "    CP [R.a], R.b"


def test_program_to_text_empty():
    """Test converting empty program."""
    program = []
    text = program_to_text(program)
    assert text == ""


def test_program_to_text_only_labels():
    """Test converting program with only labels."""
    program = [
        Label("start"),
        Label("end"),
    ]
    text = program_to_text(program, blank_line_before_label=False)
    assert text == "start:\nend:"


def test_program_to_text_complex():
    """Test converting a complex program with loops and function calls."""
    program = [
        I.CALL(func := Label("print_hi")),
        I.JMP(end := Label("end")),
        func,
        I.OOUT(LC["H"]),
        I.OOUT(LC["i"], L[1]),
        I.RET(),
        end,
    ]
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    CALL print_hi"
    assert lines[1] == "    JMP end"
    assert lines[2] == "print_hi:"
    assert lines[3] == "    OOUT 'H', 0"
    assert lines[4] == "    OOUT 'i', 1"
    assert lines[5] == "    RET"
    assert lines[6] == "end:"


# ============================================================================
# Formatting Options
# ============================================================================


def test_program_to_text_custom_indent_size():
    """Test custom indentation size."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
    ]
    # 2-space indent
    text = program_to_text(program, indent_size=2)
    assert text == "  CP 5, R.a\n  ADD R.a, 1, R.a"

    # 8-space indent
    text = program_to_text(program, indent_size=8)
    assert text == "        CP 5, R.a\n        ADD R.a, 1, R.a"


def test_program_to_text_comment_spacing():
    """Test custom spacing before inline comments."""
    program = [
        I.CP(5, R.a).with_comment("Initialize"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
    ]

    # No spacing (default is 1)
    text = program_to_text(program, comment_spacing=0)
    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "    CP 5, R.a; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a; Increment"

    # Default spacing (1)
    text = program_to_text(program, comment_spacing=1)
    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "    CP 5, R.a ; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a ; Increment"

    # Extra spacing (2)
    text = program_to_text(program, comment_spacing=2)
    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "    CP 5, R.a  ; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a  ; Increment"


def test_program_to_text_label_inline():
    """Test inline label style (label on same line as next instruction)."""
    program = [
        I.CP(5, R.a),
        loop := Label("loop"),
        I.NOUT(R.a, L[1]),
        I.SUB(R.a, L[1]),
        I.JGT(loop, R.a, L[0]),
    ]

    # Separate line style without blank lines
    text = program_to_text(program, label_inline=False, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 5
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1, R.a"
    assert lines[4] == "    JGT loop, R.a, 0"

    # Inline: labels on same line as next instruction
    text = program_to_text(program, label_inline=True, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 4
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop: NOUT R.a, 1"
    assert lines[2] == "    SUB R.a, 1, R.a"
    assert lines[3] == "    JGT loop, R.a, 0"


def test_program_to_text_label_inline_at_end():
    """Test inline label style when label is at end of program."""
    program = [
        I.CP(5, R.a),
        Label("end"),
    ]

    # Label at end should still appear even when inline style is enabled
    text = program_to_text(program, label_inline=True, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "end:"


def test_program_to_text_label_inline_consecutive_labels():
    """Test inline label style with consecutive labels."""
    program = [
        I.CP(5, R.a),
        Label("label1"),
        Label("label2"),
        Label("label3"),
        I.NOUT(R.a, L[1]),
    ]

    # All labels should appear inline before the instruction
    text = program_to_text(program, label_inline=True, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "label1: label2: label3: NOUT R.a, 1"


def test_program_to_text_blank_line_before_label():
    """Test adding blank line before labels."""
    program = [
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
        Label("end"),
        I.NOOP(),
    ]

    # Default: no blank lines
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 5
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "end:"
    assert lines[4] == "    NOOP"

    # With blank lines before labels
    text = program_to_text(program, blank_line_before_label=True)
    lines = text.split("\n")
    assert len(lines) == 7
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before loop
    assert lines[2] == "loop:"
    assert lines[3] == "    NOUT R.a, 1"
    assert lines[4] == ""  # blank line before end
    assert lines[5] == "end:"
    assert lines[6] == "    NOOP"


def test_program_to_text_blank_line_before_label_inline():
    """Test that blank_line_before_label works with label_inline=True."""
    program = [
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
        I.SUB(R.a, L[1]),
    ]

    # Inline labels WITH blank line before them
    text = program_to_text(program, label_inline=True, blank_line_before_label=True)
    lines = text.split("\n")
    assert len(lines) == 4
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before loop
    assert lines[2] == "loop: NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1, R.a"


def test_program_to_text_blank_line_before_first_label():
    """Test that blank line is NOT added before first label at program start."""
    program = [
        Label("start"),
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
    ]

    text = program_to_text(program, blank_line_before_label=True)
    lines = text.split("\n")
    assert len(lines) == 5
    assert lines[0] == "start:"  # No blank line before first label
    assert lines[1] == "    CP 5, R.a"
    assert lines[2] == ""  # blank line before loop
    assert lines[3] == "loop:"
    assert lines[4] == "    NOUT R.a, 1"


def test_program_to_text_blank_line_consecutive_labels():
    """Test that consecutive labels only get one blank line before them."""
    program = [
        I.CP(5, R.a),
        Label("label1"),
        Label("label2"),
        I.NOUT(R.a, L[1]),
    ]

    text = program_to_text(program, blank_line_before_label=True)
    lines = text.split("\n")
    assert len(lines) == 5
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before first label
    assert lines[2] == "label1:"
    assert lines[3] == "label2:"  # No blank line before consecutive label
    assert lines[4] == "    NOUT R.a, 1"


def test_program_to_text_align_comments():
    """Test aligning inline comments at a column."""
    program = [
        I.CP(5, R.a).with_comment("Initialize"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
        I.NOUT(R.a, L[1]).with_comment("Print"),
    ]

    # Default: no alignment
    text = program_to_text(program, align_comments=False, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a ; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a ; Increment"
    assert lines[2] == "    NOUT R.a, 1 ; Print"

    # Align at column 30
    text = program_to_text(
        program, align_comments=True, comment_column=30, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a                 ; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a           ; Increment"
    assert lines[2] == "    NOUT R.a, 1               ; Print"
    # Verify all comments start at column 30
    for line in lines:
        assert line.index(";") == 30


def test_program_to_text_align_comments_exceeds_column():
    """Test comment alignment when instruction exceeds column."""
    program = [
        I.CP(5, R.a).with_comment("Short"),
        I.ADD(R.a, R.b, M[R.a]).with_comment("Very long instruction"),
    ]

    # Align at column 20 (second instruction will exceed this)
    text = program_to_text(
        program, align_comments=True, comment_column=20, blank_line_before_label=False
    )
    lines = text.split("\n")

    # First line should align at column 20
    assert lines[0] == "    CP 5, R.a       ; Short"
    assert lines[0].index(";") == 20

    # Second line exceeds column, should fall back to comment_spacing
    assert lines[1] == "    ADD R.a, R.b, [R.a] ; Very long instruction"


def test_program_to_text_align_comments_custom_spacing_fallback():
    """Test that comment_spacing is used when instruction exceeds column."""
    program = [
        I.ADD(R.a, R.b, M[R.a]).with_comment("Long instruction"),
    ]

    # Column 10 will be exceeded, fallback to comment_spacing=3
    text = program_to_text(
        program,
        align_comments=True,
        comment_column=10,
        comment_spacing=3,
        blank_line_before_label=False,
    )
    lines = text.split("\n")

    # Should use 3 spaces before comment
    assert lines[0] == "    ADD R.a, R.b, [R.a]   ; Long instruction"


def test_program_to_text_align_comments_standalone_not_aligned():
    """Test that standalone comments are never aligned."""
    from dt31.parser import Comment

    program = [
        Comment("Standalone comment"),
        I.CP(5, R.a).with_comment("Inline comment"),
        Comment("Another standalone"),
    ]

    text = program_to_text(
        program, align_comments=True, comment_column=30, blank_line_before_label=False
    )
    lines = text.split("\n")

    # Standalone comments should not be aligned
    assert lines[0] == "; Standalone comment"
    assert lines[2] == "; Another standalone"

    # Inline comment should be aligned
    assert lines[1] == "    CP 5, R.a                 ; Inline comment"
    assert lines[1].index(";") == 30


def test_program_to_text_align_comments_labels_with_comments():
    """Test comment alignment on labels."""
    program = [
        Label("loop").with_comment("Main loop"),
        I.CP(5, R.a).with_comment("Init"),
    ]

    # Separate style
    text = program_to_text(
        program, label_inline=False, align_comments=True, comment_column=30
    )
    lines = text.split("\n")
    assert lines[0] == "loop:                         ; Main loop"
    assert lines[1] == "    CP 5, R.a                 ; Init"

    # Inline style
    text = program_to_text(
        program, label_inline=True, align_comments=True, comment_column=30
    )
    lines = text.split("\n")
    assert lines[0] == "loop: CP 5, R.a               ; Init"


def test_program_to_text_combination_all_options():
    """Test combining multiple formatting options together."""
    program = [
        I.CP(10, R.x).with_comment("Initialize"),
        loop := Label("loop").with_comment("Main loop"),
        I.NOUT(R.x, L[1]).with_comment("Print"),
        I.SUB(R.x, L[1]),
        I.JGT(loop, R.x, L[0]),
    ]

    # 2-space indent, inline labels, blank lines, aligned comments
    text = program_to_text(
        program,
        indent_size=2,
        comment_spacing=2,
        label_inline=True,
        blank_line_before_label=True,
        align_comments=True,
        comment_column=25,
    )
    lines = text.split("\n")

    assert lines[0] == "  CP 10, R.x             ; Initialize"
    assert lines[1] == ""  # blank line before label
    assert lines[2] == "loop: NOUT R.x, 1        ; Print"
    assert lines[3] == "  SUB R.x, 1, R.x"
    assert lines[4] == "  JGT loop, R.x, 0"

    # Verify alignment
    assert lines[0].index(";") == 25
    assert lines[2].index(";") == 25


# ============================================================================
# Hide Default Output Parameters
# ============================================================================


def test_program_to_text_hide_default_out_binary_operations():
    """Test hide_default_out with BinaryOperation instructions."""
    program = [
        I.ADD(R.a, R.b),  # Default out=R.a
        I.SUB(R.a, L[1]),  # Default out=R.a
        I.MUL(R.b, L[2]),  # Default out=R.b
    ]

    # Without hide_default_out (default)
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b, R.a"
    assert lines[1] == "    SUB R.a, 1, R.a"
    assert lines[2] == "    MUL R.b, 2, R.b"

    # With hide_default_out
    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b"
    assert lines[1] == "    SUB R.a, 1"
    assert lines[2] == "    MUL R.b, 2"


def test_program_to_text_hide_default_out_non_default_output():
    """Test that non-default output parameters are still shown."""
    program = [
        I.ADD(R.a, R.b, R.c),  # Non-default out=R.c
        I.SUB(R.a, L[1], R.b),  # Non-default out=R.b
    ]

    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b, R.c"
    assert lines[1] == "    SUB R.a, 1, R.b"


def test_program_to_text_hide_default_out_unary_operations():
    """Test hide_default_out with UnaryOperation instructions."""
    program = [
        I.NOT(R.a),  # Default out=R.a
        I.BNOT(R.b),  # Default out=R.b
        I.NOT(R.a, R.c),  # Non-default out=R.c
    ]

    # Without hide_default_out
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    NOT R.a, R.a"
    assert lines[1] == "    BNOT R.b, R.b"
    assert lines[2] == "    NOT R.a, R.c"

    # With hide_default_out
    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    NOT R.a"
    assert lines[1] == "    BNOT R.b"
    assert lines[2] == "    NOT R.a, R.c"  # Non-default still shown


def test_program_to_text_hide_default_out_nout():
    """Test hide_default_out with NOUT instruction."""
    program = [
        I.NOUT(R.a),  # Default b=L[0] (no newline)
        I.NOUT(R.a, L[1]),  # Non-default b=L[1] (with newline)
    ]

    # Without hide_default_out
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    NOUT R.a, 0"
    assert lines[1] == "    NOUT R.a, 1"

    # With hide_default_out
    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    NOUT R.a"
    assert lines[1] == "    NOUT R.a, 1"


def test_program_to_text_hide_default_out_oout():
    """Test hide_default_out with OOUT instruction."""
    program = [
        I.OOUT(LC["H"]),  # Default b=L[0] (no newline)
        I.OOUT(LC["i"], L[1]),  # Non-default b=L[1] (with newline)
    ]

    # Without hide_default_out
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    OOUT 'H', 0"
    assert lines[1] == "    OOUT 'i', 1"

    # With hide_default_out
    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    OOUT 'H'"
    assert lines[1] == "    OOUT 'i', 1"


def test_program_to_text_hide_default_out_exit():
    """Test hide_default_out with EXIT instruction."""
    program = [
        I.EXIT(),  # Default status_code=L[0]
        I.EXIT(L[1]),  # Non-default status_code
    ]

    # Without hide_default_out
    text = program_to_text(program, blank_line_before_label=False)
    lines = text.split("\n")
    assert lines[0] == "    EXIT 0"
    assert lines[1] == "    EXIT 1"

    # With hide_default_out
    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    EXIT"
    assert lines[1] == "    EXIT 1"


def test_program_to_text_hide_default_out_with_comments():
    """Test hide_default_out combined with comments."""
    program = [
        I.ADD(R.a, R.b).with_comment("Sum"),
        I.NOUT(R.a).with_comment("Print"),
    ]

    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b ; Sum"
    assert lines[1] == "    NOUT R.a ; Print"


def test_program_to_text_hide_default_out_with_aligned_comments():
    """Test hide_default_out combined with aligned comments."""
    program = [
        I.ADD(R.a, R.b).with_comment("Sum"),
        I.NOUT(R.a).with_comment("Print result"),
    ]

    text = program_to_text(
        program,
        hide_default_out=True,
        align_comments=True,
        comment_column=30,
        blank_line_before_label=False,
    )
    lines = text.split("\n")
    # "    ADD R.a, R.b" = 16 chars, pad to 30, then "; Sum"
    assert lines[0] == "    ADD R.a, R.b              ; Sum"
    assert lines[1] == "    NOUT R.a                  ; Print result"


def test_program_to_text_hide_default_out_all_instruction_types():
    """Test hide_default_out with a variety of instruction types."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),  # BinaryOperation with default out
        I.NOT(R.a),  # UnaryOperation with default out
        I.NOUT(R.a),  # NOUT with default newline
        I.OOUT(LC["!"]),  # OOUT with default newline
        I.EXIT(),  # EXIT with default status
    ]

    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "    ADD R.a, 1"
    assert lines[2] == "    NOT R.a"
    assert lines[3] == "    NOUT R.a"
    assert lines[4] == "    OOUT '!'"
    assert lines[5] == "    EXIT"


def test_program_to_text_hide_default_out_mixed_defaults_non_defaults():
    """Test program with mix of default and non-default parameters."""
    program = [
        I.ADD(R.a, R.b),  # Default out
        I.ADD(R.a, R.b, R.c),  # Non-default out
        I.SUB(R.x, L[1]),  # Default out
        I.SUB(R.x, L[1], R.y),  # Non-default out
    ]

    text = program_to_text(
        program, hide_default_out=True, blank_line_before_label=False
    )
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b"
    assert lines[1] == "    ADD R.a, R.b, R.c"
    assert lines[2] == "    SUB R.x, 1"
    assert lines[3] == "    SUB R.x, 1, R.y"
