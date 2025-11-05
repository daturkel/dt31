"""Command-line interface for dt31.

This module provides the `dt31` command-line executable for parsing and executing
dt31 assembly files. The CLI automatically detects registers used in programs and
validates syntax before execution.

## Installation

After installing the dt31 package, the `dt31` command becomes available:

```bash
pip install dt31
```

## Basic Usage

Execute a `.dt` assembly file:

```bash
dt31 program.dt
```

## Command-Line Options

- **file** (required): Path to the `.dt` assembly file to execute
- **-d, --debug**: Enable step-by-step debug output during execution
- **-p, --parse-only**: Validate syntax without executing the program
- **--registers**: Comma-separated list of register names (auto-detected by default)
- **--memory**: Memory size in bytes (default: 256)
- **--stack-size**: Stack size (default: 256)

## Examples

```bash
# Execute a program
dt31 countdown.dt

# Validate syntax only
dt31 --parse-only program.dt

# Run with debug output
dt31 --debug program.dt

# Use custom memory size
dt31 --memory 1024 program.dt

# Specify registers explicitly
dt31 --registers a,b,c,d,e program.dt
```

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
"""

import argparse
import sys
from pathlib import Path

from dt31 import DT31
from dt31.assembler import extract_registers_from_program
from dt31.parser import ParserError, parse_program


def main() -> None:
    """Main entry point for the dt31 CLI.

    This function implements the complete CLI workflow:

    1. **Parse arguments**: Process command-line arguments including file path,
       debug mode, parse-only mode, and CPU configuration options.
    2. **Read file**: Load the `.dt` assembly file from disk.
    3. **Parse program**: Convert assembly text to dt31 instruction objects.
    4. **Auto-detect registers**: Scan the program to identify which registers
       are used. This allows the CPU to be created with exactly the registers
       needed by the program.
    5. **Validate syntax** (if --parse-only): Exit after successful parsing.
    6. **Create CPU**: Initialize a DT31 CPU with the specified or auto-detected
       configuration. Validate that user-provided registers (if any) include all
       registers used by the program.
    7. **Execute program**: Run the program on the CPU with optional debug output.
    8. **Handle errors**: Provide clear error messages for file I/O errors, parse
       errors, runtime errors, and interrupts.

    ## Exit Codes

    - **0**: Program executed successfully or passed validation (--parse-only)
    - **1**: Error occurred (file not found, parse error, runtime error, etc.)
    - **130**: User interrupted execution (Ctrl+C)

    ## Error Output

    All error messages are written to stderr. In debug mode, runtime errors
    include CPU state information (registers and stack size) to aid in debugging.

    ## Examples

    Basic execution:
    ```shell
    $ dt31 countdown.dt
    5
    4
    3
    2
    1
    ```

    Validation only:
    ```shell
    $ dt31 --parse-only program.dt
    ✓ program.dt parsed successfully
    ```

    Debug mode:
    ```shell
    $ dt31 --debug program.dt
    [0] CP 5, R.a
    Registers: {'R.a': 5, 'R.b': 0}
    Stack: []
    ...
    ```

    Custom configuration:

    ```shell
    $ dt31 --memory 1024 --stack-size 512 --registers a,b,c,d program.dt
    ```
    """
    parser = argparse.ArgumentParser(
        prog="dt31",
        description="Execute dt31 assembly programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  dt31 program.dt                     Parse and execute program
  dt31 --debug program.dt             Execute with debug output
  dt31 --parse-only program.dt        Validate syntax only
  dt31 --memory 512 program.dt        Use 512 slots of memory
  dt31 --registers a,b,c,d program.dt  Use custom registers
        """,
    )

    parser.add_argument(
        "file",
        type=str,
        help="Path to .dt assembly file to execute",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug output during execution",
    )

    parser.add_argument(
        "-p",
        "--parse-only",
        action="store_true",
        help="Parse the file but don't execute (validate syntax only)",
    )

    parser.add_argument(
        "--registers",
        type=str,
        help="Comma-separated list of register names (e.g., a,b,c,d)",
    )

    parser.add_argument(
        "--memory",
        type=int,
        default=256,
        help="Memory size in bytes (default: 256)",
    )

    parser.add_argument(
        "--stack-size",
        type=int,
        default=256,
        help="Stack size (default: 256)",
    )

    args = parser.parse_args()

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

    # Parse the assembly program
    try:
        program = parse_program(assembly_text)
    except ParserError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract registers used in the program
    registers_used = extract_registers_from_program(program)

    # If parse-only mode, we're done
    if args.parse_only:
        print(f"✓ {args.file} parsed successfully", file=sys.stderr)
        sys.exit(0)

    # Create CPU with custom configuration
    cpu_kwargs = {
        "memory_size": args.memory,
        "stack_size": args.stack_size,
    }
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
    try:
        cpu.run(program, debug=args.debug)
    except (EOFError, KeyboardInterrupt):
        # Handle interrupt gracefully (e.g., Ctrl+C during debug mode input)
        print("\n\nExecution interrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nRuntime error: {e}", file=sys.stderr)
        if args.debug:
            state = cpu.state
            print("\nCPU state at error:", file=sys.stderr)
            # Print registers (keys starting with R.)
            registers = {k: v for k, v in state.items() if k.startswith("R.")}
            print(f"  Registers: {registers}", file=sys.stderr)
            print(f"  Stack size: {len(state['stack'])}", file=sys.stderr)
        sys.exit(1)

    # Success
    sys.exit(0)


if __name__ == "__main__":
    main()  # pragma: no cover
