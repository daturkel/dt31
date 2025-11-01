# dt31

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![Coverage Badge](coverage-badge.svg)

A toy computer emulator in Python with a simple instruction set and virtual machine.

## Installation

```shell
pip install dt31
```

## Usage

```python
from dt31 import Computer

# Create and run programs
computer = Computer()
# Your code here
```

## Development

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run invoke test

# Run tests with coverage
uv run invoke coverage
```

## License

MIT License
