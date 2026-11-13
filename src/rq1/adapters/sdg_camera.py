"""SDG-Warehouse camera parameters (Isaac Sim / USD) → a full_camera calibration in OpenCV convention (T-18, WP-13).

USD row-vector convention: p_cam = [p_world, 1] · V (translation in V's last row); the camera looks down −Z, +Y up.
OpenCV: x_cam = R · x_world + t, camera looks down +Z, +Y down; F = diag(1, −1, −1) converts between the two.
The world frame is the dataset's declared frame (metersPerSceneUnit = 1.0, AR-35 item 7); the calibration is
dataset_supplied and supplied_unvalidated until GV-02."""
from __future__ import annotations

import json
from typing import Any

import numpy as np

from rq1.schema.errors import ContractError

F = np.diag([1.0, -1.0, -1.0])


def static_params(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """The per-frame camera records of one camera must be identical (a static camera); returns the first."""
    keys = ("cameraViewTransform", "cameraProjection", "renderProductResolution", "cameraModel", "metersPerSceneUnit")
    first = {k: frames[0][k] for k in keys}
    for i, f in enumerate(frames[1:], 1):
        if json.dumps({k: f[k] for k in keys}, sort_keys=True) != json.dumps(first, sort_keys=True):
            raise ContractError("ERR-INVARIANT", f"SDG camera parameters change at frame {i}; moving cameras are not supported")
    return frames[0]


def calibration(cp: dict[str, Any]) -> dict[str, Any]:
    if cp["cameraModel"] != "pinhole":
        raise ContractError("ERR-SPEC", f"SDG camera model {cp['cameraModel']} is not supported (pinhole only)")
    if cp["metersPerSceneUnit"] != 1.0:
        raise ContractError("ERR-SPEC", f"metersPerSceneUnit {cp['metersPerSceneUnit']}: metres expected")
    V = np.array(cp["cameraViewTransform"], float).reshape(4, 4)
    P = np.array(cp["cameraProjection"], float).reshape(4, 4)
    W, H = cp["renderProductResolution"]
    R = F @ V[:3, :3].T
    t = F @ V[3, :3]
    K = [P[0, 0] * W / 2, 0.0, W / 2 * (1 - P[2, 0]), 0.0, P[1, 1] * H / 2, H / 2 * (1 + P[2, 1]), 0.0, 0.0, 1.0]
    return {"calibration_tier": "full_camera", "method": "dataset_supplied", "intrinsics_K": [float(x) for x in K],
            "R_cam_from_world": [float(x) for x in R.ravel()], "t_cam_from_world_m": [float(x) for x in t],
            "distortion_model": "none", "distortion_coeffs": [], "homography_assumes_undistorted": False,
            "quality_state": "supplied_unvalidated", "image_size_px": [int(W), int(H)]}


def project(cal: dict[str, Any], points_w: np.ndarray) -> np.ndarray:
    """Pinhole projection of world points (n × 3) to pixels (n × 2)."""
    K = np.array(cal["intrinsics_K"]).reshape(3, 3)
    R = np.array(cal["R_cam_from_world"]).reshape(3, 3)
    t = np.array(cal["t_cam_from_world_m"])
    cam = points_w @ R.T + t
    uvw = cam @ K.T
    return uvw[:, :2] / uvw[:, 2:3]
