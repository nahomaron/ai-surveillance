"""PyAV reader: packets in bitstream order mapped to decoder output (AR-25, AR-26)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

from rq1.fixtures.clips import apply_faults, read_faults

from . import quality
from .timestamps import PacketRecord

DECODE_ERRORS = (av.error.InvalidDataError,)


@dataclass(frozen=True)
class StreamInfo:
    time_base: Fraction
    width: int
    height: int
    decoder_build: str


def decoder_build() -> str:
    return f"PyAV {av.__version__}; libavcodec {'.'.join(map(str, av.library_versions['libavcodec']))}"


def luma_plane(frame: av.VideoFrame) -> np.ndarray:
    """The 8-bit luma plane as decoded (no range conversion) for planar YUV; other formats are converted to gray."""
    name = frame.format.name
    if name.startswith(("yuv", "yuvj", "nv12", "nv21")) and frame.planes[0].line_size >= frame.width:
        plane = frame.planes[0]
        return np.frombuffer(plane, np.uint8).reshape(frame.height, plane.line_size)[:, :frame.width]
    return frame.to_ndarray(format="gray")


def read_packets(path: str | Path, faults_path: str | Path | None = None, luma_stats: bool = False) -> tuple[list[PacketRecord], StreamInfo]:
    """Decode every packet. A packet that raises, or whose frame never appears, is an undecodable frame.
    With `luma_stats`, each decoded frame's luma statistics are kept (rules versions that need pixels); pixels are not."""
    faults = read_faults(faults_path) if faults_path else {}
    fed: list[tuple[int, int | None, int | None]] = []
    events: list[tuple] = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        info = StreamInfo(Fraction(stream.time_base), stream.codec_context.width, stream.codec_context.height, decoder_build())
        for packet in container.demux(stream):
            if packet.size:
                index = len(fed)
                apply_faults(index, packet, faults)
                fed.append((index, packet.pts, packet.dts))
                try:
                    decoded = packet.decode()
                except DECODE_ERRORS:
                    events.append(("fail", index))
                    continue
            else:
                decoded = packet.decode()
            events += [("frame", f.pts, f.dts, quality.stats(luma_plane(f)) if luma_stats else None) for f in decoded]
    matched: dict[int, int] = {}
    failed = {e[1] for e in events if e[0] == "fail"}
    seq_of_fail = {e[1]: i for i, e in enumerate(events) if e[0] == "fail"}

    def take(predicate) -> int | None:
        for index, pts, dts in fed:
            if index not in matched and index not in failed and predicate(pts, dts):
                return index
        return None

    for seq, event in enumerate(events):
        if event[0] != "frame":
            continue
        _, pts, dts, _ = event
        index = take(lambda p, d: pts is not None and p == pts)
        if index is None and dts is not None:
            index = take(lambda p, d: p is None and d == dts)
        if index is None:
            index = take(lambda p, d: p is None and d is None)
        if index is None:
            index = take(lambda p, d: True)
        if index is not None:
            matched[index] = seq
    records, extra = [], len(events)
    for index, pts, dts in fed:
        if index in matched:
            records.append(PacketRecord(index, matched[index], pts, dts, True, events[matched[index]][3]))
        elif index in failed:
            records.append(PacketRecord(index, seq_of_fail[index], pts, dts, False))
        else:
            records.append(PacketRecord(index, extra, pts, dts, False))
            extra += 1
    return records, info
