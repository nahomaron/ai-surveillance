"""Synthetic S1 tables for substrate tests: regular frames, optional excluded frames and dropouts (TEST-ONLY)."""
from __future__ import annotations

from typing import Any

from rq1.ids import core

Row = dict[str, Any]


def build(n: int, dt: float = 0.1, recording: str = "r", excluded: frozenset[int] = frozenset(), dropouts: dict[int, float] | None = None,
          uncertain: frozenset[int] = frozenset(), width: int = 1000, height: int = 600) -> dict[str, list[Row]]:
    """Frame k starts at k*dt plus earlier dropouts; `dropouts[k]` inserts extra frame-less time after frame k (gap_unobserved).
    `excluded` frames are timed but undecodable; `uncertain` frames are eligible but `timing_uncertain`."""
    rec = core.anchor_id("rec", "recording", [recording])
    tl = core.anchor_id("tl", "timeline", ["recording_local", rec])
    cam = core.anchor_id("cam", "camera", [recording])
    frames, pieces, t, index = [], [], 0.0, 0
    dropouts = dropouts or {}
    for k in range(n):
        eligible = k not in excluded
        status = "excluded_own_support" if not eligible else ("timing_uncertain" if k in uncertain else ("final_assumed" if k == n - 1 else "measured"))
        frames.append({"recording_id": rec, "decode_seq": k, "frame_index": index if eligible else None, "eligible": eligible, "t_resolved_s": round(t, 9),
                       "t_tl_s": round(t, 9), "support_start_tl_s": round(t, 9), "support_s": dt, "support_status": status, "decode_ok": eligible})
        state = "usable" if eligible and k not in uncertain else "unusable"
        pieces.append([round(t, 9), round(t + dt, 9), state])
        index += eligible
        t += dt
        if k in dropouts:
            pieces.append([round(t, 9), round(t + dropouts[k], 9), "gap_unobserved"])
            t += dropouts[k]
    merged: list[list] = []
    for piece in pieces:
        if merged and merged[-1][2] == piece[2] and abs(merged[-1][1] - piece[0]) < 1e-9:
            merged[-1][1] = piece[1]
        else:
            merged.append(list(piece))
    coverage = [{"cov_id": core.make_id("cov", [rec, a]), "timeline_id": tl, "camera_id": cam, "recording_id": rec if s != "gap_unobserved" else None,
                 "t_start_tl_s": a, "t_end_tl_s": b, "coverage_state": s} for a, b, s in merged]
    summary = [{"recording_id": rec, "width_px": width, "height_px": height}]
    return {"frame": frames, "coverage_segment": coverage, "decode_summary": summary}
