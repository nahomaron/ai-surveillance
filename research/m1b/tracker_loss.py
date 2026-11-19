"""T-25p revision (Owner instruction of 19 Nov 2026, item 2d): where frame-level recall is lost between S2 and S3.

  PYTHONPATH=src .venv/bin/python research/m1b/tracker_loss.py   -> research/m1b/pilot_tracker_loss.json

Reads the stored pilot artifacts only (S2 `detection`, S3 `track_point`) and the T-21 oracle references; no stage is re-run.
Per class, on every eligible pilot frame, against the reference-visible boxes clipped to the image (the probe's reference,
as in `evaluate_pilot.detection_counts`), with the probe matcher (`zs_match.match`: same class, IoU >= 0.3, one-to-one by
descending IoU):
- bands: the kept S2 detections by score band [thr, 0.10), [0.10, 0.25), >= 0.25, each split by (i) matched to a reference
  box among all S2 detections of the frame, (ii) whether the detection became a `tracked` S3 point (its `detection_id`);
- stages: matched references for (1) S2 detections, (2) tracked S3 points, (3) tracked + predicted S3 points. Lost points
  carry no box and take no part. Matcher order: tracked points by their detection's score, predicted points after them
  (score 0), input order otherwise. A tracked point carries its detection's box (AR-62 item 3).
The band edges 0.10 and 0.25 are ByteTrack's default track_low_thresh and track_high_thresh (descriptive only).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import zs_match as zm  # noqa: E402

CLASSES = ("person", "forklift")
THRESHOLDS = {"person": 0.20, "forklift": 0.05}  # D-45 item 0 (= rq1.perception.s2.THRESHOLDS)
LOW, HIGH = 0.10, 0.25
BANDS = ("[thr, 0.10)", "[0.10, 0.25)", ">= 0.25")
KINDS = ("matched_tracked", "matched_not_tracked", "unmatched_tracked", "unmatched_not_tracked")


def band(score: float) -> str:
    return BANDS[0] if score < LOW else BANDS[1] if score < HIGH else BANDS[2]


def camera(refs_by_frame: dict, dets: list[dict], points: list[dict], frames, thresholds: dict = THRESHOLDS) -> dict:
    """refs_by_frame: frame -> [(class, box)]; dets: S2 rows (det_id, frame_index, class, bbox_xyxy_px, score);
    points: S3 points with their track's class (frame_index, class, bbox_xyxy_px, state, detection_id)."""
    for d in dets:
        if d["score"] < thresholds[d["class"]]:
            raise ValueError(f"detection {d['det_id']} below the {d['class']} threshold")
    score = {d["det_id"]: d["score"] for d in dets}
    tracked_ids = {p["detection_id"] for p in points if p["state"] == "tracked"}
    dets_f, pts_f = defaultdict(list), defaultdict(list)
    for d in dets:
        dets_f[d["frame_index"]].append(d)
    for p in points:
        if p["state"] in ("tracked", "predicted"):
            pts_f[p["frame_index"]].append(p)
    bands = {c: {b: dict.fromkeys(KINDS, 0) for b in BANDS} for c in CLASSES}
    stages = {c: {"references": 0, "s2": 0, "tracked": 0, "tracked_predicted": 0} for c in CLASSES}
    for i in frames:
        for c in CLASSES:
            refs = [b for cc, b in refs_by_frame.get(i, []) if cc == c]
            ds = [d for d in dets_f.get(i, []) if d["class"] == c]
            m = zm.match(refs, [(d["bbox_xyxy_px"], d["score"]) for d in ds])
            matched = {ds[j]["det_id"] for _, j, _ in m}
            for d in ds:
                kind = ("matched_" if d["det_id"] in matched else "unmatched_") + ("tracked" if d["det_id"] in tracked_ids else "not_tracked")
                bands[c][band(d["score"])][kind] += 1
            ps = [p for p in pts_f.get(i, []) if p["class"] == c]
            trk = [(p["bbox_xyxy_px"], score[p["detection_id"]]) for p in ps if p["state"] == "tracked"]
            pred = [(p["bbox_xyxy_px"], 0.0) for p in ps if p["state"] == "predicted"]
            st = stages[c]
            st["references"] += len(refs)
            st["s2"] += len(m)
            st["tracked"] += len(zm.match(refs, trk))
            st["tracked_predicted"] += len(zm.match(refs, trk + pred))
    return {"bands": bands, "stages": stages}


def add(total: dict, part: dict) -> None:
    for c in CLASSES:
        for b in BANDS:
            for k in KINDS:
                total["bands"][c][b][k] += part["bands"][c][b][k]
        for k, v in part["stages"][c].items():
            total["stages"][c][k] += v


def empty() -> dict:
    return {"bands": {c: {b: dict.fromkeys(KINDS, 0) for b in BANDS} for c in CLASSES},
            "stages": {c: {"references": 0, "s2": 0, "tracked": 0, "tracked_predicted": 0} for c in CLASSES}}


def run() -> dict:  # pragma: no cover - driver over stored artifacts
    import pilot_common as pc
    import evaluate_pilot as ep
    ev = ep.ev
    totals = {v: empty() for v in ("all", "ceiling", "eye_level")}
    recs = sorted(p.name for p in (pc.OUT / "cam").iterdir() if (p / "pipeline.json").exists())
    for rec in recs:
        pipe = json.loads((pc.OUT / "cam" / rec / "pipeline.json").read_text())
        cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
        s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
        trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
        ds = ep.files.read_table(str(pc.ROOT / f"out/t17_sdg/{pipe['s1']}/decode_summary.parquet"), "decode_summary", ev.m.A.SCHEMA_VERSION)[0]
        refs = {}
        for i, v in ep.ref_boxes(s3o, trk_key, cam.classes).items():
            refs[i] = [(c, b) for _, c, b in ((k, c, ep.ev_clip(b, ds["width_px"], ds["height_px"])) for k, c, b in v) if b is not None]
        dets = ep.load_pilot(pipe["s2"])["detection"]
        s3c = ep.load_pilot(pipe["s3"])
        cls = {t["track_local_id"]: t["class"] for t in s3c["track"]}
        points = [{**p, "class": cls[p["track_nk"][1]]} for p in s3c["track_point"]]
        part = camera(refs, dets, points, sorted(cam.eligible))
        for v in ("all", pc.viewpoint(cam.camera_name)):
            add(totals[v], part)
    return {"status": "T-25p revision item 2d; descriptive; synthetic SDG validation; nothing validated", "cameras": len(recs),
            "matching": {"iou_min": zm.IOU_M, "rule": "the probe matcher (same class, one-to-one by descending IoU)"},
            "bands": list(BANDS), "thresholds": THRESHOLDS, "bytetrack": {"track_low_thresh": LOW, "track_high_thresh": HIGH},
            "results": totals}


if __name__ == "__main__":  # pragma: no cover
    out = run()
    p = os.path.join(os.path.dirname(__file__), "pilot_tracker_loss.json")
    with open(p, "w") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out["results"]["all"]["stages"], indent=1))
