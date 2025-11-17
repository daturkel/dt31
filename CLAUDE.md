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

- **[src/dt31/cpu.py](src/dt31/cpu.py)**: The DT31 CPU class with registers, memory, stack, execution logic, and serialization (`dump()`/`load_from_dump()`)
- **[src/dt31/instructions.py](src/dt31/instructions.py)**: Instruction definitions and implementations
- **[src/dt31/operands.py](src/dt31/operands.py)**: Operand types (Literal, Register, Memory, Label)
- **[src/dt31/parser.py](src/dt31/parser.py)**: Parser for text-based assembly syntax with comment preservation
- **[src/dt31/assembler.py](src/dt31/assembler.py)**: Two-pass assembler for label resolution
- **[src/dt31/cli.py](src/dt31/cli.py)**: Command-line interface for executing `.dt` assembly files
- **[src/dt31/exceptions.py](src/dt31/exceptions.py)**: Custom exception types

## Key Features

- **CPU Serialization**: Use `cpu.dump()` to save state and `DT31.load_from_dump(state)` to restore
- **Resume Execution**: Call `cpu.run()` without arguments to resume from current instruction pointer
- **CLI Debugging**: Use `--dump {none,error,success,all}` and `--dump-file` for state inspection

## Development Workflow

**All commands use `uv` for dependency management.** Common commands from [tasks.py](tasks.py):

- **Testing**: `uv run invoke test` (or `uv run invoke test --ci` for coverage.xml)
- **Documentation**: `uv run invoke docs` to generate, `uv run invoke serve-docs` to serve locally
- **Dependencies**: `uv run invoke sync` to sync dev dependencies
- **Pre-commit**: `uv run prek install --install-hooks` to set up, `uv run prek run --all-files` to run checks manually

### Code Quality

- Use pytest for all tests (do not group tests into classes)
- Pre-commit hooks managed via `prek` (Ruff for linting and formatting)
- All code changes must pass pre-commit checks before committing
- GitHub Actions workflows handle CI, releases, and docs

### Git Commits and Pull Requests

- **Commit messages**: Keep concise (1-2 sentences max), focus on the "what" and "why"
- **PR descriptions**: Keep brief and to the point
  - Summary: 2-4 bullet points covering key changes
  - Test plan: Short checklist of what was tested
  - Avoid verbose explanations unless complexity requires it

## Instruction Set Guidelines

When adding or modifying instructions:

1. **Naming**: Use clear, uppercase abbreviations (e.g., `ADD`, `JMP`, `NOUT`)
2. **Implementation**: Each instruction should be a class in [src/dt31/instructions.py](src/dt31/instructions.py)
3. **Base Classes**: Use helpers like `NullaryOperation` (no inputs, e.g., `RND`), `UnaryOperation`, or `BinaryOperation`
4. **Operand Handling**: Support appropriate operand types (literals, registers, memory references)
5. **Documentation**: Include clear docstrings explaining the instruction's behavior
6. **Testing**: Add comprehensive tests in [tests/test_instructions.py](tests/test_instructions.py)
7. **Comments**: Instructions support `.with_comment("text")` for inline comments in assembly output

### Custom Instructions

Users can extend dt31 with custom instructions via the CLI's `--custom-instructions` flag or programmatically via `parse_program(custom_instructions=...)`.

**Security Warning**: The `--custom-instructions` flag executes arbitrary Python code. Only load files from trusted sources.

Custom instructions must:
- Subclass `dt31.instructions.Instruction` (or helpers like `NullaryOperation`, `UnaryOperation`, `BinaryOperation`)
- Be exported in an `INSTRUCTIONS` dict mapping instruction names to classes
- Follow the same naming, documentation, and testing standards as built-in instructions

See [examples/custom_instructions.py](examples/custom_instructions.py) and [README.md](README.md) for details.

## Documentation Standards

- All public classes and methods must have Google-style docstrings
- Include examples in docstrings for complex operations
- Type hints required for all function signatures
- Keep [README.md](README.md) in sync with actual capabilities

## Roadmap

See the [README.md](README.md) roadmap section for current priorities. When implementing roadmap items, discuss the approach before making significant architectural changes.
