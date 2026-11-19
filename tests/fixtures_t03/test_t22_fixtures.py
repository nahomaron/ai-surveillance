"""Appendix T T22 (contract E-1.2.20; CR-027, D-44): fixtures FX-13 and FX-13a to FX-13f.

Expected values below are retyped from the T22 "Fixtures and tests" paragraph, with the T22.7 / T22.8 rules applied by
hand where the paragraph names only the outcome (hand calculation in each fixture's `hand_calculation`). They are not
imported from the generator. The review application (V-02, branch v02-review-ui) runs these fixtures through its own
code path; on this branch they are data plus the schema and VR-E-053 checks that already exist.
"""
import json
from pathlib import Path

import pytest

from rq1.schema import validate, vr_rules

ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "records"
FX13 = ["FX-13", "FX-13a", "FX-13b", "FX-13c", "FX-13d", "FX-13e", "FX-13f"]
BATCH = "rvb_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a13"


def load(fixture_id):
    return json.loads((ROOT / f"{fixture_id}.json").read_text(encoding="utf-8"))


def by_pseudonym(fx):
    return {a["pseudonym"]: a for a in fx["inputs"]["annotators"]}


def labels(fx):
    names = {a["anr_id"]: a["pseudonym"] for a in fx["inputs"]["annotators"]}
    return [(names[r["annotator_id"]], r["namespace"], r["label"], r["confidence"]) for r in fx["inputs"]["assessments"]]


@pytest.mark.determinism
@pytest.mark.parametrize("fixture_id", FX13)
def test_rows_are_schema_valid(fixture_id):
    fx = load(fixture_id)
    assert fx["source"].startswith("Appendix T T22") and fx["version_label"] == "TEST-ONLY"
    for row in fx["inputs"]["annotators"]:
        assert validate.validate_row("annotator", row) == [], row
        assert row["qualification_ref"].strip()  # T22.2 (c)
    for row in fx["inputs"]["assessments"]:
        assert validate.validate_row("reviewer_assessment", row) == [], row
        assert row["confidence"] in (1.0, 2.0, 3.0) and row["rationale"].strip()  # T22.5 (b), (c)


@pytest.mark.determinism
def test_vr_e_053_flags_only_the_fx13d_assessment():
    for fixture_id in FX13:
        rows = load(fixture_id)["inputs"]["assessments"]
        issues = vr_rules.check_blind_reference("reviewer_assessment", rows)
        assert [i.rule for i in issues] == (["VR-E-053"] if fixture_id == "FX-13d" else []), fixture_id


@pytest.mark.determinism
def test_fx13_two_reviewers_disagree_tier2():
    fx = load("FX-13")
    assert fx["inputs"]["target"]["g2_label"] == "lbl_nm"
    assert labels(fx) == [("R-A", "reference", "nm", 2.0), ("R-B", "reference", "ud", 3.0)]
    assert all(r["blind"] is True and r["shown_system_output"] is False for r in fx["inputs"]["assessments"])
    assert all(a["independence_attestation"] is True for a in fx["inputs"]["annotators"])
    assert fx["inputs"]["adjudicator_decision"]["final_label"] == "ud"
    exp = fx["expected"]
    assert exp["mapped_system_label"] == "nm" and exp["refused"] is False
    [adj] = exp["adjudications"]
    assert (adj["tier"], adj["method"], adj["final_label"], adj["reference_class"], adj["namespace"]) == \
        ("tier2", "adjudicator", "ud", "independent_expert_judgment", "reference")
    assert adj["assessment_ids"] == [r["rva_id"] for r in fx["inputs"]["assessments"]]
    assert adj["agreement_stat_ref"] == BATCH
    [status] = exp["status_entries"]
    assert (status["status"], status["layer"], status["namespace"], status["basis_adjudication"]) == ("rejected", "C", "reference", 0)
    assert status["config_id"] == fx["inputs"]["target"]["config_id"]


@pytest.mark.determinism
def test_fx13a_agreement_tier1_without_adjudicator():
    fx = load("FX-13a")
    assert fx["inputs"]["target"]["g2_label"] is None
    assert labels(fx) == [("R-A", "reference", "not_hazardous", 3.0), ("R-B", "reference", "not_hazardous", 2.0)]
    assert {a["role"] for a in fx["inputs"]["annotators"]} == {"c_layer_reviewer"}
    assert fx["inputs"]["adjudicator_decision"] is None
    exp = fx["expected"]
    assert exp["mapped_system_label"] == "not_hazardous"
    [adj] = exp["adjudications"]
    assert (adj["tier"], adj["method"], adj["final_label"], adj["reference_class"]) == ("tier1", "agreement", "not_hazardous", "independent_expert_judgment")
    assert [s["status"] for s in exp["status_entries"]] == ["confirmed"]


@pytest.mark.determinism
def test_fx13b_unsure_goes_to_tier2_and_disputed():
    fx = load("FX-13b")
    assert [x[2] for x in labels(fx)] == ["unsure", "nm"]
    assert fx["inputs"]["adjudicator_decision"]["final_label"] == "unsure"
    exp = fx["expected"]
    [adj] = exp["adjudications"]
    assert (adj["tier"], adj["method"], adj["final_label"]) == ("tier2", "adjudicator", "unsure")
    assert [s["status"] for s in exp["status_entries"]] == ["disputed"]
    assert exp["ev_m12"] == {"in_kappa": False, "counted_under": "unsure"}


@pytest.mark.determinism
def test_fx13c_exposure_rule_refuses_reference_assessment():
    fx = load("FX-13c")
    prior = fx["inputs"]["prior_records"]
    assert [(r["namespace"], r["blind"], r["shown_system_output"]) for r in prior] == [("candidate_review", False, True)]
    target = fx["inputs"]["target"]
    other = fx["inputs"]["other_targets"][0]
    assert prior[0]["target_id"] == other["target_id"] != target["target_id"]
    assert other["recording_id"] == target["recording_id"]
    assert prior[0]["annotator_id"] == fx["inputs"]["assessments"][0]["annotator_id"]
    assert fx["inputs"]["assessments"][0]["namespace"] == "reference"
    assert fx["expected"] == {"refused": True, "rule": "T22.2 (b)", "stored_assessments": 0, "adjudications": [], "status_entries": []}


@pytest.mark.determinism
def test_fx13d_unblind_reference_assessment_refused():
    fx = load("FX-13d")
    [row] = fx["inputs"]["assessments"]
    assert (row["namespace"], row["shown_system_output"]) == ("reference", True)
    assert fx["expected"] == {"refused": True, "rule": "VR-E-053", "stored_assessments": 0, "adjudications": [], "status_entries": []}


@pytest.mark.determinism
def test_fx13e_audit_disagreement_reopens_tier1():
    fx = load("FX-13e")
    assert labels(fx) == [("R-A", "reference", "nm", 3.0), ("R-B", "reference", "nm", 2.0), ("ADJ", "reference", "ud", 2.0)]
    assert fx["inputs"]["audit_sample"] == [fx["inputs"]["target"]["target_id"]]
    assert fx["inputs"]["adjudicator_decision"]["final_label"] == "ud"
    exp = fx["expected"]
    first, second = exp["adjudications"]
    ids = [r["rva_id"] for r in fx["inputs"]["assessments"]]
    assert (first["tier"], first["method"], first["final_label"], first["assessment_ids"]) == ("tier1", "agreement", "nm", ids[:2])
    assert (second["tier"], second["method"], second["final_label"], second["assessment_ids"]) == ("tier2", "adjudicator", "ud", ids)
    assert [(s["status"], s["basis_adjudication"]) for s in exp["status_entries"]] == [("confirmed", 0), ("rejected", 1)]
    assert exp["audit"] == {"n_audited": 1, "n_agree": 0, "agreement_rate": 0.0}
    assert exp["tier1_record_remains"] is True


@pytest.mark.determinism
def test_fx13f_unattested_adjudicator_refused():
    fx = load("FX-13f")
    adj = by_pseudonym(fx)["ADJ"]
    assert (adj["role"], adj["independence_attestation"]) == ("adjudicator", False)
    assert [x[2] for x in labels(fx)] == ["nm", "ct"]
    assert fx["expected"] == {"refused": True, "code": "ERR-SPEC", "rule": "T22.9", "adjudications": [], "status_entries": []}
