"""D-25 ruling (13 Nov 2026), item A: frame-quality flag counts, low_light tags and the per-frame spread (P99 - P1) of dark
frames (P99 <= 32) for each recording under a pixel rules version. Statistics only, no pixels.
low_light is reported under the implemented reading (median P99 over non-black frames, AR-49) and, for comparison, the
other reading (median P99 over all decoded frames, recording not entirely black).
Usage: PYTHONPATH=src python -I rv2_check.py <rules_version> <data_root> <out.json> <list.json|video> [...]
A .json argument is a previous check file; its recordings (paths relative to data_root's parent `data/`) are used."""
import collections
import json
import multiprocessing
import os
import statistics
import sys

from rq1.decode import quality, timestamps, video
from rq1.decode.timestamps import DecodeConfig

VERSION, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=VERSION, declared={})


def one(rel):
    packets, info = video.read_packets(os.path.join(ROOT, rel), luma_stats=True)
    r = timestamps.resolve(packets, info.time_base, cfg, None)
    luma = [p.luma for p in packets if p.decode_ok and p.luma is not None]
    p99_all = [s.p99 for s in luma]
    any_kept = any("black" not in quality.frame_flags(s, VERSION) for s in luma)
    dark_spread = collections.Counter(s.p99 - s.p1 for s in luma if s.p99 <= quality.BLACK_P99_MAX)
    return {"recording": rel, "frames": len(r.frames), "eligible": sum(f.eligible for f in r.frames),
            "flags": dict(sorted(collections.Counter(x for f in r.frames for x in f.quality_flags).items())),
            "condition_tags": r.condition_tags, "median_p99_all": float(statistics.median(p99_all)),
            "low_light_other_reading": bool(any_kept and statistics.median(p99_all) <= quality.LOW_LIGHT_MEDIAN_P99_MAX),
            "p99_min": min(p99_all), "p99_max": max(p99_all),
            "dark_frames": sum(dark_spread.values()), "dark_spread_hist": {str(k): v for k, v in sorted(dark_spread.items())}}


def main():
    recs = []
    for a in sys.argv[4:]:
        recs += [r["recording"] for r in json.load(open(a))["recordings"]] if a.endswith(".json") else [a]
    recs = sorted(set(recs))
    with multiprocessing.Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        rows = pool.map(one, recs, chunksize=1)
    tot = collections.Counter()
    for r in rows:
        tot.update(r["flags"])
    summary = {"recordings": len(rows), "frames": sum(r["frames"] for r in rows), "eligible": sum(r["eligible"] for r in rows),
               "flag_frames": dict(sorted(tot.items())),
               "recordings_with_flag": {k: sum(1 for r in rows if k in r["flags"]) for k in sorted(tot)},
               "low_light": [r["recording"] for r in rows if "low_light" in r["condition_tags"]],
               "low_light_other_reading": [r["recording"] for r in rows if r["low_light_other_reading"]]}
    json.dump({"rules_version": VERSION, "summary": summary, "recordings": rows}, open(OUT, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
