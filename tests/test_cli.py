"""Tests for the CLI."""

import os
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

    with patch.object(sys, "argv", ["dt31", "run", file_path]):
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
    with patch.object(sys, "argv", ["dt31", "run", "--registers", "x,z", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Missing registers" in captured.err
    assert "y" in captured.err


def test_check_valid_file(temp_dt_file, capsys):
    """Test check command with valid file."""
    assembly = """
    CP 10, R.x
    NOUT R.x, 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "check", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "is valid" in captured.err


def test_cli_file_not_found(capsys):
    with patch.object(sys, "argv", ["dt31", "run", "nonexistent.dt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_cli_parse_error(temp_dt_file, capsys):
    assembly = "INVALID_INSTRUCTION R.x"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "run", file_path]):
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

    with patch.object(sys, "argv", ["dt31", "run", file_path]):
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

    with patch.object(sys, "argv", ["dt31", "run", "--memory", "1024", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "99" in captured.out


def test_cli_custom_stack_size(temp_dt_file, capsys):
    """Test --stack-size option."""
    assembly = """
    CP 42, R.a
    PUSH R.a
    POP R.b
    NOUT R.b, 1
    """
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "run", "--stack-size", "512", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "42" in captured.out


def test_cli_user_registers_superset_ok(temp_dt_file, capsys):
    assembly = """
    CP 5, R.x
    NOUT R.x, 1
    """
    file_path = temp_dt_file(assembly)

    # Provide extra registers beyond what's needed
    with patch.object(sys, "argv", ["dt31", "run", "--registers", "x,y,z", file_path]):
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

        with patch.object(sys, "argv", ["dt31", "run", str(file_path)]):
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
    with patch.object(sys, "argv", ["dt31", "run", "--memory", "0", file_path]):
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

        with patch.object(sys, "argv", ["dt31", "run", file_path]):
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
    with patch.object(sys, "argv", ["dt31", "run", file_path]):
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
    with patch.object(sys, "argv", ["dt31", "run", "--debug", file_path]):
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
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
        ["dt31", "run", "--custom-instructions", "nonexistent.py", str(program_file)],
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
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
        ["dt31", "run", "--custom-instructions", str(custom_file), str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # If ADD was not overridden, result would be 8
    # With override, result is 5 * 3 = 15
    assert "15" in captured.out


def test_check_with_custom_instructions(tmp_path, capsys) -> None:
    """Test that custom instructions work with check command."""
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
            "check",
            "--custom-instructions",
            str(custom_file),
            str(program_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "is valid" in captured.err


def test_check_parse_error(temp_dt_file, capsys) -> None:
    """Test check command with parse error."""
    assembly = "INVALID_INSTRUCTION R.x"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "check", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Parse error" in captured.err


def test_check_file_not_found(capsys) -> None:
    """Test check command with nonexistent file."""
    with patch.object(sys, "argv", ["dt31", "check", "nonexistent.dt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_check_custom_instructions_error(tmp_path, capsys) -> None:
    """Test check command with invalid custom instructions file."""
    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 5, R.a")

    with patch.object(
        sys,
        "argv",
        ["dt31", "check", "--custom-instructions", "nonexistent.py", str(program_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err


def test_check_io_error_reading_file(tmp_path, capsys) -> None:
    """Test IOError when reading file with check command (permission denied, etc.)."""
    # Create a real file path that exists
    file_path = tmp_path / "test.dt"
    file_path.write_text("CP 1, R.a")

    # Mock Path.read_text to raise IOError
    with patch("dt31.cli.Path") as mock_path:
        mock_path_instance = MagicMock()
        mock_path_instance.read_text.side_effect = IOError("Permission denied")
        mock_path.return_value = mock_path_instance

        with patch.object(sys, "argv", ["dt31", "check", str(file_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err
    assert "Permission denied" in captured.err


def test_custom_instructions_debug_output(tmp_path, capsys) -> None:
    """Test debug output when loading custom instructions with run command."""
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

    # Mock DT31.run to avoid interactive debug mode
    with patch("dt31.cli.DT31") as mock_dt31_class:
        mock_cpu = MagicMock()
        mock_cpu.run.return_value = None
        mock_dt31_class.return_value = mock_cpu

        with patch.object(
            sys,
            "argv",
            [
                "dt31",
                "run",
                "--debug",
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
            [
                "dt31",
                "run",
                "--custom-instructions",
                str(custom_file),
                str(program_file),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err
    assert "Could not load module" in captured.err


def test_dump_on_error_with_explicit_path(temp_dt_file, tmp_path, capsys):
    """Test --dump error with explicit file path."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "my_crash.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Runtime error" in captured.err
    assert f"CPU state dumped to: {dump_path}" in captured.err

    # Verify dump file was created and contains expected data
    assert dump_path.exists()
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert "cpu_state" in dump_data
    assert "error" in dump_data
    assert dump_data["error"]["type"] == "ZeroDivisionError"
    assert "instruction" in dump_data["error"]  # New: includes last instruction
    assert dump_data["cpu_state"]["registers"]["a"] == 10
    assert dump_data["cpu_state"]["registers"]["b"] == 0


def test_dump_on_error_auto_generate_filename(
    temp_dt_file, tmp_path, capsys, monkeypatch
):
    """Test --dump-on-error with auto-generated filename."""
    assembly = """
    CP 999, R.a
    CP [R.a], R.b
    """
    file_path = temp_dt_file(assembly, "countdown.dt")

    # Change to temp directory so auto-generated file goes there
    monkeypatch.chdir(tmp_path)

    # Use -- to separate flag from positional argument
    with patch.object(sys, "argv", ["dt31", "run", "--dump", "error", "--", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Runtime error" in captured.err
    assert "CPU state dumped to: countdown_crash_" in captured.err

    # Find the generated file
    dump_files = list(tmp_path.glob("countdown_crash_*.json"))
    assert len(dump_files) == 1

    # Verify dump file contains expected data
    import json

    with open(dump_files[0]) as f:
        dump_data = json.load(f)

    assert "cpu_state" in dump_data
    assert "error" in dump_data
    assert "memory has no index 999" in dump_data["error"]["message"]


def test_dump_on_error_not_triggered_on_success(temp_dt_file, tmp_path, capsys):
    """Test that --dump-on-error doesn't create file on successful execution."""
    assembly = """
    CP 42, R.a
    NOUT R.a, 1
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "should_not_exist.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "42" in captured.out
    # Dump file should not exist
    assert not dump_path.exists()


def test_dump_on_error_includes_traceback(temp_dt_file, tmp_path, capsys):
    """Test that dump includes full traceback."""
    assembly = """
    PUSH 1
    PUSH 2
    POP R.a
    POP R.a
    POP R.a
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "stack_underflow.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1

    # Verify dump contains traceback
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert "traceback" in dump_data["error"]
    assert "stack underflow" in dump_data["error"]["message"]
    assert len(dump_data["error"]["traceback"]) > 0


def test_dump_on_error_write_failure(temp_dt_file, tmp_path, capsys):
    """Test handling of write failure when dumping crash state."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    file_path = temp_dt_file(assembly)
    dump_path = "/invalid/path/crash.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", dump_path, file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Runtime error" in captured.err
    # Should report failure to dump
    assert "Failed to dump CPU state" in captured.err


def test_dump_on_error_with_program_loaded(temp_dt_file, tmp_path, capsys):
    """Test that dump includes the loaded program."""
    assembly = """
    CP 5, R.x
    CP 3, R.y
    CP 0, R.z
    DIV R.x, R.z
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "program_dump.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1

    # Verify dump includes program
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert dump_data["cpu_state"]["program"] is not None
    assert "CP 5, R.x" in dump_data["cpu_state"]["program"]
    assert "DIV R.x, R.z" in dump_data["cpu_state"]["program"]


def test_dump_on_exit_with_explicit_path(temp_dt_file, tmp_path, capsys):
    """Test --dump-on-exit with explicit file path."""
    assembly = """
    CP 10, R.a
    CP 5, R.b
    ADD R.a, R.b
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "final_state.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "success", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"CPU state dumped to: {dump_path}" in captured.err

    # Verify dump file was created and contains expected data
    assert dump_path.exists()
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert "cpu_state" in dump_data
    assert "error" not in dump_data  # No error on successful execution
    assert dump_data["cpu_state"]["registers"]["a"] == 15
    assert dump_data["cpu_state"]["registers"]["b"] == 5


def test_dump_on_exit_auto_generate_filename(
    temp_dt_file, tmp_path, capsys, monkeypatch
):
    """Test --dump-on-exit with auto-generated filename."""
    assembly = """
    CP 42, R.x
    """
    file_path = temp_dt_file(assembly, "myprogram.dt")

    # Change to temp directory so auto-generated file goes there
    monkeypatch.chdir(tmp_path)

    with patch.object(
        sys, "argv", ["dt31", "run", "--dump", "success", "--", file_path]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "CPU state dumped to: myprogram_final_" in captured.err

    # Find the generated file
    dump_files = list(tmp_path.glob("myprogram_final_*.json"))
    assert len(dump_files) == 1

    # Verify dump file contains expected data
    import json

    with open(dump_files[0]) as f:
        dump_data = json.load(f)

    assert "cpu_state" in dump_data
    assert "error" not in dump_data
    assert dump_data["cpu_state"]["registers"]["x"] == 42


def test_dump_all_mode_on_error(temp_dt_file, tmp_path, capsys):
    """Test --dump all mode (only error triggers on crash)."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    file_path = temp_dt_file(assembly)

    # Don't specify dump-file, let it auto-generate
    with patch.object(
        sys,
        "argv",
        [
            "dt31",
            "run",
            "--dump",
            "all",
            file_path,
        ],
    ):
        # Change to temp directory for auto-generated file
        import os

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
        finally:
            os.chdir(old_cwd)

    assert exc_info.value.code == 1

    # Should have created a crash dump
    crash_dumps = list(tmp_path.glob("*_crash_*.json"))
    assert len(crash_dumps) == 1


def test_dump_on_exit_with_successful_program(temp_dt_file, tmp_path, capsys):
    """Test --dump-on-exit captures final state after successful execution."""
    assembly = """
    CP 1, R.counter
    loop:
        ADD R.counter, 1
        JGT loop, 5, R.counter
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "final.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "success", "--dump-file", str(dump_path), file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    # Verify final state
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert dump_data["cpu_state"]["registers"]["counter"] == 5


def test_dump_on_exit_write_failure(temp_dt_file, capsys):
    """Test handling of write failure when dumping on exit."""
    assembly = """
    CP 42, R.a
    """
    file_path = temp_dt_file(assembly)
    dump_path = "/invalid/path/final.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "success", "--dump-file", dump_path, file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    # Should still exit successfully even if dump fails
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Failed to dump CPU state" in captured.err


def test_dump_error_with_ip_past_end(temp_dt_file, tmp_path, capsys):
    """Test that dump includes last instruction when IP goes past program end."""
    assembly = """
    CP 10, R.a
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "past_end.json"

    # Mock CPU to raise error after IP increments past end

    original_main = main

    def patched_main():
        # Run normally but catch at the right point
        original_main()

    # Create a scenario where IP is past the end
    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        # Patch the CPU run to simulate EndOfProgram error with IP past end
        from dt31 import DT31

        def run_with_error(self, *args, **kwargs):
            # Execute normally first
            self.load(args[0] if args else kwargs.get("program"))
            # Set IP past the end
            self.set_register("ip", len(self.instructions) + 5)
            # Raise an error
            raise RuntimeError("Simulated error with IP past end")

        with patch.object(DT31, "run", run_with_error):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1

    # Verify dump contains the last instruction
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    assert "instruction" in dump_data["error"]
    assert "repr" in dump_data["error"]["instruction"]
    assert "str" in dump_data["error"]["instruction"]
    assert "CP" in dump_data["error"]["instruction"]["repr"]
    assert "R.a" in dump_data["error"]["instruction"]["repr"]


def test_dump_error_instruction_retrieval_fails(temp_dt_file, tmp_path, capsys):
    """Test that dump succeeds even if instruction retrieval fails."""
    assembly = """
    CP 10, R.a
    CP 0, R.b
    DIV R.a, R.b
    """
    file_path = temp_dt_file(assembly)
    dump_path = tmp_path / "retrieval_fails.json"

    with patch.object(
        sys,
        "argv",
        ["dt31", "run", "--dump", "error", "--dump-file", str(dump_path), file_path],
    ):
        # Patch get_register to raise an exception
        from dt31 import DT31

        original_get_register = DT31.get_register

        def failing_get_register(self, name):
            if name == "ip":
                raise RuntimeError("Cannot get IP")
            return original_get_register(self, name)

        with patch.object(DT31, "get_register", failing_get_register):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1

    # Verify dump was created despite instruction retrieval failure
    import json

    with open(dump_path) as f:
        dump_data = json.load(f)

    # Should still have error info, just no instruction
    assert "error" in dump_data
    assert "instruction" not in dump_data["error"]


# ===== Format Command Tests =====


def test_format_basic(temp_dt_file, capsys):
    """Test basic formatting in-place."""
    assembly = "CP 5,R.a\nNOUT R.a,1"  # Unformatted
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"✓ Formatted {file_path}" in captured.err

    # Read formatted file
    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "    CP 5, R.a" in formatted
    assert "    NOUT R.a, 1" in formatted


def test_format_already_formatted(temp_dt_file, capsys):
    """Test file that's already formatted."""
    assembly = (
        "    CP 5, R.a\n    NOUT R.a, 1\n"  # Already formatted with trailing newline
    )
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"✓ {file_path} is already formatted" in captured.err


def test_format_check_needs_formatting(temp_dt_file, capsys):
    """Test --check mode with file needing formatting."""
    assembly = "CP 5,R.a"  # Unformatted
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--check", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1  # Exit with error code
    captured = capsys.readouterr()
    assert f"✗ {file_path} would be reformatted" in captured.err

    # Verify file was NOT modified
    from pathlib import Path

    unchanged = Path(file_path).read_text()
    assert unchanged == "CP 5,R.a"


def test_format_check_already_formatted(temp_dt_file, capsys):
    """Test --check mode with file already formatted."""
    assembly = "    CP 5, R.a\n"  # With trailing newline
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--check", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"✓ {file_path} is already formatted" in captured.err


def test_format_diff_shows_changes(temp_dt_file, capsys):
    """Test --diff mode shows unified diff."""
    assembly = "CP 5,R.a"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--diff", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # Should show diff in stdout
    assert "---" in captured.out
    assert "+++" in captured.out
    assert "-CP 5,R.a" in captured.out
    assert "+    CP 5, R.a" in captured.out

    # File should NOT be modified
    from pathlib import Path

    unchanged = Path(file_path).read_text()
    assert unchanged == "CP 5,R.a"


def test_format_diff_no_changes(temp_dt_file, capsys):
    """Test --diff mode with no changes."""
    assembly = "    CP 5, R.a\n"  # With trailing newline
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--diff", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"✓ {file_path} is already formatted" in captured.err
    assert "---" not in captured.out  # No diff output


def test_format_check_and_diff(temp_dt_file, capsys):
    """Test combining --check and --diff."""
    assembly = "CP 5,R.a"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--check", "--diff", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1  # Should fail check
    captured = capsys.readouterr()
    # Should show diff
    assert "---" in captured.out
    assert "+++" in captured.out


def test_format_indent_size(temp_dt_file, capsys):
    """Test --indent-size option."""
    assembly = "CP 5, R.a"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--indent-size", "2", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "  CP 5, R.a" in formatted  # 2 spaces, not 4


def test_format_comment_spacing(temp_dt_file, capsys):
    """Test --comment-margin option."""
    assembly = """
CP 5, R.a ; Initialize
"""
    file_path = temp_dt_file(assembly)

    with patch.object(
        sys, "argv", ["dt31", "format", "--comment-margin", "3", file_path]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "    CP 5, R.a   ; Initialize" in formatted  # 3 spaces before ;


def test_format_label_inline(temp_dt_file, capsys):
    """Test --label-inline option."""
    assembly = """
loop:
CP 5, R.a
"""
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", "--label-inline", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "loop: CP 5, R.a" in formatted  # Label on same line


def test_format_no_blank_line_before_label(temp_dt_file, capsys):
    """Test --no-blank-line-before-label option."""
    assembly = """
CP 5, R.a
loop:
ADD R.a, 1
"""
    file_path = temp_dt_file(assembly)

    with patch.object(
        sys, "argv", ["dt31", "format", "--no-blank-line-before-label", file_path]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    lines = formatted.strip().split("\n")
    # Should NOT have blank line between instruction and label
    assert len(lines) == 3  # 3 lines total, no blank line


def test_format_align_comments(temp_dt_file, capsys):
    """Test --align-comments option with explicit column."""
    assembly = "CP 5, R.a ; Test1\nCP 6, R.b ; Test2"
    file_path = temp_dt_file(assembly)

    with patch.object(
        sys,
        "argv",
        ["dt31", "format", "--align-comments", "--comment-column", "40", file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    # Both instructions are short enough to align at column 40
    # Check that comments are aligned (both at same column)
    lines = [l for l in formatted.split("\n") if ";" in l]  # noqa: E741
    comment_positions = [line.index(";") for line in lines]

    # All comments should be at the same position
    assert len(set(comment_positions)) == 1, (
        f"Comments not aligned: {comment_positions}"
    )
    # And that position should be at column 40
    assert comment_positions[0] == 40, (
        f"Comment position {comment_positions[0]} not at 40"
    )


def test_format_comment_column(temp_dt_file, capsys):
    """Test --comment-column option."""
    assembly = """
CP 5, R.a ; Test
"""
    file_path = temp_dt_file(assembly)

    with patch.object(
        sys,
        "argv",
        ["dt31", "format", "--align-comments", "--comment-column", "30", file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    # Comment should start at column 30
    assert formatted.index(";") == 30


def test_format_auto_align_comments(temp_dt_file, capsys):
    """Test auto-align comments (without explicit --comment-column)."""
    assembly = "CP 5, R.a ; Short\nADD R.a, R.b, R.c ; Longer"
    file_path = temp_dt_file(assembly)

    # Use --align-comments without --comment-column to trigger auto-calculation
    with patch.object(sys, "argv", ["dt31", "format", "--align-comments", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    lines = [l for l in formatted.split("\n") if ";" in l]  # noqa: E741

    # Both comments should be aligned at the same position
    comment_positions = [line.index(";") for line in lines]
    assert len(set(comment_positions)) == 1, (
        f"Comments not aligned: {comment_positions}"
    )

    # The position should be based on longest instruction + default margin (2)
    # Longest line is "    ADD R.a, R.b, R.c" = 21 chars
    # So comments should be at 21 + 2 = 23
    assert comment_positions[0] == 23


def test_format_comment_margin(temp_dt_file, capsys):
    """Test --comment-margin option."""
    assembly = "CP 5, R.a ; Test1\nCP 6, R.b ; Test2"
    file_path = temp_dt_file(assembly)

    # Use custom margin of 4 with auto-align
    with patch.object(
        sys,
        "argv",
        ["dt31", "format", "--align-comments", "--comment-margin", "4", file_path],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    lines = [l for l in formatted.split("\n") if ";" in l]  # noqa: E741

    # Comments should be aligned with margin of 4
    # Longest line is "    CP 6, R.b" = 13 chars
    # So comments should be at 13 + 4 = 17
    comment_positions = [line.index(";") for line in lines]
    assert comment_positions[0] == 17


def test_format_show_default_args(temp_dt_file, capsys):
    """Test --show-default-args option."""
    assembly = """
ADD R.a, R.b
NOUT R.a
"""
    file_path = temp_dt_file(assembly)

    with patch.object(
        sys, "argv", ["dt31", "format", "--show-default-args", file_path]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "    ADD R.a, R.b, R.a" in formatted  # Default out shown
    assert "    NOUT R.a, 0" in formatted  # Default b shown


def test_format_io_error_reading_file(tmp_path, capsys):
    """Test IOError when reading file for formatting (permission denied, etc.)."""
    # Create a real file path that exists
    file_path = tmp_path / "test.dt"
    file_path.write_text("CP 1, R.a")

    # Mock Path.read_text to raise IOError
    with patch("dt31.cli.Path") as mock_path:
        mock_path_instance = MagicMock()
        mock_path_instance.read_text.side_effect = IOError("Permission denied")
        mock_path.return_value = mock_path_instance

        with patch.object(sys, "argv", ["dt31", "format", str(file_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err
    assert "Permission denied" in captured.err


def test_format_file_not_found(capsys):
    """Test format with nonexistent file."""
    with patch.object(sys, "argv", ["dt31", "format", "nonexistent.dt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_format_parse_error(temp_dt_file, capsys):
    """Test format with invalid syntax."""
    assembly = "INVALID_INSTRUCTION R.x"
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Parse error" in captured.err


def test_format_preserves_comments(temp_dt_file, capsys):
    """Test that formatting preserves comments."""
    assembly = """
; This is a standalone comment
CP 5, R.a ; inline comment
loop:     ; label comment
    ADD R.a, 1
"""
    file_path = temp_dt_file(assembly)

    with patch.object(sys, "argv", ["dt31", "format", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    from pathlib import Path

    formatted = Path(file_path).read_text()
    assert "; This is a standalone comment" in formatted
    assert "; inline comment" in formatted
    assert "; label comment" in formatted


def test_format_custom_instructions(tmp_path, capsys):
    """Test format with custom instructions."""
    # Create custom instruction file
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

INSTRUCTIONS = {"DOUBLE": DOUBLE}
"""
    )

    # Create program file
    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 5,R.a\nDOUBLE R.a")

    with patch.object(
        sys,
        "argv",
        [
            "dt31",
            "format",
            "--custom-instructions",
            str(custom_file),
            str(program_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0

    # Verify formatting worked
    formatted = program_file.read_text()
    assert "    CP 5, R.a" in formatted
    assert "    DOUBLE R.a" in formatted


def test_format_custom_instructions_error(tmp_path, capsys):
    """Test format with invalid custom instructions file."""
    program_file = tmp_path / "program.dt"
    program_file.write_text("CP 5, R.a")

    with patch.object(
        sys,
        "argv",
        [
            "dt31",
            "format",
            "--custom-instructions",
            "nonexistent.py",
            str(program_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading custom instructions" in captured.err


def test_format_empty_file(temp_dt_file, capsys):
    """Test formatting an empty file."""
    file_path = temp_dt_file("")

    with patch.object(sys, "argv", ["dt31", "format", file_path]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "is already formatted" in captured.err


def test_format_io_error_writing_file(tmp_path, capsys):
    """Test IOError when writing formatted file (permission denied, disk full, etc.)."""
    # Create a file that needs formatting
    file_path = tmp_path / "test.dt"
    file_path.write_text("CP 5,R.a")  # Unformatted

    # Mock Path.write_text to raise IOError
    with patch("dt31.cli.Path") as mock_path_class:
        # Create a mock Path instance
        mock_path = MagicMock()

        # read_text should succeed (return unformatted content)
        mock_path.read_text.return_value = "CP 5,R.a"

        # write_text should raise IOError
        mock_path.write_text.side_effect = IOError("Permission denied")

        # Make Path() constructor return our mock
        mock_path_class.return_value = mock_path

        with patch.object(sys, "argv", ["dt31", "format", str(file_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error writing to" in captured.err
    assert "Permission denied" in captured.err


def test_cli_unknown_command(capsys):
    """Test behavior with unknown/invalid command."""
    # Directly test the else branch by patching parse_args to return invalid command
    import argparse

    with patch("dt31.cli.argparse.ArgumentParser.parse_args") as mock_parse_args:
        # Create a mock args object with an unexpected command
        mock_args = argparse.Namespace(command="unknown")
        mock_parse_args.return_value = mock_args

        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    # The help message should be printed (captured in stderr by argparse)
    # but we can't easily verify it since parser.print_help() goes directly to stdout


# ===== Globbing Tests =====


def test_check_multiple_files(temp_dt_file, capsys):
    """Test check command with multiple files."""
    file1 = temp_dt_file("CP 10, R.a", "file1.dt")
    file2 = temp_dt_file("CP 20, R.b", "file2.dt")

    with patch.object(sys, "argv", ["dt31", "check", file1, file2]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "file1.dt is valid" in captured.err
    assert "file2.dt is valid" in captured.err
    assert "All 2 file(s) are valid" in captured.err


def test_check_multiple_files_with_errors(tmp_path, capsys):
    """Test check command with multiple files where some have errors."""
    (tmp_path / "file1.dt").write_text("CP 10, R.a")
    (tmp_path / "file2.dt").write_text("INVALID_INSTRUCTION R.x")
    (tmp_path / "file3.dt").write_text("CP 30, R.c")

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(
            sys, "argv", ["dt31", "check", "file1.dt", "file2.dt", "file3.dt"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "file1.dt is valid" in captured.err
    assert "Parse error in file2.dt" in captured.err
    assert "file3.dt is valid" in captured.err
    assert "1 of 3 file(s) failed validation" in captured.err


def test_check_glob_pattern(tmp_path, capsys):
    """Test check command with glob pattern."""
    # Create multiple .dt files
    (tmp_path / "prog1.dt").write_text("CP 1, R.a")
    (tmp_path / "prog2.dt").write_text("CP 2, R.b")
    (tmp_path / "prog3.dt").write_text("CP 3, R.c")

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(sys, "argv", ["dt31", "check", "*.dt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "prog1.dt is valid" in captured.err
    assert "prog2.dt is valid" in captured.err
    assert "prog3.dt is valid" in captured.err
    assert "All 3 file(s) are valid" in captured.err


def test_format_multiple_files(temp_dt_file, capsys):
    """Test format command with multiple files."""
    file1 = temp_dt_file("CP 10,R.a", "file1.dt")
    file2 = temp_dt_file("CP 20,R.b", "file2.dt")

    with patch.object(sys, "argv", ["dt31", "format", file1, file2]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Formatted file1.dt" in captured.err or "file1.dt" in captured.err
    assert "Formatted file2.dt" in captured.err or "file2.dt" in captured.err
    assert "Formatted 2 of 2 file(s)" in captured.err


def test_format_multiple_files_check_mode(temp_dt_file, capsys):
    """Test format --check with multiple files."""
    file1 = temp_dt_file("CP 10,R.a", "file1.dt")  # Needs formatting
    file2 = temp_dt_file("    CP 20, R.b\n", "file2.dt")  # Already formatted

    with patch.object(sys, "argv", ["dt31", "format", "--check", file1, file2]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1  # Should fail since file1 needs formatting
    captured = capsys.readouterr()
    assert "file1.dt would be reformatted" in captured.err
    assert "file2.dt is already formatted" in captured.err
    assert "1 of 2 file(s) would be reformatted" in captured.err


def test_format_glob_pattern(tmp_path, capsys):
    """Test format command with glob pattern."""
    # Create multiple .dt files
    (tmp_path / "prog1.dt").write_text("CP 1,R.a")
    (tmp_path / "prog2.dt").write_text("CP 2,R.b")

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(sys, "argv", ["dt31", "format", "*.dt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Formatted 2 of 2 file(s)" in captured.err


def test_check_no_files_match_pattern(tmp_path, capsys):
    """Test check command when glob pattern matches no files."""

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(sys, "argv", ["dt31", "check", "*.dt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "No files matched the provided patterns" in captured.err


def test_format_no_files_match_pattern(tmp_path, capsys):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(sys, "argv", ["dt31", "format", "*.dt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "No files matched the provided patterns" in captured.err


def test_check_recursive_glob(tmp_path, capsys):
    """Test check command with recursive glob pattern."""
    # Create nested directories with .dt files
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir2").mkdir()
    (tmp_path / "prog1.dt").write_text("CP 1, R.a")
    (tmp_path / "subdir1" / "prog2.dt").write_text("CP 2, R.b")
    (tmp_path / "subdir2" / "prog3.dt").write_text("CP 3, R.c")

    # Change to temp directory for glob to work

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.object(sys, "argv", ["dt31", "check", "**/*.dt"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    finally:
        os.chdir(old_cwd)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    # Should find all 3 files
    assert "All 3 file(s) are valid" in captured.err


def test_format_multiple_files_already_formatted(temp_dt_file, capsys):
    file1 = temp_dt_file("    CP 10, R.a\n", "file1.dt")  # Already formatted
    file2 = temp_dt_file("    CP 20, R.b\n", "file2.dt")  # Already formatted

    with patch.object(sys, "argv", ["dt31", "format", file1, file2]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "All 2 file(s) are already formatted" in captured.err


def test_format_multiple_files_check_mode_all_formatted(temp_dt_file, capsys):
    file1 = temp_dt_file("    CP 10, R.a\n", "file1.dt")  # Already formatted
    file2 = temp_dt_file("    CP 20, R.b\n", "file2.dt")  # Already formatted

    with patch.object(sys, "argv", ["dt31", "format", "--check", file1, file2]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "All 2 file(s) are already formatted" in captured.err
