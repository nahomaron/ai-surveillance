# T-22 zero-shot detector probe (D-42 option (a), 19 Nov 2026)

**Status:** probe only, on SDG **validation** data (synthetic; test partition reserved, D-37). The results are descriptive and are not a measurement of the instrument. Nothing here is "validated", and no detector output entered S4, S5 or S8.

Files:
- raw numbers: `research/m1b/zero_shot_probe.json`;
- weights record: `zero_shot_weights.json`;
- scripts: `zero_shot_frames.py` (selection and reference boxes, main `.venv`), `zero_shot_probe.py` (detectors and evaluation, `.venv-det`), `zs_match.py` (matcher).

## Plain-language summary

We asked two "open-vocabulary" detectors, which find objects named by a text prompt, to find **people** and **forklifts** in 100 synthetic warehouse frames. We then compared their boxes with the simulator's own boxes (190 visible objects in all).

- **Grounding DINO tiny** found most of both:
  - people: 95 % found, with almost no false boxes, at its best threshold;
  - forklifts: 89 % found, 96 % of its boxes correct (threshold 0.45).
  - It is slow on this laptop: about **17 s per frame**.
- **YOLO-World v2-s** is about **47 times faster** (0.35 s per frame). It finds people well (90 % found, 98 % correct), but it misses many forklifts:
  - it found 63 % at its lowest threshold, and fewer at any higher one;
  - its forklift scores are low: it finds 38 % at threshold 0.10 and 12 % at 0.25;
  - its best forklift threshold is the lowest tested (0.05), so a lower threshold might find more. That was not tried.
- Both models do worse on **eye-level** cameras than on ceiling cameras for forklifts. On eye level, YOLO-World found 51 % and Grounding DINO 83 %.

**Limits:**
- These are 100 synthetic validation frames from one dataset and one prompt pair.
- The best thresholds were chosen on the same frames they are reported on.
- These numbers say nothing yet about how well the instrument measures exposure. That needs the detector-path pilot, which has not been run.

## What was fixed before any detector was run (Owner instruction)

- **Frames:** 100 SDG validation frames, 5 from each of 20 validation cameras: 10 ceiling and 10 eye-level, chosen by a seeded draw (seed 2026111901). The 5 frames are evenly spaced in each recording. No SmartSpaces, no test partition, no real footage.
- **Prompts:** exactly the two class texts "person" and "forklift", for both models. No other prompt was tried.
- **Reference:** the simulator boxes of the oracle path, using the T17 box convention clipped to the image, for visible objects only.
- **Matching:** same class, IoU ≥ 0.3 (iou_m of the frozen pre-registration), one-to-one by descending IoU.
- **Report:** recall and precision per model and class at score thresholds 0.05, 0.10, …, 0.50, and the threshold with the highest F1. Per viewpoint class as well. Seconds per frame (median, P90) and peak memory.

## Choices the instruction did not fix (made by the agent, for Architect review)

None of these changes a contract definition. They are listed because each can move the numbers a little.

1. **Draw procedure.**
   - Pool: SDG validation cameras of the frozen split that have an ORACLE-S3 (226: 109 ceiling, 117 eye-level). Viewpoint is taken from the camera name (`ceiling_*` or `eye_*`).
   - Draw: one numpy PCG64 generator, ceiling drawn first, each pool sorted by rec_id, `choice(n, 10, replace=False)`. This is the same draw style as the split draw.
2. **Frame spacing.** Positions ⌊(2j + 1)·n / 10⌋, j = 0..4, in the eligible frames. With n = 300 these are frame_index 30, 90, 150, 210 and 270.
3. **Reference boxes.**
   - The T17.1 `tracked` points at g_max = 15 (pre-registration v1): dataset-visible and eligible, after T17.5.
   - Each box is in CF-IMG and clipped to [0, W] × [0, H].
   - Only the classes person and forklift occur on these frames.
4. **YOLO-World settings.**
   - Ultralytics defaults: input 640, NMS IoU 0.7, max 300 boxes.
   - Confidence floor 0.05, the lowest probe threshold.
   - Text embeddings for the two prompts are computed once, before timing.
5. **Grounding DINO settings.**
   - Text "person. forklift.": the two class texts in the model's phrase format.
   - Processor defaults: shortest side 800, longest side 1333.
   - Each of the 900 queries gets one class: the phrase whose tokens have the higher maximum sigmoid score. Its score is that maximum, and it is kept when ≥ 0.05.
   - No NMS. The model's standard output has none, so duplicate boxes lower precision.
6. **Ties.**
   - Matching: equal IoUs are broken by higher detection score, then by input order.
   - Best-F1: equal F1s go to the lower threshold.
7. **Timing** (as in `feasibility.md`):
   - batch 1;
   - frame 000 run once as warm-up, not timed;
   - wall-clock from the decoded RGB array in memory to the final box list, pre- and post-processing included, disk read excluded;
   - torch default threads;
   - no other job running.

   Peak memory is the process's peak resident set size, with one model per process.

## Results (validation data, descriptive)

References (visible objects on the 100 frames): person 93 (ceiling 50, eye level 43); forklift 97 (ceiling 50, eye level 47). These counts are small, so each rate below moves by about 0.01–0.02 per object.

### Best-F1 threshold per model, class and viewpoint

| model | class | viewpoint | best threshold | recall | precision | F1 | TP / refs / dets |
|---|---|---|---|---|---|---|---|
| YOLO-World v2-s | person | all | 0.20 | 0.90 | 0.98 | 0.94 | 84 / 93 / 86 |
| YOLO-World v2-s | person | ceiling | 0.20 | 0.92 | 1.00 | 0.96 | 46 / 50 / 46 |
| YOLO-World v2-s | person | eye_level | 0.30 | 0.88 | 0.97 | 0.93 | 38 / 43 / 39 |
| YOLO-World v2-s | forklift | all | 0.05 | 0.63 | 0.92 | 0.75 | 61 / 97 / 66 |
| YOLO-World v2-s | forklift | ceiling | 0.05 | 0.74 | 1.00 | 0.85 | 37 / 50 / 37 |
| YOLO-World v2-s | forklift | eye_level | 0.05 | 0.51 | 0.83 | 0.63 | 24 / 47 / 29 |
| Grounding DINO tiny | person | all | 0.45 | 0.95 | 1.00 | 0.97 | 88 / 93 / 88 |
| Grounding DINO tiny | person | ceiling | 0.20 | 0.94 | 0.98 | 0.96 | 47 / 50 / 48 |
| Grounding DINO tiny | person | eye_level | 0.30 | 0.98 | 1.00 | 0.99 | 42 / 43 / 42 |
| Grounding DINO tiny | forklift | all | 0.45 | 0.89 | 0.96 | 0.92 | 86 / 97 / 90 |
| Grounding DINO tiny | forklift | ceiling | 0.45 | 0.94 | 1.00 | 0.97 | 47 / 50 / 47 |
| Grounding DINO tiny | forklift | eye_level | 0.45 | 0.83 | 0.91 | 0.87 | 39 / 47 / 43 |

### Speed and memory (Intel Core i7-5650U, 2 cores, CPU only)

| model | median s/frame | P90 s/frame | min–max | peak memory (RSS) | boxes at score ≥ 0.05 (100 frames) |
|---|---|---|---|---|---|
| YOLO-World v2-s | 0.352 | 0.374 | 0.303–0.466 | 1772 MB | 177 |
| Grounding DINO tiny | 16.546 | 19.726 | 15.157–24.151 | 2320 MB | 1001 |

### Recall / precision at every threshold (all frames; per viewpoint in the JSON)

**YOLO-World v2-s**

| threshold | person recall | person precision | forklift recall | forklift precision |
|---|---|---|---|---|
| 0.05 | 0.95 | 0.79 | 0.63 | 0.92 |
| 0.10 | 0.94 | 0.90 | 0.38 | 1.00 |
| 0.15 | 0.91 | 0.93 | 0.25 | 1.00 |
| 0.20 | 0.90 | 0.98 | 0.16 | 1.00 |
| 0.25 | 0.90 | 0.98 | 0.12 | 1.00 |
| 0.30 | 0.89 | 0.99 | 0.11 | 1.00 |
| 0.35 | 0.89 | 0.99 | 0.09 | 1.00 |
| 0.40 | 0.89 | 0.99 | 0.05 | 1.00 |
| 0.45 | 0.89 | 0.99 | 0.03 | 1.00 |
| 0.50 | 0.89 | 0.99 | 0.03 | 1.00 |

**Grounding DINO tiny**

| threshold | person recall | person precision | forklift recall | forklift precision |
|---|---|---|---|---|
| 0.05 | 0.98 | 0.27 | 1.00 | 0.15 |
| 0.10 | 0.96 | 0.64 | 1.00 | 0.31 |
| 0.15 | 0.96 | 0.84 | 1.00 | 0.42 |
| 0.20 | 0.96 | 0.96 | 1.00 | 0.52 |
| 0.25 | 0.96 | 0.96 | 1.00 | 0.58 |
| 0.30 | 0.95 | 0.99 | 1.00 | 0.66 |
| 0.35 | 0.95 | 0.99 | 0.97 | 0.71 |
| 0.40 | 0.95 | 0.99 | 0.95 | 0.86 |
| 0.45 | 0.95 | 1.00 | 0.89 | 0.96 |
| 0.50 | 0.94 | 1.00 | 0.81 | 0.98 |

## Environment and downloads

**Environment.**
- `.venv-det` (Python 3.9.6, PyTorch 2.2.2 CPU, torch threads 2), pinned in `requirements_detector.txt`.
- New installs:
  - Ultralytics 8.4.215 and transformers 4.57.6, the newest versions that support Python 3.9 and torch 2.2.2, with their dependencies;
  - the Ultralytics CLIP fork at commit `7ffa84b3` (Owner answer);
  - `opencv-python` pinned to 4.10.0.84, because 4.11 has no wheel for macOS 12 x86_64.
- No existing package changed version. The project `.venv` is unchanged.

**Downloads** (each below 1 GB), in git-ignored `out/m1b/weights/`. SHA-256 values are in `zero_shot_weights.json` and `NOTICE.md`.

| file | bytes | licence |
|---|---|---|
| yolov8s-worldv2.pt | 25,923,032 | AGPL-3.0 (Ultralytics) |
| CLIP ViT-B-32.pt (text encoder) | 353,976,522 | MIT (openai/CLIP) |
| grounding-dino-tiny model.safetensors + 7 small files | 689,359,096 + 946,449 | Apache-2.0 |
| **total weights** | **1,070,205,099** | |

**Budget** (Owner answer, 19 Nov 2026: weights count, cap raised to 31.5 GB):
- datasets: 29,242,415,000 bytes;
- feasibility weights: 306,653,228 bytes;
- these weights: 1,070,205,099 bytes;
- **total 30,619,273,327 bytes (30.62 GB) of 31.5 GB.**

The Python packages installed for this task (0.43 GB on disk; download size not recorded) are not counted in that total.

**Data sent off this computer:** none. The only network traffic was the download requests.
- Ultralytics usage reporting (`sync`) was switched off before the first prediction.
- Hugging Face telemetry was switched off.
- Ultralytics automatic package installation was switched off.

## Rulings (D-45, Owner, 19 Nov 2026)

- The seven choices above are ACCEPTED as recorded. The probe is not re-run.
- The probe thresholds are the fixed values of the detector-path pilot (T-25p), with no further tuning:
  - YOLO-World v2-s: person 0.20, forklift 0.05;
  - Grounding DINO tiny: 0.45 for both.
- These thresholds were chosen on the 20 probe cameras above, so those cameras are excluded from everything in the pilot.
- Grounding DINO is not run at scale (about 13 days on this laptop). It is used only in the pilot's 100-frame check on other cameras.

## Not done (STOP, D-45)

- Detector output did not enter S4, S5 or S8. The detector-path pilot spec comes from the Architect first.
- No fine-tuning.
- No Ultralytics tracker.
- No other prompt was tried.
- No change to the frozen pre-registration or to any analysis module.
- Nothing ran on the test partition, SmartSpaces or real footage.
