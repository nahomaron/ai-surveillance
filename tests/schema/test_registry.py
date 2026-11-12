"""T-01 part A: schema source (E-1.2.1 sections 1 and 5, F.1 A1.3, A2, A3, A5).

Expected names below are transcribed from the contract text. CT-E-01, 05 and 30
are not written here because their text is absent (CR-001).
"""
import jsonschema
import pyarrow as pa
import pytest

from rq1.schema import registry
from rq1.schema.errors import ERROR_CODES

# Contract section 5 tables plus the F.1 additions.
EXPECTED_TABLES = {
    "dataset_source", "license_component", "site", "session", "camera", "source_file",
    "recording", "timeline", "clock_alignment", "camera_group", "world_frame", "calibration",
    "context_map",
    "footprint_prior", "substrate_config", "clearance_band_scheme", "rule_configuration",
    "evaluation_config",  # prefix evc (AR-16); defined by the Architect's ruling on AR-42 item 3 (12 Nov 2026)
    "decode_summary", "frame", "coverage_segment",
    "detection", "track", "track_point",
    "object_state", "pow", "pair_series", "exposure_profile", "activity_segment", "gpw",
    "flag_series", "episode", "discarded_episode", "event_link", "candidate_event",
    "event_count_summary",
    "load_state", "e2_occupancy_series", "e2_occupancy_profile",
    "sampling_plan", "reference_window", "annotator", "annotation_record",
    "ref_object_presence", "ref_interaction", "ref_geometry", "ref_coverage_label",
    "reviewer_assessment", "adjudication", "validation_status_log",
    "split_manifest", "leakage_audit", "match_record", "error_attribution",
    "completeness_record", "metric_result", "acceptance_criterion", "measurement_fitness",
    "track_identity_assoc", "track_identity_summary",
    "decode_config", "geometry_config", "sampling_plan_config",  # F.1 A1.2, fields per AR-5
    "execution", "evidence_clip", "retention_policy", "access_log", "stage_error",
}

# Section 2.4 prefixes, with None for the two keyed tables that have no ID.
EXPECTED_PREFIX = {
    "dataset_source": "dsr", "license_component": "lic", "site": "sit", "session": "ses",
    "camera": "cam", "source_file": "src", "recording": "rec", "timeline": "tl",
    "clock_alignment": "clk", "camera_group": "cgp", "world_frame": "wf", "calibration": "cal",
    "context_map": "ctx", "decode_summary": "dsm", "frame": None, "coverage_segment": "cov",
    "detection": "det", "track": "trk", "track_point": "tpt", "object_state": "ost",
    "pow": "pow", "pair_series": "psr", "exposure_profile": "exp", "activity_segment": "act",
    "gpw": "gpw", "flag_series": None, "episode": "ep", "discarded_episode": "dep",
    "event_link": "lnk", "candidate_event": "evt", "event_count_summary": "ecs",
    "load_state": "lds", "e2_occupancy_series": "e2s", "e2_occupancy_profile": "e2p",
    "sampling_plan": "spl", "reference_window": "rwn", "split_manifest": "spm",
    "leakage_audit": "lka", "match_record": "mat", "error_attribution": "era",
    "completeness_record": "cmr", "metric_result": "mtr", "acceptance_criterion": "acc",
    "measurement_fitness": "fit",
}

# F.1 A1.3 revised natural keys.
EXPECTED_KEYS = {
    "site": ["dataset_id", "site_label"],
    "session": ["site_id", "session_label"],
    "camera": ["site_id", "camera_label"],
    "recording": ["src_id", "session_id", "camera_id", "registration_label"],
    "timeline": ["kind", "anchor_id"],
    "clock_alignment": ["recording_id", "method", "version"],
    "camera_group": ["timeline_id", "camera_ids"],
    "world_frame": ["site_id", "label", "version"],
    "calibration": ["camera_id", "calibration_tier", "method", "valid_from_us", "version"],
    "context_map": ["site_id", "version"],
    "completeness_record": ["window_id", "metric_id", "support_basis", "config_id", "stratum"],
    "match_record": ["window_id", "config_id", "scenario", "label_group", "ref_event_id", "system_event_id"],
    "metric_result": ["metric_id", "definition_version", "config_id", "scenario", "label",
                      "support_basis", "sample_type", "estimand", "weighted", "slice"],
    "ref_object_presence": ["window_id", "camera_id", "physical_identity_id"],
    "ref_interaction": ["window_id", "person_identity_id", "forklift_identity_id", "t_onset_us"],
    "ref_geometry": ["window_id", "physical_identity_id", "camera_id", "frame_index"],
    "ref_coverage_label": ["window_id", "camera_id", "t_start_us"],
    "track_identity_assoc": ["window_id", "camera_id", "frame_index", "track_id", "physical_identity_id"],
    "track_identity_summary": ["window_id", "track_id"],
}

ANCHOR_TABLES = {
    "dataset_source", "license_component", "site", "session", "camera", "source_file", "recording",
    "timeline", "clock_alignment", "camera_group", "world_frame", "calibration", "context_map",
}


def test_every_contract_table_is_registered():
    assert set(registry.TABLES) == EXPECTED_TABLES


@pytest.mark.determinism
@pytest.mark.parametrize("table,prefix", sorted(EXPECTED_PREFIX.items()))
def test_prefix(table, prefix):
    assert registry.TABLES[table].prefix == prefix


@pytest.mark.determinism
@pytest.mark.parametrize("table,key", sorted(EXPECTED_KEYS.items()))
def test_revised_natural_keys(table, key):
    assert registry.TABLES[table].key_names() == key


@pytest.mark.determinism
@pytest.mark.parametrize("table", sorted(ANCHOR_TABLES))
def test_anchor_tables_have_no_same_artifact_nk(table):
    """F.1 A1.2: references inside anchor keys use the parent's anchor ID."""
    assert not [f.name for f in registry.TABLES[table].fields if f.name.endswith(("_nk", "_nks"))]
    assert registry.TABLES[table].identity_class == "anchor"


@pytest.mark.determinism
@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_generates_valid_arrow_and_json_schema(table):
    assert isinstance(registry.arrow_schema(table), pa.Schema)
    jsonschema.Draft202012Validator.check_schema(registry.json_schema(table))


@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_nullable_fields_have_reason_sibling(table):
    names = {f.name: f for f in registry.TABLES[table].fields}
    for field in names.values():
        if field.nullable and not field.name.endswith("_null_reason"):
            assert names[f"{field.name}_null_reason"].nullable


@pytest.mark.determinism
def test_arrow_type_mapping_section_1_1():
    schema = registry.arrow_schema("flag_series")
    assert schema.field("P").type == pa.int8()
    schema = registry.arrow_schema("frame")
    assert schema.field("decode_seq").type == pa.int64()
    assert schema.field("ts_source").type == pa.dictionary(pa.int32(), pa.utf8())
    assert schema.field("t_resolved_s").type == pa.float64()
    assert schema.field("t_resolved_s").nullable
    assert not schema.field("support_s").nullable
    assert registry.arrow_schema("dataset_source").field("retrieved_utc").type == pa.timestamp("us", tz="UTC")


@pytest.mark.determinism
def test_f1_field_additions():
    fields = lambda t: {f.name for f in registry.TABLES[t].fields}
    assert "dataset_kind" in fields("dataset_source")
    for table in ["ref_object_presence", "ref_interaction", "ref_geometry", "ref_coverage_label",
                  "adjudication", "metric_result", "match_record"]:
        assert "reference_class" in fields(table), table
    assert {"t_start_tl_s", "t_end_tl_s", "unobservable_reason", "eligible_support_s", "timeline_id"} <= fields("ref_coverage_label")


def test_contact_state_has_no_observed_contact_value():
    values = registry.ENUMS["contact_state"]
    assert values == ("none_observed", "undetermined", "suspected", "not_assessable")


def test_no_forbidden_field_in_any_table():
    # Appendix T VR-E-041. stage_error.severity is the section 5.10 error severity (AR-11).
    for table in registry.TABLES:
        assert registry.forbidden_field_names(table) == [], table


@pytest.mark.determinism
def test_nk_is_json_array_in_json_schema_and_text_in_arrow():
    # AR-4: Appendix T T5 gives ["rec_a",1] in the payload; Parquet stores its JCS text.
    assert registry.json_schema("track_point")["properties"]["track_nk"] == {"type": "array"}
    assert registry.arrow_schema("track_point").field("track_nk").type == pa.utf8()


# AR-3: prefixes assigned where the contract gives none.
AR3_PREFIX = {
    "footprint_prior": "fpp", "substrate_config": "sbc", "clearance_band_scheme": "bsc", "rule_configuration": "rcf",
    "decode_config": "dcf", "geometry_config": "gcf", "sampling_plan_config": "spc",
    "ref_object_presence": "rop", "ref_interaction": "rin", "ref_geometry": "rgm", "ref_coverage_label": "rcl",
    "track_identity_assoc": "tia", "track_identity_summary": "tis",
    "annotator": "anr", "annotation_record": "anc", "reviewer_assessment": "rva", "adjudication": "adj",
    "retention_policy": "rtp", "access_log": "alg", "evidence_clip": "ecl", "stage_error": "ser",
}


@pytest.mark.determinism
@pytest.mark.parametrize("table,prefix", sorted(AR3_PREFIX.items()))
def test_ar3_prefixes(table, prefix):
    assert registry.TABLES[table].prefix == prefix
    assert registry.TABLES[table].fields[0].name == f"{prefix}_id"


def test_ar1_version_columns_are_strings():
    for table in ("clock_alignment", "calibration"):
        assert {f.name: f.type.kind for f in registry.TABLES[table].fields}["version"] == "str"


def test_ar9_ref_geometry_has_label_source():
    assert "label_source" in {f.name for f in registry.TABLES["ref_geometry"].fields}


def test_site_has_no_establishment_identifier():
    names = {f.name for f in registry.TABLES["site"].fields}
    assert not {n for n in names if any(x in n for x in ("establishment", "employer", "naics", "osha"))}


def test_error_codes_section_10_3_and_f1_a6():
    assert ERROR_CODES == {
        "ERR-TIMESTAMPS": "fatal", "ERR-DECODE-FRAME": "data_recorded", "ERR-CALIB-MISSING": "data_recorded",
        "ERR-CALIB-FAILED": "fatal", "ERR-CALIB-TIER": "fatal", "ERR-SCHEMA-MAJOR": "fatal",
        "ERR-UNKNOWN-ENUM": "fatal", "ERR-NATURAL-KEY": "fatal", "ERR-FK": "fatal", "ERR-INVARIANT": "fatal",
        "ERR-LEAKAGE": "fatal", "ERR-AUDIT-PENDING": "fatal", "ERR-NAMESPACE": "fatal",
        "ERR-FORBIDDEN-FIELD": "fatal", "ERR-ECS-AGGREGATE": "fatal",
        "ERR-ANCHOR-CONFLICT": "fatal", "ERR-SPEC": "fatal", "ERR-EXPORT-CLASS": "fatal",
    }


def _json_validator(table):
    return jsonschema.Draft202012Validator(registry.json_schema(table))


def test_json_schema_accepts_valid_row():
    assert not list(_json_validator("session").iter_errors(registry.minimal_row("session")))


def test_json_schema_rejects_null_without_reason():
    row = registry.minimal_row("session")
    row["scenario_ref_null_reason"] = None
    assert list(_json_validator("session").iter_errors(row))


def test_json_schema_rejects_non_null_with_reason():
    row = registry.minimal_row("session")
    row["scenario_ref"] = "script-1"
    assert list(_json_validator("session").iter_errors(row))


def test_json_schema_rejects_unknown_enum_and_extra_column():
    row = registry.minimal_row("detection")
    row["class"] = "bicycle"
    assert list(_json_validator("detection").iter_errors(row))
    row = registry.minimal_row("detection")
    row["extra"] = 1
    assert list(_json_validator("detection").iter_errors(row))


@pytest.mark.determinism
def test_enum_columns_are_stored_as_dictionary_in_arrow_table():
    table = registry.to_arrow("detection", [registry.minimal_row("detection")])
    assert table.schema.field("class").type == pa.dictionary(pa.int32(), pa.utf8())
    assert table.column("class").to_pylist() == ["person"]
