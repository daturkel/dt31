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
    assert str(M[3]) == "M[3]"
    assert str(M[M[3]]) == "M[M[3]]"
    m1 = M[3]
    m2 = MemoryReference(3)
    assert isinstance(m1, MemoryReference)
    assert m1.address == m2.address
    m3 = M[M[2]]
    assert isinstance(m3, MemoryReference)
    assert isinstance(m3.address, MemoryReference)
    assert m3.address.address == 2


def test_r_shorthand():
    assert str(R["a"]) == "R[a]"
    r1 = R["a"]
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


def test_label_init():
    label = Label("my_function")
    assert label.name == "my_function"
    assert str(label) == "my_function"


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
    assert str(label1) == "start"
    label2 = Label("loop_begin")
    assert str(label2) == "loop_begin"
