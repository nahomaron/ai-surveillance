"""D-63 STEP 3: the v2 reference-window lock (AR-71 item 11, accepted under D-63 ruling 1; representation AR-72).

For every window of V0 `m1a-sdg-test` (art_hfchmhd3zbgjl24gnqaxifaoo3): annotation_status = locked, locked_utc = LOCKED_UTC
(the event time of the lock, taken once; an event column outside the payload hash, AR-7), lock_sha256 = the SHA-256 of the
JCS form of the window's natural key and bounds, the reference-set label, the camera's v2 reference S5 (ID and payload hash)
and the reference entries overlapping [t_start, t_guard_end) (`readiness_v2.window_lock_hash`).

The lock is a new V0-stage artifact that references V0 (and the 471 v2 test reference S5 artifacts) as inputs. V0 is not
rewritten. The lock artifact holds a copy of V0's sampling_plan row (the same-artifact key of reference_window.plan_nk) and the
471 locked windows. It is built twice, independently, and the two must be identical.

  PYTHONPATH=src .venv/bin/python research/preregistration/lock_v2.py
      -> out/prereg/<lock artifact>/, docs/preregistration/window_lock_v2.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readiness_v2 as rd  # noqa: E402

from rq1.schema import registry  # noqa: E402
from rq1.schema.errors import ContractError  # noqa: E402

ROOT = rd.ROOT
CONTRACT = "E-1.2.26"
LOCKED_UTC = datetime(2026, 11, 26, 15, 47, 13, tzinfo=timezone.utc)  # event time of the lock, taken once (D-63 STEP 3)
RECORD = ROOT / "docs/preregistration/window_lock_v2.json"

lock_hash = rd.window_lock_hash


def strip_derived(table: str, row: dict) -> dict:
    """Drop the step-6 derived columns (own ID; *_id beside *_nk; *_ids beside *_nks) so the row can be rebuilt."""
    spec = registry.TABLES[table]
    drop = {f"{spec.prefix}_id"} if spec.prefix else set()
    for f in spec.fields:
        if f.name.endswith("_nk") and f.type.kind == "nk":
            drop |= {f"{f.name[:-3]}_id", f"{f.name[:-3]}_id_null_reason"} if f.nullable else {f"{f.name[:-3]}_id"}
        elif f.name.endswith("_nks") and f.type.kind == "list" and f.type.item.kind == "nk":
            drop.add(f"{f.name[:-4]}_ids")
    return {k: v for k, v in row.items() if k not in drop}


def locked_window(window: dict, sha256: str, locked_utc: datetime) -> dict:
    """The window with its three lock fields set; every other field as stored in V0. Only a planned window is locked."""
    if window["annotation_status"] != "planned":
        raise ContractError("ERR-SPEC", f"window {window['camera_group_id']}/{window['window_index']} is {window['annotation_status']}, not planned")
    return {**window, "annotation_status": "locked", "locked_utc": locked_utc, "locked_utc_null_reason": None,
            "lock_sha256": sha256, "lock_sha256_null_reason": None}


def build_once(commit: str, env: str):
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


def _file_hashes(directory: Path) -> dict:
    return {i["path"]: i["file_sha256"] for i in json.loads((directory / "manifest.json").read_text())["files"]}


def main():  # pragma: no cover - reads stored artifacts
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


if __name__ == "__main__":
    main()
