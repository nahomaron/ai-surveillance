"""T-22 zero-shot detector probe (D-42 option (a), Owner instruction of 19 Nov 2026). Runs in `.venv-det` (Python 3.9,
PyTorch 2.2.2 CPU). Not part of the pipeline; nothing here measures the instrument, and nothing is "validated".

  .venv-det/bin/python research/m1b/zero_shot_probe.py fetch                         -> weights + research/m1b/zero_shot_weights.json
  .venv-det/bin/python research/m1b/zero_shot_probe.py run yolo_world <frames_dir>   -> out/m1b/zs_det_yolo_world.json
  .venv-det/bin/python research/m1b/zero_shot_probe.py run grounding_dino <frames_dir>
  .venv-det/bin/python research/m1b/zero_shot_probe.py evaluate <frames_dir>         -> research/m1b/zero_shot_probe.json

Frames and reference boxes come from `zero_shot_frames.py` (main `.venv`). Prompts: exactly the two class texts
"person" and "forklift" for both models; no other prompt is tried.

Models and post-processing (each library's standard path, lowest probe threshold 0.05 kept, everything else default):
- YOLO-World v2-s (`yolov8s-worldv2.pt`, Ultralytics 8.4.215): `set_classes(["person", "forklift"])` once (CLIP ViT-B/32
  text encoder), then `predict(conf=0.05)` with the library defaults (imgsz 640, NMS IoU 0.7, max_det 300). Input: the
  RGB frame flipped to BGR (Ultralytics' numpy convention).
- Grounding DINO tiny (IDEA-Research/grounding-dino-tiny, transformers 4.57.6): text "person. forklift." (the two class
  texts in the model's phrase format: lower case, each phrase ended by "."). Processor defaults (shortest side 800,
  longest 1333). Per query (900): class score = max sigmoid token logit over that phrase's tokens; class = the phrase with
  the higher score; score = that maximum; kept when >= 0.05. No NMS (the model's standard output has none). Boxes:
  normalized cx, cy, w, h scaled to the original frame.

Timing as in `feasibility.md`: batch 1; one warm-up frame (frame 000), not timed; then all 100 frames in order;
wall-clock per frame from the decoded RGB array in memory to the final box list (pre- and post-processing included;
reading the .npy from disk excluded); torch threads = torch default; no other job running. Peak memory = the process's
peak resident set size (`ru_maxrss`) at the end of the run, one model per process.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = ROOT / "out/m1b/weights"
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "out/m1b/ultralytics_config")  # settings file outside the home folder
os.environ["YOLO_AUTOINSTALL"] = "false"  # Ultralytics must not pip-install anything by itself
os.environ["HF_HOME"] = str(WEIGHTS / "hf")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zs_match as zm  # noqa: E402

CLASSES = ("person", "forklift")
SCORE_MIN = 0.05
YW_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s-worldv2.pt"
YW_FILE = WEIGHTS / "ultralytics/yolov8s-worldv2.pt"
GD_REPO, GD_REV = "IDEA-Research/grounding-dino-tiny", "a2bb814dd30d776dcf7e30523b00659f4f141c71"
GD_FILES = ("config.json", "model.safetensors", "preprocessor_config.json", "special_tokens_map.json", "tokenizer.json",
            "tokenizer_config.json", "vocab.txt", "added_tokens.json")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def ultralytics_settings():
    from ultralytics import settings
    settings.update({"sync": False, "weights_dir": str(WEIGHTS / "ultralytics"), "datasets_dir": str(ROOT / "out/m1b/ultralytics_datasets"),
                     "runs_dir": str(ROOT / "out/m1b/ultralytics_runs")})
    assert settings["sync"] is False


def yolo_world():
    ultralytics_settings()
    from ultralytics import YOLOWorld
    model = YOLOWorld(str(YW_FILE))
    model.set_classes(list(CLASSES))
    names = model.names

    def one(img):
        r = model.predict(img[:, :, ::-1], conf=SCORE_MIN, device="cpu", verbose=False)[0]
        b = r.boxes
        return [{"class": names[int(c)], "box": [round(float(v), 3) for v in xyxy], "score": round(float(s), 6)}
                for xyxy, s, c in zip(b.xyxy.tolist(), b.conf.tolist(), b.cls.tolist())]
    return one


def grounding_dino():
    import torch
    from huggingface_hub import snapshot_download
    from PIL import Image
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
    path = snapshot_download(GD_REPO, revision=GD_REV, allow_patterns=list(GD_FILES))
    processor = AutoProcessor.from_pretrained(path)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(path, use_safetensors=True).eval()
    text = ". ".join(CLASSES) + "."
    ids = processor.tokenizer(text)["input_ids"]
    spans, pos = {}, 1  # token positions of each phrase ([CLS] at 0; "." separates phrases)
    for cls in CLASSES:
        n = len(processor.tokenizer(cls, add_special_tokens=False)["input_ids"])
        spans[cls] = list(range(pos, pos + n))
        pos += n + 1  # the phrase, then "."
    assert processor.tokenizer.convert_ids_to_tokens([ids[i] for i in spans["person"]]) == ["person"]
    assert "".join(t.replace("##", "") for t in processor.tokenizer.convert_ids_to_tokens([ids[i] for i in spans["forklift"]])) == "forklift"

    def one(img):
        h, w = img.shape[:2]
        inputs = processor(images=Image.fromarray(img), text=text, return_tensors="pt")
        with torch.no_grad():
            out = model(**inputs)
        prob = out.logits[0].sigmoid()  # (900, 256)
        per = torch.stack([prob[:, spans[c]].max(1).values for c in CLASSES], 1)  # (900, 2)
        score, cls = per.max(1)
        keep = (score >= SCORE_MIN).nonzero().flatten().tolist()
        boxes = out.pred_boxes[0]
        dets = []
        for q in keep:
            cx, cy, bw, bh = boxes[q].tolist()
            dets.append({"class": CLASSES[int(cls[q])], "box": [round((cx - bw / 2) * w, 3), round((cy - bh / 2) * h, 3), round((cx + bw / 2) * w, 3),
                                                                 round((cy + bh / 2) * h, 3)], "score": round(float(score[q]), 6)})
        return sorted(dets, key=lambda d: -d["score"])
    return one


MODELS = {"yolo_world": yolo_world, "grounding_dino": grounding_dino}


def fetch():
    import urllib.request
    YW_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not YW_FILE.exists():
        urllib.request.urlretrieve(YW_URL, YW_FILE.with_suffix(".part"))
        YW_FILE.with_suffix(".part").rename(YW_FILE)
    yolo_world()  # set_classes downloads the CLIP ViT-B/32 text encoder (clip.load checks its SHA-256 against the URL)
    grounding_dino()  # snapshot_download of the pinned revision
    rec = {"yolov8s-worldv2.pt": {"url": YW_URL, "path": str(YW_FILE.relative_to(ROOT))}}
    clip = WEIGHTS / "ultralytics/clip/ViT-B-32.pt"
    import clip as clip_pkg
    rec["ViT-B-32.pt (CLIP text encoder)"] = {"url": clip_pkg.clip._MODELS["ViT-B/32"], "path": str(clip.relative_to(ROOT))}
    from huggingface_hub import snapshot_download
    gd = Path(snapshot_download(GD_REPO, revision=GD_REV, allow_patterns=list(GD_FILES)))
    for f in sorted(gd.iterdir()):
        rec[f"grounding-dino-tiny/{f.name}"] = {"url": f"https://huggingface.co/{GD_REPO}/resolve/{GD_REV}/{f.name}", "path": str(f.relative_to(ROOT))}
    for v in rec.values():
        p = ROOT / v["path"]
        v["bytes"], v["sha256"] = p.stat().st_size, sha256(p.resolve())
    (ROOT / "research/m1b/zero_shot_weights.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))


def run(name, frames_dir, out_path=None):
    """`out_path`: another output file (T-25p frame-level check); default out/m1b/zs_det_<name>.json (the probe)."""
    import torch
    frames_dir = Path(frames_dir)
    meta = json.load(open(frames_dir / "frames.json"))
    one = MODELS[name]()
    one(np.load(frames_dir / meta[0]["file"]))  # warm-up, not timed
    times, dets = [], []
    for m in meta:
        img = np.load(frames_dir / m["file"])
        t0 = time.perf_counter()
        d = one(img)
        times.append(time.perf_counter() - t0)
        dets.append(d)
        print(m["file"], f"{times[-1]:.3f}s", len(d), flush=True)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    import transformers
    import ultralytics
    out = {"model": name, "frames": [m["file"] for m in meta], "seconds": [round(t, 4) for t in times], "peak_rss_bytes": int(peak),
           "torch": torch.__version__, "torch_threads": torch.get_num_threads(), "ultralytics": ultralytics.__version__,
           "transformers": transformers.__version__, "python": platform.python_version(), "detections": dets}
    p = Path(out_path) if out_path else ROOT / f"out/m1b/zs_det_{name}.json"
    p.write_text(json.dumps(out) + "\n")
    print("wrote", p)


def evaluate(frames_dir):
    frames_dir = Path(frames_dir)
    meta = json.load(open(frames_dir / "frames.json"))
    res = {"status": "zero-shot probe (D-42 option (a)); validation data; descriptive; not a measurement of the instrument; nothing validated",
           "selection": {"seed": 2026111901, "cameras": [], "frames": [{k: m[k] for k in ("file", "rec_id", "camera", "viewpoint", "frame_index")} for m in meta]},
           "references": {}, "matching": {"iou_min": zm.IOU_M, "rule": "same class, one-to-one by descending IoU"}, "models": {}}
    seen = []
    for m in meta:
        if m["rec_id"] not in seen:
            seen.append(m["rec_id"])
            res["selection"]["cameras"].append({k: m[k] for k in ("rec_id", "run", "camera", "viewpoint")})
    views = {"all": meta, "ceiling": [m for m in meta if m["viewpoint"] == "ceiling"], "eye_level": [m for m in meta if m["viewpoint"] == "eye_level"]}
    res["references"] = {v: {c: sum(1 for m in ms for r in m["references"] if r["class"] == c) for c in CLASSES} for v, ms in views.items()}
    platform_info = {"machine": platform.machine(), "macos": platform.mac_ver()[0], "cpu": os.popen("sysctl -n machdep.cpu.brand_string").read().strip(),
                     "logical_cpus": os.cpu_count()}
    res["platform"] = platform_info
    for name in MODELS:
        p = ROOT / f"out/m1b/zs_det_{name}.json"
        if not p.exists():
            continue
        d = json.load(open(p))
        assert d["frames"] == [m["file"] for m in meta]
        by_file = dict(zip(d["frames"], d["detections"]))
        t = np.array(d["seconds"])
        entry = {"versions": {k: d[k] for k in ("torch", "torch_threads", "ultralytics", "transformers", "python")},
                 "seconds_per_frame": {"median": round(float(np.median(t)), 3), "p90": round(float(np.percentile(t, 90)), 3),
                                       "min": round(float(t.min()), 3), "max": round(float(t.max()), 3), "frames_timed": len(t)},
                 "peak_rss_mb": round(d["peak_rss_bytes"] / 1e6, 1),
                 "detections_score_ge_0_05": sum(len(x) for x in d["detections"]), "results": {}}
        for v, ms in views.items():
            fr = [{"references": m["references"], "detections": by_file[m["file"]]} for m in ms]
            entry["results"][v] = {}
            for c in CLASSES:
                rows = {th: zm.counts(fr, c, th) for th in zm.THRESHOLDS}
                best = zm.best_f1(rows)
                entry["results"][v][c] = {"by_threshold": {f"{th:.2f}": r for th, r in rows.items()},
                                          "best_f1_threshold": None if best is None else f"{best:.2f}"}
        res["models"][name] = entry
    p = ROOT / "research/m1b/zero_shot_probe.json"
    p.write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "evaluate":
        evaluate(sys.argv[2])
