"""CR-042 (Architect ruling, Owner decision D-65, 27 Nov 2026): on stitched identities, M, R4, R5 and the contact cue read
each member track's stored S4 state for its own frames; nothing is combined or recomputed across a stitch gap (T8.1).

Construction (synthetic S1, 10 fps): person track 1 on frames 0-59 standing at (0, 1.9); forklift track 2 on frames 0-19
moving +x at 1.0 m/s (0.1 m per frame), forklift track 3 on frames 20-59 (adjacent: no frame between the members) moving
+x at 0.5 m/s. Tracks 2 and 3 form one stitched identity. Expected values by construction: every per-frame provider input
of the stitched pair equals the one the same frame gets on the unstitched pair (person, member track); in particular a
rate window at the boundary frame 19 / 20 never mixes the two members (a mixed window would show forklift
deceleration from 1.0 to 0.5 m/s; per member it shows none).
"""
import dataclasses

from rq1.events import providers, s5
from rq1.fixtures import synthetic_s1
from rq1.substrate import builder

from test_part_b import config, s4_spec
from test_t25_stitching import _stitched_s3

RULES = providers.RuleParams(p_provider="R2", k_img=0.05, d_p=3.0, v_min=0.3, d_pc=1.0, ttc_max=1.5, pet_max=1.5, tau=2.0,
                             conflict=("R3", "R4"), r5=True, w_e=1.0, e_turn=1.5, e_acc=1.0, e_dec=1.0, k_sigma=2.0)
BOX = [100.0, 100.0, 140.0, 200.0]
FBOX = [300.0, 100.0, 500.0, 220.0]


def _truth(n=60, split=20):
    pts = lambda frames, box: [{"frame_index": i, "bbox": box, "state": "tracked"} for i in frames]
    return [{"local_id": 1, "class": "person", "points": pts(range(n), BOX)},
            {"local_id": 2, "class": "forklift", "points": pts(range(split), FBOX)},
            {"local_id": 3, "class": "forklift", "points": pts(range(split, n), FBOX)}]


def _positions(n=60, split=20):
    out = {(1, i): {"xy": [0.0, 1.9], "cov": [0.0025, 0.0, 0.0025]} for i in range(n)}
    out.update({(2, i): {"xy": [-6.0 + 0.1 * i, 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(split)})
    out.update({(3, i): {"xy": [-6.0 + 0.1 * split + 0.05 * (i - split), 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(split, n)})
    return out


def _built():
    s1 = synthetic_s1.build(60)
    s3, st, sid, trk_of = _stitched_s3(s1, _truth())
    cfg = config(g_max=3)
    plain = builder.SubstrateBuilder().build(s1, s3, _positions(), None, cfg, s4_spec(inputs=(s3.artifact_id,)))
    joined = builder.SubstrateBuilder().build(s1, st, _positions(), None, cfg, s4_spec(inputs=(st.artifact_id,)))
    return s1, s3, st, plain, joined


def _flags(s1, s4, members=None):
    frames = s1["frame"]
    index = providers.S4Index(s4.tables, frames, s1["coverage_segment"], members=members)
    out = {}
    for p in s4.tables["pow"]:
        nk = [p["person_track_id"], p["forklift_track_id"], p["start_frame"]]
        for f in providers.flag_frames(s4.tables, RULES, frames, s1["coverage_segment"], pow_nk=nk, index=index):
            out[f.frame_index] = f
    return out


def test_stitch_members_from_s3():
    s1, s3, st, plain, joined = _built()
    members = providers.stitch_members(st.tables)
    trk = {t["track_local_id"]: t["trk_id"] for t in st.tables["track"]}
    fork_unit = joined.tables["pow"][0]["forklift_track_id"]
    assert members[fork_unit] == [trk[2], trk[3]]  # chain order
    assert providers.stitch_members(s3.tables) == {}  # no stitch_id: no units


def test_stitched_pair_frame_with_member_state_gets_m_input():
    s1, s3, st, plain, joined = _built()
    fixed = _flags(s1, joined, providers.stitch_members(st.tables))
    assert len(fixed) == 60 and all(f.M != 2 for f in fixed.values())  # M known on every frame (the forklift moves: M = 1)
    defective = _flags(s1, joined)  # the CR-042 defect: no member map, no state found
    assert all(f.M == 2 for f in defective.values())


def test_stitched_flags_equal_the_members_own_flags_frame_by_frame():
    s1, s3, st, plain, joined = _built()
    fixed = _flags(s1, joined, providers.stitch_members(st.tables))
    own = _flags(s1, plain)  # one POW per (person, member track): 0-20 with track 2, 20-60 with track 3
    assert sorted(own) == sorted(fixed) == list(range(60))
    # `closing_rate` is an S4 pair-series value (T8.3: window over the POW's contiguous span); on the stitched S4 that span
    # crosses the stitch by T25.1 (e), and S4 is unchanged by CR-042, so it is compared with the stitched S4's own value.
    series = {r["frame_index"]: r["closing_rate_mps"] for r in joined.tables["pair_series"]}
    for i in range(60):
        a, b = dataclasses.asdict(fixed[i]), dataclasses.asdict(own[i])
        assert a.pop("closing_rate") == series[i]
        b.pop("closing_rate")
        assert a == b, i  # M, C_by (R3, R4), E, rates (R5, contact cue), speed, visible: the member's own inputs


def test_no_rate_run_spans_the_stitch():
    s1, s3, st, plain, joined = _built()
    members = providers.stitch_members(st.tables)
    index = providers.S4Index(joined.tables, s1["frame"], s1["coverage_segment"], members=members)
    unit = joined.tables["pow"][0]["forklift_track_id"]
    rows, runs = index.prepared(unit)
    assert sorted(rows) == list(range(60))  # each frame has its member's stored state
    # frames 0-19 belong to track 2 and 20-59 to track 3: no run crosses 19 / 20, although the frames are adjacent
    assert all(max(r) < 20 or min(r) >= 20 for r in runs.values())
    assert runs[19] == list(range(20)) and runs[20] == list(range(20, 60))
    trk = {t["track_local_id"]: t["trk_id"] for t in st.tables["track"]}
    assert all(rows[i]["track_id"] == (trk[2] if i < 20 else trk[3]) for i in range(60))  # stored rows, not recomputed
