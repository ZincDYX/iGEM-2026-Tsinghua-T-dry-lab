"""Minimal local `.env` loader for optional agent credentials."""

from __future__ import annotations

import os
import re
from pathlib import Path

_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_local_env(path: Path = Path(".env"), *, override: bool = False) -> bool:
    """Load a simple KEY=VALUE file without overriding process secrets by default."""
    if not path.is_file():
        return False
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not _KEY.fullmatch(key):
            raise ValueError(f"Invalid .env key on line {line_number}: {key!r}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if override or key not in os.environ:
            os.environ[key] = value
    return True
