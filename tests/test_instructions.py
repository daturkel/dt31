from collections import deque
from copy import copy

import pytest

from dt31 import instructions as I
from dt31.operands import L, M, MemoryReference, R


def test_bare_instruction(cpu):
    with pytest.raises(NotImplementedError):
        I.Instruction("foo")(cpu)


def test_noop(cpu):
    memory = copy(cpu.memory)
    registers = {r: copy(cpu.get_register(r)) for r in cpu.registers}
    registers["ip"] += 1
    assert I.NOOP()(cpu) == 0
    assert cpu.memory == memory
    assert cpu.registers == registers


def test_unary_operation_advances_one(cpu):
    I.NOT(1, M[10])(cpu)
    assert cpu.get_register("ip") == 1
    I.NOT(1, M[10])(cpu)
    assert cpu.get_register("ip") == 2


def test_unary_operation_writes_memory(cpu):
    I.BNOT(1, M[10])(cpu)
    assert cpu.get_memory(10) == -2


def test_unary_operation_writes_register(cpu):
    I.BNOT(1, R["a"])(cpu)
    assert cpu.get_register("a") == -2


def test_unary_operation_validates_types(cpu):
    with pytest.raises(ValueError) as e1:
        I.BNOT(1, L[1])
    assert "must be a Reference or None" in str(e1.value)
    with pytest.raises(ValueError) as e2:
        I.BNOT(1)  # type: ignore
    assert "must be called with a reference as" in str(e2.value)


def test_unary_operation_writes_to_default_register(cpu):
    I.BNOT(R["a"])(cpu)
    assert cpu.get_register("a") == -31


def test_unary_operation_writes_to_default_memory(cpu):
    I.BNOT(M[1])(cpu)
    assert cpu.get_memory(1) == -11


def test_binary_operation_advances_one(cpu):
    I.ADD(1, 1, M[10])(cpu)
    assert cpu.get_register("ip") == 1
    I.ADD(1, 1, M[10])(cpu)
    assert cpu.get_register("ip") == 2


def test_binary_operation_writes_memory(cpu):
    I.ADD(1, 1, M[10])(cpu)
    assert cpu.get_memory(10) == 2


def test_binary_operation_writes_register(cpu):
    I.ADD(1, 1, R["a"])(cpu)
    assert cpu.get_register("a") == 2


def test_binary_operation_validates_types(cpu):
    with pytest.raises(ValueError) as e1:
        I.ADD(1, 1, L[1])
    assert "must be a Reference or None" in str(e1.value)
    with pytest.raises(ValueError) as e2:
        I.ADD(1, 1)
    assert "must be called with a reference as" in str(e2.value)


def test_binary_operation_writes_to_default_register(cpu):
    I.ADD(R["a"], 2)(cpu)
    assert cpu.get_register("a") == 32


def test_binary_operation_writes_to_default_memory(cpu):
    I.ADD(M[1], 2)(cpu)
    assert cpu.get_memory(1) == 12


def test_add(cpu):
    assert I.ADD(1, 3, M[10])(cpu) == 4


def test_sub(cpu):
    assert I.SUB(3, 2, M[10])(cpu) == 1


def test_mul(cpu):
    assert I.MUL(2, 4, M[10])(cpu) == 8


def test_div(cpu):
    assert I.DIV(5, 2, M[10])(cpu) == 2


def test_mod(cpu):
    assert I.MOD(5, 3, M[10])(cpu) == 2


def test_bsl(cpu):
    assert I.BSL(5, 2, M[10])(cpu) == 20


def test_bsr(cpu):
    assert I.BSR(19, 2, M[10])(cpu) == 4


def test_band(cpu):
    assert I.BAND(29, 23, M[10])(cpu) == 21


def test_bor(cpu):
    assert I.BOR(29, 23, M[10])(cpu) == 31


def test_bxor(cpu):
    assert I.BXOR(29, 23, M[10])(cpu) == 10


def test_bnot(cpu):
    assert I.BNOT(29, M[10])(cpu) == -30


def test_lt(cpu):
    assert I.LT(30, 20, M[10])(cpu) == 0
    assert I.LT(20, 30, M[10])(cpu) == 1
    assert I.LT(20, 20, M[10])(cpu) == 0


def test_gt(cpu):
    assert I.GT(30, 20, M[10])(cpu) == 1
    assert I.GT(20, 30, M[10])(cpu) == 0
    assert I.GT(20, 20, M[10])(cpu) == 0


def test_leq(cpu):
    assert I.LE(30, 20, M[10])(cpu) == 0
    assert I.LE(20, 30, M[10])(cpu) == 1
    assert I.LE(20, 20, M[10])(cpu) == 1


def test_geq(cpu):
    assert I.GE(30, 20, M[10])(cpu) == 1
    assert I.GE(20, 30, M[10])(cpu) == 0
    assert I.GE(20, 20, M[10])(cpu) == 1


def test_eq(cpu):
    assert I.EQ(30, 30, M[10])(cpu) == 1
    assert I.EQ(30, 31, M[10])(cpu) == 0


def test_neq(cpu):
    assert I.NE(30, 30, M[10])(cpu) == 0
    assert I.NE(30, 31, M[10])(cpu) == 1


def test_and(cpu):
    assert I.AND(0, 1, M[10])(cpu) == 0
    assert I.AND(1, 0, M[10])(cpu) == 0
    assert I.AND(0, 0, M[10])(cpu) == 0
    assert I.AND(1, 1, M[10])(cpu) == 1
    assert I.AND(-1, 1, M[10])(cpu) == 1


def test_or(cpu):
    assert I.OR(0, 1, M[10])(cpu) == 1
    assert I.OR(0, 0, M[10])(cpu) == 0
    assert I.OR(1, 1, M[10])(cpu) == 1
    assert I.OR(1, -1, M[10])(cpu) == 1


def test_xor(cpu):
    assert I.XOR(0, 1, M[10])(cpu) == 1
    assert I.XOR(0, 0, M[10])(cpu) == 0
    assert I.XOR(1, 1, M[10])(cpu) == 0
    assert I.XOR(1, 0, M[10])(cpu) == 1
    assert I.XOR(-1, 1, M[10])(cpu) == 0


def test_not(cpu):
    assert I.NOT(10, M[10])(cpu) == 0
    assert I.NOT(0, M[10])(cpu) == 1
    assert I.NOT(-1, M[10])(cpu) == 0


def test_jump(cpu):
    inst = I.Jump("foo", M[10])
    assert isinstance(inst.dest, MemoryReference)
    assert inst.dest.address == 10
    with pytest.raises(NotImplementedError):
        I.Jump("foo", M[10])(cpu)

    with pytest.raises(NotImplementedError):
        inst = I.Jump("foo", M[10])
        inst._jump_condition = lambda x: True  # type: ignore
        inst(cpu)


def test_binary_jump_sets_a_and_b(cpu):
    inst = I.BinaryJump("foo", M[13], M[10], M[2])
    assert isinstance(inst.a, MemoryReference)
    assert inst.a.address == 10
    assert isinstance(inst.b, MemoryReference)
    assert inst.b.address == 2


def test_jmp(cpu):
    I.JMP(10)(cpu)
    assert cpu.get_register("ip") == 10


def test_rjmp(cpu):
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 2
    I.RJMP(10)(cpu)
    assert cpu.get_register("ip") == 12


def test_jeq(cpu):
    assert cpu.get_register("ip") == 0
    I.JEQ(M[1], 30, R.a)(cpu)
    assert cpu.get_register("ip") == 10
    I.JEQ(M[1], 31, R.a)(cpu)
    assert cpu.get_register("ip") == 11


def test_rjeq(cpu):
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 2
    I.RJEQ(M[1], 30, R.a)(cpu)
    assert cpu.get_register("ip") == 12
    I.RJEQ(M[1], 31, R.a)(cpu)
    assert cpu.get_register("ip") == 13


def test_jne(cpu):
    assert cpu.get_register("ip") == 0
    I.JNE(M[1], 30, R.a)(cpu)
    assert cpu.get_register("ip") == 1
    I.JNE(M[1], 31, R.a)(cpu)
    assert cpu.get_register("ip") == 10


def test_rjne(cpu):
    assert cpu.get_register("ip") == 0
    I.RJNE(M[1], 30, R.a)(cpu)
    assert cpu.get_register("ip") == 1
    I.RJNE(M[1], 31, R.a)(cpu)
    assert cpu.get_register("ip") == 11


def test_jif(cpu):
    assert str(I.JIF(M[1], 2)) == "JIF(dest=M[1], a=2)"
    assert cpu.get_register("ip") == 0
    I.JIF(M[1], 2)(cpu)
    assert cpu.get_register("ip") == 10
    I.JIF(M[2], 0)(cpu)
    assert cpu.get_register("ip") == 11


def test_rjif(cpu):
    assert cpu.get_register("ip") == 0
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 2
    I.RJIF(M[1], 2)(cpu)
    assert cpu.get_register("ip") == 12
    I.RJIF(M[2], 0)(cpu)
    assert cpu.get_register("ip") == 13


def test_jgt(cpu):
    assert cpu.get_register("ip") == 0
    I.JGT(M[1], 3, 2)(cpu)
    assert cpu.get_register("ip") == 10
    I.JGT(M[2], 2, 2)(cpu)
    assert cpu.get_register("ip") == 11


def test_rjgt(cpu):
    assert cpu.get_register("ip") == 0
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 2
    I.RJGT(M[1], 3, 2)(cpu)
    assert cpu.get_register("ip") == 12
    I.RJGT(M[2], 2, 2)(cpu)
    assert cpu.get_register("ip") == 13


def test_jge(cpu):
    assert cpu.get_register("ip") == 0
    I.JGE(M[1], 3, 2)(cpu)
    assert cpu.get_register("ip") == 10
    I.JGE(M[2], 2, 2)(cpu)
    assert cpu.get_register("ip") == 20
    I.JGE(R.a, 1, 2)(cpu)
    assert cpu.get_register("ip") == 21


def test_rjge(cpu):
    assert cpu.get_register("ip") == 0
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 2
    I.RJGE(M[1], 3, 2)(cpu)
    assert cpu.get_register("ip") == 12
    I.RJGE(M[2], 2, 2)(cpu)
    assert cpu.get_register("ip") == 32
    I.RJGE(R.a, 1, 2)(cpu)
    assert cpu.get_register("ip") == 33


def test_push_pop(cpu):
    assert str(I.PUSH(2)) == "PUSH(a=2)"
    assert str(I.POP()) == "POP(out=None)"
    I.PUSH(2)(cpu)
    assert cpu.stack == deque([2])
    I.PUSH(M[1])(cpu)
    assert cpu.stack == deque([2, 10])
    I.PUSH(R.a)(cpu)
    assert cpu.stack == deque([2, 10, 30])
    I.PUSH(M[R.a])(cpu)
    assert cpu.stack == deque([2, 10, 30, 0])
    I.POP(M[20])(cpu)
    assert M[20].resolve(cpu) == 0
    assert cpu.stack == deque([2, 10, 30])
    I.POP(M[20])(cpu)
    assert M[20].resolve(cpu) == 30
    assert cpu.stack == deque([2, 10])
    I.POP(M[20])(cpu)
    assert M[20].resolve(cpu) == 10
    assert cpu.stack == deque([2])
    I.POP()(cpu)
    assert M[20].resolve(cpu) == 10
    assert cpu.stack == deque([])


def test_cp(cpu):
    assert str(str(I.CP(2, M[10]))) == "CP(a=2, out=M[10])"
    assert I.CP(2, M[10])(cpu) == 2
    assert cpu.get_memory(10) == 2
    assert I.CP(R.a, M[20])(cpu) == 30
    assert cpu.get_memory(20) == 30
    assert I.CP(M[M[2]], M[M[5]])(cpu) == 30
    assert cpu.get_memory(0) == 30
    assert I.CP(M[10], R.b)(cpu) == 2
    assert cpu.get_register("b") == 2


def test_nout_no_newline(cpu, capsys):
    assert str(I.NOUT(L[1])) == "NOUT(a=1, b=0)"
    assert I.NOUT(L[2])(cpu) == 0
    captured = capsys.readouterr()
    assert captured.out == "2"


def test_nout_newline(cpu, capsys):
    assert str(I.NOUT(L[2], L[1])) == "NOUT(a=2, b=1)"
    assert I.NOUT(L[2], L[1])(cpu) == 0
    captured = capsys.readouterr()
    assert captured.out == "2\n"


def test_oout_no_newline(cpu, capsys):
    assert str(I.OOUT(L[1])) == "OOUT(a=1, b=0)"
    assert I.OOUT(L[65])(cpu) == 0
    captured = capsys.readouterr()
    assert captured.out == "A"


def test_oout_newline(cpu, capsys):
    assert str(I.OOUT(L[2], L[1])) == "OOUT(a=2, b=1)"
    assert I.OOUT(L[65], L[1])(cpu) == 0
    captured = capsys.readouterr()
    assert captured.out == "A\n"


def test_nin(cpu, monkeypatch):
    assert str(I.NIN(M[10])) == "NIN(out=M[10])"
    monkeypatch.setattr("builtins.input", lambda: "31")
    assert I.NIN(R["a"])(cpu) == 31
    assert cpu.get_register("a") == 31


def test_oin(cpu, monkeypatch):
    assert str(I.OIN(M[10])) == "OIN(out=M[10])"
    monkeypatch.setattr("builtins.input", lambda: "A")
    assert I.OIN(R["a"])(cpu) == 65
    assert cpu.get_register("a") == 65


def test_semp(cpu):
    assert I.SEMP(M[0])(cpu) == 1
    assert cpu.get_memory(0) == 1
    I.PUSH(2)(cpu)
    assert I.SEMP(M[0])(cpu) == 0
    assert cpu.get_memory(0) == 0
    I.POP()(cpu)
    assert I.SEMP(M[0])(cpu) == 1
    assert cpu.get_memory(0) == 1
    assert str(I.SEMP(M[10])) == "SEMP(out=M[10])"
