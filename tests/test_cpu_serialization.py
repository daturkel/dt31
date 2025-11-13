"""Tests for CPU serialization (dump/load)."""

import pytest

from dt31.cpu import DT31
from dt31.parser import parse_program


def test_dump_load_roundtrip_basic():
    """Test that dump/load preserves basic CPU state."""
    program = "CP 10, R.a\nCP 20, R.b"
    program = parse_program(program)

    cpu = DT31()
    cpu.load(program)
    cpu.step()  # Execute first instruction

    # Dump state
    state = cpu.dump()

    # Load into new CPU
    cpu2 = DT31.load_from_dump(state)

    # Verify registers match
    assert cpu2.get_register("a") == 10
    assert cpu2.get_register("b") == 0
    assert cpu2.get_register("ip") == 1

    # Verify program was included
    assert state["program"] is not None
    assert "CP 10, R.a" in state["program"]

    # Verify they can continue executing from same point
    cpu.step()  # Execute second instruction in original
    cpu2.step()  # Execute second instruction in restored

    assert cpu.get_register("b") == cpu2.get_register("b") == 20


def test_dump_load_with_memory():
    """Test dump/load preserves memory contents."""
    program = "CP 100, M[0]\nCP 200, M[10]\nCP M[0], R.a"
    program = parse_program(program)

    cpu = DT31()
    cpu.load(program)
    cpu.step()  # M[0] = 100
    cpu.step()  # M[10] = 200

    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)

    assert cpu2.memory[0] == 100
    assert cpu2.memory[10] == 200
    assert cpu2.get_register("ip") == 2

    # Continue execution
    cpu2.step()  # CP M[0], R.a
    assert cpu2.get_register("a") == 100


def test_dump_load_with_stack():
    """Test dump/load preserves stack contents."""
    program = "CP 10, R.a\nPUSH R.a\nCP 20, R.a\nPUSH R.a"
    program = parse_program(program)

    cpu = DT31()
    cpu.load(program)
    cpu.step()  # CP 10, R.a
    cpu.step()  # PUSH R.a
    cpu.step()  # CP 20, R.a
    cpu.step()  # PUSH R.a

    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)

    assert list(cpu2.stack) == [10, 20]
    assert cpu2.get_register("ip") == 4


def test_dump_load_custom_registers():
    """Test dump/load with custom register names."""
    program = "CP 42, R.x\nCP 99, R.y"
    program = parse_program(program)

    cpu = DT31(registers=["x", "y", "z"])
    cpu.load(program)
    cpu.step()  # Execute first instruction

    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)

    assert cpu2.get_register("x") == 42
    assert cpu2.get_register("y") == 0
    assert cpu2.get_register("z") == 0
    assert "x" in cpu2.registers
    assert "y" in cpu2.registers
    assert "z" in cpu2.registers


def test_dump_load_custom_config():
    """Test dump/load preserves CPU configuration."""
    program = "CP 1, M[500]"
    program = parse_program(program)

    cpu = DT31(memory_size=1024, stack_size=512, wrap_memory=True)
    cpu.load(program)
    cpu.step()

    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)

    assert cpu2.memory_size == 1024
    assert cpu2.stack_size == 512
    assert cpu2.wrap_memory is True
    assert cpu2.memory[500] == 1


def test_dump_with_program():
    """Test that dump() automatically includes program text."""
    program = parse_program("CP 10, R.a")
    cpu = DT31()
    cpu.load(program)
    cpu.step()

    state = cpu.dump()
    # Program should be automatically converted to text
    assert state["program"] is not None
    assert "CP 10, R.a" in state["program"]
    assert state["registers"]["a"] == 10


def test_dump_load_without_program():
    """Test dump/load of CPU with no program loaded."""
    cpu = DT31()
    cpu.set_register("a", 42)
    cpu.set_memory(10, 100)
    cpu.push(99)

    state = cpu.dump()
    assert state["program"] is None

    cpu2 = DT31.load_from_dump(state)
    assert cpu2.get_register("a") == 42
    assert cpu2.memory[10] == 100
    assert list(cpu2.stack) == [99]
    assert cpu2.instructions == []  # No program loaded


def test_load_from_dump_missing_fields():
    """Test that load_from_dump validates required fields."""
    incomplete_state = {
        "registers": {"a": 0, "ip": 0},
        "memory": [0] * 256,
        # Missing stack and config
    }

    with pytest.raises(ValueError, match="missing required field"):
        DT31.load_from_dump(incomplete_state)


def test_dump_load_mid_program():
    """Test dump/load in the middle of program execution."""
    program = "CP 10, R.a\nCP 20, R.b\nCP 30, R.c\nADD R.a, R.b, R.c"
    program = parse_program(program)

    cpu = DT31()
    cpu.load(program)

    # Execute first two instructions
    cpu.step()  # CP 10, R.a
    cpu.step()  # CP 20, R.b

    # Capture state mid-execution
    mid_state = cpu.dump()
    assert mid_state["registers"]["a"] == 10
    assert mid_state["registers"]["b"] == 20
    assert mid_state["registers"]["c"] == 0
    assert mid_state["registers"]["ip"] == 2

    # Load from mid-point into new CPU
    cpu2 = DT31.load_from_dump(mid_state)
    assert cpu2.get_register("a") == 10
    assert cpu2.get_register("b") == 20
    assert cpu2.get_register("c") == 0
    assert cpu2.get_register("ip") == 2

    # Both CPUs should execute remaining instructions identically
    cpu.step()  # CP 30, R.c
    cpu2.step()  # CP 30, R.c
    assert cpu.get_register("c") == cpu2.get_register("c") == 30

    cpu.step()  # ADD R.a, R.b, R.c
    cpu2.step()  # ADD R.a, R.b, R.c
    assert cpu.get_register("c") == cpu2.get_register("c") == 30  # a + b = 30


def test_dump_preserves_all_memory():
    """Test that dump saves entire memory array, not just non-zero."""
    program = "CP 100, M[0]\nCP 0, M[1]"
    program = parse_program(program)

    cpu = DT31(memory_size=256)
    cpu.load(program)
    cpu.step()
    cpu.step()

    state = cpu.dump()

    # Full memory array should be preserved
    assert len(state["memory"]) == 256
    assert state["memory"][0] == 100
    assert state["memory"][1] == 0  # Explicitly set to 0
    assert state["memory"][255] == 0  # Default 0


def test_dump_load_empty_stack():
    """Test dump/load with empty stack."""
    program = "CP 10, R.a"
    program = parse_program(program)

    cpu = DT31()
    cpu.load(program)
    cpu.step()

    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)

    assert list(cpu2.stack) == []


def test_dump_load_preserves_instruction_pointer():
    """Test that IP is correctly preserved across dump/load."""
    program = "CP 1, R.a\nCP 2, R.a\nCP 3, R.a\nCP 4, R.a"
    program = parse_program(program)

    # Test at start (IP=0, a=0)
    cpu = DT31()
    cpu.load(program)
    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)
    assert cpu2.get_register("ip") == 0
    assert cpu2.get_register("a") == 0

    # Test after first instruction (IP=1, a=1)
    cpu.step()
    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)
    assert cpu2.get_register("ip") == 1
    assert cpu2.get_register("a") == 1

    # Test after second instruction (IP=2, a=2)
    cpu.step()
    state = cpu.dump()
    cpu2 = DT31.load_from_dump(state)
    assert cpu2.get_register("ip") == 2
    assert cpu2.get_register("a") == 2
