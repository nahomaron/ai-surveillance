"""D-58 STEP 4: event-level check of T25 on the 116 tuning cameras (diagnostic). Diagnostic, tuning subset, not a reported
result. All configurations use BL-6, N4 and label group G1.

  PYTHONPATH=src .venv/bin/python research/m1b/d58_events.py estimate                (2 cameras; STOP above 3 h)
  PYTHONPATH=src .venv/bin/python research/m1b/d58_events.py run [workers] [rec ...]  -> out/m1b/d58/events/<rec>.json
  PYTHONPATH=src .venv/bin/python research/m1b/d58_events.py aggregate               -> research/m1b/d58_events_tune.json

Configurations (D-58 STEP 4; B-both and A without T25 are added for comparison):
  C-v2        stored D-54 S4 (detector S3, T24 on); T25.1 off, T25.2 off
  C-v2+T25    the stored detector S3 stitched with the STEP 3 winner (T25.1), S4 as C-v2, T25.2 on
  B-both      stored D-54 S4 (oracle boxes, T24 on); off / off             (comparison)
  B-both+T25  as B-both, T25.2 on (T25.1 off: oracle)
  A           stored T-21 base S4 (simulator positions); off / off         (comparison)
  A+T25       as A, T25.2 on
Event definitions:
  alpha  m_gap 5 frames for the system and the stored base references (T21; reference S5 at m_gap 5).
  beta   m_gap_s 1.0 s for the system and for a diagnostic reference set rebuilt from simulator truth with m_gap_s 1.0
         (T21.1 procedure on the stored T21 reference S4; T25.2 does not apply to references, T25.2 d). Label: "diagnostic,
         not the v2 reference". 1.0 s is a placeholder for this check only, not a v2 candidate.
  With T25.2 on and alpha, the join gap limit is m_gap frames x delta_nom (T25.2 b).
A5.2 pair of an event (CR-037 item 3), both readings reported, none chosen:
  (a) at the closest-approach member's CA frame (primary reading applied in the code);
  (b) every member resolved at its own CA frame; the pair if all agree, otherwise unknown (no match).
  With a stitched identity the track resolved is the member track with a point at that frame, else the member at the
  episode's first frame. With one member, (a) = (b) = the D-54 resolution.
Measures, overall and by viewpoint: EV-M1 and EV-M2 with counts; system events and members per event; unobserved gap
time; unmatched events with same-pair overlap by IoU band (`extent_check` bands); references covered by two or more
same-pair events; the D-57 split mechanisms remaining, on events: two consecutive same-pair events covering one G1
assessable reference; (i) the boundary members are in one POW, (ii) other POWs of the same pair units, (iii) other units.
Checks: C-v2 under alpha equals the D-54 EV counts and the D-57 split counts; the beta reference procedure at m_gap 5
reproduces the stored reference S5 payload and the stored reference list on every camera.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from collections import Counter
from multiprocessing import Pool
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
C_OUT = ROOT / "out/m1b/v2t24/c"
B_OUT = ROOT / "out/m1b/v2t24/b"
M1A = ROOT / "out/m1a/run1/sdg"
M1A_ART = M1A / "artifacts"
OUT = __import__("pathlib").Path(os.environ.get("D58_OUT", str(ROOT / "out/m1b/d58")))  # D58_OUT: runtime estimate only
STATUS = "diagnostic, tuning subset, not a reported result"
CONTRACT = "E-1.2.26"
BL = "BL-6"
CONFIGS = ("C-v2", "C-v2+T25", "B-both", "B-both+T25", "A", "A+T25")
DEFS = ("alpha", "beta")
READINGS = ("a", "b")
BETA_M_GAP_S = 1.0  # placeholder for this check only (D-58), not a v2 candidate
BETA_REF_LABEL = "D-58 diagnostic reference set, m_gap_s 1.0: diagnostic, not the v2 reference"
LIMIT_H = 3.0
MECHANISMS = ("i", "ii", "iii")
LABELS = ("O", "H", "PC", "NM", "UD", "CT", "IE")


def stitch_params():
    from rq1.tracking import stitching
    sel = json.loads((ROOT / "research/m1b/d58_stitch_grid.json").read_text())["selection"]
    return stitching.params_from(sel["chosen_params"]), sel["chosen"]


def s5_config(ctx, definition: str, join: bool):
    """alpha without T25.2 is the v1 BL-6 configuration (stored S5); every other one carries a diagnostic label."""
    base = m.s5_config(ctx, BL, m.S4_BASE, m.S5_BASE)
    if definition == "alpha" and not join:
        return base
    label = f"D-58 diagnostic {definition}{' + T25.2' if join else ''} (not frozen)"
    return dataclasses.replace(base, version_label=label, m_gap_s=BETA_M_GAP_S if definition == "beta" else None,
                               join_across_pow=True if join else None)


# ---------------------------------------------------------------------------------------------------- pure functions

def pair_resolver(s4: dict, rows, summ, member_track):
    """Episode -> A5.2 pair (CR-037 item 3). member_track(unit, frame) -> the track of the unit with a point on that frame
    (None if none); identity when the units are tracks."""
    from rq1.evaluation import association as assoc
    pows = {p["pow_id"]: p for p in s4["pow"]}

    def pair_of(ep):
        pw = pows[ep["pow_id"]]
        f = ep["closest_approach_frame"]
        tracks = []
        for unit in (pw["person_track_id"], pw["forklift_track_id"]):
            t = member_track(unit, f) if f is not None else None
            tracks.append(t if t is not None else member_track(unit, ep["start_frame"]))
        pair, _ = assoc.event_pair(rows, summ, tracks[0], tracks[1], f)
        return tuple(pair) if pair else None
    return pair_of


def event_rows(s4: dict, s5: dict, pair_of) -> list[dict]:
    """S_VIEW candidate events with their members and both pair readings."""
    from rq1.events import candidates
    eps = {(e["pow_id"], e["start_frame"]): e for e in s5.get("episode", [])}
    pows = {p["pow_id"]: p for p in s4["pow"]}
    out = []
    for ev in s5.get("candidate_event", []):
        if ev["scenario"] != "S_VIEW":
            continue
        members = [eps[tuple(nk)] for nk in ev["member_episode_nks"]]
        pairs = [pair_of(e) for e in members]
        pa = pair_of(candidates._ca_member(members))
        pb = pairs[0] if all(p is not None and p == pairs[0] for p in pairs) else None
        units = [(pows[e["pow_id"]]["person_track_id"], pows[e["pow_id"]]["forklift_track_id"]) for e in members]
        out.append({"id": ev["evt_id"], "t0": ev["t_onset_tl_s"], "t1": ev["t_end_tl_s"], "labels": frozenset(x for x in LABELS if ev[f"lbl_{x}"]),
                    "pair": {"a": pa, "b": pb}, "n_members": len(members), "unobserved_gap_s": ev.get("unobserved_gap_s", 0.0),
                    "first": {"pow_id": members[0]["pow_id"], "units": units[0]}, "last": {"pow_id": members[-1]["pow_id"], "units": units[-1]},
                    "nk": ev["member_episode_nks"][0]})
    return out


def system_events(events: list[dict], reading: str):
    from rq1.evaluation import matching as mt
    return [mt.SystemEvent(e["nk"], e["id"], e["t0"], e["t1"], e["pair"][reading], e["labels"]) for e in events]


def split_mechanism(a: dict, b: dict) -> str:
    """D-57 mechanisms on events: the last member of a and the first member of b."""
    if a["last"]["pow_id"] == b["first"]["pow_id"]:
        return "i"
    return "ii" if a["last"]["units"] == b["first"]["units"] else "iii"


def event_measures(refs, groups, events: list[dict], reading: str, usable: float) -> dict:
    import extent_check as xc
    import evaluate_pilot as ep
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation import matching as mt
    sysev = system_events(events, reading)
    records = mt.match_window(refs, sysev, "G1", ep.ev.S8["iou_m"], "rule_conformance", groups)
    counts = em.window_counts(records, usable)
    R = [(r.ref_event_id, tuple(r.pair), r.t_onset, r.t_offset) for r in refs if r.assessable and "G1" in groups[r.ref_event_id]]
    E = {e.system_event_id: (e.system_event_id, e.pair, e.t_onset, e.t_offset) for e in sysev if mt.in_group(e, "G1")}
    unmatched = [E[r["system_event_id"]] for r in records if r["match_type"] in ("false_alert", "duplicate_alert")]
    covering = lambda r: sorted((e for e in events if e["pair"][reading] == r[1] and mt.temporal_iou((r[2], r[3]), (e["t0"], e["t1"])) > 0),
                                key=lambda e: (e["t0"], e["t1"], e["id"]))
    per_ref, splits = [], []
    for r in R:
        cov = covering(r)
        per_ref.append(len(cov))
        splits += [split_mechanism(a, b) for a, b in zip(cov, cov[1:])]
    return {"counts": counts.__dict__, "unmatched_bands": [xc.band(xc.best_same_pair_iou(e, R)) for e in unmatched],
            "refs_events": per_ref, "splits": splits}


def camera_summary(events: list[dict]) -> dict:
    return {"events": len(events), "members": dict(Counter(str(min(e["n_members"], 4)) for e in events)),
            "member_episodes": sum(e["n_members"] for e in events), "joined_events": sum(1 for e in events if e["n_members"] >= 2),
            "unobserved_gap_s": sum(e["unobserved_gap_s"] for e in events),
            "pair_readings_differ": sum(1 for e in events if e["pair"]["a"] != e["pair"]["b"])}


# ---------------------------------------------------------------------------------------------------- drivers

def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def _save(art, origin) -> str:
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    return art.artifact_id


def _spec_of(man) -> "m.Spec":
    s = man["spec"]
    return m.Spec(s["stage"], s["schema_bundle"], s["code_commit"], s["environment_digest"], tuple(s["config_ids"]), tuple(s["input_artifact_ids"]),
                  s["seeds"])


def _ns(tables, man, art_id):
    return SimpleNamespace(tables=tables, spec=man["spec"], artifact_id=art_id)


def references_from(s5t: dict, s4r: dict, key_by_trk: dict, visible: dict, s5_id: str, rec: str):
    """T21.1-T21.3 reference entries from a reference S5 (as `run_m1a.unit_reference`) and the N4 references."""
    from rq1.evaluation import matching as mt
    from rq1.ids import core
    pows = {p["pow_id"]: p for p in s4r["pow"]}
    entries, refs, groups = [], [], {}
    for e in s5t.get("episode", []):
        pw = pows[e["pow_id"]]
        person, fork = key_by_trk[pw["person_track_id"]], key_by_trk[pw["forklift_track_id"]]
        both = set(visible.get(person, ())) & set(visible.get(fork, ()))
        assessable = any(e["start_frame"] <= i < e["end_frame_excl"] for i in both)
        entries.append({"pow_id": e["pow_id"], "start_frame": e["start_frame"], "end_frame_excl": e["end_frame_excl"], "t_start_tl_s": e["t_start_tl_s"],
                        "t_end_tl_s": e["t_end_tl_s"], "lbl_O": e["lbl_O"], "lbl_H": e["lbl_H"], "lbl_PC": e["lbl_PC"], "person_key": person,
                        "forklift_key": fork, "assessable": assessable})
        rid = core.make_id("rin", {"rec_id": rec, "person": person, "forklift": fork, "start_frame": e["start_frame"], "end_frame_excl": e["end_frame_excl"],
                                   "reference_s5": s5_id})
        refs.append(mt.Reference(rid, e["t_start_tl_s"], e["t_end_tl_s"], (person, fork), assessable))
        groups[rid] = frozenset({"G1"}) if (e["lbl_O"] or e["lbl_H"] or e["lbl_PC"]) else frozenset()
    return entries, refs, groups


def run_camera(args) -> tuple[str, str, float]:  # pragma: no cover - driver over stored artifacts
    rec, prov = args
    import d54_b_v2 as b
    import d54_c_v2 as c
    import d57_split as sp
    import evaluate_pilot as ep
    from rq1.evaluation import association as assoc
    from rq1.events import s5
    from rq1.schema import files
    from rq1.substrate import builder
    from rq1.tracking import s3_config as sc
    from rq1.tracking import stitching
    path = OUT / "events" / f"{rec}.json"
    if path.exists():
        return rec, "skipped", 0.0
    t0 = time.time()
    ev = ep.ev
    ctx = m.Context("sdg")
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    support = cam.support()
    usable = sum(support.values())
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    s1dir = ROOT / f"out/t17_sdg/{ctx.camera(rec)['s1']}"
    s1 = {"frame": cam.frames, "coverage_segment": cam.coverage,
          "decode_summary": files.read_table(str(s1dir / "decode_summary.parquet"), "decode_summary", m.A.SCHEMA_VERSION)}
    base_unit, ref_unit = cam.units["base"], cam.units["reference"]
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", base_unit["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    rows_o, _, _ = ev.association(s3o, trk_key)
    summ_o, _ = assoc.summarize(rows_o, sup_all(rows_o))
    refs_by_frame = ep.ref_boxes(s3o, trk_key, cam.classes)
    res = {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "status": STATUS, "code_commit": prov[0], "contract": CONTRACT,
           "checks": {}, "artifacts": {}, "measures": {}}
    # --- references: alpha = stored base references; beta = diagnostic set rebuilt with m_gap_s 1.0 (T21.1 procedure)
    s4r, man4r = sp.load_art(ref_unit["s4"], M1A_ART)
    s5r_stored, man5r = sp.load_art(ref_unit["s5"], M1A_ART)
    s3r, _ = sp.load_art(ref_unit["s3"], M1A_ART)
    key_by_trk = ev.track_map(s3r, ev.reference_keys(cam.truth_rows), cam.classes)
    alpha_cfg = s5_config(ctx, "alpha", False)
    rebuilt5 = s5.build(s1, _ns(s4r, man4r, ref_unit["s4"]), alpha_cfg, _spec_of(man5r))
    entries_stored, refs_a, groups_a = references_from(s5r_stored, s4r, key_by_trk, cam.visible, ref_unit["s5"], rec)
    want = [{k: r[k] for k in entries_stored[0]} for r in ref_unit["references"]] if entries_stored else []
    refs_check, groups_check = ev.references(cam)
    res["checks"]["reference_procedure_at_m_gap_5"] = (rebuilt5.payload_sha256 == man5r["payload_sha256"]) and entries_stored == want and \
        [(r.ref_event_id, r.t_onset, r.t_offset, r.pair, r.assessable) for r in refs_a] == [(r.ref_event_id, r.t_onset, r.t_offset, r.pair, r.assessable) for r in refs_check]
    origin_ref = man4r["data_origin"]
    beta_cfg = dataclasses.replace(alpha_cfg, version_label=BETA_REF_LABEL, m_gap_s=BETA_M_GAP_S)
    beta5 = s5.build(s1, _ns(s4r, man4r, ref_unit["s4"]), beta_cfg, _spec("S5", prov, (s5.config_id(beta_cfg),), (ref_unit["s4"],)))
    res["artifacts"]["beta_reference_s5"] = _save(beta5, origin_ref)
    _, refs_b, groups_b = references_from(beta5.tables, s4r, key_by_trk, cam.visible, beta5.artifact_id, rec)
    references = {"alpha": (refs_a, groups_a), "beta": (refs_b, groups_b)}
    res["references"] = {d: {"references": len(r), "assessable_g1": sum(1 for x in r if x.assessable and "G1" in g[x.ref_event_id])} for d, (r, g) in references.items()}
    # --- system side
    pipe = json.loads((C_OUT / "cam" / rec / "pipeline.json").read_text())
    brun = json.loads((B_OUT / "cam" / f"{rec}.json").read_text())["runs"]["B-both"]
    s3c, man3c = sp.load_art(pipe["s3"], C_OUT / "artifacts")
    rows_c, _, _ = ep.association_detector(s3c, refs_by_frame)
    summ_c, _ = assoc.summarize(rows_c, sup_all(rows_c))
    s4c, man4c = sp.load_art(pipe["runs"]["C-v2"]["s4"], C_OUT / "artifacts")
    s4b, man4b = sp.load_art(brun["s4"], B_OUT / "artifacts")
    s4a, man4a = sp.load_art(base_unit["s4"], M1A_ART)
    # C-v2+T25: the stored detector S3 stitched with the STEP 3 winner; S4 as C-v2 (T24 on)
    params, chosen = stitch_params()
    floor = {(r["track_id"], r["frame_index"]): (r["x_m"], r["y_m"]) for r in s4c["object_state"] if r["x_m"] is not None}
    recording = cam.frames[0]["recording_id"]
    frames = {f["frame_index"]: f for f in cam.frames if f["eligible"] and f["recording_id"] == recording}
    accepted = stitching.links(stitching.tracks_of(s3c), frames, cam.coverage, params, floor)
    sid = stitching.stitch_ids(stitching.chains([t["trk_id"] for t in s3c["track"]], accepted), stitching.natural_keys(s3c))
    _, pkg = c.package()
    trc = sc.trc_id(pkg["run_config"], m.S4_BASE["g_max"], stitch=params)
    s3s = stitching.apply(SimpleNamespace(tables=s3c), sid, _spec("S3", prov, (trc,), tuple(man3c["spec"]["input_artifact_ids"])))
    origin = man4c["data_origin"]
    res["artifacts"]["stitched_s3"] = _save(s3s, origin)
    _, base_cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    t24_cfg, _, _ = b.run_config(base_cfg, gate=True, shift=True)
    s4s_art = builder.SubstrateBuilder().build(s1, s3s, {}, ctx_cal(ctx, rec), t24_cfg, _spec("S4", prov, tuple(man4c["spec"]["config_ids"]), (s3s.artifact_id,)))
    res["artifacts"]["stitched_s4"] = _save(s4s_art, origin)
    rows_s, _, _ = ep.association_detector(s3s.tables, refs_by_frame)
    summ_s, _ = assoc.summarize(rows_s, sup_all(rows_s))
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3s.tables["track"]}
    member_at = {(p["stitch_id"], p["frame_index"]): by_local[p["track_nk"][1]] for p in s3s.tables["track_point"]}
    res["stitching"] = {"links": len(accepted), "links_by_class": dict(Counter(next(t["class"] for t in s3c["track"] if t["trk_id"] == a["a"]) for a in accepted)),
                        "winner": chosen, "s3_config_id": trc}
    ident = lambda u, f: u
    stitched = lambda u, f: member_at.get((u, f))
    systems = {"C-v2": (s4c, man4c, pipe["runs"]["C-v2"]["s4"], pipe["runs"]["C-v2"]["s5"][BL], C_OUT / "artifacts", rows_c, summ_c, ident, False),
               "C-v2+T25": (s4s_art.tables, {"spec": s4s_art.spec}, s4s_art.artifact_id, None, None, rows_s, summ_s, stitched, True),
               "B-both": (s4b, man4b, brun["s4"], brun["s5"][BL], B_OUT / "artifacts", rows_o, summ_o, ident, False),
               "B-both+T25": (s4b, man4b, brun["s4"], None, None, rows_o, summ_o, ident, True),
               "A": (s4a, man4a, base_unit["s4"], base_unit["s5"][BL], M1A_ART, rows_o, summ_o, ident, False),
               "A+T25": (s4a, man4a, base_unit["s4"], None, None, rows_o, summ_o, ident, True)}
    for name, (s4t, man4, s4_id, s5_stored, root, rows, summ, member_track, join) in systems.items():
        pair_of = pair_resolver(s4t, rows, summ, member_track)
        res["measures"][name] = {}
        for d in DEFS:
            if d == "alpha" and not join:
                s5t, _ = sp.load_art(s5_stored, root)
                s5_id = s5_stored
            else:
                cfg = s5_config(ctx, d, join)
                art = s5.build(s1, _ns(s4t, man4, s4_id), cfg, _spec("S5", prov, (s5.config_id(cfg),), (s4_id,)))
                s5t, s5_id = art.tables, _save(art, origin if name.startswith("C") else man4.get("data_origin", origin))
            events = event_rows(s4t, s5t, pair_of)
            refs, groups = references[d]
            row = {"s5": s5_id, "summary": camera_summary(events), "by_reading": {}}
            for rd in READINGS:
                row["by_reading"][rd] = event_measures(refs, groups, events, rd, usable)
            res["measures"][name][d] = row
    res["seconds"] = round(time.time() - t0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, res)
    return rec, "done", res["seconds"]


def ctx_cal(ctx, rec):  # pragma: no cover - driver
    import run_pilot as rp
    _, _, cal = rp.load_s1(ctx, rec)
    if cal is None:
        raise RuntimeError(f"{rec}: no calibration")
    return cal


# ---------------------------------------------------------------------------------------------------- aggregation

def pool(parts: list[dict]) -> dict:
    """parts: per-camera event_measures of one (configuration, definition, reading)."""
    import extent_check as xc
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation.event_metrics import WindowCounts
    wc = [WindowCounts(**p["counts"]) for p in parts]
    h = em.headline(wc)
    t = {k: sum(getattr(x, k) for x in wc) for k in ("a", "m", "s", "m_s")}
    bands = [b for p in parts for b in p["unmatched_bands"]]
    refs = [n for p in parts for n in p["refs_events"]]
    splits = Counter(s for p in parts for s in p["splits"])
    return {"EV-M1": h["EV-M1"], "EV-M2": h["EV-M2"], "assessable_references": t["a"], "matched_references": t["m"], "system_events_g1": t["s"],
            "matched_events": t["m_s"], "unmatched_events": t["s"] - t["m_s"],
            "unmatched_by_band": {bd: bands.count(bd) for bd in xc.BANDS}, "unmatched_with_same_pair_overlap": sum(1 for bd in bands if bd != xc.BANDS[0]),
            "references_with_2plus_events": sum(1 for n in refs if n >= 2), "references_with_1_event": sum(1 for n in refs if n == 1),
            "splits": sum(splits.values()), "splits_by_mechanism": {k: splits.get(k, 0) for k in MECHANISMS}}


def pool_summary(parts: list[dict]) -> dict:
    members: Counter = Counter()
    for p in parts:
        members.update(p["members"])
    ev = sum(p["events"] for p in parts)
    return {"system_events": ev, "member_episodes": sum(p["member_episodes"] for p in parts), "members_per_event": (sum(p["member_episodes"] for p in parts) / ev) if ev else None,
            "events_by_members": {k: members.get(k, 0) for k in ("1", "2", "3", "4")}, "joined_events": sum(p["joined_events"] for p in parts),
            "unobserved_gap_s": sum(p["unobserved_gap_s"] for p in parts), "pair_readings_differ": sum(p["pair_readings_differ"] for p in parts)}


def summarize(cams: list[dict]) -> dict:
    out = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        out[view] = {"cameras": len(sub), "references": {d: {k: sum(c["references"][d][k] for c in sub) for k in ("references", "assessable_g1")} for d in DEFS}}
        for name in CONFIGS:
            out[view][name] = {}
            for d in DEFS:
                rows = [c["measures"][name][d] for c in sub]
                out[view][name][d] = {"summary": pool_summary([r["summary"] for r in rows]),
                                      **{f"reading_{rd}": pool([r["by_reading"][rd] for r in rows]) for rd in READINGS}}
    return out


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "events" / f"{r}.json").read_text()) for r in recs]
    table = summarize(cams)
    d54 = json.loads((ROOT / "research/m1b/d54_c_v2_tune.json").read_text())["tuning_116"]["all"]["C-v2"]
    d57 = json.loads((ROOT / "research/m1b/d57_split_diagnosis.json").read_text())
    c_alpha = table["all"]["C-v2"]["alpha"]["reading_a"]
    checks = {"reference_procedure_at_m_gap_5": sum(c["checks"]["reference_procedure_at_m_gap_5"] for c in cams), "cameras": len(cams),
              "c_v2_alpha_equals_d54": all(c_alpha[k] == d54[k] for k in ("EV-M1", "EV-M2", "assessable_references", "matched_references"))
              and c_alpha["system_events_g1"] == d54["system_events"],
              "c_v2_alpha_splits": c_alpha["splits_by_mechanism"], "d57_c_v2_splits": d57_splits(d57)}
    _, chosen = stitch_params()
    return {"status": STATUS, "decision": "D-58 STEP 4", "contract": "E-1.2.26 (Appendix T T25); v1 base values otherwise", "baseline": BL,
            "label_group": "G1", "matching": "N4 (unchanged)", "stitch_winner": chosen, "stitch_status": "STEP 3 winner, selected, not frozen",
            "definitions": {"alpha": "m_gap 5 frames, system and the stored base references (T21)",
                            "beta": f"m_gap_s {BETA_M_GAP_S} s, system and a reference set rebuilt from simulator truth with m_gap_s {BETA_M_GAP_S} "
                                    f"({BETA_REF_LABEL}); {BETA_M_GAP_S} s is a placeholder for this check only, not a v2 candidate"},
            "pair_readings": {"a": "CR-037 item 3 (a): at the closest-approach member's CA frame (applied in the code)",
                              "b": "CR-037 item 3 (b): every member at its own CA frame; unknown unless all agree"},
            "configurations": {"C-v2": "stored D-54 S4 and S5 (T25 off)", "C-v2+T25": "stitched detector S3 (T25.1, STEP 3 winner), S4 as C-v2, T25.2 on",
                               "B-both": "stored D-54 B-both (comparison)", "B-both+T25": "stored B-both S4, T25.2 on (T25.1 off: oracle)",
                               "A": "stored T-21 base (comparison)", "A+T25": "stored T-21 base S4, T25.2 on"},
            "checks": checks, "runtime_s": round(sum(c["seconds"] for c in cams), 1),
            "stitching": {"links": sum(c["stitching"]["links"] for c in cams),
                          "links_by_class": dict(sum((Counter(c["stitching"]["links_by_class"]) for c in cams), Counter()))},
            "tuning_116": table}


def d57_splits(d57: dict) -> dict | None:
    try:
        return d57["configs"]["C-v2"]["all"]["by_mechanism"]
    except (KeyError, TypeError):
        return None


def estimate() -> None:  # pragma: no cover - driver
    import run_pilot as rp
    import v2_sets
    global OUT
    prov = rp.provenance()
    t = v2_sets.tuning()
    OUT = __import__("pathlib").Path(os.environ.get("D58_EST", str(OUT.parent / "d58_estimate")))
    rows = []
    for rec in (t[0], t[-1]):
        _, _, s = run_camera((rec, prov))
        rows.append({"rec_id": rec, "seconds": s})
    per = sum(r["seconds"] for r in rows) / len(rows)
    est = {"status": "D-58 STEP 4 runtime estimate (2 tuning cameras, first and last)", "rows": rows, "per_camera_s": per,
           "total_116_cameras_h_serial": round(per * 116 / 3600, 3), "limit_h": LIMIT_H, "stop": per * 116 / 3600 > LIMIT_H}
    print(json.dumps(est, indent=1))


def main():  # pragma: no cover
    import run_pilot as rp
    import v2_sets
    what = sys.argv[1]
    if what == "estimate":
        estimate()
        return
    if what == "aggregate":
        p = ROOT / "research/m1b/d58_events_tune.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    if what == "run":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        tuning = v2_sets.tuning()
        recs = sys.argv[3:] or tuning
        assert set(recs) <= set(tuning), "tuning subset only (D-58)"
        prov = rp.provenance()
        jobs = [(r, prov) for r in recs]
        it = map(run_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=2).imap_unordered(run_camera, jobs)
        for n, r in enumerate(it, 1):
            print(n, *r, flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
