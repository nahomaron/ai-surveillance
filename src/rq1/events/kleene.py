"""Kleene three-valued logic on `tri` values: 0 false, 1 true, 2 unknown (E-1.2.1 section 1.1)."""
from __future__ import annotations


def k_and(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return 1 if a == b == 1 else 2


def k_or(a: int, b: int) -> int:
    if a == 1 or b == 1:
        return 1
    return 0 if a == b == 0 else 2


def any_of(values) -> int:
    out = 0
    for v in values:
        out = k_or(out, v)
    return out
