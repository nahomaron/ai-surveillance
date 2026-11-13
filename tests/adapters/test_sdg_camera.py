"""T-18 part A: SDG (Isaac Sim / USD) camera parameters → full_camera calibration in OpenCV convention.

USD uses row vectors (p_cam = [p_world, 1] · V, translation in V's last row) and a camera that looks down −Z with +Y up.
OpenCV uses column vectors and a camera looking down +Z with +Y down: F = diag(1, −1, −1), R = F · V[:3,:3]ᵀ, t = F · V[3,:3].
From the projection P (row vectors): fx = P00·W/2, fy = P11·H/2, cx = W/2·(1 − P20), cy = H/2·(1 + P21).
Hand values: P00 = 1.732050852618065 and P11 = 3.0792015157654484 at 1920 × 1080 (as in the SDG files) give
fx = 1.732050852618065 × 960 = 1662.7688185133424 and fy = 3.0792015157654484 × 540 = 1662.7688185133421."""
import math

import numpy as np
import pytest

from rq1.adapters import sdg_camera
from rq1.schema.errors import ContractError

P00, P11 = 1.732050852618065, 3.0792015157654484


def params(view=None, p20=0.0, p21=0.0, model="pinhole", units=1.0):
    view = np.eye(4) if view is None else view
    proj = [P00, 0, 0, 0, 0, P11, 0, 0, p20, p21, 1e-9, -1.0, 0, 0, 0.01, 0]
    return {"cameraViewTransform": list(np.asarray(view, float).ravel()), "cameraProjection": proj, "cameraModel": model,
            "renderProductResolution": [1920, 1080], "metersPerSceneUnit": units}


def usd_pixel(cp, point):
    V = np.array(cp["cameraViewTransform"]).reshape(4, 4)
    P = np.array(cp["cameraProjection"]).reshape(4, 4)
    clip = np.append(point, 1.0) @ V @ P
    ndc = clip[:3] / clip[3]
    W, H = cp["renderProductResolution"]
    return np.array([(ndc[0] + 1) / 2 * W, (1 - ndc[1]) / 2 * H])


@pytest.mark.determinism
def test_intrinsics_hand_values():
    c = sdg_camera.calibration(params())
    K = np.array(c["intrinsics_K"]).reshape(3, 3)
    assert K[0, 0] == pytest.approx(1662.7688185133424, abs=1e-9) and K[1, 1] == pytest.approx(1662.7688185133421, abs=1e-9)
    assert (K[0, 2], K[1, 2]) == (960.0, 540.0)
    assert c["distortion_model"] == "none" and c["distortion_coeffs"] == []


@pytest.mark.determinism
def test_identity_view_hand_projection():
    # Camera at the origin looking down −Z. World (1, 0.5, −10): x/z_cv = 0.1, y_cv/z_cv = −0.05
    # → u = 960 + 1662.7688185133424 × 0.1 = 1126.2768818513342; v = 540 − 1662.7688185133421 × 0.05 = 456.8615590743329.
    uv = sdg_camera.project(sdg_camera.calibration(params()), np.array([[1.0, 0.5, -10.0]]))[0]
    assert uv == pytest.approx([1126.2768818513342, 456.8615590743329], abs=1e-9)


@pytest.mark.determinism
def test_opencv_projection_equals_usd_projection():
    rng = np.random.default_rng(20261112)
    a, b = math.radians(35.0), math.radians(-120.0)
    rot_x = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    rot_z = np.array([[math.cos(b), -math.sin(b), 0], [math.sin(b), math.cos(b), 0], [0, 0, 1]])
    V = np.eye(4)
    V[:3, :3] = (rot_z @ rot_x).T  # any rotation, written in row-vector form
    V[3, :3] = [0.3, -1.2, -7.6]
    cp = params(V, p20=0.01, p21=-0.02)
    cal = sdg_camera.calibration(cp)
    R, t = np.array(cal["R_cam_from_world"]).reshape(3, 3), np.array(cal["t_cam_from_world_m"])
    pts = rng.uniform(-5, 5, size=(50, 3))
    in_front = (pts @ R.T + t)[:, 2] > 0.1
    got = sdg_camera.project(cal, pts[in_front])
    want = np.array([usd_pixel(cp, p) for p in pts[in_front]])
    assert in_front.sum() > 10 and np.abs(got - want).max() < 1e-6
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12) and np.linalg.det(R) == pytest.approx(1.0)


@pytest.mark.determinism
def test_record_fields_and_refusals():
    c = sdg_camera.calibration(params())
    assert (c["calibration_tier"], c["method"], c["quality_state"], c["homography_assumes_undistorted"]) == \
        ("full_camera", "dataset_supplied", "supplied_unvalidated", False)
    with pytest.raises(ContractError):
        sdg_camera.calibration(params(model="fisheyePolynomial"))  # only pinhole is supported
    with pytest.raises(ContractError):
        sdg_camera.calibration(params(units=0.01))  # metres only (AS-E-02/03; qualification Part 2)


@pytest.mark.determinism
def test_static_camera_required():
    a, b = params(), params()
    b["cameraViewTransform"][12] = 0.5  # the camera moved 0.5 m along x
    assert sdg_camera.static_params([a, a, a]) == a
    with pytest.raises(ContractError):
        sdg_camera.static_params([a, b])
