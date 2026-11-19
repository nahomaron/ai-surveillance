"""T-25p: markdown tables for `reports/M1b_pilot_report.md` from `pilot_results.json` and `pilot_frame_check.json`.

  PYTHONPATH=src .venv/bin/python research/m1b/pilot_report_tables.py > out/m1b/pilot/tables.md
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLS = {"A": "A oracle, simulator positions", "B": "B oracle boxes, full_camera", "C": "C detector path"}
CFG = ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6")


def f(v, n=2):
    return "—" if v is None else f"{v:.{n}f}"


def ci(v, n=2):
    return "—" if not v else f"[{v[0]:.{n}f}, {v[1]:.{n}f}]"


def pct(v, n=1):
    return "—" if v is None else f"{100 * v:.{n}f} %"


def main():
    r = json.load(open(ROOT / "research/m1b/pilot_results.json"))
    fc = json.load(open(ROOT / "research/m1b/pilot_frame_check.json"))
    out = []
    p = out.append
    p(f"Cameras: {r['cameras']} ({r['viewpoints']['ceiling']} ceiling, {r['viewpoints']['eye_level']} eye-level); leakage groups: "
      f"{r['leakage_groups']}; references: {r['references']['n']} ({r['references']['assessable']} assessable, {r['references']['g1']} in G1).\n")
    p("### EV-M1 (recall) and EV-M2 (precision), label group G1, with Target B intervals\n")
    p("| configuration | column | EV-M1 | Target B | matched / assessable | EV-M2 | Target B | matched / system | episodes | candidate events |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for bl in CFG:
        for col in COLS:
            e = r["ev"][col][bl]
            c = e["counts"]
            p(f"| {bl} | {col} | {f(e['EV-M1'])} | {ci(e['EV-M1_target_b'])} | {c['m']} / {c['a']} | {f(e['EV-M2'])} | {ci(e['EV-M2_target_b'])} | "
              f"{c['m_s']} / {c['s']} | {e['runs']['episodes']} | {e['runs']['events']} |")
    p("\n### Per-label recall and precision (O, H, PC; descriptive, D-40 item 5)\n")
    p("| configuration | column | O recall | O precision | H recall | H precision | PC recall | PC precision |")
    p("|---|---|---|---|---|---|---|---|")
    for bl in CFG:
        for col in COLS:
            L = r["labels"][col][bl]
            p(f"| {bl} | {col} | " + " | ".join(f"{f(L[x]['recall'])} | {f(L[x]['precision'])}" for x in ("O", "H", "PC")) + " |")
    p("\n### Detection, frame level, all pilot frames (column C; probe matcher, IoU ≥ 0.3)\n")
    p("| viewpoint | class | recall | precision | TP / references / detections |")
    p("|---|---|---|---|---|")
    for v in ("all", "ceiling", "eye_level"):
        for c in ("person", "forklift"):
            d = r["detection"][v][c]
            p(f"| {v} | {c} | {f(d['recall'])} | {f(d['precision'])} | {d['tp']} / {d['references']} / {d['detections']} |")
    p("\n### Frame-level check, 100 frames on 20 pilot cameras (item 3c), fixed thresholds\n")
    p("| model | viewpoint | class | recall | precision | TP / references / detections |")
    p("|---|---|---|---|---|---|")
    for mdl, name in (("yolo_world", "YOLO-World v2-s"), ("grounding_dino", "Grounding DINO tiny")):
        for v in ("all", "ceiling", "eye_level"):
            for c in ("person", "forklift"):
                d = fc["models"][mdl]["results"][v][c]
                p(f"| {name} | {v} | {c} | {f(d['recall'])} | {f(d['precision'])} | {d['tp']} / {d['references']} / {d['detections']} |")
    p("\n### Tracking (column C; T-12 association at iou_cm 0.5; IDF1 per class)\n")
    p("| class | tracks | one_to_one | id_switch | fragment | unmatched_system | identity switches | identities never matched | IDF1 | IDTP / IDFP / IDFN |")
    p("|---|---|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        t = r["tracking"][c]
        s = t["status"]
        p(f"| {c} | {t['tracks']} | {s['one_to_one']} | {s['id_switch']} | {s['fragment']} | {s['unmatched_system']} | {t['n_switches']} | "
          f"{t['missed_identities']} | {f(t['IDF1'], 3)} | {t['IDTP']:.0f} / {t['IDFP']:.0f} / {t['IDFN']:.0f} |")
    p("\nBridging (D-45 item 1) and detections by ByteTrack score band:\n")
    p("| class | tracked points | predicted points (bridged) | runs bridged | runs lost (> 15) | frames lost in long runs | detections ≥ 0.25 | in (0.10, 0.25) | ≤ 0.10 |")
    p("|---|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        b, s = r["tracking"][c]["bridging"], r["score_bands"][c]
        p(f"| {c} | {b['tracked']} | {b['predicted']} | {b['runs_bridged']} | {b['runs_lost']} | {b['lost_long_run']} | {s['ge_high']} | {s['low_to_high']} | {s['le_low']} |")
    p("\n### Position accuracy (D-41), columns B and C\n")
    p("| column | class | evidence class | n | median (m) | P95 (m) | > 1 m | > 2 m | > 5 m |")
    p("|---|---|---|---|---|---|---|---|---|")
    for col in ("B", "C"):
        for key, e in r["position"][col]["error"].items():
            cls, evc = key.split("|")
            if e["n"] == 0:
                continue
            p(f"| {col} | {cls} | {evc} | {e['n']} | {f(e['median_m'])} | {f(e['p95_m'])} | {pct(e['share_gt_1m'])} | {pct(e['share_gt_2m'])} | {pct(e['share_gt_5m'])} |")
    p("\nPosition availability (object-frames of the S4 run; share by null reason):\n")
    p("| column | class | object-frames | with a position | by null reason | position but no matched identity (not scored) |")
    p("|---|---|---|---|---|---|")
    for col in ("B", "C"):
        for c in ("person", "forklift"):
            a = r["position"][col]["availability"][c]
            nulls = ", ".join(f"{k[5:]} {v['n']} ({pct(v['share'])})" for k, v in a.items() if k.startswith("null:")) or "none"
            pos = a.get("position", {"n": 0, "share": None})
            nm = a.get("position_without_matched_identity", {"n": 0})["n"]
            p(f"| {col} | {c} | {a['object_frames']} | {pos['n']} ({pct(pos['share'])}) | {nulls} | {nm} |")
    p("\n### Completeness (ratio of sums; Target B intervals)\n")
    p("| metric | basis | " + " | ".join(COLS[c] for c in COLS) + " |")
    p("|---|---|---|---|---|")
    for key in sorted(r["cm"]["A"]):
        metric, basis = key.split(" ", 1)
        p(f"| {metric} | {basis} | " + " | ".join(f"{f(r['cm'][c][key]['value'])} {ci(r['cm'][c][key]['target_b'])}" for c in COLS) + " |")
    p("\n### Runtime (this laptop: Intel Core i7-5650U, 2 cores, CPU only)\n")
    p("| stage | total |")
    p("|---|---|")
    names = {"s2_detector": "S2 YOLO-World inference (sum of per-frame times)", "s2_wall": "S2 wall time incl. decoding and pipe",
             "s2_build": "S2 artifact build", "s3_track": "S3 ByteTrack (incl. `.venv-det` start) and S3 build", "s4": "S4 full_camera", "s5": "S5 BL-2..BL-6 (5 configurations)"}
    for k, v in r["runtime_s"].items():
        p(f"| {names.get(k, k)} | {v / 3600:.2f} h ({v:.0f} s) |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
