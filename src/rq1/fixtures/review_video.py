"""A synthetic fixture video for the V-02 tests and report screenshots: plain shapes on a grey floor, no footage.

Two "persons" (discs) and one "forklift" (rectangle) move across a 320 x 180 frame at 10 fps for 10 s, so the scene has
more than one person and the T22.4 outlines apply. `boxes()` gives the pixel box of each object per frame.
"""
from __future__ import annotations

from pathlib import Path

import av
import numpy as np

W, H, FPS, N = 320, 180, 10, 100


def _objects(k: int) -> dict[str, tuple[int, int, int, int]]:
    fx = 20 + 2 * k
    p1x = 280 - k
    p2x = 40 + k // 2
    return {"forklift": (fx, 80, fx + 60, 120), "person": (p1x - 8, 70, p1x + 8, 110), "person2": (p2x - 8, 20, p2x + 8, 60)}


def boxes() -> dict[str, list[list[float]]]:
    """Per object, [time_s, x1, y1, x2, y2] for every frame."""
    out: dict[str, list[list[float]]] = {}
    for k in range(N):
        for name, (x1, y1, x2, y2) in _objects(k).items():
            out.setdefault(name, []).append([k / FPS, float(x1), float(y1), float(x2), float(y2)])
    return out


def write(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(path), "w") as container:
        stream = container.add_stream("libx264", rate=FPS)
        stream.width, stream.height, stream.pix_fmt = W, H, "yuv420p"
        stream.options = {"crf": "28", "preset": "veryfast"}
        for k in range(N):
            img = np.full((H, W, 3), 120, dtype=np.uint8)
            for name, (x1, y1, x2, y2) in _objects(k).items():
                if name == "forklift":
                    img[y1:y2, x1:x2] = (200, 160, 40)
                else:
                    yy, xx = np.ogrid[:H, :W]
                    cy, cx, r = (y1 + y2) // 2, (x1 + x2) // 2, 8
                    img[(yy - cy) ** 2 + (xx - cx) ** 2 <= r * r] = (60, 90, 200)
            for packet in stream.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path
