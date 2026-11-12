"""Appendix T section T9 (contract E-1.2.7; D-9). Every expected value is an Appendix N value or a hand calculation written here."""
import dataclasses
import json
import math
import random
from pathlib import Path

import pytest

from rq1.events import engine, providers
from rq1.events.engine import FrameFlags, Rates
from rq1.schema import vr_rules

from test_engine_part_a import PARAMS, RULES, V, s4_for

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
OFF = dataclasses.replace(PARAMS, r5_enabled=False)


def frame(i, **kw):
    base = dict(P=1, M=1, C_by={"R3": 0}, E=0, Q=1, clearance=1.0, sigma=0.05, overlap=0, image_gap_norm=0.5)
    base.update(kw)
    return FrameFlags(i, i / 10, 0.1, **base)


# --- T9.2 rates, from object-state rows (10 fps, w_e = 1.0 s, v_min = 0.3) ---------------------------------------

def frames_10fps(n):
    return {i: {"frame_index": i, "t_resolved_s": i / 10, "support_start_tl_s": i / 10, "support_s": 0.1} for i in range(n)}


def rows(n, speed, heading=lambda t: 0.0, usable=None):
    out = []
    for i in range(n):
        t = i / 10
        ok = usable is None or i in usable
        out.append({"frame_index": i, "x_m": 0.0 if ok else None, "evidence_class": "detected" if ok else "insufficient",
                    "speed_mps": speed(t) if ok else None, "heading_rad": heading(t) if ok else None})
    return out


@pytest.mark.determinism
def test_t9_2_forklift_deceleration_with_shifted_window():
    # Forklift speed 4 - 2.5 t. At t = 1.0 the window is [0.5, 1.5]: a = frame 5 (2.75), b = frame 15 (0.25), decel 2.5/1.0 = 2.5.
    # At t = 0 the window shifts to [0, 1.0]: 4.0 -> 1.5, also 2.5 m/s^2.
    rates = providers.r5_rates(rows(20, lambda t: 1.0), rows(20, lambda t: 4 - 2.5 * t), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].forklift_decel == pytest.approx(2.5, abs=1e-9) and rates[0].forklift_decel == pytest.approx(2.5, abs=1e-9)
    assert rates[10].person_speed_change == pytest.approx(0.0, abs=1e-12) and rates[10].person_turn_rate == pytest.approx(0.0, abs=1e-12)
    assert engine.evasive(rates[10], V["e_turn"], V["e_acc"], V["e_dec"]) == 1  # 2.5 > e_dec 2.0
    assert engine.evasive_ratio(rates[10], V["e_turn"], V["e_acc"], V["e_dec"]) == pytest.approx(1.25, abs=1e-9)  # 2.5 / 2.0


@pytest.mark.determinism
def test_t9_2_accelerating_forklift_has_zero_deceleration():
    rates = providers.r5_rates(rows(20, lambda t: 1.0), rows(20, lambda t: 1 + 2 * t), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].forklift_decel == 0.0


@pytest.mark.determinism
def test_t9_2_person_turn_rate_and_speed_change():
    # Person speed 0.5 + 1.2 t, heading 2 t: at t = 1.0, a = 0.5 s, b = 1.5 s: speed change 1.2/1.0, turn 2.0/1.0.
    rates = providers.r5_rates(rows(20, lambda t: 0.5 + 1.2 * t, lambda t: 2 * t), rows(20, lambda t: 0.0), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].person_speed_change == pytest.approx(1.2, abs=1e-9) and rates[10].person_turn_rate == pytest.approx(2.0, abs=1e-9)
    assert engine.criteria(rates[10], V["e_turn"], V["e_acc"], V["e_dec"]) == (1, 1, 0)  # 2.0 > 1.5, 1.2 > 1.0, decel 0


@pytest.mark.determinism
def test_t9_2_heading_difference_is_wrapped():
    assert providers.wrap(-6.0) == pytest.approx(2 * math.pi - 6.0, abs=1e-12)
    assert providers.wrap(math.pi) == pytest.approx(math.pi) and providers.wrap(-math.pi) == pytest.approx(math.pi)  # (-pi, pi]
    # Heading 3.0 at a and -3.0 at b: |wrap(-6.0)| = 0.2832 rad over 1.0 s, not 6.0 rad/s.
    rates = providers.r5_rates(rows(20, lambda t: 1.0, lambda t: 3.0 if t < 1.0 else -3.0), rows(20, lambda t: 0.0), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].person_turn_rate == pytest.approx(2 * math.pi - 6.0, abs=1e-9)


@pytest.mark.determinism
def test_t9_2_turn_is_false_without_motion():
    # Person stops: speed 1.0 at a, 0.1 < v_min at b. The turn criterion is FALSE; the stop is captured by speed change 0.9/1.0.
    rates = providers.r5_rates(rows(20, lambda t: 1.0 if t < 1.2 else 0.1, lambda t: 0.0), rows(20, lambda t: 0.0), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].turn_false and rates[10].person_turn_rate is None
    assert rates[10].person_speed_change == pytest.approx(0.9, abs=1e-9)
    assert engine.criteria(rates[10], V["e_turn"], V["e_acc"], V["e_dec"]) == (0, 0, 0)


@pytest.mark.determinism
def test_t9_2_unknown_when_ends_span_less_than_half_window():
    # Person usable on frames 0-3 only (span 0.3 s < w_e/2 = 0.5 s): its criteria are unknown; the forklift's are not.
    rates = providers.r5_rates(rows(20, lambda t: 1.0, usable=set(range(4))), rows(20, lambda t: 1.0), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[2].person_speed_change is None and rates[2].person_turn_rate is None and not rates[2].turn_false
    assert rates[2].forklift_decel == 0.0
    assert engine.criteria(rates[2], V["e_turn"], V["e_acc"], V["e_dec"]) == (2, 2, 0)
    assert engine.evasive(rates[2], V["e_turn"], V["e_acc"], V["e_dec"]) == 2


@pytest.mark.determinism
def test_t9_2_frame_outside_the_run_is_unknown():
    # CR-009 item 2 (provisional): the person is lost on frame 10, so frame 10 has no run and no window.
    usable = set(range(20)) - {10}
    rates = providers.r5_rates(rows(20, lambda t: 1.0, usable=usable), rows(20, lambda t: 1.0), frames_10fps(20), [], w_e=1.0, v_min=0.3)
    assert rates[10].person_speed_change is None and rates[9].person_speed_change == pytest.approx(0.0, abs=1e-12)


@pytest.mark.determinism
def test_t9_2_window_does_not_cross_a_coverage_break():
    # A not_recorded segment between frames 9 and 10 splits the forklift run: at frame 9 the window is [0, 0.9] and the
    # speed jump at frame 10 is never seen. Forklift speed 2.0 before, 0.0 after.
    frames = frames_10fps(20)
    for f in frames.values():
        f["support_s"] = 0.09  # frame 9 support ends at 0.99 s, frame 10 starts at 1.00 s
    cov = [{"coverage_state": "not_recorded", "t_start_tl_s": 0.992, "t_end_tl_s": 0.998}]
    rates = providers.r5_rates(rows(20, lambda t: 1.0), rows(20, lambda t: 2.0 if t < 0.95 else 0.0), frames, cov, w_e=1.0, v_min=0.3)
    assert rates[9].forklift_decel == 0.0 and rates[10].forklift_decel == 0.0


def test_t9_2_e_in_kleene_logic():
    assert engine.evasive(Rates(), 1.5, 1.0, 2.0) == 2
    assert engine.evasive(Rates(person_speed_change=1.5), 1.5, 1.0, 2.0) == 1  # one true criterion decides
    assert engine.evasive(Rates(person_speed_change=0.5, forklift_decel=0.5), 1.5, 1.0, 2.0) == 2  # turn unknown
    assert engine.evasive(Rates(person_speed_change=0.5, forklift_decel=0.5, turn_false=True), 1.5, 1.0, 2.0) == 0


def test_t9_2_exp_evasive_score_is_max_over_i_plus():
    # I = [0, 5); I+ = [0, 15). Ratios: frame 2 speed change 0.5/1.0 = 0.5; frame 12 (after I) decel 3.0/2.0 = 1.5.
    frames = [frame(i, P=1 if i < 5 else 0, rates=Rates(person_speed_change=0.0, forklift_decel=0.0, turn_false=True)) for i in range(30)]
    frames[2].rates = Rates(person_speed_change=0.5, forklift_decel=0.0, turn_false=True)
    frames[12].rates = Rates(person_speed_change=0.0, forklift_decel=3.0, turn_false=True)
    frames[20].rates = Rates(person_speed_change=0.0, forklift_decel=9.0, turn_false=True)  # outside I+, ignored
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["attr_end_frame_excl"] == 15 and ep["exp_evasive_score"] == pytest.approx(1.5, abs=1e-12)


# --- T9.3 contact cue ----------------------------------------------------------------------------------------------

def test_t9_3_cue_units():
    k_c, k_turn = V["k_c"], V["k_c_turn"]
    assert (k_c, k_turn) == (3.0, 3.0)
    assert engine.contact_cue(Rates(forklift_decel=3.5, person_speed_change=0.0, turn_false=True), k_c, k_turn) == 1
    assert engine.contact_cue(Rates(forklift_decel=0.0, person_speed_change=3.1, turn_false=True), k_c, k_turn) == 1
    assert engine.contact_cue(Rates(forklift_decel=0.0, person_speed_change=0.0, person_turn_rate=3.2), k_c, k_turn) == 1  # rad/s vs k_c_turn
    assert engine.contact_cue(Rates(forklift_decel=2.9, person_speed_change=2.9, person_turn_rate=2.9), k_c, k_turn) == 0
    assert engine.contact_cue(Rates(forklift_decel=0.0, person_speed_change=0.0), k_c, k_turn) == 2  # turn unknown
    assert engine.contact_cue(None, k_c, k_turn) == 2


def test_t9_3_cue_at_ca_gives_suspected():
    # Overlap at the minimum-clearance frame 5 (-0.10 m) with forklift deceleration 3.5 m/s^2 > k_c there: suspected, CT.
    frames = [frame(i, clearance=0.5 - 0.12 * min(i, 5), overlap=0, rates=Rates(0.0, 0.0, None, True)) for i in range(10)]
    frames[5].overlap, frames[5].rates = 1, Rates(person_speed_change=0.0, forklift_decel=3.5, turn_false=True)
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert (ep["closest_approach_frame"], ep["contact_state"], ep["lbl_CT"]) == (5, "suspected", True)
    frames[5].rates = Rates(person_speed_change=0.0, forklift_decel=2.0, turn_false=True)
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["contact_state"] == "undetermined"  # overlap without a cue


# --- T9.4 E when R5 is disabled -------------------------------------------------------------------------------------

def test_t9_4_r5_disabled():
    frames = [frame(i, E=2, clearance=0.4) for i in range(10)]  # E would be unknown if assessed
    (ep,), _ = engine.run_pow(frames, OFF)
    assert (ep["E_ep"], ep["e_assessed"], ep["K"]) == (0, False, 1)  # K = (0.4 < d_nm 0.5)
    frames = [frame(i, E=2, clearance=1.0) for i in range(10)]
    (ep,), _ = engine.run_pow(frames, OFF)
    assert (ep["E_ep"], ep["K"], ep["lbl_NM"], ep["lbl_UD"], ep["lbl_IE"]) == (0, 0, False, False, False)
    frames = [frame(i, E=2, clearance=None, image_gap_norm=0.2) for i in range(10)]
    (ep,), _ = engine.run_pow(frames, OFF)
    assert ep["K"] == 2  # no measured clearance: (minclr < d_nm) is unknown
    (ep,), _ = engine.run_pow([frame(i, E=2) for i in range(10)], PARAMS)
    assert (ep["E_ep"], ep["e_assessed"], ep["K"]) == (2, True, 2)


@pytest.mark.determinism
@pytest.mark.parametrize("r5", [False, True])
def test_t9_4_check_g2_gives_h(r5):
    expected, s4, _, s1 = s4_for("N2-G2")
    flags = providers.flag_frames(s4.tables, dataclasses.replace(RULES, r5=r5), s1["frame"], s1["coverage_segment"])
    (ep,), _ = engine.run_pow(flags, dataclasses.replace(PARAMS, r5_enabled=r5))
    got = [n for n in ("O", "H", "PC", "NM", "UD", "CT", "IE") if ep[f"lbl_{n}"]]
    assert got == expected["episodes"][0]["labels"] == ["H"] and ep["e_assessed"] is r5 and ep["E_ep"] == 0


# --- N2 end to end through S4 and S5 ---------------------------------------------------------------------------------

@pytest.mark.determinism
@pytest.mark.parametrize("name", ["N2-G1", "N2-G2", "N2-G3"])
def test_n2_episodes_end_to_end(name):
    expected, s4, _, s1 = s4_for(name)
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    episodes, discarded = engine.run_pow(flags, PARAMS)
    assert len(episodes) == len(expected["episodes"]) == 1 and discarded == []
    ep, want = episodes[0], expected["episodes"][0]
    assert (ep["start_frame"], ep["end_frame_excl"]) == (want["start_frame"], want["end_frame_excl"])
    assert [n for n in ("O", "H", "PC", "NM", "UD", "CT", "IE") if ep[f"lbl_{n}"]] == want["labels"]
    if "minclr_m" in want:
        assert ep["minclr_m"] == pytest.approx(want["minclr_m"], abs=1e-6)
    if "duration_detected_s" in want:
        assert ep["duration_detected_s"] == pytest.approx(want["duration_detected_s"], abs=1e-6)  # G1: 5.000 s
    assert ep["ca_observed"] and ep["E_ep"] == 0 and vr_rules.check_episode_labels(ep) == []


# --- T9.5 closest-approach frame -------------------------------------------------------------------------------------

def test_t9_5_observed_ca():
    # Clearance 1.0, 0.8, ..., minimum 0.2 at frames 4 and 6 (earliest tie: 4), rising afterwards; all measured.
    values = [1.0, 0.8, 0.6, 0.4, 0.2, 0.3, 0.2, 0.5, 0.7, 0.9]
    ca, t_ca, observed = engine.closest_approach([frame(i, clearance=v) for i, v in enumerate(values)])
    assert (ca.frame_index, t_ca, observed) == (4, pytest.approx(0.4), True)


def test_t9_5_unobserved_continuation_with_ttca():
    # Measured frames 0-9, still closing (rate 0.1 m/s > 0) at m* = 9, frames 10-14 unmeasured. ttca(9) = 0.3 s:
    # t_CA = 0.9 + 0.3 = 1.2 s, nearest frame 12.
    inside = [frame(i, clearance=1.0 - 0.01 * i if i < 10 else None, closing_rate=0.1 if i < 10 else None, ttca=0.3 if i == 9 else None) for i in range(15)]
    ca, t_ca, observed = engine.closest_approach(inside)
    assert (ca.frame_index, t_ca, observed) == (12, pytest.approx(1.2), False)


def test_t9_5_unobserved_continuation_without_ttca_uses_end_of_i():
    # ttca null and closing rate null at m*: t_CA = end of I = 1.4 + 0.1 = 1.5 s; the nearest frame of I is 14.
    inside = [frame(i, clearance=1.0 - 0.01 * i if i < 10 else None) for i in range(15)]
    ca, t_ca, observed = engine.closest_approach(inside)
    assert (ca.frame_index, t_ca, observed) == (14, pytest.approx(1.5), False)


def test_t9_5_diverging_at_last_measured_frame_stays_observed():
    inside = [frame(i, clearance=1.0 - 0.01 * i if i < 10 else None, closing_rate=-0.2 if i < 10 else None) for i in range(15)]
    ca, _, observed = engine.closest_approach(inside)
    assert (ca.frame_index, observed) == (9, True)


def test_t9_5_minimum_not_at_last_measured_frame_stays_observed():
    inside = [frame(i, clearance=[0.5, 0.3, 0.4, 0.6][i] if i < 4 else None, closing_rate=0.5) for i in range(8)]
    ca, _, observed = engine.closest_approach(inside)
    assert (ca.frame_index, observed) == (1, True)


def test_t9_5_no_measured_clearance_uses_image_gap():
    inside = [frame(i, clearance=None, image_gap_norm=[0.4, 0.1, 0.3, 0.1, 0.5][i]) for i in range(5)]
    ca, t_ca, observed = engine.closest_approach(inside)
    assert (ca.frame_index, t_ca, observed) == (1, pytest.approx(0.1), False)  # earliest of the tied minima


def test_t9_5_no_boxes_gives_null_ca_and_not_assessable():
    frames = [frame(i, clearance=None, image_gap_norm=None, M=1) for i in range(10)]
    assert engine.closest_approach(frames) == (None, None, False)
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert (ep["closest_approach_frame"], ep["ca_observed"], ep["contact_state"], ep["lbl_IE"]) == (None, False, "not_assessable", True)
    assert vr_rules.check_episode_labels(ep) == []


# --- T9.6 usable frames around CA and contact-state order ------------------------------------------------------------

@pytest.mark.determinism
def test_t9_6_n1_t10_and_t11():
    # Appendix N1 rows as corrected by T9.9: W_CA = frames 10-19 (|t - 1.5| <= 0.5 s within the 20-frame POW).
    for row, contact in (("T10", "undetermined"), ("T11", "not_assessable")):
        fixture = json.loads((FIX / f"N1-{row}.json").read_text())
        assert fixture["expected"]["contact_state"] == contact
    from test_engine_part_a import run_n1
    (episodes, _), expected = run_n1("T10")
    assert episodes[0]["contact_state"] == expected["contact_state"] == "undetermined"
    (episodes, _), expected = run_n1("T11")
    assert episodes[0]["contact_state"] == expected["contact_state"] == "not_assessable"


def test_t9_6_w_ca_reaches_into_i_plus():
    # I = [0, 10) closes at frame 9 = CA (minimum clearance, still measured). W_CA = frames 4-14 (|t - 0.9| <= 0.5 s).
    # Q is 0 on frames 4-9 but 1 on frames 10-14, which lie in I+: the episode is assessable, and Q = 0 at CA gives undetermined.
    frames = [frame(i, P=1 if i < 10 else 0, M=1 if i < 10 else 0, clearance=1.0 - 0.05 * min(i, 9) + (0.2 if i > 9 else 0),
                    Q=0 if 4 <= i < 10 else 1, closing_rate=-0.1) for i in range(20)]
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert (ep["end_frame_excl"], ep["closest_approach_frame"], ep["contact_state"], ep["lbl_IE"]) == (10, 9, "undetermined", True)
    for f in frames[10:15]:
        f.Q = 0
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["contact_state"] == "not_assessable"


def test_t9_6_q_insufficient_at_ca_comes_before_suspected():
    frames = [frame(i, clearance=-0.1, overlap=1, rates=Rates(0.0, 4.0, None, True)) for i in range(10)]
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["contact_state"] == "suspected"
    frames[0].Q = 0  # CA = frame 0 (earliest tie)
    (ep,), _ = engine.run_pow(frames, PARAMS)
    assert ep["contact_state"] == "undetermined"


# --- T9.7 lifecycle with unknown trigger values ----------------------------------------------------------------------

def lifecycle(pattern):
    frames = [frame(i, P=p, M=0) for i, p in enumerate(pattern)]
    return [(e["start_frame"], e["end_frame_excl"]) for e in engine.run_pow(frames, PARAMS)[0]]


@pytest.mark.determinism
def test_t9_7_unknown_runs():
    assert lifecycle([1] * 3 + [2] * 10 + [1] * 3) == [(0, 16)]  # 10 unknown frames: > m_gap 5 but <= g_max 15, no 0
    assert lifecycle([1] * 3 + [2] * 16 + [1] * 3) == [(0, 3), (19, 22)]  # 16 > g_max
    assert lifecycle([1] * 3 + [2] * 3 + [0] + [2] * 3 + [1] * 3) == [(0, 3), (10, 13)]  # 7 frames with a 0: m_gap applies
    assert lifecycle([1] * 3 + [0, 2, 0, 2, 0] + [1] * 3) == [(0, 11)]  # length 5 <= m_gap
    assert lifecycle([2] * 5 + [1] * 3 + [2] * 4) == [(5, 8)]  # opens only on T = 1; a trailing run never bridges


# --- T9.8 onset_sensitive --------------------------------------------------------------------------------------------

@pytest.mark.determinism
def test_t9_8_onset_sensitive():
    # T9.8 with T10.4: onset uses the frame's P/M/C borderline; the clearance flag is set only from frames of I.
    def run(borderline_at):
        frames = [frame(i, P=1 if 3 <= i < 10 else 0, M=0) for i in range(12)]
        frames[borderline_at].borderline = frozenset({"clearance_within_k_sigma"})
        frames[borderline_at].onset = True
        (ep,), _ = engine.run_pow(frames, PARAMS)
        return ep["borderline_flags"]
    assert run(3) == ["clearance_within_k_sigma", "onset_sensitive"]  # opening frame
    assert run(2) == ["onset_sensitive"]  # the frame before opening is outside I, so it adds no other flag (T10.4)
    assert run(4) == ["clearance_within_k_sigma"]  # later frames are not onset


def test_section_6_0_borderline_frames_from_providers():
    assert providers.borderline(1.95, 2.0, 0.05, 2.0) and not providers.borderline(1.85, 2.0, 0.05, 2.0)  # |d| <= 0.10
    assert providers.borderline(2.0, 2.0, None, 2.0) and not providers.borderline(1.99, 2.0, None, 2.0)  # null sigma uses 0
    assert not providers.borderline(None, 2.0, 0.05, 2.0)


# --- CL-INV over the full T9 engine ----------------------------------------------------------------------------------

@pytest.mark.determinism
@pytest.mark.parametrize("seed", range(200))
def test_cl_inv_property_with_t9_inputs(seed):
    rng = random.Random(seed)
    n = rng.randint(3, 30)
    pick = lambda: rng.choice([0, 1, 2])
    opt = lambda f: rng.choice([None, f()])
    frames = [FrameFlags(i, i / 10, 0.1, P=pick(), M=pick(), C_by={"R3": pick()}, E=pick(), Q=rng.choice([0, 1]),
                         clearance=opt(lambda: rng.uniform(-0.3, 3.0)), sigma=opt(lambda: 0.05), closing_rate=opt(lambda: rng.uniform(-1, 1)),
                         ttca=opt(lambda: rng.uniform(0.1, 2.0)), image_gap_norm=opt(lambda: rng.uniform(-0.2, 1.0)), overlap=pick(),
                         rates=opt(lambda: Rates(opt(lambda: rng.uniform(0, 4)), opt(lambda: rng.uniform(0, 4)), opt(lambda: rng.uniform(0, 4)), rng.random() < 0.3)))
              for i in range(n)]
    episodes, _ = engine.run_pow(frames, dataclasses.replace(PARAMS, r5_enabled=rng.random() < 0.7))
    for ep in episodes:
        assert vr_rules.check_episode_labels(ep) == [], ep


# --- Single-camera candidate events and counts (section 5.6, section 7) ------------------------------------------------

def _episodes_for(name):
    _, s4, _, s1 = s4_for(name)
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    episodes, _ = engine.run_pow(flags, PARAMS)
    return [{**ep, "pow_id": "pow_" + "a" * 26, "camera_id": "cam_" + "a" * 26, "recording_id": "rec_x", "timeline_id": "tl_x"} for ep in episodes]


@pytest.mark.determinism
def test_single_camera_events_are_singletons_in_every_scenario():
    from rq1.events import candidates
    eps = _episodes_for("N2-G3")
    events = candidates.candidate_events(eps)
    assert [e["scenario"] for e in events] == ["S_VIEW", "S_LINK", "S_POSS"]  # one episode, one event per scenario
    for ev in events:
        assert ev["member_episode_nks"] == [["pow_" + "a" * 26, 0]] and ev["edges_used"] == [] and not ev["ambiguous"]
        assert (ev["lbl_PC"], ev["summary_label"], ev["K_ev"]) == (True, "PC", eps[0]["K"])
        assert vr_rules.check_event_labels(ev) == []  # VR-E-032: labels recomputed from event flags
    counts = candidates.count_summaries(events, eps, [("recording", "rec_x"), ("timeline", "tl_x")])
    # T10.6: 2 scopes x 3 scenarios x 8 labels; the G3 event carries PC only.
    assert len(counts) == 48
    got = {(c["scope_type"], c["scenario"], c["label"]): c["n_events"] for c in counts}
    assert all(got[(t, sc, "all")] == 1 and got[(t, sc, "PC")] == 1 for t in ("recording", "timeline") for sc in candidates.SCENARIOS)
    assert sum(got.values()) == 12  # every other label is 0
    assert all(c["wording"] == "scenario_count" and [a["status"] for a in c["assumptions"]] == ["unverified"] * 3 for c in counts)  # LK-07


@pytest.mark.determinism
def test_single_camera_counts_satisfy_lk_04():
    from rq1.events import candidates
    frames = [frame(i, P=1 if (i < 3 or 13 <= i) else 0, M=1) for i in range(20)]  # Appendix N1 T12 pattern: two episodes
    eps = [{**ep, "pow_id": "pow_" + "a" * 26, "camera_id": "cam_" + "a" * 26, "recording_id": "r", "timeline_id": "t"} for ep in engine.run_pow(frames, PARAMS)[0]]
    counts = {c["scenario"]: c["n_events"] for c in candidates.count_summaries(candidates.candidate_events(eps), eps, [("recording", "r")]) if c["label"] == "all"}
    assert counts == {"S_VIEW": 2, "S_LINK": 2, "S_POSS": 2}  # S_VIEW >= S_LINK >= S_POSS, equal on one camera


@pytest.mark.determinism
def test_s5_rows_match_the_schema():
    from rq1.events import candidates
    from rq1.schema import validate
    _, s4, _, s1 = s4_for("N2-G3")
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    episodes, _ = engine.run_pow(flags, PARAMS)
    rows = engine.flag_series_rows("pow_" + "a" * 26, flags)
    assert len(rows) == 10 and validate.validate_rows("flag_series", rows) == []
    assert [r["T"] for r in rows] == [1] * 10 and all(r["T"] == 1 and r["C_any"] == 1 for r in rows)  # T = P or X or C_any
    eps = [{**ep, "pow_id": "pow_" + "a" * 26, "camera_id": "cam_" + "a" * 26, "recording_id": "rec_x", "timeline_id": "tl_x"} for ep in episodes]
    events = candidates.candidate_events(eps)
    assert validate.validate_rows("candidate_event", events) == []
    assert validate.validate_rows("event_count_summary", candidates.count_summaries(events, eps, [("recording", "rec_x")])) == []


def test_t9_schema_fields():
    # T9.4 e_assessed, T9.5 ca_observed (episode); T9.3 k_c_turn (rule_configuration.classification). AR-38 item 6.
    from rq1.schema import registry
    episode = {f.name: f for f in registry.TABLES["episode"].fields}
    assert episode["e_assessed"].type.kind == "bool" and not episode["e_assessed"].nullable
    assert episode["ca_observed"].type.kind == "bool" and not episode["ca_observed"].nullable
    classification = next(f for f in registry.TABLES["rule_configuration"].fields if f.name == "classification")
    assert {f.name: f.type.kind for f in classification.type.fields}["k_c_turn"] == "f64"
