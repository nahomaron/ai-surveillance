"""IDF1 against simulator identities (D-45 item 1; F.1 A5.2 inputs; AR-62 item 6).

F.1 names TrackEval as the normative implementation of IDF1. TrackEval is not installed (not pre-approved), so this is
a line-for-line port of TrackEval's `Identity` metric (trackeval/metrics/identity.py, `eval_sequence`), with its
similarity = box IoU and threshold = iou_cm (0.5, frozen pre-registration v1):
- per frame, every (reference, system) pair with IoU >= threshold is a potential match (no one-to-one step per frame);
- one global assignment of reference identities to system tracks (`linear_sum_assignment` on FN + FP costs, with
  dummy rows and columns of cost 1e10 as TrackEval builds them);
- IDTP = reference boxes - IDFN; IDF1 = IDTP / max(1, IDTP + 0.5 IDFP + 0.5 IDFN).
Inputs per frame: system boxes {track: box}, reference boxes {identity: box}, one class at a time.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment


def _iou(a, b) -> float:
    iw = min(a[2], b[2]) - max(a[0], b[0])
    ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


def idf1(frames: dict[int, tuple[dict[str, tuple], dict[str, tuple]]], threshold: float = 0.5) -> dict:
    """`frames`: frame -> (system {track_id: box}, reference {identity: box})."""
    gt_ids = sorted({g for _, (_, ref) in frames.items() for g in ref})
    tr_ids = sorted({t for _, (sys_, _) in frames.items() for t in sys_})
    gi, ti = {g: k for k, g in enumerate(gt_ids)}, {t: k for k, t in enumerate(tr_ids)}
    ng, nt = len(gt_ids), len(tr_ids)
    potential = np.zeros((ng, nt))
    gt_count, tr_count = np.zeros(ng), np.zeros(nt)
    for i in sorted(frames):
        sys_, ref = frames[i]
        for g, gb in ref.items():
            gt_count[gi[g]] += 1
            for t, tb in sys_.items():
                if _iou(gb, tb) >= threshold:
                    potential[gi[g], ti[t]] += 1
        for t in sys_:
            tr_count[ti[t]] += 1
    if ng == 0 or nt == 0:
        idfn, idfp = gt_count.sum(), tr_count.sum()
        idtp = 0.0
    else:
        fp = np.zeros((ng + nt, ng + nt))
        fn = np.zeros((ng + nt, ng + nt))
        fp[ng:, :nt] = 1e10
        fn[:ng, nt:] = 1e10
        for g in range(ng):
            fn[g, :nt] = gt_count[g]
            fn[g, nt + g] = gt_count[g]
        for t in range(nt):
            fp[:ng, t] = tr_count[t]
            fp[t + ng, t] = tr_count[t]
        fn[:ng, :nt] -= potential
        fp[:ng, :nt] -= potential
        rows, cols = linear_sum_assignment(fn + fp)
        idfn, idfp = fn[rows, cols].sum(), fp[rows, cols].sum()
        idtp = gt_count.sum() - idfn
    return {"IDTP": float(idtp), "IDFP": float(idfp), "IDFN": float(idfn), "IDF1": float(idtp / max(1.0, idtp + 0.5 * idfp + 0.5 * idfn)),
            "reference_boxes": float(gt_count.sum()), "system_boxes": float(tr_count.sum()), "identities": ng, "tracks": nt}
