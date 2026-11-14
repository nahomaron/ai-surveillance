"""T-18 part C: register every held SDG run as one S0 artifact (data_origin synthetic_rendered). Statistics and IDs only.
Sources: member directories (`data/raw/sdg/members/<shard>/`) and the held shard 00538, whose RGB videos were extracted to
`data/derived/sdg_rgb_sample/` and whose camera parameters are read from the tar. Run lineage: `metadata/runs.parquet`.
retrieved_utc = the arrival time of the last SDG file of the holding (AR-52 item 6).
Writes the artifact to <out_dir> (git-ignored `out/`) and a summary (artifact ID, counts, cameras without calibration).
Usage: PYTHONPATH=src python s0_register_sdg.py <data_root> <out_dir> <summary.json>"""
import collections
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import av
import pyarrow.parquet as pq

from rq1.adapters import registration as reg
from rq1.adapters import sdg_camera
from rq1.ids.artifact import Spec, write_artifact
from rq1.registry.registrar import Registrar

RETRIEVED_UTC = datetime(2026, 11, 13, 1, 57, 47, tzinfo=timezone.utc)
HELD_TAR = "raw/sdg/artifacts/forklift_human_nearmiss/nearmiss-artifacts-00538.tar"
HELD_RGB = "derived/sdg_rgb_sample"
ROOT = Path(__file__).resolve().parents[3]


def video(root, rel):
    path = os.path.join(root, rel)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    with av.open(path) as c:
        codec = c.streams.video[0].codec_context.name
    return reg.Video(rel, h.hexdigest(), os.path.getsize(path), "mp4", codec)


def calibration(lines):
    return sdg_camera.calibration(sdg_camera.static_params([json.loads(l) for l in lines]))


def main():
    root, out_dir, summary_path = sys.argv[1], sys.argv[2], sys.argv[3]
    index = {r["run_id"]: r for r in pq.read_table(os.path.join(root, "raw/sdg/metadata/runs.parquet")).to_pylist()}
    cams = collections.defaultdict(dict)  # artifact run -> view -> (video, calibration)
    members = os.path.join(root, "raw/sdg/members")
    for shard in sorted(os.listdir(members)):
        d = os.path.join(members, shard)
        if not os.path.isdir(d):
            continue
        names = set(os.listdir(d))
        for n in sorted(names):
            if n.endswith(".rgb.mp4"):
                run, view = n.split(".")[:2]
                cp = f"{run}.{view}.camera_params.jsonl"
                cal = calibration(open(os.path.join(d, cp)).read().splitlines()) if cp in names else None
                cams[run][view] = (video(root, f"raw/sdg/members/{shard}/{n}"), cal)
    with tarfile.open(os.path.join(root, HELD_TAR)) as tf:
        tnames = {m.name: m for m in tf.getmembers()}
        for n in sorted(os.listdir(os.path.join(root, HELD_RGB))):
            if n.endswith(".rgb.mp4"):
                run, view = n.split(".")[:2]
                cp = f"{run}.{view}.camera_params.jsonl"
                cal = calibration(tf.extractfile(tnames[cp]).read().decode().splitlines()) if cp in tnames else None
                cams[run][view] = (video(root, f"{HELD_RGB}/{n}"), cal)
    runs = [reg.SdgRun(run, index[reg.rgb_run_id(run)], views) for run, views in sorted(cams.items())]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    built = Registrar().register(reg.sdg_metadata(runs, RETRIEVED_UTC), Spec("S0", "E-1.2.15", commit, env, (), (), {}))
    write_artifact(built, os.path.join(out_dir, built.artifact_id), "synthetic_rendered")
    t = built.tables
    calibrated = {c["camera_id"] for c in t["calibration"]}
    labels = {c["cam_id"]: c["camera_label"] for c in t["camera"]}
    summary = {"artifact_id": built.artifact_id, "payload_sha256": built.payload_sha256, "code_commit": commit,
               "retention_policy": {**reg.RETENTION_SYNTHETIC, "rtp_id": reg.retention_policy_id()},
               "rows": {name: len(rows) for name, rows in sorted(t.items())},
               "codecs": dict(collections.Counter(f["codec"] for f in t["source_file"])),
               "cameras_without_calibration": sorted(labels[c] for c in labels if c not in calibrated),
               "sessions": [{"ses_id": s["ses_id"], "ext_run_id": s["lineage"]["ext_run_id"], "seed": s["lineage"]["seed"],
                             "generation_batch": s["lineage"]["generation_batch"]} for s in sorted(t["session"], key=lambda s: s["session_label"])],
               "recordings": sorted([r["rec_id"], r["registration_label"]] for r in t["recording"])}
    # Index for the T17 driver (git-ignored, next to the artifact): one entry per recording.
    rec = {r["registration_label"]: r for r in t["recording"]}
    tl = {x["tl_id"]: x for x in t["timeline"]}
    index = []
    for run in runs:
        ext = reg.rgb_run_id(run.artifact_run)
        for view, (vid, cal) in sorted(run.cameras.items()):
            r = rec[f"{ext}.{view}"]
            held = vid.uri.startswith(HELD_RGB)
            index.append({"dataset": "sdg", "run": ext, "camera": view, "rec_id": r["rec_id"], "camera_id": r["camera_id"], "timeline": tl[r["timeline_id"]],
                          "uri": vid.uri, "calibration": cal, "s0": built.artifact_id,
                          "annotation": {"tar": HELD_TAR} if held else {"dir": os.path.dirname(vid.uri)}, "prefix": f"{run.artifact_run}.{view}"})
    json.dump(index, open(os.path.join(out_dir, "index.json"), "w"))
    json.dump(summary, open(summary_path, "w"), indent=1)
    print(json.dumps({k: summary[k] for k in ("artifact_id", "rows", "codecs", "cameras_without_calibration")}, indent=1))


if __name__ == "__main__":
    main()
