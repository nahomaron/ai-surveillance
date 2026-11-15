"""G-PR freeze (D-34 C.2, D-35, contract E-1.2.18): the X0b split, the V0 sampling plans and the acceptance-criterion
records of the M1a pre-registration. Values come from `rq1.pipeline.prereg` only.

X0b v1 holds the 720 SDG recordings and the 19 Warehouse_000 recordings (all synthetic_rendered: one data_origin per file,
VR-E-005; Owner answer of 14 Nov 2026). Warehouse_001 is validation through its leakage edge to Warehouse_000 (T16.2) and
enters at M1b as a new split version.
V0: one plan per dataset row and partition (accepted AR): SDG validation, SDG test, SmartSpaces Warehouse_000 validation.
Frame = the camera groups (one camera each) whose recording has usable truth (T17.4, from the T17.7 counts); census of
windows (n_h = N_h) in strata dataset row x viewpoint class. Reads S0 and S1 coverage only (VR-E-050).
Artifacts go to the git-ignored <out_dir>; the freeze record (IDs, lists, criteria) to <record.json>.
Usage: PYTHONPATH=src python research/preregistration/freeze.py <out_dir> <record.json>"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from rq1.ids import artifact as artifacts
from rq1.ids.artifact import Spec, build_artifact, write_artifact
from rq1.pipeline import prereg
from rq1.sampling import plan as sampling
from rq1.schema import files, vr_rules
from rq1.splits import builder as splits
from rq1.splits import draw

ROOT = Path(__file__).resolve().parents[2]
S0_SDG = ROOT / "out/s0_sdg/art_xwrldyhquvmorjhpjxb573tbxk"
S0_SS000 = ROOT / "out/s0_smartspaces/art_k3kmwlyr3dwyaztop6bedfkxts"
COUNTS = {"sdg": ROOT / "research/datasets/part3/t17_counts_sdg.json", "smartspaces": ROOT / "research/datasets/part3/t17_counts_smartspaces.json"}
S1_DIRS = {"sdg": ROOT / "out/t17_sdg", "smartspaces": ROOT / "out/t17_smartspaces"}


def provenance():
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def read(directory, table):
    return files.read_table(os.path.join(directory, f"{table}.parquet"), table, artifacts.SCHEMA_VERSION)


def s0(directory):
    manifest = json.load(open(os.path.join(directory, "manifest.json")))
    assert artifacts.verify(str(directory)) == manifest["artifact_id"]
    return manifest["artifact_id"], manifest["data_origin"], {t: read(directory, t) for t in ("dataset_source", "session", "recording", "camera", "camera_group")}


def main():
    out_dir, record_path = sys.argv[1:3]
    commit, env = provenance()
    sdg_id, sdg_origin, sdg = s0(S0_SDG)
    ss_id, ss_origin, ss = s0(S0_SS000)
    assert sdg_origin == ss_origin == "synthetic_rendered"
    assert ss["session"][0]["lineage"]["ext_run_id"] == "Warehouse_000"

    # X0b: SDG partitions by the D-35 draw; Warehouse_000 validation.
    sessions = {s["ses_id"]: s for s in sdg["session"]}
    runs = sorted((s["lineage"]["ext_run_id"], s["lineage"]["generation_batch"]) for s in sdg["session"])
    run_partition = draw.draw_validation(runs, prereg.SDG_VALIDATION_PER_FAMILY, prereg.SPLIT_SEED)
    rows = []
    for tables, partition_of in ((sdg, lambda s: run_partition[s["lineage"]["ext_run_id"]]), (ss, lambda s: "validation")):
        d, by_session = tables["dataset_source"][0], {s["ses_id"]: s for s in tables["session"]}
        rows += [{"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": d["dsr_id"], "dataset_name": d["name"],
                  "lineage": by_session[r["session_id"]]["lineage"], "partition": partition_of(by_session[r["session_id"]])} for r in tables["recording"]]
    split = splits.freeze(rows, prereg.SPLIT_LABEL, prereg.SPLIT_VERSION, prereg.TIER, prereg.FROZEN_UTC)
    x0b = build_artifact(Spec("X0b", prereg.CONTRACT, commit, env, (prereg.SPLIT_DRAW_ID,), (sdg_id, ss_id), {"split_draw": prereg.SPLIT_SEED}),
                         {"split_manifest": [split]})
    write_artifact(x0b, os.path.join(out_dir, x0b.artifact_id), "synthetic_rendered")
    spm = x0b.tables["split_manifest"][0]["spm_id"]
    group_of = {m: g["leakage_group_id"] for g in split["leakage_groups"] for m in g["member_recording_ids"]}
    partition_of = splits.recording_partitions(split)
    groups_by_partition = {p: sorted({group_of[r] for r, q in partition_of.items() if q == p}) for p in ("validation", "test")}
    assert len(split["leakage_groups"]) == 73 and len(groups_by_partition["validation"]) == 25 and len(groups_by_partition["test"]) == 48

    # V0: one plan per dataset row and partition.
    usable = {}
    for ds, path in COUNTS.items():
        for c in json.load(open(path))["cameras"]:
            usable[c["rec_id"]] = (c["s1"], "no_truth" not in c and "refused" not in c)
    plans, v0_record = [], []
    specs = [("sdg", "validation", sdg, sdg["dataset_source"][0]), ("sdg", "test", sdg, sdg["dataset_source"][0]),
             ("smartspaces_000", "validation", ss, ss["dataset_source"][0])]
    for key, partition, tables, d in specs:
        cfg = prereg.SAMPLING[key]
        cam = {c["cam_id"]: c for c in tables["camera"]}
        group = {g["camera_ids"][0]: g for g in tables["camera_group"]}
        population, s1_ids, outside = [], set(), []
        for r in sorted(tables["recording"], key=lambda r: r["rec_id"]):
            if partition_of[r["rec_id"]] != partition:
                continue
            s1_id, ok = usable[r["rec_id"]]
            if not ok:
                outside.append(r["registration_label"])  # T17.4: outside the oracle and reference populations
                continue
            coverage = read(S1_DIRS["sdg" if key == "sdg" else "smartspaces"] / s1_id, "coverage_segment")
            extent = (min(c["t_start_tl_s"] for c in coverage), max(c["t_end_tl_s"] for c in coverage))
            g = group[r["camera_id"]]
            assert g["timeline_id"] == r["timeline_id"] and extent[0] == 0.0
            stratum = f"{key}:{cam[r['camera_id']]['viewpoint_class']}"
            population += [{**w, "stratum_id": stratum, "recording_ids": [r["rec_id"]], "partition_at_sampling": partition, "leakage_group_id": group_of[r["rec_id"]]}
                           for w in sampling.tile_windows(g["cgp_id"], r["timeline_id"], extent, cfg["w_ref_s"], cfg["w_guard_s"], 0.0)]
            s1_ids.add(s1_id)
        sampling.check_inputs([{"stage": "S1", "table": "coverage_segment"}, {"stage": "X0b", "table": "split_manifest"}])
        strata = {h: sum(1 for w in population if w["stratum_id"] == h) for h in sorted({w["stratum_id"] for w in population})}
        selected = sampling.draw_res(population, strata, prereg.SAMPLING_SEED)  # census: n_h = N_h, pi = 1, weight 1
        label = f"m1a-{key}-{partition}"
        frame = {"camera_group_ids": sorted({w["camera_group_id"] for w in population}), "w_ref_s": cfg["w_ref_s"], "w_guard_s": cfg["w_guard_s"], "tiling_origin_tl_s": 0.0}
        tables_v0 = sampling.plan_rows(label, "1", "RES", spm, population, selected, strata, prereg.SAMPLING_SEED, frame, prereg.FROZEN_UTC,
                                       population_definition_ref=f"{partition} partition of {spm}, dataset row {d['dsr_id']} ({d['name']}, {d['data_origin']}), "
                                                                 "camera groups with usable truth (T17.4)")
        v0 = build_artifact(Spec("V0", prereg.CONTRACT, commit, env, (), (x0b.artifact_id, *sorted(s1_ids)), {"res": prereg.SAMPLING_SEED}), tables_v0)
        write_artifact(v0, os.path.join(out_dir, v0.artifact_id), "synthetic_rendered")
        p = v0.tables["sampling_plan"][0]
        v0_record.append({"plan_label": label, "artifact_id": v0.artifact_id, "payload_sha256": v0.payload_sha256, "plan_id": p["spl_id"], "frame_sha256": p["frame_sha256"],
                          "population_definition_ref": p["population_definition_ref"], "w_ref_s": cfg["w_ref_s"], "w_guard_s": cfg["w_guard_s"],
                          "strata": p["strata"], "windows": len(v0.tables["reference_window"]), "camera_groups": len(frame["camera_group_ids"]),
                          "leakage_groups": len({w["leakage_group_id"] for w in population}), "recordings_outside_t17_4": sorted(outside)})

    criteria = prereg.criteria()
    run_list = lambda p: sorted(r for r, q in run_partition.items() if q == p)
    record = {"contract": prereg.CONTRACT, "code_commit": commit, "requirements_lock_sha256": env, "frozen_utc": prereg.FROZEN_UTC.isoformat(),
              "preregistration_ref": prereg.PREREGISTRATION_REF, "parameters": "pre-registered (G-PR, D-34, D-35)",
              "split": {"artifact_id": x0b.artifact_id, "payload_sha256": x0b.payload_sha256, "spm_id": spm, "split_label": prereg.SPLIT_LABEL,
                        "version": prereg.SPLIT_VERSION, "tier": prereg.TIER, "basis": split["basis"], "s0_inputs": [sdg_id, ss_id],
                        "split_draw_config_id": prereg.SPLIT_DRAW_ID, "split_draw_record": prereg.SPLIT_DRAW_RECORD,
                        "leakage_groups": len(split["leakage_groups"]), "leakage_groups_by_partition": {k: len(v) for k, v in groups_by_partition.items()},
                        "recordings": len(rows), "families": draw.family_table(runs, run_partition),
                        "sdg_validation_runs": run_list("validation"), "sdg_test_runs": run_list("test"),
                        "smartspaces": {"Warehouse_000": "validation (in X0b v1)",
                                        "Warehouse_001": "validation by its leakage edge to Warehouse_000 (T16.2); not in X0b v1 (VR-E-005: one data_origin per file); enters at M1b as a new split version"}},
              "sampling_plans": v0_record,
              "acceptance_criteria": [{**c, "frozen_utc": c["frozen_utc"].isoformat()} for c in criteria]}
    json.dump(record, open(record_path, "w"), indent=1)
    print(json.dumps({k: record[k] for k in ("code_commit", "frozen_utc")} | {"split": {k: v for k, v in record["split"].items() if not k.startswith("sdg_")}},
                     indent=1), "\n", json.dumps([{k: v for k, v in p.items() if k != "recordings_outside_t17_4"} for p in v0_record], indent=1))


if __name__ == "__main__":
    main()
