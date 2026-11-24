"""D-54 STEP 3: run configurations, availability rows and error summary of the B-v2 diagnostic (hand-made inputs)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d54_b_v2 as b  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../substrate"))
from test_part_b import config  # noqa: E402


def test_gate_run_sets_s_max_and_keeps_the_priors():
    base = config()
    cfg, gcf, rec = b.run_config(base, gate=True, shift=False)
    assert cfg.s_max == 0.1 and cfg.priors == base.priors and rec["s_max_m_per_px"] == 0.1


def test_shift_run_changes_only_the_forklift_prior():
    base = config()
    cfg, gcf, rec = b.run_config(base, gate=False, shift=True)
    f = cfg.priors["forklift"]
    assert (f["anchor"], f["anchor_offset_m"], f["anchor_taper_m"]) == ("box_bottom_centre", 1.00, 2.0)
    assert cfg.priors["person"] == base.priors["person"] and cfg.s_max is None and "s_max_m_per_px" not in rec
    assert cfg.prior_ids["forklift"] != b.run_config(base, gate=False, shift=False)[0].prior_ids["forklift"]
    assert len({b.run_config(base, **o)[1] for o in b.RUNS.values()}) == 3  # three distinct geometry configurations


def _row(x=None, s="absent", reason=None, ev="visible"):
    r = {"x_m": x, "evidence_state": ev}
    if s != "absent":
        r["floor_resolution_m_per_px"], r["floor_resolution_m_per_px_null_reason"] = s, reason
    return r


@pytest.mark.parametrize("row, cat", [(_row(x=1.0), "position"), (_row(x=1.0, s=0.05), "position"), (_row(s=0.3), "resolution_limit"),
                                      (_row(s=None, reason="not_observable"), "no_floor_intersection"),
                                      (_row(s=None, reason="not_applicable", ev="lost"), "lost"), (_row(ev="lost"), "lost"), (_row(), "other_null")])
def test_availability_rows(row, cat):
    assert b.availability_category(row) == cat


def test_error_summary_hand_values():
    out = b.error_summary([0.5, 1.5, 3.0, 12.0])
    # linear-interpolation median of [0.5, 1.5, 3.0, 12.0] = (1.5 + 3.0) / 2; P95 = 3.0 + 0.85 * 9.0
    assert out["median_m"] == pytest.approx(2.25) and out["p95_m"] == pytest.approx(10.65)
    assert (out["share_gt_1m"], out["share_gt_2m"], out["share_gt_10m"]) == (0.75, 0.5, 0.25)
