# dt31

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![Coverage Badge](coverage-badge.svg)

A toy computer emulator in Python with a simple instruction set and virtual machine. dt31 is a toy computer that simulates a CPU with registers, memory, a stack, and a rich instruction set.

## Features

- **Simple CPU Architecture**: Configurable registers, fixed-size memory, and stack-based operations
- **Rich Instruction Set**: 60+ instructions including arithmetic, bitwise operations, logic, control flow, and I/O
- **Assembly Support**: Two-pass assembler with label resolution for jumps and function calls
- **Assembly Parser**: Parse and execute `.dt` assembly files with text-based syntax
- **Text Output**: Convert Python programs to assembly text format for sharing and documentation
- **Command-Line Interface**: Execute `.dt` files directly with the `dt31` command
- **Intuitive API**: Clean operand syntax (`R.a`, `M[100]`, `L[42]`, `LC['A']`)
- **Debug Mode**: Step-by-step execution with state inspection and breakpoints
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

### Parsing Programs from Text

```python
from dt31 import DT31
from dt31.parser import parse_program

cpu = DT31()

# Write assembly code as text
assembly = """
CP 5, R.a             ; Copy 5 into register a
loop:
    NOUT R.a, 1       ; Output register a with newline
    SUB R.a, 1        ; Decrement a
    JGT loop, R.a, 0  ; Jump to loop if a > 0
"""

# Parse and run
program = parse_program(assembly)
cpu.run(program)
# 5
# 4
# 3
# 2
# 1
```

### Converting Programs to Text

You can convert Python programs to assembly text format for sharing or documentation:

```python
from dt31 import I, Label
from dt31.assembler import program_to_text
from dt31.operands import R, L, LC

# Create a program in Python
program = [
    I.CP(5, R.a),
    loop := Label("loop"),
    I.OOUT(LC["*"]),           # Print asterisk
    I.SUB(R.a, L[1]),
    I.JGT(loop, R.a, L[0]),
]

# Convert to assembly text
text = program_to_text(program)
print(text)
# Output:
#     CP 5, R.a
# loop:
#     OOUT '*', 0
#     SUB R.a, 1, R.a
#     JGT loop, R.a, 0
```

This is useful for:
- Debugging generated programs
- Sharing programs in text format
- Documentation and teaching
- Round-trip conversion (Python ↔ text)

### Using the Command Line

Once installed, you can execute `.dt` assembly files directly from the command line:

```shell
# Create a simple program file
cat > countdown.dt << 'EOF'
CP 5, R.a             ; Copy 5 into register a
loop:
    NOUT R.a, 1       ; Output register a with newline
    SUB R.a, 1        ; Decrement a
    JGT loop, R.a, 0  ; Jump to loop if a > 0
EOF

# Execute the program
dt31 countdown.dt
# 5
# 4
# 3
# 2
# 1
```

#### CLI Options

- `--debug` or `-d`: Enable step-by-step debug output
- `--parse-only` or `-p`: Validate syntax without executing
- `--registers a,b,c,d`: Specify custom registers (auto-detected by default)
- `--memory 512`: Set memory size in bytes (default: 256)
- `--stack-size 512`: Set stack size (default: 256)
- `--custom-instructions PATH` or `-i PATH`: Load custom instruction definitions from a Python file

```shell
# Parse and validate only (no execution)
dt31 --parse-only program.dt

# Run with debug output
dt31 --debug program.dt

# Use custom memory size
dt31 --memory 1024 program.dt

# Specify registers explicitly
dt31 --registers a,b,c,d,e program.dt

# Use custom instructions
dt31 --custom-instructions my_instructions.py program.dt
```

#### Custom Instructions

You can define custom instructions in a Python file and load them using the `--custom-instructions` flag. Your Python file must define an `INSTRUCTIONS` dict mapping instruction names to `dt31.instructions.Instruction` subclasses:

```python
# my_instructions.py
from dt31.instructions import UnaryOperation
from dt31.operands import Operand, Reference

class TRIPLE(UnaryOperation):
    """Triple a value."""
    def __init__(self, a: Operand, out: Reference | None = None):
        super().__init__("TRIPLE", a, out)

    def _calc(self, cpu: "DT31") -> int:
        return self.a.resolve(cpu) * 3

INSTRUCTIONS = {"TRIPLE": TRIPLE}
```

Then use them in your assembly programs:

```
CP 5, R.a
TRIPLE R.a
NOUT R.a, 1  ; Outputs 15
```

Run with: `dt31 --custom-instructions my_instructions.py program.dt`

**Security Warning**: Loading custom instruction files executes arbitrary Python code. Only load files from trusted sources.

See the [CLI documentation](https://daturkel.github.io/dt31/dt31/cli.html) for more details on running text assembly programs, [instructions documentation](https://daturkel.github.io/dt31/dt31/instructions.html) for additional info on custom instructions.

## Examples

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

Users can easily define their own custom instructions by subclassing `dt31.instructions.Instruction`.

See the [instructions documentation](https://daturkel.github.io/dt31/dt31/instructions.html) for the complete reference.

### CPU Architecture

The DT31 CPU includes:

- **Registers**: General-purpose registers (default: `a`, `b`, and `c`)
- **Memory**: Fixed-size byte array (default: 256 slots)
- **Stack**: For temporary values and function calls (default: 256 slots)
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

### Assembly Text Syntax

dt31 supports writing programs in both Python and text-based assembly syntax. The text syntax is designed to be human-readable and closely resembles traditional assembly languages.

#### Basic Syntax Rules

**Instructions and Operands:**
```
INSTRUCTION operand1, operand2, operand3
```

- Instructions are case-insensitive (`ADD`, `add`, and `Add` are all valid)
- Register names and label names are case-*sensitive*
- Operands are separated by commas (spaces around commas are optional)
- Comments start with `;` and continue to end of line
- Blank lines and indentation are ignored

#### Operand Syntax Differences

The text syntax differs from Python syntax in how operands are written:

| Operand Type | Python Syntax | Text Syntax | Example |
|--------------|---------------|-------------|---------|
| **Numeric Literal** | `L[42]` | `42` | `CP 42, R.a` |
| **Negative Literal** | `L[-5]` | `-5` | `ADD R.a, -5` |
| **Character Literal** | `LC["A"]` | `'A'` | `OOUT 'H', 0` |
| **Register** | `R.a` | `R.a` | `ADD R.a, R.b` |
| **Memory (direct)** | `M[100]` | `[100]` or `M[100]` | `CP 42, [100]` |
| **Memory (indirect)** | `M[R.a]` | `[R.a]` or `M[R.a]` | `CP [R.a], R.b` |
| **Label** | `Label("loop")` | `loop` | `JMP loop` |

**Key Differences:**

1. **Literals**: In text syntax, bare numbers are literals (no `L[...]` wrapper needed)
2. **Characters**: Use single quotes `'A'` instead of `LC["A"]`
3. **Memory**: The `M` prefix is optional (both `[100]` and `M[100]` work)
4. **Labels**: Bare identifiers are labels (no `Label(...)` constructor needed)
5. **Registers**: **Must** use `R.` prefix in both syntaxes

#### Label Definition

Labels mark positions in code and can be defined in two ways:

```
; Label on its own line
loop:
    ADD R.a, 1
    JLT loop, R.a, 10

; Label on same line as instruction
start: CP 0, R.a
```

Label names must contain only alphanumeric characters and underscores.

#### Complete Example Comparison

**Python Syntax:**
```python
from dt31 import DT31, I, Label
from dt31.operands import R, L, LC, M

cpu = DT31()
program = [
    I.CP(L[5], R.a),
    loop := Label("loop"),
    I.NOUT(R.a, L[1]),
    I.SUB(R.a, L[1]),
    I.JGT(loop, R.a, L[0]),
]
cpu.run(program)
```

**Text Syntax:**
```python
from dt31 import DT31
from dt31.parser import parse_program

cpu = DT31()
assembly = """
    CP 5, R.a             ; Copy 5 into register a
    loop:                 ; Define loop label
        NOUT R.a, 1       ; Output register a
        SUB R.a, 1        ; Decrement a
        JGT loop, R.a, 0  ; Jump if a > 0
"""
program = parse_program(assembly)
cpu.run(program)
```

Both programs produce the same output: `5 4 3 2 1`

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
- [Parser](https://daturkel.github.io/dt31/dt31/parser.html) - Assembly text parsing
- [Assembler](https://daturkel.github.io/dt31/dt31/assembler.html) - Label resolution and assembly
- [CLI](https://daturkel.github.io/dt31/dt31/cli.html) - Command-line interface

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
- [x] Parse and execute `.dt` files
- [x] Breakpoint instruction
- [x] Clearer handing of input during debug mode
- [x] Python to text output
- [ ] User-definable macros (in both python and assembly syntax)
- [ ] File I/O
- [ ] Data handling?
- [ ] Input error handling rather than immediate crash
- [ ] Preserve comments in parser (then text formatter)?

## License

MIT License
