"""T-21, G-M1a ruling D-40 item 5 (17 Nov 2026): descriptive per-label breakdown (O, H, PC) of recall and precision per
configuration on SDG validation. Not a pre-registered metric; no interval is a decision input.

For label L: references = T21 references whose labels include L (assessable ones are scored, as in EV-M1);
system events = S_VIEW candidate events whose labels include L. Matching: `matching.match_window` unchanged (same pair
condition, iou_m, N4 assignment), run on these two subsets with every reference in one group ("any"; no event abstains
in it, T10.7(a)). recall_L = matched / assessable references with L; precision_L = matched / system events with L.
Target A interval (stratified window bootstrap) as in aggregate_m1a. Simulator_truth geometry (base run).

  python research/m1a/ev_by_label.py run1   -> research/m1a/ev_by_label_sdg.json
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import aggregate_m1a as agg  # noqa: E402
import evaluate_m1a as ev  # noqa: E402
import m1a_common as m  # noqa: E402
from rq1.evaluation import association as assoc  # noqa: E402
from rq1.evaluation import estimators as est  # noqa: E402
from rq1.evaluation import matching as mt  # noqa: E402

LABELS3 = ("O", "H", "PC")


def camera(label, rec):
    cam = ev.Camera("sdg", label, rec)
    m.Context("sdg").camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    support = cam.support()
    base = cam.units["base"]
    s3 = ev.load_art(label, "sdg", base["s3"])
    trk_key = ev.track_map(s3, ev.oracle_keys(cam.visible), cam.classes)
    rows, _, _ = ev.association(s3, trk_key)
    summaries, _ = assoc.summarize(rows, {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}})
    refs, _ = ev.references(cam)
    ref_labels = {}
    for ref, r in zip(refs, cam.units["reference"]["references"]):
        ref_labels[ref.ref_event_id] = frozenset(x for x in LABELS3 if r[f"lbl_{x}"])
    s4 = ev.load_art(label, "sdg", base["s4"])
    out = {"stratum": cam.window["stratum_id"], "leakage_group": cam.window["leakage_group_id"], "counts": {}}
    for bl, art in base["s5"].items():
        events = ev.system_events(s4, ev.load_art(label, "sdg", art), rows, summaries)
        for lab in LABELS3:
            rs = [r for r in refs if lab in ref_labels[r.ref_event_id]]
            es = [e for e in events if lab in e.labels]
            rec_ = mt.match_window(rs, es, "any", ev.S8["iou_m"], "rule_conformance", {r.ref_event_id: frozenset({"any"}) for r in rs})
            kinds = [r["match_type"] for r in rec_]
            out["counts"][(bl, lab)] = {"assessable": kinds.count("matched") + kinds.count("miss") + kinds.count("abstained_miss"),
                                        "matched": kinds.count("matched"), "system": len(es),
                                        "false_alert": kinds.count("false_alert"), "duplicate": kinds.count("duplicate_alert")}
    return out


def target_a(rows):
    """Stratified window bootstrap (Target A) of sum y / sum x; None when the denominator is 0, or when a resample has
    a zero denominator (rare labels)."""
    if sum(x for _, x, _ in rows) == 0:
        return None
    strata = defaultdict(list)
    for st, x, y in rows:
        strata[st].append((x, y))
    try:
        ci = list(est.stratified_bootstrap_ratio(dict(strata), {st: 1.0 for st in strata}, ev.S8["B"], ev.S8["seed"]))
    except ZeroDivisionError:
        return None
    return None if any(math.isnan(v) for v in ci) else ci  # resamples without the label (few references): not computable


def main(label):
    recs = sorted(c["rec_id"] for c in m.Context("sdg").validation_cameras())
    cams = []
    for n, rec in enumerate(recs, 1):
        cams.append(camera(label, rec))
        if n % 25 == 0:
            print(n, flush=True)
    res = {"dataset": "sdg", "label": label, "status": "experimental (synthetic, oracle perception, validation partition); descriptive (D-40 item 5)",
           "reading": "agreement with the BL-6 reference definition applied to complete truth (T21.5), per label", "cameras": len(cams), "by_config": {}}
    for bl in agg.CFG:
        res["by_config"][bl] = {}
        for lab in LABELS3:
            c = [(x["stratum"], x["leakage_group"], x["counts"][(bl, lab)]) for x in cams]
            tot = defaultdict(int)
            for *_, d in c:
                for k, v in d.items():
                    tot[k] += v
            recall = target_a([(s, d["assessable"], d["matched"]) for s, g, d in c])
            prec = target_a([(s, d["system"], d["matched"]) for s, g, d in c])
            res["by_config"][bl][lab] = {**tot, "recall": tot["matched"] / tot["assessable"] if tot["assessable"] else None,
                                         "recall_target_a": recall,
                                         "precision": tot["matched"] / tot["system"] if tot["system"] else None,
                                         "precision_target_a": prec}
    p = ev.ROOT / "research/m1a/ev_by_label_sdg.json"
    p.write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", p)
    for bl, d in res["by_config"].items():
        print(bl, {k: (v["assessable"], v["matched"], v["system"], v["recall"] and round(v["recall"], 3), v["precision"] and round(v["precision"], 3)) for k, v in d.items()})


if __name__ == "__main__":
    main(sys.argv[1])
