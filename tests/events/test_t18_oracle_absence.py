"""Appendix T T18 amendment 2 (E-1.2.16): "pair-level S4/S5 output on a fixture is identical before and after amendment 2".

Fixture: 60 frames at 10 fps, hand camera of test_t17_oracle_truth (straight down from 10 m, 1920 x 1080). Person static at
(1.0, 2.0); forklift at x(t) = -2.5 + t on y = 0 with yaw 0 (the N2-G2 layout moved to x = 1). The person is not visible on
a run of frames starting at frame 20. "Before" is T17.2 as first written: every not-visible frame inside the visible span is
predicted (a g_max that no run reaches).

Run of g_max = 15 frames: the points are the same under both rules, so S3, S4 and S5 are identical (same artifact IDs).
Run of g_max + 1 frames: after the amendment the 16 frames have no person point. That is a T8.1 gap longer than g_max, so
the POW ends with gap_exceeded and a second POW continues it; before the amendment the 16 predicted points were joint
frames of one POW. The pair-level output therefore differs for runs longer than g_max (pinned here, and reported)."""
import pytest

from rq1.adapters import oracle_truth as ot
from rq1.adapters import sdg_truth
from rq1.events import s5
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.substrate import builder, oracle

from test_engine_part_a import FORK, PERSON
from test_t10 import BANDS, SUBSTRATE, build_s5

CAL = {"intrinsics_K": [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0], "R_cam_from_world": [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0],
       "t_cam_from_world_m": [0.0, 0.0, 10.0], "image_size_px": [1920, 1080]}
N, G, START, BEFORE = 60, SUBSTRATE["g_max"], 20, 10 ** 9


def _obs(cls, xy, visible):
    box3d = {"x_min": -0.2, "x_max": 0.2, "y_min": -0.2, "y_max": 0.2, "z_min": 0.0, "z_max": 1.0,
             "transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [xy[0], xy[1], 0.0, 1]]}
    return ot.sdg_obs(CAL, sdg_truth.ObjectTruth(cls, cls, xy, 0.0, None, visible, box3d))[0]


def build(run, g_max):
    frames = [{"p": _obs("person", (1.0, 2.0), None if START <= k < START + run else (1045, 300, 1090, 355)),
               "f": _obs("forklift", (-2.5 + k / 10, 0.0), (300, 600, 500, 720))} for k in range(N)]
    tracks, counts = ot.camera_tracks(CAL, frames, g_max, frozenset())
    s1 = synthetic_s1.build(N, width=1920, height=1080)
    truth, positions = ot.s3_truth(tracks, {"p": "person", "f": "forklift"}, {k: k for k in range(N)})
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.16", "f", "f", ("orc_" + "a" * 26,), (), {}))
    cfg = builder.SubstrateConfig(G, 0.3, 0.5, 2.0, {"forklift"}, {"person": PERSON, "forklift": FORK}, {"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                  BANDS, 0.5)
    s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, Spec("S4", "E-1.2.16", "f", "f", ("gcf_" + "a" * 26, s5.substrate_config_id(SUBSTRATE)), (s3.artifact_id,), {}))
    return counts, s3, s4, build_s5(s1, s4)


@pytest.mark.determinism
def test_run_of_g_max_frames_gives_identical_s4_and_s5_before_and_after():
    (c_before, s3_before, s4_before, s5_before), (c_after, s3_after, s4_after, s5_after) = build(G, BEFORE), build(G, G)
    assert c_after == c_before and (c_after["predicted"], c_after["lost"]) == (G, 0)
    assert s3_after.artifact_id == s3_before.artifact_id
    assert s4_after.artifact_id == s4_before.artifact_id and s4_after.tables == s4_before.tables
    assert s5_after.artifact_id == s5_before.artifact_id and s5_after.tables == s5_before.tables
    # the comparison is not empty: one POW over all 60 frames with a pair row on each, and at least one episode
    (window,) = s4_after.tables["pow"]
    assert (window["start_frame"], window["end_frame_excl"]) == (0, N) and len(s4_after.tables["pair_series"]) == N
    assert len(s5_after.tables["episode"]) >= 1


def test_run_of_g_max_plus_one_frames_ends_the_pow_after_the_amendment():
    (c_before, _, s4_before, _), (c_after, _, s4_after, _) = build(G + 1, BEFORE), build(G + 1, G)
    assert (c_before["predicted"], c_before["lost"]) == (G + 1, 0) and (c_after["predicted"], c_after["lost"], c_after["lost_long_run"]) == (0, G + 1, G + 1)
    (one,) = s4_before.tables["pow"]  # before: the predicted points are joint frames (T8.1), one POW
    assert (one["start_frame"], one["end_frame_excl"]) == (0, N)
    first, second = sorted(s4_after.tables["pow"], key=lambda r: r["start_frame"])  # after: a gap of 16 > g_max
    assert (first["start_frame"], first["end_frame_excl"], first["end_reason"]) == (0, START, "gap_exceeded")
    assert (second["start_frame"], second["end_frame_excl"]) == (START + G + 1, N) and second["continuation_of_nk"] is not None
    assert len(s4_after.tables["pair_series"]) == N - (G + 1)
