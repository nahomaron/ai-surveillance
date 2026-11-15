"""Geometry validation GV-01, GV-03 to GV-08 (F.1 Appendix N7) and the MR-08 helpers. Expected values are hand calculations
written beside each assertion. Percentiles use numpy's "linear" method, as EV-M8 does (T10.7)."""
import math

import pytest

from rq1.evaluation import gv


@pytest.mark.determinism
def test_gv01_bias_rmse_p95():
    # errors (dx, dy): (3, 4) |e| = 5; (0, 0) 0; (-3, 0) 3; (0, -4) 4. Bias = (0/4, 0/4) = (0, 0).
    # RMSE = sqrt((25 + 0 + 9 + 16) / 4) = sqrt(12.5) = 3.5355339; P95 of [0, 3, 4, 5]: rank 0.95 * 3 = 2.85 -> 4 + 0.85 = 4.85.
    out = gv.gv01([(3.0, 4.0), (0.0, 0.0), (-3.0, 0.0), (0.0, -4.0)])
    assert out["n"] == 4 and out["bias_x_m"] == 0.0 and out["bias_y_m"] == 0.0
    assert out["rmse_m"] == pytest.approx(math.sqrt(12.5)) and out["p95_m"] == pytest.approx(4.85)
    assert gv.gv01([])["rmse_m"] is None


@pytest.mark.determinism
def test_gv05_coverage_and_inflation():
    # Sigma = identity, e = (1, 0), (2, 0), (0, 3): d2 = 1, 4, 9. Coverage at 2.2789: 1/3; at 6.1801: 2/3.
    # median(d2) = 4 -> inflation sqrt(4 / 1.3863) = 1.6986..., applied (> 1).
    out = gv.gv05([(1.0, 0.0), (2.0, 0.0), (0.0, 3.0)], [[1.0, 0.0, 1.0]] * 3)
    assert out["coverage_68"] == pytest.approx(1 / 3) and out["coverage_95"] == pytest.approx(2 / 3)
    assert out["inflation"] == pytest.approx(math.sqrt(4 / 1.3863)) and out["inflation_applied"] is True
    # A null covariance cannot be scored: such units are left out and counted.
    out = gv.gv05([(1.0, 0.0), (2.0, 0.0)], [None, None])
    assert out["n"] == 0 and out["n_without_covariance"] == 2 and out["coverage_68"] is None


@pytest.mark.determinism
def test_gv05_correlated_covariance():
    # Sigma = [[2, 1], [1, 2]] (sxx, sxy, syy), inverse = [[2, -1], [-1, 2]] / 3; e = (1, 1): d2 = (2 - 1 - 1 + 2) / 3 = 2/3.
    assert gv.gv05([(1.0, 1.0)], [[2.0, 1.0, 2.0]])["d2"] == [pytest.approx(2 / 3)]


@pytest.mark.determinism
def test_gv06_spearman_and_disagreement():
    # Ranks of x (1, 2, 3, 4) and y (10, 30, 20, 40): d = (0, -1, 1, 0), rho = 1 - 6 * 2 / (4 * 15) = 0.8.
    assert gv.spearman([1.0, 2.0, 3.0, 4.0], [10.0, 30.0, 20.0, 40.0]) == pytest.approx(0.8)
    # P pairs (R1, R2): known on both in 4 of 5 (2 = unknown); they differ on 1 -> 0.25.
    out = gv.p_disagreement([(1, 1), (0, 1), (1, 2), (0, 0), (1, 1)])
    assert (out["n"], out["disagree"], out["rate"]) == (4, 1, 0.25)


@pytest.mark.determinism
def test_signed_error_summary_for_gv04_gv07_gv08():
    # Differences (-1, 0, 1, 2): bias 0.5; RMSE sqrt((1 + 0 + 1 + 4) / 4) = sqrt(1.5); SD (sample) sqrt(5/3);
    # P5 rank 0.15 -> -1 + 0.15 = -0.85; P95 rank 2.85 -> 1 + 0.85 = 1.85.
    out = gv.signed_summary([-1.0, 0.0, 1.0, 2.0])
    assert out["n"] == 4 and out["bias"] == 0.5 and out["rmse"] == pytest.approx(math.sqrt(1.5))
    assert out["sd"] == pytest.approx(math.sqrt(5 / 3)) and out["p5"] == pytest.approx(-0.85) and out["p95"] == pytest.approx(1.85)


@pytest.mark.determinism
def test_gv08_realized_minimum_over_the_horizon():
    # POW frames at t = 0, 0.5, 1.0, 1.5, 2.5 s with clearances 3, 2, null, 1, 0.5; tau = 2 s; the series ends at 2.5 s.
    # From t = 0: [0, 2] is inside the series -> clearances 3, 2, 1 -> min 1. From t = 0.5: [0.5, 2.5] -> 2, 1, 0.5 -> 0.5.
    # From t = 1.0: [1, 3] runs past the series end (2.5 s), so the realized minimum is not observed -> None (AR-59 item 7).
    series = [(0.0, 3.0), (0.5, 2.0), (1.0, None), (1.5, 1.0), (2.5, 0.5)]
    assert gv.realized_min(series, 0, 2.0) == 1.0
    assert gv.realized_min(series, 1, 2.0) == 0.5
    assert gv.realized_min(series, 2, 2.0) is None
    assert gv.realized_min([(0.0, None), (2.0, None)], 0, 2.0) is None  # no measured clearance in the window


@pytest.mark.determinism
def test_mr08_label_stability_and_elasticity():
    # Base episodes A [0, 10) {H}, B [20, 30) {O}. Grid point 1: A' [1, 10) {H} (IoU 0.9 >= 0.3, same labels), B' [20, 30) {H}.
    # Grid point 2: A'' [0, 2) {H} (IoU 0.2 < 0.3 -> unmatched -> not stable), no B. A: 1 of 2 stable -> 0.5; B: 0 of 2 -> 0.
    base = [("pair", 0.0, 10.0, frozenset({"H"})), ("pair", 20.0, 30.0, frozenset({"O"}))]
    grid = [[("pair", 1.0, 10.0, frozenset({"H"})), ("pair", 20.0, 30.0, frozenset({"H"}))], [("pair", 0.0, 2.0, frozenset({"H"}))]]
    assert gv.label_stability(base, grid, 0.3) == [0.5, 0.0]
    # Another pair never matches: same interval, other pair -> not stable.
    assert gv.label_stability([("p", 0.0, 1.0, frozenset())], [[("q", 0.0, 1.0, frozenset())]], 0.3) == [0.0]
    # Elasticity (dY / Y) / (dtheta / theta): Y 10 -> 12 when theta 2 -> 3: (0.2) / (0.5) = 0.4. Y = 0: null.
    assert gv.elasticity(10.0, 12.0, 2.0, 3.0) == pytest.approx(0.4)
    assert gv.elasticity(0.0, 3.0, 2.0, 3.0) is None
