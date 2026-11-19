"""T-25p item 3c (D-45): independent frame-level check of both zero-shot detectors on cameras that were not in the probe.

  PYTHONPATH=src .venv/bin/python research/m1b/frame_check.py select
  PYTHONPATH=src .venv/bin/python research/m1b/frame_check.py extract out/m1b/pilot/frame_check
  .venv-det/bin/python research/m1b/zero_shot_probe.py run yolo_world out/m1b/pilot/frame_check out/m1b/pilot/fc_det_yolo_world.json
  .venv-det/bin/python research/m1b/zero_shot_probe.py run grounding_dino out/m1b/pilot/frame_check out/m1b/pilot/fc_det_grounding_dino.json
  PYTHONPATH=src .venv/bin/python research/m1b/frame_check.py evaluate out/m1b/pilot/frame_check  -> research/m1b/pilot_frame_check.json

Selection: the probe procedure (`zero_shot_frames.select`, `even_positions`) with seed 2026111902 on the pool of SDG
validation cameras with an ORACLE-S3 minus the 20 probe cameras, i.e. 10 ceiling and 10 eye-level pilot cameras, 5 evenly
spaced eligible frames each. Reference boxes, models and matching are the probe's. Scoring is at the fixed D-45 item 0
thresholds only (YOLO-World person 0.20, forklift 0.05; Grounding DINO 0.45 both); no threshold is chosen here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilot_common as pc  # noqa: E402
import zero_shot_frames as zf  # noqa: E402
import zs_match as zm  # noqa: E402

THRESHOLDS = {"yolo_world": {"person": 0.20, "forklift": 0.05}, "grounding_dino": {"person": 0.45, "forklift": 0.45}}  # D-45 item 0


def selection() -> list[dict]:
    cameras, runs = zf.committed_inputs()
    probe = set(pc.probe_cameras())
    return zf.select([c for c in cameras if c["rec_id"] not in probe], runs, pc.FRAME_CHECK_SEED)


def evaluate(frames_dir: Path) -> dict:
    meta = json.load(open(frames_dir / "frames.json"))
    views = {"all": meta, "ceiling": [m for m in meta if m["viewpoint"] == "ceiling"], "eye_level": [m for m in meta if m["viewpoint"] == "eye_level"]}
    res = {"status": "T-25p frame-level check (D-45 item 3c); synthetic SDG validation; descriptive; nothing validated",
           "seed": pc.FRAME_CHECK_SEED, "cameras": sorted({(m["rec_id"], m["viewpoint"]) for m in meta}), "frames": len(meta),
           "matching": {"iou_min": zm.IOU_M, "rule": "same class, one-to-one by descending IoU (the probe matcher)"},
           "references": {v: {c: sum(1 for m in ms for r in m["references"] if r["class"] == c) for c in zf.CLASSES} for v, ms in views.items()},
           "thresholds": THRESHOLDS, "models": {}}
    for name, th in THRESHOLDS.items():
        p = pc.OUT / f"fc_det_{name}.json"
        d = json.load(open(p))
        assert d["frames"] == [m["file"] for m in meta]
        by_file = dict(zip(d["frames"], d["detections"]))
        secs = sorted(d["seconds"])
        res["models"][name] = {"seconds_per_frame_median": secs[len(secs) // 2], "results": {
            v: {c: zm.counts([{"references": m["references"], "detections": by_file[m["file"]]} for m in ms], c, th[c]) for c in zf.CLASSES}
            for v, ms in views.items()}}
    return res


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "select":
        for c in selection():
            print(c["viewpoint"], c["rec_id"], c["run"], c["camera"])
    elif cmd == "extract":
        zf.extract(Path(sys.argv[2]), seed=pc.FRAME_CHECK_SEED, exclude=frozenset(pc.probe_cameras()))
    elif cmd == "evaluate":
        out = evaluate(Path(sys.argv[2]))
        (pc.ROOT / "research/m1b/pilot_frame_check.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(json.dumps({k: out["models"][k]["results"]["all"] for k in out["models"]}, indent=1))
