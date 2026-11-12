"""CT-T12-03 and CT-E-22: Appendix T T12.3 (contract E-1.2.10) oracle-factorial attribution. Expected values are the
T12.3 checks; the extra cases are hand-derived from T12.3 steps 1 to 5."""
import pytest

from rq1.evaluation import attribution as att

P, T, G = "perception", "tracking", "geometry"
RUNS = {s: f"art_{'_'.join(sorted(s)) or 'none'}" for s in att.oracle_subsets()}


def supersets(*stages):
    return {s for s in att.oracle_subsets() if set(stages) <= s}


def test_ct_e_22_fx_16_joint():
    # FX-16: R = all supersets of {perception, geometry}; M = {{P, G}}, k = 2.
    record, diag = att.oracle_attribution({}, supersets(P, G), RUNS)
    assert (record["primary_stage"], record["secondary_factors"], record["attribution_status"]) == (P, [G], "verified_oracle_joint")
    assert record["oracle_artifact_ids"] == [RUNS[frozenset({P, G})]]  # runs of the sets in M
    assert att.check([record], "synthetic_rendered") == []  # VR-E-061 holds
    assert diag["non_monotone_sets"] == []


@pytest.mark.parametrize("resolved", [{frozenset({P})}, supersets(P)])
def test_ct_t12_03_perception_alone(resolved):
    record, _ = att.oracle_attribution({}, resolved, RUNS)
    assert (record["primary_stage"], record["secondary_factors"], record["attribution_status"]) == (P, [], "verified_oracle_single")


def test_ct_t12_03_tie_between_single_stages():
    # {P} and {G} each resolve: M = {{P}, {G}}, k = 1; the earliest stage in their union is perception.
    record, _ = att.oracle_attribution({}, supersets(P) | supersets(G), RUNS)
    assert (record["primary_stage"], record["secondary_factors"], record["attribution_status"]) == (P, [G], "verified_oracle_single")
    assert record["oracle_artifact_ids"] == sorted([RUNS[frozenset({P})], RUNS[frozenset({G})]])


def test_ct_t12_03_nothing_resolves():
    failing_5 = {"tracking": False, "geometry": False, "event_reasoning": True}
    record, _ = att.oracle_attribution(failing_5, set(), RUNS)
    assert (record["primary_stage"], record["attribution_status"]) == ("event_reasoning", "diagnostic_inferred")
    record, _ = att.oracle_attribution({"reference_ambiguity": True}, set(), RUNS)
    assert (record["primary_stage"], record["attribution_status"]) == ("reference_ambiguity", "diagnostic_inferred")
    record, _ = att.oracle_attribution({s: False for s in att.STAGES}, set(), RUNS)
    assert (record["primary_stage"], record["attribution_status"], record["oracle_artifact_ids"]) == ("unresolved", "unresolved", [])


def test_t12_3_step_1_evidence_unavailable_skips_the_factorial():
    record, _ = att.oracle_attribution({"evidence_unavailable": True}, supersets(P), RUNS)
    assert (record["primary_stage"], record["attribution_status"], record["oracle_artifact_ids"]) == ("evidence_unavailable", "diagnostic_inferred", [])


def test_t12_3_step_4_report_diagnostics():
    # {T} resolves but its superset {T, G} does not: non-monotone, counted for the milestone report.
    resolved = {frozenset({T}), frozenset({P, T}), frozenset({P, T, G})}
    record, diag = att.oracle_attribution({"perception": True}, resolved, RUNS)
    assert (record["primary_stage"], record["attribution_status"]) == (T, "verified_oracle_single")
    # M = {{T}} ({P, T} contains {T}); the rule tests say perception, so the two disagree. {T} resolves while {T, G} does not.
    assert diag == {"rule_primary": P, "disagrees": True, "non_monotone_sets": [[T]]}
    with pytest.raises(ValueError):
        att.oracle_attribution({}, {frozenset()}, RUNS)  # Resolved(empty) is false by construction


def test_t12_3_step_5_prerequisites():
    # Rule 4 needs rule 3 to pass; rule 5 needs rule 4 (and so rule 3) to pass. Not evaluated otherwise.
    got = att.diagnose({"tracking": True, "geometry": True, "event_reasoning": True})
    assert (got["primary_stage"], got["secondary_factors"]) == ("tracking", [])
    assert got["rule_test_results"] == {"tracking": "fail", "geometry": "not_evaluated", "event_reasoning": "not_evaluated"}
    got = att.diagnose({"tracking": False, "geometry": True, "event_reasoning": True})
    assert (got["primary_stage"], got["rule_test_results"]["event_reasoning"]) == ("geometry", "not_evaluated")
