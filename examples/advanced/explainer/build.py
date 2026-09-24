"""Build sudoku-explainer.html from template.html, vm.js and the sudoku example files."""

import json
from pathlib import Path

HERE = Path(__file__).parent
ADVANCED = HERE.parent


def main() -> None:
    vm = (
        (HERE / "vm.js")
        .read_text()
        .replace('if (typeof module !== "undefined") module.exports = DT31;\n', "")
    )
    source = (ADVANCED / "sudoku.dt").read_text()
    puzzles = {
        "easy": (ADVANCED / "sudoku_easy.txt").read_text(),
        "hardest": (ADVANCED / "sudoku_hard.txt").read_text(),
    }
    page = (
        (HERE / "template.html")
        .read_text()
        .replace("/*__VM__*/", vm)
        .replace("/*__SRC__*/", json.dumps(source))
        .replace("/*__PUZZLES__*/", json.dumps(puzzles))
    )
    (HERE / "sudoku-explainer.html").write_text(page)


if __name__ == "__main__":
    main()
