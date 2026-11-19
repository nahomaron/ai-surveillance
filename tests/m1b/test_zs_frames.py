"""T-22 zero-shot probe frame selection (Owner instruction of 19 Nov 2026, item 3): reproducible from the seed, and no
test-partition recording can be selected (D-37). Uses committed files only (freeze record, T17 counts)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import zero_shot_frames as zf  # noqa: E402


def _cams(run, n_ceiling, n_eye, s3="art_x"):
    return ([{"rec_id": f"rec_{run}_c{i:02d}", "run": run, "camera": f"ceiling_{i:02d}", "s3": s3} for i in range(n_ceiling)]
            + [{"rec_id": f"rec_{run}_e{i:02d}", "run": run, "camera": f"eye_{i:02d}", "s3": s3} for i in range(n_eye)])


@pytest.mark.determinism
def test_selection_is_reproducible_from_the_seed():
    cameras, val = zf.committed_inputs()
    a, b = zf.select(cameras, val, zf.SEED), zf.select(cameras, val, zf.SEED)
    assert a == b
    assert zf.SEED == 2026111901
    assert [c["viewpoint"] for c in a] == ["ceiling"] * 10 + ["eye_level"] * 10
    assert len({c["rec_id"] for c in a}) == 20
    assert zf.select(cameras, val, zf.SEED + 1) != a  # the seed matters


@pytest.mark.determinism
def test_selection_matches_the_committed_probe_record():
    """The cameras and frames in research/m1b/zero_shot_probe.json are the ones the seeded draw gives."""
    rec = json.load(open(ROOT / "research/m1b/zero_shot_probe.json"))
    cameras, val = zf.committed_inputs()
    sel = zf.select(cameras, val)
    assert [c["rec_id"] for c in sel] == [c["rec_id"] for c in rec["selection"]["cameras"]]
    frames = [(f["rec_id"], f["frame_index"]) for f in rec["selection"]["frames"]]
    assert frames == [(c["rec_id"], i) for c in sel for i in zf.even_positions(300)]


def test_even_positions_hand_values():
    # floor((2j + 1) * 300 / 10), j = 0..4
    assert zf.even_positions(300) == [30, 90, 150, 210, 270]
    assert zf.even_positions(10) == [1, 3, 5, 7, 9]


def test_test_partition_recording_is_refused_d_37():
    cam = {"rec_id": "rec_t", "run": "run_test", "camera": "ceiling_00", "s3": "art_t"}
    with pytest.raises(zf.LeakageError) as e:
        zf.require_validation(cam, ["run_val"])
    assert e.value.code == "ERR-LEAKAGE"


def test_test_partition_cameras_are_never_drawn():
    cams = _cams("run_val", 10, 10) + _cams("run_test", 40, 40)
    for seed in range(50):
        assert {c["run"] for c in zf.select(cams, ["run_val"], seed)} == {"run_val"}
    with pytest.raises(ValueError):  # the pool is validation-only, so too few validation cameras cannot be filled from test
        zf.select(_cams("run_val", 9, 10) + _cams("run_test", 40, 40), ["run_val"])


def test_cameras_without_oracle_s3_are_not_drawn():
    cams = _cams("run_val", 10, 10) + _cams("run_val2", 10, 10, s3=None)
    assert {c["run"] for c in zf.select(cams, ["run_val", "run_val2"], 7)} == {"run_val"}


def test_committed_selection_is_all_validation():
    cameras, val = zf.committed_inputs()
    assert all(c["run"] in set(val) for c in zf.select(cameras, val))


def test_clip_box():
    assert zf.clip_box((-5.0, 10.0, 30.0, 1090.0), 1920, 1080) == (0.0, 10.0, 30.0, 1080.0)
    assert zf.clip_box((1920.0, 0.0, 1930.0, 5.0), 1920, 1080) is None
