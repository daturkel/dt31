#!/usr/bin/env python3
"""Smoke tests for dt31 package.

Quick verification that basic functionality works. Designed to be run in isolation
against an installed wheel or source distribution to ensure the package was built
correctly with all necessary files included.

Run with:
    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py
"""

import sys
from io import StringIO


def test_basic_imports():
    """Test that all core modules can be imported."""
    try:
        from dt31 import DT31, LC, I, L, Label, M, R  # noqa: F401
        from dt31.assembler import assemble, program_to_text  # noqa: F401
        from dt31.instructions import ADD, CP, NOUT  # noqa: F401
        from dt31.operands import (  # noqa: F401
            Literal,
            MemoryReference,
            RegisterReference,
        )
        from dt31.parser import parse_program  # noqa: F401

        print("✓ All core modules imported successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        assert False


def test_basic_execution():
    """Test basic program execution."""
    try:
        from dt31 import DT31, I, L, R

        cpu = DT31()
        program = [
            I.CP(42, R.a),
            I.NOUT(R.a, L[0]),
        ]

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()

        cpu.run(program)

        sys.stdout = old_stdout
        output = captured.getvalue()

        if output.strip() == "42":
            print("✓ Basic program execution works")
        else:
            print(f"✗ Program output incorrect: expected '42', got '{output.strip()}'")
            assert False
    except Exception as e:
        sys.stdout = old_stdout
        print(f"✗ Basic execution failed: {e}")
        assert False


def test_parser():
    """Test assembly text parsing."""
    try:
        from dt31 import DT31
        from dt31.parser import parse_program

        cpu = DT31()
        assembly = """
        CP 5, R.a
        NOUT R.a, 1
        """

        program = parse_program(assembly)

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()

        cpu.run(program)

        sys.stdout = old_stdout
        output = captured.getvalue()

        if output.strip() == "5":
            print("✓ Parser works")
        else:
            print(f"✗ Parser output incorrect: expected '5', got '{output.strip()}'")
            assert False
    except Exception as e:
        sys.stdout = old_stdout
        print(f"✗ Parser test failed: {e}")
        assert False


def test_labels():
    """Test label resolution in assembly."""
    try:
        from dt31 import DT31, I, L, Label, R

        cpu = DT31()
        program = [
            I.CP(3, R.a),
            loop := Label("loop"),
            I.SUB(R.a, L[1]),
            I.JGT(loop, R.a, L[0]),
        ]

        cpu.run(program)

        if cpu.get_register("a") == 0:
            print("✓ Label resolution works")
        else:
            print(
                f"✗ Label test failed: register a = {cpu.get_register('a')}, expected 0"
            )
            assert False
    except Exception as e:
        print(f"✗ Label test failed: {e}")
        assert False


def test_stack_operations():
    """Test stack push/pop."""
    try:
        from dt31 import DT31, I, R

        cpu = DT31()
        program = [
            I.CP(42, R.a),
            I.PUSH(R.a),
            I.CP(0, R.a),
            I.POP(R.a),
        ]

        cpu.run(program)

        if cpu.get_register("a") == 42:
            print("✓ Stack operations work")
        else:
            print(
                f"✗ Stack test failed: register a = {cpu.get_register('a')}, expected 42"
            )
            assert False
    except Exception as e:
        print(f"✗ Stack test failed: {e}")
        assert False


def test_memory_operations():
    """Test memory read/write."""
    try:
        from dt31 import DT31, I, M, R

        cpu = DT31()
        program = [
            I.CP(99, M[10]),
            I.CP(M[10], R.a),
        ]

        cpu.run(program)

        if cpu.get_register("a") == 99:
            print("✓ Memory operations work")
        else:
            print(
                f"✗ Memory test failed: register a = {cpu.get_register('a')}, expected 99"
            )
            assert False
    except Exception as e:
        print(f"✗ Memory test failed: {e}")
        assert False


def test_program_to_text():
    """Test program to text conversion."""
    try:
        from dt31 import I, L, Label, R
        from dt31.assembler import program_to_text

        program = [
            I.CP(5, R.a),
            loop := Label("loop"),
            I.SUB(R.a, L[1]),
            I.JGT(loop, R.a, L[0]),
        ]

        text = program_to_text(program)

        if "CP 5, R.a" in text and "loop:" in text and "JGT" in text:
            print("✓ Program to text conversion works")
        else:
            print(f"✗ Program to text failed: unexpected output\n{text}")
            assert False
    except Exception as e:
        print(f"✗ Program to text test failed: {e}")
        assert False


def main():
    """Run all smoke tests."""
    print("Running dt31 smoke tests...")
    print()

    tests = [
        test_basic_imports,
        test_basic_execution,
        test_parser,
        test_labels,
        test_stack_operations,
        test_memory_operations,
        test_program_to_text,
    ]

    results = [test() for test in tests]

    print()
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"All {total} smoke tests passed! ✓")
        sys.exit(0)
    else:
        print(f"{passed}/{total} smoke tests passed, {total - passed} failed ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
