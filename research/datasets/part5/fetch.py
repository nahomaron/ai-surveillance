"""D-59 download (qualification Part 5): fetch the named files of candidates.json and check each against its SHA-256.

Usage: python -I fetch.py <candidates.json> <dest_root> <log.json> <kind> <scene>...
kind: `screen` (ground_truth.json, calibration.json, map.png) or `videos` (videos/*.mp4).
dest_root receives `MTMC_Tracking_2026/...` paths as published. A file already present with the right hash is skipped.
A mismatch is fetched once more; a second mismatch deletes the file and is reported. curl is used, not urllib
(urllib hung on this machine on 24 Nov 2026). Same rules as part3/fetch.py."""
import hashlib
import json
import os
import subprocess
import sys

URL = "https://huggingface.co/datasets/{repo}/resolve/{rev}/{path}"
SCREEN = ("ground_truth.json", "calibration.json", "map.png")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url, dest):
    tmp = dest + ".part"
    subprocess.run(["curl", "-sSfL", "--retry", "3", "-A", "rq1-qualification", "-o", tmp, url], check=True)
    os.replace(tmp, dest)


def wanted(f, kind):
    name = f["path"].rsplit("/", 1)[1]
    return name in SCREEN if kind == "screen" else f["path"].endswith(".mp4")


def main():
    cand, root, log_path, kind, scenes = (json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4],
                                          sys.argv[5:])
    log = json.load(open(log_path)) if os.path.exists(log_path) else []
    done = {x["path"] for x in log if x["status"] != "hash_mismatch_deleted"}
    for s in scenes:
        for f in cand["scenes"][s]["files"]:
            if not wanted(f, kind) or f["path"] in done:
                continue
            dest = os.path.join(root, f["path"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            status = "present"
            if not (os.path.exists(dest) and os.path.getsize(dest) == f["size"] and sha256(dest) == f["sha256"]):
                status = "fetched"
                for _ in range(2):
                    fetch(URL.format(repo=cand["source"], rev=cand["revision"], path=f["path"]), dest)
                    if os.path.getsize(dest) == f["size"] and sha256(dest) == f["sha256"]:
                        break
                    status = "refetched"
                else:
                    os.remove(dest)
                    status = "hash_mismatch_deleted"
            log.append({"path": f["path"], "size": f["size"], "sha256": f["sha256"], "status": status})
            json.dump(log, open(log_path, "w"), indent=1)
            print(status, f["path"], f["size"], flush=True)
    bad = [x for x in log if x["status"] == "hash_mismatch_deleted"]
    print(f"DONE {len(log)} files, {sum(x['size'] for x in log if x['status'] != 'hash_mismatch_deleted')} bytes,"
          f" {len(bad)} mismatches", flush=True)


if __name__ == "__main__":
    main()
