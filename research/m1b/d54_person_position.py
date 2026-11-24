"""D-54 STEP 4: person-position diagnostic on the 116 tuning cameras. Diagnostic, tuning subset, not a reported result.
Classifies; recommends no rule. Stored outputs only (column B, column A, and the D-53 step 2 runs B-tune and B-sim-P).

  PYTHONPATH=src .venv/bin/python research/m1b/d54_person_position.py   -> research/m1b/d54_person_position.json

(a) Person position error in column B (stored T-21 `full_camera` S4: oracle boxes, full_camera), with the D1 definitions
    (`d1_anchor_angle.py`, `cr007_evidence.py`): camera centre C = -R^T t; error = estimate minus the simulator position of
    the oracle track's identity; line of sight = unit vector from C's floor point to the true position; along = error .
    line of sight (signed; negative = toward the camera), across = |perpendicular component| (unsigned, as D1). Split by floor distance r from C to the estimate (0-2, 2-5, 5-10, 10-20, >= 20 m), viewpoint,
    evidence state (object_state.evidence_state) and whether the oracle box is clipped at the image bottom (its bottom
    edge y2 >= image height - 1 px, the last pixel row; oracle boxes have integer edges inside the image).
(b) Median along-sight error against the simulator person box's half-depth: half the extent of the SDG 3D box's floor
    face (its 4 lowest corners) projected on the line of sight, per frame; also half the box's floor length and width.
(c) Each B-tune unmatched BL-6 G1 event (false or duplicate alert, N4) with no counterpart in B-sim-P. "Counterpart" is
    not defined by D-54 and the count depends on it (CR-035), so both readings are reported, neither chosen:
    reading 1, a B-sim-P G1 system event of the same identity pair whose time interval overlaps (temporal IoU > 0);
    reading 2, the same, but only B-sim-P events that are themselves unmatched. At the event's
    closest-approach frame (its first member episode's `closest_approach_frame`): person error along / across; the
    clearance of B (B-tune), of B-sim-P (simulator person position, camera forklift) and of A (simulator positions for
    both); the constant-velocity predicted minimum clearance of each; which providers fired (BL-6: R2 = `P_ep`; R3, R4,
    R5 = `C_ep_by_provider`; R1 is not in BL-6); and whether the episode starts or ends where the B clearance or the B
    predicted minimum clearance crosses d_p or d_pc (the pair-frame before the start frame and the last frame of the
    episode against the next one). Cause class (at the closest-approach frame, B against B-sim-P): which BL-6 threshold the
    B value is below while the B-sim-P value is not (d_p for the clearance, R2; d_pc for the predicted minimum, R3).
(d) The same for every reference B-sim-P matches and B-tune does not, at the closest-approach frame of the B-sim-P event.
Thresholds: d_p 2.0 m, d_pc 1.0 m (pre-registration v1 base values, `m1a_common.S5_BASE`).
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from cr007_evidence import _q, camera_centre, decompose, unit  # noqa: E402

STATUS = "diagnostic, tuning subset, not a reported result"
R_BINS = ((0, 2), (2, 5), (5, 10), (10, 20), (20, None))
BL = "BL-6"


def r_bin(r: float) -> str:
    for lo, hi in R_BINS:
        if r >= lo and (hi is None or r < hi):
            return f"{lo}-{hi}" if hi is not None else f">={lo}"
    raise ValueError(r)


def half_depth(floor_xy: list, los: tuple) -> float:
    """Half the extent of the floor-face corners projected on the unit line of sight."""
    proj = [x * los[0] + y * los[1] for x, y in floor_xy]
    return (max(proj) - min(proj)) / 2


def bottom_clipped(bbox: list, height: int) -> bool:
    return bbox[3] >= height - 1


def crossing(before: float | None, after: float | None, threshold: float) -> bool:
    """True when the value moves from one side of the threshold to the other (either direction)."""
    if before is None or after is None:
        return False
    return (before < threshold) != (after < threshold)


def cause_class(x: dict, y: dict, d_p: float, d_pc: float, nx: str = "B", ny: str = "B-sim-P") -> str:
    """x, y: {"clearance", "pred_min"} of runs nx and ny at the frame. Which threshold nx is below and ny is not."""
    below = lambda v, t: v is not None and v < t
    dp = below(x["clearance"], d_p) and not below(y["clearance"], d_p)
    dpc = below(x["pred_min"], d_pc) and not below(y["pred_min"], d_pc)
    if dp and dpc:
        return f"{nx} below d_p and d_pc, {ny} not"
    if dp:
        return f"{nx} clearance below d_p only, {ny} not"
    if dpc:
        return f"{nx} predicted minimum below d_pc only, {ny} not"
    if x["clearance"] is None or y["clearance"] is None:
        return f"clearance not measured in {nx} or {ny}"
    return f"same side of d_p and d_pc in {nx} and {ny}"


def stats(rows: list[dict]) -> dict:
    al, ac = [r["along"] for r in rows], [r["across"] for r in rows]
    return {"n": len(rows), "along_signed_median_m": _q(al, 50), "along_signed_p05_m": _q(al, 5), "along_signed_p95_m": _q(al, 95),
            "along_abs_median_m": _q([abs(x) for x in al], 50), "across_signed_median_m": _q(ac, 50),
            "across_abs_median_m": _q([abs(x) for x in ac], 50), "error_median_m": _q([math.hypot(a, c) for a, c in zip(al, ac)], 50),
            "error_p95_m": _q([math.hypot(a, c) for a, c in zip(al, ac)], 95)}


# ------------------------------------------------------------------------------------------------------------------ driver

def _pred(row):
    if row is None:
        return None
    return next((p["pred_min_clearance_m"] for p in row["predicted"] if p["motion_model_id"] == "constant_velocity"), None)


def _series(s4: dict) -> dict:
    """(person track, forklift track, frame) -> pair_series row."""
    pows = {p["pow_id"]: p for p in s4["pow"]}
    return {(pows[r["pow_id"]]["person_track_id"], pows[r["pow_id"]]["forklift_track_id"], r["frame_index"]): r for r in s4["pair_series"]}


def camera(rec: str) -> dict:  # pragma: no cover - driver over stored artifacts
    import d2_position_contribution as d2
    import evaluate_pilot as ep_
    import pilot_common as pc
    import run_pilot as rp
    from rq1.evaluation import association as assoc
    from rq1.evaluation import matching as mt
    from rq1.schema import files
    m = pc.m
    ev = ep_.ev
    S5 = m.S5_BASE
    ctx = m.Context("sdg")
    cam = ev.Camera("sdg", ep_.M1A_LABEL, rec)
    view = pc.viewpoint(cam.camera_name)
    _, _, cal = rp.load_s1(ctx, rec)
    C = camera_centre(cal["R_cam_from_world"], cal["t_cam_from_world_m"])
    height = files.read_table(str(pc.ROOT / f"out/t17_sdg/{ctx.camera(rec)['s1']}/decode_summary.parquet"), "decode_summary", m.A.SCHEMA_VERSION)[0]["height_px"]
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3o = ev.load_art(ep_.M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3o["track"]}
    box = {(by_local[p["track_nk"][1]], p["frame_index"]): p["bbox_xyxy_px"] for p in s3o["track_point"]}
    s4b = ev.load_art(ep_.M1A_LABEL, "sdg", fc["s4"])
    s4a = ev.load_art(ep_.M1A_LABEL, "sdg", base["s4"])
    # 3D person boxes: floor corners per (identity, frame_index)
    data = m.load(ctx, rec)
    floor = {}
    for k, objs in enumerate(data.frames):
        i = data.seq.get(k)
        if i is None:
            continue
        for key, o in objs.items():
            if data.classes[key] == "person":
                import numpy as np
                c = np.asarray(o.corners() if callable(o.corners) else o.corners, float)
                floor[(str(key), i)] = [tuple(x) for x in c[np.argsort(c[:, 2])[:4], :2]]
    # (a), (b)
    rows = []
    for r in s4b["object_state"]:
        if r["x_m"] is None or r["track_id"] not in trk_key:
            continue
        key = trk_key[r["track_id"]]
        if cam.classes[key] != "person":
            continue
        t = cam.truth.get((key, r["frame_index"]))
        if t is None:
            continue
        los = unit((t[3], t[4]), C)
        along, across = decompose((r["x_m"], r["y_m"]), (t[3], t[4]), los)
        fl = floor.get((key, r["frame_index"]))
        dims = None
        if fl:
            d = sorted(math.hypot(fl[a][0] - fl[b][0], fl[a][1] - fl[b][1]) for a in range(4) for b in range(a + 1, 4))
            dims = (d[2] / 2, d[0] / 2)  # half length, half width
        rows.append({"along": along, "across": across, "r": math.hypot(r["x_m"] - C[0], r["y_m"] - C[1]), "view": view,
                     "evidence_state": r["evidence_state"], "clipped": bottom_clipped(box[(r["track_id"], r["frame_index"])], height),
                     "half_depth": half_depth(fl, los) if fl else None, "half_length": dims[0] if dims else None, "half_width": dims[1] if dims else None})
    # (c), (d): B-tune vs B-sim-P (D-53 step 2 outputs)
    d2rec = json.loads((d2.OUT / "cam" / f"{rec}.json").read_text())
    load = lambda a: d2._load(a, d2.OUT / "artifacts")
    s4t, s5t = load(d2rec["runs"]["B-tune"]["s4"]), load(d2rec["runs"]["B-tune"]["s5"][BL])
    s4p, s5p = load(d2rec["runs"]["B-sim-P"]["s4"]), load(d2rec["runs"]["B-sim-P"]["s5"][BL])
    support = cam.support()
    rows_o, _, _ = ev.association(s3o, trk_key)
    summ, _ = assoc.summarize(rows_o, {f: support.get(f, 0.0) for f in {x["frame_index"] for x in rows_o}})
    refs, groups = ev.references(cam)
    ev_t = [e for e in ev.system_events(s4t, s5t, rows_o, summ) if mt.in_group(e, "G1")]
    ev_p = [e for e in ev.system_events(s4p, s5p, rows_o, summ) if mt.in_group(e, "G1")]
    rec_t = mt.match_window(refs, ev.system_events(s4t, s5t, rows_o, summ), "G1", ev.S8["iou_m"], "rule_conformance", groups)
    rec_p = mt.match_window(refs, ev.system_events(s4p, s5p, rows_o, summ), "G1", ev.S8["iou_m"], "rule_conformance", groups)
    ser = {"B": _series(s4t), "P": _series(s4p), "A": _series(s4a)}
    eps = {"B": {(e["pow_id"], e["start_frame"]): e for e in s5t.get("episode", [])}, "P": {(e["pow_id"], e["start_frame"]): e for e in s5p.get("episode", [])}}
    pows = {"B": {p["pow_id"]: p for p in s4t["pow"]}, "P": {p["pow_id"]: p for p in s4p["pow"]}}
    person_state = {(r["track_id"], r["frame_index"]): r for r in s4b["object_state"]}

    def frame_facts(person_trk, fork_trk, i):
        out = {"frame": i}
        for k in ("B", "P", "A"):
            row = ser[k].get((person_trk, fork_trk, i))
            out[f"clearance_{k}"] = row["clearance_m"] if row else None
            out[f"pred_min_{k}"] = _pred(row)
        ps = person_state.get((person_trk, i))
        key = trk_key.get(person_trk)
        t = cam.truth.get((key, i)) if key else None
        if ps and ps["x_m"] is not None and t:
            los = unit((t[3], t[4]), C)
            out["person_along_m"], out["person_across_m"] = decompose((ps["x_m"], ps["y_m"]), (t[3], t[4]), los)
        else:
            out["person_along_m"] = out["person_across_m"] = None
        return out

    def episode_facts(k, ev_):
        e = eps[k][tuple(ev_.nk)]
        pw = pows[k][e["pow_id"]]
        pt, ft = pw["person_track_id"], pw["forklift_track_id"]
        fired = (["R2"] if e["P_ep"] else []) + sorted(p for p, v in e["C_ep_by_provider"].items() if v)
        s = ser[k]
        g = lambda i: s.get((pt, ft, i))
        first, last = e["start_frame"], e["end_frame_excl"] - 1
        prev_, next_ = g(first - 1), g(last + 1)
        cr = {}
        for side, (a, b) in (("start", (prev_, g(first))), ("end", (g(last), next_))):
            cr[side] = {"clearance_crosses_d_p": crossing(a and a["clearance_m"], b and b["clearance_m"], S5["d_p"]),
                        "clearance_crosses_d_pc": crossing(a and a["clearance_m"], b and b["clearance_m"], S5["d_pc"]),
                        "pred_min_crosses_d_pc": crossing(_pred(a), _pred(b), S5["d_pc"]), "neighbour_frame_in_pow": (a is not None and b is not None)}
        return e, pt, ft, fired, cr

    unmatched = [r for r in rec_t if r["match_type"] in ("false_alert", "duplicate_alert")]
    t_by_id = {e.system_event_id: e for e in ev_t}
    unmatched_p = {r["system_event_id"] for r in rec_p if r["match_type"] in ("false_alert", "duplicate_alert")}
    out_c = []
    for r in unmatched:
        e = t_by_id[r["system_event_id"]]
        over = [x for x in ev_p if x.pair is not None and e.pair is not None and tuple(x.pair) == tuple(e.pair)
                and mt.temporal_iou((x.t_onset, x.t_offset), (e.t_onset, e.t_offset)) > 0]
        no_any, no_unmatched = not over, not any(x.system_event_id in unmatched_p for x in over)
        if not no_unmatched:
            continue  # a counterpart under both readings
        epi, pt, ft, fired, cr = episode_facts("B", e)
        f = frame_facts(pt, ft, epi["closest_approach_frame"])
        out_c.append({"rec_id": rec, "viewpoint": view, "match_type": r["match_type"], "reading_1_no_counterpart": no_any,
                      "reading_2_no_counterpart": no_unmatched, "b_sim_p_overlapping_events": len(over),
                      "providers_fired_B": fired, "crossings_B": cr, **f,
                      "cause": cause_class({"clearance": f["clearance_B"], "pred_min": f["pred_min_B"]}, {"clearance": f["clearance_P"], "pred_min": f["pred_min_P"]},
                                           S5["d_p"], S5["d_pc"])})
    matched_t = {r["ref_event_id"] for r in rec_t if r["match_type"] == "matched"}
    p_by_id = {e.system_event_id: e for e in ev_p}
    out_d = []
    for r in rec_p:
        if r["match_type"] != "matched" or r["ref_event_id"] in matched_t:
            continue
        e = p_by_id[r["system_event_id"]]
        epi, pt, ft, fired, cr = episode_facts("P", e)
        f = frame_facts(pt, ft, epi["closest_approach_frame"])
        b_same = [x for x in ev_t if x.pair is not None and e.pair is not None and tuple(x.pair) == tuple(e.pair)
                  and mt.temporal_iou((x.t_onset, x.t_offset), (e.t_onset, e.t_offset)) > 0]
        out_d.append({"rec_id": rec, "viewpoint": view, "providers_fired_B_sim_P": fired, "crossings_B_sim_P": cr,
                      "b_tune_same_pair_overlapping_events": len(b_same), **f,
                      "cause": cause_class({"clearance": f["clearance_P"], "pred_min": f["pred_min_P"]}, {"clearance": f["clearance_B"], "pred_min": f["pred_min_B"]},
                                           S5["d_p"], S5["d_pc"], "B-sim-P", "B")})
    return {"rec_id": rec, "rows": rows, "c": out_c, "d": out_d,
            "counts": {"b_tune_unmatched": len(unmatched), "b_sim_p_unmatched": sum(1 for r in rec_p if r["match_type"] in ("false_alert", "duplicate_alert"))}}


def split(rows, key, order=None) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    keys = order or sorted(groups, key=str)
    return {str(k): stats(groups[k]) for k in keys if k in groups}


def summarize_events(items: list[dict]) -> dict:
    out = {"n": len(items), "by_cause": dict(Counter(x["cause"] for x in items).most_common()),
           "by_viewpoint": dict(Counter(x["viewpoint"] for x in items).most_common())}
    pk = "providers_fired_B" if items and "providers_fired_B" in items[0] else "providers_fired_B_sim_P"
    ck = "crossings_B" if pk == "providers_fired_B" else "crossings_B_sim_P"
    out["providers_fired"] = dict(Counter("+".join(x[pk]) or "none" for x in items).most_common())
    for side in ("start", "end"):
        out[f"{side}_crossings"] = {k: sum(1 for x in items if x[ck][side][k]) for k in ("clearance_crosses_d_p", "clearance_crosses_d_pc", "pred_min_crosses_d_pc")}
        out[f"{side}_no_neighbour_pair_frame"] = sum(1 for x in items if not x[ck][side]["neighbour_frame_in_pow"])
    al = [x["person_along_m"] for x in items if x["person_along_m"] is not None]
    out["person_along_at_ca"] = {"n": len(al), "median_m": _q(al, 50), "p05_m": _q(al, 5), "p95_m": _q(al, 95)}
    ac = [x["person_across_m"] for x in items if x["person_across_m"] is not None]
    out["person_across_at_ca"] = {"n": len(ac), "median_m": _q(ac, 50)}
    for k in ("B", "P", "A"):
        v = [x[f"clearance_{k}"] for x in items if x[f"clearance_{k}"] is not None]
        out[f"clearance_{k}_at_ca"] = {"n": len(v), "median_m": _q(v, 50)}
    diff = [x["clearance_B"] - x["clearance_P"] for x in items if x["clearance_B"] is not None and x["clearance_P"] is not None]
    out["clearance_B_minus_B_sim_P_at_ca"] = {"n": len(diff), "median_m": _q(diff, 50), "p05_m": _q(diff, 5), "p95_m": _q(diff, 95)}
    return out


def run() -> dict:  # pragma: no cover
    import v2_sets
    cams = [camera(r) for r in v2_sets.tuning()]
    rows = [x for c in cams for x in c["rows"]]
    hd = [r["half_depth"] for r in rows if r["half_depth"] is not None]
    items_c = [x for c in cams for x in c["c"]]
    items_d = [x for c in cams for x in c["d"]]
    rkeys = [f"{lo}-{hi}" if hi is not None else f">={lo}" for lo, hi in R_BINS]
    return {"status": STATUS, "decision": "D-54 STEP 4", "contract": "E-1.2.24 / E-1.2.25 (stored outputs; no rule)", "cameras": len(cams),
            "recommendation": "none (D-54 STEP 4: classify, do not interpret; recommend no rule)",
            "definitions": __doc__.split("Classifies; recommends no rule.")[1].strip(),
            "a_person_error_column_b": {"all": stats(rows), "by_r": split(rows, lambda r: r_bin(r["r"]), rkeys),
                                        "by_viewpoint": split(rows, lambda r: r["view"]), "by_evidence_state": split(rows, lambda r: r["evidence_state"]),
                                        "by_bottom_clipped": split(rows, lambda r: r["clipped"], [False, True])},
            "b_half_depth": {"n": len(hd), "person_box_half_depth_median_m": _q(hd, 50), "p05_m": _q(hd, 5), "p95_m": _q(hd, 95),
                             "half_length_median_m": _q([r["half_length"] for r in rows if r["half_length"] is not None], 50),
                             "half_width_median_m": _q([r["half_width"] for r in rows if r["half_width"] is not None], 50),
                             "along_signed_median_m": stats(rows)["along_signed_median_m"], "along_abs_median_m": stats(rows)["along_abs_median_m"],
                             "frames_without_3d_box": sum(1 for r in rows if r["half_depth"] is None)},
            "c_b_tune_unmatched_without_b_sim_p_counterpart": {
                "b_tune_unmatched_total": sum(c["counts"]["b_tune_unmatched"] for c in cams),
                "b_sim_p_unmatched_total": sum(c["counts"]["b_sim_p_unmatched"] for c in cams),
                "readings": "CR-035: counterpart not defined by D-54; both readings reported, neither chosen",
                "reading_1": {"counterpart": "a B-sim-P G1 event of the same pair with temporal IoU > 0",
                              **summarize_events([x for x in items_c if x["reading_1_no_counterpart"]])},
                "reading_2": {"counterpart": "an unmatched B-sim-P G1 event of the same pair with temporal IoU > 0",
                              **summarize_events(items_c)},
                "events": items_c},
            "d_references_recovered_by_b_sim_p": {**summarize_events(items_d), "references": items_d}}


if __name__ == "__main__":  # pragma: no cover
    import pilot_common as pc
    p = pc.ROOT / "research/m1b/d54_person_position.json"
    pc.write_json(p, run())
    print("wrote", p)
