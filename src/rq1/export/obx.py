"""RQ2 observation export, OBX (E-1.2.1 section 11; F.1 A2 export classes EXP-1 to EXP-5).

One serializer and one set of validators serve both export classes; only the class guard differs (EXP-5). Every file is
the JCS form of {"metadata": {...}, "rows": [...]}, rows sorted by JCS, so output is byte-deterministic. The data
dictionary holds the JSON Schema of every exported table (the OBX schemas). Fixture exports go to `<root>/fixture/` (EXP-1)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from rq1.ids import lineage
from rq1.schema import registry, validate, vr_rules
from rq1.schema.validate import Issue
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError

Row = dict[str, Any]
CONTRACT = "E-1.2.10"
TEST_ONLY = "TEST-ONLY"

# Section 11 parts and the tables each one carries.
PARTS = {
    "1_provenance": ("dataset_source", "license_component", "site", "session", "camera", "camera_group", "recording", "timeline", "source_file"),
    "2_coverage_activity": ("coverage_segment", "activity_segment"),
    "3_substrate": ("pow", "exposure_profile"),
    "4_events": ("episode", "discarded_episode", "candidate_event", "event_count_summary", "load_state", "e2_occupancy_profile"),
    "5_validation_summary": ("validation_status_log", "adjudication"),
    "6_completeness": ("completeness_record",),
    "7_uncertainty_register": ("metric_result",),
    "8_fitness": ("measurement_fitness",),
}
EXCLUDED_VALUE_FRAGMENTS = registry.FORBIDDEN_FRAGMENTS  # section 11 "Excluded"; VR-E-041 names, scanned in values too (CT-E-27)


def _part_of(table: str) -> str:
    for part, tables in PARTS.items():
        if table in tables:
            return part
    raise ContractError("ERR-SPEC", f"table {table} belongs to no OBX part (section 11)")


def check_class(export_class: str, configurations: list[Row], datasets: list[Row], test_partition_config_ids: set[str] = frozenset()) -> None:
    """EXP-1 to EXP-3. `configurations` are configuration records with their ID under `config_id`; `datasets` are
    dataset_source rows. Raises ERR-EXPORT-CLASS on mixed inputs, in both directions."""
    test_only = [c["config_id"] for c in configurations if c.get("version_label") == TEST_ONLY]
    fixture = [d.get("name", "?") for d in datasets if d["dataset_kind"] == "fixture"]
    if export_class == "fixture_verification":
        research_cfg = [c["config_id"] for c in configurations if c.get("version_label") != TEST_ONLY]
        research_ds = [d.get("name", "?") for d in datasets if d["dataset_kind"] != "fixture"]
        if research_cfg or research_ds:
            raise ContractError("ERR-EXPORT-CLASS", f"EXP-1: fixture export with research inputs: configs {research_cfg}, datasets {research_ds}")
    elif export_class == "research":
        if test_only or fixture:
            raise ContractError("ERR-EXPORT-CLASS", f"EXP-2: research export with TEST-ONLY configs {test_only} or fixture datasets {fixture}")
        unregistered = sorted(c["config_id"] for c in configurations if c["config_id"] in test_partition_config_ids and not c.get("preregistration_ref"))
        if unregistered:
            raise ContractError("ERR-EXPORT-CLASS", f"EXP-2: test-partition metrics from configs without preregistration_ref: {unregistered}")
    else:
        raise ContractError("ERR-UNKNOWN-ENUM", f"export_class {export_class}")


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def check_content(tables: dict[str, list[Row]]) -> list:
    """Validators shared by both classes (EXP-5): schema rows, forbidden names and values (VR-E-041, section 11, CT-E-27),
    observed-contact values (VR-E-034), reference states (VR-E-040) and zero exposure from observed_no_detection (VR-E-040)."""
    issues = []
    for table, rows in sorted(tables.items()):
        issues += validate.validate_rows(table, rows)
        issues += vr_rules.check_no_observed_contact(table, rows)
        issues += vr_rules.check_no_reference_states(table, rows)
        for row in rows:
            for text in _strings(row):
                hit = next((f for f in EXCLUDED_VALUE_FRAGMENTS if f in text.lower()), None)
                if hit:
                    issues.append(Issue("VR-E-041", "ERR-FORBIDDEN-FIELD", table, "*", f"forbidden content '{hit}'"))
            state = row.get("ai_activity_state")
            if state in ("observed_no_detection", "not_evaluated") and any(_zero_exposure(k, v) for k, v in row.items()):
                # VR-E-040; extended to not_evaluated (CD-03) by the Architect's ruling on AR-46 item 7
                issues.append(Issue("VR-E-040", None, table, "*", f"{state} mapped to zero exposure"))
    return issues


def _zero_exposure(key: str, value: Any) -> bool:
    if not (key.startswith("exp_") or key.startswith("t_in_band")):
        return False
    return value == 0 or (isinstance(value, list) and bool(value) and all(x == 0 for x in value))


def _file(metadata: Row, rows: list[Row]) -> bytes:
    return canonical_json({"metadata": metadata, "rows": sorted(rows, key=canonical_json)})


def serialize(export_class: str, tables: dict[str, list[Row]]) -> dict[str, bytes]:
    """The single serializer (EXP-5): every table file, the data dictionary (OBX schemas) and the manifest."""
    research_use = export_class == "research"
    files: dict[str, bytes] = {}
    for table in sorted(tables):
        meta = {"export_class": export_class, "research_use": research_use, "table": table, "part": _part_of(table), "contract": CONTRACT}
        files[f"tables/{table}.json"] = _file(meta, tables[table])
    dictionary = {table: registry.json_schema(table) for table in sorted(tables)}
    files["data_dictionary.json"] = canonical_json({"metadata": {"export_class": export_class, "research_use": research_use, "contract": CONTRACT},
                                                    "schemas": dictionary})
    manifest = {"export_class": export_class, "research_use": research_use, "contract": CONTRACT,
                "parts": {part: sorted(t for t in tables if t in members) for part, members in PARTS.items()},
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files["manifest.json"] = canonical_json(manifest)
    return files


def check_lineage(artifact_ids: list[str], store: dict) -> list[str]:
    """CT-E-28: artifact IDs whose rows cannot be traced through art_ IDs to any source_file (src_)."""
    return sorted(a for a in artifact_ids if not lineage.trace_sources(a, store))


def export(export_class: str, tables: dict[str, list[Row]], configurations: list[Row], datasets: list[Row], root: Path,
           test_partition_config_ids: set[str] = frozenset()) -> dict:
    """Guard, validate, serialize and write. Returns the manifest. Nothing is written if any check fails."""
    check_class(export_class, configurations, datasets, test_partition_config_ids)
    issues = check_content(tables)
    if issues:
        fatal = [i for i in issues if i.code] or issues
        raise ContractError(fatal[0].code or "ERR-INVARIANT", f"{fatal[0].rule} {fatal[0].table}.{fatal[0].field}: {fatal[0].message}")
    files = serialize(export_class, tables)
    target = Path(root) / ("fixture" if export_class == "fixture_verification" else "research")
    for name, data in files.items():
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(data)
    return json.loads(files["manifest.json"])
