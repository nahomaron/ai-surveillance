"""D-61 section 1.6: v2 registered criteria keep the v1 targets, rules, slices and estimands; version 2; new acc IDs."""
from rq1.pipeline import prereg, prereg_v2


def test_v2_criteria_keep_v1_targets_and_rules():
    v1, v2 = prereg.criteria(), prereg_v2.criteria()
    assert [c["criterion_label"] for c in v2] == ["C1-MR-01", "C2-GV-01-ceiling", "C2-GV-01-eye_level", "C3-GV-07", "C4-GV-04"]
    assert [c["target"] for c in v2] == [1.0, 0.25, 0.25, 0.15, 0.10]  # D-61 1.6: targets unchanged (0.25 = 0.5 / 2; 0.15 = 0.3 / 2)
    for a, b in zip(v1, v2):
        for k in ("criterion_label", "metric_id", "slice", "rule", "target", "estimand", "n_min_units", "ci_level", "output_id", "criterion_type"):
            assert a[k] == b[k], k
        assert b["version"] == "2" and b["preregistration_ref"] == "docs/preregistration_v2_FROZEN.md, version 2"
        assert b["frozen_utc"] == prereg_v2.FROZEN_UTC and a["acc_id"] != b["acc_id"]


def test_v2_criteria_are_deterministic_and_v1_unchanged():
    assert prereg_v2.criteria() == prereg_v2.criteria()
    assert [c["acc_id"] for c in prereg.criteria()] == ["acc_tzjtfybncoz2hlqu62w4myrw4n", "acc_eoxyzlbdojmylidna45ultqozf",
                                                         "acc_w3m4qgj3rci5f7gv3cdaujbqmq", "acc_suetxtthdff6bf5r3y76cfsq2z",
                                                         "acc_kmy7qocn5vmwq6ir33mwdevv2m"]  # the v1 freeze record (14 Nov 2026)
    assert set(prereg_v2.BASIS) == {c["criterion_label"] for c in prereg_v2.criteria()}
