"""T-25p: markdown tables for `reports/M1b_pilot_report.md` from `pilot_results.json`, `pilot_frame_check.json` and
`pilot_tracker_loss.json` (Owner revision of 19 Nov 2026, items 2d and 5).

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
    tl = json.load(open(ROOT / "research/m1b/pilot_tracker_loss.json"))
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
    p(f"IDF1 is pooled over the {r['cameras']} cameras by summing IDTP, IDFP and IDFN per class, then IDF1 = IDTP / (IDTP + 0.5 IDFP + 0.5 IDFN). "
      "n below: reference boxes (IDTP + IDFN) and system points (IDTP + IDFP).\n")
    p("| class | tracks | one_to_one | id_switch | fragment | unmatched_system | identity switches | identities never matched | IDF1 | IDTP / IDFP / IDFN | n references / system points |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        t = r["tracking"][c]
        s = t["status"]
        p(f"| {c} | {t['tracks']} | {s['one_to_one']} | {s['id_switch']} | {s['fragment']} | {s['unmatched_system']} | {t['n_switches']} | "
          f"{t['missed_identities']} | {f(t['IDF1'], 3)} | {t['IDTP']:.0f} / {t['IDFP']:.0f} / {t['IDFN']:.0f} | {t['IDTP'] + t['IDFN']:.0f} / {t['IDTP'] + t['IDFP']:.0f} |")
    p("\nBridging (D-45 item 1):\n")
    p("| class | tracked points | predicted points (bridged) | runs bridged | runs lost (> 15) | frames lost in long runs |")
    p("|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        b = r["tracking"][c]["bridging"]
        p(f"| {c} | {b['tracked']} | {b['predicted']} | {b['runs_bridged']} | {b['runs_lost']} | {b['lost_long_run']} |")
    t_all = tl["results"]["all"]
    p("\n### Detections by score band, reference match and tracking (column C, all pilot frames; `tracker_loss.py`)\n")
    p("Bands: class threshold (person 0.20, forklift 0.05) to 0.10, 0.10 to 0.25, 0.25 and above (ByteTrack's default track_low_thresh "
      "and track_high_thresh). Matched: matched to a reference-visible box by the probe matcher (IoU ≥ 0.3) among all S2 detections "
      "of the frame. Tracked: the detection became a `tracked` S3 point.\n")
    p("| class | band | detections | matched, tracked | matched, not tracked | unmatched, tracked | unmatched, not tracked | share of matched that were tracked |")
    p("|---|---|---|---|---|---|---|---|")
    for c in ("person", "forklift"):
        for bnd in tl["bands"]:
            k = t_all["bands"][c][bnd]
            n = sum(k.values())
            if n == 0:
                p(f"| {c} | {bnd} | 0 (empty: the class threshold is above 0.10) | — | — | — | — | — |" if c == "person" and bnd.startswith("[thr") else f"| {c} | {bnd} | 0 | — | — | — | — | — |")
                continue
            mt = k["matched_tracked"] + k["matched_not_tracked"]
            p(f"| {c} | {bnd} | {n} | {k['matched_tracked']} | {k['matched_not_tracked']} | {k['unmatched_tracked']} | {k['unmatched_not_tracked']} | {pct(k['matched_tracked'] / mt if mt else None)} |")
    p("\nFrame-level recall stage by stage (same references and matcher; matched references / reference boxes):\n")
    p("| viewpoint | class | reference boxes | S2 detections (after thresholds) | tracked S3 points | tracked + predicted S3 points |")
    p("|---|---|---|---|---|---|")
    for v in ("all", "ceiling", "eye_level"):
        for c in ("person", "forklift"):
            st = tl["results"][v]["stages"][c]
            n = st["references"]
            p(f"| {v} | {c} | {n} | {f(st['s2'] / n)} ({st['s2']}) | {f(st['tracked'] / n)} ({st['tracked']}) | {f(st['tracked_predicted'] / n)} ({st['tracked_predicted']}) |")
    p("\n### Position accuracy (D-41), columns B and C\n")
    p("| column | class | evidence class | n | median (m) | P95 (m) | > 1 m | > 2 m | > 5 m |")
    p("|---|---|---|---|---|---|---|---|---|")
    for col in ("B", "C"):
        for key, e in r["position"][col]["error"].items():
            cls, evc = key.split("|")
            if e["n"] == 0:
                continue
            p(f"| {col} | {cls} | {evc} | {e['n']} | {f(e['median_m'])} | {f(e['p95_m'])} | {pct(e['share_gt_1m'])} | {pct(e['share_gt_2m'])} | {pct(e['share_gt_5m'])} |")
    p("\nDenominators: column B scores every object-frame with a position (oracle tracks carry their identity). Column C scores an "
      "object-frame only when its track is matched to an identity on that frame (A5.2 `matched`):\n")
    p("| column | class | object-frames with a position | scored (error computed) | with a position, no matched identity (not scored) |")
    p("|---|---|---|---|---|")
    for col in ("B", "C"):
        for c in ("person", "forklift"):
            a = r["position"][col]["availability"][c]
            pos = a.get("position", {"n": 0})["n"]
            nm = a.get("position_without_matched_identity", {"n": 0})["n"]
            p(f"| {col} | {c} | {pos} | {r['position'][col]['error'][f'{c}|all']['n']} | {nm} |")
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
