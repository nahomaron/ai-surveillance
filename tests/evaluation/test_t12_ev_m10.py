"""CT-T12-02: Appendix T T12.2 (contract E-1.2.10) EV-M10 and the sensitivity values. Expected values are the T12.2 check."""
import pytest

from rq1.evaluation import event_metrics as em
from rq1.evaluation import matching as mt

PAIR = ("p1", "f1")


def check_window():
    # T12.2 check (w = 1): s1 matched to the assessable reference r1; s2 overlaps the unobservable reference r2; s3 lies
    # elsewhere with no reference; s4 is abstained (IE, no NM/UD/CT) and overlaps r2. Label group G2.
    refs = [mt.Reference("r1", 0.0, 1.0, PAIR), mt.Reference("r2", 5.0, 6.0, PAIR, assessable=False)]
    events = [mt.SystemEvent(["pow", 1], "s1", 0.0, 1.0, PAIR, frozenset({"H", "UD"})),
              mt.SystemEvent(["pow", 2], "s2", 5.0, 6.0, ("p9", "f9"), frozenset({"H", "UD"})),  # no pair condition
              mt.SystemEvent(["pow", 3], "s3", 10.0, 11.0, PAIR, frozenset({"H", "UD"})),
              mt.SystemEvent(["pow", 4], "s4", 5.2, 5.8, PAIR, frozenset({"H", "IE"}))]
    groups = {"r1": frozenset({"G1", "G2"}), "r2": frozenset({"G1", "G2"})}
    records = mt.match_window(refs, events, "G2", 0.3, "rule_conformance", groups)
    return refs, events, records, groups


@pytest.mark.determinism
def test_ct_t12_02_check_values():
    refs, events, records, groups = check_window()
    # N4 literal: s2 and s3 are false alerts; r2 is unobservable_reference; s4 makes no record.
    assert sorted((r["match_type"], r["ref_event_id"], r["system_event_id"]) for r in records) == [
        ("false_alert", None, "s2"), ("false_alert", None, "s3"), ("matched", "r1", "s1"), ("unobservable_reference", "r2", None)]
    counts = em.window_counts(records, 3600.0)
    assert em.headline([counts])["EV-M2"] == pytest.approx(1 / 3)  # headline unchanged: 1 matched / 3 non-abstained
    overlaps = mt.unobservable_overlap(refs, events, records, "G2", groups)
    sens = em.sensitivity_excluding_unobservable_overlap([counts], [overlaps])
    assert sens["label"] == "sensitivity_excluding_unobservable_overlap"
    assert sens["EV-M2"] == pytest.approx(1 / 2)  # s2 removed from s: 1 / 2
    assert sens["EV-M7"] == pytest.approx(1.0)  # f = 2 - 1 = 1 alert per usable hour (headline 2.0)
    table = em.ev_m10([overlaps])
    assert (table["weighted"]["non_abstained"], table["weighted"]["abstained"]) == (1.0, 1.0)  # T12.2 check
    assert table["weighted"]["by_label"] == {"non_abstained:H": 1.0, "non_abstained:UD": 1.0, "abstained:H": 1.0, "abstained:IE": 1.0}
    assert table["note"] == "These events are neither confirmed nor refuted by the reference."


@pytest.mark.determinism
def test_ev_m10_weighting_and_no_abstention_outside_g2():
    refs, events, records, groups = check_window()
    overlaps = mt.unobservable_overlap(refs, events, records, "G2", groups)
    table = em.ev_m10([overlaps, overlaps], [2.0, 1.0])
    assert (table["weighted"]["non_abstained"], table["unweighted"]["non_abstained"]) == (3.0, 2.0)
    g1 = mt.match_window(refs, events, "G1", 0.3, "rule_conformance", groups)
    # In G1 nothing abstains (T10.7(a)): s4 decides, overlaps r2 and matches nothing, so it is non_abstained there.
    got = {e["system_event_id"]: e["decision"] for e in mt.unobservable_overlap(refs, events, g1, "G1", groups)}
    assert got == {"s2": "non_abstained", "s4": "non_abstained"}
