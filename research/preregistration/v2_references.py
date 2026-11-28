"""D-61 STEP 5: the pre-registration v2 reference sets (T21.1-T21.3) for the tuning (116), reporting (110) and test (471)
SDG cameras, from simulator truth only, at the v2 base values (D-61 section 1.3, 1.7). Synthetic-data evaluation.

  PYTHONPATH=src .venv/bin/python research/preregistration/v2_references.py estimate            (2 cameras)
  PYTHONPATH=src .venv/bin/python research/preregistration/v2_references.py run [workers] [set ...]
        -> out/v2/references/artifacts/, out/v2/references/<set>/<rec>.json
  PYTHONPATH=src .venv/bin/python research/preregistration/v2_references.py verify [workers] [set ...]
        second independent build into out/v2/references_verify/; payload hashes and artifact IDs must be equal

Per camera: the T21.1 reference S3 (every object of the truth on every eligible frame with a pose, `m1a_common`) ->
S4 simulator_truth at the v2 values (label "preregistration-v2") -> S5 BL-6 at the v2 values with m_gap_s 1.5 and
T25.2 off (T25.2 d: no join for references) -> reference entries with A5.2 object keys and T21.3 assessability.
No system output is read or built: no S2, no tracker, no oracle S3 at g_max (D-61 hard limit: reference building from
truth is the one exception on test). Test cameras are loaded with `m1a_common.load_for_reference` only.
The v1 base references (out/m1a/run1/) and the D-61 STEP 4 diagnostic set (out/m1b/d61/reference_diag/) are not touched.
SmartSpaces references are not built: T21.1 is infeasible on scene-wide truth (D-39) and the v2 amendment promised in
D-40 item 3 does not exist (CR-039).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research/m1b"))
import v2_values as v2  # noqa: E402

m = v2.m
ROOT = v2.ROOT
OUT = Path(os.environ.get("V2REF_OUT", str(ROOT / "out/v2/references")))
LABEL = "preregistration-v2"
BL = "BL-6"
SETS = ("tuning", "reporting", "test")
EXPECTED = {"tuning": 116, "reporting": 110, "test": 471}
STATUS = "pre-registration v2 reference set (T21.1, simulator truth); synthetic-data evaluation"
REF_KEYS = ("pow_id", "start_frame", "end_frame_excl", "t_start_tl_s", "t_end_tl_s", "lbl_O", "lbl_H", "lbl_PC")


def provenance() -> tuple[str, str]:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if dirty and os.environ.get("V2REF_SMOKE") != "1":
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    commit = "uncommitted" if dirty else subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def cameras(name: str) -> list[str]:
    """The camera set, in rec_id order: tuning and reporting from `v2_camera_sets.json`; test = every SDG camera of an
    X0b test run with usable truth (T17.4, an ORACLE-S3 in the T17 counts), as the V0 plan m1a-sdg-test."""
    import v2_sets
    if name == "tuning":
        return v2_sets.tuning()
    if name == "reporting":
        return v2_sets.reporting()
    if name == "test":
        freeze = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())
        test_runs = set(freeze["split"]["sdg_test_runs"])
        counts = json.loads((ROOT / "research/datasets/part3/t17_counts_sdg.json").read_text())["cameras"]
        return sorted(c["rec_id"] for c in counts if c["run"] in test_runs and c.get("s3"))
    raise ValueError(name)


def reference_entries(s5_tables: dict, s4_tables: dict, key_by_trk: dict, visible: dict) -> list[dict]:
    """T21.2-T21.3 entries, as `run_m1a.unit_reference` (G1 labels only; assessable on eligible jointly visible frames)."""
    pows = {p["pow_id"]: p for p in s4_tables["pow"]}
    refs = []
    for e in s5_tables.get("episode", []):
        pw = pows[e["pow_id"]]
        person, fork = key_by_trk[pw["person_track_id"]], key_by_trk[pw["forklift_track_id"]]
        both = set(visible.get(person, ())) & set(visible.get(fork, ()))
        assessable = any(e["start_frame"] <= i < e["end_frame_excl"] for i in both)
        refs.append({**{k: e[k] for k in REF_KEYS}, "person_key": person, "forklift_key": fork, "assessable": assessable,
                     "status": "assessable" if assessable else "unobservable_reference"})
    return refs


def list_sha256(refs: list[dict]) -> str:
    return hashlib.sha256(json.dumps(refs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def set_sha256(rows: list[dict]) -> str:
    """Hash of a reference set: the JCS-like JSON of (rec_id, S3/S4/S5 artifact IDs and payload hashes, list hash) in rec_id order."""
    keep = [{k: r[k] for k in ("rec_id", "s3", "s4", "s5", "s3_payload_sha256", "s4_payload_sha256", "s5_payload_sha256", "references_sha256")}
            for r in sorted(rows, key=lambda r: r["rec_id"])]
    return hashlib.sha256(json.dumps(keep, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, v2.CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def build_camera(args) -> tuple[str, str, float]:  # pragma: no cover - driver
    name, rec, prov, out = args
    if name != "tuning" or rec not in cameras("tuning"):
        raise SystemExit("refused: D-66/D-67 restrict v2 reference building to tuning")
    from rq1.adapters import oracle_truth as ot
    from rq1.events import s5
    from rq1.ids import core
    from rq1.substrate import builder, oracle
    path = out / name / f"{rec}.json"
    if path.exists():
        return rec, "skipped", 0.0
    t0 = time.time()
    ctx = m.Context("sdg")
    data = m.load_for_reference(ctx, rec)
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    tracks = m.reference_tracks(data)
    truth, positions = ot.s3_truth(tracks, data.classes, data.seq)
    s3r = oracle.OracleTrackSource().tracks(rec, truth, data.s1["frame"], _spec("S3", prov, (core.make_id("orc", {"t21_reference": 1}),), ()))
    record, cfg, _, _ = v2.substrate_config(ctx, LABEL)
    gcf = core.make_id("gcf", {"geometry": "simulator_truth"})
    s4r = builder.SubstrateBuilder().build(data.s1, s3r, positions, None, cfg, _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3r.artifact_id,)))
    c5 = v2.s5_config(ctx, BL, LABEL, False)
    s5r = s5.build(data.s1, s4r, c5, _spec("S5", prov, (s5.config_id(c5),), (s4r.artifact_id,)))
    for art in (s3r, s4r, s5r):
        target = out / "artifacts" / art.artifact_id
        if not (target / "manifest.json").exists():
            m.A.write_artifact(art, target, origin, register=out / "register.jsonl")
    key_by_local = {i: str(k) for i, k in enumerate(sorted(tracks, key=str), 1)}
    key_by_trk = {t["trk_id"]: key_by_local[t["track_local_id"]] for t in s3r.tables["track"]}
    refs = reference_entries(s5r.tables, s4r.tables, key_by_trk, m.visible_frames(data))
    res = {"rec_id": rec, "set": name, "status": STATUS, "code_commit": prov[0], "environment_digest": prov[1], "contract": v2.CONTRACT,
           "decision": v2.DECISION, "label": LABEL, "s3": s3r.artifact_id, "s4": s4r.artifact_id, "s5": s5r.artifact_id,
           "s3_payload_sha256": s3r.payload_sha256, "s4_payload_sha256": s4r.payload_sha256, "s5_payload_sha256": s5r.payload_sha256,
           "s4_config_ids": [s5.substrate_config_id(record), gcf], "s5_config_id": s5.config_id(c5), "references": refs,
           "references_sha256": list_sha256(refs), "seconds": round(time.time() - t0, 2)}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=1, sort_keys=True))
    os.replace(tmp, path)
    return rec, "done", res["seconds"]


def summary(out: Path = OUT) -> dict:  # pragma: no cover - driver
    sets = {}
    for name in ("tuning",):
        recs = cameras(name)
        rows = [json.loads((out / name / f"{r}.json").read_text()) for r in recs]
        refs = [x for r in rows for x in r["references"]]
        sets[name] = {"cameras": len(rows), "expected": EXPECTED[name], "references": len(refs),
                      "assessable": sum(1 for x in refs if x["assessable"]),
                      "assessable_g1": sum(1 for x in refs if x["assessable"] and (x["lbl_O"] or x["lbl_H"] or x["lbl_PC"])),
                      "s5_config_ids": sorted({r["s5_config_id"] for r in rows}), "s4_config_ids": sorted({tuple(r["s4_config_ids"]) for r in rows}),
                      "code_commits": sorted({r["code_commit"] for r in rows}), "set_sha256": set_sha256(rows),
                      "per_camera": [{k: r[k] for k in ("rec_id", "s3", "s4", "s5", "s5_payload_sha256", "references_sha256")} for r in rows]}
    return sets


def _jobs(names, prov, out):
    return [(n, r, prov, out) for n in names for r in cameras(n)]


def main():  # pragma: no cover
    what = sys.argv[1]
    if what == "estimate":
        prov = provenance()
        out = Path(os.environ.get("V2REF_EST", str(OUT.parent / "references_estimate")))
        rows = [build_camera(("tuning", rec, prov, out)) for rec in (cameras("tuning")[0], cameras("tuning")[-1])]
        per = sum(r[2] for r in rows) / len(rows)
        print(json.dumps({"rows": rows, "per_camera_s": per, "total_tuning_h_serial": round(per * len(cameras("tuning")) / 3600, 3)}, indent=1))
        return
    if what in ("run", "verify"):
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        names = sys.argv[3:] or ["tuning"]
        if names != ["tuning"]:
            raise SystemExit("refused: D-66/D-67 restrict v2 reference building to tuning")
        prov = provenance()
        out = OUT if what == "run" else OUT.parent / "references_verify"
        jobs = _jobs(names, prov, out)
        it = map(build_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap_unordered(build_camera, jobs)
        for n, r in enumerate(it, 1):
            print(n, *r, flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
