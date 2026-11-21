"""Appendix T T23.16 and T23.25 (d) (contract E-1.2.23; D-49) in the V-02 store: FX-14l and FX-14n.

Expected values are retyped from the D-49.1 section 6.1 table (fixtures FX-14l, FX-14n)."""
from __future__ import annotations

import pytest

from conftest import clip_target, load_fixture
from rq1.review.frame import FixtureFrame
from rq1.schema.errors import ContractError
from rq1.validation import reference as REF

WF_AM = "workflow area_manager (T23): manager decision record, not a reference reviewer"
WF_SM = "workflow safety_manager (T23): manager decision record, not a reference adjudicator"
REVIEWERS = [{"anr_id": "anr_" + f"fx14l{p}".ljust(26, "0"), "role": "c_layer_reviewer", "pseudonym": f"R-{p.upper()}",
              "qualification_ref": "completed T22 handbook training and pilot batch, 2026-11-19", "independence_attestation": True}
             for p in "ab"]
WHY = "The forklift brakes hard as the person steps out."


def _cr_target(tid: str) -> dict:
    return {"target_type": "system_episode", "target_id": tid, "recording_id": "rec_" + tid[3:], "config_id": "rcf_" + "bl6fx14".ljust(26, "0"),
            "g2_label": "lbl_nm", "summary_label": "NM"}


def _cr_records(store, targets):
    """Three candidate_review assessment + adjudication pairs, as the workflow writes them (T23.5 a, c)."""
    am = store.add_annotator("AM-X", "c_layer_reviewer", WF_AM, False, "pw-am")["anr_id"]
    sm = store.add_annotator("SM-X", "adjudicator", WF_SM, False, "pw-sm")["anr_id"]
    out = []
    for t in targets:
        rva = store.import_candidate_review(
            {"rva_id": "rva_" + t["target_id"][3:], "annotator_id": am, "namespace": "candidate_review", "target_type": "system_episode",
             "target_id": t["target_id"], "label": "not_hazardous", "confidence": 3.0, "rationale": "Parked truck.", "blind": False,
             "shown_system_output": True, "review_time_s": None, "review_time_s_null_reason": "not_observable",
             "submitted_utc": "2026-11-19T10:00:00.000000Z"}, t["recording_id"])
        out.append(store.add_candidate_review_adjudication(t, "nm", [rva["rva_id"]], sm, report_id="rpt_" + "fx14l".ljust(26, "0")))
    return out


def test_fx14l_candidate_review_records_never_enter_reference_statistics(make_app, video):
    exp = load_fixture("FX-14l")["expected"]
    fx = load_fixture("FX-14l")["inputs"]
    app = make_app(targets=[clip_target(fx["reference_target"], video)], annotators=REVIEWERS)
    assert app.assess("R-A", "nm", 3.0, WHY)[0] == 303 and app.assess("R-B", "nm", 2.0, WHY)[0] == 303
    [ref] = [e["row"] for e in app.store.adjudications() if e["row"]["namespace"] == "reference"]
    assert (ref["tier"], ref["method"], ref["reference_class"]) == ("tier1", "agreement", "independent_expert_judgment")
    cr = _cr_records(app.store, [_cr_target(t) for t in fx["candidate_targets"]])
    assert len(cr) == exp["candidate_review_adjudications"]
    assert all(r["reference_class"] is None and r["reference_class_null_reason"] == "not_applicable" for r in cr)
    assert len(REF.reference_adjudications(app.store.root)) == exp["reference_adjudications"]
    assert len(REF.ev_m12_population(app.store.root)["pairs"]) == exp["ev_m12_targets"]
    assert app.store.agreement(app.batch)["n_targets"] == exp["kappa_targets"]
    # a later T22 batch: the three candidate_review targets are not treated as reviewed (T22.14 c counts batch targets only)
    reviewers = [a["anr_id"] for a in REVIEWERS]
    later = app.store.create_batch(FixtureFrame([clip_target(_cr_target(t), video) for t in fx["candidate_targets"]],
                                                config_id=_cr_target(fx["candidate_targets"][0])["config_id"]), 7, reviewers, None, pilot=False)
    assert later["target_ids"] == sorted(fx["candidate_targets"]) and later["excluded_earlier_targets"] == 3 + 1
    assert exp["later_batch_unchanged"] is True


def test_t23_16_a_mixed_namespaces_are_refused(make_app, video):
    fx = load_fixture("FX-14l")["inputs"]
    app = make_app(targets=[clip_target(fx["reference_target"], video)], annotators=REVIEWERS)
    app.assess("R-A", "nm", 3.0, WHY)
    ref_rva = [e["row"]["rva_id"] for e in app.store.assessments() if e["row"]["namespace"] == "reference"]
    sm = app.store.add_annotator("SM-Y", "adjudicator", WF_SM, False, "pw")["anr_id"]
    before = (app.store.root / "adjudication.jsonl").read_bytes() if (app.store.root / "adjudication.jsonl").exists() else b""
    with pytest.raises(ContractError) as err:
        app.store.add_candidate_review_adjudication(_cr_target(fx["candidate_targets"][0]), "nm", ref_rva, sm, report_id=None)
    assert err.value.code == "ERR-SPEC" and "T23.16 (a)" in str(err.value)
    after = (app.store.root / "adjudication.jsonl").read_bytes() if (app.store.root / "adjudication.jsonl").exists() else b""
    assert after == before


def test_fx14n_workflow_manager_row_is_refused_for_reference_at_once(make_app, video):
    fx = load_fixture("FX-14n")
    app = make_app(targets=[clip_target(load_fixture("FX-14l")["inputs"]["reference_target"], video)], annotators=REVIEWERS)
    target = app.store.manifest(app.batch)["target_ids"][0]
    am = app.store.add_annotator("AM-W", "c_layer_reviewer", fx["inputs"]["qualification_ref"], False, "pw")["anr_id"]
    with pytest.raises(ContractError) as err:
        app.store.submit(app.batch, target, am, "nm", 2.0, WHY)
    assert fx["expected"]["rule"] in str(err.value) and err.value.code == "ERR-SPEC"
    sm = app.store.add_annotator("SM-W", "adjudicator", WF_SM, False, "pw")["anr_id"]
    with pytest.raises(ContractError) as err:
        app.store.adjudicate(app.batch, target, sm, "nm")
    assert "T23.25 (d)" in str(err.value)
    assert not [e for e in app.store.assessments() if e["row"]["annotator_id"] in (am, sm)]
