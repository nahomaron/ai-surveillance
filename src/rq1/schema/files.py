"""Parquet reading and writing with E-1.2.1 section 2.5 metadata (AR-4 for natural keys)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from . import registry, validate, vr_rules
from .errors import check_schema_major


def write_table(table: str, rows: list[dict[str, Any]], path: str | Path, metadata: dict[str, str], row_group_size: int | None = None) -> None:
    arrow = registry.to_arrow(table, rows)
    pq.write_table(arrow.replace_schema_metadata(dict(metadata)), path, row_group_size=row_group_size)


def _metadata(path: str | Path) -> dict[str, str]:
    raw = pq.read_schema(path).metadata or {}
    return {k.decode(): v.decode() for k, v in raw.items()}


def read_table(path: str | Path, table: str, supported: str) -> list[dict[str, Any]]:
    """Read a file, ignoring columns this reader does not know (CT-E-30); a major mismatch is fatal."""
    meta = _metadata(path)
    check_schema_major(meta["schema_version"], supported)
    known = {f.name for f in registry.TABLES[table].fields}
    columns = [name for name in pq.read_schema(path).names if name in known]
    return registry.decode_rows(table, pq.read_table(path, columns=columns).to_pylist())


def validate_file(path: str | Path, table: str, supported: str) -> list[validate.Issue]:
    """CT-E-01: VR-E-001, 002, 003 and 005 on one file. VR-E-004 needs the artifact (`vr_rules.check_ids`)."""
    meta = _metadata(path)
    issues = vr_rules.check_parquet_metadata(meta, supported)
    if any(i.code == "ERR-SCHEMA-MAJOR" for i in issues):
        return issues
    rows = read_table(path, table, supported)
    issues += validate.validate_rows(table, rows)
    origins = [r["data_origin"] for r in rows if "data_origin" in r]
    if "data_origin" in meta:
        origins.append(meta["data_origin"])
    return issues + vr_rules.check_data_origins(origins)
