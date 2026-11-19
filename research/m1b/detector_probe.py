"""M1b feasibility probe (G-M1a ruling D-40 item 9, 17 Nov 2026). Runs in `.venv-det` (Python 3.9, CPU only), not in
the project `.venv`. Not part of the pipeline; no result here is a measurement of the instrument.

  .venv-det/bin/python research/m1b/detector_probe.py <frames_dir>   -> research/m1b/detector_probe.json

Frames: 10 decoded SDG validation frames (5 ceiling, 5 eye-level camera; RGB uint8 .npy + frames.json), outside git.
Timing: batch 1, one warm-up frame (not timed), then the 10 frames in order; wall-clock per frame includes
pre-processing and post-processing; torch threads = torch default; ORT CPUExecutionProvider, default session options.
Also recorded (descriptive, T-22 input): COCO classes output at score >= 0.5 on these frames (no assumption that
forklifts give nothing).
Weights cache: out/m1b/weights (git-ignored).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "out/m1b/weights"
os.environ.setdefault("TORCH_HOME", str(CACHE / "torch"))

import onnxruntime as ort  # noqa: E402
import torch  # noqa: E402
import torchvision  # noqa: E402
from torchvision.models import detection as D  # noqa: E402

COCO = D.FasterRCNN_ResNet50_FPN_V2_Weights.COCO_V1.meta["categories"]  # 91-entry torchvision COCO list
COCO80 = [c for c in COCO if c not in ("__background__", "N/A")]  # YOLOX class order (80 classes)
YOLOX = {"yolox_nano": ("https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx", 416),
         "yolox_s": ("https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx", 640)}
TV = {"ssdlite320_mobilenet_v3_large": (D.ssdlite320_mobilenet_v3_large, D.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1),
      "fasterrcnn_mobilenet_v3_large_fpn": (D.fasterrcnn_mobilenet_v3_large_fpn, D.FasterRCNN_MobileNet_V3_Large_FPN_Weights.COCO_V1),
      "fasterrcnn_resnet50_fpn_v2": (D.fasterrcnn_resnet50_fpn_v2, D.FasterRCNN_ResNet50_FPN_V2_Weights.COCO_V1)}
LICENCES = {
    "torchvision (code)": "BSD-3-Clause (torchvision LICENSE)",
    "torchvision COCO weights": "no separate weight licence stated by torchvision; trained on COCO 2017 (annotations CC BY 4.0; images under Flickr terms) — needs Owner check before use beyond research",
    "YOLOX (code and released weights)": "Apache-2.0 (Megvii-BaseDetection/YOLOX LICENSE)",
    "Ultralytics YOLOv5/v8/11 (not benchmarked)": "AGPL-3.0 or commercial Enterprise licence — not used here because of the copyleft terms",
    "RT-DETR (not benchmarked)": "Apache-2.0 (lyuwenyu/RT-DETR; also in Hugging Face transformers)",
    "PyTorch": "BSD-style (torch LICENSE)", "ONNX Runtime": "MIT",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch(name, url) -> Path:
    p = CACHE / f"{name}.onnx"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, p.with_suffix(".part"))
        p.with_suffix(".part").rename(p)
    return p


def labels_summary(per_frame):
    out = {}
    for frame in per_frame:
        for lab in frame:
            out[lab] = out.get(lab, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def run_tv(name, frames):
    ctor, weights = TV[name]
    model = ctor(weights=weights).eval()
    size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / 1e6

    def one(img):
        x = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        with torch.no_grad():
            det = model([x])[0]
        keep = det["scores"] >= 0.5
        return [COCO[i] for i in det["labels"][keep].tolist()]
    one(frames[0][1])
    times, labels = [], []
    for _, img in frames:
        t0 = time.perf_counter()
        labels.append(one(img))
        times.append(time.perf_counter() - t0)
    return {"runtime": f"PyTorch {torch.__version__} CPU", "weights": str(weights), "params_mb_fp32": round(size_mb, 1)}, times, labels


def run_yolox(name, frames):
    url, size = YOLOX[name]
    path = fetch(name, url)
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0].name
    strides = (8, 16, 32)
    grids, exp = [], []
    for s in strides:
        n = size // s
        yv, xv = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        grids.append(np.stack([xv, yv], -1).reshape(-1, 2))
        exp.append(np.full((n * n, 1), s))
    grids, exp = np.concatenate(grids), np.concatenate(exp)

    def one(img):
        h, w = img.shape[:2]
        r = min(size / h, size / w)
        nh, nw = int(h * r), int(w * r)
        # nearest-neighbour letterbox resize in numpy (no OpenCV in this environment); BGR order as the YOLOX demo
        yi = (np.arange(nh) / r).astype(int).clip(0, h - 1)
        xi = (np.arange(nw) / r).astype(int).clip(0, w - 1)
        pad = np.full((size, size, 3), 114, np.uint8)
        pad[:nh, :nw] = img[yi][:, xi][:, :, ::-1]
        x = pad.transpose(2, 0, 1)[None].astype(np.float32)
        out = sess.run(None, {inp: x})[0][0]
        scores = out[:, 4:5] * out[:, 5:]
        cls, sc = scores.argmax(1), scores.max(1)
        keep = sc >= 0.5
        xy = (out[keep, :2] + grids[keep]) * exp[keep]
        wh = np.exp(out[keep, 2:4]) * exp[keep]
        boxes = np.concatenate([xy - wh / 2, xy + wh / 2], 1)
        k = torchvision.ops.batched_nms(torch.from_numpy(boxes).float(), torch.from_numpy(sc[keep]).float(), torch.from_numpy(cls[keep]), 0.45)
        return [COCO80[i] for i in cls[keep][k.numpy()].tolist()]
    one(frames[0][1])
    times, labels = [], []
    for _, img in frames:
        t0 = time.perf_counter()
        labels.append(one(img))
        times.append(time.perf_counter() - t0)
    return {"runtime": f"ONNX Runtime {ort.__version__} CPUExecutionProvider", "weights": url, "weights_sha256": sha256(path),
            "file_mb": round(path.stat().st_size / 1e6, 1), "input": f"{size}x{size} letterbox"}, times, labels


def main(frames_dir):
    meta = json.load(open(Path(frames_dir) / "frames.json"))
    frames = [(m_, np.load(Path(frames_dir) / m_["file"])) for m_ in meta]
    res = {"status": "feasibility probe (D-40 item 9); not a measurement of the instrument",
           "platform": {"machine": platform.machine(), "macos": platform.mac_ver()[0], "cpu": os.popen("sysctl -n machdep.cpu.brand_string").read().strip(),
                        "logical_cpus": os.cpu_count(), "python": platform.python_version(), "torch_threads": torch.get_num_threads()},
           "frames": [{k: v for k, v in m_.items() if k != "file"} for m_, _ in frames],
           "licences": LICENCES, "models": {}}
    for name in list(TV) + list(YOLOX):
        info, times, labels = (run_tv if name in TV else run_yolox)(name, frames)
        t = np.array(times)
        res["models"][name] = {**info, "frames_timed": len(t), "total_s": round(float(t.sum()), 3), "fps": round(len(t) / float(t.sum()), 3),
                               "per_frame_s": {"median": round(float(np.median(t)), 3), "max": round(float(t.max()), 3)},
                               "labels_score_ge_0_5": {"ceiling": labels_summary(labels[:5]), "eye_level": labels_summary(labels[5:])}}
        print(name, res["models"][name]["fps"], "fps", res["models"][name]["labels_score_ge_0_5"], flush=True)
    p = ROOT / "research/m1b/detector_probe.json"
    p.write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    main(sys.argv[1])
