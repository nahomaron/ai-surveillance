"""Error registry: E-1.2.1 section 10.3 plus F.1 A6."""
from __future__ import annotations

ERROR_CODES = {
    "ERR-TIMESTAMPS": "fatal",
    "ERR-DECODE-FRAME": "data_recorded",
    "ERR-CALIB-MISSING": "data_recorded",
    "ERR-CALIB-FAILED": "fatal",
    "ERR-CALIB-TIER": "fatal",
    "ERR-SCHEMA-MAJOR": "fatal",
    "ERR-UNKNOWN-ENUM": "fatal",
    "ERR-NATURAL-KEY": "fatal",
    "ERR-FK": "fatal",
    "ERR-INVARIANT": "fatal",
    "ERR-LEAKAGE": "fatal",
    "ERR-AUDIT-PENDING": "fatal",
    "ERR-NAMESPACE": "fatal",
    "ERR-FORBIDDEN-FIELD": "fatal",
    "ERR-ECS-AGGREGATE": "fatal",
    "ERR-ANCHOR-CONFLICT": "fatal",
    "ERR-SPEC": "fatal",
    "ERR-EXPORT-CLASS": "fatal",
}


class ContractError(Exception):
    """A contract violation carrying its section 10.3 error code."""

    def __init__(self, code: str, message: str):
        if code not in ERROR_CODES:
            raise ValueError(f"unregistered error code: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code


def _major(version: str) -> tuple[int, int]:
    parts = version.removeprefix("E-").split(".")
    return int(parts[0]), int(parts[1])


def check_schema_major(found: str, supported: str) -> None:
    """Package F section 9: E-1.2.x is a minor change, E-1.3 is a major one."""
    if _major(found) != _major(supported):
        raise ContractError("ERR-SCHEMA-MAJOR", f"found {found}, supported {supported}")
