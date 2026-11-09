"""T-01 part A: active VR rules whose text exists in the contract.

Every rule in rq1.fixtures.vr_cases has one passing and one failing fixture. The failing
fixture must raise exactly the cited rule.
"""
import pytest

from rq1.fixtures.vr_cases import CASES
from rq1.schema import coverage, registry, validate
from rq1.schema.errors import ContractError, check_schema_major


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.rule)
def test_passing_fixture_has_no_issues(case):
    assert case.run(case.good()) == []


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.rule)
def test_failing_fixture_is_rejected_by_the_cited_rule(case):
    issues = case.run(case.bad())
    assert case.rule in {i.rule for i in issues}
    if case.code:
        assert case.code in {i.code for i in issues if i.rule == case.rule}


def test_coverage_lists_every_active_rule_exactly_once():
    report = coverage.vr_status()
    expected = {f"VR-E-{n:03d}" for n in [*range(1, 6), *range(10, 22), 30, 31, 32, 34, 40, 41,
                                         *range(50, 56), *range(60, 63), 70, 71]}
    assert set(report) == expected
    assert "VR-E-033" not in report and "VR-E-063" not in report  # superseded, section 12.1


def test_each_implemented_rule_has_a_failing_fixture_and_others_are_marked():
    report = coverage.vr_status()
    with_cases = {c.rule for c in CASES}
    assert {r for r, s in report.items() if s.status == "implemented"} == with_cases
    assert {r for r, s in report.items() if s.status == "blocked_no_text"} == {
        f"VR-E-{n:03d}" for n in [1, 4, 5, *range(11, 22), 30, 31, 32, 34, 50, 51, 53, 54, 60, 61, 62, 71]}


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


@pytest.mark.parametrize("value", ["trk_abc", "TRK_zr3hb5b6y2jjuw7ab7aml6ymtf", "toolong_zr3hb5b6y2jjuw7ab7aml6ymtf"])
def test_bad_id_format_rejected(value):
    row = registry.minimal_row("track")
    row["recording_id"] = value
    assert validate.validate_row("track", row)


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
