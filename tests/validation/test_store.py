"""T-11: validation store. F.1 A3 (FX-RC, CT-RC), A5.1 (RV), E-1.2.1 section 5.8; Appendix T CT-E-24, CT-E-25, VR-E-052/053/055."""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from rq1.fixtures import synthetic_s1
from rq1.ids import core
from rq1.ids.artifact import Spec, build_artifact
from rq1.schema import validate, vr_rules
from rq1.schema.errors import ContractError
from rq1.validation import converter, coverage_rules, namespace, status_log

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
WF = core.anchor_id("wf", "world_frame", ["w"])


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


def window(exhaustive=True, inputs=None):
    i = inputs or fx("FX-RC-1")["inputs"]
    return {"rwn_id": "rwn_" + "w" * 26, "t_start_tl_s": i["window_t_start_tl_s"], "t_end_tl_s": i["window_t_end_tl_s"],
            "t_guard_end_tl_s": i["t_guard_end_tl_s"], "exhaustive": exhaustive}


def forklift_everywhere(n):
    return {"objects": [{"physical_identity_id": "f1", "class": "forklift", "frames": {i: {"bbox": [10.0, 10.0, 50.0, 40.0], "xy": [1.0, 2.0]} for i in range(n)}}],
            "interactions": []}


def unobservable(spans):
    return [{"t_start_tl_s": round(s["t_start_tl_s"], 9), "t_end_tl_s": round(s["t_end_tl_s"], 9), "reason": s["unobservable_reason"],
             "eligible_support_s": round(s["eligible_support_s"], 9), "frames": s["start_frame"]} for s in spans if s["ref_activity_state"] == "unobservable"]


def convert(s1, truth, win=None):
    return converter.SimReferenceConverter().convert(win or window(), s1, truth, WF)


# CT-RC-01: FX-RC-1 to 5 produce exactly the listed spans and durations
@pytest.mark.determinism
def test_fx_rc_1_corrupt_frames():
    expected = fx("FX-RC-1")["expected"]["unobservable_spans"][0]
    s1 = synthetic_s1.build(350, excluded=frozenset(range(100, 115)))
    spans = convert(s1, forklift_everywhere(335))["ref_coverage_label"]
    assert unobservable(spans) == [{"t_start_tl_s": expected["t_start_tl_s"], "t_end_tl_s": expected["t_end_tl_s"], "reason": expected["reason"],
                                    "eligible_support_s": 0.0, "frames": None}]
    present = sum(s["eligible_support_s"] for s in spans if s["ref_activity_state"] == "objects_present_no_interaction")
    assert present == pytest.approx(35.0 - expected["excluded_support_s"], abs=1e-9)  # RC-04: the 1.5 s is in no reference duration


@pytest.mark.determinism
def test_fx_rc_2_dropout():
    expected = fx("FX-RC-2")["expected"]["unobservable_spans"][0]
    s1 = synthetic_s1.build(321, dropouts={200: 2.9})  # frame 201 starts at 23.0 s
    spans = convert(s1, forklift_everywhere(321))["ref_coverage_label"]
    assert unobservable(spans) == [{"t_start_tl_s": expected["t_start_tl_s"], "t_end_tl_s": expected["t_end_tl_s"], "reason": expected["reason"],
                                    "eligible_support_s": 0.0, "frames": expected["frame_bounds"]}]


@pytest.mark.determinism
def test_fx_rc_3_not_recording():
    expected = fx("FX-RC-3")["expected"]["unobservable_spans"][0]
    s1 = synthetic_s1.build(250)
    gap = dict(s1["coverage_segment"][0], cov_id="cov_" + "n" * 26, recording_id=None, t_start_tl_s=25.0, t_end_tl_s=35.0, coverage_state="not_recorded")
    s1["coverage_segment"].append(gap)
    spans = convert(s1, forklift_everywhere(250))["ref_coverage_label"]
    assert unobservable(spans) == [{"t_start_tl_s": 25.0, "t_end_tl_s": 35.0, "reason": expected["reason"], "eligible_support_s": 0.0, "frames": expected["frame_bounds"]}]


@pytest.mark.determinism
def test_fx_rc_4_forklift_present_system_detects_nothing():
    expected = fx("FX-RC-4")["expected"]
    s1 = synthetic_s1.build(350)
    spans = convert(s1, forklift_everywhere(350))["ref_coverage_label"]
    assert {s["ref_activity_state"] for s in spans} == {expected["ref_activity_state"]}


@pytest.mark.determinism
def test_fx_rc_5_verified_absent_only_from_validation_store():
    expected = fx("FX-RC-5")["expected"]
    s1 = synthetic_s1.build(350)
    out = convert(s1, {"objects": [], "interactions": []})
    spans = out["ref_coverage_label"]
    assert {s["ref_activity_state"] for s in spans} == {expected["ref_activity_state"]}
    assert all(s["label_source"] == "simulator_truth" and s["eligible_support_s"] > 0 for s in spans)
    assert sum(s["eligible_support_s"] for s in spans) == pytest.approx(35.0, abs=1e-9)  # RC-04: support, not span length
    assert coverage_rules.check(spans, window(), s1["coverage_segment"], s1["frame"]) == []


@pytest.mark.determinism
def test_not_exhaustive_window_never_verified_absent():
    spans = convert(synthetic_s1.build(350), {"objects": [], "interactions": []}, window(exhaustive=False))["ref_coverage_label"]
    assert "reference_verified_absent" not in {s["ref_activity_state"] for s in spans}


# CT-RC-02: FX-RC-6 rejected
@pytest.mark.determinism
def test_fx_rc_6_rejected():
    expected = fx("FX-RC-6")["expected"]["rejected_by"]
    s1 = synthetic_s1.build(321, dropouts={200: 2.9})
    spans = convert(s1, forklift_everywhere(321))["ref_coverage_label"]
    bad = [dict(s, ref_activity_state="reference_verified_absent", unobservable_reason=None, unobservable_reason_null_reason="not_applicable")
           if s["ref_activity_state"] == "unobservable" else s for s in spans]
    assert sorted({i.rule for i in coverage_rules.check(bad, window(), s1["coverage_segment"], s1["frame"])}) == expected


# CT-RC-03: random coverage timelines
@pytest.mark.determinism
@pytest.mark.parametrize("seed", range(40))
def test_ct_rc_03_property(seed):
    rng = random.Random(seed)
    n = 350
    excluded = frozenset(i for i in range(n) if rng.random() < 0.05)
    dropouts = {i: round(rng.choice([0.5, 1.0, 2.0]), 1) for i in range(n - 1) if rng.random() < 0.01}
    s1 = synthetic_s1.build(n, excluded=excluded, dropouts=dropouts)
    end = s1["coverage_segment"][-1]["t_end_tl_s"]
    win = {"rwn_id": "rwn_" + "w" * 26, "t_start_tl_s": 0.0, "t_end_tl_s": min(30.0, end), "t_guard_end_tl_s": min(35.0, end), "exhaustive": True}
    eligible = sum(1 for f in s1["frame"] if f["eligible"])
    present = {i for i in range(eligible) if rng.random() < 0.5}
    truth = {"objects": [{"physical_identity_id": "f1", "class": "forklift", "frames": {i: {"bbox": [1.0, 1.0, 5.0, 5.0], "xy": [0.0, 0.0]} for i in present}}], "interactions": []}
    spans = convert(s1, truth, win)["ref_coverage_label"]
    assert coverage_rules.check(spans, win, s1["coverage_segment"], s1["frame"]) == []  # RC-01 to RC-04


def test_rc_05_and_vr_e_040_no_reference_state_in_observation_store():
    assert [i.rule for i in coverage_rules.check_rc_05("activity_segment", [{"ai_activity_state": "reference_verified_absent"}])] == ["RC-05"]


@pytest.mark.determinism
def test_reference_tables_build_as_cv_sim_artifact_and_validate():
    s1 = synthetic_s1.build(350)
    tables = convert(s1, forklift_everywhere(350))
    built = build_artifact(Spec("CV-SIM", "E-1.2.6", "f", "f", (), ("art_" + "a" * 26,), {}), tables)
    for table, rows in built.tables.items():
        assert vr_rules.check_ids(table, rows, built.artifact_id) == [], table
        for row in rows:
            assert row["reference_class"] == "independent_perceptual_geometric" and row["label_source"] == "simulator_truth"
    presence = built.tables["ref_object_presence"][0]
    # Annotation covers the window plus its guard (section 8): eligible frames inside [0, 35).
    assert presence["presence_intervals"] == [{"start_frame": 0, "end_frame_excl": 350}]
    assert len(built.tables["ref_geometry"]) == 350


@pytest.mark.determinism
def test_rv_01_interaction_references_are_rule_conformance():
    s1 = synthetic_s1.build(350)
    truth = forklift_everywhere(350)
    truth["objects"].append({"physical_identity_id": "p1", "class": "person", "frames": {i: {"bbox": [60.0, 10.0, 80.0, 60.0], "xy": [1.0, 3.0]} for i in range(350)}})
    truth["interactions"] = [{"person": "p1", "forklift": "f1", "t_onset_tl_s": 5.0, "t_offset_tl_s": 8.0, "evasive_action": "no"}]
    out = convert(s1, truth)
    assert out["ref_interaction"][0]["reference_class"] == "rule_conformance"  # RV-01
    states = {(round(s["t_start_tl_s"], 9), round(s["t_end_tl_s"], 9), s["ref_activity_state"]) for s in out["ref_coverage_label"]}
    assert (5.0, 8.0, "interaction_present") in states


def test_rv_02_rule_conformance_results_carry_no_claim():
    rows = [{"metric_id": "EV-M1", "reference_class": "rule_conformance", "claim_level": "L2"}]
    assert [i.rule for i in namespace.check_rv_02(rows)] == ["RV-02"]
    assert namespace.check_rv_02([{**rows[0], "claim_level": "none"}]) == []


# CT-E-25 and VR-E-055 namespace guard
def test_ct_e_25_candidate_review_label_as_reference():
    record = {"namespace": "candidate_review", "label_source": "human_corrected_from_model"}
    with pytest.raises(ContractError) as exc:
        namespace.require_reference(record)
    assert exc.value.code == "ERR-NAMESPACE"
    with pytest.raises(ContractError):
        namespace.require_reference({"namespace": "reference", "label_source": "model_only"})
    namespace.require_reference({"namespace": "reference", "label_source": "human_manual", "blind_to_system": True})


def test_vr_e_053_reference_records_are_blind():
    with pytest.raises(ContractError):
        namespace.require_reference({"namespace": "reference", "label_source": "human_manual", "blind_to_system": False})


# CT-E-24: status log hash chain; episode labels unchanged
@pytest.mark.determinism
def test_ct_e_24_status_log(tmp_path):
    episode_rows = {"episode": [__import__("rq1.fixtures.identity_rows", fromlist=["x"]).episode("pow_" + "a" * 26, 0)]}
    built = build_artifact(Spec("S5", "E-1.2.6", "f", "f", ("rcf_" + "a" * 26,), (), {}), episode_rows)
    before = json.dumps(built.tables, default=str, sort_keys=True)
    log = status_log.StatusLog(tmp_path / "status.jsonl")
    target = built.tables["episode"][0]["ep_id"]
    for k, status in enumerate(["unreviewed", "confirmed"]):
        log.append(target_type="system_episode", target_id=target, config_id="rcf_" + "a" * 26, status=status, layer="C", namespace="reference",
                   basis_ids=[], actor_id="anr_018f3a2e-7b1c-7def-8a12-3456789abcde", created_utc=T0 + timedelta(minutes=k))
    assert json.dumps(built.tables, default=str, sort_keys=True) == before  # labels unchanged
    assert log.verify() == []
    entries = [json.loads(line) for line in (tmp_path / "status.jsonl").read_text().splitlines()]
    assert [e["seq"] for e in entries] == [0, 1] and entries[1]["prev_hash"] == entries[0]["record_hash"]
    assert entries[0]["prev_hash"] == "0" * 64  # AR-36 genesis value
    for e in entries:
        row = dict(e, created_utc=datetime.fromisoformat(e["created_utc"]))
        assert validate.validate_row("validation_status_log", row) == []
    lines = (tmp_path / "status.jsonl").read_text().splitlines()
    tampered = json.loads(lines[0])
    tampered["status"] = "rejected"
    (tmp_path / "status.jsonl").write_text(json.dumps(tampered) + "\n" + lines[1] + "\n")
    assert [i.rule for i in log.verify()] == ["CT-E-24"]


@pytest.mark.determinism
def test_status_log_is_append_only(tmp_path):
    log = status_log.StatusLog(tmp_path / "s.jsonl")
    log.append(target_type="system_episode", target_id="ep_" + "a" * 26, config_id="rcf_" + "a" * 26, status="unreviewed", layer="C",
               namespace="reference", basis_ids=[], actor_id="anr_018f3a2e-7b1c-7def-8a12-3456789abcde", created_utc=T0)
    assert not hasattr(log, "update") and not hasattr(log, "delete")
