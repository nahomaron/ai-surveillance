"""D-25 Architect review item 1a: P99 - P1 of luma (nearest rank) on every frame flagged `black` by rv2-provisional,
grouped (i) red-lit runs, (ii) frames already judged truly blank, (iii) all others. Statistics only, no pixels.
Usage: PYTHONPATH=src python rv2_sflat_evidence.py <members_check.json> <data_root> <out.json>"""
import collections
import json
import sys

from rq1.decode import quality, timestamps, video
from rq1.decode.timestamps import DecodeConfig

RED_LIT = ("run_43_seed_631373023", "run_6_seed_1833142794")  # group (i)
BLANK = ("run_18_seed_1313717419.eye_00", range(21, 103))  # group (ii): D-25 record, frames 21-102 (seq)
cfg = DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=quality.RV2_PROVISIONAL, declared={})


def group(rec, seq):
    if any(r in rec for r in RED_LIT):
        return "i_red_lit"
    if BLANK[0] in rec and seq in BLANK[1]:
        return "ii_judged_blank"
    return "iii_other"


def summary(v):
    v = sorted(v)
    q = lambda p: v[-(-p * len(v) // 100) - 1]  # nearest rank
    return {"n": len(v), "min": v[0], "p1": q(1), "p5": q(5), "p50": q(50), "p95": q(95), "p99": q(99), "max": v[-1],
            "hist": dict(sorted(collections.Counter(v).items()))}


check = json.load(open(sys.argv[1]))
spread, per_rec = collections.defaultdict(list), []
for r in check["recordings"]:
    if not r["flags"].get("black"):
        continue
    packets, info = video.read_packets(f"{sys.argv[2]}/{r['recording']}", luma_stats=True)
    res = timestamps.resolve(packets, info.time_base, cfg, None)
    luma = {p.seq: p.luma for p in packets}
    rows = collections.defaultdict(list)
    for f in res.frames:
        if "black" in f.quality_flags:
            s = luma[f.seq]
            rows[group(r["recording"], f.seq)].append((f.seq, s.p99 - s.p1))
    for g, v in sorted(rows.items()):
        spread[g] += [d for _, d in v]
        per_rec.append({"recording": r["recording"], "group": g, "black_frames": len(v),
                        "seq_min": min(s for s, _ in v), "seq_max": max(s for s, _ in v),
                        "spread_min": min(d for _, d in v), "spread_max": max(d for _, d in v)})
        print(per_rec[-1], flush=True)
out = {"rules_version": quality.RV2_PROVISIONAL, "statistic": "P99(Y) - P1(Y), nearest rank, frames flagged black",
       "groups": {g: summary(v) for g, v in sorted(spread.items())}, "recordings": per_rec}
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(json.dumps(out["groups"], indent=1))
