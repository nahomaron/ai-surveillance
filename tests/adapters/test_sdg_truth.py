"""T-18 part B: SDG per-camera truth (classes by prim name, floor pose from the 3D box, raw 2D boxes) and the truth
round trip through the part A calibration. Expected values are hand calculations written beside each assertion."""
import json
import math

import numpy as np
import pytest

from rq1.adapters import sdg_camera, sdg_truth
from rq1.schema.errors import ContractError
from rq1.substrate import geometry

# Row-vector transform: local x -> world (0, 1, 0), local y -> world (-1, 0, 0) (90 deg about z), translation (10, 5, 0).
T90 = [[0.0, 1.0, 0.0, 0.0], [-1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [10.0, 5.0, 0.0, 1.0]]
BOX = {"x_min": -2.0, "x_max": 1.0, "y_min": -0.5, "y_max": 0.5, "z_min": 0.0, "z_max": 3.0, "transform": T90}


def agent(cls, box3d=BOX, loose=(10, 20, 30, 40), tight=(12, 22, 28, 38)):
    ann = {"bounding_box_3d_fast": box3d}
    if loose:
        ann["bounding_box_2d_loose_fast"] = dict(zip(("x_min", "y_min", "x_max", "y_max"), loose))
    if tight:
        ann["bounding_box_2d_tight_fast"] = dict(zip(("x_min", "y_min", "x_max", "y_max"), tight))
    return {"label": {"class": cls}, "annotators": ann}


@pytest.mark.determinism
def test_floor_pose_hand_values():
    # Local floor-face centre ((-2 + 1)/2, 0, 0) = (-0.5, 0, 0). World x = -0.5 * T00 + T30 = 10; y = -0.5 * T01 + T31 = 4.5.
    # Yaw = atan2(T01, T00) = atan2(1, 0) = pi/2.
    xy, yaw = sdg_truth.floor_pose(BOX)
    assert xy == pytest.approx((10.0, 4.5), abs=1e-12) and yaw == pytest.approx(math.pi / 2, abs=1e-12)
    # 180 deg: T00 = -1, T01 = -0.0 -> atan2 gives -pi, wrapped to +pi ((-pi, pi]).
    flip = {**BOX, "transform": [[-1.0, -0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]}
    assert sdg_truth.floor_pose(flip)[1] == math.pi


@pytest.mark.determinism
def test_classes_by_prim_name_and_label():
    assert sdg_truth.object_class(sdg_truth.FORKLIFT_PRIM, {"label": {"class": "robot"}}) == "forklift"
    assert sdg_truth.object_class("/World/Characters/Worker/Worker_0/ManRoot/x", {"label": {"class": "character"}}) == "person"
    assert sdg_truth.object_class("/World/Robots/other/Robot", {"label": {"class": "robot"}}) is None  # not identified by class


@pytest.mark.determinism
def test_parse_frame_reads_boxes_and_visibility():
    line = json.dumps({"agents": {sdg_truth.FORKLIFT_PRIM: agent("robot", tight=None),
                                  "/World/Characters/Worker/Worker_0/ManRoot/m": agent("character"),
                                  "/World/Robots/cart/Cart": agent("robot"),
                                  "/World/Characters/Worker/Worker_1/ManRoot/m": {"label": {"class": "character"}, "annotators": {}}},
                       "objects": {}})
    objs = sdg_truth.parse_frame(line)
    # Sorted by prim; the cart is not an E1 object; Worker_1 has no 3D box (no pose) and is left out.
    assert [(o.cls, o.prim) for o in objs] == [("person", "/World/Characters/Worker/Worker_0/ManRoot/m"), ("forklift", sdg_truth.FORKLIFT_PRIM)]
    person, fork = objs
    assert person.tight == (12, 22, 28, 38) and fork.tight is None and fork.loose == (10, 20, 30, 40)
    assert fork.xy == pytest.approx((10.0, 4.5)) and fork.yaw == pytest.approx(math.pi / 2)


@pytest.mark.determinism
def test_parse_camera_refuses_line_count_mismatch():
    line = json.dumps({"agents": {}, "objects": {}})
    assert len(sdg_truth.parse_camera([line] * 3, 3)) == 3
    with pytest.raises(ContractError) as err:
        sdg_truth.parse_camera([line] * 3, 4)
    assert err.value.code == "ERR-INVARIANT"


def oblique_camera():
    """USD camera 6 m above (0, -4), pitched 40 deg down from horizontal, looking along +y. Camera-to-world M (row vectors):
    rows are the camera's x, y, z axes in world, then its position; the USD camera looks down its -z."""
    a = math.radians(40)
    fwd = np.array([0.0, math.cos(a), -math.sin(a)])
    x = np.array([1.0, 0.0, 0.0])
    z = -fwd
    y = np.cross(z, x)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3], m[3, :3] = x, y, z, (0.0, -4.0, 6.0)
    view = np.linalg.inv(m)
    proj = [1.732050852618065, 0, 0, 0, 0, 3.0792015157654484, 0, 0, 0.0, 0.0, 1e-9, -1.0, 0, 0, 0.01, 0]
    return sdg_camera.calibration({"cameraViewTransform": list(view.ravel()), "cameraProjection": proj, "cameraModel": "pinhole",
                                   "renderProductResolution": [1920, 1080], "metersPerSceneUnit": 1.0})


@pytest.mark.determinism
def test_truth_round_trip_through_calibration():
    # WP-13 test: a truth floor point -> pixel (part A projection) -> floor (S4 full_camera ray-floor intersection) returns
    # the same point within 1e-6 m.
    cal = oblique_camera()
    for x, y in [(0.0, 3.0), (2.5, 1.0), (-1.75, 6.5), (10.0, 4.5)]:
        uv = sdg_camera.project(cal, np.array([[x, y, 0.0]]))[0]
        back = geometry.full_camera_to_floor(cal, (float(uv[0]), float(uv[1])))
        assert back == pytest.approx((x, y), abs=1e-6)


@pytest.mark.determinism
def test_hull_excess():
    # A box at the image centre region: loose box = the clipped hull of its own projection -> excess 0 (to rounding);
    # the same loose box widened by 10 px on the right -> excess 10.
    cal = oblique_camera()
    box = {"x_min": -0.5, "x_max": 0.5, "y_min": -0.5, "y_max": 0.5, "z_min": 0.0, "z_max": 1.8,
           "transform": [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0.0, 3.0, 0.0, 1.0]]}
    uv = sdg_camera.project(cal, sdg_truth.box_corners(box))
    hull = (uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max())
    assert 0 <= hull[0] and hull[2] < 1919 and 0 <= hull[1] and hull[3] < 1079  # fully inside: no clipping
    obj = sdg_truth.ObjectTruth("p", "person", (0.0, 3.0), 0.0, hull, None, box)
    assert sdg_truth.hull_excess(cal, obj) == pytest.approx(0.0, abs=1e-9)
    wide = sdg_truth.ObjectTruth("p", "person", (0.0, 3.0), 0.0, (hull[0], hull[1], hull[2] + 10, hull[3]), None, box)
    assert sdg_truth.hull_excess(cal, wide) == pytest.approx(10.0, abs=1e-9)
