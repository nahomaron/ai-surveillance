"""D-60 STEP 2 (T-26r): S0 registration and S1 coverage of the 11 D-59 SmartSpaces scenes (118 recordings).

S0, as T-18 (`part3/s0_register_smartspaces.py`): one S0 artifact per scene, `synthetic_rendered`, CR-020 option (a) version
label; lineage per D-60 ruling 4 (`layout_id` = SHA-256 of `map.png`, `generation_batch` = `MTMC_Tracking_2026/<folder>@d38193b`,
AR-70); calibration from `calibration.json`. Before registering, every video and every `map.png` is hashed from disk and
compared with `candidates.json` (qualification Part 5); any difference refuses the run.
S1: rules version rv2 with the decode configuration of the T-17 S1 runs (`part3/t17_oracle.py` DECODE_RECORD, the S1 the
tuning cameras use, D-45 item 3b). S1 only: no oracle track, no ground truth read, no detector (D-60 hard limits).
Resumable: an S1 artifact already written for a recording with the same configuration and S0 input is verified and kept.
Summaries carry IDs and frame counts only (frames decoded and eligible, for the STEP 5 integrity check).

Usage: PYTHONPATH=src .venv/bin/python research/datasets/part5/s0_s1_d59.py s0|s1 [workers]
  out/s0_d59/<art>/, out/s0_d59/index.json, research/datasets/part5/s0_d59_summary.json
  out/s1_d59/<art>/, research/datasets/part5/s1_d59_summary.json
"""
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path

import av

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/datasets/part3"))
import t17_oracle as t17  # noqa: E402  (DECODE_RECORD, DCF, decode parameters; nothing runs at import)

from rq1.adapters import registration as reg  # noqa: E402
from rq1.adapters import smartspaces  # noqa: E402
from rq1.decode import quality, stage  # noqa: E402
from rq1.decode.timestamps import DecodeConfig  # noqa: E402
from rq1.ids import artifact as artifacts  # noqa: E402
from rq1.ids.artifact import Spec, write_artifact  # noqa: E402
from rq1.pipeline import d60  # noqa: E402
from rq1.registry.registrar import Registrar  # noqa: E402
from rq1.schema import files  # noqa: E402

DATA = ROOT / "data"
BASE = "raw/smartspaces/MTMC_Tracking_2026"
S0_DIR, S1_DIR = ROOT / "out/s0_d59", ROOT / "out/s1_d59"
PART5 = ROOT / "research/datasets/part5"
CANDIDATES = PART5 / "candidates.json"


def provenance():
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research/datasets"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def published():
    """path (relative to the data root) -> (sha256, size), from candidates.json."""
    c = json.load(open(CANDIDATES))
    assert c["revision"].startswith(reg.D59_REVISION) and reg.SS_VERSION.endswith(c["revision"])
    return {f"raw/smartspaces/{f['path']}": (f["sha256"], f["size"]) for s in c["scenes"].values() for f in s["files"]}


def s0(commit, env):
    pub, registrar, index = published(), Registrar(), []
    summary = {"decision": d60.DECISION, "contract": d60.CONTRACT, "code_commit": commit, "retrieved_utc": d60.RETRIEVED_UTC.isoformat(), "scenes": []}
    S0_DIR.mkdir(parents=True, exist_ok=True)
    for name, folder in sorted(d60.SCENES.items()):
        rel = f"{BASE}/{folder}/{name}"
        map_rel = f"{rel}/map.png"
        map_sha = sha256(DATA / map_rel)
        if (map_sha, os.path.getsize(DATA / map_rel)) != pub[map_rel]:
            raise SystemExit(f"{map_rel}: hash or size differs from candidates.json")
        cals = smartspaces.calibrations(smartspaces.load(str(DATA / rel / "calibration.json")))
        cams = {}
        for n in sorted(os.listdir(DATA / rel / "videos")):
            if not n.endswith(".mp4"):
                continue
            vrel = f"{rel}/videos/{n}"
            digest, size = sha256(DATA / vrel), os.path.getsize(DATA / vrel)
            if (digest, size) != pub[vrel]:
                raise SystemExit(f"{vrel}: hash or size differs from candidates.json")
            with av.open(str(DATA / vrel)) as c:
                codec = c.streams.video[0].codec_context.name
            cams[n[:-4]] = (reg.Video(vrel, digest, size, "mp4", codec), cals.get(n[:-4]))
        meta = reg.smartspaces_metadata(reg.SmartSpacesScene(name, d60.DATA_ORIGIN, None, cams), d60.RETRIEVED_UTC,
                                        layout_id=map_sha, generation_batch=reg.d59_generation_batch(folder))
        built = registrar.register(meta, Spec("S0", d60.CONTRACT, commit, env, (), (), {}))
        write_artifact(built, str(S0_DIR / built.artifact_id), d60.DATA_ORIGIN)
        t = built.tables
        rec = {r["registration_label"]: r for r in t["recording"]}
        tl = {x["tl_id"]: x for x in t["timeline"]}
        for cam, (vid, cal) in sorted(cams.items()):
            r = rec[f"{name}.{cam}"]
            index.append({"dataset": "smartspaces_d59", "run": name, "tier": d60.tier(name), "camera": cam, "rec_id": r["rec_id"], "camera_id": r["camera_id"],
                          "timeline": tl[r["timeline_id"]], "uri": vid.uri, "sha256": vid.sha256, "size_bytes": vid.size_bytes,
                          "calibration": cal, "s0": built.artifact_id})
        summary["scenes"].append({"scene": name, "tier": d60.tier(name), "folder": folder, "artifact_id": built.artifact_id, "payload_sha256": built.payload_sha256,
                                  "data_origin": d60.DATA_ORIGIN, "dataset_version": t["dataset_source"][0]["version"], "dsr_id": t["dataset_source"][0]["dsr_id"],
                                  "rows": {k: len(v) for k, v in sorted(t.items())}, "lineage": t["session"][0]["lineage"],
                                  "cameras": len(cams), "cameras_without_calibration": sorted(c for c, (_, cal) in cams.items() if cal is None),
                                  "recordings": sorted([r["rec_id"], r["registration_label"]] for r in t["recording"])})
    json.dump(index, open(S0_DIR / "index.json", "w"))
    by_tier = {k: sum(s["cameras"] for s in summary["scenes"] if s["tier"] == k) for k in (1, 2)}
    assert by_tier == {1: d60.TIER1_CAMERAS, 2: d60.TIER2_CAMERAS}, by_tier
    summary["cameras_by_tier"] = {str(k): v for k, v in by_tier.items()}
    summary["layouts"] = {str(k): len({s["lineage"]["layout_id"] for s in summary["scenes"] if s["tier"] == k}) for k in (1, 2)}
    json.dump(summary, open(PART5 / "s0_d59_summary.json", "w"), indent=1)
    print(json.dumps({k: summary[k] for k in ("cameras_by_tier", "layouts")}), [(s["scene"], s["artifact_id"], s["cameras"], s["cameras_without_calibration"]) for s in summary["scenes"]])


def s1_worker(args):
    entry, commit, env = args
    t0 = time.time()
    cfg = DecodeConfig(k_sup=t17.V["k_sup"], f_untimed=t17.V["f_untimed"], f_sub=t17.V["f_sub"], rules_version=quality.RV2, declared={})
    item = stage.S1Input(recording_id=entry["rec_id"], camera_id=entry["camera_id"], path=DATA / entry["uri"])
    s1 = stage.run_s1(entry["timeline"], [item], cfg, Spec("S1", d60.CONTRACT, commit, env, (t17.DCF,), (entry["s0"],), {}))
    write_artifact(s1, str(S1_DIR / s1.artifact_id), d60.DATA_ORIGIN)
    return entry["rec_id"], s1.artifact_id, round(time.time() - t0, 1)


def kept_s1(entry):
    """A verified S1 artifact already written for this recording with this configuration and S0 input, or None."""
    for art in sorted(os.listdir(S1_DIR)):
        m = json.load(open(S1_DIR / art / "manifest.json"))
        spec = m["spec"]
        if spec["stage"] == "S1" and spec["config_ids"] == [t17.DCF] and spec["input_artifact_ids"] == [entry["s0"]] and \
                files.read_table(str(S1_DIR / art / "decode_summary.parquet"), "decode_summary", artifacts.SCHEMA_VERSION)[0]["recording_id"] == entry["rec_id"]:
            if artifacts.verify(str(S1_DIR / art)) != art:
                raise SystemExit(f"{art}: stored S1 artifact does not verify")
            return art
    return None


def s1(commit, env, workers):
    index = json.load(open(S0_DIR / "index.json"))
    S1_DIR.mkdir(parents=True, exist_ok=True)
    done = {e["rec_id"]: kept_s1(e) for e in index}
    todo = [e for e in index if done[e["rec_id"]] is None]
    print(f"{len(index) - len(todo)} kept, {len(todo)} to decode with {workers} workers", flush=True)
    with multiprocessing.Pool(workers) as pool:
        for rec, art, sec in pool.imap_unordered(s1_worker, [(e, commit, env) for e in todo]):
            done[rec] = art
            print(rec, art, sec, "s", flush=True)
    cams, totals = [], {"recordings": 0, "frames_decoded": 0, "frames_eligible": 0}
    for e in index:
        art = done[e["rec_id"]]
        frames = files.read_table(str(S1_DIR / art / "frame.parquet"), "frame", artifacts.SCHEMA_VERSION)
        cov = files.read_table(str(S1_DIR / art / "coverage_segment.parquet"), "coverage_segment", artifacts.SCHEMA_VERSION)
        m = json.load(open(S1_DIR / art / "manifest.json"))
        row = {"run": e["run"], "tier": e["tier"], "camera": e["camera"], "rec_id": e["rec_id"], "s0": e["s0"], "s1": art, "s1_code_commit": m["spec"]["code_commit"],
               "frames_decoded": len(frames), "frames_eligible": sum(1 for f in frames if f["eligible"]), "coverage_segments": len(cov),
               "coverage_extent_tl_s": [min(c["t_start_tl_s"] for c in cov), max(c["t_end_tl_s"] for c in cov)]}
        cams.append(row)
        totals["recordings"] += 1
        totals["frames_decoded"] += row["frames_decoded"]
        totals["frames_eligible"] += row["frames_eligible"]
    summary = {"decision": d60.DECISION, "contract": d60.CONTRACT, "decode_config_id": t17.DCF, "decode_record": t17.DECODE_RECORD,
               "totals": totals, "totals_by_tier": {str(k): {f: sum(c[f] for c in cams if c["tier"] == k) for f in ("frames_decoded", "frames_eligible")} for k in (1, 2)},
               "cameras": cams}
    json.dump(summary, open(PART5 / "s1_d59_summary.json", "w"), indent=1)
    print(json.dumps({k: summary[k] for k in ("decode_config_id", "totals", "totals_by_tier")}, indent=1))


if __name__ == "__main__":
    commit, env = provenance()
    if sys.argv[1] == "s0":
        s0(commit, env)
    elif sys.argv[1] == "s1":
        s1(commit, env, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    else:
        raise SystemExit(__doc__)
