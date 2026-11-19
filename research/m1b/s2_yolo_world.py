"""T-23s / T-25p: S2 detector run, YOLO-World v2-s on every eligible frame (D-45 items 0 and 2). Runs in `.venv-det`.

  .venv-det/bin/python research/m1b/s2_yolo_world.py <rec_id> [<rec_id> ...]    -> out/m1b/pilot/s2raw/<rec_id>.json.gz

Per recording (resumable: a finished recording is skipped):
- frames come from `s2_frames.py` (main `.venv`, PyAV), eligible frames in decode order;
- YOLO-World v2-s (`yolov8s-worldv2.pt`) with `set_classes(["person", "forklift"])` once, then
  `predict(conf=0.05, device="cpu")` with the Ultralytics defaults (imgsz 640, NMS IoU 0.7, max_det 300), input RGB flipped
  to BGR: exactly the T-22 probe path (`zero_shot_probe.yolo_world`);
- every box with score >= 0.05 is stored raw; the class thresholds (person 0.20, forklift 0.05) are applied when the S2
  artifact is built (`rq1.perception.s2`), so the stored file is threshold-independent;
- per-frame wall time from the decoded array to the box list (as in the probe); the first frame of each recording also
  carries the model warm-up and is flagged.
Ultralytics settings live in out/m1b/ultralytics_config (sync off); no automatic installs.
"""
from __future__ import annotations

import gzip
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "out/m1b/ultralytics_config")
os.environ["YOLO_AUTOINSTALL"] = "false"

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zero_shot_probe as zp  # noqa: E402

RAW = ROOT / "out/m1b/pilot/s2raw"
MAIN_PY = ROOT / ".venv/bin/python"


def frames(rec_id: str):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    proc = subprocess.Popen([str(MAIN_PY), str(ROOT / "research/m1b/s2_frames.py"), rec_id], stdout=subprocess.PIPE, cwd=ROOT, env=env)
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError(f"{rec_id}: frame stream ended without an end marker")
            head = json.loads(line)
            if "end" in head:
                break
            n = head["height"] * head["width"] * 3
            buf = proc.stdout.read(n)
            if len(buf) != n:
                raise RuntimeError(f"{rec_id}: short frame read")
            yield head, np.frombuffer(buf, dtype=np.uint8).reshape(head["height"], head["width"], 3)
    finally:
        proc.stdout.close()
        if proc.wait() != 0:
            raise RuntimeError(f"{rec_id}: decoder exited with {proc.returncode}")


def provenance() -> str:
    """The code commit; refused when the source tree has uncommitted changes (as the T-21 driver does)."""
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research/m1b"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main(recs: list[str]) -> None:
    commit = provenance()
    import torch
    import ultralytics
    one = zp.yolo_world()
    RAW.mkdir(parents=True, exist_ok=True)
    weights = json.load(open(ROOT / "research/m1b/zero_shot_weights.json"))
    for rec in recs:
        dst = RAW / f"{rec}.json.gz"
        if dst.exists():
            print(rec, "skipped", flush=True)
            continue
        t0 = time.time()
        rows, seconds, size = [], [], None
        for head, img in frames(rec):
            t1 = time.perf_counter()
            dets = one(img)
            seconds.append(round(time.perf_counter() - t1, 4))
            size = (head["width"], head["height"])
            rows.append({"frame_index": head["frame_index"], "decode_seq": head["decode_seq"], "detections": dets})
        out = {"rec_id": rec, "model": "yolov8s-worldv2.pt", "weights_sha256": weights["yolov8s-worldv2.pt"]["sha256"],
               "classes": list(zp.CLASSES), "score_floor": zp.SCORE_MIN, "predict": {"imgsz": 640, "iou": 0.7, "max_det": 300, "device": "cpu"},
               "width": size[0], "height": size[1], "frames": rows, "seconds": seconds, "first_frame_includes_warmup": True,
               "wall_s": round(time.time() - t0, 1), "torch": torch.__version__, "torch_threads": torch.get_num_threads(),
               "ultralytics": ultralytics.__version__, "python": platform.python_version(), "code_commit": commit}
        tmp = dst.with_suffix(".tmp")
        with gzip.open(tmp, "wt") as f:
            json.dump(out, f)
        os.replace(tmp, dst)
        print(rec, "done", len(rows), "frames", out["wall_s"], "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
