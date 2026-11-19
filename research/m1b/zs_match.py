"""T-22 zero-shot probe: box matching and counts (pure Python; imported by `.venv-det` and by the main `.venv` tests).

Matching (Owner instruction of 19 Nov 2026): same class, IoU >= 0.3 (iou_m of the frozen pre-registration), one-to-one
by descending IoU. Ties in IoU are broken by detection order (descending score, then input order) and then by reference
input order, so the result is deterministic. Boxes are (x1, y1, x2, y2) in CF-IMG pixels.
"""
from __future__ import annotations

IOU_M = 0.3
THRESHOLDS = tuple(round(0.05 * i, 2) for i in range(1, 11))  # 0.05, 0.10, ..., 0.50


def iou(a, b) -> float:
    iw = min(a[2], b[2]) - max(a[0], b[0])
    ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union


def match(refs: list, dets: list, iou_min: float = IOU_M) -> list[tuple[int, int, float]]:
    """One-to-one greedy matching of one class on one frame. `refs`: boxes; `dets`: (box, score) pairs.
    Returns (ref index, det index, IoU) for every match."""
    order = sorted(range(len(dets)), key=lambda j: (-dets[j][1], j))
    rank = {j: r for r, j in enumerate(order)}
    pairs = [(iou(refs[i], dets[j][0]), i, j) for i in range(len(refs)) for j in range(len(dets))]
    pairs = sorted((p for p in pairs if p[0] >= iou_min), key=lambda p: (-p[0], rank[p[2]], p[1]))
    used_r, used_d, out = set(), set(), []
    for v, i, j in pairs:
        if i not in used_r and j not in used_d:
            used_r.add(i)
            used_d.add(j)
            out.append((i, j, v))
    return sorted(out)


def counts(frames: list[dict], cls: str, threshold: float, iou_min: float = IOU_M) -> dict:
    """Totals over frames. Each frame: {"references": [{"class", "box"}], "detections": [{"class", "box", "score"}]}.
    Detections with score >= threshold take part."""
    tp = n_ref = n_det = 0
    for f in frames:
        refs = [r["box"] for r in f["references"] if r["class"] == cls]
        dets = [(d["box"], d["score"]) for d in f["detections"] if d["class"] == cls and d["score"] >= threshold]
        tp += len(match(refs, dets, iou_min))
        n_ref += len(refs)
        n_det += len(dets)
    return summarize(tp, n_ref, n_det)


def summarize(tp: int, n_ref: int, n_det: int) -> dict:
    fp, fn = n_det - tp, n_ref - tp
    return {"tp": tp, "fp": fp, "fn": fn, "references": n_ref, "detections": n_det,
            "recall": tp / n_ref if n_ref else None,
            "precision": tp / n_det if n_det else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else None}


def best_f1(rows: dict) -> float | None:
    """The threshold with the highest F1; ties go to the lower threshold. None when no F1 is defined."""
    scored = [(r["f1"], -t) for t, r in rows.items() if r["f1"] is not None]
    return -max(scored)[1] if scored else None
