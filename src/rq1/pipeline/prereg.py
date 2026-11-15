"""M1a pre-registration freeze (G-PR; Owner decisions D-34 and D-35, 14 Nov 2026; contract E-1.2.18).

The Owner's values are written here once, as data, and nowhere else in code. `docs/preregistration_FROZEN.md` states them
in words; `research/preregistration/freeze.py` builds the X0b split, the V0 sampling plans and the acceptance-criterion
records from them.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from rq1.ids import core
from rq1.schema.validate import validate_rows

from rq1.splits import draw

Row = dict[str, Any]
CONTRACT = "E-1.2.18"
PREREGISTRATION_REF = "docs/preregistration_FROZEN.md, version 1"
FROZEN_UTC = datetime(2026, 11, 15, 1, 47, 59, tzinfo=timezone.utc)  # supplied event time of the freeze (taken once, AR-57 item 6)

# D-34 B.2 and D-35 (b): split
SPLIT_LABEL, SPLIT_VERSION, TIER = "m1a", "1", "T1"
SPLIT_SEED = 2026111401
SDG_VALIDATION_PER_FAMILY = {"warehouse_osmos": 12, "warehouse_osmos_1": 5, "warehouse_osmos_2": 7}
SPLIT_DRAW_RECORD = {"rule": "D-34 item B.2, D-35 option (b)", "strata": "batch family", "derivation": draw.DERIVATION,
                     "validation_per_family": SDG_VALIDATION_PER_FAMILY, "seed": SPLIT_SEED, "rng": "numpy PCG64",
                     "smartspaces_synthetic_group": "validation", "tier": TIER}
SPLIT_DRAW_ID = core.make_id("sdr", SPLIT_DRAW_RECORD)

# D-34 B.3, B.10: sampling (census of windows; one camera = one camera group)
SAMPLING = {"sdg": {"w_ref_s": 10.0, "w_guard_s": 0.0}, "smartspaces_000": {"w_ref_s": 30.0, "w_guard_s": 5.0}}
SAMPLING_SEED = SPLIT_SEED  # a census draws nothing; the plan record still names a seed (AR-57 item 4)

# D-34 B.9: bootstrap
BOOTSTRAP_B, BOOTSTRAP_SEED, CI_LEVEL = 2000, 2026111402, 0.95

# D-34 B.6: forklift_turning (T20.2)
W_TURN_S, E_FTURN_DEG_S, E_FTURN_SENSITIVITY_DEG_S = 0.5, 5.0, (2.0, 10.0)
E_FTURN_RAD_S = math.radians(E_FTURN_DEG_S)

SDG_ROW = "SDG-Warehouse near-miss (synthetic_rendered)"
EXACT_CLASS_SLICE = {"run": "M1a run", "stages": "every exact-class artifact of the run"}


def _test_slice(**kw: str) -> dict[str, str]:
    return {"dataset_row": SDG_ROW, "partition": "test", **kw}


def criteria() -> list[Row]:
    """D-34 item B.7: criteria #1-#4 (n_min as drafted). Criterion #2 is one record per viewpoint class (AR accepted at
    the freeze, D-35 reply). Criteria #5-#10 are not registered."""
    common = {"version": "1", "ci_level": CI_LEVEL, "preregistration_ref": PREREGISTRATION_REF, "frozen_utc": FROZEN_UTC}
    rows = [
        # MR-01 value: 1.0 when every exact-class payload hash of the second run equals the first, else 0.0 (AR-57 item 5)
        {"criterion_label": "C1-MR-01", "output_id": "all exact stages", "criterion_type": "repeatability", "metric_id": "MR-01",
         "slice": EXACT_CLASS_SLICE, "rule": "exact_equal", "target": 1.0, "estimand": "frame_description", "n_min_units": 1},
        *[{"criterion_label": f"C2-GV-01-{vc}", "output_id": "object positions", "criterion_type": "technical_accuracy", "metric_id": "GV-01",
           "slice": _test_slice(geometry_method="full_camera", statistic="RMSE", viewpoint_class=vc), "rule": "ci_upper_le", "target": 0.25,
           "estimand": "new_session_performance", "n_min_units": 20} for vc in ("ceiling", "eye_level")],
        {"criterion_label": "C3-GV-07", "output_id": "speed", "criterion_type": "technical_accuracy", "metric_id": "GV-07",
         "slice": _test_slice(geometry_method="full_camera", statistic="speed RMSE", w_v_s="0.5"), "rule": "ci_upper_le", "target": 0.15,
         "estimand": "new_session_performance", "n_min_units": 20},
        {"criterion_label": "C4-GV-04", "output_id": "clearance", "criterion_type": "technical_accuracy", "metric_id": "GV-04",
         "slice": _test_slice(statistic="bias, prior footprint minus simulator 3D box footprint"), "rule": "abs_bias_ci_within", "target": 0.10,
         "estimand": "new_session_performance", "n_min_units": 20},
    ]
    rows = [{**r, **common} for r in rows]
    validate_rows("acceptance_criterion", rows, raise_fatal=True)
    return [{"acc_id": core.make_id("acc", {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items()}), **r} for r in rows]
