"""Reference coverage invariants RC-01 to RC-05 (F.1 A3) and VR-E-052."""
from __future__ import annotations

from typing import Any

from rq1.schema import vr_rules
from rq1.schema.validate import Issue

Row = dict[str, Any]
REASON = {"not_recorded": "not_recorded", "gap_unobserved": "gap_unobserved", "unusable": "unusable_footage"}
TOL = 1e-6


def eligible_support(frames: list[Row], a: float, b: float) -> float:
    total = 0.0
    for f in frames:
        if f["eligible"] and f["support_s"] and f["support_status"] != "timing_uncertain":
            start = f["support_start_tl_s"]
            total += max(0.0, min(start + f["support_s"], b) - max(start, a))
    return total


def check(spans: list[Row], window: Row, coverage: list[Row], frames: list[Row]) -> list[Issue]:
    issues = [Issue("RC-01", "ERR-INVARIANT", "ref_coverage_label", i.field, i.message)
              for i in vr_rules.check_tiling("RC-01", "ref_coverage_label", spans, (window["t_start_tl_s"], window["t_guard_end_tl_s"]))]
    for span in spans:
        a, b = span["t_start_tl_s"], span["t_end_tl_s"]
        blocked = [c for c in coverage if c["coverage_state"] in REASON and c["t_start_tl_s"] < b - TOL and c["t_end_tl_s"] > a + TOL]
        for c in blocked:
            if span["ref_activity_state"] != "unobservable" or span.get("unobservable_reason") != REASON[c["coverage_state"]]:
                issues.append(Issue("RC-02", "ERR-INVARIANT", "ref_coverage_label", "ref_activity_state", f"{c['coverage_state']} must be unobservable"))
                break
        if span["ref_activity_state"] == "reference_verified_absent":
            if not window["exhaustive"] or span["eligible_support_s"] <= 0 or span["label_source"] not in ("simulator_truth", "human_manual"):
                issues.append(Issue("RC-03", "ERR-INVARIANT", "ref_coverage_label", "ref_activity_state", "verified absence not permitted here"))
        if abs(span["eligible_support_s"] - eligible_support(frames, a, b)) > TOL:
            issues.append(Issue("RC-04", "ERR-INVARIANT", "ref_coverage_label", "eligible_support_s", "not the clipped eligible support"))
    return issues


def check_rc_05(table: str, rows: list[Row]) -> list[Issue]:
    """RC-05: no Observation-store table carries a reference state (with VR-E-040)."""
    return [Issue("RC-05", "ERR-INVARIANT", table, i.field, i.message) for i in vr_rules.check_no_reference_states(table, rows)]
