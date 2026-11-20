"""Evidence clips for workflow reports (T23.2 d): one evidence_clip row per member episode.

decoded_frame_sha256 holds the SHA-256 of each decoded frame's 8-bit luma plane, the same digest S1 computes
(`rq1.decode.quality.stats`), for frames [start_frame, end_frame_excl) in decode order (AR-63 item 7).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import av
import numpy as np

from rq1.decode.video import luma_plane


def frame_hashes(video: str | Path, start_frame: int, end_frame_excl: int) -> list[str]:
    out: list[str] = []
    with av.open(str(video)) as container:
        for k, frame in enumerate(container.decode(video=0)):
            if k >= end_frame_excl:
                break
            if k >= start_frame:
                y = np.ascontiguousarray(luma_plane(frame), dtype=np.uint8)
                out.append(hashlib.sha256(y.tobytes()).hexdigest())
    return out
