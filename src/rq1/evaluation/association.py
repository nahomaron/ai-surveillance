"""Physical-identity association, system tracks to reference identities (F.1 A5.2).

Inputs per window and camera: system boxes and reference boxes per eligible frame. Every step is deterministic:
inputs are sorted canonically before the solver (system: track natural key; reference: physical_identity_id)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

Row = dict[str, Any]
MICRO = 1_000_000


@dataclass(frozen=True)
class Box:
    object_id: str  # track natural key (system) or physical_identity_id (reference)
    cls: str
    xyxy: tuple[float, float, float, float]


def box_iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def quantize(iou: float) -> int:
    return int(round(iou * MICRO))


def associate_frame(system: list[Box], reference: list[Box], iou_cm: float, eps_amb: float) -> list[tuple[str | None, str | None, str]]:
    """A5.2 steps 1-5 for one frame: (track, identity, status) rows."""
    sys_sorted = sorted(system, key=lambda b: b.object_id)
    ref_sorted = sorted(reference, key=lambda b: b.object_id)
    ious = {(s.object_id, r.object_id): box_iou(s.xyxy, r.xyxy) for s in sys_sorted for r in ref_sorted if s.cls == r.cls}
    floor = quantize(iou_cm)
    weight = lambda s, r: quantize(ious[(s, r)]) if (s, r) in ious and quantize(ious[(s, r)]) >= floor else 0
    assigned: list[tuple[str, str]] = []
    if sys_sorted and ref_sorted:
        matrix = np.array([[weight(s.object_id, r.object_id) for r in ref_sorted] for s in sys_sorted], dtype=float)
        rows, cols = linear_sum_assignment(matrix, maximize=True)
        assigned = [(sys_sorted[i].object_id, ref_sorted[j].object_id) for i, j in zip(rows, cols) if matrix[i, j] > 0]
    out: list[tuple[str | None, str | None, str]] = []
    used_sys, used_ref = {a for a, _ in assigned}, {x for _, x in assigned}
    tol = quantize(eps_amb)
    for s, r in assigned:
        value = quantize(ious[(s, r)])
        close = lambda pair: pair in ious and quantize(ious[pair]) >= floor and abs(value - quantize(ious[pair])) <= tol
        rival_refs = [x.object_id for x in ref_sorted if x.object_id != r and close((s, x.object_id))]
        rival_sys = [a.object_id for a in sys_sorted if a.object_id != s and close((a.object_id, r))]
        out.append((s, r, "ambiguous" if rival_refs or rival_sys else "matched"))
        # An unassigned rival's time on this frame is ambiguous too, never unmatched or missed (AR-39 item 1).
        out += [(s, x, "ambiguous") for x in rival_refs if x not in used_ref]
        out += [(a, r, "ambiguous") for a in rival_sys if a not in used_sys]
    seen_sys = {row[0] for row in out}
    seen_ref = {row[1] for row in out}
    out += [(b.object_id, None, "unmatched_system") for b in sys_sorted if b.object_id not in seen_sys]
    out += [(None, b.object_id, "missed_reference") for b in ref_sorted if b.object_id not in seen_ref]
    return sorted(out, key=lambda row: (row[0] or "", row[1] or "", row[2]))


def associate(frames: dict[int, tuple[list[Box], list[Box]]], iou_cm: float, eps_amb: float) -> list[Row]:
    """Frame-level association rows (`track_identity_assoc` content without window and camera keys), frame order."""
    out = []
    for i in sorted(frames):
        system, reference = frames[i]
        for track, identity, status in associate_frame(system, reference, iou_cm, eps_amb):
            out.append({"frame_index": i, "track_id": track, "physical_identity_id": identity, "status": status})
    return out


def summarize(rows: list[Row], support: dict[int, float]) -> tuple[list[Row], list[str]]:
    """`track_identity_summary` rows per track, and the reference identities with no matched frame (`missed_reference`)."""
    tracks = sorted({r["track_id"] for r in rows if r["track_id"] is not None})
    identities = sorted({r["physical_identity_id"] for r in rows if r["physical_identity_id"] is not None})
    matched = [r for r in rows if r["status"] == "matched"]
    covering: dict[str, set[str]] = {}
    for r in matched:
        covering.setdefault(r["physical_identity_id"], set()).add(r["track_id"])
    out = []
    for track in tracks:
        own = sorted((r for r in matched if r["track_id"] == track), key=lambda r: r["frame_index"])
        if not own:
            out.append({"track_id": track, "dominant_identity_id": None, "dominant_share": None, "n_identities": 0, "n_switches": 0, "status": "unmatched_system"})
            continue
        by_id: dict[str, float] = {}
        for r in own:
            by_id[r["physical_identity_id"]] = by_id.get(r["physical_identity_id"], 0.0) + support[r["frame_index"]]
        total = sum(by_id.values())
        dominant = min(by_id, key=lambda k: (-round(by_id[k], 9), k))  # largest support; ties to the lower identity ID
        switches = sum(1 for a, b in zip(own, own[1:]) if a["physical_identity_id"] != b["physical_identity_id"])
        if len(by_id) >= 2:
            status = "id_switch"
        elif len(covering[dominant]) >= 2:
            status = "fragment"
        else:
            status = "one_to_one"
        out.append({"track_id": track, "dominant_identity_id": dominant, "dominant_share": by_id[dominant] / total, "n_identities": len(by_id),
                    "n_switches": switches, "status": status})
    missed = [i for i in identities if i not in covering]
    return out, missed


def matched_support(rows: list[Row], support: dict[int, float]) -> dict[str, float]:
    """Support of `matched` frames per identity (input to CM-01/02, T-14)."""
    out: dict[str, float] = {}
    for r in rows:
        if r["status"] == "matched":
            out[r["physical_identity_id"]] = out.get(r["physical_identity_id"], 0.0) + support[r["frame_index"]]
    return out


def event_pair(rows: list[Row], summaries: list[Row], person_track: str, forklift_track: str, ca_frame: int | None) -> tuple[tuple[str, str] | None, dict[str, str]]:
    """A5.2 "Use downstream": each track's identity at the CA frame if `matched` there, else its dominant identity.
    If either side has neither, the pair is unknown (None): the event cannot match and counts as a false alert."""
    dominant = {s["track_id"]: s["dominant_identity_id"] for s in summaries}
    pair, via = [], {}
    for role, track in (("person", person_track), ("forklift", forklift_track)):
        at = next((r for r in rows if r["frame_index"] == ca_frame and r["track_id"] == track and r["status"] == "matched"), None)
        if at is not None:
            pair.append(at["physical_identity_id"])
            via[role] = "frame_association"
        elif dominant.get(track) is not None:
            pair.append(dominant[track])
            via[role] = "dominant_identity"
        else:
            return None, {}
    return (pair[0], pair[1]), via
