"""D-54 STEP 3b: the package jobs and the pooled extent measures (hand-made inputs)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d54_c_v2 as c  # noqa: E402


def test_jobs_person_is_column_c_and_forklift_is_the_package():
    col_c = {"params": {"track_high_thresh": 0.25}}
    pkg = {"tracker_id": "bytetrack", "params": {"track_high_thresh": 0.05}}
    j = c.jobs(col_c, pkg)
    assert j[0] == {"job": "person", "tracker_id": "bytetrack", "class": "person", "params": {"track_high_thresh": 0.25}}
    assert j[1] == {"job": c.PACKAGE, "tracker_id": "bytetrack", "class": "forklift", "params": {"track_high_thresh": 0.05}}


def test_pool_extent_hand_counts():
    parts = [{"unmatched_bands": ["0", "(0, 0.1]", ">= 0.3"], "per_ref": [{"matched": True, "episodes": 1, "linked": 0},
                                                                         {"matched": False, "episodes": 3, "linked": 1}],
              "episodes": 5, "episodes_with_continuation": 1},
             {"unmatched_bands": ["0"], "per_ref": [{"matched": True, "episodes": 2, "linked": 1}], "episodes": 2, "episodes_with_continuation": 1}]
    out = c.pool_extent(parts)
    assert out["unmatched_events"] == 4 and out["unmatched_with_same_pair_overlap"] == 2
    assert out["references_matched_or_overlapped"] == 3 and out["of_which_matched"] == 2
    assert out["references_with_2plus_episodes"] == 2 and out["by_episode_count"] == {"1": 1, "2": 1, "3": 1}
    assert (out["episodes_overlapping_references"], out["of_which_linked"]) == (6, 2)
    assert (out["episodes"], out["episodes_with_continuation_of_nk"]) == (7, 2)
