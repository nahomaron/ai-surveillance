"""One passing and one failing fixture per VR rule that has contract text (T-01 part A)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rq1.schema import registry, validate


@dataclass(frozen=True)
class Case:
    rule: str
    citation: str
    code: str | None
    good: Callable[[], Any]
    bad: Callable[[], Any]
    run: Callable[[Any], list]


def _row(table: str, **changes) -> dict[str, Any]:
    row = registry.minimal_row(table)
    row.update(changes)
    return row


def _single(table: str) -> Callable[[dict[str, Any]], list]:
    return lambda row: validate.validate_row(table, row)


def _frames(*times) -> list[dict[str, Any]]:
    return [_row("frame", decode_seq=i, frame_index=i, frame_index_null_reason=None, eligible=True,
                 t_resolved_s=t, t_resolved_s_null_reason=None) for i, t in enumerate(times)]


def _span(**changes) -> dict[str, Any]:
    base = {"ref_activity_state": "reference_verified_absent", "eligible_support_s": 1.0, "label_source": "simulator_truth"}
    return _row("ref_coverage_label", **{**base, **changes})


def _window(exhaustive: bool) -> dict[str, Any]:
    return _row("reference_window", exhaustive=exhaustive)


CASES = [
    Case("VR-E-002", "Section 1.4: a null carries a reason; a non-null value carries none.", None,
         lambda: _row("session", scenario_ref=None, scenario_ref_null_reason="not_applicable"),
         lambda: _row("session", scenario_ref=None, scenario_ref_null_reason=None), _single("session")),
    Case("VR-E-003", "Sections 1.1, 1.4: f64 forbids NaN and infinity.", None,
         lambda: _row("frame", support_s=0.033),
         lambda: _row("frame", support_s=float("nan")), _single("frame")),
    Case("VR-E-010", "Section 12.1: resolved timestamps strictly increasing over eligible frames.", None,
         lambda: _frames(0.0, 0.033, 0.066),
         lambda: _frames(0.0, 0.033, 0.033), validate.check_frames),
    Case("VR-E-041", "Section 5.7: forbidden E2 quantities.", "ERR-FORBIDDEN-FIELD",
         lambda: _row("load_state"),
         lambda: {**_row("load_state"), "potential_energy_j": 1.0}, _single("load_state")),
    Case("VR-E-052", "Section 5.8 and F.1 A3 RC-03: verified absence only in exhaustive windows with support.", None,
         lambda: (_span(), _window(True)),
         lambda: (_span(), _window(False)), lambda pair: validate.check_ref_coverage(*pair)),
    Case("VR-E-055", "Section 5.8: reference label source is simulator_truth or human_manual.", "ERR-NAMESPACE",
         lambda: _row("ref_geometry", label_source="human_manual"),
         lambda: _row("ref_geometry", label_source="model_only"), _single("ref_geometry")),
    Case("VR-E-070", "Section 5.1 site: approvals_ref required for real origins.", None,
         lambda: _row("site", data_origin="real_staged", approvals_ref="ethics-1", approvals_ref_null_reason=None),
         lambda: _row("site", data_origin="real_staged", approvals_ref=None, approvals_ref_null_reason="not_supplied"),
         _single("site")),
]
