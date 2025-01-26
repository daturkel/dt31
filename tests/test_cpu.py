import pytest

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, M, R


def test_stack_too_small():
    with pytest.raises(ValueError) as e:
        DT31(stack_size=0)
    assert "stack_size" in str(e.value)

    with pytest.raises(ValueError) as e:
        DT31(stack_size=-1)
    assert "stack_size" in str(e.value)


def test_memory_too_small():
    with pytest.raises(ValueError) as e:
        DT31(memory_size=0)
    assert "memory_size" in str(e.value)

    with pytest.raises(ValueError) as e:
        DT31(memory_size=-1)
    assert "memory_size" in str(e.value)


def test_no_ip_register():
    with pytest.raises(ValueError) as e:
        DT31(registers=["ip"])
    assert "reserved" in str(e.value)


def test_set_registers():
    cpu = DT31(registers=["a", "d", "xy"])
    assert set(cpu.registers.keys()) == set(["a", "d", "xy", "ip"])


def test_stack_underflow(cpu):
    cpu.push(2)
    assert cpu.pop() == 2
    with pytest.raises(RuntimeError) as e:
        cpu.pop()
    assert "underflow" in str(e.value)


def test_stack_overflow(cpu):
    for _ in range(256):
        cpu.push(0)
    with pytest.raises(RuntimeError) as e:
        cpu.push(0)
    assert "overflow" in str(e.value)


def test_get_unknown_register(cpu):
    with pytest.raises(ValueError) as e:
        cpu.get_register("x")
    assert "unknown register" in str(e.value)


def test_set_unknown_register(cpu):
    with pytest.raises(ValueError) as e:
        cpu.set_register("x", 0)
    assert "unknown register" in str(e.value)


def test_get_set(cpu):
    assert cpu[M[1]] == 10
    assert cpu[R.a] == 30
    cpu[M[1]] = 2
    assert cpu[M[1]] == 2
    cpu[R.a] = 9
    assert cpu[R.a] == 9


def test_get_set_invalid_type(cpu):
    with pytest.raises(ValueError) as e:
        cpu[L[1]]
    assert "can't get item with type" in str(e.value)
    with pytest.raises(ValueError) as e:
        cpu[L[1]] = 2
    assert "can't get item with type" in str(e.value)


def test_get_memory(cpu):
    assert cpu.get_memory(1) == 10
    with pytest.raises(IndexError):
        cpu.get_memory(1000)
    cpu.wrap_memory = True
    assert cpu.get_memory(257) == 10


def test_set_memory(cpu):
    cpu.set_memory(1, 99)
    assert cpu.get_memory(1) == 99
    with pytest.raises(IndexError):
        cpu.set_memory(1000, 0)
    cpu.wrap_memory = True
    cpu.set_memory(257, 999)
    assert cpu.get_memory(1) == 999


def test_run_resets_instructions(cpu):
    cpu.set_register("ip", 100)
    cpu.run([])
    assert cpu.get_register("ip") == 0


def test_halt_on_negative_instruction(cpu):
    cpu.run([I.JMP(-1)])
    assert cpu.get_register("ip") == -1


def test_halt_on_instruction_overflow(cpu):
    cpu.run([I.JMP(3), I.NOOP()])
    assert cpu.get_register("ip") == 3


def test_run_example(cpu):
    cpu.run([I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])])
    assert cpu.get_memory(1) == 110
    assert cpu.get_register("ip") == 3
