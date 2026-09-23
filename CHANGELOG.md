# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `dt31 to-python` command, which converts a `.dt` file into a standalone Python
  program using the Python API. Comments are kept as `.with_comment(...)` calls.
  Accepts `-o`, `-r`, `-m`, `-s` and `-d`. (#48, #53)
- `SNIN`, `SCIN` and `SSTRIN` input instructions, which write a status code instead
  of raising on end of input or an unparseable line, so a program can loop over
  piped input until it runs out. (#45)
- `--max-steps` option on `dt31 run`, and a `max_steps` argument to `DT31.run()`,
  which raise `StepLimitExceeded` once the step budget is used up. (#66)
- `DT31RuntimeError` exception hierarchy: `DivisionByZero`, `StackOverflow`,
  `StackUnderflow`, `MemoryOutOfBounds`, `InvalidOperand` and `StepLimitExceeded`.
  Each carries the failing instruction's `ip`, `instruction` and source `line`. (#65, #66)
- Parsed instructions record their source line number, which is shown in CLI
  runtime errors, error dumps and undefined-label errors. (#64)

### Changed

- **Breaking:** errors a program triggers at runtime now raise `DT31RuntimeError`
  subclasses instead of `ZeroDivisionError`, `RuntimeError`, `IndexError` or
  `ValueError`. Code that catches the old builtin types needs updating. (#65)
- **Breaking:** passing an operand of the wrong type to an instruction or CPU
  accessor now raises `TypeError` instead of `ValueError`. (#56)
- Input prompts are written to stderr instead of stdout, and only when stdin is a
  terminal. (#51, #61)
- Debug output (`--debug`, `step(debug=True)`) and `BRK`/`BRKD` output go to stderr
  instead of stdout. (#62)
- Debug output shows character literals as characters (`LC["H"]`) and jump targets
  by label name (`JMP(dest=loop)`). (#46, #48)
- `DT31.run()` is faster when debug mode and step timing are off. (#51, #60)

### Fixed

- A `;` inside a character literal (`COUT ';'`) is no longer treated as the start
  of a comment. (#54)
- Malformed operands such as `[1]junk`, `R.a-b` or `--5` raise `ParserError`
  instead of being silently truncated or raising a bare `ValueError`. (#54)
- `POP`, `SEMP`, `NIN`, `SNIN`, `CIN`, `SCIN` and `NEXT` reject a non-reference
  output operand at parse time instead of failing at runtime. (#54)

## [0.11.0] and earlier

See [GitHub Releases](https://github.com/daturkel/dt31/releases).

[Unreleased]: https://github.com/daturkel/dt31/compare/0.11.0...HEAD
[0.11.0]: https://github.com/daturkel/dt31/releases/tag/0.11.0
