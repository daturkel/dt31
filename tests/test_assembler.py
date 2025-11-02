import pytest

from dt31 import instructions as I
from dt31.assembler import AssemblyError, assemble
from dt31.operands import L, Label, Literal, R


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
    assert str(program[0]) == "CP(a=0, out=R[a])"


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
