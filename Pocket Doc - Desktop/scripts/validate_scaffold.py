from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_python_files() -> None:
    for path in (ROOT / "backend").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def check_frontend_files() -> None:
    required = [
        ROOT / "frontend" / "index.html",
        ROOT / "frontend" / "styles.css",
        ROOT / "frontend" / "app.js",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing frontend files: {missing}")


if __name__ == "__main__":
    parse_python_files()
    check_frontend_files()
    print("scaffold ok")
