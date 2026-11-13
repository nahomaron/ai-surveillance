"""D-25 step 1: rv2-provisional flag counts on every held synthetic recording (expected 0). Statistics only.
Usage: PYTHONPATH=src python rv2_synthetic_check.py <out.json> <video> [<video> ...]"""
import collections
import json
import sys
from fractions import Fraction

from rq1.decode import quality, timestamps, video
from rq1.decode.timestamps import DecodeConfig

cfg = DecodeConfig(k_sup=1.5, f_untimed=0.05, f_sub=0.1, rules_version=quality.RV2_PROVISIONAL, declared={})
out = []
for path in sys.argv[2:]:
    packets, info = video.read_packets(path, luma_stats=True)
    r = timestamps.resolve(packets, info.time_base, cfg, None)
    counts = collections.Counter(flag for f in r.frames for flag in f.quality_flags)
    p99 = [p.luma.p99 for p in packets if p.luma]
    out.append({"recording": path.split("data/", 1)[-1], "frames": len(r.frames), "flags": dict(sorted(counts.items())),
                "p99_min": min(p99), "p99_max": max(p99), "eligible": sum(f.eligible for f in r.frames)})
    print(out[-1], flush=True)
json.dump({"rules_version": quality.RV2_PROVISIONAL, "recordings": out}, open(sys.argv[1], "w"), indent=1)
