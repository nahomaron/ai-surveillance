"""PhysicalAI-SmartSpaces (MTMC_Tracking_2026, synthetic scenes) camera calibration and per-frame truth (T-18 part C, WP-13).

Calibration (`calibration.json`, one record per camera): `intrinsicMatrix` K (3 x 3) and `extrinsicMatrix` E = [R | t]
(3 x 4, OpenCV convention, x_cam = R x_world + t, metres). No distortion is supplied and the scenes are rendered, so the
model is a pinhole (`distortion_model = none`). The supplied `cameraMatrix` and `homography` are NOT K E: they map the
dataset's map-image coordinates (`scaleFactor`, `translationToGlobalCoordinates`) and are not read. Check (data check
`research/datasets/part3/smartspaces_truth_check.py`): with K E, 99.9 % of the visible 2D boxes lie within 2 px of the
image-clipped projection of the object's own 3D box.

Truth (`ground_truth.json`): frame id (string key "0" .. "8999") -> objects. Frame id k is decoded frame k in presentation
order (decode_seq k) of every camera of the scene (qualification 2.7: shared frame index). Per object: `object type`,
`object id`, `3d location` = 3D box centre (metres), `3d bounding box scale` = extents along the box's local x, y, z,
`3d bounding box rotation` = (roll, pitch, yaw about z) in radians, `2d bounding box visible` = camera -> [x0, y0, x1, y1]
for the cameras in which the object is visible (qualification 2.6). Field names contain spaces (card discrepancy 5).
- Class: `Person` -> person, `Forklift` -> forklift, `PalletTruck` -> pallet_truck (present, not an E1 pair class, D-22).
- Footprint centre: the centre of the box's floor face, (x, y) of `3d location` (D-8: simulator footprint centre).
- Forklift yaw: the direction of the box's long horizontal axis, wrapped to (-pi, pi] (AR-52). The forklift's long axis is
  its local y axis on every forklift box of the scene, so yaw = rotation_z + pi/2. Persons: yaw None (not_applicable).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from rq1.schema.errors import ContractError

CLASSES = {"Person": "person", "Forklift": "forklift", "PalletTruck": "pallet_truck"}
E1_CLASSES = frozenset({"person", "forklift"})


def _attr(sensor: dict[str, Any], name: str) -> str:
    for a in sensor.get("attributes", []):
        if a["name"] == name:
            return a["value"]
    raise ContractError("ERR-SPEC", f"SmartSpaces camera {sensor.get('id')}: attribute {name} missing")


def calibration(sensor: dict[str, Any]) -> dict[str, Any]:
    """One `calibration.json` sensor record -> a full_camera calibration (OpenCV convention, metres)."""
    if sensor.get("type") != "camera":
        raise ContractError("ERR-SPEC", f"SmartSpaces sensor {sensor.get('id')} is not a camera")
    K = np.array(sensor["intrinsicMatrix"], float)
    E = np.array(sensor["extrinsicMatrix"], float)
    if K.shape != (3, 3) or E.shape != (3, 4):
        raise ContractError("ERR-SPEC", f"SmartSpaces camera {sensor['id']}: K must be 3 x 3 and E 3 x 4")
    R = E[:, :3]
    if np.abs(R @ R.T - np.eye(3)).max() > 1e-9 or abs(np.linalg.det(R) - 1) > 1e-9:
        raise ContractError("ERR-SPEC", f"SmartSpaces camera {sensor['id']}: extrinsic rotation is not a proper rotation")
    return {"calibration_tier": "full_camera", "method": "dataset_supplied", "intrinsics_K": [float(x) for x in K.ravel()],
            "R_cam_from_world": [float(x) for x in R.ravel()], "t_cam_from_world_m": [float(x) for x in E[:, 3]],
            "distortion_model": "none", "distortion_coeffs": [], "homography_assumes_undistorted": False,
            "quality_state": "supplied_unvalidated", "image_size_px": [int(_attr(sensor, "frameWidth")), int(_attr(sensor, "frameHeight"))]}


def calibrations(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """camera id -> calibration, for every camera sensor of a scene's `calibration.json`."""
    if doc.get("calibrationType") != "cartesian":
        raise ContractError("ERR-SPEC", f"SmartSpaces calibrationType {doc.get('calibrationType')}: cartesian expected")
    return {s["id"]: calibration(s) for s in doc["sensors"] if s.get("type") == "camera"}


@dataclass(frozen=True)
class ObjectTruth:
    obj_id: int
    cls: str  # person | forklift | pallet_truck
    xy: tuple[float, float]  # footprint centre, world metres
    yaw: float | None  # forklift long-axis direction, (-pi, pi]; None for other classes
    centre: tuple[float, float, float]  # 3D box centre
    scale: tuple[float, float, float]  # extents along local x, y, z
    rotation: tuple[float, float, float]
    visible: dict[str, tuple[int, int, int, int]]  # camera id -> visible 2D box [x0, y0, x1, y1]


def _wrap(angle: float) -> float:
    a = math.remainder(angle, 2 * math.pi)
    return math.pi if a <= -math.pi else a


def forklift_yaw(scale: tuple[float, float, float], rotation_z: float) -> float:
    """Direction of the long horizontal axis: local x when it is the longer one, otherwise local y (= rotation + pi/2)."""
    if scale[0] == scale[1]:
        raise ContractError("ERR-INVARIANT", "forklift box with equal horizontal extents: no long axis")
    return _wrap(rotation_z if scale[0] > scale[1] else rotation_z + math.pi / 2)


def parse_object(o: dict[str, Any]) -> ObjectTruth:
    cls = CLASSES.get(o["object type"])
    if cls is None:
        raise ContractError("ERR-SPEC", f"SmartSpaces object type {o['object type']} is not known")
    centre = tuple(float(v) for v in o["3d location"])
    scale = tuple(float(v) for v in o["3d bounding box scale"])
    rotation = tuple(float(v) for v in o["3d bounding box rotation"])
    yaw = forklift_yaw(scale, rotation[2]) if cls == "forklift" else None
    visible = {cam: tuple(int(v) for v in box) for cam, box in sorted(o.get("2d bounding box visible", {}).items())}
    return ObjectTruth(int(o["object id"]), cls, (centre[0], centre[1]), yaw, centre, scale, rotation, visible)


def parse_frames(doc: dict[str, Any], n_video_frames: int) -> list[list[ObjectTruth]]:
    """All frames of a scene, indexed by decode_seq; objects sorted by id. Refuses a frame-id set other than 0 .. n-1,
    since frame k could then not be tied to decoded frame k."""
    if sorted(doc, key=int) != [str(k) for k in range(n_video_frames)]:
        raise ContractError("ERR-INVARIANT", f"ground truth frame ids are not 0..{n_video_frames - 1}")
    return [sorted((parse_object(o) for o in doc[str(k)]), key=lambda t: t.obj_id) for k in range(n_video_frames)]


def box_corners(obj: ObjectTruth) -> np.ndarray:
    """The 8 world corners (8 x 3) of the 3D box (rotation about z only; roll and pitch are 0 on forklifts and pallet
    trucks and below 2e-5 rad on persons in the data held)."""
    (cx, cy, cz), (sx, sy, sz), a = obj.centre, obj.scale, obj.rotation[2]
    c, s = math.cos(a), math.sin(a)
    out = []
    for dx in (-sx / 2, sx / 2):
        for dy in (-sy / 2, sy / 2):
            for dz in (-sz / 2, sz / 2):
                out.append((cx + c * dx - s * dy, cy + s * dx + c * dy, cz + dz))
    return np.array(out)


def hull_excess(cal: dict[str, Any], obj: ObjectTruth, camera: str) -> float | None:
    """How far the visible box in `camera` extends beyond the image-clipped projection of the 3D box, in px (<= 0:
    contained). None when the object is not visible there or a corner is behind the camera."""
    from .sdg_camera import project

    box = obj.visible.get(camera)
    if box is None:
        return None
    corners = box_corners(obj)
    r = np.array(cal["R_cam_from_world"]).reshape(3, 3)
    if ((corners @ r.T + np.array(cal["t_cam_from_world_m"]))[:, 2] <= 0).any():
        return None
    uv = project(cal, corners)
    w, h = cal["image_size_px"]
    hull = (max(uv[:, 0].min(), 0), max(uv[:, 1].min(), 0), min(uv[:, 0].max(), w - 1), min(uv[:, 1].max(), h - 1))
    return float(max(hull[0] - box[0], hull[1] - box[1], box[2] - hull[2], box[3] - hull[3]))


def load(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)
