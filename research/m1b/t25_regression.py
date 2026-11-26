"""D-58 STEP 2 regression (T25.4 "Regression"): with the T25 parameters absent, the stored D-54 and D-57 artifacts at m_gap 5
rebuild byte-identical (same payload SHA-256, same artifact ID) under the T25 code.

  PYTHONPATH=src .venv/bin/python research/m1b/t25_regression.py [workers]   -> research/m1b/t25_regression.json

On every one of the 116 tuning cameras (`v2_sets.tuning()`), for each configuration:
  C-v2    S4 from the stored detector S3 (`out/m1b/v2t24/c`), full_camera, T24 on (`d54_b_v2.run_config`, gate and shift)
  B-both  S4 from the rebuilt ORACLE-S3 (checked against the stored one), full_camera, T24 on
  A       S4 from the rebuilt ORACLE-S3 with simulator positions (stored T-21 `base` unit)
and from each rebuilt S4, S5 BL-6 at m_gap 5 (v1 base values). Every rebuild uses the stored manifest's own specification,
so the artifact ID is comparable: S4 against the stored D-54 S4; S5 against the stored D-54 S5 and against the D-57 sweep's
m_gap 5 artifact (`out/m1b/d57`). Stored artifacts are read, never written. Tuning cameras only (D-58 hard limits).
"""
from __future__ import annotations

import json
import os
import sys
from multiprocessing import Pool
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
C_OUT = ROOT / "out/m1b/v2t24/c"
B_OUT = ROOT / "out/m1b/v2t24/b"
D57 = ROOT / "out/m1b/d57"
M1A = ROOT / "out/m1a/run1/sdg"
BL = "BL-6"


def _manifest(root, art_id):
    return json.loads((root / art_id / "manifest.json").read_text())


def _spec(man) -> "m.Spec":
    s = man["spec"]
    return m.Spec(s["stage"], s["schema_bundle"], s["code_commit"], s["environment_digest"], tuple(s["config_ids"]), tuple(s["input_artifact_ids"]),
                  s["seeds"])


def _tables(root, art_id):
    from rq1.schema import files
    man = _manifest(root, art_id)
    return {f["path"][:-8]: files.read_table(str(root / art_id / f["path"]), f["path"][:-8], m.A.SCHEMA_VERSION) for f in man["files"]}


def _same(built, root, art_id) -> dict:
    man = _manifest(root, art_id)
    return {"stored": art_id, "rebuilt": built.artifact_id, "payload_equal": built.payload_sha256 == man["payload_sha256"],
            "id_equal": built.artifact_id == art_id}


def check_camera(rec: str) -> dict:  # pragma: no cover - driver over stored artifacts
    import d54_b_v2 as b
    from rq1.events import s5
    from rq1.substrate import builder
    ctx = m.Context("sdg")
    unit = json.loads((M1A / rec / "base.json").read_text())
    pipe = json.loads((C_OUT / "cam" / rec / "pipeline.json").read_text())
    brun = json.loads((B_OUT / "cam" / f"{rec}.json").read_text())["runs"]["B-both"]
    sweep = json.loads((D57 / "mgap" / f"{rec}.json").read_text())["configs"]
    data = m.load(ctx, rec)
    s3o, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], (unit["code_commit"], unit["environment_digest"]))
    _, base_cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    t24_cfg, _, _ = b.run_config(base_cfg, gate=True, shift=True)
    s3c = SimpleNamespace(artifact_id=pipe["s3"], tables=_tables(C_OUT / "artifacts", pipe["s3"]))
    c5 = m.s5_config(ctx, BL, m.S4_BASE, m.S5_BASE)
    runs = {"C-v2": (s3c, {}, data.calibration, t24_cfg, pipe["runs"]["C-v2"]["s4"], pipe["runs"]["C-v2"]["s5"][BL], C_OUT / "artifacts"),
            "B-both": (s3o, {}, data.calibration, t24_cfg, brun["s4"], brun["s5"][BL], B_OUT / "artifacts"),
            "A": (s3o, positions, None, base_cfg, unit["s4"], unit["s5"][BL], M1A / "artifacts")}
    out = {"rec_id": rec, "oracle_s3_equal": s3o.artifact_id == unit["s3"]}
    for name, (s3, pos, cal, cfg, s4_id, s5_id, root) in runs.items():
        s4 = builder.SubstrateBuilder().build(data.s1, s3, pos, cal, cfg, _spec(_manifest(root, s4_id)))
        row = {"S4": _same(s4, root, s4_id)}
        s5a = s5.build(data.s1, s4, c5, _spec(_manifest(root, s5_id)))
        row["S5 (D-54)"] = _same(s5a, root, s5_id)
        d57_id = sweep[name]["5"]["s5"]
        s5b = s5.build(data.s1, s4, c5, _spec(_manifest(D57 / "artifacts", d57_id)))
        row["S5 (D-57 m_gap 5)"] = _same(s5b, D57 / "artifacts", d57_id)
        out[name] = row
    return out


def main():  # pragma: no cover
    import v2_sets
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    recs = v2_sets.tuning()
    it = map(check_camera, recs) if workers == 1 else Pool(workers, maxtasksperchild=4).imap(check_camera, recs)
    rows = []
    for n, r in enumerate(it, 1):
        rows.append(r)
        print(n, r["rec_id"], all(v["payload_equal"] and v["id_equal"] for c in ("C-v2", "B-both", "A") for v in r[c].values()), flush=True)
    keys = ("S4", "S5 (D-54)", "S5 (D-57 m_gap 5)")
    ident = {c: {k: sum(r[c][k]["payload_equal"] and r[c][k]["id_equal"] for r in rows) for k in keys} for c in ("C-v2", "B-both", "A")}
    res = {"decision": "D-58 STEP 2 (T25.4 regression)", "contract": "E-1.2.26 code, T25 parameters absent", "cameras": len(rows),
           "sample": "all 116 tuning cameras", "oracle_s3_equal": sum(r["oracle_s3_equal"] for r in rows),
           "all_identical": all(r[c][k]["payload_equal"] and r[c][k]["id_equal"] for r in rows for c in ident for k in keys),
           "identical": ident, "per_camera": sorted(rows, key=lambda r: r["rec_id"])}
    pc.write_json(ROOT / "research/m1b/t25_regression.json", res)
    print("all identical:", res["all_identical"], json.dumps(ident))


if __name__ == "__main__":
    main()
