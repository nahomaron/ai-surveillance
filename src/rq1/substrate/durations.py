"""Support-based durations by evidence class (E-1.2.1 sections 3.4 and 3.6; ST-6; TI-04, TI-09, TI-10; EC-01)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

Row = dict[str, Any]
OBJECT_CLASS = {"tracked": "detected", "predicted": "inferred", "lost": "insufficient"}


def object_class(state: str | None) -> str:
    """Section 3.4 on an eligible frame. No track point on the frame counts as `lost`."""
    return OBJECT_CLASS.get(state, "insufficient")


def combine(a: str, b: str) -> str:
    """Section 3.4 pair-frame class."""
    if "insufficient" in (a, b):
        return "insufficient"
    return "detected" if a == b == "detected" else "inferred"


def pair_class(first: Callable[[int], str], second: Callable[[int], str]) -> Callable[[int], str]:
    return lambda frame_index: combine(first(frame_index), second(frame_index))


def interval_extent(frames: list[Row], f_start: int, f_end_excl: int) -> tuple[float, float]:
    """Section 3.6: [t(f_start), t(f_last) + s_last), with f_last the last eligible frame in the interval."""
    by_index = {f["frame_index"]: f for f in frames if f["eligible"]}
    first, last = by_index[f_start], by_index[f_end_excl - 1]
    return first["support_start_tl_s"], last["support_start_tl_s"] + last["support_s"]


def class_durations(frames: list[Row], a: float, b: float, class_of: Callable[[int], str]) -> dict[str, float]:
    """Sum of clipped support |S_k ∩ [a, b)| by class. Ineligible and timing-uncertain support is insufficient (ST-6);
    frame-less time (gaps, not recorded) carries no support and so enters no class (TI-04)."""
    out = {"detected": 0.0, "inferred": 0.0, "insufficient": 0.0, "total": 0.0}
    for f in frames:
        if not f["support_s"] or f["support_start_tl_s"] is None:
            continue
        start = f["support_start_tl_s"]
        clipped = max(0.0, min(start + f["support_s"], b) - max(start, a))
        if clipped <= 0:
            continue
        usable = f["eligible"] and f["support_status"] != "timing_uncertain"
        out["insufficient" if not usable else class_of(f["frame_index"])] += clipped
        out["total"] += clipped
    return out
