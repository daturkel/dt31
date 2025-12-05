"""Command-line interface for dt31.

This module provides the `dt31` command-line executable for parsing, executing, and
formatting dt31 assembly files. The CLI automatically detects registers used in programs
and validates syntax before execution.

## Installation

After installing the dt31 package, the `dt31` command becomes available:

```bash
pip install dt31
```

## Commands

The dt31 CLI provides three main commands:

- **run**: Execute `.dt` assembly files
- **check**: Validate syntax of `.dt` assembly files
- **format**: Format `.dt` assembly files with consistent style
- --version: Show dt31 version

## Basic Usage

```bash
dt31 run program.dt       # Execute program
dt31 check program.dt     # Validate syntax
dt31 format program.dt    # Format file in-place
```

## Run Command

Execute `.dt` assembly files with configurable CPU settings.

**Options:**

- **file** (required): Path to the `.dt` assembly file to execute
- **-d, --debug**: Enable step-by-step debug output during execution
- **-i, --custom-instructions**: Path to Python file containing custom instruction definitions
- **--registers**: Comma-separated list of register names (auto-detected by default)
- **--memory**: Memory size in bytes (default: 256)
- **--stack-size**: Stack size (default: 256)
- **--dump**: When to dump CPU state - 'none' (default), 'error', 'success', or 'all'
- **--dump-file**: File path for dump (auto-generates timestamped filename if not specified)

**Examples:**

```bash
# Execute a program
dt31 run countdown.dt

# Run with debug output
dt31 run --debug program.dt

# Use custom memory size
dt31 run --memory 1024 program.dt

# Specify registers explicitly
dt31 run --registers a,b,c,d,e program.dt

# Load custom instructions
dt31 run --custom-instructions my_instructions.py program.dt

# Dump CPU state on error
dt31 run --dump error --dump-file crash.json program.dt
dt31 run --dump error program.dt  # Auto-generates program_crash_TIMESTAMP.json

# Dump CPU state after successful execution
dt31 run --dump success --dump-file final.json program.dt
dt31 run --dump success program.dt  # Auto-generates program_final_TIMESTAMP.json

# Dump on both error and success
dt31 run --dump all program.dt  # Auto-generates timestamped files
```

## Check Command

Validate the syntax of `.dt` assembly files without executing them.

**Options:**

- **file** (required): Path to the `.dt` assembly file to validate
- **-i, --custom-instructions**: Path to Python file containing custom instruction definitions

**Examples:**

```bash
# Validate syntax of a program
dt31 check program.dt

# Validate with custom instructions
dt31 check --custom-instructions custom.py program.dt
```

**Exit Codes (Check Command):**

- **0**: File is valid
- **1**: Error (file not found, parse error, or custom instruction error)

## Format Command

Format `.dt` assembly files with consistent style, following Black/Ruff conventions
(formats in-place by default).

**Options:**

- **file** (required): Path to the `.dt` assembly file to format
- **--check**: Check if formatting is needed without modifying the file (exit 1 if changes needed)
- **--diff**: Show formatting changes as a unified diff without modifying the file
- **-i, --custom-instructions**: Path to Python file containing custom instruction definitions
- **--indent-size**: Number of spaces per indentation level (default: 4)
- **--label-inline**: Place labels on same line as next instruction (default: False)
- **--blank-lines**: Control blank line handling: 'preserve' (default), 'auto', or 'none'
- **--align-comments**: Align inline comments (auto-calculates column if --comment-column not specified)
- **--comment-column**: Column position for aligned comments (default: auto-calculate)
- **--comment-margin**: Spaces before inline comments and margin for auto-alignment (default: 2)
- **--strip-comments**: Remove all comments from output (default: False)
- **--show-default-args**: Show instruction arguments even when they match defaults (default: False)

**Examples:**

```bash
# Format file in-place
dt31 format program.dt

# Check if formatting is needed (CI/pre-commit)
dt31 format --check program.dt

# Preview formatting changes
dt31 format --diff program.dt

# Format with custom style
dt31 format --indent-size 2 --label-inline program.dt

# Show default arguments
dt31 format --show-default-args program.dt

# Auto-align comments (calculates optimal column)
dt31 format --align-comments program.dt

# Align comments at specific column
dt31 format --align-comments --comment-column 40 program.dt

# Auto-align with custom margin
dt31 format --align-comments --comment-margin 4 program.dt

# Strip all comments from output
dt31 format --strip-comments program.dt

# Format file with custom instructions
dt31 format --custom-instructions my_instructions.py program.dt

# Check and show diff if needed
dt31 format --check --diff program.dt
```

**Exit Codes (Format Command):**

- **0**: Success (formatted, already formatted, or `--check` passed)
- **1**: Error (file not found, parse error, `--check` failed, IO error)

## Register Auto-Detection

The CLI automatically detects which registers are used in your program and creates
a CPU with exactly those registers. This eliminates the need to manually specify
registers in most cases.

If you explicitly provide `--registers`, the CLI validates that all registers used
in the program are included in your list.

## Exit Codes

- **0**: Success
- **1**: Error (file not found, parse error, runtime error, or CPU creation error)
- **130**: Execution interrupted (Ctrl+C)

## Error Handling

The CLI provides helpful error messages for common issues:

- **File not found**: Clear message indicating which file couldn't be found
- **Parse errors**: Line number and description of syntax errors
- **Runtime errors**: Exception message with optional CPU state (in debug mode)
- **Register errors**: List of missing registers when validation fails

## CPU State Dumps

The `--dump` option saves complete CPU state to JSON for debugging:

- **Error dumps** (`--dump error` or `--dump all`): Include CPU state, error info,
  traceback, and the failing instruction in both `repr` and `str` formats
- **Success dumps** (`--dump success` or `--dump all`): Include final CPU state
  after successful execution

Dumps are auto-saved with timestamped filenames (`program_crash_YYYYMMDD_HHMMSS.json`
or `program_final_YYYYMMDD_HHMMSS.json`) unless `--dump-file` specifies a custom path.

Example error dump structure:
```json
{
  "cpu_state": {
    "registers": {...},
    "memory": [...],
    "stack": [...],
    "program": "...",
    "config": {...}
  },
  "error": {
    "type": "ZeroDivisionError",
    "message": "integer division or modulo by zero",
    "instruction": {
      "repr": "DIV(a=R.a, b=R.b, out=R.a)",
      "str": "DIV R.a, R.b, R.a"
    },
    "traceback": "..."
  }
}
```
"""

import argparse
import difflib
import glob
import importlib.metadata
import importlib.util
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

from dt31 import DT31
from dt31.assembler import extract_registers_from_program
from dt31.formatter import program_to_text
from dt31.instructions import Instruction
from dt31.parser import ParserError, parse_program


def format_time(nanoseconds: int) -> str:
    """Format time in nanoseconds with appropriate units (µs, ms, or s).

    Args:
        nanoseconds: Time in nanoseconds

    Returns:
        Formatted string with appropriate unit (e.g., "1.23s", "123.46ms", "12.35µs")

    Examples:
        >>> format_time(1_234_567_890)
        '1.23s'
        >>> format_time(123_456_789)
        '123.46ms'
        >>> format_time(12_345_678)
        '12.35ms'
        >>> format_time(1_234_567)
        '1234.57µs'
        >>> format_time(123_456)
        '123.46µs'
    """
    if nanoseconds >= 1_000_000_000:  # >= 1 second
        return f"{nanoseconds / 1_000_000_000:.2f}s"
    elif nanoseconds >= 1_000_000:  # >= 1 millisecond
        return f"{nanoseconds / 1_000_000:.2f}ms"
    else:  # < 1 millisecond
        return f"{nanoseconds / 1_000:.2f}µs"


def expand_file_patterns(patterns: list[str]) -> list[str]:
    """Expand glob patterns to actual file paths.

    Args:
        patterns: List of file paths and/or glob patterns

    Returns:
        List of resolved file paths (sorted)

    Example:
        >>> expand_file_patterns(["program.dt", "*.dt"])
        ['program.dt', 'hello.dt', 'countdown.dt']
    """
    expanded_files = []
    for pattern in patterns:
        # Check if pattern contains glob characters
        if any(char in pattern for char in ["*", "?", "[", "]"]):
            # Use glob to expand the pattern
            matches = glob.glob(pattern, recursive=True)
            if matches:
                expanded_files.extend(matches)
            # If no matches, keep the original pattern (will error later)
        else:
            # Not a glob pattern, add as-is
            expanded_files.append(pattern)

    # Remove duplicates and sort
    return sorted(set(expanded_files))


def _create_run_parser(subparsers) -> None:
    """Create the 'run' subcommand parser.

    Args:
        subparsers: The subparsers object from add_subparsers()
    """
    run_parser = subparsers.add_parser(
        "run",
        help="Execute a dt31 assembly program",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  dt31 run program.dt                     Parse and execute program
  dt31 run --debug program.dt             Execute with debug output
  dt31 run --memory 512 program.dt        Use 512 slots of memory
  dt31 run --registers a,b,c,d program.dt  Use custom registers
        """,
    )

    run_parser.add_argument(
        "file",
        type=str,
        help="Path to .dt assembly file to execute",
    )

    run_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug output during execution",
    )

    run_parser.add_argument(
        "-r",
        "--registers",
        type=str,
        help="Comma-separated list of register names (e.g., a,b,c,d)",
    )

    run_parser.add_argument(
        "-m",
        "--memory",
        type=int,
        help="Memory size in bytes (default: 256)",
    )

    run_parser.add_argument(
        "-s",
        "--stack-size",
        type=int,
        help="Stack size (default: 256)",
    )

    run_parser.add_argument(
        "-i",
        "--custom-instructions",
        type=str,
        metavar="PATH",
        help="Path to Python file containing custom instruction definitions",
    )

    run_parser.add_argument(
        "--dump",
        type=str,
        default="none",
        choices=["none", "error", "success", "all"],
        help="When to dump CPU state: 'none' (default), 'error', 'success', or 'all'",
    )

    run_parser.add_argument(
        "--dump-file",
        type=str,
        metavar="FILE",
        help="File path for CPU state dump (auto-generates if not specified)",
    )

    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show runtime statistics (wall time, execution time, and step count)",
    )


def _create_check_parser(subparsers) -> None:
    """Create the 'check' subcommand parser.

    Args:
        subparsers: The subparsers object from add_subparsers()
    """
    check_parser = subparsers.add_parser(
        "check",
        help="Validate syntax of a dt31 assembly file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  dt31 check program.dt                               Validate syntax
  dt31 check --custom-instructions custom.py prog.dt  Validate with custom instructions
  dt31 check program1.dt program2.dt                  Validate multiple files
  dt31 check "*.dt"                                   Validate all .dt files (glob pattern)
  dt31 check "**/*.dt"                                Validate all .dt files recursively
        """,
    )

    check_parser.add_argument(
        "files",
        type=str,
        nargs="+",
        metavar="FILE",
        help="Path(s) to .dt assembly file(s) to validate (supports glob patterns)",
    )

    check_parser.add_argument(
        "--custom-instructions",
        "-i",
        type=str,
        metavar="PATH",
        help="Path to Python file containing custom instruction definitions",
    )


def run_command(args: argparse.Namespace) -> None:
    """Execute the 'run' subcommand - parse and execute a dt31 program.

    Args:
        args: Parsed command-line arguments from argparse

    This function implements the complete execution workflow:
    1. Load custom instructions (if provided)
    2. Read and parse the assembly file
    3. Auto-detect registers used in the program
    4. Create CPU with appropriate configuration
    5. Execute the program with optional debug output
    6. Handle errors and dump CPU state if requested

    Exit codes:
        0: Program executed successfully or passed validation (--parse-only)
        1: Error occurred (file not found, parse error, runtime error, etc.)
        130: User interrupted execution (Ctrl+C)
    """
    # Load custom instructions if provided
    custom_instructions = None
    if args.custom_instructions:
        try:
            custom_instructions = load_custom_instructions(args.custom_instructions)
            if args.debug:
                print(
                    f"Loaded {len(custom_instructions)} custom instruction(s): "
                    f"{', '.join(custom_instructions.keys())}",
                    file=sys.stderr,
                )
        except (FileNotFoundError, ImportError, ValueError, TypeError) as e:
            print(f"Error loading custom instructions: {e}", file=sys.stderr)
            sys.exit(1)

    # Read the input file
    file_path = Path(args.file)
    try:
        assembly_text = file_path.read_text()
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse the assembly program with custom instructions
    try:
        program = parse_program(assembly_text, custom_instructions=custom_instructions)
    except ParserError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract registers used in the program
    registers_used = extract_registers_from_program(program)

    # Create CPU with custom configuration
    cpu_kwargs = {}
    if args.memory is not None:
        cpu_kwargs["memory_size"] = args.memory
    if args.stack_size is not None:
        cpu_kwargs["stack_size"] = args.stack_size

    if args.registers:
        # User provided explicit registers - validate they include all used registers
        user_registers = args.registers.split(",")
        missing = set(registers_used) - set(user_registers)
        if missing:
            print(
                f"Error: Program uses registers {registers_used} but --registers only specified {user_registers}",
                file=sys.stderr,
            )
            print(f"Missing registers: {sorted(missing)}", file=sys.stderr)
            sys.exit(1)
        cpu_kwargs["registers"] = user_registers
    elif registers_used:
        # Auto-detect registers from program
        cpu_kwargs["registers"] = registers_used
    # else: no registers used, CPU will use defaults

    try:
        cpu = DT31(**cpu_kwargs)
    except Exception as e:
        print(f"Error creating CPU: {e}", file=sys.stderr)
        sys.exit(1)

    # Execute the program
    exit_code = 0
    try:
        cpu.run(program, debug=args.debug)
    except (EOFError, KeyboardInterrupt):
        # Handle interrupt gracefully (e.g., Ctrl+C during debug mode input)
        print("\n\nExecution interrupted", file=sys.stderr)
        exit_code = 130
    except SystemExit as e:
        # Catch SystemExit to display verbose stats before re-raising
        exit_code = e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"\nRuntime error: {e}", file=sys.stderr)
        if args.debug:
            state = cpu.state
            print("\nCPU state at error:", file=sys.stderr)
            # Print registers (keys starting with R.)
            registers = {k: v for k, v in state.items() if k.startswith("R.")}
            print(f"  Registers: {registers}", file=sys.stderr)
            print(f"  Stack size: {len(state['stack'])}", file=sys.stderr)

        # Dump CPU state to file if requested
        if args.dump in ("error", "all"):
            dump_path = generate_dump_path(args.file, args.dump_file, "crash")
            try:
                dump_cpu_state(cpu, dump_path, error=e)
                print(f"CPU state dumped to: {dump_path}", file=sys.stderr)
            except Exception as dump_error:
                print(f"Failed to dump CPU state: {dump_error}", file=sys.stderr)

        exit_code = 1
    finally:
        # Display verbose statistics if requested (always, even on error/exit)
        if args.verbose:
            print(file=sys.stderr)

            # Always show wall time
            print(f"Wall time: {format_time(cpu.wall_time_ns)}", file=sys.stderr)

            print(
                f"Execution time: {format_time(cpu.execution_time_ns)}", file=sys.stderr
            )

            print(f"Steps: {cpu.step_count}", file=sys.stderr)

    # Exit early if there was an error or interrupt
    if exit_code != 0:
        sys.exit(exit_code)

    # Dump CPU state on exit if requested
    if args.dump in ("success", "all"):
        dump_path = generate_dump_path(args.file, args.dump_file, "final")
        try:
            dump_cpu_state(cpu, dump_path)
            print(f"CPU state dumped to: {dump_path}", file=sys.stderr)
        except Exception as dump_error:
            print(f"Failed to dump CPU state: {dump_error}", file=sys.stderr)

    # Success
    sys.exit(0)


def check_command(args: argparse.Namespace) -> None:
    """Execute the 'check' subcommand - validate syntax of a dt31 program.

    Args:
        args: Parsed command-line arguments from argparse

    This function implements the syntax validation workflow:
    1. Load custom instructions (if provided)
    2. Expand glob patterns to file paths
    3. Read and parse each assembly file
    4. Report success or error for each file

    Exit codes:
        0: All files are valid
        1: Error occurred (file not found, parse error, etc.)
    """
    # Load custom instructions if provided
    custom_instructions = None
    if args.custom_instructions:
        try:
            custom_instructions = load_custom_instructions(args.custom_instructions)
        except (FileNotFoundError, ImportError, ValueError, TypeError) as e:
            print(f"Error loading custom instructions: {e}", file=sys.stderr)
            sys.exit(1)

    # Expand glob patterns
    file_paths = expand_file_patterns(args.files)

    if not file_paths:
        print("Error: No files matched the provided patterns", file=sys.stderr)
        sys.exit(1)

    # Track results
    failed_files = []

    # Process each file
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        # Use relative path for display if possible, otherwise use the original path
        try:
            display_path = file_path.relative_to(Path.cwd())
        except ValueError:
            # File is not relative to cwd, use original path
            display_path = file_path

        # Read the input file
        try:
            assembly_text = file_path.read_text()
        except FileNotFoundError:
            print(f"Error: File not found: {display_path}", file=sys.stderr)
            failed_files.append(file_path_str)
            continue
        except IOError as e:
            print(f"Error reading file {display_path}: {e}", file=sys.stderr)
            failed_files.append(file_path_str)
            continue

        # Parse the assembly program with custom instructions
        try:
            parse_program(assembly_text, custom_instructions=custom_instructions)
        except ParserError as e:
            print(f"Parse error in {display_path}: {e}", file=sys.stderr)
            failed_files.append(file_path_str)
            continue

        # Success for this file
        print(f"✓ {display_path} is valid", file=sys.stderr)

    # Exit with appropriate code
    if failed_files:
        if len(file_paths) > 1:
            print(
                f"\n✗ {len(failed_files)} of {len(file_paths)} file(s) failed validation",
                file=sys.stderr,
            )
        sys.exit(1)
    else:
        if len(file_paths) > 1:
            print(f"\n✓ All {len(file_paths)} file(s) are valid", file=sys.stderr)
        sys.exit(0)


def _create_format_parser(subparsers) -> None:
    """Create the 'format' subcommand parser.

    Args:
        subparsers: The subparsers object from add_subparsers()
    """
    format_parser = subparsers.add_parser(
        "format",
        help="Format a dt31 assembly file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  dt31 format program.dt                   Format file in-place
  dt31 format --check program.dt           Check if formatting needed
  dt31 format --diff program.dt            Show formatting changes
  dt31 format --check --diff program.dt    Check and show diff
  dt31 format --show-default-args prog.dt  Show default arguments
  dt31 format program1.dt program2.dt      Format multiple files
  dt31 format "*.dt"                       Format all .dt files (glob pattern)
  dt31 format "**/*.dt"                    Format all .dt files recursively
        """,
    )

    format_parser.add_argument(
        "files",
        type=str,
        nargs="+",
        metavar="FILE",
        help="Path(s) to .dt assembly file(s) to format (supports glob patterns)",
    )

    # Validation flags
    format_parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check if file needs formatting without modifying (exit 1 if changes needed)",
    )

    format_parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Show diff of changes without applying them (can combine with --check)",
    )

    # Formatting options (7 total)
    format_parser.add_argument(
        "-I",
        "--indent-size",
        type=int,
        default=4,
        metavar="N",
        help="Number of spaces per indentation level (default: 4)",
    )

    format_parser.add_argument(
        "-l",
        "--label-inline",
        action="store_true",
        help="Place labels on same line as next instruction (default: False)",
    )

    format_parser.add_argument(
        "-b",
        "--blank-lines",
        choices=["auto", "preserve", "none"],
        default="preserve",
        help="Control blank line handling: 'preserve' keeps source formatting (default), "
        "'auto' adds blank lines before labels, 'none' removes automatic blank lines",
    )

    format_parser.add_argument(
        "-a",
        "--align-comments",
        action="store_true",
        help="Align inline comments at comment-column (default: False)",
    )

    format_parser.add_argument(
        "-C",
        "--comment-column",
        type=int,
        default=None,
        metavar="N",
        help="Column position for aligned comments. If not specified and --align-comments "
        "is used, column is auto-calculated based on longest instruction + --comment-margin.",
    )

    format_parser.add_argument(
        "-m",
        "--comment-margin",
        type=int,
        default=2,
        metavar="N",
        help="Spaces before inline comment semicolon. Also used as margin when auto-aligning "
        "comments (default: 2).",
    )

    format_parser.add_argument(
        "-D",
        "--show-default-args",
        action="store_false",
        dest="hide_default_args",
        help="Show arguments even when they match the default value (default: False)",
    )

    format_parser.add_argument(
        "-s",
        "--strip-comments",
        action="store_true",
        help="Remove all comments from output (standalone and inline). Overrides --align-comments (default: False)",
    )

    # Custom instructions support (needed for parsing)
    format_parser.add_argument(
        "-i",
        "--custom-instructions",
        type=str,
        metavar="PATH",
        help="Path to Python file containing custom instruction definitions",
    )


def _format_single_file(
    file_path: str,
    custom_instructions: dict[str, type[Instruction]] | None,
    check_mode: bool,
    show_diff: bool,
    formatting_options: dict,
) -> bool:
    """Format a single dt31 assembly file.

    This is a helper function that handles formatting one file. It's separated
    to make it easy to add glob support in the future by wrapping this in a loop.

    Args:
        file_path: Path to the file to format
        custom_instructions: Optional custom instructions dict
        check_mode: If True, don't modify file, just check if changes needed
        show_diff: If True, don't modify file, just show unified diff of changes
        formatting_options: Dict of formatting options to pass to program_to_text()

    Returns:
        True if file needs formatting (or was formatted), False if already formatted

    Raises:
        SystemExit: On file not found, parse error, or IO error
    """
    path = Path(file_path)

    # Read the input file
    try:
        original_text = path.read_text()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse the program
    # Extract blank_lines from formatting_options to determine if we need to preserve newlines during parsing
    blank_lines = formatting_options.get("blank_lines", "preserve")
    preserve_newlines = blank_lines == "preserve"
    try:
        program = parse_program(
            original_text,
            custom_instructions=custom_instructions,
            preserve_newlines=preserve_newlines,
        )
    except ParserError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # Format the program (formatter ensures trailing newline)
    formatted_text = program_to_text(program, **formatting_options)

    # Check if changes are needed
    needs_formatting = original_text != formatted_text

    # Handle --diff flag
    if show_diff:
        if needs_formatting:
            # Show unified diff
            diff = difflib.unified_diff(
                original_text.splitlines(keepends=True),
                formatted_text.splitlines(keepends=True),
                fromfile=f"{file_path} (original)",
                tofile=f"{file_path} (formatted)",
            )
            sys.stdout.writelines(diff)
        else:
            print(f"✓ {file_path} is already formatted", file=sys.stderr)

    # Handle --check mode (or --diff mode - both don't modify files)
    if check_mode or show_diff:
        if needs_formatting and not show_diff:
            # Only print this if we didn't already show diff
            print(f"✗ {file_path} would be reformatted", file=sys.stderr)
        elif not needs_formatting and not show_diff:
            # Only print if we didn't already print in diff section
            print(f"✓ {file_path} is already formatted", file=sys.stderr)
        return needs_formatting

    # Default mode: write formatted output
    if needs_formatting:
        try:
            path.write_text(formatted_text)
            print(f"✓ Formatted {file_path}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing to {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"✓ {file_path} is already formatted", file=sys.stderr)

    return needs_formatting


def format_command(args: argparse.Namespace) -> None:
    """Execute the 'format' subcommand - format dt31 assembly files.

    Args:
        args: Parsed command-line arguments from argparse

    Exit codes:
        0: Success (all files formatted or already formatted, or --check passed)
        1: Error (file not found, parse error, --check failed, or IO error)
    """
    # Load custom instructions if provided
    custom_instructions = None
    if args.custom_instructions:
        try:
            custom_instructions = load_custom_instructions(args.custom_instructions)
        except (FileNotFoundError, ImportError, ValueError, TypeError) as e:
            print(f"Error loading custom instructions: {e}", file=sys.stderr)
            sys.exit(1)

    # Prepare formatting options
    formatting_options = {
        "indent_size": args.indent_size,
        "label_inline": args.label_inline,
        "blank_lines": args.blank_lines,
        "align_comments": args.align_comments,
        "comment_column": args.comment_column,
        "comment_margin": args.comment_margin,
        "strip_comments": args.strip_comments,
        "hide_default_args": args.hide_default_args,
    }

    # Expand glob patterns
    file_paths = expand_file_patterns(args.files)

    if not file_paths:
        print("Error: No files matched the provided patterns", file=sys.stderr)
        sys.exit(1)

    # Track results
    files_needing_formatting = []

    # Format each file
    for file_path in file_paths:
        needs_formatting = _format_single_file(
            file_path,
            custom_instructions,
            args.check,
            args.diff,
            formatting_options,
        )
        if needs_formatting:
            files_needing_formatting.append(file_path)

    # Exit with appropriate code
    if args.check and files_needing_formatting:
        if len(file_paths) > 1:
            print(
                f"\n✗ {len(files_needing_formatting)} of {len(file_paths)} file(s) would be reformatted",
                file=sys.stderr,
            )
        sys.exit(1)
    else:
        if len(file_paths) > 1 and not args.diff:
            if files_needing_formatting and not args.check:
                print(
                    f"\n✓ Formatted {len(files_needing_formatting)} of {len(file_paths)} file(s)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"\n✓ All {len(file_paths)} file(s) are already formatted",
                    file=sys.stderr,
                )
        sys.exit(0)


def main() -> None:
    """Main entry point for the dt31 CLI.

    Supports two subcommands:
    - run: Execute a dt31 assembly program
    - format: Format a dt31 assembly file with consistent style

    Exit codes:
        0: Success
        1: Error occurred
        130: User interrupted execution (Ctrl+C)
    """
    # Create main parser with subcommands
    parser = argparse.ArgumentParser(
        prog="dt31",
        description="dt31 assembly language tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show dt31 version"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=False,
    )

    # Create 'run' subcommand
    _create_run_parser(subparsers)

    # Create 'check' subcommand
    _create_check_parser(subparsers)

    # Create 'format' subcommand
    _create_format_parser(subparsers)

    args = parser.parse_args()

    if args.version:
        print(f"dt31 v{importlib.metadata.version('dt31')}")
        sys.exit(0)

    # Dispatch to appropriate command handler
    if args.command == "run":
        run_command(args)
    elif args.command == "check":
        check_command(args)
    elif args.command == "format":
        format_command(args)
    else:
        # Should never reach here due to required subcommand, but handle gracefully
        parser.print_help()
        sys.exit(1)


def generate_dump_path(program_file: str, user_path: str | None, suffix: str) -> str:
    """Generate the path for CPU state dump file.

    Args:
        program_file: Path to the program file being executed
        user_path: User-specified path (None for auto-generate)
        suffix: Suffix for auto-generated filename ("crash" or "final")

    Returns:
        Path to use for dump file

    Example:
        >>> generate_dump_path("countdown.dt", None, "crash")
        'countdown_crash_20251106_143022.json'
        >>> generate_dump_path("countdown.dt", None, "final")
        'countdown_final_20251106_143022.json'
        >>> generate_dump_path("countdown.dt", "my_dump.json", "crash")
        'my_dump.json'
    """
    if user_path:
        return user_path

    # Auto-generate filename from program name
    program_name = Path(program_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{program_name}_{suffix}_{timestamp}.json"


def dump_cpu_state(cpu: DT31, file_path: str, error: Exception | None = None) -> None:
    """Dump CPU state to JSON file, optionally with error info.

    Args:
        cpu: The DT31 CPU instance
        file_path: Path to write the JSON dump
        error: Optional exception to include in dump

    Raises:
        IOError: If the file cannot be written
    """
    dump_data = {"cpu_state": cpu.dump()}

    if error is not None:
        error_info: dict[str, str | dict[str, str]] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }

        # Include the last instruction that was executed (or attempted)
        try:
            ip = cpu.get_register("ip")
            instruction = None
            if 0 <= ip < len(cpu.instructions):
                instruction = cpu.instructions[ip]
            elif ip >= len(cpu.instructions) and len(cpu.instructions) > 0:
                # IP went past end, show last instruction
                instruction = cpu.instructions[-1]

            if instruction is not None:
                error_info["instruction"] = {
                    "repr": repr(instruction),
                    "str": str(instruction),
                }
        except Exception:
            # If we can't get the instruction, don't fail the dump
            pass

        dump_data["error"] = error_info

    with open(file_path, "w") as f:
        json.dump(dump_data, f, indent=2)


def load_custom_instructions(file_path: str) -> dict[str, type[Instruction]]:
    """Load custom instruction definitions from a Python file.

    The file should define an INSTRUCTIONS dict mapping instruction names
    to Instruction subclasses.

    Args:
        file_path: Path to Python file containing custom instructions

    Returns:
        Dictionary mapping instruction names to instruction classes

    Raises:
        FileNotFoundError: If the file doesn't exist
        ImportError: If the file can't be loaded as a Python module
        ValueError: If the file doesn't define an INSTRUCTIONS dict
        TypeError: If INSTRUCTIONS contains non-Instruction classes

    Example:
        ```python
        # custom_instructions.py
        from dt31.instructions import Instruction
        from dt31.operands import Operand

        class MYINST(Instruction):
            def __init__(self, a: Operand, b: Operand):
                super().__init__("MYINST")
                self.a = a
                self.b = b

            def _calc(self, cpu):
                return 0

        INSTRUCTIONS = {
            "MYINST": MYINST,
        }
        ```

        Load the custom instructions:
        ```python
        custom = load_custom_instructions("custom_instructions.py")
        ```
    """

    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Custom instructions file not found: {file_path}")

    # Load module from file
    spec = importlib.util.spec_from_file_location("custom_instructions", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Extract INSTRUCTIONS dict
    if not hasattr(module, "INSTRUCTIONS"):
        raise ValueError(
            f"Custom instructions file must define an INSTRUCTIONS dict. "
            f"Found attributes: {', '.join(dir(module))}"
        )

    instructions = getattr(module, "INSTRUCTIONS")
    if not isinstance(instructions, dict):
        raise TypeError(
            f"INSTRUCTIONS must be a dict, got {type(instructions).__name__}"
        )

    # Validate all values are Instruction subclasses

    for name, cls in instructions.items():
        if not isinstance(cls, type) or not issubclass(cls, Instruction):
            raise TypeError(
                f"Instruction '{name}' must be a subclass of Instruction, got {cls}"
            )

    return instructions


if __name__ == "__main__":
    main()  # pragma: no cover
