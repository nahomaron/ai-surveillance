"""Truth-side distribution of the forklift yaw rate, for the `forklift_turning` stratum proposal of T-20 (CR-023 ruling,
14 Nov 2026). Statistics only; no system output, no metric.
Estimator (the T9.2 construction applied to the forklift's yaw): for frame k, a and b are the first and last frames of the
window of length W centred on t_k, shifted to lie inside the object's run of frames (as T9.1), with t_b - t_a >= W / 2;
yaw_rate = |wrap(yaw_b - yaw_a)| / (t_b - t_a), wrap to (-pi, pi]. Frames at 30 fps. Reported in degrees per second for the
adapter's yaw (box long axis), per dataset and window, over all forklift frames and split by truth speed (centre
displacement over the same a..b) against V_MIN.
Usage: PYTHONPATH=src python yaw_rate_distribution.py <out.json> <sdg_members_root> <smartspaces ground_truth.json>"""
import collections
import glob
import json
import math
import os
import sys

from rq1.adapters import sdg_truth, smartspaces

FPS, V_MIN, WINDOWS_S = 30.0, 0.3, (0.5, 1.0)
EDGES = (1, 2, 5, 10, 15, 20, 30, 45, 60, 75, 90, 120)  # deg/s bin upper edges; the last bin is open


def rates(path, window_s):
    """path: per frame (xy, yaw) or None. Yields (yaw rate deg/s, speed m/s) for frames with a usable window."""
    half = int(round(window_s * FPS / 2))
    runs, start = [], None
    for k, p in enumerate(path + [None]):
        if p is not None and start is None:
            start = k
        elif p is None and start is not None:
            runs.append((start, k - 1))
            start = None
    for lo, hi in runs:
        if hi - lo < half:  # t_b - t_a >= W / 2 cannot hold
            continue
        for k in range(lo, hi + 1):
            a = min(max(k - half, lo), max(hi - 2 * half, lo))
            b = min(a + 2 * half, hi)
            dt = (b - a) / FPS
            if dt < window_s / 2 - 1e-9:
                continue
            (xa, ya), yaw_a = path[a]
            (xb, yb), yaw_b = path[b]
            yield abs(math.degrees(math.remainder(yaw_b - yaw_a, 2 * math.pi))) / dt, math.hypot(xb - xa, yb - ya) / dt


def summary(values):
    v = sorted(values)
    if not v:
        return {"frames": 0}
    rank = lambda q: round(v[max(1, math.ceil(q * len(v))) - 1], 2)
    hist, i = collections.OrderedDict(), 0
    for lo, hi in zip((0,) + EDGES, EDGES + (None,)):
        n = 0
        while i < len(v) and (hi is None or v[i] < hi):
            i, n = i + 1, n + 1
        hist[f"[{lo}, {hi if hi is not None else 'inf'})"] = n
    return {"frames": len(v), "p50": rank(0.5), "p90": rank(0.9), "p99": rank(0.99), "max": round(v[-1], 2), "histogram_deg_per_s": hist}


def report(paths):
    out = {}
    for w in WINDOWS_S:
        pairs = [r for path in paths for r in rates(path, w)]
        out[f"window_{w}_s"] = {"all_frames": summary([r for r, _ in pairs]), "moving": summary([r for r, s in pairs if s >= V_MIN]),
                                "not_moving": summary([r for r, s in pairs if s < V_MIN])}
    return out


def main():
    out_path, members, gt_path = sys.argv[1:4]
    res = {"fps": FPS, "v_min_mps": V_MIN, "percentiles": "nearest-rank", "estimator": "T9.2 construction on the forklift yaw (see the script)"}
    sdg = []
    for f in sorted(glob.glob(os.path.join(members, "*", "*.ceiling_00.object_detection.jsonl"))):
        path = []
        for line in open(f):
            fk = [o for o in sdg_truth.parse_frame(line) if o.cls == "forklift"]
            path.append((fk[0].xy, fk[0].yaw) if fk else None)
        sdg.append(path)
    res["sdg"] = {"runs": len(sdg), **report(sdg)}
    doc = smartspaces.load(gt_path)
    paths = collections.defaultdict(lambda: [None] * len(doc))
    for k in range(len(doc)):
        for o in doc[str(k)]:
            if o["object type"] == "Forklift":
                t = smartspaces.parse_object(o)
                paths[t.obj_id][k] = (t.xy, t.yaw)
    res["smartspaces"] = {"forklifts": len(paths), **report(list(paths.values()))}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
