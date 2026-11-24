"""D-55 step 1: S2 artifacts for the 20 T-22 probe cameras of the tuning subset (main `.venv`; resumable per camera).

  .venv-det/bin/python research/m1b/s2_yolo_world.py <probe rec_ids>    (detector, raw boxes -> out/m1b/pilot/s2raw/)
  PYTHONPATH=src .venv/bin/python research/m1b/v2_probe_s2.py            (this script: S2 artifacts)

- The S2 configuration is the pilot's: the model and inference configuration IDs are computed from `run_pilot.MODEL` and
  `run_pilot.INFERENCE` and must equal the configuration IDs of every stored pilot S2 artifact; otherwise STOP.
- S2 is built exactly as `run_pilot.run_camera` builds it (same checks against S1), plus the licence rows of D-47 item 5:
  the YOLO-World row and the CLIP ViT-B/32 text encoder row (`pilot_license_components.json`) inside the artifact.
- Output: out/m1b/v2trk/artifacts/<art_id>/ (with `execution.json`, appended to out/m1b/v2trk/register.jsonl) and
  out/m1b/v2trk/s2/<rec_id>.json per camera. No existing artifact is read for writing or touched.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import run_pilot as rp  # noqa: E402
import v2_sets  # noqa: E402

pc, m = rp.pc, rp.m
from rq1.ids import core  # noqa: E402
from rq1.perception import s2  # noqa: E402

OUT = pc.ROOT / "out/m1b/v2trk"


def config_ids() -> tuple:
    return tuple(sorted((core.make_id("mdl", rp.MODEL), core.make_id("inf", rp.INFERENCE))))


def license_rows() -> list[dict]:
    rec = json.loads((pc.ROOT / "research/m1b/pilot_license_components.json").read_text())["rows"]
    by_comp = {r["row"]["component"]: r for r in rec}
    rows = [rp.LICENSE, by_comp["ViT-B-32.pt"]["row"]]
    for r in rows:
        if s2.component_id(r) != by_comp[r["component"]]["lic_id"]:
            raise SystemExit(f"STOP: licence row {r['component']} differs from the recorded one")
    if by_comp["yolov8s-worldv2.pt"]["row"] != rp.LICENSE:
        raise SystemExit("STOP: the YOLO-World licence row differs from the pilot's")
    return rows


def check_pilot_config() -> None:
    stored = set()
    for p in sorted((pc.OUT / "cam").glob("*/pipeline.json")):
        s2_id = json.loads(p.read_text())["s2"]
        stored.add(tuple(json.loads((pc.OUT / "artifacts" / s2_id / "manifest.json").read_text())["spec"]["config_ids"]))
    if stored != {config_ids()}:
        raise SystemExit(f"STOP: S2 configuration IDs {config_ids()} differ from the pilot's {sorted(stored)}")


def probe_tuning_cameras() -> list[str]:
    sets = v2_sets.load()
    recs = sorted(c["rec_id"] for c in sets["tuning"]["cameras"] if c["probe_camera"])
    if len(recs) != 20 or recs != pc.probe_cameras():
        raise SystemExit("STOP: the probe cameras of the tuning subset are not the 20 T-22 probe cameras")
    return recs


def run_camera(ctx, rec, prov, lic_rows) -> dict:
    dst = OUT / "s2" / f"{rec}.json"
    if dst.exists():
        return json.loads(dst.read_text())
    cam, s1, _ = rp.load_s1(ctx, rec)
    origin = json.load(open(pc.ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    t0 = time.time()
    with gzip.open(pc.RAW / f"{rec}.json.gz", "rt") as f:
        raw = json.load(f)
    eligible = sorted(fr["frame_index"] for fr in s1["frame"] if fr["eligible"])
    if [fr["frame_index"] for fr in raw["frames"]] != eligible:
        raise RuntimeError(f"{rec}: S2 raw frames differ from the S1 eligible frames")
    summ = s1["decode_summary"][0]
    if (raw["width"], raw["height"]) != (summ["width_px"], summ["height_px"]):
        raise RuntimeError(f"{rec}: frame size differs from S1")
    lic = s2.component_id(rp.LICENSE)
    art = s2.build(rec, {fr["frame_index"]: fr["detections"] for fr in raw["frames"]}, raw["width"], raw["height"], lic,
                   rp.spec("S2", prov, config_ids(), (cam["s1"],)), license_rows=lic_rows)
    target = OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin, register=OUT / "register.jsonl")
    out = {"rec_id": rec, "camera": cam["camera"], "viewpoint": pc.viewpoint(cam["camera"]), "s1": cam["s1"], "s2": art.artifact_id,
           "config_ids": list(config_ids()), "code_commit": prov[0], "environment_digest": prov[1], "contract": pc.CONTRACT,
           "license_components": [r | {"lic_id": s2.component_id(r)} for r in lic_rows],
           "detections": {c: sum(1 for r in art.tables["detection"] if r["class"] == c) for c in ("person", "forklift")},
           "s2_detector_seconds": round(sum(raw["seconds"]), 1), "s2_wall_s": raw["wall_s"], "raw_code_commit": raw["code_commit"],
           "build_s": round(time.time() - t0, 2)}
    (OUT / "s2").mkdir(parents=True, exist_ok=True)
    pc.write_json(dst, out)
    return out


def main() -> None:  # pragma: no cover - driver over stored inputs
    check_pilot_config()
    prov = rp.provenance()
    lic_rows = license_rows()
    ctx = m.Context("sdg")
    recs = probe_tuning_cameras()
    missing = [r for r in recs if not (pc.RAW / f"{r}.json.gz").exists()]
    if missing:
        raise SystemExit(f"raw detector output missing for {len(missing)} cameras: run s2_yolo_world.py first")
    for n, r in enumerate(recs, 1):
        out = run_camera(ctx, r, prov, lic_rows)
        print(n, r, out["s2"], out["detections"], flush=True)


if __name__ == "__main__":
    main()
