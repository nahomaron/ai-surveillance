"""T-21, G-M1a rulings (D-40, 17 Nov 2026) on AR-59 items 5 and 7. Re-report only; the stored evaluation is unchanged.

  python research/m1a/gv_revised.py <ds> run1 cameras     -> out/m1a/run1/<ds>/<rec>/gvrev.pkl.gz (resumable)
  python research/m1a/gv_revised.py <ds> run1 aggregate   -> research/m1a/gv_revised_<ds>.json

GV-04 (item 5 REVISED): at the simulator positions (both objects' simulator xy and the forklift's simulator yaw on the
  pair-frame), clearance with the prior footprint minus clearance with the simulator 3D-box floor footprint. Pair-frames:
  the measured pair-frames of the simulator_truth S4 (base run). Same estimator as before (signed summary, bias intervals).
  The stored base clearance_m is the prior-footprint clearance at the same positions; agreement is counted as a check.
GV-08 against simulator truth (item 7, addition): on each full_camera POW, the full_camera constant-velocity
  pred_min_clearance_m at frame k minus the realized minimum over [t_k, t_k + tau] of the simulator_truth clearance series
  (base S4: simulator positions, prior footprint) of the same person and forklift tracks on the POW's frames; realized
  minimum as gv.realized_min (null past the POW's last frame or with no simulator clearance in the window).
"""
from __future__ import annotations

import gzip
import json
import os
import pickle
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import aggregate_m1a as agg  # noqa: E402
import evaluate_m1a as ev  # noqa: E402
import m1a_common as m  # noqa: E402
from rq1.evaluation import gv  # noqa: E402
from rq1.substrate import geometry  # noqa: E402


def camera(ds, label, rec):
    path = ev.out_dir(label, ds) / rec / "gvrev.pkl.gz"
    if path.exists():
        return "skipped"
    m.Context(ds).camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    cam = ev.Camera(ds, label, rec)
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3 = ev.load_art(label, ds, base["s3"])
    if fc.get("s3") not in (None, base["s3"]):
        raise RuntimeError(f"{rec}: full_camera and base use different S3 artifacts")
    trk_key = ev.track_map(s3, ev.oracle_keys(cam.visible), cam.classes)
    s4b = ev.load_art(label, ds, base["s4"])
    radius, (L0, W0) = m.S4_BASE["person_radius_m"], m.FORK_PRIOR_M[ds]
    out = {"stratum": cam.window["stratum_id"] if cam.windows else None, "leakage_group": cam.windows[0]["leakage_group_id"],
           "gv04_sim": [], "gv04_check": [0, 0], "gv08_truth": []}
    sim_clear = {}
    for r in s4b["pair_series"]:
        pt, ft = r["pow_nk"][0], r["pow_nk"][1]
        if r["clearance_state"] == "measured" and r["clearance_m"] is not None:
            sim_clear[(pt, ft, r["frame_index"])] = r["clearance_m"]
            p, f = cam.truth.get((trk_key[pt], r["frame_index"])), cam.truth.get((trk_key[ft], r["frame_index"]))
            if p is None or f is None or f[6] is None:
                continue
            if f[5] is None:
                prior = geometry.disc_clearance(p[3:5], radius, f[3:5], geometry.circumscribed_radius(L0, W0))
                box = geometry.disc_clearance(p[3:5], radius, f[3:5], geometry.circumscribed_radius(f[6], f[7]))
            else:
                prior = geometry.clearance(p[3:5], radius, f[3:5], f[5], L0, W0)
                box = geometry.clearance(p[3:5], radius, f[3:5], f[5], f[6], f[7])
            out["gv04_check"][0] += 1
            out["gv04_check"][1] += abs(prior - r["clearance_m"]) > 1e-9
            out["gv04_sim"].append((f"{f[6]:.2f}x{f[7]:.2f}", r["evidence_class"], prior - box))
    del s4b
    if fc.get("s4") is not None:
        s4f = ev.load_art(label, ds, fc["s4"])
        times = {i: f["t_tl_s"] for i, f in cam.eligible.items()}
        by_pow = defaultdict(list)
        for r in s4f["pair_series"]:
            by_pow[tuple(r["pow_nk"])].append(r)
        for nk, rs in by_pow.items():
            rs.sort(key=lambda r: r["frame_index"])
            ser = [(times[r["frame_index"]], sim_clear.get((nk[0], nk[1], r["frame_index"]))) for r in rs]
            for k, r in enumerate(rs):
                pred = next((e for e in r["predicted"] if e["motion_model_id"] == "constant_velocity"), None)
                if pred is None:
                    continue
                real = gv.realized_min(ser, k, pred["horizon_s"])
                if real is not None:
                    out["gv08_truth"].append((r["evidence_class"], pred["pred_min_clearance_m"] - real))
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as fh:
        pickle.dump(out, fh)
    os.replace(tmp, path)
    return f"done gv04 {len(out['gv04_sim'])} (check mismatches {out['gv04_check'][1]}) gv08 {len(out['gv08_truth'])}"


def signed(rows_by_key, ds):
    res = {}
    for key, rows in sorted(rows_by_key.items()):
        s = gv.signed_summary([v for *_, v in rows])
        per = defaultdict(lambda: [0, 0.0])
        for st, g, v in rows:
            per[(st, g)][0] += 1
            per[(st, g)][1] += v
        s["bias_ci"] = agg._ci([(st, g, n, sm) for (st, g), (n, sm) in per.items()], ds)
        s.pop("sum"), s.pop("sum_sq")
        res[key] = s
    return res


def aggregate(ds, label):
    recs = sorted(c["rec_id"] for c in m.Context(ds).validation_cameras())
    g4, g8, check = defaultdict(list), defaultdict(list), [0, 0]
    for rec in recs:
        with gzip.open(ev.out_dir(label, ds) / rec / "gvrev.pkl.gz", "rb") as fh:
            c = pickle.load(fh)
        check[0] += c["gv04_check"][0]
        check[1] += c["gv04_check"][1]
        for size, evc, v in c["gv04_sim"]:
            for key in (f"{size}|{evc}", f"{size}|all"):
                g4[key].append((c["stratum"], c["leakage_group"], v))
        for evc, v in c["gv08_truth"]:
            for key in (evc, "all"):
                g8[key].append((c["stratum"], c["leakage_group"], v))
    out = {"dataset": ds, "label": label, "status": "experimental (synthetic, oracle perception, validation partition)",
           "ruling": "D-40 item 4 (G-M1a, 17 Nov 2026): AR-59 item 5 revised; item 7 addition",
           "cameras": len(recs),
           "GV-04_at_simulator_positions": signed(g4, ds),
           "GV-04_check": {"pair_frames": check[0], "prior_clearance_differs_from_stored_base_clearance": check[1]},
           "GV-08_against_simulator_truth": signed(g8, ds)}
    p = ev.ROOT / f"research/m1a/gv_revised_{ds}.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    ds, label, what = sys.argv[1:4]
    if what == "cameras":
        for n, rec in enumerate(sorted(c["rec_id"] for c in m.Context(ds).validation_cameras()), 1):
            print(n, rec, camera(ds, label, rec), flush=True)
    else:
        aggregate(ds, label)
