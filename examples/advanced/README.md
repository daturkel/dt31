# Advanced examples

Larger dt31 programs. Run the commands from this directory.

## Sudoku solver

`sudoku.dt` solves a puzzle by backtracking and animates it in the terminal with
ANSI escape codes. It picks the empty cell with the fewest candidates at each step,
using row, column and box bitmasks plus a popcount table. The input is 81 cells in
any layout: digits are givens, and `.` or `0` is an empty cell.

```shell
PYTHONUNBUFFERED=1 dt31 run --memory 2048 sudoku.dt < sudoku_hardest.txt
```

`PYTHONUNBUFFERED=1` makes each cell update show up as it happens. Without it,
output only reaches the terminal at each newline. `sudoku_hardest.txt` takes about
14,000 placements; `sudoku_easy.txt` solves with no backtracking.

## Language detection

`langid.dt` trains a character-level Markov chain for each language, then labels
each input line with the most probable language and generates a line of text from
each model. Probabilities are kept as exact fractions in unbounded integer
registers, so there are no logarithms and no rounding. `langid_input.txt` trains on
the Universal Declaration of Human Rights in six languages, from the
[UDHR in Unicode](https://github.com/eric-muller/udhr) project.

```shell
dt31 run --memory 130000 langid.dt < langid_input.txt
```

## Quine

`quine.dt` prints its own source exactly. Line 1 loads a 1,213-digit number that
packs the rest of the file into base-128 digits. The program prints line 1 around
that number, then unpacks it to print everything else.

```shell
dt31 run quine.dt | diff - quine.dt
```

Editing anything below line 1 means recomputing the number.

## Advent of Code

Each program prints the answers to part 1 and part 2 on separate lines. Only the
worked examples from the puzzle text are included; pass your own input on stdin.

| Program | Puzzle | Example input | Expected output |
|---|---|---|---|
| `aoc2021_day9.dt` | 2021 Day 9: Smoke Basin | `aoc2021_day9_example.txt` | `15`, `1134` |
| `aoc2022_day11.dt` | 2022 Day 11: Monkey in the Middle | `aoc2022_day11_example.txt` | `10605`, `2713310158` |
| `aoc2023_day8.dt` | 2023 Day 8: Haunted Wasteland | `aoc2023_day8_example1.txt` | `2`, `2` |
| | | `aoc2023_day8_example2.txt` | `-1`, `6` |

```shell
dt31 run --memory 40000 --stack-size 30000 aoc2021_day9.dt < aoc2021_day9_example.txt
dt31 run --memory 4000 --stack-size 1000 aoc2022_day11.dt < aoc2022_day11_example.txt
dt31 run --memory 102000 --stack-size 1000 aoc2023_day8.dt < aoc2023_day8_example1.txt
```

Day 8 prints `-1` for part 1 when the input has no `AAA`/`ZZZ` nodes, as in its
second example.
