"""Estimators of Appendix N5 used so far: Horvitz-Thompson total, ratio, Kish n_eff, stratified window bootstrap."""
from __future__ import annotations

import numpy as np


def ht_total(weights: list[float], values: list[float]) -> float:
    return float(sum(w * y for w, y in zip(weights, values)))


def ratio(weights: list[float], numerators: list[float], denominators: list[float]) -> float:
    return ht_total(weights, numerators) / ht_total(weights, denominators)


def kish_n_eff(weights: list[float]) -> float:
    return sum(weights) ** 2 / sum(w * w for w in weights)


def stratified_bootstrap_ratio(sample: dict[str, list[tuple[float, float]]], weights: dict[str, float], B: int, seed: int) -> tuple[float, float]:
    """Target A interval: in each stratum draw n_h windows with replacement, recompute the ratio sum(w m) / sum(w a);
    percentile interval (2.5 %, 97.5 %); RNG numpy PCG64 seeded from configuration."""
    rng = np.random.Generator(np.random.PCG64(seed))
    strata = sorted(sample)
    arrays = {h: np.array(sample[h], dtype=float) for h in strata}
    estimates = np.empty(B)
    for b in range(B):
        num = den = 0.0
        for h in strata:
            rows = arrays[h][rng.integers(0, len(arrays[h]), len(arrays[h]))]
            num += weights[h] * rows[:, 1].sum()
            den += weights[h] * rows[:, 0].sum()
        estimates[b] = num / den
    low, high = np.percentile(estimates, [2.5, 97.5])
    return float(low), float(high)


Z95 = 1.959964  # N5 Wilson z


def _percentiles(estimates: np.ndarray) -> tuple[float, float]:
    low, high = np.percentile(estimates, [2.5, 97.5])
    return float(low), float(high)


def cluster_bootstrap_ratio(windows: list[tuple[str, str, float, float, float]], B: int, seed: int) -> tuple[float, float]:
    """Target B interval (N5): draw leakage groups with replacement, stratified by data origin (each origin draws as many
    groups as it has), carry window weights, recompute sum(w y) / sum(w x); percentile interval (2.5 %, 97.5 %).
    Each window: (data_origin, leakage_group_id, weight, x, y). Origins and groups are sorted before drawing."""
    rng = np.random.Generator(np.random.PCG64(seed))
    by_origin: dict[str, dict[str, list[tuple[float, float, float]]]] = {}
    for origin, group, w, x, y in windows:
        by_origin.setdefault(origin, {}).setdefault(group, []).append((w, x, y))
    plan = [(origin, [np.array(by_origin[origin][g], dtype=float) for g in sorted(by_origin[origin])]) for origin in sorted(by_origin)]
    estimates = np.empty(B)
    for b in range(B):
        num = den = 0.0
        for _, groups in plan:
            for k in rng.integers(0, len(groups), len(groups)):
                rows = groups[k]
                num += float((rows[:, 0] * rows[:, 2]).sum())
                den += float((rows[:, 0] * rows[:, 1]).sum())
        estimates[b] = num / den
    return _percentiles(estimates)


def paired_stratified_bootstrap_difference(sample: dict[str, list[tuple[float, float, float, float]]], weights: dict[str, float],
                                           B: int, seed: int) -> tuple[float, float]:
    """Paired comparison (N5): the same resampled windows for both configurations; interval of R_a - R_b.
    Each window: (x_a, y_a, x_b, y_b); R = sum(w y) / sum(w x) per configuration."""
    rng = np.random.Generator(np.random.PCG64(seed))
    strata = sorted(sample)
    arrays = {h: np.array(sample[h], dtype=float) for h in strata}
    estimates = np.empty(B)
    for b in range(B):
        t = np.zeros(4)
        for h in strata:
            rows = arrays[h][rng.integers(0, len(arrays[h]), len(arrays[h]))]
            t += weights[h] * rows.sum(axis=0)
        estimates[b] = t[1] / t[0] - t[3] / t[2]
    return _percentiles(estimates)


def wilson(successes: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """Wilson interval for independent units (N5). None when n = 0 (not_applicable)."""
    if n == 0:
        return None
    p = successes / n
    centre = p + z * z / (2 * n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    denom = 1 + z * z / n
    return float((centre - half) / denom), float((centre + half) / denom)


def bland_altman(system: list[float], reference: list[float]) -> dict[str, float] | None:
    """d = system - reference; bias = mean(d); LoA = bias +- 1.96 SD(d), SD with n - 1 (N5). None if n < 2."""
    d = np.asarray(system, dtype=float) - np.asarray(reference, dtype=float)
    if d.size < 2:
        return None
    bias, sd = float(d.mean()), float(d.std(ddof=1))
    return {"bias": bias, "sd": sd, "loa_low": bias - 1.96 * sd, "loa_high": bias + 1.96 * sd, "n": int(d.size)}


def icc_2_1(ratings: list[list[float]]) -> float:
    """ICC(2,1), two-way random effects, absolute agreement, single measure (Shrout & Fleiss 1979).
    `ratings`: n targets x k raters, complete."""
    x = np.asarray(ratings, dtype=float)
    n, k = x.shape
    grand = x.mean()
    ss_rows = k * ((x.mean(axis=1) - grand) ** 2).sum()
    ss_cols = n * ((x.mean(axis=0) - grand) ** 2).sum()
    ss_err = ((x - grand) ** 2).sum() - ss_rows - ss_cols
    bms, jms, ems = ss_rows / (n - 1), ss_cols / (k - 1), ss_err / ((n - 1) * (k - 1))
    return float((bms - ems) / (bms + (k - 1) * ems + k * (jms - ems) / n))


def cohen_kappa(a: list, b: list) -> float | None:
    """(p_o - p_e) / (1 - p_e) for two raters (N5). None if p_e = 1 (not_applicable)."""
    n = len(a)
    cats = sorted(set(a) | set(b), key=str)
    p_o = sum(1 for x, y in zip(a, b) if x == y) / n
    p_e = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return None if p_e == 1 else (p_o - p_e) / (1 - p_e)


def krippendorff_alpha_nominal(units: list[list]) -> float | None:
    """Krippendorff's alpha, nominal metric, for more than two raters (N5). Each unit lists the values it received
    (missing values omitted); units with fewer than two values are not pairable. None if expected disagreement is 0."""
    coincidence: dict[tuple, float] = {}
    for values in units:
        m = len(values)
        if m < 2:
            continue
        for i, c in enumerate(values):
            for j, k in enumerate(values):
                if i != j:
                    coincidence[(c, k)] = coincidence.get((c, k), 0.0) + 1.0 / (m - 1)
    totals: dict = {}
    for (c, _), v in coincidence.items():
        totals[c] = totals.get(c, 0.0) + v
    n = sum(totals.values())
    observed = sum(v for (c, k), v in coincidence.items() if c != k)
    expected = sum(totals[c] * totals[k] for c in totals for k in totals if c != k)
    return None if expected == 0 else 1 - (n - 1) * observed / expected
