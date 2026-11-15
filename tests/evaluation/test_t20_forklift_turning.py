"""Appendix T T20.2 (E-1.2.18): the report-time stratum forklift_turning.

Hand set-up: 30 frames per second, t_i = i / 30 s, frames 0..59, all eligible, one coverage segment (no break), the forklift
tracked (detected) with a position on every frame. w_turn = 0.5 s, e_fturn = 5 deg/s = 0.0872664626 rad/s.
At frame 30 (t = 1.0 s) the window is [0.75, 1.25] s; frames lie at multiples of 1/30 s, so it holds frames 23..37
(22.5 and 37.5 are not frames): a = 23, b = 37, t_b - t_a = 14/30 s = 0.4667 s >= w_turn / 2 = 0.25 s.
- constant yaw: rate 0 -> false.
- yaw = 75 deg/s * t: rate = 75 deg/s * (14/30) / (14/30) = 75 deg/s = 1.3089969390 rad/s > e_fturn -> true.
- yaw jumps by pi (half-turn) between frames 29 and 30: fold(pi) = 0, rate 0 -> false.
- yaw null on every frame -> unknown.
"""
import math

import pytest

from rq1.evaluation import strata
from rq1.schema.errors import ContractError

FPS, N = 30, 60
W_TURN, E_FTURN = 0.5, math.radians(5.0)
FRAMES = {i: {"frame_index": i, "t_resolved_s": i / FPS, "eligible": True, "support_start_tl_s": i / FPS, "support_s": 1 / FPS} for i in range(N)}
COVERAGE = [{"t_start_tl_s": 0.0, "t_end_tl_s": N / FPS, "coverage_state": "observed"}]


def fork(yaw, evidence="detected", positions=range(N)):
    return [{"frame_index": i, "x_m": 1.0 if i in positions else None, "y_m": 2.0, "yaw_rad": yaw(i), "evidence_class": evidence} for i in range(N)]


def at(rows, k=30, frames=FRAMES):
    return strata.forklift_turning(rows, frames, COVERAGE, W_TURN, E_FTURN)[k]


def test_constant_yaw_is_false():
    r = at(fork(lambda i: 0.4))
    assert r.state == strata.FALSE and r.yaw_rate_rad_s == pytest.approx(0.0, abs=1e-12)


def test_75_deg_per_s_is_true():
    r = at(fork(lambda i: math.radians(75.0) * i / FPS))
    assert r.state == strata.TRUE and r.yaw_rate_rad_s == pytest.approx(1.3089969390, abs=1e-9)


def test_a_half_turn_jump_is_false():
    r = at(fork(lambda i: 0.2 + (math.pi if i >= 30 else 0.0)))
    assert r.state == strata.FALSE and r.yaw_rate_rad_s == pytest.approx(0.0, abs=1e-12)


def test_null_yaw_is_unknown():
    r = at(fork(lambda i: None))
    assert r.state == strata.UNKNOWN and r.yaw_rate_rad_s is None


def test_window_too_short_is_unknown():
    """Positions only on frames 30..35: the run is 5/30 s = 0.1667 s long, shorter than w_turn, so the whole run is the
    window, and t_b - t_a = 0.1667 s < w_turn / 2 = 0.25 s -> unknown. A frame outside every run (frame 10) -> unknown."""
    rows = fork(lambda i: 0.0, positions=range(30, 36))
    out = strata.forklift_turning(rows, FRAMES, COVERAGE, W_TURN, E_FTURN)
    assert out[30].state == strata.UNKNOWN and out[10].state == strata.UNKNOWN


def test_window_is_shifted_at_the_track_end():
    """T9.1 shift: at frame 59 (t = 1.9667 s) the window is shifted to [1.4667, 1.9667] s = frames 44..59, t_b - t_a = 0.5 s.
    Yaw 75 deg/s -> rate 75 deg/s."""
    r = at(fork(lambda i: math.radians(75.0) * i / FPS), k=59)
    assert r.state == strata.TRUE and r.yaw_rate_rad_s == pytest.approx(math.radians(75.0), abs=1e-9)


def test_threshold_is_strict():
    """rate = e_fturn exactly -> false (true only when rate > e_fturn)."""
    rows = fork(lambda i: E_FTURN * i / FPS)
    out = strata.forklift_turning(rows, FRAMES, COVERAGE, W_TURN, E_FTURN)
    assert out[30].yaw_rate_rad_s == pytest.approx(E_FTURN, abs=1e-12)
    assert strata.forklift_turning(rows, FRAMES, COVERAGE, W_TURN, E_FTURN + 1e-12)[30].state == strata.FALSE


def test_fold_range():
    assert strata.fold(math.pi) == pytest.approx(0.0, abs=1e-12)
    assert strata.fold(math.pi / 2) == pytest.approx(math.pi / 2)
    assert strata.fold(-math.pi / 2) == pytest.approx(math.pi / 2)  # (-pi/2, pi/2]
    assert strata.fold(math.radians(100.0)) == pytest.approx(math.radians(-80.0))


def test_reportable_paths_d_8():
    assert strata.turning_reportable("oracle", False)
    assert strata.turning_reportable("detector", True) and not strata.turning_reportable("detector", False)
    with pytest.raises(ContractError):
        strata.turning_reportable("other", True)


def test_parameters_are_checked():
    with pytest.raises(ContractError) as e:
        strata.forklift_turning(fork(lambda i: 0.0), FRAMES, COVERAGE, 0.0, E_FTURN)
    assert e.value.code == "ERR-SPEC"
