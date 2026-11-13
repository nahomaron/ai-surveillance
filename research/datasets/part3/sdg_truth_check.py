"""T-18 part B data check on every held SDG artifacts run (members directories and the held shard tar). Statistics only.
Per camera: annotation lines vs video frames; E1 objects per frame; tight-box (visible) frames; reprojection excess of the
loose box beyond the clipped 3D-box hull (> 2 px listed); corners behind the camera. Per run: whether
metro_agent_data.world_position ever changes, and the 3D-box floor-centre path length per object.
Usage: PYTHONPATH=src python sdg_truth_check.py <out.json> <members_root> <frames_check.json> [<shard.tar> ...]"""
import collections
import json
import math
import os
import sys
import tarfile

import av

from rq1.adapters import sdg_camera, sdg_truth


def sources(members_root, tars):
    for shard in sorted(os.listdir(members_root)):
        d = os.path.join(members_root, shard)
        if os.path.isdir(d):
            yield shard, (lambda name, d=d: open(os.path.join(d, name), "rb")), sorted(os.listdir(d))
    for t in tars:
        tf = tarfile.open(t)
        names = {m.name: m for m in tf.getmembers()}
        yield os.path.basename(t), (lambda name, tf=tf, names=names: tf.extractfile(names[name])), sorted(names)


def main():
    out_path, members_root, frames_check = sys.argv[1], sys.argv[2], sys.argv[3]
    video_frames = {os.path.basename(r["recording"]): r["frames"] for r in json.load(open(frames_check))["recordings"]}
    cams_out, runs_out, excess = [], [], []
    for shard, opener, names in sources(members_root, sys.argv[4:]):
        for run in sorted({n.split(".")[0] for n in names if n.endswith(".object_detection.jsonl")}):
            stale, paths = collections.defaultdict(set), collections.defaultdict(list)
            for cam in sorted({n.split(".")[1] for n in names if n.startswith(run + ".") and n.endswith(".object_detection.jsonl")}):
                missing = [m for m in ("camera_params.jsonl", "rgb.mp4") if f"{run}.{cam}.{m}" not in names]
                if missing:
                    cams_out.append({"shard": shard, "run": run, "camera": cam, "missing_members": missing})
                    continue
                lines = opener(f"{run}.{cam}.object_detection.jsonl").read().splitlines()
                n_video = video_frames.get(f"{run}.{cam}.rgb.mp4")
                if n_video is None:  # not in the frames check (held shard tar): count the video's frames by demuxing
                    with av.open(opener(f"{run}.{cam}.rgb.mp4")) as c:
                        n_video = sum(1 for p in c.demux(video=0) if p.size)
                cal = sdg_camera.calibration(sdg_camera.static_params([json.loads(l) for l in opener(f"{run}.{cam}.camera_params.jsonl").read().splitlines()]))
                row = {"shard": shard, "run": run, "camera": cam, "lines": len(lines), "video_frames": n_video, "objects": collections.Counter(),
                       "visible": collections.Counter(), "behind": 0, "excess_gt_2px": 0}
                for k, line in enumerate(lines):
                    raw = json.loads(line)["agents"]
                    for prim, a in raw.items():
                        if sdg_truth.object_class(prim, a) and cam.endswith("00") and "metro_agent_data" in a:
                            stale[prim].add(json.dumps(a["metro_agent_data"]["world_position"]))
                    for o in sdg_truth.parse_frame(line):
                        row["objects"][o.cls] += 1
                        row["visible"][o.cls] += o.tight is not None
                        if cam == "ceiling_00":
                            paths[o.prim].append(o.xy)
                        e = sdg_truth.hull_excess(cal, o)
                        if e is None and o.loose is not None:
                            row["behind"] += 1
                        elif e is not None and e > 2:
                            row["excess_gt_2px"] += 1
                            excess.append({"run": run, "camera": cam, "decode_seq": k, "class": o.cls, "excess_px": round(e, 1), "visible": o.tight is not None})
                cams_out.append(row)
            runs_out.append({"shard": shard, "run": run,
                             "world_position_values": {p: len(v) for p, v in sorted(stale.items())},
                             "box_path_m": {p: round(sum(math.dist(a, b) for a, b in zip(v, v[1:])), 3) for p, v in sorted(paths.items())}})
    summary = {"runs": len(runs_out), "cameras": len(cams_out),
               "cameras_missing_members": [f"{c['run']}.{c['camera']}" for c in cams_out if "missing_members" in c],
               "cameras_line_count_mismatch": [f"{c['run']}.{c['camera']}" for c in cams_out if "lines" in c and c["lines"] != c["video_frames"]],
               "boxes": sum(sum(c["objects"].values()) for c in cams_out if "objects" in c),
               "visible": sum(sum(c["visible"].values()) for c in cams_out if "visible" in c),
               "behind_camera": sum(c.get("behind", 0) for c in cams_out), "excess_gt_2px": len(excess),
               "runs_world_position_constant": sum(all(n == 1 for n in r["world_position_values"].values()) for r in runs_out)}
    json.dump({"summary": summary, "excess": excess, "runs": runs_out, "cameras": cams_out}, open(out_path, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
