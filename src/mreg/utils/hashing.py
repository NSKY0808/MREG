import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Stable UTF-8 JSON representation; reject nonfinite numbers."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
