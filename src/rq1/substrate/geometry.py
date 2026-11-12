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
                          forklift_v: tuple[float, float], yaw: float, length: float, width: float, horizon_s: float) -> tuple[float, float]:
    """Minimum clearance over [0, horizon] with both objects at constant velocity. The signed distance of a convex set
    composed with a linear path is convex in time, so a golden-section search finds the minimum."""
    def at(t: float) -> float:
        return clearance((person[0] + person_v[0] * t, person[1] + person_v[1] * t), radius,
                         (forklift[0] + forklift_v[0] * t, forklift[1] + forklift_v[1] * t), yaw, length, width)

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
