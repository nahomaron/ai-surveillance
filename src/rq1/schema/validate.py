"""Row validators. Only rules whose text exists in the contract are implemented (see CR-001)."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from . import registry
from .errors import ERROR_CODES, ContractError
from .types import Field, Type

_ID = re.compile(r"^[a-z0-9]{2,4}_([a-z0-9]{26}|[0-9a-f-]{36})$")
_REFERENCE_SOURCES = {"simulator_truth", "human_manual"}  # section 5.8
_REAL_ORIGINS = {"real_natural", "real_staged"}
_REF_TABLES = {"ref_object_presence", "ref_interaction", "ref_geometry", "ref_coverage_label"}


_I_JSON_MAX = 2**53 - 1
# AR-8: columns that cannot legitimately be negative, where a negative value can only be a sentinel.
_NON_NEGATIVE = re.compile(
    r"(^|\.)(frame_index|decode_seq|det_index|window_index|error_index|seq|audit_seq|track_local_id|.*_frame|.*_frame_excl"
    r"|minclr_frame|n_.*|.*_frames|click_count|size_bytes|span_s|support_s|eligible_support_s|t_.*_support_s"
    r"|t_(detected|inferred|insufficient|clearance_unknown|motion_unknown|moving_detected|moving_inferred"
    r"|stationary_detected|stationary_inferred|joint_visible|coobserved|occupied_detected|occupied_inferred"
    r"|not_occupied|occupancy_unknown)_s|duration_.*_s|.*sigma.*|.*speed.*_mps|score|delta_nom_s|mount_height_m)$"
)


def is_sentinel(column: str, value: float) -> bool:
    """AR-8: VR-E-003 forbids sentinels such as -1; only non-negative columns can be checked."""
    return value < 0 and bool(_NON_NEGATIVE.search(column))


_UTC_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


def _canonical_utc(text: str) -> bool:
    """AR-7 (revised): exactly YYYY-MM-DDTHH:MM:SS.ffffffZ, and a real date and time."""
    if not _UTC_TEXT.match(text):
        return False
    try:
        datetime.strptime(text, registry.UTC_FORMAT)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class Issue:
    rule: str  # VR rule ID, or SCHEMA for section 1.1 and 1.2 type rules
    code: str | None  # section 10.3 code, only when the contract names one
    table: str
    field: str
    message: str


def _check_value(table: str, path: str, t: Type, value: Any, constraints: frozenset[str], issues: list[Issue]) -> None:
    def bad(message: str, rule: str = "SCHEMA", code: str | None = None) -> None:
        issues.append(Issue(rule, code, table, path, message))

    kind = t.kind
    if kind == "id":
        if not (isinstance(value, str) and _ID.match(value)):
            bad(f"not an id: {value!r}")
    elif kind == "nk":
        if not isinstance(value, list):
            bad(f"natural key must be a JSON array: {value!r}")
    elif kind == "str":
        if not isinstance(value, str):
            bad(f"not a string: {value!r}")
    elif kind in ("i32", "i64"):
        if isinstance(value, bool) or not isinstance(value, int):
            bad(f"not an integer: {value!r}")
        elif not -(2 ** (31 if kind == "i32" else 63)) <= value < 2 ** (31 if kind == "i32" else 63):
            bad(f"out of range: {value!r}")
        elif abs(value) > _I_JSON_MAX:
            bad(f"outside the I-JSON integer range that RFC 8785 can hash (AR-18): {value!r}")
        elif is_sentinel(path, value):
            bad(f"negative sentinel in a non-negative column: {value}", "VR-E-003")
    elif kind == "f64":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            bad(f"not a number: {value!r}")
        elif not math.isfinite(value):
            bad("NaN or infinity is forbidden", "VR-E-003")
        elif is_sentinel(path, value):
            bad(f"negative sentinel in a non-negative column: {value}", "VR-E-003")
        elif "ge0" in constraints and value < 0:
            bad(f"must be >= 0: {value}")
        elif ("01" in constraints or path.endswith("_frac")) and not 0 <= value <= 1:
            bad(f"must be in [0, 1]: {value}")
    elif kind == "bool":
        if not isinstance(value, bool):
            bad(f"not a bool: {value!r}")
    elif kind == "tri":
        if isinstance(value, bool) or value not in (0, 1, 2):
            bad(f"tri must be 0, 1 or 2: {value!r}")
    elif kind == "ts":
        if isinstance(value, str):
            if not _canonical_utc(value):
                bad(f"timestamp not in YYYY-MM-DDTHH:MM:SS.ffffffZ form: {value!r}", "UTC-FORMAT")
        elif not (isinstance(value, datetime) and value.utcoffset() == timedelta(0)):
            bad(f"not a UTC timestamp: {value!r}")
    elif kind == "enum":
        if value not in t.values:
            bad(f"unknown enum value: {value!r}", code="ERR-UNKNOWN-ENUM")
    elif kind == "list":
        if not isinstance(value, list):
            bad(f"not a list: {value!r}")
            return
        if t.size is not None and len(value) != t.size:
            bad(f"expected {t.size} items, got {len(value)}")
        for i, item in enumerate(value):
            _check_value(table, f"{path}[{i}]", t.item, item, frozenset(), issues)
        if "bbox" in constraints and len(value) == 4 and not (value[0] < value[2] and value[1] < value[3]):
            bad("box must satisfy x1 < x2 and y1 < y2")
    elif kind == "map":
        if not isinstance(value, dict):
            bad(f"not a map: {value!r}")
            return
        for key, item in value.items():
            _check_value(table, f"{path}.key", t.key, key, frozenset(), issues)
            _check_value(table, f"{path}[{key}]", t.item, item, frozenset(), issues)
    elif kind == "struct":
        if not isinstance(value, dict):
            bad(f"not a struct: {value!r}")
            return
        _check_fields(table, path + ".", t.fields, value, issues)


def _check_fields(table: str, prefix: str, fields, row: dict[str, Any], issues: list[Issue]) -> None:
    known = {f.name: f for f in fields}
    for name in row:
        if name not in known:
            issues.append(Issue("SCHEMA", None, table, prefix + name, "unknown column"))
    for f in fields:
        if f.name not in row:
            if not f.derived:
                issues.append(Issue("SCHEMA", None, table, prefix + f.name, "missing column"))
            continue
        value = row[f.name]
        path = prefix + f.name
        if f.name.endswith("_null_reason") and f.name[:-12] in known:
            base = row.get(f.name[:-12])
            if base is None and value is None:
                issues.append(Issue("VR-E-002", None, table, path, "a null value requires a reason"))
            elif base is not None and value is not None:
                issues.append(Issue("VR-E-002", None, table, path, "a non-null value must carry no reason"))
            if value is not None:
                _check_value(table, path, f.type, value, f.constraints, issues)
            continue
        if value is None:
            if not f.nullable:
                issues.append(Issue("SCHEMA", None, table, path, "null in a non-nullable field"))
            continue
        _check_value(table, path, f.type, value, f.constraints, issues)


def validate_row(table: str, row: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    _check_fields(table, "", registry.TABLES[table].fields, row, issues)
    for name in row:
        if registry.is_forbidden(table, name):
            issues.append(Issue("VR-E-041", "ERR-FORBIDDEN-FIELD", table, name, "forbidden quantity"))
    if table == "site" and row.get("data_origin") in _REAL_ORIGINS and row.get("approvals_ref") is None:
        issues.append(Issue("SITE-APPROVALS", None, table, "approvals_ref", "required for real data origins (section 5.1)"))
    if table in _REF_TABLES and row.get("label_source") not in _REFERENCE_SOURCES:
        issues.append(Issue("VR-E-055", "ERR-NAMESPACE", table, "label_source", "not a permitted reference source"))
    if table == "annotation_record" and row.get("namespace") == "reference" and row.get("label_source") not in _REFERENCE_SOURCES:
        issues.append(Issue("VR-E-055", "ERR-NAMESPACE", table, "label_source", "not a permitted reference source"))
    return issues


def validate_rows(table: str, rows: list[dict[str, Any]], raise_fatal: bool = False) -> list[Issue]:
    issues = [issue for row in rows for issue in validate_row(table, row)]
    if raise_fatal:
        for issue in issues:
            if issue.code and ERROR_CODES[issue.code] == "fatal":
                raise ContractError(issue.code, f"{table}.{issue.field}: {issue.message}")
    return issues
