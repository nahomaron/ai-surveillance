"""S3 tracker adapter, T2 comparator: Ultralytics BoT-SORT on S2 detections (D-55 step 2; same path as AR-62).

Runs in `.venv-det` (Python 3.9, Ultralytics 8.4.215, AGPL-3.0 accepted under D-43), like `rq1.tracking.bytetrack`:

- Parameters: Ultralytics' installed `botsort.yaml`, with exactly two options switched off (D-55 step 2):
  - re-identification: `with_reid: false` (the installed default is already false; it is set explicitly);
  - camera-motion compensation: `gmc_method: "none"`. In the installed `trackers/utils/gmc.py` (GMC.__init__, the
    `elif self.method in {"none", "None", None}` branch) this sets the method to None; `GMC.apply` then returns the
    identity warp, and `BYTETracker._pre_first_associate` skips GMC altogether when the method is None. No image is
    needed: with ReID off and GMC off, `update(results)` without an image is the documented path.
- Assignment: the NumPy path with the same `lap` stub (`bytetrack._prepare`, AR-62 item 5).
- One instance per class, stepped once per eligible frame; input and output format identical to `rq1.tracking.bytetrack`
  (`bytetrack.run_class` with `tracker_class=BOTSORT`).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from . import bytetrack as bt

SWITCHED_OFF = {"with_reid": False, "gmc_method": "none"}  # D-55 step 2


def installed_defaults() -> dict:
    """The installed `botsort.yaml`, every key, unchanged (`yaml_file` is the loader's own bookkeeping key)."""
    import ultralytics
    from ultralytics.utils import YAML
    cfg = dict(YAML.load(Path(ultralytics.__file__).parent / "cfg/trackers/botsort.yaml"))
    cfg.pop("yaml_file", None)
    return {k: cfg[k] for k in sorted(cfg)}


def default_params() -> dict:
    """The D-55 BoT-SORT defaults: the installed defaults with the two options switched off."""
    return {**installed_defaults(), **SWITCHED_OFF}


def default_config() -> dict:
    import ultralytics
    return {"library": f"ultralytics {ultralytics.__version__}", "tracker": "BOTSORT", "tracker_id": "botsort",
            "assignment": "ultralytics.utils.ops.linear_sum_assignment (use_lap=False)", "params": default_params(),
            "switched_off": dict(SWITCHED_OFF), "per_class": list(bt.CLASSES), "step": "one update per eligible frame"}


def _prepare():
    bt._prepare()  # lap stub and the NumPy assignment path, before the BoT-SORT import
    from ultralytics.trackers.bot_sort import BOTSORT
    return BOTSORT


def run_class(frames: List[int], detections: List[dict], cls: str, params: dict = None) -> List[dict]:
    params = params if params is not None else default_params()
    if params.get("with_reid") or str(params.get("gmc_method")).lower() != "none":
        raise ValueError("D-55 step 2: BoT-SORT runs with with_reid false and gmc_method none")
    return bt.run_class(frames, detections, cls, params, tracker_class=_prepare())


def run(frames: List[int], detections: List[dict], params_by_class: Dict[str, dict] = None) -> dict:
    config = default_config()
    if params_by_class is not None:
        if set(params_by_class) != set(bt.CLASSES):
            raise ValueError("params_by_class must name every class")
        config["params_by_class"] = params_by_class
    return {"config": config, "logs": {c: run_class(frames, detections, c, (params_by_class or {}).get(c)) for c in bt.CLASSES}}
