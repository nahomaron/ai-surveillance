import json, sys, time
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT / "research/datasets/part3"))
import t17_oracle as drv
from rq1.adapters import oracle_truth as ot
index = [e for e in json.load(open(ROOT / "out/s0_smartspaces/index.json")) if e["run"] == "Warehouse_000"]
ann = drv.Annotations(str(ROOT / "data")); total = 0; out = []
t0 = time.time()
for e in sorted(index, key=lambda e: e["camera"]):
    frames, classes = drv.smartspaces_frames(e, ann, 9000, {})
    tracks, _ = ot.camera_tracks(e["calibration"], frames, 15, frozenset())
    occ = {k: {p.decode_seq for p in pts} for k, pts in tracks.items()}
    persons = [k for k in occ if classes[k] == "person"]; forks = [k for k in occ if classes[k] == "forklift"]
    n = sum(len(occ[p] & occ[f]) for p in persons for f in forks)
    out.append((e["camera"], len(persons), len(forks), n)); total += n
    print(e["camera"], len(persons), len(forks), n, round(time.time() - t0), flush=True)
print("TOTAL pair-frames", total)
