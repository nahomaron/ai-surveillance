"""D-47: markdown tables for the C' / N9 / CR-007 section of `reports/M1b_pilot_report.md`.

  PYTHONPATH=src .venv/bin/python research/m1b/d47_report_tables.py > out/m1b/pilot/tables_d47.md

Inputs: pilot_results.json (column C), pilot_results_cprime.json (C'), pilot_tracker_loss.json and _cprime.json,
pilot_n9.json, cr007_evidence.json. The f83a241 tables (`pilot_report_tables.py`) are unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG = ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6")
CP = "C'"


def load(name):
    return json.load(open(ROOT / "research/m1b" / name))


def f(v, n=2):
    return "—" if v is None else f"{v:.{n}f}"


def ci(v, n=2):
    return "—" if not v else f"[{v[0]:.{n}f}, {v[1]:.{n}f}]"


def pct(v, n=1):
    return "—" if v is None else f"{100 * v:.{n}f} %"


def main():
    rc, rp = load("pilot_results.json"), load("pilot_results_cprime.json")
    tc, tp = load("pilot_tracker_loss.json"), load("pilot_tracker_loss_cprime.json")
    n9, ce = load("pilot_n9.json"), load("cr007_evidence.json")
    cols = (("C", rc), (CP, rp))
    out = []
    p = out.append
    p(f"Cameras: C {rc['cameras']}, C' {rp['cameras']}; the same S2 artifacts; references as in the pilot ({rc['references']['assessable']} assessable).\n")
    p("#### Events: EV-M1 and EV-M2 (G1, Target B intervals), C and C' (post-hoc, exploratory)\n")
    p("| configuration | column | EV-M1 | Target B | matched / assessable | EV-M2 | Target B | matched / system | candidate events |")
    p("|---|---|---|---|---|---|---|---|---|")
    for bl in CFG:
        for name, r in cols:
            e = r["ev"][name][bl]
            c = e["counts"]
            p(f"| {bl} | {name} | {f(e['EV-M1'])} | {ci(e['EV-M1_target_b'])} | {c['m']} / {c['a']} | {f(e['EV-M2'])} | {ci(e['EV-M2_target_b'])} | {c['m_s']} / {c['s']} | {e['runs']['events']} |")
    p("\n#### Per-label recall and precision (O, H, PC; descriptive)\n")
    p("| configuration | column | O recall | O precision | H recall | H precision | PC recall | PC precision |")
    p("|---|---|---|---|---|---|---|---|")
    for bl in CFG:
        for name, r in cols:
            L = r["labels"][name][bl]
            p(f"| {bl} | {name} | " + " | ".join(f"{f(L[x]['recall'])} | {f(L[x]['precision'])}" for x in ("O", "H", "PC")) + " |")
    p("\n#### Tracking (T-12 association at iou_cm 0.5; IDF1 pooled over cameras by summed IDTP / IDFP / IDFN)\n")
    p("Tracks started = tracks reported by the tracker. False tracks = tracks whose T-12 status is `unmatched_system` (never matched to an identity).\n")
    p("| class | column | tracks started | one_to_one | fragment | id_switch (status) | false tracks | identity switches | identities never matched | IDF1 | n references / system points |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        for name, r in cols:
            t = r["tracking"][c]
            s = t["status"]
            p(f"| {c} | {name} | {t['tracks']} | {s['one_to_one']} | {s['fragment']} | {s['id_switch']} | {s['unmatched_system']} | {t['n_switches']} | {t['missed_identities']} | "
              f"{f(t['IDF1'], 3)} | {t['IDTP'] + t['IDFN']:.0f} / {t['IDTP'] + t['IDFP']:.0f} |")
    p("\nBridging (g_max 15):\n")
    p("| class | column | tracked points | predicted points | runs bridged | runs lost (> 15) | frames lost in long runs |")
    p("|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        for name, r in cols:
            b = r["tracking"][c]["bridging"]
            p(f"| {c} | {name} | {b['tracked']} | {b['predicted']} | {b['runs_bridged']} | {b['runs_lost']} | {b['lost_long_run']} |")
    p("\n#### Frame-level recall stage by stage (same references and matcher as the pilot)\n")
    p("| viewpoint | class | reference boxes | S2 detections | C tracked | C tracked + predicted | C' tracked | C' tracked + predicted |")
    p("|---|---|---|---|---|---|---|---|")
    for v in ("all", "ceiling", "eye_level"):
        for c in ("person", "forklift"):
            a, b = tc["results"][v]["stages"][c], tp["results"][v]["stages"][c]
            n = a["references"]
            assert b["references"] == n and b["s2"] == a["s2"]
            p(f"| {v} | {c} | {n} | {f(a['s2'] / n)} | {f(a['tracked'] / n)} | {f(a['tracked_predicted'] / n)} | {f(b['tracked'] / n)} | {f(b['tracked_predicted'] / n)} |")
    p("\nC' detections by score band, reference match and tracking (bands as in the pilot; the C' thresholds differ from the band edges):\n")
    p("| class | band | detections | matched, tracked | matched, not tracked | unmatched, tracked | unmatched, not tracked | share of matched that were tracked (C → C') |")
    p("|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        for bnd in tp["bands"]:
            k, k0 = tp["results"]["all"]["bands"][c][bnd], tc["results"]["all"]["bands"][c][bnd]
            n = sum(k.values())
            if n == 0:
                continue
            mt, mt0 = k["matched_tracked"] + k["matched_not_tracked"], k0["matched_tracked"] + k0["matched_not_tracked"]
            p(f"| {c} | {bnd} | {n} | {k['matched_tracked']} | {k['matched_not_tracked']} | {k['unmatched_tracked']} | {k['unmatched_not_tracked']} | "
              f"{pct(k0['matched_tracked'] / mt0 if mt0 else None)} → {pct(k['matched_tracked'] / mt if mt else None)} |")
    p("\n#### Position (D-41), C and C' (scored on frames whose track is matched to an identity)\n")
    p("| column | class | n scored | median (m) | P95 (m) | > 1 m | > 2 m | > 5 m | with a position, not scored |")
    p("|---|---|---|---|---|---|---|---|---|")
    for name, r in cols:
        for c in ("person", "forklift"):
            e = r["position"][name]["error"][f"{c}|all"]
            nm = r["position"][name]["availability"][c].get("position_without_matched_identity", {"n": 0})["n"]
            p(f"| {name} | {c} | {e['n']} | {f(e['median_m'])} | {f(e['p95_m'])} | {pct(e['share_gt_1m'])} | {pct(e['share_gt_2m'])} | {pct(e['share_gt_5m'])} | {nm} |")
    p("\n#### Completeness (ratio of sums; Target B intervals)\n")
    p("| metric | basis | C | C' |")
    p("|---|---|---|---|")
    for key in sorted(rc["cm"]["C"]):
        metric, basis = key.split(" ", 1)
        p(f"| {metric} | {basis} | {f(rc['cm']['C'][key]['value'])} {ci(rc['cm']['C'][key]['target_b'])} | {f(rp['cm'][CP][key]['value'])} {ci(rp['cm'][CP][key]['target_b'])} |")
    p("\n#### N9 rule tests on the unmatched BL-6 events (rules 1-3; rules 4 and 5 not evaluated, CR-029)\n")
    p("\"unresolved\" here means not attributed by rules 1-3.\n")
    p("| column | unmatched events | false_alert | duplicate_alert | evidence_unavailable | perception | tracking | unresolved | ceiling: perception / tracking / unresolved | eye level: perception / tracking / unresolved |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for name in ("C", CP):
        d = n9["columns"][name]
        ps = d["primary_stage"]
        g = lambda v, k: ps[v].get(k, 0)
        p(f"| {name} | {d['unmatched_events']} | {d['by_match_type'].get('false_alert', 0)} | {d['by_match_type'].get('duplicate_alert', 0)} | "
          f"{g('all', 'evidence_unavailable')} | {g('all', 'perception')} | {g('all', 'tracking')} | {g('all', 'unresolved')} | "
          f"{g('ceiling', 'perception')} / {g('ceiling', 'tracking')} / {g('ceiling', 'unresolved')} | {g('eye_level', 'perception')} / {g('eye_level', 'tracking')} / {g('eye_level', 'unresolved')} |")
    p("\nDescriptive cross-check (not an N9 rule): overlap in time with a reference interaction of the same identity pair.\n")
    p("| column | pair unresolved | no reference of the pair | reference of the pair, no overlap | overlap, temporal IoU < 0.3 (iou_m) | overlap ≥ 0.3 |")
    p("|---|---|---|---|---|---|")
    for name in ("C", CP):
        s = n9["columns"][name]["same_pair_reference"]
        p(f"| {name} | {s['pair_unresolved']} | {s['no_reference_of_pair']} | {s['reference_of_pair_no_overlap']} | {s['overlap_below_iou_m']} | {s['overlap_at_or_above_iou_m']} |")
    p("\n#### CR-007 / D-8 evidence: column B forklift position error along and across the viewing direction\n")
    p("Error = estimate − simulator footprint centre. Line of sight: from the camera's floor point to the true position; "
      "along < 0 means the estimate lies between the camera and the true centre. Optical axis: the camera's axis projected on the floor.\n")
    p("| viewpoint | n | error median / P95 (m) | line of sight: along, signed median | along |·| median / P95 | across median / P95 | share beyond the truth | optical axis: along signed median | across median / P95 | camera-to-object distance median (m) |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for v in ("all", "ceiling", "eye_level"):
        d = ce["decomposition"][v]
        L, A = d["los"], d["axis"]
        p(f"| {v} | {d['n']} | {f(d['error_median_m'])} / {f(d['error_p95_m'])} | {f(L['along_signed_median_m'])} | {f(L['along_abs_median_m'])} / {f(L['along_abs_p95_m'])} | "
          f"{f(L['across_median_m'])} / {f(L['across_p95_m'])} | {pct(L['share_along_beyond_truth'])} | {f(A['along_signed_median_m'])} | {f(A['across_median_m'])} / {f(A['across_p95_m'])} | {f(d['distance_median_m'])} |")
    p(f"\nColumn B events for cameras (one worker–forklift pair each: {ce['one_pair_per_camera']}) by median forklift error:\n")
    p("| group | cameras (ceiling / eye level) | configuration | EV-M1 | matched / assessable | EV-M2 | matched / system |")
    p("|---|---|---|---|---|---|---|")
    for g in ("below_1m", "at_or_above_1m"):
        d = ce["ev_split"][g]
        for bl in CFG:
            e = d["ev_B"][bl]
            c = e["counts"]
            p(f"| {g.replace('_', ' ')} | {d['cameras']} ({d['by_viewpoint']['ceiling']} / {d['by_viewpoint']['eye_level']}) | {bl} | {f(e['EV-M1'])} | {c['m']} / {c['a']} | {f(e['EV-M2'])} | {c['m_s']} / {c['s']} |")
    p("\n#### C' runtime (this laptop, mains power, no other agent)\n")
    p("| stage | total |")
    p("|---|---|")
    for k, v in rp["runtime_s"].items():
        if k.startswith("s2"):
            continue
        p(f"| {k} | {v / 3600:.2f} h ({v:.0f} s) |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
