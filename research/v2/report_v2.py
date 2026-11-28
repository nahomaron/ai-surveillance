"""D-63 STEP 5 / STEP 7: `research/v2/<partition>_report.md` from `<partition>_results.json` (tables only; every number
comes from the results file). Synthetic-data evaluation; experimental.

  PYTHONPATH=src .venv/bin/python research/v2/report_v2.py dev        (tuning; diagnostic, out/v2/dev_m1c/dev_report.md)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import run_v2 as rv  # noqa: E402

COL = {"A": "oracle path (simulator positions)", "B": "oracle boxes, full_camera geometry", "C": "detector path"}


def f(v, d=3):
    if v is None:
        return "—"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(f(x, d) for x in v) + "]"
    return f"{v:.{d}f}" if isinstance(v, float) else str(v)


def ev_rows(table: dict) -> list[str]:
    out = ["| Viewpoint | Cameras | Groups | a | m | s | EV-M1 | Target A | Target B | EV-M2 | Target A | Target B | False | Duplicate | Usable camera-hours | EV-M7 | Target A | Target B |", "|" + "---|" * 18]
    for view, t in table.items():
        e1, e2, e7 = t["EV-M1"], t["EV-M2"], t["EV-M7"]
        c = t["counts"]
        out.append(f"| {view} | {t['cameras']} | {t['leakage_groups']} | {c['a']} | {c['m']} | {c['s']} | {f(e1['value'])} | {f(e1['target_a'])} | {f(e1['target_b'])} | "
                   f"{f(e2['value'])} | {f(e2['target_a'])} | {f(e2['target_b'])} | "
                   f"{f(c.get('false'))} | {f(c.get('duplicate'))} | {f(c['u'])} | {f(e7['value'], 1)} | "
                   f"{f(e7['target_a'], 1)} | {f(e7['target_b'], 1)} |")
    return out


def gv01_rows(gv: dict, col: str) -> list[str]:
    out = ["| Viewpoint, class | Scored | Reference n | RMSE (m) | Target B | median | P95 | > 1 m | > 2 m | > 5 m | Availability |", "|" + "---|" * 11]
    for key, s in gv[col]["GV-01"].items():
        av = ", ".join(f"{k} {v}" for k, v in s["availability"].items())
        out.append(f"| {key} | {s['n']} | {f(s.get('reference_n'))} | {f(s['rmse_m'])} | {f(s['rmse_ci_target_b'])} | {f(s['median_m'])} | {f(s['p95_m'])} | {f(s['share_gt_1m'])} | "
                   f"{f(s['share_gt_2m'])} | {f(s['share_gt_5m'])} | {av} |")
    return out


def gv07_rows(gv: dict, col: str) -> list[str]:
    out = ["| Viewpoint, class | Scored | Reference n | RMSE (m/s) | Target B | bias | median abs | P95 abs |", "|" + "---|" * 8]
    for key, s in gv[col]["GV-07"].items():
        out.append(f"| {key} | {s['n']} | {f(s.get('reference_n'))} | {f(s['rmse_mps'])} | {f(s['rmse_ci_target_b'])} | {f(s['bias_mps'])} | {f(s['median_abs_mps'])} | {f(s['p95_abs_mps'])} |")
    return out


def render(r: dict) -> str:
    iou0 = r["headline"]["iou_m"]
    L = [f"# Pre-registration v2 — {r['partition']} run: tables (D-61 §1.6)", "",
         f"**Status:** {r['status']}. {r['wording']}", "",
         f"Cameras {r['cameras']} ({', '.join(f'{k} {v}' for k, v in r['viewpoints'].items())}); leakage groups {r['leakage_groups']}; "
         f"references {r['references']['n']} (assessable {r['references']['assessable']}, G1 {r['references']['g1']}). Code commit(s): {', '.join(r['code_commits'])}. "
         f"Contract {r['contract']}. Configuration: {r['preregistration']}.", "",
         "Checks: " + "; ".join(f"{k} {v}" for k, v in r["checks"].items()) + ".", "",
         *([("**Disclosure (D-65).** " + " ".join(r["disclosure"])), ""] if r.get("disclosure") else []),
         "## 1. Headline: BL-6, detector path", "", f"N4 matching, label group G1, iou_m {iou0}. EV-M1 and EV-M2 are descriptive under C12. EV-M7 is false and duplicate candidates per usable synthetic camera-hour.", "",
         *ev_rows(r["headline"]["table"]), "",
         "## 2. Decomposition (BL-6)", "", "Oracle results are never substituted for detector-path capability.", ""]
    for k, t in r["decomposition"].items():
        L += [f"**{k}** ({COL[k[0]]})", "", *ev_rows(t), ""]
    L += ["## 3. Registered criteria", "", "Each target is half the threshold it decides (D-61 §1.6). GV-04 is circular: reported, never cited as evidence. "
          "A failed criterion is reported as failed; targets are not moved.", "",
          "| Criterion | Rule | Target | Value | Target B interval | n units (min) | Decision | Status |", "|" + "---|" * 8]
    for c in r["criteria"]:
        L.append(f"| {c['criterion_label']} | {c['rule']} | {c['target']} | {f(c['value'])} | {f(c['ci_target_b'])} | {c['n_units']} ({c['n_min_units']}) | {c['decision']} | {c['status']} |")
    mr = r["MR-01"]
    L += ["", f"MR-01: {mr['cameras']} cameras run, {mr['repeated']} repeated, {len(mr['differing'])} differing.", "",
          "## 4. Descriptive GV (no decision)", "", "GV-01 position error, full_camera (B, oracle boxes):", "", *gv01_rows(r["gv"], "B"), "",
          "GV-01 position error on detector boxes (C, A5.2 matched identity):", "", *gv01_rows(r["gv"], "C"), "",
          "GV-07 speed error at w_v 0.5 s, full_camera (B). The speed outlier share is not computed: no cut is stated (CR-041 item 3).", "", *gv07_rows(r["gv"], "B"), "",
          "GV-07 on detector boxes (C):", "", *gv07_rows(r["gv"], "C"), "",
          f"GV-04 (simulator positions, D-40 item 4): bias {f(r['gv']['GV-04']['bias_m'])} m, Target B {f(r['gv']['GV-04']['bias_ci_target_b'])}, n {r['gv']['GV-04']['n']}. {r['gv']['GV-04']['note']}.", "",
          "## 5. EV-M1 / EV-M2 by iou_m and viewpoint", ""]
    for k in sorted(r["ev"]):
        for iou, t in r["ev"][k].items():
            L += [f"**{k}, iou_m {iou}**", "", *ev_rows(t), ""]
    L += ["## 6. IE share, borderline flags, paired comparisons", "", "| Column, baseline | Events (all) | IE events | IE share | Episodes | speed_near_v_min |", "|" + "---|" * 6]
    for k in sorted(r["ie"]):
        a = r["ie"][k]["all"]
        L.append(f"| {k} | {a['events']} | {a['ie_events']} | {f(a['ie_share'])} | {r['flags'][k]['episodes']} | {r['flags'][k]['speed_near_v_min']} |")
    L += ["", "Paired comparisons (T11.2 paired bootstrap, difference a − b). **No decision rule is registered** for any pair (CR-041 item 2); "
          "the oracle pairs are the registered comparisons, the detector pairs are reported without a decision rule.", "",
          "| Pair | iou_m | Metric | a | b | a − b | Target A | Target B |", "|" + "---|" * 8]
    for name, p in r["paired"].items():
        for iou in sorted(k for k in p if k not in ("registered", "path")):
            for metric, d in p[iou].items():
                L.append(f"| {name} ({p['path']}) | {iou} | {metric} | {f(d['value_a'])} | {f(d['value_b'])} | {f(d['difference'])} | {f(d['target_a'])} | {f(d['target_b'])} |")
    L += ["", "## Limitations", "", "The fifteen limitations of `docs/preregistration_v2_FROZEN.md` §10 and limitations 16–20 of `research/v2/reporting_plan.md` apply to every number here.", ""]
    return "\n".join(L) + "\n"


def main():  # pragma: no cover
    part = sys.argv[1]
    src = (rv.partition_dir("dev") / "dev_results.json") if part == "dev" else ROOT / f"research/v2/{part}_results.json"
    if part != "dev":
        raise SystemExit("refused: historical v2 reports are archival")
    dst = rv.partition_dir("dev") / "dev_report.md"
    dst.write_text(render(json.loads(src.read_text())))
    print("wrote", dst)


if __name__ == "__main__":
    main()
