"""Tracker fixtures (D-45 item 1, T-23): oracle detections with injected dropouts and box noise. TEST-ONLY.

Pure Python (importable under Python 3.9 in `.venv-det`). Boxes are CF-IMG pixels on a 1920 x 1080 image.

FX-TRK-1 (`dropouts`): frames 0..119, frame 38 ineligible (not shown to the tracker).
- P1 (person, 40 x 100 px) moves right 3 px/frame from x1 = 100. Dropouts: frames 20..24 (5 eligible frames:
  bridged -> predicted) and 60..79 (20 eligible frames > g_max 15, < track_buffer 30: lost, same track resumes).
- P2 (person, 40 x 100 px) moves right 1 px/frame from x1 = 900. Dropout 30..45 = 16 camera frames, of which frame 38
  is ineligible -> 15 eligible frames = g_max: bridged -> predicted on its 15 eligible frames (T19 counting).
- F1 (forklift, 200 x 150 px) moves left 2 px/frame from x1 = 1500. Dropout 70..109 (40 eligible frames > track_buffer
  30): the tracker drops the track and starts a new one -> two tracks on one identity (fragment).
- Box noise: each coordinate + N(0, 1 px), seeded (random.Random(seed)); scores: person 0.9, forklift 0.6.

FX-TRK-2 (`swap`): frames 0..59, two persons standing still, Q1 at x1 = 200 and Q2 at x1 = 400 (40 x 100 px, y1 = 300).
From frame 30 on they exchange places. An IoU tracker keeps each location, so each track changes identity once
(identity switch on both tracks). No noise.
"""
from __future__ import annotations

import random
from typing import Dict, List, Tuple

SEED = 2026111903
W, H = 1920, 1080


def _box(x1: float, y1: float, w: float, h: float) -> List[float]:
    return [x1, y1, x1 + w, y1 + h]


def dropouts(seed: int = SEED, noise_px: float = 1.0) -> dict:
    rng = random.Random(seed)
    frames = list(range(120))
    ineligible = {38}
    objects = {
        "P1": ("person", lambda i: _box(100 + 3 * i, 300, 40, 100), set(range(20, 25)) | set(range(60, 80)), 0.9),
        "P2": ("person", lambda i: _box(900 + 1 * i, 500, 40, 100), set(range(30, 46)), 0.9),
        "F1": ("forklift", lambda i: _box(1500 - 2 * i, 700, 200, 150), set(range(70, 110)), 0.6),
    }
    return _render(frames, ineligible, objects, rng, noise_px)


def swap() -> dict:
    frames = list(range(60))
    objects = {
        "Q1": ("person", lambda i: _box(200 if i < 30 else 400, 300, 40, 100), set(), 0.9),
        "Q2": ("person", lambda i: _box(400 if i < 30 else 200, 300, 40, 100), set(), 0.9),
    }
    return _render(frames, set(), objects, random.Random(0), 0.0)


def _render(frames, ineligible, objects, rng, noise_px) -> dict:
    """{"frames": eligible frame_index list, "detections": S2-like rows, "truth": [(frame, identity, class, box)]}.
    Truth boxes are noise-free and present on every eligible frame (the simulator sees through dropouts)."""
    dets: List[dict] = []
    truth: List[Tuple[int, str, str, List[float]]] = []
    eligible = [i for i in frames if i not in ineligible]
    for i in eligible:
        per: Dict[str, List[dict]] = {}
        for key in sorted(objects):
            cls, box_at, drop, score = objects[key]
            box = box_at(i)
            truth.append((i, key, cls, box))
            if i in drop:
                continue
            noisy = [v + (rng.gauss(0.0, noise_px) if noise_px else 0.0) for v in box]
            per.setdefault(cls, []).append({"box": noisy, "score": score, "key": key})
        k = 0
        for cls in ("person", "forklift"):
            for d in sorted(per.get(cls, []), key=lambda d: (-d["score"], d["box"][0], d["box"][1])):
                dets.append({"frame_index": i, "det_index": k, "class": cls, "bbox_xyxy_px": d["box"], "score": d["score"],
                             "_identity": d["key"]})
                k += 1
    return {"frames": eligible, "all_frames": list(frames), "detections": dets, "truth": truth, "width": W, "height": H}
