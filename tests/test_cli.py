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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
    with patch.object(sys, "argv", ["dt31", "--dump", "error", "--", file_path]):
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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
        sys, "argv", ["dt31", "--dump", "error", "--dump-file", dump_path, file_path]
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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
        ["dt31", "--dump", "success", "--dump-file", str(dump_path), file_path],
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

    with patch.object(sys, "argv", ["dt31", "--dump", "success", "--", file_path]):
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
        ["dt31", "--dump", "success", "--dump-file", str(dump_path), file_path],
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
        sys, "argv", ["dt31", "--dump", "success", "--dump-file", dump_path, file_path]
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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
        ["dt31", "--dump", "error", "--dump-file", str(dump_path), file_path],
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
