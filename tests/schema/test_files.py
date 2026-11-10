"""CT-E-01, CT-E-05 and CT-E-30 (Appendix T), and VR-E-001 and VR-E-005 on real Parquet files."""
import datetime as dt

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rq1.schema import files, registry, validate, vr_rules
from rq1.schema.errors import ContractError

META = {"schema_id": "detection", "schema_version": "E-1.2.3", "artifact_id": "art_" + "a" * 26,
        "data_origin": "synthetic_rendered", "payload_sha256": "0" * 64}


def _write(tmp_path, table="detection", rows=None, meta=META):
    path = tmp_path / f"{table}.parquet"
    files.write_table(table, rows or [registry.minimal_row(table)], path, meta)
    return path


def test_ct_e_01_produced_file_conforms(tmp_path):
    assert files.validate_file(_write(tmp_path), "detection", "E-1.2.3") == []


@pytest.mark.parametrize("table", sorted(registry.TABLES))
def test_every_table_round_trips_through_parquet(tmp_path, table):
    row = registry.minimal_row(table)
    path = _write(tmp_path, table, [row], {**META, "schema_id": table})
    assert files.read_table(path, table, "E-1.2.3") == [row]


def test_nested_values_round_trip(tmp_path):
    row = registry.minimal_row("flag_series")
    row["C_by_provider"] = {"R3": 1, "R4": 2}
    path = _write(tmp_path, "flag_series", [row])
    assert files.read_table(path, "flag_series", "E-1.2.3")[0]["C_by_provider"] == {"R3": 1, "R4": 2}
    point = registry.minimal_row("track_point")
    point["track_nk"] = ["rec_a", 1]
    path = _write(tmp_path, "track_point", [point])
    assert files.read_table(path, "track_point", "E-1.2.3")[0]["track_nk"] == ["rec_a", 1]


def test_ct_e_01_rejects_execution_key_in_metadata(tmp_path):
    path = _write(tmp_path, meta={**META, "run_id": "run_x"})
    assert "VR-E-001" in {i.rule for i in files.validate_file(path, "detection", "E-1.2.3")}


def test_ct_e_30_minor_reader_ignores_added_column(tmp_path):
    path = _write(tmp_path)
    table = pq.read_table(path)
    extended = table.append_column("added_later", pa.array(["x"]))
    pq.write_table(extended.replace_schema_metadata({**table.schema.metadata}), path)
    assert files.read_table(path, "detection", "E-1.2.9") == [registry.minimal_row("detection")]


def test_ct_e_30_major_mismatch_fails(tmp_path):
    path = _write(tmp_path, meta={**META, "schema_version": "E-1.3.0"})
    with pytest.raises(ContractError) as exc:
        files.read_table(path, "detection", "E-1.2.3")
    assert exc.value.code == "ERR-SCHEMA-MAJOR"


def _uncalibrated_state():
    row = registry.minimal_row("object_state")
    row["geometry_method"] = "image_only"
    world = ("calibration_id", "world_frame_id", "x_m", "y_m", "pos_cov_m2", "yaw_rad", "yaw_sigma_rad",
             "speed_mps", "speed_sigma_mps", "heading_rad")
    for name in world:
        row[name] = None
        row[f"{name}_null_reason"] = "uncalibrated"
    return row


def test_ct_e_05_uncalibrated_world_fields_null_with_reason():
    row = _uncalibrated_state()
    assert validate.validate_row("object_state", row) == []
    assert vr_rules.check_object_states([row], {}) == []


def test_ct_e_05_sentinel_world_value_is_rejected():
    row = _uncalibrated_state()
    row["x_m"], row["x_m_null_reason"] = -1.0, None
    assert "VR-E-014" in {i.rule for i in vr_rules.check_object_states([row], {})}


def test_ar7_timestamps_round_trip_in_rfc3339_jcs_form():
    from rq1.schema.canonical import canonical_json
    value = dt.datetime(2026, 1, 1, 0, 0, 0, 5, tzinfo=dt.timezone.utc)
    assert canonical_json({"t": value}) == b'{"t":"2026-01-01T00:00:00.000005Z"}'
