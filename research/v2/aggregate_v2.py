"""D-63 STEP 5 / STEP 7: aggregation of a v2 partition run into `research/v2/<partition>_results.json` (tables of
D-61 section 1.6). Synthetic-data evaluation; experimental. Automated outputs are candidates; nothing is validated.

  PYTHONPATH=src .venv/bin/python research/v2/aggregate_v2.py dev          -> out/v2/dev/dev_results.json (tuning; diagnostic)
  PYTHONPATH=src .venv/bin/python research/v2/aggregate_v2.py reporting    -> research/v2/reporting_results.json

Intervals (pre-registration v1 section 4.4, unchanged in v2): Target A (frame_description, stratified window bootstrap,
strata = V0 strata) and Target B (new_session_performance, cluster bootstrap over leakage groups within data origin);
B 2,000, seed 2026111402, 95 %. Census windows: weight 1. Paired comparisons by T11.2 on EV-M1, EV-M2, EV-M7.
No decision rule is registered for any paired comparison (CR-041 item 2): differences and intervals only.
Registered criteria (v2 section 9): their slices are the SDG test partition. On another partition the same statistic
is printed with the decision the rule would give, labelled "not the registered decision" (CR-041 item 1).
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import run_v2 as rv  # noqa: E402

B, SEED, ORIGIN = 2000, 2026111402, "synthetic_rendered"
VIEWS = ("all", "ceiling", "eye_level")
PAIRS = (("BL-2", "BL-3"), ("BL-3", "BL-6"))
METRICS = {"EV-M1": ("a", "m"), "EV-M2": ("s", "m_s"), "EV-M7": ("u", "f")}
POS_CUTS_M = (1.0, 2.0, 5.0)  # D-41 position outlier shares (as the T-25p pilot tables)
RERUN_DISCLOSURE = [
    "This is the second reporting run (Owner decision D-65, 27 Nov 2026). The first run (commit d20fb82; "
    "research/v2/reporting_results.json and reporting_report.md, kept on record with a defect warning) was defective on the "
    "detector path: S5 looked up object states by the stitched identity's ID (sti_), while S4 object states keep their track "
    "IDs (trk_), so on 0 of 19,750 detector-path pair-frames did it find either object's state; M was unknown on every "
    "frame, R4 had no speeds, and R5 and the contact cue had no input (CR-042).",
    "The fix (CR-042 reading 1): on stitched identities M, R4, R5 and the contact cue read each member track's stored S4 "
    "state for its own frames; nothing is combined or recomputed across a stitch gap. S4 and every frozen v2 value and "
    "configuration are unchanged.",
    "The oracle-path (column A) and full_camera (column B) numbers of the first run, which the defect did not affect, were "
    "seen before this re-run, as were the defective detector-path numbers.",
]
WORDING = "Automated outputs are candidate events; no output is a near miss, collision or contact. Nothing here is validated."


# ------------------------------------------------------------------------------------------------ pure functions

def ci(rows: list[tuple[str, str, float, float]]) -> dict:
    """rows: (stratum, leakage group, x, y). Target A and Target B intervals of sum y / sum x (as aggregate_m1a._ci)."""
    from rq1.evaluation import estimators as est
    if not rows or sum(r[2] for r in rows) == 0:
        return {"target_a": None, "target_b": None}
    strata = defaultdict(list)
    for s, _, x, y in rows:
        strata[s].append((x, y))
    a = est.stratified_bootstrap_ratio(dict(strata), {s: 1.0 for s in strata}, B, SEED)
    b = est.cluster_bootstrap_ratio([(ORIGIN, g, 1.0, x, y) for _, g, x, y in rows], B, SEED)
    return {"target_a": list(a), "target_b": list(b)}


def ratio(rows) -> dict:
    x, y = sum(r[2] for r in rows), sum(r[3] for r in rows)
    return {"numerator": y, "denominator": x, "value": y / x if x > 0 else None}


def in_view(cam: dict, view: str) -> bool:
    return view == "all" or cam["viewpoint"] == view


def ev_table(cams: list[dict], key: str, iou: str) -> dict:
    """EV-M1, EV-M2, EV-M7 (value and intervals) and the pooled counts for one column|baseline at one iou_m, per viewpoint."""
    out = {}
    for view in VIEWS:
        sub = [c for c in cams if in_view(c, view)]
        tot = {k: sum(c["ev"][key][iou]["counts"][k] for c in sub) for k in ("a", "m", "s", "m_s", "f", "u")}
        res = {"cameras": len(sub), "leakage_groups": len({c["leakage_group"] for c in sub}), "counts": tot}
        for name, (xk, yk) in METRICS.items():
            rows = [(c["stratum"], c["leakage_group"], c["ev"][key][iou]["counts"][xk], c["ev"][key][iou]["counts"][yk]) for c in sub]
            res[name] = {**ratio(rows), **ci(rows)}
        out[view] = res
    return out


def paired(cams: list[dict], col: str, a: str, b: str, iou: str) -> dict:
    """T11.2 paired bootstrap of a - b on EV-M1, EV-M2, EV-M7 (both estimands); no decision rule (CR-041 item 2)."""
    from rq1.evaluation import estimators as est
    out = {}
    for name, (xk, yk) in METRICS.items():
        rows = [(c["stratum"], ORIGIN, c["leakage_group"], 1.0, c["ev"][f"{col}|{a}"][iou]["counts"][xk], c["ev"][f"{col}|{a}"][iou]["counts"][yk],
                 c["ev"][f"{col}|{b}"][iou]["counts"][xk], c["ev"][f"{col}|{b}"][iou]["counts"][yk]) for c in cams]
        xa, ya, xb, yb = (sum(r[i] for r in rows) for i in (4, 5, 6, 7))
        ok = xa > 0 and xb > 0
        out[name] = {"value_a": ya / xa if xa else None, "value_b": yb / xb if xb else None, "difference": (ya / xa - yb / xb) if ok else None,
                     "target_a": list(est.paired_bootstrap_difference(rows, "frame_description", B, SEED)) if ok else None,
                     "target_b": list(est.paired_bootstrap_difference(rows, "new_session_performance", B, SEED)) if ok else None,
                     "decision_rule": None}
    return out


def _q(values, q):
    from rq1.evaluation import event_metrics as em
    return float(em.percentile(values, q)) if values else None


def gv01_summary(cams: list[dict], col: str, view: str, cls: str = "all") -> dict:
    """GV-01 RMSE with Target A / B intervals (from per-camera sums of squares, as aggregate_m1a.gv_aggregate), the D-41
    form (median, P95, share above 1, 2, 5 m) and position availability by null reason."""
    per, norms, avail = [], [], defaultdict(int)
    for c in cams:
        if not in_view(c, view):
            continue
        g = c["gv"][col]
        e = [math.hypot(dx, dy) for k, _, dx, dy in g["gv01"] if cls in ("all", k)]
        norms += e
        per.append((c["stratum"], c["leakage_group"], len(e), sum(v * v for v in e)))
        for k, v in g["availability"].items():
            if cls in ("all", k.split("|")[0]):
                avail[k.split("|", 1)[1]] += v
    n = len(norms)
    mse = ci(per)
    return {"n": n, "rmse_m": math.sqrt(sum(v * v for v in norms) / n) if n else None,
            "rmse_ci_target_a": [math.sqrt(v) for v in mse["target_a"]] if mse["target_a"] else None,
            "rmse_ci_target_b": [math.sqrt(v) for v in mse["target_b"]] if mse["target_b"] else None,
            "median_m": _q(norms, 50), "p95_m": _q(norms, 95), **{f"share_gt_{int(x)}m": (sum(1 for v in norms if v > x) / n) if n else None for x in POS_CUTS_M},
            "leakage_groups": len({p[1] for p in per}), "availability": dict(sorted(avail.items()))}


def gv07_summary(cams: list[dict], col: str, view: str = "all", cls: str = "all") -> dict:
    """GV-07 speed error at w_v 0.5: RMSE with intervals, bias, and the D-41 form median and P95 of |error|. The speed
    outlier share has no stated cut (CR-041 item 3) and is not computed."""
    per, errs = [], []
    for c in cams:
        if not in_view(c, view):
            continue
        e = [v for k, _, v in c["gv"][col]["gv07"] if cls in ("all", k)]
        errs += e
        per.append((c["stratum"], c["leakage_group"], len(e), sum(v * v for v in e)))
    n = len(errs)
    mse = ci(per)
    absv = [abs(v) for v in errs]
    return {"n": n, "rmse_mps": math.sqrt(sum(v * v for v in errs) / n) if n else None,
            "rmse_ci_target_a": [math.sqrt(v) for v in mse["target_a"]] if mse["target_a"] else None,
            "rmse_ci_target_b": [math.sqrt(v) for v in mse["target_b"]] if mse["target_b"] else None,
            "bias_mps": sum(errs) / n if n else None, "median_abs_mps": _q(absv, 50), "p95_abs_mps": _q(absv, 95),
            "outlier_share": None, "outlier_share_null_reason": "no stated speed cut (CR-041 item 3)", "leakage_groups": len({p[1] for p in per})}


def gv04_summary(cams: list[dict]) -> dict:
    """GV-04 bias (prior footprint minus simulator 3D box footprint, D-40 item 4) with Target A / B intervals."""
    per, vals = [], []
    for c in cams:
        v = [d for _, _, d in c["gv"]["gv04_simulator_positions"]]
        vals += v
        per.append((c["stratum"], c["leakage_group"], len(v), sum(v)))
    b = ci(per)
    return {"n": len(vals), "bias_m": sum(vals) / len(vals) if vals else None, "bias_ci_target_a": b["target_a"], "bias_ci_target_b": b["target_b"],
            "leakage_groups": len({p[1] for p in per}), "note": "GV-04 is circular (the prior is the dataset box): reported, never cited as evidence"}


def m_inputs_total(cams: list[dict]) -> dict | None:
    """CR-042 guard totals per column|baseline: pair-frames with both states, M unknown among them, share (None before D-65)."""
    if not all("m_inputs" in c["checks"] for c in cams):
        return None
    keys = sorted({k for c in cams for k in c["checks"]["m_inputs"]})
    out = {}
    for k in keys:
        both = sum(c["checks"]["m_inputs"][k]["pair_frames_with_both_states"] for c in cams)
        miss = sum(c["checks"]["m_inputs"][k]["m_missing"] for c in cams)
        out[k] = {"pair_frames_with_both_states": both, "m_missing": miss, "share_missing": (miss / both) if both else None}
    return out


def mr01(run: list[dict], repeat: list[dict]) -> dict:
    """MR-01: 1.0 when every exact-class artifact ID and payload hash of the repeat equals the run (AR-57 item 5), else 0.0."""
    a = {c["rec_id"]: c["artifact_digest"] for c in run}
    b = {c["rec_id"]: c["artifact_digest"] for c in repeat}
    differ = sorted(r for r in a if r in b and b[r] != a[r])
    return {"cameras": len(a), "repeated": len(b), "differing": differ, "value": None if set(a) != set(b) else (0.0 if differ else 1.0)}


def criterion_rows(freeze: dict, values: dict, n_groups: int, partition: str) -> list[dict]:
    """The registered criteria with the statistic of this run and the decision `fitness.decide_criterion` gives it.
    Off the test partition the decision is labelled "not the registered decision" (registered slice: test)."""
    from rq1.evaluation import fitness
    out = []
    for c in freeze["acceptance_criteria"]:
        label = c["criterion_label"]
        v = values[label]
        result = {"validity": "valid", "n_units": 1 if c["metric_id"] == "MR-01" else n_groups, "value": v.get("value"),
                  "ci_low": (v.get("ci") or [None, None])[0], "ci_high": (v.get("ci") or [None, None])[1]}
        decision = fitness.decide_criterion(c, result)
        registered_slice = c["slice"].get("partition", "any") if isinstance(c["slice"], dict) else "any"
        applies = registered_slice in ("any", partition) or c["metric_id"] == "MR-01"
        out.append({"criterion_label": label, "acc_id": c["acc_id"], "metric_id": c["metric_id"], "rule": c["rule"], "target": c["target"],
                    "n_min_units": c["n_min_units"], "n_units": result["n_units"], "value": v.get("value"), "ci_target_b": v.get("ci"),
                    "decision": decision, "registered_slice_partition": registered_slice,
                    "status": "registered decision" if applies else f"not the registered decision (registered slice: {registered_slice}; CR-041 item 1)"})
    return out


# ------------------------------------------------------------------------------------------------ driver

def load(partition: str):  # pragma: no cover
    base = rv.partition_dir(partition)
    run = [json.loads(p.read_text()) for p in sorted((base / "cam").glob("*.json"))]
    rep = [json.loads(p.read_text()) for p in sorted((base / "repeat").glob("*.json"))] if (base / "repeat").exists() else []
    return base, run, rep


def aggregate(partition: str) -> dict:  # pragma: no cover
    freeze = json.loads(rv.FREEZE.read_text())
    _, cams, rep = load(partition)
    expected = rv.cameras(partition)
    if sorted(c["rec_id"] for c in cams) != sorted(expected):
        raise SystemExit(f"STOP: {len(cams)} of {len(expected)} cameras present")
    commits = sorted({c["code_commit"] for c in cams})
    keys = sorted(cams[0]["ev"])
    iou0 = str(rv.v2.IOU_M)
    res = {"partition": partition, "status": rv.STATUS, "wording": WORDING, "contract": rv.v2.CONTRACT, "code_commits": commits,
           "preregistration": "docs/preregistration_v2_FROZEN.md (freeze record SHA-256 in docs/preregistration/freeze_record_v2.json)",
           "cameras": len(cams), "viewpoints": {v: sum(1 for c in cams if in_view(c, v)) for v in VIEWS},
           "leakage_groups": len({c["leakage_group"] for c in cams}),
           "references": {k: sum(c["references"][k] for c in cams) for k in ("n", "assessable", "g1")},
           "checks": {"configs_equal_freeze": sum(1 for c in cams if c["checks"]["configs_equal_freeze"]),
                      "reference_equals_freeze": sum(1 for c in cams if c["checks"]["reference_equals_freeze"]),
                      "person_log_reproduces_pilot": sum(1 for c in cams if c["checks"]["person_log_reproduces_pilot"]),
                      "gv04_pair_frames_and_prior_mismatches": [sum(c["checks"]["gv04_prior_clearance_differs_from_stored"][i] for c in cams) for i in (0, 1)],
                      "stitch_links": sum(c["checks"]["stitch_links"] for c in cams),
                      "m_inputs": m_inputs_total(cams)},
           "runtime_s": round(sum(c["seconds"] for c in cams), 1)}
    # 1-2. headline (C|BL-6) and decomposition (A|BL-6, B|BL-6); 5. every column x baseline x iou_m
    res["ev"] = {k: {iou: ev_table(cams, k, iou) for iou in (str(x) for x in rv.IOUS)} for k in keys}
    res["headline"] = {"key": "C|BL-6", "iou_m": iou0, "table": res["ev"]["C|BL-6"][iou0]}
    res["decomposition"] = {k: res["ev"][k][iou0] for k in ("A|BL-6", "B|BL-6", "C|BL-6")}
    # 6. IE share, speed_near_v_min, paired comparisons
    res["ie"] = {k: {v: (lambda e, n: {"events": n, "ie_events": e, "ie_share": e / n if n else None})(
        sum(c["ie"][k]["ie_events"] for c in cams if in_view(c, v)), sum(c["ie"][k]["events"] for c in cams if in_view(c, v))) for v in VIEWS} for k in keys}
    res["flags"] = {k: {f: sum(c["flags"][k][f] for c in cams) for f in cams[0]["flags"][k]} for k in keys}
    res["paired"] = {f"{col} {a} - {b}": {"registered": col == "A", "path": "oracle" if col == "A" else "detector",
                                          **{iou: paired(cams, col, a, b, iou) for iou in (str(x) for x in rv.IOUS)}}
                     for col in ("A", "C") for a, b in PAIRS}
    # 3-4. GV
    res["gv"] = {col: {"GV-01": {f"{v}|{cls}": gv01_summary(cams, col, v, cls) for v in VIEWS for cls in ("all", "person", "forklift")},
                       "GV-07": {f"{v}|{cls}": gv07_summary(cams, col, v, cls) for v in VIEWS for cls in ("all", "person", "forklift")}}
                 for col in ("B", "C")}
    res["gv"]["GV-04"] = gv04_summary(cams)
    res["MR-01"] = mr01(cams, rep)
    b = res["gv"]["B"]
    vals = {"C1-MR-01": {"value": res["MR-01"]["value"], "ci": None},
            "C2-GV-01-ceiling": {"value": b["GV-01"]["ceiling|all"]["rmse_m"], "ci": b["GV-01"]["ceiling|all"]["rmse_ci_target_b"]},
            "C2-GV-01-eye_level": {"value": b["GV-01"]["eye_level|all"]["rmse_m"], "ci": b["GV-01"]["eye_level|all"]["rmse_ci_target_b"]},
            "C3-GV-07": {"value": b["GV-07"]["all|all"]["rmse_mps"], "ci": b["GV-07"]["all|all"]["rmse_ci_target_b"]},
            "C4-GV-04": {"value": res["gv"]["GV-04"]["bias_m"], "ci": res["gv"]["GV-04"]["bias_ci_target_b"]}}
    res["criteria"] = criterion_rows(freeze, vals, res["leakage_groups"], rv.REFERENCE_SET[partition])
    if partition == "reporting_rerun":
        res["disclosure"] = RERUN_DISCLOSURE
    return res


def main():  # pragma: no cover
    partition = sys.argv[1]
    res = aggregate(partition)
    path = (rv.partition_dir("dev") / "dev_results.json") if partition == "dev" else ROOT / f"research/v2/{partition}_results.json"
    path.write_text(json.dumps(res, indent=1, sort_keys=True, default=list) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
