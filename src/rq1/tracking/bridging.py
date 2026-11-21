"""Detector-path S3 track points from a tracker log (D-45 item 1; Appendix T T8.1, T18 amendment 2, T19; AR-62).

Pure Python, importable under Python 3.9 (`.venv-det`) and in the main environment.

Input: a per-class tracker log over the eligible frames of one recording, in decode order. Each log entry is
    {"frame_index": i, "tracked": [[track_id, det_index, [x1, y1, x2, y2]], ...], "lost": [[track_id, [x1, y1, x2, y2]], ...]}
where `tracked` lists the tracks the tracker reports on that frame with their matched detection (the detection's own
box, AR-62 item 3) and `lost` lists the tracks the tracker keeps alive without a detection, with the box it predicts for
that frame. Ineligible frames are not in the log: they carry no point (T19), and the bridge length below is counted
in log entries, i.e. in eligible frames, as the T8.1 gap is.

Rule (D-45 item 1, the T19 rule at the frozen g_max):
- a frame on which the track is matched to a detection -> state `tracked` (evidence class detected), with the detection;
- a run of eligible frames between two matched frames of the same track -> state `predicted` (evidence class inferred)
  with the tracker's predicted box when the run has <= g_max eligible frames; a longer run is lost (no point);
- after the last matched frame the track has no point (the tracker never re-found it), nor before the first.
"""
from __future__ import annotations

from typing import Dict, List, Optional

G_MAX = 15  # frozen pre-registration v1 base value (section 4.2)


def points_from_log(log: List[dict], g_max: int = G_MAX) -> Dict[int, dict]:
    """Track id -> {"points": [{"frame_index", "state", "bbox", "det_index"}], "counts": {...}} for every track with at
    least one matched frame. Points are in frame order. det_index is None on predicted points."""
    if g_max < 0:
        raise ValueError(f"g_max must be >= 0, got {g_max}")
    order = [e["frame_index"] for e in log]
    if order != sorted(order) or len(set(order)) != len(order):
        raise ValueError("log frames must be strictly increasing (eligible frames in decode order)")
    matched: Dict[int, Dict[int, tuple]] = {}
    predicted: Dict[int, Dict[int, List[float]]] = {}
    for pos, e in enumerate(log):
        for tid, det_index, box in e.get("tracked", []):
            if pos in matched.setdefault(int(tid), {}):
                raise ValueError(f"track {tid} matched twice on frame {e['frame_index']}")
            matched[int(tid)][pos] = (int(det_index), [float(v) for v in box])
        for tid, box in e.get("lost", []):
            predicted.setdefault(int(tid), {})[pos] = [float(v) for v in box]
    out: Dict[int, dict] = {}
    for tid in sorted(matched):
        hits = sorted(matched[tid])
        counts = {"tracked": len(hits), "predicted": 0, "lost_long_run": 0, "runs_bridged": 0, "runs_lost": 0}
        points = []
        for a, b in zip(hits, hits[1:] + [None]):
            det_index, box = matched[tid][a]
            points.append({"frame_index": order[a], "state": "tracked", "bbox": box, "det_index": det_index})
            if b is None or b - a == 1:
                continue
            run = range(a + 1, b)
            if len(run) > g_max:
                counts["lost_long_run"] += len(run)
                counts["runs_lost"] += 1
                continue
            counts["runs_bridged"] += 1
            for pos in run:
                pbox: Optional[List[float]] = predicted.get(tid, {}).get(pos)
                if pbox is None:
                    raise ValueError(f"track {tid}: no predicted box on bridged frame {order[pos]}")
                if not (pbox[0] < pbox[2] and pbox[1] < pbox[3]):
                    counts["predicted_degenerate"] = counts.get("predicted_degenerate", 0) + 1  # no area: no point
                    continue
                points.append({"frame_index": order[pos], "state": "predicted", "bbox": pbox, "det_index": None})
                counts["predicted"] += 1
        out[tid] = {"points": points, "counts": counts}
    return out


def foot_point(box: List[float]) -> List[float]:
    """Bottom-centre of a CF-IMG box (the T-21 full_camera rule, D-45 item 1)."""
    return [(box[0] + box[2]) / 2.0, box[3]]
