"""D-53 step 4 (D5): the CR-026 pixel-sensitivity table split by v2 camera set. Descriptive; stored outputs only.

  PYTHONPATH=src .venv/bin/python research/m1b/d5_sensitivity_split.py   -> research/m1b/d5_sensitivity_split.json

Same definitions as `research/m1a/position_sensitivity.py` (D-40 item 6): the stored per-camera files
out/m1a/run1/sdg/<rec>/posdiag.npz and possens.npz (column B, oracle boxes, `full_camera`, persons and forklifts), and the
`sensitivity_limits` block of its `aggregate`, restricted to a camera list: GV-01 points (position and truth); flagged =
sensitivity > s_max; caught = flagged share of points with error > 10 m (and > 2 m); lost = flagged share of good points;
good = error < 1 m (the stored definition; the count with error <= 1 m is given beside it); P99 of kept points.
Check: on all 226 validation cameras the function reproduces the stored `position_sensitivity_sdg.json` block exactly.
SmartSpaces: no tuning split is defined; its stored table is copied unchanged.
The 110 reporting cameras enter this descriptive table only (D-53 step 4).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

sys.path.insert(0, str(pc.ROOT / "research/m1a"))
import position_sensitivity as ps  # noqa: E402

KEYS = ("cls", "state", "err", "has_pos", "has_truth")


def load_arrays(recs: list[str], base) -> dict:
    parts = []
    for rec in sorted(recs):
        d = np.load(base / rec / "posdiag.npz")
        if int(d["n"]) == 0:
            continue
        z = np.load(base / rec / "possens.npz")
        parts.append({**{k: d[k] for k in KEYS}, "sens": z["sens"]})
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


def limits(a: dict) -> dict:
    """`position_sensitivity.aggregate`, block `sensitivity_limits`, unchanged, plus the error <= 1 m count."""
    gv = a["has_pos"] & a["has_truth"]
    err, sens = np.where(gv, a["err"], np.nan), a["sens"]
    big2, big10, good = gv & (err > 2), gv & (err > 10), gv & (err < 1)
    good_le = gv & (err <= 1)
    lim = {}
    for L in ps.LIMITS:
        flag = gv & (sens > L)
        kept = gv & ~flag
        lim[str(L)] = {"flagged": int(flag.sum()), "flagged_share": round(float(flag.sum() / gv.sum()), 4),
                       "caught_share_of_err_gt_2m": round(float((flag & big2).sum() / max(big2.sum(), 1)), 4),
                       "caught_share_of_err_gt_10m": round(float((flag & big10).sum() / max(big10.sum(), 1)), 4),
                       "lost_share_of_good_lt_1m": round(float((flag & good).sum() / max(good.sum(), 1)), 4),
                       "counts": {"err_gt_2m": int(big2.sum()), "err_gt_10m": int(big10.sum()), "good_lt_1m": int(good.sum())},
                       "kept": ps.q3(np.where(kept, err, np.nan)),
                       "lost_share_of_good_le_1m": round(float((flag & good_le).sum() / max(good_le.sum(), 1)), 4)}
    return {"gv01_points": int(gv.sum()), "sensitivity_limits": lim}


def strip_extra(lim: dict) -> dict:
    return {L: {k: v for k, v in row.items() if k != "lost_share_of_good_le_1m"} for L, row in lim.items()}


def run() -> dict:  # pragma: no cover - driver over stored outputs
    import v2_sets
    base = pc.ROOT / "out/m1a/run1/sdg"
    allrecs = [c["rec_id"] for c in pc.m.Context("sdg").validation_cameras()]
    stored = json.loads((pc.ROOT / "research/m1a/position_sensitivity_sdg.json").read_text())
    full = limits(load_arrays(allrecs, base))
    check = strip_extra(full["sensitivity_limits"]) == stored["sensitivity_limits"] and full["gv01_points"] == stored["gv01_points"]
    if not check:
        raise RuntimeError("the split function does not reproduce the stored SDG table")
    sets = {"tuning": v2_sets.tuning(), "reporting": v2_sets.reporting()}
    ss = json.loads((pc.ROOT / "research/m1a/position_sensitivity_smartspaces.json").read_text())
    return {"status": "D-53 step 4: descriptive; CR-026 pixel-sensitivity table split by v2 camera set; stored outputs; not a reported result",
            "contract": "E-1.2.24 (no change)", "source": "research/m1a/position_sensitivity.py definitions; out/m1a/run1/sdg/<rec>/posdiag.npz, possens.npz",
            "columns": {"flagged_share": "share of GV-01 points with sensitivity > s_max", "caught_share_of_err_gt_10m": "share of errors > 10 m flagged",
                        "lost_share_of_good_lt_1m": "share of good points (error < 1 m, stored definition) flagged",
                        "lost_share_of_good_le_1m": "the same with error <= 1 m (D-53 wording)", "kept.p99_m": "P99 error of the kept points"},
            "check_all_226_reproduce_stored_sdg_table": check,
            "sdg": {name: {"cameras": len(recs), **limits(load_arrays(recs, base))} for name, recs in sets.items()},
            "smartspaces": {"note": "no tuning split is defined for SmartSpaces; the stored table is copied unchanged",
                            "source": "research/m1a/position_sensitivity_smartspaces.json", "gv01_points": ss["gv01_points"],
                            "sensitivity_limits": ss["sensitivity_limits"]}}


if __name__ == "__main__":  # pragma: no cover
    p = pc.ROOT / "research/m1b/d5_sensitivity_split.json"
    pc.write_json(p, run())
    print("wrote", p)
