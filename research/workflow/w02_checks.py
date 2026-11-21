"""W-02 (D-49 step 3): regression and reference-protection evidence, read-only.

  PYTHONPATH=src .venv/bin/python research/workflow/w02_checks.py <out.json>

- D-49.1 section 6.2 item 3: the reconstruction check (`ids.artifact.verify`, CT-FK-05 read-back) on every stored M1a
  and pilot artifact, under the E-1.2.23 schema.
- Section 6.2 item 4: every stored adjudication, assessment and status entry of every store under out/review/ validates
  under the E-1.2.23 reader without being rewritten; every hash chain verifies.
- Section 6.3: the stores, their batches and manifests; any batch target from a demo run; any batch annotator exposed
  under T23.25 (c); the T22-frame episodes left per summary label after excluding the demo runs, against T22.6 / T22.14 (e)
  for n_batch = 60.

Nothing is written under out/ (the SHA-256 of every file of every store is compared before and after). No stage runs, no
batch is drawn, no record is written.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rq1.ids import artifact  # noqa: E402
from rq1.review import protocol as P  # noqa: E402
from rq1.review.frame import SdgFrame  # noqa: E402
from rq1.review.registry import StoreRegistry, exposure_reasons, stores_summary  # noqa: E402
from rq1.schema import validate  # noqa: E402
from rq1.schema.errors import ContractError  # noqa: E402
from rq1.validation.reference import read_adjudication_row  # noqa: E402
from rq1.validation.status_log import StatusLog  # noqa: E402
from rq1.workflow.store import HashLog  # noqa: E402

REVIEW = ROOT / "out/review"
DEMO = REVIEW / "demo_20261119"


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x] if path.exists() else []


def digest(paths: list[Path]) -> dict[str, str]:
    out = {}
    for root in paths:
        if root.exists():
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def stores() -> list[Path]:
    """Every folder under out/review/ that holds V-02 or T23 records (registered or not)."""
    names = ("adjudication.jsonl", "reviewer_assessment.jsonl", "validation_status_log.jsonl", "wf_report_log.jsonl", "annotator.jsonl",
             "demo_manifest.json", "profiles.json")
    found = {p.parent for n in names for p in REVIEW.rglob(n)}
    return sorted(found)


def _verify_one(d: Path) -> tuple[str, str, str | None]:
    """(folder, status, message): status is pass, fail or skip (not an artifact folder)."""
    try:
        m = json.loads((d / "manifest.json").read_text())
    except ValueError:
        return str(d), "skip", None
    if "artifact_id" not in m or "artifact_spec_id" not in m:
        return str(d), "skip", None
    try:
        return (str(d), "pass", None) if artifact.verify(d) == m["artifact_id"] else (str(d), "fail", "different id")
    except (ContractError, OSError, KeyError, ValueError) as err:
        return str(d), "fail", str(err)[:200]


def readback(progress: Path | None = None) -> dict:
    """Section 6.2 item 3: every artifact folder (a manifest.json with an artifact_id) under out/m1a and out/m1b/pilot,
    checked in worker processes (read-only)."""
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    dirs = sorted({m.parent for base in (ROOT / "out/m1a", ROOT / "out/m1b/pilot") for m in base.rglob("manifest.json")})
    res = {"folders": len(dirs), "checked": 0, "passed": 0, "failed": [], "skipped_not_artifact": 0, "by_tree": {}}
    with ProcessPoolExecutor() as pool:
        for k, (d, status, msg) in enumerate(pool.map(_verify_one, dirs, chunksize=8), 1):
            if progress and k % 200 == 0:
                progress.write_text(f"{k}/{len(dirs)} {round(time.time() - t0)} s\n")
            if status == "skip":
                res["skipped_not_artifact"] += 1
                continue
            tree = str(Path(d).parent.relative_to(ROOT))
            res["by_tree"].setdefault(tree, [0, 0])
            res["checked"] += 1
            res["by_tree"][tree][0] += 1
            if status == "pass":
                res["passed"] += 1
                res["by_tree"][tree][1] += 1
            else:
                res["failed"].append([d, msg])
    res["seconds"] = round(time.time() - t0, 1)
    return res


def records(roots: list[Path]) -> list[dict]:
    """Section 6.2 item 4."""
    out = []
    for root in roots:
        r = {"store": str(root.relative_to(ROOT)), "adjudications": 0, "assessments": 0, "status_entries": 0, "report_log_entries": 0,
             "issues": [], "status_chain": None, "report_chain": None}
        for e in _jsonl(root / "adjudication.jsonl"):
            r["adjudications"] += 1
            try:
                row = read_adjudication_row(e["row"])
                issues = validate.validate_row("adjudication", row)
                if issues:
                    r["issues"].append(["adjudication", row["adj_id"], issues[0].rule, issues[0].message])
            except ContractError as err:
                r["issues"].append(["adjudication", e["row"].get("adj_id"), err.code, str(err)])
        for e in _jsonl(root / "reviewer_assessment.jsonl"):
            r["assessments"] += 1
            issues = validate.validate_row("reviewer_assessment", e["row"])
            if issues:
                r["issues"].append(["reviewer_assessment", e["row"]["rva_id"], issues[0].rule, issues[0].message])
        status = root / "validation_status_log.jsonl"
        if status.exists():
            entries = _jsonl(status)
            r["status_entries"] = len(entries)
            for e in entries:
                issues = validate.validate_row("validation_status_log", e)
                if issues:
                    r["issues"].append(["validation_status_log", e["status_id"], issues[0].rule, issues[0].message])
            r["status_chain"] = "intact" if not StatusLog(status).verify() else "BROKEN"
        log = root / "wf_report_log.jsonl"
        if log.exists():
            entries = _jsonl(log)
            r["report_log_entries"] = len(entries)
            for e in entries:
                issues = validate.validate_row("wf_report_log", e)
                if issues:
                    r["issues"].append(["wf_report_log", e["entry_id"], issues[0].rule, issues[0].message])
            v = HashLog(log, "wf_report_log").verify()
            r["report_chain"] = "intact" if not v else f"BROKEN: {v[0].message}"
        out.append(r)
    return out


def protection(roots: list[Path]) -> dict:
    """Section 6.3 items 1 and 3 (report only)."""
    real = StoreRegistry.default()
    view = StoreRegistry(ROOT / "out/review/.w02_view_registry_unused.json")  # never written: a read-only union of all stores
    view.roots = lambda: [r.resolve() for r in roots]  # type: ignore[method-assign]
    summary = stores_summary(real, roots)
    demo_recs = {r for s in summary for r in s["demo_recordings"]}
    people = {}
    for root in roots:
        people.update({a["anr_id"]: a["pseudonym"] for a in _jsonl(root / "annotator.jsonl")})
    for s in summary:
        for b in s["batches"]:
            b["targets_from_demo_runs"] = sorted(set(b["recordings"]) & demo_recs)
            b["exposed_annotators"] = []
            for a in b["annotators"] or []:
                who = people.get(a["annotator_id"], "?")
                reasons = sorted({x for rec in b["recordings"] for x in exposure_reasons(view, who, rec)})
                if reasons:
                    b["exposed_annotators"].append([a["annotator_id"], who, reasons])
            b["n_recordings"] = len(b.pop("recordings"))
            b["n_targets"] = len(b.pop("target_ids"))
        s["n_demo_recordings"] = len(s.pop("demo_recordings"))
    return {"registry": [str(p) for p in real.roots()], "stores": summary}


def frame_counts() -> dict:
    """Section 6.3 item 2: the BL-6 episodes of the T22 frame (T-21 oracle run, SDG validation) per summary label, all and
    after excluding every recording of the demo runs; T22.6 equal share and the T22.14 (e) water-filling for n_batch = 60."""
    frame = SdgFrame(ROOT, "BL-6")
    manifest = json.loads((DEMO / "demo_manifest.json").read_text())
    demo_recs = {r for run in manifest["runs"] for r in run["camera_rec_ids"]}
    eps = frame.episodes()
    count = lambda xs: {s: sum(1 for e in xs if e["stratum"] == s) for s in P.STRATA}
    before, after = count(eps), count([e for e in eps if e["recording_id"] not in demo_recs])
    n = P.PARAMS["n_batch"]
    present = [s for s in P.STRATA if after[s] > 0]
    share = n / len(present) if present else None
    # water-filling without the seed-dependent remainder: strata below the share are capped; report the capped strata and the
    # share the others receive (the integer remainder goes by largest remainder with ties broken by the batch seed)
    alloc_by_seed = {seed: P.allocate({s: after[s] for s in present}, n, seed) for seed in (0, 1, 2)}
    return {"configuration": "BL-6", "frame_run": "out/m1a/run1/sdg (T-21 oracle run)", "config_id": frame.config_id,
            "episodes_all": before, "episodes_after_excluding_demo_runs": after, "excluded_episodes": sum(before.values()) - sum(after.values()),
            "demo_runs": len(manifest["runs"]), "demo_recordings": len(demo_recs), "n_batch": n, "strata_present": present,
            "equal_share": share, "below_equal_share": [s for s in present if after[s] < share] if share else [],
            "water_filling_examples_seed_0_1_2": alloc_by_seed}


def main() -> None:
    out = Path(sys.argv[1])
    roots = stores()
    watched = [REVIEW]
    before = digest(watched)
    result = {"stores_found": [str(r.relative_to(ROOT)) for r in roots], "readback": readback(out.with_suffix(".progress")), "records": records(roots),
              "protection": protection(roots), "frame": frame_counts()}
    result["out_review_unchanged"] = digest(watched) == before
    out.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: result[k] for k in ("stores_found", "out_review_unchanged")}, indent=1))
    print(json.dumps({k: v for k, v in result["readback"].items() if k != "by_tree"}, indent=1))


if __name__ == "__main__":
    main()
