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
    I.BNOT(1, R.a)(cpu)
    assert cpu.get_register("a") == -2


def test_unary_operation_validates_types(cpu):
    with pytest.raises(ValueError) as e1:
        I.BNOT(1, L[1])  # type: ignore
    assert "must be a Reference or None" in str(e1.value)
    with pytest.raises(ValueError) as e2:
        I.BNOT(1)  # type: ignore
    assert "must be called with a reference as" in str(e2.value)


def test_unary_operation_writes_to_default_register(cpu):
    I.BNOT(R.a)(cpu)
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
    I.ADD(1, 1, R.a)(cpu)
    assert cpu.get_register("a") == 2


def test_binary_operation_validates_types(cpu):
    with pytest.raises(ValueError) as e1:
        I.ADD(1, 1, L[1])  # type: ignore
    assert "must be a Reference or None" in str(e1.value)
    with pytest.raises(ValueError) as e2:
        I.ADD(1, 1)
    assert "must be called with a reference as" in str(e2.value)


def test_binary_operation_writes_to_default_register(cpu):
    I.ADD(R.a, 2)(cpu)
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
    assert str(inst) == "foo(dest=M[10])"
    with pytest.raises(NotImplementedError):
        I.Jump("foo", M[10])(cpu)

    with pytest.raises(NotImplementedError):
        inst = I.Jump("foo", M[10])
        inst._jump_condition = lambda x: True  # type: ignore
        inst(cpu)


def test_jump_with_label(cpu):
    from dt31.operands import Label

    label = Label("my_label")
    inst = I.Jump("foo", label)
    assert isinstance(inst.dest, Label)
    assert inst.dest.name == "my_label"
    assert str(inst) == "foo(dest=my_label)"


def test_binary_jump_sets_a_and_b(cpu):
    inst = I.BinaryJump("foo", M[13], M[10], M[2])
    assert isinstance(inst.a, MemoryReference)
    assert inst.a.address == 10
    assert isinstance(inst.b, MemoryReference)
    assert inst.b.address == 2


def test_jmp(cpu):
    assert str(I.JMP(10)) == "JMP(dest=10)"
    I.JMP(10)(cpu)
    assert cpu.get_register("ip") == 10


def test_rjmp(cpu):
    assert str(I.RJMP(10)) == "RJMP(dest=10)"
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
    monkeypatch.setattr("builtins.input", lambda prompt: "31")
    assert I.NIN(R.a)(cpu) == 31
    assert cpu.get_register("a") == 31


def test_oin(cpu, monkeypatch):
    assert str(I.OIN(M[10])) == "OIN(out=M[10])"
    monkeypatch.setattr("builtins.input", lambda prompt: "A")
    assert I.OIN(R.a)(cpu) == 65
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


def test_call_pushes_return_address(cpu):
    assert str(I.CALL(100)) == "CALL(dest=100)"
    assert cpu.get_register("ip") == 0
    assert cpu.stack == deque([])
    I.CALL(100)(cpu)
    # Should push IP+1 (which is 1) and jump to 100
    assert cpu.get_register("ip") == 100
    assert cpu.stack == deque([1])


def test_call_with_memory_reference(cpu):
    # Set memory location to hold target address
    cpu.set_memory(50, 200)
    assert cpu.get_register("ip") == 0
    I.CALL(M[50])(cpu)
    # Should push IP+1 (which is 1) and jump to value at M[50] (200)
    assert cpu.get_register("ip") == 200
    assert cpu.stack == deque([1])


def test_call_with_register(cpu):
    # Set register to hold target address
    cpu.set_register("a", 150)
    assert cpu.get_register("ip") == 0
    I.CALL(R.a)(cpu)
    # Should push IP+1 (which is 1) and jump to value in R.a (150)
    assert cpu.get_register("ip") == 150
    assert cpu.stack == deque([1])


def test_ret_pops_and_jumps(cpu):
    assert str(I.RET()) == "RET()"
    # Simulate a function call sequence
    cpu.set_register("ip", 5)
    I.CALL(100)(cpu)
    assert cpu.get_register("ip") == 100
    assert cpu.stack == deque([6])
    # Now return
    I.RET()(cpu)
    assert cpu.get_register("ip") == 6
    assert cpu.stack == deque([])


def test_call_from_different_ip_positions(cpu):
    # Test that return address changes based on current IP
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    I.NOOP()(cpu)
    assert cpu.get_register("ip") == 3
    I.CALL(100)(cpu)
    # Should push IP+1 (which is 4) and jump to 100
    assert cpu.get_register("ip") == 100
    assert cpu.stack == deque([4])
    I.RET()(cpu)
    assert cpu.get_register("ip") == 4
    assert cpu.stack == deque([])


def test_call_ret_sequence(cpu):
    # More complex sequence: call from different locations
    assert cpu.get_register("ip") == 0
    I.CALL(50)(cpu)
    assert cpu.stack == deque([1])
    assert cpu.get_register("ip") == 50
    # Nested call
    I.CALL(75)(cpu)
    assert cpu.stack == deque([1, 51])
    assert cpu.get_register("ip") == 75
    # Return from nested call
    I.RET()(cpu)
    assert cpu.get_register("ip") == 51
    assert cpu.stack == deque([1])
    # Return from first call
    I.RET()(cpu)
    assert cpu.get_register("ip") == 1
    assert cpu.stack == deque([])


def test_rcall_relative_call(cpu):
    assert str(I.RCALL(10)) == "RCALL(dest=10)"
    assert cpu.get_register("ip") == 0
    assert cpu.stack == deque([])
    I.RCALL(10)(cpu)
    # Should push IP+1 (which is 1) and jump to IP+10 (0+10=10)
    assert cpu.get_register("ip") == 10
    assert cpu.stack == deque([1])


def test_rcall_with_operands(cpu):
    # Set IP to 20
    cpu.set_register("ip", 20)
    # RCALL with offset in memory
    cpu.set_memory(5, 15)
    I.RCALL(M[5])(cpu)
    # Should push IP+1 (which is 21) and jump to IP+offset (20+15=35)
    assert cpu.get_register("ip") == 35
    assert cpu.stack == deque([21])


def test_rcall_negative_offset(cpu):
    # Test relative call with negative offset
    cpu.set_register("ip", 50)
    I.RCALL(-10)(cpu)
    # Should push IP+1 (which is 51) and jump to IP+(-10) (50-10=40)
    assert cpu.get_register("ip") == 40
    assert cpu.stack == deque([51])


def test_rcall_ret_sequence(cpu):
    # Test relative call and return
    cpu.set_register("ip", 10)
    I.RCALL(20)(cpu)
    assert cpu.get_register("ip") == 30
    assert cpu.stack == deque([11])
    I.RET()(cpu)
    assert cpu.get_register("ip") == 11
    assert cpu.stack == deque([])


def test_multiple_rcall_ret(cpu):
    # Test multiple relative calls and returns
    cpu.set_register("ip", 0)
    I.RCALL(5)(cpu)
    assert cpu.stack == deque([1])
    assert cpu.get_register("ip") == 5
    I.RCALL(10)(cpu)
    assert cpu.stack == deque([1, 6])
    assert cpu.get_register("ip") == 15
    I.RCALL(5)(cpu)
    assert cpu.stack == deque([1, 6, 16])
    assert cpu.get_register("ip") == 20
    # Return from all calls
    I.RET()(cpu)
    assert cpu.get_register("ip") == 16
    I.RET()(cpu)
    assert cpu.get_register("ip") == 6
    I.RET()(cpu)
    assert cpu.get_register("ip") == 1
    assert cpu.stack == deque([])


def test_instruction_equality():
    # Test instructions with no operands
    assert I.NOOP() == I.NOOP()
    assert I.NOOP() != I.RET()

    # Test instructions with single operand
    assert I.PUSH(5) == I.PUSH(5)
    assert I.PUSH(5) != I.PUSH(6)
    assert I.PUSH(5) != I.POP()

    # Test instructions with multiple operands
    assert I.ADD(R.a, L[5]) == I.ADD(R.a, L[5])
    assert I.ADD(R.a, L[5]) != I.ADD(R.b, L[5])
    assert I.ADD(R.a, L[5]) != I.ADD(R.a, L[6])
    assert I.ADD(R.a, L[5]) != I.SUB(R.a, L[5])

    # Test instructions with memory references
    assert I.ADD(M[1], M[2]) == I.ADD(M[1], M[2])
    assert I.ADD(M[1], M[2]) != I.ADD(M[1], M[3])

    # Test jump instructions
    assert I.JMP(100) == I.JMP(100)
    assert I.JMP(100) != I.JMP(200)
    assert I.JEQ(10, R.a, L[5]) == I.JEQ(10, R.a, L[5])
    assert I.JEQ(10, R.a, L[5]) != I.JEQ(20, R.a, L[5])


def test_brk_displays_state_and_waits(cpu, capsys, monkeypatch):
    """Test that BRK prints state and waits for input."""
    # Set up some state to display
    cpu.set_register("a", 42)
    cpu.set_memory(10, 100)

    # Mock input to simulate pressing Enter (accept optional prompt parameter)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    # Execute BRK instruction
    result = I.BRK()(cpu)

    # Check return value
    assert result == 0

    # Check that state was printed (state is printed as dict representation)
    captured = capsys.readouterr()
    assert "BRK -> 0" in captured.out
    assert "'R.a': 42" in captured.out
    assert "'M[10]': 100" in captured.out

    # Check IP advanced
    assert cpu.get_register("ip") == 1


def test_brk_in_program(cpu, capsys, monkeypatch):
    """Test BRK in a complete program."""
    # Mock input to simulate pressing Enter (accept optional prompt parameter)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    program = [
        I.CP(5, R.a),
        I.BRK(),  # Should pause here
        I.ADD(R.a, L[1]),
        I.NOUT(R.a, L[1]),
    ]

    cpu.run(program)

    captured = capsys.readouterr()
    # Should see BRK output
    assert "BRK -> 0" in captured.out
    # Should see final output
    assert "6" in captured.out


def test_brkd_switches_to_debug_mode(cpu, capsys, monkeypatch):
    """Test that BRKD switches to debug mode for rest of execution."""
    # Track input calls to verify debug mode
    input_calls = []

    def mock_input(prompt=""):
        input_calls.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", mock_input)

    program = [
        I.CP(1, R.a),  # Not in debug mode
        I.BRKD(),  # Switch to debug mode
        I.ADD(R.a, L[1]),  # Should run in debug mode (wait for input)
        I.ADD(R.a, L[1]),  # Should run in debug mode (wait for input)
        I.NOUT(R.a, L[1]),  # Should run in debug mode (wait for input)
    ]

    cpu.run(program)

    captured = capsys.readouterr()

    # Should see BRKD output
    assert "BRKD -> 0" in captured.out

    # Should see debug output for instructions after BRKD
    assert "ADD(a=R.a, b=1, out=R.a) -> 2" in captured.out
    assert "ADD(a=R.a, b=1, out=R.a) -> 3" in captured.out
    assert "NOUT(a=R.a, b=1) -> 0" in captured.out

    # Should see final output
    assert "3" in captured.out

    # Verify input was called for BRKD and each subsequent instruction
    # BRKD triggers 1 input(), then 3 more instructions each trigger input() in debug mode
    assert len(input_calls) == 4


def test_brk_and_brkd_equality(cpu):
    """Test that BRK and BRKD instructions compare correctly."""
    assert I.BRK() == I.BRK()
    assert I.BRKD() == I.BRKD()
    assert I.BRK() != I.BRKD()
