"""D-55 step 4: tracking measures of one class on one camera from a tracker log (pure; main `.venv`).

Pilot definitions, unchanged:
- points: `rq1.tracking.bridging.points_from_log` at g_max 15 (the S3 points: `tracked` with the detection box,
  `predicted` with the tracker's box on bridged runs; lost frames carry no point).
- IDF1: `idf1.idf1` (TrackEval port) at iou_cm 0.5; system boxes = every S3 point (tracked and predicted), reference
  boxes = the reference-visible boxes (T17.6), unclipped, as `evaluate_pilot.evaluate_camera` builds them.
- frame matching: `zs_match.match` (same class, IoU >= 0.3, one-to-one by descending score), references = the
  reference-visible boxes clipped to the image, as `tracker_loss.camera` matches them (tracked points carry their
  detection's score, predicted points score 0).

D-55 measures (reading recorded in CR-033 item 2):
- "tracked point" is a point in state `tracked` (pilot_tracker_loss stage `tracked`). Primary:
  coverage = references matched by a tracked point / references; precision = tracked points matched / tracked points;
  fragments = distinct tracks whose tracked points are matched to the reference identity.
- Secondary, reported beside it (not used by the selection): the same with every S3 point (tracked and predicted;
  pilot_tracker_loss stage `tracked_predicted`).
- counts: tracks started (tracks with a point), predicted points, bridged gaps (runs_bridged), longest bridged gap in
  eligible frames (a run of 1..g_max eligible frames between two matched frames of one track).
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import idf1 as idf  # noqa: E402
import zs_match as zm  # noqa: E402
from rq1.tracking import bridging  # noqa: E402

G_MAX = 15
IOU_CM = 0.5
VARIANTS = ("tracked", "all")  # primary, secondary


def longest_bridged(log: list[dict], g_max: int = G_MAX) -> int:
    pos = defaultdict(list)
    for k, e in enumerate(log):
        for tid, _, _ in e["tracked"]:
            pos[int(tid)].append(k)
    best = 0
    for ks in pos.values():
        for a, b in zip(ks, ks[1:]):
            if 1 <= b - a - 1 <= g_max:
                best = max(best, b - a - 1)
    return best


def measures(log: list[dict], refs: dict, refs_clipped: dict, score: dict, frames: list[int], g_max: int = G_MAX) -> dict:
    """log: tracker log of one class; refs / refs_clipped: frame -> [(identity, box)] of that class (clipped: boxes
    already clipped, None dropped); score: det_index key (frame, det_index) -> score; frames: eligible frames."""
    pts = bridging.points_from_log(log, g_max)
    by_frame = defaultdict(list)
    for tid, tr in pts.items():
        for p in tr["points"]:
            by_frame[p["frame_index"]].append((tid, p))
    sys_frames = {i: ({tid: tuple(p["bbox"]) for tid, p in v}, {}) for i, v in by_frame.items()}
    for i, v in refs.items():
        sys_frames.setdefault(i, ({}, {}))[1].update({k: tuple(b) for k, b in v})
    id1 = idf.idf1(sys_frames, IOU_CM)
    out = {"idf1": {k: id1[k] for k in ("IDTP", "IDFP", "IDFN", "reference_boxes", "system_boxes", "identities", "tracks")}}
    refs_n = 0
    cov = dict.fromkeys(VARIANTS, 0)
    npts, nmatch = dict.fromkeys(VARIANTS, 0), dict.fromkeys(VARIANTS, 0)
    frag = {v: defaultdict(set) for v in VARIANTS}
    for i in frames:
        rs = refs_clipped.get(i, [])
        refs_n += len(rs)
        ps = sorted(by_frame.get(i, []), key=lambda x: x[0])
        for v in VARIANTS:
            use = [(tid, p) for tid, p in ps if v == "all" or p["state"] == "tracked"]
            cand = [(p["bbox"], score[(i, p["det_index"])] if p["state"] == "tracked" else 0.0) for _, p in use]
            mm = zm.match([b for _, b in rs], cand)
            cov[v] += len(mm)
            npts[v] += len(use)
            nmatch[v] += len(mm)
            for ri, dj, _ in mm:
                frag[v][rs[ri][0]].add(use[dj][0])
    idents = sorted({k for v in refs_clipped.values() for k, _ in v}, key=str)
    out["coverage"] = {"references": refs_n, **{f"matched_{v}": cov[v] for v in VARIANTS}}
    out["precision"] = {**{f"points_{v}": npts[v] for v in VARIANTS}, **{f"points_matched_{v}": nmatch[v] for v in VARIANTS}}
    out["fragments"] = {str(k): {v: len(frag[v].get(k, ())) for v in VARIANTS} for k in idents}
    out["counts"] = {"tracks": len(pts), "tracked": sum(t["counts"]["tracked"] for t in pts.values()),
                     "predicted": sum(t["counts"]["predicted"] for t in pts.values()),
                     "runs_bridged": sum(t["counts"]["runs_bridged"] for t in pts.values()), "longest_bridged": longest_bridged(log, g_max)}
    return out


def _div(a, b):
    return a / b if b else None


def pool(parts: list[dict]) -> dict:
    """Pooled over cameras: IDF1 from summed IDTP/IDFP/IDFN (as `evaluate_pilot.aggregate`); ratios of sums; fragments
    per identity = mean over the reference identities covered by at least one track."""
    s = lambda f: sum(f(p) for p in parts)
    tp, fp, fn = s(lambda p: p["idf1"]["IDTP"]), s(lambda p: p["idf1"]["IDFP"]), s(lambda p: p["idf1"]["IDFN"])
    out = {"cameras": len(parts), "IDTP": tp, "IDFP": fp, "IDFN": fn, "idf1": tp / max(1.0, tp + 0.5 * fp + 0.5 * fn),
           "references": s(lambda p: p["coverage"]["references"])}
    for v in VARIANTS:
        frs = [f[v] for p in parts for f in p["fragments"].values()]
        covered = [n for n in frs if n >= 1]
        out[v] = {"coverage": _div(s(lambda p: p["coverage"][f"matched_{v}"]), out["references"]),
                  "precision": _div(s(lambda p: p["precision"][f"points_matched_{v}"]), s(lambda p: p["precision"][f"points_{v}"])),
                  "points": s(lambda p: p["precision"][f"points_{v}"]), "points_matched": s(lambda p: p["precision"][f"points_matched_{v}"]),
                  "matched_references": s(lambda p: p["coverage"][f"matched_{v}"]),
                  "identities": len(frs), "identities_covered": len(covered), "identities_two_or_more": sum(1 for n in covered if n >= 2),
                  "fragments_per_identity": _div(sum(covered), len(covered))}
    out["counts"] = {k: s(lambda p: p["counts"][k]) for k in ("tracks", "tracked", "predicted", "runs_bridged")}
    out["counts"]["longest_bridged"] = max((p["counts"]["longest_bridged"] for p in parts), default=0)
    return out


def quantile(values: list, q: float):
    """Nearest-rank quantile (P90 = the smallest value with at least 90 % of the values at or below it)."""
    if not values:
        return None
    v = sorted(values)
    import math
    return v[max(0, math.ceil(q / 100 * len(v)) - 1)]


def median(values: list):
    if not values:
        return None
    v = sorted(values)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
