"""Time invariants used by S1 and later stages (Appendix T TI-02, TI-03, TI-09, TI-10, TI-12, TI-13)."""
from __future__ import annotations

from typing import Any

from rq1.schema.validate import Issue

TOL_S = 1e-6


def clip_support(start: float, end: float, a: float, b: float) -> float:
    """TI-09 and TI-10: the part of support [start, end) inside [a, b)."""
    return max(0.0, min(end, b) - max(start, a))


def check_edge(edge: str, timeline_a: dict[str, Any], timeline_b: dict[str, Any]) -> list[Issue]:
    """TI-12: L and P edges only between episodes on the same aligned_session timeline."""
    same = timeline_a["tl_id"] == timeline_b["tl_id"] and timeline_a["kind"] == "aligned_session"
    return [] if edge not in ("L", "P") or same else [Issue("TI-12", "ERR-INVARIANT", "event_link", "edge", "L or P edge across timelines")]


def check_window_timeline(group_timeline_id: str, window_timeline_id: str) -> list[Issue]:
    """TI-13."""
    return [] if group_timeline_id == window_timeline_id else [Issue("TI-13", "ERR-INVARIANT", "reference_window", "timeline_id", "window crosses timelines")]


def _segment_of(frame: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any] | None:
    start = frame["support_start_tl_s"]
    for s in segments:
        if s["t_start_tl_s"] - TOL_S <= start < s["t_end_tl_s"] - TOL_S:
            return s
    return None


def check_ti_02(frames: list[dict[str, Any]], segments: list[dict[str, Any]]) -> list[Issue]:
    usable = [s for s in segments if s["coverage_state"] in ("usable", "usable_degraded")]
    in_usable = sum(f["support_s"] for f in frames if f["support_s"] > 0 and _segment_of(f, usable) is not None)
    total = sum(s["support_s"] for s in usable)
    return [] if abs(in_usable - total) <= TOL_S else [Issue("TI-02", "ERR-INVARIANT", "coverage_segment", "support_s", f"{in_usable} != {total}")]


def check_ti_03(segments: list[dict[str, Any]]) -> list[Issue]:
    return [Issue("TI-03", "ERR-INVARIANT", "coverage_segment", "support_s", "gap or not_recorded segment with support or frames")
            for s in segments if s["coverage_state"] in ("gap_unobserved", "not_recorded") and (s["support_s"] != 0 or s["start_frame"] is not None)]
