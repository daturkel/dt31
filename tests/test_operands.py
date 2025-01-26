import pytest

from dt31.operands import (
    L,
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
    m1 = M[3]
    m2 = MemoryReference(3)
    assert isinstance(m1, MemoryReference)
    assert m1.address == m2.address
    m3 = M[M[2]]
    assert isinstance(m3, MemoryReference)
    assert isinstance(m3.address, MemoryReference)
    assert m3.address.address == 2


def test_r_shorthand():
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
    assert o2.address == 2
    o3 = as_op(R.a)
    assert isinstance(o3, RegisterReference)
    assert o3.register == "a"
    with pytest.raises(ValueError):
        as_op("asd")  # type: ignore
