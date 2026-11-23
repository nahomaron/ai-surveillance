"""D-53 step 1 (D1, with D3): forklift position error against viewing angle. Diagnostic, tuning subset, not a reported
result. Stored outputs only; nothing in the pipeline changes.

  PYTHONPATH=src .venv/bin/python research/m1b/d1_anchor_angle.py   -> research/m1b/d1_anchor_angle.json

Source: the stored column B S4 (oracle boxes, `full_camera`; T-21 `full_camera` unit) of the 116 tuning cameras
(`v2_camera_sets.json`). Definitions reused from `cr007_evidence.py`: camera centre C = -R^T t; error = estimate minus
the simulator footprint centre of the oracle track's identity; line of sight = unit vector from C's floor point to the
true centre; along = error . line of sight (signed; negative = estimate toward the camera).
- theta: angle between the forklift body axis (simulator yaw = box long axis, CR-023) and the line of sight, folded to
  [0, 90] degrees (the footprint is symmetric under a half-turn and a mirror).
- h(theta) = (L/2)|cos theta| + (W/2)|sin theta|, L = 3.03 m, W = 1.13 m (SDG prior, pre-registration v1 / D-34 B.5):
  the half-extent of the footprint rectangle along the line of sight.
- r: floor distance from C to the estimated point.
- Bins: [0, 15), [15, 30), [30, 45), [45, 60), [60, 75), [75, 90]. Percentiles: linear interpolation (as cr007_evidence).
- Candidate d: median |along| over all tuning frames, rounded to 0.05 m. Residual after a constant shift by d:
  |along - (-d)| = |along + d|.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cr007_evidence import _q, camera_centre, decompose, unit  # noqa: E402

L_M, W_M = 3.03, 1.13
BINS = ((0, 15), (15, 30), (30, 45), (45, 60), (60, 75), (75, 90))
NEAR_M = 2.0
STATUS = "diagnostic, tuning subset, not a reported result"


def fold_theta(yaw: float, los: tuple) -> float:
    """Angle (degrees, [0, 90]) between the body axis (cos yaw, sin yaw) and the unit line of sight."""
    c = abs(math.cos(yaw) * los[0] + math.sin(yaw) * los[1])
    return math.degrees(math.acos(min(1.0, c)))


def h_theta(theta_deg: float, length: float = L_M, width: float = W_M) -> float:
    t = math.radians(theta_deg)
    return (length / 2) * abs(math.cos(t)) + (width / 2) * abs(math.sin(t))


def bin_of(theta_deg: float) -> str:
    for lo, hi in BINS:
        if lo <= theta_deg < hi or (hi == 90 and theta_deg <= 90):
            return f"{lo}-{hi}"
    raise ValueError(theta_deg)


def round_to(x: float, step: float = 0.05) -> float:
    return round(round(x / step) * step, 2)


def frame_row(est: tuple, truth: tuple, yaw: float, centre: tuple) -> dict:
    los = unit(truth, centre)
    along, across = decompose(est, truth, los)
    th = fold_theta(yaw, los)
    return {"along": along, "across": across, "theta": th, "h": h_theta(th), "r": math.hypot(est[0] - centre[0], est[1] - centre[1])}


def by_bin(rows: list[dict]) -> dict:
    out = {}
    for lo, hi in BINS:
        key = f"{lo}-{hi}"
        rs = [r for r in rows if bin_of(r["theta"]) == key]
        al = [r["along"] for r in rs]
        out[key] = {"n": len(rs), "along_signed_median_m": _q(al, 50), "along_signed_p05_m": _q(al, 5), "along_signed_p95_m": _q(al, 95),
                    "h_theta_median_m": _q([r["h"] for r in rs], 50)}
    return out


def residual(rows: list[dict], d: float) -> dict:
    out = {}
    for lo, hi in BINS:
        key = f"{lo}-{hi}"
        res = [abs(r["along"] + d) for r in rows if bin_of(r["theta"]) == key]
        out[key] = {"n": len(res), "median_m": _q(res, 50), "p95_m": _q(res, 95)}
    allr = [abs(r["along"] + d) for r in rows]
    out["all"] = {"n": len(allr), "median_m": _q(allr, 50), "p95_m": _q(allr, 95)}
    return out


def summarize(rows_by_view: dict, cameras: int, no_yaw: int) -> dict:
    allrows = rows_by_view["all"]
    d = round_to(_q([abs(r["along"]) for r in allrows], 50))
    return {"status": STATUS, "contract": "E-1.2.24 (no change)", "source": "stored column B S4 (T-21 full_camera unit, label run1), oracle boxes",
            "cameras": cameras, "forklift_object_frames": len(allrows), "frames_without_simulator_yaw": no_yaw,
            "definitions": {"along": "error . unit line of sight (camera floor point -> true centre); negative = toward the camera",
                            "theta": "angle between simulator yaw axis (box long axis) and line of sight, folded to [0, 90] deg",
                            "h_theta": f"(L/2)|cos theta| + (W/2)|sin theta|, L = {L_M} m, W = {W_M} m (SDG prior)",
                            "r": "floor distance from the camera centre's floor point to the estimated point",
                            "candidate_d": "median |along| over all tuning frames, rounded to 0.05 m",
                            "residual": "|along + d| (error left after a constant shift of the estimate by d away from the camera)",
                            "percentiles": "linear interpolation"},
            "along_by_theta": {v: by_bin(rs) for v, rs in rows_by_view.items()},
            "d3_share_r_lt_2m": {v: {"n": len(rs), "r_lt_2m": sum(1 for r in rs if r["r"] < NEAR_M),
                                     "share": (sum(1 for r in rs if r["r"] < NEAR_M) / len(rs)) if rs else None} for v, rs in rows_by_view.items()},
            "along_abs_median_m_unrounded": _q([abs(r["along"]) for r in allrows], 50),
            "candidate_d_m": d,
            "residual_after_d": residual(allrows, d)}


def run() -> dict:  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    import pilot_common as pc
    import run_pilot as rp
    import v2_sets
    ev = ep.ev
    ctx = pc.m.Context("sdg")
    rows_by_view = {"all": [], "ceiling": [], "eye_level": []}
    no_yaw = 0
    recs = v2_sets.tuning()
    for rec in recs:
        cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
        view = pc.viewpoint(cam.camera_name)
        _, _, cal = rp.load_s1(ctx, rec)
        C = camera_centre(cal["R_cam_from_world"], cal["t_cam_from_world_m"])
        s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
        trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
        s4 = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["full_camera"]["s4"])
        for r in s4["object_state"]:
            if r["x_m"] is None or r["track_id"] not in trk_key:
                continue
            key = trk_key[r["track_id"]]
            if cam.classes[key] != "forklift":
                continue
            t = cam.truth.get((key, r["frame_index"]))
            if t is None:
                continue
            if t[5] is None:
                no_yaw += 1
                continue
            row = frame_row((r["x_m"], r["y_m"]), (t[3], t[4]), t[5], C)
            rows_by_view["all"].append(row)
            rows_by_view[view].append(row)
    return summarize(rows_by_view, len(recs), no_yaw)


if __name__ == "__main__":  # pragma: no cover
    import pilot_common as pc
    p = pc.ROOT / "research/m1b/d1_anchor_angle.json"
    pc.write_json(p, run())
    print("wrote", p)
