"""D-50 item 2: episode extent and fragmentation on the detector path (descriptive; N4 and the reported metrics unchanged).

Definitions (stated in the report):
- references: the assessable G1 references (the N4 rows); events: the deciding G1 system events (the N4 columns);
- best same-pair temporal IoU of an unmatched event: max over references with the same identity pair (0 if none);
  bands 0, (0, 0.1], (0.1, 0.2], (0.2, 0.3), >= 0.3;
- "any temporal overlap, same pair" (descriptive, not the N4 metric): a reference counts as found when some event of the same
  pair overlaps it (IoU > 0); an event counts as supported when it overlaps some reference of the same pair; no one-to-one rule.
Hand-built case (timeline seconds; pair X = (p1, f1), Y = (p2, f2)):
  references: R1 X [0, 10); R2 X [20, 30); R3 Y [40, 50)
  events:     E1 X [1, 9)  -> IoU(R1) = 8/10 = 0.8
              E2 X [9, 12) -> IoU(R1) = 1/12 = 0.0833 (band (0, 0.1])
              E3 X [25, 26) -> IoU(R2) = 1/10 = 0.1 (band (0, 0.1])
              E4 Y [60, 70) -> no overlap (band 0)
              E5 None-pair [0, 50) -> pair unresolved, never supports
  any-overlap: refs found R1 (E1, E2), R2 (E3); R3 not -> 2 / 3; events supported E1, E2, E3 -> 3 / 5
  episodes overlapping R1 (same pair): ep1 [1, 9) not linked, ep2 [9, 12) continuation of ep1 -> 2 episodes, 1 linked
Band edges: 0.1 falls in (0, 0.1]; 0.2 in (0.1, 0.2]; 0.3 in ">= 0.3".
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import extent_check as xc  # noqa: E402

X, Y = ("p1", "f1"), ("p2", "f2")
REFS = [("R1", X, 0.0, 10.0), ("R2", X, 20.0, 30.0), ("R3", Y, 40.0, 50.0)]
EVENTS = [("E1", X, 1.0, 9.0), ("E2", X, 9.0, 12.0), ("E3", X, 25.0, 26.0), ("E4", Y, 60.0, 70.0), ("E5", None, 0.0, 50.0)]


def test_best_same_pair_iou():
    assert math.isclose(xc.best_same_pair_iou(EVENTS[1], REFS), 1 / 12)
    assert math.isclose(xc.best_same_pair_iou(EVENTS[2], REFS), 0.1)
    assert xc.best_same_pair_iou(EVENTS[3], REFS) == 0.0
    assert xc.best_same_pair_iou(EVENTS[4], REFS) == 0.0


def test_bands():
    assert [xc.band(v) for v in (0.0, 1e-9, 0.1, 0.1000001, 0.2, 0.25, 0.3, 0.8)] == [
        "0", "(0, 0.1]", "(0, 0.1]", "(0.1, 0.2]", "(0.1, 0.2]", "(0.2, 0.3)", ">= 0.3", ">= 0.3"]


def test_any_overlap_counts():
    assert xc.any_overlap(REFS, EVENTS) == {"a": 3, "found": 2, "s": 5, "supported": 3}


def test_episodes_per_reference():
    eps = [(X, 1.0, 9.0, False), (X, 9.0, 12.0, True), (Y, 0.0, 5.0, False)]
    assert xc.episodes_overlapping(REFS[0], eps) == (2, 1)
    assert xc.episodes_overlapping(REFS[2], eps) == (0, 0)
