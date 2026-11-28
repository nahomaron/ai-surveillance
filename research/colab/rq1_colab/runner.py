"""D-60 STEP 4 (a): S2 detection on Colab GPU, the frozen D-45 detector, raw output in the `out/m1b/pilot/s2raw/` format.

Standalone (no `rq1` import). The same path as the CPU run (`research/m1b/s2_yolo_world.py`, `s2_frames.py`,
`zero_shot_probe.yolo_world`):
- frames: PyAV `container.decode(video=0)` in decode order, `to_ndarray(format="rgb24")`, only the eligible frames that
  the job manifest lists from the stored S1 `frame` table (decode_seq -> frame_index); the count must equal the manifest's;
- model: YOLO-World v2-s (`yolov8s-worldv2.pt`), `set_classes(["person", "forklift"])` once, `predict(img[:, :, ::-1],
  conf=0.05, verbose=False)` with the Ultralytics defaults (imgsz 640, NMS IoU 0.7, max_det 300); RGB flipped to BGR;
- every box with score >= 0.05 is stored raw (class, box rounded to 3 decimals, score to 6); the class thresholds
  (person 0.20, forklift 0.05) are applied when the S2 artifact is built on the laptop, as for the CPU files.
Checks: the SHA-256 of both weight files (`yolov8s-worldv2.pt`, CLIP `ViT-B-32.pt`) and of every input video against
the job manifest, before use. Resumable per camera: a camera whose output file and `.done.json` sidecar exist and agree
is skipped. `colab_manifest.json` (rewritten after every camera) lists every output file with its SHA-256, the device,
the versions, wall times and frame counts, and the SHA-256 of the job manifest.

  python -m rq1_colab.runner --job <job.json> --data-root <dir> --out <dir> --weights-dir <dir> [--device 0] [--verify-only]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from pathlib import Path
from typing import Callable, Iterator

from . import access

CLASSES = ("person", "forklift")
SCORE_FLOOR = 0.05
PREDICT = {"imgsz": 640, "iou": 0.7, "max_det": 300}
MODEL = "yolov8s-worldv2.pt"
WEIGHTS = {  # research/m1b/zero_shot_weights.json
    MODEL: {"url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s-worldv2.pt", "bytes": 25923032,
            "sha256": "9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792"},
    "clip/ViT-B-32.pt": {"url": "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt",
                         "bytes": 353976522, "sha256": "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af"},
}
PINNED = {"ultralytics": "8.4.215", "av": "19.0.2"}
MANIFEST = "colab_manifest.json"


class RunnerError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def compress(seq_to_index: dict[int, int]) -> list[list[int]]:
    """{decode_seq: frame_index} -> runs [seq_start, length, index_start] where both rise by 1."""
    runs: list[list[int]] = []
    for s in sorted(seq_to_index):
        i = seq_to_index[s]
        if runs and runs[-1][0] + runs[-1][1] == s and runs[-1][2] + runs[-1][1] == i:
            runs[-1][1] += 1
        else:
            runs.append([s, 1, i])
    return runs


def expand(runs: list[list[int]]) -> dict[int, int]:
    out: dict[int, int] = {}
    for s, n, i in runs:
        if n < 1 or s < 0:
            raise RunnerError(f"bad eligibility run {[s, n, i]}")
        for k in range(n):
            if s + k in out:
                raise RunnerError(f"decode_seq {s + k} listed twice")
            out[s + k] = i + k
    if len(set(out.values())) != len(out):
        raise RunnerError("a frame_index is listed twice")
    return out


def frames(video: Path, seq_to_index: dict[int, int]) -> Iterator[tuple[int, int, "object"]]:
    """(decode_seq, frame_index, RGB uint8 array) of the eligible frames, in decode order (`s2_frames.py`)."""
    access.refuse_path(video)
    import av
    n = 0
    with av.open(str(video)) as container:
        for k, frame in enumerate(container.decode(video=0)):
            if k not in seq_to_index:
                continue
            n += 1
            yield k, seq_to_index[k], frame.to_ndarray(format="rgb24")
    if n != len(seq_to_index):
        raise RunnerError(f"{video}: decoded {n} eligible frames, the manifest lists {len(seq_to_index)}")


def fetch_weights(weights_dir: Path, download: Callable[[str, Path], None] | None = None) -> dict[str, str]:
    """Each weight file at weights_dir/<name>: downloaded from its published URL when absent, then checked by SHA-256."""
    got = {}
    for name, w in WEIGHTS.items():
        path = weights_dir / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".part")
            (download or (lambda url, p: urllib.request.urlretrieve(url, p)))(w["url"], tmp)
            os.replace(tmp, path)
        digest = sha256(path)
        if digest != w["sha256"] or path.stat().st_size != w["bytes"]:
            raise RunnerError(f"{name}: SHA-256 {digest} or size differs from the D-45 weights")
        got[name] = digest
    return got


def yolo_world(weights_dir: Path, device: str) -> Callable:
    """The probe's `yolo_world()` with the device as the only change."""
    from ultralytics import YOLOWorld, settings
    import ultralytics.nn.text_model as text_model
    settings.update({"sync": False, "weights_dir": str(weights_dir)})
    # `text_model` binds WEIGHTS_DIR at import; point it at the checked folder so CLIP loads <weights_dir>/clip/ViT-B-32.pt,
    # the file whose SHA-256 was checked (clip.load also checks it against the hash in its URL).
    text_model.WEIGHTS_DIR = Path(weights_dir)
    model = YOLOWorld(str(weights_dir / MODEL))
    model.set_classes(list(CLASSES))
    if sha256(weights_dir / "clip/ViT-B-32.pt") != WEIGHTS["clip/ViT-B-32.pt"]["sha256"]:
        raise RunnerError("CLIP text encoder changed after set_classes")
    names = model.names

    def one(img):
        r = model.predict(img[:, :, ::-1], conf=SCORE_FLOOR, device=device, verbose=False)[0]
        b = r.boxes
        return [{"class": names[int(c)], "box": [round(float(v), 3) for v in xyxy], "score": round(float(s), 6)}
                for xyxy, s, c in zip(b.xyxy.tolist(), b.conf.tolist(), b.cls.tolist())]
    return one


def environment(device: str) -> dict:
    env = {"python": platform.python_version(), "platform": platform.platform(), "device": device}
    for mod in ("torch", "ultralytics", "av", "numpy", "cv2"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception as e:  # recorded, never hidden
            env[mod] = f"unavailable: {type(e).__name__}"
    try:
        import torch
        env["cuda"] = torch.version.cuda
        env["cudnn"] = torch.backends.cudnn.version()
        env["device_name"] = torch.cuda.get_device_name(int(device)) if device not in ("cpu", "mps") else device
        env["torch_threads"] = torch.get_num_threads()
    except Exception as e:
        env["device_name"] = f"unavailable: {type(e).__name__}"
    env["runner_commit"] = runner_commit()
    return env


def runner_commit() -> str | None:
    """The repository commit of the runner: `RQ1_RUNNER_COMMIT` (set by the notebook from its clone), else the commit pip
    installed this package from (PEP 610 direct_url.json), else None."""
    if os.environ.get("RQ1_RUNNER_COMMIT"):
        return os.environ["RQ1_RUNNER_COMMIT"]
    try:
        from importlib.metadata import distribution
        d = json.loads(distribution("rq1-colab").read_text("direct_url.json") or "{}")
        return d.get("vcs_info", {}).get("commit_id")
    except Exception:
        return None


def _done_path(out: Path, rec: str) -> Path:
    return out / f"{rec}.done.json"


def finished(out: Path, rec: str, cache_key: str) -> dict | None:
    """The sidecar of a finished camera when its output file still has the recorded SHA-256, else None."""
    access.refuse_camera({"rec_id": rec})
    gz, done = out / f"{rec}.json.gz", _done_path(out, rec)
    if not (gz.exists() and done.exists()):
        return None
    side = json.loads(done.read_text())
    return side if side.get("cache_key") == cache_key and side.get("sha256") == sha256(gz) else None


def run_camera(cam: dict, data_root: Path, out: Path, detect: Callable, env: dict, weights: dict[str, str], cache_key: str) -> dict:
    access.refuse_camera(cam, data_root)
    video = data_root / cam["uri"]
    digest = sha256(video)
    if digest != cam["sha256"] or video.stat().st_size != cam["size_bytes"]:
        raise RunnerError(f"{cam['rec_id']}: input video {cam['uri']} differs from the manifest (SHA-256 {digest})")
    seq = expand(cam["eligible_runs"])
    if len(seq) != cam["n_eligible"]:
        raise RunnerError(f"{cam['rec_id']}: eligibility runs give {len(seq)} frames, the manifest says {cam['n_eligible']}")
    t0 = time.time()
    rows, seconds, size = [], [], None
    for k, i, img in frames(video, seq):
        t1 = time.perf_counter()
        dets = detect(img)
        seconds.append(round(time.perf_counter() - t1, 4))
        size = (img.shape[1], img.shape[0])
        rows.append({"frame_index": i, "decode_seq": k, "detections": dets})
    rec = {"rec_id": cam["rec_id"], "model": MODEL, "weights_sha256": weights[MODEL], "classes": list(CLASSES), "score_floor": SCORE_FLOOR,
           "predict": {**PREDICT, "device": env["device"]}, "width": size[0] if size else None, "height": size[1] if size else None,
           "frames": rows, "seconds": seconds, "first_frame_includes_warmup": True, "wall_s": round(time.time() - t0, 1),
           "torch": env.get("torch"), "torch_threads": env.get("torch_threads"), "ultralytics": env.get("ultralytics"), "python": env.get("python"),
           "code_commit": env.get("runner_commit"), "device_name": env.get("device_name"), "cuda": env.get("cuda"), "av": env.get("av"),
           "input_sha256": digest}
    gz = out / f"{cam['rec_id']}.json.gz"
    tmp = gz.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as f:
        json.dump(rec, f)
    os.replace(tmp, gz)
    side = {"cache_key": cache_key, "rec_id": cam["rec_id"], "file": gz.name, "sha256": sha256(gz), "bytes": gz.stat().st_size, "frames": len(rows),
            "n_eligible": cam["n_eligible"], "wall_s": rec["wall_s"], "input_sha256": digest, "device_name": env.get("device_name")}
    done = _done_path(out, cam["rec_id"])
    temporary = done.with_suffix(".tmp")
    temporary.write_text(json.dumps(side, indent=1))
    os.replace(temporary, done)
    return side


def write_manifest(out: Path, job: dict, job_sha: str, env: dict, weights: dict[str, str], cache_key: str) -> dict:
    access.refuse_manifest(job)
    files = {}
    for cam in job["cameras"]:
        side = finished(out, cam["rec_id"], cache_key)
        if side is not None:
            files[cam["rec_id"]] = side
    m = {"job": job["job"], "job_manifest_sha256": job_sha, "decision": job.get("decision"), "environment": env, "pinned": PINNED,
         "weights_sha256": weights, "cameras_in_job": len(job["cameras"]), "cameras_finished": len(files),
         "complete": len(files) == len(job["cameras"]), "frames_total": sum(f["frames"] for f in files.values()),
         "wall_s_total": round(sum(f["wall_s"] for f in files.values()), 1), "files": [files[k] for k in sorted(files)]}
    tmp = out / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(m, indent=1))
    os.replace(tmp, out / MANIFEST)
    return m


def verify_inputs(job: dict, data_root: Path) -> list[str]:
    access.refuse_manifest(job, data_root)
    bad = []
    for cam in job["cameras"]:
        p = data_root / cam["uri"]
        if not p.exists():
            bad.append(f"missing: {cam['uri']}")
        elif p.stat().st_size != cam["size_bytes"] or sha256(p) != cam["sha256"]:
            bad.append(f"differs: {cam['uri']}")
    return bad


def main(argv: list[str] | None = None, detector: Callable | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--job", required=True)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--weights-dir", required=True)
    ap.add_argument("--device", default="0")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args(argv)
    job_path, data_root, out, wdir = Path(a.job), Path(a.data_root), Path(a.out), Path(a.weights_dir)
    job_sha = sha256(job_path)
    job = json.loads(job_path.read_text())
    if job.get("format") != "rq1-colab-job-1":
        raise RunnerError(f"{job_path}: not an rq1-colab job manifest")
    bad = verify_inputs(job, data_root)
    if bad:
        raise RunnerError("input check failed:\n" + "\n".join(bad))
    print(f"inputs: {len(job['cameras'])} videos, every SHA-256 equal to the manifest", flush=True)
    weights = fetch_weights(wdir)
    print("weights: SHA-256 equal to the D-45 weights", flush=True)
    if a.verify_only:
        return {"verified": len(job["cameras"])}
    out.mkdir(parents=True, exist_ok=True)
    env = environment(a.device)
    cache_key = hashlib.sha256(json.dumps({"job": job_sha, "environment": env, "weights": weights},
                                        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    detect = detector or yolo_world(wdir, a.device)
    for cam in job["cameras"]:
        if finished(out, cam["rec_id"], cache_key) is not None:
            print(cam["rec_id"], "already finished: skipped", flush=True)
            continue
        side = run_camera(cam, data_root, out, detect, env, weights, cache_key)
        m = write_manifest(out, job, job_sha, env, weights, cache_key)
        print(cam["rec_id"], "done", side["frames"], "frames", side["wall_s"], "s;", m["cameras_finished"], "of", m["cameras_in_job"], flush=True)
    m = write_manifest(out, job, job_sha, env, weights, cache_key)
    print("complete" if m["complete"] else "INCOMPLETE", m["cameras_finished"], "of", m["cameras_in_job"], "cameras", flush=True)
    return m


if __name__ == "__main__":
    try:
        main()
    except (RunnerError, ValueError) as e:
        sys.exit(f"STOPPED: {e}")
