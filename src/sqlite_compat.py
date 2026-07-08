"""Ensure sqlite3 meets ChromaDB's minimum version (3.35+).

Oracle Linux and some other distros ship an older system sqlite.
When that happens, swap in pysqlite3-binary if it is installed.
"""

from __future__ import annotations

import sqlite3
import sys


def ensure_modern_sqlite() -> None:
    if sqlite3.sqlite_version_info >= (3, 35, 0):
        return
    try:
        import pysqlite3  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - env-specific
        raise RuntimeError(
            "System sqlite3 is too old for ChromaDB "
            f"(found {sqlite3.sqlite_version}, need >= 3.35.0). "
            "Install the workaround with: pip install pysqlite3-binary"
        ) from exc
    sys.modules["sqlite3"] = pysqlite3


ensure_modern_sqlite()
