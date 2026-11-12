"""T-01 part A: active VR rules whose text exists in the contract.

Every rule in rq1.fixtures.vr_cases has one passing and one failing fixture. The failing
fixture must raise exactly the cited rule.
"""
import pytest

from rq1.fixtures.vr_cases import CASES
from rq1.schema import coverage, registry, validate
from rq1.schema.errors import ContractError, check_schema_major


@pytest.mark.determinism
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.rule)
def test_passing_fixture_has_no_issues(case):
    assert case.run(case.good()) == []


@pytest.mark.determinism
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.rule)
def test_failing_fixture_is_rejected_by_the_cited_rule(case):
    issues = case.run(case.bad())
    assert case.rule in {i.rule for i in issues}
    if case.code:
        assert case.code in {i.code for i in issues if i.rule == case.rule}


@pytest.mark.determinism
def test_coverage_lists_every_active_rule_exactly_once():
    # Appendix T T1. VR-E-019 is a numbering gap (AR-10); 033 and 063 are superseded.
    report = coverage.vr_status()
    expected = {f"VR-E-{n:03d}" for n in [*range(1, 6), *range(10, 19), 20, 21, 30, 31, 32, 34, 40, 41,
                                         *range(50, 56), *range(60, 63), 70, 71]}
    assert set(report) == expected
    assert len(report) == 33


@pytest.mark.determinism
def test_every_active_rule_has_a_failing_fixture():
    report = coverage.vr_status()
    assert {r for r, s in report.items() if s.status == "implemented"} == {c.rule for c in CASES}
    assert {s.status for s in report.values()} == {"implemented"}


@pytest.mark.determinism
def test_site_approvals_still_required_for_real_origins():
    # Section 5.1 keeps this requirement; Appendix T moved the VR-E-070 ID to source_file and clips.
    row = registry.minimal_row("site")
    row.update(data_origin="real_staged", approvals_ref=None, approvals_ref_null_reason="not_supplied")
    assert "SITE-APPROVALS" in {i.rule for i in validate.validate_row("site", row)}


@pytest.mark.parametrize("column,value,bad", [
    ("frame_index", -1, True), ("n_gaps", -1, True), ("span_s", -1.0, True), ("speed_mps", -1.0, True),
    ("x_m", -1.0, False), ("offset_s", -1.0, False), ("image_gap_px", -1.0, False),
])
def test_ar8_sentinel_applies_only_to_non_negative_columns(column, value, bad):
    assert validate.is_sentinel(column, value) is bad


@pytest.mark.determinism
def test_ar15_time_keys_use_exact_half_even_microseconds():
    from rq1.ids.core import to_us
    assert to_us(0.1) == 100000
    # Hand calculation from Decimal(x) * 10**6:
    assert to_us(1.5e-6) == 2  # 1.500000000000000038... rounds up
    assert to_us(2.5e-6) == 3  # 2.500000000000000204... rounds up
    assert to_us(5e-7) == 0  # 0.499999999999999977... rounds down


def test_unknown_enum_is_fatal_err_unknown_enum():
    row = registry.minimal_row("flag_series")
    row["P"] = 3
    assert not [i for i in validate.validate_row("flag_series", row) if i.code == "ERR-UNKNOWN-ENUM"]  # tri, not enum
    row = registry.minimal_row("detection")
    row["class"] = "bicycle"
    assert [i for i in validate.validate_row("detection", row) if i.code == "ERR-UNKNOWN-ENUM"]


@pytest.mark.parametrize("value", [3, -1, None, True])
def test_tri_only_accepts_0_1_2(value):
    row = registry.minimal_row("flag_series")
    row["P"] = value
    assert validate.validate_row("flag_series", row)


@pytest.mark.determinism
@pytest.mark.parametrize("value", ["trk_abc", "TRK_zr3hb5b6y2jjuw7ab7aml6ymtf", "toolong_zr3hb5b6y2jjuw7ab7aml6ymtf"])
def test_bad_id_format_rejected(value):
    row = registry.minimal_row("track")
    row["recording_id"] = value
    assert validate.validate_row("track", row)


@pytest.mark.determinism
def test_id_accepts_derived_and_uuid_forms():
    row = registry.minimal_row("track")
    row["recording_id"] = "rec_zr3hb5b6y2jjuw7ab7aml6ymtf"
    assert validate.validate_row("track", row) == []
    row["recording_id"] = "rec_018f3a2e-7b1c-7def-8a12-3456789abcde"
    assert validate.validate_row("track", row) == []


def test_unknown_column_rejected():
    row = registry.minimal_row("track")
    row["notes"] = "x"
    assert validate.validate_row("track", row)


@pytest.mark.determinism
def test_nullable_nested_struct_requires_reason():
    row = registry.minimal_row("session")
    row["lineage"]["seed"] = None
    row["lineage"]["seed_null_reason"] = None
    assert {i.rule for i in validate.validate_row("session", row)} >= {"VR-E-002"}


def test_frac_suffix_is_bounded_section_1_2():
    row = registry.minimal_row("decode_summary")
    row["untimed_frac"] = 1.5
    assert validate.validate_row("decode_summary", row)


def test_bbox_requires_x1_lt_x2_section_4_1():
    row = registry.minimal_row("detection")
    row["bbox_xyxy_px"] = [5.0, 1.0, 4.0, 2.0]
    assert validate.validate_row("detection", row)


@pytest.mark.determinism
@pytest.mark.parametrize("table", sorted(registry.TABLES))
def test_minimal_row_is_valid_and_loads_into_arrow(table):
    row = registry.minimal_row(table)
    assert validate.validate_row(table, row) == []
    assert registry.to_arrow(table, [row]).num_rows == 1


def test_validate_table_raises_fatal_contract_error():
    row = registry.minimal_row("detection")
    row["class"] = "bicycle"
    with pytest.raises(ContractError) as exc:
        validate.validate_rows("detection", [row], raise_fatal=True)
    assert exc.value.code == "ERR-UNKNOWN-ENUM"


@pytest.mark.parametrize("found,ok", [("E-1.2.2", True), ("E-1.2.9", True), ("E-1.3.0", False), ("E-2.0.0", False)])
def test_schema_major_uses_package_f_section_9(found, ok):
    # Package F section 9: E-1.2.x is minor, E-1.3 is major.
    if ok:
        check_schema_major(found, "E-1.2.2")
    else:
        with pytest.raises(ContractError) as exc:
            check_schema_major(found, "E-1.2.2")
        assert exc.value.code == "ERR-SCHEMA-MAJOR"
