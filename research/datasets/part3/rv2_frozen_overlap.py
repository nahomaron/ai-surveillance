"""Architect, 13 Nov 2026, item 2 (D-25 evidence): for every `frozen` frame under `rv2`, whether it is also `black`, and the
spread (P99 - P1) of any that are not. Statistics only, no pixels.
Usage: PYTHONPATH=src python -I rv2_frozen_overlap.py <data_root> <out.json> <check.json>
Recordings: those with a `frozen` flag in the given rv2 check file."""
import collections
import json
import os
import sys

from rq1.decode import quality, timestamps, video
from rq1.decode.timestamps import DecodeConfig

ROOT, OUT, CHECK = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=quality.RV2, declared={})


def ranges(seqs):
    out = []
    for s in sorted(seqs):
        if out and s == out[-1][1] + 1:
            out[-1][1] = s
        else:
            out.append([s, s])
    return out


rows = []
for rel in [r["recording"] for r in json.load(open(CHECK))["recordings"] if "frozen" in r["flags"]]:
    packets, info = video.read_packets(os.path.join(ROOT, rel), luma_stats=True)
    r = timestamps.resolve(packets, info.time_base, cfg, None)
    luma = {p.seq: p.luma for p in packets}
    frozen = [f for f in r.frames if "frozen" in f.quality_flags]
    not_black = [f for f in frozen if "black" not in f.quality_flags]
    rows.append({"recording": rel, "frozen": len(frozen), "frozen_and_black": len(frozen) - len(not_black),
                 "frozen_seq_ranges": ranges(f.seq for f in frozen),
                 "frozen_p99_hist": {str(k): v for k, v in sorted(collections.Counter(luma[f.seq].p99 for f in frozen).items())},
                 "frozen_spread_hist": {str(k): v for k, v in sorted(collections.Counter(luma[f.seq].p99 - luma[f.seq].p1 for f in frozen).items())},
                 "not_black_seq_ranges": ranges(f.seq for f in not_black),
                 "not_black_spread_hist": {str(k): v for k, v in sorted(collections.Counter(luma[f.seq].p99 - luma[f.seq].p1 for f in not_black).items())}})
summary = {"frozen": sum(x["frozen"] for x in rows), "frozen_and_black": sum(x["frozen_and_black"] for x in rows)}
json.dump({"rules_version": quality.RV2, "summary": summary, "recordings": rows}, open(OUT, "w"), indent=1)
print(json.dumps({"summary": summary, "recordings": rows}, indent=1))
