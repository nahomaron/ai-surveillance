"""Sampling frames for V-02 reference batches (Appendix T T22.6 a, T22.11).

`SdgFrame` reads the S5 artifacts that the T-21 SDG validation run already wrote (out/m1a/run1/sdg): the episodes of
one named configuration (default BL-6) in the validation partition of the frozen X0b split. It reads files only; it runs
no stage. `FixtureFrame` serves tests and the report screenshots.

`describe()` returns the system-side description of one target: what the server needs to play the clip (T22.4) and to
write the status entry (T22.8). It is stored with the batch and is never sent to a reviewer page.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from rq1.review import protocol as P
from rq1.schema.errors import ContractError

# T22.4: a neutral outline per object of the target pair, one fixed colour per object for the whole clip.
OUTLINE_COLOURS = {"person": "#ffffff", "forklift": "#8fd3ff"}


class FixtureFrame:
    """A frame given as a list of target descriptions (fixtures and screenshots only)."""

    dataset = "fixture"

    def __init__(self, targets: list[dict[str, Any]], name: str = "BL-6", config_id: str = "", partition: str = "validation") -> None:
        self.name, self.config_id, self.partition = name, config_id, partition
        self._targets = {t["target_id"]: t for t in targets}

    def episodes(self) -> list[dict[str, Any]]:
        return [{"target_id": t["target_id"], "stratum": t["stratum"], "recording_id": t["recording_id"]} for t in self._targets.values()]

    def describe(self, target_id: str) -> dict[str, Any]:
        return dict(self._targets[target_id])


class SdgFrame:
    """Episodes of one configuration in the SDG validation partition, from the T-21 run outputs (read only)."""

    dataset = "sdg"

    def __init__(self, root: str | Path, configuration: str = "BL-6", run_dir: str = "out/m1a/run1/sdg") -> None:
        self.root = Path(root)
        self.name = configuration
        self.partition = "validation"
        self.run = self.root / run_dir
        freeze = json.loads((self.root / "docs/preregistration/freeze_record.json").read_text())
        self.validation_runs = set(freeze["split"]["sdg_validation_runs"])
        self.index = {e["rec_id"]: e for e in json.loads((self.root / "out/s0_sdg/index.json").read_text())}
        counts = json.loads((self.root / "research/datasets/part3/t17_counts_sdg.json").read_text())
        self.s1 = {c["rec_id"]: c["s1"] for c in counts["cameras"]}
        self._episodes: dict[str, dict[str, Any]] = {}
        config_ids = set()
        for base_path in sorted(self.run.glob("rec_*/base.json")):
            base = json.loads(base_path.read_text())
            rec = base["rec_id"]
            entry = self.index[rec]
            if entry["dataset"] != "sdg" or entry["run"] not in self.validation_runs:
                raise ContractError("ERR-LEAKAGE", f"{rec} is not an SDG validation recording (D-37, T22.11)")
            art = self.run / "artifacts" / base["s5"][configuration]
            manifest = json.loads((art / "manifest.json").read_text())
            config_ids.update(manifest["spec"]["config_ids"])
            for row in pq.read_table(art / "episode.parquet").to_pylist():
                self._episodes[row["ep_id"]] = {"row": row, "rec": rec, "s3": base["s3"], "s4": base["s4"],
                                                "config_id": manifest["spec"]["config_ids"][0]}
        if len(config_ids) != 1:
            raise ContractError("ERR-SPEC", f"{configuration} has {len(config_ids)} rule configurations in this run")
        self.config_id = config_ids.pop()

    def episodes(self) -> list[dict[str, Any]]:
        return [{"target_id": k, "stratum": v["row"]["summary_label"], "recording_id": v["rec"]} for k, v in sorted(self._episodes.items())]

    def describe(self, target_id: str) -> dict[str, Any]:
        ep = self._episodes[target_id]
        row, rec = ep["row"], ep["rec"]
        s1 = self.root / "out/t17_sdg" / self.s1[rec]
        times = {f["frame_index"]: f["t_tl_s"] for f in pq.read_table(s1 / "frame.parquet", columns=["frame_index", "t_tl_s"]).to_pylist()}
        summary = pq.read_table(s1 / "decode_summary.parquet").to_pylist()[0]
        rec_start, rec_end = summary["extent_start_tl_s"], summary["extent_end_tl_s"]
        iplus_end = times.get(row["attr_end_frame_excl"], rec_end)  # I+ = [open, attr end); the end is the next frame's time
        start, end = P.clip_window(row["t_start_tl_s"], iplus_end, rec_start, rec_end, P.PARAMS["c_pad_s"])
        return {
            "target_type": "system_episode", "target_id": target_id, "recording_id": rec, "config_id": ep["config_id"],
            "stratum": row["summary_label"],
            "g2_label": P.g2_from_flags(lbl_NM=row["lbl_NM"], lbl_UD=row["lbl_UD"], lbl_CT=row["lbl_CT"]),
            "video": str((self.root / "data" / self.index[rec]["uri"]).resolve()),
            "clip_start_s": start, "clip_end_s": end, "fps": 1.0 / summary["delta_nom_s"],
            "width": summary["width_px"], "height": summary["height_px"],
            "outlines": self._outlines(ep, times, start, end),
        }

    def _outlines(self, ep: dict[str, Any], times: dict[int, float], start: float, end: float) -> list[dict[str, Any]]:
        """Outlines only where the clip shows more than one person or more than one forklift (T22.4)."""
        art = self.run / "artifacts"
        pow_row = next(r for r in pq.read_table(art / ep["s4"] / "pow.parquet").to_pylist() if r["pow_id"] == ep["row"]["pow_id"])
        tracks = {r["trk_id"]: r["class"] for r in pq.read_table(art / ep["s3"] / "track.parquet").to_pylist()}
        frames = {k for k, t in times.items() if start <= t < end}
        points: dict[str, dict[int, list[float]]] = {}
        for p in pq.read_table(art / ep["s3"] / "track_point.parquet", columns=["track_id", "frame_index", "bbox_xyxy_px"]).to_pylist():
            if p["frame_index"] in frames and p["bbox_xyxy_px"] is not None:
                points.setdefault(p["track_id"], {})[p["frame_index"]] = [float(v) for v in p["bbox_xyxy_px"]]
        in_clip = [tracks[t] for t in points]
        if in_clip.count("person") <= 1 and in_clip.count("forklift") <= 1:
            return []
        out = []
        for cls, trk in (("person", pow_row["person_track_id"]), ("forklift", pow_row["forklift_track_id"])):
            boxes = points.get(trk, {})
            out.append({"colour": OUTLINE_COLOURS[cls], "boxes": [[times[k], *boxes[k]] for k in sorted(boxes)]})
        return out
