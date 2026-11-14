"""T-18 / T16: register the real SmartSpaces scenes Warehouse_026 and Warehouse_027 under the real row
(`…/real_staged`), D-24 b and D-26 conditions unchanged: reference-free checks only, no annotation, VR-E-070 pending values.
SHA-256 and size come from the download log (each file was checked against the publisher's hash at download); the size on
disk is compared without reading the file. The only read of a video is the codec probe (container header), and every
read is appended to the access log (qualification 3.5). IDs and counts only; no frame is decoded.
retrieved_utc = the arrival time of the last file of the two scenes.
Usage: PYTHONPATH=src python s0_register_smartspaces_real.py <data_root> <out_dir> <summary.json>"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import av

from rq1.adapters import registration as reg
from rq1.ids import core
from rq1.ids.artifact import Spec, write_artifact
from rq1.registry.access_log import AccessLog
from rq1.registry.registrar import Registrar
from rq1.schema import vr_rules

RETRIEVED_UTC = datetime(2026, 11, 13, 0, 58, 22, tzinfo=timezone.utc)
BASE = "raw/real/smartspaces"
SCENES = ("Warehouse_026", "Warehouse_027")
ROOT = Path(__file__).resolve().parents[3]


def main():
    root, out_dir, summary_path = sys.argv[1], sys.argv[2], sys.argv[3]
    fetched = {f["path"]: f for f in json.load(open(os.path.join(root, BASE, "fetch_log.json"))) if f["status"] == "fetched"}
    log = AccessLog(os.path.join(root, "derived/real/access_log.jsonl"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    registrar, summary = Registrar(), {"code_commit": commit, "retention_policy": {**reg.RETENTION_REAL, "rtp_id": reg.retention_policy_id(reg.RETENTION_REAL)},
                                       "approvals_ref": reg.APPROVALS_REF_D26, "scenes": []}
    for name in SCENES:
        cams = {}
        for rel, f in sorted(fetched.items()):
            if rel.startswith(f"test/{name}/videos/") and rel.endswith(".mp4"):
                path = os.path.join(root, BASE, rel)
                if os.path.getsize(path) != f["size"]:
                    raise SystemExit(f"{rel}: size on disk differs from the download log")
                log.append("implementation-agent", "read", core.source_id(f["sha256"]), "S0 registration: codec probe (container header)", datetime.now(timezone.utc))
                with av.open(path) as c:
                    codec = c.streams.video[0].codec_context.name
                cams[os.path.basename(rel)[:-4]] = reg.Video(f"{BASE}/{rel}", f["sha256"], f["size"], "mp4", codec)
        built = registrar.register(reg.smartspaces_real_metadata(name, cams, RETRIEVED_UTC), Spec("S0", "E-1.2.15", commit, env, (), (), {}))
        write_artifact(built, os.path.join(out_dir, built.artifact_id), "real_staged")
        t = built.tables
        issues = vr_rules.check_retention(t["source_file"], {f["src_id"] for f in t["source_file"]}, {reg.retention_policy_id(reg.RETENTION_REAL)}, [])
        if issues:
            raise SystemExit(f"VR-E-070: {issues}")
        summary["scenes"].append({"scene": name, "artifact_id": built.artifact_id, "payload_sha256": built.payload_sha256, "data_origin": "real_staged",
                                  "dataset_version": t["dataset_source"][0]["version"], "dsr_id": t["dataset_source"][0]["dsr_id"],
                                  "rows": {k: len(v) for k, v in sorted(t.items())}, "codecs": sorted({f["codec"] for f in t["source_file"]}),
                                  "recordings": sorted([r["rec_id"], r["registration_label"]] for r in t["recording"])})
    summary["access_log"] = {"entries": len(log.entries()), "chain_ok": log.verify(), "last_record_hash": log.entries()[-1]["record_hash"]}
    json.dump(summary, open(summary_path, "w"), indent=1)
    print(json.dumps([{k: s[k] for k in ("scene", "artifact_id", "dataset_version", "rows", "codecs")} for s in summary["scenes"]] + [summary["access_log"]], indent=1))


if __name__ == "__main__":
    main()
