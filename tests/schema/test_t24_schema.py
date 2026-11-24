"""T24.0 (E-1.2.25) and AR-67: the T24 fields may be absent; an absent field enters no hash, no Parquet column and no ID."""
import pyarrow.parquet as pq
import pytest

from rq1.ids.artifact import config_id
from rq1.schema import files, registry, validate

T24_FIELDS = {"footprint_prior": ["anchor_offset_m", "anchor_taper_m"], "geometry_config": ["s_max_m_per_px"],
              "object_state": ["floor_resolution_m_per_px", "floor_resolution_m_per_px_null_reason"]}


def _fields(table):
    return {f.name: f for f in registry.TABLES[table].fields}


@pytest.mark.parametrize("table", sorted(T24_FIELDS))
def test_t24_fields_exist_and_may_be_absent(table):
    fields = _fields(table)
    for name in T24_FIELDS[table]:
        assert name in fields and registry.may_be_absent(fields[name])
    assert fields.get("floor_resolution_m_per_px") is None or fields["floor_resolution_m_per_px"].nullable


@pytest.mark.parametrize("table", sorted(T24_FIELDS))
def test_minimal_row_omits_the_t24_fields(table):
    row = registry.minimal_row(table)
    assert not set(T24_FIELDS[table]) & set(row)
    assert validate.validate_row(table, row) == []
    assert set(T24_FIELDS[table]).isdisjoint(registry.json_schema(table)["required"])


def test_absent_fields_leave_the_configuration_id_unchanged():
    row = registry.minimal_row("geometry_config")
    before = config_id("geometry_config", row)
    assert config_id("geometry_config", dict(row)) == before
    on = dict(row, s_max_m_per_px=0.1)
    assert validate.validate_row("geometry_config", on) == []
    assert config_id("geometry_config", on) != before


def test_reason_without_its_value_is_refused():
    row = registry.minimal_row("object_state")
    bad = dict(row, floor_resolution_m_per_px_null_reason="not_observable")
    assert any(i.field == "floor_resolution_m_per_px" for i in validate.validate_row("object_state", bad))
    bad2 = dict(row, floor_resolution_m_per_px=0.05)
    assert any(i.field == "floor_resolution_m_per_px_null_reason" for i in validate.validate_row("object_state", bad2))
    ok = dict(row, floor_resolution_m_per_px=0.05, floor_resolution_m_per_px_null_reason=None)
    assert validate.validate_row("object_state", ok) == []


def test_parquet_has_no_column_for_an_absent_field_and_reads_back_without_it(tmp_path):
    row = registry.minimal_row("object_state")
    path = tmp_path / "os.parquet"
    files.write_table("object_state", [row], path, {"schema_version": "E-1.2.4"})
    names = pq.read_schema(path).names
    assert "floor_resolution_m_per_px" not in names and "floor_resolution_m_per_px_null_reason" not in names
    assert files.read_table(path, "object_state", "E-1.2.4") == [row]
    on = dict(row, floor_resolution_m_per_px=None, floor_resolution_m_per_px_null_reason="not_observable")
    files.write_table("object_state", [on], path, {"schema_version": "E-1.2.4"})
    assert files.read_table(path, "object_state", "E-1.2.4") == [on]


def test_mixed_presence_in_one_table_is_refused():
    row = registry.minimal_row("object_state")
    on = dict(row, floor_resolution_m_per_px=0.05, floor_resolution_m_per_px_null_reason=None)
    with pytest.raises(ValueError):
        registry.to_arrow("object_state", [row, on])
