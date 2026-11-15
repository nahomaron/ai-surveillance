"""D-34 item B.8 (C.3): the truth-side tables of the pre-registration draft §5 (not-visible run lengths, POW sensitivity
counts) and §6.1 (forklift yaw rate), recomputed on the VALIDATION runs of the frozen split only, beside the all-runs
tables; plus the forklift 3D-box sizes behind the footprint priors. Truth-side statistics only: no S5, no S8, no system
output, no metric against a reference. Nothing is re-chosen from these numbers.

Sources: the frozen split (`docs/preregistration/freeze_record.json`); the T17.7 counts under T20.1
(`research/datasets/part3/t17_counts_*.json`); the SDG `ceiling_00` annotation files (the estimator and file set of
`research/datasets/part3/yaw_rate_distribution.py`, unchanged). SmartSpaces: the whole synthetic leakage group is validation
and the all-runs SmartSpaces tables were computed on Warehouse_000 truth, so its validation tables equal its all-runs tables
by construction; they are recomputed from the per-camera counts anyway.
Usage: PYTHONPATH=src python research/preregistration/validation_truth_tables.py <sdg_members_root> <out.json>"""
import collections
import glob
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/datasets/part3"))
import yaw_rate_distribution as yrd  # noqa: E402  (the draft's estimator, reused unchanged)

from rq1.adapters import oracle_truth as ot  # noqa: E402
from rq1.adapters import sdg_truth  # noqa: E402

LIMITS = (5, 15, 30, 60, 150, 300)
G_VALUES = ("5", "15", "30", "60")
YAW_GROUPS = (("< 1", 0, 1), ("1 to < 5", 1, 5), ("5 to < 20", 5, 20), ("20 to < 120", 20, 120), (">= 120", 120, None))


def run_tables(cameras):
    hist = collections.defaultdict(collections.Counter)
    for c in cameras:
        for cls, by_length in c.get("not_visible_run_lengths", {}).items():
            for n, count in by_length.items():
                hist[cls][int(n)] += count
    out = {}
    for cls, h in sorted(hist.items()):
        lengths = [n for n, count in h.items() for _ in range(count)]
        runs, frames = len(lengths), sum(lengths)
        out[cls] = {**ot.run_length_summary(lengths),
                    "share_le": {str(m): {"runs": round(sum(1 for n in lengths if n <= m) / runs, 4) if runs else None,
                                          "frames": round(sum(n for n in lengths if n <= m) / frames, 4) if frames else None} for m in LIMITS}}
    return out


def pow_tables(cameras):
    return {g: {"pows": sum(c["pow_sensitivity"][g]["pows"] for c in cameras if "pow_sensitivity" in c),
                "pows_ended_gap_exceeded": sum(c["pow_sensitivity"][g]["pows_ended_gap_exceeded"] for c in cameras if "pow_sensitivity" in c)} for g in G_VALUES}


def yaw_groups(summary):
    h = summary["histogram_deg_per_s"]
    total = summary["frames"]
    def count(lo, hi):
        return sum(n for k, n in h.items() if float(k[1:].split(",")[0]) >= lo and (hi is None or k.split(", ")[1].rstrip(")") != "inf" and float(k.split(", ")[1].rstrip(")")) <= hi))
    groups = {name: count(lo, hi) for name, lo, hi in YAW_GROUPS}
    return {"frames": total, "p50": summary["p50"], "p90": summary["p90"], "p99": summary["p99"], "max": summary["max"],
            "groups": {k: {"frames": v, "share": round(v / total, 4)} for k, v in groups.items()}}


def sdg_paths(members, runs):
    paths, sizes, files = [], [], []
    for f in sorted(glob.glob(os.path.join(members, "*", "*.ceiling_00.object_detection.jsonl"))):
        name = os.path.basename(f)
        if runs is not None and not any(f"_{r}.ceiling_00." in name for r in runs):
            continue
        files.append(name)
        path = []
        for line in open(f):
            fk = [o for o in sdg_truth.parse_frame(line) if o.cls == "forklift"]
            path.append((fk[0].xy, fk[0].yaw) if fk else None)
            for o in fk:
                c = sdg_truth.box_corners(o.box3d)  # corners 4*ix + 2*iy + iz
                a, b = float(np.linalg.norm(c[4, :2] - c[0, :2])), float(np.linalg.norm(c[2, :2] - c[0, :2]))
                sizes.append((round(max(a, b), 2), round(min(a, b), 2)))
        paths.append(path)
    return paths, sizes, files


def main():
    members, out_path = sys.argv[1:3]
    freeze = json.load(open(ROOT / "docs/preregistration/freeze_record.json"))
    validation = set(freeze["split"]["sdg_validation_runs"])
    sdg = json.load(open(ROOT / "research/datasets/part3/t17_counts_sdg.json"))
    ss = json.load(open(ROOT / "research/datasets/part3/t17_counts_smartspaces.json"))
    sdg_val = [c for c in sdg["cameras"] if c["run"] in validation]
    ss_000 = [c for c in ss["cameras"] if c["run"] == "Warehouse_000"]
    res = {"rule": "D-34 item B.8; truth-side statistics only (no S5, no S8, no system output)", "split_artifact": freeze["split"]["artifact_id"],
           "counts_code_commit": sdg["code_commit"], "contract": freeze["contract"], "run_length_unit": sdg["run_length_unit"], "percentiles": "nearest-rank",
           "sdg": {"validation_runs": len(validation), "validation_cameras": len(sdg_val), "validation_cameras_with_oracle_tracks": sum("s3" in c for c in sdg_val),
                   "run_lengths": {"validation": run_tables(sdg_val), "all_runs": run_tables(sdg["cameras"])},
                   "pow_sensitivity": {"validation": pow_tables(sdg_val), "all_runs": pow_tables(sdg["cameras"])}},
           "smartspaces_warehouse_000": {"cameras": len(ss_000), "note": "the whole synthetic group is validation: validation = all runs",
                                         "run_lengths": {"validation": run_tables(ss_000)}, "pow_sensitivity": {"validation": pow_tables(ss_000)}}}
    val_paths, val_sizes, val_files = sdg_paths(members, validation)
    all_paths, all_sizes, all_files = sdg_paths(members, None)
    yaw = {}
    for label, paths in (("validation", val_paths), ("all_runs", all_paths)):
        rep = yrd.report(paths)
        yaw[label] = {w: yaw_groups(rep[w]["all_frames"]) for w in rep}
    res["sdg"]["yaw_rate_deg_per_s"] = {"runs_with_ceiling_00_annotation": {"validation": len(val_files), "all_runs": len(all_files)}, **yaw}
    count = lambda sizes: {f"{l} x {w}": n for (l, w), n in sorted(collections.Counter(sizes).items())}
    res["sdg"]["forklift_box_size_m"] = {"validation": count(val_sizes), "all_runs": count(all_sizes)}
    prev = json.load(open(ROOT / "research/datasets/part3/yaw_rate_distribution.json"))["smartspaces"]
    res["smartspaces_warehouse_000"]["yaw_rate_deg_per_s"] = {"validation": {w: yaw_groups(prev[w]["all_frames"]) for w in ("window_0.5_s", "window_1.0_s")},
                                                              "source": "research/datasets/part3/yaw_rate_distribution.json (Warehouse_000 truth = the validation group)"}
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
