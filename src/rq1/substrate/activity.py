"""Activity segments (E-1.2.1 section 3.5; CD-01 to CD-03): same tiling as coverage, never from reference data."""
from __future__ import annotations

from typing import Any

Row = dict[str, Any]
NOT_EVALUATED = {"not_recorded", "gap_unobserved", "unusable"}


def _state(classes: set[str], pair_classes: set[str]) -> str:
    if "person" in classes and classes & pair_classes:
        return "pair_detected"
    return "objects_detected_no_pair" if classes else "observed_no_detection"


def _row(segment: Row, a: float, b: float, state: str, perception_artifact_id: str | None) -> Row:
    row = {"timeline_id": segment["timeline_id"], "camera_id": segment["camera_id"], "t_start_tl_s": a, "t_end_tl_s": b,
           "coverage_segment_id": segment["cov_id"], "coverage_state": segment["coverage_state"], "ai_activity_state": state,
           "support_s": 0.0 if state == "not_evaluated" else b - a}
    evaluated = state != "not_evaluated"
    row["perception_artifact_id"] = perception_artifact_id if evaluated else None
    row["perception_artifact_id_null_reason"] = None if evaluated else "not_applicable"
    return row


def build(coverage: list[Row], frames: list[Row], detections: dict[int, set[str]], pair_classes: set[str], perception_artifact_id: str) -> list[Row]:
    """`detections[frame_index]` holds the classes with a `tracked` object on that eligible frame."""
    eligible = sorted((f for f in frames if f["eligible"] and f["support_s"]), key=lambda f: f["support_start_tl_s"])
    rows: list[Row] = []
    for segment in sorted(coverage, key=lambda s: s["t_start_tl_s"]):
        a, b = segment["t_start_tl_s"], segment["t_end_tl_s"]
        if segment["coverage_state"] in NOT_EVALUATED:
            rows.append(_row(segment, a, b, "not_evaluated", None))
            continue
        pieces = []
        for f in eligible:
            start, end = f["support_start_tl_s"], f["support_start_tl_s"] + f["support_s"]
            if start >= a - 1e-9 and end <= b + 1e-9:
                pieces.append([start, end, _state(detections.get(f["frame_index"], set()), pair_classes)])
        merged: list[list] = []
        for piece in pieces:
            if merged and merged[-1][2] == piece[2] and abs(merged[-1][1] - piece[0]) < 1e-9:
                merged[-1][1] = piece[1]
            else:
                merged.append(piece)
        if merged:
            merged[0][0], merged[-1][1] = a, b
        rows += [_row(segment, s, e, state, perception_artifact_id) for s, e, state in merged]
    return rows
