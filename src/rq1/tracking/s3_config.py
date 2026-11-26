"""S3 run configuration and its configuration ID (F.1 A1.2 configuration class: `id(prefix, JCS(content))`; D-55 step 2).

Pure Python (importable in `.venv-det` and in the main environment). The installed tracker defaults are passed in; this
module never imports Ultralytics.

- `run_config(base, per_class)`: the tracker part of the S3 run configuration.
  - `base` is `rq1.tracking.bytetrack.default_config()` as installed (column C's recorded configuration).
  - `per_class`: {class: {"tracker_id": "bytetrack" | "botsort", "params": {...}}}.
  - Column C case (every class ByteTrack with exactly `base["params"]`): `base` is returned unchanged, without a
    `tracker_id` field. Adding the field would change column C's S3 configuration ID and therefore its S3 artifact IDs
    (`trc_id` hashes the whole configuration); D-55 step 2 then says to leave the field out for that case (CR-033).
  - Every other case: the library, assignment and step from `base`, and per class the tracker_id, the tracker class
    name and the full parameter dict.
- `trc_id(config, g_max, stitch=None)`: the S3 tracker configuration ID, the exact dict `research/m1b/run_pilot.py` hashes;
  with T25.1 stitching parameters they are added under `stitch` (T25.0: absent, the ID is unchanged).
"""
from __future__ import annotations

from typing import Dict

from rq1.ids import core

TRACKER_CLASS = {"bytetrack": "BYTETracker", "botsort": "BOTSORT"}
BRIDGING = "D-45 item 1"
TRACKED_BOX = "detection box (AR-62 item 3)"


def is_column_c(base: dict, per_class: Dict[str, dict]) -> bool:
    return set(per_class) == set(base["per_class"]) and all(
        v["tracker_id"] == "bytetrack" and v["params"] == base["params"] for v in per_class.values())


def run_config(base: dict, per_class: Dict[str, dict]) -> dict:
    if set(per_class) != set(base["per_class"]):
        raise ValueError(f"per_class must name exactly {base['per_class']}")
    for c, v in per_class.items():
        if v["tracker_id"] not in TRACKER_CLASS:
            raise ValueError(f"{c}: unknown tracker_id {v['tracker_id']}")
    if is_column_c(base, per_class):
        return base  # CR-033: column C's recorded configuration, unchanged
    return {"library": base["library"], "assignment": base["assignment"], "step": base["step"], "per_class": list(base["per_class"]),
            "classes": {c: {"tracker_id": per_class[c]["tracker_id"], "tracker": TRACKER_CLASS[per_class[c]["tracker_id"]],
                            "params": {k: per_class[c]["params"][k] for k in sorted(per_class[c]["params"])}} for c in base["per_class"]}}


def trc_id(config: dict, g_max: int, stitch=None) -> str:
    """`stitch`: T25.1 parameters (`rq1.tracking.stitching.StitchParams`) or None. Absent, the dict hashed is the E-1.2.25
    one, so the ID is unchanged (T25.0); present, they enter under the key `stitch` (AR-69 item 2)."""
    record = {"tracker": config, "g_max": g_max, "bridging": BRIDGING, "tracked_box": TRACKED_BOX}
    if stitch is not None:
        record["stitch"] = stitch.as_record()
    return core.make_id("trc", record)
