"""Many tracker runs on one recording in one `.venv-det` process (D-55 steps 3 and 4).

The `.venv-det` start (Python, NumPy, Ultralytics imports) is paid once per recording, not once per configuration. Each
job is one tracker instance on one class, stepped exactly as `rq1.tracking.bytetrack.run_class` steps it (a fresh
instance per job, so jobs never share state).

  PYTHONPATH=src .venv-det/bin/python -m rq1.tracking.grid <in.json> <out.json>
in.json: {"frames": [...], "detections": [...] (as `rq1.tracking.bytetrack`),
          "jobs": [{"job": name, "tracker_id": "bytetrack" | "botsort", "class": "person" | "forklift", "params": {...}}]}
out.json: {"library": ..., "logs": {name: per-frame log (bytetrack format)}}
"""
from __future__ import annotations

import json
import os
import sys
from typing import List

from . import bytetrack as bt

TRACKERS = ("bytetrack", "botsort")


def run_job(frames: List[int], detections: List[dict], job: dict) -> List[dict]:
    if job["class"] not in bt.CLASSES:
        raise ValueError(f"unknown class {job['class']}")
    if job["tracker_id"] == "bytetrack":
        return bt.run_class(frames, detections, job["class"], job["params"])
    if job["tracker_id"] == "botsort":
        from . import botsort
        return botsort.run_class(frames, detections, job["class"], job["params"])
    raise ValueError(f"unknown tracker_id {job['tracker_id']}")


def run(frames: List[int], detections: List[dict], jobs: List[dict]) -> dict:
    import ultralytics
    names = [j["job"] for j in jobs]
    if len(set(names)) != len(names):
        raise ValueError("job names must be unique")
    return {"library": f"ultralytics {ultralytics.__version__}", "logs": {j["job"]: run_job(frames, detections, j) for j in jobs}}


def main(argv: List[str]) -> None:
    with open(argv[1]) as f:
        inp = json.load(f)
    out = run(inp["frames"], inp["detections"], inp["jobs"])
    tmp = argv[2] + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, sort_keys=True)
    os.replace(tmp, argv[2])


if __name__ == "__main__":
    main(sys.argv)
