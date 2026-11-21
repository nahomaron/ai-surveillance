"""Appendix T T23.16 (contract E-1.2.23; D-49): the single way evaluation code obtains adjudications.

`reference_adjudications(store_root)` returns the stored adjudication rows with namespace = reference and
reference_class = independent_expert_judgment, excluding pilot targets (T23.16 e, T22.10 b, T22.14 d). Stored rows written
before E-1.2.23 have no reference_class_null_reason column; they are read with the reason null, which is valid only for a
reference row with a non-null class (T23.16 f). A stored candidate_review row without the reason is ERR-INVARIANT. No
stored row is rewritten.

`direct_read_violations(src_root)` is the static check of T23.16 (e): no module under src/rq1/evaluation/,
src/rq1/pipeline/ or src/rq1/review/protocol.py reads the adjudication or assessment files in any other way.

The store layout read here is the V-02 one (AR-61 item 5): JSONL envelopes {batch_id, recording_id, row} in
adjudication.jsonl; batch manifests in batches/<batch_id>/manifest.json; batch targets in batches/<batch_id>/targets.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rq1.schema import validate
from rq1.schema.errors import ContractError

EXPERT = "independent_expert_judgment"
REASON = "reference_class_null_reason"


def read_adjudication_row(row: dict[str, Any]) -> dict[str, Any]:
    """T23.16 (f): a stored row as the E-1.2.23 reader sees it (a copy; the stored row is never changed)."""
    if REASON in row:
        return dict(row)
    if row.get("namespace") == "reference" and row.get("reference_class") is not None:
        return {**row, REASON: None}
    raise ContractError("ERR-INVARIANT", f"stored adjudication {row.get('adj_id')} in namespace {row.get('namespace')!r} has no "
                                         f"{REASON} (T23.16 f: only a reference row with a class may omit it)")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _manifests(root: Path) -> dict[str, dict[str, Any]]:
    folder = root / "batches"
    if not folder.exists():
        return {}
    return {p.name: json.loads((p / "manifest.json").read_text(encoding="utf-8"))
            for p in sorted(folder.iterdir()) if (p / "manifest.json").exists()}


def stored_adjudications(store_root: str | Path) -> list[dict[str, Any]]:
    """Every stored adjudication envelope, its row read under T23.16 (f). For the V-02 store itself, not for evaluation."""
    out = []
    for e in _jsonl(Path(store_root) / "adjudication.jsonl"):
        out.append({**e, "row": read_adjudication_row(e["row"])})
    return out


def reference_adjudications(store_root: str | Path) -> list[dict[str, Any]]:
    """T23.16 (e): reference rows with reference_class = independent_expert_judgment, pilot targets excluded, in stored order.
    Every returned row passes the E-1.2.23 row validator (VR-E-056 included)."""
    root = Path(store_root)
    manifests = _manifests(root)
    pilot_batches = {b for b, m in manifests.items() if m.get("pilot")}
    pilot_targets = {t for b in pilot_batches for t in manifests[b].get("target_ids", [])}
    out = []
    for e in stored_adjudications(root):
        row = e["row"]
        if row["namespace"] != "reference" or row["reference_class"] != EXPERT:
            continue
        if e.get("batch_id") in pilot_batches or row["target_id"] in pilot_targets:
            continue
        issues = validate.validate_row("adjudication", row)
        if issues:
            raise ContractError(issues[0].code or "ERR-INVARIANT", f"stored adjudication {row['adj_id']}: {issues[0].message}")
        out.append(row)
    return out


G2_MAP = {"lbl_nm": "nm", "lbl_ud": "ud", "lbl_ct": "ct"}  # T22.8 (b)


def ev_m12_population(store_root: str | Path) -> dict[str, Any]:
    """The EV-M12 input population of T22.10 (b), from `reference_adjudications` only: the current (latest) adjudication per
    target, paired with the mapped system label; a final `unsure` is counted separately and is not paired. This is the
    population, not a metric result."""
    root = Path(store_root)
    targets: dict[str, dict[str, Any]] = {}
    for b in _manifests(root):
        path = root / "batches" / b / "targets.json"
        if path.exists():
            targets.update(json.loads(path.read_text(encoding="utf-8")))
    current: dict[str, dict[str, Any]] = {}
    for row in reference_adjudications(root):
        current[row["target_id"]] = row
    pairs, unsure = [], 0
    for tid in sorted(current):
        row = current[tid]
        if row["final_label"] == "unsure":
            unsure += 1
            continue
        mapped = G2_MAP.get((targets.get(tid) or {}).get("g2_label"), "not_hazardous")
        pairs.append({"target_id": tid, "final_label": row["final_label"], "system_label": mapped, "tier": row["tier"]})
    return {"pairs": pairs, "unsure": unsure}


# --- T23.16 (e) static check ---------------------------------------------------------------------------------------------

SCANNED = ("rq1/evaluation", "rq1/pipeline", "rq1/review/protocol.py")
_DIRECT = re.compile(r"adjudication\.jsonl|reviewer_assessment\.jsonl|\.adjudications\(|\.assessments\(")


def direct_read_violations(src_root: str | Path) -> list[tuple[str, int, str]]:
    """(path, line number, line) of every direct read of the adjudication or assessment files in the scanned modules.
    Paths that do not exist (on a branch without them) are skipped."""
    root = Path(src_root)
    files: list[Path] = []
    for part in SCANNED:
        p = root / part
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files += sorted(p.rglob("*.py"))
    out = []
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if _DIRECT.search(line):
                out.append((str(f), n, line.strip()))
    return out
