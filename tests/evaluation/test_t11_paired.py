"""CT-T11-03: Appendix T T11.2 (contract E-1.2.9). The paired bootstrap follows the estimand of the compared metric.
Expected values are hand calculations written here."""
import pytest

from rq1.evaluation import estimators as est

# One stratum, one data origin, two leakage groups of three windows each, x = 2 for both configurations.
# Group g1: configuration a matches 2, b matches 0 per window; group g2: the reverse. So R_a - R_b = 0 on the full sample.
G1 = [("h", "synthetic", "g1", 1.0, 2, 2, 2, 0)] * 3
G2 = [("h", "synthetic", "g2", 1.0, 2, 0, 2, 2)] * 3
WINDOWS = G1 + G2


@pytest.mark.determinism
def test_ct_t11_03_new_session_metric_uses_cluster_resampling():
    # Cluster draws pick two groups: {g1, g1} gives 1 - 0 = 1, {g2, g2} gives -1, a mixed draw gives 0, with probabilities
    # 1/4, 1/4, 1/2. With B = 2000, about 500 replicates sit at each extreme, so the 2.5 % and 97.5 % percentiles are -1 and 1.
    assert est.paired_bootstrap_difference(WINDOWS, "new_session_performance", B=2000, seed=5) == pytest.approx((-1.0, 1.0), abs=1e-12)


@pytest.mark.determinism
def test_ct_t11_03_frame_description_metric_uses_window_resampling():
    # Window draws pick 6 windows; with k of them from g1, R_a - R_b = (2k - 2(6 - k)) / 12 = (k - 3) / 3, k ~ Binomial(6, 1/2).
    # P(k = 0) = 1/64 = 1.6 % < 2.5 % <= P(k <= 1) = 7/64, so the 2.5 % percentile is (1 - 3)/3 = -2/3 and, by symmetry,
    # the 97.5 % percentile is 2/3: narrower than the cluster interval (-1, 1).
    window = est.paired_bootstrap_difference(WINDOWS, "frame_description", B=2000, seed=5)
    cluster = est.paired_bootstrap_difference(WINDOWS, "new_session_performance", B=2000, seed=5)
    assert window == pytest.approx((-2 / 3, 2 / 3), abs=1e-12)
    assert window[1] - window[0] < cluster[1] - cluster[0]


def test_ct_t11_03_conditional_metric_gets_no_paired_interval():
    assert est.paired_bootstrap_difference(WINDOWS, "conditional_on_selection", B=100, seed=5) is None
