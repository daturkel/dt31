from dt31 import instructions as I
from dt31.formatter import program_to_text
from dt31.operands import LC, L, Label, M, R
from dt31.parser import Comment


def test_program_to_text_simple():
    """Test converting a simple program to text."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
        I.NOUT(R.a, L[1]),
    ]
    text = program_to_text(program)
    expected = "    CP 5, R.a\n    ADD R.a, 1, R.a\n    NOUT R.a, 1\n"
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
    assert text == "start:\nend:\n"


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


def test_program_to_text_custom_indent_size():
    """Test custom indentation size."""
    program = [
        I.CP(5, R.a),
        I.ADD(R.a, L[1]),
    ]
    # 2-space indent
    text = program_to_text(program, indent_size=2)
    assert text == "  CP 5, R.a\n  ADD R.a, 1, R.a\n"

    # 8-space indent
    text = program_to_text(program, indent_size=8)
    assert text == "        CP 5, R.a\n        ADD R.a, 1, R.a\n"


def test_program_to_text_comment_spacing():
    """Test custom spacing before inline comments."""
    program = [
        I.CP(5, R.a).with_comment("Initialize"),
        I.ADD(R.a, L[1]).with_comment("Increment"),
    ]

    # No spacing (default is 1)
    text = program_to_text(program, comment_spacing=0)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a; Increment"

    # Default spacing (1)
    text = program_to_text(program, comment_spacing=1)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a ; Initialize"
    assert lines[1] == "    ADD R.a, 1, R.a ; Increment"

    # Extra spacing (2)
    text = program_to_text(program, comment_spacing=2)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
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
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "    SUB R.a, 1, R.a"
    assert lines[4] == "    JGT loop, R.a, 0"

    # Inline: labels on same line as next instruction
    text = program_to_text(program, label_inline=True, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 5  # 4 lines + empty string from trailing newline
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
    text = program_to_text(program, label_inline=True, blank_line_before_label=False)
    lines = text.split("\n")
    assert len(lines) == 3  # 2 lines + empty string from trailing newline
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
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
    assert lines[0] == "    CP 5, R.a"
    assert lines[1] == "loop:"
    assert lines[2] == "    NOUT R.a, 1"
    assert lines[3] == "end:"
    assert lines[4] == "    NOOP"

    # With blank lines before labels
    text = program_to_text(program, blank_line_before_label=True)
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
    assert len(lines) == 5  # 4 lines + empty string from trailing newline
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

    text = program_to_text(program, blank_line_before_label=True)
    lines = text.split("\n")
    assert len(lines) == 6  # 5 lines + empty string from trailing newline
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
