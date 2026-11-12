"""Scoped fitness engine (E-1.2.1 sections 9.5, 9.6; Appendix T FT-01 to FT-11; F.1 A5.1 RV-03).

Criterion decisions come from stored metric results; the status follows the section 9.6 rule per scope, and scopes are
never merged. Event times (`acceptance_criterion.frozen_utc`, the first test-partition evaluation) are supplied from
the Owner's records and the execution record, never read from the clock (AR-7 review)."""
from __future__ import annotations

from datetime import datetime

from rq1.schema.errors import ContractError

SCOPE_FIELDS = ("output_id", "measurement_definition_version", "data_origin", "condition_stratum", "calibration_tier", "config_id", "intended_use", "criterion_ids")
GATED_TYPES = ("technical_accuracy", "completeness", "repeatability", "parameter_robustness")
STATUS_RANK = {"not_yet_assessable": 0, "unsuitable_under_tested_conditions": 1, "experimental": 2, "technically_validated": 3}
INTERPRETATION_NOTE = "Agreement with expert judgment does not show that the measure predicts injuries."
UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc(text: str) -> datetime:
    return datetime.strptime(text, UTC_FORMAT)


def check_frozen_before_test(criteria: list[dict], first_test_evaluation_utc: str | None) -> None:
    """FT-02 (CT-F-07): every criterion used was frozen before its first test-partition evaluation."""
    if first_test_evaluation_utc is None:
        return
    late = sorted(c["criterion_label"] for c in criteria if _utc(c["frozen_utc"]) >= _utc(first_test_evaluation_utc))
    if late:
        raise ContractError("ERR-INVARIANT", f"FT-02: criteria frozen after the first test-partition evaluation: {late}")


def decide_criterion(criterion: dict, result: dict | None) -> str:
    """Section 9.6 criterion decision. `result` is the stored metric_result with its context: `partition`."""
    if result is None or result["validity"] != "valid" or result["n_units"] < criterion["n_min_units"]:
        return "not_assessable"  # no valid result (FT-07: invalidated_leakage ignored), or n below n_min_units
    rule, t = criterion["rule"], criterion["target"]
    low, high, value = result.get("ci_low"), result.get("ci_high"), result.get("value")
    if rule == "exact_equal" or (rule == "flip_rate_le" and (low is None or high is None)):
        if value is None:
            return "not_assessable"
        return ("met" if value == t else "not_met") if rule == "exact_equal" else ("met" if value <= t else "not_met")
    if low is None or high is None:
        return "not_assessable"
    if rule in ("ci_upper_le", "flip_rate_le"):
        return "met" if high <= t else ("not_met" if low > t else "inconclusive")
    if rule == "ci_lower_ge":
        return "met" if low >= t else ("not_met" if high < t else "inconclusive")
    if rule == "abs_bias_ci_within":
        return "met" if -t <= low and high <= t else ("not_met" if low > t or high < -t else "inconclusive")
    raise ContractError("ERR-UNKNOWN-ENUM", f"rule {rule}")


def construct_status(definition_evidence_ref: str | None, source_refs: list[str] | None, expert_result: dict | None, requested: str) -> str:
    """Section 9.5, FT-05, FT-06, RV-03 (CT-F-08). Returns the requested status if its evidence is present; refuses otherwise."""
    if requested not in ("CV0", "CV1", "CV2"):
        raise ContractError("ERR-INVARIANT", f"FT-06: no construct status above CV2 can be stored ({requested})")
    if requested in ("CV1", "CV2") and not (definition_evidence_ref and source_refs):
        raise ContractError("ERR-INVARIANT", "FT-05: CV1 needs a versioned definition and cited source references")
    if requested == "CV2" and (expert_result is None or expert_result.get("reference_class") != "independent_expert_judgment"):
        raise ContractError("ERR-INVARIANT", "FT-05 / RV-03: CV2 needs an expert-alignment result with reference_class independent_expert_judgment")
    return requested


def decide(scope: dict, criteria: list[dict], results: dict[str, dict | None], first_test_evaluation_utc: str | None) -> dict:
    """Section 9.6 status for one scope. `criteria` are acceptance_criterion rows with `acc_id`; `results` maps acc_id to
    the stored metric_result (with context `partition`) or None. Returns decisions, status and failing interval."""
    missing = [f for f in SCOPE_FIELDS if scope.get(f) in (None, "")]
    if missing:
        raise ContractError("ERR-INVARIANT", f"FT-09 / FT-11: incomplete scope key {missing}")
    registered = {c["acc_id"]: c for c in criteria if c["acc_id"] in scope["criterion_ids"]}
    check_frozen_before_test(list(registered.values()), first_test_evaluation_utc)
    decisions = {cid: (decide_criterion(registered[cid], results.get(cid)) if cid in registered else "not_assessable")  # no registered criterion
                 for cid in sorted(scope["criterion_ids"])}
    types = {cid: registered[cid]["criterion_type"] for cid in registered}
    failing = [cid for cid in decisions if decisions[cid] == "not_met" and types.get(cid) in ("technical_accuracy", "completeness")]
    if all(d == "not_assessable" for d in decisions.values()):
        status = "not_yet_assessable"  # FT-04: missing evidence never gives unsuitable
    elif failing:
        status = "unsuitable_under_tested_conditions"  # FT-03: needs a recorded not_met
    elif _validated(scope, decisions, types, results):
        status = "technically_validated"
    elif any(d in ("met", "inconclusive") for d in decisions.values()):
        status = "experimental"
    else:
        raise ContractError("ERR-SPEC", "section 9.6 defines no status for this combination of decisions (CR-016 item 1)")
    out = {"criterion_decisions": decisions, "measurement_status": status, "failing_interval": None, "failing_interval_null_reason": "not_applicable"}
    if failing:
        r = results[failing[0]]
        out["failing_interval"], out["failing_interval_null_reason"] = {"low": r["ci_low"], "high": r["ci_high"]}, None
    return out


def _validated(scope: dict, decisions: dict, types: dict, results: dict) -> bool:
    """Section 9.6 technically_validated: every registered accuracy, completeness, repeatability and robustness criterion
    met on real data, test partition, valid split and RES windows, at least one criterion of each type, comparability
    characterized. Provisional readings of "real data" and "characterized" are CR-016 items 2 and 3 (the stricter ones)."""
    if scope["data_origin"] != "real_natural":
        return False
    gated = [cid for cid in decisions if types.get(cid) in GATED_TYPES]
    if any(decisions[cid] != "met" for cid in gated) or not all(any(types.get(c) == t for c in gated) for t in GATED_TYPES):
        return False
    for cid in gated:
        r = results[cid]
        if r.get("partition") != "test" or r["sample_type"] != "RES" or r["validity"] != "valid":
            return False
    return any(types.get(c) == "comparability" and decisions[c] != "not_assessable" for c in decisions)


def check_record(record: dict, decided: dict) -> None:
    """FT-01, FT-03, FT-08 (CT-E-29): a stored status must be the decision rule's status, or a downgrade by override."""
    stored, rule = record["measurement_status"], decided["measurement_status"]
    if stored == rule:
        return
    override = record.get("override")
    if override is None or not override.get("downgrade_only") or STATUS_RANK[stored] > STATUS_RANK[rule]:
        raise ContractError("ERR-INVARIANT", f"FT-01 / FT-08: stored status {stored} differs from the decision rule's {rule} and is not a downgrade")
    if stored == "unsuitable_under_tested_conditions" and "not_met" not in decided["criterion_decisions"].values():
        raise ContractError("ERR-INVARIANT", "FT-03: unsuitable requires a recorded not_met result")


def fitness_row(scope: dict, decided: dict, construct: str, construct_evidence: dict, parameter_sensitive: bool, override: dict | None = None) -> dict:
    """A measurement_fitness row (E-1.2.1 section 5.9) with the fixed interpretation note."""
    return {"scope": scope, "criterion_decisions": decided["criterion_decisions"], "measurement_status": decided["measurement_status"],
            "failing_interval": decided["failing_interval"], "failing_interval_null_reason": decided["failing_interval_null_reason"],
            "construct_status": construct, "construct_evidence": construct_evidence, "parameter_sensitive": parameter_sensitive,
            "override": override, "override_null_reason": None if override else "not_applicable", "interpretation_note": INTERPRETATION_NOTE}
