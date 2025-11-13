# dt31

[![PyPI - Version](https://img.shields.io/pypi/v/dt31?color=yellow)](https://pypi.org/project/dt31/)
 [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT) [![pdoc](https://img.shields.io/badge/docs-pdoc.dev-green)](https://pdoc.dev/docs/pdoc.html) [![Ruff](https://img.shields.io/badge/style-ruff-green.svg)](https://github.com/astral-sh/ruff) ![Coverage Badge](coverage-badge.svg)

A toy computer emulator and assembly language written in Python. Build programs with 60+ built-in instructions for interacting with registers, memory, and the stack. Write your programs in the native assembly syntax or directly with the Python API.

<table>
<tr>
<th>countdown.dt</th>
<th>countdown.py</th>
</tr>
<tr>
<td>

```nasm
; countdown.dt

; copy 5 to register a
CP 5, R.a
loop:
    ; print register a
    NOUT R.a, 1
    ; a = a - 1
    SUB R.a, 1
    ; jump to loop if a > 0
    JGT loop, R.a, 0

; run with: `dt31 countdown.dt`
; output: 5 4 3 2 1
```
</td>
<td>

```python
from dt31 import DT31, I, L, Label, R

# create vm with default settings
cpu = DT31()

program = [
    I.CP(5, R.a),
    loop := Label("loop"),
    I.NOUT(R.a, L[1]),
    I.SUB(R.a, L[1]),
    I.JGT(loop, R.a, L[0]),
]

cpu.run(program)
```

</td>

</tr>
</table>

## Features

- **Simple CPU Architecture**: Configurable registers, fixed-size memory, and stack-based operations
- **Rich Instruction Set**: 60+ instructions including arithmetic, bitwise operations, logic, control flow, and I/O
- **Assembly Support**: Two-pass assembler with label resolution for jumps and function calls
- **Assembly Parser**: Parse and execute `.dt` assembly files with text-based syntax
- **Command-Line Interface**: Execute `.dt` files directly with the `dt31` command
- **Python API**: Build and run programs programmatically with an intuitive API
- **Debug Mode**: Step-by-step execution with state inspection and breakpoints
- **Pure Python**: Zero dependencies

## Installation

```shell
pip install dt31
```

## Getting Started

### Hello World

Create a file `hello.dt`

```nasm
; Output "Hi!"
OOUT 'H', 0
OOUT 'i', 0
OOUT '!', 0
```

and run it with the `dt31` interpreter

```shell
dt31 hello.dt
# Hi!
```

### Basic Arithmetic

```nasm
; Add two numbers
CP 10, R.a      ; Copy 10 into register a
CP 5, R.b       ; Copy 5 into register b
ADD R.a, R.b    ; a = a + b
NOUT R.a, 1     ; Output a with newline
```

Save as `add.dt` and run: `dt31 add.dt` to output `15`.

### Loops with Labels

```nasm
; Count from 1 to 10
CP 1, R.a               ; Start counter at 1
loop:
    NOUT R.a, 1         ; Print counter
    ADD R.a, 1          ; Increment counter
    JLT loop, R.a, 11   ; Jump to loop if a < 11
```

Save as `count.dt` and run: `dt31 count.dt` to output `1 2 3 4 5 6 7 8 9 10`.

### Function Calls

```nasm
; Print a greeting multiple times
CP 3, R.a           ; Counter: print 3 times
print_loop:
    CALL greet      ; Call the greeting function
    SUB R.a, 1.     ; R.a -= 1
    JGT print_loop, R.a, 0 ; loop if R.a > 0
JMP end

greet:
    ; Reusable greeting function
    OOUT 'H', 0
    OOUT 'i', 0
    OOUT '!', 0
    OOUT ' ', 0
    RET

end:
; output: `Hi! Hi! Hi! `
```

Functions use the stack for return addresses and can be called multiple times. See the [examples](https://github.com/daturkel/dt31/tree/main/examples) directory for more complex examples.

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

## Command-Line Interface

### Basic Usage

Execute `.dt` assembly files directly:

```shell
dt31 program.dt
```

### CLI Options

- `--debug` or `-d`: Enable step-by-step debug output
- `--parse-only` or `-p`: Validate syntax without executing
- `--registers a,b,c,d`: Specify custom registers (auto-detected by default)
- `--memory 512`: Set memory size in bytes (default: 256)
- `--stack-size 512`: Set stack size (default: 256)
- `--custom-instructions PATH` or `-i PATH`: Load custom instruction definitions from a Python file
- `--dump {none,error,success,all}`: When to dump CPU state (default: none)
- `--dump-file FILE`: File path for CPU state dump (auto-generates timestamped filename if not specified)

**Examples:**

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

# Dump CPU state on error (for debugging crashes)
dt31 --dump error program.dt  # Auto-generates program_crash_TIMESTAMP.json
```

See the [CLI documentation](https://daturkel.github.io/dt31/dt31/cli.html) for complete details.

### Custom Instructions

Define custom instructions in a Python file and load them with `--custom-instructions`. Your file must export an `INSTRUCTIONS` dict and instruction names must be all-caps:

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

Use in assembly:

```nasm
CP 5, R.a
TRIPLE R.a
NOUT R.a, 1  ; Outputs 15
```

Run with: `dt31 --custom-instructions my_instructions.py program.dt`

**Security Warning**: Loading custom instruction files executes arbitrary Python code. Only load files from trusted sources.

See the [instructions documentation](https://daturkel.github.io/dt31/dt31/instructions.html) for more details on creating custom instructions.

### CPU State Dumps

The `--dump` option captures complete CPU state to JSON for debugging. Dumps include:

- **CPU state**: registers, memory, stack, and loaded program (as assembly text)
- **Error information** (on error dumps): exception type, message, traceback, and the instruction that caused the error

Error dumps include both `repr` and `str` formats of the failing instruction for easier debugging:

```json
{
  "cpu_state": {
    "registers": {"a": 10, "b": 0, "ip": 2},
    "memory": [...],
    "stack": [],
    "program": "CP 10, R.a\nCP 0, R.b\nDIV R.a, R.b",
    "config": {"memory_size": 256, "stack_size": 256, "wrap_memory": false}
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

## Assembly Language Reference

### Syntax Rules

**Instructions and Operands:**
```nasm
INSTRUCTION operand1, operand2, operand3
```

- Instructions are case-insensitive (`ADD`, `add`, and `Add` are all valid)
- Register names and label names are case-*sensitive*
- Operands are separated by commas (spaces around commas are optional)
- Comments start with `;` and continue to end of line
- Blank lines and indentation are ignored

### Operand Types

The assembly text syntax differs from Python syntax:

| Operand Type | Assembly Syntax | Python Syntax | Example |
|--------------|---------------|-------------|---------|
| **Numeric Literal** | `42`, `-5` | `L[42]`, `L[-5]` | `CP 42, R.a` |
| **Character Literal** | `'A'` | `LC["A"]` | `OOUT 'H', 0` |
| **Register** | `R.a` | `R.a` | `ADD R.a, R.b` |
| **Memory (direct)** | `[100]` or `M[100]` | `M[100]` | `CP 42, [100]` |
| **Memory (indirect)** | `[R.a]` or `M[R.a]` | `M[R.a]` | `CP [R.a], R.b` |
| **Label** | `loop` | `Label("loop")` | `JMP loop` |

**Key Differences:**

1. **Literals**: In text syntax, bare numbers are literals (no `L[...]` wrapper needed)
2. **Characters**: Use single quotes `'A'` instead of `LC["A"]`
3. **Memory**: The `M` prefix is optional (both `[100]` and `M[100]` work)
4. **Labels**: Bare identifiers are labels (no `Label(...)` constructor needed)
5. **Registers**: **Must** use `R.` prefix in both syntaxes

### Label Definition

Labels mark positions in code:

```nasm
; Label on its own line
loop:
    ADD R.a, 1
    JLT loop, R.a, 10

; Label on same line as instruction
start: CP 0, R.a
```

Label names must contain only alphanumeric characters and underscores.

## Python API

While assembly syntax is the primary way to use dt31, you can also build and run programs programmatically using the Python API.

### Creating and Running Programs

```python
from dt31 import DT31, I, L, M, R

# Create CPU instance
cpu = DT31()

# Write program as list of instructions
program = [
    I.CP(42, R.a),
    I.CP(100, M[R.a]),
    I.NOUT(R.a, L[1]),
    I.NOUT(M[R.a], L[1])
]

# Run the program
cpu.run(program)
# 42
# 100
```

### Parsing Assembly from Python

```python
from dt31 import DT31
from dt31.parser import parse_program

cpu = DT31()

assembly = """
CP 5, R.a
loop:
    NOUT R.a, 1
    SUB R.a, 1
    JGT loop, R.a, 0
"""

program = parse_program(assembly)
cpu.run(program)
# 5 4 3 2 1
```

### Converting Programs to Text

Convert Python programs to assembly text format:

```python
from dt31 import I, L, Label, LC, R
from dt31.assembler import program_to_text

# Create a program in Python
program = [
    I.CP(5, R.a),
    loop := Label("loop"),
    I.OOUT(LC["*"]),
    I.SUB(R.a, L[1]),
    I.JGT(loop, R.a, L[0]),
]

# Convert to assembly text
text = program_to_text(program)
print(text)
#     CP 5, R.a
# loop:
#     OOUT '*', 0
#     SUB R.a, 1, R.a
#     JGT loop, R.a, 0
```

### Labels and Function Calls

Labels offer a great use-case for the Python walrus operator.

```python
from dt31.operands import I, LC, Label

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

Full API documentation is available at [the docs site](https://daturkel.github.io/dt31/dt31.html). Generate the latest docs with:

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
uv run prek install --install-hooks
uv run prek install --hook-type pre-push

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
- [ ] Data handling
- [ ] Input error-handling
- [ ] Preserve comments in parser
- [ ] Formatter
- [ ] Interpreter resume from dump

## License

MIT License
