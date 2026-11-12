"""Event matching and match classes for one window (E-1.2.1 section 9.1, F.1 Appendix N4 normative tie rule)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment

from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError

MICRO = 1_000_000
GROUP_LABELS = {"G1": ("O", "H", "PC"), "G2": ("NM", "UD", "CT"), "any": ("O", "H", "PC", "NM", "UD", "CT")}


@dataclass(frozen=True)
class Reference:
    ref_event_id: str
    t_onset: float
    t_offset: float
    pair: tuple[str, str]
    assessable: bool = True


@dataclass(frozen=True)
class SystemEvent:
    nk: object  # natural key, compared by its JCS bytes
    system_event_id: str
    t_onset: float
    t_offset: float
    pair: tuple[str, str] | None  # A5.2 resolution; None = unknown pair
    labels: frozenset = field(default_factory=frozenset)  # e.g. {"H", "IE"}


def temporal_iou(a: tuple[float, float], b: tuple[float, float]) -> float:
    """|A intersect B| / |A union B| on half-open timeline intervals (N4)."""
    inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    return inter / (max(a[1], b[1]) - min(a[0], b[0])) if inter > 0 else 0.0


def in_group(event: SystemEvent, group: str) -> bool:
    return any(x in event.labels for x in GROUP_LABELS[group])


def is_abstained(labels) -> bool:
    """T10.7(a): lbl_IE and none of lbl_NM, lbl_UD, lbl_CT."""
    return "IE" in labels and not any(x in labels for x in ("NM", "UD", "CT"))


def abstained(event: SystemEvent, group: str) -> bool:
    """T10.7(a): abstention applies only to label group G2; nothing abstains in G1 or `any`."""
    return group == "G2" and is_abstained(event.labels)


def _onset_us(t: float) -> int:
    return int(round(t * MICRO))


def match_window(references: list[Reference], events: list[SystemEvent], group: str, iou_m: float, reference_class: str,
                 ref_groups: dict[str, frozenset]) -> list[dict]:
    """match_record content (without window, config and scenario keys) for one label group. `reference_class` is the
    class of the window's references (F.1 A5.1); it is recorded on every row, false alerts included (AR-39 item 5)."""
    # AR-39 item 3 (Architect ruling): label groups of references are a match-run input mapping ref_event_id -> groups,
    # produced by the reference producer (the CV-SIM converter for simulator references); it belongs to the inputs hash.
    missing = sorted(r.ref_event_id for r in references if r.ref_event_id not in ref_groups)
    if missing:
        raise ContractError("ERR-SPEC", f"no label-group entry for references {missing}")
    refs = sorted((r for r in references if group == "any" or group in ref_groups[r.ref_event_id]), key=lambda r: (_onset_us(r.t_onset), r.ref_event_id))
    deciding = sorted((e for e in events if in_group(e, group)), key=lambda e: canonical_json(e.nk))
    abstaining = [e for e in events if abstained(e, group)]
    assessable = [r for r in refs if r.assessable]
    n_rows, n_cols = len(assessable), len(deciding)
    iou = {(i, j): temporal_iou((r.t_onset, r.t_offset), (e.t_onset, e.t_offset)) for i, r in enumerate(assessable) for j, e in enumerate(deciding)}
    floor = int(round(iou_m * MICRO))
    candidate = {(i, j) for (i, j), v in iou.items()
                 if deciding[j].pair is not None and deciding[j].pair == assessable[i].pair and int(round(v * MICRO)) >= floor}
    matched: list[tuple[int, int]] = []
    if candidate:
        k = n_rows ** 2 * (n_cols + 1) + 1
        matrix = np.zeros((n_rows, n_cols), dtype=float)
        for i, j in candidate:
            b = (n_rows - i) * (n_cols + 1) + (n_cols - j)
            matrix[i, j] = int(round(iou[(i, j)] * MICRO)) * k + b  # N4 composite weight; exact below 2**53
        if matrix.max() >= 2 ** 53:
            raise OverflowError("composite weight exceeds exact float range")
        rows, cols = linear_sum_assignment(matrix, maximize=True)
        matched = sorted((i, j) for i, j in zip(rows, cols) if (i, j) in candidate)
    out = []
    for i, j in matched:
        r, e = assessable[i], deciding[j]
        out.append(_record(r, e, "matched", iou[(i, j)], reference_class))
    matched_refs = {i for i, _ in matched}
    matched_sys = {j for _, j in matched}
    for j, e in enumerate(deciding):
        if j in matched_sys:
            continue
        dup = any(iou[(i, j)] > 0 for i in matched_refs)
        out.append(_record(None, e, "duplicate_alert" if dup else "false_alert", None, reference_class))
    for i, r in enumerate(assessable):
        if i in matched_refs:
            continue
        overlapped_deciding = any(iou[(i, j)] > 0 for j in range(n_cols))
        overlapped_abstaining = any(temporal_iou((r.t_onset, r.t_offset), (e.t_onset, e.t_offset)) > 0 for e in abstaining)
        kind = "abstained_miss" if overlapped_abstaining and not overlapped_deciding else "miss"
        out.append(_record(r, None, kind, None, reference_class))
    for r in refs:
        if not r.assessable:
            out.append(_record(r, None, "unobservable_reference", None, reference_class))
    return out


def _record(r: Reference | None, e: SystemEvent | None, kind: str, iou: float | None, reference_class: str) -> dict:
    return {"ref_event_id": r.ref_event_id if r else None, "system_event_id": e.system_event_id if e else None, "match_type": kind,
            "temporal_iou": iou, "onset_error_s": (e.t_onset - r.t_onset) if (r and e) else None,
            "offset_error_s": (e.t_offset - r.t_offset) if (r and e) else None, "reference_class": reference_class}


def match_run_inputs_digest(references: list[Reference], events: list[SystemEvent], group: str, iou_m: float, reference_class: str,
                            ref_groups: dict[str, frozenset]) -> str:
    """SHA-256 over the JCS form of every input of one `match_window` call, the label-group mapping included
    (Architect ruling on AR-39 item 3). Input order does not change it. S8 records it with the match run (AR-42 item 3)."""
    import hashlib
    payload = {
        "references": sorted(([r.ref_event_id, r.t_onset, r.t_offset, list(r.pair), r.assessable] for r in references), key=canonical_json),
        "events": sorted(([e.nk, e.system_event_id, e.t_onset, e.t_offset, list(e.pair) if e.pair else None, sorted(e.labels)] for e in events),
                         key=canonical_json),
        "label_groups": {k: sorted(v) for k, v in sorted(ref_groups.items())},
        "label_group": group, "iou_m": iou_m, "reference_class": reference_class,
    }
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def unobservable_overlap(references: list[Reference], events: list[SystemEvent], records: list[dict], group: str,
                         ref_groups: dict[str, frozenset]) -> list[dict]:
    """T12.2: system events of this window and label group that overlap a reference that is not assessable (temporal
    IoU > 0, no pair condition) and are matched to no reference. Decision: non_abstained (a decision in the group, so a
    false or duplicate alert under N4) or abstained (T10.7(a), G2 only). Match classes are unchanged."""
    unobservable = [r for r in references if not r.assessable and (group == "any" or group in ref_groups[r.ref_event_id])]
    matched = {r["system_event_id"] for r in records if r["match_type"] == "matched"}
    out = []
    for e in sorted(events, key=lambda e: canonical_json(e.nk)):
        if e.system_event_id in matched or not any(temporal_iou((r.t_onset, r.t_offset), (e.t_onset, e.t_offset)) > 0 for r in unobservable):
            continue
        if in_group(e, group):
            out.append({"system_event_id": e.system_event_id, "decision": "non_abstained", "labels": sorted(e.labels)})
        elif abstained(e, group):
            out.append({"system_event_id": e.system_event_id, "decision": "abstained", "labels": sorted(e.labels)})
    return out
