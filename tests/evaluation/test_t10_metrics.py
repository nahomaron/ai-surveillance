"""CT-T10-09: Appendix T T10.7 event-metric details (contract E-1.2.8). Expected values are hand calculations written here."""
import pytest

from rq1.evaluation import event_metrics as em
from rq1.evaluation import matching as mt

# Two windows. W1 (w = 2): 4 assessable references (2 matched, 1 miss, 1 abstained_miss); 2 matched system events,
# 1 duplicate, 1 false alert. W2 (w = 1): 3 assessable references (1 matched, 2 abstained_miss); no alerts.
W1 = em.WindowCounts(a=4, m=2, s=4, m_s=2, f=2, c=3, abstained_miss=1, duplicate=1, u=1.0)
W2 = em.WindowCounts(a=3, m=1, s=1, m_s=1, f=0, c=1, abstained_miss=2, duplicate=0, u=1.0)


def test_ct_t10_09_ev_m5_m4_m11_weighted_and_unweighted():
    weighted, plain = em.headline([W1, W2], [2.0, 1.0]), em.headline([W1, W2])
    assert weighted["EV-M5"] == pytest.approx(4 / 11)  # (2x1 + 1x2) / (2x4 + 1x3)
    assert plain["EV-M5"] == pytest.approx(3 / 7)  # (1 + 2) / (4 + 3)
    assert weighted["EV-M4"] == pytest.approx(7 / 11) == pytest.approx(1 - weighted["EV-M5"])  # (2x3 + 1) / 11; T10.7(b)
    assert plain["EV-M4"] == pytest.approx(4 / 7) == pytest.approx(1 - plain["EV-M5"])
    assert weighted["EV-M11"] == pytest.approx(2 / 7)  # (2x1 + 0) / (2x(2+1) + 1x(1+0))
    assert plain["EV-M11"] == pytest.approx(1 / 4)  # 1 / (3 + 1)


def test_ct_t10_09_ev_m3_weighted_and_unweighted():
    # W1: 3 episodes, one abstained ({H, IE}, 1.0 s); POW support 10 s. W2: 2 episodes, both abstained ({PC, IE} 0.5 s each); POW 5 s.
    # {H, UD, IE} is not abstained (it carries UD).
    w1 = ([(frozenset({"H", "IE"}), 1.0), (frozenset({"H"}), 2.0), (frozenset({"H", "UD", "IE"}), 0.5)], 10.0)
    w2 = ([(frozenset({"PC", "IE"}), 0.5), (frozenset({"PC", "IE"}), 0.5)], 5.0)
    weighted, plain = em.abstention_rate([w1, w2], [2.0, 1.0]), em.abstention_rate([w1, w2])
    assert weighted["episodes"] == pytest.approx(0.5)  # (2x1 + 1x2) / (2x3 + 1x2) = 4/8
    assert plain["episodes"] == pytest.approx(3 / 5)  # (1 + 2) / (3 + 2)
    assert weighted["support"] == pytest.approx(3 / 25)  # (2x1.0 + 1x1.0) / (2x10 + 1x5)
    assert plain["support"] == pytest.approx(2 / 15)  # (1.0 + 1.0) / 15


def test_ct_t10_09_p90_and_median():
    # 5 values 0.1..0.5: P90 at h = 4 x 0.9 = 3.6 -> 0.4 + 0.6 x 0.1 = 0.46; median 0.3.
    # 4 values 0.0..0.3: P90 at h = 3 x 0.9 = 2.7 -> 0.2 + 0.7 x 0.1 = 0.27; median 0.15.
    assert em.percentile([0.5, 0.1, 0.4, 0.2, 0.3], 90) == pytest.approx(0.46) and em.percentile([0.1, 0.2, 0.3, 0.4, 0.5], 50) == pytest.approx(0.3)
    assert em.percentile([0.0, 0.1, 0.2, 0.3], 90) == pytest.approx(0.27) and em.percentile([0.0, 0.1, 0.2, 0.3], 50) == pytest.approx(0.15)
    records = [{"match_type": "matched", "onset_error_s": e, "offset_error_s": e, "temporal_iou": 1.0} for e in (0.1, -0.2, 0.3, 0.4, -0.5)]
    got = em.localization(records)
    assert (got["n"], got["onset_p90_s"], got["onset_median_s"]) == (5, pytest.approx(0.46), pytest.approx(0.3))
    assert em.localization([]) == {"n": 0, "onset_median_s": None, "onset_p90_s": None, "offset_median_s": None, "offset_p90_s": None, "mean_iou": None}


def test_ct_t10_09_abstained_only_in_g2():
    event = mt.SystemEvent(["pow_x", 0], "s0", 0.0, 1.0, ("p1", "f1"), frozenset({"H", "IE"}))
    assert mt.is_abstained(event.labels) and not mt.abstained(event, "G1") and not mt.abstained(event, "any") and mt.abstained(event, "G2")
    ref = mt.Reference("r1", 0.0, 1.0, ("p1", "f1"))
    groups = {"r1": frozenset({"G1", "G2"})}
    assert [r["match_type"] for r in mt.match_window([ref], [event], "G1", 0.3, "rule_conformance", groups)] == ["matched"]
    assert [r["match_type"] for r in mt.match_window([ref], [event], "any", 0.3, "rule_conformance", groups)] == ["matched"]
    assert [r["match_type"] for r in mt.match_window([ref], [event], "G2", 0.3, "rule_conformance", groups)] == ["abstained_miss"]
    assert not mt.is_abstained(frozenset({"H", "UD", "IE"})) and not mt.is_abstained(frozenset({"H"}))
