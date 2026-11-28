"""T-21 M1a validation run, phase 2 (S8 evaluation) from the phase-1 artifacts. Per camera, resumable.

  python research/m1a/evaluate_m1a.py <ds> <label> cameras [workers]   -> out/m1a/<label>/<ds>/<rec_id>/eval.pkl.gz
  python research/m1a/evaluate_m1a.py <ds> <label> aggregate           -> research/m1a/results_<ds>.json

Oracle path (M1a): system tracks are the ORACLE-S3 tracks; association (A5.2) of their boxes with the reference-visible boxes
(T17.6: the tracked oracle points) at iou_cm, eps_amb; pair resolution of a system event by `association.event_pair`.
References: T21 (BL-6 on complete truth, base values; G1 only; assessable per T21.3); the same reference IDs for every
sweep grid point (T21.4). Metric choices that the contract leaves to representation are AR-59 items; readings that could
change a number are flagged there for review.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import m1a_common as m  # noqa: E402
from rq1.evaluation import association as assoc  # noqa: E402
from rq1.evaluation import completeness as cm  # noqa: E402
from rq1.evaluation import estimators as est  # noqa: E402
from rq1.evaluation import event_metrics as em  # noqa: E402
from rq1.evaluation import gv  # noqa: E402
from rq1.evaluation import matching as mt  # noqa: E402
from rq1.ids import core  # noqa: E402
from rq1.schema import files  # noqa: E402
from rq1.substrate import geometry  # noqa: E402

ROOT = m.ROOT
S8 = {"iou_m": 0.3, "iou_cm": 0.5, "eps_amb": 0.02, "k_kf_s": 1.0, "B": 2000, "seed": 2026111402}  # pre-registration v1 section 4.4
V0 = {"sdg": "art_wiaoelxnrzaqb2ii44esa47k3f", "smartspaces": "art_rvcgsenmz4onjnq5jbfu4n6wax"}
LABELS = ("O", "H", "PC", "NM", "UD", "CT", "IE")
BANDS = [(None, 0.0), *zip(m.BAND_EDGES_M, m.BAND_EDGES_M[1:]), (m.BAND_EDGES_M[-1], None)]


def out_dir(label, ds) -> Path:
    return ROOT / "out/m1a" / label / ds


def load_art(label, ds, art_id) -> dict:
    d = out_dir(label, ds) / "artifacts" / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}


def oracle_keys(visible: dict[str, list[int]]) -> dict[int, str]:
    """ORACLE-S3 local id -> object key: camera_tracks keeps the objects with a visible frame (T20.1), s3_truth numbers
    them 1.. in str order (AR-59 item 1; checked against the track class below)."""
    return {i: k for i, k in enumerate(sorted((k for k, v in visible.items() if v), key=str), 1)}


def reference_keys(truth_rows) -> dict[int, str]:
    """T21 reference S3 local id -> object key: every object with a pose on an eligible frame, numbered 1.. in str order."""
    return {i: k for i, k in enumerate(sorted({r[0] for r in truth_rows}, key=str), 1)}


def track_map(s3: dict, keys: dict[int, str], classes: dict[str, str]) -> dict[str, str]:
    out = {}
    for t in s3["track"]:
        key = keys[t["track_local_id"]]
        if classes[key] != t["class"]:
            raise RuntimeError(f"track {t['track_local_id']} class {t['class']} != truth class of {key}")
        out[t["trk_id"]] = key
    return out


class Camera:
    def __init__(self, ds, label, rec):
        self.ds, self.label, self.rec = ds, label, rec
        cam = m.Context(ds).camera(rec)
        d = out_dir(label, ds) / rec
        self.units = {u: json.loads((d / f"{u}.json").read_text()) for u in ("base", "full_camera", "reference", "sweeps") if (d / f"{u}.json").exists()}
        with gzip.open(d / "truth.pkl.gz", "rb") as f:
            t = pickle.load(f)
        self.truth_rows, self.visible = t["truth_table"], t["visible_frames"]
        self.classes = {r[0]: r[1] for r in self.truth_rows}
        self.truth = {(r[0], r[2]): r for r in self.truth_rows}
        self.camera_name, self.run = cam["camera"], cam["run"]
        s1dir = ROOT / f"out/t17_{ds}/{cam['s1']}"
        self.frames = files.read_table(str(s1dir / "frame.parquet"), "frame", m.A.SCHEMA_VERSION)
        self.coverage = files.read_table(str(s1dir / "coverage_segment.parquet"), "coverage_segment", m.A.SCHEMA_VERSION)
        self.timeline = self.coverage[0]["timeline_id"]
        self.eligible = {f["frame_index"]: f for f in self.frames if f["eligible"]}
        rw = files.read_table(str(ROOT / "out/prereg" / V0[ds] / "reference_window.parquet"), "reference_window", m.A.SCHEMA_VERSION)
        self.windows = sorted((w for w in rw if w["timeline_id"] == self.timeline), key=lambda w: w["window_index"])
        self.window = self.windows[0]  # SDG: the only window of the camera

    def support(self, window=None) -> dict[int, float]:
        """Clipped eligible support per frame inside the window (E-1.2.1 section 3.4); the guard is not part of it."""
        window = window or self.window
        a, b = window["t_start_tl_s"], window["t_end_tl_s"]
        out = {}
        for i, f in self.eligible.items():
            if f["support_s"] and f["support_start_tl_s"] is not None:
                s = max(0.0, min(f["support_start_tl_s"] + f["support_s"], b) - max(f["support_start_tl_s"], a))
                if s > 0:
                    out[i] = s
        return out


def association(s3: dict, oracle_trk: dict[str, str]):
    """A5.2 on the oracle path: system boxes = ORACLE-S3 points (not lost); reference boxes = its tracked points (T17.6)."""
    cls = {t["trk_id"]: t["class"] for t in s3["track"]}
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    frames: dict[int, tuple[list, list]] = {}
    track_class: dict[int, dict[str, str]] = {}
    for p in s3["track_point"]:
        trk = by_local[p["track_nk"][1]]
        if p["state"] != "lost":
            frames.setdefault(p["frame_index"], ([], []))[0].append(assoc.Box(trk, cls[trk], tuple(p["bbox_xyxy_px"])))
            track_class.setdefault(p["frame_index"], {})[trk] = p["evidence_class"]
        if p["state"] == "tracked":
            frames.setdefault(p["frame_index"], ([], []))[1].append(assoc.Box(oracle_trk[trk], cls[trk], tuple(p["bbox_xyxy_px"])))
    rows = assoc.associate(frames, S8["iou_cm"], S8["eps_amb"])
    return rows, frames, track_class


def references(cam: Camera) -> tuple[list[mt.Reference], dict[str, frozenset]]:
    refs, groups = [], {}
    for r in cam.units["reference"]["references"]:
        rid = core.make_id("rin", {"rec_id": cam.rec, "person": r["person_key"], "forklift": r["forklift_key"], "start_frame": r["start_frame"],
                                   "end_frame_excl": r["end_frame_excl"], "reference_s5": cam.units["reference"]["s5"]})
        refs.append(mt.Reference(rid, r["t_start_tl_s"], r["t_end_tl_s"], (r["person_key"], r["forklift_key"]), r["assessable"]))
        groups[rid] = frozenset({"G1"}) if (r["lbl_O"] or r["lbl_H"] or r["lbl_PC"]) else frozenset()  # T21.2: G1 only
    return refs, groups


def system_events(s4: dict, s5: dict, rows, summaries) -> list[mt.SystemEvent]:
    episodes = {(e["pow_id"], e["start_frame"]): e for e in s5.get("episode", [])}
    pows = {p["pow_id"]: p for p in s4["pow"]}
    out = []
    for ev in s5.get("candidate_event", []):
        if ev["scenario"] != "S_VIEW":
            continue
        ep = episodes[tuple(ev["member_episode_nks"][0])]
        pw = pows[ep["pow_id"]]
        pair, _ = assoc.event_pair(rows, summaries, pw["person_track_id"], pw["forklift_track_id"], ep["closest_approach_frame"])
        out.append(mt.SystemEvent(ev["member_episode_nks"][0], ev["evt_id"], ev["t_onset_tl_s"], ev["t_end_tl_s"], pair,
                                  frozenset(x for x in LABELS if ev[f"lbl_{x}"])))
    return out


def ev_counts(refs, groups, events, usable_s):
    records = mt.match_window(refs, events, "G1", S8["iou_m"], "rule_conformance", groups)
    c = em.window_counts(records, usable_s)
    return {"counts": c.__dict__, "localization": [{k: r[k] for k in ("onset_error_s", "offset_error_s", "temporal_iou")} for r in records if r["match_type"] == "matched"],
            "match_types": {t: sum(1 for r in records if r["match_type"] == t) for t in sorted({r["match_type"] for r in records})},
            "unobservable_references": sum(1 for r in records if r["match_type"] == "unobservable_reference")}


def episode_set(s4: dict, s5: dict, trk_key: dict[str, str]) -> list[tuple]:
    pows = {p["pow_id"]: p for p in s4["pow"]}
    out = []
    for e in s5.get("episode", []):
        pw = pows[e["pow_id"]]
        out.append(((trk_key[pw["person_track_id"]], trk_key[pw["forklift_track_id"]]), e["t_start_tl_s"], e["t_end_tl_s"],
                    frozenset(x for x in LABELS if e[f"lbl_{x}"])))
    return sorted(out, key=lambda x: (x[0], x[1]))


def run_summary(s5: dict) -> dict:
    eps = s5.get("episode", [])
    return {"episodes": len(eps), "events": sum(1 for e in s5.get("candidate_event", []) if e["scenario"] == "S_VIEW"),
            "duration_s": sum(e["span_s"] for e in eps), "labels": {x: sum(1 for e in eps if e[f"lbl_{x}"]) for x in LABELS}}


def evaluate_camera(args):
    ds, label, rec, *dest = args  # optional 4th element: another output path (AR-60 equivalence check)
    path = Path(dest[0]) if dest else out_dir(label, ds) / rec / "eval.pkl.gz"
    if path.exists():
        return rec, "skipped"
    cam = Camera(ds, label, rec)
    if "reference" not in cam.units:
        return evaluate_camera_without_reference(cam, path)
    if len(cam.windows) != 1:
        raise NotImplementedError("EV-M with several windows per camera")
    support = cam.support()
    usable = sum(support.values())
    base, fc, ref = cam.units["base"], cam.units["full_camera"], cam.units["reference"]
    s3 = load_art(label, ds, base["s3"])
    trk_key = track_map(s3, oracle_keys(cam.visible), cam.classes)
    rows, _, track_class = association(s3, trk_key)
    summaries, missed = assoc.summarize(rows, {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}})
    refs, groups = references(cam)
    out = {"rec_id": rec, "camera": cam.camera_name, "run": cam.run, "stratum": cam.window["stratum_id"], "leakage_group": cam.window["leakage_group_id"],
           "window_id": cam.window["rwn_id"], "weight": cam.window["weight"], "usable_s": usable,
           "references": {"n": len(refs), "assessable": sum(r.assessable for r in refs), "g1": sum(1 for r in refs if "G1" in groups[r.ref_event_id])},
           "association": {"missed_identities": missed, "status": {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r["status"] for r in rows})}}}
    # EV-M per configuration, simulator_truth geometry (pre-registration section 7)
    s4 = load_art(label, ds, base["s4"])
    out["ev"], out["runs"], base_sets = {}, {}, {}
    for bl, art in base["s5"].items():
        s5 = load_art(label, ds, art)
        out["ev"][bl] = ev_counts(refs, groups, system_events(s4, s5, rows, summaries), usable)
        out["runs"][bl] = run_summary(s5)
        base_sets[bl] = episode_set(s4, s5, trk_key)
        # EV-M3 inputs (T10.7(a, d)): episodes of the window by onset, with their span as support; POW support = POW spans (AR-59 item 8)
        a0, a1 = cam.window["t_start_tl_s"], cam.window["t_end_tl_s"]
        out["ev"][bl]["ev_m3"] = ([(frozenset(x for x in LABELS if e[f"lbl_{x}"]), e["span_s"]) for e in s5.get("episode", []) if a0 <= e["t_start_tl_s"] < a1],
                                  sum(p["span_s"] for p in s4["pow"]))
    # Completeness CM-01 .. CM-10 (N6, T12.4, T13.1), simulator_truth run
    ref_s3, ref_s4 = load_art(label, ds, ref["s3"]), load_art(label, ds, ref["s4"])
    ref_trk = track_map(ref_s3, reference_keys(cam.truth_rows), cam.classes)
    ref_visible = {}
    trk_of_local = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    for p in s3["track_point"]:
        if p["state"] == "tracked":
            key = trk_key[trk_of_local[p["track_nk"][1]]]
            ref_visible.setdefault(p["frame_index"], {})[key] = cam.classes[key]
    ref_present = {}
    for key, cls, i, *_ in cam.truth_rows:
        ref_present.setdefault(i, set()).add(key)
    ref_moving = {}
    for r in ref_s4["object_state"]:
        key = ref_trk[r["track_id"]]
        if cam.classes[key] != "person" and r["speed_mps"] is not None and r["speed_mps"] > m.S4_BASE["v_min"]:
            ref_moving.setdefault(r["frame_index"], set()).add(key)
    ref_clear = {}  # CM-06 reference geometry: T21 reference pair-series clearance (AR-59 item 3)
    for r in ref_s4["pair_series"]:
        pair = (ref_trk[r["pow_nk"][0]], ref_trk[r["pow_nk"][1]])
        if r["clearance_m"] is not None:
            ref_clear.setdefault(pair, {})[r["frame_index"]] = r["clearance_m"]
    series = {}
    for r in s4["pair_series"]:
        series.setdefault(tuple(r["pow_nk"]), {})[r["frame_index"]] = r
    pows = [{"person_track": p["person_track_id"], "forklift_track": p["forklift_track_id"],
             "frames": {i: r["evidence_class"] for i, r in series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])].items() if i in support},
             "clearance_state": {i: r["clearance_state"] for i, r in series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])].items()},
             "clearance": {i: r["clearance_m"] for i, r in series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])].items()},
             "calibration_tier": "simulator_truth"} for p in s4["pow"]]
    w = cm.WindowFrames(support=support, ref_visible={f: v for f, v in ref_visible.items() if f in support},
                        ref_present={f: v for f, v in ref_present.items() if f in support}, assoc=[r for r in rows if r["frame_index"] in support],
                        track_class={f: v for f, v in track_class.items() if f in support}, pows=pows, ref_moving=ref_moving, ref_class=dict(cam.classes))
    comp = {}
    for basis in sorted(cm.BASES):
        comp[("CM-01", basis)] = list(cm.cm_object(w, "person", basis).values())
        comp[("CM-02", basis)] = list(cm.cm_object(w, "forklift", basis, moving_only=True).values())
        comp[("CM-03", basis)] = list(cm.cm03(w, None, basis).values())
        comp[("CM-04", basis)] = [cm.cm04(w, None, basis)]
        comp[("CM-05", basis)] = [cm.cm05(w, basis)]
        c6 = cm.cm06(w, basis, BANDS, ref_clear)
        comp[("CM-06", basis)] = [{"pair": "|".join(k), **v} for k, v in c6["pairs"].items()]
        comp[("CM-07", basis)] = [cm.cm07(w, basis)["summary"]]
        comp[("CM-08", basis)] = list(cm.cm08(w, basis).values())
        comp[("CM-09", basis)] = [cm.cm09(w, basis)]
    comp[("CM-10", "basis-independent")] = list(cm.cm10(w).values())
    out["cm"] = comp
    out["gv"] = gv_camera(cam, label, ds, s3, trk_key, fc, base)
    out["sweeps"] = sweeps_camera(cam, label, ds, refs, groups, base_sets, usable, s4)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as f:
        pickle.dump(out, f)
    os.replace(tmp, path)
    return rec, "done"


def evaluate_camera_without_reference(cam: Camera, path: Path):
    """SmartSpaces (D-39): no T21 reference unit. CM per V0 window without the reference-geometry metrics (CM-02 needs
    reference-moving frames, CM-06 reference clearance); GV on the full_camera run; no EV-M, no sweeps."""
    ds, label = cam.ds, cam.label
    base, fc = cam.units["base"], cam.units["full_camera"]
    s3 = load_art(label, ds, base["s3"])
    trk_key = track_map(s3, oracle_keys(cam.visible), cam.classes)
    rows, _, track_class = association(s3, trk_key)
    s4 = load_art(label, ds, base["s4"])
    trk_of_local = {t["track_local_id"]: t["trk_id"] for t in s3["track"]}
    ref_visible, ref_present = {}, {}
    for p in s3["track_point"]:
        if p["state"] == "tracked":
            key = trk_key[trk_of_local[p["track_nk"][1]]]
            ref_visible.setdefault(p["frame_index"], {})[key] = cam.classes[key]
    for key, cls, i, *_ in cam.truth_rows:
        ref_present.setdefault(i, set()).add(key)
    series = {}
    for r in s4["pair_series"]:
        series.setdefault(tuple(r["pow_nk"]), {})[r["frame_index"]] = r
    out = {"rec_id": cam.rec, "camera": cam.camera_name, "run": cam.run, "windows": [], "runs": {}}
    for bl, art in base["s5"].items():
        out["runs"][bl] = run_summary(load_art(label, ds, art))
    for win in cam.windows:
        support = cam.support(win)
        pows = []
        for p in s4["pow"]:
            fr = series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])]
            frames = {i: r["evidence_class"] for i, r in fr.items() if i in support}
            if frames:
                pows.append({"person_track": p["person_track_id"], "forklift_track": p["forklift_track_id"], "frames": frames,
                             "clearance_state": {i: fr[i]["clearance_state"] for i in frames}, "clearance": {i: fr[i]["clearance_m"] for i in frames},
                             "calibration_tier": "simulator_truth"})
        w = cm.WindowFrames(support=support, ref_visible={f: v for f, v in ref_visible.items() if f in support},
                            ref_present={f: v for f, v in ref_present.items() if f in support}, assoc=[r for r in rows if r["frame_index"] in support],
                            track_class={f: v for f, v in track_class.items() if f in support}, pows=pows, ref_class=dict(cam.classes))
        comp = {}
        for basis in sorted(cm.BASES):
            comp[("CM-01", basis)] = list(cm.cm_object(w, "person", basis).values())
            comp[("CM-03", basis)] = list(cm.cm03(w, None, basis).values())
            comp[("CM-04", basis)] = [cm.cm04(w, None, basis)]
            comp[("CM-05", basis)] = [cm.cm05(w, basis)]
            comp[("CM-07", basis)] = [cm.cm07(w, basis)["summary"]]
            comp[("CM-08", basis)] = list(cm.cm08(w, basis).values())
            comp[("CM-09", basis)] = [cm.cm09(w, basis)]
        comp[("CM-10", "basis-independent")] = list(cm.cm10(w).values())
        out["windows"].append({"window_id": win["rwn_id"], "stratum": win["stratum_id"], "leakage_group": win["leakage_group_id"],
                               "weight": win["weight"], "usable_s": sum(support.values()), "cm": comp})
    del s4, series
    out["stratum"], out["leakage_group"] = cam.windows[0]["stratum_id"], cam.windows[0]["leakage_group_id"]
    out["gv"] = gv_camera(cam, label, ds, s3, trk_key, fc, base)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as f:
        pickle.dump(out, f)
    os.replace(tmp, path)
    return cam.rec, "done"


def _speeds(s4: dict, trk_key) -> dict:
    return {(trk_key[r["track_id"]], r["frame_index"]): r["speed_mps"] for r in s4["object_state"] if r["speed_mps"] is not None}


def gv_camera(cam: Camera, label, ds, s3, trk_key, fc, base) -> dict:
    """GV-01, GV-04 .. GV-08 on the full_camera run (pre-registration section 7); GV-03 is in the sweeps."""
    if fc.get("s4") is None:
        return {"null_reason": fc.get("s4_null_reason", "uncalibrated")}
    s4 = load_art(label, ds, fc["s4"])
    state = {(trk_key[t], i): c for (t, i), c in {(r["track_id"], r["frame_index"]): r["evidence_class"] for r in s4["object_state"]}.items()}
    out = {"gv01": [], "gv05_cov": [], "gv04": [], "gv06_pairs": [], "gv06_p": [], "gv07": {}, "gv08": []}
    pos = {}
    for r in s4["object_state"]:
        key = trk_key[r["track_id"]]
        if r["x_m"] is None:
            continue
        t = cam.truth.get((key, r["frame_index"]))
        if t is None:
            continue
        pos[(key, r["frame_index"])] = (r["x_m"], r["y_m"], r["yaw_rad"])
        out["gv01"].append((cam.classes[key], r["evidence_class"], r["x_m"] - t[3], r["y_m"] - t[4]))
        out["gv05_cov"].append(r["pos_cov_m2"])
    # GV-04: clearance with the prior footprint minus clearance with the simulator 3D box footprint, both at the
    # full_camera positions and yaw of the pair-frame (AR-59 item 5).
    pows = {p["pow_id"]: p for p in s4["pow"]}
    prior_r, (L0, W0) = m.S4_BASE["person_radius_m"], m.FORK_PRIOR_M[ds]
    times = {i: f["t_tl_s"] for i, f in cam.eligible.items()}
    by_pow = {}
    for r in s4["pair_series"]:
        pkey, fkey = trk_key[r["pow_nk"][0]], trk_key[r["pow_nk"][1]]
        by_pow.setdefault(tuple(r["pow_nk"]), []).append(r)
        if r["clearance_state"] == "measured" and r["clearance_m"] is not None:
            p, f, t = pos.get((pkey, r["frame_index"])), pos.get((fkey, r["frame_index"])), cam.truth.get((fkey, r["frame_index"]))
            if p and f and t and t[6] is not None:
                if f[2] is None:
                    box = geometry.disc_clearance(p[:2], prior_r, f[:2], geometry.circumscribed_radius(t[6], t[7]))
                else:
                    box = geometry.clearance(p[:2], prior_r, f[:2], f[2], t[6], t[7])
                out["gv04"].append((f"{t[6]:.2f}x{t[7]:.2f}", r["evidence_class"], r["clearance_m"] - box))
            if r["image_gap_norm"] is not None:
                out["gv06_pairs"].append((r["image_gap_norm"], r["clearance_m"]))
    for nk, rs in by_pow.items():  # GV-08 on each POW's frames in time order
        rs = sorted(rs, key=lambda r: r["frame_index"])
        ser = [(times[r["frame_index"]], r["clearance_m"] if r["clearance_state"] == "measured" else None) for r in rs]
        for k, r in enumerate(rs):
            pred = next((e for e in r["predicted"] if e["motion_model_id"] == "constant_velocity"), None)
            if pred is None:
                continue
            real = gv.realized_min(ser, k, pred["horizon_s"])
            if real is not None:
                out["gv08"].append((r["evidence_class"], pred["pred_min_clearance_m"] - real))
    # GV-06 P disagreement: BL-2 (R1-P) against BL-3 (R2-P) on the full_camera run
    f2, f3 = load_art(label, ds, fc["s5"]["BL-2"])["flag_series"], load_art(label, ds, fc["s5"]["BL-3"])["flag_series"]
    p3 = {(r["pow_id"], r["frame_index"]): r["P"] for r in f3}
    out["gv06_p"] = [(r["P"], p3[(r["pow_id"], r["frame_index"])]) for r in f2 if (r["pow_id"], r["frame_index"]) in p3]
    # GV-07: full_camera speed minus simulator_truth speed at the same w_v (AR-59 item 6)
    st_speed = {0.5: _speeds(load_art(label, ds, base["s4"]), trk_key)}
    bundle_path = out_dir(label, ds) / cam.rec / "sweeps.pkl.gz"
    if bundle_path.exists():  # the simulator_truth speeds at other w_v come from the sweeps (none on SmartSpaces in v1)
        with gzip.open(bundle_path, "rb") as fh:
            bundle = pickle.load(fh)
        for w_v in (0.33, 1.0):
            st_speed[w_v] = _speeds(bundle[f"w_v={w_v}"]["s4"].tables, trk_key)
        del bundle
    fc_speed = {0.5: _speeds(s4, trk_key), **{float(k): _speeds(load_art(label, ds, v), trk_key) for k, v in fc["s4_w_v"].items() if float(k) in st_speed}}
    for w_v in sorted(st_speed):
        out["gv07"][w_v] = [(cam.classes[k[0]], state.get(k), v - st_speed[w_v][k]) for k, v in fc_speed[w_v].items() if k in st_speed[w_v]]
    return out


def sweeps_camera(cam: Camera, label, ds, refs, groups, base_sets, usable, s4_base) -> dict:
    """Per grid point and configuration: run summary, episode set (pair keys), EV G1 counts against the base reference
    (T21.4); GV-03 clearance differences for the footprint grid points."""
    with gzip.open(out_dir(label, ds) / cam.rec / "sweeps.pkl.gz", "rb") as fh:
        bundle = pickle.load(fh)
    base_clear = {(tuple(r["pow_nk"]), r["frame_index"]): r["clearance_m"] for r in s4_base["pair_series"] if r["clearance_m"] is not None}
    out = {}
    for tag, b in bundle.items():
        s3 = b["s3"].tables if b["s3"] is not None else load_art(label, ds, cam.units["base"]["s3"])
        trk_key = track_map(s3, oracle_keys(cam.visible), cam.classes)
        rows, _, _ = association(s3, trk_key)
        summaries, _ = assoc.summarize(rows, {f: 1.0 for f in {r["frame_index"] for r in rows}})
        s4 = b["s4"].tables if b["s4"] is not None else s4_base
        point = {"configs": {}}
        for bl, art in b["s5"].items():
            s5 = art.tables
            point["configs"][bl] = {"run": run_summary(s5), "episodes": episode_set(s4, s5, trk_key),
                                    "ev": ev_counts(refs, groups, system_events(s4, s5, rows, summaries), usable)["counts"]}
        if tag.startswith("fork_") or tag.startswith("person_radius"):
            point["d_clearance"] = [r["clearance_m"] - base_clear[(tuple(r["pow_nk"]), r["frame_index"])] for r in s4["pair_series"]
                                    if r["clearance_m"] is not None and (tuple(r["pow_nk"]), r["frame_index"]) in base_clear]
        out[tag] = point
    out["_base_episodes"] = base_sets
    return out


def main_cameras(ds, label, workers):
    need = ("base", "full_camera", "reference", "sweeps") if ds == "sdg" else ("base", "full_camera")
    recs = sorted(p.name for p in out_dir(label, ds).iterdir() if p.name.startswith("rec_") and all((p / f"{u}.json").exists() for u in need)
                  and (p / "truth.pkl.gz").exists())
    print(f"evaluate {ds} {label}: {len(recs)} cameras", flush=True)
    jobs = [(ds, label, r) for r in recs]
    it = map(evaluate_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap_unordered(evaluate_camera, jobs)
    for n, (rec, status) in enumerate(it, 1):
        print(n, rec, status, flush=True)


if __name__ == "__main__":
    ds, label, what = sys.argv[1:4]
    if what == "cameras":
        main_cameras(ds, label, int(sys.argv[4]) if len(sys.argv) > 4 else 1)
    else:
        import aggregate_m1a
        aggregate_m1a.main(ds, label)
