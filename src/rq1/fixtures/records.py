"""Record fixture factory (WP-02 part 1, T-03). Regenerate with `python -m rq1.fixtures.records`.

Expected values are transcribed from Appendix N or T, or computed from the closed formula quoted in
the fixture's `hand_calculation`. They do not call any measurement code. `check_fixture` refuses a
fixture that is inconsistent with the contract invariants (Package F WP-02).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from rq1.schema import vr_rules
from rq1.schema.errors import ContractError

TAG = "TEST-ONLY"
FIXTURES: dict[str, dict[str, Any]] = {}
PRECEDENCE = ("CT", "UD", "NM", "PC", "H", "O")


def _add(fixture_id: str, source: str, **body: Any) -> None:
    FIXTURES[fixture_id] = {"id": fixture_id, "source": source, "version_label": TAG, **body}


def expand(run_lengths: str) -> list[int]:
    out: list[int] = []
    for part in run_lengths.split(","):
        value, count = part.split("×")
        out += [int(value)] * int(count)
    return out


def _or(values: list[int]) -> int:
    return 1 if 1 in values else (2 if 2 in values else 0)


def _and(a: int, b: int) -> int:
    return 0 if 0 in (a, b) else (1 if a == b == 1 else 2)


def _summary(labels: list[str]) -> str:
    return next(x for x in PRECEDENCE if x in labels)


_add("TEST-ONLY-PARAMETERS", "Package F section 3; eps_amb and iou_cm from F.1 A5.2 fixtures; B from Appendix N tolerances; n_miss per AR-19; v_part from Appendix T T8.6; k_c_turn from Appendix T T9.3",
     parameters={"k_sup": 1.5, "f_untimed": 0.05, "f_sub": 0.10, "g_max": 15, "v_min": 0.3, "w_v": 0.5, "d_p": 2.0, "k_img": 0.05, "d_pc": 1.0,
                 "tau": 2.0, "ttc_max": 1.5, "pet_max": 1.0, "e_turn": 1.5, "e_acc": 1.0, "e_dec": 2.0, "w_e": 1.0, "m_gap": 5, "t_min": 0.2,
                 "w_post": 1.0, "d_nm": 0.5, "k_sigma": 2.0, "k_c": 3.0, "o_max": 0.5, "band_edges_m": [0.0, 0.5, 1.0, 2.0, 4.0], "iou_m": 0.3,
                 "iou_cm": 0.5, "k_kf": 1.0, "w_ref": 30.0, "w_guard": 5.0, "n_min": 10, "iou_rep": 0.95, "s_rep": 0.01, "eps_amb": 0.02,
                 "n_miss": 5, "bootstrap_B": 200, "v_part": 0.5, "k_c_turn": 3.0})

_N1 = [  # id, P, M, C, E, Q, minclr, overlap, cue, CA frame, contact, K, labels
    ("T1", "1×20", "0×20", "0×20", "0×20", "1×20", 1.10, "no", "no", None, "none_observed", 0, ["O"]),
    ("T2", "1×20", "1×20", "0×20", "0×20", "1×20", 1.10, "no", "no", None, "none_observed", 0, ["H"]),
    ("T3", "0×20", "2×20", "1×20", "0×20", "1×20", 2.35, "no", "no", None, "none_observed", 0, ["PC"]),
    ("T4", "1×20", "1×20", "1×20", "0×20", "1×20", 0.80, "no", "no", None, "none_observed", 0, ["H", "PC"]),
    ("T5", "1×20", "1×20", "0×20", "0×8,1×3,0×9", "1×20", 0.60, "no", "no", None, "none_observed", 1, ["H", "NM"]),
    ("T6", "1×20", "1×20", "0×20", "0×20", "1×20", -0.05, "yes", "no", None, "undetermined", 1, ["H", "UD"]),
    ("T7", "1×20", "1×20", "0×20", "0×20", "1×20", -0.10, "yes", "yes", None, "suspected", 1, ["H", "CT"]),
    ("T8", "1×20", "0×20", "0×20", "0×20", "1×20", -0.05, "yes", "no", None, "undetermined", 1, ["O"]),
    ("T9", "1×20", "0×20", "0×20", "0×20", "1×20", -0.10, "yes", "yes", None, "suspected", 1, ["O", "CT"]),
    ("T10", "0×20", "2×20", "1×20", "2×20", "1×12,0×8", 1.20, "unknown", "no", 15, "undetermined", 2, ["PC", "IE"]),
    ("T11", "1×20", "1×20", "0×20", "2×20", "1×10,0×10", 1.05, "unknown", "no", 15, "not_assessable", 2, ["H", "IE"]),
]
for row_id, p, m, c, e, q, minclr, overlap, cue, ca, contact, k, labels, in ((r[0], *r[1:6], r[6], r[7], r[8], r[9], r[10], r[11], r[12]) for r in _N1):
    routed = contact in ("undetermined", "suspected") or any(x in labels for x in ("NM", "UD", "CT", "IE"))
    # Clearance is measured on every frame, except T10 (frames 0-11, Appendix T T9.9) and T11 (frames 0-9, Appendix N1).
    measured = {"T10": [0, 12], "T11": [0, 10]}.get(row_id, [0, 20])
    source = "Appendix N1 row T10, inputs as corrected by Appendix T T9.9 (E-1.2.7)" if row_id == "T10" else f"Appendix N1 row {row_id}"
    _add(f"N1-{row_id}", source,
         inputs={"fps": 10, "n_frames": 20, "P": p, "M": m, "C_any": c, "E": e, "Q": q, "minclr_m": minclr, "minclr_sigma_m": 0.05,
                 "clearance_frames": measured, "overlap_at_ca": overlap, "contact_cue": cue, "ca_frame": ca},
         expected={"contact_state": contact, "K": k, "labels": labels, "summary_label": _summary(labels), "review_route": routed},
         hand_calculation="summary_label applies section 6 precedence CT > UD > NM > PC > H > O; review_route applies the section 6 routing rule.")
_add("N1-T12", "Appendix N1 row T12",
     inputs={"fps": 10, "n_frames": 20, "P": "1×3,0×10,1×7", "M": "1×20", "C_any": "0×20", "E": "0×20", "Q": "1×20", "minclr_m": 1.10, "minclr_sigma_m": 0.05},
     expected={"episodes": [{"start_frame": 0, "end_frame_excl": 3, "span_s": 0.3, "labels": ["H"]},
                            {"start_frame": 13, "end_frame_excl": 20, "span_s": 0.7, "labels": ["H"]}], "discarded": []},
     hand_calculation="Gap of 10 frames exceeds m_gap = 5, so two episodes.")
_add("N1-T13", "Appendix N1 row T13",
     inputs={"fps": 10, "n_frames": 20, "P": "1×1,0×19", "M": "1×20", "C_any": "0×20", "E": "0×20", "Q": "1×20"},
     expected={"episodes": [], "discarded": [{"start_frame": 0, "end_frame_excl": 1, "span_s": 0.1, "discard_reason": "shorter_than_t_min"}]},
     hand_calculation="Span 0.1 s is below t_min = 0.2 s.")

_GEOM = {"fps": 10, "person": {"shape": "disc", "radius_m": 0.30}, "forklift": {"shape": "oriented_rect", "length_m": 2.0, "width_m": 1.0, "anchor": "centre", "yaw_rad": 0.0},
         "position_sigma_m": 0.05}
_add("N2-G1", "Appendix N2 row G1", inputs={**_GEOM, "n_frames": 50, "person_xy": [0.0, 1.90], "forklift_x": "0", "forklift_speed_mps": 0.0},
     expected={"clearance_m": [1.1] * 50, "P": [1] * 50, "M": [0] * 50, "C_by_R3": [0] * 50, "pred_min_clearance_m": [1.1] * 50,
               "episodes": [{"start_frame": 0, "end_frame_excl": 50, "labels": ["O"], "duration_detected_s": 5.0}]},
     hand_calculation="Distance from (0, 1.90) to the rectangle is 1.90 - 0.50 = 1.40; clearance = 1.40 - 0.30 = 1.10. Final frame credited delta_nom: 50 x 0.1 = 5.000 s.")


def _g2(t: float) -> float:
    x = abs(-2.5 + 1.0 * t)
    return 1.1 if x <= 1.0 else math.sqrt((x - 1.0) ** 2 + 1.96) - 0.30


_T50 = [i / 10 for i in range(50)]
_add("N2-G2", "Appendix N2 row G2", inputs={**_GEOM, "n_frames": 50, "person_xy": [0.0, 1.90], "forklift_x": "-2.5 + 1.0*t", "forklift_speed_mps": 1.0},
     expected={"clearance_m": [_g2(t) for t in _T50], "P": [1] * 50, "M": [1] * 50, "C_by_R3": [0] * 50,
               "episodes": [{"start_frame": 0, "end_frame_excl": 50, "labels": ["H"], "minclr_m": 1.1}]},
     hand_calculation="Clearance 1.10 for |x| <= 1, otherwise sqrt((|x|-1)^2 + 1.96) - 0.30 (Appendix N2). Maximum 1.7518 at x = -2.5, below d_p = 2.0, so P = 1 on all frames.")
_T10 = [i / 10 for i in range(10)]
_add("N2-G3", "Appendix N2 row G3", inputs={**_GEOM, "n_frames": 10, "person_xy": [5.0, 0.0], "forklift_x": "1.5*t", "forklift_speed_mps": 1.5, "tau_s": 2.0},
     expected={"clearance_m": [3.70 - 1.5 * t for t in _T10], "pred_min_clearance_m": [0.70 - 1.5 * t for t in _T10], "P": [0] * 10, "M": [1] * 10, "C_by_R3": [1] * 10,
               "episodes": [{"start_frame": 0, "end_frame_excl": 10, "labels": ["PC"], "minclr_m": 2.35}]},
     hand_calculation="Front edge at 1.5t + 1, so clearance = 5 - (1.5t + 1) - 0.30 = 3.70 - 1.5t. Predicted over 2 s subtracts 1.5 x 2 = 3.0, giving 0.70 - 1.5t; below zero this is signed penetration.")

_add("FX-TIE", "Appendix N4 FX-TIE", inputs={"references": {"r1": [0.0, 1.0], "r2": [1.0, 2.0]}, "system": {"s1": [0.5, 1.5]}},
     expected={"iou": {"s1,r1": 1 / 3, "s1,r2": 1 / 3}, "matches": [["s1", "r1"]], "misses": ["r2"]},
     hand_calculation="Intersection 0.5, union 1.5, IoU 1/3 for each pair. The composite tie weight prefers the earlier reference.")
_add("FX-W", "Appendix N5 FX-W",
     inputs={"strata": {"h1": {"N": 10, "n": 2, "pi": 0.2, "w": 5}, "h2": {"N": 4, "n": 2, "pi": 0.5, "w": 2}},
             "windows": [{"stratum": "h1", "a": 3, "m": 2}, {"stratum": "h1", "a": 1, "m": 1}, {"stratum": "h2", "a": 2, "m": 2}, {"stratum": "h2", "a": 4, "m": 2}]},
     expected={"weighted_recall": 0.71875, "unweighted_recall": 0.70, "n_eff": 196 / 58},
     hand_calculation="(5*3 + 2*4)/(5*4 + 2*6) = 23/32 = 0.71875; 7/10 = 0.70; n_eff = 14^2/58 = 196/58.")
_add("FX-CM", "Appendix N6 FX-CM (D1-AC-04)", inputs={"fps": 10, "reference_person_visible_frames": 100, "matched_frames": 60, "missing_frames": 40, "forklift_matched": "all"},
     expected={"CM-01": 0.6, "CM-03": 0.6}, hand_calculation="6.0 s / 10.0 s = 0.600.")

_BOX1, _BOX2, _F = [100.0, 100.0, 200.0, 300.0], [400.0, 100.0, 500.0, 300.0], [600.0, 100.0, 900.0, 300.0]
_ID = {"fps": 10, "n_frames": 50, "iou_cm": 0.5, "eps_amb": 0.02}
_note_design = "Box coordinates are a fixture design choice; the expected values come from F.1 A5.2."


def _seg(obj: str, kind: str, cls: str, start: int, end: int, box: list[float]) -> dict[str, Any]:
    return {"object": obj, "side": kind, "class": cls, "start": start, "end_excl": end, "box": box}


_add("FX-ID-1", "F.1 A5.2 FX-ID-1", inputs={**_ID, "segments": [_seg("p1", "reference", "person", 0, 50, _BOX1), _seg("A", "system", "person", 0, 50, _BOX1)]},
     expected={"tracks": {"A": {"status": "one_to_one", "matched_frames": 50, "dominant_share": 1.0}}}, hand_calculation=_note_design)
_add("FX-ID-2", "F.1 A5.2 FX-ID-2",
     inputs={**_ID, "segments": [_seg("p1", "reference", "person", 0, 25, _BOX1), _seg("p2", "reference", "person", 25, 50, _BOX2),
                                 _seg("A", "system", "person", 0, 25, _BOX1), _seg("A", "system", "person", 25, 50, _BOX2)]},
     expected={"tracks": {"A": {"n_identities": 2, "n_switches": 1, "status": "id_switch", "dominant_identity": "p1", "dominant_share": 0.5}}},
     hand_calculation="Support tie of 2.5 s each goes to the lower identity ID. Share = 2.5/5.0. " + _note_design)
_add("FX-ID-3", "F.1 A5.2 FX-ID-3",
     inputs={**_ID, "segments": [_seg("p1", "reference", "person", 0, 50, _BOX1), _seg("A", "system", "person", 0, 20, _BOX1), _seg("B", "system", "person", 25, 50, _BOX1)]},
     expected={"tracks": {"A": {"status": "fragment"}, "B": {"status": "fragment"}}, "missed_reference_frames": {"p1": [20, 25]}, "CM-01": {"p1": 0.9}},
     hand_calculation="Matched 45 frames x 0.1 s = 4.5 s; visible 5.0 s; 4.5/5.0 = 0.9.")
_add("FX-ID-4", "F.1 A5.2 FX-ID-4", inputs={**_ID, "segments": [_seg("p2", "reference", "person", 0, 50, _BOX2)]},
     expected={"missed_reference_frames": {"p2": [0, 50]}, "CM-01": {"p2": 0}}, hand_calculation=_note_design)
_add("FX-ID-5", "F.1 A5.2 FX-ID-5", inputs={**_ID, "segments": [_seg("A", "system", "person", 0, 50, _BOX1)]},
     expected={"tracks": {"A": {"status": "unmatched_system"}}}, hand_calculation=_note_design)
_AMB_A, _AMB_P1, _AMB_P2 = [0.0, 0.0, 100.0, 100.0], [0.0, 0.0, 60.0, 100.0], [0.0, 0.0, 100.0, 59.0]
_ambiguous_segments = [_seg("p1", "reference", "person", 0, 10, _AMB_A), _seg("p1", "reference", "person", 10, 15, _AMB_P1), _seg("p1", "reference", "person", 15, 50, _AMB_A),
                       _seg("p2", "reference", "person", 10, 15, _AMB_P2), _seg("A", "system", "person", 0, 10, _AMB_A), _seg("A", "system", "person", 10, 15, _AMB_A),
                       _seg("A", "system", "person", 15, 50, _AMB_A)]
_add("FX-ID-6", "F.1 A5.2 FX-ID-6", inputs={**_ID, "segments": _ambiguous_segments},
     expected={"ambiguous_frames": [10, 15], "matched_frames": {"A": 45}, "unmatched_frames": {"A": 0}},
     hand_calculation="Track box area 10000. p1 is [0,0,60,100]: intersection 6000, union 10000, IoU 0.60. p2 is [0,0,100,59]: intersection 5900, union 10000, IoU 0.59. The difference 0.01 is within eps_amb 0.02.")
_add("FX-ID-7", "F.1 A5.2 FX-ID-7 and event-matching rule",
     inputs={**_ID, "segments": [*_ambiguous_segments, _seg("f1", "reference", "forklift", 0, 50, _F), _seg("F", "system", "forklift", 0, 50, _F)],
             "event": {"person_track": "A", "forklift_track": "F", "closest_approach_frame": 12}},
     expected={"event_pair": ["p1", "f1"], "resolved_via": {"person": "dominant_identity", "forklift": "frame_association"}},
     hand_calculation="Frame 12 is ambiguous for A, so the dominant identity p1 is used.")
_add("FX-ID-8", "F.1 A5.2 FX-ID-8 and Appendix N9",
     inputs={**_ID, "segments": [_seg("A", "system", "person", 0, 50, _BOX1), _seg("f1", "reference", "forklift", 0, 50, _F), _seg("F", "system", "forklift", 0, 50, _F)],
             "event": {"person_track": "A", "forklift_track": "F", "closest_approach_frame": 12}},
     expected={"event_pair": None, "match_type": "false_alert", "primary_stage": "perception"},
     hand_calculation="No reference person exists on any frame, so the result does not depend on n_miss.")

_RC = {"fps": 10, "window_t_start_tl_s": 0.0, "window_t_end_tl_s": 30.0, "t_guard_end_tl_s": 35.0, "timeline_kind": "aligned_session"}


def _span(a: float, b: float, reason: str, frames: Any = "present", **more: Any) -> dict[str, Any]:
    return {"t_start_tl_s": a, "t_end_tl_s": b, "reason": reason, **({"frame_bounds": frames} if frames != "present" else {}), **more}


_add("FX-RC-1", "F.1 A3 FX-RC-1", inputs={**_RC, "corrupt_frames": [100, 115]},
     expected={"unobservable_spans": [_span(10.0, 11.5, "unusable_footage", excluded_support_s=1.5)]}, hand_calculation="15 frames x 0.1 s = 1.5 s.")
_add("FX-RC-2", "F.1 A3 FX-RC-2", inputs={**_RC, "dropout_after_frame": 200, "next_frame_t_s": 23.0, "delta_max_s": 0.15},
     expected={"unobservable_spans": [_span(20.1, 23.0, "gap_unobserved", None)]}, hand_calculation="Frame 200 at 20.0 s keeps delta_nom = 0.1 s, so the gap starts at 20.1 s.")
_add("FX-RC-3", "F.1 A3 FX-RC-3", inputs={**_RC, "not_recording": [25.0, 35.0]}, expected={"unobservable_spans": [_span(25.0, 35.0, "not_recorded", None)]}, hand_calculation="Copied from F.1 A3.")
_add("FX-RC-4", "F.1 A3 FX-RC-4", inputs={**_RC, "simulator": "forklift present", "system_detections": 0},
     expected={"ref_activity_state": "objects_present_no_interaction", "ai_activity_state": "observed_no_detection", "CM-02_numerator": 0}, hand_calculation="Copied from F.1 A3.")
_add("FX-RC-5", "F.1 A3 FX-RC-5", inputs={**_RC, "simulator": "nothing present", "system_detections": 0},
     expected={"ref_activity_state": "reference_verified_absent", "ai_activity_state": "observed_no_detection", "reported_from": "validation_store"}, hand_calculation="Copied from F.1 A3.")
_add("FX-RC-6", "F.1 A3 FX-RC-6 (invalid)", inputs={**_RC, "span": _span(20.1, 23.0, "gap_unobserved", None), "ref_activity_state": "reference_verified_absent"},
     expected={"rejected_by": ["RC-02", "RC-03"]}, hand_calculation="Copied from F.1 A3.")

_add("FX-A3.1", "Appendix T section T3 (CT-S-08)",
     inputs={"recordings": ["A", "B", "C", "D"], "windows_per_recording": 10, "res_windows_per_recording": 2, "pi": 0.2, "shared_recordings": ["A", "B"], "shared_windows": 3,
             "discovery_basis": "sampled_annotation", "edge": "same_physical_interaction"},
     expected={"moved_to": "train", "affected_test_strata": "requires_resample", "headline_from_original_plan": "refused", "new_plan_estimand_validity": "design_valid"},
     hand_calculation="pi = 2/10 = 0.2.")
_add("FX-11", "Appendix T FX-11 (amended)", inputs={"camera_extent": [0.0, 60.0]},
     expected={"segments": [
         {"t": [0.0, 20.0], "coverage_state": "unusable", "ai_activity_state": "not_evaluated", "ref_activity_state": "unobservable", "unobservable_reason": "unusable_footage"},
         {"t": [20.0, 40.0], "coverage_state": "usable", "ai_activity_state": "observed_no_detection", "ref_activity_state": "objects_present_no_interaction"},
         {"t": [40.0, 60.0], "coverage_state": "usable", "ai_activity_state": "observed_no_detection", "ref_activity_state": "reference_verified_absent"}]},
     hand_calculation="Copied from Appendix T.")
_add("FX-12", "Appendix T FX-12 (amended)", inputs={"person_in_projected_footprint": True, "conditions": "CB-03"},
     expected={"elevation_state": "elevated", "height_m": 2.4, "height_sigma_m": 0.3, "load_mass_kg": None, "load_mass_kg_null_reason": "not_supplied", "n_e2_occupancy_profiles": 1, "episodes": []},
     hand_calculation="Copied from Appendix T. E2 is measurement only: no episode exists.")

_T4 = {
    "FX-B1": {"fixture": "FX-B1-valid-homography", "calibration_id": "cal_h1", "camera_id": "cam_03", "world_frame_id": "wf_1", "calibration_tier": "ground_plane_homography",
              "intrinsics_K": None, "intrinsics_K_null_reason": "not_applicable", "R_cam_from_world": None, "R_cam_from_world_null_reason": "not_applicable",
              "t_cam_from_world_m": None, "t_cam_from_world_m_null_reason": "not_applicable", "distortion_model": None, "distortion_model_null_reason": "not_supplied",
              "homography_assumes_undistorted": True, "homography_img_to_floor": [0.012, 0.001, -4.1, 0.0, 0.019, -6.2, 0.0, 0.0004, 1.0],
              "reproj_error_px_rmse": None, "reproj_error_px_rmse_null_reason": "not_applicable", "quality_state": "supplied_unvalidated",
              "method": "survey_points_pnp_ground_only", "height_reference_ids": []},
    "FX-B2": {"fixture": "FX-B2-invalid-height-from-homography", "track_id": "trk_load_4", "frame_index": 880, "method": "height_reference_plane", "calibration_id": "cal_h1",
              "elevation_state": "elevated", "height_m": 2.4, "height_sigma_m": 0.3, "expected_error": "CB-03: height requires full_camera calibration with height reference, multi-view, or simulator truth"},
    "FX-B3": {"fixture": "FX-B3-valid-full-camera", "calibration_id": "cal_f1", "camera_id": "cam_01", "world_frame_id": "wf_1", "calibration_tier": "full_camera", "method": "dataset_supplied",
              "valid_from_us": 0, "valid_to_us": None, "valid_to_us_null_reason": "not_applicable", "intrinsics_K": [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0],
              "R_cam_from_world": [1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0], "t_cam_from_world_m": [0.0, 3.0, 8.0], "distortion_model": "none", "distortion_coeffs": [],
              "homography_assumes_undistorted": False, "homography_img_to_floor": None, "homography_img_to_floor_null_reason": "not_computed_by_config",
              "reproj_error_px_rmse": None, "reproj_error_px_rmse_null_reason": "not_supplied", "heldout_ground_error_m_rmse": None,
              "heldout_ground_error_m_rmse_null_reason": "not_computed_by_config", "quality_state": "supplied_unvalidated", "height_reference_ids": []},
    "FX-C1": {"fixture": "FX-C1-valid-e2-profile", "e2_profile_id": "e2p_1", "person_track_id": "trk_p2", "load_track_id": "trk_load_4", "method": "image_overlap_baseline",
              "t_coobserved_s": 6.0, "t_occupied_detected_s": 1.2, "t_occupied_inferred_s": 0.3, "t_not_occupied_s": 3.9, "t_occupancy_unknown_s": 0.6},
    "FX-C2": {"fixture": "FX-C2-invalid-e2-episode", "episode_id": "ep_x", "experiment": "E2", "classification_contract": "E1_v1", "expected_error": "CC-01: experiment E2 not allowed in schema v1.1"},
    "FX-D1": {"fixture": "FX-D1-valid", "activity_segment_id": "act_1", "camera_id": "cam_02", "session_id": "ses_1", "t_start_session_s": 0.0, "t_end_session_s": 20.0,
              "coverage_state": "unusable", "ai_activity_state": "not_evaluated"},
    "FX-D2": {"fixture": "FX-D2-invalid", "activity_segment_id": "act_2", "camera_id": "cam_02", "session_id": "ses_1", "t_start_session_s": 0.0, "t_end_session_s": 20.0,
              "coverage_state": "unusable", "ai_activity_state": "observed_no_detection", "expected_error": "CD-02: unusable coverage requires not_evaluated"},
    "FX-A3": {"fixture": "FX-A3-valid-local", "recording_id": "rec_b7", "timeline_id": "tl_b7", "timeline_kind": "recording_local", "clock_alignment_id": None, "clock_alignment_id_null_reason": "not_applicable"},
    "FX-A4": {"fixture": "FX-A4-invalid-gap-without-alignment", "timeline_id": "tl_b7", "timeline_kind": "recording_local", "coverage_state": "not_recorded", "t_start_s": 120.0, "t_end_s": 180.0,
              "expected_error": "TI-11: not_recorded segments only on aligned_session timelines within a declared session extent"},
}
for _fixture_id, _record in _T4.items():
    _add(_fixture_id, "Appendix T section T4 (verbatim)", record=_record)


# --- Appendix T T22 (E-1.2.20; CR-027, D-44): C-layer blind review fixtures FX-13, FX-13a to FX-13f -----------------
_T22_BATCH = "rvb_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a13"
_T22_CONFIG = "rcf_" + "bl6fx13".ljust(26, "0")
_T22_TIME = "2026-11-19T10:00:00.000000Z"
_T22_MAP = {"lbl_nm": "nm", "lbl_ud": "ud", "lbl_ct": "ct", None: "not_hazardous"}  # T22.8 (b)


def _fid(prefix: str, tag: str) -> str:
    return f"{prefix}_{tag.ljust(26, '0')}"


def _annotator(fx: str, pseudonym: str, role: str, attested: bool = True) -> dict[str, Any]:
    qual = "EHS professional, 10 years" if role == "adjudicator" else "completed T22 handbook training and pilot batch, 2026-11-19"
    return {"anr_id": _fid("anr", f"{fx}{pseudonym}".replace("-", "").lower()), "role": role, "qualification_ref": qual,
            "independence_attestation": attested, "pseudonym": pseudonym}


def _assessment(fx: str, n: int, annotator: dict[str, Any], target: dict[str, Any], label: str, confidence: float,
                rationale: str, namespace: str = "reference", shown: bool = False) -> dict[str, Any]:
    return {"rva_id": _fid("rva", f"{fx}{n}"), "annotator_id": annotator["anr_id"], "namespace": namespace,
            "target_type": target["target_type"], "target_id": target["target_id"], "label": label, "confidence": confidence,
            "rationale": rationale, "blind": namespace == "reference", "shown_system_output": shown,
            "review_time_s": None, "review_time_s_null_reason": "not_supplied", "submitted_utc": _T22_TIME}


def _target(fx: str, g2: str | None, summary: str, rec: str = "") -> dict[str, Any]:
    return {"target_type": "system_episode", "target_id": _fid("ep", fx), "recording_id": _fid("rec", rec or fx),
            "config_id": _T22_CONFIG, "g2_label": g2, "summary_label": summary}


def _adjudication(target: dict[str, Any], final: str, tier: str, method: str, ids: list[str]) -> dict[str, Any]:
    return {"target_type": target["target_type"], "target_id": target["target_id"], "namespace": "reference", "final_label": final,
            "tier": tier, "method": method, "assessment_ids": ids, "agreement_stat_ref": _T22_BATCH, "prov_class": "human_adjudicated",
            "reference_class": "independent_expert_judgment"}


def _status(target: dict[str, Any], status: str, basis: int) -> dict[str, Any]:
    return {"target_type": target["target_type"], "target_id": target["target_id"], "config_id": target["config_id"], "status": status,
            "layer": "C", "namespace": "reference", "basis_adjudication": basis}


def _t22(fixture_id: str, target, annotators, assessments, decision, expected, hand: str, **inputs: Any) -> None:
    _add(fixture_id, f"Appendix T T22 (E-1.2.20), {fixture_id}",
         inputs={"batch_id": _T22_BATCH, "c_pad_s": 3.0, "target": target, "annotators": annotators, "assessments": assessments,
                 "adjudicator_decision": decision, **inputs},
         expected=expected, hand_calculation=hand)


def _fx13() -> None:
    # FX-13: two reviewers disagree, Tier 2 adjudication.
    t = _target("fx13", "lbl_nm", "NM")
    a, b, j = _annotator("fx13", "R-A", "c_layer_reviewer"), _annotator("fx13", "R-B", "c_layer_reviewer"), _annotator("fx13", "ADJ", "adjudicator")
    rows = [_assessment("fx13", 1, a, t, "nm", 2.0, "The forklift brakes hard as the person steps into the aisle."),
            _assessment("fx13", 2, b, t, "ud", 3.0, "The racking hides the person at the closest moment.")]
    _t22("FX-13", t, [a, b, j], rows, {"annotator_id": j["anr_id"], "final_label": "ud"},
         {"refused": False, "mapped_system_label": "nm", "adjudications": [_adjudication(t, "ud", "tier2", "adjudicator", [r["rva_id"] for r in rows])],
          "status_entries": [_status(t, "rejected", 0)]},
         "T22.7 (b): labels differ -> tier2, method adjudicator, final_label ud (adjudicator). T22.9: both assessments blind and "
         "not shown output, all three annotators attested and qualified, none exposed -> independent_expert_judgment. "
         "T22.8 (b): lbl_nm -> nm; ud != nm -> rejected; basis = the adjudication.")
    # FX-13a: both not_hazardous on an episode with no G2 label.
    t = _target("fx13a", None, "H")
    a, b = _annotator("fx13a", "R-A", "c_layer_reviewer"), _annotator("fx13a", "R-B", "c_layer_reviewer")
    rows = [_assessment("fx13a", 1, a, t, "not_hazardous", 3.0, "The forklift is parked with forks down while the person walks past."),
            _assessment("fx13a", 2, b, t, "not_hazardous", 2.0, "The forklift does not move while the person is near it.")]
    _t22("FX-13a", t, [a, b], rows, None,
         {"refused": False, "mapped_system_label": "not_hazardous",
          "adjudications": [_adjudication(t, "not_hazardous", "tier1", "agreement", [r["rva_id"] for r in rows])],
          "status_entries": [_status(t, "confirmed", 0)]},
         "T22.7 (a): same label, neither unsure -> tier1, agreement, no adjudicator. T22.8 (b): no G2 label -> not_hazardous; "
         "equal -> confirmed.")
    # FX-13b: one reviewer unsure, the other nm; adjudicator unsure.
    t = _target("fx13b", "lbl_nm", "NM")
    a, b, j = _annotator("fx13b", "R-A", "c_layer_reviewer"), _annotator("fx13b", "R-B", "c_layer_reviewer"), _annotator("fx13b", "ADJ", "adjudicator")
    rows = [_assessment("fx13b", 1, a, t, "unsure", 1.0, "I can see both paths but cannot tell whether the forklift had to stop."),
            _assessment("fx13b", 2, b, t, "nm", 2.0, "The forklift stops sharply about a metre from the person.")]
    _t22("FX-13b", t, [a, b, j], rows, {"annotator_id": j["anr_id"], "final_label": "unsure"},
         {"refused": False, "mapped_system_label": "nm",
          "adjudications": [_adjudication(t, "unsure", "tier2", "adjudicator", [r["rva_id"] for r in rows])],
          "status_entries": [_status(t, "disputed", 0)], "ev_m12": {"in_kappa": False, "counted_under": "unsure"}},
         "T22.7 (a) fails (one unsure) -> (b) tier2, adjudicator, final unsure. T22.8 (b): final unsure -> disputed. "
         "T22.10 (b): final unsure reported separately, not in kappa.")
    # FX-13c: exposure rule (T22.2 b).
    t = _target("fx13c", "lbl_nm", "NM", rec="fx13c")
    other = _target("fx13cx", "lbl_ud", "UD", rec="fx13c")
    a, b = _annotator("fx13c", "R-A", "c_layer_reviewer"), _annotator("fx13c", "R-B", "c_layer_reviewer")
    prior = _assessment("fx13c", 9, a, other, "ud", 2.0, "Reviewed with the system label shown; the mast hides the contact point.",
                        namespace="candidate_review", shown=True)
    rows = [_assessment("fx13c", 1, a, t, "nm", 2.0, "The forklift swerves away from the person at the aisle end.")]
    _t22("FX-13c", t, [a, b], rows, None,
         {"refused": True, "rule": "T22.2 (b)", "stored_assessments": 0, "adjudications": [], "status_entries": []},
         "R-A holds a candidate_review assessment on another target of the same recording -> excluded from reference "
         "assessment of every target of that recording (T22.2 b).", prior_records=[prior], other_targets=[other])
    # FX-13d: a reference assessment with shown_system_output = true.
    t = _target("fx13d", "lbl_nm", "NM")
    a, b = _annotator("fx13d", "R-A", "c_layer_reviewer"), _annotator("fx13d", "R-B", "c_layer_reviewer")
    rows = [_assessment("fx13d", 1, a, t, "nm", 2.0, "The forklift stops close to the person.", shown=True)]
    _t22("FX-13d", t, [a, b], rows, None,
         {"refused": True, "rule": "VR-E-053", "stored_assessments": 0, "adjudications": [], "status_entries": []},
         "T22.1 (a): reference assessments have blind = true and shown_system_output = false (VR-E-053); this one was shown output.")
    # FX-13e: tier-1 audit disagreement.
    t = _target("fx13e", "lbl_nm", "NM")
    a, b, j = _annotator("fx13e", "R-A", "c_layer_reviewer"), _annotator("fx13e", "R-B", "c_layer_reviewer"), _annotator("fx13e", "ADJ", "adjudicator")
    rows = [_assessment("fx13e", 1, a, t, "nm", 3.0, "The person jumps back as the forks pass."),
            _assessment("fx13e", 2, b, t, "nm", 2.0, "The forklift passes very close and the person steps back."),
            _assessment("fx13e", 3, j, t, "ud", 2.0, "The person leaves the frame just before the forks reach them.")]
    ids = [r["rva_id"] for r in rows]
    _t22("FX-13e", t, [a, b, j], rows, {"annotator_id": j["anr_id"], "final_label": "ud"},
         {"refused": False, "mapped_system_label": "nm", "tier1_record_remains": True,
          "adjudications": [_adjudication(t, "nm", "tier1", "agreement", ids[:2]), _adjudication(t, "ud", "tier2", "adjudicator", ids)],
          "status_entries": [_status(t, "confirmed", 0), _status(t, "rejected", 1)],
          "audit": {"n_audited": 1, "n_agree": 0, "agreement_rate": 0.0}},
         "T22.7 (a): nm, nm -> tier1 agreement; T22.8: nm == nm -> confirmed. T22.7 (d): audit label ud != nm -> adjudicator "
         "re-adjudicates under (b): tier2, final ud (input), assessment_ids = all three (T22.7 e); tier1 record stays. "
         "T22.8 (c): status written with the new adjudication: ud != nm -> rejected. Audit rate 0/1 = 0.0.",
         audit_sample=[t["target_id"]])
    # FX-13f: unattested adjudicator.
    t = _target("fx13f", "lbl_ct", "CT")
    a, b, j = _annotator("fx13f", "R-A", "c_layer_reviewer"), _annotator("fx13f", "R-B", "c_layer_reviewer"), _annotator("fx13f", "ADJ", "adjudicator", attested=False)
    rows = [_assessment("fx13f", 1, a, t, "nm", 2.0, "The forklift stops just short of the person."),
            _assessment("fx13f", 2, b, t, "ct", 2.0, "The forks appear to touch the person's leg.")]
    _t22("FX-13f", t, [a, b, j], rows, {"annotator_id": j["anr_id"], "final_label": "ct"},
         {"refused": True, "code": "ERR-SPEC", "rule": "T22.9", "adjudications": [], "status_entries": []},
         "T22.9: the adjudicator has independence_attestation = false -> the adjudication is refused in reference (ERR-SPEC); "
         "no adjudication, so no status entry (T22.8 c).")


_fx13()


# --- Appendix T T23 (E-1.2.22; D-48): reporting-workflow fixtures FX-14, FX-14a to FX-14i -----------------------------
# One fixture establishment and area with three cameras; calendar start Monday 2026-11-16 08:00 UTC (ISO week 2026-W47);
# every camera monitored (usable S1 coverage) for [0, 3600) s from the calendar start.
_T23_CONFIG = "rcf_" + "bl6fx14".ljust(26, "0")
_T23_EST = _fid("est", "fx14")
_T23_AREA = _fid("area", "fx14a1")
_T23_CAMS = [_fid("cam", f"fx14c{k}") for k in (1, 2, 3)]
_T23_WORLD = {
    "calendar_start_utc": "2026-11-16T08:00:00.000000Z", "period": "2026-W47",
    "establishment": {"est_id": _T23_EST, "name": "Fixture establishment", "demo": False},
    "area": {"area_id": _T23_AREA, "est_id": _T23_EST, "name": "Fixture area 1", "camera_ids": _T23_CAMS},
    "users": [{"pseudonym": "AM-1", "roles": ["area_manager"], "est_id": None, "area_ids": [_T23_AREA]},
              {"pseudonym": "SM-1", "roles": ["safety_manager"], "est_id": _T23_EST, "area_ids": []},
              {"pseudonym": "W-1", "roles": ["worker"], "est_id": None, "area_ids": []},
              {"pseudonym": "OV-1", "roles": ["oversight"], "est_id": None, "area_ids": []}],
    "monitoring": [{"camera_id": c, "segments": [{"t_start_s": 0.0, "t_end_s": 3600.0, "coverage_state": "usable"}]} for c in _T23_CAMS],
}


def _ep23(tag: str, g2: str | None, onset: float, duration: float = 1.0, cam: int = 0) -> dict[str, Any]:
    summary = {"lbl_nm": "NM", "lbl_ud": "UD", "lbl_ct": "CT", None: "H"}[g2]
    return {"ep_id": _fid("ep", f"fx14{tag}"), "recording_id": _fid("rec", f"fx14c{cam + 1}"), "camera_id": _T23_CAMS[cam],
            "config_id": _T23_CONFIG, "g2_label": g2, "summary_label": summary, "t_start_tl_s": onset,
            "t_end_tl_s": onset + duration, "minclr_m": 0.4, "minclr_m_null_reason": None, "geometry_method": "full_camera", "E_ep": 1}


def _t23(fixture_id: str, episodes, steps, expected, hand: str, **inputs: Any) -> None:
    _add(fixture_id, f"Appendix T T23 (E-1.2.22), {fixture_id}",
         inputs={"world": _T23_WORLD, "episodes": episodes, "steps": steps, **inputs}, expected=expected, hand_calculation=hand)


def _fx14() -> None:
    nm = _ep23("nm", "lbl_nm", 100.0)
    why = "The forklift brakes hard as the person steps out from the rack end."
    _t23("FX-14", [nm], [{"as": "AM-1", "action": "am_approve", "label": "nm", "rationale": why}],
         {"reports": 1, "state": "recorded", "wording": "recorded near miss (manager-approved)",
          "assessments": [{"label": "nm", "confidence": 3.0, "namespace": "candidate_review", "blind": False, "shown_system_output": True}],
          "statuses": ["confirmed"], "I2": [1, 1]},
         "T23.4: am_approve pending_am -> recorded. T23.5 (a): one assessment per member (1), label nm, confidence 3.0. "
         "T23.5 (d) with T22.8 (b): lbl_nm -> nm; nm == nm -> confirmed. I2 = am_approve / (am_approve + am_reject) = 1/(1+0) = 1/1.")
    rej = {"as": "AM-1", "action": "am_reject", "reason": "not_hazardous", "rationale": "The forklift is parked; the person walks past."}
    _t23("FX-14a", [nm], [rej, {"as": "SM-1", "action": "sm_uphold", "note": "Agree: the forks were down and the truck was parked."}],
         {"reports": 1, "state": "closed_rejected", "assessments": [{"label": "not_hazardous", "confidence": 3.0, "namespace": "candidate_review",
                                                                   "blind": False, "shown_system_output": True}],
          "adjudications": [{"final_label": "not_hazardous", "tier": "tier2", "method": "adjudicator", "namespace": "candidate_review"}],
          "statuses": ["disputed", "rejected"], "I3": [1, 1], "I4": [0, 1]},
         "T23.5 (b): reason not_hazardous -> assessment label not_hazardous; (d) after am_reject -> disputed. T23.4: am_reject -> "
         "pending_sm; sm_uphold -> closed_rejected. T23.5 (c): final_label = the area manager's label = not_hazardous; (d) "
         "T22.8 (b): lbl_nm -> nm; not_hazardous != nm -> rejected. I3 = 1/(0+1); I4 = sm_overturn/(sm_overturn+sm_uphold) = 0/(0+1).")
    _t23("FX-14b", [nm], [rej, {"as": "SM-1", "action": "sm_overturn", "label": "nm", "note": "The person had to step back; the truck was moving."}],
         {"reports": 1, "state": "recorded", "wording": "recorded near miss (safety-manager overturn)",
          "adjudications": [{"final_label": "nm", "tier": "tier2", "method": "adjudicator", "namespace": "candidate_review"}],
          "statuses": ["disputed", "confirmed"], "I4": [1, 1]},
         "As FX-14a to pending_sm; sm_overturn nm -> recorded. T23.5 (c): final_label = the safety manager's label nm; "
         "T22.8 (b): nm == nm -> confirmed. I4 = 1/(1+0).")
    ct = _ep23("ct", "lbl_ct", 200.0)
    incident = {"date_of_injury_or_illness": "2026-11-16", "time_employee_began_work": "07:00", "time_of_event": "08:03",
                "doing_just_before": "Walking along the pedestrian route to rack 4.", "what_happened": "The forks struck the employee's shin.",
                "injury_or_illness": "Bruised shin.", "object_or_substance": "Forklift forks.", "date_of_death": "",
                "treated_in_emergency_room": "no", "hospitalized_overnight": "no", "employee_pseudonym": "EMP-7",
                "health_care_professional": "HCP-2"}
    _t23("FX-14c", [ct], [{"as": "AM-1", "action": "am_approve", "label": "ct", "rationale": "The forks reach the person's leg."},
                          {"as": "SM-1", "action": "edit_fields", "fields": incident},
                          {"as": "SM-1", "action": "set_recordability", "recordable": "yes", "criteria": ["medical_treatment_beyond_first_aid"],
                           "note": "Treated by HCP-2 beyond first aid."},
                          {"as": "OWNER", "action": "hours", "hours_worked": 200000.0}],
         {"reports": 1, "kind_initial": "incident_draft", "kind": "incident", "state": "recorded", "statuses": ["confirmed"],
          "I9_cases": 1, "I9_by_criterion": {"medical_treatment_beyond_first_aid": 1}, "hours_worked": 200000.0, "incidence_rate": 1.0,
          "export_banner": "Equivalent-form data for manual transcription. Not a submission to OSHA.", "incident_fields": sorted(incident)},
         "T23.2 (c): a CT member -> incident_draft. T23.5 (d): lbl_ct -> ct; ct == ct -> confirmed. T23.8 I9: rate = cases x 200,000 / "
         "hours = 1 x 200,000 / 200,000 = 1.0. T23.7 (c): banner fixed; T23.7 (a): twelve fields.", incident=incident)
    human = {"as": "W-1", "action": "create_human", "kind": "near_miss", "offset_s": 1800.0,
             "description": "A forklift reversed out of aisle 3 while I was crossing; I stepped back."}
    _t23("FX-14d", [], [human, {"as": "AM-1", "action": "am_approve", "label": "nm"}],
         {"reports": 1, "state": "recorded", "I8": 1, "F4_k_miss_2": False, "F4_k_miss_1": True, "statuses": []},
         "T23.8 I8: one recorded human-started near_miss at +1800 s, inside the area's monitored coverage [0, 3600) s, and no AI "
         "alert report in the area within +-60 s -> I8 = 1. T23.9 F4: I8 >= k_miss: 1 >= 2 false; with k_miss = 1, 1 >= 1 true. "
         "T23.5 (e): no assessment, adjudication or status entry.")
    trio = [_ep23("e1", "lbl_nm", 0.0, cam=0), _ep23("e2", "lbl_nm", 1.5, cam=1), _ep23("e3", "lbl_nm", 3.2, cam=2)]
    _t23("FX-14e", trio, [{"as": "AM-1", "action": "am_approve", "label": "nm", "rationale": "All three views show the truck stopping hard."}],
         {"reports": 1, "members": 3, "assessments_n": 3, "statuses": ["confirmed", "confirmed", "confirmed"]},
         "Widened by 2.0 s: [-2.0, 3.0], [-0.5, 4.5], [1.2, 6.2]; 1 and 2 overlap, 2 and 3 overlap -> one group of three "
         "(transitive). One assessment and one status entry per member (T23.5 a, d).")
    twelve = [_ep23(f"f{k:02d}", "lbl_nm", 100.0 * k) for k in range(1, 13)]
    _t23("FX-14f", twelve, [], {"reports": 12, "theta_rej": 0.5, "n_flag_min": 10,
                                "rejected_10": {"I3": [10, 12], "F1": True, "wilson_lower_approx": 0.552},
                                "rejected_6": {"I3": [6, 12], "F1": False}},
         "Onsets 100 s apart, widened intervals do not overlap -> 12 reports. F1: n = 12 >= 10; Wilson lower bound of 10/12 "
         "(z = 1.959964) = 0.55197... > 0.5 -> raised (exact value derived with decimal arithmetic in the test); 6/12: lower "
         "bound 0.2538... <= 0.5 -> not raised.")
    _t23("FX-14g", [nm], [{"as": "AM-1", "action": "am_approve", "label": "nm", "rationale": why}],
         {"tamper": "one byte of the last report-log entry", "verified": False, "page_shows": "BROKEN"},
         "T23.15: the report log is hash-chained like validation_status_log; a changed byte breaks the record hash.")
    _t23("FX-14h", [nm], [], {"ai_label": "candidate near miss", "refused_phrase": "near miss", "accepted": list(RECORDED_NM_PHRASES)},
         "T23.12: automated outputs read 'candidate near miss'; unqualified 'near miss' is refused; the two recorded forms are accepted.")
    _t23("FX-14i", [], [], {"draw_after_batch": "refused (ERR-SPEC)", "batch_after_draw": "no episode of a demo run"},
         "T23.11 (b): demo runs leave the T22 frame; a demo draw over a recording already in a batch is refused, nothing written.")


RECORDED_NM_PHRASES = ("recorded near miss (manager-approved)", "recorded near miss (safety-manager overturn)")
_fx14()


def _check_t22(fixture: dict[str, Any]) -> None:
    """T22.8 (b) status mapping and T22.7 tier rule, recomputed from the fixture's own inputs."""
    target, expected = fixture["inputs"]["target"], fixture["expected"]
    mapped = _T22_MAP.get(target["g2_label"], "not_hazardous")
    if "mapped_system_label" in expected and expected["mapped_system_label"] != mapped:
        _refuse(fixture["id"], f"mapped label should be {mapped}")
    for status in expected["status_entries"]:
        final = expected["adjudications"][status["basis_adjudication"]]["final_label"]
        want = "disputed" if final == "unsure" else ("confirmed" if final == mapped else "rejected")
        if status["status"] != want:
            _refuse(fixture["id"], f"status should be {want}")
    for adj in expected["adjudications"]:
        if (adj["tier"], adj["method"]) not in {("tier1", "agreement"), ("tier2", "adjudicator"), ("tier2", "consensus_meeting")}:
            _refuse(fixture["id"], "tier and method do not match T22.7")


def _refuse(fixture_id: str, message: str) -> None:
    raise ContractError("ERR-INVARIANT", f"{fixture_id}: {message}")


def _check_n1(fixture: dict[str, Any]) -> None:
    inputs, expected = fixture["inputs"], fixture["expected"]
    p, m, c, e = (expand(inputs[x]) for x in ("P", "M", "C_any", "E"))
    x = [_and(a, b) for a, b in zip(p, m)]
    e_ep = _or(e)
    k = _or([e_ep, 1 if inputs["minclr_m"] < 0.5 else 0])  # d_nm = 0.5 (TEST-ONLY)
    if k != expected["K"]:
        _refuse(fixture["id"], f"K should be {k}")
    labels = expected["labels"]
    row = {"P_ep": 1 in p, "X_ep": 1 in x, "C_ep": 1 in c, "K": k, "contact_state": expected["contact_state"], "summary_label": expected["summary_label"]}
    row.update({f"lbl_{name}": name in labels for name in ("O", "H", "PC", "NM", "UD", "CT", "IE")})
    issues = vr_rules.check_episode_labels(row)
    if issues:
        _refuse(fixture["id"], issues[0].message)


def check_fixture(fixture: dict[str, Any]) -> None:
    """Refuse a fixture whose expected values contradict the contract invariants or its own arithmetic."""
    fixture_id = fixture["id"]
    if fixture_id.startswith("N1-") and "labels" in fixture.get("expected", {}):
        _check_n1(fixture)
    if fixture_id == "FX-W":
        strata, windows = fixture["inputs"]["strata"], fixture["inputs"]["windows"]
        weights = [strata[w["stratum"]]["w"] for w in windows]
        recall = sum(g * w["m"] for g, w in zip(weights, windows)) / sum(g * w["a"] for g, w in zip(weights, windows))
        plain = sum(w["m"] for w in windows) / sum(w["a"] for w in windows)
        n_eff = sum(weights) ** 2 / sum(g * g for g in weights)
        for got, want in ((recall, "weighted_recall"), (plain, "unweighted_recall"), (n_eff, "n_eff")):
            if abs(got - fixture["expected"][want]) > 1e-9:
                _refuse(fixture_id, f"{want} should be {got}")
    if fixture_id.startswith("FX-13"):
        _check_t22(fixture)
    if fixture_id == "FX-C1":
        r = fixture["record"]
        if abs(r["t_occupied_detected_s"] + r["t_occupied_inferred_s"] + r["t_not_occupied_s"] + r["t_occupancy_unknown_s"] - r["t_coobserved_s"]) > 1e-6:
            _refuse(fixture_id, "CC-03 sum")


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def build_all(out_dir: str | Path) -> dict[str, str]:
    """Write every record fixture and the manifest. Output is byte-deterministic."""
    target = Path(out_dir)
    (target / "records").mkdir(parents=True, exist_ok=True)
    digests: dict[str, str] = {}
    for fixture_id in sorted(FIXTURES):
        fixture = copy.deepcopy(FIXTURES[fixture_id])
        check_fixture(fixture)
        data = _dump(fixture)
        (target / "records" / f"{fixture_id}.json").write_bytes(data)
        digests[f"records/{fixture_id}.json"] = hashlib.sha256(data).hexdigest()
    (target / "manifest.json").write_bytes(_dump({"contract": "E-1.2.3", "fixtures": digests}))
    return digests


if __name__ == "__main__":
    build_all(Path("fixtures"))
