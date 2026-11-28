"""D-63 STEP 5 (T-29p): aggregation of a v2 partition run, on hand-made camera records (expected values by hand)."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/v2"))
import aggregate_v2 as ag  # noqa: E402

FREEZE = json.loads((ROOT / "docs/preregistration/freeze_record_v2.json").read_text())


def counts(a, m, s, f, u=0.1):
    return {"counts": {"a": a, "m": m, "s": s, "m_s": m, "f": f, "u": u, "c": a, "abstained_miss": 0, "duplicate": 0}}


def cam(rec, view, group, ev, gv=None):
    return {"rec_id": rec, "viewpoint": view, "stratum": f"s:{view}", "leakage_group": group, "ev": ev, "gv": gv or {}}


def test_ev_table_pools_counts_by_viewpoint():
    cams = [cam("r1", "ceiling", "g1", {"C|BL-6": {"0.3": counts(2, 1, 2, 1)}}),
            cam("r2", "eye_level", "g2", {"C|BL-6": {"0.3": counts(3, 3, 4, 1)}})]
    t = ag.ev_table(cams, "C|BL-6", "0.3")
    assert t["all"]["EV-M1"]["value"] == pytest.approx(4 / 5)  # (1 + 3) / (2 + 3)
    assert t["all"]["EV-M2"]["value"] == pytest.approx(4 / 6)  # (1 + 3) / (2 + 4)
    assert t["all"]["EV-M7"]["value"] == pytest.approx(2 / 0.2)  # 2 false alerts per 0.2 h
    assert t["ceiling"]["EV-M1"]["value"] == pytest.approx(1 / 2) and t["eye_level"]["cameras"] == 1
    assert t["all"]["leakage_groups"] == 2 and t["all"]["EV-M1"]["target_b"] is not None


def test_paired_difference_and_no_decision_rule():
    cams = [cam("r1", "ceiling", "g1", {"A|BL-3": {"0.3": counts(4, 2, 4, 2)}, "A|BL-6": {"0.3": counts(4, 3, 3, 0)}}),
            cam("r2", "ceiling", "g2", {"A|BL-3": {"0.3": counts(2, 2, 2, 0)}, "A|BL-6": {"0.3": counts(2, 2, 2, 0)}})]
    p = ag.paired(cams, "A", "BL-3", "BL-6", "0.3")
    assert p["EV-M1"]["difference"] == pytest.approx(4 / 6 - 5 / 6)  # BL-3 4/6 minus BL-6 5/6
    assert p["EV-M1"]["decision_rule"] is None and len(p["EV-M1"]["target_b"]) == 2


def test_gv01_summary_by_hand():
    gv = lambda rows, avail: {"B": {"gv01": rows, "availability": avail}}
    cams = [cam("r1", "ceiling", "g1", {}, gv([("person", "detected", 3.0, 4.0), ("forklift", "detected", 0.0, 1.0)], {"person|position": 1, "forklift|null:out_of_frame": 2})),
            cam("r2", "eye_level", "g2", {}, gv([("person", "detected", 0.6, 0.8)], {"person|position": 1}))]
    s = ag.gv01_summary(cams, "B", "all")
    # norms 5.0, 1.0, 1.0: RMSE sqrt((25 + 1 + 1) / 3) = 3.0; median 1.0; share > 1 m = 1/3, > 2 m = 1/3, > 5 m = 0
    assert s["n"] == 3 and s["rmse_m"] == pytest.approx(3.0) and s["median_m"] == pytest.approx(1.0)
    assert s["share_gt_1m"] == pytest.approx(1 / 3) and s["share_gt_5m"] == 0.0
    assert s["availability"] == {"null:out_of_frame": 2, "position": 2}
    p = ag.gv01_summary(cams, "B", "ceiling", "person")
    assert p["n"] == 1 and p["rmse_m"] == pytest.approx(5.0) and p["availability"] == {"position": 1}


def test_gv07_and_gv04_by_hand():
    cams = [cam("r1", "ceiling", "g1", {}, {"B": {"gv07": [("person", "detected", 0.3), ("forklift", "detected", -0.4)]},
                                            "gv04_simulator_positions": [("2.00x1.00", "detected", -0.5), ("2.00x1.00", "detected", -0.3)]})]
    s = ag.gv07_summary(cams, "B")
    assert s["rmse_mps"] == pytest.approx(math.sqrt((0.09 + 0.16) / 2)) and s["bias_mps"] == pytest.approx(-0.05)
    assert s["outlier_share"] is None and "CR-041" in s["outlier_share_null_reason"]
    assert ag.gv04_summary(cams)["bias_m"] == pytest.approx(-0.4)


def test_mr01():
    run = [{"rec_id": "r1", "artifact_digest": "x"}, {"rec_id": "r2", "artifact_digest": "y"}]
    assert ag.mr01(run, run)["value"] == 1.0
    assert ag.mr01(run, [run[0], {"rec_id": "r2", "artifact_digest": "z"}]) == {"cameras": 2, "repeated": 2, "differing": ["r2"], "value": 0.0}
    assert ag.mr01(run, run[:1])["value"] is None  # repeat incomplete


def test_criteria_off_the_test_partition_are_not_registered_decisions():
    vals = {"C1-MR-01": {"value": 1.0, "ci": None}, "C2-GV-01-ceiling": {"value": 0.2, "ci": [0.1, 0.2]},
            "C2-GV-01-eye_level": {"value": 0.4, "ci": [0.3, 0.5]}, "C3-GV-07": {"value": 0.2, "ci": [0.1, 0.3]},
            "C4-GV-04": {"value": 0.0, "ci": [-0.05, 0.05]}}
    rows = {r["criterion_label"]: r for r in ag.criterion_rows(FREEZE, vals, 25, "reporting")}
    assert rows["C1-MR-01"]["decision"] == "met" and rows["C1-MR-01"]["status"] == "registered decision"
    # ci_upper_le 0.25 (v2 section 9): [0.1, 0.2] met; [0.3, 0.5] not_met (low > target); [0.1, 0.3] inconclusive
    assert (rows["C2-GV-01-ceiling"]["decision"], rows["C2-GV-01-eye_level"]["decision"], rows["C3-GV-07"]["decision"]) == ("met", "not_met", "inconclusive")
    assert rows["C4-GV-04"]["decision"] == "met"  # abs_bias_ci_within 0.10
    assert rows["C2-GV-01-ceiling"]["status"].startswith("not the registered decision (registered slice: test")
    few = {r["criterion_label"]: r for r in ag.criterion_rows(FREEZE, vals, 11, "test")}
    assert few["C2-GV-01-ceiling"]["decision"] == "not_assessable"  # 11 leakage groups < n_min_units 20
    assert few["C2-GV-01-ceiling"]["status"] == "registered decision"


def test_m_inputs_total():
    mk = lambda b, m: {"checks": {"m_inputs": {"C|BL-6": {"pair_frames_with_both_states": b, "m_missing": m}}}}
    assert ag.m_inputs_total([mk(100, 0), mk(50, 3)]) == {"C|BL-6": {"pair_frames_with_both_states": 150, "m_missing": 3, "share_missing": 0.02}}
    assert ag.m_inputs_total([{"checks": {}}]) is None


def test_ev_m7_reports_false_duplicate_and_support_separately():
    from report_v2 import ev_rows

    v = counts(3, 2, 5, 3, u=0.5)
    v["counts"]["duplicate"] = 1
    t = ag.ev_table([cam("r", "ceiling", "g", {"C|BL-6": {"0.3": v}})], "C|BL-6", "0.3")
    assert t["all"]["counts"]["false"] == 2 and t["all"]["counts"]["duplicate"] == 1
    assert t["all"]["EV-M7"]["value"] == 6.0  # (2 false + 1 duplicate) / 0.5 usable camera-hour
    assert "| False | Duplicate | Usable camera-hours |" in ev_rows(t)[0]
    assert "| 2 | 1 | 0.500 | 6.0 |" in ev_rows(t)[2]


def test_report_missing_baseline_is_refused():
    keys = [f"{col}|{bl}" for col, baselines in ag.rv.COLUMNS.items() for bl in baselines]
    c = {"rec_id": "fixture", "ev": {k: {str(i): {} for i in ag.rv.IOUS} for k in keys},
         "ie": dict.fromkeys(keys), "flags": dict.fromkeys(keys), "runs": dict.fromkeys(keys), "gv": {"reference_support": {}},
         "checks": {"flag_inputs": dict.fromkeys(keys)}}
    assert ag.camera_result_keys([c]) == sorted(keys)
    del c["ev"]["A|BL-2"]
    with pytest.raises(SystemExit, match="incomplete evaluation record"):
        ag.camera_result_keys([c])
