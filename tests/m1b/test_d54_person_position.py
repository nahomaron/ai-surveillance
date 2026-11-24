"""D-54 STEP 4: classification helpers of the person-position diagnostic (hand-made inputs)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d54_person_position as pp  # noqa: E402


@pytest.mark.parametrize("r, b", [(0.0, "0-2"), (1.99, "0-2"), (2.0, "2-5"), (9.9, "5-10"), (10.0, "10-20"), (20.0, ">=20"), (55.0, ">=20")])
def test_r_bins(r, b):
    assert pp.r_bin(r) == b


def test_half_depth_of_an_axis_aligned_box():
    floor = [(0.0, 0.0), (0.6, 0.0), (0.6, 0.3), (0.0, 0.3)]  # 0.6 x 0.3 m
    assert pp.half_depth(floor, (1.0, 0.0)) == pytest.approx(0.3)
    assert pp.half_depth(floor, (0.0, 1.0)) == pytest.approx(0.15)
    s = 2 ** -0.5
    assert pp.half_depth(floor, (s, s)) == pytest.approx((0.6 + 0.3) * s / 2)  # projected corner spread / 2


def test_bottom_clipped_is_the_last_pixel_row():
    assert pp.bottom_clipped([0, 0, 10, 1079], 1080) and pp.bottom_clipped([0, 0, 10, 1080], 1080)
    assert not pp.bottom_clipped([0, 0, 10, 1078], 1080)


def test_crossing_either_direction_and_unknown():
    assert pp.crossing(2.5, 1.5, 2.0) and pp.crossing(1.5, 2.5, 2.0)
    assert not pp.crossing(2.5, 2.1, 2.0) and not pp.crossing(None, 1.0, 2.0)
    assert pp.crossing(2.0, 1.99, 2.0) and not pp.crossing(2.0, 2.0, 2.0)  # "below" is < (R2: clearance < d_p)


@pytest.mark.parametrize("b, p, cause", [
    ({"clearance": 1.5, "pred_min": 1.2}, {"clearance": 2.5, "pred_min": 1.2}, "B clearance below d_p only, B-sim-P not"),
    ({"clearance": 2.5, "pred_min": 0.5}, {"clearance": 2.5, "pred_min": 1.5}, "B predicted minimum below d_pc only, B-sim-P not"),
    ({"clearance": 1.5, "pred_min": 0.5}, {"clearance": 2.5, "pred_min": 1.5}, "B below d_p and d_pc, B-sim-P not"),
    ({"clearance": 1.5, "pred_min": 0.5}, {"clearance": None, "pred_min": None}, "B below d_p and d_pc, B-sim-P not"),
    ({"clearance": None, "pred_min": None}, {"clearance": 1.0, "pred_min": 1.0}, "clearance not measured in B or B-sim-P"),
    ({"clearance": 1.5, "pred_min": 0.5}, {"clearance": 1.0, "pred_min": 0.2}, "same side of d_p and d_pc in B and B-sim-P")])
def test_cause_class(b, p, cause):
    assert pp.cause_class(b, p, 2.0, 1.0) == cause


def test_stats_hand_values():
    rows = [{"along": -1.0, "across": 0.2}, {"along": -0.5, "across": 0.1}, {"along": 0.5, "across": 0.3}]
    s = pp.stats(rows)
    assert s["n"] == 3 and s["along_signed_median_m"] == -0.5 and s["along_abs_median_m"] == 0.5 and s["across_abs_median_m"] == 0.2
