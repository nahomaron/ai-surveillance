"""D-58 STEP 4: split mechanisms on events, the S5 configurations of the two event definitions, and the two pair readings
of CR-037 item 3 (hand-made inputs; expected values by hand beside each assertion)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d58_events as de  # noqa: E402
import pilot_common as pc  # noqa: E402


def _ev(first_pow, last_pow, first_units=("p", "f"), last_units=("p", "f")):
    return {"first": {"pow_id": first_pow, "units": first_units}, "last": {"pow_id": last_pow, "units": last_units}}


def test_split_mechanism_on_event_boundaries():
    assert de.split_mechanism(_ev("pow_1", "pow_1"), _ev("pow_1", "pow_2")) == "i"  # a's last member and b's first share a POW
    assert de.split_mechanism(_ev("pow_1", "pow_1"), _ev("pow_2", "pow_2")) == "ii"  # other POW, same units
    assert de.split_mechanism(_ev("pow_1", "pow_1"), _ev("pow_2", "pow_2", first_units=("q", "f"))) == "iii"


def test_s5_configurations():
    ctx = pc.m.Context("sdg")
    alpha = de.s5_config(ctx, "alpha", False)
    assert alpha.version_label == "preregistration-v1" and alpha.m_gap_s is None and alpha.join_across_pow is None  # the stored v1 BL-6
    a_join = de.s5_config(ctx, "alpha", True)
    assert a_join.m_gap_s is None and a_join.join_across_pow is True and "not frozen" in a_join.version_label
    beta = de.s5_config(ctx, "beta", False)
    assert beta.m_gap_s == 1.0 and beta.join_across_pow is None
    assert de.s5_config(ctx, "beta", True).join_across_pow is True
    assert de.BETA_M_GAP_S == 1.0 and "not the v2 reference" in de.BETA_REF_LABEL


def _episode(pow_id, start, ca, minclr):
    return {"pow_id": pow_id, "start_frame": start, "closest_approach_frame": ca, "minclr_m": minclr}


def test_pair_readings_a_and_b():
    s4 = {"pow": [{"pow_id": "pow_1", "person_track_id": "u_p", "forklift_track_id": "u_f"},
                  {"pow_id": "pow_2", "person_track_id": "u_p", "forklift_track_id": "u_f"}]}
    e1, e2 = _episode("pow_1", 0, 5, 1.2), _episode("pow_2", 40, 45, 0.8)
    s5 = {"episode": [e1, e2], "candidate_event": [{"scenario": "S_VIEW", "evt_id": "evt_x", "member_episode_nks": [["pow_1", 0], ["pow_2", 40]],
                                                   "t_onset_tl_s": 0.0, "t_end_tl_s": 5.0, "unobserved_gap_s": 0.5, "n_members": 2,
                                                   **{f"lbl_{x}": x == "H" for x in de.LABELS}}]}
    # Hand pair function: the first member resolves to (P1, F1), the second to (P2, F1).
    pair_of = lambda ep: ("P1", "F1") if ep["pow_id"] == "pow_1" else ("P2", "F1")
    ev = de.event_rows(s4, s5, pair_of)[0]
    assert ev["pair"]["a"] == ("P2", "F1")  # (a): the closest-approach member is the one with the lower minclr (0.8)
    assert ev["pair"]["b"] is None  # (b): the members disagree, so the pair is unknown
    assert ev["n_members"] == 2 and ev["first"]["pow_id"] == "pow_1" and ev["last"]["pow_id"] == "pow_2"
    agree = de.event_rows(s4, s5, lambda ep: ("P1", "F1"))[0]
    assert agree["pair"] == {"a": ("P1", "F1"), "b": ("P1", "F1")}
