"""T8.1 person-forklift observation windows (POW) with gap bridging; TI-08."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Row = dict[str, Any]
JOINT = {"tracked", "predicted"}
BRIDGE_BREAKS = {"not_recorded", "gap_unobserved", "unusable"}
FRAMELESS = {"not_recorded", "gap_unobserved"}


@dataclass
class Pow:
    start: int
    end_excl: int
    end_reason: str
    bridged: list[tuple[int, int]] = field(default_factory=list)
    continuation_of: int | None = None


def _break_between(frames: dict[int, Row], coverage: list[Row], a: int, b: int, states: set[str]) -> bool:
    lo = frames[a]["support_start_tl_s"] + frames[a]["support_s"]
    hi = frames[b]["support_start_tl_s"]
    return any(s["coverage_state"] in states and s["t_start_tl_s"] < hi - 1e-9 and s["t_end_tl_s"] > lo + 1e-9 for s in coverage)


def build(person: dict[int, str], forklift: dict[int, str], frames: dict[int, Row], coverage: list[Row], g_max: int) -> list[Pow]:
    """`person` and `forklift` map eligible frame_index to track-point state; missing frames have no point."""
    order = sorted(frames)
    joint = [i for i in order if person.get(i) in JOINT and forklift.get(i) in JOINT]
    if not joint:
        return []
    result: list[Pow] = []
    position = {i: k for k, i in enumerate(order)}
    jset = set(joint)
    current, previous_start = joint[0], None
    while current is not None:
        start, last, bridged, reason, resume = current, current, [], None, None
        while reason is None:
            k = position[last] + 1
            if k >= len(order):
                reason = "recording_end"
                break
            nxt = order[k]
            if nxt in jset:
                if _break_between(frames, coverage, last, nxt, FRAMELESS):
                    reason, resume = "coverage_gap", nxt
                else:
                    last = nxt
                continue
            after = next((i for i in order[k:] if i in jset), None)
            if after is None:
                later = order[k:]
                if not any(person.get(i) in JOINT for i in later):
                    reason = "track_end_person"
                elif not any(forklift.get(i) in JOINT for i in later):
                    reason = "track_end_forklift"
                else:
                    reason = "gap_exceeded"
                break
            length = position[after] - k
            if length > g_max:
                reason, resume = "gap_exceeded", after
            elif _break_between(frames, coverage, last, after, BRIDGE_BREAKS):
                reason, resume = "coverage_gap", after
            else:
                bridged.append((nxt, after))
                last = after
        result.append(Pow(start, last + 1, reason, bridged, previous_start))
        previous_start, current = start, resume
    return result
