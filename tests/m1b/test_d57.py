"""D-57 STEPS 2 and 3: split mechanism, gap inspection, quantiles, the pre-declared m_gap selection rule and the S5
configuration of the sweep (hand-made inputs; expected values by hand, recorded beside each assertion)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d57_mgap as mg  # noqa: E402
import d57_split as sp  # noqa: E402


def _ep(pow_id, pt, ft, t0, t1, s, e, cont=False, pair=("p1", "f1")):
    return {"pow_id": pow_id, "person_track_id": pt, "forklift_track_id": ft, "pair": pair, "t0": t0, "t1": t1,
            "start_frame": s, "end_frame_excl": e, "continuation": cont}


# ------------------------------------------------------------------------------------------------------------- STEP 2

def test_mechanism_same_pow_is_i():
    a, b = _ep("pow_1", "trk_p", "trk_f", 0.0, 1.0, 0, 30), _ep("pow_1", "trk_p", "trk_f", 2.0, 3.0, 60, 90)
    assert sp.mechanism(a, b) == "i"


def test_mechanism_other_pow_same_tracks_is_ii():
    a, b = _ep("pow_1", "trk_p", "trk_f", 0.0, 1.0, 0, 30), _ep("pow_2", "trk_p", "trk_f", 2.0, 3.0, 60, 90, cont=True)
    assert sp.mechanism(a, b) == "ii"


@pytest.mark.parametrize("pt, ft", [("trk_q", "trk_f"), ("trk_p", "trk_g"), ("trk_q", "trk_g")])
def test_mechanism_other_track_is_iii(pt, ft):
    a, b = _ep("pow_1", "trk_p", "trk_f", 0.0, 1.0, 0, 30), _ep("pow_2", pt, ft, 2.0, 3.0, 60, 90)
    assert sp.mechanism(a, b) == "iii"


def test_covering_episodes_same_pair_overlap_sorted_by_start():
    # reference (pair p1-f1) over [1, 5] s. e3 starts before e1; e_other is another pair; e_far does not overlap.
    ref = ("rin_1", ("p1", "f1"), 1.0, 5.0)
    e1 = _ep("pow_1", "a", "b", 2.0, 3.0, 60, 90)
    e3 = _ep("pow_2", "c", "d", 0.5, 1.5, 15, 45)
    e_other = _ep("pow_3", "a", "b", 2.0, 3.0, 60, 90, pair=("p2", "f1"))
    e_far = _ep("pow_1", "a", "b", 6.0, 7.0, 180, 210)
    e_none = _ep("pow_4", "a", "b", 2.0, 3.0, 60, 90, pair=None)
    assert sp.covering(ref, [e1, e_other, e_far, e3, e_none]) == [e3, e1]


def test_consecutive_pairs_and_gap():
    ref = ("rin_1", ("p1", "f1"), 0.0, 10.0)
    eps = [_ep("pow_1", "a", "b", 0.0, 1.0, 0, 30), _ep("pow_1", "a", "b", 2.0, 3.0, 60, 90), _ep("pow_2", "a", "b", 3.5, 4.0, 105, 120)]
    pairs = sp.consecutive_pairs(ref, eps)
    assert [(a["start_frame"], b["start_frame"]) for a, b in pairs] == [(0, 60), (60, 105)]
    # gap: 2.0 - 1.0 = 1.0 s and 60 - 30 = 30 frames; 3.5 - 3.0 = 0.5 s and 105 - 90 = 15 frames
    assert sp.gap(*pairs[0]) == (pytest.approx(1.0), 30)
    assert sp.gap(*pairs[1]) == (pytest.approx(0.5), 15)


def test_single_covering_episode_gives_no_pair():
    ref = ("rin_1", ("p1", "f1"), 0.0, 10.0)
    assert sp.consecutive_pairs(ref, [_ep("pow_1", "a", "b", 0.0, 1.0, 0, 30)]) == []


@pytest.mark.parametrize("c, expected", [(None, "null"), (0.4, "below_d_pc"), (1.0, "d_pc_to_d_p"), (1.99, "d_pc_to_d_p"),
                                         (2.0, "at_or_above_d_p"), (7.5, "at_or_above_d_p")])
def test_clearance_category_matches_the_provider_inequalities(c, expected):
    # R2: P = clearance < d_p; categories split at d_pc = 1.0 and d_p = 2.0 with the same strict "<"
    assert sp.clearance_category(c, d_p=2.0, d_pc=1.0) == expected


def test_flags_true_before_gap():
    assert sp.flags_true({"P": 1, "X": 1, "C_any": 0}) == "P+X"
    assert sp.flags_true({"P": 0, "X": 0, "C_any": 1}) == "C"
    assert sp.flags_true({"P": 2, "X": 2, "C_any": 1}) == "C"
    assert sp.flags_true({"P": 1, "X": 0, "C_any": 1}) == "P+C"


def test_inside_gap_hand_counts():
    # 10 gap frames: T = 0 x6, T = 2 x3, T = 1 x1 (a discarded short window); Q sufficient on 4 of 10
    flags = [{"T": 0}] * 6 + [{"T": 2}] * 3 + [{"T": 1}]
    q = ["sufficient"] * 4 + ["insufficient"] * 6
    out = sp.inside_gap(flags, {"P": 1, "X": 0, "C_any": 0}, 1.5, 2.4, q, d_p=2.0, d_pc=1.0)
    assert out["gap_flag_frames"] == 10
    assert out["share_T0"] == pytest.approx(0.6) and out["share_T_unknown"] == pytest.approx(0.3) and out["share_T1"] == pytest.approx(0.1)
    assert out["flags_true_before"] == "P"
    assert (out["clearance_before_m"], out["clearance_before"]) == (1.5, "d_pc_to_d_p")
    assert (out["clearance_after_m"], out["clearance_after"]) == (2.4, "at_or_above_d_p")
    assert out["share_q_sufficient"] == pytest.approx(0.4)
    assert out["q_state"] == "mixed"


@pytest.mark.parametrize("q, expected", [(["sufficient"] * 3, "sufficient"), (["insufficient"] * 2, "insufficient"), ([], "no_pair_frames")])
def test_inside_gap_q_state_summary(q, expected):
    out = sp.inside_gap([{"T": 0}] * len(q), {"P": 1, "X": 1, "C_any": 0}, None, None, q, d_p=2.0, d_pc=1.0)
    assert out["q_state"] == expected


def test_quantiles_linear_interpolation():
    # values 1..10: median 5.5; P75 (9 * 0.75 = 6.75) -> 7.75; P90 (8.1) -> 9.1; max 10
    q = sp.quantiles(list(range(1, 11)))
    assert q == {"n": 10, "median": pytest.approx(5.5), "p75": pytest.approx(7.75), "p90": pytest.approx(9.1), "max": 10}
    assert sp.quantiles([]) == {"n": 0, "median": None, "p75": None, "p90": None, "max": None}


# ------------------------------------------------------------------------------------------------------------- STEP 3

def test_grid_is_the_d57_grid():
    assert mg.GRID == (5, 15, 30, 60)
    assert mg.CONFIGS == ("C-v2", "B-both", "A")


def test_selection_keeps_ev_m1_within_002_then_highest_ev_m2():
    # EV-M1(5) = 0.578 -> keep EV-M1 >= 0.558: 5, 15, 30 kept; 60 (0.55) dropped. Highest EV-M2 of the kept: 30 (0.40).
    r = {5: (0.578, 0.329), 15: (0.570, 0.37), 30: (0.560, 0.40), 60: (0.55, 0.45)}
    out = mg.select(r)
    assert out["kept"] == [5, 15, 30] and out["chosen"] == 30


def test_selection_tie_within_0005_takes_smaller_m_gap():
    # kept: all; best EV-M2 0.404 at 60; 30 (0.400) is within 0.005 of it -> the smaller m_gap, 30
    r = {5: (0.578, 0.329), 15: (0.578, 0.37), 30: (0.578, 0.400), 60: (0.578, 0.404)}
    assert mg.select(r)["chosen"] == 30


def test_selection_tie_exactly_0005_is_a_tie():
    r = {5: (0.578, 0.400), 15: (0.578, 0.405), 30: (0.578, 0.30), 60: (0.578, 0.30)}
    assert mg.select(r)["chosen"] == 5


def test_selection_keeps_m_gap_5_always():
    r = {5: (0.578, 0.329), 15: (0.40, 0.9), 30: (0.40, 0.9), 60: (0.40, 0.9)}
    out = mg.select(r)
    assert out["kept"] == [5] and out["chosen"] == 5


def test_s5_params_change_only_m_gap():
    base = dict(mg.m.S5_BASE)
    for g in mg.GRID:
        p = mg.p5(g)
        assert p["m_gap"] == g
        assert {k: v for k, v in p.items() if k != "m_gap"} == {k: v for k, v in base.items() if k != "m_gap"}
    assert mg.m.S5_BASE == base  # the frozen v1 base values are not mutated


def test_version_label_v1_only_at_the_v1_value():
    assert mg.version_label(5) == "preregistration-v1"
    assert mg.version_label(30) == "D-57 diagnostic m_gap 30 (not frozen)"


def test_label_counts_sum_recording_scope_only():
    rows = [{"scope_type": "recording", "scenario": "S_VIEW", "label": "all", "n_events": 3},
            {"scope_type": "timeline", "scenario": "S_VIEW", "label": "all", "n_events": 3},
            {"scope_type": "recording", "scenario": "S_VIEW", "label": "PC", "n_events": 1}]
    assert mg.label_counts(rows) == {"S_VIEW|PC": 1, "S_VIEW|all": 3}
