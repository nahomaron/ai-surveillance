"""X0a/X0b split freeze, X0c leakage audit, PR-01 revision and the R-2 gate (E-1.2.1 section 8; Appendix T SP)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from rq1.schema.errors import ContractError
from rq1.schema.validate import Issue

from . import leakage

Row = dict[str, Any]
ORDER = {"train": 0, "validation": 1, "test": 2}  # PR-01: train is the least evaluative
VALIDATION_STAGES = {"V0", "V1", "V2", "V3", "V4", "CV-SIM", "X0c"}


def _assignment(split: Row) -> dict[str, str]:
    return {a["leakage_group_id"]: a["partition"] for a in split["assignments"]}


def recording_partitions(split: Row) -> dict[str, str]:
    assigned = _assignment(split)
    return {r: assigned[g["leakage_group_id"]] for g in split["leakage_groups"] for r in g["member_recording_ids"]}


def _group_of(split: Row) -> dict[str, str]:
    return {r: g["leakage_group_id"] for g in split["leakage_groups"] for r in g["member_recording_ids"]}


def freeze(recordings: list[Row], split_label: str, version: str, tier: str, frozen_utc: datetime, t2b_shared_sessions: list[str] | None = None,
           shared_scene_content: bool = False, training_recordings: tuple[str, ...] = (), training_manifest_hashes: tuple[str, ...] = ()) -> Row:
    """`SplitBuilder.freeze`. Partitions are declared per recording (AR-32); conflicts within a group raise ERR-LEAKAGE."""
    if tier == "T2b" and not shared_scene_content:
        raise ContractError("ERR-LEAKAGE", "T2b requires shared_scene_content = true")
    shared = set(t2b_shared_sessions or []) if tier == "T2b" else set()
    edges = leakage.metadata_edges(recordings, shared)
    trained = sorted(training_recordings)
    edges += [(a, b, "training_use") for a, b in zip(trained, trained[1:])]
    declared = {r["recording_id"]: r["partition"] for r in recordings}
    groups, assignments = [], []
    for members, kinds in leakage.components(sorted(declared), edges):
        partitions = sorted({declared[m] for m in members}, key=ORDER.get)
        if len(partitions) > 1:
            raise ContractError("ERR-LEAKAGE", f"VR-E-060: group {members} spans {partitions}")
        if set(members) & set(trained) and partitions != ["train"]:
            raise ContractError("ERR-LEAKAGE", "a recording used for training is outside the train partition")
        gid = leakage.group_id(members)
        groups.append({"leakage_group_id": gid, "member_recording_ids": members, "edge_types": kinds})
        assignments.append({"leakage_group_id": gid, "partition": partitions[0]})
    if tier == "T2b":
        sessions: dict[str, set[str]] = {}
        for r in recordings:
            sessions.setdefault(r["session_id"], set()).add(declared[r["recording_id"]])
        undeclared = sorted(s for s, p in sessions.items() if len(p) > 1 and s not in shared)
        if undeclared:
            raise ContractError("ERR-LEAKAGE", f"VR-E-060: undeclared shared sessions {undeclared}")
    return {"split_label": split_label, "version": version, "parent_version_id": None, "parent_version_id_null_reason": "not_applicable",
            "basis": "metadata_only", "tier": tier, "leakage_groups": groups, "assignments": assignments,
            "t2b_shared_sessions": sorted(shared) if tier == "T2b" else None, "t2b_shared_sessions_null_reason": None if tier == "T2b" else "not_applicable",
            "shared_scene_content": shared_scene_content, "training_manifest_hashes": list(training_manifest_hashes), "frozen_utc": frozen_utc,
            "revision": None, "revision_null_reason": "not_applicable"}


def _merged(split: Row, edges: list[Row]) -> list[tuple[list[str], list[str]]]:
    group_of = _group_of(split)
    nodes = sorted({g["leakage_group_id"] for g in split["leakage_groups"]})
    links = [(group_of[e["recording_a"]], group_of[e["recording_b"]], e["edge_type"]) for e in edges
             if e["recording_a"] in group_of and e["recording_b"] in group_of]
    return leakage.components(nodes, links)


def audit(split: Row, split_id: str, identities: list[Row], discovery_basis: str, audit_seq: int, recordings: list[Row] | None = None,
          audit_complete: bool = True) -> Row:
    """`LeakageAuditor.audit` (X0c). Under T2b, edges inside a declared shared session are expected and not recorded."""
    session = {r["recording_id"]: r["session_id"] for r in recordings or []}
    shared = set(split["t2b_shared_sessions"] or [])
    edges = [e for e in identities if not (session.get(e["recording_a"]) in shared and session.get(e["recording_a"]) == session.get(e["recording_b"]))]
    assigned = _assignment(split)
    violations = []
    for members, _ in _merged(split, edges):
        partitions = sorted({assigned[m] for m in members}, key=ORDER.get)
        if len(partitions) > 1:
            violations.append({"leakage_group_id": leakage.group_id(members), "partitions": partitions})
    return {"split_version_id": split_id, "audit_seq": audit_seq, "tier": split["tier"], "edges_added": [dict(e) for e in edges],
            "violations": violations, "discovery_basis": discovery_basis, "audit_complete": audit_complete}


def revise(split: Row, split_id: str, audit: Row, audit_id: str, frozen_utc: datetime) -> Row:
    """`SplitBuilder.revise`: PR-01 only. Takes no metric, label or system output (SP-07, R-4)."""
    if not audit["violations"]:
        raise ContractError("ERR-INVARIANT", "SP-03: a revision needs a triggering audit with at least one violation")
    assigned = _assignment(split)
    members_of = {g["leakage_group_id"]: g for g in split["leakage_groups"]}
    groups, assignments, moved = [], [], []
    for merged, kinds in _merged(split, audit["edges_added"]):
        target = min((assigned[m] for m in merged), key=ORDER.get)
        moved += [m for m in merged if assigned[m] != target]
        recordings = sorted(r for m in merged for r in members_of[m]["member_recording_ids"])
        types = sorted(set(kinds) | {t for m in merged for t in members_of[m]["edge_types"]})
        gid = merged[0] if len(merged) == 1 else leakage.group_id(recordings)
        groups.append({"leakage_group_id": gid, "member_recording_ids": recordings, "edge_types": types})
        assignments.append({"leakage_group_id": gid, "partition": target})
    return {**split, "version": str(int(split["version"]) + 1), "parent_version_id": split_id, "parent_version_id_null_reason": None,
            "basis": "metadata_plus_reference_identity", "leakage_groups": groups, "assignments": assignments, "frozen_utc": frozen_utc,
            "revision": {"audit_id": audit_id, "moved_groups": sorted(moved), "rule": "PR-01"}, "revision_null_reason": None}


def affected_strata(windows: list[Row], old: Row, new: Row, audit: Row) -> set[str]:
    """R-3: test strata whose windows left the test partition after a `sampled_annotation` discovery."""
    if audit["discovery_basis"] != "sampled_annotation":
        return set()
    before, after = recording_partitions(old), recording_partitions(new)
    return {w["stratum_id"] for w in windows
            if any(before.get(r) == "test" and after.get(r) != "test" for r in w["recording_ids"])}


def invalidate_results(results: list[Row], old: Row, new: Row) -> list[Row]:
    """CT-S-02: earlier S8 results on a partition that lost recordings become `invalidated_leakage`."""
    before, after = recording_partitions(old), recording_partitions(new)
    affected = {before[r] for r in before if before[r] != after.get(r)} - {"train"}
    return [{**r, "validity": "invalidated_leakage"} if r["slice"].get("partition") in affected else dict(r) for r in results]


def check_s8_allowed(partition: str, split: Row, audits: list[Row], run_start: datetime) -> None:
    """R-2 and SP-08 (reads the event-time column `frozen_utc`, AR-7 as revised)."""
    if partition != "test":
        return
    if not split["frozen_utc"] < run_start:
        raise ContractError("ERR-AUDIT-PENDING", "split frozen after the S8 run started")
    latest = max(audits, key=lambda a: a["audit_seq"], default=None)
    if latest is None or not latest["audit_complete"]:
        raise ContractError("ERR-AUDIT-PENDING", "S8 on test before the latest audit is complete (R-2)")


def check_sp_01(inputs: list[Row], validation_times: list[datetime], frozen_utc: datetime) -> list[Issue]:
    """SP-01: split v1 has no Validation-store inputs and is frozen before any Validation-store record."""
    issues = [Issue("SP-01", "ERR-LEAKAGE", "split_manifest", "inputs", f"Validation-store input {i['stage']}") for i in inputs if i["stage"] in VALIDATION_STAGES]
    issues += [Issue("SP-01", "ERR-LEAKAGE", "split_manifest", "frozen_utc", "a Validation-store record precedes the split freeze") for t in validation_times if t < frozen_utc]
    return issues
