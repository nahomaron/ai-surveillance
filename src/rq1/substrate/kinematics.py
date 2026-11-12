"""T8.2 and T8.3: least-squares velocity, speed, heading and yaw; closing rate and time to closest approach."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Fit:
    vx: float
    vy: float
    sigma_vx: float
    sigma_vy: float

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def heading(self) -> float:
        value = math.atan2(self.vy, self.vx)
        return math.pi if value == -math.pi else value  # (-pi, pi]

    @property
    def speed_sigma(self) -> float:
        if self.speed == 0:
            return math.sqrt((self.sigma_vx ** 2 + self.sigma_vy ** 2) / 2)
        return math.sqrt((self.vx * self.sigma_vx) ** 2 + (self.vy * self.sigma_vy) ** 2) / self.speed


def _slope(t: list[float], y: list[float]) -> tuple[float, float]:
    """Ordinary least-squares slope and its standard error (residual variance with n - 2 degrees of freedom)."""
    n = len(t)
    tm, ym = sum(t) / n, sum(y) / n
    sxx = sum((a - tm) ** 2 for a in t)
    slope = sum((a - tm) * (b - ym) for a, b in zip(t, y)) / sxx
    intercept = ym - slope * tm
    residual = sum((b - intercept - slope * a) ** 2 for a, b in zip(t, y))
    return slope, math.sqrt(residual / (n - 2) / sxx) if n > 2 else 0.0


def slope(t: list[float], y: list[float]) -> float:
    return _slope(t, y)[0]


def fit_velocity(t: list[float], xs: list[float], ys: list[float]) -> Fit:
    vx, sx = _slope(t, xs)
    vy, sy = _slope(t, ys)
    return Fit(vx, vy, sx, sy)


def window_ok(times: list[float], w_v: float) -> bool:
    """T8.2: at least 3 frames spanning at least w_v / 2."""
    return len(times) >= 3 and max(times) - min(times) >= w_v / 2 - 1e-9


def fill_yaw(supplied: list[float | None], speeds: list[float | None], headings: list[float | None], v_min: float) -> list[float | None]:
    """T8.2 forklift yaw: supplied yaw; else heading when speed >= v_min; else carried forward, then backward-filled."""
    yaw = [s if s is not None else (h if (v is not None and v >= v_min and h is not None) else None) for s, v, h in zip(supplied, speeds, headings)]
    last = None
    for i, value in enumerate(yaw):
        if value is None:
            yaw[i] = last
        else:
            last = value
    first = next((v for v in yaw if v is not None), None)
    return [first if v is None else v for v in yaw]


def ttca(t_at_min: float, horizon_s: float, eps: float = 1e-6) -> tuple[float | None, str | None]:
    """T8.3: null `not_applicable` at 0 (diverging or static), null `not_observable` at the horizon, else t_at_min."""
    if t_at_min <= eps:
        return None, "not_applicable"
    if t_at_min >= horizon_s - eps:
        return None, "not_observable"
    return t_at_min, None
