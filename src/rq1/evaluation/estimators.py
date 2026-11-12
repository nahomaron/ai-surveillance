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
