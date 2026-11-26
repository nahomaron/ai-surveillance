"""D-60 STEP 4 (b): the Colab job manifests, and an upload folder of hard links for the Owner.

  PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py equivalence   -> research/colab/equivalence_manifest.json
  PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py tier1         -> research/colab/tier1_manifest.json
  PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py stage <job>   -> out/colab_upload/rq1_colab/data/<uri> (hard links)

Per camera: rec_id, the video path relative to the data root (kept as the Drive layout), size, SHA-256 (from the S0
`source_file` row, checked against the file on disk), and the eligible frames of its stored S1 `frame` table as runs.
- equivalence: the 2 tuning cameras of AR-70 item 7 (S1 from `out/t17_sdg`, the S1 their CPU S2 was decoded from); the
  stored CPU raw file must list exactly these frames.
- tier1: the 45 tier-1 cameras of X0b-A1 partition `test_layout_holdout` (S1 from `out/s1_d59`). Reads S0, S1 and the
  split only: no tier-1 output exists or is read.
"""
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rq1_colab import runner as R  # noqa: E402

from rq1.ids import artifact as artifacts  # noqa: E402
from rq1.pipeline import d60  # noqa: E402
from rq1.schema import files  # noqa: E402
from rq1.splits import builder  # noqa: E402

DATA = ROOT / "data"
EQUIVALENCE = {"ceiling": "rec_67do32mc4zwrtblayv5nixp4c2", "eye_level": "rec_4vmkmof7sgq7fbjqm6zb64xpko"}  # AR-70 item 7
DETECTOR = {"model": R.MODEL, "classes": list(R.CLASSES), "score_floor": R.SCORE_FLOOR, "predict": R.PREDICT,
            "thresholds_applied_on_the_laptop": {"person": 0.20, "forklift": 0.05}, "decision": "D-45 items 0 and 2 (frozen detector)",
            "weights": {n: {"url": w["url"], "bytes": w["bytes"], "sha256": w["sha256"]} for n, w in R.WEIGHTS.items()}, "pinned": R.PINNED}


def read(directory, table):
    return files.read_table(str(Path(directory) / f"{table}.parquet"), table, artifacts.SCHEMA_VERSION)


def s0_files(s0_dir):
    return {f["src_id"]: f for f in read(s0_dir, "source_file")}, {r["rec_id"]: r for r in read(s0_dir, "recording")}


def camera(rec_id, s0_dir, s1_dir, label):
    srcs, recs = s0_files(s0_dir)
    src = srcs[recs[rec_id]["src_id"]]
    path = DATA / src["uri"]
    if path.stat().st_size != src["size_bytes"] or R.sha256(path) != src["sha256"]:
        raise SystemExit(f"{rec_id}: the file on disk differs from its S0 source_file row")
    frames = read(s1_dir, "frame")
    if {f["recording_id"] for f in frames} != {rec_id}:
        raise SystemExit(f"{s1_dir}: S1 frame table is not {rec_id}'s")
    seq = {f["decode_seq"]: f["frame_index"] for f in frames if f["eligible"]}
    return {"rec_id": rec_id, "label": label, "uri": src["uri"], "size_bytes": src["size_bytes"], "sha256": src["sha256"],
            "s0": Path(s0_dir).name, "s1": Path(s1_dir).name, "n_decoded": len(frames), "n_eligible": len(seq), "eligible_runs": R.compress(seq)}


def equivalence():
    index = {e["rec_id"]: e for e in json.load(open(ROOT / "out/s0_sdg/index.json"))}
    s1_of = {c["rec_id"]: c["s1"] for c in json.load(open(ROOT / "research/datasets/part3/t17_counts_sdg.json"))["cameras"]}
    cams = []
    for vp, rec in EQUIVALENCE.items():
        e = index[rec]
        cam = camera(rec, ROOT / "out/s0_sdg" / e["s0"], ROOT / "out/t17_sdg" / s1_of[rec], f"{e['run']}.{e['camera']} ({vp}, tuning)")
        cpu = json.load(gzip.open(ROOT / f"out/m1b/pilot/s2raw/{rec}.json.gz", "rt"))
        if {f["decode_seq"]: f["frame_index"] for f in cpu["frames"]} != R.expand(cam["eligible_runs"]):
            raise SystemExit(f"{rec}: the stored CPU S2 frames differ from its S1 eligible frames")
        cam["cpu_s2raw"] = {"file": f"out/m1b/pilot/s2raw/{rec}.json.gz", "sha256": R.sha256(ROOT / f"out/m1b/pilot/s2raw/{rec}.json.gz"),
                            "code_commit": cpu["code_commit"], "device": cpu["predict"]["device"]}
        cams.append(cam)
    return {"job": "equivalence", "purpose": "D-60 STEP 4 (c): 2 tuning cameras with stored CPU S2 (synthetic tuning data)", "cameras": cams}


def tier1():
    rec = json.load(open(ROOT / "docs/preregistration/freeze_record_X0b-A1.json"))
    split = read(ROOT / "out/prereg" / rec["artifact_id"], "split_manifest")[0]
    held_out = sorted(r for r, p in builder.recording_partitions(split).items() if p == d60.PARTITION[1])
    index = {e["rec_id"]: e for e in json.load(open(ROOT / "out/s0_d59/index.json"))}
    s1_of = {c["rec_id"]: c["s1"] for c in json.load(open(ROOT / "research/datasets/part5/s1_d59_summary.json"))["cameras"]}
    cams = [camera(r, ROOT / "out/s0_d59" / index[r]["s0"], ROOT / "out/s1_d59" / s1_of[r], f"{index[r]['run']}.{index[r]['camera']}")
            for r in sorted(held_out, key=lambda r: (index[r]["run"], index[r]["camera"]))]
    assert len(cams) == d60.TIER1_CAMERAS and all(index[c["rec_id"]]["tier"] == 1 for c in cams)
    return {"job": "tier1", "purpose": "D-60 rulings 1 and 5: S2 on the 45 tier-1 cameras (partition test_layout_holdout of X0b-A1)",
            "split": {"artifact_id": rec["artifact_id"], "spm_id": rec["spm_id"]}, "cameras": cams}


def manifest(job):
    body = {"equivalence": equivalence, "tier1": tier1}[job]()
    total = sum(c["size_bytes"] for c in body["cameras"])
    out = {"format": "rq1-colab-job-1", "decision": "D-60", "job": body["job"], "purpose": body["purpose"], "detector": DETECTOR,
           "drive_layout": "<Drive>/rq1_colab/data/<uri>; outputs to <Drive>/rq1_colab/out/<job>/", **({"split": body["split"]} if "split" in body else {}),
           "videos": len(body["cameras"]), "total_bytes": total, "total_gb": round(total / 1e9, 2), "cameras": body["cameras"]}
    path = ROOT / f"research/colab/{job}_manifest.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(job, out["videos"], "videos", out["total_bytes"], "bytes", f"({out['total_gb']} GB)", "eligible frames", sum(c["n_eligible"] for c in body["cameras"]))


def stage(job):
    """Hard links (no extra disk space) of the job's videos under out/colab_upload/rq1_colab/data/<uri>, for one folder upload."""
    m = json.load(open(ROOT / f"research/colab/{job}_manifest.json"))
    base = ROOT / "out/colab_upload/rq1_colab/data"
    for c in m["cameras"]:
        dst = base / c["uri"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            os.link(DATA / c["uri"], dst)
        if dst.stat().st_size != c["size_bytes"]:
            raise SystemExit(f"{dst}: size differs")
    print(f"{len(m['cameras'])} videos linked under {base}")


if __name__ == "__main__":
    if sys.argv[1] == "stage":
        stage(sys.argv[2])
    else:
        manifest(sys.argv[1])
