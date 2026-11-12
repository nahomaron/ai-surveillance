"""T-13: Appendix N5 estimators and intervals. Expected values come from Appendix N5 (FX-W), published worked examples,
or hand calculations written beside each assertion."""
import json
import math
from pathlib import Path

import pytest

from rq1.evaluation import estimators as est

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"


def fx_w():
    d = json.loads((FIX / "FX-W.json").read_text())
    inputs = d["inputs"]
    weights = [inputs["strata"][w["stratum"]]["w"] for w in inputs["windows"]]
    return weights, inputs["windows"], d["expected"]


@pytest.mark.determinism
def test_fx_w_weighted_and_unweighted_recall_and_n_eff():
    weights, windows, expected = fx_w()
    m, a = [w["m"] for w in windows], [w["a"] for w in windows]
    assert est.ratio(weights, m, a) == pytest.approx(expected["weighted_recall"], abs=1e-9) == pytest.approx(0.71875, abs=1e-9)
    assert est.ratio([1.0] * 4, m, a) == pytest.approx(expected["unweighted_recall"], abs=1e-9) == pytest.approx(0.70, abs=1e-9)
    assert est.kish_n_eff(weights) == pytest.approx(expected["n_eff"], abs=1e-9) == pytest.approx(3.3793103448, abs=1e-9)
    assert est.ht_total(weights, a) == 5 * 3 + 5 * 1 + 2 * 2 + 2 * 4  # 32 assessable references in the frame


@pytest.mark.determinism
def test_target_a_bootstrap_is_seeded_and_brackets_the_estimate():
    weights, windows, _ = fx_w()
    sample = {"h1": [(3, 2), (1, 1)], "h2": [(2, 2), (4, 2)]}
    w = {"h1": 5.0, "h2": 2.0}
    first = est.stratified_bootstrap_ratio(sample, w, B=200, seed=7)
    assert first == est.stratified_bootstrap_ratio(sample, w, B=200, seed=7)  # identical for the same seed and B (N4 tolerances)
    assert first[0] <= 0.71875 <= first[1]


@pytest.mark.determinism
def test_target_b_cluster_bootstrap():
    # Two origins, groups g1-g3 (synthetic) and g4 (staged). Same seed: identical interval.
    windows = [("synthetic", "g1", 5.0, 3, 2), ("synthetic", "g1", 5.0, 1, 1), ("synthetic", "g2", 2.0, 2, 2), ("synthetic", "g3", 2.0, 4, 2),
               ("staged", "g4", 1.0, 2, 1)]
    a = est.cluster_bootstrap_ratio(windows, B=200, seed=11)
    assert a == est.cluster_bootstrap_ratio(list(reversed(windows)), B=200, seed=11)  # input order does not matter
    assert a[0] < a[1]
    # Degenerate: one group per origin, so every replicate equals the point estimate (2x3 + 1x1)/(2x4 + 1x2) = 0.7.
    one = [("synthetic", "g1", 2.0, 4, 3), ("staged", "g2", 1.0, 2, 1)]
    assert est.cluster_bootstrap_ratio(one, B=50, seed=1) == pytest.approx((0.7, 0.7), abs=1e-12)


@pytest.mark.determinism
def test_paired_bootstrap_difference():
    # Frame description (window resampling). Identical configurations give (0, 0); configuration b matching one more
    # reference in two windows makes a - b never positive.
    same = [("h1", "o", "g1", 5.0, 3, 2, 3, 2), ("h1", "o", "g1", 5.0, 1, 1, 1, 1), ("h2", "o", "g2", 2.0, 2, 2, 2, 2), ("h2", "o", "g2", 2.0, 4, 2, 4, 2)]
    assert est.paired_bootstrap_difference(same, "frame_description", B=100, seed=3) == (0.0, 0.0)
    better = [("h1", "o", "g1", 5.0, 3, 2, 3, 3), ("h1", "o", "g1", 5.0, 1, 1, 1, 1), ("h2", "o", "g2", 2.0, 2, 2, 2, 2), ("h2", "o", "g2", 2.0, 4, 2, 4, 3)]
    low, high = est.paired_bootstrap_difference(better, "frame_description", B=200, seed=3)
    assert high <= 0.0 and low < 0.0


def wilson_decimal(successes, n, z="1.959964"):
    """The N5 Wilson formula in decimal arithmetic at 15 significant digits, independent of the estimator code."""
    from decimal import Decimal, localcontext
    with localcontext() as ctx:
        ctx.prec = 15
        z, n = Decimal(z), Decimal(n)
        p = Decimal(successes) / n
        centre = p + z * z / (2 * n)
        half = z * (p * (1 - p) / n + z * z / (4 * n * n)).sqrt()
        den = 1 + z * z / n
        return (centre - half) / den, (centre + half) / den


def test_wilson():
    # 8/10 with z = 1.959964, decimal at 15 digits (recorded run):
    #   z^2 = 3.841458881296; centre = 0.8 + z^2/20 = 0.9920729440648
    #   inner = 0.8 x 0.2 / 10 + z^2/400 = 0.02560364720324; sqrt = 0.160011397104206; half = z x sqrt = 0.313616577913948
    #   denominator = 1 + z^2/10 = 1.3841458881296
    #   low = 0.6784563661508 / 1.3841458881296 = 0.490162469122133; high = 1.3056895219787 / 1.3841458881296 = 0.943317849062234
    # The first hand value of the upper bound (0.943315, T-13) was an arithmetic slip, corrected to 0.9433178 (Progress log).
    low_d, high_d = wilson_decimal(8, 10)
    assert (str(low_d), str(high_d)) == ("0.490162469122133", "0.943317849062234")
    low, high = est.wilson(8, 10)
    assert low == pytest.approx(float(low_d), abs=1e-12) and high == pytest.approx(float(high_d), abs=1e-12)
    assert est.wilson(0, 0) is None
    low0, high0 = wilson_decimal(0, 10)  # z^2 / (n + z^2) = 3.841458881296 / 13.841458881296 = 0.277532... at p = 0
    low, high = est.wilson(0, 10)
    assert low == pytest.approx(float(low0), abs=1e-12) == pytest.approx(0.0, abs=1e-12) and high == pytest.approx(float(high0), abs=1e-12)


def test_bland_altman():
    # d = 0.1, -0.1, 0.2, 0.0: bias 0.05; sum of squared deviations 0.05; SD = sqrt(0.05/3) = 0.1290994;
    # LoA = 0.05 -+ 1.96 x 0.1290994 = (-0.2030349, 0.3030349).
    got = est.bland_altman([1.1, 0.9, 1.2, 1.0], [1.0, 1.0, 1.0, 1.0])
    assert got["bias"] == pytest.approx(0.05, abs=1e-12) and got["sd"] == pytest.approx(math.sqrt(0.05 / 3), abs=1e-12)
    assert (got["loa_low"], got["loa_high"], got["n"]) == (pytest.approx(-0.2030349, abs=1e-7), pytest.approx(0.3030349, abs=1e-7), 4)
    assert est.bland_altman([1.0], [1.0]) is None


def test_icc_2_1_shrout_fleiss_example():
    # Shrout & Fleiss (1979), Table 2: 6 targets x 4 judges. Published BMS 11.24, JMS 32.49, EMS 1.02;
    # ICC(2,1) = (11.24 - 1.02) / (11.24 + 3 x 1.02 + 4 x (32.49 - 1.02) / 6) = 10.22 / 35.28 = 0.29.
    data = [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]]
    assert est.icc_2_1(data) == pytest.approx(0.2897, abs=5e-4)


def test_cohen_kappa():
    # 50 items: both yes 20, A yes/B no 5, A no/B yes 10, both no 15. p_o = 0.7; p_e = 0.5 x 0.6 + 0.5 x 0.4 = 0.5; kappa = 0.4.
    a = ["y"] * 20 + ["y"] * 5 + ["n"] * 10 + ["n"] * 15
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    assert est.cohen_kappa(a, b) == pytest.approx(0.4, abs=1e-12)
    assert est.cohen_kappa(["y", "y"], ["y", "y"]) is None  # p_e = 1


def test_krippendorff_alpha_nominal():
    # Units (a,a,a), (a,a,b), (b,b,b): coincidences o_aa = 3 + 1 = 4, o_ab = o_ba = 1, o_bb = 3; n_a = 5, n_b = 4, n = 9.
    # alpha = 1 - (n - 1) x 2 / (2 x 5 x 4) = 1 - 16/40 = 0.6. A unit with one value is not pairable and changes nothing.
    units = [["a", "a", "a"], ["a", "a", "b"], ["b", "b", "b"]]
    assert est.krippendorff_alpha_nominal(units) == pytest.approx(0.6, abs=1e-12)
    assert est.krippendorff_alpha_nominal(units + [["a"]]) == pytest.approx(0.6, abs=1e-12)
    assert est.krippendorff_alpha_nominal([["a", "a"], ["a", "a"]]) is None  # no expected disagreement
