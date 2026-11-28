"""D-63 STEP 5 / STEP 7: the single pre-registration v2 run of a partition (S3-S8, frozen v2 configuration).
Synthetic-data evaluation; experimental. Results are "candidate" outputs; nothing here is validated.

  PYTHONPATH=src .venv/bin/python research/v2/run_v2.py dev <rec> [<rec> ...]      tuning cameras only, out/v2/dev_m1c/ (development)
  PYTHONPATH=src .venv/bin/python research/v2/run_v2.py estimate                     2 tuning cameras into out/v2/dev_m1c/ (runtime)
  PYTHONPATH=src .venv/bin/python research/v2/run_v2.py dev-all [workers]             all 116 tuning cameras into out/v2/dev_m1c/
  PYTHONPATH=src .venv/bin/python research/v2/run_v2.py dev-repeat [workers]          MR-01 repeat of dev-all (IDs and hashes only)

Per camera (all values from `research/preregistration/v2_values.py`, label "preregistration-v2"; every configuration ID
is checked against `docs/preregistration/freeze_record_v2.json` before anything is scored):
  A  oracle path: ORACLE-S3 at g_max 45 -> S4 simulator_truth -> S5 BL-2 .. BL-6, T25.2 on.
  B  full_camera decomposition: the same ORACLE-S3 -> S4 full_camera with T24 (dataset calibration) -> S5 BL-2, BL-3, BL-6.
  C  detector path (headline): stored S2 (frozen v2 S2 IDs) -> the D-56 tracker package -> bridged at g_max 45 -> S4
     full_camera T24 (floor positions for T25.1) -> T25.1 stitched S3 (T_s 5 s, r_g 0.5 m) -> S4 full_camera T24 ->
     S5 BL-2, BL-3, BL-6, T25.2 on.
References: the frozen v2 reference set of the partition (`out/v2/references/<partition>/<rec>.json`); its S5 ID and
payload hash must equal the freeze record. Matching N4, label group G1, at iou_m 0.3 (decides), 0.5 and 0.7.
Pair resolution: A5.2 at the CA frame. Under v2 every event has one member (limitation 16: T25.2 is inert), so the two
CR-037 readings coincide; the run checks this on every event and stops otherwise.
Run guard (CR-042, D-65): STOP if, on any column and R2 baseline, M is unknown on more than 5 % of the pair-frames where
both objects have a stored state and the forklift speed is known. S5 on column C reads the stitch membership of its S3.
Measures per camera: EV counts (EV-M1, EV-M2, EV-M7 inputs) per column x baseline x iou_m; IE share; speed_near_v_min
episode counts; GV-01 (dx, dy), GV-07 (speed minus simulator_truth speed, w_v 0.5) and position availability by null
reason on B and C; GV-04 at the simulator positions (D-40 item 4); the exact-class artifact IDs and payload hashes (MR-01).
D-66 permanently closed the test. D-63 and D-65 reporting authorizations are spent. This runner is tuning-only.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import tempfile
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in ("research/m1b", "research/m1a", "research/preregistration"):
    sys.path.insert(0, str(ROOT / p))
import v2_values as v2  # noqa: E402

m = v2.m
LABEL = "preregistration-v2"
FREEZE = ROOT / "docs/preregistration/freeze_record_v2.json"
REFS = ROOT / "out/v2/references"
OUT = ROOT / "out/v2"
STATUS = "pre-registration v2 run; synthetic-data evaluation; experimental"
A_BL = ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6")
BC_BL = ("BL-2", "BL-3", "BL-6")
COLUMNS = {"A": A_BL, "B": BC_BL, "C": BC_BL}
IOUS = tuple(v2.IOU_M_REPORTED)
REFERENCE_SET = {"dev": "tuning"}


# ------------------------------------------------------------------------------------------------ pure functions

def partition_dir(partition: str) -> Path:
    if partition not in REFERENCE_SET:
        raise SystemExit(f"refused: partition {partition!r} is not run here (D-66/D-67)")
    return OUT / "dev_m1c"


def require_camera(partition: str, rec: str) -> None:
    partition_dir(partition)
    if rec not in cameras(partition):
        raise SystemExit(f"refused: {rec!r} is outside the v2 tuning allowlist")


def expected_configs(freeze: dict) -> dict:
    """The configuration IDs every system artifact of the run must carry (freeze record, SDG)."""
    sr, tr = freeze["configurations"]["substrate_and_rules"]["sdg"], freeze["configurations"]["tracker"]
    return {"sbc": sr["substrate_config_id"], "gcf_truth": sr["geometry_config_ids"]["simulator_truth"],
            "gcf_t24": sr["geometry_config_ids"]["full_camera_t24"], "rcf": dict(sr["rule_config_ids_system"]),
            "trc": tr["s3_config_id_g_max_45"], "trc_stitched": tr["s3_config_id_g_max_45_stitched"],
            "s2": list(freeze["configurations"]["detector"]["s2_config_ids"])}


def config_mismatches(got: dict, want: dict) -> list[str]:
    """Names of the configuration IDs that differ from the freeze record (empty = the frozen configuration)."""
    bad = []
    for k, v in want.items():
        if k == "rcf":
            bad += [f"rcf {bl}" for bl, rid in got.get("rcf", {}).items() if rid != v.get(bl)]
        elif k == "s2" and k in got:
            if sorted(got[k]) != sorted(v):
                bad.append(k)
        elif k in got and got[k] != v:
            bad.append(k)
    return bad


def ie_share(events: list[dict]) -> dict:
    n = len(events)
    k = sum(1 for e in events if "IE" in e["labels"])
    return {"events": n, "ie_events": k}


def flag_counts(s5_tables: dict) -> dict:
    """Episodes carrying each borderline flag (T10.4, T11.1), and all episodes."""
    eps = s5_tables.get("episode", [])
    c = Counter(f for e in eps for f in (e.get("borderline_flags") or []))
    return {"episodes": len(eps), **{f: c.get(f, 0) for f in ("speed_near_v_min", "clearance_within_k_sigma", "onset_sensitive", "footprint_orientation_unknown")}}


def check_single_member(events: list[dict]) -> None:
    """Limitation 16: under v2 no T25.2 join can occur, so the CR-037 readings coincide. Stop if not."""
    bad = [e["id"] for e in events if e["n_members"] != 1 or e["pair"]["a"] != e["pair"]["b"]]
    if bad:
        raise SystemExit(f"STOP: {len(bad)} events with several members or differing pair readings (CR-037 would decide): {bad[:3]}")


def counts_at(refs, groups, sysev, iou: float, usable: float) -> dict:
    from rq1.evaluation import event_metrics as em
    from rq1.evaluation import matching as mt
    records = mt.match_window(refs, sysev, "G1", iou, "rule_conformance", groups)
    return {"counts": em.window_counts(records, usable).__dict__,
            "match_types": dict(sorted(Counter(r["match_type"] for r in records).items()))}


def references_of(row: dict, rec: str):
    """N4 references from a stored v2 reference file (as `evaluate_m1a.references`, with the v2 reference S5)."""
    from rq1.evaluation import matching as mt
    from rq1.ids import core
    refs, groups = [], {}
    for r in row["references"]:
        rid = core.make_id("rin", {"rec_id": rec, "person": r["person_key"], "forklift": r["forklift_key"], "start_frame": r["start_frame"],
                                   "end_frame_excl": r["end_frame_excl"], "reference_s5": row["s5"]})
        refs.append(mt.Reference(rid, r["t_start_tl_s"], r["t_end_tl_s"], (r["person_key"], r["forklift_key"]), r["assessable"]))
        groups[rid] = frozenset({"G1"}) if (r["lbl_O"] or r["lbl_H"] or r["lbl_PC"]) else frozenset()
    return refs, groups


def verified_references(row: dict, binding: dict, rec: str, ref_set: str):
    """Check the reference list actually handed to N4 against the existing freeze representation."""
    from v2_references import list_sha256
    if (row.get("set") != ref_set or row.get("rec_id") != rec or binding.get("rec_id") != rec
            or any(row.get(key) != binding[key] for key in ("s3", "s4", "s5", "s5_payload_sha256", "references_sha256"))
            or not isinstance(row.get("references"), list)
            or list_sha256(row["references"]) != binding["references_sha256"]):
        raise SystemExit(f"STOP: {rec}: consumed reference content or lineage differs from the freeze record")
    return references_of(row, rec)


def position_rows(object_states, identity_of, truth, person_tracks) -> tuple[list, dict]:
    """GV-01 inputs (class, evidence class, dx, dy) and availability by null reason (D-41). identity_of(track, frame)."""
    rows, avail = [], defaultdict(int)
    for r in object_states:
        cls = "person" if r["track_id"] in person_tracks else "forklift"
        if r["x_m"] is None:
            avail[f"{cls}|null:{r['x_m_null_reason']}"] += 1
            continue
        key = identity_of(r["track_id"], r["frame_index"])
        t = truth.get((key, r["frame_index"])) if key is not None else None
        if t is None:
            avail[f"{cls}|position_without_matched_identity"] += 1
            continue
        avail[f"{cls}|position"] += 1
        rows.append((cls, r["evidence_class"], r["x_m"] - t[3], r["y_m"] - t[4]))
    return rows, dict(sorted(avail.items()))


def speed_rows(object_states, identity_of, truth_speed, classes) -> list:
    """GV-07 inputs (class, evidence class, speed minus the simulator_truth speed of the identity, same w_v)."""
    out = []
    for r in object_states:
        if r["speed_mps"] is None:
            continue
        key = identity_of(r["track_id"], r["frame_index"])
        ts = truth_speed.get((key, r["frame_index"])) if key is not None else None
        if ts is not None:
            out.append((classes[key], r["evidence_class"], r["speed_mps"] - ts))
    return out


M_MISSING_MAX = 0.05  # D-65 / CR-042 ruling: STOP above 5 %


def m_input_check(s4_tables: dict, s5_tables: dict, member_track) -> dict:
    """CR-042 run guard. Pair-frames where both objects have a stored S4 state (found independently of S5: the member
    track of each unit on that frame, `member_track(unit, frame)`, then its object_state row) and the forklift speed is
    known; of those, the frames whose stored M is unknown (2), i.e. S5 did not get the M input."""
    states = {(r["track_id"], r["frame_index"]): r for r in s4_tables["object_state"]}
    pow_id = {(p["person_track_id"], p["forklift_track_id"], p["start_frame"]): p["pow_id"] for p in s4_tables["pow"]}
    m_of = {(r["pow_id"], r["frame_index"]): r["M"] for r in s5_tables.get("flag_series", [])}
    both = missing = 0
    for r in s4_tables["pair_series"]:
        i = r["frame_index"]
        pu, fu, start = r["pow_nk"]
        ps, fs = states.get((member_track(pu, i), i)), states.get((member_track(fu, i), i))
        if ps is None or fs is None or fs["speed_mps"] is None:
            continue
        both += 1
        missing += m_of.get((pow_id[(pu, fu, start)], i), 2) == 2
    return {"pair_frames_with_both_states": both, "m_missing": missing, "share_missing": (missing / both) if both else None}


def flag_input_audit(s1: dict, s4: dict, member_at: dict | None):
    """Audit S5's actual inputs against raw S4 states indexed independently of S5."""
    from rq1.events import engine, providers

    recording = s1["frame"][0]["recording_id"]
    frames = {row["frame_index"]: row for row in s1["frame"] if row["recording_id"] == recording and row["eligible"]}
    coverage = s1["coverage_segment"]
    own = next((c for c in coverage if c.get("recording_id") == recording), None)
    coverage = [c for c in coverage if own and (c["timeline_id"], c["camera_id"]) == (own["timeline_id"], own["camera_id"])]
    states = defaultdict(dict)
    for row in s4["object_state"]:
        states[row["track_id"]][row["frame_index"]] = row
    pairs = defaultdict(dict)
    for row in s4["pair_series"]:
        pairs[tuple(row["pow_nk"])][row["frame_index"]] = row
    counts = {name: Counter() for name in ("R4", "R5", "contact", "coverage")}

    def check(pw, rules, flags):
        p, f, start = pw["person_track_id"], pw["forklift_track_id"], pw["start_frame"]
        series = pairs[(p, f, start)]
        if len(series) != len(flags) or set(series) != {row.frame_index for row in flags}:
            raise SystemExit(f"STOP: {pw['pow_id']} flag rows do not cover the S4 pair series")
        by_member_pair = defaultdict(list)
        for i in series:
            by_member_pair[(p, f) if member_at is None else (member_at.get((p, i)), member_at.get((f, i)))].append(i)
        expected_rates = {}
        for (pt, ft), indices in by_member_pair.items():
            expected_rates.update(providers.r5_rates(list(states.get(pt, {}).values()), list(states.get(ft, {}).values()),
                                                     frames, coverage, rules.w_e, rules.v_min, only=indices))
        for flag in flags:
            i = flag.frame_index
            row = series[i]
            pt, ft = (p, f) if member_at is None else (member_at.get((p, i)), member_at.get((f, i)))
            p_speed = states.get(pt, {}).get(i, {}).get("speed_mps")
            f_speed = states.get(ft, {}).get(i, {}).get("speed_mps")
            if set(flag.C_by) != set(rules.conflict):
                raise SystemExit(f"STOP: {pw['pow_id']} frame {i}: wrong conflict provider set")
            r4 = providers.r4_c(row, p_speed, f_speed, rules.ttc_max, rules.pet_max) if "R4" in rules.conflict else None
            rates = expected_rates[i]
            expected_e = 2 if row["evidence_class"] == "insufficient" else engine.evasive(rates, rules.e_turn, rules.e_acc, rules.e_dec)
            # Contact and R5 share the raw Rates record. Compare it even when the R5 flag is disabled.
            if (flag.rates or engine.Rates()) != rates:
                raise SystemExit(f"STOP: {pw['pow_id']} frame {i}: R5/contact rate inputs differ from member states")
            turn_known = rates.turn_false or rates.person_turn_rate is not None
            complete = turn_known and rates.person_speed_change is not None and rates.forklift_decel is not None
            counts["contact"]["evaluated" if complete else "unavailable"] += 1
            for name, expected, actual, enabled in (
                ("R4", r4, flag.C_by.get("R4"), "R4" in rules.conflict),
                ("R5", expected_e if rules.r5 else 0, flag.E, rules.r5),
                ("coverage", providers.q(row["q_state"]), flag.Q, True),
            ):
                if expected != actual:
                    raise SystemExit(f"STOP: {pw['pow_id']} frame {i}: {name} differs from the S4 inputs")
                counts[name]["inapplicable" if not enabled else "unavailable" if expected == 2 else "evaluated"] += 1

    return check, counts


def artifact_digest(arts: dict) -> str:
    """SHA-256 over the sorted (name, artifact ID, payload hash) of a camera's exact-class artifacts (MR-01)."""
    rows = sorted((k, a["id"], a["payload"]) for k, a in arts.items())
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def stable_digest(value) -> str:
    from datetime import date, datetime

    def encode(item):
        if isinstance(item, (date, datetime)):
            return item.isoformat()
        if isinstance(item, (set, frozenset)):
            return sorted(item)
        raise TypeError(f"unsupported cache identity type: {type(item).__name__}")
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=encode).encode()).hexdigest()


def development_output(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.parent != OUT.resolve() or not resolved.name.startswith("dev_"):
        raise SystemExit("refused: v2 output must be an isolated dev_* directory under out/v2")
    return resolved


def without_symlinks(path: Path) -> Path:
    absolute = path.absolute()
    if absolute.resolve() != absolute:
        raise SystemExit(f"refused: unexpected path alias for {path}")
    return path


def verify_saved_artifact(directory: Path, art_id: str) -> str:
    """Verify artifact files and their configuration's binding to the recorded artifact specification."""
    from rq1.ids import core
    if not art_id.startswith("art_") or Path(art_id).name != art_id:
        raise SystemExit("STOP: invalid artifact identifier")
    target = without_symlinks(directory / art_id)
    manifest = json.loads(without_symlinks(target / "manifest.json").read_text())
    for item in manifest["files"]:
        name = item["path"]
        if Path(name).name != name or not name.endswith(".parquet"):
            raise SystemExit(f"STOP: {art_id}: invalid artifact member")
        without_symlinks(target / name)
    if manifest.get("spec") is not None and core.make_id("asp", manifest["spec"]) != manifest["artifact_spec_id"]:
        raise SystemExit(f"STOP: {art_id}: artifact specification differs from its ID")
    if m.A.verify(target) != art_id:
        raise SystemExit(f"STOP: {art_id}: stored artifact does not match its ID")
    return manifest["payload_sha256"]


def cached_result(path: Path, cache_key: str, artifacts_dir: Path) -> bool:
    if not path.exists():
        return False
    row = read_camera_record(path)
    if row["cache_key"] != cache_key:
        return False
    arts = row["artifacts"]
    if artifact_digest(arts) != row["artifact_digest"]:
        raise SystemExit("STOP: inconsistent exact artifact index in camera cache")
    for item in arts.values():
        if verify_saved_artifact(artifacts_dir, item["id"]) != item["payload"]:
            raise SystemExit("STOP: artifact payload differs from camera cache")
    return True


def read_camera_record(path: Path) -> dict:
    row = json.loads(without_symlinks(path).read_text())
    if row.pop("record_sha256", None) != stable_digest(row):
        raise SystemExit(f"STOP: {path}: camera cache record hash does not verify")
    return row


def write_camera_record(path: Path, payload: dict) -> None:
    m_write_json(path, {**payload, "record_sha256": stable_digest(payload)})


def save_verified_artifact(art, root: Path, origin: str) -> None:
    target = root / "artifacts" / art.artifact_id
    target.parent.mkdir(parents=True, exist_ok=True)
    published = False
    if not target.exists():
        with tempfile.TemporaryDirectory(dir=target.parent) as staging:
            staged = Path(staging) / "artifact"
            m.A.write_artifact(art, staged, origin)
            try:
                staged.rename(target)
                published = True
            except OSError:
                if not target.is_dir():
                    raise
    if verify_saved_artifact(target.parent, art.artifact_id) != art.payload_sha256:
        raise SystemExit(f"STOP: {art.artifact_id}: existing artifact payload differs")
    # Register only a fully published artifact and only from the writer that published it.
    if published:
        m.A._append_register(root / "register.jsonl", json.loads((target / "execution.json").read_text()))


# ------------------------------------------------------------------------------------------------ drivers

def runtime_environment() -> dict:
    import av
    import platform
    from importlib.metadata import version
    import v2_tracker_grid as grid

    code = (
        "import json, platform, sys; from importlib.metadata import version; "
        "packages = ('numpy', 'torch', 'ultralytics', 'opencv-python', 'transformers'); "
        "print(json.dumps({'python': sys.version, 'platform': platform.platform(), "
        "'packages': {p: version(p) for p in packages}}))"
    )
    detector = subprocess.run([str(grid.DET_PY), "-c", code], cwd=ROOT, env=grid.pc.DET_ENV,
                              capture_output=True, text=True, check=True)
    locks = ("requirements.lock", "research/m1b/requirements_detector.txt")
    return {"python": sys.version, "platform": platform.platform(), "device": "cpu",
            "packages": {p: version(p) for p in ("numpy", "scipy", "pyarrow", "av", "opencv-python-headless")},
            "decoder": av.library_versions_as_strings if hasattr(av, "library_versions_as_strings") else av.library_versions,
            "detector_tracker": json.loads(detector.stdout),
            "locks": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in locks}}


def provenance() -> tuple[str, str]:  # pragma: no cover
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "research"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if dirty and os.environ.get("V2RUN_DEV") != "1":
        raise SystemExit(f"refused: uncommitted changes in the source tree:\n{dirty}")
    commit = "uncommitted" if dirty else subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    environment = runtime_environment()
    digest = stable_digest(environment)
    directory = development_output(Path(os.environ.get("V2RUN_DEV_DIR", partition_dir("dev"))))
    directory.mkdir(parents=True, exist_ok=True)
    m_write_json(directory / f"environment_{digest}.json", environment)
    return commit, digest


def _spec(stage, prov, config_ids, inputs):
    return m.Spec(stage, v2.CONTRACT, prov[0], prov[1], tuple(config_ids), tuple(inputs), {})


def camera_inputs(partition: str, rec: str, ctx):  # pragma: no cover - reads stored development data
    """Camera view, S1, calibration and truth for a v2 tuning recording."""
    require_camera(partition, rec)
    import evaluate_pilot as ep
    import run_pilot as rp
    import test_access as ta
    data = m.load(ctx, rec)
    if os.environ.get("V2RUN_VIEW") == "fresh":
        return ta.CameraView(ctx, rec, ctx.camera(rec), data, ta.V0_VALIDATION), data.s1, data.calibration, data
    _, s1, cal = rp.load_s1(ctx, rec)
    return ep.ev.Camera("sdg", ep.M1A_LABEL, rec), s1, cal, data


def test_inference() -> dict:
    """AR-74: the S2 inference record of the test run. The D-45 / T-25p record with the device that ran it (the Colab
    T4 of the D-64 job, `test_s2_arrival_v2.json`); every other field unchanged. D-62 found the two devices equivalent."""
    import run_pilot as rp
    return dict(rp.INFERENCE, device="cuda (Tesla T4, Colab)")


def expected_test_s2() -> list[str]:
    import run_pilot as rp
    from rq1.ids import core
    return [core.make_id("mdl", rp.MODEL), core.make_id("inf", test_inference())]


def test_s2(ctx, rec: str, s1: dict, prov):  # pragma: no cover - reads the sealed Colab output (D-63 STEP 7 only)
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


def s2_from_raw(rec: str, raw: dict, s1: dict, spec):
    """As `run_pilot.run_camera` (S2 part): frames must equal the S1 eligible frames and the size S1's."""
    import run_pilot as rp
    from rq1.perception import s2
    eligible = sorted(fr["frame_index"] for fr in s1["frame"] if fr["eligible"])
    if [fr["frame_index"] for fr in raw["frames"]] != eligible:
        raise SystemExit(f"STOP: {rec}: S2 raw frames differ from the S1 eligible frames")
    summ = s1["decode_summary"][0]
    if (raw["width"], raw["height"]) != (summ["width_px"], summ["height_px"]):
        raise SystemExit(f"STOP: {rec}: frame size differs from S1")
    return s2.build(rec, {fr["frame_index"]: fr["detections"] for fr in raw["frames"]}, raw["width"], raw["height"], s2.component_id(rp.LICENSE), spec)


def run_camera(args) -> tuple[str, str, float]:  # pragma: no cover - driver over stored artifacts
    partition, rec, prov, out, write = args
    require_camera(partition, rec)
    out = development_output(out)
    for name in ("cam", "repeat", "artifacts", "work"):
        without_symlinks(out / name)
    without_symlinks(out / "work" / rec)
    import d54_c_v2 as c
    import d58_events as d58
    import evaluate_pilot as ep
    import run_pilot as rp
    import v2_tracker_grid as grid
    from types import SimpleNamespace
    from rq1.evaluation import association as assoc
    from rq1.events import s5
    from rq1.ids import core
    from rq1.substrate import builder
    from rq1.tracking import bridging, stitching
    from rq1.tracking import s3_config as sc
    from rq1.tracking.s3 import DetectorTrackSource
    path = without_symlinks(out / ("cam" if write else "repeat") / f"{rec}.json")
    t0 = time.time()
    freeze_bytes = FREEZE.read_bytes()
    freeze = json.loads(freeze_bytes)
    want = expected_configs(freeze)
    ev = ep.ev
    ctx = m.Context("sdg")
    cam, s1, cal, data = camera_inputs(partition, rec, ctx)
    if cal is None:
        raise SystemExit(f"STOP: {rec}: no calibration")
    origin = json.load(open(ROOT / "out/s0_sdg" / ctx.index[rec]["s0"] / "manifest.json"))["data_origin"]
    support = cam.support()
    usable = sum(support.values())
    sup_all = lambda rows: {f: support.get(f, 0.0) for f in {r["frame_index"] for r in rows}}
    arts, got = {}, {"rcf": {}}

    def keep(name, art):
        arts[name] = {"id": art.artifact_id, "payload": art.payload_sha256}
        if write:
            save_verified_artifact(art, out, origin)

    # --- references: the frozen v2 set of the partition
    ref_set = REFERENCE_SET[partition]
    ref_row = json.loads(without_symlinks(REFS / ref_set / f"{rec}.json").read_text())
    frozen = {r["rec_id"]: r for r in freeze["references"][ref_set]["per_camera"]}[rec]
    refs, groups = verified_references(ref_row, frozen, rec, ref_set)
    s2_id, art_dir = grid.s2_of(rec)
    s1_id = ctx.camera(rec)["s1"]
    s1_payload = verify_saved_artifact(ROOT / "out/t17_sdg", s1_id)
    s2_payload = verify_saved_artifact(art_dir, s2_id)
    cache_key = stable_digest({"provenance": prov, "rec_id": rec, "freeze": hashlib.sha256(freeze_bytes).hexdigest(),
                               "reference": frozen, "s1": [s1_id, s1_payload], "s2": [s2_id, s2_payload],
                               "calibration": cal, "camera_view": os.environ.get("V2RUN_VIEW"),
                               "truth": cam.truth_rows, "visible": cam.visible, "window": cam.window})
    if write and prov[0] != "uncommitted" and cached_result(path, cache_key, out / "artifacts"):
        return rec, "skipped", 0.0
    record, base_cfg, _, _ = v2.substrate_config(ctx, LABEL)
    got["sbc"] = s5.substrate_config_id(record)
    t24_cfg, gcf_t24, _ = v2.t24_config(base_cfg, "sdg")
    gcf_truth = core.make_id("gcf", {"geometry": "simulator_truth"})
    got["gcf_t24"], got["gcf_truth"] = gcf_t24, gcf_truth

    input_audits = {}

    def s5_all(col, s4a, bls, s3_stitched=None):
        """S5 per baseline. With a stitched S3 (column C), S5 reads its stitch membership (CR-042) and lists that S3 as an
        input artifact beside the S4 (AR-73)."""
        from rq1.events import providers
        members = providers.stitch_members(s3_stitched.tables) if s3_stitched is not None else None
        inputs = (s4a.artifact_id,) + ((s3_stitched.artifact_id,) if s3_stitched is not None else ())
        member_at = None
        if s3_stitched is not None:
            by_local = {t["track_local_id"]: t["trk_id"] for t in s3_stitched.tables["track"]}
            member_at = {(r["stitch_id"], r["frame_index"]): by_local[r["track_nk"][1]]
                         for r in s3_stitched.tables["track_point"]}
        res = {}
        for bl in bls:
            c5 = v2.s5_config(ctx, bl, LABEL, True)
            got["rcf"][bl] = s5.config_id(c5)
            audit, counts = flag_input_audit(s1, s4a.tables, member_at)
            res[bl] = s5.build(s1, s4a, c5, _spec("S5", prov, (got["rcf"][bl],), inputs), members=members, check_inputs=audit)
            input_audits[f"{col}|{bl}"] = counts
        return res

    # --- A and B: ORACLE-S3 at g_max 45
    s3a, positions, _ = m.s3(ctx, rec, data, v2.S4_V2["g_max"], prov)
    s4a = builder.SubstrateBuilder().build(s1, s3a, positions, None, base_cfg, _spec("S4", prov, (got["sbc"], gcf_truth), (s3a.artifact_id,)))
    s4b = builder.SubstrateBuilder().build(s1, s3a, {}, cal, t24_cfg, _spec("S4", prov, (got["sbc"], gcf_t24), (s3a.artifact_id,)))
    s5a, s5b = s5_all("A", s4a, A_BL), s5_all("B", s4b, BC_BL)
    keep("A.S3", s3a), keep("A.S4", s4a), keep("B.S4", s4b)
    for bl, a in s5a.items():
        keep(f"A.S5.{bl}", a)
    for bl, a in s5b.items():
        keep(f"B.S5.{bl}", a)
    # --- C: detector path from the stored S2
    column_c, pkg = c.package()
    got["s2"] = list(json.loads((art_dir / s2_id / "manifest.json").read_text())["spec"]["config_ids"])
    dets = grid.load_tables(art_dir, s2_id)["detection"]
    frames = sorted(cam.eligible)
    tout, _ = grid.run_tracker(rec, frames, dets, c.jobs(column_c, pkg), out / "work" / rec)
    stored_log = ep.pc.OUT / "cam" / rec / "tracker_out.json"
    person_log_reproduced = None
    if stored_log.exists():
        person_log_reproduced = tout["logs"]["person"] == json.loads(stored_log.read_text())["logs"]["person"]
        if not person_log_reproduced:
            raise SystemExit(f"STOP: {rec}: the person tracker run does not reproduce the stored pilot log")
    g = v2.S4_V2["g_max"]
    pts = {"person": bridging.points_from_log(tout["logs"]["person"], g), "forklift": bridging.points_from_log(tout["logs"][c.PACKAGE], g)}
    got["trc"] = sc.trc_id(pkg["run_config"], g)
    s3c, _ = DetectorTrackSource().tracks(rec, pts, dets, s1["frame"], _spec("S3", prov, (got["trc"],), (s2_id,)))
    s4u = builder.SubstrateBuilder().build(s1, s3c, {}, cal, t24_cfg, _spec("S4", prov, (got["sbc"], gcf_t24), (s3c.artifact_id,)))
    floor = {(r["track_id"], r["frame_index"]): (r["x_m"], r["y_m"]) for r in s4u.tables["object_state"] if r["x_m"] is not None}
    params = v2.stitch_params()
    recording = cam.frames[0]["recording_id"]
    fr = {f["frame_index"]: f for f in cam.frames if f["eligible"] and f["recording_id"] == recording}
    accepted = stitching.links(stitching.tracks_of(s3c.tables), fr, cam.coverage, params, floor)
    sid = stitching.stitch_ids(stitching.chains([t["trk_id"] for t in s3c.tables["track"]], accepted), stitching.natural_keys(s3c.tables))
    got["trc_stitched"] = sc.trc_id(pkg["run_config"], g, stitch=params)
    s3s = stitching.apply(SimpleNamespace(tables=s3c.tables), sid, _spec("S3", prov, (got["trc_stitched"],), (s2_id,)))
    s4c = builder.SubstrateBuilder().build(s1, s3s, {}, cal, t24_cfg, _spec("S4", prov, (got["sbc"], gcf_t24), (s3s.artifact_id,)))
    s5c = s5_all("C", s4c, BC_BL, s3s)
    keep("C.S3", s3c), keep("C.S3.stitched", s3s), keep("C.S4", s4c)
    for bl, a in s5c.items():
        keep(f"C.S5.{bl}", a)
    bad = config_mismatches(got, want)
    if bad:
        raise SystemExit(f"STOP: {rec}: configuration IDs differ from the freeze record: {bad}")
    # --- association
    trk_key = ev.track_map(s3a.tables, ev.oracle_keys(cam.visible), cam.classes)
    rows_o, _, _ = ev.association(s3a.tables, trk_key)
    summ_o, _ = assoc.summarize(rows_o, sup_all(rows_o))
    refs_by_frame = ep.ref_boxes(s3a.tables, trk_key, cam.classes)
    by_local = {t["track_local_id"]: t["trk_id"] for t in s3s.tables["track"]}
    member_at = {(p["stitch_id"], p["frame_index"]): by_local[p["track_nk"][1]] for p in s3s.tables["track_point"]}
    rows_c, _, _ = ep.association_detector(s3s.tables, refs_by_frame)
    summ_c, _ = assoc.summarize(rows_c, sup_all(rows_c))
    cols = {"A": (s4a, s5a, rows_o, summ_o, lambda u, f: u), "B": (s4b, s5b, rows_o, summ_o, lambda u, f: u),
            "C": (s4c, s5c, rows_c, summ_c, lambda u, f, ma=member_at: ma.get((u, f)))}
    m_check = {}
    for col, (s4t, s5s, _, _, member_track) in cols.items():
        for bl, s5x in s5s.items():
            if bl == "BL-2":
                continue  # R1 only: M is unknown by definition (section 6.0)
            m_check[f"{col}|{bl}"] = m_input_check(s4t.tables, s5x.tables, member_track)
    bad_m = {k: v for k, v in m_check.items() if v["share_missing"] is not None and v["share_missing"] > M_MISSING_MAX}
    if bad_m:
        raise SystemExit(f"STOP: {rec}: M inputs missing on more than {M_MISSING_MAX:.0%} of pair-frames with both states (CR-042 guard): {bad_m}")
    res = {"rec_id": rec, "partition": partition, "status": STATUS, "cache_key": cache_key, "code_commit": prov[0], "environment_digest": prov[1], "contract": v2.CONTRACT,
           "viewpoint": ep.pc.viewpoint(cam.camera_name), "camera": cam.camera_name, "run": cam.run, "stratum": cam.window["stratum_id"],
           "leakage_group": cam.window["leakage_group_id"], "usable_s": usable, "reference_s5": ref_row["s5"],
           "references": {"n": len(refs), "assessable": sum(r.assessable for r in refs), "g1": sum(1 for r in refs if "G1" in groups[r.ref_event_id])},
           "checks": {"configs_equal_freeze": True, "reference_equals_freeze": True, "person_log_reproduces_pilot": person_log_reproduced,
                      "stitch_links": len(accepted), "m_inputs": m_check, "flag_inputs": input_audits},
           "ev": {}, "ie": {}, "flags": {}, "runs": {}}
    for col, (s4t, s5s, rows, summ, member_track) in cols.items():
        resolver = d58.pair_resolver(s4t.tables, rows, summ, member_track)
        for bl, s5x in s5s.items():
            events = d58.event_rows(s4t.tables, s5x.tables, resolver)
            check_single_member(events)
            sysev = d58.system_events(events, "a")
            key = f"{col}|{bl}"
            res["ev"][key] = {str(iou): counts_at(refs, groups, sysev, iou, usable) for iou in IOUS}
            res["ie"][key] = ie_share(events)
            res["flags"][key] = flag_counts(s5x.tables)
            res["runs"][key] = ev.run_summary(s5x.tables)
    # --- GV (B: oracle boxes, full_camera; C: detector boxes, A5.2 matched identity)
    persons_o = {t["trk_id"] for t in s3a.tables["track"] if t["class"] == "person"}
    persons_c = {t["trk_id"] for t in s3s.tables["track"] if t["class"] == "person"}
    matched_c = {(r["track_id"], r["frame_index"]): r["physical_identity_id"] for r in rows_c if r["status"] == "matched"}
    id_b = lambda t, i: trk_key[t]
    id_c = lambda t, i: matched_c.get((t, i))
    truth_speed = {(trk_key[r["track_id"]], r["frame_index"]): r["speed_mps"] for r in s4a.tables["object_state"] if r["speed_mps"] is not None}
    gv01_b, avail_b = position_rows(s4b.tables["object_state"], id_b, cam.truth, persons_o)
    gv01_c, avail_c = position_rows(s4c.tables["object_state"], id_c, cam.truth, persons_c)
    res["gv"] = {"B": {"gv01": gv01_b, "availability": avail_b, "gv07": speed_rows(s4b.tables["object_state"], id_b, truth_speed, cam.classes)},
                 "C": {"gv01": gv01_c, "availability": avail_c, "gv07": speed_rows(s4c.tables["object_state"], id_c, truth_speed, cam.classes)}}
    gv04, gv04_check = gv04_rows(s4a.tables["pair_series"], cam.truth, trk_key, v2.S4_V2["person_radius_m"], tuple(m.FORK_PRIOR_M["sdg"]))
    res["gv"]["reference_support"] = {
        "position": dict(Counter(row[1] for row in cam.truth.values())),
        "speed": dict(Counter(cam.classes[key] for key, _ in truth_speed)),
    }
    res["gv"]["gv04_simulator_positions"] = gv04
    res["checks"]["gv04_prior_clearance_differs_from_stored"] = gv04_check
    res["artifacts"] = arts
    res["artifact_digest"] = artifact_digest(arts)
    res["seconds"] = round(time.time() - t0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = res if write else {k: res[k] for k in ("rec_id", "partition", "code_commit", "environment_digest", "cache_key", "artifacts", "artifact_digest", "seconds")}
    write_camera_record(path, payload)
    return rec, "done", res["seconds"]


def gv04_rows(pair_series, truth, trk_key, radius: float, prior_lw: tuple[float, float]) -> tuple[list, list]:
    """GV-04 as revised by D-40 item 4 (AR-59 item 5 REVISED, `research/m1a/gv_revised.py`): on the measured pair-frames
    of the simulator_truth S4, at the simulator positions of both objects and the forklift's simulator yaw, clearance with
    the prior footprint minus clearance with the simulator 3D-box floor footprint. Returns the rows
    (box size, evidence class, difference) and the check [pair-frames, prior clearance != stored clearance]."""
    from rq1.substrate import geometry
    L0, W0 = prior_lw
    rows, check = [], [0, 0]
    for r in pair_series:
        if r["clearance_state"] != "measured" or r["clearance_m"] is None:
            continue
        p, f = truth.get((trk_key[r["pow_nk"][0]], r["frame_index"])), truth.get((trk_key[r["pow_nk"][1]], r["frame_index"]))
        if p is None or f is None or f[6] is None:
            continue
        if f[5] is None:
            prior = geometry.disc_clearance(p[3:5], radius, f[3:5], geometry.circumscribed_radius(L0, W0))
            box = geometry.disc_clearance(p[3:5], radius, f[3:5], geometry.circumscribed_radius(f[6], f[7]))
        else:
            prior = geometry.clearance(p[3:5], radius, f[3:5], f[5], L0, W0)
            box = geometry.clearance(p[3:5], radius, f[3:5], f[5], f[6], f[7])
        check[0] += 1
        check[1] += abs(prior - r["clearance_m"]) > 1e-9
        rows.append((f"{f[6]:.2f}x{f[7]:.2f}", r["evidence_class"], prior - box))
    return rows, check


def m_write_json(path: Path, obj) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        tmp = Path(handle.name)
        try:
            json.dump(obj, handle, indent=1, sort_keys=True, default=list)
            handle.close()
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)


def cameras(partition: str) -> list[str]:  # pragma: no cover
    partition_dir(partition)
    import v2_sets
    return v2_sets.tuning()


def main():  # pragma: no cover
    what = sys.argv[1]
    if what in ("dev", "estimate", "dev-all", "dev-repeat"):
        workers = int(sys.argv[2]) if what in ("dev-all", "dev-repeat") and len(sys.argv) > 2 else 1
        recs = {"dev": sys.argv[2:], "estimate": [cameras("dev")[0], cameras("dev")[-1]]}.get(what, cameras("dev"))
        for rec in recs:
            require_camera("dev", rec)
        prov = provenance()
        out = development_output(Path(os.environ.get("V2RUN_DEV_DIR", partition_dir("dev"))))
        jobs = [("dev", r, prov, out, what != "dev-repeat") for r in recs]
        it = map(run_camera, jobs) if workers == 1 else Pool(workers, maxtasksperchild=2).imap_unordered(run_camera, jobs)
        for n, r in enumerate(it, 1):
            print(n, *r, flush=True)
        return
    if what in ("run", "repeat"):
        raise SystemExit("refused: D-66/D-67 retired the once-only run and repeat commands")
    raise SystemExit(what)


if __name__ == "__main__":
    main()
