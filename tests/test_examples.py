import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from dt31 import DT31
from dt31.parser import parse_program

# Add the examples directory to the path so we can import from it
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))

from bitwise_operations import bitwise_ops  # type: ignore # noqa: E402
from conditional_logic import find_max  # type: ignore # noqa: E402
from custom_instructions import ASSEMBLY, CLAMP, SQUARE  # type: ignore # noqa: E402
from factorial_memoized import factorial_memoized  # type: ignore # noqa: E402
from factorial_naive import factorial  # type: ignore # noqa: E402
from factorial_with_labels import (  # type: ignore # noqa: E402
    factorial as factorial_labels,
)
from fibonacci import fibonacci  # type: ignore # noqa: E402
from hello_world import hello_world  # type: ignore # noqa: E402
from simple_calculator import calculator  # type: ignore # noqa: E402
from sum_array import sum_array  # type: ignore # noqa: E402

TESTED_PYTHON_PROGRAMS = [
    "bitwise_operations.py",
    "conditional_logic.py",
    "custom_instructions.py",
    "factorial_memoized.py",
    "factorial_naive.py",
    "factorial_with_labels.py",
    "fibonacci.py",
    "hello_world.py",
    "simple_calculator.py",
    "sum_array.py",
]


def test_bitwise_ops(capsys):
    """Test bitwise operations with inputs 12 and 5."""
    cpu = DT31(registers=["a", "b", "c"])

    # Mock input() to return "12" then "5"
    with patch("builtins.input", side_effect=["12", "5"]):
        cpu.run(bitwise_ops, debug=False)

    captured = capsys.readouterr()

    # Expected results:
    # 12 & 5 = 4
    # 12 | 5 = 13
    # 12 ^ 5 = 9
    # ~12 = -13 (two's complement)
    # 12 << 2 = 48
    # 12 >> 1 = 6

    expected_output = "4\n13\n9\n-13\n48\n6\n"
    assert captured.out == expected_output


def test_conditional_logic(capsys):
    """Test conditional logic with three numbers to find the maximum."""
    cpu = DT31(registers=["a", "b", "c"])

    # Mock input() to return "5", "12", "8"
    with patch("builtins.input", side_effect=["5", "12", "8"]):
        cpu.run(find_max, debug=False)

    captured = capsys.readouterr()

    # Expected result: max(5, 12, 8) = 12
    expected_output = "12\n"
    assert captured.out == expected_output


def test_custom_instructions(capsys):
    """Test custom SQUARE and CLAMP instructions."""
    cpu = DT31()

    # Define custom instructions
    custom_instructions = {
        "SQUARE": SQUARE,
        "CLAMP": CLAMP,
    }

    program = parse_program(ASSEMBLY, custom_instructions=custom_instructions)
    cpu.run(program)

    captured = capsys.readouterr()

    # Expected results:
    # 5^2 = 25
    # clamp(150, 0, 100) = 100
    expected_output = "25\n100\n"
    assert captured.out == expected_output


def test_factorial_memoized(capsys):
    """Test factorial memoization - compute 5!, then 3! (cache hit), then 6!."""

    # Need CPU with "max" register
    cpu = DT31(registers=["a", "b", "c", "max"])

    # Mock input() to return "5", "3", "6"
    # This tests: compute 5!, cache hit for 3!, compute 6! using cached 5!
    # The program loops infinitely, so we'll run out of inputs and get StopIteration
    with patch("builtins.input", side_effect=["5", "3", "6"]):
        try:
            cpu.run(factorial_memoized, debug=False)
        except StopIteration:
            # Expected - program loops back for more input
            pass

    captured = capsys.readouterr()

    # Expected results:
    # 5! = 120
    # 3! = 6 (from cache)
    # 6! = 720
    expected_output = "120\n6\n720\n"
    assert captured.out == expected_output

    # Verify memoization by checking memory contains cached factorial values
    # Memory layout: M[N] = factorial(N)
    assert cpu.get_memory(1) == 1  # 1! = 1
    assert cpu.get_memory(2) == 2  # 2! = 2
    assert cpu.get_memory(3) == 6  # 3! = 6
    assert cpu.get_memory(4) == 24  # 4! = 24
    assert cpu.get_memory(5) == 120  # 5! = 120
    assert cpu.get_memory(6) == 720  # 6! = 720

    # Verify R.max register tracks the highest computed factorial
    assert cpu.get_register("max") == 6


def test_factorial_naive(capsys):
    """Test naive factorial computation."""
    # Need CPU with "a" and "b" registers
    cpu = DT31(registers=["a", "b"])

    # Mock input() to return "5"
    with patch("builtins.input", side_effect=["5"]):
        cpu.run(factorial, debug=False)

    captured = capsys.readouterr()

    # Expected result: 5! = 120
    expected_output = "120\n"
    assert captured.out == expected_output


def test_factorial_with_labels(capsys):
    """Test factorial computation using labels for control flow."""
    # Need CPU with "a" and "b" registers
    cpu = DT31(registers=["a", "b"])

    # Mock input() to return "6"
    with patch("builtins.input", side_effect=["6"]):
        cpu.run(factorial_labels, debug=False)

    captured = capsys.readouterr()

    # Expected result: 6! = 720
    expected_output = "720\n"
    assert captured.out == expected_output


def test_fibonacci(capsys):
    """Test Fibonacci sequence generation."""
    # Need CPU with "a", "b", and "c" registers, starting at 0
    cpu = DT31(registers=["a", "b", "c"])

    # Mock input() to return "10" (generate first 10 Fibonacci numbers)
    with patch("builtins.input", side_effect=["10"]):
        cpu.run(fibonacci, debug=False)

    captured = capsys.readouterr()

    # Expected: first 10 Fibonacci numbers (0, 1, 1, 2, 3, 5, 8, 13, 21, 34)
    expected_output = "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n"
    assert captured.out == expected_output


def test_hello_world(capsys):
    """Test hello world program."""
    cpu = DT31(registers=[])

    cpu.run(hello_world, debug=False)
    captured = capsys.readouterr()
    assert captured.out == "hello, world!\n"


def test_simple_calculator(capsys):
    """Test simple calculator: (a + b) * (c + d)."""
    cpu = DT31(registers=["a", "b", "c", "d", "e"])

    # Mock input() to return "2", "3", "4", "5"
    # This should compute (2 + 3) * (4 + 5) = 5 * 9 = 45
    with patch("builtins.input", side_effect=["2", "3", "4", "5"]):
        cpu.run(calculator, debug=False)

    captured = capsys.readouterr()

    # Expected result: (2 + 3) * (4 + 5) = 45
    expected_output = "45\n"
    assert captured.out == expected_output


def test_sum_array(capsys):
    """Test sum array: reads numbers until 0, then sums them."""
    cpu = DT31(registers=["a", "b", "c"])

    # Mock input() to return "10", "20", "30", "0"
    # This should sum 10 + 20 + 30 = 60
    with patch("builtins.input", side_effect=["10", "20", "30", "0"]):
        cpu.run(sum_array, debug=False)

    captured = capsys.readouterr()

    # Expected result: 10 + 20 + 30 = 60
    expected_output = "60\n"
    assert captured.out == expected_output


def test_all_py_examples_are_tested():
    all_example_files = sorted([f.name for f in examples_dir.glob("*.py")])

    assert sorted(TESTED_PYTHON_PROGRAMS) == all_example_files


# Define expected outputs for each .dt file
# Format: filename -> (input_values, expected_output) or just expected_output if no input
DT_FILE_EXPECTED_IO = {
    "countdown.dt": (None, "5\n4\n3\n2\n1\n"),
    "factorial.dt": (["5"], "120\n"),
    "factorize.dt": (["12"], "2\n2\n3\n"),
    "hello.dt": (None, "Hello World!\n"),
}


@pytest.mark.parametrize(
    "dt_file",
    [f.name for f in examples_dir.glob("*.dt") if f.name in DT_FILE_EXPECTED_IO],
)
def test_dt_file(dt_file, capsys):
    """Test that .dt assembly files can be parsed and run."""
    test_data = DT_FILE_EXPECTED_IO[dt_file]

    dt_path = examples_dir / dt_file

    # Parse the program
    with open(dt_path) as f:
        assembly = f.read()

    program = parse_program(assembly)

    # Create CPU and run
    cpu = DT31()

    # Unpack test data
    input_values, expected_output = test_data

    if input_values is not None:
        # Mock input for programs that require it
        with patch("builtins.input", side_effect=input_values):
            cpu.run(program, debug=False)
    else:
        # Run without mocking input
        cpu.run(program, debug=False)

    # Check output
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_crash_dt():
    """Test that crash.dt raises a ZeroDivisionError as expected."""
    dt_path = examples_dir / "crash.dt"

    with open(dt_path) as f:
        assembly = f.read()

    program = parse_program(assembly)
    cpu = DT31()

    # The crash.dt program divides by zero
    with pytest.raises(ZeroDivisionError):
        cpu.run(program, debug=False)


def test_binomial_dist_dt(capsys):
    """Test that binomial_dist.dt runs without error.

    We don't check the exact output since it's random, but we verify:
    1. The program runs to completion
    2. It produces output
    3. The output is a valid number in the expected range
    """
    dt_path = examples_dir / "binomial_dist.dt"

    with open(dt_path) as f:
        assembly = f.read()

    program = parse_program(assembly)
    # Program uses: R.n, R.c, R.cc, R.s, R.r, R.avg
    cpu = DT31(registers=["n", "c", "cc", "s", "r", "avg"])

    # Mock input for n argument
    with patch("builtins.input", side_effect=["10"]):
        cpu.run(program, debug=False)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out

    # Verify we got output
    assert output, "binomial_dist.dt should produce output"

    # Verify output is a number (the average)
    lines = output.strip().split("\n")
    assert len(lines) == 1, "Should output exactly one line"

    result = int(lines[0])
    # For B(10, 0.5), the expected value is 5, but allow reasonable variance
    assert 0 <= result <= 10, f"Average should be between 0 and 10, got {result}"


def test_tictactoe_dt():
    dt_path = examples_dir / "tictactoe.dt"
    with open(dt_path) as f:
        assembly = f.read()
    parse_program(assembly)


def test_bf_dt():
    dt_path = examples_dir / "bf.dt"
    with open(dt_path) as f:
        assembly = f.read()
    parse_program(assembly)


TESTED_ASSEMBLY_PROGRAMS = list(DT_FILE_EXPECTED_IO.keys()) + [
    "bf.dt",
    "binomial_dist.dt",
    "crash.dt",
    "tictactoe.dt",
]


def test_all_asm_examples_are_tested():
    all_example_files = sorted([f.name for f in examples_dir.glob("*.dt")])

    assert sorted(TESTED_ASSEMBLY_PROGRAMS) == all_example_files
