"""JSON I/O helpers shared across ETL scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """Read and parse a JSON file."""
    return json.loads(path.read_text())


def save_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """Write `data` to `path` as UTF-8 JSON, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent))
