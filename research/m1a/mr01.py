"""MR-01 (N8; criterion C1-MR-01): every exact-class artifact ID of the repeat run equals the first run's.
  python research/m1a/mr01.py <ds> <label_a> <label_b>  -> research/m1a/mr01_<ds>.json
Compares every unit record (base, full_camera, reference, sweeps) field by field, except the wall-clock `seconds`.
Value 1.0 iff every compared record is identical (AR-57 item 5)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
ds, a, b = sys.argv[1:4]
da, db = ROOT / "out/m1a" / a / ds, ROOT / "out/m1a" / b / ds
out = {"dataset": ds, "runs": [a, b], "units_compared": 0, "artifact_ids_compared": 0, "differences": [], "missing": []}


def ids(o):
    if isinstance(o, dict):
        return sum(ids(v) for v in o.values())
    if isinstance(o, list):
        return sum(ids(v) for v in o)
    return 1 if isinstance(o, str) and o.startswith("art_") else 0


for rec in sorted(p.name for p in da.iterdir() if p.name.startswith("rec_")):
    for unit in ("base", "full_camera", "reference", "sweeps"):
        pa, pb = da / rec / f"{unit}.json", db / rec / f"{unit}.json"
        if not pa.exists() or not pb.exists():
            out["missing"].append(f"{rec}/{unit}")
            continue
        x, y = json.loads(pa.read_text()), json.loads(pb.read_text())
        x.pop("seconds"), y.pop("seconds")
        out["units_compared"] += 1
        out["artifact_ids_compared"] += ids(x)
        if x != y:
            out["differences"].append(f"{rec}/{unit}")
out["value"] = 1.0 if not out["differences"] and not out["missing"] else 0.0
(ROOT / f"research/m1a/mr01_{ds}.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k not in ("differences", "missing")} | {"n_differences": len(out["differences"]), "n_missing": len(out["missing"])}))
