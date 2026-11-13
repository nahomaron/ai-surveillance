"""Download the SDG members of sdg_member_plan.json by exact byte ranges (D-24 a; Part 3 section 3.8).

Usage: python -I fetch_members.py <sdg_member_plan.json> <dest_root> <hash_log.json>
Each member is fetched as [data_offset, data_offset + size). A short or long body is retried (3 times), then reported.
The agent's own SHA-256 of every member is logged: integrity self_hashed_unverified_by_publisher. A member already on
disk with the planned size is re-hashed and kept. Members are written to <dest_root>/<shard>/<member name>."""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import urllib.request

PLAN, ROOT, LOG = sys.argv[1:4]
plan = json.load(open(PLAN))
URL = f"https://huggingface.co/datasets/{plan['source']}/resolve/{plan['revision']}/artifacts/forklift_human_nearmiss/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(job):
    shard, m = job
    dest = os.path.join(ROOT, shard, m["name"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    status = "present"
    if not (os.path.exists(dest) and os.path.getsize(dest) == m["size"]):
        status = "length_mismatch"
        for _ in range(3):
            req = urllib.request.Request(URL + shard, headers={"User-Agent": "rq1-qualification",
                                                               "Range": f"bytes={m['data_offset']}-{m['data_offset'] + m['size'] - 1}"})
            try:
                with urllib.request.urlopen(req, timeout=300) as r, open(dest + ".part", "wb") as f:
                    for block in iter(lambda: r.read(1 << 20), b""):
                        f.write(block)
            except Exception:  # noqa: BLE001 - retried
                continue
            if os.path.getsize(dest + ".part") == m["size"]:
                os.replace(dest + ".part", dest)
                status = "fetched"
                break
        if status != "fetched":
            if os.path.exists(dest + ".part"):
                os.remove(dest + ".part")
            return {"shard": shard, "name": m["name"], "size": m["size"], "data_offset": m["data_offset"], "status": status, "sha256": None}
    return {"shard": shard, "name": m["name"], "size": m["size"], "data_offset": m["data_offset"], "status": status, "sha256": sha256(dest)}


jobs = [(s["shard"], m) for s in plan["shards"] for m in s["members"]]
with cf.ThreadPoolExecutor(4) as ex:
    log = sorted(ex.map(fetch, jobs), key=lambda r: (r["shard"], r["name"]))
json.dump({"integrity": "self_hashed_unverified_by_publisher", "plan_sha256": sha256(PLAN), "members": log}, open(LOG, "w"), indent=1, sort_keys=True)
bad = [r for r in log if r["sha256"] is None]
print(f"{len(log)} members, {sum(r['size'] for r in log if r['sha256'])} bytes hashed, {len(bad)} failed")
