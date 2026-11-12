"""Append-only validation status log with a SHA-256 hash chain (E-1.2.1 section 5.8; CT-E-24)."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from rq1.schema.canonical import canonical_json
from rq1.schema.validate import Issue

GENESIS = "0" * 64  # AR-36


def _hash(entry: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json({k: v for k, v in entry.items() if k != "record_hash"})).hexdigest()


class StatusLog:
    """Entries are only appended. Status records never modify Observation-store artifacts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

    def append(self, *, target_type: str, target_id: str, config_id: str, status: str, layer: str, namespace: str, basis_ids: list[str],
               actor_id: str, created_utc: datetime) -> dict[str, Any]:
        entries = self._entries()
        entry = {"seq": len(entries), "status_id": f"sts_{uuid.uuid7()}", "target_type": target_type, "target_id": target_id, "config_id": config_id,
                 "status": status, "layer": layer, "namespace": namespace, "basis_ids": list(basis_ids), "actor_id": actor_id,
                 "created_utc": created_utc, "prev_hash": entries[-1]["record_hash"] if entries else GENESIS}
        entry["record_hash"] = _hash(entry)
        with open(self.path, "ab") as handle:
            handle.write(canonical_json(entry) + b"\n")
        return entry

    def verify(self) -> list[Issue]:
        issues, previous = [], GENESIS
        for k, entry in enumerate(self._entries()):
            if entry["seq"] != k or entry["prev_hash"] != previous or entry["record_hash"] != _hash(entry):
                issues.append(Issue("CT-E-24", "ERR-INVARIANT", "validation_status_log", "record_hash", f"chain broken at seq {k}"))
                break
            previous = entry["record_hash"]
        return issues
