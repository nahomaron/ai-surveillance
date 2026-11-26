"""Appendix T T25.2 and T25.3 (E-1.2.26; D-58): episode continuity across POW breaks, and m_gap in seconds.

Every T25.4 check for T25.2 and T25.3 is a test. Expected values are the T25.4 values or hand calculations written beside
each assertion. S5-level cases use a synthetic 10 fps S1 (frame k starts at k * 0.1 s), a person at (0, 1.9) and a
stationary forklift at (0, 0): clearance 1.9 - 0.3 - 0.5 = 1.1 m < d_p 2.0, so P = 1 and T = 1 on every pair frame, and
every POW is one episode. The forklift has no point on the frames of `gap`; with g_max 3 the POW breaks there.
"""
import dataclasses

import pytest

from rq1.events import candidates, engine, s5
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema import validate, vr_rules
from rq1.substrate import builder, oracle

from test_engine_part_a import FORK, PARAMS, PERSON, RULES

BANDS = {"bsc_" + "a" * 26: [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]}
SUBSTRATE = {"g_max": 3, "pair_classes": ["forklift"], "v_min": 0.3, "k_sup": 1.5, "motion_models": ["constant_velocity"],
             "prediction_horizon_s": 2.0, "version_label": "TEST-ONLY", "version_label_null_reason": None}


# ------------------------------------------------------------------------------------------------------------- T25.3

def test_t25_3_m_gap_seconds_to_frames():
    assert engine.m_gap_frames(1.0, 1 / 30) == 30  # 1.0 / (1/30) = 29.999999999999996 without the 1e-9 term
    assert engine.m_gap_frames(1.0, 0.1) == 10
    assert engine.m_gap_frames(0.25, 0.1) == 2  # floor(2.5)


def test_t25_3_m_gap_s_must_be_positive():
    from rq1.schema.errors import ContractError
    with pytest.raises(ContractError):
        engine.m_gap_frames(0.0, 0.1)


# ----------------------------------------------------------------------------------------------- S5-level T25.2 cases

def _s1(n, delta=0.1, **kw):
    s1 = synthetic_s1.build(n, dt=delta, **kw)
    s1["decode_summary"][0]["delta_nom_s"] = delta
    return s1


def _s4(s1, n, gap):
    truth = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [100.0, 100.0, 140.0, 200.0], "state": "tracked"} for i in range(n)]},
             {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"}
                                                             for i in range(n) if i not in gap]}]
    positions = {**{(1, i): {"xy": [0.0, 1.9], "cov": [0.0025, 0.0, 0.0025]} for i in range(n)},
                 **{(2, i): {"xy": [0.0, 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(n) if i not in gap}}
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.26", "f", "f", ("orc_" + "a" * 26,), (), {}))
    cfg = builder.SubstrateConfig(3, 0.3, 0.5, 2.0, {"forklift"}, {"person": PERSON, "forklift": FORK}, {"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                  BANDS, 0.5)
    return builder.SubstrateBuilder().build(s1, s3, positions, None, cfg,
                                            Spec("S4", "E-1.2.26", "f", "f", ("gcf_" + "a" * 26, s5.substrate_config_id(SUBSTRATE)), (s3.artifact_id,), {}))


def _cfg(**kw):
    return s5.S5Config(RULES, PARAMS, SUBSTRATE, "bsc_" + "a" * 26, version_label="TEST-ONLY", **kw)


def _s5(s1, s4, cfg):
    return s5.build(s1, s4, cfg, Spec("S5", "E-1.2.26", "f", "f", (s5.config_id(cfg),), (s4.artifact_id,), {}))


def _view(art):
    return [e for e in art.tables["candidate_event"] if e["scenario"] == "S_VIEW"]


def test_t25_2_gap_0_6_joined_into_one_event():
    s1 = _s1(40)
    s4 = _s4(s1, 40, range(15, 21))  # POW 0-15 (t 0-1.5), POW 21-40 (t 2.1-4.0): gap 0.6 s
    art = _s5(s1, s4, _cfg(m_gap_s=1.0, join_across_pow=True))
    assert len(s4.tables["pow"]) == 2
    eps = sorted(art.tables["episode"], key=lambda e: e["start_frame"])
    assert [(e["start_frame"], e["end_frame_excl"]) for e in eps] == [(0, 15), (21, 40)]
    view = _view(art)
    assert len(view) == 1
    ev = view[0]
    assert ev["n_members"] == 2
    assert ev["unobserved_gap_s"] == pytest.approx(0.6, abs=1e-9)
    assert ev["member_episode_nks"] == [[eps[0]["pow_id"], 0], [eps[1]["pow_id"], 21]]
    assert (ev["t_onset_tl_s"], ev["t_end_tl_s"]) == (pytest.approx(0.0), pytest.approx(4.0))
    assert ev["edges_used"] == [] and ev["ambiguous"] is False
    # One candidate_event per scenario (single camera: S_VIEW = S_LINK = S_POSS).
    assert sorted(e["scenario"] for e in art.tables["candidate_event"]) == ["S_LINK", "S_POSS", "S_VIEW"]
    links = art.tables["event_link"]
    assert len(links) == 1 and links[0]["basis"] == ["same_camera"] and links[0]["linkage_version"] == candidates.CONTINUITY_VERSION
    assert sorted([links[0]["episode_a_nk"], links[0]["episode_b_nk"]]) == sorted([[eps[0]["pow_id"], 0], [eps[1]["pow_id"], 21]])
    for table, rows in art.tables.items():
        assert all(validate.validate_row(table, r) == [] for r in rows), table
        assert vr_rules.check_ids(table, rows, art.artifact_id) == []
    assert all(vr_rules.check_event_labels(e) == [] for e in art.tables["candidate_event"])
    # Episodes are unchanged by the join (record IDs are artifact-scoped and differ with the configuration).
    plain = _s5(s1, s4, _cfg(m_gap_s=1.0))
    content = lambda a: [{k: v for k, v in e.items() if not k.endswith(("_id", "_ids")) or k in ("pow_id", "recording_id", "camera_id", "timeline_id")} for e in a.tables["episode"]]
    assert content(art) == content(plain)


def test_t25_2_gap_1_4_gives_two_events():
    s1 = _s1(50)
    s4 = _s4(s1, 50, range(15, 29))  # e2 starts at 2.9 s: gap 1.4 s > 1.0 s
    view = _view(_s5(s1, s4, _cfg(m_gap_s=1.0, join_across_pow=True)))
    assert len(view) == 2 and [e["n_members"] for e in view] == [1, 1] and [e["unobserved_gap_s"] for e in view] == [0.0, 0.0]


def test_t25_2_coverage_break_in_the_gap_blocks_the_join():
    s1 = _s1(40, dropouts={17: 0.2})  # gap_unobserved 0.2 s after frame 17; e2 starts at 2.3 s: gap 0.8 s <= 1.0 s
    s4 = _s4(s1, 40, range(15, 21))
    assert len(_view(_s5(s1, s4, _cfg(m_gap_s=1.0, join_across_pow=True)))) == 2


def test_t25_2_without_m_gap_s_uses_m_gap_frames_times_delta_nom():
    s1 = _s1(40)
    s4 = _s4(s1, 40, range(15, 21))
    # m_gap 5 frames x 0.1 s = 0.5 s < 0.6 s: not joined; m_gap 6 frames = 0.6 s: joined (<=).
    assert len(_view(_s5(s1, s4, _cfg(join_across_pow=True)))) == 2
    six = s5.S5Config(RULES, dataclasses.replace(PARAMS, m_gap=6), SUBSTRATE, "bsc_" + "a" * 26, version_label="TEST-ONLY", join_across_pow=True)
    assert [e["n_members"] for e in _view(_s5(s1, s4, six))] == [2]


def test_t25_2_false_or_absent_is_off():
    s1 = _s1(40)
    s4 = _s4(s1, 40, range(15, 21))
    off = _s5(s1, s4, _cfg(m_gap_s=1.0))
    false = _s5(s1, s4, _cfg(m_gap_s=1.0, join_across_pow=False))
    assert len(_view(off)) == 2 and "event_link" not in off.tables
    assert not any("n_members" in e or "unobserved_gap_s" in e for e in off.tables["candidate_event"])
    # False is present in the record (a different configuration ID, so other record IDs), but the rule is off.
    strip = lambda art: [{k: v for k, v in e.items() if not k.endswith(("_id", "_ids"))} for e in art.tables["candidate_event"]]
    assert strip(false) == strip(off) and "event_link" not in false.tables


# --------------------------------------------------------------------------------------------- T25.0 regression

def test_t25_0_rule_configuration_unchanged_without_parameters():
    base = s5.S5Config(RULES, PARAMS, SUBSTRATE, "bsc_" + "a" * 26, version_label="TEST-ONLY")
    record = s5.rule_configuration(base)
    assert record["lifecycle"] == {"m_gap_frames": PARAMS.m_gap, "t_min_s": PARAMS.t_min, "w_post_s": PARAMS.w_post}
    on = s5.rule_configuration(_cfg(m_gap_s=1.0, join_across_pow=True))
    assert on["lifecycle"] == {"m_gap_frames": PARAMS.m_gap, "t_min_s": PARAMS.t_min, "w_post_s": PARAMS.w_post, "m_gap_s": 1.0, "join_across_pow": True}
    assert s5.config_id(_cfg(m_gap_s=1.0)) not in (s5.config_id(base), s5.config_id(_cfg(m_gap_s=1.0, join_across_pow=True)))


def test_t25_0_s5_artifact_unchanged_without_parameters():
    s1 = _s1(40)
    s4 = _s4(s1, 40, range(15, 21))
    a = _s5(s1, s4, s5.S5Config(RULES, PARAMS, SUBSTRATE, "bsc_" + "a" * 26, version_label="TEST-ONLY"))
    b = _s5(s1, s4, _cfg(m_gap_s=None, join_across_pow=None))
    assert a.artifact_id == b.artifact_id and a.payload_sha256 == b.payload_sha256


def test_t25_3_m_gap_s_sets_the_lifecycle_bridge():
    # Pure engine check: T = 1, 1, then 8 frames of T = 0, then T = 1 (10 fps). m_gap_s 1.0 -> 10 frames: bridged;
    # m_gap 5 frames: two windows.
    frames = [engine.FrameFlags(i, i / 10, 0.1, P=1 if i in (0, 1, 10, 11) else 0, M=0, C_by={"R3": 0}, clearance=1.0) for i in range(12)]
    p10 = dataclasses.replace(PARAMS, m_gap=engine.m_gap_frames(1.0, 0.1))
    assert len(engine.run_pow([dataclasses.replace(f) for f in frames], p10)[0]) == 1
    assert len(engine.run_pow([dataclasses.replace(f) for f in frames], PARAMS)[0]) == 2


# ----------------------------------------------------------------------------------------------- pure T25.2 rules

def _pow(pid, start, end, person="p1", fork="f1", tl="tl", cam="cam"):
    return {"pow_id": pid, "person_track_id": person, "forklift_track_id": fork, "timeline_id": tl, "camera_id": cam, "start_frame": start,
            "end_frame_excl": end}


def _ep(pid, start, end, **kw):
    row = {"pow_id": pid, "start_frame": start, "end_frame_excl": end, "t_start_tl_s": start / 10, "t_end_tl_s": end / 10, "camera_id": "cam",
           "P_ep": True, "X_ep": False, "C_ep": False, "E_ep": 0, "K": 0, "minclr_m": 1.5, "contact_state": "none_observed", "lbl_IE": False,
           "closest_approach_frame": start}
    row.update(kw)
    return row


def _t(pows, ones=()):
    return {p["pow_id"]: {i: (1 if (p["pow_id"], i) in ones else 0) for i in range(p["start_frame"], p["end_frame_excl"])} for p in pows}


def _chains(eps, pows, ones=(), coverage=(), gap=1.0):
    return candidates.join_chains(eps, {p["pow_id"]: p for p in pows}, _t(pows, ones), list(coverage), gap)


def test_t25_2_t1_frame_in_the_gap_blocks_the_join():
    pows = [_pow("pow_a", 0, 14), _pow("pow_b", 16, 30)]
    eps = [_ep("pow_a", 0, 10), _ep("pow_b", 16, 30)]
    assert [len(c) for c in _chains(eps, pows)] == [2]  # gap 0.6 s, no T = 1 frame in it
    assert [len(c) for c in _chains(eps, pows, ones={("pow_a", 12)})] == [1, 1]  # frame 12 of pow_a: T = 1 (a discarded blip)


def test_t25_2_same_pow_is_never_joined():
    pows = [_pow("pow_a", 0, 30)]
    assert [len(c) for c in _chains([_ep("pow_a", 0, 10), _ep("pow_a", 16, 30)], pows)] == [1, 1]


def test_t25_2_other_pair_or_camera_is_not_joined():
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 16, 30, person="p2"), _pow("pow_c", 16, 30, cam="cam2")]
    eps = [_ep("pow_a", 0, 10), _ep("pow_b", 16, 30), _ep("pow_c", 16, 30)]
    assert [len(c) for c in _chains(eps, pows)] == [1, 1, 1]


def test_t25_2_joins_chain():
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 15, 25), _pow("pow_c", 30, 40)]
    eps = [_ep("pow_a", 0, 10), _ep("pow_b", 15, 25), _ep("pow_c", 30, 40)]
    chains = _chains(eps, pows)
    assert [[e["pow_id"] for e in c] for c in chains] == [["pow_a", "pow_b", "pow_c"]]
    ev = candidates.joined_events(chains, d_nm=0.5)
    assert {e["scenario"] for e in ev} == {"S_VIEW", "S_LINK", "S_POSS"}
    view = next(e for e in ev if e["scenario"] == "S_VIEW")
    assert view["n_members"] == 3 and view["unobserved_gap_s"] == pytest.approx(1.0, abs=1e-12)  # 0.5 + 0.5
    assert len(candidates.continuity_links(chains)) == 2


def test_t25_2_labels_are_recomputed_over_members_not_unioned():
    # CT-E-17 at event level: O in one member, H in the other -> the event is H only.
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 15, 25)]
    eps = [_ep("pow_a", 0, 10), _ep("pow_b", 15, 25, X_ep=True)]
    view = next(e for e in candidates.joined_events(_chains(eps, pows), d_nm=0.5) if e["scenario"] == "S_VIEW")
    assert (view["lbl_O"], view["lbl_H"], view["X_ev"], view["P_ev"]) == (False, True, True, True)
    assert vr_rules.check_event_labels(view) == []


def test_t25_2_event_flags_over_members():
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 15, 25)]
    eps = [_ep("pow_a", 0, 10, minclr_m=1.2, E_ep=2, X_ep=True), _ep("pow_b", 15, 25, minclr_m=0.4, E_ep=0, X_ep=True, contact_state="undetermined")]
    view = next(e for e in candidates.joined_events(_chains(eps, pows), d_nm=0.5) if e["scenario"] == "S_VIEW")
    assert view["minclr_ev_m"] == 0.4 and view["E_ev"] == 2  # min over members; Kleene OR of 2 and 0
    assert view["K_ev"] == 1  # K = E or (minclr < d_nm) = unknown or true = true (recomputed, not taken from a member)
    # CR-037 primary reading: contact state and IE from the member holding the event's lowest measured clearance.
    assert view["contact_state_ev"] == "undetermined" and view["lbl_UD"] and not view["lbl_NM"]
    assert vr_rules.check_event_labels(view) == []


def test_t25_2_gap_boundary_is_inclusive():
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 20, 30)]
    eps = [_ep("pow_a", 0, 10), _ep("pow_b", 20, 30)]
    assert [len(c) for c in _chains(eps, pows, gap=1.0)] == [2]  # gap 1.0 s <= 1.0 s
    assert [len(c) for c in _chains(eps, pows, gap=0.9)] == [1, 1]


def test_t25_2_chain_order_is_by_time_and_input_order_free():
    pows = [_pow("pow_a", 0, 10), _pow("pow_b", 15, 25)]
    eps = [_ep("pow_b", 15, 25), _ep("pow_a", 0, 10)]
    assert [[e["pow_id"] for e in c] for c in _chains(eps, pows)] == [["pow_a", "pow_b"]]
