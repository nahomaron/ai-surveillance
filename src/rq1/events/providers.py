"""Flag providers R1, R2, R3 and the substrate flags G and Q (E-1.2.1 section 6.0). R4 is T-19; R5 waits for CR-008."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rq1.schema.errors import ContractError

from .engine import FrameFlags

Row = dict[str, Any]


@dataclass(frozen=True)
class RuleParams:
    p_provider: str  # exactly one P provider per configuration: R1 or R2
    k_img: float
    d_p: float
    v_min: float
    d_pc: float
    tau: float
    conflict: tuple[str, ...]


def r1_p(image_gap_norm: float | None, k_img: float) -> int:
    return 2 if image_gap_norm is None else int(image_gap_norm < k_img)


def r2_p(clearance: float | None, d_p: float) -> int:
    return 2 if clearance is None else int(clearance < d_p)


def r2_m(speed: float | None, v_min: float) -> int:
    return 2 if speed is None else int(speed > v_min)


def r3_c(predicted: list[Row], d_pc: float, tau: float) -> int:
    entry = next((p for p in predicted if p["motion_model_id"] == "constant_velocity" and abs(p["horizon_s"] - tau) < 1e-9), None)
    return 2 if entry is None else int(entry["pred_min_clearance_m"] < d_pc)


def g(clearance_state: str) -> int:
    return {"measured": 1, "unmeasurable_uncalibrated": 0}.get(clearance_state, 2)


def q(q_state: str) -> int:
    return 1 if q_state == "sufficient" else 0


def flag_frames(s4: dict[str, list[Row]], rules: RuleParams, frames: list[Row], pow_nk: list | None = None) -> list[FrameFlags]:
    """Per-frame flags of one POW (the first if `pow_nk` is None). S5 reads substrate tables and never writes them."""
    if rules.p_provider not in ("R1", "R2"):
        raise ContractError("ERR-SPEC", "a configuration has exactly one P provider, R1 or R2")
    unknown = set(rules.conflict) - {"R3"}
    if unknown:
        raise ContractError("ERR-SPEC", f"conflict providers not implemented yet: {sorted(unknown)}")
    pow_row = s4["pow"][0] if pow_nk is None else next(p for p in s4["pow"] if [p["person_track_id"], p["forklift_track_id"], p["start_frame"]] == pow_nk)
    key = [pow_row["person_track_id"], pow_row["forklift_track_id"], pow_row["start_frame"]]
    speed = {r["frame_index"]: r["speed_mps"] for r in s4["object_state"] if r["track_id"] == pow_row["forklift_track_id"]}
    times = {f["frame_index"]: f for f in frames if f["eligible"]}
    out = []
    for row in sorted((r for r in s4["pair_series"] if r["pow_nk"] == key), key=lambda r: r["frame_index"]):
        i = row["frame_index"]
        p = r1_p(row["image_gap_norm"], rules.k_img) if rules.p_provider == "R1" else r2_p(row["clearance_m"], rules.d_p)
        m = 2 if rules.p_provider == "R1" else r2_m(speed.get(i), rules.v_min)  # M is unknown in every R1-only configuration
        c_by = {name: r3_c(row["predicted"], rules.d_pc, rules.tau) for name in rules.conflict}
        out.append(FrameFlags(i, times[i]["t_tl_s"], times[i]["support_s"], P=p, M=m, C_by=c_by, E=2, Q=q(row["q_state"]),
                              clearance=row["clearance_m"], sigma=row["clearance_sigma_m"], G=g(row["clearance_state"])))
    return out
