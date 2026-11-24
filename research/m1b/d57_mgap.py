"""D-57 STEP 3: m_gap sweep on the 116 tuning cameras, S5 onward only, on the stored D-54 S4 artifacts.
Diagnostic, tuning subset, not a reported result.

  PYTHONPATH=src .venv/bin/python research/m1b/d57_mgap.py estimate                  (2 cameras; STOP above 2 h)
  PYTHONPATH=src .venv/bin/python research/m1b/d57_mgap.py run [workers] [rec ...]   -> out/m1b/d57/mgap/<rec>.json, artifacts
  PYTHONPATH=src .venv/bin/python research/m1b/d57_mgap.py aggregate                 -> research/m1b/d57_mgap_sweep.json

Grid: rule_configuration.lifecycle.m_gap_frames in {5 (v1), 15, 30, 60} (T9.7); every other value is the v1 base value
(`m1a_common.S5_BASE`, `S4_BASE`), BL-6. One rule_configuration ID per value: the v1 value keeps version_label
"preregistration-v1"; the others carry "D-57 diagnostic m_gap <n> (not frozen)" (AR-68).
Configurations (stored S4, never rebuilt; D-54):
  C-v2    detector path, D-56 package, T24 on   (out/m1b/v2t24/c, run C-v2)
  B-both  oracle boxes, full_camera, T24 on     (out/m1b/v2t24/b, run B-both)
  A       simulator positions                   (stored T-21 base unit, out/m1a/run1/sdg)
Check: at m_gap 5 the rebuilt S5 payload equals the stored D-54 / T-21 S5 payload (payload_sha256) on every camera.
Measures (N4, G1, the stored T-21 BL-6 references, as the pilot): EV-M1, EV-M2 with counts; system events, unmatched events;
D-50 extent measures (`d54_c_v2.extent`): references covered by two or more same-pair episodes, unmatched events by best
same-pair IoU band; T10.6 candidate-event counts per label (event_count_summary, recording scope).
Selection (pre-declared, C-v2, all 116 cameras): keep m_gap with EV-M1 >= EV-M1(5) - 0.02; among them the highest EV-M2;
EV-M2 within 0.005 of the highest is a tie, broken by the smaller m_gap. "Selected under D-57, not frozen".
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from multiprocessing import Pool
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import d57_split as sp  # noqa: E402
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
STATUS = sp.STATUS
BL = sp.BL
CONTRACT = "E-1.2.25"
OUT = __import__("pathlib").Path(os.environ.get("D57_OUT", str(ROOT / "out/m1b/d57")))  # D57_OUT: runtime estimate only
GRID = (5, 15, 30, 60)
V1_M_GAP = 5
CONFIGS = ("C-v2", "B-both", "A")
HEADLINE = "C-v2"
EV_M1_MARGIN, EV_M2_TIE, ROUNDING = 0.02, 0.005, 1e-12
LIMIT_H = 2.0


def p5(m_gap: int) -> dict:
    return {**m.S5_BASE, "m_gap": m_gap}


def version_label(m_gap: int) -> str:
    return "preregistration-v1" if m_gap == V1_M_GAP else f"D-57 diagnostic m_gap {m_gap} (not frozen)"


def s5_config(ctx, m_gap: int):
    return dataclasses.replace(m.s5_config(ctx, BL, m.S4_BASE, p5(m_gap)), version_label=version_label(m_gap))


def select(results: dict[int, tuple[float, float]]) -> dict:
    """results: m_gap -> (EV-M1, EV-M2) on the headline configuration. The D-57 pre-declared rule."""
    floor = results[V1_M_GAP][0] - EV_M1_MARGIN
    kept = sorted(g for g, (m1, _) in results.items() if m1 >= floor - ROUNDING)
    best = max(results[g][1] for g in kept)
    tied = [g for g in kept if results[g][1] >= best - EV_M2_TIE - ROUNDING]
    return {"ev_m1_floor": floor, "kept": kept, "best_ev_m2": best, "tied": tied, "chosen": min(tied)}


def label_counts(rows: list[dict]) -> dict:
    out: dict = {}
    for r in rows:
        if r["scope_type"] != "recording":
            continue
        k = f"{r['scenario']}|{r['label']}"
        out[k] = out.get(k, 0) + r["n_events"]
    return dict(sorted(out.items()))


def _save(art, origin) -> str:
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    return art.artifact_id


def run_camera(args) -> tuple[str, str, float]:  # pragma: no cover - driver over stored artifacts
    rec, prov = args
    import d54_c_v2 as c
    import evaluate_pilot as ep
    from rq1.events import s5
    path = OUT / "mgap" / f"{rec}.json"
    if path.exists():
        return rec, "skipped", 0.0
    t0 = time.time()
    mctx = m.Context("sdg")
    res = {"rec_id": rec, "status": STATUS, "code_commit": prov[0], "environment_digest": prov[1], "contract": CONTRACT, "configs": {}}
    for config in CONFIGS:
        ctx = sp.camera_context(rec, config)
        res["viewpoint"] = ctx["viewpoint"]
        s4 = SimpleNamespace(tables=ctx["s4"], spec=ctx["man4"]["spec"], artifact_id=ctx["s4_id"])
        rows = {}
        for g in GRID:
            cfg = s5_config(mctx, g)
            rcf = s5.config_id(cfg)
            art = s5.build(ctx["s1"], s4, cfg, m.Spec("S5", CONTRACT, prov[0], prov[1], (rcf,), (ctx["s4_id"],), {}))
            row = {"rule_configuration_id": rcf, "s4": ctx["s4_id"], "s5": _save(art, ctx["man4"]["data_origin"])}
            if g == V1_M_GAP:
                row["stored_s5"] = ctx["s5_id"]
                row["payload_equals_stored_s5"] = art.payload_sha256 == ctx["man5"]["payload_sha256"]
                row["rule_configuration_equals_stored"] = rcf in ctx["man5"]["spec"]["config_ids"]
                if not row["payload_equals_stored_s5"]:
                    raise SystemExit(f"STOP: {rec} {config}: S5 at m_gap 5 does not reproduce the stored S5 payload {ctx['s5_id']}")
            events = ep.ev.system_events(ctx["s4"], art.tables, ctx["rows"], ctx["summ"])
            row["counts"] = ep.ev.ev_counts(ctx["refs"], ctx["groups"], events, ctx["usable"])["counts"]
            row["extent"] = c.extent(ctx["refs"], ctx["groups"], events, ctx["s4"], art.tables, ctx["rows"], ctx["summ"])
            row["labels"] = label_counts(art.tables.get("event_count_summary", []))
            rows[str(g)] = row
        res["configs"][config] = rows
    res["seconds"] = round(time.time() - t0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    pc.write_json(path, res)
    return rec, "done", res["seconds"]


def summarize(cams: list[dict]) -> dict:
    import d54_c_v2 as c
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation.event_metrics import WindowCounts
    out: dict = {}
    for view in ("all", "ceiling", "eye_level"):
        sub = [x for x in cams if view == "all" or x["viewpoint"] == view]
        out[view] = {"cameras": len(sub)}
        for config in CONFIGS:
            out[view][config] = {}
            for g in GRID:
                rows = [x["configs"][config][str(g)] for x in sub]
                wc = [WindowCounts(**r["counts"]) for r in rows]
                h = em.headline(wc)
                t = {k: sum(getattr(w, k) for w in wc) for k in ("a", "m", "s", "m_s")}
                ext = c.pool_extent([r["extent"] for r in rows])
                labels: dict = {}
                for r in rows:
                    for k, n in r["labels"].items():
                        labels[k] = labels.get(k, 0) + n
                out[view][config][str(g)] = {"EV-M1": h["EV-M1"], "EV-M2": h["EV-M2"], "assessable_references": t["a"], "matched_references": t["m"],
                                             "system_events": t["s"], "matched_events": t["m_s"], "unmatched_events": t["s"] - t["m_s"],
                                             "references_with_2plus_episodes": ext["references_with_2plus_episodes"],
                                             "unmatched_by_band": ext["unmatched_by_band"],
                                             "unmatched_with_same_pair_overlap": ext["unmatched_with_same_pair_overlap"],
                                             "episodes": ext["episodes"], "episodes_with_continuation_of_nk": ext["episodes_with_continuation_of_nk"],
                                             "candidate_event_counts": dict(sorted(labels.items()))}
    return out


def _ev(d: dict) -> tuple:
    return tuple(d[k] for k in ("EV-M1", "EV-M2", "assessable_references", "matched_references", "system_events", "matched_events"))


def aggregate() -> dict:  # pragma: no cover
    import v2_sets
    recs = v2_sets.tuning()
    cams = [json.loads((OUT / "mgap" / f"{r}.json").read_text()) for r in recs]
    tab = summarize(cams)
    sel = select({g: (tab["all"][HEADLINE][str(g)]["EV-M1"], tab["all"][HEADLINE][str(g)]["EV-M2"]) for g in GRID})
    stored_c = json.load(open(ROOT / "research/m1b/d54_c_v2_tune.json"))["tuning_116"]["all"]["C-v2"]
    stored_b = json.load(open(ROOT / "research/m1b/d54_b_v2_tune.json"))["ev"]
    rcf = {cfg: {str(g): sorted({x["configs"][cfg][str(g)]["rule_configuration_id"] for x in cams}) for g in GRID} for cfg in CONFIGS}
    out = {"status": STATUS, "decision": "D-57 STEP 3", "contract": "E-1.2.25; v1 base values except lifecycle.m_gap_frames", "baseline": BL,
            "label_group": "G1", "cameras": len(cams), "grid_m_gap_frames": list(GRID),
            "grid_seconds_at_30fps": {str(g): round(g / 30, 3) for g in GRID},
            "configurations": {"C-v2": "detector path, D-56 package, T24 on (stored D-54 S4)", "B-both": "oracle boxes, full_camera, T24 on (stored D-54 S4)",
                               "A": "simulator positions (stored T-21 base S4)"},
            "rule_configuration_ids": rcf,
            "selection_rule": "C-v2, all 116 cameras: keep m_gap with EV-M1 >= EV-M1(5) - 0.02; the highest EV-M2 among them; EV-M2 within 0.005 "
                              "of the highest is a tie, broken by the smaller m_gap",
            "selection": {**sel, "status": "selected under D-57, not frozen; to be checked against the literature value (item C7) before the v2 freeze"},
            "checks": {"m_gap5_payload_equals_stored_s5": {cfg: sum(x["configs"][cfg]["5"]["payload_equals_stored_s5"] for x in cams) for cfg in CONFIGS},
                       "m_gap5_rule_configuration_equals_stored": {cfg: sum(x["configs"][cfg]["5"]["rule_configuration_equals_stored"] for x in cams)
                                                                   for cfg in CONFIGS},
                       "m_gap5_ev_equals_d54": {
                           "C-v2": _ev(tab["all"]["C-v2"]["5"]) == _ev(stored_c),
                           "B-both": _ev(tab["all"]["B-both"]["5"]) == _ev(stored_b["all"]["B-both"]),
                           "A": _ev(tab["all"]["A"]["5"]) == _ev(stored_b["all"]["A (stored)"])}},
            "code_commit": sorted({x["code_commit"] for x in cams}),
            "runtime_s": round(sum(x["seconds"] for x in cams), 1),
            "results": tab}
    ch = out["checks"]
    bad = [k for k, v in ch["m_gap5_payload_equals_stored_s5"].items() if v != len(cams)] + [k for k, v in ch["m_gap5_ev_equals_d54"].items() if not v]
    if bad:
        raise SystemExit(f"STOP: m_gap 5 does not reproduce the stored D-54 results for {bad}")
    return out


def estimate() -> None:  # pragma: no cover - driver
    import run_pilot as rp
    import v2_sets
    global OUT
    prov = rp.provenance()
    t = v2_sets.tuning()
    recs = [t[0], t[-1]]
    OUT = OUT.parent / "d57_estimate"
    rows = []
    for rec in recs:
        t0 = time.time()
        run_camera((rec, prov))
        rows.append({"rec_id": rec, "seconds": round(time.time() - t0, 1)})
    per = sum(r["seconds"] for r in rows) / len(rows)
    est = {"status": "D-57 STEP 3 runtime estimate (2 tuning cameras, first and last; serial)", "rows": rows, "per_camera_s": round(per, 1),
           "total_116_cameras_serial_h": round(per * 116 / 3600, 2), "limit_h": LIMIT_H, "stop": per * 116 / 3600 > LIMIT_H}
    pc.write_json(OUT / "estimate.json", est)
    print(json.dumps(est, indent=1))


def main():  # pragma: no cover
    import run_pilot as rp
    import v2_sets
    what = sys.argv[1]
    if what == "estimate":
        estimate()
        return
    if what == "aggregate":
        p = ROOT / "research/m1b/d57_mgap_sweep.json"
        pc.write_json(p, aggregate())
        print("wrote", p)
        return
    if what == "run":
        workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        recs = sys.argv[3:] or v2_sets.tuning()
        assert set(recs) <= set(v2_sets.tuning()), "tuning subset only (D-57 ruling 8)"
        prov = rp.provenance()
        jobs = [(r, prov) for r in recs]
        t0 = time.time()
        it = map(run_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=2).imap_unordered(run_camera, jobs)
        for n, res in enumerate(it, 1):
            print(n, *res, f"elapsed {round(time.time() - t0)} s", flush=True)
        return
    raise SystemExit(what)


if __name__ == "__main__":
    main()
