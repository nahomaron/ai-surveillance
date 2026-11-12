"""T-14 part A: error attribution (E-1.2.1 section 9.4; F.1 Appendix N9; F.1 A5.2 FX-ID-8; VR-E-061).
Expected values come from the fixtures or the N9 rule text; each case states its hand reasoning."""
import json
from pathlib import Path

import pytest

from rq1.evaluation import association as assoc
from rq1.evaluation import attribution as att

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
PARAMS = json.loads((FIX / "TEST-ONLY-PARAMETERS.json").read_text())["parameters"]
N_MISS, IOU_CM = PARAMS["n_miss"], PARAMS["iou_cm"]  # 5 (AR-19), 0.5


def boxes(fixture_id):
    """Per-frame reference and system boxes of an FX-ID fixture."""
    inputs = json.loads((FIX / f"{fixture_id}.json").read_text())["inputs"]
    ref, sys_ = {}, {}
    for seg in inputs["segments"]:
        for i in range(seg["start"], seg["end_excl"]):
            (sys_ if seg["side"] == "system" else ref).setdefault(i, []).append((seg["object"], seg["class"], tuple(seg["box"])))
    return inputs, ref, sys_


@pytest.mark.determinism
def test_fx_id_8_false_alert_attributed_to_perception():
    # F.1 A5.2 FX-ID-8: the person track A has no reference person within n_miss frames, so rule 2 fails: primary = perception.
    inputs, ref, sys_ = boxes("FX-ID-8")
    expected = json.loads((FIX / "FX-ID-8.json").read_text())["expected"]
    event = inputs["event"]
    ca = event["closest_approach_frame"]
    as_boxes = lambda items: [assoc.Box(o, c, b) for o, c, b in items]
    rows = assoc.associate({i: (as_boxes(sys_.get(i, [])), as_boxes(ref.get(i, []))) for i in range(inputs["n_frames"])}, IOU_CM, PARAMS["eps_amb"])
    results = {
        "evidence_unavailable": att.rule_evidence_unavailable(True, "usable"),  # the fixture's footage is usable at frame 12
        "perception": att.rule_perception_false_alert(ref, sys_, (event["person_track"], event["forklift_track"]), ca, N_MISS, IOU_CM),
        "tracking": not any(r["track_id"] == event["person_track"] and r["status"] == "matched" for r in rows if r["frame_index"] == ca),
    }
    got = att.diagnose(results)
    assert (got["primary_stage"], got["attribution_status"]) == (expected["primary_stage"], "diagnostic_inferred")
    assert got["secondary_factors"] == ["tracking"]  # A is also unmatched: a later failing test becomes secondary
    assert got["rule_test_results"] == {"evidence_unavailable": "pass", "perception": "fail", "tracking": "fail"}


def test_n9_pipeline_order_and_unresolved():
    got = att.diagnose({"geometry": True, "perception": True, "tracking": False, "linkage": None})
    assert (got["primary_stage"], got["secondary_factors"]) == ("perception", ["geometry"])  # pipeline order, not dict order
    assert got["rule_test_results"]["linkage"] == "not_evaluated"
    none = att.diagnose({s: False for s in att.STAGES})
    assert (none["primary_stage"], none["secondary_factors"], none["attribution_status"]) == ("unresolved", [], "unresolved")
    with pytest.raises(ValueError):
        att.diagnose({"detector": True})


def test_rule_1_evidence_unavailable():
    assert att.rule_evidence_unavailable(False, "usable")  # reference unobservable at CA
    assert att.rule_evidence_unavailable(True, "unusable") and att.rule_evidence_unavailable(True, "gap_unobserved")
    assert not att.rule_evidence_unavailable(True, "usable") and not att.rule_evidence_unavailable(True, "usable_degraded")  # AR-42 item 2


@pytest.mark.determinism
def test_rule_2_perception_for_a_miss():
    # FX-ID-4: p2 present on every frame, never detected -> a miss on pair (p2, f) fails rule 2 at any CA frame.
    _, ref, sys_ = boxes("FX-ID-4")
    assert att.rule_perception_miss(ref, sys_, ("p2",), 25, N_MISS, IOU_CM)
    # FX-ID-3: p1 detected on frames 0-19 and 25-49 with identical boxes (IoU 1). At CA 22, frames 17-27 hold detections -> passes.
    _, ref, sys_ = boxes("FX-ID-3")
    assert not att.rule_perception_miss(ref, sys_, ("p1",), 22, N_MISS, IOU_CM)
    # With n_miss = 2, frames 20-24 have no detection at all -> fails.
    assert att.rule_perception_miss(ref, sys_, ("p1",), 22, 2, IOU_CM)


def test_rule_3_tracking():
    rows = [{"frame_index": 10, "physical_identity_id": "p1", "status": "matched"}, {"frame_index": 10, "physical_identity_id": "f1", "status": "ambiguous"}]
    assert att.rule_tracking(rows, ("p1", "f1"), 10, [], (5, 15))  # forklift not matched at CA
    rows[1]["status"] = "matched"
    assert not att.rule_tracking(rows, ("p1", "f1"), 10, [], (5, 15))
    assert att.rule_tracking(rows, ("p1", "f1"), 10, [12], (5, 15))  # POW break inside the reference interval
    assert not att.rule_tracking(rows, ("p1", "f1"), 10, [15], (5, 15))  # end-exclusive


def test_rule_4_geometry_and_rule_5_event_reasoning_and_rule_7():
    # k_sigma 2, sigma 0.05: |error| 0.12 > 0.10 at a frame whose decision differs -> fails; 0.08 does not; M flip does.
    differs = lambda e, ms=1, mr=1: {"decision_differs": True, "clearance_error_m": e, "sigma_m": 0.05, "m_system": ms, "m_reference": mr}
    assert att.rule_geometry([differs(0.12)], 2.0) and not att.rule_geometry([differs(0.08)], 2.0)
    assert att.rule_geometry([differs(0.0, 1, 0)], 2.0)
    assert not att.rule_geometry([{**differs(0.5), "decision_differs": False}], 2.0)  # only where the decision differs
    assert att.rule_event_reasoning(True, False) and not att.rule_event_reasoning(True, True)
    assert att.rule_reference_ambiguity("T2", False) and att.rule_reference_ambiguity("T1", True) and not att.rule_reference_ambiguity("T1", False)


def test_oracle_runner_covers_the_2_cubed_sets():
    # FX-16 shape (Appendix T): injected perception and geometry errors, resolved only when both are substituted.
    sets = att.oracle_subsets()
    assert len(sets) == 8 and sets[0] == frozenset() and sets[-1] == frozenset(att.ORACLE_STAGES)
    outcomes = att.oracle_outcomes(lambda s: not {"perception", "geometry"} <= s)
    assert [s for s, resolved in outcomes.items() if resolved] == [frozenset({"perception", "geometry"}), frozenset(att.ORACLE_STAGES)]
    # T12.3 then assigns the status (CT-E-22, test_t12_oracle.py).
    resolved = {s for s, ok in outcomes.items() if ok}
    record, _ = att.oracle_attribution({}, resolved, {s: f"art_{i:026d}" for i, s in enumerate(sets)})
    assert (record["primary_stage"], record["attribution_status"]) == ("perception", "verified_oracle_joint")


def test_vr_e_061_verified_only_on_synthetic_with_oracle_runs():
    row = {"attribution_status": "verified_oracle_joint", "oracle_artifact_ids": ["art_" + "a" * 26]}
    assert att.check([row], "synthetic_rendered") == []
    assert [i.rule for i in att.check([row], "real_natural")] == ["VR-E-061"]  # section 9.4: forbidden on real data
    assert [i.rule for i in att.check([{**row, "oracle_artifact_ids": []}], "synthetic_rendered")] == ["VR-E-061"]
    assert att.check([{"attribution_status": "diagnostic_inferred", "oracle_artifact_ids": []}], "real_natural") == []
