"""T-14 part C: scoped fitness engine (E-1.2.1 sections 9.5, 9.6; Appendix T FT-01 to FT-11, CT-F-04 to CT-F-10,
CT-E-29; F.1 RV-03). Every expected decision is derived by hand from the section 9.6 rule beside each case."""
import pytest

from rq1.evaluation import fitness as ft
from rq1.schema import validate
from rq1.schema.errors import ContractError

FROZEN = "2026-11-01T09:00:00.000000Z"  # Owner-supplied event times (AR-7 review), never the clock
FIRST_TEST = "2026-11-20T12:00:00.000000Z"
TYPES = ("technical_accuracy", "completeness", "repeatability", "parameter_robustness", "comparability")


def crit(i, ctype="technical_accuracy", rule="ci_lower_ge", target=0.8, n_min=10, frozen=FROZEN):
    return {"acc_id": f"acc_{i:026d}", "criterion_label": f"C{i}", "version": "1", "output_id": "E1-recall", "criterion_type": ctype, "metric_id": "EV-M1",
            "slice": {}, "rule": rule, "target": target, "ci_level": 0.95, "estimand": "new_session_performance", "n_min_units": n_min,
            "preregistration_ref": "docs/preregistration_FROZEN.md", "frozen_utc": frozen}


def res(low, high, value=None, n=20, validity="valid", partition="test", sample="RES"):
    return {"ci_low": low, "ci_high": high, "value": value if value is not None else (low + high) / 2 if low is not None else None,
            "n_units": n, "validity": validity, "partition": partition, "sample_type": sample}


def scope(criteria, origin="synthetic_rendered", stratum="calibrated"):
    return {"output_id": "E1-recall", "measurement_definition_version": "E1_v1", "data_origin": origin, "condition_stratum": stratum,
            "calibration_tier": "ground_plane_homography", "config_id": "rcf_" + "a" * 26, "intended_use": "candidate_event_screening",
            "criterion_ids": [c["acc_id"] for c in criteria]}


def test_criterion_rules():
    c = lambda rule, t=0.8: crit(1, rule=rule, target=t)
    assert ft.decide_criterion(c("ci_lower_ge"), res(0.82, 0.90)) == "met"  # low 0.82 >= 0.8
    assert ft.decide_criterion(c("ci_lower_ge"), res(0.60, 0.75)) == "not_met"  # high 0.75 < 0.8: excludes the target, failing side
    assert ft.decide_criterion(c("ci_lower_ge"), res(0.70, 0.90)) == "inconclusive"  # straddles 0.8
    assert ft.decide_criterion(c("ci_upper_le", 0.1), res(0.02, 0.08)) == "met"
    assert ft.decide_criterion(c("ci_upper_le", 0.1), res(0.12, 0.20)) == "not_met"
    assert ft.decide_criterion(c("abs_bias_ci_within", 0.05), res(-0.04, 0.03)) == "met"  # inside [-0.05, 0.05]
    assert ft.decide_criterion(c("abs_bias_ci_within", 0.05), res(0.06, 0.09)) == "not_met"  # entirely above 0.05
    assert ft.decide_criterion(c("abs_bias_ci_within", 0.05), res(-0.02, 0.07)) == "inconclusive"
    assert ft.decide_criterion(c("exact_equal", 1.0), res(None, None, value=1.0)) == "met"
    assert ft.decide_criterion(c("exact_equal", 1.0), res(None, None, value=0.0)) == "not_met"
    # AR-44 item 2 as revised by the Architect: flip_rate_le without a stored interval is not_assessable, except for the
    # full-enumeration metrics MR-01, MR-08, MR-09, MR-12, which use [v, v]: 0.04 <= 0.05 -> met. MR-10 needs an interval.
    assert ft.decide_criterion(c("flip_rate_le", 0.05), res(None, None, value=0.04)) == "not_assessable"
    assert ft.decide_criterion({**c("flip_rate_le", 0.05), "metric_id": "MR-08"}, res(None, None, value=0.04)) == "met"
    assert ft.decide_criterion({**c("flip_rate_le", 0.05), "metric_id": "MR-08"}, res(None, None, value=0.06)) == "not_met"
    assert ft.decide_criterion({**c("flip_rate_le", 0.05), "metric_id": "MR-10"}, res(None, None, value=0.04)) == "not_assessable"


def test_not_assessable_cases():
    c = crit(1)
    assert ft.decide_criterion(c, None) == "not_assessable"  # no result
    assert ft.decide_criterion(c, res(0.82, 0.90, n=9)) == "not_assessable"  # n below n_min_units 10
    assert ft.decide_criterion(c, res(0.82, 0.90, validity="invalidated_leakage")) == "not_assessable"  # FT-07


def test_ct_f_04_synthetic_all_met_is_experimental():
    cs = [crit(i, t) for i, t in enumerate(TYPES)]
    got = ft.decide(scope(cs), cs, {c["acc_id"]: res(0.82, 0.90) for c in cs}, FIRST_TEST)
    assert set(got["criterion_decisions"].values()) == {"met"} and got["measurement_status"] == "experimental"


def test_technically_validated_needs_real_test_res_and_every_type():
    cs = [crit(i, t) for i, t in enumerate(TYPES)]
    results = {c["acc_id"]: res(0.82, 0.90) for c in cs}
    assert ft.decide(scope(cs, "real_natural"), cs, results, FIRST_TEST)["measurement_status"] == "technically_validated"
    ecs = {**results, cs[0]["acc_id"]: res(0.82, 0.90, sample="ECS")}
    assert ft.decide(scope(cs, "real_natural"), cs, ecs, FIRST_TEST)["measurement_status"] == "experimental"  # ECS never validates
    validation = {**results, cs[1]["acc_id"]: res(0.82, 0.90, partition="validation")}
    assert ft.decide(scope(cs, "real_natural"), cs, validation, FIRST_TEST)["measurement_status"] == "experimental"
    three = cs[:2] + cs[3:]  # no repeatability criterion
    assert ft.decide(scope(three, "real_natural"), three, results, FIRST_TEST)["measurement_status"] == "experimental"


def test_ct_f_05_straddling_interval_is_inconclusive_and_experimental():
    cs = [crit(1)]
    got = ft.decide(scope(cs), cs, {cs[0]["acc_id"]: res(0.70, 0.90)}, FIRST_TEST)
    assert (list(got["criterion_decisions"].values()), got["measurement_status"]) == (["inconclusive"], "experimental")


def test_ct_f_06_no_evidence_is_not_yet_assessable():
    cs = [crit(1), crit(2, "completeness")]
    got = ft.decide(scope(cs), cs, {}, FIRST_TEST)
    assert got["measurement_status"] == "not_yet_assessable"  # FT-04: never unsuitable from missing evidence


def test_ct_f_07_criterion_frozen_after_test_evaluation_is_rejected():
    late = [crit(1, frozen="2026-11-21T00:00:00.000000Z")]
    with pytest.raises(ContractError) as exc:
        ft.decide(scope(late), late, {late[0]["acc_id"]: res(0.82, 0.90)}, FIRST_TEST)
    assert exc.value.code == "ERR-INVARIANT" and "FT-02" in str(exc.value)
    same = [crit(1, frozen=FIRST_TEST)]  # "before" is strict
    with pytest.raises(ContractError):
        ft.decide(scope(same), same, {}, FIRST_TEST)


def test_ct_f_08_construct_status():
    assert ft.construct_status(None, None, None, "CV0") == "CV0"
    with pytest.raises(ContractError):
        ft.construct_status("defn-v1", None, None, "CV1")  # FT-05: CV1 needs sources too
    assert ft.construct_status("defn-v1", ["src-1"], None, "CV1") == "CV1"
    with pytest.raises(ContractError):
        ft.construct_status("defn-v1", ["src-1"], None, "CV2")  # CT-F-08: CV2 without expert result
    with pytest.raises(ContractError):
        ft.construct_status("defn-v1", ["src-1"], {"reference_class": "rule_conformance"}, "CV2")  # RV-03
    assert ft.construct_status("defn-v1", ["src-1"], {"reference_class": "independent_expert_judgment"}, "CV2") == "CV2"
    with pytest.raises(ContractError):
        ft.construct_status("defn-v1", ["src-1"], {"reference_class": "independent_expert_judgment"}, "CV3")  # FT-06


def test_ct_f_09_and_ft_11_complete_scope_key():
    cs = [crit(1)]
    for field in ft.SCOPE_FIELDS:
        broken = {**scope(cs), field: None}
        with pytest.raises(ContractError):
            ft.decide(broken, cs, {}, FIRST_TEST)


def test_ct_f_10_scopes_are_independent():
    # Clearance accuracy fails on the uncalibrated-viewpoint scope; the calibrated scope stays experimental.
    cs = [crit(1, rule="abs_bias_ci_within", target=0.10)]
    calibrated = ft.decide(scope(cs, stratum="calibrated"), cs, {cs[0]["acc_id"]: res(-0.05, 0.12)}, FIRST_TEST)
    uncalibrated = ft.decide(scope(cs, stratum="uncalibrated_viewpoint"), cs, {cs[0]["acc_id"]: res(0.15, 0.30)}, FIRST_TEST)
    assert (calibrated["measurement_status"], uncalibrated["measurement_status"]) == ("experimental", "unsuitable_under_tested_conditions")
    assert uncalibrated["failing_interval"] == {"low": 0.15, "high": 0.30}  # recorded with the not_met result


def test_ct_e_29_and_ft_01_ft_03_ft_08_stored_status_checks():
    cs = [crit(i, t) for i, t in enumerate(TYPES)]
    decided = ft.decide(scope(cs), cs, {c["acc_id"]: res(0.82, 0.90) for c in cs}, FIRST_TEST)  # synthetic -> experimental
    with pytest.raises(ContractError):
        ft.check_record({"measurement_status": "technically_validated"}, decided)  # CT-E-29 / FT-01
    with pytest.raises(ContractError):
        ft.check_record({"measurement_status": "technically_validated", "override": {"downgrade_only": True}}, decided)  # FT-08: no upgrade
    ft.check_record({"measurement_status": "not_yet_assessable", "override": {"downgrade_only": True, "rationale": "r", "actor": "owner"}}, decided)
    with pytest.raises(ContractError):  # FT-03: unsuitable needs a recorded not_met
        ft.check_record({"measurement_status": "unsuitable_under_tested_conditions", "override": {"downgrade_only": True}}, decided)


def test_residual_status_is_experimental():
    # Appendix T T12.5 (replaces the earlier refusal): only a repeatability criterion is not_met, the other not_assessable,
    # so the status is experimental and failing_interval records the repeatability interval (0.60, 0.70).
    cs = [crit(1, "repeatability"), crit(2, "technical_accuracy")]
    got = ft.decide(scope(cs), cs, {cs[0]["acc_id"]: res(0.60, 0.70)}, FIRST_TEST)
    assert (got["measurement_status"], got["failing_interval"]) == ("experimental", {"low": 0.60, "high": 0.70})


def test_measurement_fitness_row_matches_the_schema():
    cs = [crit(1)]
    sc = {**scope(cs), "config_id": "rcf_" + "a" * 26, "criterion_ids": ["acc_" + "1" * 26]}
    decided = ft.decide(sc, cs, {}, FIRST_TEST)
    row = ft.fitness_row(sc, decided, "CV0", {"definition_evidence_ref": None, "definition_evidence_ref_null_reason": "not_supplied",
                                              "source_refs": None, "source_refs_null_reason": "not_supplied",
                                              "expert_alignment_result_id": None, "expert_alignment_result_id_null_reason": "not_supplied"}, False)
    assert validate.validate_row("measurement_fitness", row) == []
    assert row["interpretation_note"] == "Agreement with expert judgment does not show that the measure predicts injuries."  # section 9.5
