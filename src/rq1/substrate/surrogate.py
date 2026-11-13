"""R4 surrogate quantities from the T8.3 constant-velocity prediction (Appendix T T15, contract E-1.2.13).

Footprints translate without rotation over [0, tau]: the person is a disc; the forklift is the yaw-oriented prior rectangle,
or the circumscribed disc when yaw is unknown (T8.2). Every footprint and swept region is a "rounded convex polygon": a
convex polygon (possibly one point or one segment) dilated by a radius r >= 0. For two such shapes, the polygons' unsigned
distance minus both radii is <= 0 exactly when the shapes intersect, and it is convex in a translation parameter t, so the
set of t where they intersect is an interval (found by bisection, tolerance 1e-6 s).

- ttc (T15.2): earliest t in [0, tau] with predicted signed clearance <= 0; 0 if <= 0 at the frame; bisection on [0, t_at_min].
- pet_pred (T15.3): swept region of an object = convex hull of its footprint at 0 and tau. Because each footprint lies inside its
  own swept region, an object's footprint meets the conflict area A = S_person & S_forklift exactly when it meets the other
  object's swept region; that gives the occupancy interval [t_in, t_out].
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import geometry

TOL_S = 1e-6  # T15.2 bisection tolerance (seconds); also used for the T15.3 occupancy bounds (AR-49)
Point = tuple[float, float]


@dataclass(frozen=True)
class Shape:
    verts: tuple[Point, ...]  # convex polygon, counter-clockwise; one point or one segment allowed
    r: float = 0.0

    def moved(self, d: Point) -> "Shape":
        return Shape(tuple((x + d[0], y + d[1]) for x, y in self.verts), self.r)


def person_shape(centre: Point, radius: float) -> Shape:
    return Shape((centre,), radius)


def forklift_shape(centre: Point, yaw: float | None, length: float, width: float) -> Shape:
    if yaw is None:  # T8.2: circumscribed disc of the prior rectangle
        return Shape((centre,), geometry.circumscribed_radius(length, width))
    c, s = math.cos(yaw), math.sin(yaw)
    corners = [(sx * length / 2, sy * width / 2) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    return Shape(hull([(centre[0] + c * a - s * b, centre[1] + s * a + c * b) for a, b in corners]), 0.0)


def swept(shape: Shape, v: Point, tau: float) -> Shape:
    """T15.3: convex hull of the footprint at t = 0 and t = tau (translation only)."""
    end = shape.moved((v[0] * tau, v[1] * tau))
    return Shape(hull(list(shape.verts) + list(end.verts)), shape.r)


def _cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull(points: list[Point]) -> tuple[Point, ...]:
    """Andrew's monotone chain on canonically sorted, de-duplicated points; counter-clockwise; collinear points dropped."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return tuple(pts)
    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return tuple(lower[:-1] + upper[:-1])


def _edges(verts: tuple[Point, ...]) -> list[tuple[Point, Point]]:
    if len(verts) == 1:
        return [(verts[0], verts[0])]
    if len(verts) == 2:
        return [(verts[0], verts[1])]
    return [(verts[i], verts[(i + 1) % len(verts)]) for i in range(len(verts))]


def _point_segment(p: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    u = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)


def _inside(p: Point, verts: tuple[Point, ...]) -> bool:
    return len(verts) >= 3 and all(_cross(a, b, p) >= 0 for a, b in _edges(verts))


def _segments_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    d1, d2, d3, d4 = _cross(c, d, a), _cross(c, d, b), _cross(a, b, c), _cross(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4)


def polygon_distance(p: tuple[Point, ...], q: tuple[Point, ...]) -> float:
    """Unsigned distance between two convex polygons (0 when they intersect)."""
    if any(_inside(v, q) for v in p) or any(_inside(v, p) for v in q):
        return 0.0
    ep, eq = _edges(p), _edges(q)
    if any(_segments_cross(a, b, c, d) for a, b in ep for c, d in eq):
        return 0.0
    return min(min(_point_segment(v, c, d) for v in p for c, d in eq), min(_point_segment(v, a, b) for v in q for a, b in ep))


def gap(a: Shape, b: Shape) -> float:
    """<= 0 exactly when the two shapes intersect (touching counts)."""
    return polygon_distance(a.verts, b.verts) - a.r - b.r


def _argmin(f, lo: float, hi: float) -> float:
    ratio = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    for _ in range(200):
        m1, m2 = b - ratio * (b - a), a + ratio * (b - a)
        if f(m1) <= f(m2):
            b = m2
        else:
            a = m1
    return min((f(t), t) for t in (lo, (a + b) / 2, hi))[1]


def _boundary(f, outside: float, inside: float) -> float:
    """Bisection between a t with f > 0 and a t with f <= 0; returns the inside end (f <= 0), within TOL_S of the boundary."""
    while abs(inside - outside) > TOL_S:
        mid = (outside + inside) / 2
        if f(mid) <= 0:
            inside = mid
        else:
            outside = mid
    return inside


def ttc(clearance_at, t_at_min: float) -> float | None:
    """T15.2. `clearance_at(t)`: predicted signed footprint clearance; `t_at_min`: its minimiser over [0, tau] (T8.3)."""
    if clearance_at(0.0) <= 0:
        return 0.0
    if clearance_at(t_at_min) > 0:
        return None
    return _boundary(clearance_at, 0.0, t_at_min)


def occupancy(footprint: Shape, v: Point, region: Shape, tau: float) -> tuple[float, float] | None:
    """The interval of t in [0, tau] where footprint + v t meets `region`; None if it never does."""
    f = lambda t: gap(footprint.moved((v[0] * t, v[1] * t)), region)
    t_star = _argmin(f, 0.0, tau)
    if f(t_star) > 0:
        return None
    t_in = 0.0 if f(0.0) <= 0 else _boundary(f, 0.0, t_star)
    t_out = tau if f(tau) <= 0 else _boundary(f, tau, t_star)
    return t_in, t_out


def pet_pred(person: Shape, person_v: Point, fork: Shape, fork_v: Point, tau: float) -> float | None:
    """T15.3 predicted PET; None (not_applicable) when the conflict area is empty or either occupancy interval is empty."""
    s_p, s_f = swept(person, person_v, tau), swept(fork, fork_v, tau)
    if gap(s_p, s_f) > 0:
        return None
    occ_p, occ_f = occupancy(person, person_v, s_f, tau), occupancy(fork, fork_v, s_p, tau)
    if occ_p is None or occ_f is None:
        return None
    first, second = (occ_f, occ_p) if occ_f[0] <= occ_p[0] else (occ_p, occ_f)  # ties: the forklift is first
    return max(0.0, second[0] - first[1])
