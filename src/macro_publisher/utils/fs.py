"""Filesystem helpers for atomic and deterministic writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    """Create parent directories for a path."""

    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to a file."""

    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    """Write deterministic JSON with a trailing newline."""

    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
