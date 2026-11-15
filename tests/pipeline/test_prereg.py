"""G-PR freeze values (D-34, D-35). Expected values are the Owner's, copied from D-34 / D-35 (DECISIONS_NEEDED.md)."""
import math

from rq1.pipeline import prereg


def test_split_values_d_34_b2_d_35():
    assert prereg.SPLIT_SEED == 2026111401 and prereg.TIER == "T1"
    assert prereg.SDG_VALIDATION_PER_FAMILY == {"warehouse_osmos": 12, "warehouse_osmos_2": 7, "warehouse_osmos_1": 5}
    assert sum(prereg.SDG_VALIDATION_PER_FAMILY.values()) == 24  # 24 validation / 48 test of 72
    assert prereg.SPLIT_DRAW_RECORD["smartspaces_synthetic_group"] == "validation"


def test_sampling_bootstrap_and_turning_values():
    assert prereg.SAMPLING == {"sdg": {"w_ref_s": 10.0, "w_guard_s": 0.0}, "smartspaces_000": {"w_ref_s": 30.0, "w_guard_s": 5.0}}
    assert (prereg.BOOTSTRAP_B, prereg.BOOTSTRAP_SEED, prereg.CI_LEVEL) == (2000, 2026111402, 0.95)
    assert (prereg.W_TURN_S, prereg.E_FTURN_DEG_S, prereg.E_FTURN_SENSITIVITY_DEG_S) == (0.5, 5.0, (2.0, 10.0))
    assert math.isclose(prereg.E_FTURN_RAD_S, 0.0872664626, abs_tol=1e-10)


def test_criteria_d_34_b7():
    rows = prereg.criteria()
    got = [(r["metric_id"], r["rule"], r["target"], r["n_min_units"], r["slice"].get("viewpoint_class")) for r in rows]
    assert got == [("MR-01", "exact_equal", 1.0, 1, None), ("GV-01", "ci_upper_le", 0.25, 20, "ceiling"), ("GV-01", "ci_upper_le", 0.25, 20, "eye_level"),
                   ("GV-07", "ci_upper_le", 0.15, 20, None), ("GV-04", "abs_bias_ci_within", 0.10, 20, None)]
    assert all(r["frozen_utc"] == prereg.FROZEN_UTC and r["preregistration_ref"] == prereg.PREREGISTRATION_REF and r["ci_level"] == 0.95 for r in rows)
    assert all(r["slice"]["partition"] == "test" for r in rows[1:])
    assert len({r["acc_id"] for r in rows}) == 5 and rows == prereg.criteria()  # deterministic IDs
    assert not {"CM-03", "CM-08", "EV-M1", "EV-M2", "MR-08"} & {r["metric_id"] for r in rows}  # criteria #5-#10 not registered
