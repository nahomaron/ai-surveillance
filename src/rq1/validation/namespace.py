"""Namespace and reference-class guards (E-1.2.1 section 5.8, VR-E-053, VR-E-055; F.1 A5.1 RV-02)."""
from __future__ import annotations

from typing import Any

from rq1.schema.errors import ContractError
from rq1.schema.validate import Issue

REFERENCE_SOURCES = {"simulator_truth", "human_manual"}


def require_reference(record: dict[str, Any]) -> None:
    """Raise ERR-NAMESPACE unless the record may be used as reference (CT-E-25)."""
    if record.get("namespace") != "reference":
        raise ContractError("ERR-NAMESPACE", f"namespace {record.get('namespace')} offered as reference")
    if record.get("label_source") not in REFERENCE_SOURCES:
        raise ContractError("ERR-NAMESPACE", f"label source {record.get('label_source')} not permitted as reference (VR-E-055)")
    if record.get("blind_to_system", True) is not True or record.get("shown_system_output", False) is not False:
        raise ContractError("ERR-NAMESPACE", "reference record is not blind (VR-E-053)")


def check_rv_02(metric_rows: list[dict[str, Any]]) -> list[Issue]:
    """RV-02: results against rule-conformance references carry claim_level none."""
    return [Issue("RV-02", "ERR-INVARIANT", "metric_result", "claim_level", "rule_conformance result with a claim level")
            for r in metric_rows if r.get("reference_class") == "rule_conformance" and r.get("claim_level") != "none"]
