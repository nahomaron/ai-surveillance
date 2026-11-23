"""D-53 step 3 (D4): forklift offset with detector boxes. Diagnostic, tuning subset, not a reported result. Stored S2
detections only; the detector is not re-run; frame level, before tracking (no tracker setting enters).

  PYTHONPATH=src .venv/bin/python research/m1b/d4_detector_offset.py   -> research/m1b/d4_detector_offset.json

Cameras: the tuning cameras (`v2_camera_sets.json`) with a stored pilot S2 artifact (YOLO-World, `out/m1b/pilot/cam/<rec>/
pipeline.json`). The 20 T-22 probe cameras were not in the pilot and have no stored S2 run; they are listed as missing.
Matching: as the pilot frame metrics (`evaluate_pilot.detection_counts`): every eligible frame; references = the
reference-visible boxes (tracked ORACLE-S3 points, T17.6) clipped to the image; detections = the S2 rows (thresholds
applied); `zs_match.match` (same class, IoU >= 0.3, one-to-one). Forklift matches only.
Position: the detection box bottom-centre ((x1 + x2) / 2, y2) projected with `geometry.full_camera_to_floor` (as S4).
Error and its along-sight component, theta and bins: as step 1 (`d1_anchor_angle`), to the simulator centre of the matched
reference identity. For comparison on the same identity-frames: the stored column B S4 position (oracle box) where it has one.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import d1_anchor_angle as d1  # noqa: E402
from cr007_evidence import _q, camera_centre  # noqa: E402

STATUS = d1.STATUS


def bottom_centre(box) -> tuple:
    return ((box[0] + box[2]) / 2, box[3])


def table(rows: list[dict], key: str = "along") -> dict:
    al = [r[key] for r in rows if r.get(key) is not None]
    return {"n": len(al), "along_signed_median_m": _q(al, 50), "along_signed_p95_m": _q(al, 95), "along_signed_p05_m": _q(al, 5),
            "along_abs_median_m": _q([abs(x) for x in al], 50), "along_abs_p95_m": _q([abs(x) for x in al], 95)}


def summarize(rows_by_view: dict) -> dict:
    out = {}
    for v, rows in rows_by_view.items():
        out[v] = {"detector_box": table(rows), "by_theta": {}}
        paired = [r for r in rows if r.get("oracle_along") is not None]
        out[v]["paired_same_frames"] = {"n": len(paired), "detector_box": table(paired), "oracle_box_column_B": table(paired, "oracle_along"),
                                        "median_difference_detector_minus_oracle_m": _q([r["along"] - r["oracle_along"] for r in paired], 50)}
        out[v]["paired_by_theta"] = {}
        for lo, hi in d1.BINS:
            k = f"{lo}-{hi}"
            out[v]["by_theta"][k] = table([r for r in rows if d1.bin_of(r["theta"]) == k])
            pb = [r for r in paired if d1.bin_of(r["theta"]) == k]
            out[v]["paired_by_theta"][k] = {"n": len(pb), "detector_signed_median_m": _q([r["along"] for r in pb], 50),
                                            "oracle_signed_median_m": _q([r["oracle_along"] for r in pb], 50),
                                            "median_difference_detector_minus_oracle_m": _q([r["along"] - r["oracle_along"] for r in pb], 50)}
    return out


def run() -> dict:  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    import pilot_common as pc
    import run_pilot as rp
    import v2_sets
    import zs_match as zm
    from rq1.schema import files
    from rq1.substrate import geometry
    ev = ep.ev
    ctx = pc.m.Context("sdg")
    rows_by_view = {"all": [], "ceiling": [], "eye_level": []}
    used, missing, counts = [], [], defaultdict(int)
    for rec in v2_sets.tuning():
        pipe_path = pc.OUT / "cam" / rec / "pipeline.json"
        if not pipe_path.exists():
            missing.append(rec)
            continue
        used.append(rec)
        pipe = json.loads(pipe_path.read_text())
        cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
        view = pc.viewpoint(cam.camera_name)
        _, _, cal = rp.load_s1(ctx, rec)
        C = camera_centre(cal["R_cam_from_world"], cal["t_cam_from_world_m"])
        s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
        trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
        key_trk = {v: k for k, v in trk_key.items()}
        refs_by_frame = ep.ref_boxes(s3o, trk_key, cam.classes)
        s4b = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["full_camera"]["s4"])
        oracle_pos = {(r["track_id"], r["frame_index"]): (r["x_m"], r["y_m"]) for r in s4b["object_state"] if r["x_m"] is not None}
        dets = ep.load_pilot(pipe["s2"])["detection"]
        ds = files.read_table(str(pc.ROOT / f"out/t17_sdg/{pipe['s1']}/decode_summary.parquet"), "decode_summary", ev.m.A.SCHEMA_VERSION)[0]
        w, h = ds["width_px"], ds["height_px"]
        by_frame = defaultdict(list)
        for d in dets:
            if d["class"] == "forklift":
                by_frame[d["frame_index"]].append(d)
        for i in sorted(cam.eligible):
            refs = [(k, ep.ev_clip(b, w, h)) for k, c, b in refs_by_frame.get(i, []) if c == "forklift"]
            refs = [(k, b) for k, b in refs if b is not None]
            fd = by_frame.get(i, [])
            for ri, di, _ in zm.match([b for _, b in refs], [(d["bbox_xyxy_px"], d["score"]) for d in fd]):
                counts["matched"] += 1
                key = refs[ri][0]
                t = cam.truth.get((key, i))
                if t is None or t[5] is None:
                    counts["no_truth_or_yaw"] += 1
                    continue
                xy = geometry.full_camera_to_floor(cal, bottom_centre(fd[di]["bbox_xyxy_px"]))
                if xy is None:
                    counts["projection_undefined"] += 1
                    continue
                row = d1.frame_row(xy, (t[3], t[4]), t[5], C)
                op = oracle_pos.get((key_trk[key], i))
                row["oracle_along"] = d1.frame_row(op, (t[3], t[4]), t[5], C)["along"] if op else None
                rows_by_view["all"].append(row)
                rows_by_view[view].append(row)
    return {"status": STATUS, "decision": "D-53 step 3", "contract": "E-1.2.24 (no change)",
            "cameras_used": len(used), "cameras_used_by_viewpoint": {v: sum(1 for r in used if pc.viewpoint(ev.m.Context("sdg").camera(r)["camera"]) == v) for v in ("ceiling", "eye_level")},
            "cameras_missing_stored_s2": len(missing), "missing_rec_ids": missing,
            "missing_reason": "T-22 probe cameras: not in the T-25p pilot, so no stored S2 run; the detector is not re-run (D-53 step 3)",
            "detector": "YOLO-World (pilot S2, thresholds person 0.20 / forklift 0.05)", "match_counts": dict(counts),
            "definitions": {"position": "detection box bottom-centre through full_camera_to_floor",
                            "along": "as d1_anchor_angle: error . unit line of sight; negative = toward the camera",
                            "paired_same_frames": "the same identity-frames with a stored column B S4 position (oracle box)"},
            "result": summarize(rows_by_view)}


if __name__ == "__main__":  # pragma: no cover
    import pilot_common as pc
    p = pc.ROOT / "research/m1b/d4_detector_offset.json"
    pc.write_json(p, run())
    print("wrote", p)
