"""D-60 STEP 3 (T-26s): freeze the split addendum X0b-A1 and run its X0c leakage audit.

X0b-A1 records the 118 recordings of the 11 D-59 scenes (S0 of D-60 STEP 2) and nothing else, so no X0b assignment changes:
tier 1 (010, 011, 016, 017, 018, 019, 022) -> `test_layout_holdout`; tier 2 (002, 004, 006, 020) -> `reserve` (rulings 1-3).
Leakage groups = the metadata edges (E-1.2.1 section 8, T14, T16.2) plus one `same_layout` chain per `layout_id` (STEP 3).
Inputs are pre-system metadata only (R-4): the 11 S0 artifacts, and X0b's ID as a reference input. No system output exists
on these scenes (no S2 or later stage has run on them). `frozen_utc` is the supplied event time of this freeze, taken once
(AR-57 item 6), outside the hashes (AR-7). X0c: every metadata and layout edge among the 118 recordings, discovery basis
`metadata`. Cross-checks against X0b: no recording and no source file in both; layouts of tier 1 against the held layouts.
Usage: PYTHONPATH=src .venv/bin/python research/preregistration/freeze_x0b_a1.py
  -> out/prereg/<X0b-A1>/, out/prereg/<X0c>/, docs/preregistration/freeze_record_X0b-A1.json
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rq1.ids import artifact as artifacts
from rq1.ids import core
from rq1.ids.artifact import Spec, build_artifact, write_artifact
from rq1.pipeline import d60
from rq1.schema import files
from rq1.splits import builder

ROOT = Path(__file__).resolve().parents[2]
FROZEN_UTC = datetime(2026, 11, 26, 2, 0, 46, tzinfo=timezone.utc)  # supplied event time of the X0b-A1 freeze (taken once)
S0_D59 = ROOT / "out/s0_d59"
X0B_S0 = {"sdg": ROOT / "out/s0_sdg/art_xwrldyhquvmorjhpjxb573tbxk", "smartspaces_000": ROOT / "out/s0_smartspaces/art_k3kmwlyr3dwyaztop6bedfkxts"}
W000_MAP = ROOT / "data/raw/smartspaces/MTMC_Tracking_2026/train/Warehouse_000/map.png"
RECORD = ROOT / "docs/preregistration/freeze_record_X0b-A1.json"
ADDENDUM_ID = core.make_id("sdr", d60.ADDENDUM_RECORD)


def provenance():
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research/preregistration"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def read(directory, table):
    return files.read_table(os.path.join(directory, f"{table}.parquet"), table, artifacts.SCHEMA_VERSION)


def s0(directory):
    m = json.load(open(os.path.join(directory, "manifest.json")))
    if artifacts.verify(str(directory)) != m["artifact_id"]:
        raise SystemExit(f"{directory}: S0 artifact does not verify")
    return m["artifact_id"], {t: read(directory, t) for t in ("dataset_source", "session", "recording", "source_file")}


def main():
    commit, env = provenance()
    if FROZEN_UTC.tzinfo is None:
        raise SystemExit("frozen_utc must be UTC")
    index = json.load(open(S0_D59 / "index.json"))
    s0_ids = sorted({e["s0"] for e in index})
    loaded = {i: s0(S0_D59 / i)[1] for i in s0_ids}
    if any(os.path.basename(p).startswith(("s2", "s3")) for p in os.listdir(ROOT / "out") if "d59" in p):
        raise SystemExit("refused: a system-output folder for the D-59 scenes exists (R-4)")
    rows = d60.addendum_rows(list(loaded.values()))
    assert len(rows) == d60.TIER1_CAMERAS + d60.TIER2_CAMERAS

    split = d60.freeze_addendum(rows, FROZEN_UTC)
    a1 = build_artifact(Spec("X0b", d60.CONTRACT, commit, env, (ADDENDUM_ID,), (*s0_ids, d60.X0B_ARTIFACT_ID), {}), {"split_manifest": [split]})
    write_artifact(a1, str(ROOT / "out/prereg" / a1.artifact_id), d60.DATA_ORIGIN)
    spm = a1.tables["split_manifest"][0]["spm_id"]

    edges = d60.audit_edges(rows)
    audit = builder.audit(split, spm, edges, "metadata", 1, rows)
    if audit["violations"]:
        raise SystemExit(f"X0c violations: {audit['violations']}")
    x0c = build_artifact(Spec("X0c", d60.CONTRACT, commit, env, (), (a1.artifact_id,), {}), {"leakage_audit": [audit]})
    write_artifact(x0c, str(ROOT / "out/prereg" / x0c.artifact_id), d60.DATA_ORIGIN)

    # X0b is read, never written: verify it and check the addendum leaves it alone.
    x0b_dir = ROOT / "out/prereg" / d60.X0B_ARTIFACT_ID
    if artifacts.verify(str(x0b_dir)) != d60.X0B_ARTIFACT_ID or json.load(open(x0b_dir / "manifest.json"))["payload_sha256"] != d60.X0B_PAYLOAD_SHA256:
        raise SystemExit("stored X0b does not verify against its freeze record")
    x0b = read(x0b_dir, "split_manifest")[0]
    x0b_shas = {f["sha256"] for d in X0B_S0.values() for f in s0(d)[1]["source_file"]}
    a1_shas = {f["sha256"] for t in loaded.values() for f in t["source_file"]}
    disjoint = d60.check_disjoint_from_x0b(split, x0b, a1_shas, x0b_shas)
    if disjoint["recordings_in_both"] or disjoint["source_files_in_both"]:
        raise SystemExit(f"addendum overlaps X0b: {disjoint}")

    w000_map = hashlib.sha256(W000_MAP.read_bytes()).hexdigest()
    part_of = builder.recording_partitions(split)
    group_of = {m: g["leakage_group_id"] for g in split["leakage_groups"] for m in g["member_recording_ids"]}
    scenes = []
    for sid, t in sorted(loaded.items(), key=lambda kv: kv[1]["session"][0]["lineage"]["ext_run_id"]):
        lin = t["session"][0]["lineage"]
        recs = [r["rec_id"] for r in t["recording"]]
        scenes.append({"scene": lin["ext_run_id"], "tier": d60.tier(lin["ext_run_id"]), "s0": sid, "cameras": len(recs),
                       "partition": sorted({part_of[r] for r in recs}), "leakage_group_id": sorted({group_of[r] for r in recs}),
                       "layout_id": lin["layout_id"], "layout_is_warehouse_000_map": lin["layout_id"] == w000_map})
    tier1_held = sorted(s["scene"] for s in scenes if s["tier"] == 1 and s["layout_is_warehouse_000_map"])
    if tier1_held:
        raise SystemExit(f"tier-1 scenes in the held Warehouse_000 layout: {tier1_held}")
    by_part = {p: sorted({a["leakage_group_id"] for a in split["assignments"] if a["partition"] == p}) for p in sorted(set(d60.PARTITION.values()))}
    record = {"decision": d60.DECISION, "contract": d60.CONTRACT, "code_commit": commit, "requirements_lock_sha256": env,
              "frozen_utc": FROZEN_UTC.isoformat(), "artifact_id": a1.artifact_id, "payload_sha256": a1.payload_sha256, "spm_id": spm,
              "split_label": split["split_label"], "version": split["version"], "tier": split["tier"], "basis": split["basis"],
              "shared_scene_content": split["shared_scene_content"], "addendum_config_id": ADDENDUM_ID, "addendum_record": d60.ADDENDUM_RECORD,
              "s0_inputs": s0_ids, "x0b_reference_input": {"artifact_id": d60.X0B_ARTIFACT_ID, "payload_sha256": d60.X0B_PAYLOAD_SHA256, "spm_id": d60.X0B_SPM_ID},
              "recordings": len(rows), "recordings_by_partition": {p: sum(1 for v in part_of.values() if v == p) for p in by_part},
              "leakage_groups": len(split["leakage_groups"]), "leakage_groups_by_partition": {p: len(v) for p, v in by_part.items()},
              "scenes": scenes,
              "x0c_audit": {"artifact_id": x0c.artifact_id, "payload_sha256": x0c.payload_sha256, "lka_id": x0c.tables["leakage_audit"][0]["lka_id"],
                            "discovery_basis": "metadata", "edges": len(edges), "edges_by_type": {k: sum(1 for e in edges if e["edge_type"] == k) for k in sorted({e["edge_type"] for e in edges})},
                            "violations": len(audit["violations"]), "audit_complete": audit["audit_complete"]},
              "x0b_checks": {**disjoint, "warehouse_000_map_sha256": w000_map,
                             "tier1_layouts_held_before": tier1_held,
                             "tier2_scenes_in_warehouse_000_layout": sorted(s["scene"] for s in scenes if s["tier"] == 2 and s["layout_is_warehouse_000_map"])},
              "system_outputs_on_these_scenes_at_freeze": "none (S0 and S1 only)"}
    json.dump(record, open(RECORD, "w"), indent=1)
    print(json.dumps({k: v for k, v in record.items() if k not in ("scenes", "s0_inputs", "addendum_record")}, indent=1))


if __name__ == "__main__":
    main()
