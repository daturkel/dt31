"""Tests for the CLI."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from dt31.cli import main


@pytest.fixture
def temp_dt_file(tmp_path):
    """Create a temporary .dt file for testing."""

    def _create_file(content: str, filename: str = "test.dt"):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return str(file_path)

    return _create_file


def test_cli_auto_detects_registers(temp_dt_file, capsys):
    assembly = """
    CP 10, R.x
    CP 20, R.y
    ADD R.x, R.y
    NOUT R.x, 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "30" in captured.out


def test_cli_user_provided_registers_validated(temp_dt_file, capsys):
    assembly = """
    CP 10, R.x
    CP 20, R.y
    """
    file_path = temp_dt_file(assembly)

    # Provide registers that don't include 'y'
    with patch.object(sys, "argv", ["dt31", "--registers", "x,z", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Missing registers" in captured.err
    assert "y" in captured.err


def test_cli_parse_only(temp_dt_file, capsys):
    assembly = """
    CP 10, R.x
    NOUT R.x, 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "--parse-only", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "parsed successfully" in captured.err


def test_cli_file_not_found(capsys):
    with patch.object(sys, "argv", ["dt31", "nonexistent.dt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_cli_parse_error(temp_dt_file, capsys):
    assembly = "INVALID_INSTRUCTION R.x"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Parse error" in captured.err


def test_cli_no_registers_uses_defaults(temp_dt_file, capsys):
    assembly = """
    CP 42, R.a
    NOUT R.a, 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "42" in captured.out


def test_cli_custom_memory_size(temp_dt_file, capsys):
    assembly = """
    CP 99, [500]
    NOUT [500], 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "--memory", "1024", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "99" in captured.out


def test_cli_user_registers_superset_ok(temp_dt_file, capsys):
    assembly = """
    CP 5, R.x
    NOUT R.x, 1
    """
    file_path = temp_dt_file(assembly)

    # Provide extra registers beyond what's needed
    with patch.object(sys, "argv", ["dt31", "--registers", "x,y,z", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "5" in captured.out


def test_cli_io_error_reading_file(tmp_path, capsys):
    """Test IOError when reading file (permission denied, etc.)."""
    # Create a real file path that exists
    file_path = tmp_path / "test.dt"
    file_path.write_text("CP 1, R.a")

    # Mock Path.read_text to raise IOError
    with patch("dt31.cli.Path") as mock_path:
        mock_path_instance = MagicMock()
        mock_path_instance.read_text.side_effect = IOError("Permission denied")
        mock_path.return_value = mock_path_instance

        with patch.object(sys, "argv", ["dt31", str(file_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err
    assert "Permission denied" in captured.err


def test_cli_cpu_creation_error(temp_dt_file, capsys):
    """Test error during CPU creation (invalid memory size, etc.)."""
    assembly = """
    CP 1, R.a
    """
    file_path = temp_dt_file(assembly)

    # Pass invalid memory size to trigger real error
    with patch.object(sys, "argv", ["dt31", "--memory", "0", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error creating CPU" in captured.err


def test_cli_keyboard_interrupt(temp_dt_file, capsys):
    """Test handling of KeyboardInterrupt (Ctrl+C) during execution."""
    assembly = """
    CP 1, R.a
    NOUT R.a, 1
    """
    file_path = temp_dt_file(assembly)

    # Mock CPU.run to raise KeyboardInterrupt
    with patch("dt31.cli.DT31") as mock_dt31_class:
        mock_cpu = MagicMock()
        mock_cpu.run.side_effect = KeyboardInterrupt()
        mock_dt31_class.return_value = mock_cpu

        with patch.object(sys, "argv", ["dt31", file_path]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 130
    captured = capsys.readouterr()
    assert "Execution interrupted" in captured.err


def test_cli_runtime_error_without_debug(temp_dt_file, capsys):
    """Test runtime error handling without debug mode."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    file_path = temp_dt_file(assembly)

    # Trigger real division by zero error
    with patch.object(sys, "argv", ["dt31", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Runtime error" in captured.err
    # Without --debug, should not show CPU state
    assert "CPU state at error" not in captured.err


def test_cli_runtime_error_with_debug(temp_dt_file, capsys):
    """Test runtime error handling with debug mode enabled."""
    assembly = """
    CP 999, R.a
    CP [R.a], R.b
    """
    file_path = temp_dt_file(assembly)

    # Trigger real memory access error (address 999 is out of bounds)
    with patch.object(sys, "argv", ["dt31", "--debug", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Runtime error" in captured.err
    # With --debug, should show CPU state
    assert "CPU state at error" in captured.err
    assert "Registers:" in captured.err
    assert "Stack size:" in captured.err


def test_custom_instructions_basic(tmp_path, capsys) -> None:
    """Test loading and using basic custom instruction."""
    # Create custom instruction file
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import UnaryOperation
from dt31.operands import Operand, Reference

class DOUBLE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("DOUBLE", a, out)
        self.a = a

    def _calc(self, cpu) -> int:
        val = self.a.resolve(cpu)
        result = val * 2
        return result

INSTRUCTIONS = {"DOUBLE": DOUBLE}
"""
    )

    # Create program file
    program_file = tmp_path / "program.dt"
    program_file.write_text(
        """
CP 5, R.a
DOUBLE R.a
NOUT R.a, 1
"""
    )

    # Run CLI
    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "10" in captured.out


def test_custom_instructions_file_not_found(tmp_path, capsys) -> None:
    """Test error handling when custom instructions file doesn't exist."""
    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 1, R.a")

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", "nonexistent.py", str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "not found" in captured.err


def test_custom_instructions_missing_dict(tmp_path, capsys) -> None:
    """Test error handling when INSTRUCTIONS dict is missing."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import Instruction

class MYINST(Instruction):
    def __init__(self):
        super().__init__("MYINST")

    def _calc(self, cpu):
        return 0

# Missing INSTRUCTIONS dict
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 1, R.a")

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "must define an INSTRUCTIONS dict" in captured.err


def test_custom_instructions_invalid_class(tmp_path, capsys) -> None:
    """Test error handling when INSTRUCTIONS contains non-Instruction class."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
class NotAnInstruction:
    pass

INSTRUCTIONS = {"BAD": NotAnInstruction}
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 1, R.a")

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "must be a subclass of Instruction" in captured.err


def test_custom_instructions_wrong_type(tmp_path, capsys) -> None:
    """Test error handling when INSTRUCTIONS is not a dict."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
INSTRUCTIONS = ["not", "a", "dict"]
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 1, R.a")

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "must be a dict" in captured.err


def test_custom_instructions_multiple_instructions(tmp_path, capsys) -> None:
    """Test loading multiple custom instructions at once."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import UnaryOperation
from dt31.operands import Operand, Reference

class TRIPLE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("TRIPLE", a, out)

    def _calc(self, cpu):
        return self.a.resolve(cpu) * 3

class QUADRUPLE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("QUADRUPLE", a, out)

    def _calc(self, cpu):
        return self.a.resolve(cpu) * 4

INSTRUCTIONS = {"TRIPLE": TRIPLE, "QUADRUPLE": QUADRUPLE}
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text(
        """
CP 5, R.a
TRIPLE R.a
NOUT R.a, 1
CP 3, R.b
QUADRUPLE R.b
NOUT R.b, 1
"""
    )

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "15" in captured.out
    assert "12" in captured.out


def test_custom_instructions_override_builtin(tmp_path, capsys) -> None:
    """Test that custom instructions can override built-in instructions."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import BinaryOperation
from dt31.operands import Operand, Reference

# Override ADD to multiply instead
class ADD(BinaryOperation):
    def __init__(self, a: Operand, b: Operand, out: Reference | None = None):
        super().__init__("ADD", a, b, out)

    def _calc(self, cpu):
        return self.a.resolve(cpu) * self.b.resolve(cpu)

INSTRUCTIONS = {"ADD": ADD}
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text(
        """
CP 5, R.a
CP 3, R.b
ADD R.a, R.b
NOUT R.a, 1
"""
    )

    with patch.object(
        sys,
        "argv",
        ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # If ADD was not overridden, result would be 8
    # With override, result is 5 * 3 = 15
    assert "15" in captured.out


def test_custom_instructions_with_parse_only(tmp_path, capsys) -> None:
    """Test that custom instructions work with --parse-only flag."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import UnaryOperation
from dt31.operands import Operand, Reference

class SQUARE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("SQUARE", a, out)

    def _calc(self, cpu):
        val = self.a.resolve(cpu)
        return val * val

INSTRUCTIONS = {"SQUARE": SQUARE}
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text(
        """
CP 7, R.a
SQUARE R.a
NOUT R.a, 1
"""
    )

    with patch.object(
        sys,
        "argv",
        [
            "dt31",
            "--parse-only",
            "--custom-instructions",
            str(custom_file),
            str(program_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "parsed successfully" in captured.err


def test_custom_instructions_debug_output(tmp_path, capsys) -> None:
    """Test debug output when loading custom instructions."""
    # Create custom instruction file with multiple instructions
    custom_file = tmp_path / "custom.py"
    custom_file.write_text(
        """
from dt31.instructions import UnaryOperation
from dt31.operands import Operand, Reference

class DOUBLE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("DOUBLE", a, out)

    def _calc(self, cpu):
        return self.a.resolve(cpu) * 2

class TRIPLE(UnaryOperation):
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("TRIPLE", a, out)

    def _calc(self, cpu):
        return self.a.resolve(cpu) * 3

INSTRUCTIONS = {"DOUBLE": DOUBLE, "TRIPLE": TRIPLE}
"""
    )

    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 5, R.a")

    # Use --parse-only with --debug to avoid interactive execution
    with patch.object(
        sys,
        "argv",
        [
            "dt31",
            "--debug",
            "--parse-only",
            "--custom-instructions",
            str(custom_file),
            str(program_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # Check stderr for the debug message
    assert "Loaded 2 custom instruction(s):" in captured.err
    assert "DOUBLE" in captured.err
    assert "TRIPLE" in captured.err


def test_custom_instructions_import_error(tmp_path, capsys) -> None:
    """Test error handling when module cannot be loaded (spec is None)."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text("# valid python file")

    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 1, R.a")

    # Mock spec_from_file_location to return None
    with patch("dt31.cli.importlib.util.spec_from_file_location") as mock_spec:
        mock_spec.return_value = None

        with patch.object(
            sys,
            "argv",
            ["dt31", "--custom-instructions", str(custom_file), str(program_file)],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "Could not load module" in captured.err
