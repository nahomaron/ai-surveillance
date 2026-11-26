"""T-21 (M1a validation run) per-camera pipeline: S3 oracle tracks -> S4 -> S5, with the pre-registration v1 values.

Shared by the R4 equivalence check (AR-58, D-38 A.1) and the run driver. It imports `rq1` from whatever is on sys.path,
so the same file can drive the code of an older commit for the equivalence check.

Base values: `docs/preregistration_FROZEN.md` section 4 (version 1). Validation recordings only (D-36, D-37): any other
recording is refused with ERR-LEAKAGE.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/datasets/part3"))

import t17_oracle as drv  # noqa: E402
from rq1.adapters import oracle_truth as ot  # noqa: E402
from rq1.events import baselines, engine, providers, s5  # noqa: E402
from rq1.ids import artifact as A  # noqa: E402
from rq1.ids import core  # noqa: E402
from rq1.ids.artifact import Spec  # noqa: E402
from rq1.schema import files  # noqa: E402
from rq1.schema.errors import ContractError  # noqa: E402
from rq1.substrate import builder, oracle  # noqa: E402

BASELINES = ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6")

# Pre-registration v1, section 4.2 (S4) and 4.3 (S5): base values.
S4_BASE = {"g_max": 15, "v_min": 0.3, "w_v": 0.5, "tau": 2.0, "person_radius_m": 0.30, "fork_length_scale": 1.0, "fork_width_scale": 1.0}
FORK_PRIOR_M = {"sdg": (3.03, 1.13), "smartspaces": (2.68, 1.16)}  # length, width (D-34 B.5; CR-023)
BAND_EDGES_M = [0.0, 0.5, 1.0, 2.0, 4.0]
V_PART = 0.5
S5_BASE = {"k_img": 0.05, "d_p": 2.0, "d_pc": 1.0, "ttc_max": 1.5, "pet_max": 1.0, "w_e": 1.0, "e_turn": 1.5, "e_acc": 1.0, "e_dec": 2.0,
           "m_gap": 5, "t_min": 0.2, "w_post": 1.0, "d_nm": 0.5, "k_sigma": 2.0, "o_max": 0.5, "k_c": 3.0, "k_c_turn": 3.0}


class Context:
    """Frozen split, T17 counts, S0 index and annotation reader for one dataset."""

    def __init__(self, ds: str):
        self.ds = ds
        self.freeze = json.load(open(ROOT / "docs/preregistration/freeze_record.json"))
        self.counts = json.load(open(ROOT / f"research/datasets/part3/t17_counts_{ds}.json"))
        self.index = {e["rec_id"]: e for e in json.load(open(ROOT / f"out/s0_{ds}/index.json"))}
        self.ann = drv.Annotations(str(ROOT / "data"))

    def is_validation(self, cam: dict) -> bool:
        if self.ds == "sdg":
            return cam["run"] in self.freeze["split"]["sdg_validation_runs"]
        return cam["run"] == "Warehouse_000"  # X0b: the SmartSpaces synthetic group is validation (D-34 B.10)

    def camera(self, rec_id: str) -> dict:
        cam = next(c for c in self.counts["cameras"] if c["rec_id"] == rec_id)
        if not self.is_validation(cam):
            raise ContractError("ERR-LEAKAGE", f"{rec_id} is not in the validation partition of X0b (D-37)")
        return cam

    def reference_camera(self, rec_id: str) -> dict:
        """D-61 STEP 5 (section 1.7): a camera whose v2 references may be built from simulator truth, in the validation
        **or test** partition of X0b (SDG only). Only `load_for_reference` calls this; no system stage may (D-37)."""
        if self.ds != "sdg":
            raise ContractError("ERR-LEAKAGE", f"{rec_id}: v2 reference building on test is SDG only (D-61 STEP 5)")
        cam = next(c for c in self.counts["cameras"] if c["rec_id"] == rec_id)
        if cam["run"] not in self.freeze["split"]["sdg_validation_runs"] and cam["run"] not in self.freeze["split"]["sdg_test_runs"]:
            raise ContractError("ERR-LEAKAGE", f"{rec_id} is in no X0b partition")
        return cam

    def validation_cameras(self) -> list[dict]:
        """Validation cameras with an ORACLE-S3 (T17.4 usable truth), in canonical rec_id order."""
        return sorted((c for c in self.counts["cameras"] if self.is_validation(c) and c.get("s3")), key=lambda c: c["rec_id"])


@dataclasses.dataclass
class Loaded:
    s1: dict
    frames: list  # per decode_seq truth observations
    classes: dict
    seq: dict
    calibration: dict | None


def load(ctx: Context, rec_id: str) -> Loaded:
    return _load(ctx, rec_id, ctx.camera(rec_id))  # ERR-LEAKAGE unless validation (D-37)


def load_for_reference(ctx: Context, rec_id: str) -> Loaded:
    """D-61 STEP 5: truth and S1 of a validation or test camera, for T21.1 reference building from simulator truth only
    (the D-61 hard limits allow it on test; no S2 or later system stage runs there)."""
    return _load(ctx, rec_id, ctx.reference_camera(rec_id))


def _load(ctx: Context, rec_id: str, cam: dict) -> Loaded:
    entry = ctx.index[rec_id]
    s1dir = ROOT / f"out/t17_{ctx.ds}/{cam['s1']}"
    s1 = {t: files.read_table(str(s1dir / f"{t}.parquet"), t, A.SCHEMA_VERSION) for t in ("frame", "coverage_segment", "decode_summary")}
    out = {"truth_defects": [], "unchecked_boxes": 0}
    frames, classes = (drv.sdg_frames if ctx.ds == "sdg" else drv.smartspaces_frames)(entry, ctx.ann, len(s1["frame"]), out)
    seq = {f["decode_seq"]: f["frame_index"] for f in s1["frame"]}
    cal = next((c for c in files.read_table(str(ROOT / f"out/s0_{ctx.ds}" / entry["s0"] / "calibration.parquet"), "calibration", A.SCHEMA_VERSION)
                if c["camera_id"] == entry["camera_id"]), None)
    return Loaded(s1, frames, classes, seq, cal)


def spec(stage: str, commit, config_ids=(), inputs=()) -> Spec:
    """`commit`: (code commit, environment digest), or one label used for both (equivalence check)."""
    code, env = commit if isinstance(commit, tuple) else (commit, commit)
    return Spec(stage, "E-1.2.19", code, env, tuple(config_ids), tuple(inputs), {})


def s3(ctx: Context, rec_id: str, data: Loaded, g_max: int, commit: str):
    """ORACLE-S3 (T17-T20) at g_max, and the simulator positions for the simulator_truth geometry."""
    entry = ctx.index[rec_id]
    inel = frozenset(k for k, i in data.seq.items() if i is None)
    tracks, _ = ot.camera_tracks(entry["calibration"], data.frames, g_max, inel)
    truth, positions = ot.s3_truth(tracks, data.classes, data.seq)
    art = oracle.OracleTrackSource().tracks(rec_id, truth, data.s1["frame"], spec("S3", commit, (core.make_id("orc", {"g_max": g_max}),)))
    return art, positions, tracks


def substrate_config(ctx: Context, p: dict, edges: list | None = None, label: str = "preregistration-v1") -> tuple[dict, builder.SubstrateConfig, str, list]:
    """`edges` (clearance band edges, default v1 `BAND_EDGES_M`) and `label` (version_label) default to v1, so v1 IDs are unchanged."""
    edges = BAND_EDGES_M if edges is None else list(edges)
    length, width = FORK_PRIOR_M[ctx.ds]
    length, width = length * p["fork_length_scale"], width * p["fork_width_scale"]
    fork = {"class": "forklift", "shape": "oriented_rect", "length_m": length, "width_m": width, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
    priors = {"person": {"class": "person", "shape": "disc", "radius_m": p["person_radius_m"], "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"},
              "forklift": fork}
    if ctx.ds == "smartspaces":
        priors["pallet_truck"] = dict(fork, **{"class": "pallet_truck"})
    pid = {k: core.make_id("fpp", v) for k, v in priors.items()}
    bands = [(None, 0.0), *zip(edges, edges[1:]), (edges[-1], None)]
    bsc = core.make_id("bsc", {"edges_m": edges})
    record = {"g_max": p["g_max"], "pair_classes": ["forklift"], "v_min": p["v_min"], "k_sup": 1.5, "motion_models": ["constant_velocity"],
              "prediction_horizon_s": p["tau"], "version_label": label, "version_label_null_reason": None}
    cfg = builder.SubstrateConfig(p["g_max"], p["v_min"], p["w_v"], p["tau"], {"forklift"}, priors, pid, {bsc: bands}, V_PART)
    return record, cfg, bsc, bands


def s4(ctx: Context, data: Loaded, s3_art, positions: dict, geometry: str, p: dict, commit: str, edges: list | None = None,
       label: str = "preregistration-v1"):
    """geometry 'simulator_truth' (oracle positions) or 'full_camera' (foot point through the calibration)."""
    record, cfg, _, _ = substrate_config(ctx, p, edges, label)
    if geometry == "simulator_truth":
        pos, cal = positions, None
    elif geometry == "full_camera":
        if data.calibration is None:
            return None
        pos, cal = {}, data.calibration
    else:
        raise ValueError(geometry)
    gcf = core.make_id("gcf", {"geometry": geometry})
    return builder.SubstrateBuilder().build(data.s1, s3_art, pos, cal, cfg, spec("S4", commit, (s5.substrate_config_id(record), gcf), (s3_art.artifact_id,)))


def s5_config(ctx: Context, bl: str, p4: dict, p5: dict, edges: list | None = None, label: str = "preregistration-v1",
              m_gap_s: float | None = None, join_across_pow: bool | None = None) -> s5.S5Config:
    """Defaults are v1 (IDs unchanged). `m_gap_s` (T25.3) and `join_across_pow` (T25.2) are absent unless given."""
    record, _, bsc, bands = substrate_config(ctx, p4, edges, label)
    rules = providers.RuleParams(p_provider="R2", k_img=p5["k_img"], d_p=p5["d_p"], v_min=p4["v_min"], d_pc=p5["d_pc"], ttc_max=p5["ttc_max"],
                                 pet_max=p5["pet_max"], tau=p4["tau"], conflict=("R3",), r5=True, w_e=p5["w_e"], e_turn=p5["e_turn"],
                                 e_acc=p5["e_acc"], e_dec=p5["e_dec"], k_sigma=p5["k_sigma"])
    params = engine.Params(m_gap=p5["m_gap"], t_min=p5["t_min"], w_post=p5["w_post"], d_nm=p5["d_nm"], k_sigma=p5["k_sigma"], o_max=p5["o_max"],
                           g_max=p4["g_max"], w_e=p5["w_e"], k_c=p5["k_c"], k_c_turn=p5["k_c_turn"], r5_enabled=True, e_turn=p5["e_turn"],
                           e_acc=p5["e_acc"], e_dec=p5["e_dec"], bands=tuple(bands))
    r, pr = baselines.configure(bl, rules, params)
    return s5.S5Config(r, pr, record, bsc, version_label=label, m_gap_s=m_gap_s, join_across_pow=join_across_pow)


def s5_build(ctx: Context, data: Loaded, s4_art, bl: str, p4: dict, p5: dict, commit: str):
    c = s5_config(ctx, bl, p4, p5)
    return s5.build(data.s1, s4_art, c, spec("S5", commit, (s5.config_id(c),), (s4_art.artifact_id,)))


# --- T21 reference interactions (CV-SIM, oracle path; contract E-1.2.19) -------------------------------------------------

def reference_tracks(data: Loaded) -> dict:
    """T21.1: every object of the camera's truth, with a point on every eligible frame on which it exists in the truth
    (has a pose), whatever its visibility. Each point is `tracked` (detected) with a box that is never truncated, so that
    visibility does not enter the reference through the T8.6 evidence state or T8.7 Q (AR-59 item 2). The box carries
    no image measurement; only R1 reads boxes, and BL-6 does not use R1."""
    summary = next(d for d in data.s1["decode_summary"])
    w, h = summary["width_px"], summary["height_px"]
    box = (0.25 * w, 0.25 * h, 0.75 * w, 0.75 * h)
    tracks = {}
    for key in data.classes:
        points = [ot.Point(k, "tracked", box, objs[key].xy, objs[key].yaw)
                  for k, objs in enumerate(data.frames) if key in objs and data.seq.get(k) is not None]
        if points:
            tracks[key] = points
    return tracks


def reference_s3(rec_id: str, data: Loaded, commit):
    truth, positions = ot.s3_truth(reference_tracks(data), data.classes, data.seq)
    art = oracle.OracleTrackSource().tracks(rec_id, truth, data.s1["frame"], spec("S3", commit, (core.make_id("orc", {"t21_reference": 1}),)))
    return art, positions


def visible_frames(data: Loaded) -> dict[str, list[int]]:
    """T17.1 / T20.1 visible frames (dataset-visible and eligible) per object, as frame_index lists (T21.3)."""
    inel = frozenset(k for k, i in data.seq.items() if i is None)
    return {str(key): sorted(data.seq[k] for k in seqs) for key, seqs in ot._visible_frames(data.frames, inel).items()}


def floor_dims(corners) -> tuple[float, float]:
    """Length and width (m) of the floor face of a 3D box from its 8 world corners (the 4 lowest corners)."""
    import numpy as np
    c = np.asarray(corners() if callable(corners) else corners, float)
    floor = c[np.argsort(c[:, 2])[:4], :2]
    d = sorted(float(np.hypot(*(floor[i] - floor[j]))) for i in range(4) for j in range(i + 1, 4))
    return d[2], d[0]  # sorted pairwise distances of a rectangle: width, width, length, length, diagonal, diagonal


def truth_table(data: Loaded) -> list[tuple]:
    """(object key, class, frame_index, x, y, yaw, box length, box width, visible) on every eligible frame with a pose.
    Used by GV-01, GV-04 and GV-07 (simulator side)."""
    vis = {k: set(v) for k, v in visible_frames(data).items()}
    rows = []
    for k, objs in enumerate(data.frames):
        i = data.seq.get(k)
        if i is None:
            continue
        for key, o in objs.items():
            if data.classes[key] == "person":
                length = width = None
            else:
                length, width = floor_dims(o.corners)
            rows.append((str(key), data.classes[key], i, o.xy[0], o.xy[1], o.yaw, length, width, i in vis.get(str(key), ())))
    return rows
