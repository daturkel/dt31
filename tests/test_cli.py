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
