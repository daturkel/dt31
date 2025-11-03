# dt31

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![Coverage Badge](coverage-badge.svg)

A toy computer emulator in Python with a simple instruction set and virtual machine. dt31 is a toy computer that simulates a CPU with registers, memory, a stack, and a rich instruction set.

## Features

- **Simple CPU Architecture**: Configurable registers, fixed-size memory, and stack-based operations
- **Rich Instruction Set**: 60+ instructions including arithmetic, bitwise operations, logic, control flow, and I/O
- **Assembly Support**: Two-pass assembler with label resolution for jumps and function calls
- **Intuitive API**: Clean operand syntax (`R.a`, `M[100]`, `L[42]`, `LC['A']`)
- **Debug Mode**: Step-by-step execution with state inspection
- **Pure Python**: Zero dependencies

## Installation

```shell
pip install dt31
```

## Quick Start

### Hello World

```python
from dt31 import DT31, LC, I

cpu = DT31()

program = [
    I.OOUT(LC["H"]),  # Output 'H'
    I.OOUT(LC["i"]),  # Output 'i'
    I.OOUT(LC["!"]),  # Output '!'
]

cpu.run(program)
# Hi!
```

### Basic Arithmetic

```python
from dt31 import DT31, I, R, L

cpu = DT31()

program = [
    I.CP(10, R.a),           # Copy 10 into register a
    I.CP(5, R.b),            # Copy 5 into register b
    I.ADD(R.a, R.b),         # a = a + b
    I.NOUT(R.a, L[1]),       # Output a with newline
]

cpu.run(program)
# 15
```

### Loops with Labels

```python
from dt31 import DT31, I, Label
from dt31.operands import R, L

cpu = DT31()

program = [
    I.CP(1, R.a),               # Start counter at 1
    loop := Label("loop"),      # Mark loop start
    I.NOUT(R.a, L[1]),          # Print counter
    I.ADD(R.a, L[1]),           # Increment counter
    I.JLT(loop, R.a, L[11]),    # Jump if a < 11
]

cpu.run(program)
# 1 2 3 4 5 6 7 8 9 10
```

For more examples including factorial, fibonacci, function calls, and more, see the [examples](./examples/) directory.

## Core Concepts

### Operands

dt31 provides several operand types for referencing values:

- **Literals**: Constant values `L[42]`, or `LC["a"]` as a shortcut for `L[ord("a")]`
- **Registers**: CPU registers `R.a`, `R.b`, `R.c`
- **Memory**: Memory addresses `M[100]`, indirect addressing `M[R.a]`
- **Labels**: Named jump targets `Label("loop")`

See the [operands documentation](https://daturkel.github.io/dt31/dt31/operands.html) for details.

### Instructions

The instruction set includes:

- **Arithmetic**: `ADD`, `SUB`, `MUL`, `DIV`, `MOD`
- **Bitwise**: `BAND`, `BOR`, `BXOR`, `BNOT`, `BSL`, `BSR`
- **Comparisons**: `LT`, `GT`, `LE`, `GE`, `EQ`, `NE`
- **Logic**: `AND`, `OR`, `XOR`, `NOT`
- **Control Flow**: `JMP`, `RJMP`, `JEQ`, `JNE`, `JGT`, `JGE`, `JIF`
- **Functions**: `CALL`, `RCALL`, `RET`
- **Stack**: `PUSH`, `POP`, `SEMP`
- **I/O**: `NOUT`, `OOUT`, `NIN`, `OIN`
- **Data Movement**: `CP`

See the [instructions documentation](https://daturkel.github.io/dt31/dt31/instructions.html) for the complete reference.

### CPU Architecture

The DT31 CPU includes:

- **Registers**: General-purpose registers (default: `a`, `b`, and `c`)
- **Memory**: Fixed-size byte array (default: 256 bytes)
- **Stack**: For temporary values and function calls (default: 256 items)
- **Instruction Pointer**: Tracks current instruction in register `ip`

See the [CPU documentation](https://daturkel.github.io/dt31/dt31/cpu.html) for API details.

## Usage Guide

### Creating and Running Programs

```python
from dt31 import DT31, instructions as I
from dt31.operands import R, L

# Create CPU instance
cpu = DT31()

# Write program as list of instructions
program = [
    I.CP(42, R.a),
    I.NOUT(R.a, L[1]),
]

# Run the program
cpu.run(program)
# 42
```

### Working with Memory

```python
from dt31 import DT31, I, L, M, R

cpu = DT31()

program = [
    I.CP(100, M[50]),   # Store 100 at address 50
    I.CP(50, R.a),      # Put 50 in register a
    I.CP(M[R.a], R.b),  # Indirect load: b = memory[a]
    I.NOUT(R.b, L[1]),  # Output: 100
]
cpu.run(program)
# 100
```

### Function Calls

```python
from dt31.operands import LC, Label

program = [
    I.CALL(print_hi := Label("print_hi")),
    I.JMP(end := Label("end")),

    print_hi,
    I.OOUT(LC['H']),
    I.OOUT(LC['i']),
    I.RET(),

    end,
]
cpu.run(program)
# Hi
```

### Debugging with Step Execution

```python
cpu = DT31()
cpu.load(program)

# Execute one instruction at a time
cpu.step(debug=True)  # Prints instruction and state
print(cpu.state)      # Inspect CPU state
# Execute a full program one instruction at a time
cpu.run(program, debug=True)
```

### Accessing CPU State

```python
# Get register values
value = cpu.get_register('a')

# Set register values
cpu.set_register('b', 42)

# Access memory
cpu.set_memory(100, 255)
byte = cpu.get_memory(100)

# Get full state snapshot
state = cpu.state  # Returns dict with registers, memory, stack, ip
```

## Documentation

Full API documentation is available in the [documentation](https://daturkel.github.io/dt31/dt31.html). Generate the latest docs with:

```bash
uv run invoke docs
uv run invoke serve-docs  # Serve locally at http://localhost:8080
```

Key documentation pages:

- [DT31 CPU Class](https://daturkel.github.io/dt31/dt31/cpu.html) - CPU methods and state management
- [Instructions](https://daturkel.github.io/dt31/dt31/instructions.html) - Complete instruction reference
- [Operands](https://daturkel.github.io/dt31/dt31/operands.html) - Operand types and usage
- [Assembler](https://daturkel.github.io/dt31/dt31/assembler.html) - Label resolution and assembly

## Development

```bash
# Install dependencies
uv sync --dev

# Set up pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push

# Run tests
uv run invoke test
```

DT31 is open-source and contributors are welcome on [Github](https://github.com/daturkel/dt31).

## Roadmap

- [x] Character literals?
- [ ] Parse and execute `.dt` files
- [ ] Macros
- [ ] File I/O
- [ ] Data handling?
- [ ] Input error handling?
- [ ] Clearer handing of input during debug mode

## License

MIT License
