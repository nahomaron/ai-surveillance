"""Frame-quality flags by rules version (E-1.2.1 section 3.2 step 4; AR-27; D-25; D-26).

`rv1` computes no pixel flag (decode_error only); M0 fixtures only. The pixel versions compute black, overexposed and
frozen on the 8-bit luma plane with integer arithmetic:
- `rv2` (Architect ruling, 13 Nov 2026, D-25 item A): black iff P99 <= 32 AND P99 - P1 <= 2 (a no-content rule).
  All M1a synthetic recordings.
- `rv2-real-provisional`: the same rule, for real footage (still provisional; real results carry the D-26 note).
- `rv2-provisional` (superseded): black iff P99 <= 32. Kept only so the recorded D-25 evidence files reproduce.
`low_light` is a recording-level condition tag (a robustness stratum, never an exclusion). Only statistics are kept,
never pixels."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

RV2 = "rv2"
RV2_REAL = "rv2-real-provisional"
RV2_PROVISIONAL = "rv2-provisional"  # superseded by rv2 / rv2-real-provisional (D-25 ruling, 13 Nov 2026)
PIXEL_VERSIONS = frozenset({RV2, RV2_REAL, RV2_PROVISIONAL})
NO_CONTENT_VERSIONS = frozenset({RV2, RV2_REAL})  # black needs the flat test
EXPLORATORY_NOTE = "exploratory; frame-quality rules provisional"  # D-26 item 2
_PIXEL_EXCLUSIONS = frozenset({"decode_error", "black", "overexposed", "frozen"})
EXCLUSION_FLAGS = {"rv1": frozenset({"decode_error"}), **{v: _PIXEL_EXCLUSIONS for v in PIXEL_VERSIONS}}
BLACK_P99_MAX = 32  # luma, 0-255
BLACK_SPREAD_MAX = 2  # S_flat: P99 - P1 (rv2, rv2-real-provisional)
LOW_LIGHT_MEDIAN_P99_MAX = 32  # recording-level tag (rv2, rv2-real-provisional)
OVEREXPOSED_LUMA = 250  # a pixel at or above this counts
FROZEN_MIN_SPAN = Fraction(1, 2)  # seconds, t(last) - t(first) of a run of identical frames


@dataclass(frozen=True)
class LumaStats:
    n: int
    p99: int  # nearest rank: the ceil(0.99 n)-th smallest value
    p1: int  # nearest rank: the ceil(0.01 n)-th smallest value (D-25 Architect review, item 1)
    n_bright: int  # pixels with luma >= OVEREXPOSED_LUMA
    digest: str  # SHA-256 of the luma bytes; identity test for `frozen`


def needs_pixels(rules_version: str) -> bool:
    return rules_version in PIXEL_VERSIONS


def stats(luma: np.ndarray) -> LumaStats:
    y = np.ascontiguousarray(luma, dtype=np.uint8)
    n = int(y.size)
    hist = np.bincount(y.ravel(), minlength=256)
    rank = -(-99 * n // 100)  # ceil(0.99 n) in integers
    cum = np.cumsum(hist)
    p99 = int(np.searchsorted(cum, rank))
    p1 = int(np.searchsorted(cum, -(-n // 100)))  # ceil(0.01 n)
    return LumaStats(n, p99, p1, int(hist[OVEREXPOSED_LUMA:].sum()), hashlib.sha256(y.tobytes()).hexdigest())


def frame_flags(s: LumaStats, rules_version: str) -> set[str]:
    flags = set()
    flat = s.p99 - s.p1 <= BLACK_SPREAD_MAX if rules_version in NO_CONTENT_VERSIONS else True
    if s.p99 <= BLACK_P99_MAX and flat:
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


def condition_tags(frame_stats: list[LumaStats], rules_version: str) -> list[str]:
    """Recording-level tags. `low_light`: the median P99 over the decoded frames that are not black is <= 32 (AR-51 reading
    of "median frame P99 <= 32 and the frame is not black"). No frame left -> no tag. Never an exclusion."""
    if rules_version not in NO_CONTENT_VERSIONS:
        return []
    kept = sorted(s.p99 for s in frame_stats if "black" not in frame_flags(s, rules_version))
    if not kept:
        return []
    m = len(kept)
    median = Fraction(kept[m // 2]) if m % 2 else Fraction(kept[m // 2 - 1] + kept[m // 2], 2)
    return ["low_light"] if median <= LOW_LIGHT_MEDIAN_P99_MAX else []
