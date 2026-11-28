"""Historical D-63 gate checks and the development-only SDG camera view.

D-66 is terminal. The former D-63 readiness checks below are retained for fixture coverage.

Gate (D-63 rulings 1, 7, 8; R-2): every item must hold, read from the committed records, before any test camera is
loaded for S3 or later:
  1. X0c complete with 0 violations (`docs/preregistration/test_readiness_v2.json`, R-2);
  2. the window lock applied: the lock artifact verifies, its ID equals `docs/preregistration/window_lock_v2.json`, and
     all 471 windows of V0 `m1a-sdg-test` are locked;
  3. the reporting run finished (D-65 re-run): `research/v2/reporting_rerun_results.json`, 110 cameras, MR-01 1.0;
  4. the test S2 arrived intact (`docs/preregistration/test_s2_arrival_v2.json`, pass, 471 files).
`CameraView` mirrors the fields of `evaluate_m1a.Camera` that `run_v2` reads, but builds them from truth (as
`run_m1a` stored them: `m1a_common.truth_table`, `visible_frames`) and takes the windows from a given V0 / lock artifact.
On validation cameras it must equal `evaluate_m1a.Camera` field for field (checked on the 116 tuning cameras).
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V0_VALIDATION = ROOT / "out/prereg/art_wiaoelxnrzaqb2ii44esa47k3f"
V0_TEST = ROOT / "out/prereg/art_hfchmhd3zbgjl24gnqaxifaoo3"
LOCK_RECORD = ROOT / "docs/preregistration/window_lock_v2.json"
READINESS = ROOT / "docs/preregistration/test_readiness_v2.json"
REPORTING = ROOT / "research/v2/reporting_rerun_results.json"
ARRIVAL = ROOT / "docs/preregistration/test_s2_arrival_v2.json"
TEST_CAMERAS = 471


def gate_items(readiness: dict, lock_record: dict, lock_id: str | None, locked: int, reporting: dict | None, arrival: dict | None) -> dict:
    """The four gate items as booleans (pure; the driver reads the records)."""
    x0c = next((i for i in readiness.get("items", []) if i.get("item") == "X0c complete (R-2)"), None)
    return {"x0c_complete": bool(x0c and x0c["result"] == "pass" and x0c["evidence"].get("violations") == 0),
            "window_lock_applied": lock_id is not None and lock_id == lock_record.get("lock_artifact") and locked == TEST_CAMERAS,
            "reporting_run_finished": bool(reporting and reporting.get("cameras") == 110 and (reporting.get("MR-01") or {}).get("value") == 1.0),
            "test_s2_arrived": bool(arrival and arrival.get("pass") is True and arrival.get("cameras_verified") == TEST_CAMERAS)}


def gate() -> dict:
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


class CameraView:
    """The camera fields `run_v2.run_camera` reads, from simulator truth (`m1a_common.Loaded`) and a window artifact."""

    def __init__(self, ctx, rec: str, cam: dict, data, window_dir: Path):
        import sys
        sys.path.insert(0, str(ROOT / "research/m1a"))
        import m1a_common as m
        from rq1.ids import artifact as A
        from rq1.schema import files
        if window_dir.absolute() != V0_VALIDATION or window_dir.resolve() != V0_VALIDATION:
            raise SystemExit("refused: the v2 camera view only loads development windows after D-66")
        if m.Context.camera(ctx, rec) != cam:
            raise SystemExit("refused: the v2 development camera does not match its registration")
        self.ds, self.rec = "sdg", rec
        self.camera_name, self.run = cam["camera"], cam["run"]
        self.truth_rows, self.visible = m.truth_table(data), m.visible_frames(data)
        self.classes = {r[0]: r[1] for r in self.truth_rows}
        self.truth = {(r[0], r[2]): r for r in self.truth_rows}
        self.frames = data.s1["frame"]
        s1dir = ROOT / f"out/t17_sdg/{cam['s1']}"
        self.coverage = files.read_table(str(s1dir / "coverage_segment.parquet"), "coverage_segment", A.SCHEMA_VERSION)
        self.timeline = self.coverage[0]["timeline_id"]
        self.eligible = {f["frame_index"]: f for f in self.frames if f["eligible"]}
        rw = files.read_table(str(window_dir / "reference_window.parquet"), "reference_window", A.SCHEMA_VERSION)
        self.windows = sorted((w for w in rw if w["timeline_id"] == self.timeline), key=lambda w: w["window_index"])
        if len(self.windows) != 1:
            raise SystemExit(f"STOP: {rec}: {len(self.windows)} windows (SDG has one per camera)")
        self.window = self.windows[0]

    def support(self, window=None) -> dict[int, float]:
        """As `evaluate_m1a.Camera.support` (E-1.2.1 section 3.4)."""
        window = window or self.window
        a, b = window["t_start_tl_s"], window["t_end_tl_s"]
        out = {}
        for i, f in self.eligible.items():
            if f["support_s"] and f["support_start_tl_s"] is not None:
                s = max(0.0, min(f["support_start_tl_s"] + f["support_s"], b) - max(f["support_start_tl_s"], a))
                if s > 0:
                    out[i] = s
        return out
