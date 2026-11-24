"""D-57 STEP 2: why do episodes split? Stored D-54 outputs only (no new run), C-v2 and B-both, the 116 tuning cameras.
Diagnostic, tuning subset, not a reported result.

  PYTHONPATH=src .venv/bin/python research/m1b/d57_split.py cameras [workers]   -> out/m1b/d57/split/<rec>.json
  PYTHONPATH=src .venv/bin/python research/m1b/d57_split.py aggregate           -> research/m1b/d57_split_diagnosis.json

Definitions (the D-50 / D-54 extent definitions, `extent_check.py`, `d54_c_v2.extent`; BL-6, label group G1):
- references: the assessable G1 T-21 references; episodes: every BL-6 episode of the S5 artifact, its identity pair as
  resolved for N4 (`association.event_pair` at the closest-approach frame; C-v2 the A5.2 association of the detector tracks,
  B-both the oracle association). An episode with no resolved pair covers no reference.
- an episode covers a reference if it has the reference's identity pair and temporal IoU > 0.
- for a reference covered by two or more episodes: the covering episodes in order of (t_start, t_end, pow_id,
  start_frame); each consecutive pair (a, b) is one split.
- mechanism: (i) a and b in the same POW (a lifecycle split, T9.7); (ii) different POWs of the same person and forklift
  tracks (a POW break), with or without `continuation_of_nk` on b; (iii) any other track (track fragmentation).
- gap: b.t_start_tl_s - a.t_end_tl_s (s; negative when they overlap) and b.start_frame - a.end_frame_excl (frames);
  frame rate 1 / decode_summary.delta_nom_s of the recording.
- inside the gap, mechanism (i) only (frames a.end_frame_excl .. b.start_frame - 1 of the POW):
  share of flag_series frames with T = 0, T unknown (2) and T = 1 (a window shorter than t_min, discarded);
  flags true on the last frame of a (P, X, C_any); clearance_m on the last frame of a and the first frame of b,
  categorised against d_p and d_pc with the providers' strict "<" (R2 P = clearance < d_p); the pair_series q_state of
  the gap frames (share sufficient; summary sufficient / insufficient / mixed).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402
from cr007_evidence import _q  # noqa: E402
from rq1.evaluation.matching import temporal_iou  # noqa: E402

m = pc.m
ROOT = pc.ROOT
STATUS = "diagnostic, tuning subset, not a reported result"
BL = "BL-6"
OUT = ROOT / "out/m1b/d57"
C_OUT = ROOT / "out/m1b/v2t24/c"
B_OUT = ROOT / "out/m1b/v2t24/b"
M1A_ART = ROOT / "out/m1a/run1/sdg/artifacts"
D_P, D_PC = m.S5_BASE["d_p"], m.S5_BASE["d_pc"]
SPLIT_CONFIGS = ("C-v2", "B-both")
MECHANISMS = ("i", "ii", "iii")
CLEARANCE = ("below_d_pc", "d_pc_to_d_p", "at_or_above_d_p", "null")


# ---------------------------------------------------------------------------------------------------- pure functions

def covering(ref: tuple, episodes: list[dict]) -> list[dict]:
    """ref: (id, pair, t0, t1). The same-pair episodes with temporal IoU > 0, in (t0, t1, pow_id, start_frame) order."""
    hits = [e for e in episodes if e["pair"] is not None and tuple(e["pair"]) == tuple(ref[1]) and temporal_iou((ref[2], ref[3]), (e["t0"], e["t1"])) > 0]
    return sorted(hits, key=lambda e: (e["t0"], e["t1"], e["pow_id"], e["start_frame"]))


def consecutive_pairs(ref: tuple, episodes: list[dict]) -> list[tuple[dict, dict]]:
    cov = covering(ref, episodes)
    return list(zip(cov, cov[1:]))


def mechanism(a: dict, b: dict) -> str:
    if a["pow_id"] == b["pow_id"]:
        return "i"
    if (a["person_track_id"], a["forklift_track_id"]) == (b["person_track_id"], b["forklift_track_id"]):
        return "ii"
    return "iii"


def gap(a: dict, b: dict) -> tuple[float, int]:
    return b["t0"] - a["t1"], b["start_frame"] - a["end_frame_excl"]


def clearance_category(c: float | None, d_p: float, d_pc: float) -> str:
    if c is None:
        return "null"
    return "below_d_pc" if c < d_pc else "d_pc_to_d_p" if c < d_p else "at_or_above_d_p"


def flags_true(row: dict) -> str:
    names = [n for n, k in (("P", "P"), ("X", "X"), ("C", "C_any")) if row[k] == 1]
    return "+".join(names) if names else "none"


def inside_gap(flags: list[dict], before: dict, clr_before: float | None, clr_after: float | None, q_states: list[str],
               d_p: float, d_pc: float) -> dict:
    n = len(flags)
    share = lambda v: (sum(1 for f in flags if f["T"] == v) / n) if n else None
    nq = len(q_states)
    suff = sum(1 for q in q_states if q == "sufficient")
    q_sum = "no_pair_frames" if not nq else "sufficient" if suff == nq else "insufficient" if suff == 0 else "mixed"
    return {"gap_flag_frames": n, "share_T0": share(0), "share_T_unknown": share(2), "share_T1": share(1),
            "flags_true_before": flags_true(before),
            "clearance_before_m": clr_before, "clearance_before": clearance_category(clr_before, d_p, d_pc),
            "clearance_after_m": clr_after, "clearance_after": clearance_category(clr_after, d_p, d_pc),
            "share_q_sufficient": (suff / nq) if nq else None, "q_state": q_sum}


def quantiles(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "median": None, "p75": None, "p90": None, "max": None}
    return {"n": len(values), "median": _q(values, 50), "p75": _q(values, 75), "p90": _q(values, 90), "max": max(values)}


# ---------------------------------------------------------------------------------------------------- stored artifacts

def load_art(art_id: str, root) -> tuple[dict, dict]:
    from rq1.schema import files
    d = root / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}, man


def camera_context(rec: str, config: str) -> dict:  # pragma: no cover - driver over stored artifacts
    """The stored D-54 S4 and S5 (BL-6) of one configuration, with the association that resolves event pairs."""
    import evaluate_pilot as ep
    from rq1.evaluation import association as assoc
    from rq1.schema import files
    ev = ep.ev
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    support = cam.support()
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    base = cam.units["base"]
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", base["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    if config == "C-v2":
        pipe = json.loads((C_OUT / "cam" / rec / "pipeline.json").read_text())
        if pipe["s1"] != m.Context("sdg").camera(rec)["s1"]:
            raise RuntimeError(f"{rec}: C-v2 S1 differs from the camera's S1")
        s3d, _ = load_art(pipe["s3"], C_OUT / "artifacts")
        rows, _, _ = ep.association_detector(s3d, ep.ref_boxes(s3o, trk_key, cam.classes))
        s4_id, s5_id, root = pipe["runs"]["C-v2"]["s4"], pipe["runs"]["C-v2"]["s5"][BL], C_OUT / "artifacts"
    else:
        rows, _, _ = ev.association(s3o, trk_key)
        if config == "B-both":
            r = json.loads((B_OUT / "cam" / f"{rec}.json").read_text())["runs"]["B-both"]
            s4_id, s5_id, root = r["s4"], r["s5"][BL], B_OUT / "artifacts"
        elif config == "A":
            s4_id, s5_id, root = base["s4"], base["s5"][BL], M1A_ART
        else:
            raise ValueError(config)
    summ, _ = assoc.summarize(rows, sup_all(rows))
    s4, man4 = load_art(s4_id, root)
    s5t, man5 = load_art(s5_id, root)
    refs, groups = ev.references(cam)
    s1dir = ROOT / f"out/t17_sdg/{m.Context('sdg').camera(rec)['s1']}"
    ds = files.read_table(str(s1dir / "decode_summary.parquet"), "decode_summary", m.A.SCHEMA_VERSION)[0]
    return {"rec": rec, "viewpoint": pc.viewpoint(cam.camera_name), "cam": cam, "rows": rows, "summ": summ, "refs": refs, "groups": groups,
            "usable": sum(support.values()), "s4": s4, "man4": man4, "s4_id": s4_id, "s5": s5t, "man5": man5, "s5_id": s5_id,
            "s1": {"frame": cam.frames, "coverage_segment": cam.coverage}, "fps": 1.0 / ds["delta_nom_s"]}


def episodes_of(s4: dict, s5: dict, rows, summ) -> list[dict]:
    from rq1.evaluation import association as assoc
    pows = {p["pow_id"]: p for p in s4["pow"]}
    out = []
    for x in s5.get("episode", []):
        pw = pows[x["pow_id"]]
        pair, _ = assoc.event_pair(rows, summ, pw["person_track_id"], pw["forklift_track_id"], x["closest_approach_frame"])
        out.append({"pow_id": x["pow_id"], "person_track_id": pw["person_track_id"], "forklift_track_id": pw["forklift_track_id"],
                    "pair": tuple(pair) if pair else None, "t0": x["t_start_tl_s"], "t1": x["t_end_tl_s"], "start_frame": x["start_frame"],
                    "end_frame_excl": x["end_frame_excl"], "continuation": x["continuation_of_nk"] is not None})
    return out


def g1_refs(refs, groups) -> list[tuple]:
    return [(r.ref_event_id, tuple(r.pair), r.t_onset, r.t_offset) for r in refs if r.assessable and "G1" in groups[r.ref_event_id]]


def split_records(ctx: dict, config: str) -> dict:  # pragma: no cover - driver over stored artifacts
    s4, s5 = ctx["s4"], ctx["s5"]
    eps = episodes_of(s4, s5, ctx["rows"], ctx["summ"])
    pows = {p["pow_id"]: p for p in s4["pow"]}
    pow_id_of_nk = {(p["person_track_id"], p["forklift_track_id"], p["start_frame"]): p["pow_id"] for p in s4["pow"]}
    flags = {(f["pow_id"], f["frame_index"]): f for f in s5.get("flag_series", [])}
    pair_rows = {(pow_id_of_nk[tuple(r["pow_nk"])], r["frame_index"]): r for r in s4["pair_series"]}
    out, n2 = [], 0
    for ref in g1_refs(ctx["refs"], ctx["groups"]):
        pairs = consecutive_pairs(ref, eps)
        if pairs:
            n2 += 1
        for a, b in pairs:
            mech = mechanism(a, b)
            gs, gf = gap(a, b)
            rec = {"ref_id": ref[0], "mechanism": mech, "gap_s": gs, "gap_frames": gf, "fps": ctx["fps"], "b_continuation_of_nk": b["continuation"],
                   "a_pow_end_reason": pows[a["pow_id"]]["end_reason"]}
            if mech == "ii":
                rec["b_pow_continues_a_pow"] = pows[b["pow_id"]].get("continuation_of_id") == a["pow_id"]
            if mech == "i":
                pid = a["pow_id"]
                frames = range(a["end_frame_excl"], b["start_frame"])
                fl = [flags[(pid, k)] for k in frames if (pid, k) in flags]
                q = [pair_rows[(pid, k)]["q_state"] for k in frames if (pid, k) in pair_rows]
                last, first = a["end_frame_excl"] - 1, b["start_frame"]
                rec["inside"] = inside_gap(fl, flags[(pid, last)], pair_rows[(pid, last)]["clearance_m"], pair_rows[(pid, first)]["clearance_m"],
                                           q, D_P, D_PC)
            out.append(rec)
    return {"references_with_2plus_episodes": n2, "splits": out}


def camera(rec: str) -> tuple[str, str]:  # pragma: no cover - driver
    path = OUT / "split" / f"{rec}.json"
    if path.exists():
        return rec, "skipped"
    res = {"rec_id": rec, "status": STATUS, "configs": {}}
    for config in SPLIT_CONFIGS:
        ctx = camera_context(rec, config)
        res["viewpoint"] = ctx["viewpoint"]
        res["configs"][config] = split_records(ctx, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, res)
    return rec, "done"


# ---------------------------------------------------------------------------------------------------- aggregation

def summarize_splits(splits: list[dict]) -> dict:
    by_mech = Counter(s["mechanism"] for s in splits)
    out = {"splits": len(splits), "by_mechanism": {k: by_mech.get(k, 0) for k in MECHANISMS},
           "share_by_mechanism": {k: (by_mech.get(k, 0) / len(splits)) if splits else None for k in MECHANISMS}, "gap": {}}
    for k in MECHANISMS:
        sub = [s for s in splits if s["mechanism"] == k]
        out["gap"][k] = {"seconds": quantiles([s["gap_s"] for s in sub]), "frames": quantiles([s["gap_frames"] for s in sub]),
                         "b_with_continuation_of_nk": sum(1 for s in sub if s["b_continuation_of_nk"]),
                         "a_pow_end_reason": dict(sorted(Counter(s["a_pow_end_reason"] for s in sub).items()))}
        if k == "ii":
            out["gap"][k]["b_pow_continues_a_pow"] = sum(1 for s in sub if s.get("b_pow_continues_a_pow"))
    i = [s for s in splits if s["mechanism"] == "i"]
    fr = [s["gap_frames"] for s in i]
    out["mechanism_i"] = {
        "fps": sorted({round(s["fps"], 6) for s in i}),
        "gap_frames_at_most": {str(g): sum(1 for f in fr if f <= g) for g in (5, 15, 30, 60)},
        "mean_share_T0": _mean([s["inside"]["share_T0"] for s in i]), "mean_share_T_unknown": _mean([s["inside"]["share_T_unknown"] for s in i]),
        "mean_share_T1": _mean([s["inside"]["share_T1"] for s in i]),
        "gaps_with_any_T0": sum(1 for s in i if (s["inside"]["share_T0"] or 0) > 0),
        "gaps_with_T1_inside": sum(1 for s in i if (s["inside"]["share_T1"] or 0) > 0),
        "flags_true_before": dict(sorted(Counter(s["inside"]["flags_true_before"] for s in i).items())),
        "clearance_before": {c: sum(1 for s in i if s["inside"]["clearance_before"] == c) for c in CLEARANCE},
        "clearance_after": {c: sum(1 for s in i if s["inside"]["clearance_after"] == c) for c in CLEARANCE},
        "q_state_in_gap": dict(sorted(Counter(s["inside"]["q_state"] for s in i).items())),
        "mean_share_q_sufficient": _mean([s["inside"]["share_q_sufficient"] for s in i])}
    return out


def _mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "split" / f"{r}.json").read_text()) for r in recs]
    stored = json.load(open(ROOT / "research/m1b/d54_c_v2_tune.json"))["tuning_116"]["all"]["C-v2"]["extent"]["references_with_2plus_episodes"]
    res = {"status": STATUS, "decision": "D-57 STEP 2", "baseline": BL, "label_group": "G1", "cameras": len(cams),
           "source": "stored D-54 artifacts (out/m1b/v2t24/c, out/m1b/v2t24/b); no new run",
           "definitions": __doc__.split("Definitions", 1)[1].strip(), "d_p_m": D_P, "d_pc_m": D_PC, "configs": {}}
    for config in SPLIT_CONFIGS:
        n2 = sum(c["configs"][config]["references_with_2plus_episodes"] for c in cams)
        res["configs"][config] = {"references_with_2plus_episodes": n2}
        for view in ("all", "ceiling", "eye_level"):
            sub = [s for c in cams if view == "all" or c["viewpoint"] == view for s in c["configs"][config]["splits"]]
            res["configs"][config][view] = summarize_splits(sub)
    res["checks"] = {"c_v2_references_with_2plus_episodes_equals_d54": res["configs"]["C-v2"]["references_with_2plus_episodes"] == stored,
                     "d54_value": stored}
    if not res["checks"]["c_v2_references_with_2plus_episodes_equals_d54"]:
        raise SystemExit(f"STOP: C-v2 references with 2+ episodes {res['configs']['C-v2']['references_with_2plus_episodes']} != D-54 {stored}")
    return res


def main():  # pragma: no cover
    import v2_sets
    what = sys.argv[1]
    if what == "aggregate":
        p = ROOT / "research/m1b/d57_split_diagnosis.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    if what == "cameras":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        recs = sys.argv[3:] or v2_sets.tuning()
        assert set(recs) <= set(v2_sets.tuning()), "tuning subset only (D-57 ruling 8)"
        it = map(camera, recs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap_unordered(camera, recs)
        for n, res in enumerate(it, 1):
            print(n, *res, flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
