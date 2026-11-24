"""Appendix T T24 (E-1.2.25; D-54): camera-path footprint centre (T24.1) and floor-position resolution gate (T24.2).

Every T24.4 check is a test. Expected values are the T24.4 values; the builder-level cases use hand calculations recorded
inline (pinhole camera of T24.4: H = 3 m, horizontal optical axis, f = 1000 px, so s = max(H/dv, fH/dv^2)).
"""
import math
import random

import numpy as np
import pytest

from rq1.fixtures import synthetic_s1
from rq1.ids import core
from rq1.ids.artifact import config_id
from rq1.schema.errors import ContractError
from rq1.substrate import builder, geometry

from test_part_b import FORK, PERSON, build_s4, config, tracks

C0 = (0.0, 0.0)
L, W, D, R_T = 3.03, 1.13, 1.04, 2.0


# ------------------------------------------------------------------------------------------------------------ T24.1 (c)

def test_t24_1_body_along_the_sight_line():
    p_f = (10.0 - L / 2, 0.0)  # near edge of a body whose axis lies along the sight line
    assert p_f[0] == pytest.approx(8.485, abs=1e-9)
    p_c = geometry.anchor_centre(p_f, C0, D, R_T)
    assert p_c[0] == pytest.approx(9.525, abs=1e-9) and p_c[1] == pytest.approx(0.0, abs=1e-12)


def test_t24_1_body_across_the_sight_line():
    p_f = (10.0 - W / 2, 0.0)
    assert p_f[0] == pytest.approx(9.435, abs=1e-9)
    p_c = geometry.anchor_centre(p_f, C0, D, R_T)
    assert p_c[0] == pytest.approx(10.475, abs=1e-9) and p_c[1] == pytest.approx(0.0, abs=1e-12)


def test_t24_1_oblique_point():
    p_c = geometry.anchor_centre((6.0, 8.0), C0, D, R_T)
    assert p_c == pytest.approx((6.624, 8.832), abs=1e-9)


def test_t24_1_taper_inside_r_taper():
    p_c = geometry.anchor_centre((0.5, 0.0), C0, D, R_T)  # d_eff = 1.04 * 0.5 / 2 = 0.26
    assert p_c == pytest.approx((0.76, 0.0), abs=1e-12)


def test_t24_1_point_at_the_camera_foot():
    assert geometry.anchor_centre((0.0, 0.0), C0, D, R_T) == (0.0, 0.0)
    assert geometry.anchor_centre((1e-10, 0.0), C0, D, R_T) == (1e-10, 0.0)  # r < 1e-9 m


def test_t24_1_null_point():
    assert geometry.anchor_centre(None, C0, D, R_T) is None


def test_t24_1_camera_floor_centre_is_minus_rt_t():
    cal = pinhole(3.0, cy=500.0)
    cal["t_cam_from_world_m"] = list(-np.array(cal["R_cam_from_world"]).reshape(3, 3) @ np.array([2.0, -1.5, 3.0]))
    assert geometry.camera_floor_centre(cal) == pytest.approx((2.0, -1.5), abs=1e-12)


def test_t24_1_parameters_absent_keep_the_prior_and_its_id():
    prior = dict(FORK, anchor="box_bottom_centre")
    assert builder.anchor_params(prior) is None
    assert core.make_id("fpp", prior) == core.make_id("fpp", dict(FORK, anchor="box_bottom_centre"))
    assert config_id("footprint_prior", prior) == config_id("footprint_prior", dict(prior))
    with_params = dict(prior, anchor_offset_m=D, anchor_taper_m=R_T)
    assert config_id("footprint_prior", with_params) != config_id("footprint_prior", prior)  # T24.1 (f)
    assert builder.anchor_params(with_params) == (D, R_T)


@pytest.mark.parametrize("extra", [{"anchor_offset_m": 1.0}, {"anchor_taper_m": 2.0}])
def test_t24_1_one_parameter_alone_is_err_spec(extra):
    with pytest.raises(ContractError) as e:
        builder.anchor_params(dict(FORK, anchor="box_bottom_centre", **extra))
    assert e.value.code == "ERR-SPEC"


@pytest.mark.parametrize("d, r", [(-0.1, 2.0), (1.0, 0.0), (1.0, -1.0)])
def test_t24_1_parameter_ranges_are_err_spec(d, r):
    with pytest.raises(ContractError) as e:
        builder.anchor_params(dict(FORK, anchor="box_bottom_centre", anchor_offset_m=d, anchor_taper_m=r))
    assert e.value.code == "ERR-SPEC"


def test_t24_1_rear_axle_on_the_camera_path_is_err_spec():
    cfg = config()
    cfg = builder.SubstrateConfig(**{**cfg.__dict__, "priors": {"person": PERSON, "forklift": dict(FORK, anchor="rear_axle")}})
    with pytest.raises(ContractError) as e:
        build_s4(synthetic_s1.build(5), tracks(5), {}, cfg=cfg, calibration=pinhole(3.0, cy=0.0))
    assert e.value.code == "ERR-SPEC"


# ------------------------------------------------------------------------------------------------------------ T24.2 (a)

def pinhole(h: float, cy: float, cx: float = 320.0, f: float = 1000.0) -> dict:
    """T24.4 camera: centre (0, 0, h), optical axis horizontal along world +y; OpenCV axes (x right, y down, z forward)."""
    r = [[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]
    t = list(-np.array(r) @ np.array([0.0, 0.0, h]))
    return {"cal_id": "cal_" + "a" * 26, "world_frame_id": "wfr_" + "a" * 26, "calibration_tier": "full_camera", "quality_state": "unvalidated",
            "intrinsics_K": [f, 0.0, cx, 0.0, f, cy, 0.0, 0.0, 1.0], "R_cam_from_world": [x for row in r for x in row], "t_cam_from_world_m": t,
            "distortion_model": "none", "distortion_coeffs": []}


@pytest.mark.parametrize("dv, expected, gated", [(100.0, 0.300, True), (200.0, 0.075, False), (300.0, 0.03333333333, False),
                                                 (math.sqrt(30000.0), 0.1000, False)])
def test_t24_2_pinhole_values(dv, expected, gated):
    cal = pinhole(3.0, cy=500.0)
    s = geometry.floor_resolution(cal, (320.0, 500.0 + dv))
    assert s == pytest.approx(max(3.0 / dv, 3000.0 / dv ** 2), abs=1e-9)
    assert s == pytest.approx(expected, abs=1e-6)
    assert geometry.resolution_gated(s, 0.1) is gated


def test_t24_2_boundary_is_kept():
    cal = pinhole(3.0, cy=500.0)
    s = geometry.floor_resolution(cal, (320.0, 500.0 + math.sqrt(30000.0)))
    assert geometry.resolution_gated(s, 0.1) is False  # s <= s_max is kept; s carries ~1e-16 rounding here (AR-67 item 5)
    assert geometry.resolution_gated(0.1, 0.1) is False
    assert geometry.resolution_gated(0.1 + 1e-9, 0.1) is True


def test_t24_2_horizon_has_no_intersection():
    cal = pinhole(3.0, cy=500.0)
    assert geometry.floor_resolution(cal, (320.0, 500.0)) is None
    assert geometry.full_camera_to_floor(cal, (320.0, 500.0)) is None
    assert geometry.floor_resolution(cal, (320.0, 400.0)) is None  # above the horizon


@pytest.mark.parametrize("a, gated", [(0.02, False), (0.15, True)])
def test_t24_2_homography_diagonal(a, gated):
    cal = {"calibration_tier": "ground_plane_homography", "homography_img_to_floor": [a, 0.0, 0.0, 0.0, a, 0.0, 0.0, 0.0, 1.0]}
    s = geometry.floor_resolution(cal, (123.0, 45.0))
    assert s == pytest.approx(a, abs=1e-12)
    assert geometry.resolution_gated(s, 0.1) is gated


def test_t24_2_homography_projective():
    h = [0.02, 0.0, 0.0, 0.0, 0.02, 0.0, 0.0, 0.01, 1.0]
    assert geometry.homography_to_floor(h, (0.0, 100.0)) == pytest.approx((0.0, 1.0), abs=1e-12)
    cal = {"calibration_tier": "ground_plane_homography", "homography_img_to_floor": h}
    assert geometry.floor_resolution(cal, (0.0, 100.0)) == pytest.approx(0.01, abs=1e-12)


def test_t24_2_homography_w_le_0_has_no_intersection():
    cal = {"calibration_tier": "ground_plane_homography", "homography_img_to_floor": [1.0, 0, 0, 0, 1.0, 0, 0, -0.01, 1.0]}
    assert geometry.floor_resolution(cal, (0.0, 100.0)) is None  # w = 0
    assert geometry.floor_resolution(cal, (0.0, 200.0)) is None  # w < 0


def _fd_s(fn, p, h=1e-3):
    j = np.zeros((2, 2))
    for k in range(2):
        dp = np.zeros(2)
        dp[k] = h
        a, b = fn(tuple(np.array(p) + dp)), fn(tuple(np.array(p) - dp))
        j[:, k] = (np.array(a) - np.array(b)) / (2 * h)
    return float(np.linalg.svd(j, compute_uv=False)[0])


def _random_camera(rng: random.Random) -> dict:
    yaw, pitch = rng.uniform(-math.pi, math.pi), rng.uniform(0.2, 1.2)  # looking down by pitch
    centre = np.array([rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(1.0, 8.0)])
    fwd = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
    right = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    down = np.cross(fwd, right)
    r = np.vstack([right, down, fwd])
    f = rng.uniform(400, 1500)
    return {"calibration_tier": "full_camera", "intrinsics_K": [f, 0, 640, 0, f, 360, 0, 0, 1], "R_cam_from_world": list(r.ravel()),
            "t_cam_from_world_m": list(-r @ centre), "distortion_model": "none", "distortion_coeffs": []}


def test_t24_2_analytic_equals_finite_difference_on_random_cameras():
    rng = random.Random(20261123)
    checked = 0
    for _ in range(50):
        cal = _random_camera(rng)
        for _ in range(10):
            p = (rng.uniform(0, 1280), rng.uniform(0, 720))
            s = geometry.floor_resolution(cal, p)
            if s is None or s > 5.0:
                continue
            fd = _fd_s(lambda q: geometry.full_camera_to_floor(cal, q), p)
            assert s == pytest.approx(fd, abs=1e-5)
            checked += 1
    assert checked > 200


def test_t24_2_analytic_equals_finite_difference_on_random_homographies():
    rng = random.Random(7)
    for _ in range(100):
        h = [rng.uniform(0.005, 0.05), rng.uniform(-0.01, 0.01), rng.uniform(-5, 5), rng.uniform(-0.01, 0.01), rng.uniform(0.005, 0.05),
             rng.uniform(-5, 5), rng.uniform(-1e-4, 1e-4), rng.uniform(-1e-4, 1e-4), 1.0]
        cal = {"calibration_tier": "ground_plane_homography", "homography_img_to_floor": h}
        p = (rng.uniform(0, 1280), rng.uniform(0, 720))
        s = geometry.floor_resolution(cal, p)
        assert s == pytest.approx(_fd_s(lambda q: geometry.homography_to_floor(h, q), p), abs=1e-5)


# ------------------------------------------------------------------------------------------------- builder (T24.2 c, T24.3)
# The test_part_b scene: person box [100, 100, 140, 200] -> foot (120, 200); forklift box [300, 100, 500, 220] -> foot (400, 220).
# Pinhole H = 3 m, f = 1000, principal column cx = 320, principal row cy. The feet are off the principal column
# (person du = -200, forklift du = +80), so the hand formula is the off-axis one (s_hand below); on the principal column
# (du = 0) it reduces to the T24.4 formula max(H/dv, fH/dv^2). Correction recorded 23 Nov 2026: the first draft of these
# builder cases used the du = 0 formula for off-axis feet; the code was right, the hand calculation was not.
#   cy = 0:   person dv = 200 -> s = 0.07654 (kept); forklift dv = 220 -> s = 0.06219 (kept)
#   cy = 100: person dv = 100 -> s = 0.30600 (gated); forklift dv = 120 -> s = 0.20901 (gated)
#   cy = 200: person dv = 0 -> no intersection; forklift dv = 20 -> s = 7.52397 (gated)


def s_hand(du: float, dv: float, h: float = 3.0, f: float = 1000.0) -> float:
    """Horizontal-axis pinhole at height h: Y = f h / dv, X = du h / dv, so J = [[h/dv, -du h/dv^2], [0, -f h/dv^2]];
    s = sqrt of the largest eigenvalue of J^T J (closed form for 2 x 2)."""
    a, b, c, d = h / dv, -du * h / dv ** 2, 0.0, -f * h / dv ** 2
    p, q = a * a + b * b + c * c + d * d, a * d - b * c
    return math.sqrt((p + math.sqrt(p * p - 4 * q * q)) / 2)


def test_s_hand_reduces_to_the_t24_4_formula_on_the_principal_column():
    for dv in (100.0, 200.0, 300.0):
        assert s_hand(0.0, dv) == pytest.approx(max(3.0 / dv, 3000.0 / dv ** 2), abs=1e-12)

def gate_cfg(s_max=0.1, fork=None):
    cfg = config()
    priors = {"person": PERSON, "forklift": fork or FORK}
    return builder.SubstrateConfig(**{**cfg.__dict__, "priors": priors, "s_max": s_max})


def states(built):
    ids = builder.track_ids(built)
    rows = built.tables["object_state"]
    return ({r["frame_index"]: r for r in rows if r["track_id"] == ids[1]}, {r["frame_index"]: r for r in rows if r["track_id"] == ids[2]})


def test_t24_2_gate_off_adds_no_column_and_keeps_e_1_2_24():
    s1 = synthetic_s1.build(10)
    off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=pinhole(3.0, cy=0.0))
    off2, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(s_max=None), calibration=pinhole(3.0, cy=0.0))
    assert off.artifact_id == off2.artifact_id and off.payload_sha256 == off2.payload_sha256
    assert all("floor_resolution_m_per_px" not in r and "floor_resolution_m_per_px_null_reason" not in r for r in off.tables["object_state"])
    horizon, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=pinhole(3.0, cy=200.0))
    assert {r["clearance_state"] for r in horizon.tables["pair_series"]} == {"unmeasurable_occluded"}  # E-1.2.24 for horizon rays


def test_t24_2_gate_on_kept_positions_store_s_and_equal_the_gate_off_positions():
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(), calibration=pinhole(3.0, cy=0.0))
    off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=pinhole(3.0, cy=0.0))
    person, fork = states(on)
    assert person[3]["floor_resolution_m_per_px"] == pytest.approx(s_hand(-200, 200), abs=1e-9) and person[3]["floor_resolution_m_per_px_null_reason"] is None
    assert fork[3]["floor_resolution_m_per_px"] == pytest.approx(s_hand(80, 220), abs=1e-9)
    assert [(r["x_m"], r["y_m"]) for r in on.tables["object_state"]] == [(r["x_m"], r["y_m"]) for r in off.tables["object_state"]]
    assert [r["clearance_m"] for r in on.tables["pair_series"]] == [r["clearance_m"] for r in off.tables["pair_series"]]
    assert on.artifact_id != off.artifact_id  # the stored s is new payload


def test_t24_2_gated_positions_are_null_not_observable_and_clearance_is_geometry_failure():
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(), calibration=pinhole(3.0, cy=100.0))
    person, fork = states(on)
    for rows, s in ((person, s_hand(-200, 100)), (fork, s_hand(80, 120))):
        r = rows[4]
        assert r["floor_resolution_m_per_px"] == pytest.approx(s, abs=1e-9)
        assert r["x_m"] is None and r["y_m"] is None and r["x_m_null_reason"] == "not_observable" and r["y_m_null_reason"] == "not_observable"
    pairs = on.tables["pair_series"]
    assert pairs and all(p["clearance_m"] is None and p["clearance_state"] == "unmeasurable_geometry_failure" for p in pairs)
    off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=pinhole(3.0, cy=100.0))
    assert [p["q_state"] for p in pairs] == [p["q_state"] for p in off.tables["pair_series"]]  # T24.2 (e): Q unchanged


def test_t24_2_no_intersection_with_the_gate_on():
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(), calibration=pinhole(3.0, cy=200.0))
    person, fork = states(on)
    r = person[2]
    assert r["floor_resolution_m_per_px"] is None and r["floor_resolution_m_per_px_null_reason"] == "not_observable"
    assert r["x_m"] is None and r["x_m_null_reason"] == "not_observable"
    assert fork[2]["floor_resolution_m_per_px"] == pytest.approx(s_hand(80, 20), abs=1e-9)
    assert {p["clearance_state"] for p in on.tables["pair_series"]} == {"unmeasurable_geometry_failure"}


def test_t24_2_gate_applies_to_every_evidence_class_with_a_foot_pixel():
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10, person_states={4: "predicted"}), {}, cfg=gate_cfg(), calibration=pinhole(3.0, cy=100.0))
    person, _ = states(on)
    assert person[4]["evidence_class"] == "inferred" and person[4]["x_m"] is None and person[4]["floor_resolution_m_per_px"] == pytest.approx(s_hand(-200, 100), abs=1e-9)


def test_t24_2_lost_points_are_outside_the_gate_cr_034():
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10, person_states={5: "lost"}), {}, cfg=gate_cfg(), calibration=pinhole(3.0, cy=0.0))
    off, _ = build_s4(s1, tracks(10, person_states={5: "lost"}), {}, cfg=config(), calibration=pinhole(3.0, cy=0.0))
    person, _ = states(on)
    assert person[5]["floor_resolution_m_per_px"] is None and person[5]["floor_resolution_m_per_px_null_reason"] == "not_applicable"
    assert by(on)[5]["clearance_state"] == by(off)[5]["clearance_state"] == "unmeasurable_occluded"


def test_t24_2_simulator_positions_are_outside_the_gate():
    from test_part_b import n2_positions
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10), n2_positions("N2-G2", 10), cfg=gate_cfg())
    off, _ = build_s4(s1, tracks(10), n2_positions("N2-G2", 10), cfg=config())
    assert all(r["floor_resolution_m_per_px"] is None and r["floor_resolution_m_per_px_null_reason"] == "not_applicable" for r in on.tables["object_state"])
    assert [r["clearance_m"] for r in on.tables["pair_series"]] == [r["clearance_m"] for r in off.tables["pair_series"]]


def by(built):
    return {r["frame_index"]: r for r in built.tables["pair_series"]}


# ------------------------------------------------------------------------------------------------- builder (T24.1 d, T24.3)

def anchored(d=D, r=R_T):
    return dict(FORK, anchor="box_bottom_centre", anchor_offset_m=d, anchor_taper_m=r)


def test_t24_1_builder_shifts_the_forklift_away_from_the_camera():
    s1 = synthetic_s1.build(10)
    cal = pinhole(3.0, cy=0.0)
    on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(s_max=None, fork=anchored()), calibration=cal)
    off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=cal)
    _, fork_on = states(on)
    _, fork_off = states(off)
    pf = (fork_off[3]["x_m"], fork_off[3]["y_m"])
    assert (fork_on[3]["x_m"], fork_on[3]["y_m"]) == pytest.approx(geometry.anchor_centre(pf, (0.0, 0.0), D, R_T), abs=1e-12)
    assert math.hypot(fork_on[3]["x_m"] - pf[0], fork_on[3]["y_m"] - pf[1]) == pytest.approx(D, abs=1e-12)  # r > r_taper
    assert fork_on[3]["pos_cov_m2"] == fork_off[3]["pos_cov_m2"]  # T24.1 (d)
    person_on, _ = states(on)
    person_off, _ = states(off)
    assert [(r["x_m"], r["y_m"]) for r in person_on.values()] == [(r["x_m"], r["y_m"]) for r in person_off.values()]  # person prior unchanged
    assert [p["clearance_m"] for p in on.tables["pair_series"]] != [p["clearance_m"] for p in off.tables["pair_series"]]


def test_t24_1_centre_anchor_and_homography_keep_the_floor_point():
    s1 = synthetic_s1.build(10)
    cal = pinhole(3.0, cy=0.0)
    off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=cal)
    centre = dict(FORK, anchor_offset_m=D, anchor_taper_m=R_T)  # anchor = centre: E-1.2.24 behaviour
    c_on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(s_max=None, fork=centre), calibration=cal)
    assert [(r["x_m"], r["y_m"]) for r in c_on.tables["object_state"]] == [(r["x_m"], r["y_m"]) for r in off.tables["object_state"]]
    hom = {"cal_id": "cal_" + "b" * 26, "world_frame_id": "wfr_" + "b" * 26, "calibration_tier": "ground_plane_homography", "quality_state": "unvalidated",
           "homography_img_to_floor": [0.01, 0, 0, 0, 0.01, 0, 0, 0, 1.0]}
    h_off, _ = build_s4(s1, tracks(10), {}, cfg=config(), calibration=hom)
    h_on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(s_max=None, fork=anchored()), calibration=hom)
    assert [(r["x_m"], r["y_m"]) for r in h_on.tables["object_state"]] == [(r["x_m"], r["y_m"]) for r in h_off.tables["object_state"]]


def test_t24_3_gate_before_shift():
    # cy = 100: the forklift foot is gated (s = 0.208), so no centre is formed even though T24.1 is on.
    s1 = synthetic_s1.build(10)
    on, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(fork=anchored()), calibration=pinhole(3.0, cy=100.0))
    _, fork = states(on)
    assert fork[3]["x_m"] is None and fork[3]["floor_resolution_m_per_px"] == pytest.approx(s_hand(80, 120), abs=1e-9)
    on2, _ = build_s4(s1, tracks(10), {}, cfg=gate_cfg(fork=anchored()), calibration=pinhole(3.0, cy=0.0))
    _, fork2 = states(on2)
    # kept: s is that of the foot pixel, not of the shifted centre
    assert fork2[3]["floor_resolution_m_per_px"] == pytest.approx(s_hand(80, 220), abs=1e-9)
