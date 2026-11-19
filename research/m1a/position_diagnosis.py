"""T-21 / G-M1a: diagnosis of the full_camera position error (Architect, 17 Nov 2026). Validation partition only (D-37);
statistics only, no pixels decoded; no definition or frozen value changed.

  python research/m1a/position_diagnosis.py <ds> run1 cameras     -> out/m1a/run1/<ds>/<rec>/posdiag.npz (resumable)
  python research/m1a/position_diagnosis.py <ds> run1 aggregate    -> research/m1a/position_diagnosis_<ds>.json

Population: every object_state row of the stored full_camera S4 whose S3 point is tracked or predicted (not lost). The
GV-01 population is the subset with a numeric position and a truth pose on that frame (as in `evaluate_m1a.gv_camera`).
Per point:
  state           tracked (dataset visible box) | predicted (image-clipped reprojection of the 3D box, T17.2)
  err_m           |full_camera position - simulator truth position| (NaN when no position or no truth)
  foot ray        the ray through the foot point (bottom-centre of the track box, CF-IMG) in world coordinates, computed
                  as `geometry.full_camera_to_floor` does (no distortion on either dataset); angle below the horizon
                  = asin(-d_z / |d|) in degrees; outcome: front (meets z = 0 at s > 0), behind (s <= 0: at or above the
                  horizon for a camera above the floor), parallel (|d_z| < 1e-12); range = horizontal distance from the
                  camera centre to the hit
  bottom_px       (tracked only) bottom edge of the image-clipped reprojected 3D box minus bottom edge of the visible box,
                  same frame, CF-IMG pixels; 0 = the box reaches the 3D box bottom ("feet visible"), > 0 = visible box
                  ends above it. Predicted points: NaN (their box is the reprojection, difference 0 by construction)
  border          the track box is within 1 px of an image border (left, top, right or bottom)
  true_dist_m     horizontal distance from the camera centre to the true position
The recomputed position is checked against the stored S4 x_m, y_m (count of mismatches > 1e-9 m reported).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import evaluate_m1a as ev  # noqa: E402
import m1a_common as m  # noqa: E402
from rq1.adapters import oracle_truth as ot  # noqa: E402

FIELDS = ("cls", "state", "err", "angle", "outcome", "range", "bottom", "border", "true_dist", "has_pos", "has_truth", "null_reason")
CLASSES = ("person", "forklift", "pallet_truck")
STATES = ("tracked", "predicted")
OUTCOMES = ("front", "behind", "parallel")


def camera(ds: str, label: str, rec: str) -> str:
    path = ev.out_dir(label, ds) / rec / "posdiag.npz"
    if path.exists():
        return "skipped"
    ctx = m.Context(ds)
    ctx.camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    cam = ev.Camera(ds, label, rec)
    fc = cam.units["full_camera"]
    if fc.get("s4") is None:
        np.savez_compressed(path.with_suffix(".tmp.npz"), stratum=cam.window["stratum_id"], n=0)
        os.replace(path.with_suffix(".tmp.npz"), path)
        return "no full_camera"
    s3 = ev.load_art(label, ds, fc["s3"])
    s4 = ev.load_art(label, ds, fc["s4"])
    trk_key = ev.track_map(s3, ev.oracle_keys(cam.visible), cam.classes)
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    pts = {(by_local[p["track_nk"][1]], p["frame_index"]): p for p in s3["track_point"]}
    data = m.load(ctx, rec)
    cal = data.calibration
    ecal = ctx.index[rec]["calibration"]
    w, h = ecal["image_size_px"]
    seq_of = {i: k for k, i in data.seq.items() if i is not None}
    obj_key = {str(k): k for objs in data.frames for k in objs}
    K = np.array(cal["intrinsics_K"], float).reshape(3, 3)
    R = np.array(cal["R_cam_from_world"], float).reshape(3, 3)
    t = np.array(cal["t_cam_from_world_m"], float)
    centre = -R.T @ t
    rows = []
    for r in s4["object_state"]:
        p = pts.get((r["track_id"], r["frame_index"]))
        if p is None or p["state"] not in STATES:
            continue
        key = trk_key[r["track_id"]]
        x1, y1, x2, y2 = p["bbox_xyxy_px"]
        bottom = math.nan
        if p["state"] == "tracked":
            obs = data.frames[seq_of[r["frame_index"]]][obj_key[key]]
            corners = np.asarray(obs.corners() if callable(obs.corners) else obs.corners, float)
            rb = ot.clipped_reprojection(ecal, corners)
            if rb is not None:
                bottom = rb[3] - y2
        border = x1 <= 1.0 or y1 <= 1.0 or x2 >= w - 1.0 or y2 >= h - 1.0
        truth = cam.truth.get((key, r["frame_index"]))
        rows.append((CLASSES.index(cam.classes[key]), STATES.index(p["state"]), p["foot_point_px"][0], p["foot_point_px"][1],
                     np.nan if r["x_m"] is None else r["x_m"], np.nan if r["y_m"] is None else r["y_m"],
                     np.nan if truth is None else truth[3], np.nan if truth is None else truth[4], bottom, border,
                     r.get("x_m_null_reason") or ""))
    if not rows:
        np.savez_compressed(path.with_suffix(".tmp.npz"), stratum=cam.window["stratum_id"], n=0)
        os.replace(path.with_suffix(".tmp.npz"), path)
        return "no points"
    cls, state, u, v, xs, ys, tx, ty, bottom, border, reason = (np.array(c) for c in zip(*rows))
    u, v, xs, ys, tx, ty = (a.astype(float) for a in (u, v, xs, ys, tx, ty))
    ray_cam = np.linalg.solve(K, np.stack([u, v, np.ones_like(u)]))  # 3 x n, as geometry.full_camera_to_floor
    ray = R.T @ ray_cam
    dz = ray[2]
    parallel = np.abs(dz) < 1e-12
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(parallel, np.nan, -centre[2] / dz)
    front = ~parallel & (s > 0)
    hx, hy = centre[0] + s * ray[0], centre[1] + s * ray[1]
    outcome = np.where(parallel, 2, np.where(front, 0, 1))
    angle = np.degrees(np.arcsin(-dz / np.linalg.norm(ray, axis=0)))
    rng = np.where(front, np.hypot(hx - centre[0], hy - centre[1]), np.nan)
    has_pos = ~np.isnan(xs)
    mismatch = int(np.sum(has_pos != front)) + int(np.sum(np.abs(np.where(front & has_pos, hx - xs, 0)) > 1e-9)
                                                     + np.sum(np.abs(np.where(front & has_pos, hy - ys, 0)) > 1e-9))
    has_truth = ~np.isnan(tx)
    err = np.hypot(xs - tx, ys - ty)
    true_dist = np.hypot(tx - centre[0], ty - centre[1])
    reasons = sorted(set(reason.tolist()))
    np.savez_compressed(path.with_suffix(".tmp.npz"), stratum=cam.window["stratum_id"], n=len(rows), cls=cls.astype(np.int8),
                        state=state.astype(np.int8), err=err, angle=angle, outcome=outcome.astype(np.int8), range=rng, bottom=bottom.astype(float),
                        border=border.astype(bool), true_dist=true_dist, has_pos=has_pos, has_truth=has_truth,
                        null_reason=np.array([reasons.index(x) for x in reason.tolist()], np.int16), reasons=np.array(reasons),
                        cam_height=centre[2], mismatch=mismatch)
    os.replace(path.with_suffix(".tmp.npz"), path)
    return f"done n={len(rows)} mismatch={mismatch}"


def summary(err: np.ndarray) -> dict:
    e = err[~np.isnan(err)]
    if e.size == 0:
        return {"n": 0}
    q = np.quantile(e, [0.5, 0.9, 0.99])
    return {"n": int(e.size), "median_m": round(float(q[0]), 3), "p90_m": round(float(q[1]), 3), "p99_m": round(float(q[2]), 3),
            "share_gt_2m": round(float(np.mean(e > 2.0)), 4), "share_gt_10m": round(float(np.mean(e > 10.0)), 4)}


def binned(err, values, edges, mask) -> dict:
    out = {}
    for lo, hi in zip(edges, edges[1:]):
        sel = mask & (values >= lo) & (values < hi)
        out[f"[{lo}, {hi})"] = summary(err[sel])
    sel = mask & np.isnan(values)
    if sel.any():
        out["n/a"] = summary(err[sel])
    return out


def aggregate(ds: str, label: str) -> None:
    recs = sorted(c["rec_id"] for c in m.Context(ds).validation_cameras())
    parts, strata, no_fc, mismatch, heights, reasons_all = [], [], [], 0, [], {}
    for rec in recs:
        z = np.load(ev.out_dir(label, ds) / rec / "posdiag.npz", allow_pickle=False)
        if int(z["n"]) == 0:
            no_fc.append(rec)
            continue
        n = int(z["n"])
        reasons = [str(x) for x in z["reasons"]]
        part = {f: z[f] for f in ("cls", "state", "err", "angle", "outcome", "range", "bottom", "border", "true_dist", "has_pos", "has_truth")}
        part["null_reason"] = np.array([reasons[i] for i in z["null_reason"]])
        part["stratum"] = np.full(n, str(z["stratum"]).split(":")[-1])
        parts.append(part)
        mismatch += int(z["mismatch"])
        heights.append(float(z["cam_height"]))
    a = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    err, gv = a["err"], a["has_pos"] & a["has_truth"]
    e = np.where(gv, err, np.nan)
    out = {"dataset": ds, "label": label, "status": "experimental (synthetic, oracle perception, validation partition)",
           "cameras": len(recs), "cameras_without_full_camera": len(no_fc), "points": int(a["cls"].size), "gv01_points": int(gv.sum()),
           "recomputed_vs_stored_mismatches": mismatch, "camera_height_m": {"min": round(min(heights), 3), "max": round(max(heights), 3)}}
    out["all"] = summary(e)
    out["by_state"] = {s: summary(e[a["state"] == i]) for i, s in enumerate(STATES)}
    out["by_class_viewpoint_state"] = {}
    for ci, c in enumerate(CLASSES):
        for vp in sorted(set(a["stratum"].tolist())):
            for si, s in enumerate(STATES):
                sel = (a["cls"] == ci) & (a["stratum"] == vp) & (a["state"] == si)
                if sel.any():
                    out["by_class_viewpoint_state"][f"{c}|{vp}|{s}"] = summary(e[sel])
    tracked = a["state"] == 0
    out["by_bottom_edge_px_tracked"] = binned(e, a["bottom"], [-1e9, -2, 2, 10, 50, 200, 1e9], tracked)
    out["by_border"] = {f"{s}|{'touching' if b else 'not_touching'}": summary(e[(a["state"] == si) & (a["border"] == b)])
                        for si, s in enumerate(STATES) for b in (True, False)}
    out["by_ray_angle_deg"] = binned(e, a["angle"], [-90, 0, 1, 2, 5, 10, 20, 45, 90.1], np.ones_like(gv))
    out["by_true_distance_m"] = binned(e, a["true_dist"], [0, 5, 10, 20, 50, 1e9], np.ones_like(gv))
    out["by_range_m"] = binned(e, a["range"], [0, 10, 20, 50, 100, 1000, 1e12], np.ones_like(gv))
    ray = {}
    for si, s in enumerate(STATES + ("all",)):
        sel = np.ones_like(gv) if s == "all" else a["state"] == si
        ray[s] = {"points": int(sel.sum()), "at_or_above_horizon": int((sel & (a["angle"] <= 0)).sum()),
                  "meets_floor_behind_camera": int((sel & (a["outcome"] == 1)).sum()), "parallel": int((sel & (a["outcome"] == 2)).sum()),
                  "meets_floor_in_front": int((sel & (a["outcome"] == 0)).sum()),
                  "in_front_beyond_50m": int((sel & (a["outcome"] == 0) & (a["range"] > 50)).sum()),
                  "in_front_beyond_100m": int((sel & (a["outcome"] == 0) & (a["range"] > 100)).sum()),
                  "in_front_beyond_1000m": int((sel & (a["outcome"] == 0) & (a["range"] > 1000)).sum()),
                  "in_front_below_1deg": int((sel & (a["outcome"] == 0) & (a["angle"] < 1)).sum())}
    out["ray_outcomes"] = ray
    nopos = ~a["has_pos"]
    out["null_positions"] = {"n": int(nopos.sum()), "by_reason": {r: int((nopos & (a["null_reason"] == r)).sum()) for r in sorted(set(a["null_reason"][nopos].tolist()))},
                             "by_outcome": {o: int((nopos & (a["outcome"] == i)).sum()) for i, o in enumerate(OUTCOMES)}}
    far = gv & (a["outcome"] == 0) & (a["range"] > 50)
    out["gv01_share_from_beyond_50m"] = {"points": int(far.sum()), "share_of_gv01_points": round(float(far.sum() / gv.sum()), 4),
                                         "share_of_sum_squared_error": round(float(np.nansum(np.where(far, err, 0) ** 2) / np.nansum(e ** 2)), 6),
                                         "gv01_without_them": summary(np.where(far, np.nan, e)),
                                         "rmse_m_all": round(float(math.sqrt(np.nanmean(e ** 2))), 3),
                                         "rmse_m_without_them": round(float(math.sqrt(np.nanmean(np.where(far, np.nan, e) ** 2))), 3)}
    feet = tracked & (np.abs(a["bottom"]) < 2) & ~a["border"]
    out["tracked_feet_visible_not_on_border"] = summary(np.where(feet, e, np.nan))
    out["tracked_feet_hidden_or_on_border"] = summary(np.where(tracked & ~feet, e, np.nan))
    path = ev.ROOT / f"research/m1a/position_diagnosis_{ds}.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    ds, label, what = sys.argv[1:4]
    if what == "cameras":
        for n, c in enumerate(sorted(c["rec_id"] for c in m.Context(ds).validation_cameras()), 1):
            print(n, c, camera(ds, label, c), flush=True)
    else:
        aggregate(ds, label)
