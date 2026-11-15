"""Markdown tables for reports/M1a_report.md from research/m1a/results_<ds>.json (no number is typed by hand).
  python research/m1a/report_tables.py sdg > out/m1a/report_tables_sdg.md"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ds = sys.argv[1]
r = json.loads((ROOT / f"research/m1a/results_{ds}.json").read_text())


def f(v, d=3):
    if v is None:
        return "—"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(f(x, d) for x in v) + "]"
    return f"{v:.{d}f}" if isinstance(v, float) else str(v)


print(f"Cameras (windows) {r['cameras']}, leakage groups {r['leakage_groups']}, strata {', '.join(r['strata'])}. "
      f"References (T21): {r['references']['total']} ({r['references']['assessable']} assessable, {r['references']['unobservable_reference']} unobservable_reference).\n")
print("| Config | Episodes | Events | EV-M1 recall [A; B] | EV-M2 precision [A; B] | EV-M7 false alerts / h [A; B] | EV-M4 | EV-M11 | EV-M8 onset med / P90 (s) | mean IoU | matched / miss / false / dup |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for bl, e in r["ev"].items():
    i, mt, loc = e["intervals"], e["match_types"], e["EV-M8"]
    print(f"| {bl} | {e['runs']['episodes']} | {e['runs']['events']} | {f(e['EV-M1'])} {f(i['EV-M1']['target_a'])}; {f(i['EV-M1']['target_b'])} | "
          f"{f(e['EV-M2'])} {f(i['EV-M2']['target_a'])}; {f(i['EV-M2']['target_b'])} | {f(e['EV-M7'],1)} {f(i['EV-M7']['target_a'],1)}; {f(i['EV-M7']['target_b'],1)} | "
          f"{f(e['EV-M4'])} | {f(e['EV-M11'])} | {f(loc['onset_median_s'],2)} / {f(loc['onset_p90_s'],2)} | {f(loc['mean_iou'])} | "
          f"{mt.get('matched',0)} / {mt.get('miss',0)} / {mt.get('false_alert',0)} / {mt.get('duplicate_alert',0)} |")
print("\nEV-M3 (G2 abstention; episodes form / support form): " + "; ".join(f"{bl} {f(e['EV-M3']['episodes'])} / {f(e['EV-M3']['support'])}" for bl, e in r["ev"].items()))
print("\nBy viewpoint stratum (EV-M1 / EV-M2 / EV-M7):\n")
print("| Config | " + " | ".join(r["strata"]) + " |")
print("|---|" + "---|" * len(r["strata"]))
for bl, e in r["ev"].items():
    print(f"| {bl} | " + " | ".join(f"{f(e['by_stratum'][s]['EV-M1'])} / {f(e['by_stratum'][s]['EV-M2'])} / {f(e['by_stratum'][s]['EV-M7'],1)}" for s in r["strata"]) + " |")
print("\nPaired differences (T11.2), first minus second:\n")
print("| Comparison | Difference | Target A 95 % | Target B 95 % |")
print("|---|---|---|---|")
for k, v in r["paired"].items():
    d = 1 if "EV-M7" in k else 3
    print(f"| {k} | {f(v['difference'], d)} | {f(v['target_a'], d)} | {f(v['target_b'], d)} |")
print("\nCompleteness (pooled ratio of sums; Target B interval):\n")
print("| Metric | Value | Target B 95 % |")
print("|---|---|---|")
for k, v in r["cm"].items():
    if "value" in v:
        print(f"| {k} | {f(v['value'])} | {f(v.get('target_b'))} |")
    elif "pair_window_fidelity" in v:
        print(f"| {k} | intervals 0 / 1 / 2+ POWs: {v.get('0',0)} / {v.get('1',0)} / {v.get('2+',0)}; pair-window fidelity {f(v['pair_window_fidelity'])} | — |")
    else:
        print(f"| {k} | Σ\\|AI − ref\\| time in band per pair: mean {f(v.get('bias'))} s, P95 {f(v.get('p95'))} s, max {f(v.get('max'))} s, {v['n_pairs']} pairs | — |")
g = r["gv"]
print(f"\nGeometry, full_camera run ({g['cameras_with_full_camera']} cameras with a calibration).\n\nGV-01 position error (m):\n")
print("| class / evidence / viewpoint | n | RMSE [B] | P95 | bias x | bias y |")
print("|---|---|---|---|---|---|")
for k, v in g["GV-01"].items():
    print(f"| {k} | {v['n']} | {f(v['rmse_m'])} {f(v['rmse_ci_target_b'])} | {f(v['p95_m'])} | {f(v['bias_x_m'])} | {f(v['bias_y_m'])} |")
for name, unit in (("GV-04", "m"), ("GV-07", "m/s"), ("GV-08", "m")):
    print(f"\n{name} ({unit}):\n\n| stratum | n | bias [B] | RMSE | SD | P5 | P95 |\n|---|---|---|---|---|---|---|")
    for k, v in g[name].items():
        print(f"| {k} | {v['n']} | {f(v['bias'],4)} {f(v['bias_ci']['target_b'],4)} | {f(v['rmse'],4)} | {f(v['sd'],4)} | {f(v['p5'],4)} | {f(v['p95'],4)} |")
print(f"\nGV-05 / MR-11: {g['GV-05']['note'] or g['GV-05']}. GV-06: Spearman ρ(image_gap_norm, clearance_m) = {f(g['GV-06']['spearman_rho'])} over {g['GV-06']['n']} pair-frames; "
      f"R1-P vs R2-P disagreement {f(g['GV-06']['p_disagreement_R1_R2']['rate'])} ({g['GV-06']['p_disagreement_R1_R2']['disagree']} of {g['GV-06']['p_disagreement_R1_R2']['n']}).")
s = r["sweeps"]
print("\nSweeps (one at a time; totals over cameras; Δ against base):\n")
print("| Grid point | " + " | ".join(f"{bl} episodes (Δ) / EV-M1" for bl in r["ev"]) + " |")
print("|---|" + "---|" * len(r["ev"]))
for tag, p in s["grid"].items():
    print(f"| {tag} | " + " | ".join(f"{c['episodes']} ({c['delta']['episodes']:+d}) / {f(c['EV-M1'])}" for c in p["configs"].values()) + " |")
print("\nMR-08 mean label_stability_frac (share of episodes fully stable):\n")
fams = list(next(iter(s["label_stability"].values())).keys())
print("| Family | " + " | ".join(s["label_stability"]) + " |")
print("|---|" + "---|" * len(s["label_stability"]))
for fam in fams:
    print(f"| {fam} | " + " | ".join(f"{f(v[fam]['mean_label_stability_frac'])} ({f(v[fam]['share_fully_stable'])})" for v in s["label_stability"].values()) + " |")
print("\nGV-03 footprint sweep: label flip rate per configuration; Δclearance (m):\n")
for tag, v in s["GV-03_label_flip_rate"].items():
    dc = s["grid"][tag].get("d_clearance_m", {})
    print(f"- {tag}: " + ", ".join(f"{bl} {f(x['flip_rate'])}" for bl, x in v.items()) + f"; Δclearance bias {f(dc.get('bias'),4)}, P5 {f(dc.get('p5'),4)}, P95 {f(dc.get('p95'),4)}")
print(f"\nMR-10: {s['MR-10']}.")
