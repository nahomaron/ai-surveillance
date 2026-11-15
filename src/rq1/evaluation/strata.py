"""Report-time strata (Appendix T T20.2, contract E-1.2.18).

`forklift_turning` (T20.2). For pair-frame k, let a and b be the first and last frames inside the window of length w_turn
centred on t_k, shifted as in T9.1, on which the forklift's yaw (T8.2) is non-null, with t_b - t_a >= w_turn/2.
forklift_yaw_rate = |fold(yaw_b - yaw_a)| / (t_b - t_a), where fold maps the difference to (-pi/2, pi/2].
forklift_turning is true when the rate > e_fturn, false when <= e_fturn, unknown when the yaw is null on the window or the
window is too short. It is derived at report time, stored in no artifact, and changes no flag, label, episode or
denominator. Unknown frames are reported as a third group. On the detector path it is reported only where yaw is supplied
or validated (D-8).

The T9.1 run is the forklift track's contiguous run of eligible frames with non-null position and evidence class in
{detected, inferred}, not crossing a coverage break: the same run the S4 velocity window and the T9.2 rates use
(`kinematics.contiguous_runs`, `builder.crosses_break`). A frame outside every run has no window: unknown.
Rates are in rad/s; e_fturn is given in rad/s (the pre-registration states it in degrees per second).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rq1.events.providers import wrap
from rq1.schema.errors import ContractError
from rq1.substrate import kinematics
from rq1.substrate.builder import crosses_break

Row = dict[str, Any]
EPS = 1e-9
TRUE, FALSE, UNKNOWN = "true", "false", "unknown"  # the three report groups


@dataclass(frozen=True)
class Turning:
    yaw_rate_rad_s: float | None
    state: str  # TRUE | FALSE | UNKNOWN


def fold(angle: float) -> float:
    """T20.2: map a yaw difference to (-pi/2, pi/2]. A footprint rectangle is unchanged by a half-turn, so a difference
    of pi is no rotation."""
    return wrap(2.0 * angle) / 2.0


def forklift_turning(fork: list[Row], frames: dict[int, Row], coverage: list[Row], w_turn: float, e_fturn: float) -> dict[int, Turning]:
    """T20.2 for every eligible frame of the recording. `fork`: the forklift's S4 object_state rows; `frames`: eligible S1
    frame rows by frame_index (with `t_resolved_s`); `coverage`: the recording's S1 coverage segments."""
    if w_turn <= 0 or e_fturn < 0:
        raise ContractError("ERR-SPEC", f"w_turn must be > 0 and e_fturn >= 0, got {w_turn}, {e_fturn}")
    times = {i: f["t_resolved_s"] for i, f in frames.items()}
    order = sorted(frames)
    by = {r["frame_index"]: r for r in fork}
    usable = {i for i, r in by.items() if i in frames and r["x_m"] is not None and r["evidence_class"] in ("detected", "inferred")}
    runs = kinematics.contiguous_runs(order, usable, lambda a, b: crosses_break(frames, coverage, a, b))
    out = {}
    for k in order:
        run = runs.get(k)
        if not run:
            out[k] = Turning(None, UNKNOWN)
            continue
        window = [i for i in kinematics.shifted_window(run, times, times[k], w_turn) if by[i]["yaw_rad"] is not None]
        if not window or times[window[-1]] - times[window[0]] < w_turn / 2 - EPS:
            out[k] = Turning(None, UNKNOWN)
            continue
        a, b = window[0], window[-1]
        rate = abs(fold(by[b]["yaw_rad"] - by[a]["yaw_rad"])) / (times[b] - times[a])
        out[k] = Turning(rate, TRUE if rate > e_fturn else FALSE)
    return out


def turning_reportable(perception_path: str, yaw_supplied_or_validated: bool) -> bool:
    """T20.2, D-8: always on the oracle path; on the detector path only where the yaw is supplied or validated."""
    if perception_path == "oracle":
        return True
    if perception_path == "detector":
        return yaw_supplied_or_validated
    raise ContractError("ERR-UNKNOWN-ENUM", f"perception path {perception_path}")


def deg_per_s(value: float) -> float:
    """Degrees per second to rad/s (pre-registration values are stated in degrees per second)."""
    return math.radians(value)
