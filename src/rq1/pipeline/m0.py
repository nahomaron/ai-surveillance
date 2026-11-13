"""M0 integration (WP-11, T-16): the whole fixture pipeline on one generated clip.

clips -> S0 -> S1 -> oracle S3 -> S4 -> S5 -> X0b -> V0 -> CV-SIM -> X0c -> S8 (with evaluation_config) -> S8f
-> S4-E2 (FX-12 records) -> S9 (fixture export and report).

Every configuration is TEST-ONLY, every dataset is `fixture`, every time is supplied (never the clock), and nothing is
downloaded. Run `python -m rq1.pipeline.m0 <work_dir>`; it prints the artifact-ID table as JSON."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rq1.decode import stage
from rq1.decode.timestamps import DecodeConfig
from rq1.evaluation import association as assoc
from rq1.evaluation import completeness as cm
from rq1.evaluation import event_metrics as em
from rq1.evaluation import fitness as ft
from rq1.evaluation import matching as mt
from rq1.events import engine, providers, s5
from rq1.export import obx, report
from rq1.fixtures import clips
from rq1.ids import core, lineage
from rq1.ids.artifact import Artifact, Spec, build_artifact
from rq1.registry.registrar import Registrar
from rq1.sampling import plan as sampling
from rq1.splits import builder as splits
from rq1.substrate import builder, oracle
from rq1.validation import converter

Row = dict[str, Any]
CONTRACT = "E-1.2.11"
ROOT = Path(__file__).resolve().parents[3]
T_FROZEN = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)  # supplied event times (AR-7 review)
T_RETRIEVED = datetime(2026, 1, 1, tzinfo=timezone.utc)
TEST_ONLY = "TEST-ONLY"
N = 50  # frames of fx_m0_pipeline


def _params() -> Row:
    return json.loads((ROOT / "fixtures" / "records" / "TEST-ONLY-PARAMETERS.json").read_text())["parameters"]


def _provenance() -> tuple[str, str]:
    """code_commit and environment_digest of every specification: the git commit and the SHA-256 of requirements.lock."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    env = hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()
    return commit, env


def _scene() -> tuple[list[Row], dict, Row]:
    """Appendix N2 G2: person p1 static at (0, 1.90); forklift f1 at x(t) = -2.5 + t. Oracle tracks, positions, CV-SIM truth."""
    person_box, fork_box = [10.0, 10.0, 20.0, 40.0], [30.0, 10.0, 50.0, 40.0]  # inside the 64 x 64 px clip, clear of the border (T8.6)
    truth_tracks = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": person_box, "state": "tracked"} for i in range(N)]},
                    {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": fork_box, "state": "tracked"} for i in range(N)]}]
    positions = {**{(1, i): {"xy": [0.0, 1.90], "cov": [0.0025, 0.0, 0.0025]} for i in range(N)},
                 **{(2, i): {"xy": [-2.5 + i / 10, 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(N)}}
    sim = {"objects": [{"physical_identity_id": "p1", "class": "person", "frames": {i: {"bbox": person_box, "xy": [0.0, 1.90]} for i in range(N)}},
                       {"physical_identity_id": "f1", "class": "forklift", "frames": {i: {"bbox": fork_box, "xy": [-2.5 + i / 10, 0.0]} for i in range(N)}}],
           "interactions": [{"person": "p1", "forklift": "f1", "t_onset_tl_s": 0.0, "t_offset_tl_s": 5.0, "labels": ["H"]}]}
    return truth_tracks, positions, sim


def run(work: Path) -> dict[str, Any]:
    work = Path(work)
    v = _params()
    commit, env = _provenance()
    spec = lambda stage_name, cfgs, inputs, seeds=None: Spec(stage_name, CONTRACT, commit, env, tuple(cfgs), tuple(inputs), seeds or {})
    store: dict[str, Artifact] = {}

    def keep(a: Artifact) -> Artifact:
        store[a.artifact_id] = a
        return a

    # Clips and S0.
    manifest = clips.build_all(work / "clips")
    clip = work / "clips" / "fx_m0_pipeline.mkv"
    sha = manifest["clips"]["fx_m0_pipeline"]["sha256"]
    metadata = {
        "licenses": [{"component": "rq1-m0-fixture", "version": "1", "component_type": "dataset", "license_label": "fixture", "terms_location": "unknown",
                      "obligations": [], "license_status": "not_read"}],
        "datasets": [{"name": "rq1-m0-fixture", "version": "1", "data_origin": "synthetic_rendered", "dataset_kind": "fixture", "source_url": "local",
                      "retrieved_utc": T_RETRIEVED, "license": ["rq1-m0-fixture", "1"], "annotation_levels": ["objects", "tracks", "world_geometry"],
                      "unit_status": "verified",
                      "sites": [{"site_label": "s1", "data_origin": "synthetic_rendered", "site_kind": "synthetic_scene", "independent_of_development": False,
                                 "cameras": [{"camera_label": "c1", "viewpoint_class": "ceiling", "declared_overlap_camera_ids": []}],
                                 "sessions": [{"session_label": "run1", "scripted": True, "extent": None, "lineage": {"seed": 7}}]}]}],
        "source_files": [{"sha256": sha, "size_bytes": clip.stat().st_size, "container": "mkv", "codec": "mpeg4", "uri": "fx_m0_pipeline.mkv",
                          "privacy_state": "synthetic_no_persons", "retention_policy_id": "rtp_018f3a2e-7b1c-7def-8a12-3456789abcde"}],
        "recordings": [{"dataset": ["rq1-m0-fixture", "1"], "site": "s1", "session": "run1", "camera": "c1", "sha256": sha, "registration_label": "r1",
                        "alignment": None}],
    }
    s0 = keep(Registrar().register(metadata, spec("S0", (), ())))
    recording = s0.tables["recording"][0]
    timeline = s0.tables["timeline"][0]
    dataset = s0.tables["dataset_source"][0]

    # S1.
    decode_record = {"k_sup": v["k_sup"], "f_untimed": v["f_untimed"], "f_sub": v["f_sub"], "rules_version": "rv1",
                     "delta_nom_declarations": [{"recording_id": recording["rec_id"], "delta_nom_s": 0.1, "evidence_ref": "fx_m0_pipeline clip definition"}],
                     "final_frame_support": "delta_nom", "version_label": TEST_ONLY, "version_label_null_reason": None}
    dcf = core.make_id("dcf", decode_record)
    s1_cfg = DecodeConfig(k_sup=v["k_sup"], f_untimed=v["f_untimed"], f_sub=v["f_sub"], rules_version="rv1", declared={recording["rec_id"]: 0.1})
    item = stage.S1Input(recording_id=recording["rec_id"], camera_id=recording["camera_id"], path=clip, faults_path=work / "clips" / "fx_m0_pipeline.faults.json")
    s1 = keep(stage.run_s1(timeline, [item], s1_cfg, spec("S1", (dcf,), (s0.artifact_id,))))

    # Oracle S3 and S4.
    truth_tracks, positions, sim = _scene()
    orc = core.make_id("orc", {"source": "simulator_truth", "scene": "N2-G2", "version_label": TEST_ONLY})
    s3 = keep(oracle.OracleTrackSource().tracks(recording["rec_id"], truth_tracks, s1.tables["frame"], spec("S3", (orc,), (s1.artifact_id,))))
    priors = {"person": {"class": "person", "shape": "disc", "radius_m": 0.30, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"},
              "forklift": {"class": "forklift", "shape": "oriented_rect", "length_m": 2.0, "width_m": 1.0, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}}
    prior_ids = {k: core.make_id("fpp", p) for k, p in priors.items()}
    bands = [(None, 0.0), *zip(v["band_edges_m"], v["band_edges_m"][1:]), (v["band_edges_m"][-1], None)]
    band_scheme = {"edges_m": v["band_edges_m"], "bands": [{"lower_m": lo, "upper_m": hi} for lo, hi in bands], "version_label": TEST_ONLY}
    bsc = core.make_id("bsc", band_scheme)
    substrate_record = {"g_max": v["g_max"], "pair_classes": ["forklift"], "v_min": v["v_min"], "k_sup": v["k_sup"], "motion_models": ["constant_velocity"],
                        "prediction_horizon_s": v["tau"], "version_label": TEST_ONLY, "version_label_null_reason": None}
    geometry_record = {"w_v_s": v["w_v"], "v_part": v["v_part"], "motion_models": ["constant_velocity"], "footprint_prior_ids": sorted(prior_ids.values()),
                       "version_label": TEST_ONLY, "version_label_null_reason": None}
    gcf, sbc = core.make_id("gcf", geometry_record), s5.substrate_config_id(substrate_record)
    s4_cfg = builder.SubstrateConfig(v["g_max"], v["v_min"], v["w_v"], v["tau"], {"forklift"}, priors, prior_ids, {bsc: bands}, v["v_part"])
    s4 = keep(builder.SubstrateBuilder().build(s1.tables, s3, positions, None, s4_cfg, spec("S4", (gcf, sbc), (s3.artifact_id,))))

    # S5.
    rules = providers.RuleParams(p_provider="R2", k_img=v["k_img"], d_p=v["d_p"], v_min=v["v_min"], d_pc=v["d_pc"], ttc_max=v["ttc_max"], pet_max=v["pet_max"], tau=v["tau"], conflict=("R3",), r5=True,
                                 w_e=v["w_e"], e_turn=v["e_turn"], e_acc=v["e_acc"], e_dec=v["e_dec"], k_sigma=v["k_sigma"])
    params = engine.Params(m_gap=v["m_gap"], t_min=v["t_min"], w_post=v["w_post"], d_nm=v["d_nm"], k_sigma=v["k_sigma"], o_max=v["o_max"], g_max=v["g_max"],
                           w_e=v["w_e"], k_c=v["k_c"], k_c_turn=v["k_c_turn"], r5_enabled=True, e_turn=v["e_turn"], e_acc=v["e_acc"], e_dec=v["e_dec"],
                           bands=tuple(bands))
    s5_cfg = s5.S5Config(rules, params, substrate_record, bsc, version_label=TEST_ONLY)
    rcf = s5.config_id(s5_cfg)
    s5_art = keep(s5.build(s1.tables, s4, s5_cfg, spec("S5", (rcf,), (s4.artifact_id,))))

    # X0b split, V0 sampling, CV-SIM, X0c audit.
    split = splits.freeze([{"recording_id": recording["rec_id"], "session_id": recording["session_id"], "dataset_id": dataset["dsr_id"], "partition": "test",
                            "lineage": {"seed": 7}}], split_label="m0", version="1", tier="T1", frozen_utc=T_FROZEN)
    x0b = keep(build_artifact(spec("X0b", (), (s0.artifact_id,)), {"split_manifest": [split]}))
    spm = x0b.tables["split_manifest"][0]["spm_id"]
    group = split["leakage_groups"][0]["leakage_group_id"]
    extent = (min(c["t_start_tl_s"] for c in s1.tables["coverage_segment"]), max(c["t_end_tl_s"] for c in s1.tables["coverage_segment"]))
    camera_group = s0.tables["camera_group"][0]["cgp_id"]
    population = [{**w, "stratum_id": "h", "recording_ids": [recording["rec_id"]], "partition_at_sampling": "test", "leakage_group_id": group}
                  for w in sampling.tile_windows(camera_group, timeline["tl_id"], extent, v["w_ref"], v["w_guard"], extent[0])]
    selected = sampling.draw_res(population, {"h": len(population)}, seed=1)
    plan = sampling.plan_rows("m0", "1", "RES", spm, population, selected, {"h": len(population)}, 1,
                              {"camera_group_ids": [camera_group], "w_ref_s": v["w_ref"], "w_guard_s": v["w_guard"], "tiling_origin_tl_s": extent[0]}, T_FROZEN)
    v0 = keep(build_artifact(spec("V0", (), (x0b.artifact_id, s1.artifact_id), {"res": 1}), plan))
    window = {**v0.tables["reference_window"][0], "exhaustive": True}
    reference = converter.SimReferenceConverter().convert(window, s1.tables, sim, "wf_" + "0" * 26)
    cvsim = keep(build_artifact(spec("CV-SIM", (), (v0.artifact_id, s1.artifact_id)), reference))
    audit = splits.audit(split, spm, [], "metadata", 1, [{"recording_id": recording["rec_id"], "session_id": recording["session_id"]}])
    x0c = keep(build_artifact(spec("X0c", (), (x0b.artifact_id,)), {"leakage_audit": [audit]}))

    # S8: association, matching, metrics, completeness, attribution.
    s8_tables, summary = _evaluate(s3, s4, s5_art, cvsim, sim, window, rcf, spm, v)
    evc_record = mt.evaluation_config(v["iou_m"], v["iou_cm"], v["eps_amb"], v["n_miss"], v["bootstrap_B"], 1, "rule_conformance",
                                      summary["label_groups"], TEST_ONLY)
    evc = core.make_id("evc", evc_record)
    s8 = keep(build_artifact(spec("S8", (evc, spm), (s5_art.artifact_id, cvsim.artifact_id, v0.artifact_id, x0c.artifact_id)), s8_tables))

    # S8f: fitness by scope. No acceptance criterion is registered at M0, so the scope is not_yet_assessable (FT-04).
    scope = {"output_id": "E1-episodes", "measurement_definition_version": "E1_v1", "data_origin": dataset["data_origin"], "condition_stratum": "fixture",
             "calibration_tier": "ground_plane_homography", "config_id": rcf, "intended_use": "candidate_event_screening", "criterion_ids": []}
    decided = ft.decide(scope, [], {}, None)
    fit_row = ft.fitness_row(scope, decided, ft.construct_status(None, None, None, "CV0"),
                             {"definition_evidence_ref": None, "definition_evidence_ref_null_reason": "not_supplied", "source_refs": None,
                              "source_refs_null_reason": "not_supplied", "expert_alignment_result_id": None, "expert_alignment_result_id_null_reason": "not_supplied"}, False)
    s8f = keep(build_artifact(spec("S8f", (evc, spm), (s8.artifact_id,)), {"measurement_fitness": [fit_row]}))

    # S4-E2: the revised FX-12 records (CT-E-26). No E2 measurement stage exists at M0; the records come from the fixture.
    e2 = keep(build_artifact(spec("S4-E2", (gcf,), (s3.artifact_id,)), _fx12_records(s3)))

    # CT-E-28: every metric row's artifact traces to source_file through art_ IDs.
    untraced = obx.check_lineage([s8.artifact_id, s8f.artifact_id, e2.artifact_id], store)

    # S9: fixture export and report.
    tables = {"dataset_source": s0.tables["dataset_source"], "recording": s0.tables["recording"], "source_file": s0.tables["source_file"],
              "coverage_segment": s1.tables["coverage_segment"], "pow": s4.tables["pow"], "exposure_profile": s4.tables["exposure_profile"],
              **{t: s5_art.tables[t] for t in ("episode", "discarded_episode", "candidate_event", "event_count_summary")},
              "load_state": e2.tables["load_state"], "e2_occupancy_profile": e2.tables["e2_occupancy_profile"],
              "completeness_record": s8.tables["completeness_record"], "metric_result": s8.tables["metric_result"],
              "measurement_fitness": s8f.tables["measurement_fitness"]}
    configurations = [{"config_id": c, "version_label": TEST_ONLY} for c in (dcf, orc, gcf, sbc, bsc, rcf, evc)]
    export_manifest = obx.export("fixture_verification", tables, configurations, [dataset], work / "out")
    text = _report(export_manifest, s5_art, s8, summary)
    (work / "out" / "fixture" / "M0_fixture_report.md").write_text(text, encoding="utf-8")

    stages = {"S0": s0, "S1": s1, "S3": s3, "S4": s4, "S5": s5_art, "X0b": x0b, "V0": v0, "CV-SIM": cvsim, "X0c": x0c, "S8": s8, "S8f": s8f, "S4-E2": e2}
    return {"contract": CONTRACT, "code_commit": commit, "environment_digest": env,
            "artifacts": {k: {"artifact_id": a.artifact_id, "payload_sha256": a.payload_sha256, "rows": {t: len(r) for t, r in sorted(a.tables.items())}}
                          for k, a in stages.items()},
            "configurations": {"dcf": dcf, "orc": orc, "gcf": gcf, "sbc": sbc, "bsc": bsc, "rcf": rcf, "evc": evc},
            "export_files": export_manifest["files"], "lineage_untraced": untraced, "summary": {k: v_ for k, v_ in summary.items() if k != "label_groups"}}


def _evaluate(s3: Artifact, s4: Artifact, s5_art: Artifact, cvsim: Artifact, sim: Row, window: Row, rcf: str, spm: str, v: Row) -> tuple[dict, dict]:
    track_of = {t["track_local_id"]: t["trk_id"] for t in s3.tables["track"]}
    cls = {t["trk_id"]: t["class"] for t in s3.tables["track"]}
    win = window["rwn_id"]
    camera = cvsim.tables["ref_coverage_label"][0]["camera_id"]
    frames: dict[int, tuple[list, list]] = {}
    for p in s3.tables["track_point"]:
        if p["state"] != "lost" and p.get("bbox_xyxy_px"):
            frames.setdefault(p["frame_index"], ([], []))[0].append(assoc.Box(track_of[p["track_nk"][1]], cls[track_of[p["track_nk"][1]]], tuple(p["bbox_xyxy_px"])))
    for obj in sim["objects"]:
        for i, f in obj["frames"].items():
            frames.setdefault(i, ([], []))[1].append(assoc.Box(obj["physical_identity_id"], obj["class"], tuple(f["bbox"])))
    support = {f: 0.1 for f in frames}
    rows = assoc.associate(frames, v["iou_cm"], v["eps_amb"])
    summaries, missed = assoc.summarize(rows, support)
    assoc_rows = [{"window_id": win, "camera_id": camera, **r, "track_id_null_reason": None if r["track_id"] else "not_applicable",
                   "physical_identity_id_null_reason": None if r["physical_identity_id"] else "not_applicable"} for r in rows]
    summary_rows = [{"window_id": win, **s, "dominant_identity_id_null_reason": None if s["dominant_identity_id"] else "not_applicable",
                     "dominant_share_null_reason": None if s["dominant_share"] is not None else "not_applicable"} for s in summaries]

    # Matching: S_VIEW candidate events against CV-SIM interactions; the converter's labels give the mapping (AR-39 item 3 ruling).
    refs_rows = cvsim.tables.get("ref_interaction", [])
    references = [mt.Reference(r["rin_id"], r["t_onset_tl_s"], r["t_offset_tl_s"], (r["person_identity_id"], r["forklift_identity_id"]),
                               r["assessability"] == "assessable") for r in refs_rows]
    label_groups = converter.label_group_mapping(refs_rows, sim)
    episodes = {(e["pow_id"], e["start_frame"]): e for e in s5_art.tables["episode"]}
    pows = {p["pow_id"]: p for p in s4.tables["pow"]}
    events = []
    for ev in s5_art.tables["candidate_event"]:
        if ev["scenario"] != "S_VIEW":
            continue
        ep = episodes[tuple(ev["member_episode_nks"][0])]
        pw = pows[ep["pow_id"]]
        pair, _ = assoc.event_pair(rows, summaries, pw["person_track_id"], pw["forklift_track_id"], ep["closest_approach_frame"])
        labels = frozenset(x for x in ("O", "H", "PC", "NM", "UD", "CT", "IE") if ev[f"lbl_{x}"])
        events.append(mt.SystemEvent(ev["member_episode_nks"][0], ev["evt_id"], ev["t_onset_tl_s"], ev["t_end_tl_s"], pair, labels))
    match_rows, counts = [], {}
    for group in ("G1", "G2", "any"):
        records = mt.match_window(references, events, group, v["iou_m"], "rule_conformance", label_groups)
        counts[group] = em.window_counts(records, window["window_length_s"] * 3600.0 / 3600.0)
        for r in records:
            row = {"window_id": win, "config_id": rcf, "scenario": "S_VIEW", "label_group": group, **r}
            for name in ("ref_event_id", "system_event_id", "temporal_iou", "onset_error_s", "offset_error_s"):
                row[f"{name}_null_reason"] = None if row[name] is not None else "not_applicable"
            match_rows.append(row)
    headline = em.headline([counts["G1"]])

    # Metric results: rule-conformance references, so claim level none (RV-02). One window: no interval (interval_method none).
    metric_rows = []
    for metric_id in ("EV-M1", "EV-M2"):
        value = headline[metric_id]
        row = {"metric_id": metric_id, "definition_version": "N4", "split_version_id": spm, "config_id": rcf, "scenario": "S_VIEW", "label": "G1",
               "support_basis": None, "slice": {"window_id": win}, "sample_type": "RES", "estimand": "frame_description", "estimand_validity": "design_valid",
               "validity": "valid", "leakage_screening_status": "passed_available_screening", "weighted": True, "value": value,
               "ci_low": None, "ci_high": None, "ci_level": None, "interval_method": "none", "n_units": 1, "n_events": counts["G1"].a, "eff_n": 1.0,
               "counts_only": None, "shared_scene_content": False, "claim_level": "none", "coverage_companion_id": None, "reference_class": "rule_conformance"}
        metric_rows.append(row)

    # Completeness from the association and the S4 POW frames (T12.4; CM-10 with the detected placeholder, T13.1).
    pair_series = {}
    for r in s4.tables["pair_series"]:
        pair_series.setdefault(tuple(r["pow_nk"]), {})[r["frame_index"]] = r
    track_class = {}
    for p in s3.tables["track_point"]:
        track_class.setdefault(p["frame_index"], {})[track_of[p["track_nk"][1]]] = p["evidence_class"]
    w = cm.WindowFrames(support=support, ref_visible={i: {o["physical_identity_id"]: o["class"] for o in sim["objects"] if i in o["frames"]} for i in frames},
                        ref_present={i: {o["physical_identity_id"] for o in sim["objects"] if i in o["frames"]} for i in frames}, assoc=rows, track_class=track_class,
                        pows=[{"person_track": p["person_track_id"], "forklift_track": p["forklift_track_id"],
                               "frames": {i: r["evidence_class"] for i, r in pair_series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])].items()},
                               "clearance_state": {i: r["clearance_state"] for i, r in pair_series[(p["person_track_id"], p["forklift_track_id"], p["start_frame"])].items()},
                               "calibration_tier": "ground_plane_homography"} for p in s4.tables["pow"]])
    completeness = []
    for basis in sorted(cm.BASES):
        for ident, ratio in cm.cm_object(w, "person", basis).items():
            completeness.append(cm.record(win, "CM-01", basis, {"physical_identity_id": ident}, ratio, "none", v["iou_cm"], v["k_kf"]))
        for (p, f), ratio in cm.cm03(w, None, basis).items():
            completeness.append(cm.record(win, "CM-03", basis, {"pair": f"{p}|{f}"}, ratio, "none", v["iou_cm"], v["k_kf"]))
        for tier, ratio in cm.cm08(w, basis).items():
            completeness.append(cm.record(win, "CM-08", basis, {"calibration_tier": tier}, ratio, "none", v["iou_cm"], v["k_kf"]))
    completeness += cm.cm10_records(w, win, "none", v["iou_cm"], v["k_kf"])

    misses = [r for r in match_rows if r["match_type"] in ("miss", "false_alert")]
    tables = {"match_record": match_rows, "metric_result": metric_rows, "completeness_record": completeness,
              "track_identity_assoc": assoc_rows, "track_identity_summary": summary_rows}
    tables = {t: [_with_reasons(t, r) for r in rows_] for t, rows_ in tables.items()}
    summary = {"match_types": sorted({(r["label_group"], r["match_type"]) for r in match_rows}), "headline_G1": headline,
               "missed_identities": missed, "misses_and_false_alerts": len(misses), "label_groups": label_groups,
               "cm01": {r["support_basis"]: r["value"] for r in completeness if r["metric_id"] == "CM-01"}}
    return tables, summary


def _with_reasons(table: str, row: Row) -> Row:
    """Fill each missing null reason of a nullable column: not_applicable when the value is null (AR-47 item 3)."""
    from rq1.schema import registry
    out = dict(row)
    for f in registry.TABLES[table].fields:
        if f.name.endswith("_null_reason") and f.name not in out and not f.derived:
            base = f.name[: -len("_null_reason")]
            out[f.name] = None if out.get(base) is not None else "not_applicable"
    return out


def _fx12_records(s3: Artifact) -> dict[str, list[Row]]:
    """The revised FX-12 records (Appendix T): load_state elevated, height 2.4 +- 0.3 m, mass null not_supplied; one occupancy profile."""
    from rq1.fixtures import identity_rows as rows
    fx12 = json.loads((ROOT / "fixtures" / "records" / "FX-12.json").read_text())["expected"]
    track = s3.tables["track"][1]["trk_id"]
    load = rows.row("load_state", track_id=track, elevation_state=fx12["elevation_state"], height_m=fx12["height_m"], height_sigma_m=fx12["height_sigma_m"],
                    method="height_reference_plane")
    load["load_mass_kg"], load["load_mass_kg_null_reason"] = None, fx12["load_mass_kg_null_reason"]
    profile = rows.row("e2_occupancy_profile", person_track_id=s3.tables["track"][0]["trk_id"], load_track_id=track)
    return {"load_state": [load], "e2_occupancy_profile": [profile]}


def _report(manifest: dict, s5_art: Artifact, s8: Artifact, summary: dict) -> str:
    title, counts = report.counts_section(s5_art.tables["event_count_summary"])
    conformance = report.conformance_section(s8.tables["metric_result"])
    completeness = report.completeness_section(s8.tables["completeness_record"], visibility_assumed=False)
    return report.render(manifest, "fixture", "M0 fixture pipeline report", [(title, counts), conformance, completeness])


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), indent=1, sort_keys=True, default=str))
