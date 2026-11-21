"""T-23s / T-25p: stream the eligible frames of one SDG validation recording to stdout (main `.venv`, PyAV, the decoder
of S1 and of the T-22 probe). Read by `s2_yolo_world.py` in `.venv-det`.

  PYTHONPATH=src .venv/bin/python research/m1b/s2_frames.py <rec_id>

Protocol, per eligible frame in decode order: one JSON line {"frame_index", "decode_seq", "height", "width"} followed by
height * width * 3 bytes of RGB (uint8, `to_ndarray(format="rgb24")`). A final line {"end": n_frames}.
Eligibility and frame_index come from the stored S1 `frame` table (rv2, reused, D-45 item 3b). Validation recordings
only: any other is refused with ERR-LEAKAGE (`m1a_common.Context.camera`).
"""
from __future__ import annotations

import json
import sys

import av

import pilot_common as pc
from rq1.ids import artifact as A
from rq1.schema import files


def main(rec_id: str) -> None:
    ctx = pc.m.Context("sdg")
    cam = ctx.camera(rec_id)
    entry = ctx.index[rec_id]
    frames = files.read_table(str(pc.ROOT / f"out/t17_sdg/{cam['s1']}/frame.parquet"), "frame", A.SCHEMA_VERSION)
    seq = {f["decode_seq"]: f["frame_index"] for f in frames if f["eligible"]}
    out = sys.stdout.buffer
    n = 0
    with av.open(str(pc.ROOT / "data" / entry["uri"])) as container:
        for k, frame in enumerate(container.decode(video=0)):
            if k not in seq:
                continue
            img = frame.to_ndarray(format="rgb24")
            h, w = img.shape[:2]
            out.write((json.dumps({"frame_index": seq[k], "decode_seq": k, "height": h, "width": w}) + "\n").encode())
            out.write(img.tobytes())
            n += 1
    if n != len(seq):
        raise SystemExit(f"{rec_id}: decoded {n} eligible frames, S1 lists {len(seq)}")
    out.write((json.dumps({"end": n}) + "\n").encode())
    out.flush()


if __name__ == "__main__":
    main(sys.argv[1])
