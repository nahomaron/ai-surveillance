"""D-47 item 2: CR-007 / D-8 evidence (diagnosis only; no pipeline change, no anchor rule chosen).

  PYTHONPATH=src .venv/bin/python research/m1b/cr007_evidence.py   -> research/m1b/cr007_evidence.json

Column B (oracle boxes, `full_camera` geometry; the stored T-21 `full_camera` S4 of each pilot camera):
- every forklift object-frame with a position, error E - T to the simulator footprint centre of its identity (as D-41);
- decomposed along and across (a) the line of sight from the camera's floor point to the true position and (b) the
  camera's optical axis projected on the floor; median and P95 by viewpoint (along also as a signed median);
- EV-M1 / EV-M2 of column B (summed counts, as in the pilot) for cameras whose median forklift error is below 1 m and at or
  above 1 m. Each pilot camera has one worker and one forklift, so a camera is one pair (checked).
"""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(__file__))


def camera_centre(R: list, t: list) -> tuple:
    """C = -R^T t, with R row-major (R_cam_from_world)."""
    return tuple(-sum(R[3 * r + c] * t[r] for r in range(3)) for c in range(3))


def optical_axis_floor(R: list) -> tuple:
    """The camera's z axis in world coordinates (third row of R_cam_from_world), projected on the floor, unit length."""
    x, y = R[6], R[7]
    n = math.hypot(x, y)
    return (x / n, y / n)


def unit(to: tuple, frm: tuple) -> tuple:
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    n = math.hypot(dx, dy)
    return (dx / n, dy / n)


def decompose(est: tuple, truth: tuple, u: tuple) -> tuple:
    """(along, |across|) of the error est - truth relative to unit vector u on the floor."""
    ex, ey = est[0] - truth[0], est[1] - truth[1]
    return ex * u[0] + ey * u[1], abs(ex * u[1] - ey * u[0])


def _q(v, q):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def summary(rows):
    out = {"n": len(rows)}
    for key in ("los", "axis"):
        al = [r[key][0] for r in rows]
        ac = [r[key][1] for r in rows]
        out[key] = {"along_signed_median_m": _q(al, 50), "along_abs_median_m": _q([abs(x) for x in al], 50), "along_abs_p95_m": _q([abs(x) for x in al], 95),
                    "across_median_m": _q(ac, 50), "across_p95_m": _q(ac, 95), "share_along_beyond_truth": (sum(1 for x in al if x > 0) / len(al)) if al else None}
    out["error_median_m"] = _q([r["err"] for r in rows], 50)
    out["error_p95_m"] = _q([r["err"] for r in rows], 95)
    out["distance_median_m"] = _q([r["dist"] for r in rows], 50)
    return out


def run() -> dict:  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    import pilot_common as pc
    import run_pilot as rp
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation.event_metrics import WindowCounts
    ev = ep.ev
    ctx = pc.m.Context("sdg")
    rows_by_view = {"all": [], "ceiling": [], "eye_level": []}
    cams = []
    recs = sorted(p.name for p in (pc.OUT / "cam").iterdir() if (p / "eval.pkl.gz").exists())
    for rec in recs:
        cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
        view = pc.viewpoint(cam.camera_name)
        _, _, cal = rp.load_s1(ctx, rec)
        C = camera_centre(cal["R_cam_from_world"], cal["t_cam_from_world_m"])
        axis = optical_axis_floor(cal["R_cam_from_world"])
        n_cls = {c: sum(1 for k, v in cam.classes.items() if v == c) for c in ("person", "forklift")}
        s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
        trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
        s4 = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["full_camera"]["s4"])
        errs = []
        for r in s4["object_state"]:
            if r["x_m"] is None or r["track_id"] not in trk_key:
                continue
            key = trk_key[r["track_id"]]
            if cam.classes[key] != "forklift":
                continue
            t = cam.truth.get((key, r["frame_index"]))
            if t is None:
                continue
            est, tru = (r["x_m"], r["y_m"]), (t[3], t[4])
            row = {"los": decompose(est, tru, unit(tru, C[:2])), "axis": decompose(est, tru, axis), "err": math.hypot(est[0] - tru[0], est[1] - tru[1]),
                   "dist": math.hypot(tru[0] - C[0], tru[1] - C[1])}
            errs.append(row)
            rows_by_view["all"].append(row)
            rows_by_view[view].append(row)
        with gzip.open(pc.OUT / "cam" / rec / "eval.pkl.gz", "rb") as f:
            e = pickle.load(f)
        cams.append({"rec_id": rec, "viewpoint": view, "identities": n_cls, "median_forklift_error_m": _q([x["err"] for x in errs], 50),
                     "ev_B": {bl: e["ev"]["B"][bl]["counts"] for bl in e["ev"]["B"]}})
    groups = {"below_1m": [c for c in cams if c["median_forklift_error_m"] is not None and c["median_forklift_error_m"] < 1.0],
              "at_or_above_1m": [c for c in cams if c["median_forklift_error_m"] is not None and c["median_forklift_error_m"] >= 1.0],
              "no_forklift_position": [c for c in cams if c["median_forklift_error_m"] is None]}
    split = {}
    for g, cs in groups.items():
        split[g] = {"cameras": len(cs), "by_viewpoint": {v: sum(1 for c in cs if c["viewpoint"] == v) for v in ("ceiling", "eye_level")}, "ev_B": {}}
        if not cs:
            continue
        for bl in sorted(cs[0]["ev_B"]):
            wc = [WindowCounts(**c["ev_B"][bl]) for c in cs]
            h = em.headline(wc)
            tot = {k: sum(getattr(x, k) for x in wc) for k in ("a", "m", "s", "m_s")}
            split[g]["ev_B"][bl] = {"EV-M1": h["EV-M1"], "EV-M2": h["EV-M2"], "counts": tot}
    return {"status": "D-47 item 2: CR-007 / D-8 evidence; column B (oracle boxes, full_camera); diagnosis only; synthetic SDG validation",
            "definitions": {"error": "estimate minus simulator footprint centre (floor, metres)",
                            "los": "unit vector from the camera centre's floor point to the true position; along > 0 = estimate beyond the truth",
                            "axis": "camera optical axis (third row of R_cam_from_world) projected on the floor",
                            "pair_split": "per camera (one worker and one forklift per camera): median forklift error over its object-frames, < 1 m vs >= 1 m"},
            "cameras": len(cams), "one_pair_per_camera": all(c["identities"] == {"person": 1, "forklift": 1} for c in cams),
            "identity_counts_not_one_pair": [c["rec_id"] for c in cams if c["identities"] != {"person": 1, "forklift": 1}],
            "decomposition": {v: summary(rs) for v, rs in rows_by_view.items()}, "ev_split": split}


if __name__ == "__main__":  # pragma: no cover
    out = run()
    p = os.path.join(os.path.dirname(__file__), "cr007_evidence.json")
    with open(p, "w") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k in ("cameras", "one_pair_per_camera", "decomposition", "ev_split")}, indent=1)[:4000])
