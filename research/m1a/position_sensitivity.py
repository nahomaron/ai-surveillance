"""T-21, G-M1a ruling D-40 item 6 (17 Nov 2026): CR-026 evidence. Validation only; statistics only (no pixel decoded);
nothing in the pipeline changes.

  python research/m1a/position_sensitivity.py <ds> run1 cameras    -> out/m1a/run1/<ds>/<rec>/possens.npz (resumable)
  python research/m1a/position_sensitivity.py <ds> run1 aggregate  -> research/m1a/position_sensitivity_<ds>.json

Rows: the same rows, in the same order, as `position_diagnosis.py` (checked against its posdiag.npz: count and errors).

(a) Pixel sensitivity. Floor point X(u, v) = C + s d, d = R^T K^-1 (u, v, 1), s = -C_z / d_z (as
    `geometry.full_camera_to_floor`; no distortion on either dataset). Analytic Jacobian: dX/du = s (g_u - d g_u,z / d_z)
    with g_u = R^T K^-1 e_1 (same for v with e_2); horizontal components only. Sensitivity = largest singular value of
    the 2 x 2 Jacobian (m of ground displacement per px of foot-point error, worst direction); the v-column norm
    (vertical pixel error only) is kept as well. Defined only where the ray meets the floor in front of the camera.
(b) Height consistency, persons. Head point = top-centre of the track box ((x1 + x2) / 2, y1). Its ray meets the plane
    z = H (H = 1.6, 1.75, 1.9 m) at s_H = (H - C_z) / d_z; defined when s_H > 0. Head-based floor position = the
    horizontal part of that point. Disagreement = horizontal distance between the foot-based (stored full_camera) and
    the head-based position. Separation is reported between tracked persons with bottom-edge offset <= 2 px and > 10 px
    (posdiag), at disagreement cut-offs 0.5, 1, 2, 5 m.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import evaluate_m1a as ev  # noqa: E402
import m1a_common as m  # noqa: E402

HEIGHTS = (1.6, 1.75, 1.9)
LIMITS = (0.05, 0.1, 0.2, 0.5)
CUTS = (0.5, 1.0, 2.0, 5.0)


def camera(ds, label, rec):
    path = ev.out_dir(label, ds) / rec / "possens.npz"
    if path.exists():
        return "skipped"
    ctx = m.Context(ds)
    ctx.camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    diag = np.load(ev.out_dir(label, ds) / rec / "posdiag.npz")
    cam = ev.Camera(ds, label, rec)
    fc = cam.units["full_camera"]
    s3 = ev.load_art(label, ds, fc["s3"])
    s4 = ev.load_art(label, ds, fc["s4"])
    trk_key = ev.track_map(s3, ev.oracle_keys(cam.visible), cam.classes)
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    pts = {(by_local[p["track_nk"][1]], p["frame_index"]): p for p in s3["track_point"]}
    entry = ctx.index[rec]["calibration"]
    rows = []
    for r in s4["object_state"]:
        p = pts.get((r["track_id"], r["frame_index"]))
        if p is None or p["state"] not in ("tracked", "predicted"):
            continue
        key = trk_key[r["track_id"]]
        truth = cam.truth.get((key, r["frame_index"]))
        x1, y1, x2, y2 = p["bbox_xyxy_px"]
        rows.append((p["foot_point_px"][0], p["foot_point_px"][1], (x1 + x2) / 2, y1,
                     np.nan if r["x_m"] is None else r["x_m"], np.nan if r["y_m"] is None else r["y_m"],
                     np.nan if truth is None else truth[3], np.nan if truth is None else truth[4]))
    n = int(diag["n"])
    if len(rows) != n:
        raise RuntimeError(f"{rec}: {len(rows)} rows, posdiag has {n}")
    if n == 0:
        np.savez_compressed(path.with_suffix(".tmp.npz"), n=0)
        os.replace(path.with_suffix(".tmp.npz"), path)
        return "no points"
    u, v, hu, hv, xs, ys, tx, ty = (np.array(c, float) for c in zip(*rows))
    err = np.hypot(xs - tx, ys - ty)
    if not np.array_equal(np.isnan(err), np.isnan(diag["err"])) or np.nanmax(np.abs(err - diag["err"])) > 0:
        raise RuntimeError(f"{rec}: rows differ from posdiag")
    K = np.array(entry["intrinsics_K"], float).reshape(3, 3)
    R = np.array(entry["R_cam_from_world"], float).reshape(3, 3)
    t = np.array(entry["t_cam_from_world_m"], float)
    C = -R.T @ t
    Ki = np.linalg.inv(K)
    d = R.T @ (Ki @ np.stack([u, v, np.ones_like(u)]))
    gu, gv = R.T @ Ki[:, 0], R.T @ Ki[:, 1]
    front = diag["outcome"] == 0
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(front, -C[2] / d[2], np.nan)
        ju = s * (gu[:2, None] - d[:2] * gu[2] / d[2])  # 2 x n
        jv = s * (gv[:2, None] - d[:2] * gv[2] / d[2])
    a, b, c_, e = ju[0], jv[0], ju[1], jv[1]
    # largest singular value of [[a, b], [c, e]]
    q = (a * a + b * b + c_ * c_ + e * e) / 2
    sens = np.sqrt(q + np.sqrt(np.maximum(q * q - (a * e - b * c_) ** 2, 0)))
    sens_v = np.hypot(b, e)
    head = {}
    if (diag["cls"] == 0).any():
        dh = R.T @ (Ki @ np.stack([hu, hv, np.ones_like(hu)]))
        for H in HEIGHTS:
            with np.errstate(divide="ignore", invalid="ignore"):
                sh = (H - C[2]) / dh[2]
            ok = np.isfinite(sh) & (sh > 0) & (diag["cls"] == 0)
            hx, hy = C[0] + sh * dh[0], C[1] + sh * dh[1]
            head[H] = (np.where(ok, np.hypot(hx - xs, hy - ys), np.nan), np.where(ok, np.hypot(hx - tx, hy - ty), np.nan))
    np.savez_compressed(path.with_suffix(".tmp.npz"), n=n, sens=sens, sens_v=sens_v,
                        **{f"dis_{H}": head[H][0] for H in head}, **{f"herr_{H}": head[H][1] for H in head})
    os.replace(path.with_suffix(".tmp.npz"), path)
    return f"done n={n}"


def q3(x):
    x = x[~np.isnan(x)]
    if x.size == 0:
        return {"n": 0}
    qs = np.quantile(x, [0.5, 0.9, 0.99])
    return {"n": int(x.size), "median_m": round(float(qs[0]), 3), "p90_m": round(float(qs[1]), 3), "p99_m": round(float(qs[2]), 3),
            "share_gt_2m": round(float(np.mean(x > 2)), 4), "share_gt_10m": round(float(np.mean(x > 10)), 4)}


def aggregate(ds, label):
    recs = sorted(c["rec_id"] for c in m.Context(ds).validation_cameras())
    keys = ("cls", "state", "err", "bottom", "border", "has_pos", "has_truth")
    parts = []
    for rec in recs:
        d = np.load(ev.out_dir(label, ds) / rec / "posdiag.npz")
        if int(d["n"]) == 0:
            continue
        z = np.load(ev.out_dir(label, ds) / rec / "possens.npz")
        part = {k: d[k] for k in keys}
        part.update({k: z[k] for k in z.files if k != "n"})
        for H in HEIGHTS:  # cameras without persons
            for pre in ("dis_", "herr_"):
                part.setdefault(f"{pre}{H}", np.full(int(d["n"]), np.nan))
        parts.append(part)
    a = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    gv = a["has_pos"] & a["has_truth"]
    err, sens = np.where(gv, a["err"], np.nan), a["sens"]
    out = {"dataset": ds, "label": label, "status": "experimental (synthetic, oracle perception, validation partition); CR-026 evidence (D-40 item 6)",
           "gv01_points": int(gv.sum())}
    out["sensitivity_m_per_px"] = {"all": q3(np.where(gv, sens, np.nan)), "tracked": q3(np.where(gv & (a["state"] == 0), sens, np.nan)),
                                   "predicted": q3(np.where(gv & (a["state"] == 1), sens, np.nan))}
    edges = [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 1e12]
    out["error_by_sensitivity"] = {f"[{lo}, {hi})": q3(np.where(gv & (sens >= lo) & (sens < hi), err, np.nan)) for lo, hi in zip(edges, edges[1:])}
    out["error_by_sensitivity_tracked_bottom_le_2px"] = {f"[{lo}, {hi})": q3(np.where(gv & (a["state"] == 0) & (np.abs(a["bottom"]) <= 2) & (sens >= lo) & (sens < hi), err, np.nan))
                                                          for lo, hi in zip(edges, edges[1:])}
    lim = {}
    big2, big10, good = gv & (err > 2), gv & (err > 10), gv & (err < 1)
    for L in LIMITS:
        flag = gv & (sens > L)
        kept = gv & ~flag
        lim[str(L)] = {"flagged": int(flag.sum()), "flagged_share": round(float(flag.sum() / gv.sum()), 4),
                       "caught_share_of_err_gt_2m": round(float((flag & big2).sum() / max(big2.sum(), 1)), 4),
                       "caught_share_of_err_gt_10m": round(float((flag & big10).sum() / max(big10.sum(), 1)), 4),
                       "lost_share_of_good_lt_1m": round(float((flag & good).sum() / max(good.sum(), 1)), 4),
                       "counts": {"err_gt_2m": int(big2.sum()), "err_gt_10m": int(big10.sum()), "good_lt_1m": int(good.sum())},
                       "kept": q3(np.where(kept, err, np.nan))}
    out["sensitivity_limits"] = lim
    # (b) height consistency, persons, tracked
    pers = gv & (a["cls"] == 0) & (a["state"] == 0)
    lo_off, hi_off = pers & (np.abs(a["bottom"]) <= 2), pers & (a["bottom"] > 10)
    hc = {}
    for H in HEIGHTS:
        dis, herr = a[f"dis_{H}"], a[f"herr_{H}"]
        defined = ~np.isnan(dis)
        row = {"persons_tracked": int(pers.sum()), "head_estimate_defined": int((pers & defined).sum()),
               "head_estimate_error": q3(np.where(pers, herr, np.nan)),
               "disagreement_bottom_le_2px": q3(np.where(lo_off, dis, np.nan)), "disagreement_bottom_gt_10px": q3(np.where(hi_off, dis, np.nan)),
               "cuts": {}}
        for cut in CUTS:
            f_lo, f_hi = lo_off & defined & (dis > cut), hi_off & defined & (dis > cut)
            n_lo, n_hi = int((lo_off & defined).sum()), int((hi_off & defined).sum())
            row["cuts"][str(cut)] = {"bottom_le_2px": {"n": n_lo, "flagged": int(f_lo.sum()), "flagged_share": round(float(f_lo.sum() / max(n_lo, 1)), 4)},
                                     "bottom_gt_10px": {"n": n_hi, "flagged": int(f_hi.sum()), "flagged_share": round(float(f_hi.sum() / max(n_hi, 1)), 4)},
                                     "all_persons_flagged": int((pers & defined & (dis > cut)).sum()),
                                     "all_persons_flagged_err_gt_10m_share": round(float((pers & defined & (dis > cut) & (err > 10)).sum() / max((pers & (err > 10)).sum(), 1)), 4),
                                     "all_persons_flagged_err_lt_1m_share": round(float((pers & defined & (dis > cut) & (err < 1)).sum() / max((pers & (err < 1)).sum(), 1)), 4)}
        hc[str(H)] = row
    out["height_consistency_persons"] = hc
    p = ev.ROOT / f"research/m1a/position_sensitivity_{ds}.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    ds, label, what = sys.argv[1:4]
    if what == "cameras":
        for n, rec in enumerate(sorted(c["rec_id"] for c in m.Context(ds).validation_cameras()), 1):
            print(n, rec, camera(ds, label, rec), flush=True)
    else:
        aggregate(ds, label)
