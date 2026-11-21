"""D-50 item 2: episode extent and fragmentation on the detector path, C and C' (descriptive, from stored outputs only).

  PYTHONPATH=src .venv/bin/python research/m1b/extent_check.py            -> research/m1b/pilot_extent.json
  PYTHONPATH=src .venv/bin/python research/m1b/extent_check.py --tables   (markdown for the report)

BL-6, label group G1, as in the pilot's N4 matching (`matching.match_window`); N4 and the reported metrics are unchanged.
- references = the assessable G1 references; events = the deciding G1 system events; pairs as resolved for N4
  (`assoc.event_pair` at the closest-approach frame).
- per unmatched event (false or duplicate alert): the best temporal IoU with a reference of the same identity pair, by band;
- per reference that is N4-matched or overlapped (IoU > 0) by a same-pair system episode: how many same-pair BL-6 episodes
  overlap it, and how many of those carry `continuation_of_nk` (continue an earlier episode);
- "any temporal overlap, same pair" recall and precision: descriptive, not the N4 metric (no one-to-one rule, no iou_m).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from rq1.evaluation.matching import temporal_iou  # noqa: E402

BANDS = ("0", "(0, 0.1]", "(0.1, 0.2]", "(0.2, 0.3)", ">= 0.3")


def band(v: float) -> str:
    return BANDS[0] if v <= 0 else BANDS[1] if v <= 0.1 else BANDS[2] if v <= 0.2 else BANDS[3] if v < 0.3 else BANDS[4]


def best_same_pair_iou(event, refs) -> float:
    """event: (id, pair, t0, t1); refs: [(id, pair, t0, t1)]."""
    _, pair, a, b = event
    if pair is None:
        return 0.0
    return max((temporal_iou((r[2], r[3]), (a, b)) for r in refs if r[1] == pair), default=0.0)


def any_overlap(refs, events) -> dict:
    found = sum(1 for r in refs if any(e[1] is not None and e[1] == r[1] and temporal_iou((r[2], r[3]), (e[2], e[3])) > 0 for e in events))
    supported = sum(1 for e in events if e[1] is not None and any(e[1] == r[1] and temporal_iou((r[2], r[3]), (e[2], e[3])) > 0 for r in refs))
    return {"a": len(refs), "found": found, "s": len(events), "supported": supported}


def episodes_overlapping(ref, episodes) -> tuple[int, int]:
    """episodes: [(pair, t0, t1, linked)]. Returns (same-pair episodes overlapping the reference, of which linked)."""
    hits = [e for e in episodes if e[0] is not None and e[0] == ref[1] and temporal_iou((ref[2], ref[3]), (e[1], e[2])) > 0]
    return len(hits), sum(1 for e in hits if e[3])


def camera(rec: str, cam_dir: str) -> dict:  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    import pilot_common as pc
    from rq1.evaluation import association as assoc
    from rq1.evaluation import matching as mt
    ev = ep.ev
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    pipe = json.loads((pc.OUT / cam_dir / rec / "pipeline.json").read_text())
    support = cam.support()
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    refs, groups = ev.references(cam)
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    rows, _, _ = ep.association_detector(ep.load_pilot(pipe["s3"]), ep.ref_boxes(s3o, trk_key, cam.classes))
    summ, _ = assoc.summarize(rows, sup_all(rows))
    s4, s5 = ep.load_pilot(pipe["s4"]), ep.load_pilot(pipe["s5"]["BL-6"])
    events = ev.system_events(s4, s5, rows, summ)
    records = mt.match_window(refs, events, "G1", ev.S8["iou_m"], "rule_conformance", groups)
    R = [(r.ref_event_id, tuple(r.pair), r.t_onset, r.t_offset) for r in refs if r.assessable and "G1" in groups[r.ref_event_id]]
    E = [(e.system_event_id, tuple(e.pair) if e.pair else None, e.t_onset, e.t_offset) for e in events if mt.in_group(e, "G1")]
    Ebyid = {e[0]: e for e in E}
    pows = {p["pow_id"]: p for p in s4["pow"]}
    eps = []
    for x in s5.get("episode", []):
        pw = pows[x["pow_id"]]
        pair, _ = assoc.event_pair(rows, summ, pw["person_track_id"], pw["forklift_track_id"], x["closest_approach_frame"])
        eps.append((tuple(pair) if pair else None, x["t_start_tl_s"], x["t_end_tl_s"], x["continuation_of_nk"] is not None))
    matched_refs = {r["ref_event_id"] for r in records if r["match_type"] == "matched"}
    unmatched = [Ebyid[r["system_event_id"]] for r in records if r["match_type"] in ("false_alert", "duplicate_alert")]
    per_ref = []
    for r in R:
        n, linked = episodes_overlapping(r, eps)
        if r[0] in matched_refs or n > 0:
            per_ref.append({"matched": r[0] in matched_refs, "episodes": n, "linked": linked})
    return {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "unmatched_bands": [band(best_same_pair_iou(e, R)) for e in unmatched],
            "per_ref": per_ref, "any_overlap": any_overlap(R, E)}


def run() -> dict:  # pragma: no cover
    import pilot_common as pc
    res = {"status": "D-50 item 2: descriptive, not the N4 metric; BL-6, G1; synthetic SDG validation; nothing validated", "columns": {}}
    for col, cam_dir in (("C", "cam"), ("C'", "cam_cprime")):
        recs = sorted(p.name for p in (pc.OUT / cam_dir).iterdir() if (p / "pipeline.json").exists())
        cams = [camera(r, cam_dir) for r in recs]
        refs = [x for c in cams for x in c["per_ref"]]
        ao = {k: sum(c["any_overlap"][k] for c in cams) for k in ("a", "found", "s", "supported")}
        res["columns"][col] = {
            "cameras": len(cams),
            "unmatched_by_band": {b: sum(c["unmatched_bands"].count(b) for c in cams) for b in BANDS},
            "references_matched_or_overlapped": {
                "n": len(refs), "matched": sum(1 for x in refs if x["matched"]),
                "by_episode_count": {str(k): v for k, v in sorted(Counter(min(x["episodes"], 4) for x in refs).items())},
                "episodes_total": sum(x["episodes"] for x in refs), "episodes_linked": sum(x["linked"] for x in refs),
                "refs_with_2plus_episodes": sum(1 for x in refs if x["episodes"] >= 2),
                "matched_refs_with_2plus_episodes": sum(1 for x in refs if x["matched"] and x["episodes"] >= 2)},
            "any_overlap_same_pair": {**ao, "recall": ao["found"] / ao["a"] if ao["a"] else None,
                                      "precision": ao["supported"] / ao["s"] if ao["s"] else None,
                                      "label": "descriptive, not the N4 metric"}}
    return res


def tables(res: dict) -> str:
    """Markdown for the report (`extent_check.py --tables`)."""
    cols = ("C", "C'")
    L = ["#### Unmatched BL-6 events: temporal IoU with the best same-pair reference\n",
         "| column | unmatched events | " + " | ".join(BANDS) + " |", "|---|---|" + "---|" * len(BANDS)]
    for c in cols:
        d = res["columns"][c]["unmatched_by_band"]
        L.append(f"| {c} | {sum(d.values())} | " + " | ".join(str(d[b]) for b in BANDS) + " |")
    L += ["\n#### References matched (N4) or overlapped by a same-pair episode: overlapping same-pair BL-6 episodes\n",
          "| column | references | of which N4-matched | 1 episode | 2 | 3 | 4 or more | with 2 or more | N4-matched with 2 or more | episodes overlapping | of which linked by continuation_of_nk |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cols:
        d = res["columns"][c]["references_matched_or_overlapped"]
        k = d["by_episode_count"]
        L.append(f"| {c} | {d['n']} | {d['matched']} | {k.get('1', 0)} | {k.get('2', 0)} | {k.get('3', 0)} | {k.get('4', 0)} | {d['refs_with_2plus_episodes']} | "
                 f"{d['matched_refs_with_2plus_episodes']} | {d['episodes_total']} | {d['episodes_linked']} |")
    L += ["\n#### EV-M1 / EV-M2 with \"any temporal overlap, same pair\" (descriptive, not the N4 metric)\n",
          "| column | references found / assessable | recall (descriptive) | events supported / events | precision (descriptive) | N4 EV-M1 / EV-M2 (reported) |",
          "|---|---|---|---|---|---|"]
    n4 = {"C": json.load(open(os.path.join(os.path.dirname(__file__), "pilot_results.json")))["ev"]["C"]["BL-6"],
          "C'": json.load(open(os.path.join(os.path.dirname(__file__), "pilot_results_cprime.json")))["ev"]["C'"]["BL-6"]}
    for c in cols:
        d = res["columns"][c]["any_overlap_same_pair"]
        L.append(f"| {c} | {d['found']} / {d['a']} | {d['recall']:.2f} | {d['supported']} / {d['s']} | {d['precision']:.2f} | {n4[c]['EV-M1']:.2f} / {n4[c]['EV-M2']:.2f} |")
    return "\n".join(L)


if __name__ == "__main__":  # pragma: no cover
    if sys.argv[1:2] == ["--tables"]:
        print(tables(json.load(open(os.path.join(os.path.dirname(__file__), "pilot_extent.json")))))
        sys.exit(0)
    out = run()
    p = os.path.join(os.path.dirname(__file__), "pilot_extent.json")
    with open(p, "w") as f:
        f.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out["columns"], indent=1))
