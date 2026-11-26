"""D-61 STEP 6: test readiness for the v2 test run. Prepare only; no test is run (no S2 or later system stage on test).

  PYTHONPATH=src .venv/bin/python research/preregistration/readiness_v2.py
      -> out/prereg/<X0c of X0b v1>/, docs/preregistration/window_lock_proposal_v2.json, docs/preregistration/test_readiness_v2.json

Items (pass / fail, each with its evidence):
  1. X0c complete: the leakage audit (R-2) of X0b v1 over every metadata edge among its 739 recordings (E-1.2.1 section 8,
     T14, T16.2), discovery basis `metadata`, `audit_complete` true, no violation.
  2. Windows lockable: every window of the V0 plan m1a-sdg-test maps to one test recording with a v2 reference entry; a
     proposed `lock_sha256` per window (AR-71 item 11: the contract does not define its content) for the Architect.
     `locked_utc` stays null (`pending_review`): nothing is locked and no V0 artifact is rewritten.
  3. Freeze record reproducible: the two STEP 5 builds of `freeze_record_v2.json` are byte-identical.
  4. Test run IDs and hashes match X0b v1: the X0b artifact verifies and equals the v1 record; 48 test runs; 471 test cameras
     (V0 m1a-sdg-test camera groups) = the v2 test reference set.
  5. Detector and tracker weights hashed: YOLO-World and CLIP weights on disk equal the published SHA-256; the tracker
     (ByteTrack, ReID off) loads no weights.
  6. Licence row present for every component used: the SDG dataset, the detector weights, the CLIP text encoder; software
     libraries are listed with their status.
  7. Colab runtime estimate for S2 on 471 cameras: result "open". The CPU figure is measured; no Colab GPU time is
     measured yet (D-62 pending), so the GPU figure is not stated.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v2_references as vr  # noqa: E402

ROOT = vr.ROOT
X0B = ROOT / "out/prereg/art_w5v3ldr43xdsqc6l4zifmjkuuj"
V0_TEST = ROOT / "out/prereg/art_hfchmhd3zbgjl24gnqaxifaoo3"
S0 = {"sdg": ROOT / "out/s0_sdg/art_xwrldyhquvmorjhpjxb573tbxk", "smartspaces_000": ROOT / "out/s0_smartspaces/art_k3kmwlyr3dwyaztop6bedfkxts"}
RECORD = ROOT / "docs/preregistration/freeze_record_v2.json"
RECORD_2 = ROOT / "out/v2/freeze_record_v2.second_build.json"
LOCK_PROPOSAL = ROOT / "docs/preregistration/window_lock_proposal_v2.json"
OUT = ROOT / "docs/preregistration/test_readiness_v2.json"
CONTRACT = "E-1.2.26"
CPU_S_PER_FRAME = 0.388  # pilot S2 on this laptop (research/m1b/pilot_runtime_estimate.md)


def jcs(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def window_lock_hash(window: dict, rec_id: str, ref_row: dict) -> str:
    """Proposed lock_sha256 (AR-71 item 11): SHA-256 of the JCS form of the window's natural key and bounds, the reference
    set label, the camera's reference S5 (ID and payload hash) and the reference entries that overlap [t_start, t_guard_end)."""
    t0, t1 = window["t_start_tl_s"], window["t_guard_end_tl_s"]
    inside = [x for x in ref_row["references"] if x["t_start_tl_s"] < t1 and x["t_end_tl_s"] > t0]
    body = {"plan_nk": window["plan_nk"], "camera_group_id": window["camera_group_id"], "window_index": window["window_index"],
            "t_start_tl_s": t0, "t_end_tl_s": window["t_end_tl_s"], "t_guard_end_tl_s": t1, "reference_set": vr.LABEL, "rec_id": rec_id,
            "reference_s5": ref_row["s5"], "reference_s5_payload_sha256": ref_row["s5_payload_sha256"], "references": inside}
    return hashlib.sha256(jcs(body)).hexdigest()


def table(item: str, ok: bool, evidence) -> dict:
    return {"item": item, "result": "pass" if ok else "fail", "evidence": evidence}


def main():  # pragma: no cover - reads stored artifacts
    from rq1.ids import artifact as A
    from rq1.ids.artifact import Spec, build_artifact, write_artifact
    from rq1.schema import files
    from rq1.splits import builder, leakage
    read = lambda d, t: files.read_table(str(Path(d) / f"{t}.parquet"), t, A.SCHEMA_VERSION)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    v1 = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())
    rows_out = []

    # 1. X0c of X0b v1
    x0b_id = A.verify(str(X0B))
    split = read(X0B, "split_manifest")[0]
    x0b_man = json.loads((X0B / "manifest.json").read_text())
    rows = []
    for key, d in S0.items():
        tables = {t: read(d, t) for t in ("dataset_source", "session", "recording")}
        ses = {s["ses_id"]: s for s in tables["session"]}
        ds = tables["dataset_source"][0]
        rows += [{"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": ds["dsr_id"], "dataset_name": ds["name"],
                  "lineage": ses[r["session_id"]]["lineage"]} for r in tables["recording"]]
    in_split = {m for g in split["leakage_groups"] for m in g["member_recording_ids"]}
    assert {r["recording_id"] for r in rows} == in_split, "X0b recordings differ from its S0 inputs"
    edges = [{"recording_a": a, "recording_b": b, "edge_type": k, "evidence_ref": "S0 lineage (E-1.2.1 section 8)"}
             for a, b, k in sorted(leakage.metadata_edges(rows))]
    audit = builder.audit(split, split["spm_id"], edges, "metadata", 1, rows)
    x0c = build_artifact(Spec("X0c", CONTRACT, commit, env, (), (x0b_id,), {}), {"leakage_audit": [audit]})
    target = ROOT / "out/prereg" / x0c.artifact_id
    if not (target / "manifest.json").exists():
        write_artifact(x0c, str(target), "synthetic_rendered")
    rows_out.append(table("X0c complete (R-2)", audit["audit_complete"] and not audit["violations"],
                          {"x0c_artifact_id": x0c.artifact_id, "payload_sha256": x0c.payload_sha256, "lka_id": x0c.tables["leakage_audit"][0]["lka_id"],
                           "split": x0b_id, "edges": len(edges), "edges_by_type": {k: sum(1 for e in edges if e["edge_type"] == k) for k in sorted({e["edge_type"] for e in edges})},
                           "violations": len(audit["violations"]), "audit_complete": audit["audit_complete"], "discovery_basis": "metadata"}))

    # 4. test runs and cameras
    windows = read(V0_TEST, "reference_window")
    groups = read(S0["sdg"], "camera_group")
    rec_of_group = {}
    recs = read(S0["sdg"], "recording")
    rec_by_cam = {r["camera_id"]: r["rec_id"] for r in recs}
    for g in groups:
        rec_of_group[g["cgp_id"]] = rec_by_cam[g["camera_ids"][0]]
    test_refs = vr.cameras("test")
    window_recs = sorted({rec_of_group[w["camera_group_id"]] for w in windows})
    v0_man = json.loads((V0_TEST / "manifest.json").read_text())
    v1_plan = next(p for p in v1["sampling_plans"] if p["plan_label"] == "m1a-sdg-test")
    ok4 = (x0b_id == v1["split"]["artifact_id"] and x0b_man["payload_sha256"] == v1["split"]["payload_sha256"] and len(v1["split"]["sdg_test_runs"]) == 48
           and A.verify(str(V0_TEST)) == v1_plan["artifact_id"] and v0_man["payload_sha256"] == v1_plan["payload_sha256"]
           and len(windows) == 471 and window_recs == test_refs)
    rows_out.append(table("test run IDs and hashes match X0b v1 (48 runs, 471 cameras)", ok4,
                          {"x0b": x0b_id, "x0b_payload": x0b_man["payload_sha256"], "test_runs": len(v1["split"]["sdg_test_runs"]),
                           "v0_test": v1_plan["artifact_id"], "v0_payload": v0_man["payload_sha256"], "windows": len(windows),
                           "window_recordings": len(window_recs), "v2_test_reference_cameras": len(test_refs), "same_recordings": window_recs == test_refs}))

    # 2. windows lockable (proposal only)
    proposal = []
    for w in sorted(windows, key=lambda w: (w["camera_group_id"], w["window_index"])):
        rec = rec_of_group[w["camera_group_id"]]
        ref_row = json.loads((vr.OUT / "test" / f"{rec}.json").read_text())
        proposal.append({"plan_nk": w["plan_nk"], "camera_group_id": w["camera_group_id"], "window_index": w["window_index"], "rec_id": rec,
                         "annotation_status_now": w["annotation_status"], "locked_utc": None, "locked_utc_null_reason": "pending_review",
                         "proposed_lock_sha256": window_lock_hash(w, rec, ref_row)})
    lock_doc = {"status": "PROPOSAL for the Architect (D-61 STEP 6); nothing is locked; the V0 artifact is unchanged",
                "plan": "m1a-sdg-test", "v0_artifact": v1_plan["artifact_id"], "reference_set": vr.LABEL, "definition": window_lock_hash.__doc__.strip(),
                "locked_utc": "to be supplied as the event time of the lock (AR-7: event-time column, outside the payload hash), after review",
                "windows": proposal}
    LOCK_PROPOSAL.write_text(json.dumps(lock_doc, indent=1, sort_keys=True) + "\n")
    rows_out.append(table("windows lockable", len(proposal) == 471 and all(p["proposed_lock_sha256"] for p in proposal),
                          {"windows": len(proposal), "proposal": str(LOCK_PROPOSAL.relative_to(ROOT)),
                           "proposal_sha256": hashlib.sha256(LOCK_PROPOSAL.read_bytes()).hexdigest(), "locked": 0}))

    # 3. freeze record reproducible
    same = RECORD.exists() and RECORD_2.exists() and RECORD.read_bytes() == RECORD_2.read_bytes()
    rows_out.append(table("freeze record reproducible", same, {"record": str(RECORD.relative_to(ROOT)),
                                                              "sha256": hashlib.sha256(RECORD.read_bytes()).hexdigest() if RECORD.exists() else None,
                                                              "second_build_identical": same}))

    # 5. weights
    rec = json.loads(RECORD.read_text())
    w = rec["configurations"]["detector"]["weights"]
    rows_out.append(table("detector and tracker weights hashed", all(x["match"] for x in w.values()),
                          {"detector": {k: {"sha256": v["sha256"], "on_disk_equal": v["match"]} for k, v in w.items()},
                           "tracker": "ByteTrack (Ultralytics 8.4.215), ReID off: no weights loaded"}))

    # 6. licence rows
    s0_lic = read(S0["sdg"], "license_component")
    pilot = json.loads((ROOT / "research/m1b/pilot_license_components.json").read_text())["rows"]
    have = {x["component"]: (x["license_label"], x["license_status"]) for x in s0_lic} | {x["row"]["component"]: (x["row"]["license_label"], x["row"]["license_status"]) for x in pilot}
    needed = {"SDG dataset": "nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes", "detector weights": "yolov8s-worldv2.pt",
              "CLIP text encoder": "ViT-B-32.pt"}
    found = {k: {"component": v, "row": have.get(v)} for k, v in needed.items()}
    rows_out.append(table("licence row present for every component used", all(x["row"] and x["row"][1] == "verified" for x in found.values()),
                          {"components": found, "software_without_row": ["ultralytics 8.4.215 (AGPL-3.0; ByteTrack and the YOLO-World runtime)",
                                                                         "PyAV", "PyTorch"],
                           "note": "software libraries carry no license_component row in any artifact; listed for the Owner"}))

    # 7. Colab runtime estimate
    frames = 471 * 300  # 300 frames per SDG camera (qualification 3.11); eligible frames may be fewer
    rows_out.append({"item": "Colab runtime estimate for S2 on 471 cameras", "result": "open",
                     "evidence": {"frames_upper_bound": frames, "cpu_s_per_frame": CPU_S_PER_FRAME,
                                  "cpu_hours_upper_bound": round(frames * CPU_S_PER_FRAME / 3600, 1),
                                  "cpu_reference": "research/m1b/pilot_runtime_estimate.md (61,749 frames x 0.388 s, this laptop)",
                                  "colab_gpu": "not measured: the D-62 equivalence run has not returned; its Colab manifest records wall time "
                                               "per camera, from which the 471-camera estimate follows (frames x measured s per frame)"}})

    out = {"status": "D-61 STEP 6: prepared; no test run; nothing on test beyond reference building from truth and this audit",
           "contract": CONTRACT, "code_commit": commit, "items": rows_out}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for r in rows_out:
        print(f"{r['result']:5s} {r['item']}")


if __name__ == "__main__":
    main()
