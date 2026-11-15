"""AR-58 item 5: `flag_frames` with an `S4Index` returns exactly what the unindexed table scans return (all fields of
every FrameFlags), on the N2 substrate fixtures and the T15 moving fixtures, for each provider set."""
import dataclasses

import pytest

from rq1.events import providers

from test_engine_part_a import RULES, R1_RULES, s4_for
from test_t15 import GAP, HEAD_ON, PARALLEL, s4_moving


def _all_pows(s4):
    return [[p["person_track_id"], p["forklift_track_id"], p["start_frame"]] for p in s4.tables["pow"]]


@pytest.mark.determinism
@pytest.mark.parametrize("source", ["N2-G1", "N2-G2", "N2-G3", "head_on", "gap", "parallel"])
def test_indexed_flag_frames_equal_the_scans(source):
    if source.startswith("N2"):
        _, s4, _, s1 = s4_for(source)
    else:
        s1, s4 = s4_moving(10, *{"head_on": HEAD_ON, "gap": GAP, "parallel": PARALLEL}[source])
    index = providers.S4Index(s4.tables, s1["frame"], s1["coverage_segment"])
    for rules in (RULES, R1_RULES, dataclasses.replace(RULES, conflict=("R3", "R4")), dataclasses.replace(RULES, conflict=(), r5=False)):
        for nk in _all_pows(s4):
            plain = providers.flag_frames(s4.tables, rules, s1["frame"], s1["coverage_segment"], pow_nk=nk)
            indexed = providers.flag_frames(s4.tables, rules, s1["frame"], s1["coverage_segment"], pow_nk=nk, index=index)
            assert plain == indexed


@pytest.mark.determinism
def test_s5_builds_on_a_recording_with_an_ineligible_frame():
    # AR-58 item 6: S5 sorted every S1 frame by frame_index, which is null on an ineligible frame (crash). With one
    # ineligible frame added after the clip, the S5 tables are identical to those built without it.
    from test_t10 import build_s5

    s1, s4 = s4_moving(10, *HEAD_ON)
    base = build_s5(s1, s4)
    extra = dict(s1["frame"][-1], frame_index=None, eligible=False, decode_seq=s1["frame"][-1]["decode_seq"] + 1)
    with_ineligible = build_s5({**s1, "frame": s1["frame"] + [extra]}, s4)
    assert with_ineligible.tables == base.tables
