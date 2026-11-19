"""T-25p detector-path pilot (D-45 item 3): population, paths and shared constants. Main `.venv`.

Population (D-45 item 3a): every SDG validation camera with an ORACLE-S3 (`m1a_common.Context.validation_cameras`,
226), minus the 20 cameras of the T-22 probe (`zero_shot_probe.json` selection), on which the thresholds were chosen.
No SmartSpaces, no test partition (ERR-LEAKAGE from `Context.camera`), no real footage.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1a"))
import m1a_common as m  # noqa: E402

OUT = Path(os.environ.get("PILOT_OUT", str(ROOT / "out/m1b/pilot")))  # PILOT_OUT: smoke runs only
RAW = ROOT / "out/m1b/pilot/s2raw"  # raw detector output per camera (`.venv-det`)
CONTRACT = "E-1.2.21"
FRAME_CHECK_SEED = 2026111902  # D-45 item 3c


def probe_cameras() -> list[str]:
    sel = json.load(open(ROOT / "research/m1b/zero_shot_probe.json"))["selection"]["cameras"]
    return sorted(c["rec_id"] for c in sel)


def pilot_cameras(ctx: "m.Context | None" = None) -> list[dict]:
    """The pilot population in canonical rec_id order."""
    ctx = ctx or m.Context("sdg")
    probe = set(probe_cameras())
    return [c for c in ctx.validation_cameras() if c["rec_id"] not in probe]


def viewpoint(camera: str) -> str:
    if camera.startswith("ceiling_"):
        return "ceiling"
    if camera.startswith("eye_"):
        return "eye_level"
    raise ValueError(camera)


def write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)
