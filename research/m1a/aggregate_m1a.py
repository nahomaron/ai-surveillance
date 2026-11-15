"""T-21 phase 2, aggregation of the per-camera evaluations into the M1a validation results (one dataset).

Census windows (V0, inclusion probability 1, weight 1): weighted and unweighted values coincide. Intervals: Target A
(frame_description: stratified window bootstrap, strata = V0 strata) and Target B (new_session_performance: cluster
bootstrap over leakage groups within data origin), B = 2000, seed 2026111402, 95 % (pre-registration v1 section 4.4).
Status of every number: experimental, synthetic scope, oracle perception, validation partition (T12.5, D-36).
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
from collections import defaultdict

import evaluate_m1a as ev
import m1a_common as m
from rq1.evaluation import estimators as est
from rq1.evaluation import event_metrics as em
from rq1.evaluation import gv
from rq1.evaluation.event_metrics import WindowCounts

ORIGIN = {"sdg": "synthetic_rendered", "smartspaces": "synthetic_rendered"}
CFG = ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6")
PAIRED = (("BL-2", "BL-3"), ("BL-3", "BL-6"))


def _ci(rows, ds):
    """rows: (stratum, leakage group, x, y). Target A and Target B intervals of sum y / sum x."""
    if not rows or sum(r[2] for r in rows) == 0:
        return {"target_a": None, "target_b": None}
    strata = defaultdict(list)
    for s, _, x, y in rows:
        strata[s].append((x, y))
    a = est.stratified_bootstrap_ratio(dict(strata), {s: 1.0 for s in strata}, ev.S8["B"], ev.S8["seed"])
    b = est.cluster_bootstrap_ratio([(ORIGIN[ds], g, 1.0, x, y) for _, g, x, y in rows], ev.S8["B"], ev.S8["seed"])
    return {"target_a": list(a), "target_b": list(b)}


def _ratio(rows):
    x, y = sum(r[2] for r in rows), sum(r[3] for r in rows)
    return {"numerator": y, "denominator": x, "value": y / x if x > 0 else None}


def _stat(rows, ds, value_fn=None):
    out = _ratio(rows)
    out.update(_ci(rows, ds))
    if value_fn and out["value"] is not None:
        out["value"] = value_fn(out["value"])
        for k in ("target_a", "target_b"):
            if out[k]:
                out[k] = [value_fn(v) for v in out[k]]
    return out


def main(ds: str, label: str) -> None:
    root = ev.out_dir(label, ds)
    cams = []
    for d in sorted(root.iterdir()):
        p = d / "eval.pkl.gz"
        if p.exists():
            with gzip.open(p, "rb") as f:
                cams.append(pickle.load(f))
    res = {"dataset": ds, "label": label, "cameras": len(cams), "windows": len(cams), "leakage_groups": len({c["leakage_group"] for c in cams}),
           "strata": sorted({c["stratum"] for c in cams}), "status": "experimental (synthetic, oracle perception, validation partition)",
           "reference_class": "rule_conformance (T21)", "interpretation": "T21.5: event metrics on the oracle path measure the effect of camera "
           "observability (T17-T20) and of the configuration's rules relative to BL-6, not perception."}
    units = {}
    for u in ("base", "full_camera", "reference", "sweeps"):
        units[u] = sorted({json.loads((root / c["rec_id"] / f"{u}.json").read_text())["code_commit"] for c in cams})
    res["code_commits"] = units
    # References (T21)
    res["references"] = {"total": sum(c["references"]["n"] for c in cams), "assessable": sum(c["references"]["assessable"] for c in cams),
                         "g1": sum(c["references"]["g1"] for c in cams)}
    res["references"]["unobservable_reference"] = res["references"]["total"] - res["references"]["assessable"]
    # EV-M per configuration (G1)
    res["ev"] = {}
    for bl in CFG:
        wc = [WindowCounts(**c["ev"][bl]["counts"]) for c in cams]
        head = em.headline(wc)
        loc = em.localization([dict(match_type="matched", **r) for c in cams for r in c["ev"][bl]["localization"]])
        m3 = em.abstention_rate([c["ev"][bl]["ev_m3"] for c in cams])
        ci = {"EV-M1": _ci([(c["stratum"], c["leakage_group"], c["ev"][bl]["counts"]["a"], c["ev"][bl]["counts"]["m"]) for c in cams], ds),
              "EV-M2": _ci([(c["stratum"], c["leakage_group"], c["ev"][bl]["counts"]["s"], c["ev"][bl]["counts"]["m_s"]) for c in cams], ds),
              "EV-M7": _ci([(c["stratum"], c["leakage_group"], c["ev"][bl]["counts"]["u"], c["ev"][bl]["counts"]["f"]) for c in cams], ds)}
        mt = defaultdict(int)
        for c in cams:
            for k, v in c["ev"][bl]["match_types"].items():
                mt[k] += v
        res["ev"][bl] = {**head, "EV-M3": m3, "EV-M8": loc, "intervals": ci, "match_types": dict(mt),
                         "runs": {k: sum(c["runs"][bl][k] for c in cams) for k in ("episodes", "events", "duration_s")}}
        per = {}
        for s in res["strata"]:
            sub = [WindowCounts(**c["ev"][bl]["counts"]) for c in cams if c["stratum"] == s]
            per[s] = {k: v for k, v in em.headline(sub).items() if k in ("EV-M1", "EV-M2", "EV-M7")}
        res["ev"][bl]["by_stratum"] = per
    # Paired comparisons (T11.2): EV-M1, EV-M2, EV-M7
    res["paired"] = {}
    for a, b in PAIRED:
        for metric, (xk, yk) in {"EV-M1": ("a", "m"), "EV-M2": ("s", "m_s"), "EV-M7": ("u", "f")}.items():
            rows = [(c["stratum"], ORIGIN[ds], c["leakage_group"], 1.0, c["ev"][a]["counts"][xk], c["ev"][a]["counts"][yk],
                     c["ev"][b]["counts"][xk], c["ev"][b]["counts"][yk]) for c in cams]
            ra, rb = _ratio([(0, 0, r[4], r[5]) for r in rows])["value"], _ratio([(0, 0, r[6], r[7]) for r in rows])["value"]
            ok = all(sum(r[i] for r in rows) > 0 for i in (4, 6))
            res["paired"][f"{a} - {b} {metric}"] = {
                "difference": None if ra is None or rb is None else ra - rb,
                "target_a": list(est.paired_bootstrap_difference(rows, "frame_description", ev.S8["B"], ev.S8["seed"])) if ok else None,
                "target_b": list(est.paired_bootstrap_difference(rows, "new_session_performance", ev.S8["B"], ev.S8["seed"])) if ok else None}
    # Completeness (pooled ratio of sums over windows; per-pair / per-identity ratios summed)
    res["cm"] = {}
    keys = sorted({k for c in cams for k in c["cm"]})
    for metric, basis in keys:
        if metric == "CM-07":
            tot = defaultdict(int)
            for c in cams:
                for s in c["cm"][(metric, basis)]:
                    for k, v in s.items():
                        tot[k] += v
            n = sum(tot.values())
            res["cm"][f"{metric} {basis}"] = {**tot, "pair_window_fidelity": tot["1"] / n if n else None}
            continue
        if metric == "CM-06":
            vals = [p["value"] for c in cams for p in c["cm"][(metric, basis)] if p["value"] is not None]
            res["cm"][f"{metric} {basis}"] = {"n_pairs": len(vals), **{k: v for k, v in gv.signed_summary(vals).items() if k in ("bias", "p95")},
                                               "max": max(vals) if vals else None}
            continue
        rows = [(c["stratum"], c["leakage_group"], r["denominator"], r["numerator"]) for c in cams for r in c["cm"][(metric, basis)]]
        res["cm"][f"{metric} {basis}"] = _stat(rows, ds)
    # GV (full_camera run)
    res["gv"] = gv_aggregate(cams, ds)
    res["sweeps"] = sweeps_aggregate(cams)
    out = m.ROOT / f"research/m1a/results_{ds}.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True, default=str))
    print(f"wrote {out}")


def _vp(stratum: str) -> str:
    return stratum.split(":", 1)[-1]


def gv_aggregate(cams, ds) -> dict:
    out = {}
    cams = [c for c in cams if "null_reason" not in c["gv"]]
    out["cameras_with_full_camera"] = len(cams)
    # GV-01 by class x evidence class x viewpoint; RMSE interval from the per-camera sums of squares
    groups = defaultdict(list)
    for c in cams:
        for cls, evc, dx, dy in c["gv"]["gv01"]:
            for key in ((cls, evc, _vp(c["stratum"])), (cls, "all", _vp(c["stratum"])), (cls, "all", "all"), ("all", "all", _vp(c["stratum"])), ("all", "all", "all")):
                groups[key].append((c["stratum"], c["leakage_group"], dx, dy))
    out["GV-01"] = {}
    for key, rows in sorted(groups.items()):
        s = gv.gv01([(dx, dy) for *_, dx, dy in rows])
        per = defaultdict(lambda: [0, 0.0])
        for st, g, dx, dy in rows:
            per[(st, g)][0] += 1
            per[(st, g)][1] += dx * dx + dy * dy
        mse = _ci([(st, g, n, sq) for (st, g), (n, sq) in per.items()], ds)
        s.pop("sum_sq_m2")
        out["GV-01"]["|".join(key)] = {**s, "rmse_ci_target_a": [math.sqrt(v) for v in mse["target_a"]] if mse["target_a"] else None,
                                         "rmse_ci_target_b": [math.sqrt(v) for v in mse["target_b"]] if mse["target_b"] else None}
    covs = [cv for c in cams for cv in c["gv"]["gv05_cov"]]
    g5 = gv.gv05([(0.0, 0.0)] * len(covs), covs)
    out["GV-05"] = {"n_scored": g5["n"], "n_without_covariance": g5["n_without_covariance"],
                    "note": "not computable: the full_camera positions carry no positional covariance (pos_cov_m2 null, not_supplied)" if g5["n"] == 0 else None}
    out["MR-11"] = "= GV-05"

    def signed(rows_by_key):
        res = {}
        for key, rows in sorted(rows_by_key.items()):
            s = gv.signed_summary([v for *_, v in rows])
            per = defaultdict(lambda: [0, 0.0])
            for st, g, v in rows:
                per[(st, g)][0] += 1
                per[(st, g)][1] += v
            s["bias_ci"] = _ci([(st, g, n, sm) for (st, g), (n, sm) in per.items()], ds)
            s.pop("sum"), s.pop("sum_sq")
            res[key] = s
        return res
    g4, g7, g8 = defaultdict(list), defaultdict(list), defaultdict(list)
    for c in cams:
        for size, evc, v in c["gv"]["gv04"]:
            for key in (f"{size}|{evc}", f"{size}|all"):
                g4[key].append((c["stratum"], c["leakage_group"], v))
        for w_v, rows in c["gv"]["gv07"].items():
            for cls, evc, v in rows:
                for key in (f"w_v={w_v}|{cls}|{evc}", f"w_v={w_v}|{cls}|all", f"w_v={w_v}|all|all"):
                    g7[key].append((c["stratum"], c["leakage_group"], v))
        for evc, v in c["gv"]["gv08"]:
            for key in (evc, "all"):
                g8[key].append((c["stratum"], c["leakage_group"], v))
    out["GV-04"], out["GV-07"], out["GV-08"] = signed(g4), signed(g7), signed(g8)
    pairs = [p for c in cams for p in c["gv"]["gv06_pairs"]]
    out["GV-06"] = {"n": len(pairs), "spearman_rho": gv.spearman([a for a, _ in pairs], [b for _, b in pairs]),
                    "p_disagreement_R1_R2": gv.p_disagreement([p for c in cams for p in c["gv"]["gv06_p"]])}
    return out


PARAM_BASE = {**m.S4_BASE, **m.S5_BASE}


def sweeps_aggregate(cams) -> dict:
    """MR-08 (S4 and S5 grid), MR-09 / GV-03 (footprint), MR-12 (m_gap, t_min); MR-10 not computable (no calibration covariance)."""
    tags = sorted({t for c in cams for t in c["sweeps"] if not t.startswith("_")})
    out = {"MR-10": "not computable: no calibration covariance is supplied for the dataset calibrations (calibration_tier supplied_unvalidated)"}
    base_tot = {bl: {k: sum(c["runs"][bl][k] for c in cams) for k in ("episodes", "events", "duration_s")} for bl in CFG}
    grid = {}
    for tag in tags:
        name, value = tag.split("=")
        value = float(value)
        g = {}
        for bl in CFG:
            tot = {k: sum(c["sweeps"][tag]["configs"][bl]["run"][k] for c in cams) for k in ("episodes", "events", "duration_s")}
            wc = [WindowCounts(**c["sweeps"][tag]["configs"][bl]["ev"]) for c in cams]
            head = em.headline(wc)
            g[bl] = {**tot, "delta": {k: tot[k] - base_tot[bl][k] for k in tot},
                     "elasticity": {k: gv.elasticity(base_tot[bl][k], tot[k], PARAM_BASE[name], value) for k in tot},
                     "EV-M1": head["EV-M1"], "EV-M2": head["EV-M2"], "EV-M7": head["EV-M7"]}
        point = {"parameter": name, "value": value, "base": PARAM_BASE[name], "configs": g}
        dc = [v for c in cams for v in c["sweeps"][tag].get("d_clearance", [])]
        if dc:
            s = gv.signed_summary(dc)
            s.pop("sum"), s.pop("sum_sq")
            point["d_clearance_m"] = s
        grid[tag] = point
    out["grid"] = grid
    # label_stability_frac per base episode, then its mean, per parameter family and over every grid point
    fams = defaultdict(list)
    for tag in tags:
        fams[tag.split("=")[0]].append(tag)
    stab = {}
    for bl in CFG:
        stab[bl] = {}
        for fam, ftags in sorted(fams.items()) + [("all", tags)]:
            vals = []
            for c in cams:
                base = c["sweeps"]["_base_episodes"][bl]
                vals += gv.label_stability(base, [c["sweeps"][t]["configs"][bl]["episodes"] for t in ftags], ev.S8["iou_m"])
            vals = [v for v in vals if v is not None]
            stab[bl][fam] = {"n_episodes": len(vals), "mean_label_stability_frac": sum(vals) / len(vals) if vals else None,
                             "share_fully_stable": sum(1 for v in vals if v == 1.0) / len(vals) if vals else None}
    out["label_stability"] = stab
    out["GV-03_label_flip_rate"] = {}
    for tag in [t for t in tags if t.startswith("fork_")]:
        out["GV-03_label_flip_rate"][tag] = {}
        for bl in CFG:
            vals = [v for c in cams for v in gv.label_stability(c["sweeps"]["_base_episodes"][bl], [c["sweeps"][tag]["configs"][bl]["episodes"]], ev.S8["iou_m"])]
            out["GV-03_label_flip_rate"][tag][bl] = {"n_episodes": len(vals), "flip_rate": 1 - sum(vals) / len(vals) if vals else None}
    return out
