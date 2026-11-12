"""Floor geometry: signed footprint distance and constant-velocity prediction (E-1.2.1 sections 4.1, 5.5; Appendix N2).

Person: disc. Forklift: oriented rectangle. Clearance = signed distance from the person centre to the rectangle
(negative inside) minus the person radius; clearance <= 0 means overlap.
"""
from __future__ import annotations

import math


def _signed_distance(point: tuple[float, float], centre: tuple[float, float], yaw: float, length: float, width: float) -> float:
    dx, dy = point[0] - centre[0], point[1] - centre[1]
    c, s = math.cos(yaw), math.sin(yaw)
    lx, ly = abs(c * dx + s * dy) - length / 2, abs(-s * dx + c * dy) - width / 2
    outside = math.hypot(max(lx, 0.0), max(ly, 0.0))
    return outside + min(max(lx, ly), 0.0)


def clearance(person: tuple[float, float], radius: float, forklift: tuple[float, float], yaw: float, length: float, width: float) -> float:
    return _signed_distance(person, forklift, yaw, length, width) - radius


def footprint_overlap(value: float) -> int:
    """Tri-state per section 5.5 when clearance is measured."""
    return 1 if value <= 0 else 0


def predict_min_clearance(person: tuple[float, float], person_v: tuple[float, float], radius: float, forklift: tuple[float, float],
                          forklift_v: tuple[float, float], yaw: float | None, length: float, width: float, horizon_s: float) -> tuple[float, float]:
    """Minimum clearance over [0, horizon] with both objects at constant velocity. The signed distance of a convex set
    composed with a linear path is convex in time, so a golden-section search finds the minimum."""
    def at(t: float) -> float:
        p = (person[0] + person_v[0] * t, person[1] + person_v[1] * t)
        f = (forklift[0] + forklift_v[0] * t, forklift[1] + forklift_v[1] * t)
        if yaw is None:  # T8.2: unknown yaw uses the circumscribed disc
            return disc_clearance(p, radius, f, circumscribed_radius(length, width))
        return clearance(p, radius, f, yaw, length, width)

    lo, hi = 0.0, horizon_s
    ratio = (math.sqrt(5) - 1) / 2
    for _ in range(200):
        m1, m2 = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
        if at(m1) <= at(m2):
            hi = m2
        else:
            lo = m1
    candidates = [(at(t), t) for t in (0.0, (lo + hi) / 2, horizon_s)]
    return min(candidates)


def disc_clearance(person: tuple[float, float], radius: float, centre: tuple[float, float], disc_radius: float) -> float:
    """T8.2: with unknown yaw the forklift footprint is the circumscribed disc of the prior rectangle."""
    return math.hypot(person[0] - centre[0], person[1] - centre[1]) - disc_radius - radius


def circumscribed_radius(length: float, width: float) -> float:
    return 0.5 * math.sqrt(length * length + width * width)


def clearance_gradient(person: tuple[float, float], centre: tuple[float, float], yaw: float | None, length: float, width: float) -> tuple[float, float]:
    """T8.4: unit gradient of the signed footprint distance at the person centre, pointing from the footprint to the person.
    Inside the rectangle, the normal of the nearest edge. With `yaw` None the footprint is a disc."""
    dx, dy = person[0] - centre[0], person[1] - centre[1]
    if yaw is None:
        norm = math.hypot(dx, dy)
        return (dx / norm, dy / norm) if norm else (1.0, 0.0)
    c, s = math.cos(yaw), math.sin(yaw)
    lx, ly = c * dx + s * dy, -s * dx + c * dy
    qx, qy = abs(lx) - length / 2, abs(ly) - width / 2
    sx, sy = (1.0 if lx >= 0 else -1.0), (1.0 if ly >= 0 else -1.0)
    if qx > 0 or qy > 0:
        gx, gy = sx * max(qx, 0.0), sy * max(qy, 0.0)
        norm = math.hypot(gx, gy)
        gx, gy = gx / norm, gy / norm
    else:
        gx, gy = ((sx, 0.0) if qx > qy else (0.0, sy))
    return (c * gx - s * gy, s * gx + c * gy)


def clearance_sigma(u: tuple[float, float], cov_person: list[float] | None, cov_forklift: list[float] | None, yaw: float | None,
                    sigma_length: float, sigma_width: float, disc: bool) -> float | None:
    """T8.4: sigma_c^2 = u^T (S_person + S_forklift) u + sigma_dim^2; None when either covariance is null."""
    if cov_person is None or cov_forklift is None:
        return None
    sxx, sxy, syy = (a + b for a, b in zip(cov_person, cov_forklift))
    positional = u[0] * u[0] * sxx + 2 * u[0] * u[1] * sxy + u[1] * u[1] * syy
    if disc or yaw is None:
        dim = 0.5 * max(sigma_length, sigma_width)
    else:
        h = (math.cos(yaw), math.sin(yaw))
        dim = 0.5 * (abs(u[0] * h[0] + u[1] * h[1]) * sigma_length + abs(-u[0] * h[1] + u[1] * h[0]) * sigma_width)
    return math.sqrt(positional + dim * dim)


def image_gap(person_box: list[float], forklift_box: list[float]) -> tuple[float, float]:
    """T8.5 signed box gap in CF-IMG and its ratio to the person box height."""
    p, f = person_box, forklift_box
    dx = max(f[0] - p[2], p[0] - f[2])
    dy = max(f[1] - p[3], p[1] - f[3])
    gap = math.hypot(max(dx, 0.0), max(dy, 0.0)) if (dx > 0 or dy > 0) else max(dx, dy)
    return gap, gap / (p[3] - p[1])


def homography_to_floor(homography: list[float], point: tuple[float, float]) -> tuple[float, float] | None:
    h = homography
    x = h[0] * point[0] + h[1] * point[1] + h[2]
    y = h[3] * point[0] + h[4] * point[1] + h[5]
    w = h[6] * point[0] + h[7] * point[1] + h[8]
    return None if w <= 0 else (x / w, y / w)


def full_camera_to_floor(calibration: dict, point: tuple[float, float]) -> tuple[float, float] | None:
    """Ray through the pixel intersected with the floor z = 0 (CF-CAM is OpenCV; R and t map world to camera)."""
    import numpy as np

    k = np.array(calibration["intrinsics_K"], float).reshape(3, 3)
    r = np.array(calibration["R_cam_from_world"], float).reshape(3, 3)
    t = np.array(calibration["t_cam_from_world_m"], float)
    if calibration.get("distortion_model") not in (None, "none"):
        import cv2

        undistorted = cv2.undistortPoints(np.array([[point]], float), k, np.array(calibration["distortion_coeffs"], float)).ravel()
        ray_cam = np.array([undistorted[0], undistorted[1], 1.0])
    else:
        ray_cam = np.linalg.solve(k, np.array([point[0], point[1], 1.0]))
    centre = -r.T @ t
    ray = r.T @ ray_cam
    if abs(ray[2]) < 1e-12:
        return None
    s = -centre[2] / ray[2]
    if s <= 0:
        return None
    hit = centre + s * ray
    return float(hit[0]), float(hit[1])
