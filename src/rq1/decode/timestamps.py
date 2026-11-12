"""S1 core: timestamp resolution, eligibility, delta_nom and support (E-1.2.1 sections 3.2-3.3; Appendix T T7).

Pure functions over packet records. Times are exact `Fraction`s; floats appear only in stored rows.
`decode_seq` is the demux (file/DTS) position (T7.1). The presentation index used by `reorder_depth` is the
decoder output position, which also places untimed frames (AR-25 as reviewed).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from fractions import Fraction

from rq1.schema.errors import ContractError

EXCLUSION_FLAGS = {"rv1": {"decode_error"}}  # AR-27: rules version rv1 excludes undecodable frames only


@dataclass(frozen=True)
class PacketRecord:
    index: int  # demux (file/DTS) order: the stored decode_seq (T7.1)
    seq: int  # decoder output position, with undecodable frames placed where decoding failed
    pts: int | None
    dts: int | None
    decode_ok: bool


@dataclass(frozen=True)
class DecodeConfig:
    k_sup: float
    f_untimed: float
    f_sub: float
    rules_version: str
    declared: dict[str, float]  # recording_id -> delta_nom_s (T7 step 1)
    final_frame_support: str = "delta_nom"  # or "zero": the section 3.3 sensitivity variant


@dataclass
class FrameResult:
    seq: int
    index: int
    pts: int | None
    ts_source: str
    ts_status: str
    t: Fraction | None
    decode_ok: bool
    quality_flags: list[str]
    eligible: bool = False
    frame_index: int | None = None
    support_start: Fraction | None = None
    support: Fraction = Fraction(0)
    support_status: str = "zero_untimed"


@dataclass(frozen=True)
class Piece:
    start: Fraction
    end: Fraction
    state: str
    reasons: tuple[str, ...]
    support: Fraction
    frame_seqs: tuple[int, ...] = field(default_factory=tuple)


@dataclass
class Resolved:
    frames: list[FrameResult]
    pieces: list[Piece]
    uncertain: list[tuple[Fraction, Fraction]]
    reorder_depth: int
    delta_nom: Fraction
    delta_nom_source: str
    delta_nom_declared: Fraction | None
    delta_nom_median: Fraction | None
    substituted_frac: float
    untimed_frac: float
    vfr_detected: bool
    extent: tuple[Fraction, Fraction]


def _exact(value: float) -> Fraction:
    return Fraction(str(value))


def _merge(regions: list[tuple[Fraction, Fraction]]) -> list[tuple[Fraction, Fraction]]:
    out: list[tuple[Fraction, Fraction]] = []
    for a, b in sorted(regions):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _split(piece: Piece, regions: list[tuple[Fraction, Fraction]]) -> list[Piece]:
    """Cut a piece at uncertainty boundaries; parts inside become unusable `untimed_frame` (section 3.3)."""
    cuts = sorted({piece.start, piece.end} | {x for r in regions for x in r if piece.start < x < piece.end})
    parts = []
    for a, b in zip(cuts, cuts[1:]):
        inside = any(r[0] <= a and b <= r[1] for r in regions)
        share = piece.support * (b - a) / (piece.end - piece.start) if piece.support else Fraction(0)
        if inside:
            reasons = tuple(sorted({"untimed_frame", *(piece.reasons if piece.state == "unusable" else ())}))
            parts.append(Piece(a, b, "unusable", reasons, share, piece.frame_seqs))
        else:
            parts.append(Piece(a, b, piece.state, piece.reasons, share, piece.frame_seqs))
    return parts


def resolve(packets: list[PacketRecord], time_base: Fraction, cfg: DecodeConfig, declared: Fraction | None) -> Resolved:
    records = sorted(packets, key=lambda p: p.seq)
    rank = {p.seq: i for i, p in enumerate(records)}
    depth = max((abs(rank[p.seq] - p.index) for p in records if p.pts is not None), default=0)
    radius = max(1, depth)
    frames: list[FrameResult] = []
    for p in records:  # step 2: PTS, then DTS-derived only at reorder depth 0 (AR-26)
        if p.pts is not None:
            tick, source = p.pts, "pts"
        elif p.dts is not None and depth == 0:
            tick, source = p.dts, "dts_derived"
        else:
            tick, source = None, "none"
        status = "untimed" if tick is None else ("substituted" if source == "dts_derived" else ("reordered" if rank[p.seq] != p.index else "ok"))
        flags = [] if p.decode_ok else ["decode_error"]
        frames.append(FrameResult(p.seq, p.index, p.pts, source, status, None if tick is None else Fraction(tick) * time_base, p.decode_ok, flags))
    n = len(frames)
    untimed = [f for f in frames if f.t is None]
    untimed_frac = len(untimed) / n if n else 1.0
    if untimed_frac > cfg.f_untimed:
        raise ContractError("ERR-TIMESTAMPS", f"untimed fraction {untimed_frac:.3f} exceeds f_untimed {cfg.f_untimed}")
    first_at: dict[Fraction, FrameResult] = {}
    for f in sorted(frames, key=lambda f: f.index):  # step 3: duplicates keep the lowest decode_seq
        if f.t is not None:
            if f.t in first_at:
                f.ts_status, f.support_status, f.support_start = "duplicate", "zero_duplicate", f.t
            else:
                first_at[f.t] = f
    timeline = sorted(first_at.values(), key=lambda f: (f.t, f.index))
    if len(timeline) < 2:
        raise ContractError("ERR-TIMESTAMPS", "fewer than 2 timed frames (T7 step 4)")
    excluded = EXCLUSION_FLAGS[cfg.rules_version]
    for f in timeline:  # step 4
        f.eligible = f.decode_ok and not (set(f.quality_flags) & excluded)
    for i, f in enumerate(sorted((f for f in timeline if f.eligible), key=lambda f: (f.t, f.index))):  # step 5
        f.frame_index = i
    regions = []
    for u in untimed:  # ST-2, in demux order
        near = [f.t for f in frames if f.t is not None and abs(f.index - u.index) <= radius and f is not u]
        if near and min(near) < max(near):
            regions.append((min(near), max(near)))
    regions = _merge(regions)
    # T7.1 step 2: consecutive timed, non-duplicate frames in presentation order, excluding pairs overlapping U.
    pairs = [b.t - a.t for a, b in zip(timeline, timeline[1:]) if not any(a.t < r1 and r0 < b.t for r0, r1 in regions)]
    all_timed = [b.t - a.t for a, b in zip(timeline, timeline[1:])]
    median = Fraction(statistics.median(pairs)) if pairs else None
    if declared is not None:  # T7 precedence
        delta_nom, source = declared, "declared_config"
    elif median is not None:
        delta_nom, source = median, "median_adjacent_pairs"
    else:
        delta_nom, source = Fraction(statistics.median(all_timed)), "median_all_timed"
    delta_max = _exact(cfg.k_sup) * delta_nom
    pieces: list[Piece] = []
    for k, f in enumerate(timeline):  # section 3.3, support over every timed frame
        f.support_start = f.t
        if k + 1 < len(timeline):
            gap = timeline[k + 1].t - f.t
            if gap <= delta_max:
                f.support, f.support_status = gap, "measured"
            else:
                f.support, f.support_status = delta_nom, "capped"
                pieces.append(Piece(f.t + delta_nom, timeline[k + 1].t, "gap_unobserved", (), Fraction(0)))
        else:
            f.support = delta_nom if cfg.final_frame_support == "delta_nom" else Fraction(0)
            f.support_status = "final_assumed"
        if not f.eligible:
            f.support_status = "excluded_own_support"
        elif f.ts_source == "dts_derived" and f.support_status != "final_assumed":
            f.support_status = "substituted"
    for f in timeline:
        if f.support and any(f.support_start < r[1] and r[0] < f.support_start + f.support for r in regions):
            f.support_status = "timing_uncertain"
    eligible_support = sum((f.support for f in timeline if f.eligible), Fraction(0))
    substituted = sum((f.support for f in timeline if f.eligible and f.ts_source == "dts_derived"), Fraction(0))
    substituted_frac = float(substituted / eligible_support) if eligible_support else 0.0
    degrade = substituted_frac > cfg.f_sub
    for f in timeline:
        if not f.support:
            continue
        if not f.eligible:
            piece = Piece(f.t, f.t + f.support, "unusable", tuple(sorted({"excluded_frame", *f.quality_flags})), f.support, (f.seq,))
        elif f.ts_source == "dts_derived" and degrade:
            piece = Piece(f.t, f.t + f.support, "usable_degraded", ("timing_substituted",), f.support, (f.seq,))
        else:
            piece = Piece(f.t, f.t + f.support, "usable", (), f.support, (f.seq,))
        pieces.append(piece)
    split = [part for piece in sorted(pieces, key=lambda p: p.start) for part in _split(piece, regions)]
    merged: list[Piece] = []
    for piece in split:
        last = merged[-1] if merged else None
        if last and last.end == piece.start and (last.state, last.reasons) == (piece.state, piece.reasons):
            merged[-1] = Piece(last.start, piece.end, last.state, last.reasons, last.support + piece.support, tuple(dict.fromkeys(last.frame_seqs + piece.frame_seqs)))
        else:
            merged.append(piece)
    spread = pairs or all_timed
    vfr = max(spread) - min(spread) > time_base
    end = max([timeline[-1].t] + [p.end for p in merged])
    return Resolved(frames, merged, regions, depth, delta_nom, source, declared, median, substituted_frac, untimed_frac, vfr, (timeline[0].t, end))
