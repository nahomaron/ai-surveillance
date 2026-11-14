"""Access log for real-origin files (Gov table access_log; VR-E-070; qualification 3.5)."""
import json
from datetime import datetime, timezone

import pytest

from rq1.registry.access_log import GENESIS, AccessLog
from rq1.schema.errors import ContractError

T = datetime(2026, 11, 13, 22, 0, tzinfo=timezone.utc)


def test_chain_appends_and_verifies(tmp_path):
    log = AccessLog(tmp_path / "access_log.jsonl")
    a = log.append("implementation-agent", "read", "src_x", "S0 registration (codec probe)", T)
    b = log.append("implementation-agent", "read", "src_y", "S0 registration (codec probe)", T)
    assert a["prev_hash"] == GENESIS and b["prev_hash"] == a["record_hash"] and a["record_hash"] != b["record_hash"]
    assert [e["target"] for e in log.entries()] == ["src_x", "src_y"] and log.verify()


def test_tampering_breaks_the_chain(tmp_path):
    log = AccessLog(tmp_path / "access_log.jsonl")
    log.append("a", "read", "src_x", "p", T)
    log.append("a", "delete", "src_x", "p", T)
    lines = log.path.read_text().splitlines()
    first = json.loads(lines[0])
    first["purpose"] = "changed"
    log.path.write_text("\n".join([json.dumps(first), lines[1]]) + "\n")
    assert not log.verify()


def test_refusals(tmp_path):
    log = AccessLog(tmp_path / "access_log.jsonl")
    with pytest.raises(ContractError):
        log.append("a", "view", "src_x", "p", T)  # not an access_log action
    with pytest.raises(ContractError):
        log.append("a", "read", "src_x", "p", datetime(2026, 11, 13, 22, 0))  # no time zone
    assert log.entries() == []
