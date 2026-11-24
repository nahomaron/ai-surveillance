"""S3 tracker adapter: Ultralytics ByteTrack on S2 detections (D-45 item 1; WP-17 reduced to the pilot; AR-62).

Runs in `.venv-det` (Python 3.9, Ultralytics 8.4.215, AGPL-3.0 accepted under D-43). The Apache-2.0 `trackers` package
does not install there: every release needs numpy >= 2.0.2, and torch 2.2.2 in `.venv-det` is built against numpy 1.x
(D-45 item 1 fallback).

- One tracker instance per detection class ("person", "forklift"): no cross-class identity.
- Tracker parameters: Ultralytics' `bytetrack.yaml` defaults, read from the installed package and recorded in the run
  configuration; nothing is tuned.
- C' (D-47 item 1, post-hoc, exploratory): optional per-class parameters (`params_by_class`, from `cprime_params`), fixed
  by the Owner before the run: track_high_thresh = new_track_thresh = the class's detector threshold, track_low_thresh =
  min(0.10, detector threshold), everything else the installed defaults. Without it the configuration is exactly
  `default_config()`, so column C's S3 IDs are unchanged.
- Assignment: Ultralytics' own NumPy solver (`matching.linear_assignment(..., use_lap=False)`, the documented path when
  the optional `lap` package is absent; `lap` is not installed and is not pre-approved). A stub `lap` module satisfies
  the tracker's import and raises if it is ever called.
- Input: the S2 detection rows of one recording, grouped by eligible frame in decode order; the tracker steps once per
  eligible frame (ineligible frames are not shown to it).
- Output: the per-class log read by `rq1.tracking.bridging.points_from_log`.

  PYTHONPATH=src .venv-det/bin/python -m rq1.tracking.bytetrack <in.json> <out.json>
in.json: {"frames": [frame_index, ...] (eligible, decode order), "detections": [{"frame_index", "det_index", "class",
"bbox_xyxy_px", "score"}, ...], optional "params_by_class": {class: full parameter dict} (D-47 item 1)}
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from typing import Dict, List

CLASSES = ("person", "forklift")
_PATCHED = False
# Before any Ultralytics import: settings outside the home folder, no automatic package installation.
os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(__file__).resolve().parents[3] / "out/m1b/ultralytics_config"))
os.environ["YOLO_AUTOINSTALL"] = "false"


def _prepare():
    """Import Ultralytics' ByteTrack with the NumPy assignment path (no `lap`) and no settings file in the home folder."""
    global _PATCHED
    if "lap" not in sys.modules:
        try:
            import lap  # noqa: F401  (not expected in .venv-det)
            raise RuntimeError("the `lap` package is installed; AR-62 fixes the NumPy assignment path, remove `lap` or revise AR-62")
        except ImportError:
            stub = types.ModuleType("lap")
            stub.__version__ = "stub (AR-62: unused)"

            def _never(*a, **k):
                raise RuntimeError("lap.lapjv called: AR-62 requires use_lap=False")
            stub.lapjv = _never
            sys.modules["lap"] = stub
    from ultralytics.trackers.utils import matching
    if not _PATCHED:
        original = matching.linear_assignment

        def linear_assignment(cost_matrix, thresh, use_lap=True):
            return original(cost_matrix, thresh, use_lap=False)
        matching.linear_assignment = linear_assignment
        _PATCHED = True
    from ultralytics.trackers.byte_tracker import BYTETracker
    return BYTETracker


def default_config() -> dict:
    """Ultralytics' ByteTrack defaults as installed (recorded in the run configuration, not tuned)."""
    import ultralytics
    from ultralytics.utils import YAML
    path = Path(ultralytics.__file__).parent / "cfg/trackers/bytetrack.yaml"
    cfg = dict(YAML.load(path))
    cfg.pop("yaml_file", None)
    return {"library": f"ultralytics {ultralytics.__version__}", "tracker": "BYTETracker", "assignment": "ultralytics.utils.ops.linear_sum_assignment (use_lap=False)",
            "params": {k: cfg[k] for k in sorted(cfg)}, "per_class": list(CLASSES), "step": "one update per eligible frame"}


def aligned_params(defaults: dict, det_threshold: float) -> dict:
    """D-47 item 1 (C'): the defaults with track_high_thresh = new_track_thresh = det_threshold and
    track_low_thresh = min(0.10, det_threshold). Pure; the input is not modified."""
    out = dict(defaults)
    out.update(track_high_thresh=det_threshold, new_track_thresh=det_threshold, track_low_thresh=min(0.10, det_threshold))
    return out


def cprime_params(defaults: dict, det_thresholds: Dict[str, float]) -> Dict[str, dict]:
    """D-47 item 1: per-class C' parameters from the S2 class thresholds."""
    return {c: aligned_params(defaults, det_thresholds[c]) for c in CLASSES}


class _Dets:
    """The minimal Results-like object BYTETracker.update reads: conf, cls, xywh, xyxy, len, boolean indexing."""

    def __init__(self, xyxy, conf, cls):
        import numpy as np
        self.xyxy = np.asarray(xyxy, dtype=np.float32).reshape(-1, 4)
        self.conf = np.asarray(conf, dtype=np.float32).reshape(-1)
        self.cls = np.asarray(cls, dtype=np.float32).reshape(-1)
        xy = (self.xyxy[:, :2] + self.xyxy[:, 2:]) / 2
        self.xywh = np.concatenate([xy, self.xyxy[:, 2:] - self.xyxy[:, :2]], axis=1)

    def __len__(self):
        return len(self.conf)

    def __getitem__(self, mask):
        return _Dets(self.xyxy[mask], self.conf[mask], self.cls[mask])


def run_class(frames: List[int], detections: List[dict], cls: str, params: dict = None, tracker_class=None) -> List[dict]:
    """Track one class over the eligible frames. `detections`: S2 rows (any class; others are ignored). `params`: the
    tracker parameters (default: the installed defaults). `tracker_class`: the Ultralytics tracker class (default
    BYTETracker; `rq1.tracking.botsort` passes BOTSORT, D-55 step 2); the input and output format are the same."""
    from types import SimpleNamespace
    BYTETracker = _prepare()
    params = params if params is not None else default_config()["params"]
    tracker = (tracker_class or BYTETracker)(SimpleNamespace(**params))
    by_frame: Dict[int, List[dict]] = {}
    for d in detections:
        if d["class"] == cls:
            by_frame.setdefault(int(d["frame_index"]), []).append(d)
    log = []
    for i in frames:
        dets = sorted(by_frame.get(i, []), key=lambda d: d["det_index"])
        res = _Dets([d["bbox_xyxy_px"] for d in dets], [d["score"] for d in dets], [0.0] * len(dets))
        out = tracker.update(res)
        tracked = []
        for row in out.tolist() if len(out) else []:
            k = int(row[7])
            tracked.append([int(row[4]), int(dets[k]["det_index"]), [float(v) for v in dets[k]["bbox_xyxy_px"]]])
        lost = [[int(t.track_id), [float(v) for v in t.xyxy.tolist()]] for t in tracker.lost_stracks]
        log.append({"frame_index": i, "tracked": sorted(tracked), "lost": sorted(lost)})
    return log


def run(frames: List[int], detections: List[dict], params_by_class: Dict[str, dict] = None) -> dict:
    config = default_config()
    if params_by_class is not None:
        if set(params_by_class) != set(CLASSES):
            raise ValueError("params_by_class must name every class")
        config["params_by_class"] = params_by_class
    return {"config": config, "logs": {cls: run_class(frames, detections, cls, (params_by_class or {}).get(cls)) for cls in CLASSES}}


def main(argv: List[str]) -> None:
    src, dst = argv[1], argv[2]
    with open(src) as f:
        inp = json.load(f)
    out = run(inp["frames"], inp["detections"], inp.get("params_by_class"))
    tmp = dst + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, sort_keys=True)
    os.replace(tmp, dst)


if __name__ == "__main__":
    main(sys.argv)
