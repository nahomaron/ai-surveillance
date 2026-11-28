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
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


if __name__ == "__main__":
    main()
