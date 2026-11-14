"""Appendix T T17 (E-1.2.15): oracle track points and reference visibility from simulator truth.

Hand camera (as in test_smartspaces): K = [[1000, 0, 960], [0, 1000, 540], [0, 0, 1]], R = diag(1, -1, -1), t = (0, 0, 10):
at world (0, 0, 10), looking straight down, image 1920 x 1080. Hand box: x 0.8..1.2, y 1.8..2.2, z 0..1. Top face at
camera depth 9, bottom at 10: u from 960 + 800/10 = 1040 to 960 + 1200/9 = 1093.33; v from 540 - 2200/9 = 295.56 to
540 - 1800/10 = 360. Its image-clipped reprojection is therefore (1040, 295.56, 1093.33, 360).
Dataset boxes are inclusive pixel indices; in CF-IMG the tight box (1045, 300, 1090, 355) is (1045, 300, 1091, 356)."""
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from rq1.adapters import oracle_truth as ot
from rq1.adapters import sdg_camera, sdg_truth, smartspaces
from rq1.schema.errors import ContractError

CAL = {"intrinsics_K": [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0], "R_cam_from_world": [1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0],
       "t_cam_from_world_m": [0.0, 0.0, 10.0], "image_size_px": [1920, 1080]}
REPRO = (1040.0, 540 - 2200 / 9, 960 + 1200 / 9, 360.0)
TIGHT = (1045, 300, 1090, 355)  # dataset pixel indices
TIGHT_IMG = (1045.0, 300.0, 1091.0, 356.0)  # CF-IMG: max edges + 1
LOOSE = (1040, 296, 1093, 360)  # excess 0 against the reprojection
ROOT = Path(__file__).resolve().parents[2]


def sdg_obj(tight=TIGHT, loose=LOOSE, at=(1.0, 2.0, 0.0), prim=sdg_truth.FORKLIFT_PRIM):
    box3d = {"x_min": -0.2, "x_max": 0.2, "y_min": -0.2, "y_max": 0.2, "z_min": 0.0, "z_max": 1.0,
             "transform": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [at[0], at[1], at[2], 1]]}  # USD row vectors: translation in the last row
    return sdg_truth.ObjectTruth(prim, "forklift", (at[0], at[1]), 0.0, loose, tight, box3d)


def obs(**kw):
    return ot.sdg_obs(CAL, sdg_obj(**kw))[0]


@pytest.mark.determinism
def test_clipped_reprojection_hand_values():
    assert ot.clipped_reprojection(CAL, sdg_truth.box_corners(sdg_obj().box3d)) == pytest.approx(REPRO, abs=1e-9)
    # outside the image: at x = 100 m, u = 960 + 1000 x 99.8 / 10 > 1919
    assert ot.clipped_reprojection(CAL, sdg_truth.box_corners(sdg_obj(at=(100.0, 2.0, 0.0)).box3d)) is None
    # behind the camera: the whole box above the camera height of 10 m
    assert ot.clipped_reprojection(CAL, sdg_truth.box_corners(sdg_obj(at=(1.0, 2.0, 20.0)).box3d)) is None
    # straddling the camera plane on its axis: the part in front fills the image
    assert ot.clipped_reprojection(CAL, sdg_truth.box_corners(sdg_obj(at=(0.0, 0.0, 9.5)).box3d)) == pytest.approx((0.0, 0.0, 1920.0, 1080.0), abs=1e-6)
    # partly outside: x 0.8..1.2 moved to 9.4..9.8 -> u from 960 + 9400/10 = 1900 to beyond the image: clipped at W = 1920
    box = ot.clipped_reprojection(CAL, sdg_truth.box_corners(sdg_obj(at=(9.6, 2.0, 0.0)).box3d))
    assert box[0] == pytest.approx(1900.0) and box[2] == pytest.approx(1920.0)


def test_t17_1_visible_is_tracked_with_the_tight_box():
    tracks, counts = ot.camera_tracks(CAL, [{"f": obs()}])
    (p,) = tracks["f"]
    assert (p.decode_seq, p.state, p.box) == (0, "tracked", TIGHT_IMG)  # the tight box (in CF-IMG), never the loose one
    assert p.xy == (1.0, 2.0) and p.yaw == 0.0
    assert counts == {"tracked": 1, "predicted": 0, "lost": 0, "outside_span": 0, "never_visible_objects": 0}


def test_t17_2_interior_gap_is_predicted_with_the_reprojected_box():
    tracks, counts = ot.camera_tracks(CAL, [{"f": obs()}, {"f": obs(tight=None)}, {"f": obs()}])
    states = [(p.decode_seq, p.state) for p in tracks["f"]]
    assert states == [(0, "tracked"), (1, "predicted"), (2, "tracked")]
    assert tracks["f"][1].box == pytest.approx(REPRO, abs=1e-9) and tracks["f"][1].xy == (1.0, 2.0)  # position = the simulator pose
    assert (counts["tracked"], counts["predicted"], counts["lost"]) == (2, 1, 0)


@pytest.mark.parametrize("at", [(100.0, 2.0, 0.0), (1.0, 2.0, 20.0)])  # outside the image; behind the camera
def test_t17_2_empty_reprojection_is_lost(at):
    tracks, counts = ot.camera_tracks(CAL, [{"f": obs()}, {"f": obs(tight=None, loose=None, at=at)}, {"f": obs()}])
    assert [p.decode_seq for p in tracks["f"]] == [0, 2]  # no point on the lost frame
    assert (counts["tracked"], counts["predicted"], counts["lost"]) == (2, 0, 1)


def test_t17_2_frame_without_a_truth_record_is_lost():
    tracks, counts = ot.camera_tracks(CAL, [{"f": obs()}, {}, {"f": obs()}])
    assert [p.decode_seq for p in tracks["f"]] == [0, 2] and counts["lost"] == 1


def test_t17_3_no_point_outside_the_visible_span_and_no_track_when_never_visible():
    hidden = obs(tight=None)
    frames = [{"f": hidden, "g": hidden}, {"f": obs(), "g": hidden}, {"f": hidden, "g": hidden}]
    tracks, counts = ot.camera_tracks(CAL, frames)
    assert list(tracks) == ["f"] and [p.decode_seq for p in tracks["f"]] == [1]  # leading and trailing frames: no point
    assert counts == {"tracked": 1, "predicted": 0, "lost": 0, "outside_span": 5, "never_visible_objects": 1}  # g: never visible, no track


def test_t17_4_line_count_mismatch_or_missing_parameters_is_no_truth():
    assert ot.usable_truth(300, {"object_detection": 300, "camera_params": 300})
    assert not ot.usable_truth(300, {"object_detection": 298, "camera_params": 300})
    assert not ot.usable_truth(300, {"object_detection": 300, "camera_params": 131})
    assert not ot.usable_truth(300, {"object_detection": 300, "camera_params": None})  # camera parameters do not exist
    assert not ot.usable_truth(300, {})
    with pytest.raises(ContractError):
        sdg_truth.parse_camera(['{"agents": {}}'] * 298, 300)


def test_t17_5_truth_defect_is_treated_as_not_visible():
    wide = (LOOSE[0] - 300, LOOSE[1], LOOSE[2], LOOSE[3])  # excess 300 px > 157
    o, note = ot.sdg_obs(CAL, sdg_obj(loose=wide, tight=wide))
    assert note == "truth_defect" and o.visible is None and o.xy == (1.0, 2.0)  # 2D truth discarded, 3D pose kept
    tracks, counts = ot.camera_tracks(CAL, [{"f": obs()}, {"f": o}, {"f": obs()}])
    assert [(p.decode_seq, p.state) for p in tracks["f"]] == [(0, "tracked"), (1, "predicted"), (2, "tracked")]
    assert tracks["f"][1].box == pytest.approx(REPRO, abs=1e-9)
    # a defect on the last visible frame falls outside the visible span: no point (T17.3)
    tracks, _ = ot.camera_tracks(CAL, [{"f": obs()}, {"f": o}])
    assert [p.decode_seq for p in tracks["f"]] == [0]


@pytest.mark.parametrize("excess,outcome", [(80.0, None), (80.5, "refuse"), (100.0, "refuse"), (157.0, "refuse"), (157.5, "truth_defect"), (0.0, None)])
def test_t17_5_refusal_band(excess, outcome):
    loose = (LOOSE[0] - excess, LOOSE[1], LOOSE[2], LOOSE[3])  # the reprojection's left edge is exactly 1040
    if outcome == "refuse":
        with pytest.raises(ContractError) as e:
            ot.sdg_obs(CAL, sdg_obj(loose=loose))
        assert e.value.code == "ERR-INVARIANT"
    else:
        assert ot.sdg_obs(CAL, sdg_obj(loose=loose))[1] == outcome


def test_t17_5_corner_behind_the_camera_is_unchecked():
    o, note = ot.sdg_obs(CAL, sdg_obj(at=(0.0, 0.0, 9.5)))
    assert note == "unchecked" and o.visible == TIGHT


def test_smartspaces_object_absent_from_a_cameras_visible_list():
    def frame(visible):
        return smartspaces.parse_object({"object type": "Forklift", "object id": 4, "3d location": [1.0, 2.0, 0.5], "3d bounding box scale": [0.4, 0.4001, 1.0],
                                         "3d bounding box rotation": [0.0, 0.0, 0.0], "2d bounding box visible": visible})
    seen, hidden = frame({"A": [1045, 300, 1090, 355], "B": [5, 5, 9, 9]}), frame({"B": [5, 5, 9, 9]})
    frames = [{4: ot.smartspaces_obs(o, "A")} for o in (hidden, seen, hidden, seen, hidden)]
    tracks, counts = ot.camera_tracks(CAL, frames)
    assert [(p.decode_seq, p.state) for p in tracks[4]] == [(1, "tracked"), (2, "predicted"), (3, "tracked")]  # T17.2 inside, T17.3 outside
    assert tracks[4][1].box == pytest.approx((1040.0, 540 - 2200.05 / 9, 960 + 1200 / 9, 540 - 1799.95 / 10), abs=1e-6)
    assert counts["outside_span"] == 2
    never, _ = ot.camera_tracks(CAL, [{4: ot.smartspaces_obs(hidden, "A")}])
    assert never == {}


def test_s3_truth_and_reference_objects_use_eligible_frames_only():
    frames = [{"f": obs()}, {"f": obs(tight=None)}, {"f": obs()}, {"f": obs()}]
    tracks, _ = ot.camera_tracks(CAL, frames)
    seq_to_index = {0: 0, 1: 1, 2: None, 3: 2}  # decode_seq 2 is not eligible (no frame_index)
    truth, positions = ot.s3_truth(tracks, {"f": "forklift"}, seq_to_index)
    assert [(p["frame_index"], p["state"]) for p in truth[0]["points"]] == [(0, "tracked"), (1, "predicted"), (2, "tracked")]
    assert truth[0]["local_id"] == 1 and truth[0]["class"] == "forklift"
    assert positions[(1, 1)] == {"xy": [1.0, 2.0], "cov": [0.0, 0.0, 0.0], "yaw": 0.0}
    (ref,) = ot.reference_objects(tracks, {"f": "forklift"}, seq_to_index)
    assert sorted(ref["frames"]) == [0, 2] and ref["frames"][0] == {"bbox": list(TIGHT_IMG), "xy": [1.0, 2.0]}  # T17.6: visible frames only
    assert ot.s3_truth(tracks, {"f": "forklift"}, {})[0] == []  # no eligible frame: no track


def test_the_five_eye_01_frames_of_run_2_seed_516797828_are_truth_defects():
    """T17 test on the held data (git-ignored); skipped where the shard is absent."""
    tar = ROOT / "data/raw/sdg/artifacts/forklift_human_nearmiss/nearmiss-artifacts-00538.tar"
    if not tar.exists():
        pytest.skip("held SDG shard 00538 not present")
    run = "f1d9f0ca9eb2cd77acc2_fb11684081300a3c4725_run_2_seed_516797828"
    with tarfile.open(tar) as tf:
        names = {m.name: m for m in tf.getmembers()}
        read = lambda suffix: tf.extractfile(names[f"{run}.eye_01.{suffix}"]).read().decode().splitlines()
        cal = sdg_camera.calibration(sdg_camera.static_params([json.loads(l) for l in read("camera_params.jsonl")]))
        lines = read("object_detection.jsonl")
    defects, frames = [], []
    for k, line in enumerate(lines):
        row = {}
        for o in sdg_truth.parse_frame(line):
            row[o.prim], note = ot.sdg_obs(cal, o)
            if note == "truth_defect":
                defects.append((k, o.cls))
                assert row[o.prim].visible is None and o.tight is not None  # visible in the file, treated as not visible
        frames.append(row)
    assert defects == [(k, "forklift") for k in (136, 176, 199, 213, 226)]
    tracks, _ = ot.camera_tracks(cal, frames)
    states = {p.decode_seq: p.state for p in tracks[sdg_truth.FORKLIFT_PRIM]}
    assert all(states.get(k) in ("predicted", None) for k in (136, 176, 199, 213, 226))


def test_dataset_pixel_indices_to_cf_img():
    assert ot.cf_img((736, 268, 736, 269)) == (736.0, 268.0, 737.0, 270.0)  # a one-pixel-wide box of the held data: valid in CF-IMG
    assert ot.cf_img((0, 0, 1919, 1079)) == (0.0, 0.0, 1920.0, 1080.0)  # the whole image
    tracks, _ = ot.camera_tracks(CAL, [{"f": obs(tight=(736, 268, 736, 269))}])
    x1, y1, x2, y2 = tracks["f"][0].box
    assert x1 < x2 and y1 < y2
