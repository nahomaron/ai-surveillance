"""D-55 step 2: S3 run configuration with `tracker_id`; regression on column C (CR-033).

Expected values:
- COLUMN_C is the tracker configuration recorded in every stored column C `pipeline.json` (206 cameras, one distinct
  value); TRC_C is the configuration ID in every stored column C S3 manifest (`spec.config_ids`, one distinct value).
  Both were read from the stored pilot outputs, not computed by the code under test.
- Adding `tracker_id` to the column C configuration would change TRC_C, so the column C case is returned unchanged.
- Stored-artifact check (skipped when the pilot outputs are absent): one column C camera's S3 artifact is rebuilt from
  its stored tracker log, stored S2 and S1 with its stored spec, and its artifact ID equals the stored one.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from rq1.tracking import s3_config as sc

ROOT = Path(__file__).resolve().parents[2]
COLUMN_C = {"assignment": "ultralytics.utils.ops.linear_sum_assignment (use_lap=False)", "library": "ultralytics 8.4.215",
            "params": {"fuse_score": True, "match_thresh": 0.8, "new_track_thresh": 0.25, "track_buffer": 30, "track_high_thresh": 0.25,
                       "track_low_thresh": 0.1, "tracker_type": "bytetrack"},
            "per_class": ["person", "forklift"], "step": "one update per eligible frame", "tracker": "BYTETracker"}
TRC_C = "trc_i4ljlcifrwgephzz4cgjkmo5ej"


def per_class(forklift_tracker="bytetrack", forklift_params=None):
    return {"person": {"tracker_id": "bytetrack", "params": COLUMN_C["params"]},
            "forklift": {"tracker_id": forklift_tracker, "params": forklift_params or COLUMN_C["params"]}}


def test_column_c_configuration_and_id_unchanged():
    cfg = sc.run_config(copy.deepcopy(COLUMN_C), per_class())
    assert cfg == COLUMN_C and "tracker_id" not in json.dumps(cfg)
    assert sc.trc_id(cfg, 15) == TRC_C


def test_adding_the_field_would_change_column_c_id():
    """Why the field is left out for column C (CR-033)."""
    assert sc.trc_id({**COLUMN_C, "tracker_id": "bytetrack"}, 15) != TRC_C


def test_other_configurations_carry_tracker_id_per_class():
    p = {**COLUMN_C["params"], "track_low_thresh": 0.05}
    a = sc.run_config(COLUMN_C, per_class("bytetrack", p))
    b = sc.run_config(COLUMN_C, per_class("botsort", {**p, "tracker_type": "botsort", "gmc_method": "none", "with_reid": False}))
    assert a["classes"]["forklift"]["tracker_id"] == "bytetrack" and b["classes"]["forklift"]["tracker_id"] == "botsort"
    assert a["classes"]["person"] == {"tracker_id": "bytetrack", "tracker": "BYTETracker", "params": COLUMN_C["params"]}
    assert len({sc.trc_id(a, 15), sc.trc_id(b, 15), TRC_C}) == 3
    with pytest.raises(ValueError):
        sc.run_config(COLUMN_C, {"forklift": per_class()["forklift"]})
    with pytest.raises(ValueError):
        sc.run_config(COLUMN_C, per_class("sort"))


def _stored_camera():
    cams = sorted((ROOT / "out/m1b/pilot/cam").glob("*/pipeline.json")) if (ROOT / "out/m1b/pilot/cam").exists() else []
    return cams[0].parent if cams else None


@pytest.mark.skipif(_stored_camera() is None, reason="stored pilot outputs absent")
def test_column_c_stored_s3_artifact_reproduces():
    sys.path.insert(0, str(ROOT / "research/m1b"))
    import run_pilot as rp
    from rq1.ids.artifact import Spec
    from rq1.schema import files
    from rq1.tracking import bridging
    from rq1.tracking.s3 import DetectorTrackSource
    d = _stored_camera()
    pipe = json.loads((d / "pipeline.json").read_text())
    assert pipe["tracker_config"] == COLUMN_C
    man = json.loads((rp.pc.OUT / "artifacts" / pipe["s3"] / "manifest.json").read_text())
    s = man["spec"]
    assert s["config_ids"] == [sc.trc_id(sc.run_config(COLUMN_C, per_class()), 15)]
    log = json.loads((d / "tracker_out.json").read_text())
    pts = {c: bridging.points_from_log(log["logs"][c], 15) for c in ("person", "forklift")}
    dets = rp.load_artifact_tables(pipe["s2"])["detection"]
    frames = files.read_table(str(ROOT / f"out/t17_sdg/{pipe['s1']}/frame.parquet"), "frame", rp.m.A.SCHEMA_VERSION)
    spec = Spec("S3", s["schema_bundle"], s["code_commit"], s["environment_digest"], tuple(s["config_ids"]), tuple(s["input_artifact_ids"]), {})
    art, _ = DetectorTrackSource().tracks(pipe["rec_id"], pts, dets, frames, spec)
    assert art.artifact_id == pipe["s3"]
