# Claude Code Instructions for dt31

See @README.md for project overview, features, usage examples, and user-facing documentation.

## Code Style

- **Python Version**: 3.10+ (see [pyproject.toml](pyproject.toml))
- **Formatting**: Ruff for linting and formatting
- **Type Hints**: Required for all function signatures and public APIs
- **Docstrings**: Google-style (configured for pdoc in [tasks.py](tasks.py))
- **Dependencies**: Zero runtime dependencies (dev dependencies are okay)
- **Imports**: Always place imports at the top of the file (avoid inline imports unless absolutely necessary to prevent circular imports)

## Architecture

### Core Components

- **[src/dt31/cpu.py](src/dt31/cpu.py)**: The DT31 CPU class with registers, memory, stack, and execution logic
- **[src/dt31/instructions.py](src/dt31/instructions.py)**: Instruction definitions and implementations
- **[src/dt31/operands.py](src/dt31/operands.py)**: Operand types (Literal, Register, Memory, Label)
- **[src/dt31/parser.py](src/dt31/parser.py)**: Parser for text-based assembly syntax
- **[src/dt31/assembler.py](src/dt31/assembler.py)**: Two-pass assembler for label resolution
- **[src/dt31/cli.py](src/dt31/cli.py)**: Command-line interface for executing `.dt` assembly files

### Design Principles

1. **Intuitive API**: Clean operand syntax (`R.a`, `M[100]`, `L[42]`, `LC['A']`)
2. **Educational**: Code should be readable and serve as a learning tool
3. **Type Safety**: Strict type hints for better IDE support and correctness

## Development Workflow

### Testing

- Use pytest for all tests and do not group tests into classes
- Tests are in [tests/](tests/) directory
- Run tests with: `uv run invoke test`
- Coverage reports: `uv run invoke test --ci` (generates coverage.xml and coverage-badge.svg)

### Documentation

- Documentation is auto-generated using pdoc from Google-style docstrings
- Generate docs: `uv run invoke docs`
- Serve docs locally: `uv run invoke serve-docs`

### Code Quality

- Pre-commit hooks are configured (must be installed with `pre-commit install`)
- Ruff handles linting and formatting
- All code changes should pass pre-commit checks before committing

### Git Commits and Pull Requests

- **Commit messages**: Keep concise (1-2 sentences max), focus on the "what" and "why"
- **PR descriptions**: Keep brief and to the point
  - Summary: 2-4 bullet points covering key changes
  - Test plan: Short checklist of what was tested
  - Avoid verbose explanations unless complexity requires it

## Instruction Set Guidelines

When adding or modifying instructions:

1. **Naming**: Use clear, uppercase abbreviations (e.g., `ADD`, `JMP`, `NOUT`)
2. **Implementation**: Each instruction should be a function in [src/dt31/instructions.py](src/dt31/instructions.py)
3. **Operand Handling**: Support appropriate operand types (literals, registers, memory references)
4. **Documentation**: Include clear docstrings explaining the instruction's behavior
5. **Testing**: Add comprehensive tests in [tests/test_instructions.py](tests/test_instructions.py)

### Custom Instructions

Users can extend dt31 with custom instructions via the CLI's `--custom-instructions` flag or programmatically via `parse_program(custom_instructions=...)`. Custom instructions must:
- Subclass `dt31.instructions.Instruction` (or helpers like `UnaryOperation`, `BinaryOperation`)
- Be exported in an `INSTRUCTIONS` dict mapping instruction names to classes
- Follow the same naming, documentation, and testing standards as built-in instructions

See [examples/custom_instructions.py](examples/custom_instructions.py) and [README.md](README.md) for details.

## Common Tasks

### Adding a New Instruction

1. Define the instruction function in [src/dt31/instructions.py](src/dt31/instructions.py)
2. Add tests covering normal operation and edge cases
3. Update the README instruction list if it's a significant addition

### Modifying CPU Architecture

1. Changes to registers, memory, or stack should be in [src/dt31/cpu.py](src/dt31/cpu.py)
2. Ensure backward compatibility or document breaking changes
3. Update all affected tests in [tests/test_cpu.py](tests/test_cpu.py)
4. Update docstrings

### Adding Examples

- Place new examples in [examples/](examples/) directory
- Python examples should be self-contained and runnable with `uv run python example_name.py`
- Assembly examples (`.dt` files) should be runnable with `dt31 example_name.dt`
- Include comments explaining key concepts
- Reference examples in README if they demonstrate important features

## Constraints

- **Memory Model**: Configurable fixed-size array of integers and fixed set of registers
- **No Runtime Dependencies**: Do not add runtime dependencies
- **Python 3.10+ Compatibility**: Avoid Python 3.11+ features unless bumping minimum version

## Testing Philosophy

- **Unit Tests**: Test individual instructions and CPU operations in isolation
- **Integration Tests**: Test complete programs with multiple instructions
- **Edge Cases**: Test boundary conditions (stack overflow, memory limits, etc.)
- **Regression Tests**: Add tests for any bugs found and fixed

## Documentation Standards

- All public classes and methods must have Google-style docstrings
- Include examples in docstrings for complex operations
- Type hints required for all function signatures
- Keep [README.md](README.md) in sync with actual capabilities

## Roadmap

See the [README.md](README.md) roadmap section for current priorities. When implementing roadmap items, discuss the approach before making significant architectural changes.
