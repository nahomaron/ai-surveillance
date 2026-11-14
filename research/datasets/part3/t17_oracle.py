"""T-18 / Appendix T T17 as amended by T18 (E-1.2.16): S1 (rules version rv2) and ORACLE-S3 for every registered recording
of one S0 index, the T17.7 counts per run, and the not-visible run-length distribution per class (T18 amendment 3).
IDs and counts only; artifacts go to the git-ignored <out_dir>.
Parameters k_sup, f_untimed, f_sub, g_max are the TEST-ONLY values (no pre-registration is frozen): the artifacts are TEST-ONLY.
A camera whose truth is refused under T17.5 (an excess in (90, 150] px) gets no oracle track and is reported.
S1 reuse: T18 changes nothing in S1. With <previous_counts.json> <previous_out_dir>, a recording's S1 artifact of the
previous run is verified (file hashes and payload reconstruction) and reused when it has the same decode configuration
and S0 input; otherwise the recording is decoded again. The S3 artifact names the S1 artifact it was built from.
Usage: PYTHONPATH=src python t17_oracle.py <data_root> <s0_out_dir> <out_dir> <counts.json> [<previous_counts.json> <previous_out_dir>]"""
import collections
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import tarfile
from pathlib import Path

from rq1.adapters import oracle_truth as ot
from rq1.adapters import sdg_truth, smartspaces
from rq1.decode import quality, stage
from rq1.decode.timestamps import DecodeConfig
from rq1.ids import core
from rq1.ids import artifact as artifacts
from rq1.ids.artifact import Spec, write_artifact
from rq1.schema import files
from rq1.schema.errors import ContractError
from rq1.substrate import oracle

ROOT = Path(__file__).resolve().parents[3]
CONTRACT, TEST_ONLY = "E-1.2.16", "TEST-ONLY"
V = json.loads((ROOT / "fixtures" / "records" / "TEST-ONLY-PARAMETERS.json").read_text())["parameters"]
DECODE_RECORD = {"k_sup": V["k_sup"], "f_untimed": V["f_untimed"], "f_sub": V["f_sub"], "rules_version": quality.RV2, "delta_nom_declarations": [],
                 "final_frame_support": "delta_nom", "version_label": TEST_ONLY, "version_label_null_reason": None}
DCF = core.make_id("dcf", DECODE_RECORD)
G_MAX = V["g_max"]
ORC = core.make_id("orc", {"source": "simulator_truth", "rule": "Appendix T T17, T18", "g_max": G_MAX, "version_label": TEST_ONLY})
KEYS = ("tracked", "predicted", "lost", "lost_long_run", "outside_span", "never_visible_objects")


def provenance():
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return commit, hashlib.sha256((ROOT / "requirements.lock").read_bytes()).hexdigest()


def s1_worker(args):
    entry, data_root, commit, env = args
    cfg = DecodeConfig(k_sup=V["k_sup"], f_untimed=V["f_untimed"], f_sub=V["f_sub"], rules_version=quality.RV2, declared={})
    item = stage.S1Input(recording_id=entry["rec_id"], camera_id=entry["camera_id"], path=Path(data_root) / entry["uri"])
    return entry, stage.run_s1(entry["timeline"], [item], cfg, Spec("S1", CONTRACT, commit, env, (DCF,), (entry["s0"],), {}))


def reuse_s1(entry, previous, previous_dir):
    """The verified S1 artifact of the previous run for this recording: (artifact id, frame rows, manifest spec), or None."""
    art = previous.get(entry["rec_id"])
    directory = os.path.join(previous_dir or "", art or "")
    if art is None or not os.path.exists(os.path.join(directory, "manifest.json")):
        return None
    spec = json.load(open(os.path.join(directory, "manifest.json")))["spec"]
    if spec["stage"] != "S1" or spec["config_ids"] != [DCF] or spec["input_artifact_ids"] != [entry["s0"]]:
        return None
    if artifacts.verify(directory) != art:
        return None
    return art, files.read_table(os.path.join(directory, "frame.parquet"), "frame", artifacts.SCHEMA_VERSION), spec


def s1_frames(order, data_root, commit, env, out_dir, origin, previous, previous_dir):
    """Yields (entry, S1 artifact id, frame rows, S1 code commit, S1 contract label, reused) in `order`."""
    with multiprocessing.Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        for entry in order:
            kept = reuse_s1(entry, previous, previous_dir)
            if kept is not None:
                yield entry, kept[0], kept[1], kept[2]["code_commit"], kept[2]["schema_bundle"], True
                continue
            _, s1 = pool.apply(s1_worker, ((entry, data_root, commit, env),))
            write_artifact(s1, os.path.join(out_dir, s1.artifact_id), origin[entry["s0"]])
            yield entry, s1.artifact_id, s1.tables["frame"], commit, CONTRACT, False


def run_lengths(frames, classes, seq_to_index):
    """Per class: {run length in decoded frames: number of runs}; and the runs whose T18 outcome would differ if the length
    were counted in eligible frames instead (CR-024), with the runs that contain a frame that is not eligible."""
    lengths, differ, with_ineligible = collections.defaultdict(collections.Counter), 0, 0
    for key, runs in ot.not_visible_spans(frames).items():
        for start, n in runs:
            lengths[classes[key]][n] += 1
            eligible = sum(1 for k in range(start, start + n) if seq_to_index.get(k) is not None)
            with_ineligible += eligible != n
            differ += (n > G_MAX) != (eligible > G_MAX)
    return {cls: {str(n): c for n, c in sorted(counter.items())} for cls, counter in sorted(lengths.items())}, differ, with_ineligible


class Annotations:
    def __init__(self, data_root):
        self.root, self.tars, self.scenes = data_root, {}, {}

    def lines(self, entry, suffix):
        name = f"{entry['prefix']}.{suffix}"
        if "dir" in entry["annotation"]:
            path = os.path.join(self.root, entry["annotation"]["dir"], name)
            return open(path).read().splitlines() if os.path.exists(path) else None
        rel = entry["annotation"]["tar"]
        if rel not in self.tars:
            tf = tarfile.open(os.path.join(self.root, rel))
            self.tars[rel] = (tf, {m.name: m for m in tf.getmembers()})
        tf, names = self.tars[rel]
        return tf.extractfile(names[name]).read().decode().splitlines() if name in names else None

    def scene(self, entry, n_frames):
        """Parsed SmartSpaces truth; scenes with byte-identical ground truth share one parse."""
        path = os.path.join(self.root, entry["annotation"]["ground_truth"])
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 22), b""):
                h.update(block)
        key = (h.hexdigest(), n_frames)
        if key not in self.scenes:
            self.scenes = {key: smartspaces.parse_frames(smartspaces.load(path), n_frames)}
        return self.scenes[key]


def sdg_frames(entry, ann, n_video, out):
    od, cp = ann.lines(entry, "object_detection.jsonl"), ann.lines(entry, "camera_params.jsonl")
    counts = {"object_detection": None if od is None else len(od), "camera_params": None if cp is None else len(cp)}
    if entry["calibration"] is None or not ot.usable_truth(n_video, counts):
        out["no_truth"] = {"video_frames": n_video, **counts}
        return None
    cal, frames, band = entry["calibration"], [], []
    for k, line in enumerate(od):
        row = {}
        for o in sdg_truth.parse_frame(line):
            try:
                row[o.prim], note = ot.sdg_obs(cal, o)
            except ContractError:
                band.append({"decode_seq": k, "class": o.cls, "excess_px": round(sdg_truth.hull_excess(cal, o), 2), "visible": o.tight is not None})
                continue
            if note == "truth_defect":
                out["truth_defects"].append({"decode_seq": k, "class": o.cls, "excess_px": round(sdg_truth.hull_excess(cal, o), 1)})
            elif note == "unchecked":
                out["unchecked_boxes"] += 1
        frames.append(row)
    if band:
        out["refused"] = band  # T17.5: ERR-INVARIANT, no oracle track for this camera
        return None
    return frames, {prim: o.cls for row in frames for prim, o in row.items()}


def smartspaces_frames(entry, ann, n_video, out):
    parsed = ann.scene(entry, n_video)  # refuses frame ids other than 0 .. n-1 (T17.4)
    cam = entry["camera"]
    frames = [{o.obj_id: ot.smartspaces_obs(o, cam) for o in objs} for objs in parsed]
    return frames, {o.obj_id: o.cls for objs in parsed for o in objs}


def main():
    data_root, s0_dir, out_dir, counts_path = sys.argv[1:5]
    previous_path, previous_dir = (sys.argv[5], sys.argv[6]) if len(sys.argv) > 6 else (None, None)
    previous = {c["rec_id"]: c["s1"] for c in json.load(open(previous_path))["cameras"]} if previous_path else {}
    index = json.load(open(os.path.join(s0_dir, "index.json")))
    origin = {e["s0"]: json.load(open(os.path.join(s0_dir, e["s0"], "manifest.json")))["data_origin"] for e in index}
    commit, env = provenance()
    ann, cams = Annotations(data_root), []
    order = sorted(index, key=lambda e: (e["annotation"].get("ground_truth", ""), e["run"], e["camera"]))
    for entry, s1_id, frame_rows, s1_commit, s1_contract, reused in s1_frames(order, data_root, commit, env, out_dir, origin, previous, previous_dir):
        seq_to_index = {f["decode_seq"]: f["frame_index"] for f in frame_rows}
        out = {"dataset": entry["dataset"], "run": entry["run"], "camera": entry["camera"], "rec_id": entry["rec_id"], "s1": s1_id,
               "s1_code_commit": s1_commit, "s1_contract": s1_contract, "s1_reused": reused,
               "frames_decoded": len(frame_rows), "frames_eligible": sum(1 for f in frame_rows if f["eligible"]), "truth_defects": [], "unchecked_boxes": 0}
        built = (sdg_frames if entry["dataset"] == "sdg" else smartspaces_frames)(entry, ann, len(frame_rows), out)
        if built is not None:
            frames, classes = built
            tracks, counts = ot.camera_tracks(entry["calibration"], frames, G_MAX)
            out.update({k: counts[k] for k in KEYS})
            out["not_visible_run_lengths"], out["runs_differing_if_eligible_frames"], out["runs_with_ineligible_frame"] = run_lengths(frames, classes, seq_to_index)
            out["points_on_ineligible_frames"] = sum(1 for pts in tracks.values() for p in pts if seq_to_index.get(p.decode_seq) is None)
            truth, _ = ot.s3_truth(tracks, classes, seq_to_index)
            out["tracks"] = dict(sorted(collections.Counter(t["class"] for t in truth).items()))
            if truth:
                s3 = oracle.OracleTrackSource().tracks(entry["rec_id"], truth, frame_rows, Spec("S3", CONTRACT, commit, env, (ORC,), (s1_id,), {}))
                write_artifact(s3, os.path.join(out_dir, s3.artifact_id), origin[entry["s0"]])
                out["s3"] = s3.artifact_id
        cams.append(out)
        print(len(cams), "/", len(order), entry["run"], entry["camera"], flush=True)
    runs = []
    extra = ("truth_defect", "unchecked_boxes", "points_on_ineligible_frames", "runs_differing_if_eligible_frames", "runs_with_ineligible_frame")
    for key in sorted({(c["dataset"], c["run"]) for c in cams}):
        mine = [c for c in cams if (c["dataset"], c["run"]) == key]
        runs.append({"dataset": key[0], "run": key[1], "cameras": len(mine), "cameras_with_oracle_tracks": sum("s3" in c for c in mine),
                     "cameras_without_truth": sorted(c["camera"] for c in mine if "no_truth" in c),
                     "cameras_refused_t17_5": sorted(c["camera"] for c in mine if "refused" in c),
                     **{k: sum(c.get(k, 0) for c in mine) for k in KEYS},
                     "truth_defect": sum(len(c["truth_defects"]) for c in mine),
                     **{k: sum(c.get(k, 0) for c in mine) for k in extra[1:]}})
    total = {k: sum(r[k] for r in runs) for k in (*KEYS, *extra, "cameras", "cameras_with_oracle_tracks")}
    total.update({"runs": len(runs), "cameras_without_truth": sum(len(r["cameras_without_truth"]) for r in runs),
                  "cameras_refused_t17_5": sum(len(r["cameras_refused_t17_5"]) for r in runs),
                  "s1_reused": sum(c["s1_reused"] for c in cams)})
    histogram = collections.defaultdict(collections.Counter)  # (dataset, class) -> run length -> runs
    for c in cams:
        for cls, by_length in c.get("not_visible_run_lengths", {}).items():
            for n, count in by_length.items():
                histogram[(c["dataset"], cls)][int(n)] += count
    distribution = [{"dataset": d, "class": cls, **ot.run_length_summary([n for n, count in h.items() for _ in range(count)]),
                     "runs_longer_than_g_max": sum(count for n, count in h.items() if n > G_MAX),
                     "frames_in_runs_longer_than_g_max": sum(n * count for n, count in h.items() if n > G_MAX),
                     "histogram": {str(n): h[n] for n in sorted(h)}} for (d, cls), h in sorted(histogram.items())]
    summary = {"contract": CONTRACT, "code_commit": commit, "decode_config_id": DCF, "oracle_config_id": ORC, "rules_version": quality.RV2,
               "parameters": TEST_ONLY, "g_max": G_MAX, "run_length_unit": "decoded frames of the camera (CR-024)", "percentiles": "nearest-rank",
               "s1_code_commits": sorted({c["s1_code_commit"] for c in cams}),
               "reference_visibility": ot.VISIBILITY_NOTE, "total": total, "not_visible_run_lengths": distribution, "runs": runs, "cameras": cams}
    json.dump(summary, open(counts_path, "w"), indent=1)
    print(json.dumps({"total": total, "not_visible_run_lengths": [{k: v for k, v in d.items() if k != "histogram"} for d in distribution]}, indent=1))


if __name__ == "__main__":
    main()
