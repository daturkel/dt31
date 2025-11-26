import pytest

from dt31.operands import (
    LC,
    L,
    Label,
    Literal,
    M,
    MemoryReference,
    Operand,
    R,
    RegisterReference,
    as_op,
)


def test_bare_operand(cpu):
    with pytest.raises(NotImplementedError):
        o = Operand()
        o.resolve(cpu)


def test_l_shorthand():
    l1 = L[3]
    l2 = Literal(3)
    assert isinstance(l1, Literal)
    assert l1.value == l2.value


def test_m_shorthand():
    assert repr(M[3]) == "M[3]"
    assert str(M[3]) == "[3]"
    assert repr(M[M[3]]) == "M[M[3]]"
    assert str(M[M[3]]) == "[[3]]"
    m1 = M[3]
    m2 = MemoryReference(3)
    assert isinstance(m1, MemoryReference)
    assert m1.address == m2.address
    m3 = M[M[2]]
    assert isinstance(m3, MemoryReference)
    assert isinstance(m3.address, MemoryReference)
    assert m3.address.address == 2


def test_r_shorthand():
    assert repr(R.a) == "R.a"
    assert str(R.a) == "R.a"  # Same in both formats
    r1 = R.a
    r2 = R.a
    r3 = RegisterReference("a")
    assert isinstance(r1, RegisterReference)
    assert isinstance(r2, RegisterReference)
    assert r1.register == r2.register == r3.register


def test_resolve_address(cpu):
    m1 = M[2]
    assert m1.resolve_address(cpu) == 2
    cpu.set_register("a", 1)
    m2 = M[R.a]
    assert m2.resolve_address(cpu) == 1
    assert m2.resolve(cpu) == 10


def test_as_op():
    o1 = as_op(4)
    assert isinstance(o1, Literal)
    assert o1.value == 4
    o2 = as_op(M[2])
    assert isinstance(o2, MemoryReference)
    assert o2.address == L[2]
    o3 = as_op(R.a)
    assert isinstance(o3, RegisterReference)
    assert o3.register == "a"
    with pytest.raises(ValueError):
        as_op("asd")  # type: ignore


def test_literal_equality():
    a = L[2]
    b = L[2]
    assert a == b
    assert a == 2
    c = L[3]
    assert c != b
    assert c != 2
    assert a != "2"


def test_lc_shorthand():
    lc1 = LC["A"]
    l1 = Literal(65)
    assert isinstance(lc1, Literal)
    assert lc1.value == l1.value
    assert lc1.value == ord("A")


def test_lc_equality():
    assert LC["A"] == 65
    assert LC["A"] == L[65]
    assert LC["A"] == Literal(65)


def test_lc_invalid_input():
    with pytest.raises(ValueError, match="LC requires a single character"):
        LC[""]
    with pytest.raises(ValueError, match="LC requires a single character"):
        LC["ab"]
    with pytest.raises(ValueError, match="LC requires a single character"):
        LC[123]  # type: ignore


def test_lc_str_repr():
    """Test that character literals render correctly in str and repr."""
    lc = LC["A"]
    assert repr(lc) == "65"
    assert str(lc) == "'A'"

    lc2 = LC["z"]
    assert repr(lc2) == "122"
    assert str(lc2) == "'z'"


def test_literal_str_repr():
    """Test that numeric literals render correctly in str and repr."""
    lit = L[42]
    assert repr(lit) == "42"
    assert str(lit) == "42"

    lit2 = L[-5]
    assert repr(lit2) == "-5"
    assert str(lit2) == "-5"


def test_is_char_flag():
    """Test that is_char flag is set correctly for L vs LC."""
    # Numeric literals created with L should NOT have is_char set
    l_numeric = L[65]
    assert l_numeric.is_char is False
    assert str(l_numeric) == "65"  # Renders as number

    # Character literals created with LC SHOULD have is_char set
    lc_char = LC["A"]
    assert lc_char.is_char is True
    assert str(lc_char) == "'A'"  # Renders as character

    # Even though they have the same value, they render differently
    assert l_numeric.value == lc_char.value == 65
    assert str(l_numeric) != str(lc_char)


def test_label_init():
    label = Label("my_function")
    assert label.name == "my_function"
    assert repr(label) == "my_function"
    assert str(label) == "my_function"  # Same in both formats


def test_label_resolve_raises_error(cpu):
    label = Label("unresolved_label")
    with pytest.raises(RuntimeError, match="Unresolved label 'unresolved_label'"):
        label.resolve(cpu)
    with pytest.raises(RuntimeError, match="must be assembled using assemble"):
        label.resolve(cpu)
    with pytest.raises(
        RuntimeError, match="can only be used as jump/call destinations"
    ):
        label.resolve(cpu)


def test_label_str():
    label1 = Label("start")
    assert repr(label1) == "start"
    assert str(label1) == "start"  # Same in both formats
    label2 = Label("loop_begin")
    assert repr(label2) == "loop_begin"
    assert str(label2) == "loop_begin"


def test_memory_reference_equality():
    m1 = M[5]
    m2 = M[5]
    m3 = M[10]
    assert m1 == m2
    assert m1 != m3
    # Test nested memory references
    m4 = M[M[2]]
    m5 = M[M[2]]
    m6 = M[M[3]]
    assert m4 == m5
    assert m4 != m6
    # Test memory references with register addresses
    m7 = M[R.a]
    m8 = M[R.a]
    m9 = M[R.b]
    assert m7 == m8
    assert m7 != m9


def test_register_reference_equality():
    r1 = R.a
    r2 = R.a
    r3 = R.b
    assert r1 == r2
    assert r1 != r3
    assert r1 != "a"


def test_label_equality():
    l1 = Label("start")
    l2 = Label("start")
    l3 = Label("end")
    assert l1 == l2
    assert l1 != l3
    assert l1 != "start"


def test_register_name_validation_valid():
    """Test that valid register names are accepted."""
    # Valid identifiers
    R.a
    R.b
    R.my_register
    R.reg123
    R._private
    R.CamelCase

    # Direct construction
    RegisterReference("valid_name")
    RegisterReference("x")
    RegisterReference("_underscore")


def test_register_name_validation_invalid_identifier():
    """Test that invalid Python identifiers are rejected."""
    with pytest.raises(ValueError, match="Invalid register name"):
        RegisterReference("123")

    with pytest.raises(ValueError, match="Invalid register name"):
        RegisterReference("my-register")

    with pytest.raises(ValueError, match="Invalid register name"):
        RegisterReference("my.register")

    with pytest.raises(ValueError, match="Invalid register name"):
        RegisterReference("my register")

    with pytest.raises(ValueError, match="Invalid register name"):
        RegisterReference("")


def test_register_name_validation_dunder():
    """Test that double underscore names are rejected."""
    with pytest.raises(ValueError, match="cannot start with double underscores"):
        RegisterReference("__dunder__")

    with pytest.raises(ValueError, match="cannot start with double underscores"):
        RegisterReference("__init__")

    with pytest.raises(ValueError, match="cannot start with double underscores"):
        RegisterReference("__name")

    # Single underscore should be fine
    RegisterReference("_single")


def test_register_name_validation_via_r_shorthand():
    """Test that validation works when using R.name syntax."""
    # Valid names should work
    assert isinstance(R.valid, RegisterReference)
    assert isinstance(R._private, RegisterReference)

    # Dunder names are intercepted by __getattribute__ before validation
    # so they don't trigger ValueError but return the actual dunder method
    # This is intentional to avoid breaking metaclass behavior


def test_with_comment_method_label():
    """Test the with_comment() method on labels."""
    label = Label("loop")
    commented_label = label.with_comment("Loop start")

    assert commented_label.comment == "Loop start"
    assert commented_label == label
    assert commented_label is not label
