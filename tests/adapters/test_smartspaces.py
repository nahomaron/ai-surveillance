"""T-18 part C: SmartSpaces calibration (K, E -> full_camera) and per-frame truth.

Hand camera: K = [[1000, 0, 960], [0, 1000, 540], [0, 0, 1]]; E = [R | t] with R = diag(1, -1, -1), t = (0, 0, 10): the
camera sits at world (0, 0, 10) and looks straight down. World (1, 2, 0) -> camera (1, -2, 10) -> u = 960 + 1000 x 0.1 = 1060,
v = 540 + 1000 x (-0.2) = 340."""
import math

import numpy as np
import pytest

from rq1.adapters import sdg_camera, smartspaces
from rq1.schema.errors import ContractError
from rq1.substrate import geometry


def sensor(R=((1, 0, 0), (0, -1, 0), (0, 0, -1)), t=(0, 0, 10)):
    E = [list(map(float, row)) + [float(ti)] for row, ti in zip(R, t)]
    return {"type": "camera", "id": "Camera_0000", "intrinsicMatrix": [[1000.0, 0.0, 960.0], [0.0, 1000.0, 540.0], [0.0, 0.0, 1.0]],
            "extrinsicMatrix": E, "cameraMatrix": [[9.0] * 4] * 3, "homography": [[1.0] * 3] * 3,  # map-image matrices: never read
            "attributes": [{"name": "fps", "value": "30"}, {"name": "frameWidth", "value": "1920"}, {"name": "frameHeight", "value": "1080"}]}


def obj(kind="Forklift", scale=(1.16, 2.68, 1.99), rot=0.0, loc=(1.0, 2.0, 0.995), visible=None, oid=7):
    return {"object type": kind, "object id": oid, "3d location": list(loc), "3d bounding box scale": list(scale),
            "3d bounding box rotation": [0.0, 0.0, rot], "2d bounding box visible": visible or {}}


@pytest.mark.determinism
def test_calibration_hand_projection_and_floor_round_trip():
    cal = smartspaces.calibration(sensor())
    assert cal["calibration_tier"] == "full_camera" and cal["method"] == "dataset_supplied" and cal["quality_state"] == "supplied_unvalidated"
    assert cal["distortion_model"] == "none" and cal["distortion_coeffs"] == [] and cal["image_size_px"] == [1920, 1080]
    assert sdg_camera.project(cal, np.array([[1.0, 2.0, 0.0]]))[0] == pytest.approx([1060.0, 340.0], abs=1e-9)
    # WP-13 truth round trip: a floor point through the calibration and back onto the floor, within 1e-6 m.
    xy = geometry.full_camera_to_floor(cal, (1060.0, 340.0))
    assert xy == pytest.approx((1.0, 2.0), abs=1e-6)


def test_calibration_refusals():
    with pytest.raises(ContractError):
        smartspaces.calibration(sensor(R=((2, 0, 0), (0, -1, 0), (0, 0, -1))))  # not a rotation
    with pytest.raises(ContractError):
        smartspaces.calibration({**sensor(), "type": "lidar"})
    with pytest.raises(ContractError):
        smartspaces.calibrations({"calibrationType": "geo", "sensors": [sensor()]})
    assert list(smartspaces.calibrations({"calibrationType": "cartesian", "sensors": [sensor()]})) == ["Camera_0000"]


@pytest.mark.determinism
def test_forklift_yaw_is_the_long_axis():
    # local y long (as on every SmartSpaces forklift): yaw = rotation + pi/2, wrapped to (-pi, pi]
    assert smartspaces.forklift_yaw((1.16, 2.68, 1.99), 0.0) == pytest.approx(math.pi / 2)
    assert smartspaces.forklift_yaw((1.16, 2.68, 1.99), 2.0) == pytest.approx(2.0 + math.pi / 2 - 2 * math.pi)  # -2.7124
    assert smartspaces.forklift_yaw((1.16, 2.68, 1.99), -math.pi / 2) == pytest.approx(0.0)
    assert smartspaces.forklift_yaw((1.16, 2.68, 1.99), math.pi / 2) == math.pi  # pi + 0 -> pi, never -pi
    # local x long: yaw = rotation
    assert smartspaces.forklift_yaw((3.0, 1.0, 2.0), 0.5) == pytest.approx(0.5)
    with pytest.raises(ContractError):
        smartspaces.forklift_yaw((1.0, 1.0, 2.0), 0.0)


def test_classes_and_parse():
    f = smartspaces.parse_object(obj(visible={"Camera_0003": [1, 2, 3, 4]}))
    assert (f.cls, f.obj_id, f.xy, f.visible) == ("forklift", 7, (1.0, 2.0), {"Camera_0003": (1, 2, 3, 4)})
    assert f.yaw == pytest.approx(math.pi / 2)
    p = smartspaces.parse_object(obj("Person", (0.59, 0.55, 1.86)))
    assert p.cls == "person" and p.yaw is None
    t = smartspaces.parse_object(obj("PalletTruck", (0.76, 1.76, 1.62)))
    assert t.cls == "pallet_truck" and t.cls not in smartspaces.E1_CLASSES and t.yaw is None  # D-22: present, not an E1 class
    with pytest.raises(ContractError):
        smartspaces.parse_object(obj("Drone"))


def test_frame_ids_must_be_the_decoded_frames():
    doc = {"1": [obj(oid=9), obj("Person", (0.5, 0.5, 1.8), oid=3)], "0": []}
    frames = smartspaces.parse_frames(doc, 2)
    assert frames[0] == [] and [o.obj_id for o in frames[1]] == [3, 9]  # objects sorted by id
    with pytest.raises(ContractError):
        smartspaces.parse_frames(doc, 3)  # a frame of the video has no truth
    with pytest.raises(ContractError):
        smartspaces.parse_frames({"0": [], "2": []}, 2)


@pytest.mark.determinism
def test_hull_excess_hand_values():
    # Box centre (1, 2, 0.5), extents 0.4 x 0.4 x 1.0, no rotation, hand camera. Top face z = 1 (camera depth 9), bottom z = 0
    # (depth 10). u: min 960 + 800/10 = 1040, max 960 + 1200/9 = 1093.33; v: min 540 - 2200/9 = 295.56, max 540 - 1800/10 = 360.
    cal = smartspaces.calibration(sensor())
    o = smartspaces.parse_object(obj("Person", (0.4, 0.4, 1.0), loc=(1.0, 2.0, 0.5), visible={"C": [1040, 296, 1093, 360], "D": [1030, 296, 1093, 360]}))
    assert smartspaces.hull_excess(cal, o, "C") == pytest.approx(0.0, abs=1e-9)  # max(0, -0.44, -0.33, 0)
    assert smartspaces.hull_excess(cal, o, "D") == pytest.approx(10.0)
    assert smartspaces.hull_excess(cal, o, "E") is None  # not visible in E
