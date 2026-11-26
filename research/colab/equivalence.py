"""D-60 STEP 4 (c): equivalence check of the Colab GPU detector output against the stored CPU S2 raw files (2 tuning cameras).

Pass criteria (D-60, never loosened):
  C1 every CPU detection with score >= threshold + 0.02 has a Colab detection of the same class with IoU >= 0.95;
  C2 the score difference of matched pairs has P99 <= 0.02;
  C3 detection counts per class differ by <= 2 %.
Thresholds: the D-45 class thresholds, person 0.20, forklift 0.05. Readings (AR-70 item 6; where the ruling leaves a
choice, the stricter one is applied, and the check passes only if every reading passes):
- pairs are formed per frame and class, one-to-one, greedy by IoU descending (ties: CPU box order, then Colab box order),
  among CPU boxes with score >= threshold and Colab boxes of the stored file (score >= 0.05) with IoU >= 0.95;
- C1 uses those one-to-one pairs (a Colab box serves at most one CPU box);
- C2 is |score_colab - score_cpu|, P99 by numpy's default linear interpolation, on two sets: the matched pairs of the
  CPU boxes >= threshold, and of the CPU boxes >= threshold + 0.02; both must be <= 0.02;
- C3 counts boxes with score >= threshold, per class, for each camera and for the two cameras together:
  |n_colab - n_cpu| <= 0.02 * n_cpu (n_cpu = 0 requires n_colab = 0);
- both files must list the same eligible frames (decode_seq, frame_index) in the same order, else the check fails.
Usage: python research/colab/equivalence.py <cpu_dir> <colab_dir> <rec_id> [<rec_id> ...] > result.json
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np

THRESHOLDS = {"person": 0.20, "forklift": 0.05}  # D-45 item 0
MARGIN, IOU_MIN, P99_MAX, COUNT_REL_MAX = 0.02, 0.95, 0.02, 0.02
EPS = 1e-9  # comparison allowance for rounded scores (stored to 6 decimals)


def iou(a: list[float], b: list[float]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def kept(dets: list[dict], cls: str) -> list[dict]:
    return [d for d in dets if d["class"] == cls and d["score"] >= THRESHOLDS[cls] - EPS]


def match_frame(cpu: list[dict], gpu: list[dict], cls: str) -> list[tuple[int, int, float]]:
    """One-to-one pairs (cpu index in kept(cpu), gpu index among gpu boxes of cls, IoU), greedy by IoU descending."""
    a = kept(cpu, cls)
    b = [d for d in gpu if d["class"] == cls]
    cand = sorted(((-iou(x["box"], y["box"]), i, j) for i, x in enumerate(a) for j, y in enumerate(b)), key=lambda t: (t[0], t[1], t[2]))
    used_a, used_b, pairs = set(), set(), []
    for neg, i, j in cand:
        if -neg < IOU_MIN - EPS:
            break
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        pairs.append((i, j, -neg))
    return pairs


def p99(values: list[float]) -> float | None:
    return float(np.percentile(np.asarray(values, dtype=float), 99)) if values else None


def compare(cpu: dict, gpu: dict) -> dict:
    """Per-camera tallies. Raises nothing: a frame mismatch is reported and fails the check."""
    fa = [(f["decode_seq"], f["frame_index"]) for f in cpu["frames"]]
    fb = [(f["decode_seq"], f["frame_index"]) for f in gpu["frames"]]
    out = {"rec_id": cpu["rec_id"], "frames_cpu": len(fa), "frames_colab": len(fb), "frames_equal": fa == fb, "classes": {}}
    if fa != fb:
        return out
    for cls, thr in THRESHOLDS.items():
        n_cpu = n_gpu = strict = strict_matched = 0
        diff_all, diff_strict, unmatched = [], [], []
        for f, g in zip(cpu["frames"], gpu["frames"]):
            a = kept(f["detections"], cls)
            b = [d for d in g["detections"] if d["class"] == cls]
            n_cpu += len(a)
            n_gpu += len(kept(g["detections"], cls))
            pairs = {i: j for i, j, _ in match_frame(f["detections"], g["detections"], cls)}
            for i, d in enumerate(a):
                hi = d["score"] >= thr + MARGIN - EPS
                strict += hi
                if i in pairs:
                    delta = abs(b[pairs[i]]["score"] - d["score"])
                    diff_all.append(delta)
                    if hi:
                        diff_strict.append(delta)
                        strict_matched += 1
                elif hi:
                    unmatched.append({"decode_seq": f["decode_seq"], "box": d["box"], "score": d["score"]})
        out["classes"][cls] = {"threshold": thr, "n_cpu": n_cpu, "n_colab": n_gpu, "cpu_at_or_above_threshold_plus_margin": strict,
                               "matched_at_or_above_threshold_plus_margin": strict_matched, "unmatched_examples": unmatched[:20], "unmatched": len(unmatched),
                               "matched_pairs": len(diff_all), "score_diff_p99_all_kept": p99(diff_all), "score_diff_p99_plus_margin": p99(diff_strict),
                               "score_diff_max_all_kept": max(diff_all) if diff_all else None, "_diff_all": diff_all, "_diff_strict": diff_strict}
    return out


def count_ok(n_cpu: int, n_gpu: int) -> bool:
    return abs(n_gpu - n_cpu) <= COUNT_REL_MAX * n_cpu + EPS


def verdict(cams: list[dict]) -> dict:
    checks = []
    for c in cams:
        checks.append({"check": "frames_equal", "rec_id": c["rec_id"], "pass": c["frames_equal"]})
        for cls, k in c.get("classes", {}).items():
            checks.append({"check": "C1", "rec_id": c["rec_id"], "class": cls, "value": k["unmatched"], "pass": k["unmatched"] == 0})
            for key, name in (("score_diff_p99_all_kept", "C2_all_kept"), ("score_diff_p99_plus_margin", "C2_plus_margin")):
                checks.append({"check": name, "rec_id": c["rec_id"], "class": cls, "value": k[key], "pass": k[key] is None or k[key] <= P99_MAX + EPS})
            checks.append({"check": "C3", "rec_id": c["rec_id"], "class": cls, "value": [k["n_cpu"], k["n_colab"]], "pass": count_ok(k["n_cpu"], k["n_colab"])})
    if all(c["frames_equal"] for c in cams):
        for cls in THRESHOLDS:
            diffs = [d for c in cams for d in c["classes"][cls]["_diff_all"]]
            strict = [d for c in cams for d in c["classes"][cls]["_diff_strict"]]
            n_cpu = sum(c["classes"][cls]["n_cpu"] for c in cams)
            n_gpu = sum(c["classes"][cls]["n_colab"] for c in cams)
            checks.append({"check": "C2_all_kept", "rec_id": "both", "class": cls, "value": p99(diffs), "pass": not diffs or p99(diffs) <= P99_MAX + EPS})
            checks.append({"check": "C2_plus_margin", "rec_id": "both", "class": cls, "value": p99(strict), "pass": not strict or p99(strict) <= P99_MAX + EPS})
            checks.append({"check": "C3", "rec_id": "both", "class": cls, "value": [n_cpu, n_gpu], "pass": count_ok(n_cpu, n_gpu)})
    for c in cams:
        for k in c.get("classes", {}).values():
            k.pop("_diff_all", None)
            k.pop("_diff_strict", None)
    return {"pass": all(x["pass"] for x in checks), "failed": [x for x in checks if not x["pass"]], "checks": checks, "cameras": cams,
            "criteria": {"C1": "CPU score >= threshold + 0.02 -> Colab box, same class, IoU >= 0.95 (one-to-one)", "C2": "P99 |score diff| of matched pairs <= 0.02",
                         "C3": "per-class counts (score >= threshold) differ by <= 2 %", "thresholds": THRESHOLDS}}


def load(path: Path) -> dict:
    with gzip.open(path, "rt") as f:
        return json.load(f)


def main(cpu_dir: str, colab_dir: str, recs: list[str]) -> dict:
    cams = [compare(load(Path(cpu_dir) / f"{r}.json.gz"), load(Path(colab_dir) / f"{r}.json.gz")) for r in recs]
    return verdict(cams)


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2], sys.argv[3:]), indent=1))
