"""T8.6 evidence state per object-frame and T8.7 evidence sufficiency Q per pair-frame."""
from __future__ import annotations

from typing import Any


def evidence_state(point: dict[str, Any] | None, image_size: tuple[int, int], visibility_frac: float | None, v_part: float) -> str:
    if point is None or point["state"] == "lost":
        return "lost"
    if point["state"] == "predicted":
        return "occluded_predicted"
    x1, y1, x2, y2 = point["bbox_xyxy_px"]
    width, height = image_size
    if x1 <= 1 or y1 <= 1 or x2 >= width - 1 or y2 >= height - 1:
        return "truncated"
    if visibility_frac is not None and visibility_frac < v_part:
        return "partially_visible"
    return "visible"


def q_state(pair_class: str, person: str, forklift: str, support_status: str, coverage: str | None = None) -> tuple[str, list[str]]:
    """Sufficient iff the pair class is detected, neither object is truncated and the support is not timing-uncertain.
    `usable_degraded` coverage alone never makes Q insufficient. T10.9: a lost or missing object is `*_lost`; `*_occluded`
    is listed only for state = predicted. The reasons are descriptive and never change q_state."""
    reasons = []
    for role, state in (("person", person), ("forklift", forklift)):
        if state == "occluded_predicted":
            reasons.append(f"{role}_occluded")
        elif state == "lost":
            reasons.append(f"{role}_lost")
    if person == forklift == "occluded_predicted":
        reasons.append("predicted_only")
    if "truncated" in (person, forklift):
        reasons.append("truncated")
    if support_status == "timing_uncertain":
        reasons.append("timing_uncertain")
    sufficient = pair_class == "detected" and "truncated" not in (person, forklift) and support_status != "timing_uncertain"
    return ("sufficient", []) if sufficient else ("insufficient", reasons)
