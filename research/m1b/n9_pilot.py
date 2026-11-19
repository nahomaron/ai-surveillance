"""D-47 item 3: N9 rule tests on the unmatched BL-6 candidate events of columns C and C' (descriptive only).

  PYTHONPATH=src .venv/bin/python research/m1b/n9_pilot.py   -> research/m1b/pilot_n9.json

An unmatched event is a deciding system event of G1 matching whose record is `false_alert` or `duplicate_alert`
(`matching.match_window`, as in T-21). Rules, in pipeline order (`rq1.evaluation.attribution`):
  1 evidence_unavailable: coverage at the event's closest-approach frame (its first member episode's CA frame) not usable;
  2 perception: `rule_perception_false_alert` (AR-42 item 1), n_miss 5, iou_cm 0.5;
  3 tracking: the event's two tracks are not both `matched` at its CA frame (FX-ID-8; F.1 A5.2 "Event matching");
  4 geometry and 5 event_reasoning: not evaluated (CR-029); 6 linkage (M2) and 7 reference_ambiguity (no reference):
    not evaluated.
`diagnose` gives the first failing rule as primary_stage; with rules 4 and 5 not evaluated, "unresolved" here means
"not attributed by rules 1-3". No oracle factorial is run (T12.3 is not applied; the pilot has no detector-path oracle runs).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from rq1.evaluation import attribution as att  # noqa: E402

N_MISS = 5  # pre-registration v1 (iou_cm / n_miss = 0.5 / 5 frames)
IOU_CM = 0.5
NOT_EVALUATED = {"geometry": None, "event_reasoning": None, "linkage": None, "reference_ambiguity": None}


def diagnose_unmatched(tracks: tuple[str, str], ca: int, coverage_state: str, reference: dict, system: dict, assoc_rows: list[dict]) -> dict:
    """tracks: (person track, forklift track); reference/system: frame -> [(object id, class, xyxy)]; assoc_rows: A5.2 rows."""
    matched = {r["track_id"] for r in assoc_rows if r["frame_index"] == ca and r["status"] == "matched"}
    results = {"evidence_unavailable": att.rule_evidence_unavailable(True, coverage_state),
               "perception": att.rule_perception_false_alert(reference, system, tracks, ca, N_MISS, IOU_CM),
               "tracking": not set(tracks) <= matched, **NOT_EVALUATED}
    return att.diagnose(results)


def _tuples(frames_side: dict) -> dict:
    return {i: [(b.object_id, b.cls, tuple(b.xyxy)) for b in v] for i, v in frames_side.items()}


def camera(rec: str, cam_dir: str) -> list[dict]:  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    import pilot_common as pc
    from rq1.evaluation import association as assoc
    from rq1.evaluation import matching as mt
    ev = ep.ev
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    pipe = json.loads((pc.OUT / cam_dir / rec / "pipeline.json").read_text())
    if pipe.get("s4") is None:
        return []
    support = cam.support()
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    refs, groups = ev.references(cam)
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    refs_by_frame = ep.ref_boxes(s3o, trk_key, cam.classes)
    s3c = ep.load_pilot(pipe["s3"])
    rows, frames, _ = ep.association_detector(s3c, refs_by_frame)
    summ, _ = assoc.summarize(rows, sup_all(rows))
    s4, s5 = ep.load_pilot(pipe["s4"]), ep.load_pilot(pipe["s5"]["BL-6"])
    events = ev.system_events(s4, s5, rows, summ)
    records = mt.match_window(refs, events, "G1", ev.S8["iou_m"], "rule_conformance", groups)
    evts = {e.system_event_id: e for e in events}
    episodes = {(e["pow_id"], e["start_frame"]): e for e in s5.get("episode", [])}
    pows = {p["pow_id"]: p for p in s4["pow"]}
    by_evt = {}
    for e in s5.get("candidate_event", []):
        ep_ = episodes[tuple(e["member_episode_nks"][0])]
        pw = pows[ep_["pow_id"]]
        by_evt[e["evt_id"]] = ((pw["person_track_id"], pw["forklift_track_id"]), ep_["closest_approach_frame"])
    s1dir = pc.ROOT / f"out/t17_sdg/{pipe['s1']}"
    cov = ep.files.read_table(str(s1dir / "coverage_segment.parquet"), "coverage_segment", ev.m.A.SCHEMA_VERSION)
    system = _tuples({i: v[0] for i, v in frames.items()})
    reference = _tuples({i: v[1] for i, v in frames.items()})
    out = []
    for r in records:
        if r["match_type"] not in ("false_alert", "duplicate_alert"):
            continue
        tracks, ca = by_evt[r["system_event_id"]]
        state = next((c["coverage_state"] for c in cov if c["start_frame"] is not None and c["start_frame"] <= ca < c["end_frame_excl"]), "not_recorded")
        d = diagnose_unmatched(tracks, ca, state, reference, system, rows)
        e = evts[r["system_event_id"]]
        same = [x for x in refs if e.pair is not None and tuple(x.pair) == tuple(e.pair)]
        tiou = max((mt.temporal_iou((x.t_onset, x.t_offset), (e.t_onset, e.t_offset)) for x in same), default=None)
        out.append({"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "system_event_id": r["system_event_id"], "match_type": r["match_type"],
                    "ca_frame": ca, "pair_resolved": e.pair is not None, "references_of_pair": len(same), "max_temporal_iou_same_pair": tiou, **d})
    return out


def run() -> dict:  # pragma: no cover
    import pilot_common as pc
    res = {"status": "D-47 item 3: N9 rule tests (1-3) on unmatched BL-6 events; descriptive; synthetic SDG validation; nothing validated",
           "rules": {"n_miss": N_MISS, "iou_cm": IOU_CM, "not_evaluated": sorted(NOT_EVALUATED), "cr": "CR-029 (rules 4 and 5 on the detector path)"},
           "columns": {}}
    for col, cam_dir in (("C", "cam"), ("C'", "cam_cprime")):
        recs = sorted(p.name for p in (pc.OUT / cam_dir).iterdir() if (p / "pipeline.json").exists())
        rows = [x for rec in recs for x in camera(rec, cam_dir)]
        res["columns"][col] = {
            "cameras": len(recs), "unmatched_events": len(rows),
            "by_match_type": dict(sorted(Counter(x["match_type"] for x in rows).items())),
            "primary_stage": {v: dict(sorted(Counter(x["primary_stage"] for x in rows if v == "all" or x["viewpoint"] == v).items()))
                              for v in ("all", "ceiling", "eye_level")},
            "rule_fail_counts": {s: sum(1 for x in rows if x["rule_test_results"].get(s) == "fail") for s in ("evidence_unavailable", "perception", "tracking")},
            "secondary_tracking_under_perception": sum(1 for x in rows if x["primary_stage"] == "perception" and "tracking" in x["secondary_factors"]),
            # descriptive, not N9: overlap in time with a reference interaction of the same identity pair (any G1 reference)
            "same_pair_reference": {"pair_unresolved": sum(1 for x in rows if not x["pair_resolved"]),
                                    "no_reference_of_pair": sum(1 for x in rows if x["pair_resolved"] and x["references_of_pair"] == 0),
                                    "reference_of_pair_no_overlap": sum(1 for x in rows if x["references_of_pair"] and not x["max_temporal_iou_same_pair"]),
                                    "overlap_below_iou_m": sum(1 for x in rows if x["max_temporal_iou_same_pair"] and x["max_temporal_iou_same_pair"] < 0.3),
                                    "overlap_at_or_above_iou_m": sum(1 for x in rows if x["max_temporal_iou_same_pair"] and x["max_temporal_iou_same_pair"] >= 0.3)},
            "events": rows}
    return res


if __name__ == "__main__":  # pragma: no cover
    out = run()
    p = os.path.join(os.path.dirname(__file__), "pilot_n9.json")
    with open(p, "w") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({c: {k: v for k, v in d.items() if k != "events"} for c, d in out["columns"].items()}, indent=1))
