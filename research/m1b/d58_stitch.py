"""D-58 STEP 3: T25.1 stitching selection on the 116 tuning cameras, by tracking measures only (like D-55).
Diagnostic, tuning subset, not a reported result. The winner is selected, not frozen.

  PYTHONPATH=src .venv/bin/python research/m1b/d58_stitch.py estimate              (2 cameras)
  PYTHONPATH=src .venv/bin/python research/m1b/d58_stitch.py run [workers] [rec ...] -> out/m1b/d58/stitch/<rec>.json
  PYTHONPATH=src .venv/bin/python research/m1b/d58_stitch.py aggregate              -> research/m1b/d58_stitch_grid.json

Input per camera: the D-56 package tracks (the stored D-54 detector S3 of `out/m1b/v2t24/c`), with T24 on: the floor
position of a track point is the `object_state` x_m, y_m of the stored C-v2 S4 (T24.2 gate and T24.1 shift; AR-69 item 9).
No detection, no tracker run, no S4+ here.

Grid: T_s {1, 2, 3, 5} s x r_g {0.5, 1, 2} m; v_max person 2.5 m/s, forklift 4.0 m/s; k_img 1.0 (fixed design values);
plus "off". Stitching runs per class over both classes (T25.1 b: same class).

Measures per configuration (D-55 definitions, `v2_tracker_measures`, applied to stitched identities): IDF1 per class
(system identities = stitched identities; boxes = every S3 point; references = reference-visible boxes, iou_cm 0.5),
fragments per identity (primary: tracked points; distinct stitched identities matched to a reference identity, mean
over covered identities), point precision per class (tracked points matched / tracked points), and links accepted.
Check: with stitching off the measures equal the stored D-55 grid result of the package (forklift) and of the person job
on every camera (counts excepted: they describe the tracker log, not the points).

Rule (pre-declared, D-58 STEP 3): guard point precision per class >= 0.95; objective forklift IDF1 + person IDF1; keep
configurations within 0.01 of the best; then fewer forklift fragments per identity, then smaller T_s, then smaller r_g.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
C_OUT = ROOT / "out/m1b/v2t24/c"
OUT = __import__("pathlib").Path(os.environ.get("D58_OUT", str(ROOT / "out/m1b/d58")))  # D58_OUT: runtime estimate only
STATUS = "diagnostic, tuning subset, not a reported result"
PACKAGE = "trc_7flfpx52d2siiljxkqwcorr7nz"  # D-56
T_S = (1.0, 2.0, 3.0, 5.0)
R_G = (0.5, 1.0, 2.0)
V_MAX = {"person": 2.5, "forklift": 4.0}  # design values (D-58 STEP 3), not fitted
K_IMG = 1.0
GUARD, WITHIN, ROUNDING = 0.95, 0.01, 1e-12
CLASSES = ("person", "forklift")


def grid() -> list[dict]:
    out = [{"name": "off", "params": None}]
    for t in T_S:
        for r in R_G:
            out.append({"name": f"Ts{t:g}_rg{r:g}", "params": {"stitch_max_gap_s": t, "stitch_v_max_mps": dict(V_MAX), "stitch_r_gate_m": r,
                                                               "stitch_img_gate": K_IMG}})
    return out


def measures_units(units: dict, refs: dict, refs_clipped: dict, frames: list[int]) -> dict:
    """`v2_tracker_measures.measures` on S3 points grouped by unit (stitched identity, or track with stitching off).
    units: unit label -> [(frame_index, state, box, score)] (score: the detection's score on tracked points, 0 on predicted).
    A unit's label is the smallest tracker ID among its member tracks, so that with stitching off the labels, and with them
    every tie order, are those of `measures` (the tracker IDs)."""
    import idf1 as idf
    import v2_tracker_measures as vm
    import zs_match as zm
    by_frame = defaultdict(list)
    for uid, pts in units.items():
        for p in pts:
            by_frame[p[0]].append((uid, p))
    sys_frames = {i: ({uid: tuple(p[2]) for uid, p in v}, {}) for i, v in by_frame.items()}
    for i, v in refs.items():
        sys_frames.setdefault(i, ({}, {}))[1].update({k: tuple(b) for k, b in v})
    id1 = idf.idf1(sys_frames, vm.IOU_CM)
    out = {"idf1": {k: id1[k] for k in ("IDTP", "IDFP", "IDFN", "reference_boxes", "system_boxes", "identities", "tracks")}}
    refs_n = 0
    cov = dict.fromkeys(vm.VARIANTS, 0)
    npts, nmatch = dict.fromkeys(vm.VARIANTS, 0), dict.fromkeys(vm.VARIANTS, 0)
    frag = {v: defaultdict(set) for v in vm.VARIANTS}
    for i in frames:
        rs = refs_clipped.get(i, [])
        refs_n += len(rs)
        ps = sorted(by_frame.get(i, []), key=lambda x: x[0])
        for v in vm.VARIANTS:
            use = [(uid, p) for uid, p in ps if v == "all" or p[1] == "tracked"]
            mm = zm.match([b for _, b in rs], [(p[2], p[3]) for _, p in use])
            cov[v] += len(mm)
            npts[v] += len(use)
            nmatch[v] += len(mm)
            for ri, dj, _ in mm:
                frag[v][rs[ri][0]].add(use[dj][0])
    idents = sorted({k for v in refs_clipped.values() for k, _ in v}, key=str)
    out["coverage"] = {"references": refs_n, **{f"matched_{v}": cov[v] for v in vm.VARIANTS}}
    out["precision"] = {**{f"points_{v}": npts[v] for v in vm.VARIANTS}, **{f"points_matched_{v}": nmatch[v] for v in vm.VARIANTS}}
    out["fragments"] = {str(k): {v: len(frag[v].get(k, ())) for v in vm.VARIANTS} for k in idents}
    out["counts"] = {"tracks": len(units), "tracked": sum(1 for v in units.values() for p in v if p[1] == "tracked"),
                     "predicted": sum(1 for v in units.values() for p in v if p[1] == "predicted"), "runs_bridged": 0, "longest_bridged": 0}
    return out


def camera_inputs(rec: str) -> dict:  # pragma: no cover - driver over stored artifacts
    import d54_c_v2 as c
    import run_pilot as rp
    import v2_tracker_grid as g
    from rq1.tracking import stitching
    ctx = m.Context("sdg")
    _, s1, _ = rp.load_s1(ctx, rec)
    pipe = json.loads((C_OUT / "cam" / rec / "pipeline.json").read_text())
    s3 = c._load(pipe["s3"], C_OUT / "artifacts")
    s4 = c._load(pipe["runs"]["C-v2"]["s4"], C_OUT / "artifacts")
    floor = {(r["track_id"], r["frame_index"]): (r["x_m"], r["y_m"]) for r in s4["object_state"] if r["x_m"] is not None}
    s2_id, art_dir = g.s2_of(rec)
    score = {d["det_id"]: d["score"] for d in g.load_tables(art_dir, s2_id)["detection"]}
    refs_all, camo, ep = g.references(rec)
    ds = next(d for d in s1["decode_summary"])
    recording = s1["frame"][0]["recording_id"]
    frames = {f["frame_index"]: f for f in s1["frame"] if f["eligible"] and f["recording_id"] == recording}
    own = [cv for cv in s1["coverage_segment"] if cv.get("recording_id") == recording]
    coverage = [cv for cv in s1["coverage_segment"] if cv["timeline_id"] == own[0]["timeline_id"] and cv["camera_id"] == own[0]["camera_id"]]
    refs, clipped = {}, {}
    for cls in CLASSES:
        r = {i: [(k, bb) for k, cc, bb in v if cc == cls] for i, v in refs_all.items()}
        refs[cls] = r
        clipped[cls] = {i: [(k, cb) for k, cb in ((k, ep.ev_clip(bb, ds["width_px"], ds["height_px"])) for k, bb in v) if cb is not None] for i, v in r.items()}
    tracks = stitching.tracks_of(s3)
    cls_of = {t["trk_id"]: t["class"] for t in s3["track"]}
    pts = {t["trk_id"]: [] for t in s3["track"]}
    trk_of = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    for p in s3["track_point"]:
        sc = score[p["detection_id"]] if p["state"] == "tracked" else 0.0
        pts[trk_of[p["track_nk"][1]]].append((p["frame_index"], p["state"], list(p["bbox_xyxy_px"]), sc))
    tid = {trk_of[int(local)]: int(v[1]) for local, v in pipe["local_map"].items()}
    return {"rec": rec, "viewpoint": pc.viewpoint(camo.camera_name), "s3_id": pipe["s3"], "tid": tid, "frames": frames, "coverage": coverage, "floor": floor,
            "tracks": tracks, "cls_of": cls_of, "points": {k: sorted(v) for k, v in pts.items()}, "refs": refs, "clipped": clipped,
            "eligible": sorted(frames), "s3": s3}


def run_camera(rec: str) -> tuple[str, str, float]:  # pragma: no cover - driver over stored artifacts
    import v2_tracker_grid as g
    from rq1.tracking import stitching
    path = OUT / "stitch" / f"{rec}.json"
    if path.exists():
        return rec, "skipped", 0.0
    t0 = time.time()
    x = camera_inputs(rec)
    nk = stitching.natural_keys(x["s3"])
    res = {"rec_id": rec, "viewpoint": x["viewpoint"], "status": STATUS, "s3": x["s3_id"], "configs": {}}
    for cfg in grid():
        if cfg["params"] is None:
            unit_of, accepted = {t: t for t in x["points"]}, []
        else:
            params = stitching.params_from(cfg["params"])
            accepted = stitching.links(x["tracks"], x["frames"], x["coverage"], params, x["floor"])
            unit_of = stitching.stitch_ids(stitching.chains(list(x["points"]), accepted), nk)
        row = {"links": {c: sum(1 for a in accepted if x["cls_of"][a["a"]] == c) for c in CLASSES},
               "links_by_gate": {gt: sum(1 for a in accepted if a["gate"] == gt) for gt in ("floor", "image")}}
        for cls in CLASSES:
            label: dict[str, int] = {}
            for t in x["points"]:
                if x["cls_of"][t] == cls:
                    label[unit_of[t]] = min(label.get(unit_of[t], x["tid"][t]), x["tid"][t])
            units = defaultdict(list)
            for t, pts in x["points"].items():
                if x["cls_of"][t] == cls:
                    units[label[unit_of[t]]] += pts
            row[cls] = measures_units(dict(units), x["refs"][cls], x["clipped"][cls], x["eligible"])
        res["configs"][cfg["name"]] = row
    stored = json.loads((g.GRID_DIR / f"{rec}.json").read_text())
    strip = lambda d: {k: v for k, v in d.items() if k != "counts"}
    res["off_reproduces_d55"] = {"person": strip(res["configs"]["off"]["person"]) == strip(stored["person"]),
                                 "forklift": strip(res["configs"]["off"]["forklift"]) == strip(stored["configs"][PACKAGE])}
    if not all(res["off_reproduces_d55"].values()):
        raise SystemExit(f"STOP: {rec}: stitching off does not reproduce the stored D-55 measures {res['off_reproduces_d55']}")
    res["seconds"] = round(time.time() - t0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, res)
    return rec, "done", res["seconds"]


def pool_cls(parts: list[dict]) -> dict:
    import v2_tracker_measures as vm
    p = vm.pool(parts)
    return {"idf1": p["idf1"], "IDTP": p["IDTP"], "IDFP": p["IDFP"], "IDFN": p["IDFN"], "precision": p["tracked"]["precision"],
            "fragments_per_identity": p["tracked"]["fragments_per_identity"], "identities_covered": p["tracked"]["identities_covered"],
            "identities_two_or_more": p["tracked"]["identities_two_or_more"], "coverage": p["tracked"]["coverage"],
            "secondary_all_points": {k: p["all"][k] for k in ("precision", "fragments_per_identity", "coverage")}, "system_identities": p["counts"]["tracks"]}


def summarize(cams: list[dict]) -> dict:
    out = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if view == "all" or c["viewpoint"] == view]
        out[view] = {"cameras": len(sub)}
        for cfg in grid():
            n = cfg["name"]
            row = {c: pool_cls([x["configs"][n][c] for x in sub]) for c in CLASSES}
            row["links"] = {c: sum(x["configs"][n]["links"][c] for x in sub) for c in CLASSES}
            row["links_by_gate"] = {gt: sum(x["configs"][n]["links_by_gate"][gt] for x in sub) for gt in ("floor", "image")}
            row["objective"] = row["forklift"]["idf1"] + row["person"]["idf1"]
            out[view][n] = row
    return out


def select(table: dict) -> dict:
    """The pre-declared D-58 STEP 3 rule on the pooled 116-camera values (`summarize(...)["all"]`). "off" takes part."""
    names = [c["name"] for c in grid()]
    params = {c["name"]: c["params"] for c in grid()}
    guarded = [n for n in names if all(table[n][c]["precision"] >= GUARD - ROUNDING for c in CLASSES)]
    best = max(table[n]["objective"] for n in guarded)
    kept = [n for n in guarded if table[n]["objective"] >= best - WITHIN - ROUNDING]
    key = lambda n: (table[n]["forklift"]["fragments_per_identity"], params[n]["stitch_max_gap_s"] if params[n] else 0.0,
                     params[n]["stitch_r_gate_m"] if params[n] else 0.0)
    chosen = min(kept, key=key)
    return {"guard_point_precision": GUARD, "guarded": guarded, "best_objective": best, "within": WITHIN, "kept": kept,
            "order": "fewer forklift fragments per identity, then smaller T_s, then smaller r_g", "chosen": chosen, "chosen_params": params[chosen],
            "status": "selected under D-58, not frozen"}


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "stitch" / f"{r}.json").read_text()) for r in recs]
    table = summarize(cams)
    return {"status": STATUS, "decision": "D-58 STEP 3", "contract": "E-1.2.26 (Appendix T T25.1)", "tracker_package": PACKAGE,
            "input": "stored D-54 detector S3 (D-56 package), floor positions from the stored C-v2 S4 object_state (T24 on)",
            "grid": {"T_s_s": list(T_S), "r_g_m": list(R_G), "v_max_mps": V_MAX, "k_img": K_IMG, "v_max_k_img_status": "fixed design values (D-58)"},
            "measures": "D-55 definitions (v2_tracker_measures) on stitched identities; primary variant tracked points; IDF1 at iou_cm 0.5 over every S3 point",
            "checks": {"off_reproduces_d55": sum(all(c["off_reproduces_d55"].values()) for c in cams), "cameras": len(cams)},
            "runtime_s": round(sum(c["seconds"] for c in cams), 1), "selection": select(table["all"]), "tuning_116": table,
            "caveat_d56": "The package accepts forklift detections down to score 0.05. Point precision was measured on synthetic SDG data only and is "
                          "not known for real footage."}


def main():  # pragma: no cover
    import v2_sets
    what = sys.argv[1]
    tuning = v2_sets.tuning()
    if what == "estimate":
        rows = []
        for rec in (tuning[0], tuning[-1]):
            _, _, s = run_camera(rec)
            rows.append({"rec_id": rec, "seconds": s})
        per = sum(r["seconds"] for r in rows) / len(rows)
        print(json.dumps({"rows": rows, "per_camera_s": per, "total_116_h_serial": round(per * 116 / 3600, 3)}))
        return
    if what == "run":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        recs = sys.argv[3:] or tuning
        assert set(recs) <= set(tuning), "tuning subset only (D-58)"
        it = map(run_camera, recs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap_unordered(run_camera, recs)
        for n, r in enumerate(it, 1):
            print(n, *r, flush=True)
        return
    if what == "aggregate":
        p = ROOT / "research/m1b/d58_stitch_grid.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
