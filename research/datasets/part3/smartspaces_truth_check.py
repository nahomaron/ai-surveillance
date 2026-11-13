"""T-18 part C data check, SmartSpaces synthetic scenes (statistics only, no pixels).
Per scene: calibration and ground-truth file hashes (Warehouse_001 is a re-render of 000: identical files expected);
frame ids vs each camera's video frame count; per camera, the visible 2D boxes against the image-clipped projection of
the object's 3D box under K E (`smartspaces.hull_excess`); forklift long axis; box floor height (z_centre - h/2); roll
and pitch.
Usage: PYTHONPATH=src python smartspaces_truth_check.py <out.json> <frames_check.json> <scene_dir> [...]"""
import collections
import hashlib
import json
import os
import sys

import numpy as np

from rq1.adapters import smartspaces


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pct(values, q):
    return round(float(np.percentile(values, q)), 3) if values else None


def main():
    out_path, frames_check = sys.argv[1], sys.argv[2]
    frames = {r["recording"]: r["frames"] for r in json.load(open(frames_check))["recordings"]}
    scenes = []
    for scene_dir in sys.argv[3:]:
        name = os.path.basename(scene_dir.rstrip("/"))
        cal_path, gt_path = os.path.join(scene_dir, "calibration.json"), os.path.join(scene_dir, "ground_truth.json")
        cals = smartspaces.calibrations(smartspaces.load(cal_path))
        doc = smartspaces.load(gt_path)
        n_video = {cam: n for rec, n in frames.items() if f"/{name}/videos/" in rec for cam in [os.path.basename(rec)[:-4]]}
        counts = sorted(set(n_video.values()))
        if len(counts) != 1:
            raise SystemExit(f"{name}: cameras differ in frame count {counts}")
        parsed = smartspaces.parse_frames(doc, counts[0])  # refuses frame ids other than 0 .. n-1
        excess = collections.defaultdict(list)
        behind = collections.Counter()
        listed, floor_z, axes, tilt = [], collections.defaultdict(list), collections.Counter(), collections.defaultdict(float)
        for k, objs in enumerate(parsed):
            for o in objs:
                floor_z[o.cls].append(o.centre[2] - o.scale[2] / 2)
                if o.cls == "forklift":
                    axes["y_long" if o.scale[1] > o.scale[0] else "x_long"] += 1
                tilt[o.cls] = max(tilt[o.cls], abs(o.rotation[0]), abs(o.rotation[1]))
                for cam in o.visible:
                    if cam not in cals:
                        raise SystemExit(f"{name}: visible box in camera {cam} without calibration")
                    e = smartspaces.hull_excess(cals[cam], o, cam)
                    if e is None:
                        behind[o.cls] += 1
                        continue
                    excess[o.cls].append(e)
                    if e > 2:
                        listed.append({"frame": k, "camera": cam, "class": o.cls, "obj_id": o.obj_id, "excess_px": round(e, 1)})
        allx = [e for v in excess.values() for e in v]
        scenes.append({"scene": name, "calibration_sha256": sha(cal_path), "ground_truth_sha256": sha(gt_path),
                       "cameras_calibrated": sorted(cals), "cameras_with_video": sorted(n_video), "video_frames": counts[0], "truth_frames": len(parsed),
                       "visible_boxes": len(allx), "behind_camera": dict(behind),
                       "within_2px": sum(e <= 2 for e in allx), "excess_gt_2px": len(listed),
                       "excess_px": {c: {"n": len(v), "p50": pct(v, 50), "p99": pct(v, 99), "max": round(max(v), 3)} for c, v in sorted(excess.items())},
                       "forklift_axes": dict(axes), "max_abs_roll_pitch_rad": {c: round(v, 9) for c, v in sorted(tilt.items())},
                       "box_floor_z_m": {c: {"min": round(min(v), 4), "p50": pct(v, 50), "max": round(max(v), 4)} for c, v in sorted(floor_z.items())},
                       "excess_gt_2px_list": listed[:200]})
    json.dump({"scenes": scenes}, open(out_path, "w"), indent=1)
    print(json.dumps([{k: v for k, v in s.items() if k != "excess_gt_2px_list"} for s in scenes], indent=1))


if __name__ == "__main__":
    main()
