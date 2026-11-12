"""PyAV reader: packets in bitstream order mapped to decoder output (AR-25, AR-26)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av

from rq1.fixtures.clips import apply_faults, read_faults

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


def read_packets(path: str | Path, faults_path: str | Path | None = None) -> tuple[list[PacketRecord], StreamInfo]:
    """Decode every packet. A packet that raises, or whose frame never appears, is an undecodable frame."""
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
            events += [("frame", f.pts, f.dts) for f in decoded]
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
        _, pts, dts = event
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
            records.append(PacketRecord(index, matched[index], pts, dts, True))
        elif index in failed:
            records.append(PacketRecord(index, seq_of_fail[index], pts, dts, False))
        else:
            records.append(PacketRecord(index, extra, pts, dts, False))
            extra += 1
    return records, info
