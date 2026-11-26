"""Appendix T T25.1 (E-1.2.26; D-58): track stitching, and S4 pairs formed from stitched identities (T25.1 e).

Every T25.4 check for T25.1 is a test. Expected values are the T25.4 values or hand calculations written beside each
assertion. Frames are 10 fps (synthetic S1: frame k starts at k * 0.1 s).
"""
import dataclasses

import pytest

from rq1.fixtures import synthetic_s1
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.schema.errors import ContractError
from rq1.tracking import s3_config, stitching

from test_part_b import FORK, PERSON, S3_SPEC, build_s4, config, s4_spec

P = stitching.StitchParams(max_gap_s=2.0, v_max_mps={"person": 2.5, "forklift": 3.0}, r_gate_m=1.0, img_gate=2.5)
BOX = [100.0, 100.0, 140.0, 200.0]


def s1_frames(n=60, **kw):
    s1 = synthetic_s1.build(n, **kw)
    return s1, {f["frame_index"]: f for f in s1["frame"] if f["eligible"]}


def trk(tid, cls, frames, state="tracked", box=BOX):
    return stitching.Track(tid, cls, [(i, state, list(box)) for i in frames])


def links(tracks, floor=None, params=P, n=60, **kw):
    s1, frames = s1_frames(n, **kw)
    return stitching.links(tracks, frames, s1["coverage_segment"], params, floor or {})


# ------------------------------------------------------------------------------------------------------- T25.4 T25.1

def test_t25_1_stitched_with_cost_half():
    # A ends at frame 10 (t 1.0 s), B starts at frame 20 (t 2.0 s): 1.0 s apart; floor distance 2.0 m.
    a, b = trk("trk_a", "forklift", range(0, 11)), trk("trk_b", "forklift", range(20, 30))
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b", 20): (2.0, 0.0)}
    out = links([a, b], floor)
    assert [(x["a"], x["b"]) for x in out] == [("trk_a", "trk_b")]
    assert out[0]["gate"] == "floor"
    assert out[0]["cost"] == pytest.approx(0.5, abs=1e-12)  # 2.0 / (3 * 1.0 + 1.0)
    assert out[0]["dt_s"] == pytest.approx(1.0, abs=1e-9)


def test_t25_1_not_stitched_outside_the_floor_gate():
    # 0.5 s apart (frames 10 -> 15), 3.0 m apart: gate 3 * 0.5 + 1.0 = 2.5 m < 3.0 m.
    a, b = trk("trk_a", "forklift", range(0, 11)), trk("trk_b", "forklift", range(15, 30))
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b", 15): (3.0, 0.0)}
    assert links([a, b], floor) == []


def test_t25_1_lower_cost_wins_for_one_b():
    a1, a2 = trk("trk_a1", "forklift", range(0, 11)), trk("trk_a2", "forklift", range(2, 11))
    b = trk("trk_b", "forklift", range(20, 30))
    # a1 -> b: 2.0 / 4.0 = 0.5; a2 -> b: 1.0 / 4.0 = 0.25 (both end at frame 10, 1.0 s before b).
    floor = {("trk_a1", 10): (0.0, 0.0), ("trk_a2", 10): (1.0, 0.0), ("trk_b", 20): (2.0, 0.0)}
    out = links([a1, a2, b], floor)
    assert [(x["a"], x["b"]) for x in out] == [("trk_a2", "trk_b")]
    assert out[0]["cost"] == pytest.approx(0.25, abs=1e-12)


def test_t25_1_overlapping_tracks_are_never_stitched():
    a, b = trk("trk_a", "forklift", range(0, 21)), trk("trk_b", "forklift", range(15, 30))
    floor = {("trk_a", 20): (0.0, 0.0), ("trk_b", 15): (0.1, 0.0)}
    assert links([a, b], floor) == []


def test_t25_1_a_coverage_break_blocks_the_link():
    # A gap_unobserved segment of 0.2 s after frame 14 lies between A's end (frame 10) and B's start (frame 20).
    a, b = trk("trk_a", "forklift", range(0, 11)), trk("trk_b", "forklift", range(20, 30))
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b", 20): (0.5, 0.0)}
    assert links([a, b], floor, dropouts={14: 0.2}) == []
    assert len(links([a, b], floor)) == 1  # the same tracks without the break are linked


def test_t25_1_image_gate_hand_value():
    # No floor positions. A's last box [0, 0, 30, 40] (centre (15, 20), diagonal 50); B's first box [60, 80, 90, 120]
    # (centre (75, 100), diagonal 50). Centre distance sqrt(60^2 + 80^2) = 100; k_img 2.5: gate 125, cost 100 / 125 = 0.8.
    a = trk("trk_a", "person", range(0, 11), box=[0.0, 0.0, 30.0, 40.0])
    b = trk("trk_b", "person", range(20, 30), box=[60.0, 80.0, 90.0, 120.0])
    out = links([a, b])
    assert [(x["a"], x["b"], x["gate"]) for x in out] == [("trk_a", "trk_b", "image")]
    assert out[0]["cost"] == pytest.approx(0.8, abs=1e-12)
    tight = stitching.StitchParams(2.0, {"person": 2.5, "forklift": 3.0}, 1.0, 1.5)  # gate 75 < 100
    assert links([a, b], params=tight) == []


def test_t25_1_image_gate_when_only_one_endpoint_has_a_floor_position():
    a = trk("trk_a", "person", range(0, 11), box=[0.0, 0.0, 30.0, 40.0])
    b = trk("trk_b", "person", range(20, 30), box=[60.0, 80.0, 90.0, 120.0])
    out = links([a, b], {("trk_a", 10): (0.0, 0.0)})
    assert out[0]["gate"] == "image" and out[0]["cost"] == pytest.approx(0.8, abs=1e-12)


# ----------------------------------------------------------------------------------------------- T25.1 (b), (d) rules

def test_t25_1_gap_longer_than_t_s_is_not_a_candidate():
    a, b = trk("trk_a", "forklift", range(0, 11)), trk("trk_b", "forklift", range(32, 40))  # 2.2 s > T_s 2.0
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b", 32): (0.0, 0.0)}
    assert links([a, b], floor) == []
    c = trk("trk_c", "forklift", range(30, 40))  # exactly 2.0 s: a candidate (<= T_s)
    assert len(links([a, c], {**floor, ("trk_c", 30): (0.0, 0.0)})) == 1


def test_t25_1_classes_must_match():
    a, b = trk("trk_a", "person", range(0, 11)), trk("trk_b", "forklift", range(20, 30))
    assert links([a, b], {("trk_a", 10): (0.0, 0.0), ("trk_b", 20): (0.0, 0.0)}) == []


def test_t25_1_endpoints_are_tracked_points():
    # A's last point is `predicted` (frame 12): t_A is its last `tracked` point (frame 10), and a point of A in state
    # `predicted` lies after t_A, so (A, B) is no candidate (T25.1 b).
    a = stitching.Track("trk_a", "forklift", [(i, "tracked", BOX) for i in range(11)] + [(12, "predicted", BOX)])
    b = trk("trk_b", "forklift", range(20, 30))
    assert links([a, b], {("trk_a", 10): (0.0, 0.0), ("trk_b", 20): (0.0, 0.0)}) == []


def test_t25_1_links_form_chains_and_one_successor_each():
    a, b, c = trk("trk_a", "forklift", range(0, 11)), trk("trk_b", "forklift", range(20, 31)), trk("trk_c", "forklift", range(40, 50))
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b", 20): (1.0, 0.0), ("trk_b", 30): (1.0, 0.0), ("trk_c", 40): (2.0, 0.0)}
    out = links([a, b, c], floor)
    assert [(x["a"], x["b"]) for x in out] == [("trk_a", "trk_b"), ("trk_b", "trk_c")]
    # a -> c is also a candidate (3.0 s > T_s 2.0: it is not); every track has at most one successor and predecessor.
    chains = stitching.chains(["trk_a", "trk_b", "trk_c"], out)
    assert chains == [["trk_a", "trk_b", "trk_c"]]


def test_t25_1_equal_cost_tie_breaks_on_gap_then_jcs():
    a = trk("trk_a", "forklift", range(0, 11))
    b1, b2 = trk("trk_b1", "forklift", range(20, 30)), trk("trk_b2", "forklift", range(20, 30))
    floor = {("trk_a", 10): (0.0, 0.0), ("trk_b1", 20): (1.0, 0.0), ("trk_b2", 20): (1.0, 0.0)}
    out = links([b2, a, b1], floor)  # input order does not matter
    assert [(x["a"], x["b"]) for x in out] == [("trk_a", "trk_b1")]  # equal cost and gap: JCS of [a, b] decides


def test_t25_1_stitch_id_is_content_addressed_from_member_ids():
    ids = stitching.stitch_ids([["trk_a", "trk_b"], ["trk_c"]])
    assert ids["trk_a"] == ids["trk_b"] == core.make_id("sti", ["trk_a", "trk_b"])
    assert ids["trk_c"] == core.make_id("sti", ["trk_c"]) != ids["trk_a"]


# ----------------------------------------------------------------------------------------------------- T25.1 (a) params

def test_t25_1_parameters_all_or_none():
    assert stitching.params_from({}) is None
    full = {"stitch_max_gap_s": 2.0, "stitch_v_max_mps": {"person": 2.5, "forklift": 4.0}, "stitch_r_gate_m": 1.0, "stitch_img_gate": 1.0}
    assert stitching.params_from(full) == stitching.StitchParams(2.0, {"person": 2.5, "forklift": 4.0}, 1.0, 1.0)
    for name in full:
        with pytest.raises(ContractError):
            stitching.params_from({k: v for k, v in full.items() if k != name})


@pytest.mark.parametrize("bad", [{"stitch_max_gap_s": 0.0}, {"stitch_r_gate_m": -0.1}, {"stitch_img_gate": 0.0},
                                 {"stitch_v_max_mps": {"person": 0.0, "forklift": 4.0}}])
def test_t25_1_parameter_ranges(bad):
    full = {"stitch_max_gap_s": 2.0, "stitch_v_max_mps": {"person": 2.5, "forklift": 4.0}, "stitch_r_gate_m": 1.0, "stitch_img_gate": 1.0}
    with pytest.raises(ContractError):
        stitching.params_from({**full, **bad})


def test_t25_0_trc_id_unchanged_without_stitching():
    cfg = {"library": "x"}
    assert s3_config.trc_id(cfg, 15) == s3_config.trc_id(cfg, 15, stitch=None)
    on = s3_config.trc_id(cfg, 15, stitch=P)
    assert on != s3_config.trc_id(cfg, 15)


# ------------------------------------------------------------------------------- T25.1 (e): S3 stitch_id and S4 pairs

def _two_fork_tracks(n=60, gap=range(20, 30)):
    person = {"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": BOX, "state": "tracked"} for i in range(n)]}
    f1 = {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"} for i in range(gap.start)]}
    f2 = {"local_id": 3, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"} for i in range(gap.stop, n)]}
    return [person, f1, f2]


def _positions(n=60):
    out = {(1, i): {"xy": [0.0, 1.9], "cov": [0.0025, 0.0, 0.0025]} for i in range(n)}
    out.update({(k, i): {"xy": [0.0, 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for k in (2, 3) for i in range(n)})
    return out


def _stitched_s3(s1, truth):
    from rq1.substrate import oracle
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], S3_SPEC)
    trk_of = {t["track_local_id"]: t["trk_id"] for t in s3.tables["track"]}
    sid = stitching.stitch_ids([[trk_of[1]], [trk_of[2], trk_of[3]]], stitching.natural_keys(s3.tables))
    spec = Spec("S3", "E-1.2.26", "f", "f", (s3_config.trc_id({"library": "x"}, 15, stitch=P),), (), {})
    return s3, stitching.apply(s3, sid, spec), sid, trk_of


def test_t25_1_e_points_keep_track_ids_and_carry_stitch_id():
    s1 = synthetic_s1.build(60)
    s3, st, sid, trk_of = _stitched_s3(s1, _two_fork_tracks())
    rec = s1["frame"][0]["recording_id"]
    assert sid[trk_of[2]] == sid[trk_of[3]] == core.make_id("sti", [[rec, 2], [rec, 3]])  # from member natural keys
    assert [{k: v for k, v in t.items() if k != "trk_id"} for t in st.tables["track"]] == [{k: v for k, v in t.items() if k != "trk_id"} for t in s3.tables["track"]]
    before = {(p["track_nk"][1], p["frame_index"]): p for p in s3.tables["track_point"]}
    for p in st.tables["track_point"]:
        # The track natural key is kept; `tpt_id` and the derived `track_id` are artifact-scoped (section 2.3) and change with
        # the new S3 artifact (AR-69 item 1).
        scoped = ("stitch_id", "tpt_id", "track_id")
        assert {k: v for k, v in p.items() if k not in scoped} == {k: v for k, v in before[(p["track_nk"][1], p["frame_index"])].items() if k not in scoped}
        assert p["stitch_id"] == sid[trk_of[p["track_nk"][1]]]
    assert len(st.tables["track_point"]) == len(s3.tables["track_point"])  # no point created or imputed


def test_t25_1_e_s4_pairs_are_formed_from_stitched_identities():
    from rq1.substrate import builder
    s1 = synthetic_s1.build(60)
    s3, st, sid, trk_of = _stitched_s3(s1, _two_fork_tracks())
    plain = builder.SubstrateBuilder().build(s1, s3, _positions(), None, config(g_max=3), s4_spec(inputs=(s3.artifact_id,)))
    joined = builder.SubstrateBuilder().build(s1, st, _positions(), None, config(g_max=3), s4_spec(inputs=(st.artifact_id,)))
    # Without stitching: one POW per (person, forklift track), 0-20 and 30-60.
    assert sorted((p["forklift_track_id"], p["start_frame"], p["end_frame_excl"]) for p in plain.tables["pow"]) == \
        sorted([(trk_of[2], 0, 20), (trk_of[3], 30, 60)])
    # With stitching: both POWs belong to the one stitched forklift identity. The 10-frame gap exceeds g_max 3, so the POW
    # breaks there (T8.1 unchanged) and the second POW continues the first.
    pows = sorted(joined.tables["pow"], key=lambda p: p["start_frame"])
    assert [(p["person_track_id"], p["forklift_track_id"], p["start_frame"], p["end_frame_excl"], p["end_reason"]) for p in pows] == [
        (sid[trk_of[1]], sid[trk_of[2]], 0, 20, "gap_exceeded"), (sid[trk_of[1]], sid[trk_of[2]], 30, 60, "recording_end")]
    assert pows[1]["continuation_of_nk"] == [sid[trk_of[1]], sid[trk_of[2]], 0]
    # Object states stay per original track and are identical; pair-series values are those of the member tracks.
    local = lambda art, s3a: {t["trk_id"]: t["track_local_id"] for t in s3a.tables["track"]}
    states = lambda art, s3a: sorted((local(art, s3a)[r["track_id"]], r["frame_index"], tuple((k, str(v)) for k, v in sorted(r.items()) if k not in ("track_id", "ost_id")))
                                     for r in art.tables["object_state"])
    assert states(joined, st) == states(plain, s3)
    clear = lambda art: sorted((r["frame_index"], r["clearance_m"]) for r in art.tables["pair_series"])
    assert clear(joined) == clear(plain)


def test_t25_1_e_bridged_gap_between_members_follows_t8_1():
    from rq1.substrate import builder
    s1 = synthetic_s1.build(60)
    s3, st, sid, trk_of = _stitched_s3(s1, _two_fork_tracks(gap=range(20, 23)))  # 3 frames <= g_max 3: bridged
    joined = builder.SubstrateBuilder().build(s1, st, _positions(), None, config(g_max=3), s4_spec(inputs=(st.artifact_id,)))
    assert [(p["start_frame"], p["end_frame_excl"], p["bridged_gaps"]) for p in joined.tables["pow"]] == [(0, 60, [{"start_frame": 20, "end_frame_excl": 23}])]
    assert not any(r["frame_index"] in (20, 21, 22) and r["clearance_m"] is not None for r in joined.tables["pair_series"])  # nothing imputed


def test_t25_1_e_every_point_or_none_carries_stitch_id():
    from rq1.substrate import builder
    s1 = synthetic_s1.build(60)
    s3, st, sid, trk_of = _stitched_s3(s1, _two_fork_tracks())
    broken = dataclasses.replace(st, tables={**st.tables, "track_point": [dict(p) for p in st.tables["track_point"]]})
    broken.tables["track_point"][0].pop("stitch_id")
    with pytest.raises(ContractError):
        builder.SubstrateBuilder().build(s1, broken, _positions(), None, config(g_max=3), s4_spec(inputs=(st.artifact_id,)))


def test_t25_1_f_off_for_oracle_tracks():
    with pytest.raises(ContractError):
        stitching.require_non_oracle("orc_" + "a" * 26)
    stitching.require_non_oracle("trc_" + "a" * 26)
