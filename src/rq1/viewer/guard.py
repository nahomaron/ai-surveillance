"""V-01 guards: validation partition of the frozen X0b split only; S1 read only when its decode values are the frozen ones.

- No frozen split (no freeze record, or its X0b artifact missing, incomplete or not reconstructing) -> ERR-SPEC, for every
  recording.
- A recording whose leakage group is not in the validation partition, or that is not in the split at all (for example
  SmartSpaces Warehouse_001, outside X0b v1) -> ERR-SPEC. D-37 reserves the test partition: nothing is built for it.
- S1 reuse (Owner decision, V-01 session of 14 Nov 2026): the S1 artifacts held were built before the freeze under a
  decode record labelled as test parameters, with the same numbers as the frozen section 4.1 values. An S1 artifact is read
  only when its decode configuration ID rebuilds from a record carrying exactly the frozen numbers (FROZEN_DECODE). The
  label never reaches a page.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rq1.decode import quality
from rq1.ids import artifact, core
from rq1.schema import files
from rq1.schema.errors import ContractError
from rq1.splits.builder import recording_partitions

from . import settings

Row = dict[str, Any]
FREEZE_RECORD = Path("docs") / "preregistration" / "freeze_record.json"
SPLIT_DIR = Path("out") / "prereg"
_HELD_DECODE_LABEL = "TEST" + "-ONLY"  # label of the decode record of the S1 artifacts held (pre-freeze); numbers = section 4.1


def load_frozen_split(root: str | Path) -> tuple[Row, str]:
    """The frozen X0b split_manifest row named by the freeze record, after the artifact reconstruction check."""
    root = Path(root)
    record_path = root / FREEZE_RECORD
    if not record_path.exists():
        raise ContractError("ERR-SPEC", "no frozen split: freeze record not found; the viewer shows nothing without a frozen X0b split")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    art = (record.get("split") or {}).get("artifact_id")
    directory = root / SPLIT_DIR / str(art)
    if not art or not (directory / "manifest.json").exists():
        raise ContractError("ERR-SPEC", f"no frozen split: X0b artifact {art} not found under {SPLIT_DIR}")
    try:
        rebuilt = artifact.verify(directory)
    except ContractError as e:
        raise ContractError("ERR-SPEC", f"no frozen split: X0b artifact {art} does not verify ({e})") from e
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if rebuilt != art or manifest["spec"]["stage"] != "X0b":
        raise ContractError("ERR-SPEC", f"no frozen split: {art} is not the frozen X0b artifact")
    (split,) = files.read_table(directory / "split_manifest.parquet", "split_manifest", artifact.SCHEMA_VERSION)
    if split.get("frozen_utc") is None or split.get("spm_id") != record["split"].get("spm_id"):
        raise ContractError("ERR-SPEC", f"no frozen split: {art} carries no freeze time or another split_manifest")
    return split, art


def partitions(split: Row) -> dict[str, str]:
    return recording_partitions(split)


def require_validation(split: Row, recording_id: str) -> str:
    partition = partitions(split).get(recording_id)
    if partition != "validation":
        where = "not in the frozen split" if partition is None else f"in the {partition} partition"
        raise ContractError("ERR-SPEC", f"V-01 shows validation-partition recordings only; {recording_id} is {where} (D-37)")
    return partition


def decode_record(label: str) -> Row:
    """The S1 decode record with the frozen section 4.1 values (same fields as the T-18 driver's record)."""
    v = settings.FROZEN_DECODE
    if v["rules_version"] != quality.RV2:
        raise ContractError("ERR-SPEC", "frozen rules version is not the implemented rv2")
    return {"k_sup": v["k_sup"], "f_untimed": v["f_untimed"], "f_sub": v["f_sub"], "rules_version": quality.RV2, "delta_nom_declarations": [],
            "final_frame_support": "delta_nom", "version_label": label, "version_label_null_reason": None}


def check_decode_config(config_ids: list[str]) -> str:
    """ERR-SPEC unless the S1 artifact's decode configuration is a record with the frozen numbers."""
    accepted = {core.make_id("dcf", decode_record(label)) for label in (_HELD_DECODE_LABEL,)}
    found = [c for c in config_ids if c.startswith("dcf_")]
    if len(found) != 1 or found[0] not in accepted:
        raise ContractError("ERR-SPEC", f"S1 decode configuration {found} does not carry the frozen section 4.1 values")
    return found[0]
