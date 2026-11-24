"""D-55 step 2: record every key of the installed Ultralytics `botsort.yaml` with its default, and the D-55 settings.
Runs in `.venv-det`.

  PYTHONPATH=src .venv-det/bin/python research/m1b/botsort_keys.py   -> research/m1b/botsort_keys.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "out/m1b/ultralytics_config")
os.environ["YOLO_AUTOINSTALL"] = "false"
sys.path.insert(0, str(ROOT / "src"))

from rq1.tracking import botsort, bytetrack  # noqa: E402


def main() -> None:
    import ultralytics
    out = {"status": "D-55 step 2: installed BoT-SORT keys and the D-55 BoT-SORT settings (record only)",
           "library": f"ultralytics {ultralytics.__version__}", "file": "ultralytics/cfg/trackers/botsort.yaml",
           "installed_defaults": botsort.installed_defaults(), "d55_params": botsort.default_params(),
           "switched_off": {"with_reid": {"value": False, "installed_default": botsort.installed_defaults()["with_reid"],
                                          "effect": "no ReID encoder (trackers/utils/reid.py build_encoder returns None)"},
                            "gmc_method": {"value": "none", "installed_default": botsort.installed_defaults()["gmc_method"],
                                           "effect": "GMC.__init__ maps 'none' to method None; GMC.apply returns the identity warp and "
                                                     "BYTETracker._pre_first_associate skips GMC when the method is None (trackers/utils/gmc.py, "
                                                     "trackers/byte_tracker.py); no image is read"}},
           "assignment": "NumPy path, the AR-62 `lap` stub (rq1.tracking.bytetrack._prepare)",
           "bytetrack_installed_defaults": bytetrack.default_config()["params"]}
    p = ROOT / "research/m1b/botsort_keys.json"
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(p)


if __name__ == "__main__":
    main()
