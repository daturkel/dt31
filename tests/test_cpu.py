import pytest

import dt31.instructions as I
from dt31.assembler import AssemblyError, extract_registers_from_program
from dt31.cpu import DT31
from dt31.exceptions import (
    DivisionByZero,
    InvalidOperand,
    MemoryOutOfBounds,
    StackOverflow,
    StackUnderflow,
)
from dt31.operands import L, M, R
from dt31.parser import parse_program


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
    assert set(cpu.registers.keys()) == {"a", "d", "xy", "ip"}


def test_cpu_validates_register_names():
    """Test that CPU initialization validates register names."""
    # Valid names should work
    DT31(registers=["foo", "bar", "_private"])

    # Invalid identifier should fail
    with pytest.raises(ValueError, match="Invalid register name"):
        DT31(registers=["123invalid"])

    with pytest.raises(ValueError, match="Invalid register name"):
        DT31(registers=["my-register"])

    # Dunder names should fail
    with pytest.raises(ValueError, match="cannot start with double underscores"):
        DT31(registers=["__dunder__"])

    with pytest.raises(ValueError, match="cannot start with double underscores"):
        DT31(registers=["valid", "__invalid"])


def test_stack_underflow(cpu):
    cpu.push(2)
    assert cpu.pop() == 2
    with pytest.raises(StackUnderflow) as e:
        cpu.pop()
    assert str(e.value) == "stack underflow"


def test_stack_overflow(cpu):
    for _ in range(256):
        cpu.push(0)
    with pytest.raises(StackOverflow) as e:
        cpu.push(0)
    assert str(e.value) == "stack overflow"


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
    with pytest.raises(TypeError) as e:
        cpu[L[1]]
    assert "can't get item with type" in str(e.value)
    with pytest.raises(TypeError) as e:
        cpu[L[1]] = 2
    assert "can't get item with type" in str(e.value)


def test_get_memory(cpu):
    assert cpu.get_memory(1) == 10
    with pytest.raises(MemoryOutOfBounds) as e:
        cpu.get_memory(1000)
    assert str(e.value) == "memory has no index 1000"
    cpu.wrap_memory = True
    assert cpu.get_memory(257) == 10


def test_set_memory(cpu):
    cpu.set_memory(1, 99)
    assert cpu.get_memory(1) == 99
    with pytest.raises(MemoryOutOfBounds) as e:
        cpu.set_memory(1000, 0)
    assert str(e.value) == "memory has no index 1000"
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


def test_run_debug(cpu, capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: None)
    cpu.run([I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])], debug=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    output = captured.err
    assert output.splitlines() == [
        "ADD(a=M[1], b=M[2], out=M[1]) -> 30",
        "{'M[1]': 30, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 1, 'stack': []}",
        "NOOP() -> 0",
        "{'M[1]': 30, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 2, 'stack': []}",
        "JGT(dest=0, a=100, b=M[1]) -> 0",
        "{'M[1]': 30, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 0, 'stack': []}",
        "ADD(a=M[1], b=M[2], out=M[1]) -> 50",
        "{'M[1]': 50, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 1, 'stack': []}",
        "NOOP() -> 0",
        "{'M[1]': 50, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 2, 'stack': []}",
        "JGT(dest=0, a=100, b=M[1]) -> 0",
        "{'M[1]': 50, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 0, 'stack': []}",
        "ADD(a=M[1], b=M[2], out=M[1]) -> 70",
        "{'M[1]': 70, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 1, 'stack': []}",
        "NOOP() -> 0",
        "{'M[1]': 70, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 2, 'stack': []}",
        "JGT(dest=0, a=100, b=M[1]) -> 0",
        "{'M[1]': 70, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 0, 'stack': []}",
        "ADD(a=M[1], b=M[2], out=M[1]) -> 90",
        "{'M[1]': 90, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 1, 'stack': []}",
        "NOOP() -> 0",
        "{'M[1]': 90, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 2, 'stack': []}",
        "JGT(dest=0, a=100, b=M[1]) -> 0",
        "{'M[1]': 90, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 0, 'stack': []}",
        "ADD(a=M[1], b=M[2], out=M[1]) -> 110",
        "{'M[1]': 110, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 1, 'stack': []}",
        "NOOP() -> 0",
        "{'M[1]': 110, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 2, 'stack': []}",
        "JGT(dest=0, a=100, b=M[1]) -> 0",
        "{'M[1]': 110, 'M[2]': 20, 'R.a': 30, 'R.b': 40, 'R.c': 50, 'R.ip': 3, 'stack': []}",
    ]


def test_run_fast_path_matches_debug_and_timing_paths(capsys, monkeypatch):
    """run()'s fast path (no debug, no track_step_time) must produce the same
    final CPU state as run(debug=True) and a track_step_time=True CPU, for
    the same program, including the loop-exit and jump-heavy control flow."""
    monkeypatch.setattr("builtins.input", lambda: None)

    def make_program():
        return [
            I.CP(5, R.a),
            I.NOUT(R.a, L[0]),
            I.SUB(R.a, L[1]),
            I.JGT(1, R.a, L[0]),
            I.CALL(6),
            I.JMP(8),
            I.CP(99, R.b),
            I.RET(),
        ]

    fast_cpu = DT31()
    fast_cpu.run(make_program())

    debug_cpu = DT31()
    debug_cpu.run(make_program(), debug=True)
    capsys.readouterr()  # discard debug output

    timing_cpu = DT31(track_step_time=True)
    timing_cpu.run(make_program())

    assert fast_cpu.state == debug_cpu.state == timing_cpu.state
    assert fast_cpu.step_count == debug_cpu.step_count == timing_cpu.step_count
    assert (
        fast_cpu.get_register("ip")
        == debug_cpu.get_register("ip")
        == timing_cpu.get_register("ip")
    )


def test_run_fast_path_matches_slow_path_on_negative_ip(capsys, monkeypatch):
    """EndOfProgram via a negative ip halts identically on both paths."""
    monkeypatch.setattr("builtins.input", lambda: None)

    fast_cpu = DT31()
    fast_cpu.run([I.JMP(-1)])

    debug_cpu = DT31()
    debug_cpu.run([I.JMP(-1)], debug=True)
    capsys.readouterr()

    assert fast_cpu.get_register("ip") == debug_cpu.get_register("ip") == -1
    assert fast_cpu.step_count == debug_cpu.step_count


def test_run_without_load_raises_error(cpu):
    with pytest.raises(RuntimeError, match="No program loaded"):
        cpu.run()


def test_run_without_arguments_after_load(cpu):
    program = [I.CP(5, R.a), I.ADD(R.a, L[3]), I.NOOP()]
    cpu.load(program)
    cpu.run()
    assert cpu.get_register("a") == 8
    assert cpu.get_register("ip") == 3


def test_run_without_arguments_resumes_from_ip(cpu):
    program = [I.CP(1, R.a), I.ADD(R.a, L[1]), I.ADD(R.a, L[1]), I.NOOP()]
    cpu.load(program)
    cpu.step()  # Execute first instruction: a = 1
    assert cpu.get_register("a") == 1
    assert cpu.get_register("ip") == 1
    cpu.run()  # Should resume from ip=1
    assert cpu.get_register("a") == 3
    assert cpu.get_register("ip") == 4


def test_load(cpu):
    insts = [I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])]
    cpu.load(insts)
    assert cpu.instructions == insts
    assert cpu.get_register("ip") == 0


def test_step(cpu):
    insts = [I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])]
    cpu.load(insts)
    cpu.step()
    assert cpu.get_register("ip") == 1
    assert cpu.get_memory(1) == 30
    cpu.step()
    assert cpu.get_register("ip") == 2
    cpu.step()
    assert cpu.get_register("ip") == 0
    cpu.step()
    assert cpu.get_register("ip") == 1
    assert cpu.get_memory(1) == 50


def test_track_step_time_default_off(cpu):
    """track_step_time defaults to False: step() executes correctly but skips timing."""
    assert cpu.track_step_time is False
    insts = [I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])]
    cpu.load(insts)
    cpu.step()
    cpu.step()
    cpu.step()
    # execution is unaffected
    assert cpu.get_register("ip") == 0
    assert cpu.get_memory(1) == 30
    # timing bookkeeping is skipped, but step_count still counts
    assert cpu.step_count == 3
    assert cpu.instruction_time_ns == 0
    assert cpu.blocking_time_ns == 0


def test_track_step_time_enabled():
    """With track_step_time=True, step() records per-instruction timing."""
    cpu = DT31(track_step_time=True)
    insts = [I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])]
    cpu.load(insts)
    cpu.step()
    cpu.step()
    cpu.step()
    assert cpu.step_count == 3
    assert cpu.instruction_time_ns > 0


def test_track_step_time_enabled_counts_blocking_time(monkeypatch):
    """With track_step_time=True, time spent in a blocking instruction is also
    added to blocking_time_ns (a subset of instruction_time_ns)."""
    monkeypatch.setattr("builtins.input", lambda: "5")
    cpu = DT31(track_step_time=True)
    cpu.load([I.NIN(R.a)])
    cpu.step()
    assert cpu.get_register("a") == 5
    assert cpu.blocking_time_ns > 0
    assert cpu.blocking_time_ns <= cpu.instruction_time_ns


def test_step_debug(cpu, capsys):
    insts = [I.ADD(M[1], M[2]), I.NOOP(), I.JGT(0, 100, M[1])]
    cpu.load(insts)
    cpu.step(debug=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err == "ADD(a=M[1], b=M[2], out=M[1]) -> 30\n" + str(cpu.state) + "\n"
    )


def test_state(cpu):
    assert cpu.state == {
        "M[1]": 10,
        "M[2]": 20,
        "R.a": 30,
        "R.b": 40,
        "R.c": 50,
        "R.ip": 0,
        "stack": [],
    }
    cpu.push(2)
    cpu.set_register("c", 4)
    cpu.set_memory(1, 9)
    assert cpu.state == {
        "M[1]": 9,
        "M[2]": 20,
        "R.a": 30,
        "R.b": 40,
        "R.c": 4,
        "R.ip": 0,
        "stack": [2],
    }


def test_cpu_validates_missing_registers():
    """Test that CPU raises error when program uses missing registers."""
    cpu = DT31(registers=["a", "b"])
    program: list[I.Instruction | I.Label] = [
        I.CP(L[10], R.x)
    ]  # 'x' not in CPU registers

    with pytest.raises(AssemblyError) as exc_info:
        cpu.load(program)

    assert "x" in str(exc_info.value)
    assert "Missing registers" in str(exc_info.value)


def test_cpu_validates_multiple_missing_registers():
    """Test error message with multiple missing registers."""
    cpu = DT31(registers=["a"])
    program = [
        I.CP(L[10], R.x),
        I.CP(L[20], R.y),
        I.ADD(R.x, R.y),
    ]

    with pytest.raises(AssemblyError) as exc_info:
        cpu.load(program)

    error_msg = str(exc_info.value)
    assert "x" in error_msg
    assert "y" in error_msg


def test_cpu_accepts_valid_registers():
    """Test that CPU accepts program when all registers exist."""
    cpu = DT31(registers=["x", "y"])
    program = [
        I.CP(L[10], R.x),
        I.CP(L[20], R.y),
        I.ADD(R.x, R.y),
    ]

    # Should not raise
    cpu.load(program)
    assert len(cpu.instructions) == 3


def test_cpu_run_with_auto_detected_registers():
    """Test running a program with auto-detected registers."""

    program = [
        I.CP(L[5], R.counter),
        I.NOUT(R.counter, L[1]),
    ]

    registers = extract_registers_from_program(program)
    cpu = DT31(registers=registers)
    cpu.run(program)

    assert cpu.get_register("counter") == 5


def test_step_count(cpu):
    program = [I.NOOP(), I.NOOP(), I.NOOP(), I.NOOP()]
    cpu.load(program)
    assert cpu.step_count == 0
    cpu.step()
    assert cpu.step_count == 1
    cpu.step()
    assert cpu.step_count == 2
    cpu.run(program)
    assert cpu.step_count == 6


def test_comments_in_debug_output(capsys):
    """Test that inline comments appear in debug output."""
    code = "CP 5, R.a  ; Initialize counter"

    program = parse_program(code)
    cpu = DT31()

    cpu.load(program)
    cpu.step(debug=True)

    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.strip().split("\n")
    assert lines[0] == "CP(a=5, b=R.a) -> 5  ; Initialize counter"


def test_no_comment_in_debug_output(capsys):
    """Test that instructions without comments don't show semicolons."""
    code = "CP 5, R.a"

    program = parse_program(code)
    cpu = DT31()

    cpu.load(program)
    cpu.step(debug=True)

    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.strip().split("\n")
    assert lines[0] == "CP(a=5, b=R.a) -> 5"


def test_timing_accumulates_across_runs():
    """Test that timing attributes accumulate across multiple run() calls."""
    cpu = DT31(track_step_time=True)
    program = [I.CP(5, R.a), I.ADD(R.a, L[1])]

    # First run
    cpu.run(program)
    first_wall = cpu.wall_time_ns
    first_instruction = cpu.instruction_time_ns
    assert first_wall > 0
    assert first_instruction > 0
    assert cpu.step_count == 2

    # Second run (reset IP and run again)
    cpu.set_register("ip", 0)
    cpu.run()  # Run without instructions reuses loaded program

    # Check accumulation - wall time from second run() should be added
    assert cpu.wall_time_ns > first_wall
    assert cpu.instruction_time_ns > first_instruction
    assert cpu.step_count == 4


def test_execution_time_property():
    """Test that execution_time_ns property computes correctly."""
    cpu = DT31(track_step_time=True)
    program = [I.CP(10, R.a), I.ADD(R.a, L[5])]
    cpu.run(program)

    # Execution time should equal instruction time minus I/O time
    assert cpu.execution_time_ns == cpu.instruction_time_ns - cpu.blocking_time_ns
    # For non-I/O instructions, they should be equal
    assert cpu.execution_time_ns == cpu.instruction_time_ns
    assert cpu.blocking_time_ns == 0


def test_wall_time_includes_instruction_time():
    """Test that wall time is >= instruction time."""
    cpu = DT31(track_step_time=True)
    program = [I.CP(1, R.a), I.ADD(R.a, L[1]), I.SUB(R.a, L[1])]
    cpu.run(program)

    assert cpu.wall_time_ns >= cpu.instruction_time_ns
    assert cpu.instruction_time_ns > 0


def test_step_count_matches_instructions():
    """Test that step_count matches the number of executed instructions."""
    cpu = DT31()
    program = [I.CP(1, R.a), I.ADD(R.a, L[2]), I.MUL(R.a, L[3])]
    cpu.run(program)

    assert cpu.step_count == 3


# ===== DT31RuntimeError hierarchy =====


def test_division_by_zero_via_step_python_api():
    """DIV by zero via step() raises DivisionByZero with ip/instruction set and
    line=None for a program built via the Python API."""
    cpu = DT31()
    div_instruction = I.DIV(R.a, L[0])
    cpu.load([div_instruction])

    try:
        _ = 1 // 0
    except ZeroDivisionError as original:
        expected_message = str(original)

    with pytest.raises(DivisionByZero) as e:
        cpu.step()

    assert str(e.value) == expected_message
    assert e.value.ip == 0
    assert e.value.instruction is cpu.instructions[0]
    assert e.value.line is None
    assert isinstance(e.value.__cause__, ZeroDivisionError)


def test_division_by_zero_via_run_fast_path():
    """DIV by zero raises DivisionByZero via run()'s fast path (no debug, no
    step-time tracking)."""
    cpu = DT31()
    program = [I.CP(0, R.b), I.DIV(R.a, R.b)]

    with pytest.raises(DivisionByZero) as e:
        cpu.run(program)

    assert e.value.ip == 1
    assert e.value.instruction is cpu.instructions[1]
    assert isinstance(e.value.__cause__, ZeroDivisionError)


def test_division_by_zero_via_step_slow_path(capsys):
    """DIV by zero raises DivisionByZero via step()'s debug (slow) path too."""
    cpu = DT31()
    program = [I.CP(0, R.b), I.DIV(R.a, R.b)]
    cpu.load(program)
    cpu.step(debug=True)  # CP 0, R.b

    with pytest.raises(DivisionByZero) as e:
        cpu.step(debug=True)  # DIV R.a, R.b

    assert e.value.ip == 1
    assert e.value.instruction is cpu.instructions[1]
    assert isinstance(e.value.__cause__, ZeroDivisionError)


def test_mod_by_zero_raises_division_by_zero():
    """MOD by zero also raises DivisionByZero."""
    cpu = DT31()
    program = [I.CP(0, R.b), I.MOD(R.a, R.b)]

    with pytest.raises(DivisionByZero):
        cpu.run(program)


def test_division_by_zero_line_from_parsed_program():
    """DivisionByZero.line reflects the source line for a parsed program."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    cpu = DT31()
    program = parse_program(assembly)

    with pytest.raises(DivisionByZero) as e:
        cpu.run(program)

    assert e.value.line == 4


def test_stack_underflow_context_attached_via_step():
    """StackUnderflow raised by pop() gets ip/instruction/line attached by step()."""
    cpu = DT31()
    pop_instruction = I.POP(R.a)
    cpu.load([pop_instruction])

    with pytest.raises(StackUnderflow) as e:
        cpu.step()

    assert str(e.value) == "stack underflow"
    assert e.value.ip == 0
    assert e.value.instruction is cpu.instructions[0]
    assert e.value.line is None


def test_stack_overflow_context_attached_via_run():
    """StackOverflow raised by push() gets ip/instruction/line attached via run()."""
    cpu = DT31(stack_size=1)
    program = [I.PUSH(1), I.PUSH(2)]

    with pytest.raises(StackOverflow) as e:
        cpu.run(program)

    assert str(e.value) == "stack overflow"
    assert e.value.ip == 1
    assert e.value.instruction is cpu.instructions[1]


def test_memory_out_of_bounds_context_attached():
    """MemoryOutOfBounds raised by an instruction gets ip/instruction/line attached."""
    cpu = DT31(memory_size=4)
    program = [I.CP(10, M[100])]

    with pytest.raises(MemoryOutOfBounds) as e:
        cpu.run(program)

    assert str(e.value) == "memory has no index 100"
    assert e.value.ip == 0
    assert e.value.instruction is cpu.instructions[0]


def test_invalid_operand_context_attached():
    """InvalidOperand raised by RINT gets ip/instruction/line attached."""
    cpu = DT31()
    program = [I.RINT(5, 1, R.a)]

    with pytest.raises(InvalidOperand) as e:
        cpu.run(program)

    assert "got a=5, b=1" in str(e.value)
    assert e.value.ip == 0
    assert e.value.instruction is cpu.instructions[0]


def test_dt31_runtime_error_is_common_base():
    """All new runtime error types share the DT31RuntimeError base."""
    from dt31.exceptions import DT31RuntimeError

    assert issubclass(DivisionByZero, DT31RuntimeError)
    assert issubclass(StackUnderflow, DT31RuntimeError)
    assert issubclass(StackOverflow, DT31RuntimeError)
    assert issubclass(MemoryOutOfBounds, DT31RuntimeError)
    assert issubclass(InvalidOperand, DT31RuntimeError)
