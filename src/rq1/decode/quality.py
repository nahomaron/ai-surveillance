"""Frame-quality flags by rules version (E-1.2.1 section 3.2 step 4; AR-27; D-25 proposal; D-26 provisional use).

`rv1` computes no pixel flag (decode_error only). `rv2-provisional` adds black, overexposed and frozen, computed on the
8-bit luma plane with integer arithmetic. It is PROVISIONAL: the Architect has not reviewed it (D-25); every result that
uses it carries "exploratory; frame-quality rules provisional" (D-26 item 2). Only statistics are kept, never pixels."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

RV2 = "rv2-provisional"
EXPLORATORY_NOTE = "exploratory; frame-quality rules provisional"  # D-26 item 2
EXCLUSION_FLAGS = {"rv1": frozenset({"decode_error"}), RV2: frozenset({"decode_error", "black", "overexposed", "frozen"})}
BLACK_P99_MAX = 32  # luma, 0-255
OVEREXPOSED_LUMA = 250  # a pixel at or above this counts
FROZEN_MIN_SPAN = Fraction(1, 2)  # seconds, t(last) - t(first) of a run of identical frames


@dataclass(frozen=True)
class LumaStats:
    n: int
    p99: int  # nearest rank: the ceil(0.99 n)-th smallest value
    n_bright: int  # pixels with luma >= OVEREXPOSED_LUMA
    digest: str  # SHA-256 of the luma bytes; identity test for `frozen`


def needs_pixels(rules_version: str) -> bool:
    return rules_version == RV2


def stats(luma: np.ndarray) -> LumaStats:
    y = np.ascontiguousarray(luma, dtype=np.uint8)
    n = int(y.size)
    hist = np.bincount(y.ravel(), minlength=256)
    rank = -(-99 * n // 100)  # ceil(0.99 n) in integers
    p99 = int(np.searchsorted(np.cumsum(hist), rank))
    return LumaStats(n, p99, int(hist[OVEREXPOSED_LUMA:].sum()), hashlib.sha256(y.tobytes()).hexdigest())


def frame_flags(s: LumaStats) -> set[str]:
    flags = set()
    if s.p99 <= BLACK_P99_MAX:
        flags.add("black")
    if 2 * s.n_bright >= s.n:
        flags.add("overexposed")
    return flags


def frozen_seqs(timed: list[tuple[Fraction, int, LumaStats]]) -> set[int]:
    """`timed`: (t, seq, stats) in presentation order. Frames after the first of a run of byte-identical luma frames whose
    span reaches FROZEN_MIN_SPAN."""
    out: set[int] = set()
    start = 0
    for k in range(1, len(timed) + 1):
        if k < len(timed) and timed[k][2].digest == timed[k - 1][2].digest:
            continue
        if timed[k - 1][0] - timed[start][0] >= FROZEN_MIN_SPAN:
            out.update(seq for _, seq, _ in timed[start + 1:k])
        start = k
    return out
