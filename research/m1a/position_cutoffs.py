"""T-21 / G-M1a: evidence for CR-026 (counts only). What a range limit or a ray-angle limit on full_camera foot rays would
remove from the GV-01 population, from the per-camera posdiag.npz written by position_diagnosis.py. No rule applied.
  python research/m1a/position_cutoffs.py   -> research/m1a/position_cutoffs.json"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import evaluate_m1a as ev, m1a_common as m

out = {"status": "experimental (synthetic, oracle perception, validation partition); evidence only, no rule applied"}
for ds in ("sdg", "smartspaces"):
    parts = []
    for rec in sorted(c["rec_id"] for c in m.Context(ds).validation_cameras()):
        z = np.load(ev.out_dir("run1", ds) / rec / "posdiag.npz")
        if int(z["n"]):
            parts.append({k: z[k] for k in ("err", "angle", "range", "true_dist", "has_pos", "has_truth", "state")})
    a = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    gv = a["has_pos"] & a["has_truth"]
    e, n = a["err"][gv], int(gv.sum())
    def rule(drop):
        d = drop[gv]
        kept, gone = e[~d], e[d]
        q = np.quantile(kept, [0.5, 0.9, 0.99]) if kept.size else [np.nan] * 3
        return {"nulled": int(d.sum()), "nulled_share": round(float(d.mean()), 4),
                "nulled_with_error_le_1m": int((gone <= 1).sum()), "nulled_with_error_gt_10m": int((gone > 10).sum()),
                "kept_median_m": round(float(q[0]), 3), "kept_p90_m": round(float(q[1]), 3), "kept_p99_m": round(float(q[2]), 3),
                "kept_share_gt_2m": round(float((kept > 2).mean()), 4), "kept_share_gt_10m": round(float((kept > 10).mean()), 4),
                "kept_rmse_m": round(float(np.sqrt(np.mean(kept ** 2))), 3)}
    res = {"gv01_points": n, "true_distance_gt_50m": int((a["true_dist"][gv] > 50).sum()), "none": rule(np.zeros_like(a["range"], bool))}
    for r in (20, 30, 50, 100):
        res[f"range_gt_{r}m"] = rule(a["range"] > r)
    for g in (1, 2, 3, 5):
        res[f"angle_lt_{g}deg"] = rule(a["angle"] < g)
    out[ds] = res
p = ev.ROOT / "research/m1a/position_cutoffs.json"
p.write_text(json.dumps(out, indent=1) + "\n")
for ds in ("sdg", "smartspaces"):
    print(ds, out[ds]["gv01_points"], "true>50m", out[ds]["true_distance_gt_50m"])
    for k, v in out[ds].items():
        if isinstance(v, dict): print("  ", k, v)
