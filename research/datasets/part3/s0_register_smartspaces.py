"""T-18: register the SmartSpaces synthetic scenes, one S0 artifact per scene (CR-020 option (a): one dataset_source per
data_origin, version label `<edition>@<revision>/<data_origin>`; VR-E-005 one origin per file). IDs and counts only.
Warehouse_000: synthetic_rendered. Warehouse_001: synthetic_transferred, render parent Warehouse_000 (qualification 2.4).
retrieved_utc = the arrival time of the last file of the two scenes.
Usage: PYTHONPATH=src python s0_register_smartspaces.py <data_root> <out_dir> <summary.json>"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import av

from rq1.adapters import registration as reg
from rq1.adapters import smartspaces
from rq1.ids.artifact import Spec, write_artifact
from rq1.registry.registrar import Registrar

RETRIEVED_UTC = datetime(2026, 11, 12, 16, 48, 36, tzinfo=timezone.utc)
BASE = "raw/smartspaces/MTMC_Tracking_2026/train"
SCENES = [("Warehouse_000", "synthetic_rendered", None), ("Warehouse_001", "synthetic_transferred", "Warehouse_000")]
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


def main():
    root, out_dir, summary_path = sys.argv[1], sys.argv[2], sys.argv[3]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    registrar, index, summary = Registrar(), [], {"code_commit": commit, "scenes": []}
    for name, origin, parent in SCENES:
        cals = smartspaces.calibrations(smartspaces.load(os.path.join(root, BASE, name, "calibration.json")))
        cams = {}
        for n in sorted(os.listdir(os.path.join(root, BASE, name, "videos"))):
            if n.endswith(".mp4"):
                cams[n[:-4]] = (video(root, f"{BASE}/{name}/videos/{n}"), cals.get(n[:-4]))
        built = registrar.register(reg.smartspaces_metadata(reg.SmartSpacesScene(name, origin, parent, cams), RETRIEVED_UTC),
                                   Spec("S0", "E-1.2.15", commit, env, (), (), {}))
        write_artifact(built, os.path.join(out_dir, built.artifact_id), origin)
        t = built.tables
        rec = {r["registration_label"]: r for r in t["recording"]}
        tl = {x["tl_id"]: x for x in t["timeline"]}
        for cam, (vid, cal) in sorted(cams.items()):
            r = rec[f"{name}.{cam}"]
            index.append({"dataset": "smartspaces", "run": name, "camera": cam, "rec_id": r["rec_id"], "camera_id": r["camera_id"],
                          "timeline": tl[r["timeline_id"]], "uri": vid.uri, "calibration": cal, "s0": built.artifact_id,
                          "annotation": {"ground_truth": f"{BASE}/{name}/ground_truth.json"}})
        summary["scenes"].append({"scene": name, "artifact_id": built.artifact_id, "payload_sha256": built.payload_sha256, "data_origin": origin,
                                  "dataset_version": t["dataset_source"][0]["version"], "dsr_id": t["dataset_source"][0]["dsr_id"],
                                  "rows": {k: len(v) for k, v in sorted(t.items())}, "lineage": t["session"][0]["lineage"],
                                  "cameras_without_calibration": sorted(c for c, (_, cal) in cams.items() if cal is None),
                                  "recordings": sorted([r["rec_id"], r["registration_label"]] for r in t["recording"])})
    json.dump(index, open(os.path.join(out_dir, "index.json"), "w"))
    json.dump(summary, open(summary_path, "w"), indent=1)
    print(json.dumps([{k: s[k] for k in ("scene", "artifact_id", "data_origin", "dataset_version", "rows", "cameras_without_calibration")} for s in summary["scenes"]], indent=1))


if __name__ == "__main__":
    main()
