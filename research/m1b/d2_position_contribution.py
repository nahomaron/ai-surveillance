"""D-53 step 2 (D2): does forklift position drive the oracle-box loss? Diagnostic, tuning subset, not a reported result.
These runs never enter a report table beside A, B, C or C'.

  PYTHONPATH=src .venv/bin/python research/m1b/d2_position_contribution.py run [workers] [rec ...]  -> out/m1b/v2diag/
  PYTHONPATH=src .venv/bin/python research/m1b/d2_position_contribution.py aggregate              -> research/m1b/d2_position_contribution.json

Diagnostic adapter (no S4 code change): the unchanged `SubstrateBuilder` takes simulator positions per (track, frame) and
uses the calibration (`full_camera`) for every track-frame without one (builder `_object_states`). Runs, each S3 -> S4 ->
S5 BL-6 under the frozen v1 base values (`m1a_common.S4_BASE`, `S5_BASE`):
  B-tune   column B unchanged: no simulator position supplied (= T-21 `full_camera` S4; its payload hash is checked
           against the stored column B S4)
  B-sim-F  forklift positions and covariances from the simulator (the ORACLE-S3 simulator position records); persons
           `full_camera`
  B-sim-P  person positions from the simulator; forklifts `full_camera`
Only position and covariance are substituted: the simulator yaw carried by the position record is removed, so the
forklift heading is derived exactly as in column B (yaw is not part of D2's question).
S3: the ORACLE-S3 is rebuilt with the stored T-21 unit's provenance and must have the stored artifact ID (= column B's S3).
Evaluation: N4 against the stored T-21 BL-6 references, label group G1, A5.2 oracle association (as column B of the pilot,
`evaluate_pilot.evaluate_camera`); EV-M1 / EV-M2 by summed counts (`event_metrics.headline`), overall and by viewpoint.
Column A: the stored T-21 `base` unit (simulator positions for both), evaluated the same way on the same cameras.
Execution records: `execution.json` beside every artifact (`write_artifact`), appended to out/m1b/v2diag/register.jsonl,
plus a per-camera record out/m1b/v2diag/cam/<rec>.json (commit, environment digest, seconds, artifact IDs).
"""
from __future__ import annotations

import json
import os
import resource
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
OUT = __import__("pathlib").Path(os.environ.get("V2DIAG_OUT", str(ROOT / "out/m1b/v2diag")))  # V2DIAG_OUT: run-time estimate only
STATUS = "diagnostic, tuning subset, not a reported result"
RUNS = {"B-tune": None, "B-sim-F": "forklift", "B-sim-P": "person"}
BL = "BL-6"
CONTRACT = "E-1.2.24"


def substitute(positions: dict, track_class: dict, cls: str | None) -> dict:
    """Simulator position records of the tracks of class `cls` only, without yaw. positions: (local_id, frame) -> record;
    track_class: local_id -> class."""
    if cls is None:
        return {}
    return {k: {"xy": list(v["xy"]), "cov": list(v["cov"])} for k, v in positions.items() if track_class[k[0]] == cls}


def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def _save(art, origin) -> str:
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    return art.artifact_id


def run_camera(args):  # pragma: no cover - driver
    rec, prov = args
    import run_pilot as rp
    from rq1.ids import core
    from rq1.events import s5
    from rq1.substrate import builder
    rec_path = OUT / "cam" / f"{rec}.json"
    if rec_path.exists():
        return rec, "skipped", {}
    ctx = m.Context("sdg")
    unit = json.loads((ROOT / "out/m1a/run1/sdg" / rec / "base.json").read_text())
    fc = json.loads((ROOT / "out/m1a/run1/sdg" / rec / "full_camera.json").read_text())
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    t0 = time.time()
    data = m.load(ctx, rec)
    s3, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], (unit["code_commit"], unit["environment_digest"]))
    if s3.artifact_id != unit["s3"]:
        raise RuntimeError(f"{rec}: rebuilt ORACLE-S3 {s3.artifact_id} != stored {unit['s3']}")
    if data.calibration is None:
        raise RuntimeError(f"{rec}: no calibration")
    track_class = {t["track_local_id"]: t["class"] for t in s3.tables["track"]}
    record, cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    stored_b = json.loads((ROOT / "out/m1a/run1/sdg/artifacts" / fc["s4"] / "manifest.json").read_text())
    out = {"rec_id": rec, "status": STATUS, "code_commit": prov[0], "environment_digest": prov[1], "contract": CONTRACT,
           "preregistration": "docs/preregistration_FROZEN.md, version 1 (base values)", "s3": s3.artifact_id, "runs": {},
           "seconds": {"load_s3": round(time.time() - t0, 1)}}
    for name, cls in RUNS.items():
        t1 = time.time()
        pos = substitute(positions, track_class, cls)
        gcf = core.make_id("gcf", {"geometry": "full_camera"} if cls is None else
                           {"geometry": "full_camera", "diagnostic_substitution": f"simulator positions and covariances: {cls}", "decision": "D-53 step 2"})
        s4 = builder.SubstrateBuilder().build(data.s1, s3, pos, data.calibration, cfg,
                                              _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3.artifact_id,)))
        c5 = m.s5_config(ctx, BL, m.S4_BASE, m.S5_BASE)
        s5a = s5.build(data.s1, s4, c5, _spec("S5", prov, (s5.config_id(c5),), (s4.artifact_id,)))
        out["runs"][name] = {"substituted_class": cls, "substituted_object_frames": len(pos), "s4": _save(s4, origin), "s5": {BL: _save(s5a, origin)},
                             "s4_payload_sha256": s4.payload_sha256}
        out["seconds"][name] = round(time.time() - t1, 1)
    out["b_tune_payload_equals_stored_B"] = out["runs"]["B-tune"]["s4_payload_sha256"] == stored_b["payload_sha256"]
    out["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1)  # macOS: bytes
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(rec_path, out)
    return rec, "done", out["seconds"]


# ------------------------------------------------------------------------------------------------------------- evaluation

def _load(art_id, root):
    from rq1.schema import files
    d = root / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}


def evaluate_camera(rec):  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    from rq1.evaluation import association as assoc
    ev = ep.ev
    path = OUT / "eval" / f"{rec}.json"
    if path.exists():
        return rec, "skipped"
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    rec_ = json.loads((OUT / "cam" / f"{rec}.json").read_text())
    usable = sum(cam.support().values())
    refs, groups = ev.references(cam)
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    rows, _, _ = ev.association(s3o, trk_key)
    sup = {f: cam.support().get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    summ, _ = assoc.summarize(rows, sup)
    stored = ROOT / "out/m1a/run1/sdg/artifacts"
    cols = {"A (stored)": (base["s4"], base["s5"][BL], stored), "B (stored)": (fc["s4"], fc["s5"][BL], stored)}
    for name, r in rec_["runs"].items():
        cols[name] = (r["s4"], r["s5"][BL], OUT / "artifacts")
    out = {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "stratum": cam.window["stratum_id"], "ev": {}}
    for name, (a4, a5, root) in cols.items():
        events = ev.system_events(_load(a4, root), _load(a5, root), rows, summ)
        out["ev"][name] = ev.ev_counts(refs, groups, events, usable)["counts"]
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, out)
    return rec, "done"


def summarize(cams: list[dict]) -> dict:
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation.event_metrics import WindowCounts
    out = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        out[view] = {"cameras": len(sub)}
        for col in sorted(cams[0]["ev"]):
            wc = [WindowCounts(**c["ev"][col]) for c in sub]
            h = em.headline(wc)
            t = {k: sum(getattr(x, k) for x in wc) for k in ("a", "m", "s", "m_s")}
            out[view][col] = {"EV-M1": h["EV-M1"], "EV-M2": h["EV-M2"], "assessable_references": t["a"], "matched_references": t["m"],
                              "missed_references": t["a"] - t["m"], "system_events": t["s"], "matched_events": t["m_s"],
                              "unmatched_events": t["s"] - t["m_s"]}
    return out


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "eval" / f"{r}.json").read_text()) for r in recs]
    runs = [json.loads((OUT / "cam" / f"{r}.json").read_text()) for r in recs]
    return {"status": STATUS, "decision": "D-53 step 2", "contract": "E-1.2.24 (no change)", "cameras": len(cams),
            "baseline": BL, "label_group": "G1", "matching": "N4 (frozen v1 S8 values), stored T-21 BL-6 references; summed counts as the pilot report",
            "runs": {"B-tune": "column B unchanged (oracle boxes, full_camera), re-run through the diagnostic adapter",
                     "B-sim-F": "column B with forklift positions and covariances from the simulator; persons full_camera",
                     "B-sim-P": "column B with person positions and covariances from the simulator; forklifts full_camera",
                     "A (stored)": "column A (simulator positions for both), stored T-21 base unit, same cameras",
                     "B (stored)": "column B, stored T-21 full_camera unit, same cameras (cross-check of B-tune)"},
            "yaw": "not substituted: the simulator yaw is removed from the substituted position records",
            "checks": {"b_tune_s4_payload_equals_stored_B": sum(r["b_tune_payload_equals_stored_B"] for r in runs),
                       "s3_rebuilt_equals_stored": len(runs)},
            "code_commit": sorted({r["code_commit"] for r in runs}),
            "ev": summarize(cams)}


def main():  # pragma: no cover
    import run_pilot as rp
    import v2_sets
    what = sys.argv[1]
    if what == "aggregate":
        p = ROOT / "research/m1b/d2_position_contribution.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tuning = v2_sets.tuning()
    recs = sys.argv[3:] or tuning
    assert set(recs) <= set(tuning), "tuning subset only (D-53)"
    if what == "run":
        prov = rp.provenance()
        jobs, fn = [(r, prov) for r in recs], run_camera
    elif what == "evaluate":
        jobs, fn = recs, evaluate_camera
    else:
        raise SystemExit(what)
    print(f"{what}: {len(jobs)} cameras, workers {workers}", flush=True)
    t0 = time.time()
    it = map(fn, jobs) if workers == 1 else Pool(workers, maxtasksperchild=1).imap_unordered(fn, jobs)
    for n, res in enumerate(it, 1):
        print(n, *res, f"elapsed {round(time.time() - t0)} s", flush=True)


if __name__ == "__main__":
    main()
