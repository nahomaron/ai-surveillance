"""T-23 (D-45 item 1): detector-path track points from a tracker log. Hand-built logs; expected values from the rule
(bridge of <= g_max = 15 eligible frames -> predicted / inferred; longer -> lost, no point; nothing after the last match).

unittest only, so it runs in `.venv-det` (`PYTHONPATH=src .venv-det/bin/python -m unittest discover -s tests/m1b -p 'test_tracking_*.py'`)
and in the main suite.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from rq1.tracking import bridging as br  # noqa: E402

B = [0.0, 0.0, 10.0, 20.0]


def log_for(frames, matched, lost_frames=None, tid=1):
    """Eligible `frames`; track `tid` matched (det 0) on `matched`, lost with box B on every other frame after its first match."""
    out, seen = [], False
    for i in frames:
        e = {"frame_index": i, "tracked": [], "lost": []}
        if i in matched:
            e["tracked"].append([tid, 0, B])
            seen = True
        elif seen and (lost_frames is None or i in lost_frames):
            e["lost"].append([tid, B])
        out.append(e)
    return out


def states(points):
    return [(p["frame_index"], p["state"]) for p in points]


class Bridging(unittest.TestCase):
    def test_bridge_of_g_max_frames_is_predicted(self):
        # matched 0 and 16; frames 1..15 = 15 eligible frames = g_max -> 15 predicted points
        pts = br.points_from_log(log_for(range(17), {0, 16}))[1]
        self.assertEqual(states(pts["points"]), [(0, "tracked")] + [(i, "predicted") for i in range(1, 16)] + [(16, "tracked")])
        self.assertEqual(pts["counts"]["predicted"], 15)
        self.assertTrue(all(p["det_index"] is None for p in pts["points"] if p["state"] == "predicted"))

    def test_run_over_g_max_is_lost(self):
        # matched 0 and 17; frames 1..16 = 16 eligible frames > g_max -> no points there
        pts = br.points_from_log(log_for(range(18), {0, 17}))[1]
        self.assertEqual(states(pts["points"]), [(0, "tracked"), (17, "tracked")])
        self.assertEqual((pts["counts"]["lost_long_run"], pts["counts"]["runs_lost"]), (16, 1))

    def test_run_counted_in_eligible_frames(self):
        # T19: camera frames 1..16 (16 frames), frame 8 ineligible (absent from the log) -> 15 eligible frames -> predicted
        frames = [i for i in range(18) if i != 8]
        pts = br.points_from_log(log_for(frames, {0, 17}))[1]
        self.assertEqual([i for i, s in states(pts["points"]) if s == "predicted"], [i for i in range(1, 17) if i != 8])
        self.assertNotIn(8, [p["frame_index"] for p in pts["points"]])

    def test_nothing_after_last_match(self):
        pts = br.points_from_log(log_for(range(10), {0, 1, 2}))[1]
        self.assertEqual(states(pts["points"]), [(0, "tracked"), (1, "tracked"), (2, "tracked")])

    def test_tracked_point_carries_detection(self):
        log = [{"frame_index": 4, "tracked": [[7, 3, [1, 2, 3, 4]]], "lost": []}]
        self.assertEqual(br.points_from_log(log)[7]["points"], [{"frame_index": 4, "state": "tracked", "bbox": [1.0, 2.0, 3.0, 4.0], "det_index": 3}])

    def test_missing_prediction_is_an_error(self):
        with self.assertRaises(ValueError):
            br.points_from_log(log_for(range(5), {0, 4}, lost_frames={1, 2}))

    def test_unsorted_log_is_an_error(self):
        with self.assertRaises(ValueError):
            br.points_from_log([{"frame_index": 2}, {"frame_index": 1}])

    def test_foot_point_is_bottom_centre(self):
        self.assertEqual(br.foot_point([100.0, 50.0, 140.0, 250.0]), [120.0, 250.0])


if __name__ == "__main__":
    unittest.main()
