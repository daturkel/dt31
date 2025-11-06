# dt31 Documentation

A toy computer emulator in Python with a simple instruction set and virtual machine.

## Features

- **Simple CPU Architecture**: Configurable registers, fixed-size memory, and stack-based operations
- **Rich Instruction Set**: 60+ instructions including arithmetic, bitwise operations, logic, control flow, and I/O
- **Assembly Support**: Two-pass assembler with label resolution for jumps and function calls
- **Intuitive API**: Clean operand syntax (`R.a`, `M[100]`, `L[42]`, `LC['A']`)
- **Debug Mode**: Step-by-step execution with state inspection
- **Pure Python**: Zero runtime dependencies

## Documentation Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

getting-started
tutorials/index
```

```{toctree}
:maxdepth: 3
:caption: API Reference

api/index
```

## Quick Example

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

## Project Links

- [GitHub Repository](https://github.com/daturkel/dt31)
- [PyPI Package](https://pypi.org/project/dt31/)
