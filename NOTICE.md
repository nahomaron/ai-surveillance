# NOTICE

This repository's own code and documents are licensed under the GNU Affero General Public License v3.0 (`LICENSE`, unmodified text; Owner decision D-43, 19 Nov 2026).

**Reason for the record (D-43):** the working system uses an AGPL-3.0 detector (Ultralytics YOLO-World, D-42). The Owner may relicense the project's own code later.

## Third-party material referred to but not contained

**No dataset files and no model weights are in this repository.**
- Datasets are kept outside git under `data/` (git-ignored).
- Weights are kept in `out/m1b/weights/` (git-ignored).
- The repository holds only code that reads them, together with derived counts, statistics and identifiers.

Licences are as stated by each source, not legal advice. Dataset licences are as recorded in `research/datasets/qualification.md`.

### Datasets

| material | source | licence | notes |
|---|---|---|---|
| SDG-Warehouse near-miss data (`nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes`, v1.0) | https://huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes (revision `d5b88d3abcf659f304a107f4336b71b4e2159133`) | OpenMDW-1.1 | Synthetic (Isaac Sim). Licence text pinned in `qualification.md` Part 1. |
| PhysicalAI-SmartSpaces `MTMC_Tracking_2026` (`nvidia/PhysicalAI-SmartSpaces`) | https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces (revision `d38193be60906679124732a4be9a6516821e2bed`) | CC BY 4.0 | Attribution with a licence link and an indication of changes when sharing. |
| Video Dataset for Safe and Unsafe Behaviours (Mendeley Data `xjmtb22pff`, v1) | https://doi.org/10.17632/xjmtb22pff.1 | CC BY 4.0 | Real footage, testing only (D-21). **No frames, crops or faces from it are in this repository (D-24 c).** Mendeley notes that content identified as belonging to a third party may need further permission. |

### Detector weights and text encoders used

The SHA-256 values are of the files as downloaded. Machine-readable records:
- T-22 zero-shot probe: `research/m1b/zero_shot_weights.json`;
- M1b feasibility probe: `research/m1b/feasibility.md` and `detector_probe.json`.

| file | used in | source URL | SHA-256 | licence |
|---|---|---|---|---|
| `yolov8s-worldv2.pt` (YOLO-World v2-s) | T-22 zero-shot probe | https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s-worldv2.pt | `9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792` | AGPL-3.0 (Ultralytics; a paid Enterprise licence is offered as an alternative) |
| `ViT-B-32.pt` (OpenAI CLIP ViT-B/32, YOLO-World text encoder) | T-22 zero-shot probe | https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt | `40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af` | MIT. This is the licence of the `openai/CLIP` repository, which distributes the weights. Loaded through the `ultralytics/CLIP` fork (MIT), commit `7ffa84b3bfa40c42ecc1c77147a855e69cb2dd40`. |
| `model.safetensors` and tokenizer/config files (IDEA-Research/grounding-dino-tiny) | T-22 zero-shot probe | https://huggingface.co/IDEA-Research/grounding-dino-tiny (revision `a2bb814dd30d776dcf7e30523b00659f4f141c71`) | `1a2412ef99bd74bcd3c2a246fa1e48581f8889a1300c9051974741314fc042f3` (model.safetensors; other files in `zero_shot_weights.json`) | Apache-2.0 (model card) |
| `ssdlite320_mobilenet_v3_large_coco-a79551df.pth` | M1b feasibility probe | https://download.pytorch.org/models/ssdlite320_mobilenet_v3_large_coco-a79551df.pth | `a79551df90c79834bcd3bb3845ef9d966b5449a3a9b2833ae8404778ca5d65d2` | torchvision code BSD-3-Clause. No separate weight licence is stated. Trained on COCO 2017 (annotations CC BY 4.0; images under Flickr terms). |
| `fasterrcnn_mobilenet_v3_large_fpn-fb6a3cc7.pth` | M1b feasibility probe | https://download.pytorch.org/models/fasterrcnn_mobilenet_v3_large_fpn-fb6a3cc7.pth | `fb6a3cc702b1df54c18a44b26708cd083614211062d0c36d2ca7bf9270df3533` | same as above |
| `fasterrcnn_resnet50_fpn_v2_coco-dd69338a.pth` | M1b feasibility probe | https://download.pytorch.org/models/fasterrcnn_resnet50_fpn_v2_coco-dd69338a.pth | `dd69338a24b8d7381807e247652bdc356325bcbaf1cd3e092e00e0a1a58706bf` | same as above |
| `yolox_nano.onnx` | M1b feasibility probe | https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx | `c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d` | Apache-2.0 (YOLOX repository) |
| `yolox_s.onnx` | M1b feasibility probe | https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx | `c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063` | Apache-2.0 (YOLOX repository) |

### Software used by the detector environment (installed, not contained)

These are installed into `.venv-det`, pinned in `research/m1b/requirements_detector.txt`:
- PyTorch and torchvision: BSD-style;
- ONNX Runtime: MIT;
- Ultralytics 8.4.215: AGPL-3.0;
- transformers 4.57.6: Apache-2.0.

The project environment is pinned in `requirements.lock`.
