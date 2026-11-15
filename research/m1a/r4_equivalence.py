"""D-38 A.1 / AR-58 acceptance check on ALL SDG validation pair-frames: the code before the speed-up (commit 5780320)
against the code after it.

  PYTHONPATH=<src of one code tree> python research/m1a/r4_equivalence.py dump <label> <out_dir> [workers]
  python research/m1a/r4_equivalence.py compare <out_dir> <label_old> <label_new> <summary.json>

`dump` writes one pickle per camera (<out_dir>/<label>/<rec_id>.pkl, written atomically; finished cameras are skipped on
a restart). Per geometry (simulator_truth, full_camera): the S4 pair_series rows and, for BL-2 .. BL-6 at the base
values, the S5 flag_series and episode rows. `compare` applies the acceptance rule of D-38 A.1:
  - every pair_series field identical, except ttc_s and pet_pred_s, which may differ by <= 1e-6 s (null and null reasons identical);
  - every C_by_R4 value and every S5 flag_series and episode field identical (labels, flags, boundaries).
Fields that carry an upstream artifact ID are compared too and reported separately (they change whenever any S4 value
changes, bit-identity not being required).
"""
from __future__ import annotations

import json
import math
import os
import pickle
import sys
from multiprocessing import Pool

TOL_S = 1e-6
GEOMETRIES = ("simulator_truth", "full_camera")


def _dump_one(args):
    label, out_dir, rec_id = args
    import m1a_common as m
    path = os.path.join(out_dir, label, f"{rec_id}.pkl")
    if os.path.exists(path):
        return rec_id, "skipped"
    ctx = m.Context("sdg")
    data = m.load(ctx, rec_id)
    s3_art, positions, _ = m.s3(ctx, rec_id, data, m.S4_BASE["g_max"], "equivalence")
    result = {"rec_id": rec_id}
    for geometry in GEOMETRIES:
        s4_art = m.s4(ctx, data, s3_art, positions, geometry, m.S4_BASE, "equivalence")
        if s4_art is None:
            result[geometry] = None
            continue
        g = {"s4_id": s4_art.artifact_id, "pair_series": s4_art.tables["pair_series"], "s5": {}}
        for bl in m.BASELINES:
            a = m.s5_build(ctx, data, s4_art, bl, m.S4_BASE, m.S5_BASE, "equivalence")
            g["s5"][bl] = {"artifact_id": a.artifact_id, "flag_series": a.tables["flag_series"], "episode": a.tables.get("episode", [])}
        result[geometry] = g
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(result, f)
    os.replace(tmp, path)
    return rec_id, "done"


def dump(label: str, out_dir: str, workers: int) -> None:
    sys.path.insert(0, os.path.dirname(__file__))
    import m1a_common as m
    os.makedirs(os.path.join(out_dir, label), exist_ok=True)
    recs = [c["rec_id"] for c in m.Context("sdg").validation_cameras()]
    print(f"{label}: {len(recs)} validation cameras", flush=True)
    with Pool(workers) as pool:
        for n, (rec, status) in enumerate(pool.imap_unordered(_dump_one, [(label, out_dir, r) for r in recs]), 1):
            print(n, rec, status, flush=True)


def _key(row):
    return (json.dumps(row.get("pow_nk") or row.get("pow_id"), sort_keys=True), row.get("frame_index"), row.get("start_frame"))


ID_FIELDS = {"pow_id", "episode_id", "flag_series_id", "s4_artifact_id"}  # reported separately if they differ


def _cmp_rows(old, new, where, tol_fields, out):
    if len(old) != len(new):
        out["row_count"].append({"where": where, "old": len(old), "new": len(new)})
        return
    for a, b in zip(sorted(old, key=_key), sorted(new, key=_key)):
        if set(a) != set(b):
            out["field_sets"].append({"where": where, "key": _key(a)})
            continue
        for f in a:
            x, y = a[f], b[f]
            if x == y:
                continue
            if f in tol_fields and isinstance(x, float) and isinstance(y, float):
                d = abs(x - y)
                out["max_abs_diff"][f] = max(out["max_abs_diff"].get(f, 0.0), d)
                out["n_diff"][f] = out["n_diff"].get(f, 0) + 1
                if not d <= TOL_S:
                    out["beyond_tolerance"].append({"where": where, "key": _key(a), "field": f, "old": x, "new": y})
                continue
            target = "id_fields" if f in ID_FIELDS or f.endswith("_id") else "mismatch"
            out[target].append({"where": where, "key": _key(a), "field": f, "old": repr(x)[:200], "new": repr(y)[:200]})


def compare(out_dir: str, old_label: str, new_label: str, summary_path: str) -> int:
    out = {"cameras": 0, "pair_frames": {g: 0 for g in GEOMETRIES}, "pair_frames_with_pet": 0, "pair_frames_with_ttc": 0, "r4_frames": 0,
           "row_count": [], "field_sets": [], "mismatch": [], "id_fields": [], "beyond_tolerance": [], "max_abs_diff": {}, "n_diff": {}, "missing": []}
    names = sorted(os.listdir(os.path.join(out_dir, old_label)))
    for name in names:
        if not name.endswith(".pkl"):
            continue
        new_path = os.path.join(out_dir, new_label, name)
        if not os.path.exists(new_path):
            out["missing"].append(name)
            continue
        old, new = (pickle.load(open(os.path.join(out_dir, lab, name), "rb")) for lab in (old_label, new_label))
        out["cameras"] += 1
        for g in GEOMETRIES:
            if (old[g] is None) != (new[g] is None):
                out["mismatch"].append({"where": f"{name}/{g}", "field": "geometry run present"})
                continue
            if old[g] is None:
                continue
            ps_old, ps_new = old[g]["pair_series"], new[g]["pair_series"]
            out["pair_frames"][g] += len(ps_old)
            out["pair_frames_with_pet"] += sum(r["pet_pred_s"] is not None for r in ps_old)
            out["pair_frames_with_ttc"] += sum(r["ttc_s"] is not None for r in ps_old)
            _cmp_rows(ps_old, ps_new, f"{name}/{g}/pair_series", {"ttc_s", "pet_pred_s"}, out)
            for bl in old[g]["s5"]:
                o, n = old[g]["s5"][bl], new[g]["s5"][bl]
                out["r4_frames"] += sum(1 for r in o["flag_series"] if "R4" in (r.get("C_by_provider") or {}))
                for table in ("flag_series", "episode"):
                    _cmp_rows(o[table], n[table], f"{name}/{g}/{bl}/{table}", set(), out)
    out["accepted"] = not (out["row_count"] or out["field_sets"] or out["mismatch"] or out["beyond_tolerance"] or out["missing"])
    for k in ("mismatch", "id_fields", "beyond_tolerance"):
        out[f"{k}_count"] = len(out[k])
        out[k] = out[k][:50]
    with open(summary_path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, indent=1))
    return 0 if out["accepted"] else 1


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 3)
    else:
        sys.exit(compare(*sys.argv[2:6]))
