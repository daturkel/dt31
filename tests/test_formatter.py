import io
import subprocess
import sys
from contextlib import redirect_stdout

import pytest

from dt31 import instructions as I
from dt31.formatter import program_to_python, program_to_text
from dt31.operands import LC, L, Label, M, R
from dt31.parser import BlankLine, Comment, parse_program


def test_program_to_text_simple():
    """Test converting a simple program to text."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
        I.NOUT(R.a, L[1]),
    ]
    text = program_to_text(program)
    expected = "    CP 5, R.a\n    ADD R.a, 1\n    NOUT R.a, 1\n"
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
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1"
    assert lines[4] == "    JGT loop, R.a, 0"


def test_program_to_text_character_literals():
    """Test that character literals render correctly."""
    program = [
        I.COUT(LC["H"]),
        I.COUT(LC["i"], L[1]),
    ]
    text = program_to_text(program)
    lines = text.split("\n")
    assert lines[0] == "    COUT 'H'"
    assert lines[1] == "    COUT 'i', 1"


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
    text = program_to_text(program, blank_lines="none")
    assert text == "start:\nend:\n"


def test_program_to_text_complex():
    """Test converting a complex program with loops and function calls."""
    program = [
        I.CALL(func := Label("print_hi")),
        I.JMP(end := Label("end")),
        func,
        I.COUT(LC["H"]),
        I.COUT(LC["i"], L[1]),
        I.RET(),
        end,
    ]
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    CALL print_hi"
    assert lines[1] == "    JMP end"
    assert lines[2] == "print_hi:"
    assert lines[3] == "    COUT 'H'"
    assert lines[4] == "    COUT 'i', 1"
    assert lines[5] == "    RET"
    assert lines[6] == "end:"


def test_program_to_text_custom_indent_size():
    """Test custom indentation size."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
    ]
    # 2-space indent
    text = program_to_text(program, indent_size=2)
    assert text == "  CP 5, R.a\n  ADD R.a, 1\n"

    # 8-space indent
    text = program_to_text(program, indent_size=8)
    assert text == "        CP 5, R.a\n        ADD R.a, 1\n"


def test_program_to_text_comment_spacing():
    """Test custom margin before inline comments."""
    program = [
        I.CP(5, R.a).with_comment("Initialize"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
    ]

    # No margin
    text = program_to_text(program, comment_margin=0)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a; Initialize"
    assert lines[1] == "    ADD R.a, 1; Increment"

    # Single space margin
    text = program_to_text(program, comment_margin=1)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a ; Initialize"
    assert lines[1] == "    ADD R.a, 1 ; Increment"

    # Default margin (2)
    text = program_to_text(program, comment_margin=2)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a  ; Initialize"
    assert lines[1] == "    ADD R.a, 1  ; Increment"


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
    text = program_to_text(program, label_inline=False, blank_lines="none")
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1"
    assert lines[4] == "    JGT loop, R.a, 0"

    # Inline: labels on same line as next instruction
    text = program_to_text(program, label_inline=True, blank_lines="none")
    lines = text.split("\n")
    assert len(lines) == 5  # 4 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop: NOUT R.a, 1"
    assert lines[2] == "    SUB R.a, 1"
    assert lines[3] == "    JGT loop, R.a, 0"


def test_program_to_text_label_inline_at_end():
    """Test inline label style when label is at end of program."""
    program = [
        I.CP(5, R.a),
        Label("end"),
    ]

    # Label at end should still appear even when inline style is enabled
    text = program_to_text(program, label_inline=True, blank_lines="none")
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
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
    text = program_to_text(program, label_inline=True, blank_lines="none")
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "label1: label2: label3: NOUT R.a, 1"


def test_program_to_text_blank_line_before_label():
    """Test blank line modes with labels."""
    program = [
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
        Label("end"),
        I.NOOP(),
    ]

    # blank_lines="none": no blank lines
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "end:"
    assert lines[4] == "    NOOP"

    # blank_lines="auto": add blank lines before labels
    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 8  # 7 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before loop
    assert lines[2] == "loop:"
    assert lines[3] == "    NOUT R.a, 1"
    assert lines[4] == ""  # blank line before end
    assert lines[5] == "end:"
    assert lines[6] == "    NOOP"


def test_program_to_text_blank_line_before_label_inline():
    """Test that blank_lines='auto' works with label_inline=True."""
    program = [
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
        I.SUB(R.a, L[1]),
    ]

    # Inline labels WITH blank line before them
    text = program_to_text(program, label_inline=True, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 5  # 4 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before loop
    assert lines[2] == "loop: NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1"


def test_program_to_text_blank_line_before_first_label():
    """Test that blank line is NOT added before first label at program start."""
    program = [
        Label("start"),
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
    ]

    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
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

    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == ""  # blank line before first label
    assert lines[2] == "label1:"
    assert lines[3] == "label2:"  # No blank line before consecutive label
    assert lines[4] == "    NOUT R.a, 1"


def test_program_to_text_blank_line_before_comment_and_label():
    """Test that blank line is added before comment when it precedes a label."""
    program = [
        I.NOOP(),
        Comment("foo"),
        Label("label"),
        I.CP(5, R.a),
    ]

    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    NOOP"
    assert lines[1] == ""  # blank line before comment (to keep it with label)
    assert lines[2] == "; foo"
    assert lines[3] == "label:"
    assert lines[4] == "    CP 5, R.a"


def test_program_to_text_multiple_comments_before_label():
    """Test that blank line is added before first comment when multiple comments precede a label."""
    program = [
        I.NOOP(),
        Comment("comment 1"),
        Comment("comment 2"),
        Label("label"),
        I.CP(5, R.a),
    ]

    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 7  # 6 lines + empty string from trailing newline
    assert lines[0] == "    NOOP"
    assert lines[1] == ""  # blank line before first comment
    assert lines[2] == "; comment 1"
    assert lines[3] == "; comment 2"  # no blank line before second comment
    assert lines[4] == "label:"
    assert lines[5] == "    CP 5, R.a"


def test_program_to_text_comment_not_before_label():
    """Test that blank line is NOT added before comment when it doesn't precede a label."""
    program = [
        I.NOOP(),
        Comment("standalone comment"),
        I.CP(5, R.a),
    ]

    text = program_to_text(program, blank_lines="auto")
    lines = text.split("\n")
    assert len(lines) == 4  # 3 lines + empty string from trailing newline
    assert lines[0] == "    NOOP"
    assert lines[1] == "    ; standalone comment"  # no blank line before comment
    assert lines[2] == "    CP 5, R.a"


def test_program_to_text_align_comments():
    """Test aligning inline comments at a column."""
    program = [
        I.CP(5, R.a).with_comment("Initialize"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
        I.NOUT(R.a, L[1]).with_comment("Print"),
    ]

    # Default: no alignment (default margin is 2)
    text = program_to_text(program, align_comments=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a  ; Initialize"
    assert lines[1] == "    ADD R.a, 1  ; Increment"
    assert lines[2] == "    NOUT R.a, 1  ; Print"

    # Align at column 30
    text = program_to_text(
        program, align_comments=True, comment_column=30, blank_lines="none"
    )
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a                 ; Initialize"
    assert lines[1] == "    ADD R.a, 1                ; Increment"
    assert lines[2] == "    NOUT R.a, 1               ; Print"
    # Verify all comments start at column 30 (skip empty trailing line)
    for line in lines:
        if line:  # Skip empty string from trailing newline
            assert line.index(";") == 30


def test_program_to_text_align_comments_exceeds_column():
    """Test comment alignment when instruction exceeds column."""
    program = [
        I.CP(5, R.a).with_comment("Short"),
        I.ADD(R.a, R.b, M[R.a]).with_comment("Very long instruction"),
    ]

    # Align at column 20 (second instruction will exceed this)
    text = program_to_text(
        program, align_comments=True, comment_column=20, blank_lines="none"
    )
    lines = text.split("\n")

    # First line should align at column 20
    assert lines[0] == "    CP 5, R.a       ; Short"
    assert lines[0].index(";") == 20

    # Second line exceeds column, should fall back to comment_margin
    assert lines[1] == "    ADD R.a, R.b, [R.a]  ; Very long instruction"


def test_program_to_text_align_comments_custom_spacing_fallback():
    """Test that comment_margin is used when instruction exceeds column."""
    program = [
        I.ADD(R.a, R.b, M[R.a]).with_comment("Long instruction"),
    ]

    # Column 10 will be exceeded, fallback to comment_margin=3
    text = program_to_text(
        program,
        align_comments=True,
        comment_column=10,
        comment_margin=3,
        blank_lines="none",
    )
    lines = text.split("\n")

    # Should use 3 spaces before comment
    assert lines[0] == "    ADD R.a, R.b, [R.a]   ; Long instruction"


def test_program_to_text_align_comments_standalone_not_aligned():
    """Test that standalone comments are never aligned."""
    program = [
        Comment("Standalone comment"),
        I.CP(5, R.a).with_comment("Inline comment"),
        Comment("Another standalone"),
    ]

    text = program_to_text(
        program, align_comments=True, comment_column=30, blank_lines="none"
    )
    lines = text.split("\n")

    # Standalone comments should not be aligned
    assert lines[0] == "    ; Standalone comment"
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
        comment_margin=2,
        label_inline=True,
        blank_lines="auto",
        align_comments=True,
        comment_column=25,
    )
    lines = text.split("\n")

    assert lines[0] == "  CP 10, R.x             ; Initialize"
    assert lines[1] == ""  # blank line before label
    assert lines[2] == "loop: NOUT R.x, 1        ; Print"
    assert lines[3] == "  SUB R.x, 1"
    assert lines[4] == "  JGT loop, R.x, 0"

    # Verify alignment
    assert lines[0].index(";") == 25
    assert lines[2].index(";") == 25


# ============================================================================
# Hide Default Arguments
# ============================================================================


def test_program_to_text_hide_default_args_binary_operations():
    """Test hide_default_args with BinaryOperation instructions."""
    program = [
        I.ADD(R.a, R.b),  # Default out=R.a
        I.SUB(R.a, L[1]),  # Default out=R.a
        I.MUL(R.b, L[2]),  # Default out=R.b
    ]

    # With hide_default_args (default)
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b"
    assert lines[1] == "    SUB R.a, 1"
    assert lines[2] == "    MUL R.b, 2"

    # Without hide_default_args
    text = program_to_text(program, hide_default_args=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b, R.a"
    assert lines[1] == "    SUB R.a, 1, R.a"
    assert lines[2] == "    MUL R.b, 2, R.b"


def test_program_to_text_hide_default_args_non_default_output():
    """Test that non-default arguments are still shown."""
    program = [
        I.ADD(R.a, R.b, R.c),  # Non-default out=R.c
        I.SUB(R.a, L[1], R.b),  # Non-default out=R.b
    ]

    text = program_to_text(program, hide_default_args=True, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b, R.c"
    assert lines[1] == "    SUB R.a, 1, R.b"


def test_program_to_text_hide_default_args_unary_operations():
    """Test hide_default_args with UnaryOperation instructions."""
    program = [
        I.NOT(R.a),  # Default out=R.a
        I.BNOT(R.b),  # Default out=R.b
        I.NOT(R.a, R.c),  # Non-default out=R.c
    ]

    # With hide_default_args (default)
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    NOT R.a"
    assert lines[1] == "    BNOT R.b"
    assert lines[2] == "    NOT R.a, R.c"  # Non-default still shown

    # Without hide_default_args
    text = program_to_text(program, hide_default_args=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    NOT R.a, R.a"
    assert lines[1] == "    BNOT R.b, R.b"
    assert lines[2] == "    NOT R.a, R.c"


def test_program_to_text_hide_default_args_nout():
    """Test hide_default_args with NOUT instruction."""
    program = [
        I.NOUT(R.a),  # Default b=L[0] (no newline)
        I.NOUT(R.a, L[1]),  # Non-default b=L[1] (with newline)
    ]

    # With hide_default_args (default)
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    NOUT R.a"
    assert lines[1] == "    NOUT R.a, 1"

    # Without hide_default_args
    text = program_to_text(program, hide_default_args=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    NOUT R.a, 0"
    assert lines[1] == "    NOUT R.a, 1"


def test_program_to_text_hide_default_args_cout():
    """Test hide_default_args with COUT instruction."""
    program = [
        I.COUT(LC["H"]),  # Default b=L[0] (no newline)
        I.COUT(LC["i"], L[1]),  # Non-default b=L[1] (with newline)
    ]

    # With hide_default_args (default)
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    COUT 'H'"
    assert lines[1] == "    COUT 'i', 1"

    # Without hide_default_args
    text = program_to_text(program, hide_default_args=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    COUT 'H', 0"
    assert lines[1] == "    COUT 'i', 1"


def test_program_to_text_hide_default_args_exit():
    """Test hide_default_args with EXIT instruction."""
    program = [
        I.EXIT(),  # Default status_code=L[0]
        I.EXIT(L[1]),  # Non-default status_code
    ]

    # With hide_default_args (default)
    text = program_to_text(program, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    EXIT"
    assert lines[1] == "    EXIT 1"

    # Without hide_default_args
    text = program_to_text(program, hide_default_args=False, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    EXIT 0"
    assert lines[1] == "    EXIT 1"


def test_program_to_text_hide_default_args_with_comments():
    """Test hide_default_args combined with comments."""
    program = [
        I.ADD(R.a, R.b).with_comment("Sum"),
        I.NOUT(R.a).with_comment("Print"),
    ]

    text = program_to_text(program, hide_default_args=True, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b  ; Sum"
    assert lines[1] == "    NOUT R.a  ; Print"


def test_program_to_text_hide_default_args_with_aligned_comments():
    """Test hide_default_args combined with aligned comments."""
    program = [
        I.ADD(R.a, R.b).with_comment("Sum"),
        I.NOUT(R.a).with_comment("Print result"),
    ]

    text = program_to_text(
        program,
        hide_default_args=True,
        align_comments=True,
        comment_column=30,
        blank_lines="none",
    )
    lines = text.split("\n")
    # "    ADD R.a, R.b" = 16 chars, pad to 30, then "; Sum"
    assert lines[0] == "    ADD R.a, R.b              ; Sum"
    assert lines[1] == "    NOUT R.a                  ; Print result"


def test_program_to_text_hide_default_args_all_instruction_types():
    """Test hide_default_args with a variety of instruction types."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),  # BinaryOperation with default out
        I.NOT(R.a),  # UnaryOperation with default out
        I.NOUT(R.a),  # NOUT with default newline
        I.COUT(LC["!"]),  # COUT with default newline
        I.EXIT(),  # EXIT with default status
    ]

    text = program_to_text(program, hide_default_args=True, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "    ADD R.a, 1"
    assert lines[2] == "    NOT R.a"
    assert lines[3] == "    NOUT R.a"
    assert lines[4] == "    COUT '!'"
    assert lines[5] == "    EXIT"


def test_program_to_text_hide_default_args_mixed_defaults_non_defaults():
    """Test program with mix of default and non-default arguments."""
    program = [
        I.ADD(R.a, R.b),  # Default out
        I.ADD(R.a, R.b, R.c),  # Non-default out
        I.SUB(R.x, L[1]),  # Default out
        I.SUB(R.x, L[1], R.y),  # Non-default out
    ]

    text = program_to_text(program, hide_default_args=True, blank_lines="none")
    lines = text.split("\n")
    assert lines[0] == "    ADD R.a, R.b"
    assert lines[1] == "    ADD R.a, R.b, R.c"
    assert lines[2] == "    SUB R.x, 1"
    assert lines[3] == "    SUB R.x, 1, R.y"


def test_strip_comments_basic():
    """Test that strip_comments removes all comment types."""
    program = [
        Comment("Standalone comment"),
        I.CP(5, R.a).with_comment("Inline comment"),
        Label("loop").with_comment("Label comment"),
        I.ADD(R.a, L[1]).with_comment("Another inline"),
    ]

    text = program_to_text(program, strip_comments=True, blank_lines="none")
    expected = "    CP 5, R.a\nloop:\n    ADD R.a, 1\n"
    assert text == expected


def test_strip_comments_overrides_align():
    """Test that strip_comments takes precedence over align_comments."""
    program = [
        I.CP(5, R.a).with_comment("Comment 1"),
        I.ADD(R.a, L[1]).with_comment("Comment 2"),
    ]

    # Both flags set, strip should win
    text = program_to_text(
        program, strip_comments=True, align_comments=True, comment_column=40
    )
    expected = "    CP 5, R.a\n    ADD R.a, 1\n"
    assert text == expected


def test_strip_comments_preserves_structure():
    """Test that stripping comments preserves structure."""
    program = [
        I.CP(5, R.a).with_comment("Init"),
        Label("loop"),
        I.ADD(R.a, L[1]),
        I.JGT(Label("loop"), R.a, L[0]),
    ]

    # With blank_lines="auto" to add blank line before label
    text = program_to_text(program, strip_comments=True, blank_lines="auto")
    expected = "    CP 5, R.a\n\nloop:\n    ADD R.a, 1\n    JGT loop, R.a, 0\n"
    assert text == expected


def test_strip_comments_edge_cases():
    """Test strip_comments with edge cases."""
    # Only comments
    program = [Comment("Only comment")]
    text = program_to_text(program, strip_comments=True)
    assert text == ""

    # No comments to strip
    program = [I.CP(5, R.a), I.ADD(R.a, L[1])]
    text_normal = program_to_text(program, strip_comments=False)
    text_stripped = program_to_text(program, strip_comments=True)
    assert text_normal == text_stripped
    expected = "    CP 5, R.a\n    ADD R.a, 1\n"
    assert text_stripped == expected


def test_strip_comments_inline_labels():
    """Test strip_comments with inline labels that have comments."""
    program = [
        I.CP(5, R.a),
        Label("loop").with_comment("Loop start"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
    ]

    text = program_to_text(
        program, strip_comments=True, label_inline=True, blank_lines="none"
    )
    expected = "    CP 5, R.a\nloop: ADD R.a, 1\n"
    assert text == expected


def test_auto_align_comments():
    """Test automatic comment column calculation."""
    program = [
        I.CP(5, R.a).with_comment("Short"),
        I.ADD(R.a, R.b, R.c).with_comment("Longer instruction"),
        I.SUB(R.a, L[1]).with_comment("Medium"),
    ]

    text = program_to_text(program, align_comments=True)

    # Longest line is "    ADD R.a, R.b, R.c" = 21 chars
    # With default margin=2, comments should start at column 23
    expected = "    CP 5, R.a          ; Short\n    ADD R.a, R.b, R.c  ; Longer instruction\n    SUB R.a, 1         ; Medium\n"
    assert text == expected


def test_auto_align_custom_margin():
    """Test custom comment margin."""
    program = [
        I.CP(5, R.a).with_comment("Comment"),
        I.ADD(R.a, R.b).with_comment("Another"),
    ]

    text = program_to_text(program, align_comments=True, comment_margin=4)

    # Longest line is "    ADD R.a, R.b" = 16 chars (default hides R.a output)
    # With margin=4, comments should start at column 20
    expected = "    CP 5, R.a       ; Comment\n    ADD R.a, R.b    ; Another\n"
    assert text == expected


def test_fixed_column_overrides_auto():
    """Test that explicit comment_column disables auto-calculation."""
    program = [
        I.CP(5, R.a).with_comment("Short"),
        I.ADD(R.a, R.b, R.c).with_comment("Long"),
    ]

    # Use fixed column 30
    text = program_to_text(program, align_comments=True, comment_column=30)

    expected = (
        "    CP 5, R.a                 ; Short\n    ADD R.a, R.b, R.c         ; Long\n"
    )
    assert text == expected


def test_auto_align_with_hide_default_args():
    """Test that auto-calculation respects hide_default_args."""
    program = [
        I.ADD(R.a, R.b).with_comment("Test"),
    ]

    # With hide_default_args, instruction is shorter
    text_hidden = program_to_text(program, align_comments=True, hide_default_args=True)
    text_shown = program_to_text(program, align_comments=True, hide_default_args=False)

    # Extract semicolon positions
    pos_hidden = text_hidden.index(";")
    pos_shown = text_shown.index(";")

    # Comment should be closer when output is hidden
    assert pos_hidden < pos_shown

    # Verify exact output
    # "    ADD R.a, R.b" = 16 chars, +2 margin = 18
    expected_hidden = "    ADD R.a, R.b  ; Test\n"
    assert text_hidden == expected_hidden

    # "    ADD R.a, R.b, R.a" = 21 chars, +2 margin = 23
    expected_shown = "    ADD R.a, R.b, R.a  ; Test\n"
    assert text_shown == expected_shown


def test_auto_align_edge_cases():
    """Test auto-align with edge cases."""
    # Empty program
    text = program_to_text([], align_comments=True)
    assert text == ""

    # Only comments (no instructions to measure)
    program = [Comment("Only comment")]
    text = program_to_text(program, align_comments=True)
    # Should not crash, comment_column will be 0 + margin = 2
    assert text == "; Only comment\n"

    # No comments to align
    program = [I.CP(5, R.a), I.ADD(R.a, L[1])]
    text = program_to_text(program, align_comments=True)
    expected = "    CP 5, R.a\n    ADD R.a, 1\n"
    assert text == expected


def test_margin_ignored_with_column():
    """Test that comment_margin is ignored when comment_column is specified."""
    program = [I.CP(5, R.a).with_comment("Test")]

    # Both should produce identical output
    text1 = program_to_text(
        program, align_comments=True, comment_column=40, comment_margin=2
    )
    text2 = program_to_text(
        program, align_comments=True, comment_column=40, comment_margin=10
    )

    assert text1 == text2
    expected = "    CP 5, R.a                           ; Test\n"
    assert text1 == expected


# ============================================================================
# Preserve Newlines
# ============================================================================


def test_preserve_newlines_basic():
    """Test that preserve_newlines preserves blank lines from source."""
    text = """CP 5, R.a

ADD R.a, 1

NOUT R.a, 1
"""
    program = parse_program(text, preserve_newlines=True)

    # Verify BlankLine objects were created
    assert isinstance(program[0], I.Instruction)
    assert isinstance(program[1], BlankLine)
    assert isinstance(program[2], I.Instruction)
    assert isinstance(program[3], BlankLine)
    assert isinstance(program[4], I.Instruction)

    # Format with preserve_newlines
    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    CP 5, R.a\n\n    ADD R.a, 1\n\n    NOUT R.a, 1\n"
    assert formatted == expected


def test_preserve_newlines_multiple_blanks():
    """Test preserving multiple consecutive blank lines."""
    text = """CP 5, R.a


ADD R.a, 1
"""
    program = parse_program(text, preserve_newlines=True)

    # Should have 2 blank lines
    assert isinstance(program[1], BlankLine)
    assert isinstance(program[2], BlankLine)

    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    CP 5, R.a\n\n\n    ADD R.a, 1\n"
    assert formatted == expected


def test_preserve_newlines_with_labels():
    """Test preserve_newlines with labels."""
    text = """CP 5, R.a

loop:
    NOUT R.a, 1
    SUB R.a, 1

    JGT loop, R.a, 0
"""
    program = parse_program(text, preserve_newlines=True)
    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    CP 5, R.a\n\nloop:\n    NOUT R.a, 1\n    SUB R.a, 1\n\n    JGT loop, R.a, 0\n"
    assert formatted == expected


def test_preserve_newlines_no_automatic_blanks():
    """Test that blank_lines='preserve' doesn't add automatic blank lines."""
    text = """CP 5, R.a
loop:
    NOUT R.a, 1
"""
    program = parse_program(text, preserve_newlines=True)

    # With blank_lines="preserve", should NOT add blank lines automatically
    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    CP 5, R.a\nloop:\n    NOUT R.a, 1\n"
    assert formatted == expected


def test_preserve_newlines_false_ignores_blank_lines():
    """Test that blank_lines modes other than 'preserve' ignore BlankLine objects."""
    program = [
        I.CP(5, R.a),
        BlankLine(),
        I.ADD(R.a, L[1]),
    ]

    # With blank_lines="none", BlankLine should be ignored
    formatted = program_to_text(program, blank_lines="none")
    expected = "    CP 5, R.a\n    ADD R.a, 1\n"
    assert formatted == expected

    # With blank_lines="auto", BlankLine should also be ignored
    formatted = program_to_text(program, blank_lines="auto")
    expected = "    CP 5, R.a\n    ADD R.a, 1\n"
    assert formatted == expected


def test_preserve_newlines_with_comments():
    """Test preserve_newlines with standalone comments."""
    text = """; Initialize
CP 5, R.a

; Loop
loop:
    NOUT R.a, 1
"""
    program = parse_program(text, preserve_newlines=True)
    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    ; Initialize\n    CP 5, R.a\n\n; Loop\nloop:\n    NOUT R.a, 1\n"
    assert formatted == expected


def test_program_to_text_standalone_comment_indentation():
    """Test that a standalone comment is indented only when directly above an instruction."""
    text = """; header

; section
loop:
; step 1
; step 2
    CP 5, R.a
    ; before blank

    NOUT R.a, 1
    ; trailing
"""
    program = parse_program(text, preserve_newlines=True)
    expected = """; header

; section
loop:
    ; step 1
    ; step 2
    CP 5, R.a
; before blank

    NOUT R.a, 1
; trailing
"""
    assert program_to_text(program) == expected


def test_program_to_text_standalone_comment_before_inline_label():
    """Test that a comment above an inline-labeled instruction stays at column 0."""
    program = [
        Label("loop"),
        Comment("body"),
        I.NOUT(R.a, L[1]),
        Comment("next"),
        I.JMP(Label("loop")),
    ]
    expected = "; body\nloop: NOUT R.a, 1\n    ; next\n    JMP loop\n"
    assert program_to_text(program, label_inline=True) == expected


def test_program_to_text_indented_comment_before_label_auto_blank_line():
    """Test that blank_lines="auto" keeps an indented comment's block together before a label."""
    program = [
        I.NOOP(),
        Comment("note"),
        Label("loop"),
        I.NOOP(),
    ]
    expected = "    NOOP\n\n; note\nloop:\n    NOOP\n"
    assert program_to_text(program, blank_lines="auto") == expected


def test_format_round_trips_comment_text():
    """Test that comment spacing and bare semicolons survive formatting."""
    text = """; Algorithm:
;   - step one
;
;   - step two

    CP 5, R.a  ;   aligned
"""
    program = parse_program(text, preserve_newlines=True)
    assert program_to_text(program) == text


def test_preserve_newlines_empty_lines_only():
    """Test program with only blank lines."""
    text = """

"""
    program = parse_program(text, preserve_newlines=True)

    # Should have 2 BlankLine objects
    assert len(program) == 2
    assert all(isinstance(item, BlankLine) for item in program)

    formatted = program_to_text(program, blank_lines="preserve")
    # Two BlankLines append two "" to lines list
    # "\n".join(["", ""]) gives "\n", and we ensure trailing newline
    expected = "\n"
    assert formatted == expected


def test_preserve_newlines_with_inline_comments():
    """Test preserve_newlines with inline comments."""
    text = """CP 5, R.a  ; Init

ADD R.a, 1  ; Increment
"""
    program = parse_program(text, preserve_newlines=True)
    formatted = program_to_text(program, blank_lines="preserve")
    expected = "    CP 5, R.a  ; Init\n\n    ADD R.a, 1  ; Increment\n"
    assert formatted == expected


def test_preserve_newlines_roundtrip():
    """Test that preserve_newlines maintains formatting through parse/format cycle."""
    original = """; Factorial example
CP 5, R.a
CALL factorial

JMP end

factorial:
    JGT recursive_case, R.a, 1
    CP 1, R.a
    RET

recursive_case:
    PUSH R.a
    SUB R.a, 1
    CALL factorial
    POP R.b
    MUL R.a, R.b
    RET

end:
"""
    program = parse_program(original, preserve_newlines=True)
    formatted = program_to_text(program, blank_lines="preserve")

    # Reparse and format again
    program2 = parse_program(formatted, preserve_newlines=True)
    formatted2 = program_to_text(program2, blank_lines="preserve")

    # Should be identical after second cycle
    assert formatted == formatted2


def test_program_to_python_simple():
    """Basic instructions with no labels: only DT31/I imported, no register ops."""
    program = [
        I.CP(5, R.a),
        I.NOUT(R.a, L[1]),
    ]
    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=5, b=R.a),\n"
        "    I.NOUT(a=R.a, b=1),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_no_registers_omits_the_kwarg():
    """A program that uses no registers gets a plain `DT31()` -- not
    `DT31(registers=[])`, which would zero out the default a/b/c registers
    instead of just not needing any of them."""
    out = program_to_python([I.COUT(LC["H"])])
    assert out == (
        "from dt31 import DT31, LC, I\n"
        "\n"
        "program = [\n"
        '    I.COUT(a=LC["H"], b=0),\n'
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    cpu = DT31()\n"
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_cpu_config_kwargs():
    """memory_size/stack_size/debug are passed through to the generated
    `DT31(...)`/`cpu.run(...)` calls only when given -- mirroring
    `cli.run_command`'s own cpu_kwargs construction, so the common case still
    reads as a plain call with no default arguments spelled out."""
    program = [I.CP(5, R.a)]

    out = program_to_python(program, memory_size=1024, stack_size=64, debug=True)
    assert out == (
        "from dt31 import DT31, I, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=5, b=R.a),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"], memory_size=1024, stack_size=64)\n'
        "    cpu.run(program, debug=True)\n"
    )

    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=5, b=R.a),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_explicit_registers_override_auto_detection():
    """Passing `registers=` skips auto-detection entirely -- the caller (the
    CLI's `-r/--registers`) is trusted to have already validated it covers
    every register the program uses."""
    out = program_to_python([I.CP(5, R.a)], registers=["a", "b", "c"])
    assert out == (
        "from dt31 import DT31, I, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=5, b=R.a),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a", "b", "c"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_explicit_registers_validated():
    """Unlike the auto-detected list (each name already validated when its
    `RegisterReference` was constructed), an explicit `registers=` list is
    caller-supplied and must be checked itself -- otherwise an invalid name
    reaching this function directly (bypassing the CLI's own check) could
    produce broken or unsafe generated source."""
    with pytest.raises(ValueError, match="Invalid register name"):
        program_to_python([I.CP(5, R.a)], registers=["1bad"])


def test_program_to_python_imports_only_what_is_used():
    """M/R/LC/Label are only imported when actually referenced."""
    # No operand types beyond plain literals: only DT31, I needed.
    out = program_to_python([I.NOOP()])
    assert out == (
        "from dt31 import DT31, I\n"
        "\n"
        "program = [\n"
        "    I.NOOP(),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    cpu = DT31()\n"
        "    cpu.run(program, debug=False)\n"
    )

    # Memory reference pulls in M.
    out = program_to_python([I.CP(1, M[0])])
    assert out == (
        "from dt31 import DT31, I, M\n"
        "\n"
        "program = [\n"
        "    I.CP(a=1, b=M[0]),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    cpu = DT31()\n"
        "    cpu.run(program, debug=False)\n"
    )

    # Character literal pulls in LC.
    out = program_to_python([I.COUT(LC["A"])])
    assert out == (
        "from dt31 import DT31, LC, I\n"
        "\n"
        "program = [\n"
        '    I.COUT(a=LC["A"], b=0),\n'
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    cpu = DT31()\n"
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_label_walrus_on_first_occurrence_reference():
    """A label referenced before its marker position gets the walrus at the
    reference; the marker later just uses the bare name (mirrors
    examples/factorial_with_labels.py's hand-written style)."""
    program = [
        I.CP(1, R.a),
        I.JGT(end := Label("end"), R.a, 0),
        end,
        I.NOUT(R.a, L[1]),
    ]
    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, Label, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=1, b=R.a),\n"
        '    I.JGT(dest=(end := Label("end")), a=R.a, b=0),\n'
        "    end,\n"
        "    I.NOUT(a=R.a, b=1),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_label_walrus_on_first_occurrence_marker():
    """A label whose marker comes before any reference gets the walrus at the
    marker position; later references use the bare name."""
    program = [
        loop := Label("loop"),
        I.NOUT(R.a, L[1]),
        I.SUB(R.a, L[1]),
        I.JGT(loop, R.a, 0),
    ]
    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, Label, R\n"
        "\n"
        "program = [\n"
        '    loop := Label("loop"),\n'
        "    I.NOUT(a=R.a, b=1),\n"
        "    I.SUB(a=R.a, b=1, out=R.a),\n"
        "    I.JGT(dest=loop, a=R.a, b=0),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_invalid_identifier_label_name():
    """A label name that's a Python keyword or starts with a digit can't be a
    walrus target, so every occurrence gets its own fresh Label(...) literal
    instead -- no renaming, no shared variable, no collision bookkeeping."""
    text = "JGT class, R.a, 0\nclass:\nNOUT R.a, 1"
    program = parse_program(text)
    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, Label, R\n"
        "\n"
        "program = [\n"
        '    I.JGT(dest=Label("class"), a=R.a, b=0),\n'
        '    Label("class"),\n'
        "    I.NOUT(a=R.a, b=1),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_comments_and_blank_lines():
    program = [
        Comment("a comment"),
        I.CP(5, R.a),
        BlankLine(),
        I.NOUT(R.a, L[1]),
    ]
    out = program_to_python(program)
    assert out == (
        "from dt31 import DT31, I, R\n"
        "\n"
        "program = [\n"
        "    # a comment\n"
        "    I.CP(a=5, b=R.a),\n"
        "\n"
        "    I.NOUT(a=R.a, b=1),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a"])\n'
        "    cpu.run(program, debug=False)\n"
    )


@pytest.mark.parametrize(
    "source",
    [
        "CP 3, R.a\nNOUT R.a, 1",
        ("CP 3, R.a\nloop:\nNOUT R.a, 1\nSUB R.a, 1\nJGT loop, R.a, 0\n"),
        "JGT class, R.a, 0\nclass:\nNOUT R.a, 1",
        # Relative jumps and calls take their destination as `delta`, not
        # `dest`, so generating the call from the repr has to use that name.
        "CP 0, R.a\nADD R.a, 1\nNOUT R.a, 1\nRJLT -2, R.a, 3",
        "RCALL 2\nJMP 5\nCOUT 'h', 1\nRET",
        # Label names that collide with what the generated module binds must not
        # be bound with the walrus operator, or they shadow the import.
        "JMP R\nR:\nCP 5, R.a\nNOUT R.a, 1",
        "JMP M\nM:\nCP 5, [1]\nNOUT [1], 1",
        "JMP I\nI:\nNOUT 1, 1",
        "JMP program\nprogram:\nNOUT 1, 1",
        "CP 10, R.a\nCP 3, R.b\nCP 7, [R.a + 5]\nCP 8, [R.a-R.b]\nNOUT [R.a+5], 1\nNOUT [R.a-3], 1",
        "CP 97, R.c\nCP 5, [R.c-'a']\nCP 6, [100-R.c]\nNOUT [0], 1\nNOUT [3], 1\nNOUT [R.c+','], 1",
        # Comments ride along as `.with_comment(...)` calls.
        "CP 5, R.a  ; init\nloop:  ; top\nNOUT R.a, 1\nSUB R.a, 1\nJGT loop, R.a, 0  ; again",
    ],
)
def test_program_to_python_generated_file_executes_correctly(tmp_path, source):
    """The generated .py file isn't just syntactically valid -- running it
    produces the same output as running the original .dt program directly."""
    from dt31 import DT31
    from dt31.assembler import extract_registers_from_program

    program = parse_program(source)
    registers = extract_registers_from_program(program)
    cpu = DT31(registers=registers)
    expected = io.StringIO()
    with redirect_stdout(expected):
        cpu.run(program, debug=False)

    py_source = program_to_python(program)
    py_file = tmp_path / "generated.py"
    py_file.write_text(py_source)

    result = subprocess.run(
        [sys.executable, str(py_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected.getvalue()


def test_program_to_python_empty_comment():
    out = program_to_python([Comment(""), I.NOOP()])
    assert out == (
        "from dt31 import DT31, I\n"
        "\n"
        "program = [\n"
        "    #\n"
        "    I.NOOP(),\n"
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    cpu = DT31()\n"
        "    cpu.run(program, debug=False)\n"
    )


def test_program_to_python_preserves_instruction_comments():
    program = parse_program("CP 5, R.a  ; initialise the counter")
    out = program_to_python(program)
    assert '    I.CP(a=5, b=R.a).with_comment("initialise the counter"),\n' in out


def test_program_to_python_preserves_label_comments():
    program = parse_program("loop:  ; top of loop\nNOUT 1, 1")
    out = program_to_python(program)
    assert '    loop := Label("loop").with_comment("top of loop"),\n' in out


def test_program_to_python_label_walrus_binds_the_commented_label():
    """`with_comment` returns a copy, so the call has to sit inside the walrus --
    otherwise the bound name is a different, uncommented object to the one in the
    list."""
    source = "loop:  ; top of loop\nNOUT 1, 1\nJGT loop, 1, 0"
    namespace: dict = {}
    exec(program_to_python(parse_program(source)), namespace)

    label = namespace["program"][0]
    assert namespace["loop"] is label
    assert label.comment == "top of loop"
    assert namespace["program"][2].dest is label


def test_program_to_python_forward_jump_marker_comment_stays_outside():
    """A marker whose name was already bound by an earlier jump can't amend the
    binding in place, so its comment hangs off the name instead."""
    out = program_to_python(parse_program("JMP end\nNOUT 1, 1\nend:  ; done"))
    assert '    I.JMP(dest=(end := Label("end"))),\n' in out
    assert '    end.with_comment("done"),\n' in out


def test_program_to_python_comments_survive_a_round_trip(tmp_path):
    """A comment written in assembly survives .dt -> .py -> program -> .dt."""
    source = "CP 5, R.a  ; initialise the counter\nNOUT R.a, 1"
    py_file = tmp_path / "generated.py"
    py_file.write_text(program_to_python(parse_program(source)))

    namespace: dict = {}
    exec(compile(py_file.read_text(), str(py_file), "exec"), namespace)

    assert namespace["program"][0].comment == "initialise the counter"
    assert "; initialise the counter" in program_to_text(namespace["program"])


def test_program_to_python_escapes_quotes_in_comments():
    program = [I.NOOP().with_comment('he said "hi"')]
    out = program_to_python(program)
    assert '    I.NOOP().with_comment("he said \\"hi\\""),\n' in out


def test_program_to_python_keeps_non_ascii_comments_literal():
    program = [I.NOOP().with_comment("data \u2260 0")]
    out = program_to_python(program)
    assert '.with_comment("data \u2260 0")' in out


@pytest.mark.parametrize(
    "name", ["DT31", "I", "L", "LC", "Label", "M", "R", "cpu", "program"]
)
def test_program_to_python_reserved_label_names_are_not_bound(name):
    """A label named after something the generated module binds is emitted as a
    literal `Label(...)` at every occurrence rather than via the walrus."""
    program = [I.JMP(Label(name)), Label(name)]
    out = program_to_python(program)
    assert f"{name} :=" not in out
    assert out.count(f'Label("{name}")') == 2


def test_program_to_python_comment_text_does_not_add_imports():
    """Import selection reads the program's operands, not the rendered source, so
    a comment that happens to mention M[...] or R.a introduces no import."""
    program = [
        Comment("bump M[0] and R.a, see LC['x'] and Label(foo)"),
        I.NOOP().with_comment("also mentions M[1] and R.b"),
    ]
    out = program_to_python(program)
    assert out.startswith("from dt31 import DT31, I\n")


def test_program_to_python_imports_label_for_a_bare_marker():
    """A label that is never a jump destination still needs the Label import."""
    out = program_to_python([Label("start"), I.NOOP()])
    assert out.startswith("from dt31 import DT31, I, Label\n")


def test_program_to_python_imports_lc_for_a_nested_char_literal():
    """Operand walking recurses, so a char literal inside a memory reference is
    still detected."""
    out = program_to_python([I.CP(1, M[LC["A"]])])
    assert out.startswith("from dt31 import DT31, LC, I, M\n")


def test_program_to_text_memory_offsets():
    program = parse_program(
        "CP [ R.a + 5 ], M[R.a-R.b]\nNOUT [100 - R.a], 1\nCOUT [R.c + ','], 1"
    )
    assert program_to_text(program) == (
        "    CP [R.a + 5], [R.a - R.b]\n"
        "    NOUT [100 - R.a], 1\n"
        "    COUT [R.c + ','], 1\n"
    )


def test_program_to_python_memory_offsets():
    program = parse_program("CP 1, [R.a+5]\nCP [100-R.b], R.c\nCP 2, [R.c-'a']")
    assert program_to_python(program) == (
        "from dt31 import DT31, LC, I, M, R\n"
        "\n"
        "program = [\n"
        "    I.CP(a=1, b=M[R.a + 5]),\n"
        "    I.CP(a=M[100 - R.b], b=R.c),\n"
        '    I.CP(a=2, b=M[R.c - LC["a"]]),\n'
        "]\n"
        "\n"
        'if __name__ == "__main__":\n'
        '    cpu = DT31(registers=["a", "b", "c"])\n'
        "    cpu.run(program, debug=False)\n"
    )
