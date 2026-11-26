"""Pre-registration v2 freeze (Owner decision D-61, 26 Nov 2026; contract E-1.2.26).

The registered criteria of v2 (D-61 section 1.6): targets, rules, slices, estimands and n_min unchanged from v1 (`prereg.criteria`),
version 2, with the new basis "each measurement error is at most half the threshold it decides" (GV-01 0.25 m = d_nm / 2;
GV-07 0.15 m/s = v_min / 2). The basis is stated in `docs/preregistration_v2_FROZEN.md` and the freeze record; it is not
an acceptance_criterion field. The v1 records (`prereg.py`) are never changed.
"""
from __future__ import annotations

from datetime import datetime, timezone

from rq1.ids import core
from rq1.pipeline import prereg
from rq1.schema.validate import validate_rows

CONTRACT = "E-1.2.26"
PREREGISTRATION_REF = "docs/preregistration_v2_FROZEN.md, version 2"
VERSION = "2"
FROZEN_UTC = datetime(2026, 11, 26, 14, 29, 25, tzinfo=timezone.utc)  # supplied event time of the v2 freeze (taken once, AR-57 item 6)

# D-61 section 1.6: the half-threshold basis of each registered target
BASIS = {"C1-MR-01": "repeatability: every exact-class artifact identical (unchanged from v1)",
         "C2-GV-01-ceiling": "0.25 m = d_nm / 2 (d_nm 0.5 m)", "C2-GV-01-eye_level": "0.25 m = d_nm / 2 (d_nm 0.5 m)",
         "C3-GV-07": "0.15 m/s = v_min / 2 (v_min 0.3 m/s)",
         "C4-GV-04": "0.10 m (unchanged); GV-04 is circular (the prior is the dataset box): reported, never cited as evidence"}


def criteria() -> list[dict]:
    """The v1 criteria #1-#4 with version 2, the v2 reference and the v2 freeze time; content-addressed acc IDs."""
    rows = []
    for r in prereg.criteria():
        row = {k: v for k, v in r.items() if k != "acc_id"}
        row.update({"version": VERSION, "preregistration_ref": PREREGISTRATION_REF, "frozen_utc": FROZEN_UTC})
        rows.append(row)
    validate_rows("acceptance_criterion", rows, raise_fatal=True)
    return [{"acc_id": core.make_id("acc", {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items()}), **r} for r in rows]
