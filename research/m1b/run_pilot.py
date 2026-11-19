"""T-25p detector-path pilot (D-45 item 3b), phase 1: artifacts per camera, resumable. Main `.venv`; the tracker runs in
`.venv-det` through a subprocess.

  PYTHONPATH=src .venv/bin/python research/m1b/run_pilot.py [rec_id ...]     (default: every pilot camera with S2 raw output)

Per camera (out/m1b/pilot/cam/<rec_id>/pipeline.json; artifacts under out/m1b/pilot/artifacts/):
  S1  stored rv2 artifact, reused (T-21)
  S2  `rq1.perception.s2.build` from the YOLO-World raw output (`s2_yolo_world.py`): thresholds person 0.20 / forklift 0.05
  S3  ByteTrack (`rq1.tracking.bytetrack`, `.venv-det`) -> `rq1.tracking.bridging` (g_max 15) -> `rq1.tracking.s3`
  S4  full_camera geometry from the detector boxes (foot point = bottom-centre), pre-registration v1 base values; no yaw is
      supplied, so T8.2 heading and footprint fallbacks apply as the builder implements them
  S5  BL-2 .. BL-6 at the frozen base values
Validation partition only (ERR-LEAKAGE otherwise). The source tree must be clean: the commit goes into every spec.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

m = pc.m
from rq1.ids import core  # noqa: E402
from rq1.ids.artifact import Spec  # noqa: E402
from rq1.perception import s2  # noqa: E402
from rq1.schema import files  # noqa: E402
from rq1.substrate import builder  # noqa: E402
from rq1.events import s5  # noqa: E402
from rq1.tracking import bridging  # noqa: E402
from rq1.tracking.s3 import DetectorTrackSource  # noqa: E402

ROOT = pc.ROOT
DET_PY = ROOT / ".venv-det/bin/python"
WEIGHTS = json.load(open(ROOT / "research/m1b/zero_shot_weights.json"))
MODEL = {"model": "yolov8s-worldv2.pt", "weights_sha256": WEIGHTS["yolov8s-worldv2.pt"]["sha256"],
         "text_encoder_sha256": WEIGHTS["ViT-B-32.pt (CLIP text encoder)"]["sha256"], "classes": ["person", "forklift"]}
INFERENCE = {"imgsz": 640, "nms_iou": 0.7, "max_det": 300, "score_floor": 0.05, "thresholds": s2.THRESHOLDS, "device": "cpu",
             "frames": "every eligible frame (rv2), decode order"}
LICENSE = s2.weights_component("yolov8s-worldv2.pt", WEIGHTS["yolov8s-worldv2.pt"]["sha256"], WEIGHTS["yolov8s-worldv2.pt"]["url"], "AGPL-3.0")


def provenance() -> tuple[str, str]:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research/m1b", "research/m1a"], cwd=ROOT, capture_output=True, text=True,
                           check=True).stdout.strip()
    if dirty and os.environ.get("PILOT_SMOKE") != "1":
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    commit = "uncommitted" if dirty else subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes() + (ROOT / "research/m1b/requirements_detector.txt").read_bytes()).hexdigest()
    return commit, env


def spec(stage, prov, config_ids, inputs) -> Spec:
    return Spec(stage, pc.CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def save(art, origin) -> str:
    target = pc.OUT / "artifacts" / art.artifact_id
    if not (target / "manifest.json").exists():
        m.A.write_artifact(art, target, origin)
    return art.artifact_id


def load_s1(ctx, rec):
    cam = ctx.camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    entry = ctx.index[rec]
    s1dir = ROOT / f"out/t17_sdg/{cam['s1']}"
    s1 = {t: files.read_table(str(s1dir / f"{t}.parquet"), t, m.A.SCHEMA_VERSION) for t in ("frame", "coverage_segment", "decode_summary")}
    cal = next((c for c in files.read_table(str(ROOT / "out/s0_sdg" / entry["s0"] / "calibration.parquet"), "calibration", m.A.SCHEMA_VERSION)
                if c["camera_id"] == entry["camera_id"]), None)
    return cam, s1, cal


def tracker_config() -> dict:
    out = subprocess.run([str(DET_PY), "-c", "import json; from rq1.tracking import bytetrack as b; print(json.dumps(b.default_config(), sort_keys=True))"],
                         cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


def run_camera(ctx, rec, prov, trk_cfg) -> dict:
    d = pc.OUT / "cam" / rec
    d.mkdir(parents=True, exist_ok=True)
    if (d / "pipeline.json").exists():
        return json.loads((d / "pipeline.json").read_text())
    cam, s1, cal = load_s1(ctx, rec)
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    times = {}
    # S2
    t0 = time.time()
    with gzip.open(pc.RAW / f"{rec}.json.gz", "rt") as f:
        raw = json.load(f)
    eligible = sorted(fr["frame_index"] for fr in s1["frame"] if fr["eligible"])
    if [fr["frame_index"] for fr in raw["frames"]] != eligible:
        raise RuntimeError(f"{rec}: S2 raw frames differ from the S1 eligible frames")
    summ = s1["decode_summary"][0]
    if (raw["width"], raw["height"]) != (summ["width_px"], summ["height_px"]):
        raise RuntimeError(f"{rec}: frame size differs from S1")
    lic = s2.component_id(LICENSE)
    s2_art = s2.build(rec, {fr["frame_index"]: fr["detections"] for fr in raw["frames"]}, raw["width"], raw["height"], lic,
                      spec("S2", prov, (core.make_id("mdl", MODEL), core.make_id("inf", INFERENCE)), (cam["s1"],)))
    s2_id = save(s2_art, origin)
    dets = s2_art.tables["detection"]
    times["s2_build"] = round(time.time() - t0, 2)
    # S3
    t0 = time.time()
    trk_in, trk_out = d / "tracker_in.json", d / "tracker_out.json"
    trk_in.write_text(json.dumps({"frames": eligible, "detections": [{k: r[k] for k in ("frame_index", "det_index", "class", "bbox_xyxy_px", "score")}
                                                                    for r in dets]}))
    subprocess.run([str(DET_PY), "-m", "rq1.tracking.bytetrack", str(trk_in), str(trk_out)], cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src")}, check=True)
    log = json.loads(trk_out.read_text())
    if log["config"] != trk_cfg:
        raise RuntimeError(f"{rec}: tracker configuration changed during the run")
    pts = {c: bridging.points_from_log(log["logs"][c], m.S4_BASE["g_max"]) for c in ("person", "forklift")}
    trc = core.make_id("trc", {"tracker": trk_cfg, "g_max": m.S4_BASE["g_max"], "bridging": "D-45 item 1", "tracked_box": "detection box (AR-62 item 3)"})
    s3_art, local_map = DetectorTrackSource().tracks(rec, pts, dets, s1["frame"], spec("S3", prov, (trc,), (s2_id,)))
    s3_id = save(s3_art, origin)
    times["s3_track"] = round(time.time() - t0, 2)
    counts = {c: {k: sum(tr["counts"].get(k, 0) for tr in pts[c].values()) for k in ("tracked", "predicted", "lost_long_run", "runs_bridged", "runs_lost",
                                                                                       "predicted_degenerate")} | {"tracks": len(pts[c])} for c in pts}
    # S4 full_camera, S5 BL-2..BL-6
    t0 = time.time()
    out = {"rec_id": rec, "camera": cam["camera"], "viewpoint": pc.viewpoint(cam["camera"]), "code_commit": prov[0], "environment_digest": prov[1],
           "contract": pc.CONTRACT, "preregistration": "docs/preregistration_FROZEN.md, version 1", "s1": cam["s1"], "s2": s2_id, "s3": s3_id,
           "license_component": LICENSE | {"lic_id": lic}, "tracker_config": trk_cfg, "track_counts": counts,
           "local_map": {str(k): list(v) for k, v in local_map.items()}, "detections": {c: sum(1 for r in dets if r["class"] == c) for c in ("person", "forklift")},
           "s2_detector_seconds": round(sum(raw["seconds"]), 1), "s2_wall_s": raw["wall_s"], "s5": {}}
    if cal is None:
        out.update(s4=None, s4_null_reason="uncalibrated")
    else:
        record, cfg, _, _ = m.substrate_config(ctx, m.S4_BASE)
        gcf = core.make_id("gcf", {"geometry": "full_camera"})
        s4_art = builder.SubstrateBuilder().build(s1, s3_art, {}, cal, cfg, spec("S4", prov, (s5.substrate_config_id(record), gcf), (s3_id,)))
        out["s4"] = save(s4_art, origin)
        times["s4"] = round(time.time() - t0, 2)
        t0 = time.time()
        for bl in m.BASELINES:
            c = m.s5_config(ctx, bl, m.S4_BASE, m.S5_BASE)
            out["s5"][bl] = save(s5.build(s1, s4_art, c, spec("S5", prov, (s5.config_id(c),), (out["s4"],))), origin)
        times["s5"] = round(time.time() - t0, 2)
    out["seconds"] = times
    pc.write_json(d / "pipeline.json", out)
    return out


def main(recs: list[str]) -> None:
    prov = provenance()
    ctx = m.Context("sdg")
    pilot = [c["rec_id"] for c in pc.pilot_cameras(ctx)]
    recs = recs or [r for r in pilot if (pc.RAW / f"{r}.json.gz").exists()]
    for r in recs:
        if r not in pilot:
            raise SystemExit(f"{r} is not a pilot camera")
    trk_cfg = tracker_config()
    print(f"pilot pipeline: {len(recs)} cameras, commit {prov[0]}", flush=True)
    t0 = time.time()
    for n, r in enumerate(recs, 1):
        out = run_camera(ctx, r, prov, trk_cfg)
        print(n, r, json.dumps(out.get("seconds")), f"elapsed {round(time.time() - t0)} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
