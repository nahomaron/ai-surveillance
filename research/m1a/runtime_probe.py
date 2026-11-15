"""Timing probe for D-36 step 1 (validation recordings only): S3 -> S4 (simulator_truth and full_camera) -> S5 BL-2..BL-6."""
import json, os, sys, time, resource, tracemalloc
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT / "research/datasets/part3"))
import t17_oracle as drv
from rq1.adapters import oracle_truth as ot
from rq1.events import engine, providers, s5, baselines
from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.schema import files
from rq1.ids import artifact as A
from rq1.substrate import builder, oracle

ds, rec = sys.argv[2], sys.argv[3]
freeze = json.load(open(ROOT / "docs/preregistration/freeze_record.json"))
counts = json.load(open(ROOT / f"research/datasets/part3/t17_counts_{ds}.json"))
cam = next(c for c in counts["cameras"] if c["rec_id"] == rec)
assert ds == "smartspaces" and cam["run"] == "Warehouse_000" or cam["run"] in freeze["split"]["sdg_validation_runs"], "validation only (D-37)"
index = json.load(open(ROOT / f"out/s0_{ds}/index.json")); entry = next(e for e in index if e["rec_id"] == rec)
s1dir = ROOT / f"out/t17_{ds}/{cam['s1']}"
s1 = {t: files.read_table(str(s1dir / f"{t}.parquet"), t, A.SCHEMA_VERSION) for t in ("frame", "coverage_segment", "decode_summary")}
t0 = time.time(); tracemalloc.start()
out = {"truth_defects": [], "unchecked_boxes": 0}
frames, classes = (drv.sdg_frames if ds == "sdg" else drv.smartspaces_frames)(entry, drv.Annotations(str(ROOT / "data")), len(s1["frame"]), out)
seq = {f["decode_seq"]: f["frame_index"] for f in s1["frame"]}
inel = frozenset(k for k, i in seq.items() if i is None)
tracks, _ = ot.camera_tracks(entry["calibration"], frames, 15, inel)
truth, positions = ot.s3_truth(tracks, classes, seq)
spec = lambda st, c=(), i=(): Spec(st, "E-1.2.18", "probe", "probe", tuple(c), tuple(i), {})
s3 = oracle.OracleTrackSource().tracks(rec, truth, s1["frame"], spec("S3", (core.make_id("orc", {"probe": 1}),)))
t_s3 = time.time() - t0
fork = {"sdg": (3.03, 1.13), "smartspaces": (2.68, 1.16)}[ds]
priors = {"person": {"class": "person", "shape": "disc", "radius_m": 0.30, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"},
          "forklift": {"class": "forklift", "shape": "oriented_rect", "length_m": fork[0], "width_m": fork[1], "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}}
if ds == "smartspaces":
    priors["pallet_truck"] = dict(priors["forklift"], **{"class": "pallet_truck"})
pid = {k: core.make_id("fpp", p) for k, p in priors.items()}
edges = [0.0, 0.5, 1.0, 2.0, 4.0]; bands = [(None, 0.0), *zip(edges, edges[1:]), (edges[-1], None)]
bsc = core.make_id("bsc", {"edges_m": edges})
sub = {"g_max": 15, "pair_classes": ["forklift"], "v_min": 0.3, "k_sup": 1.5, "motion_models": ["constant_velocity"], "prediction_horizon_s": 2.0, "version_label": "probe", "version_label_null_reason": None}
cfg = builder.SubstrateConfig(15, 0.3, 0.5, 2.0, {"forklift"}, priors, pid, {bsc: bands}, 0.5)
t1 = time.time()
s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, spec("S4", (s5.substrate_config_id(sub), core.make_id("gcf", {"probe": 1})), (s3.artifact_id,)))
t_s4 = time.time() - t1
rules = providers.RuleParams(p_provider="R2", k_img=0.05, d_p=2.0, v_min=0.3, d_pc=1.0, ttc_max=1.5, pet_max=1.0, tau=2.0, conflict=("R3",), r5=True, w_e=1.0, e_turn=1.5, e_acc=1.0, e_dec=2.0, k_sigma=2.0)
params = engine.Params(m_gap=5, t_min=0.2, w_post=1.0, d_nm=0.5, k_sigma=2.0, o_max=0.5, g_max=15, w_e=1.0, k_c=3.0, k_c_turn=3.0, r5_enabled=True, e_turn=1.5, e_acc=1.0, e_dec=2.0, bands=tuple(bands))
t_s5 = {}
for bl in ("BL-2", "BL-3", "BL-4", "BL-5", "BL-6"):
    r, p = baselines.configure(bl, rules, params)
    c = s5.S5Config(r, p, sub, bsc, version_label="probe")
    t2 = time.time(); a = s5.build(s1, s4, c, spec("S5", (s5.config_id(c),), (s4.artifact_id,))); t_s5[bl] = round(time.time() - t2, 2)
cal = next((c for c in files.read_table(str(ROOT / f"out/s0_{ds}" / entry["s0"] / "calibration.parquet"), "calibration", A.SCHEMA_VERSION) if c["camera_id"] == entry["camera_id"]), None)
t3 = time.time()
s4fc = builder.SubstrateBuilder().build(s1, s3, {}, cal, cfg, spec("S4", (s5.substrate_config_id(sub), core.make_id("gcf", {"probe": 2})), (s3.artifact_id,))) if cal else None
t_fc = time.time() - t3
_, peak = tracemalloc.get_traced_memory()
print(json.dumps({"ds": ds, "rec": rec, "frames": len(s1["frame"]), "tracks": len(truth), "pows": len(s4.tables["pow"]), "pair_series": len(s4.tables["pair_series"]),
                  "t_s3": round(t_s3, 1), "t_s4": round(t_s4, 1), "t_s5": t_s5, "t_s4_full_camera": round(t_fc, 1),
                  "episodes": len(a.tables.get("episode", [])), "peak_traced_MB": round(peak / 2**20), "maxrss_MB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20)}))
