"""T-25p revision (Owner instruction of 19 Nov 2026, item 2d): detections by score band, split by reference match and by
whether they became a tracked S3 point; frame-level recall stage by stage. Hand-computed toy case.

Bands (Owner item 2d): [thr, 0.10), [0.10, 0.25), >= 0.25 per class (thr = the D-45 class threshold).

Toy case, two eligible frames (the probe matcher: same class, IoU >= 0.3, one-to-one by descending IoU):
  frame 0
    references: forklift A = (0, 0, 10, 10), B = (20, 0, 30, 10); person C = (100, 0, 110, 20)
    S2 detections:
      p forklift (0, 0, 10, 10)  score 0.30   -> band >= 0.25;        IoU(p, A) = 1
      s forklift (20, 0, 30, 10) score 0.15   -> band [0.10, 0.25);   IoU(s, B) = 1
      u forklift (21, 0, 31, 10) score 0.06   -> band [thr, 0.10);    IoU(u, B) = 90 / 110 = 0.818 (B already taken by s)
      t forklift (50, 0, 60, 10) score 0.07   -> band [thr, 0.10);    no reference
      q person   (100, 0, 110, 20) score 0.22 -> band [0.20, 0.25) (person thr 0.20 > 0.10: the first band is empty)
    S3 points: tracked from p (detection_id p); predicted forklift box V = (20, 0, 30, 10)
  frame 1
    references: forklift A; no detections, no points
  Expected:
    forklift: >= 0.25: matched & tracked 1; [0.10, 0.25): matched & not tracked 1; [thr, 0.10): unmatched & not tracked 2
    person: [0.20, 0.25): matched & not tracked 1
    stage recall, forklift (3 references): S2 2/3; tracked 1/3 (p's box = A); tracked + predicted 2/3 (p-A, V-B)
    stage recall, person (1 reference): S2 1/1; tracked 0/1; tracked + predicted 0/1
Boundaries: 0.10 falls in [0.10, 0.25), 0.25 in >= 0.25 (Owner's half-open bands). ByteTrack's own low band is
(0.10, 0.25) (byte_tracker.py line 338), so a score of exactly 0.10 is unused by the tracker but counted in [0.10, 0.25) here.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/m1b"))
import tracker_loss as tl  # noqa: E402

A, B, C = (0, 0, 10, 10), (20, 0, 30, 10), (100, 0, 110, 20)


def det(i, cls, box, score, frame=0):
    return {"det_id": i, "frame_index": frame, "class": cls, "bbox_xyxy_px": list(box), "score": score}


def point(frame, cls, box, state, det_id=None):
    return {"frame_index": frame, "class": cls, "bbox_xyxy_px": list(box), "state": state, "detection_id": det_id}


REFS = {0: [("forklift", A), ("forklift", B), ("person", C)], 1: [("forklift", A)]}
DETS = [det("p", "forklift", A, 0.30), det("s", "forklift", B, 0.15), det("u", "forklift", (21, 0, 31, 10), 0.06),
        det("t", "forklift", (50, 0, 60, 10), 0.07), det("q", "person", C, 0.22)]
POINTS = [point(0, "forklift", A, "tracked", "p"), point(0, "forklift", B, "predicted")]
THR = {"person": 0.20, "forklift": 0.05}


class TrackerLoss(unittest.TestCase):
    def test_band_boundaries(self):
        self.assertEqual(tl.band(0.05), tl.BANDS[0])
        self.assertEqual(tl.band(0.0999), tl.BANDS[0])
        self.assertEqual(tl.band(0.10), tl.BANDS[1])
        self.assertEqual(tl.band(0.2499), tl.BANDS[1])
        self.assertEqual(tl.band(0.25), tl.BANDS[2])

    def test_toy_breakdown(self):
        out = tl.camera(REFS, DETS, POINTS, frames=[0, 1])
        f, p = out["bands"]["forklift"], out["bands"]["person"]
        self.assertEqual(f[tl.BANDS[2]], {"matched_tracked": 1, "matched_not_tracked": 0, "unmatched_tracked": 0, "unmatched_not_tracked": 0})
        self.assertEqual(f[tl.BANDS[1]], {"matched_tracked": 0, "matched_not_tracked": 1, "unmatched_tracked": 0, "unmatched_not_tracked": 0})
        self.assertEqual(f[tl.BANDS[0]], {"matched_tracked": 0, "matched_not_tracked": 0, "unmatched_tracked": 0, "unmatched_not_tracked": 2})
        self.assertEqual(p[tl.BANDS[1]], {"matched_tracked": 0, "matched_not_tracked": 1, "unmatched_tracked": 0, "unmatched_not_tracked": 0})
        self.assertEqual(sum(p[tl.BANDS[0]].values()) + sum(p[tl.BANDS[2]].values()), 0)

    def test_toy_stage_recall(self):
        out = tl.camera(REFS, DETS, POINTS, frames=[0, 1])
        self.assertEqual(out["stages"]["forklift"], {"references": 3, "s2": 2, "tracked": 1, "tracked_predicted": 2})
        self.assertEqual(out["stages"]["person"], {"references": 1, "s2": 1, "tracked": 0, "tracked_predicted": 0})

    def test_thresholds_are_the_s2_thresholds(self):
        from rq1.perception import s2
        self.assertEqual(tl.THRESHOLDS, s2.THRESHOLDS)

    def test_threshold_guard(self):
        # a detection below its class threshold cannot occur in S2 output; the module refuses it
        with self.assertRaises(ValueError):
            tl.camera(REFS, [det("x", "person", C, 0.15)], [], frames=[0], thresholds=THR)


if __name__ == "__main__":
    unittest.main()
