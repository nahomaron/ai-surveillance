"""D-54 STEP 3: column B with T24 on, on the 116 tuning cameras (oracle boxes, BL-6). Diagnostic, tuning subset, not a
reported result. These runs never enter a report table beside A, B, C or C'.

  PYTHONPATH=src .venv/bin/python research/m1b/d54_b_v2.py run [workers] [rec ...]       -> out/m1b/v2t24/b/
  PYTHONPATH=src .venv/bin/python research/m1b/d54_b_v2.py evaluate [workers] [rec ...]
  PYTHONPATH=src .venv/bin/python research/m1b/d54_b_v2.py aggregate                    -> research/m1b/d54_b_v2_tune.json

Runs (each ORACLE-S3 -> S4 full_camera -> S5 BL-6, frozen v1 base values `m1a_common.S4_BASE`, `S5_BASE`; Appendix T T24,
E-1.2.25, with the D-54 v2 candidate values, selected, not frozen):
  B-T24.2  s_max_m_per_px = 0.1 (T24.2); footprint priors unchanged
  B-T24.1  forklift prior anchor = box_bottom_centre, anchor_offset_m d = 1.00, anchor_taper_m r_taper = 2.0 (T24.1); no gate
  B-both   both
The person prior is unchanged (anchor = centre, no T24.1 parameters). S3: the ORACLE-S3 rebuilt with the stored T-21 unit's
provenance, which must have the stored artifact ID (= column B's S3), as in D-53 step 2.
Beside them (stored, not re-run): B-tune = column B (the stored T-21 `full_camera` unit; D-53 step 2 showed its payload
equals the B-tune rebuild on all 116 cameras) and A (the stored T-21 `base` unit).
Evaluation: N4 against the stored T-21 BL-6 references, label group G1, A5.2 oracle association, summed counts; overall
and by viewpoint (as `d2_position_contribution.py`).
Position error (forklift, D1 definitions, `d1_anchor_angle.py`): estimate minus the simulator footprint centre of the
oracle track's identity; |error|; median, P95 (linear interpolation) and the shares above 1, 2 and 10 m.
Availability (D-41; T24.2 (e)): object-frames by class and viewpoint: numeric position; resolution limit (s > s_max);
no floor intersection; lost point (CR-034 reading (a)); other null.
CR-034 size: lost object-frames, and the pair-frames whose clearance_state would change under reading (b).
"""
from __future__ import annotations

import json
import os
import resource
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
OUT = __import__("pathlib").Path(os.environ.get("D54B_OUT", str(ROOT / "out/m1b/v2t24/b")))  # D54B_OUT: runtime estimate only
STATUS = "diagnostic, tuning subset, not a reported result"
BL = "BL-6"
CONTRACT = "E-1.2.25"
S_MAX = 0.1  # D-54 ruling 2, selected, not frozen
D_M, R_TAPER_M = 1.00, 2.0  # D-54 ruling 1 (SDG prior), selected, not frozen
RUNS = {"B-T24.2": {"gate": True, "shift": False}, "B-T24.1": {"gate": False, "shift": True}, "B-both": {"gate": True, "shift": True}}
OUTLIER_M = (1.0, 2.0, 10.0)


def run_config(cfg, gate: bool, shift: bool):
    """The S4 configuration of one run: the v1 base `SubstrateConfig` with the T24 parameters of the run."""
    from rq1.ids import core
    from rq1.substrate import builder
    priors = dict(cfg.priors)
    if shift:
        priors["forklift"] = dict(priors["forklift"], anchor="box_bottom_centre", anchor_offset_m=D_M, anchor_taper_m=R_TAPER_M)
    prior_ids = {k: core.make_id("fpp", v) for k, v in priors.items()}
    new = builder.SubstrateConfig(**{**cfg.__dict__, "priors": priors, "prior_ids": prior_ids, "s_max": S_MAX if gate else None})
    gcf_record = {"geometry": "full_camera", "footprint_prior_ids": sorted(prior_ids.values())}
    if gate:
        gcf_record["s_max_m_per_px"] = S_MAX
    return new, core.make_id("gcf", gcf_record), gcf_record


def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def _save(art, origin) -> str:
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    return art.artifact_id


def cr034_counts(s3, s4, calibration, s_max) -> dict:
    """Lost object-frames; those whose carried-forward pixel would be gated or miss the floor; the pair-frames now
    `unmeasurable_occluded` that reading (b) would make `unmeasurable_geometry_failure`."""
    from rq1.substrate import geometry
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3.tables["track"]}
    lost, flagged = 0, set()
    for p in s3.tables["track_point"]:
        if p["state"] != "lost":
            continue
        lost += 1
        s = geometry.floor_resolution(calibration, tuple(p["foot_point_px"]))
        if s is None or geometry.resolution_gated(s, s_max):
            flagged.add((by_local[p["track_nk"][1]], p["frame_index"]))
    pows = {p["pow_id"]: p for p in s4.tables["pow"]}
    flips = 0
    for r in s4.tables["pair_series"]:
        if r["clearance_state"] != "unmeasurable_occluded":
            continue
        pw = pows[r["pow_id"]]
        if (pw["person_track_id"], r["frame_index"]) in flagged or (pw["forklift_track_id"], r["frame_index"]) in flagged:
            flips += 1
    return {"lost_object_frames": lost, "lost_gated_or_no_floor": len(flagged), "pair_frames_occluded_to_geometry_failure_under_b": flips}


def run_camera(args):  # pragma: no cover - driver
    rec, prov = args
    from rq1.events import s5
    from rq1.substrate import builder
    rec_path = OUT / "cam" / f"{rec}.json"
    if rec_path.exists():
        return rec, "skipped", {}
    ctx = m.Context("sdg")
    unit = json.loads((ROOT / "out/m1a/run1/sdg" / rec / "base.json").read_text())
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    t0 = time.time()
    data = m.load(ctx, rec)
    s3, _, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], (unit["code_commit"], unit["environment_digest"]))
    if s3.artifact_id != unit["s3"]:
        raise RuntimeError(f"{rec}: rebuilt ORACLE-S3 {s3.artifact_id} != stored {unit['s3']}")
    if data.calibration is None:
        raise RuntimeError(f"{rec}: no calibration")
    record, base_cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    out = {"rec_id": rec, "status": STATUS, "code_commit": prov[0], "environment_digest": prov[1], "contract": CONTRACT,
           "preregistration": "docs/preregistration_FROZEN.md, version 1 (base values); T24 values: D-54 v2 candidates, selected, not frozen",
           "s3": s3.artifact_id, "runs": {}, "seconds": {"load_s3": round(time.time() - t0, 1)}}
    for name, opt in RUNS.items():
        t1 = time.time()
        cfg, gcf, gcf_record = run_config(base_cfg, **opt)
        s4 = builder.SubstrateBuilder().build(data.s1, s3, {}, data.calibration, cfg, _spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3.artifact_id,)))
        c5 = m.s5_config(ctx, BL, m.S4_BASE, m.S5_BASE)
        s5a = s5.build(data.s1, s4, c5, _spec("S5", prov, (s5.config_id(c5),), (s4.artifact_id,)))
        out["runs"][name] = {**opt, "geometry_config": gcf_record, "gcf": gcf, "s4": _save(s4, origin), "s5": {BL: _save(s5a, origin)}}
        if opt["gate"]:
            out["runs"][name]["cr034"] = cr034_counts(s3, s4, data.calibration, S_MAX)
        out["seconds"][name] = round(time.time() - t1, 1)
    out["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 20, 1)  # macOS: bytes
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(rec_path, out)
    return rec, "done", out["seconds"]


# ------------------------------------------------------------------------------------------------------------- evaluation

def _load(art_id, root):
    from rq1.schema import files
    d = root / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}


def availability_category(row: dict) -> str:
    """One object_state row -> its D-41 / T24.2 (e) availability row."""
    if row["x_m"] is not None:
        return "position"
    if "floor_resolution_m_per_px" in row:
        reason = row["floor_resolution_m_per_px_null_reason"]
        if row["floor_resolution_m_per_px"] is not None:
            return "resolution_limit"  # numeric s with a null position: s > s_max
        if reason == "not_observable":
            return "no_floor_intersection"
        if reason == "not_applicable" and row["evidence_state"] == "lost":
            return "lost"
    if row["evidence_state"] == "lost":
        return "lost"
    return "other_null"


def forklift_errors(s4: dict, trk_key: dict, cam) -> list[float]:
    import math
    out = []
    for r in s4["object_state"]:
        if r["x_m"] is None or r["track_id"] not in trk_key:
            continue
        key = trk_key[r["track_id"]]
        if cam.classes[key] != "forklift":
            continue
        t = cam.truth.get((key, r["frame_index"]))
        if t is None:
            continue
        out.append(math.hypot(r["x_m"] - t[3], r["y_m"] - t[4]))
    return out


def evaluate_camera(rec):  # pragma: no cover - driver over stored artifacts
    import evaluate_pilot as ep
    from rq1.evaluation import association as assoc
    ev = ep.ev
    path = OUT / "eval" / f"{rec}.json"
    if path.exists():
        return rec, "skipped"
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    rec_ = json.loads((OUT / "cam" / f"{rec}.json").read_text())
    usable = sum(cam.support().values())
    refs, groups = ev.references(cam)
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    track_class = {t["trk_id"]: t["class"] for t in s3o["track"]}
    rows, _, _ = ev.association(s3o, trk_key)
    sup = {f: cam.support().get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    summ, _ = assoc.summarize(rows, sup)
    stored = ROOT / "out/m1a/run1/sdg/artifacts"
    cols = {"A (stored)": (base["s4"], base["s5"][BL], stored), "B-tune (stored B)": (fc["s4"], fc["s5"][BL], stored)}
    for name, r in rec_["runs"].items():
        cols[name] = (r["s4"], r["s5"][BL], OUT / "artifacts")
    out = {"rec_id": rec, "viewpoint": pc.viewpoint(cam.camera_name), "ev": {}, "forklift_error_m": {}, "availability": {}}
    for name, (a4, a5, root) in cols.items():
        s4 = _load(a4, root)
        events = ev.system_events(s4, _load(a5, root), rows, summ)
        out["ev"][name] = ev.ev_counts(refs, groups, events, usable)["counts"]
        if name != "A (stored)":
            out["forklift_error_m"][name] = forklift_errors(s4, trk_key, cam)
            avail = {}
            for r in s4["object_state"]:
                cls = track_class.get(r["track_id"], "other")
                cat = availability_category(r)
                avail.setdefault(cls, {}).setdefault(cat, 0)
                avail[cls][cat] += 1
            out["availability"][name] = avail
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, out)
    return rec, "done"


def error_summary(errors: list[float]) -> dict:
    from cr007_evidence import _q
    n = len(errors)
    return {"n": n, "median_m": _q(errors, 50), "p95_m": _q(errors, 95),
            **{f"share_gt_{int(t)}m": (sum(1 for e in errors if e > t) / n if n else None) for t in OUTLIER_M}}


def aggregate() -> dict:  # pragma: no cover
    import d2_position_contribution as d2
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "eval" / f"{r}.json").read_text()) for r in recs]
    runs = [json.loads((OUT / "cam" / f"{r}.json").read_text()) for r in recs]
    cols = [c for c in cams[0]["forklift_error_m"]]
    errors, avail = {}, {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        errors[view] = {col: error_summary([e for c in sub for e in c["forklift_error_m"][col]]) for col in cols}
        avail[view] = {}
        for col in cols:
            tot: dict = {}
            for c in sub:
                for cls, cats in c["availability"][col].items():
                    for cat, n in cats.items():
                        tot.setdefault(cls, {}).setdefault(cat, 0)
                        tot[cls][cat] += n
            avail[view][col] = {cls: {"object_frames": sum(v.values()), **dict(sorted(v.items())),
                                      **{f"share_{k}": v[k] / sum(v.values()) for k in sorted(v)}} for cls, v in sorted(tot.items())}
    cr034 = {}
    for name in ("B-T24.2", "B-both"):
        keys = runs[0]["runs"][name]["cr034"].keys()
        cr034[name] = {k: sum(r["runs"][name]["cr034"][k] for r in runs) for k in keys}
    return {"status": STATUS, "decision": "D-54 STEP 3", "contract": "E-1.2.25 (Appendix T T24); v1 base values otherwise",
            "cameras": len(cams), "baseline": BL, "label_group": "G1",
            "t24_values": {"s_max_m_per_px": S_MAX, "forklift_anchor": "box_bottom_centre", "anchor_offset_m": D_M, "anchor_taper_m": R_TAPER_M,
                           "person_prior": "unchanged (anchor centre, no T24.1 parameters)", "status": "D-54 v2 candidate values, selected, not frozen"},
            "matching": "N4 (frozen v1 S8 values), stored T-21 BL-6 references; summed counts as the pilot report",
            "runs": {"B-T24.2": "column B (oracle boxes, full_camera) with the T24.2 gate, s_max 0.1 m/px",
                     "B-T24.1": "column B with the T24.1 forklift centre shift, d 1.00 m, r_taper 2.0 m",
                     "B-both": "column B with both",
                     "B-tune (stored B)": "column B, stored T-21 full_camera unit (= the D-53 B-tune rebuild on all 116 cameras)",
                     "A (stored)": "column A (simulator positions for both), stored T-21 base unit"},
            "position_error_definition": "forklift: |estimate - simulator footprint centre| of the oracle track's identity (D1 definitions); "
                                         "median and P95 linear interpolation; shares above 1, 2 and 10 m",
            "availability_rows": {"position": "numeric position", "resolution_limit": "resolution limit (s > s_max)",
                                  "no_floor_intersection": "no floor intersection (floor_resolution null, not_observable)",
                                  "lost": "lost point (no position in E-1.2.24; CR-034 reading (a))", "other_null": "any other null position"},
            "cr034_size": cr034,
            "checks": {"s3_rebuilt_equals_stored": len(runs)},
            "code_commit": sorted({r["code_commit"] for r in runs}),
            "ev": d2.summarize(cams), "forklift_position_error": errors, "availability": avail}


def main():  # pragma: no cover
    import run_pilot as rp
    import v2_sets
    what = sys.argv[1]
    if what == "aggregate":
        p = ROOT / "research/m1b/d54_b_v2_tune.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tuning = v2_sets.tuning()
    recs = sys.argv[3:] or tuning
    assert set(recs) <= set(tuning), "tuning subset only (D-54 ruling 5)"
    if what == "run":
        prov = rp.provenance()
        jobs, fn = [(r, prov) for r in recs], run_camera
    elif what == "evaluate":
        jobs, fn = recs, evaluate_camera
    else:
        raise SystemExit(what)
    print(f"{what}: {len(jobs)} cameras, workers {workers}", flush=True)
    t0 = time.time()
    it = map(fn, jobs) if workers == 1 else Pool(workers, maxtasksperchild=1).imap_unordered(fn, jobs)
    for n, res in enumerate(it, 1):
        print(n, *res, f"elapsed {round(time.time() - t0)} s", flush=True)


if __name__ == "__main__":
    main()
