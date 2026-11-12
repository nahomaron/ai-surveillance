"""Artifact builder: the seven-step construction of E-1.2.1 section 2.3, with F.1 A1 identity classes."""
from __future__ import annotations

import hashlib
import json
import os
import platform as py_platform
import socket
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rq1.schema import files, registry
from rq1.schema import validate as schema_validate
from rq1.schema.canonical import canonical_json, sort_set
from rq1.schema.errors import ContractError
from rq1.schema import vr_rules
from rq1.schema.vr_rules import natural_key

from . import core

Row = dict[str, Any]
SCHEMA_VERSION = "E-1.2.4"
# F.1 A1.2 ART-ISO: prefixes that must appear exactly once in a spec (AR-16 names the prefixes).
ART_ISO = {"S2": ("mdl", "inf"), "S3": ("trc|orc",), "S4": ("gcf", "sbc"), "S5": ("rcf",), "S8": ("evc", "spm")}
TOLERANCE_STAGES = {"S2"}
# Target table of each same-artifact reference (section 2.4).
NK_TARGETS = {"track_nk": "track", "pow_nk": "pow", "continuation_of_nk": None, "member_pow_nks": "pow",
              "episode_a_nk": "episode", "episode_b_nk": "episode", "member_episode_nks": "episode",
              "plan_nk": "sampling_plan", "match_nk": "match_record"}


@dataclass(frozen=True)
class Spec:
    stage: str
    schema_bundle: str
    code_commit: str
    environment_digest: str
    config_ids: tuple[str, ...]
    input_artifact_ids: tuple[str, ...]
    seeds: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "schema_bundle": self.schema_bundle, "code_commit": self.code_commit,
                "environment_digest": self.environment_digest, "config_ids": sorted(self.config_ids),
                "input_artifact_ids": sorted(self.input_artifact_ids), "seeds": self.seeds}


@dataclass(frozen=True)
class Identity:
    artifact_spec_id: str
    spec: dict[str, Any] | None
    payload_sha256: str
    artifact_id: str
    payload: dict[str, list[Row]]


@dataclass(frozen=True)
class Artifact(Identity):
    tables: dict[str, list[Row]]


def check_art_iso(spec: Spec) -> None:
    available = [*spec.config_ids, *spec.input_artifact_ids]
    for wanted in ART_ISO.get(spec.stage, ()):
        count = sum(1 for item in available if item.split("_", 1)[0] in wanted.split("|"))
        if count != 1:
            raise ContractError("ERR-SPEC", f"{spec.stage}: expected exactly one {wanted}, found {count}")


def spec_id(spec: Spec) -> str:
    """Step 1."""
    check_art_iso(spec)
    return f"asp_{core.b32(hashlib.sha256(canonical_json(spec.as_dict())).digest())}"


def _payload_columns(table: str) -> set[str]:
    return {f.name for f in registry.TABLES[table].fields if not f.derived}


def _canonical_row(table: str, row: Row) -> Row:
    """Keep payload columns and put contract-defined sets in canonical order (section 1.5)."""
    payload = {k: v for k, v in row.items() if k in _payload_columns(table)}
    for name, value in payload.items():
        if name.endswith("_nks") or (table == "camera_group" and name == "camera_ids"):
            payload[name] = sort_set(value)
    return payload


def _canonical_tables(tables: dict[str, list[Row]]) -> dict[str, list[Row]]:
    out = {}
    for table in sorted(tables, key=lambda name: name.encode("utf-8")):
        rows = [_canonical_row(table, row) for row in tables[table]]
        out[table] = sorted(rows, key=lambda r: canonical_json(natural_key(table, r)))
    return out


def payload_stream(tables: dict[str, list[Row]]) -> bytes:
    """Step 4: tables in byte-wise name order; rows by byte-wise JCS(natural key) (Appendix T T5)."""
    lines = []
    for table, rows in _canonical_tables(tables).items():
        lines += [table.encode("utf-8") + b"\t" + canonical_json(row) + b"\n" for row in rows]
    return b"".join(lines)


def _target_table(table: str, column: str, row: Row) -> str:
    if column == "subject_nk":
        return row["subject_type"]
    target = NK_TARGETS.get(column)
    return target if target else table


def _references(table: str, row: Row) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for f in registry.TABLES[table].fields:
        if f.derived or row.get(f.name) is None:
            continue
        if f.type.kind == "nk":
            out.append((f.name, [row[f.name]]))
        elif f.type.kind == "list" and f.type.item.kind == "nk":
            out.append((f.name, row[f.name]))
    return out


def _check_integrity(tables: dict[str, list[Row]]) -> None:
    """Step 3."""
    keys: dict[str, set[bytes]] = {}
    for table, rows in tables.items():
        seen: set[bytes] = set()
        for row in rows:
            key = canonical_json(natural_key(table, row))
            if key in seen:
                raise ContractError("ERR-NATURAL-KEY", f"{table}: {key.decode()}")
            seen.add(key)
        keys[table] = seen
    for table, rows in tables.items():
        for row in rows:
            for column, values in _references(table, row):
                target = _target_table(table, column, row)
                for value in values:
                    if canonical_json(value) not in keys.get(target, set()):
                        raise ContractError("ERR-FK", f"{table}.{column}: {value} not found in {target}")


def compute_identity(spec: Spec | str, tables: dict[str, list[Row]]) -> Identity:
    """Steps 1 to 5. Reads no artifact-derived ID (ID-09)."""
    asp = spec if isinstance(spec, str) else spec_id(spec)
    payload = _canonical_tables(tables)
    _check_integrity(payload)
    digest = hashlib.sha256(payload_stream(payload)).hexdigest()
    return Identity(asp, None if isinstance(spec, str) else spec.as_dict(), digest, core.make_id("art", [asp, digest]), payload)


def _own_id(table: str, row: Row, artifact_id: str) -> str | None:
    spec = registry.TABLES[table]
    if spec.prefix is None:
        return None
    if table == "source_file":
        return core.source_id(row["sha256"])
    if spec.identity_class == "anchor":
        return core.anchor_id(spec.prefix, table, natural_key(table, row))
    if spec.identity_class == "configuration":
        return core.make_id(spec.prefix, row)
    if spec.identity_class == "observation":
        return core.observation_id(spec.prefix, table, artifact_id, natural_key(table, row))
    raise ContractError("ERR-SPEC", f"{table}: {spec.identity_class} records are not built as artifacts")


def _derive(identity: Identity) -> dict[str, list[Row]]:
    """Step 6."""
    index: dict[str, dict[bytes, str | None]] = {}
    out: dict[str, list[Row]] = {}
    for table, rows in identity.payload.items():
        index[table] = {}
        out[table] = []
        for row in rows:
            own = _own_id(table, row, identity.artifact_id)
            prefix = registry.TABLES[table].prefix
            out[table].append({**({f"{prefix}_id": own} if prefix else {}), **row})
            index[table][canonical_json(natural_key(table, row))] = own
    for table, rows in out.items():
        for row in rows:
            for f in registry.TABLES[table].fields:
                if f.name.endswith("_nk") and f.type.kind == "nk":
                    base = f.name[:-3]
                    value = row.get(f.name)
                    target = _target_table(table, f.name, row)
                    row[f"{base}_id"] = None if value is None else index[target][canonical_json(value)]
                    if f.nullable:
                        row[f"{base}_id_null_reason"] = row.get(f"{f.name}_null_reason")
                elif f.name.endswith("_nks") and f.type.kind == "list" and f.type.item.kind == "nk":
                    target = _target_table(table, f.name, row)
                    row[f"{f.name[:-4]}_ids"] = [index[target][canonical_json(v)] for v in row[f.name]]
    return out


def build_artifact(spec: Spec | str, tables: dict[str, list[Row]], *, validate: bool = True) -> Artifact:
    """Steps 1 to 6. `validate=False` exists only for the partial-row vector of Appendix T T5."""
    if validate:  # before hashing, so that NaN and infinity are reported as contract violations
        _validate({table: [_canonical_row(table, row) for row in rows] for table, rows in tables.items()})
    identity = compute_identity(spec, tables)
    return Artifact(identity.artifact_spec_id, identity.spec, identity.payload_sha256, identity.artifact_id, identity.payload, _derive(identity))


def _validate(payload: dict[str, list[Row]]) -> None:
    for table, rows in payload.items():
        issues = schema_validate.validate_rows(table, rows, raise_fatal=True)
        if issues:
            first = issues[0]
            raise ContractError("ERR-INVARIANT", f"{first.rule} {table}.{first.field}: {first.message}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_artifact(built: Artifact, directory: str | Path, data_origin: str, clock: Callable[[], datetime] | None = None,
                   host: str | None = None, register: str | Path | None = None) -> Path:
    """Step 7. `manifest.json` is written last and `execution.json` separately."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    started = clock()
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    meta = {"schema_version": SCHEMA_VERSION, "artifact_id": built.artifact_id, "data_origin": data_origin, "payload_sha256": built.payload_sha256}
    listing = []
    for table in sorted(built.tables):
        name = f"{table}.parquet"
        files.write_table(table, built.tables[table], target / name, {**meta, "schema_id": table})
        listing.append({"path": name, "file_sha256": _sha256(target / name), "rows": len(built.tables[table])})
    stage = built.spec["stage"] if built.spec else "unknown"
    manifest = {"artifact_spec_id": built.artifact_spec_id, "spec": built.spec, "payload_sha256": built.payload_sha256,
                "artifact_id": built.artifact_id, "files": listing, "data_origin": data_origin,
                "reproducibility_class": "tolerance" if stage in TOLERANCE_STAGES else "exact", "complete": True}
    temporary = target / "manifest.json.tmp"
    temporary.write_bytes(canonical_json(manifest))
    os.replace(temporary, target / "manifest.json")
    record = _execution_record(built.artifact_spec_id, built.artifact_id, stage, started, clock(), host, "complete")
    (target / "execution.json").write_bytes(canonical_json(record))
    _append_register(register, record)
    return target


def _execution_record(asp: str, art: str | None, stage: str, started: datetime, ended: datetime, host: str | None, status: str) -> Row:
    """Section 2.5, in the shape of the `execution` table."""
    return {"run_id": f"run_{uuid.uuid7()}", "artifact_spec_id": asp, "artifact_id": art,
            "artifact_id_null_reason": None if art else "upstream_failure", "stage": stage, "started_utc": started, "ended_utc": ended,
            "host": host or socket.gethostname(),
            "platform": {"cpu": py_platform.machine(), "gpu": None, "gpu_null_reason": "not_supplied", "driver": None, "driver_null_reason": "not_supplied"},
            "status": status, "compared_to_artifact_id": None, "compared_to_artifact_id_null_reason": "not_applicable",
            "tolerance_report_ref": None, "tolerance_report_ref_null_reason": "not_applicable", "logs_ref": ""}


def _append_register(register: str | Path | None, record: Row) -> None:
    if register:
        with open(register, "ab") as handle:
            handle.write(canonical_json(record) + b"\n")


def record_failed_run(directory: str | Path, spec: Spec, clock: Callable[[], datetime] | None = None, host: str | None = None,
                      register: str | Path | None = None) -> Path:
    """Section 2.5 and 10.3: a failed run leaves `execution.json` and no complete artifact."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    started = clock()
    record = _execution_record(spec_id(spec), None, spec.stage, started, clock(), host, "failed")
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "execution.json"
    path.write_bytes(canonical_json(record))
    _append_register(register, record)
    return path


def verify(directory: str | Path, check_file_hashes: bool = True) -> str:
    """Reconstruction check (CT-FK-05): drop derived columns and repeat steps 3 and 4."""
    target = Path(directory)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("complete") is not True:
        raise ContractError("ERR-INVARIANT", "artifact is not complete")
    tables: dict[str, list[Row]] = {}
    for item in manifest["files"]:
        path = target / item["path"]
        if check_file_hashes and _sha256(path) != item["file_sha256"]:
            raise ContractError("ERR-INVARIANT", f"file hash mismatch: {item['path']}")
        table = item["path"].removesuffix(".parquet")
        tables[table] = files.read_table(path, table, SCHEMA_VERSION)
    rebuilt = compute_identity(manifest["artifact_spec_id"], tables)
    if rebuilt.payload_sha256 != manifest["payload_sha256"] or rebuilt.artifact_id != manifest["artifact_id"]:
        raise ContractError("ERR-INVARIANT", "reconstruction does not match the stored payload hash")
    return rebuilt.artifact_id


def validate_artifact(directory: str | Path) -> list[schema_validate.Issue]:
    """CT-E-01 on a produced artifact: VR-E-001 to 005 for every file, using the manifest's `art_`."""
    target = Path(directory)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    issues: list[schema_validate.Issue] = []
    for item in manifest["files"]:
        table = item["path"].removesuffix(".parquet")
        issues += files.validate_file(target / item["path"], table, SCHEMA_VERSION)
        issues += vr_rules.check_ids(table, files.read_table(target / item["path"], table, SCHEMA_VERSION), manifest["artifact_id"])
    return issues


def duplicate_ids(artifacts: list[Artifact]) -> list[str]:
    """ID-05: global uniqueness of record IDs across artifacts."""
    seen: set[str] = set()
    repeated: set[str] = set()
    for built in artifacts:
        for table, rows in built.tables.items():
            prefix = registry.TABLES[table].prefix
            if prefix is None or registry.TABLES[table].identity_class == "anchor":
                continue
            for row in rows:
                value = row[f"{prefix}_id"]
                (repeated if value in seen else seen).add(value)
    return sorted(repeated)


def unresolved_references(built: Artifact, known_ids: set[str]) -> list[str]:
    """CT-NK-08: payload ID references (input, anchor, configuration) that do not resolve."""
    missing: set[str] = set()
    for table, rows in built.payload.items():
        for f in registry.TABLES[table].fields:
            if f.derived:
                continue
            is_id = f.type.kind == "id"
            is_list = f.type.kind == "list" and f.type.item.kind == "id"
            if not (is_id or is_list):
                continue
            for row in rows:
                value = row.get(f.name)
                if value is not None:
                    missing |= {v for v in ([value] if is_id else value) if v not in known_ids}
    return sorted(missing)
