"""D-59 candidate list: every non-depth file of the SmartSpaces 2026 scenes named in qualification Part 5 (5.3).

Usage: python -I candidates.py <out.json>
Reads the public Hub tree at the pinned revision (metadata only, no data file). Records path, size and Git-LFS SHA-256
of each file. Depth maps are left out (size; Part 1). Also records each scene's map.png and ground_truth.json hashes,
which identify layouts and re-renders (5.2)."""
import json
import sys
import subprocess

REPO = "nvidia/PhysicalAI-SmartSpaces"
REV = "d38193be60906679124732a4be9a6516821e2bed"
TIER1 = ["008", "009", "010", "011", "012", "013", "014", "015", "016", "017", "018", "019", "022"]
TIER2 = ["002", "004", "006", "020"]
SPLIT = {s: ("val" if int(s) >= 20 else "train") for s in TIER1 + TIER2}


def tree(path):
    url = f"https://huggingface.co/api/datasets/{REPO}/tree/{REV}/{path}?recursive=true"
    # curl, not urllib: urllib hung on this machine on 24 Nov 2026 (no connection opened); curl answered in < 1 s.
    out = subprocess.run(["curl", "-sSf", "-m", "120", "-A", "rq1-qualification", url], check=True,
                         capture_output=True).stdout
    return json.loads(out)


def main():
    scenes = {}
    for s in TIER1 + TIER2:
        print("listing", s, file=sys.stderr, flush=True)
        base = f"MTMC_Tracking_2026/{SPLIT[s]}/Warehouse_{s}"
        files = []
        for x in tree(base):
            if x["type"] != "file" or "depth" in x["path"].lower():
                continue
            sha = x["lfs"]["oid"] if "lfs" in x else None
            files.append({"path": x["path"], "size": x["size"], "sha256": sha, "git_oid": x["oid"]})
        files.sort(key=lambda f: f["path"])
        by = {f["path"].rsplit("/", 1)[1]: f for f in files}
        scenes[f"Warehouse_{s}"] = {
            "tier": 1 if s in TIER1 else 2, "split": SPLIT[s],
            "videos": sum(f["path"].endswith(".mp4") for f in files),
            "bytes": sum(f["size"] for f in files),
            "map_sha256": by["map.png"]["sha256"], "ground_truth_sha256": by["ground_truth.json"]["sha256"],
            "files": files,
        }
    out = {"source": REPO, "revision": REV, "scenes": scenes}
    json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True)
    for k, v in scenes.items():
        print(k, v["tier"], v["videos"], v["bytes"], v["map_sha256"][:10], v["ground_truth_sha256"][:10])


if __name__ == "__main__":
    main()
