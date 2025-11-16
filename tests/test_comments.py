import dt31.instructions as I
from dt31 import DT31
from dt31.assembler import program_to_text
from dt31.operands import L, Label, R
from dt31.parser import Comment, parse_program

# -------------------------------- Comment Parsing -------------------------------- #


def test_comment_on_label():
    """Test parsing label with comment."""
    text = "loop:  ; Main loop"
    program = parse_program(text)

    assert len(program) == 1
    assert isinstance(program[0], Label)
    assert program[0].name == "loop"
    assert program[0].comment == "Main loop"


def test_comment_on_instruction():
    """Test parsing instruction with comment."""
    text = "CP 5, R.a  ; Initialize counter"
    program = parse_program(text)

    assert len(program) == 1
    assert program[0].comment == "Initialize counter"  # type: ignore
    assert program[0] == I.CP(5, R.a)


def test_standalone_comment():
    """Test parsing standalone comment line."""
    text = "; This is a standalone comment"
    program = parse_program(text)

    assert len(program) == 1
    assert isinstance(program[0], Comment)
    assert program[0].comment == "This is a standalone comment"


def test_multiple_standalone_comments():
    """Test parsing multiple standalone comments."""
    text = """
    ; Comment 1
    ; Comment 2
    CP 5, R.a
    ; Comment 3
    """
    program = parse_program(text)

    assert len(program) == 4
    assert isinstance(program[0], Comment)
    assert isinstance(program[1], Comment)
    assert isinstance(program[3], Comment)
    assert program[0].comment == "Comment 1"
    assert program[1].comment == "Comment 2"
    assert program[3].comment == "Comment 3"


def test_comment_with_special_characters():
    """Test parsing comments with special characters."""
    text = "CP 5, R.a  ; Special chars: !@#$%^&*()[]{}|\\/?<>,.`~"
    program = parse_program(text)

    assert program[0].comment == "Special chars: !@#$%^&*()[]{}|\\/?<>,.`~"


def test_empty_comment():
    """Test parsing empty comment (just semicolon)."""
    text = "CP 5, R.a  ;"
    program = parse_program(text)

    assert program[0].comment == ""


def test_label_and_instruction_same_line_with_comment():
    """Test label and instruction on same line with comment."""
    text = "loop: CP 5, R.a  ; Initialize"
    program = parse_program(text)

    assert len(program) == 2
    assert isinstance(program[0], Label)
    assert program[0].name == "loop"
    assert program[0].comment == "Initialize"
    assert program[1].comment == "Initialize"


# ----------------------------- with_comment Method ------------------------------ #


def test_with_comment_method_instruction():
    """Test the with_comment() method on instructions."""
    inst = I.CP(5, R.a)
    commented_inst = inst.with_comment("Test comment")

    assert commented_inst.comment == "Test comment"
    assert commented_inst == inst  # Should be equal (comments excluded from equality)
    assert commented_inst is not inst  # Should be a new instance


def test_with_comment_method_label():
    """Test the with_comment() method on labels."""
    label = Label("loop")
    commented_label = label.with_comment("Loop start")

    assert commented_label.comment == "Loop start"
    assert commented_label == label
    assert commented_label is not label


# -------------------------------- Round-Tripping -------------------------------- #


def test_round_trip_with_comments():
    """Test that comments are preserved when converting text → Python → text."""
    original = """CP 5, R.a ; Initialize counter
loop: ; Main loop
    NOUT R.a, 1 ; Print value
    SUB R.a, 1
    JGT loop, R.a, 0"""

    # Parse to Python
    program = parse_program(original)

    # Convert back to text
    reconstructed = program_to_text(program)

    # Parse the reconstructed text
    re_parsed = parse_program(reconstructed)

    # Check that comments are preserved
    assert program[0].comment == re_parsed[0].comment
    assert program[1].comment == re_parsed[1].comment
    assert program[2].comment == re_parsed[2].comment


def test_round_trip_with_standalone_comments():
    """Test round-tripping with standalone comment lines."""
    original = """; Program start
CP 5, R.a
; This is a loop
loop:
    NOUT R.a, 1
; End of program"""

    program = parse_program(original)
    reconstructed = program_to_text(program)
    re_parsed = parse_program(reconstructed)

    # Check structure is preserved
    assert len(program) == len(re_parsed)
    for orig, reparsed in zip(program, re_parsed):
        if isinstance(orig, Comment):
            assert isinstance(reparsed, Comment)
            assert orig.comment == reparsed.comment
        elif isinstance(orig, Label):
            assert isinstance(reparsed, Label)
            assert orig.name == reparsed.name
            assert orig.comment == reparsed.comment
        else:
            assert type(orig) is type(reparsed)
            assert orig.comment == reparsed.comment


def test_program_to_text_with_comments():
    """Test program_to_text outputs comments correctly."""
    program = [
        Comment("Program start"),
        I.CP(5, R.a),
        Label("loop").with_comment("Main loop"),
        I.NOUT(R.a, L[1]).with_comment("Print"),
        I.SUB(R.a, L[1]),
        I.JGT(Label("loop"), R.a, L[0]),
    ]

    text = program_to_text(program)

    assert "; Program start" in text
    assert "loop: ; Main loop" in text
    assert "NOUT R.a, 1 ; Print" in text
    # SUB should not have comment
    assert "SUB R.a, 1, R.a" in text
    assert "SUB R.a, 1, R.a ;" not in text


def test_program_to_text_without_comments():
    """Test program_to_text works normally when no comments present."""
    program = [
        I.CP(5, R.a),
        Label("loop"),
        I.NOUT(R.a, L[1]),
    ]

    text = program_to_text(program)

    assert ";" not in text
    assert "CP 5, R.a" in text
    assert "loop:" in text


# -------------------------------- Comment Class --------------------------------- #


def test_comment_str():
    """Test Comment __str__ method."""
    comment = Comment("This is a comment")
    assert str(comment) == "; This is a comment"


def test_comment_repr():
    """Test Comment __repr__ method."""
    comment = Comment("This is a comment")
    assert repr(comment) == 'Comment("This is a comment")'


def test_comment_equality():
    """Test Comment equality."""
    c1 = Comment("Same text")
    c2 = Comment("Same text")
    c3 = Comment("Different text")

    assert c1 == c2
    assert c1 != c3
    assert c2 != c3


def test_comment_inequality_with_other_types():
    """Test Comment inequality with non-Comment objects."""
    comment = Comment("Test")

    assert comment != "Test"
    assert comment != Label("test")
    assert comment != I.CP(5, R.a)


# ----------------------------- Debug Output --------------------------------- #


def test_comments_in_debug_output(capsys):
    """Test that inline comments appear in debug output."""
    code = "CP 5, R.a  ; Initialize counter"

    program = parse_program(code)
    cpu = DT31()

    cpu.load(program)
    cpu.step(debug=True)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert lines[0] == "CP(a=5, b=R.a) -> 5  ; Initialize counter"


def test_no_comment_in_debug_output(capsys):
    """Test that instructions without comments don't show semicolons."""
    code = "CP 5, R.a"

    program = parse_program(code)
    cpu = DT31()

    cpu.load(program)
    cpu.step(debug=True)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert lines[0] == "CP(a=5, b=R.a) -> 5"
