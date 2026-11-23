"""D-53 step 3: bottom-centre and the paired summary (hand-computed)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d4_detector_offset as d4  # noqa: E402


def test_bottom_centre():
    assert d4.bottom_centre((10.0, 20.0, 30.0, 60.0)) == (20.0, 60.0)


def test_paired_difference():
    rows = [{"along": -0.5, "oracle_along": -1.0, "theta": 5.0}, {"along": -0.7, "oracle_along": -1.0, "theta": 80.0},
            {"along": -0.9, "oracle_along": None, "theta": 80.0}]
    s = d4.summarize({"all": rows})["all"]
    assert s["detector_box"]["n"] == 3 and s["detector_box"]["along_signed_median_m"] == pytest.approx(-0.7)
    assert s["paired_same_frames"]["n"] == 2
    # differences 0.5 and 0.3 -> median 0.4
    assert s["paired_same_frames"]["median_difference_detector_minus_oracle_m"] == pytest.approx(0.4)
    assert s["by_theta"]["75-90"]["n"] == 2 and s["by_theta"]["0-15"]["n"] == 1
    # paired 75-90: one row (-0.7 vs -1.0) -> difference 0.3; paired 0-15: -0.5 vs -1.0 -> 0.5
    assert s["paired_by_theta"]["75-90"]["n"] == 1
    assert s["paired_by_theta"]["75-90"]["median_difference_detector_minus_oracle_m"] == pytest.approx(0.3)
    assert s["paired_by_theta"]["0-15"]["median_difference_detector_minus_oracle_m"] == pytest.approx(0.5)
