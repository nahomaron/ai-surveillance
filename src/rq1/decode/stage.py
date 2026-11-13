"""S1 stage: decode summary, frames and coverage segments for one timeline (E-1.2.1 sections 3.2-3.5, 5.3)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.schema.errors import ContractError

from . import quality, timestamps, video
from .timestamps import DecodeConfig, Piece, Resolved

Row = dict[str, Any]


@dataclass(frozen=True)
class S1Input:
    recording_id: str
    camera_id: str
    path: Path
    faults_path: Path | None = None  # TEST-ONLY timestamp-fault overlay (AR-21)
    offset_s: float = 0.0  # clock alignment, aligned_session timelines only
    drift_ppm: float = 0.0


def _nullable(value: Any, reason: str) -> tuple[Any, Any]:
    return value, (None if value is not None else reason)


def _f(value: Fraction | None) -> float | None:
    return None if value is None else float(value)


def run_s1(timeline: Row, inputs: list[S1Input], cfg: DecodeConfig, spec: Spec) -> Artifact:
    """Raises ERR-TIMESTAMPS before anything is written, so a rejected recording leaves no artifact."""
    summaries, frame_rows, by_camera = [], [], {}
    aligned = timeline["kind"] == "aligned_session"
    for item in inputs:
        packets, info = video.read_packets(item.path, item.faults_path, luma_stats=quality.needs_pixels(cfg.rules_version))
        declared = cfg.declared.get(item.recording_id)
        result = timestamps.resolve(packets, info.time_base, cfg, None if declared is None else Fraction(str(declared)))
        scale = 1 + Fraction(str(item.drift_ppm)) / 1_000_000 if aligned else Fraction(1)
        offset = Fraction(str(item.offset_s)) if aligned else Fraction(0)

        def to_tl(t: Fraction) -> Fraction:
            return t * scale + offset

        frame_rows += [_frame_row(item.recording_id, f, to_tl, scale) for f in result.frames]
        summaries.append(_summary_row(item.recording_id, info, result, to_tl))
        mapped = [Piece(to_tl(p.start), to_tl(p.end), p.state, p.reasons, p.support * scale, p.frame_seqs) for p in result.pieces]
        by_camera.setdefault(item.camera_id, []).append((item.recording_id, mapped, {f.seq: f.frame_index for f in result.frames}))
    coverage = []
    for camera_id, recordings in sorted(by_camera.items()):
        coverage += _coverage(timeline, camera_id, recordings, cfg.rules_version)
    return build_artifact(spec, {"decode_summary": summaries, "frame": frame_rows, "coverage_segment": coverage})


def _frame_row(recording_id: str, f: timestamps.FrameResult, to_tl, scale: Fraction) -> Row:
    row = {"recording_id": recording_id, "decode_seq": f.index, "ts_source": f.ts_source, "ts_status": f.ts_status, "decode_ok": f.decode_ok,
           "quality_flags": list(f.quality_flags), "eligible": f.eligible, "support_s": float(f.support * scale), "support_status": f.support_status}
    row["frame_index"], row["frame_index_null_reason"] = _nullable(f.frame_index, "not_applicable")
    row["pts"], row["pts_null_reason"] = _nullable(f.pts, "not_observable")
    row["t_resolved_s"], row["t_resolved_s_null_reason"] = _nullable(_f(f.t), "not_observable")
    row["t_tl_s"], row["t_tl_s_null_reason"] = _nullable(_f(None if f.t is None else to_tl(f.t)), "not_observable")
    row["support_start_tl_s"], row["support_start_tl_s_null_reason"] = _nullable(_f(None if f.support_start is None else to_tl(f.support_start)), "not_observable")
    return row


def _summary_row(recording_id: str, info: video.StreamInfo, r: Resolved, to_tl) -> Row:
    row = {"recording_id": recording_id, "decoder_build": info.decoder_build, "width_px": info.width, "height_px": info.height,
           "time_base_num": info.time_base.numerator, "time_base_den": info.time_base.denominator, "n_frames_decoded": len(r.frames),
           "n_frames_timed": sum(1 for f in r.frames if f.t is not None), "n_frames_eligible": sum(1 for f in r.frames if f.eligible),
           "reorder_depth": r.reorder_depth, "vfr_detected": r.vfr_detected, "delta_nom_s": float(r.delta_nom), "delta_nom_source": r.delta_nom_source,
           "substituted_support_frac": r.substituted_frac, "untimed_frac": r.untimed_frac,
           "extent_start_tl_s": float(to_tl(r.extent[0])), "extent_end_tl_s": float(to_tl(r.extent[1])), "rejected": False}
    row["delta_nom_declared_s"], row["delta_nom_declared_s_null_reason"] = _nullable(_f(r.delta_nom_declared), "not_supplied")
    row["delta_nom_median_s"], row["delta_nom_median_s_null_reason"] = _nullable(_f(r.delta_nom_median), "not_applicable")
    return row


def _segment(timeline: Row, camera_id: str, recording_id: str | None, piece: Piece, frame_index: dict[int, int | None], rules_version: str) -> Row:
    indices = sorted(i for i in (frame_index.get(s) for s in piece.frame_seqs) if i is not None)
    row = {"timeline_id": timeline["tl_id"], "camera_id": camera_id, "t_start_tl_s": float(piece.start), "t_end_tl_s": float(piece.end),
           "coverage_state": piece.state, "support_s": float(piece.support), "unusable_reasons": list(piece.reasons), "rules_version": rules_version}
    row["recording_id"], row["recording_id_null_reason"] = _nullable(recording_id, "not_applicable")
    row["start_frame"], row["start_frame_null_reason"] = _nullable(indices[0] if indices else None, "not_applicable")
    row["end_frame_excl"], row["end_frame_excl_null_reason"] = _nullable(indices[-1] + 1 if indices else None, "not_applicable")
    return row


def _coverage(timeline: Row, camera_id: str, recordings: list, rules_version: str) -> list[Row]:
    """Section 3.5: tile the (timeline, camera) extent exactly once, without detector output (CT-E-04)."""
    items = sorted(((rec, p, idx) for rec, pieces, idx in recordings for p in pieces), key=lambda x: x[1].start)
    for (_, a, _), (_, b, _) in zip(items, items[1:]):
        if b.start < a.end:
            raise ContractError("ERR-INVARIANT", "recordings of one camera overlap on the timeline")
    rows: list[Row] = []
    if timeline["kind"] == "aligned_session":
        cursor, end = Fraction(str(timeline["extent_start_tl_s"])), Fraction(str(timeline["extent_end_tl_s"]))
        if items[0][1].start < cursor or items[-1][1].end > end:
            raise ContractError("ERR-INVARIANT", "recording support outside the declared timeline extent")
    else:
        cursor, end = items[0][1].start, items[-1][1].end
    for recording_id, piece, frame_index in items:
        if piece.start > cursor:  # TI-11: only reachable on aligned_session timelines
            rows.append(_segment(timeline, camera_id, None, Piece(cursor, piece.start, "not_recorded", (), Fraction(0)), {}, rules_version))
        rows.append(_segment(timeline, camera_id, recording_id, piece, frame_index, rules_version))
        cursor = piece.end
    if cursor < end:
        rows.append(_segment(timeline, camera_id, None, Piece(cursor, end, "not_recorded", (), Fraction(0)), {}, rules_version))
    return rows
