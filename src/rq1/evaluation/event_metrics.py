"""Event metrics EV-M1-M8 and EV-M11 from match records (F.1 Appendix N4; E-1.2.1 section 9.2).
EV-M9, EV-M10 and EV-M12 need A-layer and expert inputs and are computed with the evaluation store (T-13/T-14)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .estimators import ht_total
from .matching import is_abstained


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


def localization(records: list[dict]) -> dict[str, float | int | None]:
    """EV-M8 (T10.7(c,d)): unweighted, over matched pairs. Median and P90 of |onset error| and |offset error| by numpy
    percentile, method "linear"; mean temporal IoU; n reported with the values. No matched pair: null (not_applicable)."""
    matched = [r for r in records if r["match_type"] == "matched"]
    out: dict[str, float | int | None] = {"n": len(matched)}
    if not matched:
        return {**out, "onset_median_s": None, "onset_p90_s": None, "offset_median_s": None, "offset_p90_s": None, "mean_iou": None}
    onset = [abs(r["onset_error_s"]) for r in matched]
    offset = [abs(r["offset_error_s"]) for r in matched]
    return {**out, "onset_median_s": percentile(onset, 50), "onset_p90_s": percentile(onset, 90), "offset_median_s": percentile(offset, 50),
            "offset_p90_s": percentile(offset, 90), "mean_iou": sum(r["temporal_iou"] for r in matched) / len(matched)}


def percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q, method="linear"))


def abstention_rate(windows: list[tuple[list[tuple[frozenset, float]], float]], weights: list[float] | None = None) -> dict[str, float | None]:
    """EV-M3 (T10.7(a,d)). Each window: ([(episode labels, episode support)], POW support), episodes by onset window.
    Episodes form: sum w * abstained episodes / sum w * episodes. Support form: sum w * abstained support / sum w * POW support."""
    w = weights if weights is not None else [1.0] * len(windows)
    abst = [float(sum(1 for labels, _ in eps if is_abstained(labels))) for eps, _ in windows]
    count = [float(len(eps)) for eps, _ in windows]
    abst_support = [sum(s for labels, s in eps if is_abstained(labels)) for eps, _ in windows]
    pow_support = [float(p) for _, p in windows]
    return {"episodes": _ratio(w, abst, count), "support": _ratio(w, abst_support, pow_support)}


SENSITIVITY_LABEL = "sensitivity_excluding_unobservable_overlap"
EV_M10_NOTE = "These events are neither confirmed nor refuted by the reference."


def ev_m10(overlaps: list[list[dict]], weights: list[float] | None = None) -> dict:
    """T12.2 EV-M10: per decision and per label (lbl_*), RES-weighted totals with unweighted values alongside."""
    w = weights if weights is not None else [1.0] * len(overlaps)

    def table(ws):
        out: dict = {"non_abstained": 0.0, "abstained": 0.0, "by_label": {}}
        for wi, window in zip(ws, overlaps):
            for e in window:
                out[e["decision"]] += wi
                for label in e["labels"]:
                    key = f"{e['decision']}:{label}"
                    out["by_label"][key] = out["by_label"].get(key, 0.0) + wi
        return out
    return {"weighted": table(w), "unweighted": table([1.0] * len(overlaps)), "note": EV_M10_NOTE}


def sensitivity_excluding_unobservable_overlap(windows: list[WindowCounts], overlaps: list[list[dict]], weights: list[float] | None = None) -> dict:
    """T12.2: EV-M2 and EV-M7 with the non-abstained unobservable-overlap events removed from s_i and f_i. Reported beside
    the headline values under SENSITIVITY_LABEL, never in their place."""
    w = weights if weights is not None else [1.0] * len(windows)
    n = [float(sum(1 for e in o if e["decision"] == "non_abstained")) for o in overlaps]
    return {"label": SENSITIVITY_LABEL,
            "EV-M2": _ratio(w, [float(x.m_s) for x in windows], [x.s - k for x, k in zip(windows, n)]),
            "EV-M7": _ratio(w, [x.f - k for x, k in zip(windows, n)], [x.u for x in windows])}
