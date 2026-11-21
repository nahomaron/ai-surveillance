"""T-25p detector-path pilot (D-45 item 3), phase 2: S8 evaluation per camera, then aggregation. Main `.venv`.

  PYTHONPATH=src .venv/bin/python research/m1b/evaluate_pilot.py cameras [workers]   -> out/m1b/pilot/cam/<rec>/eval.pkl.gz
  PYTHONPATH=src .venv/bin/python research/m1b/evaluate_pilot.py aggregate           -> research/m1b/pilot_results.json
  PYTHONPATH=src .venv/bin/python research/m1b/evaluate_pilot.py cameras-cprime [workers] / aggregate-cprime
                                                                                    -> research/m1b/pilot_results_cprime.json
  (D-47 item 1: column C' only, from out/m1b/pilot/cam_cprime/; the same functions as column C)

Three columns on the same pilot cameras (D-45 item 3d):
  A  oracle path, simulator positions: T-21 `base` unit (ORACLE-S3 -> S4 simulator_truth -> S5)
  B  oracle boxes with full_camera geometry: T-21 `full_camera` unit (same ORACLE-S3 -> S4 full_camera -> S5)
  C  detector path: S2 YOLO-World -> S3 ByteTrack -> S4 full_camera -> S5 (`run_pilot.py`)
References: the stored T21 references of the camera (rule_conformance, G1, T21.3 assessability), unchanged.
Association (F.1 A5.2, iou_cm 0.5, eps_amb 0.02): system boxes = the column's S3 points (not lost); reference boxes = the
reference-visible boxes (T17.6: tracked ORACLE-S3 points), as in T-21 (`evaluate_m1a.association`). A and B share the
oracle association; C associates the detector tracks. Event pairs by `association.event_pair`; matching, EV counts and
completeness by the T-21 functions, unchanged.
Detection (frame level): every eligible pilot frame; references = the reference-visible boxes clipped to the image (the
probe's reference); detections = S2 rows (thresholds already applied); the probe matcher (`zs_match`, IoU >= 0.3).
Tracking: track_identity_summary statuses and switches (T-12), IDF1 (TrackEval port, `idf1.py`), per class, column C.
Position (D-41): B and C object_state rows with a position, error to the simulator position of the identity (B: the
oracle track's object; C: the identity matched to the track on that frame, A5.2 `matched`); availability by null reason.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402
sys.path.insert(0, str(pc.ROOT / "research/m1a"))
import aggregate_m1a as agg  # noqa: E402
import evaluate_m1a as ev  # noqa: E402
import idf1 as idf  # noqa: E402
import zs_match as zm  # noqa: E402
from rq1.evaluation import association as assoc  # noqa: E402
from rq1.evaluation import completeness as cm  # noqa: E402
from rq1.evaluation import event_metrics as em  # noqa: E402
from rq1.evaluation import matching as mt  # noqa: E402
from rq1.evaluation.event_metrics import WindowCounts  # noqa: E402
from rq1.schema import files  # noqa: E402

M1A_LABEL = "run1"
COLUMNS = ("A", "B", "C")
LABELS3 = ("O", "H", "PC")
CLASSES = ("person", "forklift")
CUTS_M = (1.0, 2.0, 5.0)


def load_pilot(art_id) -> dict:
    d = pc.OUT / "artifacts" / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], ev.m.A.SCHEMA_VERSION) for f in man["files"]}


def ref_boxes(s3o, trk_key, classes):
    """frame -> [(identity, class, box)] of the reference-visible boxes (T17.6)."""
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3o["track"]}
    out = defaultdict(list)
    for p in s3o["track_point"]:
        if p["state"] == "tracked":
            key = trk_key[by_local[p["track_nk"][1]]]
            out[p["frame_index"]].append((key, classes[key], tuple(p["bbox_xyxy_px"])))
    return out


def association_detector(s3c, refs_by_frame):
    cls = {t["trk_id"]: t["class"] for t in s3c["track"]}
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3c["track"]}
    frames: dict[int, tuple[list, list]] = {i: ([], [assoc.Box(k, c, b) for k, c, b in v]) for i, v in refs_by_frame.items()}
    track_class: dict[int, dict[str, str]] = {}
    for p in s3c["track_point"]:
        trk = by_local[p["track_nk"][1]]
        if p["state"] != "lost":
            frames.setdefault(p["frame_index"], ([], []))[0].append(assoc.Box(trk, cls[trk], tuple(p["bbox_xyxy_px"])))
            track_class.setdefault(p["frame_index"], {})[trk] = p["evidence_class"]
    return assoc.associate(frames, ev.S8["iou_cm"], ev.S8["eps_amb"]), frames, track_class


def label_counts(refs, ref_labels, events) -> dict:
    """D-40 item 5 per-label breakdown (as `ev_by_label.camera`)."""
    out = {}
    for lab in LABELS3:
        rs = [r for r in refs if lab in ref_labels[r.ref_event_id]]
        es = [e for e in events if lab in e.labels]
        rec_ = mt.match_window(rs, es, "any", ev.S8["iou_m"], "rule_conformance", {r.ref_event_id: frozenset({"any"}) for r in rs})
        kinds = [r["match_type"] for r in rec_]
        out[lab] = {"assessable": kinds.count("matched") + kinds.count("miss") + kinds.count("abstained_miss"), "matched": kinds.count("matched"),
                    "system": len(es)}
    return out


def pows_input(s4, support, tier):
    series = defaultdict(dict)
    for r in s4["pair_series"]:
        series[tuple(r["pow_nk"])][r["frame_index"]] = r
    out = []
    for p in s4["pow"]:
        fr = series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])]
        out.append({"person_track": p["person_track_id"], "forklift_track": p["forklift_track_id"],
                    "frames": {i: r["evidence_class"] for i, r in fr.items() if i in support},
                    "clearance_state": {i: r["clearance_state"] for i, r in fr.items()}, "clearance": {i: r["clearance_m"] for i, r in fr.items()},
                    "calibration_tier": tier})
    return out


def completeness(cam, support, rows, track_class, s4, tier, ref_visible, ref_present):
    w = cm.WindowFrames(support=support, ref_visible={f: v for f, v in ref_visible.items() if f in support},
                        ref_present={f: v for f, v in ref_present.items() if f in support}, assoc=[r for r in rows if r["frame_index"] in support],
                        track_class={f: v for f, v in track_class.items() if f in support}, pows=pows_input(s4, support, tier), ref_class=dict(cam.classes))
    out = {}
    for basis in sorted(cm.BASES):
        out[("CM-01", basis)] = list(cm.cm_object(w, "person", basis).values())
        out[("CM-03", basis)] = list(cm.cm03(w, None, basis).values())
        out[("CM-08", basis)] = list(cm.cm08(w, basis).values())
    return out


def positions(s4, identity_of, cam):
    """identity_of(track_id, frame) -> object key or None. Returns errors (class, evidence class, metres) and availability."""
    errors, avail = [], defaultdict(int)
    for r in s4["object_state"]:
        cls = "person" if r["track_id"] in identity_of.person_tracks else "forklift"
        avail[(cls, "position" if r["x_m"] is not None else f"null:{r['x_m_null_reason']}")] += 1
        if r["x_m"] is None:
            continue
        key = identity_of(r["track_id"], r["frame_index"])
        t = cam.truth.get((key, r["frame_index"])) if key is not None else None
        if t is None:
            avail[(cls, "position_without_matched_identity")] += 1
            continue
        errors.append((cls, r["evidence_class"], math.hypot(r["x_m"] - t[3], r["y_m"] - t[4])))
    return errors, dict(avail)


class Identity:
    def __init__(self, fn, person_tracks):
        self.fn, self.person_tracks = fn, person_tracks

    def __call__(self, track, frame):
        return self.fn(track, frame)


def detection_counts(dets, refs_by_frame, frames, w, h):
    out = {c: [0, 0, 0] for c in CLASSES}  # tp, references, detections
    by_frame = defaultdict(list)
    for d in dets:
        by_frame[d["frame_index"]].append(d)
    for i in frames:
        refs = [(c, ev_clip(b, w, h)) for _, c, b in refs_by_frame.get(i, [])]
        for c in CLASSES:
            rb = [b for cc, b in refs if cc == c and b is not None]
            db = [(d["bbox_xyxy_px"], d["score"]) for d in by_frame.get(i, []) if d["class"] == c]
            out[c][0] += len(zm.match(rb, db))
            out[c][1] += len(rb)
            out[c][2] += len(db)
    return out


def ev_clip(b, w, h):
    x1, y1, x2, y2 = max(0.0, b[0]), max(0.0, b[1]), min(float(w), b[2]), min(float(h), b[3])
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None


VARIANTS = {None: ("cam", "C"), "cprime": ("cam_cprime", "C'")}  # D-47 item 1: C' beside C, never replacing it


def evaluate_camera(rec, variant=None):
    cam_dir, det_col = VARIANTS[variant]
    path = pc.OUT / cam_dir / rec / "eval.pkl.gz"
    if path.exists():
        return rec, "skipped"
    cam = ev.Camera("sdg", M1A_LABEL, rec)
    pipe = json.loads((pc.OUT / cam_dir / rec / "pipeline.json").read_text())
    support = cam.support()
    usable = sum(support.values())
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    refs, groups = ev.references(cam)
    ref_labels = {ref.ref_event_id: frozenset(x for x in LABELS3 if r[f"lbl_{x}"]) for ref, r in zip(refs, cam.units["reference"]["references"])}
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3o = ev.load_art(M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    rows_o, _, tc_o = ev.association(s3o, trk_key)
    summ_o, _ = assoc.summarize(rows_o, sup_all(rows_o))
    refs_by_frame = ref_boxes(s3o, trk_key, cam.classes)
    s3c = load_pilot(pipe["s3"])
    rows_c, frames_c, tc_c = association_detector(s3c, refs_by_frame)
    summ_c, missed_c = assoc.summarize(rows_c, sup_all(rows_c))
    ref_visible = defaultdict(dict)
    for i, v in refs_by_frame.items():
        for k, c, _ in v:
            ref_visible[i][k] = c
    ref_present = defaultdict(set)
    for key, cls, i, *_ in cam.truth_rows:
        ref_present[i].add(key)
    detector_col = (load_pilot(pipe["s4"]), {bl: load_pilot(a) for bl, a in pipe["s5"].items()}, rows_c, summ_c, tc_c, "full_camera")
    if variant is None:
        cols = {"A": (ev.load_art(M1A_LABEL, "sdg", base["s4"]), {bl: ev.load_art(M1A_LABEL, "sdg", a) for bl, a in base["s5"].items()}, rows_o, summ_o, tc_o, "simulator_truth"),
                "B": (ev.load_art(M1A_LABEL, "sdg", fc["s4"]), {bl: ev.load_art(M1A_LABEL, "sdg", a) for bl, a in fc["s5"].items()}, rows_o, summ_o, tc_o, "full_camera"),
                "C": detector_col}
    else:
        cols = {det_col: detector_col}
    out = {"rec_id": rec, "camera": cam.camera_name, "viewpoint": pc.viewpoint(cam.camera_name), "stratum": cam.window["stratum_id"],
           "leakage_group": cam.window["leakage_group_id"], "usable_s": usable,
           "references": {"n": len(refs), "assessable": sum(r.assessable for r in refs), "g1": sum(1 for r in refs if "G1" in groups[r.ref_event_id])},
           "ev": {}, "labels": {}, "runs": {}, "cm": {}, "position": {}, "seconds": pipe["seconds"],
           "s2_detector_seconds": pipe["s2_detector_seconds"], "s2_wall_s": pipe["s2_wall_s"], "track_counts": pipe["track_counts"]}
    for col, (s4, s5s, rows, summ, tc, tier) in cols.items():
        out["ev"][col], out["labels"][col], out["runs"][col] = {}, {}, {}
        for bl, s5 in s5s.items():
            events = ev.system_events(s4, s5, rows, summ)
            out["ev"][col][bl] = ev.ev_counts(refs, groups, events, usable)
            out["labels"][col][bl] = label_counts(refs, ref_labels, events)
            out["runs"][col][bl] = ev.run_summary(s5)
        out["cm"][col] = completeness(cam, support, rows, tc, s4, tier, ref_visible, ref_present)
    # position accuracy and availability (D-41), B and C
    persons_o = {t["trk_id"] for t in s3o["track"] if t["class"] == "person"}
    if variant is None:
        out["position"]["B"] = positions(cols["B"][0], Identity(lambda t, i: trk_key[t], persons_o), cam)
    matched_c = {(r["track_id"], r["frame_index"]): r["physical_identity_id"] for r in rows_c if r["status"] == "matched"}
    persons_c = {t["trk_id"] for t in s3c["track"] if t["class"] == "person"}
    out["position"][det_col] = positions(cols[det_col][0], Identity(lambda t, i: matched_c.get((t, i)), persons_c), cam)
    # tracking (C): T-12 statuses and IDF1 per class
    cls_c = {t["trk_id"]: t["class"] for t in s3c["track"]}
    out["tracking"] = {}
    for c in CLASSES:
        ss = [s for s in summ_c if cls_c[s["track_id"]] == c]
        fr = {i: ({b.object_id: b.xyxy for b in sb if b.cls == c}, {b.object_id: b.xyxy for b in rb if b.cls == c}) for i, (sb, rb) in frames_c.items()}
        out["tracking"][c] = {"tracks": len(ss), "status": {s: sum(1 for x in ss if x["status"] == s) for s in ("one_to_one", "id_switch", "fragment", "unmatched_system")},
                              "n_switches": sum(x["n_switches"] for x in ss), "missed_identities": sum(1 for k in missed_c if cam.classes[k] == c),
                              "idf1": idf.idf1(fr, ev.S8["iou_cm"])}
    # detection, frame level (C)
    dets = load_pilot(pipe["s2"])["detection"]
    ds = files.read_table(str(pc.ROOT / f"out/t17_sdg/{pipe['s1']}/decode_summary.parquet"), "decode_summary", ev.m.A.SCHEMA_VERSION)[0]
    out["detection"] = detection_counts(dets, refs_by_frame, sorted(cam.eligible), ds["width_px"], ds["height_px"])
    # descriptive: kept detections by the ByteTrack default score bands (first stage and new tracks >= 0.25; second stage
    # only in (0.1, 0.25); never used <= 0.1), and how many became tracked points
    tcfg = pipe["tracker_config"]["params"]
    hi, lo = tcfg["track_high_thresh"], tcfg["track_low_thresh"]
    out["score_bands"] = {c: {"ge_high": sum(1 for d in dets if d["class"] == c and d["score"] >= hi),
                              "low_to_high": sum(1 for d in dets if d["class"] == c and lo < d["score"] < hi),
                              "le_low": sum(1 for d in dets if d["class"] == c and d["score"] <= lo),
                              "tracked_points": pipe["track_counts"][c]["tracked"]} for c in CLASSES}
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as f:
        pickle.dump(out, f)
    os.replace(tmp, path)
    return rec, "done"


# ---------------------------------------------------------------------------------------------------------------- aggregate

def _q(v, q):
    return float(em.percentile(v, q)) if v else None


def pos_summary(errs):
    if not errs:
        return {"n": 0}
    return {"n": len(errs), "median_m": _q(errs, 50), "p95_m": _q(errs, 95), **{f"share_gt_{int(c)}m": sum(1 for e in errs if e > c) / len(errs) for c in CUTS_M}}


def aggregate(variant=None) -> dict:
    cam_dir, det_col = VARIANTS[variant]
    cams = []
    for rec in (pc.OUT / cam_dir).iterdir():
        p = rec / "eval.pkl.gz"
        if p.exists():
            with gzip.open(p, "rb") as f:
                cams.append(pickle.load(f))
    cams.sort(key=lambda c: c["rec_id"])
    res = {"status": "experimental; synthetic (SDG); validation partition only; zero-shot detector; nothing validated",
           "contract": pc.CONTRACT, "preregistration": "version 1 (frozen), base values", "cameras": len(cams),
           "viewpoints": {v: sum(1 for c in cams if c["viewpoint"] == v) for v in ("ceiling", "eye_level")},
           "leakage_groups": len({c["leakage_group"] for c in cams}), "strata": sorted({c["stratum"] for c in cams}),
           "references": {k: sum(c["references"][k] for c in cams) for k in ("n", "assessable", "g1")}, "ev": {}, "labels": {}, "cm": {}, "position": {}}
    columns = list(cams[0]["ev"])  # A, B, C for the pilot; C' alone for the variant
    for col in columns:
        res["ev"][col], res["labels"][col] = {}, {}
        for bl in agg.CFG:
            wc = [WindowCounts(**c["ev"][col][bl]["counts"]) for c in cams]
            head = em.headline(wc)
            tot = {k: sum(getattr(x, k) for x in wc) for k in ("a", "m", "s", "m_s")}
            res["ev"][col][bl] = {"EV-M1": head["EV-M1"], "EV-M2": head["EV-M2"], "counts": tot,
                                  "EV-M1_target_b": agg._ci([(c["stratum"], c["leakage_group"], c["ev"][col][bl]["counts"]["a"], c["ev"][col][bl]["counts"]["m"]) for c in cams], "sdg")["target_b"],
                                  "EV-M2_target_b": agg._ci([(c["stratum"], c["leakage_group"], c["ev"][col][bl]["counts"]["s"], c["ev"][col][bl]["counts"]["m_s"]) for c in cams], "sdg")["target_b"],
                                  "unobservable_references": sum(c["ev"][col][bl]["unobservable_references"] for c in cams),
                                  "runs": {k: sum(c["runs"][col][bl][k] for c in cams) for k in ("episodes", "events")}}
            labs = {}
            for lab in LABELS3:
                a = sum(c["labels"][col][bl][lab]["assessable"] for c in cams)
                mm = sum(c["labels"][col][bl][lab]["matched"] for c in cams)
                s = sum(c["labels"][col][bl][lab]["system"] for c in cams)
                labs[lab] = {"assessable": a, "matched": mm, "system": s, "recall": mm / a if a else None, "precision": mm / s if s else None}
            res["labels"][col][bl] = labs
        res["cm"][col] = {}
        for key in sorted({k for c in cams for k in c["cm"][col]}):
            rows = [(c["stratum"], c["leakage_group"], r["denominator"], r["numerator"]) for c in cams for r in c["cm"][col][key]]
            st = agg._ratio(rows)
            st["target_b"] = agg._ci(rows, "sdg")["target_b"]
            res["cm"][col][" ".join(key)] = st
    for col in list(cams[0]["position"]):
        errs = defaultdict(list)
        avail = defaultdict(int)
        for c in cams:
            e, a = c["position"][col]
            for cls, evc, d in e:
                for key in (f"{cls}|{evc}", f"{cls}|all", "all|all"):
                    errs[key].append(d)
            for (cls, reason), n in a.items():
                avail[(cls, reason)] += n
        res["position"][col] = {"error": {k: pos_summary(v) for k, v in sorted(errs.items())}, "availability": {}}
        for cls in CLASSES:
            tot = sum(n for (c, r), n in avail.items() if c == cls and not r.startswith("position_without"))
            res["position"][col]["availability"][cls] = {"object_frames": tot, **{r: {"n": n, "share": n / tot if tot else None}
                                                                                   for (c, r), n in sorted(avail.items()) if c == cls}}
    res["detection"] = {}
    for v in ("all", "ceiling", "eye_level"):
        sub = [c for c in cams if v == "all" or c["viewpoint"] == v]
        res["detection"][v] = {cls: zm.summarize(sum(c["detection"][cls][0] for c in sub), sum(c["detection"][cls][1] for c in sub),
                                                 sum(c["detection"][cls][2] for c in sub)) for cls in CLASSES}
    res["tracking"] = {}
    for cls in CLASSES:
        t = {k: sum(c["tracking"][cls]["idf1"][k] for c in cams) for k in ("IDTP", "IDFP", "IDFN")}
        res["tracking"][cls] = {"tracks": sum(c["tracking"][cls]["tracks"] for c in cams),
                                "status": {s: sum(c["tracking"][cls]["status"][s] for c in cams) for s in ("one_to_one", "id_switch", "fragment", "unmatched_system")},
                                "n_switches": sum(c["tracking"][cls]["n_switches"] for c in cams),
                                "missed_identities": sum(c["tracking"][cls]["missed_identities"] for c in cams),
                                **t, "IDF1": t["IDTP"] / max(1.0, t["IDTP"] + 0.5 * t["IDFP"] + 0.5 * t["IDFN"])}
        res["tracking"][cls]["bridging"] = {k: sum(c["track_counts"][cls][k] for c in cams) for k in c["track_counts"][cls]}
    res["score_bands"] = {cls: {k: sum(c["score_bands"][cls][k] for c in cams) for k in ("ge_high", "low_to_high", "le_low", "tracked_points")} for cls in CLASSES}
    secs = defaultdict(float)
    for c in cams:
        for k, v in c["seconds"].items():
            secs[k] += v
        secs["s2_detector"] += c["s2_detector_seconds"]
        secs["s2_wall"] += c["s2_wall_s"]
    res["runtime_s"] = {k: round(v, 1) for k, v in sorted(secs.items())}
    return res


def _evaluate_cprime(rec):
    return evaluate_camera(rec, "cprime")


def main_cameras(workers, variant=None):
    cam_dir, _ = VARIANTS[variant]
    fn = evaluate_camera if variant is None else _evaluate_cprime
    recs = sorted(p.name for p in (pc.OUT / cam_dir).iterdir() if (p / "pipeline.json").exists())
    print(f"evaluate pilot ({cam_dir}): {len(recs)} cameras", flush=True)
    it = map(fn, recs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap_unordered(fn, recs)
    for n, (rec, status) in enumerate(it, 1):
        print(n, rec, status, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "cameras":
        main_cameras(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    elif sys.argv[1] == "cameras-cprime":
        main_cameras(int(sys.argv[2]) if len(sys.argv) > 2 else 1, "cprime")
    elif sys.argv[1] == "aggregate-cprime":
        r = aggregate("cprime")
        pc.write_json(pc.ROOT / "research/m1b/pilot_results_cprime.json", r)
        print("wrote research/m1b/pilot_results_cprime.json")
    else:
        r = aggregate()
        pc.write_json(pc.ROOT / "research/m1b/pilot_results.json", r)
        print("wrote research/m1b/pilot_results.json")
