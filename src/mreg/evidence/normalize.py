import json
from pathlib import Path
from typing import Any


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def read_json(path: Path) -> Any:
    """Read bounded local JSON without silently discarding duplicate fields."""
    if path.stat().st_size > 10_000_000:
        raise ValueError("input exceeds 10 MB limit")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
