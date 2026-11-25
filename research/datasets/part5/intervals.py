"""D-59 post-download checks (qualification Part 5, 5.8), as Part 2 (2.5) for every new recording.

Usage: python -I intervals.py <out.json> <scene_dir>...
Per video: codec, declared fps, width x height, frame count and the frame-interval distribution from packet timestamps in
presentation order (PyAV, demux only, no pixels decoded); VFR when any interval differs from the median by more than
1 ms (rv1, AR-27, as 2.5). Per scene: whether every camera's frame count equals the ground-truth frame count, and
whether every video has a calibration entry. Statistics only."""
import json
import os
import sys
from fractions import Fraction

import av
import numpy as np


def video_stats(path):
    with av.open(path) as c:
        s = c.streams.video[0]
        pts = sorted(p.pts for p in c.demux(s) if p.pts is not None)
        tb = s.time_base
        info = {"codec": s.codec_context.name, "declared_fps": float(s.average_rate or 0),
                "width": s.codec_context.width, "height": s.codec_context.height}
    d = np.diff(np.array([float(Fraction(p) * tb) for p in pts])) * 1000.0
    med = float(np.median(d))
    info.update({"frames": len(pts), "min_ms": round(float(d.min()), 3), "median_ms": round(med, 3),
                 "p99_ms": round(float(np.percentile(d, 99)), 3), "max_ms": round(float(d.max()), 3),
                 "vfr": bool(np.any(np.abs(d - med) > 1.0))})
    return info


def main():
    out = {}
    for scene_dir in sys.argv[2:]:
        name = os.path.basename(scene_dir.rstrip("/"))
        gt_frames = len(json.load(open(os.path.join(scene_dir, "ground_truth.json"))))
        cal = json.load(open(os.path.join(scene_dir, "calibration.json")))
        cal_ids = {x.get("id") for x in cal.get("sensors", [])}
        vids = {}
        for n in sorted(os.listdir(os.path.join(scene_dir, "videos"))):
            if n.endswith(".mp4"):
                vids[n[:-4]] = video_stats(os.path.join(scene_dir, "videos", n))
        out[name] = {"ground_truth_frames": gt_frames, "videos": vids,
                     "all_frame_counts_equal_ground_truth": all(v["frames"] == gt_frames for v in vids.values()),
                     "cameras_without_calibration": sorted(set(vids) - cal_ids),
                     "vfr_recordings": sum(v["vfr"] for v in vids.values())}
        v = list(vids.values())
        print(name, len(v), "frames", sorted({x["frames"] for x in v}), "gt", gt_frames,
              "interval ms", min(x["min_ms"] for x in v), max(x["max_ms"] for x in v), "vfr", out[name]["vfr_recordings"],
              "nocal", out[name]["cameras_without_calibration"], sorted({(x["width"], x["height"], x["codec"]) for x in v}),
              flush=True)
    json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
