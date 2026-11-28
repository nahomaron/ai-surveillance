"""D-63 STEP 6 (T-29h): verify that a returned Colab S2 output folder is complete and unaltered, by hashes only.

D-63 ruling 8: the test S2 output is hashed on arrival and otherwise left untouched. This module reads only the
bookkeeping the runner writes (`colab_manifest.json`, the `.done.json` sidecars: hashes, sizes, frame counts, timings,
environment) and the raw bytes of each `.json.gz` for SHA-256. It never decompresses or parses an output file, and
it reports no detection content.

Usage:
  PYTHONPATH=src .venv/bin/python research/colab/arrival.py --job research/colab/test_manifest.json \
      --out out/colab/test --record docs/preregistration/test_s2_arrival_v2.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rq1_colab import access

MANIFEST = "colab_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(job_path: Path, out: Path) -> dict:
    problems: list[str] = []
    job_sha = sha256(job_path)
    job = json.loads(job_path.read_text())
    access.refuse_manifest(job)
    m = json.loads((out / MANIFEST).read_text())
    cams = {c["rec_id"]: c for c in job["cameras"]}

    if m.get("job") != job.get("job"):
        problems.append(f"job name {m.get('job')!r} != {job.get('job')!r}")
    if m.get("job_manifest_sha256") != job_sha:
        problems.append("colab_manifest job_manifest_sha256 differs from the job manifest's SHA-256")
    if m.get("complete") is not True or m.get("cameras_finished") != len(cams) or m.get("cameras_in_job") != len(cams):
        problems.append("colab_manifest does not report a complete job")
    want_w = {k: v["sha256"] for k, v in job.get("detector", {}).get("weights", {}).items()}
    if m.get("weights_sha256") != want_w:
        problems.append("weights SHA-256 differ from the job's detector block")

    listed = {f["rec_id"]: f for f in m.get("files", [])}
    if set(listed) != set(cams):
        problems.append(f"manifest files: {len(set(cams) - set(listed))} missing, {len(set(listed) - set(cams))} extra")
    on_disk = {p.name for p in out.glob("*.json.gz")}
    expected = {f"{r}.json.gz" for r in cams}
    if on_disk != expected:
        problems.append(f"output files on disk: {len(expected - on_disk)} missing, {len(on_disk - expected)} extra")
    sidecars = {p.name for p in out.glob("*.done.json")}
    if sidecars != {f"{r}.done.json" for r in cams}:
        problems.append("sidecar set differs from the job's cameras")

    files = []
    for rec in sorted(cams):
        cam, gz, done = cams[rec], out / f"{rec}.json.gz", out / f"{rec}.done.json"
        if not gz.exists() or not done.exists():
            continue
        digest, size = sha256(gz), gz.stat().st_size
        side = json.loads(done.read_text())
        entry = listed.get(rec, {})
        for name, src in (("sidecar", side), ("manifest", entry)):
            if src.get("sha256") != digest or src.get("bytes") != size:
                problems.append(f"{rec}: {name} hash/size differs from the file")
            if src.get("frames") != cam["n_eligible"] or src.get("n_eligible") != cam["n_eligible"]:
                problems.append(f"{rec}: {name} frame count differs from the job's n_eligible")
            if src.get("input_sha256") != cam["sha256"]:
                problems.append(f"{rec}: {name} input video hash differs from the job")
        files.append({"rec_id": rec, "file": gz.name, "sha256": digest, "bytes": size})

    return {"job": job.get("job"), "decision": job.get("decision"), "job_manifest": str(job_path),
            "job_manifest_sha256": job_sha, "colab_manifest_sha256": sha256(out / MANIFEST),
            "runner_commit": m.get("environment", {}).get("runner_commit"),
            "device_name": m.get("environment", {}).get("device_name"),
            "pip_freeze": {p.name: sha256(p) for p in sorted(out.glob("pip_freeze_*.txt"))},
            "cameras_verified": len(files), "pass": not problems, "problems": problems, "files": files}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--record")
    a = ap.parse_args(argv)
    r = verify(Path(a.job), Path(a.out))
    if a.record:
        rec = {"record": "D-63 STEP 6 arrival of sealed Colab S2 output (hashes only; outputs not opened)",
               "verified_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **r}
        Path(a.record).write_text(json.dumps(rec, indent=1) + "\n")
    print("PASS" if r["pass"] else "FAIL", r["cameras_verified"], "output files hashed")
    for p in r["problems"]:
        print("  -", p)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
