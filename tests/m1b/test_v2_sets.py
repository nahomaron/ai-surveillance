"""D-53 step 0: tuning / reporting split by run (hand-made population)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import v2_sets  # noqa: E402

CAMS = [{"rec_id": "r1", "run": "A", "camera": "ceiling_1"}, {"rec_id": "r2", "run": "A", "camera": "eye_1"},
        {"rec_id": "r3", "run": "B", "camera": "eye_2"}, {"rec_id": "r4", "run": "C", "camera": "ceiling_2"}]


def test_whole_run_goes_to_tuning_when_one_camera_is_a_probe_camera():
    s = v2_sets.split(CAMS, {"r2"})
    assert [c["rec_id"] for c in s["tuning"]["cameras"]] == ["r1", "r2"]
    assert [c["rec_id"] for c in s["reporting"]["cameras"]] == ["r3", "r4"]
    assert s["tuning"]["by_viewpoint"] == {"ceiling": 1, "eye_level": 1}
    assert s["reporting"]["runs"] == ["B", "C"]


def test_check_reports_wrong_counts():
    s = v2_sets.split(CAMS, {"r2"})
    assert any("expected 116" in p for p in v2_sets.check(s))


def test_probe_camera_outside_population_is_refused():
    with pytest.raises(ValueError):
        v2_sets.split(CAMS, {"r9"})
