"""Forklift yaw against the direction of motion (agent's check for AR-52 item 2 / AR-50 item 3; statistics only).
For every forklift and frame k: displacement d = xy(k + STEP) - xy(k). Where |d| / (STEP / 30 s) >= V_MIN, the angle
between the motion direction and the yaw axis is folded to [0, 90] degrees (the footprint is symmetric under a half-turn).
0 = moving along the yaw axis (forwards or backwards); 90 = moving across it. Reported for the adapter's yaw (long axis)
and, for comparison, the literal supplied rotation. Frames are split by yaw rate over the same step: straight (< TURN deg/s)
and turning (a pivoting forklift's box centre moves across its axis, so only straight frames test the axis).
Usage: PYTHONPATH=src python yaw_motion_check.py <out.json> <sdg_members_root> <smartspaces ground_truth.json>"""
import collections
import glob
import json
import math
import os
import sys

import numpy as np

from rq1.adapters import sdg_truth, smartspaces

STEP, FPS, V_MIN, TURN = 10, 30.0, 0.3, 5.0


def fold(angle):
    a = abs(math.remainder(angle, math.pi))
    return math.degrees(a)


def stats(values):
    if not values:
        return {"n": 0}
    v = np.array(values)
    return {"n": len(v), "p50": round(float(np.percentile(v, 50)), 2), "p90": round(float(np.percentile(v, 90)), 2), "p99": round(float(np.percentile(v, 99)), 2),
            "max": round(float(v.max()), 2), "within_15_deg": round(float((v <= 15).mean()), 4), "beyond_75_deg": round(float((v >= 75).mean()), 4)}


def angles(path):
    """path: list of (xy, yaw_adapter, yaw_literal) per frame (None where absent)."""
    out = {"straight": ([], []), "turning": ([], [])}
    for k in range(len(path) - STEP):
        p, q = path[k], path[k + STEP]
        if p is None or q is None:
            continue
        dx, dy = q[0][0] - p[0][0], q[0][1] - p[0][1]
        if math.hypot(dx, dy) / (STEP / FPS) < V_MIN:
            continue
        heading = math.atan2(dy, dx)
        rate = abs(math.degrees(math.remainder(q[1] - p[1], 2 * math.pi))) / (STEP / FPS)
        a, b = out["straight" if rate < TURN else "turning"]
        a.append(fold(heading - p[1]))
        b.append(fold(heading - p[2]))
    return out


def report(total, i):
    """`all` is the Architect's check (every frame above the speed threshold); the split explains it."""
    return {"all": stats(total["straight"][i] + total["turning"][i]), **{kind: stats(v[i]) for kind, v in total.items()}}


def merge(total, part):
    for kind in total:
        total[kind][0].extend(part[kind][0])
        total[kind][1].extend(part[kind][1])


def main():
    out_path, members, gt_path = sys.argv[1:4]
    res = {"step_frames": STEP, "v_min_mps": V_MIN, "turn_deg_per_s": TURN}
    total, runs = {"straight": ([], []), "turning": ([], [])}, 0
    for f in sorted(glob.glob(os.path.join(members, "*", "*.ceiling_00.object_detection.jsonl"))):
        path = []
        for line in open(f):
            fk = [o for o in sdg_truth.parse_frame(line) if o.cls == "forklift"]
            path.append((fk[0].xy, fk[0].yaw, fk[0].yaw) if fk else None)  # SDG: adapter yaw is the supplied local-x direction
        merge(total, angles(path))
        runs += 1
    res["sdg"] = {"runs": runs, "adapter_yaw_long_axis_local_x": report(total, 0)}
    doc = smartspaces.load(gt_path)
    paths = collections.defaultdict(lambda: [None] * len(doc))
    for k in range(len(doc)):
        for o in doc[str(k)]:
            if o["object type"] == "Forklift":
                t = smartspaces.parse_object(o)
                paths[t.obj_id][k] = (t.xy, t.yaw, t.rotation[2])
    total = {"straight": ([], []), "turning": ([], [])}
    for path in paths.values():
        merge(total, angles(path))
    res["smartspaces"] = {"forklifts": len(paths), "adapter_yaw_long_axis_rotation_plus_90": report(total, 0),
                          "literal_rotation_z": report(total, 1)}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
