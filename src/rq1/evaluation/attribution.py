"""Error attribution (E-1.2.1 section 9.4; F.1 Appendix N9).

Diagnostic rule tests run in pipeline order; the first failing test is `primary_stage`, later failing tests are
`secondary_factors`, and if no test fails the result is `unresolved`. The 2^3 oracle substitution runner reports which
substitution sets resolve the error, and `oracle_attribution` assigns the T12.3 status on synthetic data."""
from __future__ import annotations

from itertools import combinations
from typing import Callable

from rq1.schema import vr_rules

from .association import box_iou

STAGES = ("evidence_unavailable", "perception", "tracking", "geometry", "event_reasoning", "linkage", "reference_ambiguity")
ORACLE_STAGES = ("perception", "tracking", "geometry")
USABLE = ("usable", "usable_degraded")  # AR-42 item 2

Box = tuple[str, str, tuple[float, float, float, float]]  # (object id, class, xyxy)


def diagnose(results: dict[str, bool | None]) -> dict:
    """N9: `results[stage]` is True when the stage's test fails, False when it passes, None when it was not evaluated
    (for example linkage before M2). Returns the error_attribution content without match_nk and oracle IDs."""
    unknown = set(results) - set(STAGES)
    if unknown:
        raise ValueError(f"unknown stages {sorted(unknown)}")
    results = prerequisites(results)
    failing = [s for s in STAGES if results.get(s) is True]
    record = {"rule_test_results": {s: ("fail" if results[s] else "pass") if results.get(s) is not None else "not_evaluated" for s in STAGES if s in results}}
    if not failing:  # "tests conflict" is not detected until CR-014 is decided
        return {**record, "primary_stage": "unresolved", "secondary_factors": [], "attribution_status": "unresolved"}
    return {**record, "primary_stage": failing[0], "secondary_factors": failing[1:], "attribution_status": "diagnostic_inferred"}


def prerequisites(results: dict[str, bool | None]) -> dict[str, bool | None]:
    """T12.3.5: rules 4 and 5 are not_evaluated when their prerequisite fails. N9 rule 4 needs "association is correct"
    (rule 3 passes); rule 5 needs "correct flags" (rule 4 passes, and so rule 3)."""
    out = dict(results)
    if out.get("tracking") is True and "geometry" in out:
        out["geometry"] = None
    if (results.get("tracking") is True or out.get("geometry") is True) and "event_reasoning" in out:
        out["event_reasoning"] = None
    return out


def oracle_attribution(results: dict[str, bool | None], resolved: set, run_ids: dict) -> tuple[dict, dict]:
    """T12.3 on synthetic data with oracle runs. `resolved` holds the substitution sets C with Resolved(C) true (from the
    oracle adapters; at M0 given as input); `run_ids` maps each set to its oracle run's artifact ID.
    Returns the error_attribution content (without match_nk) and the milestone-report diagnostics of T12.3.4."""
    if frozenset() in resolved:
        raise ValueError("Resolved(empty set) is false by construction (T12.3.2)")
    rule = diagnose(results)  # rule_test_results are always stored (T12.3.4)
    base = {"rule_test_results": rule["rule_test_results"], "oracle_artifact_ids": []}
    if prerequisites(results).get("evidence_unavailable") is True:  # T12.3.1: no factorial
        return {**base, "primary_stage": "evidence_unavailable", "secondary_factors": [], "attribution_status": "diagnostic_inferred"}, {}
    minimal = [c for c in resolved if not any(o < c for o in resolved)]
    non_monotone = sorted((sorted(c) for c in resolved if any(c < o and o not in resolved for o in oracle_subsets())), key=str)
    if not minimal:  # T12.3.3a
        checked = prerequisites(results)
        stage = next((s for s in ("event_reasoning", "reference_ambiguity") if checked.get(s) is True), None)
        out = {**base, "primary_stage": stage or "unresolved", "secondary_factors": [], "attribution_status": "diagnostic_inferred" if stage else "unresolved"}
    else:  # T12.3.3b
        k = min(len(c) for c in minimal)
        first = set().union(*(c for c in minimal if len(c) == k))
        primary = next(s for s in ORACLE_STAGES if s in first)
        involved = set().union(*minimal)
        out = {**base, "primary_stage": primary, "secondary_factors": [s for s in ORACLE_STAGES if s in involved and s != primary],
               "attribution_status": "verified_oracle_single" if k == 1 else "verified_oracle_joint",
               "oracle_artifact_ids": sorted(run_ids[c] for c in minimal)}
    return out, {"rule_primary": rule["primary_stage"], "disagrees": rule["primary_stage"] != out["primary_stage"], "non_monotone_sets": non_monotone}


# --- N9 rule tests -------------------------------------------------------------------------------------------------

def rule_evidence_unavailable(reference_observable_at_ca: bool, coverage_state_at_ca: str) -> bool:
    """1. The reference is unobservable at the closest-approach frame, or coverage there is not usable."""
    return not reference_observable_at_ca or coverage_state_at_ca not in USABLE


def _near(frames: dict[int, list[Box]], ca: int, n_miss: int) -> list[tuple[int, Box]]:
    return [(f, b) for f in range(ca - n_miss, ca + n_miss + 1) for b in frames.get(f, [])]


def rule_perception_miss(reference: dict[int, list[Box]], system: dict[int, list[Box]], pair: tuple[str, str], ca: int, n_miss: int, iou_cm: float) -> bool:
    """2, for a miss: no system detection of the reference person or forklift with IoU >= iou_cm within +-n_miss frames
    of the reference closest-approach frame."""
    for ref_id in pair:
        hits = [(f, r) for f, r in _near(reference, ca, n_miss) if r[0] == ref_id]
        if not any(s[1] == r[1] and box_iou(s[2], r[2]) >= iou_cm for f, r in hits for s in system.get(f, [])):
            return True
    return False


def rule_perception_false_alert(reference: dict[int, list[Box]], system: dict[int, list[Box]], tracks: tuple[str, str], ca: int, n_miss: int,
                                iou_cm: float) -> bool:
    """2, for a false alert (F.1 A5.2 FX-ID-8): a system track of the event has no reference object of its class with
    IoU >= iou_cm within +-n_miss frames of the event's closest-approach frame (AR-42 item 1)."""
    for track in tracks:
        hits = [(f, s) for f, s in _near(system, ca, n_miss) if s[0] == track]
        if not any(r[1] == s[1] and box_iou(s[2], r[2]) >= iou_cm for f, s in hits for r in reference.get(f, [])):
            return True
    return False


def rule_tracking(assoc_rows: list[dict], pair: tuple[str, str], ca: int, pow_break_frames: list[int], ref_interval: tuple[int, int]) -> bool:
    """3. The identity association at the reference CA frame is not `matched` for both objects, or a POW break lies
    within the reference interval [start, end_excl)."""
    matched = {r["physical_identity_id"] for r in assoc_rows if r["frame_index"] == ca and r["status"] == "matched"}
    return not set(pair) <= matched or any(ref_interval[0] <= f < ref_interval[1] for f in pow_break_frames)


def rule_geometry(frames: list[dict], k_sigma: float) -> bool:
    """4. At a frame where the flag decision differs from the reference-geometry decision, |clearance error| > k_sigma * sigma
    (sigma 0 if null) or the speed error flips M. Each frame: decision_differs, clearance_error_m, sigma_m, m_system, m_reference."""
    for f in frames:
        if not f["decision_differs"]:
            continue
        err = f.get("clearance_error_m")
        if (err is not None and abs(err) > k_sigma * (f.get("sigma_m") or 0.0)) or f.get("m_system") != f.get("m_reference"):
            return True
    return False


def rule_event_reasoning(triggers_from_reference_flags: bool, triggers_in_output: bool) -> bool:
    """5. Flags computed from reference geometry would trigger (or not) differently from the configuration's output."""
    return triggers_from_reference_flags != triggers_in_output


def rule_reference_ambiguity(tier: str | None, unsure: bool) -> bool:
    """7. The reference is Tier 2 or unsure."""
    return unsure or (tier is not None and tier.startswith("T2"))


# --- oracle substitution ---------------------------------------------------------------------------------------------

def oracle_subsets() -> list[frozenset]:
    """The 2^3 substitution sets over perception, tracking and geometry, smallest first, in pipeline order."""
    return [frozenset(c) for k in range(len(ORACLE_STAGES) + 1) for c in combinations(ORACLE_STAGES, k)]


def oracle_outcomes(error_present: Callable[[frozenset], bool]) -> dict[frozenset, bool]:
    """Run the downstream pipeline with simulator truth substituted for each set; True = the error is resolved
    (no longer present). `error_present(frozenset())` is the unsubstituted run."""
    return {s: not error_present(s) for s in oracle_subsets()}


def check(rows: list[dict], data_origin: str) -> list:
    """VR-E-061 on attribution records: verified_* only for synthetic data with oracle runs referenced."""
    return vr_rules.check_attribution(rows, data_origin)
