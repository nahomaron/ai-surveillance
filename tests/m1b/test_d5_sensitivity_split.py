"""D-53 step 4: the limits block on hand-made points."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d5_sensitivity_split as d5  # noqa: E402


def test_limits_hand_values():
    # 5 GV-01 points (one more without truth): errors 0.5, 1.0, 3.0, 12.0, 0.2; sensitivities 0.01, 0.3, 0.3, 0.6, 0.15
    a = {"has_pos": np.array([1, 1, 1, 1, 1, 1], bool), "has_truth": np.array([1, 1, 1, 1, 1, 0], bool),
         "err": np.array([0.5, 1.0, 3.0, 12.0, 0.2, 99.0]), "sens": np.array([0.01, 0.3, 0.3, 0.6, 0.15, 9.0])}
    out = d5.limits(a)
    assert out["gv01_points"] == 5
    r = out["sensitivity_limits"]["0.2"]  # flagged: 1.0, 3.0, 12.0
    assert r["flagged"] == 3 and r["flagged_share"] == 0.6
    assert r["caught_share_of_err_gt_10m"] == 1.0 and r["caught_share_of_err_gt_2m"] == 1.0
    assert r["lost_share_of_good_lt_1m"] == 0.0  # good (< 1): 0.5, 0.2, none flagged
    assert r["lost_share_of_good_le_1m"] == round(1 / 3, 4)  # good (<= 1): 0.5, 1.0, 0.2; 1.0 flagged
    assert r["kept"]["n"] == 2
    r5 = out["sensitivity_limits"]["0.5"]  # flagged: 12.0 only
    assert r5["flagged"] == 1 and r5["caught_share_of_err_gt_2m"] == 0.5
