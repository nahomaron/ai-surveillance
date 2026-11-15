"""V-01 inputs for a held recording: S0 index entry, verified S1 tables, simulator truth through the T-18 driver's
annotation readers (`research/datasets/part3/t17_oracle.py`: `Annotations`, `sdg_frames`, `smartspaces_frames`, unchanged),
viewpoint class (S0 camera table) and the low_light tag (rv2 check, AR-51).

The partition guard runs before anything is read. All inputs are read-only; nothing is written here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from rq1.ids import artifact
from rq1.schema import files
from rq1.schema.errors import ContractError

from . import guard, payload, settings

Row = dict[str, Any]
DATASETS = ("sdg", "smartspaces")
S1_TABLES = ("frame", "coverage_segment", "decode_summary")
LOW_LIGHT_FILE = Path("research/datasets/part3/rv2_check_synthetic.json")
# The T16 row name of SDG contains the dataset's own words "near-miss"; pages follow the wording rules, so the row is shown by
# its dataset ID (preregistration_FROZEN.md section 1) instead.
SDG_ROW_DISPLAY = "SDG-Warehouse, nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes (synthetic_rendered)"


def _driver(root: Path):
    path = root / "research" / "datasets" / "part3" / "t17_oracle.py"
    spec = importlib.util.spec_from_file_location("rq1_viewer_t17_oracle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Source:
    """Read-only access to the held data under `root` (the repository; data in its git-ignored `data/` and `out/`)."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.split, self.split_artifact_id = guard.load_frozen_split(self.root)
        self.entries: dict[str, tuple[str, Row]] = {}
        self.cameras: dict[str, Row] = {}
        for ds in DATASETS:
            for e in json.loads((self.root / "out" / f"s0_{ds}" / "index.json").read_text(encoding="utf-8")):
                self.entries[e["rec_id"]] = (ds, e)
            counts = json.loads((self.root / "research" / "datasets" / "part3" / f"t17_counts_{ds}.json").read_text(encoding="utf-8"))
            self.cameras.update({c["rec_id"]: c for c in counts["cameras"]})
        checks = json.loads((self.root / LOW_LIGHT_FILE).read_text(encoding="utf-8"))["recordings"]
        self.low_light = {r["recording"]: ("yes" if "low_light" in r["condition_tags"] else "no") for r in checks}
        self.prereg_sha256 = hashlib.sha256((self.root / settings.PREREGISTRATION_PATH).read_bytes()).hexdigest()
        self._drv = None
        self._ann = None

    def validation_recordings(self) -> list[str]:
        """Validation-partition recordings held with an S1 artifact, sorted by (dataset, run, camera)."""
        parts = guard.partitions(self.split)
        out = [r for r, p in parts.items() if p == "validation" and r in self.entries and "s1" in self.cameras.get(r, {})]
        return sorted(out, key=lambda r: (self.entries[r][0], self.entries[r][1]["run"], self.entries[r][1]["camera"]))

    @lru_cache(maxsize=4)
    def _camera_table(self, s0: str, ds: str) -> dict[str, Row]:
        rows = files.read_table(self.root / "out" / f"s0_{ds}" / s0 / "camera.parquet", "camera", artifact.SCHEMA_VERSION)
        return {r["cam_id"]: r for r in rows}

    def s1(self, recording_id: str) -> dict[str, list[Row]]:
        ds, _ = self.entries[recording_id]
        cam = self.cameras.get(recording_id, {})
        if "s1" not in cam:
            raise ContractError("ERR-SPEC", f"{recording_id}: no S1 artifact held")
        directory = self.root / "out" / f"t17_{ds}" / cam["s1"]
        if artifact.verify(directory) != cam["s1"]:
            raise ContractError("ERR-SPEC", f"{recording_id}: S1 artifact {cam['s1']} does not verify")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        guard.check_decode_config(manifest["spec"]["config_ids"])
        return {t: files.read_table(directory / f"{t}.parquet", t, artifact.SCHEMA_VERSION) for t in S1_TABLES}

    def build(self, recording_id: str, code_commit: str) -> Row:
        partition = guard.require_validation(self.split, recording_id)  # before any data is read
        if recording_id not in self.entries:
            raise ContractError("ERR-SPEC", f"{recording_id}: not in the held S0 indexes")
        ds, entry = self.entries[recording_id]
        s1 = self.s1(recording_id)
        if self._drv is None:
            self._drv = _driver(self.root)
            self._ann = self._drv.Annotations(str(self.root / "data"))
        notes: Row = {"truth_defects": [], "unchecked_boxes": 0}
        reader = self._drv.sdg_frames if ds == "sdg" else self._drv.smartspaces_frames
        got = reader(entry, self._ann, len(s1["frame"]), notes)
        if got is None:
            raise ContractError("ERR-SPEC", f"{recording_id}: no usable simulator truth (T17.4) or truth refused (T17.5)")
        frames, classes = got
        camera = self._camera_table(entry["s0"], ds).get(entry["camera_id"], {})
        row = SDG_ROW_DISPLAY if ds == "sdg" else f"SmartSpaces MTMC_Tracking_2026 {entry['run']} (synthetic_rendered)"
        header = {"dataset_row": row, "run": entry["run"], "camera": entry["camera"], "recording_id": recording_id,
                  "viewpoint_class": camera.get("viewpoint_class", "not recorded"), "low_light": self.low_light.get(entry["uri"], "not recorded"),
                  "code_commit": code_commit, "contract": settings.CONTRACT, "preregistration_sha256": self.prereg_sha256,
                  "split_artifact_id": self.split_artifact_id, "partition": partition}
        return payload.build(header, s1, frames, classes, entry["calibration"], settings.FORK_PRIOR[ds])

    def file_name(self, recording_id: str) -> str:
        ds, e = self.entries[recording_id]
        stem = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in f"{ds}__{e['run']}__{e['camera']}")
        return stem + ".html"
