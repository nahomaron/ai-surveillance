"""Gaps found by the post-T-02 completeness audit (10 Nov 2026)."""
import json
from datetime import datetime, timezone

import pytest

from rq1.fixtures import identity_rows as rows
from rq1.ids import artifact
from rq1.ids.artifact import Spec
from rq1.schema import files, registry, validate
from rq1.schema.errors import ContractError

SPEC = Spec("S3", "E-1.2.3", "f", "f", ("trc_" + "a" * 26,), (), {})
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _tables():
    return {"track": [rows.track(1)], "track_point": [rows.track_point(1, 5)]}


def _written(tmp_path):
    return artifact.write_artifact(artifact.build_artifact(SPEC, _tables()), tmp_path / "x", "synthetic_rendered", clock=lambda: T0, host="h")


def _load_execution(path):
    record = json.loads(path.read_text())
    for name in ("started_utc", "ended_utc"):
        record[name] = datetime.fromisoformat(record[name])
    return record


def test_execution_json_conforms_to_its_schema(tmp_path):
    assert validate.validate_row("execution", _load_execution(_written(tmp_path) / "execution.json")) == []


def test_failed_run_record_section_2_5(tmp_path):
    path = artifact.record_failed_run(tmp_path, SPEC, clock=lambda: T0, host="h")
    record = _load_execution(path)
    assert validate.validate_row("execution", record) == []
    assert record["status"] == "failed" and record["artifact_id"] is None
    assert record["artifact_id_null_reason"] == "upstream_failure"
    assert not (tmp_path / "manifest.json").exists()


def test_run_register_is_append_only_jsonl(tmp_path):
    built = artifact.build_artifact(SPEC, _tables())
    register = tmp_path / "runs.jsonl"
    for name in "ab":
        artifact.write_artifact(built, tmp_path / name, "synthetic_rendered", register=register)
    assert len(register.read_text().splitlines()) == 2


def test_ct_e_01_covers_vr_e_004_on_produced_artifact(tmp_path):
    assert artifact.validate_artifact(_written(tmp_path)) == []


def test_ct_e_01_detects_wrong_id_in_produced_file(tmp_path):
    directory = _written(tmp_path)
    path = directory / "track.parquet"
    data = files.read_table(path, "track", "E-1.2.3")
    data[0]["trk_id"] = "trk_" + "z" * 26
    meta = {"schema_id": "track", "schema_version": "E-1.2.3", "artifact_id": json.loads((directory / "manifest.json").read_text())["artifact_id"],
            "data_origin": "synthetic_rendered", "payload_sha256": "0"}
    files.write_table("track", data, path, meta)
    assert "VR-E-004" in {i.rule for i in artifact.validate_artifact(directory)}


def test_incomplete_artifact_is_refused(tmp_path):
    directory = _written(tmp_path)
    manifest = json.loads((directory / "manifest.json").read_text())
    (directory / "manifest.json").write_text(json.dumps({**manifest, "complete": False}))
    with pytest.raises(ContractError):
        artifact.verify(directory)


def test_ct_id_07_rewrite_changes_file_hash_only(tmp_path):
    directory = _written(tmp_path)
    path = directory / "track_point.parquet"
    before = artifact._sha256(path)
    meta = {"schema_id": "track_point", "schema_version": "E-1.2.3", "artifact_id": "a", "data_origin": "synthetic_rendered", "payload_sha256": "0"}
    data = files.read_table(path, "track_point", "E-1.2.3") * 1
    files.write_table("track_point", data, path, meta, row_group_size=1)
    assert artifact._sha256(path) != before


@pytest.mark.parametrize("value,bad", [(2**53 - 1, False), (-(2**53 - 1), False), (2**53, True), (2**60, True)])
def test_ar18_integers_outside_i_json_range_are_rejected(value, bad):
    row = rows.row("session")
    row["lineage"]["seed"], row["lineage"]["seed_null_reason"] = value, None
    assert bool(validate.validate_row("session", row)) is bad


def test_ar18_is_a_contract_error_not_a_serializer_crash():
    tables = {"track": [rows.track(2**60)]}
    with pytest.raises(ContractError) as exc:
        artifact.build_artifact(SPEC, tables)
    assert exc.value.code == "ERR-INVARIANT"


def _columns(table):
    return {f.name: f.type.kind for f in registry.TABLES[table].fields if not f.derived and not f.name.endswith("_null_reason")}


def test_ar5_config_table_columns():
    # E-1.2.4 T7 adds the delta_nom declaration; AR-24 names it and the final-frame variant field.
    assert _columns("decode_config") == {"k_sup": "f64", "f_untimed": "f64", "f_sub": "f64", "rules_version": "str", "version_label": "str",
                                         "delta_nom_declarations": "list", "final_frame_support": "enum"}
    # E-1.2.6 T8.6 adds v_part (AR-35 places it in geometry_config).
    assert _columns("geometry_config") == {"w_v_s": "f64", "v_part": "f64", "motion_models": "list", "footprint_prior_ids": "list", "version_label": "str"}
    assert _columns("sampling_plan_config") == {"sample_type": "enum", "w_ref_s": "f64", "w_guard_s": "f64", "tiling_origin_tl_s": "f64",
                                                "strata": "list", "seed": "i64", "version_label": "str"}


def test_ar6_named_configuration_fields():
    # AR-35 adds the T8.3 prediction horizon.
    assert _columns("substrate_config") == {"g_max": "i32", "pair_classes": "list", "v_min": "f64", "k_sup": "f64", "motion_models": "list",
                                            "prediction_horizon_s": "f64", "version_label": "str"}
    for table in ("footprint_prior", "clearance_band_scheme", "rule_configuration"):
        assert "version_label" in _columns(table)


def test_ar2_representative_inferred_types():
    assert _columns("metric_result")["n_units"] == "i64" and _columns("metric_result")["eff_n"] == "f64"
    assert _columns("reference_window")["weight"] == "f64" and _columns("reference_window")["window_index"] == "i64"
    assert _columns("completeness_record")["numerator"] == "f64"
