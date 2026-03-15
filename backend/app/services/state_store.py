"""Simple JSON-backed persistence for MVP runtime state."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _json_default(obj: object) -> str:
    """Fallback encoder: converts datetime/date to ISO-8601 strings."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JsonStateStore:
    """Persist and retrieve JSON documents with parent-dir auto-creation."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, default: Any) -> Any:
        """Load JSON content from disk or return a default value."""

        if not self.path.exists():
            return default
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return default

    def save(self, payload: Any) -> None:
        """Persist JSON content to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True, default=_json_default)
        temp_path.replace(self.path)
