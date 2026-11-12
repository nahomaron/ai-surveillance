"""Completeness metrics (F.1 Appendix N6; A5.2 "Use downstream"). Support is clipped eligible support per frame.
"Matched" means a `track_identity_assoc` status `matched` for the same identity on that frame. Each metric is computed
on both support bases: `detected` (system evidence class detected) and `detected_plus_inferred`.

Implemented here: CM-01, CM-02 (with the reference-moving restriction as a stratum), CM-03, CM-04, CM-09.
CM-05, CM-06, CM-07, CM-08 and CM-10 wait for CR-015."""
from __future__ import annotations

from dataclasses import dataclass, field

BASES = {"detected": ("detected",), "detected_plus_inferred": ("detected", "inferred")}


@dataclass(frozen=True)
class WindowFrames:
    """One window and camera, frame level."""
    support: dict[int, float]  # clipped eligible support per frame (s)
    ref_visible: dict[int, dict[str, str]]  # frame -> {physical_identity_id: class} of visible reference objects
    ref_present: dict[int, set]  # frame -> identities present (visible or not)
    assoc: list[dict]  # track_identity_assoc rows: frame_index, track_id, physical_identity_id, status
    track_class: dict[int, dict[str, str]]  # frame -> {track_id: evidence class of the system track point}
    pows: list[dict] = field(default_factory=list)  # {"person_track", "forklift_track", "frames": {frame: pair evidence class}}
    ref_moving: dict[int, set] = field(default_factory=dict)  # frame -> forklift identities moving (CM-02 restriction)


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


def cm03(w: WindowFrames, pairs: list[tuple[str, str]], basis: str) -> dict[tuple[str, str], dict]:
    """CM-03 per reference pair: s(co-visible frames covered by a POW whose tracks are matched to that pair, the POW
    pair-frame in the basis) / s(co-visible frames). Co-visible: both reference objects visible on the frame."""
    ok, out = BASES[basis], {}
    for pair in pairs:
        frames = [f for f, objs in w.ref_visible.items() if pair[0] in objs and pair[1] in objs]
        out[pair] = _ratio(sum(w.support[f] for f in frames if _covered(w, pair, f, ok)), sum(w.support[f] for f in frames))
    return out


def cm04(w: WindowFrames, pairs: list[tuple[str, str]], basis: str) -> dict:
    """CM-04: reference pairs with at least one co-visible frame covered as in CM-03 / reference pairs."""
    per = cm03(w, pairs, basis)
    return _ratio(float(sum(1 for r in per.values() if r["numerator"] > 0)), float(len(pairs)))


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
