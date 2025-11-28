import pytest

import dt31.instructions as I
from dt31 import DT31
from dt31.assembler import extract_registers_from_program
from dt31.formatter import program_to_text
from dt31.instructions import Instruction
from dt31.operands import LC, L, Label, M, R
from dt31.parser import (
    MEMORY_PATTERN,
    REGISTER_PREFIX_PATTERN,
    TOKEN_PATTERN,
    Comment,
    ParserError,
    parse_operand,
    parse_program,
)

# ----------------------------------- Token pattern ---------------------------------- #


def test_token_pattern_raw_basic():
    assert TOKEN_PATTERN.findall("CP 5, R.a") == ["CP", "5", "R.a"]
    assert TOKEN_PATTERN.findall("ADD a, b, c") == ["ADD", "a", "b", "c"]


def test_token_pattern_no_space():
    assert TOKEN_PATTERN.findall("XXX 5,R.a,',',' '") == [
        "XXX",
        "5",
        "R.a",
        "','",
        "' '",
    ]


def test_token_pattern_memory_references():
    assert TOKEN_PATTERN.findall("M[100]") == ["M[100]"]
    assert TOKEN_PATTERN.findall("[100]") == ["[100]"]
    assert TOKEN_PATTERN.findall("M[R.a]") == ["M[R.a]"]


def test_token_pattern_character_literals():
    assert TOKEN_PATTERN.findall("'H'") == ["'H'"]
    assert TOKEN_PATTERN.findall("OOUT 'A'") == ["OOUT", "'A'"]
    assert TOKEN_PATTERN.findall("CP 'x', R.a") == ["CP", "'x'", "R.a"]
    assert TOKEN_PATTERN.findall("CP 'x',R.a") == ["CP", "'x'", "R.a"]


def test_token_pattern_register_syntax():
    assert TOKEN_PATTERN.findall("CP R.a, R.B") == ["CP", "R.a", "R.B"]
    assert TOKEN_PATTERN.findall("CP R.foo,R.x") == ["CP", "R.foo", "R.x"]
    assert TOKEN_PATTERN.findall("R.my_reg") == ["R.my_reg"]


def test_token_pattern_complex_line():
    assert TOKEN_PATTERN.findall("ADD M[100], R.a, [R.b]") == [
        "ADD",
        "M[100]",
        "R.a",
        "[R.b]",
    ]


def test_token_pattern_negative_numbers():
    assert TOKEN_PATTERN.findall("CP -5, R.a") == ["CP", "-5", "R.a"]
    assert TOKEN_PATTERN.findall("ADD a, -10") == ["ADD", "a", "-10"]


def test_token_pattern_labels():
    assert TOKEN_PATTERN.findall("loop") == ["loop"]
    assert TOKEN_PATTERN.findall("JMP start") == ["JMP", "start"]


def test_token_pattern_whitespace_handling():
    assert TOKEN_PATTERN.findall("  CP   5  ,  R.a  ") == ["CP", "5", "R.a"]
    assert TOKEN_PATTERN.findall("\tADD\ta,\tb") == ["ADD", "a", "b"]


# ---------------------------------- Memory pattern ---------------------------------- #


def test_memory_pattern_basic():
    m = MEMORY_PATTERN.match("M[100]")
    assert m is not None
    assert m.group(1) == "100"


def test_memory_pattern_no_prefix():
    """Test matching memory references without M prefix."""
    m = MEMORY_PATTERN.match("[100]")
    assert m is not None
    assert m.group(1) == "100"


def test_memory_pattern_register_indirect():
    """Test matching indirect memory references with registers."""
    m = MEMORY_PATTERN.match("M[R.a]")
    assert m is not None
    assert m.group(1) == "R.a"


def test_memory_pattern_bare_register():
    """Test matching memory references with bare register names."""
    m = MEMORY_PATTERN.match("[a]")
    assert m is not None
    assert m.group(1) == "a"


def test_memory_pattern_complex():
    """Test matching complex memory references."""
    m = MEMORY_PATTERN.match("M[M[100]]")
    assert m is not None
    assert m.group(1) == "M[100]"

    m = MEMORY_PATTERN.match("[[R.a]]")
    assert m is not None
    assert m.group(1) == "[R.a]"

    m = MEMORY_PATTERN.match("[M[R.a]]")
    assert m is not None
    assert m.group(1) == "M[R.a]"

    m = MEMORY_PATTERN.match("[R.index]")
    assert m is not None
    assert m.group(1) == "R.index"


def test_memory_pattern_no_match():
    """Test that non-memory references don't match."""
    assert MEMORY_PATTERN.match("R.a") is None
    assert MEMORY_PATTERN.match("100") is None
    assert MEMORY_PATTERN.match("'A'") is None


# --------------------------------- Register pattern --------------------------------- #


def test_register_pattern_basic():
    """Test matching basic register references."""
    m = REGISTER_PREFIX_PATTERN.match("R.a")
    assert m is not None
    assert m.group(1) == "a"


def test_register_pattern_long_names():
    """Test matching registers with longer names."""
    m = REGISTER_PREFIX_PATTERN.match("R.foo")
    assert m is not None
    assert m.group(1) == "foo"

    m = REGISTER_PREFIX_PATTERN.match("R.my_register")
    assert m is not None
    assert m.group(1) == "my_register"


def test_register_pattern_alphanumeric():
    """Test matching registers with alphanumeric names."""
    m = REGISTER_PREFIX_PATTERN.match("R.reg1")
    assert m is not None
    assert m.group(1) == "reg1"

    m = REGISTER_PREFIX_PATTERN.match("R.r2d2")
    assert m is not None
    assert m.group(1) == "r2d2"


def test_register_pattern_no_match():
    """Test that non-register references don't match."""
    assert REGISTER_PREFIX_PATTERN.match("a") is None
    assert REGISTER_PREFIX_PATTERN.match("100") is None
    assert REGISTER_PREFIX_PATTERN.match("M[100]") is None
    assert REGISTER_PREFIX_PATTERN.match("'A'") is None


# --------------------------------- parse_operand -------------------------------- #


def test_parse_operand_numeric_literals():
    result = parse_operand("42")
    assert result == L[42]

    result = parse_operand("0")
    assert result == L[0]

    result = parse_operand("-5")
    assert result == L[-5]

    result = parse_operand("999")
    assert result == L[999]


def test_parse_operand_character_literals():
    result = parse_operand("'H'")
    assert result == LC["H"]

    result = parse_operand("'a'")
    assert result == LC["a"]

    result = parse_operand("' '")
    assert result == LC[" "]

    result = parse_operand("'0'")
    assert result == LC["0"]


def test_parse_operand_character_literal_errors():
    """Test that invalid character literals raise errors."""
    with pytest.raises(ParserError, match="Invalid character literal"):
        parse_operand("''")

    with pytest.raises(ParserError, match="Invalid character literal"):
        parse_operand("'abc'")

    with pytest.raises(ParserError, match="must contain exactly one character"):
        parse_operand("'ab'")


def test_parse_operand_registers_prefixed():
    """Test parsing R. prefixed register names."""
    result = parse_operand("R.a")
    assert result == R.a

    result = parse_operand("R.foo")
    assert result == R.foo

    result = parse_operand("R.my_register")
    assert result == R.my_register

    result = parse_operand("R.reg1")
    assert result == R.reg1


def test_parse_operand_memory_basic():
    """Test parsing basic memory references."""
    result = parse_operand("[100]")
    assert result == M[100]

    result = parse_operand("M[100]")
    assert result == M[100]

    result = parse_operand("[0]")
    assert result == M[0]


def test_parse_operand_memory_register_indirect():
    """Test parsing memory references with register indirection."""
    result = parse_operand("M[R.a]")
    assert result == M[R.a]

    result = parse_operand("[R.foo]")
    assert result == M[R.foo]

    result = parse_operand("[R.b]")
    assert result == M[R.b]


def test_parse_operand_memory_nested():
    """Test parsing nested memory references."""
    result = parse_operand("M[M[100]]")
    assert result == M[M[100]]

    result = parse_operand("[[R.a]]")
    assert result == M[M[R.a]]

    result = parse_operand("[M[R.a]]")
    assert result == M[M[R.a]]


def test_parse_operand_memory_with_label_error():
    """Test that labels cannot be used as memory addresses."""
    with pytest.raises(ParserError, match="Labels cannot be used as memory addresses"):
        parse_operand("[unknown_identifier]")

    with pytest.raises(ParserError, match="Labels cannot be used as memory addresses"):
        parse_operand("M[loop]")

    # Bare identifiers are now labels, so [a] should error
    with pytest.raises(ParserError, match="Labels cannot be used as memory addresses"):
        parse_operand("[a]")


def test_parse_operand_labels():
    result = parse_operand("loop")
    assert isinstance(result, Label)
    assert result.name == "loop"

    result = parse_operand("end_label")
    assert isinstance(result, Label)
    assert result.name == "end_label"

    result = parse_operand("a")
    assert isinstance(result, Label)
    assert result.name == "a"


# --------------------------------- parse_program -------------------------------- #


def test_parse_program_empty():
    """Test parsing empty program."""
    program = parse_program("")
    assert program == []


def test_parse_program_whitespace_only():
    """Test parsing program with only whitespace."""
    program = parse_program("   \n  \n\t\n  ")
    assert program == []


def test_parse_program_commas_only():
    """Test parsing program with lines containing only commas."""
    program = parse_program(",,,\n   ,,,   \nCP 5, R.a")
    expected = [I.CP(5, R.a)]
    assert program == expected


def test_parse_program_single_instruction():
    """Test parsing a single instruction."""
    program = parse_program("CP 5, R.a")
    expected = [I.CP(5, R.a)]
    assert program == expected


def test_parse_program_multiple_instructions():
    """Test parsing multiple instructions."""
    text = """
    CP 10, R.a
    CP 5, R.b
    ADD R.a, R.b
    NOUT R.a, 1
    """
    program = parse_program(text)
    expected = [
        I.CP(10, R.a),
        I.CP(5, R.b),
        I.ADD(R.a, R.b),
        I.NOUT(R.a, 1),
    ]
    assert program == expected


def test_parse_program_with_comments():
    """Test that comments are preserved correctly."""
    from dt31.parser import Comment

    text = """
    CP 5, R.a  ; This is a comment
    ; This entire line is a comment
    ADD R.a, 1 ; Another comment
    """
    program = parse_program(text)

    # Check that we have the right number and types of items
    assert len(program) == 3
    assert isinstance(program[0], type(I.CP(5, R.a)))
    assert isinstance(program[1], Comment)
    assert isinstance(program[2], type(I.ADD(R.a, 1)))

    # Check comments are attached
    assert program[0].comment == "This is a comment"
    assert program[1].comment == "This entire line is a comment"
    assert program[2].comment == "Another comment"

    # Check instructions are correct (excluding comments)
    assert program[0] == I.CP(5, R.a)
    assert program[2] == I.ADD(R.a, 1)


def test_parse_program_label_only_line():
    """Test parsing labels on their own line."""
    text = """
    CP 1, R.a
    loop:
    NOUT R.a, 1
    ADD R.a, 1
    JGT loop, R.a, 10
    """
    program = parse_program(text)
    expected = [
        I.CP(1, R.a),
        Label("loop"),
        I.NOUT(R.a, 1),
        I.ADD(R.a, 1),
        I.JGT(Label("loop"), R.a, 10),
    ]
    assert program == expected


def test_parse_program_label_with_instruction():
    """Test parsing label on same line as instruction."""
    text = """
    CP 1, R.a
    loop: NOUT R.a, 1
    ADD R.a, 1
    JGT loop, R.a, 10
    """
    program = parse_program(text)
    expected = [
        I.CP(1, R.a),
        Label("loop"),
        I.NOUT(R.a, 1),
        I.ADD(R.a, 1),
        I.JGT(Label("loop"), R.a, 10),
    ]
    assert program == expected


def test_parse_program_multiple_labels():
    """Test parsing multiple labels."""
    text = """
    start:
    CP 0, R.a
    loop:
    NOUT R.a, 1
    ADD R.a, 1
    JGT loop, R.a, 5
    end:
    """
    program = parse_program(text)
    labels = [item for item in program if isinstance(item, Label)]
    assert len(labels) == 3
    assert labels[0].name == "start"
    assert labels[1].name == "loop"
    assert labels[2].name == "end"


def test_parse_program_multiple_labels_on_same_line():
    """Test parsing multiple labels on the same line."""
    text = "foo: bar: baz: CP R.a, R.b"
    program = parse_program(text)
    assert len(program) == 4
    assert isinstance(program[0], Label)
    assert program[0].name == "foo"
    assert isinstance(program[1], Label)
    assert program[1].name == "bar"
    assert isinstance(program[2], Label)
    assert program[2].name == "baz"
    assert isinstance(program[3], I.CP)


def test_parse_program_multiple_labels_with_comment():
    """Test that comment is attached only to the last label."""
    text = "foo: bar: baz: CP R.a, R.b ; test comment"
    program = parse_program(text)
    assert len(program) == 4
    # First two labels should have no comment
    assert program[0].comment == ""
    assert program[1].comment == ""
    # Last label should have the comment
    assert program[2].comment == "test comment"
    # Instruction should also have the comment
    assert program[3].comment == "test comment"


def test_parse_program_multiple_labels_no_instruction():
    """Test multiple labels with no instruction after."""
    text = "foo: bar: baz:"
    program = parse_program(text)
    assert len(program) == 3
    assert isinstance(program[0], Label)
    assert program[0].name == "foo"
    assert isinstance(program[1], Label)
    assert program[1].name == "bar"
    assert isinstance(program[2], Label)
    assert program[2].name == "baz"


def test_parse_program_label_validation_valid():
    """Test that valid label names are accepted."""
    text = """
    valid_label:
    loop123:
    _underscore:
    CamelCase:
    """
    program = parse_program(text)
    labels = [item for item in program if isinstance(item, Label)]
    assert len(labels) == 4
    assert labels[0].name == "valid_label"
    assert labels[1].name == "loop123"
    assert labels[2].name == "_underscore"
    assert labels[3].name == "CamelCase"


def test_parse_program_label_validation_invalid():
    """Test that invalid label names raise errors."""
    with pytest.raises(ParserError, match="Invalid label name"):
        parse_program("invalid-label:")

    with pytest.raises(ParserError, match="Invalid label name"):
        parse_program("label with spaces:")

    with pytest.raises(ParserError, match="Invalid label name"):
        parse_program("label!:")


def test_parse_program_character_literals():
    """Test parsing character literals in instructions."""
    text = """
    OOUT 'H', 0
    OOUT 'i', 0
    OOUT '!', 0
    """
    program = parse_program(text)
    expected = [
        I.OOUT(LC["H"], 0),
        I.OOUT(LC["i"], 0),
        I.OOUT(LC["!"], 0),
    ]
    assert program == expected


def test_parse_program_memory_references():
    """Test parsing various memory reference formats."""
    text = """
    CP 100, M[50]
    CP M[50], R.a
    CP M[R.a], R.b
    CP R.a, [100]
    """
    program = parse_program(text)
    expected = [
        I.CP(100, M[50]),
        I.CP(M[50], R.a),
        I.CP(M[R.a], R.b),
        I.CP(R.a, M[100]),
    ]
    assert program == expected


def test_parse_program_mixed_operands():
    """Test parsing instructions with various operand types."""
    text = """
    CP 42, R.a
    CP R.a, M[100]
    ADD R.a, 10
    JMP loop
    OOUT 'X', 0
    """
    program = parse_program(text)
    expected = [
        I.CP(42, R.a),
        I.CP(R.a, M[100]),
        I.ADD(R.a, 10),
        I.JMP(Label("loop")),
        I.OOUT(LC["X"], 0),
    ]
    assert program == expected


def test_parse_program_case_insensitive_instructions():
    """Test that instruction names are case insensitive."""
    text = """
    cp 5, R.a
    ADD R.a, 1
    Nout R.a, 1
    """
    program = parse_program(text)
    expected = [
        I.CP(5, R.a),
        I.ADD(R.a, 1),
        I.NOUT(R.a, 1),
    ]
    assert program == expected


def test_parse_program_no_spaces_after_commas():
    """Test parsing instructions without spaces after commas."""
    text = "CP 5,R.a\nADD R.a,R.b"
    program = parse_program(text)
    expected = [
        I.CP(5, R.a),
        I.ADD(R.a, R.b),
    ]
    assert program == expected


def test_parse_program_negative_numbers():
    """Test parsing negative number literals."""
    text = """
    CP -5, R.a
    ADD R.a, -10
    SUB R.a, -3
    """
    program = parse_program(text)
    expected = [
        I.CP(-5, R.a),
        I.ADD(R.a, -10),
        I.SUB(R.a, -3),
    ]
    assert program == expected


def test_parse_program_unknown_instruction():
    """Test that unknown instructions raise errors."""
    with pytest.raises(ParserError, match="Unknown instruction 'INVALID'"):
        parse_program("INVALID R.a, R.b")


def test_parse_program_wrong_operand_count():
    """Test that wrong operand count raises errors."""
    # CP requires at least 1 operand (a, with optional out)
    # But passing 0 operands should fail
    with pytest.raises(ParserError, match="Error creating instruction"):
        parse_program("CP")

    # ADD with only 1 operand should fail
    with pytest.raises(ParserError, match="Error creating instruction"):
        parse_program("ADD R.a")


def test_parse_program_invalid_operand_syntax():
    """Test that invalid operand syntax raises errors."""
    with pytest.raises(ParserError, match="Labels cannot be used as memory addresses"):
        parse_program("CP [invalid_label], R.a")


def test_parse_program_custom_instructions():
    """Test parsing with custom instruction definitions."""

    class CUSTOM(Instruction):
        def __init__(self, x: int, y: int):
            super().__init__("CUSTOM")
            self.x = x
            self.y = y

        def _calc(self, cpu) -> int:
            return 0

    text = """
    CUSTOM 10, 20
    CP 5, R.a
    """
    program = parse_program(text, custom_instructions={"CUSTOM": CUSTOM})
    assert len(program) == 2
    assert program[0].name == "CUSTOM"
    assert program[1].name == "CP"


def test_parse_program_custom_instructions_override():
    """Test that custom instructions can override built-ins."""

    class CUSTOM_CP(Instruction):
        def __init__(self, x: int):
            super().__init__("CUSTOM_CP")
            self.x = x

        def _calc(self, cpu) -> int:
            return 0

    text = "CP 42"
    program = parse_program(text, custom_instructions={"CP": CUSTOM_CP})
    assert len(program) == 1
    assert program[0].name == "CUSTOM_CP"


def test_parse_program_line_numbers_in_errors():
    """Test that error messages include line numbers."""
    text = """
    CP 5, R.a
    INVALID R.a, R.b
    ADD R.a, 1
    """
    with pytest.raises(ParserError, match="Line 3:"):
        parse_program(text)


def test_parse_program_complete_loop_example():
    """Test parsing a complete program with loop."""
    text = """
    CP 1, R.a
    loop:
        NOUT R.a, 1
        ADD R.a, 1
        JGT loop, R.a, 11
    """
    program = parse_program(text)
    expected = [
        I.CP(1, R.a),
        Label("loop"),
        I.NOUT(R.a, 1),
        I.ADD(R.a, 1),
        I.JGT(Label("loop"), R.a, 11),
    ]
    assert program == expected


def test_parse_program_function_call_example():
    """Test parsing a program with function calls."""
    text = """
    CALL print_hi
    JMP end

    print_hi:
        OOUT 'H', 0
        OOUT 'i', 0
        RET

    end:
    """
    program = parse_program(text)
    expected = [
        I.CALL(Label("print_hi")),
        I.JMP(Label("end")),
        Label("print_hi"),
        I.OOUT(LC["H"], 0),
        I.OOUT(LC["i"], 0),
        I.RET(),
        Label("end"),
    ]
    assert program == expected


# ------------------------------- Round-trip test -------------------------------- #


def test_round_trip_comprehensive():
    """Test comprehensive round-trip: text → parse → to_text → parse with all features."""
    original = """; Countdown program
CP 5, R.a ; Initialize counter
loop: ; Main loop
    NOUT R.a, 1 ; Print value
    SUB R.a, 1
    JGT loop, R.a, 0
; Done"""

    # Parse original
    program = parse_program(original)

    # Verify structure
    assert len(program) == 7
    assert isinstance(program[0], Comment)
    assert program[0].comment == "Countdown program"
    assert program[1].comment == "Initialize counter"
    assert isinstance(program[2], Label)
    assert program[2].comment == "Main loop"
    assert program[3].comment == "Print value"
    assert isinstance(program[6], Comment)

    # Convert to text
    reconstructed = program_to_text(program)

    # Re-parse
    re_parsed = parse_program(reconstructed)

    # Verify round-trip preserves structure and comments
    assert len(program) == len(re_parsed)
    for orig, reparsed in zip(program, re_parsed):
        assert type(orig) is type(reparsed)
        if isinstance(orig, Comment):
            assert orig.comment == reparsed.comment
        elif isinstance(orig, Label):
            assert orig.name == reparsed.name
            assert orig.comment == reparsed.comment
        else:
            assert orig == reparsed
            assert orig.comment == reparsed.comment

    # Verify programs execute identically
    registers = extract_registers_from_program(program)
    cpu1 = DT31(registers=registers)
    cpu1.run(program)
    result1 = cpu1.get_register("a")

    cpu2 = DT31(registers=registers)
    cpu2.run(re_parsed)
    result2 = cpu2.get_register("a")

    assert result1 == result2 == 0


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
    assert "loop:  ; Main loop" in text  # 2 spaces (default margin)
    assert "NOUT R.a, 1  ; Print" in text  # 2 spaces (default margin)
    # SUB should not have comment (default arg hidden)
    assert "SUB R.a, 1" in text
    assert "SUB R.a, 1 ;" not in text


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
