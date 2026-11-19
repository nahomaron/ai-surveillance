"""T-22 zero-shot probe matcher (Owner instruction of 19 Nov 2026, item 3): hand-computed toy cases.

Written with unittest only, so it runs in `.venv-det` (`python -m unittest discover -s tests/m1b -p 'test_zs_match.py'`)
as well as in the main suite.

Toy case (hand calculation):
  references (forklift): A = (0, 0, 10, 10), B = (10, 0, 20, 10)
  detections (forklift): P = (0, 0, 10, 10) score 0.9; Q = (5, 0, 15, 10) score 0.8; R = (14, 0, 24, 10) score 0.1
  IoU(P, A) = 100 / 100 = 1.0
  IoU(Q, A) = 50 / (100 + 100 - 50) = 1/3;  IoU(Q, B) = 50 / 150 = 1/3
  IoU(R, B) = 60 / (100 + 100 - 60) = 3/7 = 0.428571...;  IoU(R, A) = 0;  IoU(P, B) = 0 (edges touch only)
  Descending IoU, one-to-one: P-A (1.0), R-B (3/7); Q is left over (A and B taken).
    -> TP 2, FP 1, FN 0; recall 1.0, precision 2/3, F1 = 4 / (4 + 1 + 0) = 0.8
  At threshold 0.2, R drops out: P-A (1.0), then Q-B (1/3 >= 0.3) -> TP 2, FP 0, FN 0; recall 1, precision 1, F1 1.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/m1b"))
import zs_match as zm  # noqa: E402

A, B = (0, 0, 10, 10), (10, 0, 20, 10)
P, Q, R = (0, 0, 10, 10), (5, 0, 15, 10), (14, 0, 24, 10)


def frame(dets, refs=((A, "forklift"), (B, "forklift"))):
    return {"references": [{"class": c, "box": b} for b, c in refs],
            "detections": [{"class": c, "box": b, "score": s} for b, s, c in dets]}


class ZeroShotMatcher(unittest.TestCase):
    def test_iou_hand_values(self):
        self.assertEqual(zm.iou(P, A), 1.0)
        self.assertAlmostEqual(zm.iou(Q, A), 1 / 3, places=12)
        self.assertAlmostEqual(zm.iou(Q, B), 1 / 3, places=12)
        self.assertAlmostEqual(zm.iou(R, B), 3 / 7, places=12)
        self.assertEqual(zm.iou(P, B), 0.0)

    def test_three_detection_toy_case(self):
        dets = [(P, 0.9), (Q, 0.8), (R, 0.1)]
        m = zm.match([A, B], dets)
        self.assertEqual([(i, j) for i, j, _ in m], [(0, 0), (1, 2)])  # P-A, R-B; Q unmatched
        c = zm.counts([frame([(P, 0.9, "forklift"), (Q, 0.8, "forklift"), (R, 0.1, "forklift")])], "forklift", 0.05)
        self.assertEqual((c["tp"], c["fp"], c["fn"]), (2, 1, 0))
        self.assertEqual(c["recall"], 1.0)
        self.assertAlmostEqual(c["precision"], 2 / 3, places=12)
        self.assertAlmostEqual(c["f1"], 0.8, places=12)

    def test_threshold_removes_r_and_q_takes_b(self):
        c = zm.counts([frame([(P, 0.9, "forklift"), (Q, 0.8, "forklift"), (R, 0.1, "forklift")])], "forklift", 0.2)
        self.assertEqual((c["tp"], c["fp"], c["fn"], c["precision"], c["f1"]), (2, 0, 0, 1.0, 1.0))

    def test_class_must_agree(self):
        c = zm.counts([frame([(P, 0.9, "person")])], "forklift", 0.05)
        self.assertEqual((c["tp"], c["fn"], c["detections"], c["precision"]), (0, 2, 0, None))
        c = zm.counts([frame([(P, 0.9, "person")])], "person", 0.05)
        self.assertEqual((c["tp"], c["fp"], c["references"], c["recall"]), (0, 1, 0, None))

    def test_iou_boundary_is_inclusive(self):
        # (0,0,3,10) inside A: intersection 30, union 100 -> IoU 0.3 exactly, matched (IoU >= 0.3)
        self.assertEqual(zm.iou((0, 0, 3, 10), A), 0.3)
        self.assertEqual(len(zm.match([A], [((0, 0, 3, 10), 0.5)])), 1)
        # (0,0,2,10): 20 / 100 = 0.2 -> not matched
        self.assertEqual(zm.match([A], [((0, 0, 2, 10), 0.5)]), [])

    def test_best_f1_ties_go_to_lower_threshold(self):
        rows = {0.05: {"f1": 0.5}, 0.10: {"f1": 0.8}, 0.15: {"f1": 0.8}, 0.20: {"f1": None}}
        self.assertEqual(zm.best_f1(rows), 0.10)
        self.assertIsNone(zm.best_f1({0.05: {"f1": None}}))

    def test_thresholds(self):
        self.assertEqual(zm.THRESHOLDS, (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5))


if __name__ == "__main__":
    unittest.main()
