"""D-61 STEP 4: one diagnostic event check at the pre-registration v2 base values on the 116 tuning cameras.
Diagnostic, tuning subset, not a reported result. Synthetic-data evaluation; experimental. This check selects nothing.

  PYTHONPATH=src .venv/bin/python research/m1b/d61_events.py estimate                (2 cameras; STOP above 3 h)
  PYTHONPATH=src .venv/bin/python research/m1b/d61_events.py run [workers] [rec ...]  -> out/m1b/d61/events/<rec>.json
  PYTHONPATH=src .venv/bin/python research/m1b/d61_events.py aggregate               -> research/m1b/d61_events_tune.json

Values: `research/preregistration/v2_values.py` (D-61 section 1.3-1.5): S4 g_max 45; S5 pet_max 1.5, d_p 3.0, w_post 1.5,
e_dec 1.0, k_c 1.5, m_gap_s 1.5 (T25.3); band edges 0, 0.5, 1, 2, 3, 4 m; T24 on (d 1.00 m, r_taper 2.0 m, s_max 0.1);
T25.1 = the D-58 STEP 3 selection (T_s 5 s, r_g 0.5 m); T25.2 on. BL-6, N4 (iou_m 0.3), label group G1, unchanged.

Configurations:
  C-v2+T25  stored S2 (no detection) -> the D-56 tracker package, re-run (logs are not stored; the run must reproduce
            the stored D-55 grid measures) -> bridged at g_max 45 -> S4 full_camera with T24 (floor positions for T25.1)
            -> T25.1 stitched S3 -> S4 -> S5 BL-6 with T25.2.
  A+T25     ORACLE-S3 at g_max 45 -> S4 simulator_truth -> S5 BL-6 with T25.2.
Reference set (diagnostic, stored apart from the STEP 5 references under out/m1b/d61/reference_diag/): the T21.1 reference
S3 (rebuilt; its payload must equal the stored T-21 reference S3) -> S4 simulator_truth at the v2 values -> S5 BL-6 at the
v2 values, m_gap_s 1.5, T25.2 off (T25.2 d). References and G1 groups as T21.1-T21.3 (`d58_events.references_from`).
g_max counterfactual (for "the IE share caused by the new g_max" only, AR-71 item 5): both configurations once more with
g_max 15 and every other value v2. Not scored. Check: the detector S3 bridged at g_max 15 equals the stored D-54 S3 payload.
Measures: EV-M1 / EV-M2 with counts (CR-037 pair readings a and b); system events, members per event (n_members),
joined events, unobserved_gap_s; IE share = S_VIEW events carrying lbl_IE / all S_VIEW events, at g_max 45 and 15.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from multiprocessing import Pool
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../preregistration"))
import pilot_common as pc  # noqa: E402
import v2_values as v2  # noqa: E402

m = pc.m
ROOT = pc.ROOT
C_OUT = ROOT / "out/m1b/v2t24/c"
M1A = ROOT / "out/m1a/run1/sdg"
M1A_ART = M1A / "artifacts"
OUT = __import__("pathlib").Path(os.environ.get("D61_OUT", str(ROOT / "out/m1b/d61")))  # D61_OUT: runtime estimate only
STATUS = "diagnostic, tuning subset, not a reported result; synthetic-data evaluation; experimental"
CONTRACT = v2.CONTRACT
BL = "BL-6"
CONFIGS = ("C-v2+T25", "A+T25")
READINGS = ("a", "b")
GMAX_CF = 15  # v1 g_max, counterfactual only
LIMIT_H = 3.0
LABEL_SYS = "D-61 diagnostic: v2 base values (not frozen)"
LABEL_CF = "D-61 diagnostic: v2 base values, g_max 15 counterfactual (not frozen)"
LABEL_REF = "D-61 diagnostic v2 tuning reference set: diagnostic, not the v2 reference (STEP 5)"


# ---------------------------------------------------------------------------------------------------- pure functions

def ie_share(events: list[dict]) -> dict:
    """IE share of S_VIEW candidate events (`d58_events.event_rows` rows): events carrying lbl_IE / all events."""
    n = len(events)
    k = sum(1 for e in events if "IE" in e["labels"])
    return {"events": n, "ie_events": k, "ie_share": (k / n) if n else None}


def ie_attribution(at_v2: dict, at_cf: dict) -> dict:
    """IE share at g_max 45 (v2) minus IE share at g_max 15, every other value v2 (AR-71 item 5)."""
    a, b = at_v2["ie_share"], at_cf["ie_share"]
    return {"g_max_45": at_v2, "g_max_15": at_cf, "difference": (a - b) if a is not None and b is not None else None,
            "ie_events_difference": at_v2["ie_events"] - at_cf["ie_events"]}


def pool_ie(parts: list[dict]) -> dict:
    n = sum(p["events"] for p in parts)
    k = sum(p["ie_events"] for p in parts)
    return {"events": n, "ie_events": k, "ie_share": (k / n) if n else None}


# ---------------------------------------------------------------------------------------------------- drivers

def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def _save(art, origin, sub: str = "") -> str:
    root = OUT / sub if sub else OUT
    target = root / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=root / "register.jsonl")
    return art.artifact_id


def _manifest(art_id, root) -> dict:
    return json.loads((root / art_id / "manifest.json").read_text())


def detector_chain(ctx, rec, s1, cal, out_logs, dets, s2_id, pkg, cam, g_max, label, prov, origin, save):  # pragma: no cover - driver
    """Bridged S3 at g_max -> T24 S4 (floor) -> T25.1 stitched S3 -> S4 -> S5 BL-6 with T25.2."""
    import d54_b_v2 as b
    import d54_c_v2 as c
    from rq1.events import s5
    from rq1.substrate import builder
    from rq1.tracking import bridging, stitching
    from rq1.tracking import s3_config as sc
    from rq1.tracking.s3 import DetectorTrackSource
    pts = {"person": bridging.points_from_log(out_logs["person"], g_max), "forklift": bridging.points_from_log(out_logs[c.PACKAGE], g_max)}
    trc = sc.trc_id(pkg["run_config"], g_max)
    s3_art, _ = DetectorTrackSource().tracks(rec, pts, dets, s1["frame"], _spec("S3", prov, (trc,), (s2_id,)))
    record, base_cfg, _, _ = v2.substrate_config(ctx, label, g_max)
    cfg, gcf, _ = b.run_config(base_cfg, gate=True, shift=True)
    s4_ids = (s5.substrate_config_id(record), gcf)
    s4u = builder.SubstrateBuilder().build(s1, s3_art, {}, cal, cfg, _spec("S4", prov, s4_ids, (s3_art.artifact_id,)))
    floor = {(r["track_id"], r["frame_index"]): (r["x_m"], r["y_m"]) for r in s4u.tables["object_state"] if r["x_m"] is not None}
    params = v2.stitch_params()
    recording = cam.frames[0]["recording_id"]
    frames = {f["frame_index"]: f for f in cam.frames if f["eligible"] and f["recording_id"] == recording}
    accepted = stitching.links(stitching.tracks_of(s3_art.tables), frames, cam.coverage, params, floor)
    sid = stitching.stitch_ids(stitching.chains([t["trk_id"] for t in s3_art.tables["track"]], accepted), stitching.natural_keys(s3_art.tables))
    trc_s = sc.trc_id(pkg["run_config"], g_max, stitch=params)
    s3s = stitching.apply(SimpleNamespace(tables=s3_art.tables), sid, _spec("S3", prov, (trc_s,), (s2_id,)))
    s4s = builder.SubstrateBuilder().build(s1, s3s, {}, cal, cfg, _spec("S4", prov, s4_ids, (s3s.artifact_id,)))
    c5 = v2.s5_config(ctx, BL, label, True, g_max)
    s5a = s5.build(s1, s4s, c5, _spec("S5", prov, (s5.config_id(c5),), (s4s.artifact_id,)))
    ids = {"s3": s3_art.artifact_id, "s3_payload": s3_art.payload_sha256, "s3_config": trc, "s3_stitched": s3s.artifact_id, "s3_stitched_config": trc_s,
           "s4": s4s.artifact_id, "s5": s5a.artifact_id, "s5_config": s5.config_id(c5), "gcf": gcf,
           "links": len(accepted), "links_by_class": dict(Counter(next(t["class"] for t in s3_art.tables["track"] if t["trk_id"] == a["a"]) for a in accepted))}
    if save:
        for art in (s3_art, s3s, s4s, s5a):
            _save(art, origin)
    return s3s, s4s, s5a, ids


def oracle_chain(ctx, rec, data, s1, g_max, label, prov, origin, save):  # pragma: no cover - driver
    from rq1.events import s5
    from rq1.ids import core
    from rq1.substrate import builder
    s3_art, positions, _ = m.s3(ctx, rec, data, g_max, prov)
    record, cfg, _, _ = v2.substrate_config(ctx, label, g_max)
    gcf = core.make_id("gcf", {"geometry": "simulator_truth"})
    s4a = builder.SubstrateBuilder().build(s1, s3_art, positions, None, cfg, _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3_art.artifact_id,)))
    c5 = v2.s5_config(ctx, BL, label, True, g_max)
    s5a = s5.build(s1, s4a, c5, _spec("S5", prov, (s5.config_id(c5),), (s4a.artifact_id,)))
    if save:
        for art in (s3_art, s4a, s5a):
            _save(art, origin)
    return s3_art, s4a, s5a, {"s3": s3_art.artifact_id, "s4": s4a.artifact_id, "s5": s5a.artifact_id, "s5_config": s5.config_id(c5)}


def reference_chain(ctx, rec, data, s1, prov, origin):  # pragma: no cover - driver
    """T21.1 at the v2 values: reference S3 (complete truth) -> S4 simulator_truth -> S5 BL-6, T25.2 off (T25.2 d)."""
    from rq1.events import s5
    from rq1.ids import core
    from rq1.substrate import builder
    s3r, positions = m.reference_s3(rec, data, prov)
    record, cfg, _, _ = v2.substrate_config(ctx, LABEL_REF)
    gcf = core.make_id("gcf", {"geometry": "simulator_truth"})
    s4r = builder.SubstrateBuilder().build(s1, s3r, positions, None, cfg, _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3r.artifact_id,)))
    c5 = v2.s5_config(ctx, BL, LABEL_REF, False)
    s5r = s5.build(s1, s4r, c5, _spec("S5", prov, (s5.config_id(c5),), (s4r.artifact_id,)))
    for art in (s3r, s4r, s5r):
        _save(art, origin, "reference_diag")
    return s3r, s4r, s5r


def run_camera(args) -> tuple[str, str, float]:  # pragma: no cover - driver over stored artifacts
    rec, prov = args
    import d54_c_v2 as c
    import d58_events as d58
    import evaluate_pilot as ep
    import run_pilot as rp
    import v2_tracker_grid as grid
    import v2_tracker_measures as vm
    from rq1.evaluation import association as assoc
    path = OUT / "events" / f"{rec}.json"
    if path.exists():
        return rec, "skipped", 0.0
    t0 = time.time()
    ev = ep.ev
    ctx = m.Context("sdg")
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    _, s1, cal = rp.load_s1(ctx, rec)
    if cal is None:
        raise RuntimeError(f"{rec}: no calibration")
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    support = cam.support()
    usable = sum(support.values())
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    data = m.load(ctx, rec)
    res = {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "status": STATUS, "code_commit": prov[0], "contract": CONTRACT,
           "decision": "D-61 STEP 4", "checks": {}, "artifacts": {}, "measures": {}, "ie": {}}
    # --- diagnostic v2 reference set
    s3r, s4r, s5r = reference_chain(ctx, rec, data, s1, prov, origin)
    ref_unit = cam.units["reference"]
    res["checks"]["reference_s3_equals_t21"] = s3r.payload_sha256 == _manifest(ref_unit["s3"], M1A_ART)["payload_sha256"]
    key_by_trk = ev.track_map(s3r.tables, ev.reference_keys(cam.truth_rows), cam.classes)
    _, refs, groups = d58.references_from(s5r.tables, s4r.tables, key_by_trk, cam.visible, s5r.artifact_id, rec)
    res["artifacts"]["reference"] = {"s3": s3r.artifact_id, "s4": s4r.artifact_id, "s5": s5r.artifact_id}
    res["references"] = {"references": len(refs), "assessable_g1": sum(1 for x in refs if x.assessable and "G1" in groups[x.ref_event_id])}
    # --- detector path: tracker re-run on the stored S2 (no detection)
    column_c, pkg = c.package()
    s2_id, art_dir = grid.s2_of(rec)
    dets = grid.load_tables(art_dir, s2_id)["detection"]
    refs_all, camo, gep = grid.references(rec)
    frames = sorted(camo.eligible)
    out, _ = grid.run_tracker(rec, frames, dets, c.jobs(column_c, pkg), OUT / "work" / rec)
    stored = json.loads((grid.GRID_DIR / f"{rec}.json").read_text())
    ds = s1["decode_summary"][0]
    score = {(x["frame_index"], x["det_index"]): x["score"] for x in dets}
    for cls, job, ref in (("person", "person", stored["person"]), ("forklift", c.PACKAGE, stored["configs"][c.PACKAGE])):
        rb = {i: [(k, bb) for k, cc, bb in v if cc == cls] for i, v in refs_all.items()}
        clipped = {i: [(k, cb) for k, cb in ((k, gep.ev_clip(bb, ds["width_px"], ds["height_px"])) for k, bb in v) if cb is not None] for i, v in rb.items()}
        res["checks"][f"tracker_reproduces_d55_{cls}"] = json.loads(json.dumps(vm.measures(out["logs"][job], rb, clipped, score, frames))) == ref
    if not all(v for k, v in res["checks"].items() if k.startswith("tracker_")):
        raise SystemExit(f"STOP: {rec}: the tracker run does not reproduce the stored D-55 result")
    s3o_base = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
    trk_key_base = ev.track_map(s3o_base, ev.oracle_keys(cam.visible), cam.classes)
    refs_by_frame = ep.ref_boxes(s3o_base, trk_key_base, cam.classes)
    systems = {}
    for g_max, label, save in ((v2.S4_V2["g_max"], LABEL_SYS, True), (GMAX_CF, LABEL_CF, False)):
        s3s, s4s, s5s, ids = detector_chain(ctx, rec, s1, cal, out["logs"], dets, s2_id, pkg, cam, g_max, label, prov, origin, save)
        if g_max == GMAX_CF:
            pipe = json.loads((C_OUT / "cam" / rec / "pipeline.json").read_text())
            res["checks"]["detector_s3_g_max_15_equals_d54"] = ids["s3_payload"] == _manifest(pipe["s3"], C_OUT / "artifacts")["payload_sha256"]
        by_local = {t["track_local_id"]: t["trk_id"] for t in s3s.tables["track"]}
        member_at = {(p["stitch_id"], p["frame_index"]): by_local[p["track_nk"][1]] for p in s3s.tables["track_point"]}
        rows_s, _, _ = ep.association_detector(s3s.tables, refs_by_frame)
        summ_s, _ = assoc.summarize(rows_s, sup_all(rows_s))
        systems[("C-v2+T25", g_max)] = (s4s.tables, s5s.tables, rows_s, summ_s, lambda u, f, ma=member_at: ma.get((u, f)), ids)
        s3a, s4a, s5a, ida = oracle_chain(ctx, rec, data, s1, g_max, label, prov, origin, save)
        trk_key = ev.track_map(s3a.tables, ev.oracle_keys(cam.visible), cam.classes)
        rows_o, _, _ = ev.association(s3a.tables, trk_key)
        summ_o, _ = assoc.summarize(rows_o, sup_all(rows_o))
        systems[("A+T25", g_max)] = (s4a.tables, s5a.tables, rows_o, summ_o, lambda u, f: u, ida)
    for (name, g_max), (s4t, s5t, rows, summ, member_track, ids) in systems.items():
        events = d58.event_rows(s4t, s5t, d58.pair_resolver(s4t, rows, summ, member_track))
        res["ie"].setdefault(name, {})[str(g_max)] = ie_share(events)
        res["artifacts"].setdefault(name, {})[str(g_max)] = ids
        if g_max == GMAX_CF:
            continue
        res["measures"][name] = {"summary": d58.camera_summary(events),
                                 "by_reading": {rd: d58.event_measures(refs, groups, events, rd, usable) for rd in READINGS}}
    res["seconds"] = round(time.time() - t0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, res)
    return rec, "done", res["seconds"]


# ---------------------------------------------------------------------------------------------------- aggregation

def summarize(cams: list[dict]) -> dict:
    import d58_events as d58
    out = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        out[view] = {"cameras": len(sub), "references": {k: sum(c["references"][k] for c in sub) for k in ("references", "assessable_g1")}}
        for name in CONFIGS:
            rows = [c["measures"][name] for c in sub]
            ie = {g: pool_ie([c["ie"][name][g] for c in sub]) for g in (str(v2.S4_V2["g_max"]), str(GMAX_CF))}
            out[view][name] = {"summary": d58.pool_summary([r["summary"] for r in rows]),
                               **{f"reading_{rd}": d58.pool([r["by_reading"][rd] for r in rows]) for rd in READINGS},
                               "ie_by_g_max": ie_attribution(ie[str(v2.S4_V2["g_max"])], ie[str(GMAX_CF)])}
    return out


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "events" / f"{r}.json").read_text()) for r in recs]
    checks = {k: sum(1 for c in cams if c["checks"].get(k)) for k in sorted({k for c in cams for k in c["checks"]})}
    checks["cameras"] = len(cams)
    sel = v2.stitch_selection()
    return {"status": STATUS, "decision": "D-61 STEP 4 (replaces D-58 STEP 4)", "contract": CONTRACT, "selects": "nothing",
            "values": {"S4": v2.S4_V2, "S5": v2.S5_V2, "m_gap_s": v2.M_GAP_S, "band_edges_m": v2.BAND_EDGES_V2, "T24": v2.T24,
                       "stitch": sel, "join_across_pow": v2.JOIN_ACROSS_POW, "changed_from_v1": v2.changed_from_v1()},
            "baseline": BL, "label_group": "G1", "matching": "N4 (unchanged), iou_m 0.3",
            "reference_set": f"{LABEL_REF}; out/m1b/d61/reference_diag/, apart from the STEP 5 references",
            "pair_readings": {"a": "CR-037 item 3 (a): at the closest-approach member's CA frame (applied in the code)",
                              "b": "CR-037 item 3 (b): every member at its own CA frame; unknown unless all agree"},
            "ie_share": "S_VIEW events carrying lbl_IE / all S_VIEW events; 'caused by the new g_max' = share at g_max 45 minus the share at "
                        "g_max 15 with every other value v2 (AR-71 item 5)",
            "stitch_note": "the D-58 STEP 3 selection was made on detector S3 bridged at g_max 15 (v1); D-61 STEP 3 = D-58 STEP 3 as written",
            "checks": checks, "runtime_s": round(sum(c["seconds"] for c in cams), 1),
            "stitching_links_g_max_45": sum(c["artifacts"]["C-v2+T25"][str(v2.S4_V2["g_max"])]["links"] for c in cams),
            "tuning_116": summarize(cams)}


def estimate() -> None:  # pragma: no cover - driver
    import run_pilot as rp
    import v2_sets
    global OUT
    prov = rp.provenance()
    t = v2_sets.tuning()
    OUT = __import__("pathlib").Path(os.environ.get("D61_EST", str(OUT.parent / "d61_estimate")))
    rows = []
    for rec in (t[0], t[-1]):
        _, _, s = run_camera((rec, prov))
        rows.append({"rec_id": rec, "seconds": s})
    per = sum(r["seconds"] for r in rows) / len(rows)
    est = {"status": "D-61 STEP 4 runtime estimate (2 tuning cameras, first and last)", "rows": rows, "per_camera_s": per,
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
        p = ROOT / "research/m1b/d61_events_tune.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    if what == "run":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        tuning = v2_sets.tuning()
        recs = sys.argv[3:] or tuning
        assert set(recs) <= set(tuning), "tuning subset only (D-61)"
        prov = rp.provenance()
        jobs = [(r, prov) for r in recs]
        it = map(run_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=2).imap_unordered(run_camera, jobs)
        for n, r in enumerate(it, 1):
            print(n, *r, flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
