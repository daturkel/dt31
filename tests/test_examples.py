import sys
from pathlib import Path
from unittest.mock import patch

from dt31 import DT31
from dt31.parser import parse_program

# Add the examples directory to the path so we can import from it
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))

from bitwise_operations import bitwise_ops  # type: ignore # noqa: E402
from conditional_logic import find_max  # type: ignore # noqa: E402
from custom_instructions import ASSEMBLY, CLAMP, SQUARE  # type: ignore # noqa: E402
from factorial_memoized import factorial_memoized  # type: ignore # noqa: E402
from hello_world import hello_world  # type: ignore # noqa: E402

TESTED_PROGRAMS = [
    "hello_world.py",
    "bitwise_operations.py",
    "conditional_logic.py",
    "custom_instructions.py",
    "factorial_memoized.py",
]


def test_hello_world(capsys, cpu):
    cpu.run(hello_world, debug=False)
    captured = capsys.readouterr()
    assert captured.out == "hello, world!\n"


def test_bitwise_ops(capsys, cpu):
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


def test_conditional_logic(capsys, cpu):
    """Test conditional logic with three numbers to find the maximum."""
    # Mock input() to return "5", "12", "8"
    with patch("builtins.input", side_effect=["5", "12", "8"]):
        cpu.run(find_max, debug=False)

    captured = capsys.readouterr()

    # Expected result: max(5, 12, 8) = 12
    expected_output = "12\n"
    assert captured.out == expected_output


def test_custom_instructions(capsys, cpu):
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
