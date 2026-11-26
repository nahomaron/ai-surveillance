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
    """Reads V0, S0 and the stored v2 test references afresh and builds the lock artifact."""
    from rq1.ids import artifact as A
    from rq1.ids.artifact import Spec, build_artifact
    from rq1.schema import files
    read = lambda d, t: files.read_table(str(Path(d) / f"{t}.parquet"), t, A.SCHEMA_VERSION)
    v0_id = A.verify(str(rd.V0_TEST))
    plan = [strip_derived("sampling_plan", r) for r in read(rd.V0_TEST, "sampling_plan")]
    windows = [strip_derived("reference_window", r) for r in read(rd.V0_TEST, "reference_window")]
    recs = read(rd.S0["sdg"], "recording")
    rec_by_cam = {r["camera_id"]: r["rec_id"] for r in recs}
    rec_of_group = {g["cgp_id"]: rec_by_cam[g["camera_ids"][0]] for g in read(rd.S0["sdg"], "camera_group")}
    proposal = {(p["camera_group_id"], p["window_index"]): p["proposed_lock_sha256"]
                for p in json.loads(rd.LOCK_PROPOSAL.read_text())["windows"]}
    locked, s5_ids, listing, mismatch = [], set(), [], 0
    for w in sorted(windows, key=lambda w: (w["camera_group_id"], w["window_index"])):
        rec = rec_of_group[w["camera_group_id"]]
        ref_row = json.loads((rd.vr.OUT / "test" / f"{rec}.json").read_text())
        h = lock_hash(w, rec, ref_row)
        mismatch += h != proposal.get((w["camera_group_id"], w["window_index"]))
        s5_ids.add(ref_row["s5"])
        locked.append(locked_window(w, h, LOCKED_UTC))
        listing.append({"camera_group_id": w["camera_group_id"], "window_index": w["window_index"], "rec_id": rec, "lock_sha256": h,
                        "reference_s5": ref_row["s5"]})
    spec = Spec("V0", CONTRACT, commit, env, (), (v0_id, *sorted(s5_ids)), {})
    built = build_artifact(spec, {"sampling_plan": plan, "reference_window": locked})
    return built, v0_id, listing, mismatch, len(s5_ids)


def _file_hashes(directory: Path) -> dict:
    return {i["path"]: i["file_sha256"] for i in json.loads((directory / "manifest.json").read_text())["files"]}


def main():  # pragma: no cover - reads stored artifacts
    from rq1.ids import artifact as A
    from rq1.ids.artifact import write_artifact
    from rq1.schema import vr_rules
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    v0_manifest_before = (rd.V0_TEST / "manifest.json").read_bytes()
    first, v0_id, listing, mismatch, n_s5 = build_once(commit, env)
    second, _, listing2, _, _ = build_once(commit, env)
    target = ROOT / "out/prereg" / first.artifact_id
    if (target / "manifest.json").exists():
        raise SystemExit(f"lock artifact {first.artifact_id} already stored; not rewritten")
    write_artifact(first, str(target), "synthetic_rendered")
    with tempfile.TemporaryDirectory() as tmp:
        write_artifact(second, tmp, "synthetic_rendered")
        files_equal = _file_hashes(target) == _file_hashes(Path(tmp))
    assert A.verify(str(target)) == first.artifact_id
    assert (rd.V0_TEST / "manifest.json").read_bytes() == v0_manifest_before and A.verify(str(rd.V0_TEST)) == v0_id
    rows = first.tables["reference_window"]
    vr054 = vr_rules.check_windows_locked(rows, datetime.now(timezone.utc))
    listing_sha = hashlib.sha256(rd.jcs(listing)).hexdigest()
    record = {
        "record": "v2 reference-window lock (Owner decision D-63 STEP 3; definition AR-71 item 11, accepted under D-63 ruling 1; representation AR-72)",
        "contract": CONTRACT, "code_commit": commit, "requirements_lock_sha256": env,
        "locked_utc": LOCKED_UTC.isoformat().replace("+00:00", "Z"),
        "plan": "m1a-sdg-test", "v0_artifact": v0_id, "v0_unchanged": True, "reference_set": rd.vr.LABEL,
        "lock_artifact": first.artifact_id, "lock_payload_sha256": first.payload_sha256, "lock_files": _file_hashes(target),
        "reference_s5_inputs": n_s5, "windows": len(rows), "annotation_status_locked": sum(r["annotation_status"] == "locked" for r in rows),
        "equal_to_d61_proposal": mismatch == 0, "windows_differing_from_proposal": mismatch,
        "second_build": {"artifact_id_equal": second.artifact_id == first.artifact_id, "payload_equal": second.payload_sha256 == first.payload_sha256,
                         "files_equal": files_equal, "listing_equal": listing2 == listing},
        "vr_e_054_issues_now": len(vr054),
        "definition": rd.window_lock_hash.__doc__.strip().replace("Proposed lock_sha256", "lock_sha256"),
        "per_window_listing_sha256": listing_sha, "per_window": listing,
        "statement": "Applied before any S3 or later stage on the test partition (D-63 ruling 1). No test S2 exists at the lock."}
    RECORD.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "per_window"}, indent=1))


if __name__ == "__main__":
    main()
