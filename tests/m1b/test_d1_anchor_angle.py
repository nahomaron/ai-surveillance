"""D-53 step 1: hand-computed values for theta folding, h(theta), binning and the residual."""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d1_anchor_angle as d1  # noqa: E402


def test_h_theta_hand_values():
    # theta = 0: L/2 = 3.03 / 2 = 1.515; theta = 90: W/2 = 1.13 / 2 = 0.565
    assert d1.h_theta(0) == pytest.approx(1.515, abs=1e-12)
    assert d1.h_theta(90) == pytest.approx(0.565, abs=1e-12)
    # theta = 45: (1.515 + 0.565) * sqrt(2)/2 = 2.08 * 0.70710678 = 1.47078210
    assert d1.h_theta(45) == pytest.approx(1.4707821, abs=1e-7)


def test_theta_folding():
    los = (1.0, 0.0)
    assert d1.fold_theta(0.0, los) == pytest.approx(0.0, abs=1e-9)
    assert d1.fold_theta(math.pi, los) == pytest.approx(0.0, abs=1e-6)  # half-turn: same axis
    assert d1.fold_theta(math.pi / 2, los) == pytest.approx(90.0)
    assert d1.fold_theta(-math.pi / 2, los) == pytest.approx(90.0)
    assert d1.fold_theta(math.radians(120), los) == pytest.approx(60.0)  # |cos 120| = 0.5 -> 60
    assert d1.fold_theta(math.radians(-30), (0.0, 1.0)) == pytest.approx(60.0)  # axis at -30 deg vs line of sight at 90 deg


def test_bins_edges():
    assert d1.bin_of(0) == "0-15"
    assert d1.bin_of(15) == "15-30"
    assert d1.bin_of(74.999) == "60-75"
    assert d1.bin_of(90) == "75-90"


def test_frame_row_sign_and_distance():
    # camera at origin, truth at (10, 0), estimate at (9, 0.5): along = -1 (toward camera), across 0.5, r = hypot(9, 0.5)
    r = d1.frame_row((9.0, 0.5), (10.0, 0.0), 0.0, (0.0, 0.0, 5.0))
    assert r["along"] == pytest.approx(-1.0)
    assert r["across"] == pytest.approx(0.5)
    assert r["r"] == pytest.approx(math.hypot(9.0, 0.5))
    assert r["theta"] == pytest.approx(0.0, abs=1e-9)
    assert r["h"] == pytest.approx(1.515)


def test_candidate_d_and_residual():
    rows = [{"along": a, "theta": 10.0, "h": 1.5, "r": 5.0} for a in (-1.0, -1.04, -0.9)]
    # median |along| = 1.0 -> d = 1.0; residuals |a + 1| = 0, 0.04, 0.1 -> median 0.04
    out = d1.summarize({"all": rows, "ceiling": rows, "eye_level": []}, 1, 0)
    assert out["candidate_d_m"] == 1.0
    assert out["residual_after_d"]["0-15"]["median_m"] == pytest.approx(0.04)
    assert d1.round_to(1.024) == 1.0 and d1.round_to(1.026) == 1.05
