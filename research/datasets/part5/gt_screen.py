"""D-59 ground-truth screen (qualification Part 5, 5.4), run on each candidate scene's ground_truth.json before its
videos are downloaded.

Usage: python -I gt_screen.py <out.json> <ground_truth.json>...
Per scene: frame count and implied duration at 30 fps; distinct object ids per class; frames with at least one Forklift
and at least one Person in the scene; frames with a Forklift and a Person visible in the same camera (2d box present);
cameras that see both in one frame. Rule (declared before download, 5.4): a scene qualifies when at least one frame
holds a Forklift and a Person (class names as in the adapter; PalletTruck is not a forklift, D-22).
Statistics only: no box or position is written."""
import json
import os
import sys
from collections import defaultdict


def screen(path):
    doc = json.load(open(path))
    ids = defaultdict(set)
    both_scene = both_cam = 0
    cams_both = set()
    for fid in sorted(doc, key=int):
        objs = doc[fid]
        cls_cams = defaultdict(set)
        present = set()
        for o in objs:
            t = o["object type"]
            ids[t].add(o["object id"])
            present.add(t)
            for cam in (o.get("2d bounding box visible") or {}):
                cls_cams[cam].add(t)
        if {"Forklift", "Person"} <= present:
            both_scene += 1
        hit = [c for c, ts in cls_cams.items() if {"Forklift", "Person"} <= ts]
        if hit:
            both_cam += 1
            cams_both.update(hit)
    n = len(doc)
    return {
        "frames": n, "duration_s_at_30fps": round(n / 30, 3),
        "object_ids_per_class": {k: len(v) for k, v in sorted(ids.items())},
        "frames_forklift_and_person_in_scene": both_scene,
        "frames_forklift_and_person_same_camera": both_cam,
        "cameras_seeing_both": len(cams_both),
        "qualifies": both_scene > 0,
    }


def main():
    out = {}
    for p in sys.argv[2:]:
        scene = os.path.basename(os.path.dirname(os.path.abspath(p)))
        out[scene] = screen(p)
        print(scene, json.dumps(out[scene], sort_keys=True))
    json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
