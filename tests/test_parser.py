from dt31.parser import (
    MEMORY_PATTERN,
    REGISTER_PREFIX_PATTERN,
    TOKEN_PATTERN,
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
