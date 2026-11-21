"""Appendix T T23.16 (contract E-1.2.23; D-49): adjudication.reference_class is nullable, VR-E-056, and the reader rule for
stored rows written before the change (T23.16 f). Expected outcomes are retyped from T23.16 and the FX-14j / FX-14k rows of
the D-49.1 section 6.1 table."""
import pytest

from rq1.schema import registry, validate
from rq1.schema.errors import ContractError
from rq1.validation.reference import read_adjudication_row

# The FX-14j and FX-14k rows, retyped here so these tests need no workflow fixture file (they also run where only the
# scoped E-1.2.23 schema change exists, D-49.1 section 6.2 item 5).
ROWS = {
    "FX-14j": {"namespace": "candidate_review", "reference_class": "independent_expert_judgment", "reference_class_null_reason": None},
    "FX-14k": {"namespace": "reference", "reference_class": None, "reference_class_null_reason": "not_applicable"},
}


def _row(name):
    tag = name[-1]
    return {"adj_id": f"adj_fx14{tag}".ljust(30, "0"), "target_type": "system_episode", "target_id": f"ep_fx14{tag}".ljust(29, "0"),
            "final_label": "nm", "tier": "tier2", "method": "adjudicator", "assessment_ids": [f"rva_fx14{tag}".ljust(30, "0")],
            "agreement_stat_ref": None, "agreement_stat_ref_null_reason": "not_applicable", "prov_class": "human_adjudicated",
            **ROWS[name]}


def _vr056(row):
    return [i for i in validate.validate_row("adjudication", row) if i.rule == "VR-E-056"]


def test_reference_class_is_nullable_with_a_reason_sibling():
    fields = {f.name: f for f in registry.TABLES["adjudication"].fields}
    assert fields["reference_class"].nullable is True
    assert fields["reference_class_null_reason"].nullable is True


def test_fx14j_candidate_review_with_a_class_is_refused():
    issues = _vr056(_row("FX-14j"))
    assert issues and issues[0].code == "ERR-NAMESPACE"


def test_fx14k_reference_with_a_null_class_is_refused():
    row = _row("FX-14k")
    assert not [i for i in validate.validate_row("adjudication", row) if i.rule == "VR-E-002"]  # VR-E-002 alone accepts it
    assert _vr056(row)


@pytest.mark.parametrize("namespace,cls,reason,ok", [
    ("reference", "independent_expert_judgment", None, True),
    ("candidate_review", None, "not_applicable", True),
    ("candidate_review", None, "not_supplied", False),  # T23.16 (b): the reason is not_applicable
    ("reference", "rule_conformance", None, True),  # VR-E-056 checks presence; T22.9 sets the value
    ("study_d6", None, "not_applicable", False),  # "any other combination is refused"
    ("pseudo_label", "independent_expert_judgment", None, False),
])
def test_vr_e_056_combinations(namespace, cls, reason, ok):
    row = {**_row("FX-14j"), "namespace": namespace, "reference_class": cls, "reference_class_null_reason": reason}
    assert (not _vr056(row)) is ok


def test_stored_reference_row_without_the_reason_column_reads_as_null():
    """T23.16 (f): no stored row is rewritten; a missing reason is read as null, valid only in reference with a class."""
    stored = {k: v for k, v in _row("FX-14j").items() if k != "reference_class_null_reason"}
    stored.update(namespace="reference")
    got = read_adjudication_row(stored)
    assert got["reference_class_null_reason"] is None and validate.validate_row("adjudication", got) == []
    assert "reference_class_null_reason" not in stored  # the input dict is not changed


def test_stored_candidate_review_row_without_the_reason_is_err_invariant():
    stored = {k: v for k, v in _row("FX-14j").items() if k != "reference_class_null_reason"}
    stored.update(reference_class=None)
    with pytest.raises(ContractError) as err:
        read_adjudication_row(stored)
    assert err.value.code == "ERR-INVARIANT"


def test_minimal_row_is_valid():
    row = registry.minimal_row("adjudication")
    assert validate.validate_row("adjudication", row) == []
