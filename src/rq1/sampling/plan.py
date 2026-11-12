"""V0 sampling frame, RES and ECS plans (E-1.2.1 section 8; Appendix T SP-02, SP-09, SP-10; AR-33)."""
from __future__ import annotations

import hashlib
from datetime import datetime
from fractions import Fraction
from typing import Any

import numpy as np

from rq1.schema import vr_rules
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.schema.validate import Issue
from rq1.splits.builder import recording_partitions

Row = dict[str, Any]
RATE_METRICS = {"EV-M7"}  # per-hour burden; frequency aggregates are added as metrics are defined


def tile_windows(camera_group_id: str, timeline_id: str, extent: tuple[float, float], w_ref: float, w_guard: float, origin: float) -> list[Row]:
    """Non-overlapping windows of w_ref from the tiling origin. The last window may be shorter, and the guard is clipped
    at the extent end (Owner decision D-7)."""
    start, end, width = Fraction(str(extent[0])), Fraction(str(extent[1])), Fraction(str(w_ref))
    if Fraction(str(origin)) != start:
        raise ContractError("ERR-SPEC", "tiling origin must equal the timeline extent start")
    guard = Fraction(str(w_guard))
    windows, k = [], 0
    while start + k * width < end:
        a, b = start + k * width, min(start + (k + 1) * width, end)
        windows.append({"camera_group_id": camera_group_id, "timeline_id": timeline_id, "window_index": k, "t_start_tl_s": float(a), "t_end_tl_s": float(b),
                        "window_length_s": float(b - a), "t_guard_end_tl_s": float(min(b + guard, end))})
        k += 1
    return windows


def check_inputs(inputs: list[Row]) -> None:
    """VR-E-050 and CT-E-18: V0 reads no S2 to S5 output."""
    issues = vr_rules.check_v0_inputs(inputs)
    if issues:
        raise ContractError("ERR-INVARIANT", issues[0].message)


def draw_res(population: list[Row], strata_n: dict[str, int], seed: int) -> list[Row]:
    """Stratified simple random sampling without replacement; pi = n_h / N_h, weight = 1 / pi."""
    rng = np.random.Generator(np.random.PCG64(seed))
    ordered = sorted(population, key=lambda w: (w["stratum_id"], w["camera_group_id"], w["window_index"]))
    selected: list[Row] = []
    for stratum in sorted(strata_n):
        frame = [w for w in ordered if w["stratum_id"] == stratum]
        n = strata_n[stratum]
        if n > len(frame):
            raise ContractError("ERR-SPEC", f"stratum {stratum}: n_h {n} exceeds N_h {len(frame)}")
        picks = sorted(int(i) for i in rng.choice(len(frame), n, replace=False))
        selected += [{**frame[i], "inclusion_prob": n / len(frame), "weight": len(frame) / n, "sample_type": "RES"} for i in picks]
    return selected


def ecs_windows(windows: list[Row], basis: str) -> list[Row]:
    """Windows chosen from system outputs: ECS, with no inclusion probability or weight."""
    return [{**w, "inclusion_prob": None, "weight": None, "sample_type": "ECS", "ecs_selection_basis": basis} for w in windows]


def headline_windows(windows: list[Row]) -> list[Row]:
    return [w for w in windows if w["sample_type"] == "RES"]


def test_domain(windows: list[Row], split: Row) -> list[Row]:
    """Windows whose recordings are all in the test partition of `split`."""
    partitions = recording_partitions(split)
    return [w for w in windows if all(partitions.get(r) == "test" for r in w["recording_ids"])]


def estimand_validity(audits: list[Row], fresh_plan: bool = False) -> str:
    """R-3 and SP-11."""
    if fresh_plan:
        return "design_valid"
    return "requires_resample" if any(a["discovery_basis"] == "sampled_annotation" and a["violations"] for a in audits) else "design_valid"


def check_sp_09(plan_frozen: datetime, audits: list[Row]) -> list[Issue]:
    """SP-09: headline metrics only from a plan whose population no later sample-based discovery altered."""
    return [Issue("SP-09", "ERR-INVARIANT", "metric_result", "estimand_validity", "plan population altered by a sampled_annotation discovery")
            for a in audits if a["discovery_basis"] == "sampled_annotation" and a["violations"] and a["frozen_after"] > plan_frozen]


def check_sp_10(rows: list[Row]) -> list[Issue]:
    return [Issue("SP-10", "ERR-INVARIANT", "metric_result", "metric_id", f"{r['metric_id']} rate under conditional_on_selection")
            for r in rows if r["estimand"] == "conditional_on_selection" and r["metric_id"] in RATE_METRICS]


def check_sp_02(windows: list[Row], current_split_id: str) -> list[Issue]:
    return [Issue("SP-02", "ERR-INVARIANT", "reference_window", "split_version_id", "window references a superseded split")
            for w in windows if w["split_version_id"] != current_split_id]


def _nullable(value: Any, reason: str) -> tuple[Any, Any]:
    return value, None if value is not None else reason


def plan_rows(plan_label: str, version: str, sample_type: str, split_version_id: str, population: list[Row], selected: list[Row], strata_n: dict[str, int],
              seed: int, frame: Row, frozen_utc: datetime, ecs_selection_basis: str | None = None, supersedes_plan_id: str | None = None) -> dict[str, list[Row]]:
    keys = sorted([w["camera_group_id"], w["window_index"], w["stratum_id"]] for w in population)
    plan = {"plan_label": plan_label, "version": version, "sample_type": sample_type, "split_version_id": split_version_id,
            "population_definition_ref": f"test partition of {split_version_id}", "frame_definition": frame,
            "frame_sha256": hashlib.sha256(canonical_json(keys)).hexdigest(),
            "strata": [{"stratum_id": h, "definition": "pre-system metadata", "N_h": sum(1 for w in population if w["stratum_id"] == h), "n_h": n}
                       for h, n in sorted(strata_n.items())],
            "stratifier_inputs": ["stratum_id"], "seed": seed, "frozen_utc": frozen_utc}
    plan["supersedes_plan_id"], plan["supersedes_plan_id_null_reason"] = _nullable(supersedes_plan_id, "not_applicable")
    plan["ecs_selection_basis"], plan["ecs_selection_basis_null_reason"] = _nullable(ecs_selection_basis, "not_applicable")
    windows = []
    for w in selected:
        row = {"plan_nk": [plan_label, version], "camera_group_id": w["camera_group_id"], "timeline_id": w["timeline_id"], "window_index": w["window_index"],
               "t_start_tl_s": w["t_start_tl_s"], "t_end_tl_s": w["t_end_tl_s"], "window_length_s": w.get("window_length_s", w["t_end_tl_s"] - w["t_start_tl_s"]),
               "t_guard_end_tl_s": w["t_guard_end_tl_s"], "stratum_id": w["stratum_id"],
               "sample_type": w["sample_type"], "exhaustive": True, "annotation_status": "planned", "split_version_id": split_version_id,
               "partition_at_sampling": w["partition_at_sampling"], "leakage_group_id": w["leakage_group_id"]}
        row["inclusion_prob"], row["inclusion_prob_null_reason"] = _nullable(w["inclusion_prob"], "not_applicable")
        row["weight"], row["weight_null_reason"] = _nullable(w["weight"], "not_applicable")
        row["locked_utc"], row["locked_utc_null_reason"] = None, "pending_review"
        row["lock_sha256"], row["lock_sha256_null_reason"] = None, "pending_review"
        windows.append(row)
    return {"sampling_plan": [plan], "reference_window": windows}
