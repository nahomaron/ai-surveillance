"""Canonical JSON: RFC 8785 (JCS), E-1.2.1 section 1.5."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import rfc8785


def canonical_json(value: Any) -> bytes:
    """Serialize with RFC 8785. Integral floats follow JCS number form (1.0 becomes 1)."""
    return rfc8785.dumps(_normalize(value))


def _normalize(value: Any) -> Any:
    """AR-7: a `ts` value is hashed as UTC RFC 3339 text with microseconds."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def sort_set(elements: list[Any]) -> list[Any]:
    """Order a contract-defined set by the canonical JSON of its elements."""
    return sorted(elements, key=canonical_json)
