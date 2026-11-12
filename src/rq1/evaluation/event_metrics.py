"""Event metrics EV-M1-M8 and EV-M11 from match records (F.1 Appendix N4; E-1.2.1 section 9.2).
EV-M9, EV-M10 and EV-M12 need A-layer and expert inputs and are computed with the evaluation store (T-13/T-14)."""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from .estimators import ht_total


@dataclass(frozen=True)
class WindowCounts:
    """N4 per-window quantities."""
    a: int  # assessable references
    m: int  # matched references
    s: int  # non-abstained system events
    m_s: int  # matched system events
    f: int  # false + duplicate alerts
    c: int  # assessable references receiving a non-abstained decision
    abstained_miss: int
    duplicate: int
    u: float  # usable eligible support, hours


def window_counts(records: list[dict], usable_support_s: float) -> WindowCounts:
    kinds = [r["match_type"] for r in records]
    n = kinds.count
    a = n("matched") + n("miss") + n("abstained_miss")
    return WindowCounts(a=a, m=n("matched"), s=n("matched") + n("false_alert") + n("duplicate_alert"), m_s=n("matched"),
                        f=n("false_alert") + n("duplicate_alert"), c=a - n("abstained_miss"),  # AR-39 item 4
                        abstained_miss=n("abstained_miss"), duplicate=n("duplicate_alert"), u=usable_support_s / 3600.0)


def _ratio(weights: list[float], num: list[float], den: list[float]) -> float | None:
    d = ht_total(weights, den)
    return ht_total(weights, num) / d if d > 0 else None  # null `not_applicable` when the denominator is 0


def headline(windows: list[WindowCounts], weights: list[float] | None = None) -> dict[str, float | None]:
    """EV-M1, M2, M4, M5, M6, M7, M11. RES windows carry w = 1/pi; unweighted versions use w = 1."""
    w = weights if weights is not None else [1.0] * len(windows)
    col = lambda name: [float(getattr(x, name)) for x in windows]
    return {"EV-M1": _ratio(w, col("m"), col("a")), "EV-M2": _ratio(w, col("m_s"), col("s")), "EV-M4": _ratio(w, col("c"), col("a")),
            "EV-M5": _ratio(w, col("abstained_miss"), col("a")), "EV-M6": _ratio(w, col("m"), col("c")), "EV-M7": _ratio(w, col("f"), col("u")),
            "EV-M11": _ratio(w, col("duplicate"), [x.m_s + x.duplicate for x in windows])}


def localization(records: list[dict]) -> dict[str, float | None]:
    """EV-M8 over matched pairs: median and P90 of |onset error| and |offset error|, and mean temporal IoU."""
    matched = [r for r in records if r["match_type"] == "matched"]
    if not matched:
        return {"onset_median_s": None, "onset_p90_s": None, "offset_median_s": None, "offset_p90_s": None, "mean_iou": None}
    onset = [abs(r["onset_error_s"]) for r in matched]
    offset = [abs(r["offset_error_s"]) for r in matched]
    return {"onset_median_s": statistics.median(onset), "onset_p90_s": p90(onset), "offset_median_s": statistics.median(offset),
            "offset_p90_s": p90(offset), "mean_iou": sum(r["temporal_iou"] for r in matched) / len(matched)}


def p90(values: list[float]) -> float:
    """Linear interpolation between order statistics (numpy's default, Hyndman-Fan type 7). CR-010 item 3."""
    xs = sorted(values)
    h = (len(xs) - 1) * 0.9
    lo = int(h)
    return xs[lo] + (h - lo) * (xs[min(lo + 1, len(xs) - 1)] - xs[lo])


def abstention_rate(episodes: list[tuple[bool, float]], pow_support_s: float) -> dict[str, float | None]:
    """EV-M3: abstained episodes / all episodes; abstained support / POW support. Input: (lbl_IE, episode support)."""
    n = len(episodes)
    return {"episodes": sum(1 for ie, _ in episodes if ie) / n if n else None,
            "support": sum(s for ie, s in episodes if ie) / pow_support_s if pow_support_s > 0 else None}
