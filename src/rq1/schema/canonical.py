"""Canonical JSON: RFC 8785 (JCS), E-1.2.1 section 1.5."""
from __future__ import annotations

from typing import Any

import rfc8785


def canonical_json(value: Any) -> bytes:
    """Serialize with RFC 8785. Integral floats follow JCS number form (1.0 becomes 1)."""
    return rfc8785.dumps(value)


def sort_set(elements: list[Any]) -> list[Any]:
    """Order a contract-defined set by the canonical JSON of its elements."""
    return sorted(elements, key=canonical_json)
