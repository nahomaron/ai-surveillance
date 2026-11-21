"""S2 detector stage (D-45 items 0 and 2; T8.6; E-1.2.1 section 5.4; AR-62 item 1). Hand-computed cases.

Frame 7, image 1920 x 1080, raw boxes:
  a forklift (300, 400, 500, 600) score 0.04  -> dropped (< 0.05)
  b forklift (100, 400, 300, 600) score 0.05  -> kept (>= 0.05)
  c person   (10, 20, 50, 120)    score 0.19  -> dropped (< 0.20)
  d person   (0.5, 20, 40, 120)   score 0.30  -> kept; truncated (x1 <= 1)
  e person   (900, 20, 940, 120)  score 0.30  -> kept; not truncated
  f forklift (1800, 900, 1919.2, 1079) score 0.05 -> kept; truncated (x2 >= 1919)
det_index order: class (person before forklift), then -score, then x1, then y1:
  0 = d (person 0.30, x1 0.5), 1 = e (person 0.30, x1 900), 2 = b (forklift 0.05, x1 100), 3 = f (forklift 0.05, x1 1800)
"""
from __future__ import annotations

import pytest

from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.perception import s2

pytestmark = pytest.mark.determinism
RAW = {7: [{"class": "forklift", "box": [300, 400, 500, 600], "score": 0.04}, {"class": "forklift", "box": [100, 400, 300, 600], "score": 0.05},
           {"class": "person", "box": [10, 20, 50, 120], "score": 0.19}, {"class": "person", "box": [0.5, 20, 40, 120], "score": 0.30},
           {"class": "person", "box": [900, 20, 940, 120], "score": 0.30}, {"class": "forklift", "box": [1800, 900, 1919.2, 1079], "score": 0.05}]}
COMP = s2.weights_component("yolov8s-worldv2.pt", "ab" * 32, "https://example.invalid/w.pt", "AGPL-3.0")
REC = core.make_id("rec", "s2-fixture")
SPEC = Spec("S2", "E-1.2.21", "test", "test", (core.make_id("mdl", "fixture"), core.make_id("inf", "fixture")), (), {})


def test_threshold_order_truncation():
    rows = s2.detection_rows(REC, RAW, 1920, 1080, s2.component_id(COMP))
    assert [(r["det_index"], r["class"], r["bbox_xyxy_px"][0], r["truncated"]) for r in rows] == [
        (0, "person", 0.5, True), (1, "person", 900.0, False), (2, "forklift", 100.0, False), (3, "forklift", 1800.0, True)]
    assert all(r["score_calibrated"] is None and r["score_calibrated_null_reason"] == "not_computed_by_config" for r in rows)


def test_thresholds_are_the_d45_values():
    assert s2.THRESHOLDS == {"person": 0.20, "forklift": 0.05}


def test_truncated_boundary():
    assert s2.truncated([1.0, 5, 10, 10], 100, 100) and not s2.truncated([1.01, 1.01, 98.99, 98.99], 100, 100)
    assert s2.truncated([5, 5, 99.0, 10], 100, 100) and s2.truncated([5, 5, 10, 99.0], 100, 100)


def test_artifact_is_tolerance_class_and_stable():
    a = s2.build(REC, RAW, 1920, 1080, s2.component_id(COMP), SPEC)
    b = s2.build(REC, RAW, 1920, 1080, s2.component_id(COMP), SPEC)
    assert a.artifact_id == b.artifact_id and len(a.tables["detection"]) == 4
    assert s2.component_id(COMP).startswith("lic_")
    assert all(r["model_component_id"] == s2.component_id(COMP) for r in a.tables["detection"])
