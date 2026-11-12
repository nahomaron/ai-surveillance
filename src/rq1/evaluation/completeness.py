"""Completeness metrics (F.1 Appendix N6; A5.2 "Use downstream"). Support is clipped eligible support per frame.
"Matched" means a `track_identity_assoc` status `matched` for the same identity on that frame. Each metric is computed
on both support bases: `detected` (system evidence class detected) and `detected_plus_inferred`.

CM-01 to CM-10 and pooling follow N6 as clarified by Appendix T T12.4 (contract E-1.2.10; T13, E-1.2.11). Reference objects in
`ref_visible` are co-visible candidates: visible or partially visible, or present when the dataset has no visibility truth
(then `visibility_assumed` is set and reports print "reference visibility assumed")."""
from __future__ import annotations

from dataclasses import dataclass, field

from .association import summarize
from .estimators import bland_altman

BASES = {"detected": ("detected",), "detected_plus_inferred": ("detected", "inferred")}


@dataclass(frozen=True)
class WindowFrames:
    """One window and camera, frame level."""
    support: dict[int, float]  # clipped eligible support per frame (s)
    ref_visible: dict[int, dict[str, str]]  # frame -> {physical_identity_id: class} of visible reference objects
    ref_present: dict[int, set]  # frame -> identities present (visible or not)
    assoc: list[dict]  # track_identity_assoc rows: frame_index, track_id, physical_identity_id, status
    track_class: dict[int, dict[str, str]]  # frame -> {track_id: evidence class of the system track point}
    pows: list[dict] = field(default_factory=list)  # {"person_track", "forklift_track", "frames": {frame: pair evidence class},
    #   optional "clearance_state": {frame: state}, "clearance": {frame: m or None}, "calibration_tier": str}
    ref_moving: dict[int, set] = field(default_factory=dict)  # frame -> forklift identities moving (CM-02 restriction)
    ref_class: dict[str, str] = field(default_factory=dict)  # identity -> class, for identities that are present but never visible
    visibility_assumed: bool = False  # no visibility truth: presence counts as co-visible (T12.4)


def _ratio(num: float, den: float) -> dict:
    return {"numerator": num, "denominator": den, "value": num / den if den > 0 else None, "value_null_reason": None if den > 0 else "not_applicable"}


def _matched(w: WindowFrames) -> dict[int, dict[str, str]]:
    """frame -> {identity: matched track}."""
    out: dict[int, dict[str, str]] = {}
    for r in w.assoc:
        if r["status"] == "matched":
            out.setdefault(r["frame_index"], {})[r["physical_identity_id"]] = r["track_id"]
    return out


def cm_object(w: WindowFrames, cls: str, basis: str, moving_only: bool = False) -> dict[str, dict]:
    """CM-01 (person) and CM-02 (forklift), per reference identity: s(visible frames matched to the identity, with the
    matched track's point in the basis) / s(visible frames). CM-02 with `moving_only` keeps reference-moving frames only."""
    matched, ok = _matched(w), BASES[basis]
    ids = sorted({i for f in w.ref_visible.values() for i, c in f.items() if c == cls})
    out = {}
    for ident in ids:
        frames = [f for f, objs in w.ref_visible.items() if objs.get(ident) == cls and (not moving_only or ident in w.ref_moving.get(f, set()))]
        num = sum(w.support[f] for f in frames if ident in matched.get(f, {}) and w.track_class.get(f, {}).get(matched[f][ident]) in ok)
        out[ident] = _ratio(num, sum(w.support[f] for f in frames))
    return out


def _covered(w: WindowFrames, pair: tuple[str, str], f: int, ok: tuple) -> bool:
    m = _matched(w).get(f, {})
    return any(p["frames"].get(f) in ok and m.get(pair[0]) == p["person_track"] and m.get(pair[1]) == p["forklift_track"] for p in w.pows)


def reference_pairs(w: WindowFrames) -> list[tuple[str, str]]:
    """T12.4: (person p, forklift f) with at least one eligible frame of the window on which both are co-visible."""
    pairs = set()
    for objs in w.ref_visible.values():
        persons = [i for i, c in objs.items() if c == "person"]
        forks = [i for i, c in objs.items() if c != "person"]
        pairs |= {(p, f) for p in persons for f in forks}
    return sorted(pairs)


def _covisible(w: WindowFrames, pair: tuple[str, str]) -> list[int]:
    return sorted(f for f, objs in w.ref_visible.items() if pair[0] in objs and pair[1] in objs)


def _attributed(w: WindowFrames, pow_: dict, f: int) -> tuple[str, str] | None:
    """T12.4: the pair (p, f) a POW frame is attributed to: both tracks matched, to p and f, on that frame."""
    m = {r["track_id"]: r["physical_identity_id"] for r in w.assoc if r["frame_index"] == f and r["status"] == "matched"}
    person, fork = m.get(pow_["person_track"]), m.get(pow_["forklift_track"])
    return (person, fork) if person is not None and fork is not None else None


def cm03(w: WindowFrames, pairs: list[tuple[str, str]] | None, basis: str) -> dict[tuple[str, str], dict]:
    """CM-03 per reference pair: s(co-visible frames covered by a POW whose tracks are matched to that pair, the POW
    pair-frame in the basis) / s(co-visible frames). Co-visible: both reference objects visible on the frame."""
    ok, out = BASES[basis], {}
    for pair in (pairs if pairs is not None else reference_pairs(w)):
        frames = _covisible(w, pair)
        out[pair] = _ratio(sum(w.support[f] for f in frames if _covered(w, pair, f, ok)), sum(w.support[f] for f in frames))
    return out


def cm04(w: WindowFrames, pairs: list[tuple[str, str]] | None, basis: str) -> dict:
    """CM-04: reference pairs with at least one co-visible frame covered as in CM-03 / reference pairs."""
    per = cm03(w, pairs, basis)
    return _ratio(float(sum(1 for r in per.values() if r["numerator"] > 0)), float(len(per)))


def _units(w: WindowFrames, basis: str):
    """POW frames of the basis: (pow index, frame)."""
    ok = BASES[basis]
    return [(k, f) for k, p in enumerate(w.pows) for f, c in sorted(p["frames"].items()) if c in ok]


def cm05(w: WindowFrames, basis: str) -> dict:
    """T12.4 CM-05: POW frames of the basis, excluding frames where either track is ambiguous; numerator, frames attributed
    to no reference pair. Ambiguous support is returned separately (`ambiguous_support_s`), outside the ratio."""
    pairs = set(reference_pairs(w))
    ambiguous = {(r["frame_index"], r["track_id"]) for r in w.assoc if r["status"] == "ambiguous"}
    num = den = amb = 0.0
    for k, f in _units(w, basis):
        p = w.pows[k]
        if (f, p["person_track"]) in ambiguous or (f, p["forklift_track"]) in ambiguous:
            amb += w.support[f]
            continue
        den += w.support[f]
        if _attributed(w, p, f) not in pairs:
            num += w.support[f]
    return {**_ratio(num, den), "ambiguous_support_s": amb}


def band_index(bands: list, value: float) -> int:
    return next(k for k, (lo, hi) in enumerate(bands) if (lo is None or value >= lo) and (hi is None or value < hi))


def cm06(w: WindowFrames, basis: str, bands: list, ref_clearance: dict | None) -> dict:
    """T12.4 CM-06 per reference pair: AI time in band from POW frames attributed to the pair (measured clearance, basis);
    reference time in band from co-visible frames by reference clearance. Value = sum over bands of |AI_b - ref_b|.
    Bland-Altman over (pair, band) units, descriptive only (n reported, no interval claim). Without reference geometry
    (`ref_clearance` None) every value is null with reason not_supplied."""
    pairs = reference_pairs(w)
    if ref_clearance is None:
        return {"pairs": {pair: {"value": None, "value_null_reason": "not_supplied"} for pair in pairs}, "bland_altman": None}
    per, ai_all, ref_all = {}, [], []
    for pair in pairs:
        ai, ref = [0.0] * len(bands), [0.0] * len(bands)
        for k, f in _units(w, basis):
            p = w.pows[k]
            value = p.get("clearance", {}).get(f)
            if value is not None and p.get("clearance_state", {}).get(f, "measured") == "measured" and _attributed(w, p, f) == pair:
                ai[band_index(bands, value)] += w.support[f]
        for f in _covisible(w, pair):
            value = ref_clearance.get(pair, {}).get(f)
            if value is not None:
                ref[band_index(bands, value)] += w.support[f]
        per[pair] = {"value": sum(abs(a - r) for a, r in zip(ai, ref)), "value_null_reason": None, "ai_s": ai, "ref_s": ref}
        ai_all += ai
        ref_all += ref
    return {"pairs": per, "bland_altman": bland_altman(ai_all, ref_all)}


def cm07(w: WindowFrames, basis: str) -> dict:
    """T12.4 CM-07 (N6): for each reference co-presence interval (maximal run of consecutive eligible co-visible frames
    of a pair), the number of POWs with at least one frame of the basis attributed to the pair inside it."""
    order = sorted(w.support)
    position = {f: i for i, f in enumerate(order)}
    intervals = []
    for pair in reference_pairs(w):
        frames = _covisible(w, pair)
        runs: list[list[int]] = []
        for f in frames:
            if runs and position[f] == position[runs[-1][-1]] + 1:
                runs[-1].append(f)
            else:
                runs.append([f])
        for run in runs:
            inside = set(run)
            count = len({k for k, f in _units(w, basis) if f in inside and _attributed(w, w.pows[k], f) == pair})
            intervals.append({"pair": pair, "start_frame": run[0], "end_frame_excl": run[-1] + 1, "n_pows": count})
    n = len(intervals)
    summary = {"0": sum(1 for i in intervals if i["n_pows"] == 0), "1": sum(1 for i in intervals if i["n_pows"] == 1),
               "2+": sum(1 for i in intervals if i["n_pows"] >= 2)}
    return {"intervals": intervals, "summary": summary, "pair_window_fidelity": summary["1"] / n if n else None}


def cm08(w: WindowFrames, basis: str) -> dict[str, dict]:
    """T12.4 CM-08 per calibration tier: POW frames of the basis whose clearance_state is not measured / POW frames of the basis."""
    out: dict[str, list[float]] = {}
    for k, f in _units(w, basis):
        p = w.pows[k]
        acc = out.setdefault(p.get("calibration_tier", "unknown"), [0.0, 0.0])
        acc[1] += w.support[f]
        if p.get("clearance_state", {}).get(f, "measured") != "measured":
            acc[0] += w.support[f]
    return {tier: _ratio(num, den) for tier, (num, den) in sorted(out.items())}


def cm10(w: WindowFrames) -> dict[tuple[str, str], dict]:
    """T12.4 CM-10 per reference pair: co-visible frames on which a POW whose dominant pair is (p, f) has an insufficient
    pair-frame / co-visible frames. Frames with no POW pair-frame count in neither. The numerator is insufficient evidence,
    which no basis contains, so CM-10 is basis-independent (Appendix T T13.1)."""
    summaries, _ = summarize(w.assoc, w.support)
    dominant = {s["track_id"]: s["dominant_identity_id"] for s in summaries}
    out = {}
    for pair in reference_pairs(w):
        frames = _covisible(w, pair)
        own = [p for p in w.pows if (dominant.get(p["person_track"]), dominant.get(p["forklift_track"])) == pair]
        num = sum(w.support[f] for f in frames if any(p["frames"].get(f) == "insufficient" for p in own))
        out[pair] = _ratio(num, sum(w.support[f] for f in frames))
    return out


def pooled(ratios: list[dict], weights: list[float] | None = None) -> dict:
    """T12.4 pooling over RES windows: sum w * numerator / sum w * denominator (a ratio of sums), unweighted alongside."""
    w = weights if weights is not None else [1.0] * len(ratios)
    weighted = _ratio(sum(wi * r["numerator"] for wi, r in zip(w, ratios)), sum(wi * r["denominator"] for wi, r in zip(w, ratios)))
    plain = _ratio(sum(r["numerator"] for r in ratios), sum(r["denominator"] for r in ratios))
    return {"weighted": weighted, "unweighted": plain}


def cm09(w: WindowFrames, basis: str) -> dict:
    """CM-09: s(inferred track frames whose track is matched to a present reference object) / s(inferred track frames).
    Only inferred frames count, so on the `detected` basis the denominator is 0 and the value is null (not_applicable)."""
    if "inferred" not in BASES[basis]:
        return _ratio(0.0, 0.0)
    matched_tracks = {(r["frame_index"], r["track_id"]): r["physical_identity_id"] for r in w.assoc if r["status"] == "matched"}
    units = [(f, t) for f, tracks in w.track_class.items() for t, c in tracks.items() if c == "inferred"]
    num = sum(w.support[f] for f, t in units if matched_tracks.get((f, t)) in w.ref_present.get(f, set()))
    return _ratio(num, sum(w.support[f] for f, _ in units))


def record(window_id: str, metric_id: str, basis: str, stratum: dict, ratio: dict, interp_method: str, iou_cm: float, k_kf_s: float) -> dict:
    """A completeness_record row (E-1.2.1 section 5.9). Track-level completeness has no rule configuration (AR-43 item 2)."""
    return {"window_id": window_id, "metric_id": metric_id, "support_basis": basis, "config_id": None, "config_id_null_reason": "not_applicable",
            "stratum": stratum, **ratio, "interp_method": interp_method, "iou_cm": iou_cm, "k_kf_s": k_kf_s}


def cm10_records(w: WindowFrames, window_id: str, interp_method: str, iou_cm: float, k_kf_s: float) -> list[dict]:
    """T13.1: CM-10 is computed once and stored with support_basis = detected as a key placeholder; reports print
    "basis-independent"."""
    return [record(window_id, "CM-10", "detected", {"pair": f"{p}|{f}"}, ratio, interp_method, iou_cm, k_kf_s) for (p, f), ratio in cm10(w).items()]
