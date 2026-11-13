"""Flag providers R1 to R5 and the substrate flags G and Q (E-1.2.1 section 6.0; Appendix T T9.2; R4: T15, E-1.2.13)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rq1.schema.errors import ContractError
from rq1.substrate import kinematics
from rq1.substrate.builder import crosses_break

from .engine import FrameFlags, Rates, evasive

Row = dict[str, Any]
EPS = 1e-9


@dataclass(frozen=True)
class RuleParams:
    p_provider: str  # exactly one P provider per configuration: R1 or R2
    k_img: float
    d_p: float
    v_min: float
    d_pc: float
    ttc_max: float  # R4 (T15.5: <= tau)
    pet_max: float  # R4 (T15.5: <= tau)
    tau: float
    conflict: tuple[str, ...]
    r5: bool
    w_e: float
    e_turn: float
    e_acc: float
    e_dec: float
    k_sigma: float


def r1_p(image_gap_norm: float | None, k_img: float) -> int:
    return 2 if image_gap_norm is None else int(image_gap_norm < k_img)


def r2_p(clearance: float | None, d_p: float) -> int:
    return 2 if clearance is None else int(clearance < d_p)


def r2_m(speed: float | None, v_min: float) -> int:
    return 2 if speed is None else int(speed > v_min)


def _cv(predicted: list[Row], tau: float) -> Row | None:
    return next((p for p in predicted if p["motion_model_id"] == "constant_velocity" and abs(p["horizon_s"] - tau) < EPS), None)


def r3_c(predicted: list[Row], d_pc: float, tau: float) -> int:
    entry = _cv(predicted, tau)
    return 2 if entry is None else int(entry["pred_min_clearance_m"] < d_pc)


def r4_c(row: Row, person_speed: float | None, fork_speed: float | None, ttc_max: float, pet_max: float) -> int:
    """T15.4: unknown when the frame is uncalibrated or either velocity is null; otherwise TTC part OR PET part (T15.2, T15.3)."""
    if row["clearance_state"] == "unmeasurable_uncalibrated" or person_speed is None or fork_speed is None:
        return 2
    for name in ("ttc_s", "pet_pred_s"):
        if row[name] is None and row[f"{name}_null_reason"] != "not_applicable":
            raise ContractError("ERR-INVARIANT", f"pair-frame {row['frame_index']}: velocities and calibration present but {name} not computed")
    ttc_part = row["ttc_s"] is not None and row["ttc_s"] < ttc_max
    pet_part = row["pet_pred_s"] is not None and row["pet_pred_s"] < pet_max
    return int(ttc_part or pet_part)


def check_r4(ttc_max: float, pet_max: float, tau: float) -> None:
    """T15.5: ttc_max <= tau and pet_max <= tau, otherwise ERR-SPEC (checked for every configuration, AR-49 item 4)."""
    if ttc_max > tau or pet_max > tau:
        raise ContractError("ERR-SPEC", f"T15.5: ttc_max {ttc_max} and pet_max {pet_max} must not exceed tau {tau}")


def g(clearance_state: str) -> int:
    return {"measured": 1, "unmeasurable_uncalibrated": 0}.get(clearance_state, 2)


def q(q_state: str) -> int:
    return 1 if q_state == "sufficient" else 0


def wrap(angle: float) -> float:
    """Wrap to (-pi, pi]."""
    value = math.fmod(angle + math.pi, 2 * math.pi)
    value = value + 2 * math.pi if value < 0 else value
    value -= math.pi
    return math.pi if value <= -math.pi + 1e-15 else value


def borderline(value: float | None, threshold: float, sigma: float | None, k_sigma: float) -> bool:
    """Section 6.0: |value - threshold| <= k_sigma * sigma; a null sigma counts as 0 (Appendix N1 note)."""
    return value is not None and abs(value - threshold) <= k_sigma * (sigma or 0.0) + EPS


def _ends(rows: dict[int, Row], runs: dict[int, list[int]], times: dict[int, float], k: int, w_e: float) -> tuple[int, int] | None:
    """T9.2: first and last frames with a non-null smoothed speed in the w_e window centred on t_k, shifted as in T9.1
    inside the object's run; null unless t_b - t_a >= w_e / 2. A frame outside every run has no window (CR-009 item 2)."""
    run = runs.get(k)
    if not run:
        return None
    window = [i for i in kinematics.shifted_window(run, times, times[k], w_e) if rows[i]["speed_mps"] is not None]
    if not window or times[window[-1]] - times[window[0]] < w_e / 2 - EPS:
        return None
    return window[0], window[-1]


def r5_rates(person: list[Row], fork: list[Row], frames: dict[int, Row], coverage: list[Row], w_e: float, v_min: float) -> dict[int, Rates]:
    """T9.2 rates for every frame of the recording, from the S4 smoothed speeds and headings."""
    times = {i: f["t_resolved_s"] for i, f in frames.items()}
    order = sorted(frames)
    brk = lambda a, b: crosses_break(frames, coverage, a, b)

    def prepare(rows: list[Row]):
        by = {r["frame_index"]: r for r in rows}
        usable = {i for i, r in by.items() if r["x_m"] is not None and r["evidence_class"] in ("detected", "inferred")}
        return by, kinematics.contiguous_runs(order, usable, brk)

    p_rows, p_runs = prepare(person)
    f_rows, f_runs = prepare(fork)
    out = {}
    for k in order:
        change = turn = decel = None
        turn_false = False
        pe = _ends(p_rows, p_runs, times, k, w_e)
        if pe:
            a, b = (p_rows[i] for i in pe)
            dt = times[pe[1]] - times[pe[0]]
            change = abs(b["speed_mps"] - a["speed_mps"]) / dt
            if a["speed_mps"] >= v_min and b["speed_mps"] >= v_min:
                if a["heading_rad"] is not None and b["heading_rad"] is not None:
                    turn = abs(wrap(b["heading_rad"] - a["heading_rad"])) / dt
            else:
                turn_false = True
        fe = _ends(f_rows, f_runs, times, k, w_e)
        if fe:
            a, b = (f_rows[i] for i in fe)
            decel = max(0.0, -(b["speed_mps"] - a["speed_mps"])) / (times[fe[1]] - times[fe[0]])
        out[k] = Rates(person_speed_change=change, forklift_decel=decel, person_turn_rate=turn, turn_false=turn_false)
    return out


def flag_frames(s4: dict[str, list[Row]], rules: RuleParams, frames: list[Row], coverage: list[Row], pow_nk: list | None = None) -> list[FrameFlags]:
    """Per-frame flags of one POW (the first if `pow_nk` is None). S5 reads substrate tables and never writes them."""
    if rules.p_provider not in ("R1", "R2"):
        raise ContractError("ERR-SPEC", "a configuration has exactly one P provider, R1 or R2")
    unknown = set(rules.conflict) - {"R3", "R4"}
    if unknown:
        raise ContractError("ERR-SPEC", f"unknown conflict providers: {sorted(unknown)}")
    check_r4(rules.ttc_max, rules.pet_max, rules.tau)
    pow_row = s4["pow"][0] if pow_nk is None else next(p for p in s4["pow"] if [p["person_track_id"], p["forklift_track_id"], p["start_frame"]] == pow_nk)
    key = [pow_row["person_track_id"], pow_row["forklift_track_id"], pow_row["start_frame"]]
    eligible = {f["frame_index"]: f for f in frames if f["eligible"]}
    recording = frames[0]["recording_id"]
    own = [c for c in coverage if c.get("recording_id") == recording]
    cov = [c for c in coverage if own and c["timeline_id"] == own[0]["timeline_id"] and c["camera_id"] == own[0]["camera_id"]]
    person = [r for r in s4["object_state"] if r["track_id"] == pow_row["person_track_id"]]
    fork = [r for r in s4["object_state"] if r["track_id"] == pow_row["forklift_track_id"]]
    person_by = {r["frame_index"]: r for r in person}
    fork_by = {r["frame_index"]: r for r in fork}
    rates = r5_rates(person, fork, eligible, cov, rules.w_e, rules.v_min)  # T10.3(c): the cue needs them even when R5 is off
    seen = lambda r: r is not None and r["evidence_state"] in ("visible", "partially_visible")
    out = []
    for row in sorted((r for r in s4["pair_series"] if r["pow_nk"] == key), key=lambda r: r["frame_index"]):
        i = row["frame_index"]
        fk = fork_by.get(i)
        speed, speed_sigma = (fk["speed_mps"], fk["speed_sigma_mps"]) if fk else (None, None)
        c_by = {}
        if "R3" in rules.conflict:
            c_by["R3"] = r3_c(row["predicted"], rules.d_pc, rules.tau)
        if "R4" in rules.conflict:  # no borderline flag from R4 in this version (T15.5)
            ps = person_by.get(i)
            c_by["R4"] = r4_c(row, ps["speed_mps"] if ps else None, speed, rules.ttc_max, rules.pet_max)
        cv = _cv(row["predicted"], rules.tau)
        clear_near = borderline(row["clearance_m"], rules.d_p, row["clearance_sigma_m"], rules.k_sigma)
        gap_near = borderline(row["image_gap_norm"], rules.k_img, None, rules.k_sigma)  # sigma 0: equality (T10.4)
        speed_near = borderline(speed, rules.v_min, speed_sigma, rules.k_sigma)
        if rules.p_provider == "R1":
            p, m = r1_p(row["image_gap_norm"], rules.k_img), 2  # M is unknown in every R1-only configuration
            onset = gap_near
        else:
            p, m = r2_p(row["clearance_m"], rules.d_p), r2_m(speed, rules.v_min)
            onset = clear_near or speed_near
        if "R3" in rules.conflict and cv is not None and borderline(cv["pred_min_clearance_m"], rules.d_pc, cv["sigma_m"], rules.k_sigma):
            onset = True  # T9.8: borderline for P, M or an enabled C provider
        # T10.4 frame bullets, each only under its T11.1 condition (the minclr and CA bullets are episode-level, in the engine).
        flags = set()
        r2 = rules.p_provider == "R2"  # R2 provides both P and M (section 6.0)
        if (r2 and clear_near) or (rules.p_provider == "R1" and gap_near):
            flags.add("clearance_within_k_sigma")
        if "R3" in rules.conflict and any(borderline(e["pred_min_clearance_m"], rules.d_pc, e["sigma_m"], rules.k_sigma) for e in row["predicted"]):
            flags.add("clearance_within_k_sigma")
        if r2 and speed_near:
            flags.add("speed_near_v_min")
        frame_rates = rates.get(i)
        if not rules.r5:
            e = 0  # T9.4
        elif row["evidence_class"] == "insufficient":
            e = 2  # T10.3(b): an object is lost, ineligible or timing-uncertain at this frame
        else:
            e = evasive(frame_rates, rules.e_turn, rules.e_acc, rules.e_dec)
        out.append(FrameFlags(i, eligible[i]["t_tl_s"], eligible[i]["support_s"], P=p, M=m, C_by=c_by, E=e, Q=q(row["q_state"]),
                              clearance=row["clearance_m"], sigma=row["clearance_sigma_m"], G=g(row["clearance_state"]),
                              closing_rate=row["closing_rate_mps"], ttca=row["ttca_s"], image_gap_norm=row["image_gap_norm"],
                              overlap=row["footprint_overlap"], rates=frame_rates, evidence_class=row["evidence_class"],
                              borderline=frozenset(flags), extra_flags=frozenset(row.get("borderline_flags", [])), onset=onset,
                              speed=speed, sigma_reason=row["clearance_sigma_m_null_reason"], ttca_reason=row["ttca_s_null_reason"],
                              visible=seen(person_by.get(i)) and seen(fk)))
    return out
