"""D-54 STEP 2 regression (T24.4 "Regression"): with the T24 parameters absent, stored E-1.2.24 S4 artifacts rebuild
byte-identical (same payload SHA-256, same artifact ID) under the T24 code.

  PYTHONPATH=src .venv/bin/python research/m1b/t24_regression.py [n]   -> research/m1b/t24_regression.json

Sample: the first n tuning cameras (canonical rec_id order, `v2_sets.tuning()`) that are pilot cameras, default 8. For each:
  M1a column A  (stored T-21 `base` unit: ORACLE-S3, simulator positions)   rebuilt from the rebuilt ORACLE-S3
  M1a column B  (stored T-21 `full_camera` unit: ORACLE-S3, full_camera)    rebuilt from the rebuilt ORACLE-S3
  pilot C       (stored T-25p pipeline: detector S3, full_camera)           rebuilt from the stored S3 artifact
Each rebuild uses the stored S4 manifest's own specification (so the artifact ID is comparable) and the unchanged v1 base
configuration (`m1a_common.substrate_config(ctx, S4_BASE)`), with no T24 parameter. Tuning cameras only (D-54 ruling 5).
The stored artifacts are read, never written.
"""
from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
ROOT = pc.ROOT
STORED_M1A = ROOT / "out/m1a/run1/sdg/artifacts"
STORED_PILOT = ROOT / "out/m1b/pilot/artifacts"


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


def check_camera(rec: str) -> dict:  # pragma: no cover - driver over stored artifacts
    from rq1.substrate import builder
    ctx = m.Context("sdg")
    unit = json.loads((ROOT / "out/m1a/run1/sdg" / rec / "base.json").read_text())
    fc = json.loads((ROOT / "out/m1a/run1/sdg" / rec / "full_camera.json").read_text())
    pilot = json.loads((ROOT / "out/m1b/pilot/cam" / rec / "pipeline.json").read_text())
    data = m.load(ctx, rec)
    s3, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], (unit["code_commit"], unit["environment_digest"]))
    assert s3.artifact_id == unit["s3"], rec
    _, cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
    out = {"rec_id": rec}
    for name, s4_id, pos in (("M1a A", unit["s4"], positions), ("M1a B", fc["s4"], {})):
        man = _manifest(STORED_M1A, s4_id)
        cal = None if name == "M1a A" else data.calibration
        built = builder.SubstrateBuilder().build(data.s1, s3, pos, cal, cfg, _spec(man))
        out[name] = {"stored": s4_id, "rebuilt": built.artifact_id, "payload_equal": built.payload_sha256 == man["payload_sha256"],
                     "id_equal": built.artifact_id == s4_id}
    man = _manifest(STORED_PILOT, pilot["s4"])
    s3c = SimpleNamespace(artifact_id=pilot["s3"], tables=_tables(STORED_PILOT, pilot["s3"]))
    built = builder.SubstrateBuilder().build(data.s1, s3c, {}, data.calibration, cfg, _spec(man))
    out["pilot C"] = {"stored": pilot["s4"], "rebuilt": built.artifact_id, "payload_equal": built.payload_sha256 == man["payload_sha256"],
                      "id_equal": built.artifact_id == pilot["s4"]}
    return out


def main():  # pragma: no cover
    import v2_sets
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    pilot = {c["rec_id"] for c in pc.pilot_cameras()}
    recs = [r for r in v2_sets.tuning() if r in pilot][:n]
    rows = []
    for rec in recs:
        rows.append(check_camera(rec))
        print(json.dumps(rows[-1]), flush=True)
    cols = ("M1a A", "M1a B", "pilot C")
    res = {"decision": "D-54 STEP 2 (T24.4 regression)", "contract": "E-1.2.25 code, T24 parameters absent", "cameras": len(rows),
           "sample": "first n tuning cameras that are pilot cameras, canonical rec_id order", "n": n,
           "all_identical": all(r[c]["payload_equal"] and r[c]["id_equal"] for r in rows for c in cols),
           "identical": {c: sum(r[c]["payload_equal"] and r[c]["id_equal"] for r in rows) for c in cols}, "per_camera": rows}
    pc.write_json(ROOT / "research/m1b/t24_regression.json", res)
    print("all identical:", res["all_identical"], res["identical"])


if __name__ == "__main__":
    main()
