"""T23.11 (a), (b): the demo draw, and the SDG episode source it reads (stored S5 artifacts only; no stage is run).

Source (D-48 step 4): the BL-6 S5 artifacts of the D-45 detector-path pilot (column C, `out/m1b/pilot/cam/*/pipeline.json`)
when they exist, otherwise the T-21 BL-6 oracle artifacts (`out/m1a/run1/sdg/*/base.json`). A pilot run's cameras that the
pilot did not process (the T-22 probe cameras) belong to the area but have no source output; they are listed as such
(CR-030 item 6).

Representation (AR-63 item 11): runs are grouped by D-35 family (first path element of session.lineage.generation_batch);
one numpy PCG64 generator seeded with the demo seed draws 3 runs per family without replacement from the run names sorted,
families in sorted order, then one calendar offset per run (whole seconds in [0, 28 days - 1 hour)), in the same order.
The simulated calendar starts on Monday 2026-11-02 00:00 UTC. Each run's cameras are placed on the calendar by the run's
offset, so episodes of one run share one time axis (T23.11 a).

E-1.2.23 (D-49): T23.21 (c) groups across cameras only on a declared axis; the manifest names the evidence
(`timebase_evidence_ref`, tag `workflow_timebase_declared`, not a clock_alignment) and a run without it groups per camera.
T23.26: the manifest copies the alert source's reported figures (`source_quality`). T23.23 (a): each camera's coverage is
processed by its S5 artifact of the source configuration. T23.24 (b): each member episode carries the provenance of its
clearance at the minimum-clearance pair-frame (sigma, sigma_status, q_state, q_reasons; S4 artifact; calibration tier).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from rq1.review import protocol as P
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.workflow import rules as R

CALENDAR_START = datetime(2026, 11, 2, tzinfo=timezone.utc)
CALENDAR_DAYS = 28
RUNS_PER_FAMILY = 3
EST_NAMES = ("Simulated warehouse North", "Simulated warehouse South", "Simulated warehouse East", "Simulated warehouse West")
# T23.21 (c), quoted: the evidence of one simulator clock per SDG run [V].
SDG_TIMEBASE_REF = "qualification.md §2.7: one simulator clock per SDG run (dataset card); equal frame counts"
# T23.26: the figures of the D-45 pilot column C (reports/M1b_pilot_report.md on m0-implementation, ec63113), BL-6.
PILOT_C_QUALITY = {"config": "BL-6", "path": "detector_path_pilot_d45", "cm03": 0.12, "ev_m1": 0.11, "ev_m2": 0.22,
                   "report_ref": "reports/M1b_pilot_report.md (m0-implementation ec63113), BL-6 column C"}


def _spec(message: str) -> ContractError:
    return ContractError("ERR-SPEC", message)


class SdgDemoSource:
    def __init__(self, root: str | Path, configuration: str = "BL-6") -> None:
        self.root = Path(root)
        self.configuration = configuration
        pilot = sorted((self.root / "out/m1b/pilot/cam").glob("rec_*/pipeline.json"))
        self.timebase_evidence_ref = SDG_TIMEBASE_REF
        if pilot:
            self.path, self.art_root = "detector_path_pilot_d45", self.root / "out/m1b/pilot/artifacts"
            self.source_root = "out/m1b/pilot"
            self.per_rec = {json.loads(p.read_text())["rec_id"]: json.loads(p.read_text()) for p in pilot}
            self.source_quality = dict(PILOT_C_QUALITY) if configuration == "BL-6" else {"config": configuration, "path": self.path}
        else:
            self.path, self.art_root = "t21_oracle", self.root / "out/m1a/run1/sdg/artifacts"
            self.source_root = "out/m1a/run1/sdg"
            self.source_quality = {"config": configuration, "path": self.path}  # no figure recorded: "not reported"
            self.per_rec = {}
            for p in sorted((self.root / "out/m1a/run1/sdg").glob("rec_*/base.json")):
                b = json.loads(p.read_text())
                self.per_rec[b["rec_id"]] = b
        freeze = json.loads((self.root / "docs/preregistration/freeze_record.json").read_text())
        self.validation_runs = sorted(freeze["split"]["sdg_validation_runs"])
        self.index = {e["rec_id"]: e for e in json.loads((self.root / "out/s0_sdg/index.json").read_text())}
        counts = json.loads((self.root / "research/datasets/part3/t17_counts_sdg.json").read_text())
        self.s1 = {c["rec_id"]: c["s1"] for c in counts["cameras"]}
        self._family = self._families()

    def _families(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for s0 in sorted({e["s0"] for e in self.index.values() if e["dataset"] == "sdg"}):
            for row in pq.read_table(self.root / "out/s0_sdg" / s0 / "session.parquet", columns=["lineage"]).to_pylist():
                lin = row["lineage"]
                out[lin["ext_run_id"]] = lin["generation_batch"].split("/")[0]
        return out

    def runs_by_family(self) -> dict[str, list[str]]:
        fam: dict[str, list[str]] = {}
        for run in self.validation_runs:
            fam.setdefault(self._family[run], []).append(run)
        return {k: sorted(v) for k, v in sorted(fam.items())}

    def recordings(self, run: str) -> list[str]:
        return sorted(r for r, e in self.index.items() if e["dataset"] == "sdg" and e["run"] == run)

    def camera(self, rec: str) -> dict[str, Any]:
        """One camera of a run: its S1 coverage (local time) and, when it has a source S5 artifact, its episodes."""
        entry = self.index[rec]
        meta = self.per_rec.get(rec)
        s1 = self.root / "out/t17_sdg" / (meta["s1"] if meta and "s1" in meta else self.s1[rec])
        segments = [{"t_start_tl_s": s["t_start_tl_s"], "t_end_tl_s": s["t_end_tl_s"], "coverage_state": s["coverage_state"]}
                    for s in pq.read_table(s1 / "coverage_segment.parquet").to_pylist()]
        out = {"rec_id": rec, "camera_id": entry["camera_id"], "s1": s1.name, "segments": segments, "episodes": [],
               "s5": None, "has_source_output": meta is not None}
        if meta is None:
            return out
        art = self.art_root / meta["s5"][self.configuration]
        manifest = json.loads((art / "manifest.json").read_text())
        config_id = manifest["spec"]["config_ids"][0]
        out["s5"] = art.name
        methods = {r["geometry_method"] for r in pq.read_table(self.art_root / meta["s4"] / "object_state.parquet", columns=["geometry_method"]).to_pylist()}
        method = methods.pop() if len(methods) == 1 else None
        tier = (entry.get("calibration") or {}).get("calibration_tier")
        pows = {r["pow_id"]: json.dumps([r["person_track_id"], r["forklift_track_id"], r["start_frame"]], separators=(",", ":"))
                for r in pq.read_table(self.art_root / meta["s4"] / "pow.parquet", columns=["pow_id", "person_track_id", "forklift_track_id", "start_frame"]).to_pylist()}
        pair = {(r["pow_nk"], r["frame_index"]): r for r in pq.read_table(
            self.art_root / meta["s4"] / "pair_series.parquet",
            columns=["pow_nk", "frame_index", "clearance_sigma_m", "sigma_status", "q_state", "q_reasons"]).to_pylist()}
        times = {f["frame_index"]: f["t_tl_s"] for f in pq.read_table(s1 / "frame.parquet", columns=["frame_index", "t_tl_s"]).to_pylist()}
        summary = pq.read_table(s1 / "decode_summary.parquet").to_pylist()[0]
        rec_start, rec_end = summary["extent_start_tl_s"], summary["extent_end_tl_s"]
        for row in pq.read_table(art / "episode.parquet").to_pylist():
            iplus_end = times.get(row["attr_end_frame_excl"], rec_end)
            start, end = P.clip_window(row["t_start_tl_s"], iplus_end, rec_start, rec_end, P.PARAMS["c_pad_s"])
            out["episodes"].append({
                "ep_id": row["ep_id"], "recording_id": rec, "camera_id": row["camera_id"], "config_id": config_id,
                "g2_label": P.g2_from_flags(lbl_NM=row["lbl_NM"], lbl_UD=row["lbl_UD"], lbl_CT=row["lbl_CT"]),
                "summary_label": row["summary_label"], "local_t_start_s": row["t_start_tl_s"], "local_t_end_s": row["t_end_tl_s"],
                "minclr_m": row["minclr_m"], "minclr_m_null_reason": row["minclr_m_null_reason"], "geometry_method": method,
                "E_ep": row["E_ep"], "video": str((self.root / "data" / entry["uri"]).resolve()),
                **self._provenance(pair.get((pows.get(row["pow_id"]), row["minclr_frame"])), tier, meta["s4"]),
                "fps": 1.0 / summary["delta_nom_s"], "clip_start_s": start, "clip_end_s": end,
                "width": summary["width_px"], "height": summary["height_px"], "synthetic": True, "s5_artifact_id": art.name})
        return out


    @staticmethod
    def _provenance(ps: dict[str, Any] | None, tier: str | None, s4: str) -> dict[str, Any]:
        """T23.24 (b): the evidence at the episode's minimum-clearance pair-frame (None where the row is absent)."""
        ps = ps or {}
        return {"calibration_tier": tier, "clearance_sigma_m": ps.get("clearance_sigma_m"), "sigma_status": ps.get("sigma_status"),
                "q_state": ps.get("q_state"), "q_reasons": ps.get("q_reasons") or [], "prov_class": None, "s4_artifact_id": s4}


def draw_demo(store: Any, source: Any, seed: int, flag_minimums: dict[str, int] | None = None) -> dict[str, Any]:
    """T23.11 (a), (b). Refused (ERR-SPEC, nothing written) if the store already has a demo manifest, or if any recording
    of a drawn run already has a target in a T22 batch of this store."""
    if type(seed) is not int or seed < 0:
        raise _spec("the demo seed is a non-negative integer")
    if store.demo_manifest() is not None:
        raise _spec("this store already has a demo manifest (immutable, T23.11 a)")
    rng = np.random.Generator(np.random.PCG64(seed))
    families = source.runs_by_family()
    drawn: list[tuple[str, str]] = []
    for fam, runs in families.items():
        if len(runs) < RUNS_PER_FAMILY:
            raise _spec(f"family {fam} has fewer than {RUNS_PER_FAMILY} validation runs")
        drawn += [(fam, runs[i]) for i in sorted(rng.choice(len(runs), size=RUNS_PER_FAMILY, replace=False).tolist())]
    offsets = [float(x) for x in rng.integers(0, CALENDAR_DAYS * 86400 - 3600, size=len(drawn)).tolist()]
    recs = {run: source.recordings(run) for _, run in drawn}
    clash = sorted(set(r for v in recs.values() for r in v) & store.batch_recordings())
    if clash:
        raise _spec(f"T23.25 (b), T23.11 (b): {len(clash)} recording(s) of the drawn demo runs already have a target in a batch of a "
                    "registered store; demo draw refused")
    cameras = {run: [source.camera(r) for r in recs[run]] for run in recs}  # read everything before the first write
    ref = getattr(source, "timebase_evidence_ref", None)  # T23.21 (c): without it, every camera groups on its own
    quality = getattr(source, "source_quality", None)
    with store.lock:
        if flag_minimums:
            store.set_config({**{k: store.config()[k] for k in R.PARAMS}, **flag_minimums})
        elif store.config()["store_version"] == 0:
            store.set_config(dict(R.PARAMS))
        ests, areas, runs_out = {}, [], []
        for k, fam in enumerate(families):
            ests[fam] = store.add_establishment(EST_NAMES[k % len(EST_NAMES)], demo=True)
        for n, ((fam, run), offset) in enumerate(zip(drawn, offsets), 1):
            cams = cameras[run]
            area = store.add_area(ests[fam]["est_id"], f"Area {n} (simulated run {run.split('_run_')[0][:6]})", [c["camera_id"] for c in cams])
            areas.append({"area_id": area["area_id"], "est_id": area["est_id"], "name": area["name"], "run": run})
            episodes = []
            for c in cams:
                segs = [{"start_utc": R.utc(CALENDAR_START + timedelta(seconds=offset + s["t_start_tl_s"])),
                         "end_utc": R.utc(CALENDAR_START + timedelta(seconds=offset + s["t_end_tl_s"])),
                         "coverage_state": s["coverage_state"]} for s in c["segments"]]
                processed = ([{"start_utc": segs[0]["start_utc"], "end_utc": segs[-1]["end_utc"], "s5_artifact_id": c["s5"]}]
                             if c["has_source_output"] and c["s5"] and segs else [])
                store.set_monitoring(c["camera_id"], segs, bool(processed), c["s1"], processed=processed)
                for e in c["episodes"]:
                    tl = ({"timeline_id": f"demo-calendar:{run}", "timeline_kind": "workflow_timebase_declared", "timebase_evidence_ref": ref}
                          if ref else {"timeline_id": f"recording-local:{e['recording_id']}", "timeline_kind": "recording_local"})
                    episodes.append({**e, "t_start_tl_s": offset + e["local_t_start_s"], "t_end_tl_s": offset + e["local_t_end_s"], **tl})
            store.intake(area["area_id"], episodes, CALENDAR_START)
            runs_out.append({"run": run, "family": fam, "est_id": area["est_id"], "area_id": area["area_id"],
                             "camera_rec_ids": [c["rec_id"] for c in cams], "calendar_offset_s": offset,
                             "s5_artifact_ids": sorted(c["s5"] for c in cams if c["s5"])})
        manifest = {"demo_id": "dmo_" + store_uuid(), "seed": seed, "source_configuration": source.configuration,
                    "source_path": source.path, "source_root": source.source_root, "runs": runs_out,
                    "est_records": [{"est_id": e["est_id"], "name": e["name"], "family": f} for f, e in ests.items()],
                    "areas": areas, "calendar_start_utc": R.utc(CALENDAR_START), "calendar_days": CALENDAR_DAYS,
                    "created_utc": R.utc(store.clock()), "timebase_evidence_ref": ref, "timebase_evidence_ref_null_reason": None if ref else "not_supplied",
                    "timebase_tag": "workflow_timebase_declared" if ref else None, "timebase_tag_null_reason": None if ref else "not_applicable",
                    "source_quality": _quality(quality), "source_quality_null_reason": None if quality else "not_supplied"}
        store._check("demo_manifest", manifest)
        (store.root / "demo_manifest.json").write_bytes(canonical_json(manifest))
        return manifest


def _quality(q: dict[str, Any] | None) -> dict[str, Any] | None:
    if not q:
        return None
    out = {"config": q["config"], "path": q["path"]}
    for k in ("cm03", "ev_m1", "ev_m2", "report_ref"):
        out[k] = q.get(k)
        out[f"{k}_null_reason"] = None if q.get(k) is not None else "not_supplied"
    return out


def store_uuid() -> str:
    import uuid
    return str(uuid.uuid7())
