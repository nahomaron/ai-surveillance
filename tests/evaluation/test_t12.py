"""T-12: physical-identity association (F.1 A5.2, FX-ID-1-8, CT-ID-A1/A2), matching (Appendix N4, FX-TIE, CT-E-20/21),
match classes and EV-M metrics. Expected values come from the fixtures (F.1) or hand calculations written here."""
import json
import random
from pathlib import Path

import pytest

from rq1.evaluation import association as assoc
from rq1.evaluation import event_metrics as em
from rq1.evaluation import matching as mt
from rq1.schema.canonical import canonical_json

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
SUPPORT = {i: 0.1 for i in range(50)}  # 10 fps


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


def frames_of(fixture, shuffle=None):
    inputs = fixture["inputs"]
    out = {}
    for i in range(inputs["n_frames"]):
        system, reference = [], []
        for seg in inputs["segments"]:
            if seg["start"] <= i < seg["end_excl"]:
                box = assoc.Box(seg["object"], seg["class"], tuple(seg["box"]))
                (system if seg["side"] == "system" else reference).append(box)
        if shuffle:
            shuffle.shuffle(system)
            shuffle.shuffle(reference)
        out[i] = (system, reference)
    if shuffle:
        keys = list(out)
        shuffle.shuffle(keys)
        out = {k: out[k] for k in keys}
    return out


def run(name, shuffle=None):
    fixture = fx(name)
    rows = assoc.associate(frames_of(fixture, shuffle), fixture["inputs"]["iou_cm"], fixture["inputs"]["eps_amb"])
    summaries, missed = assoc.summarize(rows, SUPPORT)
    return fixture["expected"], rows, {s["track_id"]: s for s in summaries}, missed


def frames_with(rows, **match):
    return sorted(r["frame_index"] for r in rows if all(r[k] == v for k, v in match.items()))


# --- CT-ID-A1: FX-ID-1 to FX-ID-8 ------------------------------------------------------------------------------------

@pytest.mark.determinism
def test_fx_id_1_one_to_one():
    expected, rows, tracks, missed = run("FX-ID-1")
    a = tracks["A"]
    assert (a["status"], a["dominant_share"], len(frames_with(rows, track_id="A", status="matched"))) == (
        expected["tracks"]["A"]["status"], expected["tracks"]["A"]["dominant_share"], expected["tracks"]["A"]["matched_frames"])
    assert missed == []


@pytest.mark.determinism
def test_fx_id_2_identity_switch():
    expected, rows, tracks, _ = run("FX-ID-2")
    a, want = tracks["A"], expected["tracks"]["A"]
    assert (a["n_identities"], a["n_switches"], a["status"], a["dominant_identity_id"]) == (want["n_identities"], want["n_switches"], want["status"], want["dominant_identity"])
    assert a["dominant_share"] == pytest.approx(want["dominant_share"], abs=1e-12)  # tie 2.5 s each -> lower ID p1


@pytest.mark.determinism
def test_fx_id_3_fragments_and_missed_frames():
    expected, rows, tracks, _ = run("FX-ID-3")
    assert {t: s["status"] for t, s in tracks.items()} == {k: v["status"] for k, v in expected["tracks"].items()}
    lo, hi = expected["missed_reference_frames"]["p1"]
    assert frames_with(rows, physical_identity_id="p1", status="missed_reference") == list(range(lo, hi))
    # CM-01 itself is T-14; its numerator, the matched support of p1, is 45 frames x 0.1 s = 4.5 s (F.1: CM-01 = 4.5/5.0).
    assert assoc.matched_support(rows, SUPPORT)["p1"] == pytest.approx(4.5, abs=1e-9)


@pytest.mark.determinism
def test_fx_id_4_never_detected():
    expected, rows, tracks, missed = run("FX-ID-4")
    lo, hi = expected["missed_reference_frames"]["p2"]
    assert frames_with(rows, physical_identity_id="p2", status="missed_reference") == list(range(lo, hi))
    assert missed == ["p2"] and assoc.matched_support(rows, SUPPORT).get("p2", 0.0) == expected["CM-01"]["p2"] * 5.0


@pytest.mark.determinism
def test_fx_id_5_unmatched_system():
    expected, rows, tracks, _ = run("FX-ID-5")
    assert tracks["A"]["status"] == expected["tracks"]["A"]["status"]
    assert tracks["A"]["dominant_identity_id"] is None and len(frames_with(rows, track_id="A", status="unmatched_system")) == 50


@pytest.mark.determinism
def test_fx_id_6_ambiguous_frames_excluded():
    expected, rows, tracks, _ = run("FX-ID-6")
    lo, hi = expected["ambiguous_frames"]
    assert sorted({r["frame_index"] for r in rows if r["status"] == "ambiguous"}) == list(range(lo, hi))
    assert len(frames_with(rows, track_id="A", status="matched")) == expected["matched_frames"]["A"]
    assert len(frames_with(rows, track_id="A", status="unmatched_system")) == expected["unmatched_frames"]["A"]
    assert frames_with(rows, physical_identity_id="p2", status="missed_reference") == []  # the rival is ambiguous, not missed (AR-39 item 1)


@pytest.mark.determinism
def test_fx_id_7_pair_via_dominant_identity():
    expected, rows, tracks, _ = run("FX-ID-7")
    event = fx("FX-ID-7")["inputs"]["event"]
    pair, via = assoc.event_pair(rows, list(tracks.values()), event["person_track"], event["forklift_track"], event["closest_approach_frame"])
    assert list(pair) == expected["event_pair"] and via == expected["resolved_via"]


@pytest.mark.determinism
def test_fx_id_8_unknown_pair_is_a_false_alert():
    expected, rows, tracks, _ = run("FX-ID-8")
    event = fx("FX-ID-8")["inputs"]["event"]
    pair, _ = assoc.event_pair(rows, list(tracks.values()), event["person_track"], event["forklift_track"], event["closest_approach_frame"])
    assert pair is expected["event_pair"] is None
    ref = mt.Reference("r1", 1.0, 1.5, ("p1", "f1"))
    records = mw([ref], [mt.SystemEvent(["pow", 10], "s1", 1.0, 1.5, pair, frozenset({"H"}))], "G1", 0.3, "rule_conformance")
    assert {r["system_event_id"]: r["match_type"] for r in records if r["system_event_id"]} == {"s1": expected["match_type"]}
    # primary_stage = perception is error attribution (Appendix N9), implemented in T-14.


@pytest.mark.determinism
@pytest.mark.parametrize("name", [f"FX-ID-{i}" for i in range(1, 9)])
@pytest.mark.parametrize("seed", range(5))
def test_ct_id_a2_permutation_invariance(name, seed):
    _, rows, tracks, missed = run(name)
    _, rows2, tracks2, missed2 = run(name, shuffle=random.Random(seed))
    assert rows2 == rows and tracks2 == tracks and missed2 == missed


# --- Matching (N4) ---------------------------------------------------------------------------------------------------

PAIR = ("p1", "f1")


def ref(rid, a, b, pair=PAIR, assessable=True):
    return mt.Reference(rid, a, b, pair, assessable)


def mw(refs, events, group, iou_m, reference_class, groups=None):
    """Label groups per reference are a match-run input mapping (AR-39 item 3 ruling); default G1 and G2."""
    mapping = {r.ref_event_id: frozenset((groups or {}).get(r.ref_event_id, ("G1", "G2"))) for r in refs}
    return mt.match_window(refs, events, group, iou_m, reference_class, mapping)


def sev(key, a, b, pair=PAIR, labels=("H",)):
    return mt.SystemEvent(["pow_x", key], f"s{key}", a, b, pair, frozenset(labels))


def by_type(records):
    return sorted((r["match_type"], r["ref_event_id"], r["system_event_id"]) for r in records)


@pytest.mark.determinism
def test_fx_tie():
    inputs, expected = fx("FX-TIE")["inputs"], fx("FX-TIE")["expected"]
    refs = [ref(k, *v) for k, v in inputs["references"].items()]
    events = [mt.SystemEvent(["pow_x", 0], "s1", *inputs["system"]["s1"], PAIR, frozenset({"H"}))]
    assert mt.temporal_iou((0.0, 1.0), (0.5, 1.5)) == pytest.approx(expected["iou"]["s1,r1"], abs=1e-9)
    records = mw(refs, events, "G1", 0.3, "rule_conformance")
    assert [[r["system_event_id"], r["ref_event_id"]] for r in records if r["match_type"] == "matched"] == expected["matches"]
    assert [r["ref_event_id"] for r in records if r["match_type"] == "miss"] == expected["misses"]


@pytest.mark.determinism
def test_composite_weight_prefers_higher_iou_then_lower_system_key():
    # r1 [0, 1); s0 [0, 1) IoU 1.0 and s1 [0.2, 1.0) IoU 0.8: higher IoU wins; s1 overlaps the matched r1 -> duplicate_alert.
    records = mw([ref("r1", 0.0, 1.0)], [sev(1, 0.2, 1.0), sev(0, 0.0, 1.0)], "G1", 0.3, "rule_conformance")
    assert by_type(records) == [("duplicate_alert", None, "s1"), ("matched", "r1", "s0")]
    # Equal IoU 0.5: s0 [0, 0.5) and s1 [0.5, 1.0) against r1 [0, 1): the lower system key s0 wins.
    records = mw([ref("r1", 0.0, 1.0)], [sev(1, 0.5, 1.0), sev(0, 0.0, 0.5)], "G1", 0.3, "rule_conformance")
    assert by_type(records) == [("duplicate_alert", None, "s1"), ("matched", "r1", "s0")]


@pytest.mark.determinism
def test_match_classes():
    refs = [ref("r1", 0.0, 1.0), ref("r2", 5.0, 6.0), ref("r3", 10.0, 11.0, assessable=False)]
    events = [sev(0, 0.0, 1.0), sev(1, 20.0, 21.0), sev(2, 5.0, 6.0, pair=("p2", "f1")), sev(3, 10.0, 11.0)]
    records = mw(refs, events, "G1", 0.3, "rule_conformance")
    # s2 has another pair, so r2 is a miss and s2 a false alert; s3 lies on an unobservable reference and is a false alert (N4).
    assert by_type(records) == [("false_alert", None, "s1"), ("false_alert", None, "s2"), ("false_alert", None, "s3"),
                                ("matched", "r1", "s0"), ("miss", "r2", None), ("unobservable_reference", "r3", None)]
    matched = next(r for r in records if r["match_type"] == "matched")
    assert (matched["temporal_iou"], matched["onset_error_s"], matched["offset_error_s"]) == (1.0, 0.0, 0.0)
    assert {r["reference_class"] for r in records} == {"rule_conformance"}


@pytest.mark.determinism
def test_iou_m_threshold():
    # r1 [0, 1), s0 [0.71, 1.71): IoU 0.29/1.71 = 0.1696 < 0.3, no match; s0 overlaps no matched reference -> false alert.
    records = mw([ref("r1", 0.0, 1.0)], [sev(0, 0.71, 1.71)], "G1", 0.3, "rule_conformance")
    assert by_type(records) == [("false_alert", None, "s0"), ("miss", "r1", None)]


@pytest.mark.determinism
def test_label_groups_and_abstention():
    # G2 run: s0 carries UD (decides); s1 carries H and IE only (abstains in G2); s2 carries H only (no G2 decision, no record).
    refs = [ref("r1", 0.0, 1.0), ref("r2", 5.0, 6.0), ref("r3", 10.0, 11.0), ref("r4", 20.0, 21.0)]
    events = [sev(0, 0.0, 1.0, labels=("H", "UD")), sev(1, 5.0, 6.0, labels=("H", "IE")), sev(2, 10.0, 11.0, labels=("H",))]
    only_g1 = {"r4": ("G1",)}
    records = mw(refs, events, "G2", 0.3, "rule_conformance", only_g1)
    assert by_type(records) == [("abstained_miss", "r2", None), ("matched", "r1", "s0"), ("miss", "r3", None)]  # r4 not in G2
    g1 = mw(refs, events, "G1", 0.3, "rule_conformance", only_g1)
    assert [t for t, _, _ in by_type(g1)].count("matched") == 3 and ("miss", "r4", None) in by_type(g1)  # IE events still decide in G1


@pytest.mark.determinism
@pytest.mark.parametrize("seed", range(20))
def test_ct_e_20_matching_determinism(seed):
    rng = random.Random(seed)
    refs = [ref(f"r{i}", t, t + rng.choice([0.5, 1.0, 1.5]), pair=rng.choice([PAIR, ("p2", "f1")])) for i, t in enumerate(rng.sample(range(0, 40, 2), 8))]
    events = [sev(i, t / 2, t / 2 + rng.choice([0.5, 1.0]), pair=rng.choice([PAIR, ("p2", "f1"), None]), labels=rng.choice([("H",), ("H", "UD"), ("H", "IE")]))
              for i, t in enumerate(rng.sample(range(0, 80), 10))]
    canon = lambda recs: sorted(canonical_json(r) for r in recs)
    for group in ("G1", "G2", "any"):
        base = canon(mw(refs, events, group, 0.3, "rule_conformance"))
        for _ in range(5):
            r2, e2 = refs[:], events[:]
            rng.shuffle(r2)
            rng.shuffle(e2)
            assert canon(mw(r2, e2, group, 0.3, "rule_conformance")) == base


@pytest.mark.determinism
def test_ct_e_21_abstention_counts_as_miss():
    refs = [ref("r1", 0.0, 1.0), ref("r2", 5.0, 6.0), ref("r3", 10.0, 11.0)]
    decide = [sev(0, 0.0, 1.0, labels=("H", "UD")), sev(1, 5.0, 6.0, labels=("H", "UD")), sev(2, 10.0, 11.0, labels=("H", "UD"))]
    before = em.headline([em.window_counts(mw(refs, decide, "G2", 0.3, "rule_conformance"), 3600.0)])
    abstain = decide[:2] + [sev(2, 10.0, 11.0, labels=("H", "IE"))]  # one more abstention
    after = em.headline([em.window_counts(mw(refs, abstain, "G2", 0.3, "rule_conformance"), 3600.0)])
    assert (before["EV-M1"], after["EV-M1"]) == (1.0, pytest.approx(2 / 3))  # headline recall decreases
    assert after["EV-M5"] == pytest.approx(1 / 3) and after["EV-M4"] == pytest.approx(2 / 3) and after["EV-M6"] == 1.0


# --- EV-M metrics (hand calculations) --------------------------------------------------------------------------------

def test_headline_metrics_hand_calculation():
    # Window 1: a = 4 (2 matched, 1 miss, 1 abstained miss), 1 false, 1 duplicate, u = 0.5 h.
    # Window 2: a = 2 (2 matched), 0 alerts, u = 1.0 h. Weights 2 and 1.
    w1 = em.WindowCounts(a=4, m=2, s=4, m_s=2, f=2, c=3, abstained_miss=1, duplicate=1, u=0.5)
    w2 = em.WindowCounts(a=2, m=2, s=2, m_s=2, f=0, c=2, abstained_miss=0, duplicate=0, u=1.0)
    got = em.headline([w1, w2], [2.0, 1.0])
    assert got["EV-M1"] == pytest.approx((2 * 2 + 2) / (2 * 4 + 2))  # 6/10
    assert got["EV-M2"] == pytest.approx((2 * 2 + 2) / (2 * 4 + 2))  # 6/10
    assert got["EV-M4"] == pytest.approx((2 * 3 + 2) / 10)  # 8/10
    assert got["EV-M5"] == pytest.approx(2 / 10)
    assert got["EV-M6"] == pytest.approx(6 / 8)
    assert got["EV-M7"] == pytest.approx((2 * 2) / (2 * 0.5 + 1.0))  # 4 alerts per 2 weighted hours = 2.0 per hour
    assert got["EV-M11"] == pytest.approx(2 / (2 * 3 + 2))  # duplicate / (matched system + duplicate)
    assert em.headline([em.WindowCounts(0, 0, 0, 0, 0, 0, 0, 0, 0.0)])["EV-M1"] is None  # denominator 0 -> not_applicable


@pytest.mark.determinism
def test_ev_m1_reproduces_fx_w():
    # Appendix N5 FX-W through the EV-M1 estimator: weighted 0.71875, unweighted 0.70.
    inputs, expected = fx("FX-W")["inputs"], fx("FX-W")["expected"]
    windows = [em.WindowCounts(a=w["a"], m=w["m"], s=0, m_s=0, f=0, c=w["a"], abstained_miss=0, duplicate=0, u=1.0) for w in inputs["windows"]]
    weights = [inputs["strata"][w["stratum"]]["w"] for w in inputs["windows"]]
    assert em.headline(windows, weights)["EV-M1"] == pytest.approx(expected["weighted_recall"], abs=1e-9)
    assert em.headline(windows)["EV-M1"] == pytest.approx(expected["unweighted_recall"], abs=1e-9)


def test_window_counts_from_records():
    records = [{"match_type": t} for t in ("matched", "matched", "miss", "abstained_miss", "false_alert", "duplicate_alert", "unobservable_reference")]
    c = em.window_counts(records, 1800.0)
    assert (c.a, c.m, c.s, c.m_s, c.f, c.c, c.abstained_miss, c.duplicate, c.u) == (4, 2, 4, 2, 2, 3, 1, 1, 0.5)


def test_ev_m8_localization():
    records = [{"match_type": "matched", "onset_error_s": e, "offset_error_s": -e / 2, "temporal_iou": iou}
               for e, iou in ((0.1, 0.9), (-0.3, 0.6), (0.2, 0.75), (0.0, 1.0))] + [{"match_type": "miss"}]
    got = em.localization(records)
    # |onset| = 0.0, 0.1, 0.2, 0.3: median 0.15; P90 at h = 3 x 0.9 = 2.7 -> 0.2 + 0.7 x 0.1 = 0.27. Mean IoU 3.25/4.
    assert got["onset_median_s"] == pytest.approx(0.15) and got["onset_p90_s"] == pytest.approx(0.27)
    assert got["offset_median_s"] == pytest.approx(0.075) and got["mean_iou"] == pytest.approx(0.8125)
    assert em.localization([{"match_type": "miss"}])["mean_iou"] is None


def test_ev_m3_abstention_rate():
    # T10.7(a): abstained = IE without NM/UD/CT. Episodes: {H, IE} 1.0 s abstains; {H} 2.0 s; {H, UD, IE} 0.5 s does not; {PC, IE} 0.5 s abstains.
    eps = [(frozenset({"H", "IE"}), 1.0), (frozenset({"H"}), 2.0), (frozenset({"H", "UD", "IE"}), 0.5), (frozenset({"PC", "IE"}), 0.5)]
    got = em.abstention_rate([(eps, 10.0)])
    assert got == {"episodes": 0.5, "support": pytest.approx(0.15)}  # 2/4; (1.0 + 0.5)/10


@pytest.mark.determinism
def test_ar_39_item_3_label_groups_are_an_input_mapping():
    # Architect ruling on AR-39 item 3: a reference without a label-group entry is refused, never silently dropped.
    from rq1.schema.errors import ContractError
    with pytest.raises(ContractError) as exc:
        mt.match_window([ref("r1", 0.0, 1.0)], [], "G1", 0.3, "rule_conformance", {})
    assert exc.value.code == "ERR-SPEC"
    assert by_type(mt.match_window([ref("r1", 0.0, 1.0)], [], "G2", 0.3, "rule_conformance", {"r1": frozenset({"G1"})})) == []  # not in G2
