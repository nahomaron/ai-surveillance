"""Append-only access log for real-origin files, with a SHA-256 hash chain (E-1.2.1 Gov table `access_log`; VR-E-070;
qualification 3.5: every read, export and delete of real-origin files is appended). Same chain form as the validation
status log (AR-36 item 1): the first `prev_hash` is 64 zeros; entries are JCS JSON lines. The log lives with the real
data (git-ignored); the event time is supplied by the caller."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError

GENESIS = "0" * 64
ACTIONS = ("read", "export", "delete", "policy_change")


def _hash(entry: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json({k: v for k, v in entry.items() if k != "record_hash"})).hexdigest()


class AccessLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

    def append(self, actor: str, action: str, target: str, purpose: str, time: datetime) -> dict[str, Any]:
        if action not in ACTIONS:
            raise ContractError("ERR-SPEC", f"access_log action {action} is not one of {ACTIONS}")
        if time.tzinfo is None:
            raise ContractError("ERR-SPEC", "access_log time must carry a time zone")
        existing = self.entries()
        entry = {"actor": actor, "action": action, "target": target, "purpose": purpose, "time": time.isoformat(),
                 "prev_hash": existing[-1]["record_hash"] if existing else GENESIS}
        entry["record_hash"] = _hash(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical_json(entry).decode("utf-8") + "\n")
        return entry

    def verify(self) -> bool:
        """True when every entry's hash is correct and links to the entry before it."""
        prev = GENESIS
        for e in self.entries():
            if e["prev_hash"] != prev or e["record_hash"] != _hash(e):
                return False
            prev = e["record_hash"]
        return True
