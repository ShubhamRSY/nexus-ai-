#!/usr/bin/env python3
"""Write runtime dependencies from pyproject.toml for pip-audit (excludes local package)."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/requirements-audit.txt")


def main() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data["project"]["dependencies"]
    OUT.write_text("\n".join(deps) + "\n", encoding="utf-8")
    print(f"Wrote {len(deps)} dependencies to {OUT}")


if __name__ == "__main__":
    main()
