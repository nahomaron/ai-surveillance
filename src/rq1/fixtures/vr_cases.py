"""One passing and one failing fixture per active VR rule (Appendix T, T1)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from rq1.ids import core as ids
from rq1.schema import registry, validate, vr_rules as vr
from rq1.schema.vr_rules import check_parquet_metadata


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


def _seg(a: float, b: float, **more) -> dict[str, Any]:
    return {"t_start_tl_s": a, "t_end_tl_s": b, **more}


def _state(**more) -> dict[str, Any]:
    return {"geometry_method": "ground_plane_homography", "calibration_id": "c1", "x_m": 1.0, "y_m": 1.0, "sigma_status": "calibrated", **more}


_CAL = {"c1": {"calibration_tier": "ground_plane_homography", "quality_state": "supplied_unvalidated"}}
_FAILED = {"c1": {"calibration_tier": "ground_plane_homography", "quality_state": "failed"}}


def _profile(**more) -> dict[str, Any]:
    base = {"t_total_support_s": 3.0, "t_in_band_detected_s": [1.0], "t_in_band_inferred_s": [1.0], "t_clearance_unknown_s": 0.5,
            "t_insufficient_s": 0.5, "t_moving_detected_s": 1.0, "t_moving_inferred_s": 0.5, "t_stationary_detected_s": 0.5,
            "t_stationary_inferred_s": 0.25, "t_motion_unknown_s": 0.25}
    return {**base, **more}


def _labels(suffix: str = "ep", k: str = "K", contact: str = "contact_state", **more) -> dict[str, Any]:
    """Appendix N1 T5: labels H and NM."""
    base = {f"P_{suffix}": True, f"X_{suffix}": True, f"C_{suffix}": False, k: 1, contact: "none_observed", "lbl_O": False, "lbl_H": True,
            "lbl_PC": False, "lbl_NM": True, "lbl_UD": False, "lbl_CT": False, "lbl_IE": False, "summary_label": "NM"}
    return {**base, **more}


_EV = {"suffix": "ev", "k": "K_ev", "contact": "contact_state_ev"}
_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 1, 2, tzinfo=timezone.utc)
_META = {"schema_id": "x", "schema_version": "E-1.2.3", "artifact_id": "a", "data_origin": "synthetic_rendered", "payload_sha256": "0"}


def _track(art: str, good: bool) -> list[dict[str, Any]]:
    row = {"recording_id": "rec_a", "track_local_id": 1, "trk_id": ids.observation_id("trk", "track", art, ["rec_a", 1])}
    return [row if good else {**row, "trk_id": "trk_" + "a" * 26}]


def _edge(mahal: float) -> tuple[dict[str, Any], dict[str, Any]]:
    cal = {"world_frame_id": "wf", "quality_state": "supplied_unvalidated"}
    return ({"edge": "L", "median_mahalanobis": mahal},
            {"cal_a": cal, "cal_b": cal, "same_aligned_timeline": True, "sigma_a": 0.01, "sigma_b": 0.01})


def _span(state: str = "reference_verified_absent", **more) -> dict[str, Any]:
    return {"ref_activity_state": state, "eligible_support_s": 1.0, "label_source": "simulator_truth", **_seg(0.0, 35.0), **more}


_WINDOW = {"t_start_tl_s": 0.0, "t_guard_end_tl_s": 35.0, "exhaustive": True}


def _split(tier: str, assignments: list, shared: bool = False, sessions: list | None = None) -> dict[str, Any]:
    return {"tier": tier, "assignments": [{"leakage_group_id": g, "partition": p} for g, p in assignments],
            "shared_scene_content": shared, "t2b_shared_sessions": sessions}


_ART = "art_" + "b" * 26

CASES = [
    Case("VR-E-001", "Appendix T: section 2.5 metadata, no execution-specific key, supported major.", None,
         lambda: _META, lambda: {**_META, "created_utc": "x"}, lambda m: check_parquet_metadata(m, "E-1.2.3")),
    Case("VR-E-002", "Appendix T: a null has a valid reason; a non-null value has none.", None,
         lambda: _row("session", scenario_ref=None, scenario_ref_null_reason="not_applicable"),
         lambda: _row("session", scenario_ref=None, scenario_ref_null_reason=None), _single("session")),
    Case("VR-E-003", "Appendix T: no NaN, infinity or sentinel such as -1.", None,
         lambda: _row("frame", support_s=0.033), lambda: _row("frame", support_s=float("nan")), _single("frame")),
    Case("VR-E-004", "Appendix T: every ID is recomputable according to its identity class.", None,
         lambda: _track(_ART, True), lambda: _track(_ART, False), lambda rows: vr.check_ids("track", rows, _ART)),
    Case("VR-E-005", "Appendix T: one data_origin per file.", None,
         lambda: ["synthetic_rendered"], lambda: ["synthetic_rendered", "real_natural"], vr.check_data_origins),
    Case("VR-E-010", "Appendix T (amended): strictly increasing, contiguous, support >= 0.", None,
         lambda: _frames(0.0, 0.033, 0.066), lambda: _frames(0.0, 0.033, 0.033), vr.check_frames),
    Case("VR-E-011", "Appendix T (amended): start < end and inside the extent.", None,
         lambda: [_seg(0.0, 1.0)], lambda: [_seg(1.0, 1.0)],
         lambda rows: vr.check_intervals("coverage_segment", rows, "t_start_tl_s", "t_end_tl_s", (0.0, 2.0))),
    Case("VR-E-012", "Appendix T (= TI-01): coverage tiles the extent exactly once.", None,
         lambda: [_seg(0.0, 1.0), _seg(1.0, 2.0)], lambda: [_seg(0.0, 1.0), _seg(1.5, 2.0)],
         lambda rows: vr.check_coverage_tiling(rows, (0.0, 2.0))),
    Case("VR-E-013", "Appendix T (= CD-01/02): not_evaluated exactly where coverage is not usable (FX-D1, FX-D2).", None,
         lambda: [_seg(0.0, 20.0, coverage_state="unusable", ai_activity_state="not_evaluated")],
         lambda: [_seg(0.0, 20.0, coverage_state="unusable", ai_activity_state="observed_no_detection")],
         lambda rows: vr.check_activity(rows, (0.0, 20.0))),
    Case("VR-E-014", "Appendix T (amended): world quantities only with a permitted method and tier.", None,
         lambda: [_state()], lambda: [_state(geometry_method="image_only")], lambda rows: vr.check_object_states(rows, _CAL)),
    Case("VR-E-015", "Appendix T: clearance null iff not measured; overlap iff clearance <= 0.", None,
         lambda: [{"clearance_m": -0.05, "clearance_state": "measured", "footprint_overlap": 1}],
         lambda: [{"clearance_m": -0.05, "clearance_state": "measured", "footprint_overlap": 0}], vr.check_pair_series),
    Case("VR-E-016", "Appendix T (amended): exposure sums within 1 microsecond.", None,
         lambda: [_profile()], lambda: [_profile(t_clearance_unknown_s=0.6)], vr.check_exposure_sums),
    Case("VR-E-017", "Appendix T: exactly one profile per POW and band scheme.", None,
         lambda: [{"subject_type": "pow", "subject_nk": ["p"], "band_scheme_id": "b"}],
         lambda: [{"subject_type": "pow", "subject_nk": ["p"], "band_scheme_id": "b"}] * 2,
         lambda rows: vr.check_profile_cardinality([["p"]], ["b"], rows)),
    Case("VR-E-018", "Appendix T: calibrated sigma needs GV-05 evidence.", None,
         lambda: ([_state()], {"c1": "gv05-1"}), lambda: ([_state()], {}), lambda pair: vr.check_sigma_status(*pair)),
    Case("VR-E-020", "Appendix T: no geometry from a failed calibration.", "ERR-CALIB-FAILED",
         lambda: ([_state()], _CAL), lambda: ([_state()], _FAILED), lambda pair: vr.check_object_states(*pair)),
    Case("VR-E-021", "Appendix T: SI units. The mechanical check is the column suffix (AR-13).", None,
         lambda: ["clearance_m"], lambda: ["clearance_cm"], vr.check_unit_suffixes),
    Case("VR-E-030", "Appendix T: CL-INV-01 to 11 (Appendix N1 T5 as passing input).", None,
         lambda: _labels(), lambda: _labels(lbl_NM=False, lbl_UD=True), vr.check_episode_labels),
    Case("VR-E-031", "Appendix T (amended): requirements of an L edge.", None,
         lambda: _edge(1.0), lambda: _edge(99.0), lambda pair: vr.check_linked_edge(*pair, 0.1, 5.99)),
    Case("VR-E-032", "Appendix T: event labels recomputed from event flags.", None,
         lambda: _labels(**_EV), lambda: _labels(**_EV, lbl_H=False), vr.check_event_labels),
    Case("VR-E-034", "Appendix T: no 'observed contact' value in the Observation store.", None,
         lambda: [{"contact_state": "none_observed"}], lambda: [{"contact_state": "observed_contact"}],
         lambda rows: vr.check_no_observed_contact("episode", rows)),
    Case("VR-E-040", "Appendix T: no reference state in the Observation store. The zero-exposure clause is enforced with the export in T-15.", None,
         lambda: [{"ai_activity_state": "observed_no_detection"}], lambda: [{"ai_activity_state": "reference_verified_absent"}],
         lambda rows: vr.check_no_reference_states("activity_segment", rows)),
    Case("VR-E-041", "Appendix T and section 5.7: forbidden fields.", "ERR-FORBIDDEN-FIELD",
         lambda: _row("load_state"), lambda: {**_row("load_state"), "potential_energy_j": 1.0}, _single("load_state")),
    Case("VR-E-050", "Appendix T: V0 has no Observation input except coverage.", None,
         lambda: [{"stage": "S1", "table": "coverage_segment"}], lambda: [{"stage": "S2", "table": "detection"}], vr.check_v0_inputs),
    Case("VR-E-051", "Appendix T: headline metrics use RES windows only.", "ERR-ECS-AGGREGATE",
         lambda: [{"metric_id": "EV-M1", "sample_type": "RES"}], lambda: [{"metric_id": "EV-M1", "sample_type": "ECS"}], vr.check_headline_sample_type),
    Case("VR-E-052", "Appendix T and F.1 A3: spans tile; verified absence only in exhaustive windows with support.", None,
         lambda: ([_span()], _WINDOW), lambda: ([_span()], {**_WINDOW, "exhaustive": False}), lambda pair: vr.check_ref_coverage(*pair)),
    Case("VR-E-053", "Appendix T: reference records are blind.", None,
         lambda: [{"namespace": "reference", "blind_to_system": True}], lambda: [{"namespace": "reference", "blind_to_system": False}],
         lambda rows: vr.check_blind_reference("annotation_record", rows)),
    Case("VR-E-054", "Appendix T: windows locked before the first S8 run.", None,
         lambda: [{"locked_utc": _T0}], lambda: [{"locked_utc": _T1}], lambda rows: vr.check_windows_locked(rows, _T1)),
    Case("VR-E-055", "Section 5.8: reference label source is simulator_truth or human_manual.", "ERR-NAMESPACE",
         lambda: _row("ref_geometry", label_source="human_manual"), lambda: _row("ref_geometry", label_source="model_only"), _single("ref_geometry")),
    Case("VR-E-060", "Appendix T (amended): split check per tier.", "ERR-LEAKAGE",
         lambda: _split("T1", [("g1", "train"), ("g2", "test")]), lambda: _split("T1", [("g1", "train"), ("g1", "test")]), vr.check_split),
    Case("VR-E-061", "Appendix T: verified_* only on synthetic data with oracle runs.", None,
         lambda: ([{"attribution_status": "verified_oracle_joint", "oracle_artifact_ids": ["a"]}], "synthetic_rendered"),
         lambda: ([{"attribution_status": "verified_oracle_joint", "oracle_artifact_ids": ["a"]}], "real_natural"), lambda pair: vr.check_attribution(*pair)),
    Case("VR-E-062", "Appendix T: conditional metrics carry a coverage companion.", None,
         lambda: [{"metric_id": "EV-M6", "estimand": "frame_description", "coverage_companion_id": "mtr_x"}],
         lambda: [{"metric_id": "EV-M6", "estimand": "frame_description", "coverage_companion_id": None}], vr.check_conditional_companions),
    Case("VR-E-070", "Appendix T (amended): real files have a retention policy; clips have an access class.", None,
         lambda: ([{"src_id": "s", "retention_policy_id": "p"}], {"s"}, {"p"}, [{"access_class": "team_internal"}]),
         lambda: ([{"src_id": "s", "retention_policy_id": "q"}], {"s"}, {"p"}, [{"access_class": "team_internal"}]), lambda args: vr.check_retention(*args)),
    Case("VR-E-071", "Appendix T: real-origin clips cannot be publishable.", None,
         lambda: [{"recording_id": "r", "access_class": "restricted_research"}], lambda: [{"recording_id": "r", "access_class": "publishable_synthetic_only"}],
         lambda rows: vr.check_real_clip_access(rows, {"r"})),
]
