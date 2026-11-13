"""Download the files of a Part 3 selection list and check each against its published SHA-256 (D-24).

Usage: python -I fetch.py <selection.json> <dest_root>
A file that already exists with the right hash is skipped. A mismatch is fetched once more; a second mismatch deletes the
file and is reported. Prints one summary line; writes <dest_root>/fetch_log.json (path, size, sha256, status)."""
import hashlib
import json
import os
import sys
import urllib.request

HF = {"nvidia/PhysicalAI-SmartSpaces": "https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/resolve/{rev}/{path}"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url, dest):
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "rq1-qualification"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        for block in iter(lambda: r.read(1 << 20), b""):
            f.write(block)
    os.replace(tmp, dest)


def main():
    sel, root = json.load(open(sys.argv[1])), sys.argv[2]
    log = []
    for item in sel["files"]:
        if "file_id" in item:  # Mendeley
            url, rel = sel["download_url_template"].format(file_id=item["file_id"]), item["path"]
        else:
            url = HF[sel["source"]].format(rev=sel["revision"], path=item["path"])
            rel = item["path"].split("MTMC_Tracking_2026/", 1)[1]
        dest = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        status = "present"
        if not (os.path.exists(dest) and os.path.getsize(dest) == item["size"] and sha256(dest) == item["sha256"]):
            status = "fetched"
            for attempt in range(2):
                fetch(url, dest)
                if sha256(dest) == item["sha256"]:
                    break
                status = "refetched"
            else:
                os.remove(dest)
                status = "hash_mismatch_deleted"
        log.append({"path": rel, "size": item["size"], "sha256": item["sha256"], "status": status})
    json.dump(log, open(os.path.join(root, "fetch_log.json"), "w"), indent=1)
    bad = [x for x in log if x["status"] == "hash_mismatch_deleted"]
    print(f"{len(log)} files, {sum(x['size'] for x in log)} bytes, {len(bad)} mismatches")


if __name__ == "__main__":
    main()
