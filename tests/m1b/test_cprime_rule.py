"""D-47 item 1: the C' tracker rule (post-hoc, exploratory), fixed by the Owner before the run.

Rule (D-47 item 1): per class, track_high_thresh = new_track_thresh = the class's detector threshold (D-45 item 0:
person 0.20, forklift 0.05); track_low_thresh = min(0.10, detector threshold); all other parameters the installed defaults.
Hand values:
  person:   high 0.20, new 0.20, low min(0.10, 0.20) = 0.10
  forklift: high 0.05, new 0.05, low min(0.10, 0.05) = 0.05 -> ByteTrack's low band is 0.05 < s < 0.05: empty, so the
            second association receives nothing (D-47 item 1).
Main environment (the rule is pure); the tracker behaviour under the rule is tested in `.venv-det`
(`test_tracking_bytetrack.py::CPrime`).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from rq1.tracking import bytetrack as bt  # noqa: E402

DEFAULTS = {"fuse_score": True, "match_thresh": 0.8, "new_track_thresh": 0.25, "track_buffer": 30, "track_high_thresh": 0.25,
            "track_low_thresh": 0.1, "tracker_type": "bytetrack"}  # the installed bytetrack.yaml (recorded in every C run)


class CPrimeRule(unittest.TestCase):
    def test_person(self):
        p = bt.aligned_params(DEFAULTS, 0.20)
        self.assertEqual((p["track_high_thresh"], p["new_track_thresh"], p["track_low_thresh"]), (0.20, 0.20, 0.10))

    def test_forklift_second_stage_empty(self):
        p = bt.aligned_params(DEFAULTS, 0.05)
        self.assertEqual((p["track_high_thresh"], p["new_track_thresh"], p["track_low_thresh"]), (0.05, 0.05, 0.05))
        # ByteTrack's low band is track_low_thresh < s < track_high_thresh (byte_tracker.py line 338)
        self.assertFalse(any(p["track_low_thresh"] < s < p["track_high_thresh"] for s in (0.05, 0.0500001, 0.07, 0.2)))

    def test_other_parameters_unchanged(self):
        for thr in (0.20, 0.05):
            p = bt.aligned_params(DEFAULTS, thr)
            for k in ("fuse_score", "match_thresh", "track_buffer", "tracker_type"):
                self.assertEqual(p[k], DEFAULTS[k])
        self.assertEqual(DEFAULTS["track_high_thresh"], 0.25)  # the input is not modified

    def test_params_by_class_uses_the_s2_thresholds(self):
        from rq1.perception import s2
        got = bt.cprime_params(DEFAULTS, s2.THRESHOLDS)
        self.assertEqual(set(got), {"person", "forklift"})
        self.assertEqual(got["person"]["track_high_thresh"], 0.20)
        self.assertEqual(got["forklift"]["track_low_thresh"], 0.05)


if __name__ == "__main__":
    unittest.main()
