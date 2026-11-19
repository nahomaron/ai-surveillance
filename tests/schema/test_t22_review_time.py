"""Appendix T T22.13 (contract E-1.2.20; CR-027, D-44): reviewer_assessment gains review_time_s · f64 · nullable.

"No other table, enum or ID rule changes": the neighbouring C-layer tables are pinned field by field below,
retyped from E-1.2.1 section 5.8 (the schema source before T22), not read from the registry.
"""
import pytest

from rq1.schema import registry, validate

RVA = "rva_" + "a" * 26
ANR = "anr_" + "b" * 26
EP = "ep_" + "c" * 26


def _row(**over):
    row = {"rva_id": RVA, "annotator_id": ANR, "namespace": "reference", "target_type": "system_episode", "target_id": EP,
           "label": "nm", "confidence": 2.0, "rationale": "The forklift stops abruptly as the person steps out.",
           "blind": True, "shown_system_output": False, "review_time_s": 41.5, "review_time_s_null_reason": None,
           "submitted_utc": "2026-11-19T10:00:00.000000Z"}
    row.update(over)
    return row


def test_review_time_s_is_a_nullable_f64_with_a_null_reason_sibling():
    fields = {f.name: f for f in registry.TABLES["reviewer_assessment"].fields}
    assert fields["review_time_s"].type.kind == "f64" and fields["review_time_s"].nullable is True
    assert fields["review_time_s_null_reason"].nullable is True  # section 1.1 rule for every nullable field


def test_reviewer_assessment_field_order_after_t22():
    names = [f.name for f in registry.TABLES["reviewer_assessment"].fields]
    assert names == ["rva_id", "annotator_id", "namespace", "target_type", "target_id", "label", "confidence", "rationale",
                     "blind", "shown_system_output", "review_time_s", "review_time_s_null_reason", "submitted_utc"]


@pytest.mark.parametrize("value,reason", [(41.5, None), (0.0, None), (None, "not_supplied")])
def test_valid_review_time_values(value, reason):
    assert validate.validate_row("reviewer_assessment", _row(review_time_s=value, review_time_s_null_reason=reason)) == []


@pytest.mark.parametrize("value", ["41.5", True, [1.0]])
def test_non_f64_review_time_is_refused(value):
    assert [i for i in validate.validate_row("reviewer_assessment", _row(review_time_s=value)) if i.field.endswith("review_time_s")]


def test_null_review_time_needs_its_reason():
    assert validate.validate_row("reviewer_assessment", _row(review_time_s=None, review_time_s_null_reason=None))


def test_minimal_row_and_arrow_schema_carry_the_field():
    assert "review_time_s" in registry.minimal_row("reviewer_assessment")
    assert registry.arrow_schema("reviewer_assessment").field("review_time_s").nullable


# E-1.2.1 section 5.8, unchanged by T22.13.
UNCHANGED = {
    "annotator": ["anr_id", "role", "qualification_ref", "independence_attestation", "pseudonym"],
    "adjudication": ["adj_id", "target_type", "target_id", "namespace", "final_label", "tier", "method", "assessment_ids",
                     "agreement_stat_ref", "agreement_stat_ref_null_reason", "prov_class", "reference_class"],
    "validation_status_log": ["seq", "status_id", "target_type", "target_id", "config_id", "status", "layer", "namespace",
                              "basis_ids", "actor_id", "created_utc", "prev_hash", "record_hash"],
}


@pytest.mark.parametrize("table", sorted(UNCHANGED))
def test_other_c_layer_tables_unchanged(table):
    assert [f.name for f in registry.TABLES[table].fields] == UNCHANGED[table]
