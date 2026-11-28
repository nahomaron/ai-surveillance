"""D-55 steps 3 and 4: forklift tracker grid on the 116 tuning cameras (tracking measures only; no S4, S5 or S8).

  PYTHONPATH=src .venv/bin/python research/m1b/v2_tracker_grid.py estimate     (step 3: 2 cameras x 3 configurations x 2 trackers)
  PYTHONPATH=src .venv/bin/python research/m1b/v2_tracker_grid.py run [rec ...] (step 4: per camera, resumable)
  PYTHONPATH=src .venv/bin/python research/m1b/v2_tracker_grid.py aggregate    -> research/m1b/v2_tracker_grid.json (written twice)

Configurations: the column C configuration (ByteTrack, installed defaults, both classes) and 36 forklift configurations
per tracker (T1 ByteTrack, T2 BoT-SORT with the step 2 settings): (track_high_thresh, new_track_thresh) in PAIRS,
track_low_thresh 0.05, fuse_score in (true, false), track_buffer in (30, 60, 90), match_thresh 0.8, other keys installed.
The person tracker is ByteTrack with the column C configuration in every configuration. Configuration ID: the S3
tracker configuration ID (`rq1.tracking.s3_config.trc_id` of `run_config`, F.1 A1.2 configuration class).
Per camera, one `.venv-det` process (`rq1.tracking.grid`) runs the person job once and every forklift job; for the 96
cameras with a stored column C run, the column C jobs must reproduce the stored tracker log exactly.
S2: the stored pilot S2 (96 cameras) or the D-55 step 1 S2 (20 probe cameras). Cameras: `v2_camera_sets.json` tuning only.
Per-camera results: out/m1b/v2trk/grid/<rec_id>.json.
"""
from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402
import v2_sets  # noqa: E402
import v2_tracker_measures as vm  # noqa: E402
import v2_tracker_select as sel  # noqa: E402
from rq1.schema import files  # noqa: E402
from rq1.tracking import s3_config as sc  # noqa: E402

ROOT = pc.ROOT
OUT = ROOT / "out/m1b/v2trk"
DET_PY = ROOT / ".venv-det/bin/python"
GRID_PATH = ROOT / "research/m1b/v2_tracker_grid.json"
SELECTION_PATH = ROOT / "research/m1b/v2_tracker_selection.json"
KEYS_PATH = ROOT / "research/m1b/botsort_keys.json"
GRID_DIR = OUT / os.environ.get("V2TRK_GRID", "grid")  # per-camera results; V2TRK_GRID=grid_run2 for the independent second run
PAIRS = ((0.05, 0.05), (0.05, 0.10), (0.05, 0.25), (0.10, 0.10), (0.10, 0.25), (0.25, 0.25))
LOW, FUSE, BUFFERS, MATCH = 0.05, (True, False), (30, 60, 90), 0.8
FAMILY = {"bytetrack": "T1", "botsort": "T2"}
STATUS = "tuning subset, synthetic SDG, selection evidence, not a reported result"
COLUMN_C_JOB = "column_c"
REPEATS = 5  # step 3: each configuration repeated in one process, so the per-job time stands out from the process start


def write(path, obj) -> None:
    pc.write_json(path, obj)
    with open(path, "a") as f:
        f.write("\n")


def installed() -> dict:
    k = json.loads(KEYS_PATH.read_text())
    return {"bytetrack": k["bytetrack_installed_defaults"], "botsort_installed": k["installed_defaults"], "botsort": k["d55_params"]}


def column_c_base() -> dict:
    """Column C's recorded tracker configuration (every stored pipeline.json holds the same one)."""
    cfgs = {json.dumps(json.loads(p.read_text())["tracker_config"], sort_keys=True) for p in sorted((pc.OUT / "cam").glob("*/pipeline.json"))}
    if len(cfgs) != 1:
        raise SystemExit(f"STOP: {len(cfgs)} distinct column C tracker configurations")
    return json.loads(cfgs.pop())


def grid_params(defaults: dict) -> list[dict]:
    out = []
    for (hi, new), fuse, buf in itertools.product(PAIRS, FUSE, BUFFERS):
        out.append({**defaults, "track_high_thresh": hi, "new_track_thresh": new, "track_low_thresh": LOW, "fuse_score": fuse,
                    "track_buffer": buf, "match_thresh": MATCH})
    return out


def configurations() -> list[dict]:
    """Column C first, then T1 and T2 in grid order. Each: config_id, family, tracker_id, forklift params, run config."""
    base, inst = column_c_base(), installed()
    if base["params"] != inst["bytetrack"]:
        raise SystemExit("STOP: column C's tracker parameters differ from the installed ByteTrack defaults")
    person = {"tracker_id": "bytetrack", "params": base["params"]}
    rows = []

    def add(family, tid, params, grid):
        rc = sc.run_config(base, {"person": person, "forklift": {"tracker_id": tid, "params": params}})
        rows.append({"config_id": sc.trc_id(rc, vm.G_MAX), "family": family, "tracker_id": tid, "params": params, "grid": grid,
                     "parameters_changed": sel.parameters_changed(params, inst["bytetrack"] if tid == "bytetrack" else inst["botsort_installed"]),
                     "run_config": rc})
    add("C", "bytetrack", base["params"], None)
    for tid in ("bytetrack", "botsort"):
        for p in grid_params(inst[tid]):
            add(FAMILY[tid], tid, p, {k: p[k] for k in ("track_high_thresh", "new_track_thresh", "track_low_thresh", "fuse_score", "track_buffer", "match_thresh")})
    ids = [r["config_id"] for r in rows]
    if len(set(ids)) != len(ids) or len(rows) != 73:
        raise SystemExit("STOP: configuration IDs are not unique or the grid is not 1 + 72")
    return rows


def s2_of(rec: str) -> tuple[str, "Path"]:
    pc.m.drv.refuse_closed({"rec_id": rec})
    p = pc.OUT / "cam" / rec / "pipeline.json"
    if p.exists():
        return json.loads(p.read_text())["s2"], pc.OUT / "artifacts"
    q = OUT / "s2" / f"{rec}.json"
    if q.exists():
        return json.loads(q.read_text())["s2"], OUT / "artifacts"
    raise SystemExit(f"STOP: no S2 for {rec}")


def load_tables(art_dir, art_id) -> dict:
    d = art_dir / art_id
    man = json.loads((d / "manifest.json").read_text())
    return {f["path"][:-8]: files.read_table(str(d / f["path"]), f["path"][:-8], pc.m.A.SCHEMA_VERSION) for f in man["files"]}


def references(rec: str):
    """frame -> [(identity, class, box)] reference-visible boxes (T17.6), and the camera (as `evaluate_pilot`)."""
    import evaluate_pilot as ep
    ev = ep.ev
    cam = ev.Camera("sdg", ep.M1A_LABEL, rec)
    s3o = ev.load_art(ep.M1A_LABEL, "sdg", cam.units["base"]["s3"])
    trk_key = ev.track_map(s3o, ev.oracle_keys(cam.visible), cam.classes)
    return ep.ref_boxes(s3o, trk_key, cam.classes), cam, ep


def jobs_for(configs: list[dict]) -> list[dict]:
    base = configs[0]
    jobs = [{"job": "person", "tracker_id": "bytetrack", "class": "person", "params": base["params"]}]
    return jobs + [{"job": c["config_id"], "tracker_id": c["tracker_id"], "class": "forklift", "params": c["params"]} for c in configs]


def run_tracker(rec: str, frames, dets, jobs, workdir) -> tuple[dict, float]:
    workdir.mkdir(parents=True, exist_ok=True)
    tin, tout = workdir / "grid_in.json", workdir / "grid_out.json"
    tin.write_text(json.dumps({"frames": frames, "jobs": jobs, "detections": [{k: r[k] for k in ("frame_index", "det_index", "class", "bbox_xyxy_px", "score")}
                                                                              for r in dets]}))
    t0 = time.time()
    subprocess.run([str(DET_PY), "-m", "rq1.tracking.grid", str(tin), str(tout)], cwd=ROOT, env=pc.DET_ENV, check=True)
    dt = time.time() - t0
    out = json.loads(tout.read_text())
    tout.unlink()
    tin.unlink()
    return out, dt


def camera(rec: str, configs: list[dict], viewpoint: str, workdir=None) -> dict:
    t0 = time.time()
    s2_id, art_dir = s2_of(rec)
    dets = load_tables(art_dir, s2_id)["detection"]
    refs_all, cam, ep = references(rec)
    frames = sorted(cam.eligible)
    ds = files.read_table(str(ROOT / f"out/t17_sdg/{ep.ev.m.Context('sdg').camera(rec)['s1']}/decode_summary.parquet"), "decode_summary",
                          pc.m.A.SCHEMA_VERSION)[0]
    t_load = time.time() - t0
    out, t_trk = run_tracker(rec, frames, dets, jobs_for(configs), workdir or (OUT / "work" / rec))
    t1 = time.time()
    score = {(d["frame_index"], d["det_index"]): d["score"] for d in dets}
    res = {"rec_id": rec, "viewpoint": viewpoint, "s2": s2_id, "library": out["library"], "frames": len(frames), "configs": {}}
    stored = pc.OUT / "cam" / rec / "tracker_out.json"
    if stored.exists():
        st = json.loads(stored.read_text())["logs"]
        res["column_c_reproduces_stored_log"] = {"person": out["logs"]["person"] == st["person"], "forklift": out["logs"][configs[0]["config_id"]] == st["forklift"]}
        if not all(res["column_c_reproduces_stored_log"].values()):
            raise SystemExit(f"STOP: {rec}: the column C tracker run does not reproduce the stored log")
    for cls, job in [("person", "person")] + [("forklift", c["config_id"]) for c in configs]:
        refs = {i: [(k, b) for k, c, b in v if c == cls] for i, v in refs_all.items()}
        clipped = {i: [(k, cb) for k, cb in ((k, ep.ev_clip(b, ds["width_px"], ds["height_px"])) for k, b in v) if cb is not None] for i, v in refs.items()}
        meas = vm.measures(out["logs"][job], refs, clipped, score, frames)
        if cls == "person":
            res["person"] = meas
        else:
            res["configs"][job] = meas
    res["seconds"] = {"load": round(t_load, 2), "tracker_process": round(t_trk, 2), "measures": round(time.time() - t1, 2)}
    return res


def tuning() -> list[dict]:
    sets = v2_sets.load()
    cams = sets["tuning"]["cameras"]
    if len(cams) != 116:
        raise SystemExit(f"STOP: {len(cams)} tuning cameras, expected 116")
    return cams


def run(recs: list[str]) -> None:  # pragma: no cover - driver
    configs = configurations()
    cams = {c["rec_id"]: c for c in tuning()}
    recs = recs or sorted(cams)
    t0 = time.time()
    for n, rec in enumerate(recs, 1):
        if rec not in cams:
            raise SystemExit(f"{rec} is not a tuning camera")
        dst = GRID_DIR / f"{rec}.json"
        if dst.exists():
            continue
        res = camera(rec, configs, cams[rec]["viewpoint"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        write(dst, res)
        print(n, rec, json.dumps(res["seconds"]), f"elapsed {round(time.time() - t0)} s", flush=True)


def estimate() -> None:  # pragma: no cover - driver (step 3)
    """2 tuning cameras x 3 configurations per tracker: the tracker's defaults (ByteTrack: column C; BoT-SORT: installed
    + step 2) and the first and last grid point. A 1-job process separates the process start from the per-job time."""
    configs = configurations()
    inst = installed()
    t1 = [c for c in configs if c["family"] == "T1"]
    t2 = [c for c in configs if c["family"] == "T2"]
    job = lambda name, tid, params: {"job": name, "tracker_id": tid, "class": "forklift", "params": params}
    sets = {"bytetrack": [job("defaults", "bytetrack", configs[0]["params"])] + [job(c["config_id"], "bytetrack", c["params"]) for c in (t1[0], t1[-1])],
            "botsort": [job("defaults", "botsort", inst["botsort"])] + [job(c["config_id"], "botsort", c["params"]) for c in (t2[0], t2[-1])]}
    cams = tuning()
    recs = [cams[0]["rec_id"], cams[-1]["rec_id"]]
    rows = []
    for rec in recs:
        s2_id, art_dir = s2_of(rec)
        dets = load_tables(art_dir, s2_id)["detection"]
        _, cam, _ = references(rec)
        frames = sorted(cam.eligible)
        run_tracker(rec, frames, dets, sets["bytetrack"][:1], OUT / "work" / "estimate")  # warm-up (cold imports), not timed
        _, t_one = run_tracker(rec, frames, dets, sets["bytetrack"][:1], OUT / "work" / "estimate")
        r = {"rec_id": rec, "process_1_bytetrack_job_s": round(t_one, 2), "repeats": REPEATS}
        for tid, jobs in sets.items():  # each of the 3 configurations REPEATS times in one process
            rep = [{**j, "job": f"{j['job']}#{k}"} for k in range(REPEATS) for j in jobs]
            _, t = run_tracker(rec, frames, dets, rep, OUT / "work" / "estimate")
            r[f"process_{len(rep)}_{tid}_jobs_s"] = round(t, 2)
            r[f"{tid}_per_job_s"] = max(0.0, (t - t_one) / (len(rep) - 1))
        r["start_s"] = max(0.0, t_one - r["bytetrack_per_job_s"])
        res = camera(rec, [configs[0], t1[0], t1[-1], t2[0], t2[-1]], cams[0]["viewpoint"], OUT / "work" / "estimate")
        r["camera_load_s"] = res["seconds"]["load"]
        r["measures_per_job_s"] = res["seconds"]["measures"] / 6
        rows.append(r)
    mean = lambda k: sum(r[k] for r in rows) / len(rows)
    per_cam = (mean("start_s") + mean("camera_load_s") + 38 * mean("bytetrack_per_job_s") + 36 * mean("botsort_per_job_s")
               + 74 * mean("measures_per_job_s"))
    est = {"status": "D-55 step 3: runtime estimate (2 cameras x 3 configurations x 2 trackers)", "rows": rows,
           "extrapolation": "per camera = process start + camera load + 38 ByteTrack jobs (person, column C, 36 T1) + 36 BoT-SORT jobs + 74 x measures",
           "per_camera_s": round(per_cam, 1), "total_116_cameras_h": round(per_cam * 116 / 3600, 2), "limit_h": 6}
    write(OUT / "estimate.json", est)
    print(json.dumps(est, indent=1))


def pooled(parts_by_view: dict) -> dict:
    return {v: vm.pool(p) for v, p in parts_by_view.items()}


def aggregate() -> dict:  # pragma: no cover - driver over the per-camera files
    configs = configurations()
    cams = tuning()
    per = {c["rec_id"]: json.loads((GRID_DIR / f"{c['rec_id']}.json").read_text()) for c in cams}
    views = ("all", "ceiling", "eye_level")
    person_parts = {v: [per[r]["person"] for r in per if v == "all" or per[r]["viewpoint"] == v] for v in views}
    person = pooled(person_parts)
    rows = []
    for c in configs:
        parts = {v: [per[r]["configs"][c["config_id"]] for r in per if v == "all" or per[r]["viewpoint"] == v] for v in views}
        rows.append({k: c[k] for k in ("config_id", "family", "tracker_id", "grid", "params", "parameters_changed")} |
                    {"forklift": pooled(parts), "person_idf1": {v: person[v]["idf1"] for v in views}})
    repro = [r for r in per if "column_c_reproduces_stored_log" in per[r]]
    doc = {"status": STATUS, "contract": pc.CONTRACT, "decision": "D-55 step 4", "cameras": len(per),
           "by_viewpoint": {v: len(person_parts[v]) for v in views[1:]},
           "library": sorted({p["library"] for p in per.values()}),
           "definitions": {"idf1": "idf1.py (TrackEval port), iou_cm 0.5, system = every S3 point, reference = reference-visible boxes",
                           "matching": "zs_match.match, IoU >= 0.3, one-to-one, references clipped to the image (tracker_loss.camera)",
                           "primary": "tracked point = state tracked (CR-033 item 2)", "secondary": "all = tracked and predicted points",
                           "fragments_per_identity": "mean over reference identities covered by >= 1 track of the number of distinct tracks covering it",
                           "g_max": vm.G_MAX},
           "person": {"tracker": "ByteTrack, column C configuration, run once per camera (one job) and shared by every configuration",
                      "pooled": person},
           "column_c_reproduction": {"cameras_with_stored_log": len(repro), "all_identical": all(all(per[r]["column_c_reproduces_stored_log"].values()) for r in repro)},
           "column_c": rows[0], "rows": rows[1:]}
    return doc


def selection_row(r: dict, variant: str = "tracked") -> dict:
    f = r["forklift"]["all"]
    return {"config_id": r["config_id"], "family": r["family"] if r["family"] != "C" else "C", "idf1_forklift": f["idf1"],
            "coverage": f[variant]["coverage"], "fragments_per_identity": f[variant]["fragments_per_identity"],
            "parameters_changed": r["parameters_changed"], "precision": f[variant]["precision"], "idf1_person": r["person_idf1"]["all"]}


def main(argv):  # pragma: no cover
    if argv[:1] == ["estimate"]:
        estimate()
    elif argv[:1] == ["run"]:
        run(argv[1:])
    elif argv[:1] == ["aggregate"]:
        doc = aggregate()
        write(GRID_PATH, doc)
        first = GRID_PATH.read_bytes()
        write(GRID_PATH, aggregate())
        print(GRID_PATH, "byte-identical" if GRID_PATH.read_bytes() == first else "DIFFERENT")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
