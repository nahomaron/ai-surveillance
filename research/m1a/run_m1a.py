"""T-21 M1a validation run, phase 1 (artifacts): per camera, resumable.

  python research/m1a/run_m1a.py <dataset sdg|smartspaces> <label> <units comma list> [workers] [--no-artifacts] [--cameras rec,rec]

Units per camera (each is written atomically as out/m1a/<label>/<ds>/<rec_id>/<unit>.json; a restart skips finished units):
  base        S3 ORACLE (g_max 15) -> S4 simulator_truth -> S5 BL-2..BL-6 (pre-registration v1 base values)
  full_camera S4 full_camera -> S5 BL-2..BL-6; S4 full_camera at w_v 0.33 and 1.0 (GV-07 per smoothing window)
  reference   T21: S3 from complete truth -> S4 simulator_truth -> S5 BL-6 (base values); reference episodes with T21.3
              assessability; the camera's truth table and visible frames (GV and T21.3 inputs)
  sweeps      MR-08 / MR-12 / GV-03 one-at-a-time grid (pre-registration v1 section 4), every grid point under BL-2..BL-6;
              stored as one bundle of complete artifacts (spec and tables) per camera (AR-59 item 4)

Artifacts of base, full_camera and reference are written as artifact directories under out/m1a/<label>/<ds>/artifacts/
unless --no-artifacts (used by the MR-01 repeat run, which records artifact IDs only).
Validation partition only (D-36, D-37): any other recording is refused (ERR-LEAKAGE). The source tree must be clean:
the code commit goes into every artifact spec.
"""
from __future__ import annotations

import gzip
import json
import os
import pickle
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import m1a_common as m  # noqa: E402

ROOT = m.ROOT

S4_SWEEP = [("g_max", v) for v in (5, 30, 60)] + [("v_min", v) for v in (0.2, 0.4)] + [("w_v", v) for v in (0.33, 1.0)] + \
           [("tau", v) for v in (3.0, 4.0)] + [("person_radius_m", v) for v in (0.25, 0.35)] + \
           [("fork_length_scale", v) for v in (0.9, 1.1)] + [("fork_width_scale", v) for v in (0.9, 1.1)]
S5_SWEEP = [("k_img", v) for v in (0.03, 0.08)] + [("d_p", v) for v in (1.5, 3.0)] + [("d_pc", v) for v in (0.5, 1.5)] + \
           [("ttc_max", v) for v in (1.0, 2.0)] + [("pet_max", v) for v in (0.5, 1.5)] + [("w_e", 0.5)] + \
           [("e_turn", v) for v in (0.75, 3.0)] + [("e_acc", v) for v in (0.5, 2.0)] + [("e_dec", v) for v in (1.0, 4.0)] + \
           [("m_gap", v) for v in (3, 10)] + [("t_min", v) for v in (0.1, 0.5)] + [("d_nm", v) for v in (0.3, 1.0)]
FC_WV = (0.33, 1.0)
UNITS = ("base", "full_camera", "reference", "sweeps")


def provenance() -> tuple[str, str]:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research/m1a", "research/datasets/part3"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty and os.environ.get("M1A_SMOKE") == "1":  # smoke tests only: the commit is recorded as "uncommitted"
        return "uncommitted", "uncommitted"
    if dirty:
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    import hashlib
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def _out(label, ds):
    return ROOT / "out/m1a" / label / ds


def _write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def _save(art, label, ds, origin, write) -> str:
    if write and art is not None:
        target = _out(label, ds) / "artifacts" / art.artifact_id
        if not (target / "manifest.json").exists():
            m.A.write_artifact(art, target, origin)
    return None if art is None else art.artifact_id


def _episodes(art) -> list[dict]:
    keep = ("pow_id", "start_frame", "end_frame_excl", "t_start_tl_s", "t_end_tl_s", "contact_state", "summary_label", "lbl_O", "lbl_H",
            "lbl_PC", "lbl_NM", "lbl_UD", "lbl_CT", "lbl_IE", "minclr_m", "closest_approach_frame")
    return [{k: e.get(k) for k in keep} for e in art.tables.get("episode", [])]


def unit_base(ctx, rec, data, prov, label, write, origin):
    s3, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], prov)
    s4 = m.s4(ctx, data, s3, positions, "simulator_truth", m.S4_BASE, prov)
    out = {"s3": _save(s3, label, ctx.ds, origin, write), "s4": _save(s4, label, ctx.ds, origin, write), "s5": {}}
    for bl in m.BASELINES:
        out["s5"][bl] = _save(m.s5_build(ctx, data, s4, bl, m.S4_BASE, m.S5_BASE, prov), label, ctx.ds, origin, write)
    return out


def unit_full_camera(ctx, rec, data, prov, label, write, origin):
    s3, positions, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], prov)
    s4 = m.s4(ctx, data, s3, positions, "full_camera", m.S4_BASE, prov)
    if s4 is None:
        return {"s4": None, "s4_null_reason": "uncalibrated", "s5": {}, "s4_w_v": {}}
    out = {"s3": s3.artifact_id, "s4": _save(s4, label, ctx.ds, origin, write), "s5": {}, "s4_w_v": {}}
    for bl in m.BASELINES:
        out["s5"][bl] = _save(m.s5_build(ctx, data, s4, bl, m.S4_BASE, m.S5_BASE, prov), label, ctx.ds, origin, write)
    for w_v in FC_WV:
        out["s4_w_v"][str(w_v)] = _save(m.s4(ctx, data, s3, positions, "full_camera", dict(m.S4_BASE, w_v=w_v), prov), label, ctx.ds, origin, write)
    return out


def unit_reference(ctx, rec, data, prov, label, write, origin):
    """T21.1-T21.3. Reference episodes are the BL-6 episodes on complete truth; G1 labels only (T21.2)."""
    s3, positions = m.reference_s3(rec, data, prov)
    s4 = m.s4(ctx, data, s3, positions, "simulator_truth", m.S4_BASE, prov)
    s5 = m.s5_build(ctx, data, s4, "BL-6", m.S4_BASE, m.S5_BASE, prov)
    tracks = m.reference_tracks(data)
    key_by_local = {i: str(k) for i, k in enumerate(sorted(tracks, key=str), 1)}
    key_by_trk = {t["trk_id"]: key_by_local[t["track_local_id"]] for t in s3.tables["track"]}
    pows = {p["pow_id"]: p for p in s4.tables["pow"]}
    visible = m.visible_frames(data)
    refs = []
    for e in _episodes(s5):
        pw = pows[e["pow_id"]]
        person, fork = key_by_trk[pw["person_track_id"]], key_by_trk[pw["forklift_track_id"]]
        both = set(visible.get(person, ())) & set(visible.get(fork, ()))
        assessable = any(e["start_frame"] <= i < e["end_frame_excl"] for i in both)  # T21.3 (eligible frames only, T20.1)
        refs.append({**{k: e[k] for k in ("pow_id", "start_frame", "end_frame_excl", "t_start_tl_s", "t_end_tl_s", "lbl_O", "lbl_H", "lbl_PC")},
                     "person_key": person, "forklift_key": fork, "assessable": assessable,
                     "status": "assessable" if assessable else "unobservable_reference"})
    out = {"s3": _save(s3, label, ctx.ds, origin, write), "s4": _save(s4, label, ctx.ds, origin, write),
           "s5": _save(s5, label, ctx.ds, origin, write), "references": refs}
    if write:
        with gzip.open(_out(label, ctx.ds) / rec / "truth.pkl.gz", "wb") as f:
            pickle.dump({"truth_table": m.truth_table(data), "visible_frames": visible}, f)
    return out


def unit_sweeps(ctx, rec, data, prov, label, write, origin):
    bundle, ids = {}, {}
    s3_base, pos_base, _ = m.s3(ctx, rec, data, m.S4_BASE["g_max"], prov)
    s4_base = m.s4(ctx, data, s3_base, pos_base, "simulator_truth", m.S4_BASE, prov)
    for name, value in S4_SWEEP:
        p4 = dict(m.S4_BASE, **{name: value})
        s3, pos = (m.s3(ctx, rec, data, value, prov)[:2] if name == "g_max" else (s3_base, pos_base))
        s4 = m.s4(ctx, data, s3, pos, "simulator_truth", p4, prov)
        tag = f"{name}={value}"
        bundle[tag] = {"s3": s3 if name == "g_max" else None, "s4": s4, "s5": {}}
        for bl in m.BASELINES:
            bundle[tag]["s5"][bl] = m.s5_build(ctx, data, s4, bl, p4, m.S5_BASE, prov)
    for name, value in S5_SWEEP:
        p5 = dict(m.S5_BASE, **{name: value})
        tag = f"{name}={value}"
        bundle[tag] = {"s3": None, "s4": None, "s5": {bl: m.s5_build(ctx, data, s4_base, bl, m.S4_BASE, p5, prov) for bl in m.BASELINES}}
    for tag, b in bundle.items():
        ids[tag] = {"s3": b["s3"].artifact_id if b["s3"] else None, "s4": b["s4"].artifact_id if b["s4"] else s4_base.artifact_id,
                    "s5": {bl: a.artifact_id for bl, a in b["s5"].items()}}
    if write:
        tmp = _out(label, ctx.ds) / rec / "sweeps.pkl.gz.tmp"
        with gzip.open(tmp, "wb") as f:
            pickle.dump({tag: {"s3": b["s3"], "s4": b["s4"], "s5": b["s5"]} for tag, b in bundle.items()}, f)
        os.replace(tmp, _out(label, ctx.ds) / rec / "sweeps.pkl.gz")
    return {"base_s4": s4_base.artifact_id, "grid": ids}


RUNNERS = {"base": unit_base, "full_camera": unit_full_camera, "reference": unit_reference, "sweeps": unit_sweeps}


def run_camera(args):
    ds, label, units, rec, prov, write = args
    ctx = m.Context(ds)
    ctx.camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    d = _out(label, ds) / rec
    d.mkdir(parents=True, exist_ok=True)
    todo = [u for u in units if not (d / f"{u}.json").exists()]
    if not todo:
        return rec, "skipped", {}
    origin = json.load(open(ROOT / f"out/s0_{ds}" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    t0 = time.time()
    data = m.load(ctx, rec)
    times = {"load": round(time.time() - t0, 1)}
    for u in todo:
        t1 = time.time()
        result = RUNNERS[u](ctx, rec, data, prov, label, write, origin)
        times[u] = round(time.time() - t1, 1)
        _write_json(d / f"{u}.json", {"rec_id": rec, "unit": u, "code_commit": prov[0], "environment_digest": prov[1], "contract": "E-1.2.19",
                                      "preregistration": "docs/preregistration_FROZEN.md, version 1", "seconds": times[u], **result})
    return rec, "done", times


def main():
    ds, label, units = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    workers = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 1
    write = "--no-artifacts" not in sys.argv
    assert set(units) <= set(UNITS), units
    prov = provenance()
    ctx = m.Context(ds)
    cams = [c["rec_id"] for c in ctx.validation_cameras()]
    if "--cameras" in sys.argv:
        wanted = sys.argv[sys.argv.index("--cameras") + 1].split(",")
        for r in wanted:
            ctx.camera(r)
        cams = [r for r in cams if r in wanted]
    _out(label, ds).mkdir(parents=True, exist_ok=True)
    print(f"{ds} {label} units={units} cameras={len(cams)} workers={workers} commit={prov[0]}", flush=True)
    jobs = [(ds, label, units, r, prov, write) for r in cams]
    t0 = time.time()
    if workers == 1:
        results = map(run_camera, jobs)
    else:
        pool = Pool(workers, maxtasksperchild=1)
        results = pool.imap_unordered(run_camera, jobs)
    for n, (rec, status, times) in enumerate(results, 1):
        print(n, rec, status, json.dumps(times), f"elapsed {round(time.time() - t0)} s", flush=True)


if __name__ == "__main__":
    main()
