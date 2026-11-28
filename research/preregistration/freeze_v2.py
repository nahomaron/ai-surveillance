"""D-61 STEP 5: the pre-registration v2 freeze record. Values from `v2_values.py` (D-61 section 1.3-1.5) and
`rq1.pipeline.prereg_v2` (section 1.6); reference sets from `v2_references.py` (built before, read here and verified).

  PYTHONPATH=src .venv/bin/python research/preregistration/freeze_v2.py <record.json>

The record is a pure function of the repository state and the stored v2 references: two builds at one commit are
byte-identical (`frozen_utc` is a constant taken once, AR-57 item 6). It changes no v1 record and no stored artifact.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "research/m1b"))
import v2_references as vr  # noqa: E402
import v2_values as v2  # noqa: E402

m = v2.m
ROOT = v2.ROOT
LABEL = vr.LABEL
BASELINES = m.BASELINES
REPORTING_ORDER = ["the 110 reporting cameras", "the X0b test (48 SDG runs), before 1 Dec 2026 (Owner, register F1)", "tier 1 (after D-60)"]
NOT_IN_V2 = ["detector fine-tuning (register E1/E4/E6)", "OC-SORT comparison (register D3; stated limitation)",
             "turning-zone idea for e_turn (register C5; future work)", "SmartSpaces v2 references (CR-039)"]
WEIGHTS = ("yolov8s-worldv2.pt", "ViT-B-32.pt (CLIP text encoder)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def detector() -> dict:  # pragma: no cover - reads stored artifacts and weights
    import v2_sets
    import v2_tracker_grid as grid
    cfgs = set()
    for rec in v2_sets.tuning():
        s2_id, art_dir = grid.s2_of(rec)
        cfgs.add(tuple(json.loads((art_dir / s2_id / "manifest.json").read_text())["spec"]["config_ids"]))
    if len(cfgs) != 1:
        raise SystemExit(f"STOP: the tuning S2 artifacts carry {len(cfgs)} configuration ID sets")
    published = json.loads((ROOT / "research/m1b/zero_shot_weights.json").read_text())
    weights = {}
    for name in WEIGHTS:
        w = published[name]
        actual = sha256_file(ROOT / w["path"])
        weights[name] = {"path": w["path"], "bytes": w["bytes"], "sha256": w["sha256"], "sha256_on_disk": actual, "match": actual == w["sha256"]}
    return {**v2.DETECTOR, "s2_config_ids": list(next(iter(cfgs))), "weights": weights,
            "license_components": json.loads((ROOT / "research/m1b/pilot_license_components.json").read_text())}


def tracker() -> dict:  # pragma: no cover - reads the D-55 grid configurations
    import d54_c_v2 as c
    from rq1.tracking import s3_config as sc
    column_c, pkg = c.package()
    params = v2.stitch_params()
    g = v2.S4_V2["g_max"]
    return {"package": v2.TRACKER_PACKAGE, "package_id_hashes_g_max": 15, "family": pkg["family"], "tracker_id": pkg["tracker_id"],
            "forklift_params": pkg["params"], "person_params": column_c["params"], "stitch": v2.stitch_selection(),
            "s3_config_id_g_max_45": sc.trc_id(pkg["run_config"], g), "s3_config_id_g_max_45_stitched": sc.trc_id(pkg["run_config"], g, stitch=params),
            "caveats": ["OC-SORT was not compared (register D3)", "point precision 0.979 measured on SDG only (D-56 ruling 6)",
                        "the T25.1 selection was made on detector S3 bridged at g_max 15 (D-58 STEP 3 as written)"]}


def substrate_and_rules() -> dict:
    from rq1.events import s5
    from rq1.ids import core
    out = {}
    for ds in ("sdg", "smartspaces"):
        ctx = m.Context(ds)
        record, cfg, bsc, _ = v2.substrate_config(ctx, LABEL)
        _, gcf_t24, gcf_t24_record = v2.t24_config(cfg, ds)
        out[ds] = {"substrate_config_id": s5.substrate_config_id(record), "substrate_config_record": record, "band_scheme_id": bsc,
                   "geometry_config_ids": {"simulator_truth": core.make_id("gcf", {"geometry": "simulator_truth"}),
                                           "full_camera_t24": gcf_t24, "full_camera_t24_record": gcf_t24_record},
                   "footprint_prior_ids": dict(sorted(cfg.prior_ids.items())),
                   "rule_config_ids_system": {bl: s5.config_id(v2.s5_config(ctx, bl, LABEL, True)) for bl in BASELINES},
                   "rule_config_id_reference_bl6": s5.config_id(v2.s5_config(ctx, "BL-6", LABEL, False))}
    return out


def evaluation(sets: dict) -> dict:  # pragma: no cover - reads the stored v2 references
    from rq1.evaluation import matching as mt
    from rq1.ids import core
    s8 = {"iou_cm": 0.5, "eps_amb": 0.02, "n_miss": 5, "bootstrap_B": 2000, "seed": 2026111402, "ci_level": 0.95, "k_kf_s": 1.0}
    out = {"parameters": {**s8, "iou_m": v2.IOU_M, "iou_m_reported": list(v2.IOU_M_REPORTED)}, "evaluation_config_ids": {}}
    for name in vr.SETS:
        groups = {}
        for row in sets[name]["rows"]:
            for x in row["references"]:
                rid = core.make_id("rin", {"rec_id": row["rec_id"], "person": x["person_key"], "forklift": x["forklift_key"],
                                           "start_frame": x["start_frame"], "end_frame_excl": x["end_frame_excl"], "reference_s5": row["s5"]})
                groups[rid] = frozenset({"G1"}) if (x["lbl_O"] or x["lbl_H"] or x["lbl_PC"]) else frozenset()
        out["evaluation_config_ids"][name] = {str(iou): core.make_id("evc", mt.evaluation_config(iou, s8["iou_cm"], s8["eps_amb"], s8["n_miss"], s8["bootstrap_B"],
                                                                                              s8["seed"], "rule_conformance", groups, LABEL))
                                              for iou in v2.IOU_M_REPORTED}
    return out


def references() -> dict:  # pragma: no cover - reads and verifies the stored v2 references
    raise SystemExit("refused: D-66 permanently closed the SDG final test")


def main():  # pragma: no cover
    from rq1.pipeline import prereg_v2
    record_path = Path(sys.argv[1])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    sets = references()
    commits = sorted({r["code_commit"] for s in sets.values() for r in s["rows"]})
    if len(commits) != 1 or commits[0] == "uncommitted":
        raise SystemExit(f"STOP: the v2 references were built at {commits}")
    v1 = json.loads((ROOT / "docs/preregistration/freeze_record.json").read_text())
    a1 = json.loads((ROOT / "docs/preregistration/freeze_record_X0b-A1.json").read_text())
    ref_summary = {}
    for name in vr.SETS:
        rows = sets[name]["rows"]
        refs = [x for r in rows for x in r["references"]]
        ref_summary[name] = {"cameras": len(rows), "references": len(refs), "assessable": sum(1 for x in refs if x["assessable"]),
                             "assessable_g1": sum(1 for x in refs if x["assessable"] and (x["lbl_O"] or x["lbl_H"] or x["lbl_PC"])),
                             "set_sha256": vr.set_sha256(rows), "s4_config_ids": sorted({tuple(r["s4_config_ids"]) for r in rows})[0],
                             "s5_config_id": sorted({r["s5_config_id"] for r in rows})[0],
                             "per_camera": [{k: r[k] for k in ("rec_id", "s3", "s4", "s5", "s5_payload_sha256", "references_sha256")} for r in rows]}
        assert len({tuple(r["s4_config_ids"]) for r in rows}) == 1 and len({r["s5_config_id"] for r in rows}) == 1
    record = {"contract": v2.CONTRACT, "decision": "D-61 (Owner, 26 Nov 2026)", "preregistration_ref": prereg_v2.PREREGISTRATION_REF,
              "analysis_code_commit": commits[0], "record_code_commit": head,
              "requirements_lock_sha256": hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest(),
              "frozen_utc": prereg_v2.FROZEN_UTC.isoformat(), "status": "pre-registration v2 values: design anchors and labelled assumptions, never validated thresholds",
              "values": {"S4": v2.S4_V2, "S5": v2.S5_V2, "m_gap_s": v2.M_GAP_S, "band_edges_m": v2.BAND_EDGES_V2, "join_across_pow": v2.JOIN_ACROSS_POW,
                         "delta_nom_s": v2.DELTA_NOM_S, "fork_prior_m": m.FORK_PRIOR_M, "T24": v2.T24, "changed_from_v1": v2.changed_from_v1(),
                         "grids": v2.GRIDS},
              "configurations": {"detector": detector(), "tracker": tracker(), "substrate_and_rules": substrate_and_rules(), "evaluation": evaluation(sets)},
              "acceptance_criteria": [{**c, "frozen_utc": c["frozen_utc"].isoformat()} for c in prereg_v2.criteria()],
              "criteria_basis": prereg_v2.BASIS,
              "split": {"X0b": {k: v1["split"][k] for k in ("artifact_id", "payload_sha256", "spm_id", "split_label", "version")},
                        "X0b-A1": {k: a1[k] for k in sorted(a1) if k in ("artifact_id", "payload_sha256", "spm_id", "split_label", "version")}},
              "sampling_plans_v1": [{k: p[k] for k in ("plan_label", "artifact_id", "payload_sha256", "plan_id")} for p in v1["sampling_plans"]],
              "references": ref_summary, "reporting_order": REPORTING_ORDER, "not_in_v2": NOT_IN_V2}
    record_path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: record[k] for k in ("analysis_code_commit", "record_code_commit", "frozen_utc")}, indent=1))
    print(json.dumps({k: {kk: v[kk] for kk in ("cameras", "references", "assessable_g1", "set_sha256")} for k, v in ref_summary.items()}, indent=1))


if __name__ == "__main__":
    main()
