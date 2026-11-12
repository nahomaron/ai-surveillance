"""T-08 part B: Appendix T section T8 (E-1.2.6). Every T8 check value is a test; other expected values come from
Appendix N2 fixtures, Appendix T CT rows, or hand calculations noted inline."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema import vr_rules
from rq1.substrate import builder, evidence, geometry, kinematics, oracle, pows

TOL = 1e-6
FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
S3_SPEC = Spec("S3", "E-1.2.6", "f", "f", ("orc_" + "a" * 26,), (), {})
PERSON = {"class": "person", "shape": "disc", "radius_m": 0.30, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
FORK = {"class": "forklift", "shape": "oriented_rect", "length_m": 2.0, "width_m": 1.0, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
COV = [0.05 ** 2, 0.0, 0.05 ** 2]


def config(g_max=15, w_v=0.5):
    return builder.SubstrateConfig(g_max=g_max, v_min=0.3, w_v=w_v, horizon_s=2.0, pair_classes={"forklift"}, priors={"person": PERSON, "forklift": FORK},
                                   prior_ids={"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                   band_schemes={"bsc_" + "a" * 26: [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]}, v_part=0.5)


def s4_spec(g_max_tag="a", inputs=()):
    return Spec("S4", "E-1.2.6", "f", "f", ("gcf_" + "a" * 26, "sbc_" + g_max_tag * 26, "bsc_" + "a" * 26), tuple(inputs), {})


def box(i):
    return [100.0, 100.0, 140.0, 200.0]


def tracks(n, person_states=None, fork_states=None, fork_frames=None):
    ps = person_states or {}
    fs = fork_states or {}
    person = {"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [100.0, 100.0, 140.0, 200.0], "state": ps.get(i, "tracked")} for i in range(n) if ps.get(i) != "missing"]}
    frames = fork_frames if fork_frames is not None else range(n)
    fork = {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": fs.get(i, "tracked")} for i in frames if fs.get(i) != "missing"]}
    return [person, fork]


def build_s4(s1, truth, positions, cfg=None, calibration=None, spec=None):
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], S3_SPEC)
    return builder.SubstrateBuilder().build(s1, s3, positions, calibration, cfg or config(), spec or s4_spec(inputs=(s3.artifact_id,))), s3


def n2_positions(name, n):
    person = json.loads((FIX / f"{name}.json").read_text())["inputs"]["person_xy"]
    fx = {"N2-G1": lambda t: 0.0, "N2-G2": lambda t: -2.5 + 1.0 * t, "N2-G3": lambda t: 1.5 * t}[name]
    out = {}
    for i in range(n):
        out[(1, i)] = {"xy": person, "cov": COV}
        out[(2, i)] = {"xy": [fx(i / 10), 0.0], "cov": COV, "yaw": 0.0}
    return out


def by_frame(built, table="pair_series"):
    return {r["frame_index"]: r for r in built.tables[table]}


# T8.2 check, and T9.1 check "G2 speed is still 1.000000 m/s": with the shifted window (Appendix T T9.1, E-1.2.7)
# every frame has a velocity, including the track ends.
def test_t8_2_g2_speed_heading_sigma():
    built, _ = build_s4(synthetic_s1.build(50), tracks(50), n2_positions("N2-G2", 50))
    fork = [r for r in built.tables["object_state"] if r["track_id"] == builder.track_ids(built)[2]]
    assert len(fork) == 50
    assert all(r["speed_mps"] == pytest.approx(1.0, abs=TOL) and r["heading_rad"] == pytest.approx(0.0, abs=TOL) and r["speed_sigma_mps"] == pytest.approx(0.0, abs=TOL)
               for r in fork)
    assert all(r["sigma_status"] == "uncalibrated_model" for r in fork)


def test_t9_1_window_is_shifted_not_shrunk():
    times = {i: i / 10 for i in range(10)}
    run = list(range(10))
    assert kinematics.shifted_window(run, times, 0.0, 0.5) == [0, 1, 2, 3, 4, 5]  # [0, 0.5], not [0, 0.25]
    assert kinematics.shifted_window(run, times, 0.9, 0.5) == [4, 5, 6, 7, 8, 9]  # [0.4, 0.9]
    assert kinematics.shifted_window(run, times, 0.5, 0.5) == [3, 4, 5, 6, 7]  # interior: centred [0.25, 0.75]
    assert kinematics.shifted_window([2, 3, 4], times, 0.3, 0.5) == [2, 3, 4]  # run shorter than w_v: the whole run


def test_t9_1_runs_split_at_unusable_frames_and_coverage_breaks():
    order = list(range(8))
    runs = kinematics.contiguous_runs(order, usable={0, 1, 2, 4, 5, 6, 7}, crosses_break=lambda a, b: (a, b) == (5, 6))
    assert runs[0] == [0, 1, 2] and runs[4] == [4, 5] and runs[7] == [6, 7] and 3 not in runs


def test_t9_1_lost_frame_ends_the_run_and_the_velocity_window():
    # Person lost on frame 5 of 10: frames 0-4 and 6-9 are separate runs, so frame 4's window is [0, 0.4], never across frame 5.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={5: "lost"}), n2_positions("N2-G3", 10))
    person = {r["frame_index"]: r for r in built.tables["object_state"] if r["track_id"] == builder.track_ids(built)[1]}
    assert person[4]["speed_mps"] == pytest.approx(0.0, abs=TOL) and person[5]["speed_mps"] is None
    assert person[6]["speed_mps"] == pytest.approx(0.0, abs=TOL)  # run 6-9: 4 frames spanning 0.3 s >= w_v/2


def test_t9_1_keeps_the_t8_2_span_requirement():
    # A run of 3 frames spans 0.2 s < w_v/2: T9.1 uses the whole run, and T8.2's span rule (unchanged by T9.1) makes speed null. CR-009 item 1.
    built, _ = build_s4(synthetic_s1.build(10), tracks(10, person_states={3: "lost", 7: "lost"}), n2_positions("N2-G3", 10))
    person = {r["frame_index"]: r for r in built.tables["object_state"] if r["track_id"] == builder.track_ids(built)[1]}
    assert person[4]["speed_mps"] is None and person[4]["speed_mps_null_reason"] == "not_observable"
    assert person[1]["speed_mps"] is None  # run 0-2, also 0.2 s


def test_t8_2_ols_standard_errors():
    t = [0.0, 0.1, 0.2, 0.3]
    xs = [0.0, 0.11, 0.19, 0.31]
    fit = kinematics.fit_velocity(t, xs, [0.0] * 4)
    slope = np.polyfit(t, xs, 1)[0]
    residuals = np.array(xs) - np.polyval(np.polyfit(t, xs, 1), t)
    se = math.sqrt(residuals @ residuals / 2 / sum((ti - 0.15) ** 2 for ti in t))  # hand formula, n - 2 = 2
    assert fit.vx == pytest.approx(slope, abs=1e-12) and fit.sigma_vx == pytest.approx(se, abs=1e-12)
    assert fit.speed_sigma == pytest.approx(math.sqrt((fit.vx * fit.sigma_vx) ** 2) / abs(fit.vx), abs=1e-12)


def test_t8_2_heading_null_below_v_min_and_g1_static_forklift():
    built, _ = build_s4(synthetic_s1.build(50), tracks(50), n2_positions("N2-G1", 50))
    fork = {r["frame_index"]: r for r in built.tables["object_state"] if r["track_id"] == builder.track_ids(built)[2]}
    assert fork[10]["speed_mps"] == pytest.approx(0.0, abs=TOL)
    assert fork[10]["heading_rad"] is None and fork[10]["heading_rad_null_reason"] == "not_applicable"


def test_t8_2_yaw_rules():
    assert kinematics.fill_yaw([None, None, 0.5, None], [0.0, 0.0, 1.0, 0.1], [None, None, 0.7, None], v_min=0.3) == [0.5, 0.5, 0.5, 0.5]
    assert kinematics.fill_yaw([None, None, None], [0.0, 1.0, 0.0], [None, 0.4, None], v_min=0.3) == [0.4, 0.4, 0.4]  # forward then backward fill
    assert kinematics.fill_yaw([None, None], [0.0, 0.1], [None, None], v_min=0.3) == [None, None]


def test_t8_2_unknown_yaw_uses_circumscribed_disc_and_flags():
    positions = n2_positions("N2-G1", 20)
    for k in list(positions):
        positions[k].pop("yaw", None)
    built, _ = build_s4(synthetic_s1.build(20), tracks(20), positions)
    row = by_frame(built)[5]
    radius = 0.5 * math.sqrt(2.0 ** 2 + 1.0 ** 2)
    assert row["clearance_m"] == pytest.approx(1.9 - radius - 0.30, abs=TOL)  # hand calculation: centre distance 1.9
    assert row["borderline_flags"] == ["footprint_orientation_unknown"]


# T8.3 check: G3 at t = 0 has its predicted minimum at tau, so ttca is null not_observable
def test_t8_3_g3_ttca_and_closing_rate():
    # T8.3 check at t = 0 with the exact G3 velocities (N2: speeds are exact): the minimum is at tau, so not_observable.
    _, t_min = geometry.predict_min_clearance((5.0, 0.0), (0.0, 0.0), 0.30, (0.0, 0.0), (1.5, 0.0), 0.0, 2.0, 1.0, horizon_s=2.0)
    assert t_min == pytest.approx(2.0, abs=TOL) and kinematics.ttca(t_min, 2.0) == (None, "not_observable")
    built, _ = build_s4(synthetic_s1.build(10), tracks(10), n2_positions("N2-G3", 10))
    rows = by_frame(built)
    # T9.1 check (E-1.2.7): G3 has a velocity on every frame, and ttca_s at t = 0 is null (not_observable).
    assert rows[0]["predicted"][0]["t_at_min_s"] == pytest.approx(2.0, abs=TOL)
    assert rows[0]["ttca_s"] is None and rows[0]["ttca_s_null_reason"] == "not_observable"
    assert rows[5]["closing_rate_mps"] == pytest.approx(1.5, abs=TOL)  # clearance 3.70 - 1.5 t, so -slope = 1.5


def test_t8_3_static_pair_ttca_not_applicable():
    built, _ = build_s4(synthetic_s1.build(20), tracks(20), n2_positions("N2-G1", 20))
    row = by_frame(built)[10]
    assert row["ttca_s"] is None and row["ttca_s_null_reason"] == "not_applicable"


# T8.4 check: G1 with diag(0.05^2) for both objects and zero dimension sigma gives 0.0707107 m
def test_t8_4_g1_clearance_sigma():
    built, _ = build_s4(synthetic_s1.build(50), tracks(50), n2_positions("N2-G1", 50))
    row = by_frame(built)[25]
    assert row["clearance_sigma_m"] == pytest.approx(0.0707107, abs=1e-7) and row["sigma_status"] == "uncalibrated_model"


def test_t8_4_dimension_term_and_null_covariance():
    u = geometry.clearance_gradient((0.0, 1.9), (0.0, 0.0), 0.0, 2.0, 1.0)
    assert u == pytest.approx((0.0, 1.0))
    sigma = geometry.clearance_sigma(u, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], yaw=0.0, sigma_length=0.2, sigma_width=0.1, disc=False)
    assert sigma == pytest.approx(0.5 * (0.0 * 0.2 + 1.0 * 0.1))  # hand calculation: u is perpendicular to h
    assert geometry.clearance_sigma(u, None, [0.0, 0.0, 0.0], 0.0, 0.2, 0.1, False) is None
    assert geometry.clearance_sigma((1.0, 0.0), [0.0] * 3, [0.0] * 3, None, 0.2, 0.1, True) == pytest.approx(0.1)  # disc: half max


def test_t8_4_gradient_inside_uses_nearest_edge_normal():
    assert geometry.clearance_gradient((0.9, 0.0), (0.0, 0.0), 0.0, 2.0, 1.0) == pytest.approx((1.0, 0.0))  # 0.1 from the +x edge
    assert geometry.clearance_gradient((0.0, -0.4), (0.0, 0.0), 0.0, 2.0, 1.0) == pytest.approx((0.0, -1.0))


# T8.5 checks
@pytest.mark.parametrize("f,px,norm", [([200, 120, 300, 220], 60.0, 0.60), ([170, 240, 270, 300], 50.0, 0.50), ([130, 150, 230, 250], -10.0, -0.10)])
def test_t8_5_image_gap(f, px, norm):
    assert geometry.image_gap([100, 100, 140, 200], f) == pytest.approx((px, norm), abs=1e-12)


# T8.6 and T8.7
def test_t8_6_evidence_state_precedence():
    size = (1000, 600)
    assert evidence.evidence_state(None, size, None, 0.5) == "lost"
    assert evidence.evidence_state({"state": "lost", "bbox_xyxy_px": [5, 5, 50, 50]}, size, None, 0.5) == "lost"
    assert evidence.evidence_state({"state": "predicted", "bbox_xyxy_px": [0, 0, 50, 50]}, size, None, 0.5) == "occluded_predicted"
    assert evidence.evidence_state({"state": "tracked", "bbox_xyxy_px": [0.5, 10, 50, 50]}, size, None, 0.5) == "truncated"
    assert evidence.evidence_state({"state": "tracked", "bbox_xyxy_px": [10, 10, 50, 599.2]}, size, None, 0.5) == "truncated"
    assert evidence.evidence_state({"state": "tracked", "bbox_xyxy_px": [10, 10, 50, 50]}, size, 0.4, 0.5) == "partially_visible"
    assert evidence.evidence_state({"state": "tracked", "bbox_xyxy_px": [10, 10, 50, 50]}, size, None, 0.5) == "visible"


def test_t8_7_q_state_and_reasons():
    assert evidence.q_state("detected", "visible", "visible", "measured") == ("sufficient", [])
    assert evidence.q_state("detected", "visible", "visible", "measured", coverage="usable_degraded") == ("sufficient", [])
    assert evidence.q_state("inferred", "occluded_predicted", "visible", "measured") == ("insufficient", ["person_occluded"])
    assert evidence.q_state("inferred", "occluded_predicted", "occluded_predicted", "measured") == ("insufficient", ["person_occluded", "forklift_occluded", "predicted_only"])
    assert evidence.q_state("detected", "truncated", "visible", "measured") == ("insufficient", ["truncated"])
    assert evidence.q_state("insufficient", "visible", "visible", "timing_uncertain") == ("insufficient", ["timing_uncertain"])


# T8.1 POW gap bridging
def joint_states(n, gap, kind="missing"):
    return {i: kind for i in gap}


def test_t8_1_short_gap_is_bridged_and_insufficient():
    s1 = synthetic_s1.build(30)
    built, _ = build_s4(s1, tracks(30, person_states=joint_states(30, range(10, 14))), n2_positions("N2-G1", 30))
    assert len(built.tables["pow"]) == 1
    p = built.tables["pow"][0]
    assert p["bridged_gaps"] == [{"start_frame": 10, "end_frame_excl": 14}] and p["end_reason"] == "recording_end"
    assert p["t_insufficient_s"] == pytest.approx(0.4, abs=TOL) and p["t_detected_s"] == pytest.approx(2.6, abs=TOL)
    assert by_frame(built)[11]["evidence_class"] == "insufficient"


def test_t8_1_long_gap_splits_with_continuation():
    built, _ = build_s4(synthetic_s1.build(40), tracks(40, person_states=joint_states(40, range(10, 26))), n2_positions("N2-G1", 40), cfg=config(g_max=15))
    first, second = sorted(built.tables["pow"], key=lambda p: p["start_frame"])
    assert (first["start_frame"], first["end_frame_excl"], first["end_reason"]) == (0, 10, "gap_exceeded")
    assert second["start_frame"] == 26 and second["continuation_of_nk"] == [first["person_track_id"], first["forklift_track_id"], 0]
    assert second["continuation_of_id"] == first["pow_id"]


def test_t8_1_coverage_break_inside_gap_ends_pow():
    s1 = synthetic_s1.build(30, excluded=frozenset({12}))
    built, _ = build_s4(s1, tracks(29, person_states=joint_states(29, range(10, 13))), n2_positions("N2-G1", 29))
    assert sorted((p["start_frame"], p["end_frame_excl"], p["end_reason"]) for p in built.tables["pow"])[0] == (0, 10, "coverage_gap")


def test_ti_08_frameless_gap_between_joint_frames_splits():
    s1 = synthetic_s1.build(20, dropouts={9: 4.0})
    built, _ = build_s4(s1, tracks(20), n2_positions("N2-G1", 20))
    pows_ = sorted(built.tables["pow"], key=lambda p: p["start_frame"])
    assert [(p["start_frame"], p["end_frame_excl"], p["end_reason"]) for p in pows_] == [(0, 10, "coverage_gap"), (10, 20, "recording_end")]


def test_t8_1_track_end_reasons():
    built, _ = build_s4(synthetic_s1.build(30), tracks(30, fork_frames=range(0, 20)), n2_positions("N2-G1", 30))
    assert built.tables["pow"][0]["end_reason"] == "track_end_forklift"
    built, _ = build_s4(synthetic_s1.build(30), tracks(30, person_states={i: "missing" for i in range(20, 30)}), n2_positions("N2-G1", 30))
    assert built.tables["pow"][0]["end_reason"] == "track_end_person"


# Appendix T CT-T-18, CT-F-01, CT-T-19, CT-E-05 to 08, CT-I-03, CT-I-04
def clip_s1(clip_dir, name, f_untimed=0.05):
    from rq1.decode import stage
    from rq1.decode.timestamps import DecodeConfig
    from rq1.ids import core
    r = core.anchor_id("rec", "recording", [name])
    tl = {"tl_id": core.anchor_id("tl", "timeline", ["recording_local", r]), "kind": "recording_local", "extent_start_tl_s": None, "extent_end_tl_s": None}
    item = stage.S1Input(r, core.anchor_id("cam", "camera", ["c"]), clip_dir / f"{name}.mkv", clip_dir / f"{name}.faults.json")
    return stage.run_s1(tl, [item], DecodeConfig(1.5, f_untimed, 0.10, "rv1", {r: 0.033}, "delta_nom"), Spec("S1", "E-1.2.6", "f", "f", ("dcf_" + "a" * 26,), (), {})).tables


def static_positions(n):
    return {**{(1, i): {"xy": [0.0, 1.9], "cov": COV} for i in range(n)}, **{(2, i): {"xy": [0.0, 0.0], "cov": COV, "yaw": 0.0} for i in range(n)}}


def test_ct_t_18_person_missed_on_f2_is_inferred(clip_dir):
    s1 = clip_s1(clip_dir, "fx_clip_a")
    built, _ = build_s4(s1, tracks(3, person_states={1: "predicted"}), static_positions(3))
    p = built.tables["pow"][0]
    # f2 (frame index 1) predicted: inferred 0.034; f1 corrupt: insufficient 0.033; f0 and f3 detected 0.066.
    assert (p["t_detected_s"], p["t_inferred_s"], p["t_insufficient_s"]) == pytest.approx((0.066, 0.034, 0.033), abs=1e-9)


def test_ct_f_01_one_second_bridged_by_prediction():
    built, _ = build_s4(synthetic_s1.build(40), tracks(40, person_states={i: "predicted" for i in range(10, 20)}), static_positions(40))
    p = built.tables["pow"][0]
    assert p["t_inferred_s"] == pytest.approx(1.0, abs=TOL) and p["t_detected_s"] == pytest.approx(3.0, abs=TOL)


@pytest.mark.parametrize("name,f_untimed", [("fx_clip_a", 0.05), ("fx_clip_b", 0.5), ("fx_clip_c", 0.5), ("fx_clip_d", 0.05)])
def test_ct_t_19_exposure_excludes_unusable_and_uncertain(clip_dir, name, f_untimed):
    s1 = clip_s1(clip_dir, name, f_untimed)
    n = sum(1 for f in s1["frame"] if f["eligible"])
    built, _ = build_s4(s1, tracks(n), static_positions(n))
    profile = built.tables["exposure_profile"][0]
    expected_detected = {"fx_clip_a": 0.100, "fx_clip_b": 0.067, "fx_clip_c": 0.033, "fx_clip_d": 0.133}[name]
    assert sum(profile["t_in_band_detected_s"]) == pytest.approx(expected_detected, abs=1e-9)  # nothing from unusable or uncertain support
    assert profile["t_in_band_detected_s"][3] == pytest.approx(expected_detected, abs=1e-9)  # clearance 1.10 lies in [1, 2)
    assert vr_rules.check_exposure_sums([profile]) == []


def test_ct_e_07_ct_e_08_profiles_and_sums():
    built, _ = build_s4(synthetic_s1.build(50), tracks(50, person_states={i: "predicted" for i in range(20, 25)}), n2_positions("N2-G2", 50))
    pow_keys = [[p["person_track_id"], p["forklift_track_id"], p["start_frame"]] for p in built.tables["pow"]]
    assert vr_rules.check_profile_cardinality(pow_keys, list(config().band_schemes), built.tables["exposure_profile"]) == []
    assert vr_rules.check_exposure_sums(built.tables["exposure_profile"]) == []
    profile = built.tables["exposure_profile"][0]
    assert sum(profile["t_in_band_inferred_s"]) == pytest.approx(0.5, abs=TOL)
    assert profile["t_total_support_s"] == pytest.approx(5.0, abs=TOL)
    # Forklift moves at 1.0 m/s > v_min on every frame (T9.1: the window shifts at the track ends), so no motion-unknown time.
    assert profile["t_motion_unknown_s"] == pytest.approx(0.0, abs=TOL)
    assert profile["t_joint_visible_s"] == pytest.approx(4.5, abs=TOL)  # detected frames with both objects visible


def test_ct_e_06_and_vr_e_015_on_built_series():
    built, _ = build_s4(synthetic_s1.build(10), tracks(10), n2_positions("N2-G3", 10))
    assert vr_rules.check_pair_series(built.tables["pair_series"]) == []


@pytest.mark.parametrize("name", ["N2-G1", "N2-G2", "N2-G3"])
def test_n2_through_the_substrate(name):
    fixture = json.loads((FIX / f"{name}.json").read_text())["expected"]
    n = len(fixture["clearance_m"])
    built, _ = build_s4(synthetic_s1.build(n), tracks(n), n2_positions(name, n))
    rows = by_frame(built)
    assert [rows[i]["clearance_m"] for i in range(n)] == pytest.approx(fixture["clearance_m"], abs=TOL)
    if "pred_min_clearance_m" in fixture:
        assert [rows[i]["predicted"][0]["pred_min_clearance_m"] for i in range(n)] == pytest.approx(fixture["pred_min_clearance_m"], abs=TOL)  # every frame (T9.1)
    assert len(built.tables["pow"]) == 1 and built.tables["pow"][0]["t_detected_s"] == pytest.approx(n / 10, abs=TOL)


def test_ct_e_05_fx_07_uncalibrated_camera():
    built, _ = build_s4(synthetic_s1.build(10), tracks(10), positions={})
    state = built.tables["object_state"][0]
    world = ("x_m", "y_m", "pos_cov_m2", "speed_mps", "heading_rad")
    assert state["geometry_method"] == "image_only" and all(state[f] is None and state[f"{f}_null_reason"] == "uncalibrated" for f in world)
    pair = by_frame(built)[3]
    assert (pair["clearance_m"], pair["clearance_state"], pair["footprint_overlap"]) == (None, "unmeasurable_uncalibrated", 2)
    assert pair["image_gap_px"] == pytest.approx(160.0)  # boxes [100,100,140,200] and [300,100,500,220]: dx = 160, dy < 0
    assert vr_rules.check_object_states(built.tables["object_state"], {}) == []


def test_ground_plane_homography_and_full_camera_positions():
    b1 = json.loads((FIX / "FX-B1.json").read_text())["record"]
    x, y = geometry.homography_to_floor(b1["homography_img_to_floor"], (120.0, 200.0))
    h = np.array(b1["homography_img_to_floor"]).reshape(3, 3)
    p = h @ np.array([120.0, 200.0, 1.0])
    assert (x, y) == pytest.approx((p[0] / p[2], p[1] / p[2]))
    b3 = json.loads((FIX / "FX-B3.json").read_text())["record"]
    xf, yf = geometry.full_camera_to_floor(b3, (900.0, 700.0))
    import cv2
    pixel, _ = cv2.projectPoints(np.array([[xf, yf, 0.0]]), cv2.Rodrigues(np.array(b3["R_cam_from_world"]).reshape(3, 3))[0],
                                 np.array(b3["t_cam_from_world_m"]), np.array(b3["intrinsics_K"]).reshape(3, 3), np.zeros(5))
    assert pixel.ravel() == pytest.approx([900.0, 700.0], abs=1e-6)  # round trip through the floor point


def test_ct_i_03_and_ct_i_04_identity_changes():
    s1 = synthetic_s1.build(20)
    a, s3 = build_s4(s1, tracks(20), static_positions(20))
    b, _ = build_s4(s1, tracks(20), static_positions(20), spec=s4_spec("b", inputs=(s3.artifact_id,)))  # g_max configuration changed
    assert not {p["pow_id"] for p in a.tables["pow"]} & {p["pow_id"] for p in b.tables["pow"]}
    moved = {k: {**v, "xy": [v["xy"][0] + 0.01, v["xy"][1]]} for k, v in static_positions(20).items()}
    c, _ = build_s4(s1, tracks(20), moved, spec=s4_spec(inputs=(s3.artifact_id, "art_" + "c" * 26)))  # recalibration: new geometry input
    for table in ("object_state", "pair_series", "pow"):
        prefix = {"object_state": "ost", "pair_series": "psr", "pow": "pow"}[table]
        assert not {r[f"{prefix}_id"] for r in a.tables[table]} & {r[f"{prefix}_id"] for r in c.tables[table]}


def test_s4_is_deterministic_and_ids_recompute():
    s1 = synthetic_s1.build(20)
    a, _ = build_s4(s1, tracks(20), n2_positions("N2-G2", 20))
    b, _ = build_s4(s1, tracks(20), n2_positions("N2-G2", 20))
    assert a.artifact_id == b.artifact_id
    for table, rows in a.tables.items():
        assert vr_rules.check_ids(table, rows, a.artifact_id) == [], table


def test_activity_segments_in_s4():
    built, s3 = build_s4(synthetic_s1.build(10), tracks(10, person_states={5: "predicted"}), static_positions(10))
    states = [r["ai_activity_state"] for r in sorted(built.tables["activity_segment"], key=lambda r: r["t_start_tl_s"])]
    assert states == ["pair_detected", "objects_detected_no_pair", "pair_detected"]
    assert {r["perception_artifact_id"] for r in built.tables["activity_segment"]} == {s3.artifact_id}
