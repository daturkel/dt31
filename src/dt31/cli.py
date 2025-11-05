"""Command-line interface for dt31.

This module provides a CLI executable for parsing and executing dt31 assembly files.
"""

import argparse
import sys
from pathlib import Path

from dt31 import DT31
from dt31.assembler import extract_registers_from_program
from dt31.parser import ParserError, parse_program


def main() -> None:
    """Main entry point for the dt31 CLI."""
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
