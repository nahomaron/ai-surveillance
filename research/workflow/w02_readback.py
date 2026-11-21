"""W-02 section 6.2 item 3 (D-49.1), rerun under D-51 STEP 2: the reconstruction check (`ids.artifact.verify`, CT-FK-05
read-back) on every stored M1a and pilot artifact folder, resumable and memory-safe. Read-only.

  PYTHONPATH=src .venv/bin/python research/workflow/w02_readback.py            # run or resume
  PYTHONPATH=src .venv/bin/python research/workflow/w02_readback.py --summary  # totals from the JSONL only

- The folders are every directory holding a manifest.json under out/m1a and out/m1b/pilot, sorted.
- A parent process starts one worker process per chunk of CHUNK folders. A worker checks one folder at a time, releases
  it (gc) and appends one JSONL line per folder to research/workflow/w02_readback.jsonl (flushed and fsynced), so a
  crash or shutdown loses at most the folder being checked. Recycling the worker bounds memory growth.
- On restart, folders already recorded are skipped.
- Line: {"folder", "artifact_id", "result": pass | fail | skip, "error", "max_rss_mb"}. skip = the manifest has no
  artifact_id / artifact_spec_id (not an artifact folder); max_rss_mb = the worker's peak resident memory so far.

Nothing under out/ is written. No stage runs.
"""
from __future__ import annotations

import gc
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "research/workflow/w02_readback.jsonl"
TREES = (ROOT / "out/m1a", ROOT / "out/m1b/pilot")
CHUNK = 100


def _mb(rss: int) -> float:
    return round(rss / (1024 * 1024 if sys.platform == "darwin" else 1024), 1)  # bytes on macOS, KiB on Linux


def folders() -> list[str]:
    return sorted({str(m.parent.relative_to(ROOT)) for base in TREES for m in base.rglob("manifest.json")})


def recorded() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue  # a line cut by a shutdown: its folder is checked again
            out[row["folder"]] = row
    return out


def check(folder: str) -> dict:
    from rq1.ids import artifact
    from rq1.schema.errors import ContractError
    d = ROOT / folder
    row = {"folder": folder, "artifact_id": None, "result": None, "error": None}
    try:
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        row.update(result="fail", error=f"manifest unreadable: {err}"[:300])
        return row
    if not isinstance(m, dict) or "artifact_id" not in m or "artifact_spec_id" not in m:
        row["result"] = "skip"
        return row
    row["artifact_id"] = m["artifact_id"]
    try:
        got = artifact.verify(d)
        row.update(result="pass") if got == m["artifact_id"] else row.update(result="fail", error=f"different id {got}")
    except (ContractError, OSError, KeyError, ValueError) as err:
        row.update(result="fail", error=f"{type(err).__name__}: {err}"[:300])
    return row


def worker(names: list[str]) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    with open(LOG, "a", encoding="utf-8") as out:
        for name in names:
            row = check(name)
            gc.collect()
            row["max_rss_mb"] = _mb(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
            os.fsync(out.fileno())


def summary() -> dict:
    rows = recorded()
    allf = folders()
    res = {"folders": len(allf), "recorded": sum(1 for f in allf if f in rows)}
    for k in ("pass", "fail", "skip"):
        res[k] = sum(1 for f in allf if rows.get(f, {}).get("result") == k)
    res["failures"] = [[f, rows[f]["error"]] for f in allf if rows.get(f, {}).get("result") == "fail"]
    res["peak_worker_rss_mb"] = max((r.get("max_rss_mb") or 0 for r in rows.values()), default=None)
    res["by_tree"] = {}
    for f in allf:
        if f in rows and rows[f]["result"] != "skip":
            t = str(Path(f).parent)
            n = res["by_tree"].setdefault(t, [0, 0])
            n[0] += 1
            n[1] += rows[f]["result"] == "pass"
    return res


def main() -> None:
    if "--worker" in sys.argv:
        return worker(json.loads(sys.stdin.read()))
    if "--summary" in sys.argv:
        print(json.dumps(summary(), indent=1))
        return
    t0 = time.time()
    todo = [f for f in folders() if f not in recorded()]
    print(f"{len(todo)} folders to check", flush=True)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    for k in range(0, len(todo), CHUNK):
        chunk = todo[k:k + CHUNK]
        p = subprocess.run([sys.executable, __file__, "--worker"], input=json.dumps(chunk), text=True, env=env)
        if p.returncode != 0:
            print(f"worker exited {p.returncode} at chunk {k // CHUNK}; rerun to resume", flush=True)
            sys.exit(p.returncode)
        print(f"{min(k + CHUNK, len(todo))}/{len(todo)} {round(time.time() - t0)} s; peak child RSS "
              f"{_mb(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)} MB", flush=True)
    s = summary()
    s["seconds_this_run"] = round(time.time() - t0, 1)
    s["peak_child_rss_mb_this_run"] = _mb(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    print(json.dumps({k: v for k, v in s.items() if k != "by_tree"}, indent=1))


if __name__ == "__main__":
    main()
