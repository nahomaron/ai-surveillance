"""T-21 run driver (research/m1a): D-37 enforcement and the T21.1 reference tracks (contract E-1.2.19)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/m1a"))
import m1a_common as m  # noqa: E402
from rq1.adapters import oracle_truth as ot  # noqa: E402
from rq1.schema.errors import ContractError  # noqa: E402


def _ctx(ds):
    ctx = m.Context.__new__(m.Context)
    ctx.ds = ds
    ctx.freeze = {"split": {"sdg_validation_runs": ["run_val"]}}
    ctx.counts = {"cameras": [{"rec_id": "rec_v", "run": "run_val", "s3": "art_a"}, {"rec_id": "rec_t", "run": "run_test", "s3": "art_b"},
                              {"rec_id": "rec_n", "run": "run_val", "s3": None}]}
    return ctx


@pytest.mark.determinism
def test_driver_refuses_a_test_partition_recording_d_37():
    ctx = _ctx("sdg")
    assert ctx.camera("rec_v")["run"] == "run_val"
    with pytest.raises(ContractError) as e:
        ctx.camera("rec_t")
    assert e.value.code == "ERR-LEAKAGE"
    assert [c["rec_id"] for c in ctx.validation_cameras()] == ["rec_v"]  # rec_n has no ORACLE-S3 (T17.4)


@pytest.mark.determinism
def test_smartspaces_validation_is_warehouse_000_only():
    ctx = _ctx("smartspaces")
    ctx.counts = {"cameras": [{"rec_id": "a", "run": "Warehouse_000", "s3": "x"}, {"rec_id": "b", "run": "Warehouse_001", "s3": "y"}]}
    assert ctx.camera("a")
    with pytest.raises(ContractError):
        ctx.camera("b")


@pytest.mark.determinism
def test_t21_1_reference_tracks_cover_every_eligible_frame_with_a_pose():
    # Object "p" exists on decoded frames 0-4 and is dataset-visible on 0 only; "f" exists on 1-4, never visible.
    # Frame 3 is ineligible. T21.1: a tracked point on every eligible frame with a pose, whatever the visibility.
    vis = (0, 0, 9, 9)
    frames = [{"p": ot.Obs("person", vis, None, (0.0, 0.0), None)}] + \
             [{"p": ot.Obs("person", None, None, (float(k), 0.0), None), "f": ot.Obs("forklift", None, None, (float(k), 2.0), 0.0)} for k in range(1, 5)]
    seq = {0: 0, 1: 1, 2: 2, 3: None, 4: 3}
    data = m.Loaded({"decode_summary": [{"width_px": 100, "height_px": 80}]}, frames, {"p": "person", "f": "forklift"}, seq, None)
    tracks = m.reference_tracks(data)
    assert [p.decode_seq for p in tracks["p"]] == [0, 1, 2, 4] and [p.decode_seq for p in tracks["f"]] == [1, 2, 4]
    assert all(p.state == "tracked" and p.box == (25.0, 20.0, 75.0, 60.0) for t in tracks.values() for p in t)
    assert tracks["f"][0].xy == (1.0, 2.0) and tracks["f"][0].yaw == 0.0
    # T21.3 input: visible frames are dataset-visible AND eligible (T20.1), as frame_index.
    assert m.visible_frames(data) == {"p": [0], "f": []}  # every object has an entry; f is never visible
