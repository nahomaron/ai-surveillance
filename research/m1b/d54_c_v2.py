"""D-54 STEP 3b: the detector path with the D-56 tracker package, T24 off (C-pkg) and on (C-v2), on the 116 tuning cameras.
Diagnostic, tuning subset, not a reported result. These runs never enter a report table beside the pilot columns.

  PYTHONPATH=src .venv/bin/python research/m1b/d54_c_v2.py estimate                     (2 cameras; STOP above 3 h)
  PYTHONPATH=src .venv/bin/python research/m1b/d54_c_v2.py run [rec ...]                -> out/m1b/v2t24/c/
  PYTHONPATH=src .venv/bin/python research/m1b/d54_c_v2.py evaluate [workers] [rec ...]
  PYTHONPATH=src .venv/bin/python research/m1b/d54_c_v2.py aggregate                    -> research/m1b/d54_c_v2_tune.json

Per camera:
  S2  the stored YOLO-World detections: the pilot S2 (96 cameras) or the D-55 step 1 probe S2 (20 cameras); no detection.
  S3  the D-56 package `trc_7flfpx52d2siiljxkqwcorr7nz` (T1 ByteTrack; forklift track_high, new_track and track_low 0.05,
      fuse_score false, track_buffer 90, match 0.8; person = column C ByteTrack defaults), one `.venv-det` process
      (`rq1.tracking.grid`, the D-55 runner), bridged at g_max 15 (D-45 item 1), `DetectorTrackSource` as the pilot.
      Check: the tracking measures of the new logs equal the stored D-55 grid result of the package on this camera.
  S4  full_camera, v1 base values. C-pkg: T24 off (the pilot's S4 configuration). C-v2: T24 on, the D-54 v2 candidate
      values (`d54_b_v2.run_config`, gate and shift), selected, not frozen.
  S5  BL-6.
  S8  N4 against the stored T-21 BL-6 references, label group G1, A5.2 association of the detector tracks (as the pilot).
Beside them, evaluated the same way from stored artifacts: column C (pilot, `out/m1b/pilot/cam/`; only the 96 tuning
cameras that are pilot cameras), B-tune (= stored column B) and A (stored).
Measures: EV-M1 / EV-M2 with counts; CM-03 (pair coverage, both bases, as the pilot); D-50 extent measures
(`extent_check.py` definitions): unmatched events by the best same-pair temporal IoU, references covered by two or more
same-pair episodes, episodes carrying `continuation_of_nk`; forklift and person position error and availability;
CR-034 size on C-v2.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
OUT = __import__("pathlib").Path(os.environ.get("D54C_OUT", str(ROOT / "out/m1b/v2t24/c")))  # D54C_OUT: runtime estimate only
STATUS = "diagnostic, tuning subset, not a reported result"
BL = "BL-6"
CONTRACT = "E-1.2.25"
PACKAGE = "trc_7flfpx52d2siiljxkqwcorr7nz"  # D-56
RUNS = ("C-pkg", "C-v2")
LIMIT_H = 3.0


def package():
    import v2_tracker_grid as grid
    configs = grid.configurations()
    row = next(c for c in configs if c["config_id"] == PACKAGE)
    if (row["family"], row["tracker_id"]) != ("T1", "bytetrack"):
        raise SystemExit(f"STOP: {PACKAGE} is not the T1 ByteTrack package")
    return configs[0], row


def jobs(column_c, pkg) -> list[dict]:
    return [{"job": "person", "tracker_id": "bytetrack", "class": "person", "params": column_c["params"]},
            {"job": PACKAGE, "tracker_id": pkg["tracker_id"], "class": "forklift", "params": pkg["params"]}]


def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def _save(art, origin) -> str:
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    return art.artifact_id


def run_camera(rec, prov, column_c, pkg) -> dict:  # pragma: no cover - driver
    import d54_b_v2 as b
    import run_pilot as rp
    import v2_tracker_grid as grid
    import v2_tracker_measures as vm
    from rq1.events import s5
    from rq1.substrate import builder
    from rq1.tracking import bridging
    from rq1.tracking import s3_config as sc
    from rq1.tracking.s3 import DetectorTrackSource
    d = OUT / "cam" / rec
    if (d / "pipeline.json").exists():
        return json.loads((d / "pipeline.json").read_text())
    ctx = m.Context("sdg")
    cam, s1, cal = rp.load_s1(ctx, rec)
    if cal is None:
        raise RuntimeError(f"{rec}: no calibration")
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    t0 = time.time()
    s2_id, art_dir = grid.s2_of(rec)
    dets = grid.load_tables(art_dir, s2_id)["detection"]
    refs_all, camo, ep = grid.references(rec)
    frames = sorted(camo.eligible)
    if frames != sorted(fr["frame_index"] for fr in s1["frame"] if fr["eligible"]):
        raise RuntimeError(f"{rec}: eligible frames differ")
    times = {"load": round(time.time() - t0, 2)}
    t0 = time.time()
    out, _ = grid.run_tracker(rec, frames, dets, jobs(column_c, pkg), d / "work")
    times["tracker"] = round(time.time() - t0, 2)
    # reproduction of the stored D-55 grid result (tracking measures of the package and of the person job)
    stored = json.loads((grid.GRID_DIR / f"{rec}.json").read_text())
    ds = s1["decode_summary"][0]
    score = {(x["frame_index"], x["det_index"]): x["score"] for x in dets}
    check = {}
    for cls, job, ref in (("person", "person", stored["person"]), ("forklift", PACKAGE, stored["configs"][PACKAGE])):
        refs = {i: [(k, bb) for k, c, bb in v if c == cls] for i, v in refs_all.items()}
        clipped = {i: [(k, cb) for k, cb in ((k, ep.ev_clip(bb, ds["width_px"], ds["height_px"])) for k, bb in v) if cb is not None] for i, v in refs.items()}
        check[cls] = json.loads(json.dumps(vm.measures(out["logs"][job], refs, clipped, score, frames))) == ref
    if not all(check.values()):
        raise SystemExit(f"STOP: {rec}: the package's tracker run does not reproduce the stored D-55 grid result {check}")
    t0 = time.time()
    g_max = m.S4_BASE["g_max"]
    pts = {"person": bridging.points_from_log(out["logs"]["person"], g_max), "forklift": bridging.points_from_log(out["logs"][PACKAGE], g_max)}
    trc = sc.trc_id(pkg["run_config"], g_max)
    if trc != PACKAGE:
        raise SystemExit(f"STOP: S3 configuration ID {trc} != {PACKAGE}")
    s3_art, local_map = DetectorTrackSource().tracks(rec, pts, dets, s1["frame"], _spec("S3", prov, (trc,), (s2_id,)))
    s3_id = _save(s3_art, origin)
    times["s3"] = round(time.time() - t0, 2)
    counts = {c: {k: sum(tr["counts"].get(k, 0) for tr in pts[c].values()) for k in ("tracked", "predicted", "lost_long_run", "runs_bridged", "runs_lost",
                                                                                       "predicted_degenerate")} | {"tracks": len(pts[c])} for c in pts}
    record, base_cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    res = {"rec_id": rec, "camera": cam["camera"], "viewpoint": pc.viewpoint(cam["camera"]), "status": STATUS, "code_commit": prov[0],
           "environment_digest": prov[1], "contract": CONTRACT, "preregistration": "docs/preregistration_FROZEN.md, version 1 (base values); "
           "tracker package D-56 and T24 values D-54: selected, not frozen", "s1": cam["s1"], "s2": s2_id, "s2_source": str(art_dir.relative_to(ROOT)),
           "s3": s3_id, "tracker_package": PACKAGE, "tracker_library": out["library"], "grid_reproduced": check, "track_counts": counts,
           "local_map": {str(k): list(v) for k, v in local_map.items()}, "runs": {}}
    c5 = m.s5_config(ctx, BL, m.S4_BASE, m.S5_BASE)
    for name in RUNS:
        t0 = time.time()
        if name == "C-pkg":  # the pilot's S4 configuration (run_pilot.py)
            from rq1.ids import core
            gcf_record = {"geometry": "full_camera"}
            cfg, gcf = base_cfg, core.make_id("gcf", gcf_record)
        else:
            cfg, gcf, gcf_record = b.run_config(base_cfg, gate=True, shift=True)
        s4 = builder.SubstrateBuilder().build(s1, s3_art, {}, cal, cfg, _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3_id,)))
        s5a = s5.build(s1, s4, c5, _spec("S5", prov, (s5.config_id(c5),), (s4.artifact_id,)))
        res["runs"][name] = {"geometry_config": gcf_record, "gcf": gcf, "s4": _save(s4, origin), "s5": {BL: _save(s5a, origin)}}
        if name == "C-v2":
            res["runs"][name]["cr034"] = b.cr034_counts(s3_art, s4, cal, b.S_MAX)
        times[name] = round(time.time() - t0, 2)
    res["seconds"] = times
    d.mkdir(parents=True, exist_ok=True)
    pc.write_json(d / "pipeline.json", res)
    return res


# ------------------------------------------------------------------------------------------------------------- evaluation

def extent(refs, groups, events, s4, s5, rows, summ) -> dict:
    """D-50 item 2 measures (`extent_check.camera`) on one column."""
    import extent_check as xc
    from rq1.evaluation import association as assoc
    from rq1.evaluation import matching as mt
    import evaluate_pilot as ep
    records = mt.match_window(refs, events, "G1", ep.ev.S8["iou_m"], "rule_conformance", groups)
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
        n, linked = xc.episodes_overlapping(r, eps)
        if r[0] in matched_refs or n > 0:
            per_ref.append({"matched": r[0] in matched_refs, "episodes": n, "linked": linked})
    return {"unmatched_bands": [xc.band(xc.best_same_pair_iou(e, R)) for e in unmatched], "per_ref": per_ref,
            "episodes": len(eps), "episodes_with_continuation": sum(1 for e in eps if e[3])}


def evaluate_camera(rec):  # pragma: no cover - driver over stored artifacts
    import gzip
    import pickle
    import evaluate_pilot as ep
    from rq1.evaluation import association as assoc
    ev = ep.ev
    path = OUT / "eval" / f"{rec}.pkl.gz"
    if path.exists():
        return rec, "skipped"
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    pipe = json.loads((OUT / "cam" / rec / "pipeline.json").read_text())
    support = cam.support()
    usable = sum(support.values())
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    refs, groups = ev.references(cam)
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    rows_o, _, tc_o = ev.association(s3o, trk_key)
    summ_o, _ = assoc.summarize(rows_o, sup_all(rows_o))
    refs_by_frame = ep.ref_boxes(s3o, trk_key, cam.classes)
    ref_visible, ref_present = {}, {}
    for i, v in refs_by_frame.items():
        for k, c, _ in v:
            ref_visible.setdefault(i, {})[k] = c
    for key, cls, i, *_ in cam.truth_rows:
        ref_present.setdefault(i, set()).add(key)

    def detector(s3_tables):
        rows, _, tc = ep.association_detector(s3_tables, refs_by_frame)
        summ, _ = assoc.summarize(rows, sup_all(rows))
        return rows, summ, tc

    s3new = _load(pipe["s3"], OUT / "artifacts")
    det_new = detector(s3new)
    cols = {"A (stored)": (ev.load_art(ep.M1A_LABEL, "sdg", base["s4"]), ev.load_art(ep.M1A_LABEL, "sdg", base["s5"][BL]), rows_o, summ_o, tc_o, "simulator_truth", None),
            "B-tune (stored B)": (ev.load_art(ep.M1A_LABEL, "sdg", fc["s4"]), ev.load_art(ep.M1A_LABEL, "sdg", fc["s5"][BL]), rows_o, summ_o, tc_o, "full_camera", None)}
    pilot = pc.OUT / "cam" / rec / "pipeline.json"
    if pilot.exists():
        pp = json.loads(pilot.read_text())
        s3c = ep.load_pilot(pp["s3"])
        cols["C (pilot, stored)"] = (ep.load_pilot(pp["s4"]), ep.load_pilot(pp["s5"][BL]), *detector(s3c), "full_camera", s3c)
    for name in RUNS:
        r = pipe["runs"][name]
        cols[name] = (_load(r["s4"], OUT / "artifacts"), _load(r["s5"][BL], OUT / "artifacts"), *det_new, "full_camera", s3new)
    out = {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "pilot_camera": pilot.exists(), "ev": {}, "cm03": {}, "extent": {}, "position": {}}
    persons_o = {t["trk_id"] for t in s3o["track"] if t["class"] == "person"}
    for col, (s4, s5a, rows, summ, tc, tier, s3d) in cols.items():
        events = ev.system_events(s4, s5a, rows, summ)
        out["ev"][col] = ev.ev_counts(refs, groups, events, usable)["counts"]
        cmp = ep.completeness(cam, support, rows, tc, s4, tier, ref_visible, ref_present)
        out["cm03"][col] = {basis: [(r["denominator"], r["numerator"]) for r in cmp[("CM-03", basis)]] for basis in ("detected", "detected_plus_inferred")}
        out["extent"][col] = extent(refs, groups, events, s4, s5a, rows, summ)
        if col == "A (stored)":
            continue
        if s3d is None:
            ident = ep.Identity(lambda t, i: trk_key[t], persons_o)
        else:
            matched = {(r["track_id"], r["frame_index"]): r["physical_identity_id"] for r in rows if r["status"] == "matched"}
            ident = ep.Identity(lambda t, i, mm=matched: mm.get((t, i)), {t["trk_id"] for t in s3d["track"] if t["class"] == "person"})
        out["position"][col] = ep.positions(s4, ident, cam)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as f:
        pickle.dump(out, f)
    os.replace(tmp, path)
    return rec, "done"


def _load(art_id, root):
    from rq1.schema import files
    d = root / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}


def pool_extent(parts: list[dict]) -> dict:
    import extent_check as xc
    refs = [x for p in parts for x in p["per_ref"]]
    bands = [b for p in parts for b in p["unmatched_bands"]]
    return {"unmatched_events": len(bands), "unmatched_by_band": {b: bands.count(b) for b in xc.BANDS},
            "unmatched_with_same_pair_overlap": sum(1 for b in bands if b != xc.BANDS[0]),
            "references_matched_or_overlapped": len(refs), "of_which_matched": sum(1 for x in refs if x["matched"]),
            "by_episode_count": {str(k): v for k, v in sorted(Counter(min(x["episodes"], 4) for x in refs).items())},
            "references_with_2plus_episodes": sum(1 for x in refs if x["episodes"] >= 2),
            "episodes_overlapping_references": sum(x["episodes"] for x in refs), "of_which_linked": sum(x["linked"] for x in refs),
            "episodes": sum(p["episodes"] for p in parts), "episodes_with_continuation_of_nk": sum(p["episodes_with_continuation"] for p in parts)}


def summarize(cams: list[dict], cols: list[str]) -> dict:
    import evaluate_pilot as ep
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation.event_metrics import WindowCounts
    out = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        out[view] = {"cameras": len(sub)}
        for col in cols:
            wc = [WindowCounts(**c["ev"][col]) for c in sub]
            h = em.headline(wc)
            t = {k: sum(getattr(x, k) for x in wc) for k in ("a", "m", "s", "m_s")}
            cm03 = {}
            for basis in ("detected", "detected_plus_inferred"):
                den = sum(d for c in sub for d, _ in c["cm03"][col][basis])
                num = sum(n for c in sub for _, n in c["cm03"][col][basis])
                cm03[basis] = {"numerator_s": num, "denominator_s": den, "value": num / den if den else None}
            pos = {}
            if col in sub[0]["position"]:
                for cls in ("person", "forklift"):
                    errs = [e for c in sub for (k, _, e) in c["position"][col][0] if k == cls]
                    avail: Counter = Counter()
                    for c in sub:
                        for (k, reason), n in c["position"][col][1].items():
                            if k == cls:
                                avail[reason] += n
                    pos[cls] = {"error": ep.pos_summary(errs), "availability": dict(sorted(avail.items()))}
            out[view][col] = {"EV-M1": h["EV-M1"], "EV-M2": h["EV-M2"], "assessable_references": t["a"], "matched_references": t["m"],
                              "system_events": t["s"], "matched_events": t["m_s"], "unmatched_events": t["s"] - t["m_s"], "CM-03": cm03,
                              "extent": pool_extent([c["extent"][col] for c in sub]), "position": pos}
    return out


def aggregate() -> dict:  # pragma: no cover
    import gzip
    import pickle
    import v2_sets
    recs = v2_sets.tuning()
    cams = []
    for r in recs:
        with gzip.open(OUT / "eval" / f"{r}.pkl.gz", "rb") as f:
            cams.append(pickle.load(f))
    pipes = [json.loads((OUT / "cam" / r / "pipeline.json").read_text()) for r in recs]
    pilot = [c for c in cams if c["pilot_camera"]]
    all_cols = ["A (stored)", "B-tune (stored B)", "C-pkg", "C-v2"]
    keys = pipes[0]["runs"]["C-v2"]["cr034"].keys()
    return {"status": STATUS, "decision": "D-54 STEP 3b", "contract": "E-1.2.25 (Appendix T T24); v1 base values otherwise",
            "baseline": BL, "label_group": "G1", "tracker_package": PACKAGE,
            "t24_values_c_v2": {"s_max_m_per_px": 0.1, "forklift_anchor": "box_bottom_centre", "anchor_offset_m": 1.00, "anchor_taper_m": 2.0,
                                "status": "D-54 v2 candidate values, selected, not frozen"},
            "caveat_d56": "The package accepts forklift detections down to score 0.05. Point precision 0.979 was measured on synthetic SDG data only "
                          "and is not known for real footage.",
            "runs": {"C-pkg": "S2 stored -> S3 D-56 package -> S4 full_camera, T24 off -> S5 BL-6 (the tracker effect alone)",
                     "C-v2": "as C-pkg with T24 on (T24.2 gate s_max 0.1; T24.1 forklift shift d 1.00 m, r_taper 2.0 m)",
                     "C (pilot, stored)": "pilot column C (column C tracker settings), stored; only on the 96 tuning cameras that are pilot cameras",
                     "B-tune (stored B)": "column B, stored T-21 full_camera unit", "A (stored)": "column A, stored T-21 base unit"},
            "s2": {"pilot": sum(1 for p in pipes if "pilot" in p["s2_source"]), "probe_d55": sum(1 for p in pipes if "v2trk" in p["s2_source"])},
            "checks": {"tracker_reproduces_d55_grid": sum(all(p["grid_reproduced"].values()) for p in pipes), "cameras": len(pipes)},
            "cr034_size_c_v2": {k: sum(p["runs"]["C-v2"]["cr034"][k] for p in pipes) for k in keys},
            "extent_definitions": "extent_check.py (D-50 item 2): BL-6, G1; unmatched = false or duplicate alerts; same-pair overlap = best temporal IoU "
                                  "with a same-pair reference > 0; references matched (N4) or overlapped by a same-pair episode, by the number of "
                                  "overlapping same-pair episodes; continuation_of_nk counted over all BL-6 episodes and over the overlapping ones",
            "cm03": "pair coverage (CM-03), pooled as sum of numerators / sum of denominators (as the pilot's point value)",
            "position": "|estimate - simulator position| of the identity (oracle track's object; detector: the A5.2-matched identity), as the pilot (D-41)",
            "code_commit": sorted({p["code_commit"] for p in pipes}),
            "runtime_s": {k: round(sum(p["seconds"][k] for p in pipes), 1) for k in pipes[0]["seconds"]},
            "tuning_116": summarize(cams, all_cols),
            "pilot_96": {"note": "the 96 tuning cameras that are pilot cameras (column C exists only there)",
                         **summarize(pilot, ["A (stored)", "B-tune (stored B)", "C (pilot, stored)", "C-pkg", "C-v2"])}}


def estimate() -> None:  # pragma: no cover - driver
    import run_pilot as rp
    import v2_sets
    global OUT
    column_c, pkg = package()
    prov = rp.provenance()
    t = v2_sets.tuning()
    recs = [t[0], t[-1]]
    tmp = __import__("pathlib").Path(os.environ.get("D54C_EST", str(OUT.parent / "c_estimate")))
    OUT = tmp
    rows = []
    for rec in recs:
        t0 = time.time()
        run_camera(rec, prov, column_c, pkg)
        t1 = time.time()
        evaluate_camera(rec)
        rows.append({"rec_id": rec, "run_s": round(t1 - t0, 1), "evaluate_s": round(time.time() - t1, 1)})
    per = sum(r["run_s"] + r["evaluate_s"] for r in rows) / len(rows)
    est = {"status": "D-54 STEP 3b runtime estimate (2 tuning cameras, first and last)", "rows": rows, "per_camera_s": round(per, 1),
           "total_116_cameras_h": round(per * 116 / 3600, 2), "limit_h": LIMIT_H, "stop": per * 116 / 3600 > LIMIT_H}
    pc.write_json(tmp / "estimate.json", est)
    print(json.dumps(est, indent=1))


def main():  # pragma: no cover
    import run_pilot as rp
    import v2_sets
    what = sys.argv[1]
    if what == "estimate":
        estimate()
        return
    if what == "aggregate":
        p = ROOT / "research/m1b/d54_c_v2_tune.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    tuning = v2_sets.tuning()
    if what == "run":
        recs = sys.argv[2:] or tuning
        assert set(recs) <= set(tuning), "tuning subset only (D-54 ruling 5)"
        column_c, pkg = package()
        prov = rp.provenance()
        t0 = time.time()
        for n, r in enumerate(recs, 1):
            res = run_camera(r, prov, column_c, pkg)
            print(n, r, json.dumps(res["seconds"]), f"elapsed {round(time.time() - t0)} s", flush=True)
        return
    if what == "evaluate":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        recs = sys.argv[3:] or tuning
        assert set(recs) <= set(tuning), "tuning subset only (D-54 ruling 5)"
        it = map(evaluate_camera, recs) if workers == 1 else Pool(workers, maxtasksperchild=2).imap_unordered(evaluate_camera, recs)
        for n, res in enumerate(it, 1):
            print(n, *res, flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
