# FROZEN copy of src/rq1/evaluation/gv.py at commit 636b311 (before AR-60). Do not edit.
"""Geometry validation GV-01, GV-03 to GV-08 (F.1 Appendix N7) and the MR-08 / MR-09 / MR-12 helpers (N8).

Pure functions over per-unit values; the M1a driver decides which units enter (AR-59). Percentiles use numpy's "linear"
method, as EV-M8 does (T10.7). A summary over no unit is null (not_applicable).
"""
from __future__ import annotations

import math

import numpy as np

CHI2_2_68, CHI2_2_95, CHI2_2_MEDIAN = 2.2789, 6.1801, 1.3863  # N7 GV-05


def _pct(values, q: float) -> float:
    return float(np.percentile(np.asarray(values, float), q, method="linear"))


def gv01(errors: list[tuple[float, float]]) -> dict:
    """GV-01: e_j = |p_hat_j - p_j| (m); mean bias vector, RMSE, P95."""
    n = len(errors)
    if n == 0:
        return {"n": 0, "bias_x_m": None, "bias_y_m": None, "rmse_m": None, "p95_m": None, "sum_sq_m2": 0.0}
    norms = [math.hypot(dx, dy) for dx, dy in errors]
    sq = sum(v * v for v in norms)
    return {"n": n, "bias_x_m": sum(dx for dx, _ in errors) / n, "bias_y_m": sum(dy for _, dy in errors) / n, "rmse_m": math.sqrt(sq / n),
            "p95_m": _pct(norms, 95), "sum_sq_m2": sq}


def gv05(errors: list[tuple[float, float]], covariances: list[list[float] | None]) -> dict:
    """GV-05: d2_j = e_j^T Sigma_j^-1 e_j (2D, Sigma as (sxx, sxy, syy)); coverage at the chi2_2 quantiles 2.2789 and
    6.1801; inflation factor sqrt(median(d2) / 1.3863), applied if > 1. Units without a covariance are counted, not scored."""
    d2 = []
    for (dx, dy), cov in zip(errors, covariances):
        if cov is None:
            continue
        sxx, sxy, syy = cov
        det = sxx * syy - sxy * sxy
        if det <= 0:
            continue
        d2.append((syy * dx * dx - 2 * sxy * dx * dy + sxx * dy * dy) / det)
    missing = sum(1 for c in covariances if c is None)
    if not d2:
        return {"n": 0, "n_without_covariance": missing, "d2": [], "coverage_68": None, "coverage_95": None, "inflation": None, "inflation_applied": None}
    med = float(np.median(d2))
    inflation = math.sqrt(med / CHI2_2_MEDIAN)
    return {"n": len(d2), "n_without_covariance": missing, "d2": d2, "coverage_68": sum(v <= CHI2_2_68 for v in d2) / len(d2),
            "coverage_95": sum(v <= CHI2_2_95 for v in d2) / len(d2), "inflation": inflation, "inflation_applied": inflation > 1}


def spearman(x: list[float], y: list[float]) -> float | None:
    """GV-06 Spearman rho (average ranks for ties), via scipy."""
    if len(x) < 2:
        return None
    from scipy.stats import spearmanr
    rho = spearmanr(x, y).statistic
    return None if rho is None or math.isnan(rho) else float(rho)


def p_disagreement(pairs: list[tuple[int, int]]) -> dict:
    """GV-06: share of pair-frames where R1-P and R2-P are both known (not 2) and differ."""
    known = [(a, b) for a, b in pairs if a != 2 and b != 2]
    n, d = len(known), sum(1 for a, b in known if a != b)
    return {"n": n, "disagree": d, "rate": d / n if n else None}


def signed_summary(values: list[float]) -> dict:
    """Bias (mean), RMSE, sample SD, P5 and P95 of signed differences (GV-04, GV-07, GV-08)."""
    n = len(values)
    if n == 0:
        return {"n": 0, "bias": None, "rmse": None, "sd": None, "p5": None, "p95": None, "sum": 0.0, "sum_sq": 0.0}
    s, sq = sum(values), sum(v * v for v in values)
    mean = s / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else None
    return {"n": n, "bias": mean, "rmse": math.sqrt(sq / n), "sd": sd, "p5": _pct(values, 5), "p95": _pct(values, 95), "sum": s, "sum_sq": sq}


def realized_min(series: list[tuple[float, float | None]], k: int, tau: float, eps: float = 1e-9) -> float | None:
    """GV-08 realized minimum clearance over [t_k, t_k + tau] on one POW's frames (time, clearance or None), in time order.
    Null when the horizon runs past the last frame of the series (the realized minimum is not observed) or when no frame
    in the window has a measured clearance (AR-59 item 7)."""
    t0 = series[k][0]
    if t0 + tau > series[-1][0] + eps:
        return None
    values = [c for t, c in series[k:] if t <= t0 + tau + eps and c is not None]
    return min(values) if values else None


def _iou(a: tuple[float, float], b: tuple[float, float]) -> float:
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    return inter / (max(a[1], b[1]) - min(a[0], b[0])) if inter > 0 else 0.0


def label_stability(base: list[tuple], grid: list[list[tuple]], iou_m: float) -> list[float]:
    """MR-08 label_stability_frac per base episode: the share of grid points at which an episode of the same pair with
    temporal IoU >= iou_m has an identical label set. Episodes: (pair key, t_start, t_end, frozenset of labels). Within a
    grid point, the base episode is matched to the same-pair episode of highest IoU (ties: earliest start)."""
    out = []
    for pair, a, b, labels in base:
        stable = 0
        for point in grid:
            cands = sorted(((_iou((a, b), (c, d)), -c, lab) for p, c, d, lab in point if p == pair), key=lambda x: (-x[0], -x[1]))
            if cands and cands[0][0] >= iou_m and cands[0][2] == labels:
                stable += 1
        out.append(stable / len(grid) if grid else None)
    return out


def elasticity(y0: float, y1: float, theta0: float, theta1: float) -> float | None:
    """MR-08 elasticity (dY / Y) / (dtheta / theta) between adjacent grid points (base -> neighbour)."""
    if y0 == 0 or theta0 == 0 or theta1 == theta0:
        return None
    return ((y1 - y0) / y0) / ((theta1 - theta0) / theta0)
