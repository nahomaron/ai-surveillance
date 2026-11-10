"""Clip fixture factory (WP-02 part 2, T-04), PyAV only. Regenerate the manifest with `python -m rq1.fixtures.clips`.

Containers repair missing timestamps when muxing, so a file cannot hold a frame without one. Clips that need
a timestamp fault are therefore real encoded files plus a `.faults.json` overlay applied to packets at demux,
before decoding (AR-21). Corrupt packets are real corrupted bytes inside the file.
"""
from __future__ import annotations

import fractions
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import av
import numpy as np

TIME_BASE = fractions.Fraction(1, 1000)
SIZE = 64
CASE_TIMES = [0, 33, 66, 100]


@dataclass(frozen=True)
class Clip:
    times_ms: list[int]
    source: str
    b_frames: int = 0
    gop: int = 1
    corrupt_packets: frozenset[int] = frozenset()
    faults: dict[int, dict[str, int | None]] = field(default_factory=dict)  # packet index (decode order) to overrides


def _constant(n: int, step: int = 33) -> list[int]:
    return [i * step for i in range(n)]


def _vfr(limit_ms: int, *, gap_after: int | None = None) -> list[int]:
    times, t, i = [], 0, 0
    while t < limit_ms:
        times.append(t)
        t += 33 if i % 2 == 0 else 50
        if gap_after is not None and i == gap_after:
            t += 500 - (33 if i % 2 == 0 else 50)
        i += 1
    return times


_DROPOUT = _constant(90) + [_constant(90)[-1] + 4000 + i * 33 for i in range(90)]
CLIPS: dict[str, Clip] = {
    "fx_clip_a": Clip(CASE_TIMES, "Clarification 2.3 case A (AR-21); Appendix N3; CT-T-14", corrupt_packets=frozenset({1})),
    "fx_clip_b": Clip(CASE_TIMES, "Clarification 2.3 case B (AR-21); Appendix N3; CT-T-15", faults={1: {"pts": None, "dts": None}}),
    "fx_clip_c": Clip(CASE_TIMES, "Clarification 2.3 case C (AR-21); Appendix N3; CT-T-16", b_frames=2, gop=12, faults={2: {"pts": None}}),
    "fx_clip_d": Clip(CASE_TIMES, "Clarification 2.3 case D (AR-21); Appendix N3; CT-T-17", faults={1: {"pts": None}}),
    "ct_t_01_vfr": Clip(_vfr(10000), "Appendix T CT-T-01: 10 s, intervals alternating 33 and 50 ms"),
    "ct_t_02_bframes": Clip(_constant(30), "Appendix T CT-T-02: B-frames", b_frames=2, gop=12),
    "ct_t_02_all_intra": Clip(_constant(30), "Appendix T CT-T-02: all-I copy of ct_t_02_bframes"),
    "ct_t_03_dup_pts": Clip(_constant(30), "Appendix T CT-T-03: two frames share a PTS", faults={10: {"pts": 297, "dts": 297}}),
    "ct_t_04_dropout": Clip(_DROPOUT, "Appendix T CT-T-04: 4 s dropout inside a file"),
    "ct_t_05_corrupt": Clip(_constant(60), "Appendix T CT-T-05: 15 undecodable frames", corrupt_packets=frozenset(range(20, 35))),
    "ct_t_07_file_a": Clip(_constant(60), "Appendix T CT-T-07: first of two files from one camera"),
    "ct_t_07_file_b": Clip(_constant(60), "Appendix T CT-T-07: second of two files from one camera"),
    "ct_t_08_untimed": Clip(_constant(20), "Appendix T CT-T-08: stream without timestamps", faults={i: {"pts": None, "dts": None} for i in range(20)}),
    "fx_10": Clip(_vfr(5000, gap_after=60), "Appendix T FX-10: VFR, one 0.5 s PTS gap, one corrupt frame", corrupt_packets=frozenset({10})),
}
_SHADE_OFFSET = {"ct_t_07_file_b": 97}  # keeps the two CT-T-07 files distinct in content


def _encode(clip: Clip, shade: int) -> tuple[av.CodecContext, list[av.Packet]]:
    context = av.CodecContext.create("mpeg4", "w")
    context.width = context.height = SIZE
    context.pix_fmt = "yuv420p"
    context.time_base = TIME_BASE
    context.framerate = 30
    context.thread_count = 1
    context.gop_size = clip.gop
    context.max_b_frames = clip.b_frames
    context.options = {"flags": "+bitexact"}
    packets: list[av.Packet] = []
    for index, t in enumerate(clip.times_ms):
        image = np.full((SIZE, SIZE, 3), (40 * index + 20 + shade) % 250, np.uint8)
        frame = av.VideoFrame.from_ndarray(image, format="rgb24").reformat(format="yuv420p")
        frame.pts, frame.time_base = t, TIME_BASE
        packets += context.encode(frame)
    return context, packets + context.encode(None)


def _write(path: Path, clip: Clip, shade: int) -> None:
    context, packets = _encode(clip, shade)
    with av.open(str(path), "w", format="matroska", options={"fflags": "+bitexact"}) as output:
        stream = output.add_stream("mpeg4", rate=30)
        stream.width = stream.height = SIZE
        stream.pix_fmt = "yuv420p"
        stream.time_base = TIME_BASE
        stream.codec_context.extradata = context.extradata
        for index, packet in enumerate(packets):
            data = b"\xff" * packet.size if index in clip.corrupt_packets else bytes(packet)
            copy = av.Packet(data)
            copy.stream, copy.time_base = stream, TIME_BASE
            copy.pts, copy.dts = packet.pts, packet.dts
            output.mux(copy)


def read_faults(path: str | Path) -> dict[int, dict[str, int | None]]:
    return {int(k): v for k, v in json.loads(Path(path).read_text(encoding="utf-8")).items()}


def apply_faults(index: int, packet: av.Packet, faults: dict[int, dict[str, int | None]]) -> None:
    """Apply the overlay to a demuxed packet before it is decoded (TEST-ONLY)."""
    for name, value in faults.get(index, {}).items():
        setattr(packet, name, value)


def build_all(out_dir: str | Path) -> dict[str, Any]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    entries: dict[str, Any] = {}
    for name in sorted(CLIPS):
        clip = CLIPS[name]
        path = target / f"{name}.mkv"
        _write(path, clip, _SHADE_OFFSET.get(name, 0))
        overlay = target / f"{name}.faults.json"
        overlay.write_text(json.dumps({str(k): v for k, v in sorted(clip.faults.items())}, sort_keys=True) + "\n", encoding="utf-8")
        entries[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "faults_sha256": hashlib.sha256(overlay.read_bytes()).hexdigest(),
                         "n_frames": len(clip.times_ms), "source": clip.source}
    return {"contract": "E-1.2.3", "pyav": av.__version__, "clips": entries}


if __name__ == "__main__":
    manifest = build_all(Path("out/fixture_clips"))
    Path("fixtures/clips_manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
