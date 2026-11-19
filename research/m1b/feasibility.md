# M1b feasibility: CPU detector runtime on this Mac (D-40 item 9, 17 Nov 2026)

**Status:** feasibility probe only. Nothing here measures the instrument, and nothing is "validated". The frames come from the SDG validation partition (test partition reserved, D-37). No real footage was used. Raw data: `research/m1b/detector_probe.json`. Script: `research/m1b/detector_probe.py`.

## Answer
**Yes. Both runtimes install and run on this Intel Mac:**
- **PyTorch 2.2.2 CPU** with torchvision 0.17.2;
- **ONNX Runtime 1.19.2** (CPUExecutionProvider).

The constraint is the Python version:
- PyTorch 2.2.2 is the last release with Intel-Mac (x86_64) wheels. ONNX Runtime 1.19.2 is the version pip picks for Python 3.9 on this machine.
- No wheels exist for Python 3.14 or 3.15. The project `.venv` is 3.15, so the runtimes cannot go there.
- They are installed in a separate environment, `.venv-det`, built from the macOS system Python 3.9.6 (`/usr/bin/python3`).
- That environment is git-ignored, its versions are pinned in `research/m1b/requirements_detector.txt`, and it is outside `requirements.lock`.
- No system software was installed.

## Machine
Intel Core i7-5650U (2 cores, 4 threads) at 2.2 GHz, 8 GB RAM, macOS 12.7.6. PyTorch uses 2 threads by default.

## Downloads (each below the 1 GB limit)
- **Python wheels:** torch, torchvision, onnxruntime, numpy 1.26.4 and pillow, with their dependencies. 789 MB on disk once installed (the download size was not recorded separately).
- **Weights:** 310 MB in all, in `out/m1b/weights/` (git-ignored):

| file | size | source |
|---|---|---|
| ssdlite320_mobilenet_v3_large_coco-a79551df.pth | 14 MB | download.pytorch.org (torchvision) |
| fasterrcnn_mobilenet_v3_large_fpn-fb6a3cc7.pth | 78 MB | download.pytorch.org (torchvision) |
| fasterrcnn_resnet50_fpn_v2_coco-dd69338a.pth | 175 MB | download.pytorch.org (torchvision) |
| yolox_nano.onnx | 3.7 MB | github.com/Megvii-BaseDetection/YOLOX release 0.1.1rc0 |
| yolox_s.onnx | 36 MB | same |

## Measured speed (10 SDG validation frames, 1920 × 1080)
- **Frames:** 5 from ceiling camera `ceiling_04` and 5 from eye-level camera `eye_04`, evenly spaced in each recording.
- **Timing method:**
  - batch size 1;
  - one warm-up frame, not timed;
  - wall-clock time includes pre- and post-processing;
  - no other job running.

| model | runtime | input | FPS | median s/frame |
|---|---|---|---|---|
| YOLOX-nano | ONNX Runtime | 416 letterbox | **34.3** | 0.029 |
| SSDlite320 MobileNetV3 | PyTorch | 320 (internal resize) | 7.1 | 0.136 |
| YOLOX-s | ONNX Runtime | 640 letterbox | 3.9 | 0.245 |
| Faster R-CNN MobileNetV3-FPN | PyTorch | internal resize (min side 800) | 1.1 | 0.887 |
| Faster R-CNN ResNet50-FPN v2 | PyTorch | internal resize (min side 800) | 0.12 | 8.33 |

**Scale:**
- SDG validation is 226 cameras × 300 frames = 67,800 frames.
- At 3.9 FPS (YOLOX-s) that is about 4.8 h of serial detector time; at 34 FPS (YOLOX-nano), about 33 min.
- One SmartSpaces camera has 9,000 frames: about 39 min at YOLOX-s.
- These are rough extrapolations from 10 frames.

## COCO labels output at score ≥ 0.5 on these 10 frames (descriptive, T-22 input)
COCO has no forklift class. These are only the labels the models emitted; which object each label belongs to was not checked.

| model | ceiling (5 frames) | eye level (5 frames) |
|---|---|---|
| SSDlite320 | none | person 5, suitcase 2 |
| Faster R-CNN MobileNetV3 | person 5, tv 2, skateboard 1 | person 5 |
| Faster R-CNN ResNet50 v2 | person 5, boat 1, handbag 1 | person 5, chair 2, tv 2, suitcase 1, handbag 1 |
| YOLOX-nano | person 3 | person 5 |
| YOLOX-s | person 4, truck 1 | person 5 |

What COCO models output on forklifts needs the T-22 benchmark: boxes matched to truth, on more frames.

## Candidate model licences
Taken from the projects' licence files as stated. **Not legal advice.** Weight licences need the Owner's check before any use beyond research.

| candidate | code licence | weights |
|---|---|---|
| torchvision detection models | BSD-3-Clause | Trained on COCO 2017. torchvision states no separate weight licence; COCO annotations are CC BY 4.0, images under Flickr terms. |
| YOLOX (Megvii) | Apache-2.0 | Released weights under the repository's Apache-2.0 |
| RT-DETR (not benchmarked) | Apache-2.0 | Repository releases |
| Ultralytics YOLOv5 / v8 / 11 (not benchmarked) | AGPL-3.0 or paid Enterprise licence | Same terms. Not used, because of the copyleft. |
| Runtimes | PyTorch BSD-style; ONNX Runtime MIT | — |

## Not done (STOP)
- No detector output enters the pipeline.
- No benchmark against truth.
- No fine-tuning.
- Nothing runs on the test partition.

T-22 proper (benchmark on a frame subset, with truth matching) waits for the Owner's go-ahead after this stop.
