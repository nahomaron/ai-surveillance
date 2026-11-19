# M1b detector-path pilot report — validation partition (T-25p)

**Status: complete for D-47 review.** All 206 pilot cameras ran through S2 → S5 and were evaluated; the frame-level check ran on both models.

Every number in this report is **experimental**: synthetic data (SDG), validation partition only (D-36, D-37), one zero-shot detector at fixed thresholds, one tracker at default parameters. Nothing here is "validated", and nothing here is a claim about real footage (D-45 item 4). Automated outputs are **candidate** events and **scenario counts**. No test-partition recording was processed. No acceptance criterion is registered or evaluated (D-45 item 4).

Contract E-1.2.21. Pre-registration version 1 (`docs/preregistration_FROZEN.md`), unchanged. Specification: D-45 (Owner decision with the Architect's detector-path pilot spec, 19 Nov 2026).
Run code: S2 detection commits `ac40508` (first 71 cameras) and `533d2ff` (the rest; the only change between them is the report table script, which no run imports); pipeline (S2 artifact → S5) commit `533d2ff` on all 206 cameras; evaluation and frame-level check code at the same commit. Results: `research/m1b/pilot_results.json`, `research/m1b/pilot_frame_check.json`.

## Plain-language summary (one page)

**What was run.** The pilot asks what changes when the simulator's knowledge of where each object is in the image ("oracle perception", used in M1a) is replaced by an off-the-shelf detector and tracker. It uses 206 of the 226 SDG validation camera recordings (24 simulated scenes, 10 s each, one worker and one forklift per scene). The 20 cameras used to choose the detector thresholds in the T-22 probe are left out, so the pilot does not reuse the frames those thresholds were chosen on.

- **Detector:** YOLO-World v2-s, used zero-shot with the prompts "person" and "forklift". It was not trained on this data. Thresholds are the probe's: person 0.20, forklift 0.05.
- **Tracker:** ByteTrack (Ultralytics' built-in version) with its default parameters, one tracker per class.
- **The rest of the pipeline is the M1a pipeline, unchanged:** floor positions from the dataset calibration and the bottom-centre of each box (`full_camera`), then the five rule configurations BL-2 to BL-6 at the frozen base values.

**What it is compared with.** The yardstick is the same as in M1a: BL-6 applied to the simulator's complete ground truth (Appendix T, T21), stored once per camera and not rebuilt. Three columns are reported on the same 206 cameras:
- **A, oracle path with simulator positions:** the M1a `base` result on these cameras.
- **B, oracle boxes with camera geometry:** the M1a `full_camera` result on these cameras.
- **C, detector path:** detector and tracker boxes with camera geometry (this pilot).

B to C isolates the effect of replacing oracle boxes by detector and tracker boxes. A to B is the effect of camera geometry, already reported in M1a.

**Main findings (SDG, validation, descriptive).**
1. **On the detector path, few reference interactions are found.**
   - Column C, BL-3 to BL-6: recall 0.11 (31 of 282 reference interactions), precision 0.22. BL-2: recall 0.03, precision 0.10.
   - With oracle boxes and the same camera geometry (column B): recall 0.74–0.75, precision 0.55–0.57. With simulator positions (column A): recall 0.97–1.00, precision 0.94–0.95, as in M1a.
2. **The loss comes mainly from forklift tracking, not from person detection.**
   - Persons: the detector finds 92 % of visible persons per frame (precision 0.98); tracks cover 91 % of person-visible frames (CM-01); IDF1 0.83.
   - Forklifts: the detector finds 61 % of visible forklifts per frame (precision 0.99), but tracks exist on only 16 % of forklift-visible frames (9,618 tracked points against 59,577 reference forklift boxes); forklift IDF1 0.24; 93 forklift identities are never matched by any track.
   - An interaction needs both objects tracked, so only 12 % of the frames in which a worker and a forklift are both visible are covered by a matched system pair (CM-03 0.12, against 1.00 on the oracle path).
3. **Most forklift detections fall below the tracker's default thresholds.** 81 % of the kept forklift detections score below 0.25, the score ByteTrack needs to start a track, and 34 % score 0.10 or less, which ByteTrack does not use at all. For persons, 99 % score at least 0.25. The D-45 forklift threshold (0.05) and the ByteTrack defaults were both applied as fixed; neither was tuned (D-45 items 0, 1 and 4). The pilot therefore cannot say how much of the loss is the detector and how much is this threshold mismatch.
4. **Forklifts seen at eye level are the weakest case,** as in the probe: per-frame recall 0.43 at eye level, 0.78 from the ceiling.
5. **Where the detector path does give a position, it is no worse than with oracle boxes.**
   - Persons: median error 0.23 m, P95 0.53 m, 0.5 % above 5 m (column B: 0.19 m, 0.75 m, 1.1 %).
   - Forklifts: median 0.81 m, P95 1.45 m (column B: 1.07 m, 1.48 m). These are the forklifts the tracker kept, mostly high-scoring ones, so the two columns are not the same objects.
   - Bridged person points (predicted by the tracker over a gap) are less accurate: P95 2.02 m.
6. **No identity switches** were found for either class. Fragmentation is common: 229 of 379 person tracks and 105 of 171 forklift tracks are fragments of an identity.
7. **The frame-level check on 20 cameras outside the probe repeats the probe's picture.** YOLO-World: person recall 0.94, forklift 0.59. Grounding DINO tiny: person 0.96, forklift 0.94 (eye level 0.93), at about 15 s per frame against 0.34 s for YOLO-World.
8. **Runtime:** detection took 6.4 h of wall time for 61,749 frames (estimate 6.7 h); everything after detection took 0.6 h.

**One finding already visible before evaluation.** ByteTrack's default thresholds start tracks only from detections scoring at least 0.25, and its second matching stage uses detections above 0.10. The forklift threshold fixed by D-45 is 0.05. Forklift detections between 0.05 and 0.10 can therefore never join a track, and those between 0.10 and 0.25 can only extend an existing one. On the first pilot camera, 238 forklift detections gave 99 tracked forklift points. The thresholds were not tuned (D-45 item 4). The full pilot confirms it (finding 3; table "Bridging and detections by ByteTrack score band").

## Technical report

### Scope and method
- **Population (D-45 item 3a):** the SDG validation cameras with an ORACLE-S3, minus the 20 probe cameras (`research/m1b/zero_shot_probe.json`, selection): **206 cameras**, 99 `sdg:ceiling` and 107 `sdg:eye_level`, one 10 s window each, 61,749 eligible frames. Leakage groups: 24. References (T21): 284, of which 282 assessable. Test: `tests/m1b/test_pilot_population.py`.
- **S1:** the stored `rv2` artifact of each camera, reused from T-21.
- **S2 (D-45 item 2; T-23s):** YOLO-World v2-s (`yolov8s-worldv2.pt`, SHA-256 in `research/m1b/zero_shot_weights.json`; AGPL-3.0, D-43), `set_classes(["person", "forklift"])`, Ultralytics defaults (imgsz 640, NMS IoU 0.7, max_det 300), CPU, on every eligible frame. Raw boxes at score ≥ 0.05 are stored per camera; the class thresholds person 0.20 and forklift 0.05 are applied when the `detection` artifact is built. Reproducibility class: tolerance. The weights are recorded as a `license_component` row (AR-62 item 2).
- **S3 (D-45 item 1; T-23):** Ultralytics ByteTrack (8.4.215), installed `bytetrack.yaml` defaults: track_high_thresh 0.25, track_low_thresh 0.10, new_track_thresh 0.25, match_thresh 0.8, track_buffer 30, fuse_score on. One tracker per class; one update per eligible frame. A matched frame gives a `tracked` / `detected` point carrying the detection box; a gap of at most g_max = 15 eligible frames is bridged with the tracker's predicted box (`predicted` / `inferred`); longer gaps are `lost`. No point on ineligible frames. Foot point = bottom-centre of the box. The Apache-2.0 `trackers` package could not be installed without breaking `.venv-det`, so the D-45 fallback applies; assignment uses Ultralytics' NumPy solver because `lap` is not installed (AR-62 item 5).
- **S4:** `full_camera` geometry from the S3 boxes and the dataset calibration, pre-registration v1 base values. No yaw is supplied, so the T8.2 heading and footprint fallbacks apply as the builder implements them. No `forklift_turning` stratum (D-45 item 3).
- **S5:** BL-2 to BL-6 at the frozen base values.
- **S8 (evaluation):** against the stored T21 references of each camera (`rule_conformance`, label group G1, T21.3 assessability), unchanged from T-21.
  - Association: F.1 A5.2, iou_cm 0.5, eps_amb 0.02. System boxes are the column's S3 points (not lost); reference boxes are the reference-visible boxes (T17.6). Columns A and B share the oracle association; column C associates the detector tracks.
  - Event matching, EV counts and completeness use the T-21 functions unchanged.
  - Intervals: Target B (`new_session_performance`), cluster bootstrap over leakage groups, B 2000, 95 %. Seed 2026111402, as in T-21 (pre-registration v1 section 4.4). Shown without a decision.
- **Detection (frame level):** every eligible pilot frame. References are the reference-visible boxes clipped to the image (the probe's reference); detections are the S2 rows after thresholds; the probe matcher (same class, IoU ≥ 0.3, one-to-one by descending IoU). Column C only.
- **Tracking:** T-12 association statuses and identity switches; IDF1 per class against simulator identities (`research/m1b/idf1.py`, a port of TrackEval's Identity metric; AR-62 item 6). Column C only.
- **Position (D-41):** median, P95 and the shares above 1, 2 and 5 m of the error to the simulator position, for columns B and C, by class and evidence class. Availability is reported separately: the share of object-frames with a position, and the counts by null reason. In column C an error is scored only where the track is matched to an identity on that frame (A5.2 `matched`).
- **Frame-level check (D-45 item 3c):** 100 frames, 5 evenly spaced eligible frames from each of 20 pilot cameras (10 ceiling, 10 eye-level), seed 2026111902, by the probe's selection procedure (`research/m1b/frame_check.py`). Both models at the fixed D-45 thresholds: YOLO-World person 0.20 and forklift 0.05; Grounding DINO tiny 0.45 for both. No threshold is chosen here.

### Results (generated by `research/m1b/pilot_report_tables.py` from `pilot_results.json` and `pilot_frame_check.json`)

Cameras: 206 (99 ceiling, 107 eye-level); leakage groups: 24; references: 284 (282 assessable, 284 in G1).

#### EV-M1 (recall) and EV-M2 (precision), label group G1, with Target B intervals

| configuration | column | EV-M1 | Target B | matched / assessable | EV-M2 | Target B | matched / system | episodes | candidate events |
|---|---|---|---|---|---|---|---|---|---|
| BL-2 | A | 0.54 | [0.46, 0.64] | 153 / 282 | 0.48 | [0.42, 0.55] | 153 / 317 | 317 | 317 |
| BL-2 | B | 0.54 | [0.46, 0.64] | 153 / 282 | 0.48 | [0.42, 0.55] | 153 / 317 | 317 | 317 |
| BL-2 | C | 0.03 | [0.00, 0.06] | 9 / 282 | 0.10 | [0.02, 0.18] | 9 / 92 | 92 | 92 |
| BL-3 | A | 0.97 | [0.92, 1.00] | 274 / 282 | 0.94 | [0.89, 0.97] | 274 / 293 | 293 | 293 |
| BL-3 | B | 0.74 | [0.65, 0.84] | 208 / 282 | 0.57 | [0.50, 0.63] | 208 / 368 | 368 | 368 |
| BL-3 | C | 0.11 | [0.06, 0.16] | 30 / 282 | 0.22 | [0.12, 0.34] | 30 / 137 | 137 | 137 |
| BL-4 | A | 1.00 | [0.99, 1.00] | 281 / 282 | 0.95 | [0.92, 0.97] | 281 / 296 | 296 | 296 |
| BL-4 | B | 0.75 | [0.66, 0.84] | 211 / 282 | 0.55 | [0.49, 0.62] | 211 / 383 | 383 | 383 |
| BL-4 | C | 0.11 | [0.06, 0.16] | 31 / 282 | 0.22 | [0.12, 0.34] | 31 / 141 | 141 | 141 |
| BL-5 | A | 0.97 | [0.92, 1.00] | 274 / 282 | 0.94 | [0.89, 0.97] | 274 / 293 | 293 | 293 |
| BL-5 | B | 0.74 | [0.65, 0.84] | 209 / 282 | 0.55 | [0.49, 0.62] | 209 / 377 | 377 | 377 |
| BL-5 | C | 0.11 | [0.06, 0.16] | 30 / 282 | 0.22 | [0.12, 0.33] | 30 / 139 | 139 | 139 |
| BL-6 | A | 1.00 | [0.99, 1.00] | 281 / 282 | 0.95 | [0.92, 0.97] | 281 / 296 | 296 | 296 |
| BL-6 | B | 0.74 | [0.66, 0.84] | 210 / 282 | 0.55 | [0.48, 0.62] | 210 / 382 | 382 | 382 |
| BL-6 | C | 0.11 | [0.06, 0.16] | 31 / 282 | 0.22 | [0.12, 0.33] | 31 / 142 | 142 | 142 |

#### Per-label recall and precision (O, H, PC; descriptive, D-40 item 5)

| configuration | column | O recall | O precision | H recall | H precision | PC recall | PC precision |
|---|---|---|---|---|---|---|---|
| BL-2 | A | 0.22 | 0.01 | 0.00 | — | 0.00 | — |
| BL-2 | B | 0.22 | 0.01 | 0.00 | — | 0.00 | — |
| BL-2 | C | 0.00 | 0.00 | 0.00 | — | 0.00 | — |
| BL-3 | A | 1.00 | 1.00 | 0.97 | 0.93 | 0.00 | — |
| BL-3 | B | 0.00 | 0.00 | 0.75 | 0.58 | 0.00 | — |
| BL-3 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.00 | — |
| BL-4 | A | 1.00 | 1.00 | 1.00 | 0.95 | 1.00 | 0.95 |
| BL-4 | B | 0.00 | 0.00 | 0.75 | 0.58 | 0.81 | 0.64 |
| BL-4 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.10 | 0.24 |
| BL-5 | A | 1.00 | 1.00 | 0.97 | 0.93 | 0.93 | 0.95 |
| BL-5 | B | 0.00 | 0.00 | 0.75 | 0.58 | 0.77 | 0.71 |
| BL-5 | C | 0.00 | 0.00 | 0.11 | 0.23 | 0.09 | 0.33 |
| BL-6 | A | 1.00 | 1.00 | 1.00 | 0.95 | 1.00 | 0.95 |
| BL-6 | B | 0.00 | 0.00 | 0.75 | 0.58 | 0.81 | 0.63 |
| BL-6 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.10 | 0.24 |

#### Detection, frame level, all pilot frames (column C; probe matcher, IoU ≥ 0.3)

| viewpoint | class | recall | precision | TP / references / detections |
|---|---|---|---|---|
| all | person | 0.92 | 0.98 | 51122 / 55651 / 52018 |
| all | forklift | 0.61 | 0.99 | 36073 / 59577 / 36474 |
| ceiling | person | 0.92 | 0.99 | 27018 / 29357 / 27287 |
| ceiling | forklift | 0.78 | 1.00 | 23169 / 29536 / 23259 |
| eye_level | person | 0.92 | 0.97 | 24104 / 26294 / 24731 |
| eye_level | forklift | 0.43 | 0.98 | 12904 / 30041 / 13215 |

#### Frame-level check, 100 frames on 20 pilot cameras (item 3c), fixed thresholds

| model | viewpoint | class | recall | precision | TP / references / detections |
|---|---|---|---|---|---|
| YOLO-World v2-s | all | person | 0.94 | 0.99 | 84 / 89 / 85 |
| YOLO-World v2-s | all | forklift | 0.59 | 0.98 | 56 / 95 / 57 |
| YOLO-World v2-s | ceiling | person | 0.94 | 0.98 | 47 / 50 / 48 |
| YOLO-World v2-s | ceiling | forklift | 0.70 | 1.00 | 35 / 50 / 35 |
| YOLO-World v2-s | eye_level | person | 0.95 | 1.00 | 37 / 39 / 37 |
| YOLO-World v2-s | eye_level | forklift | 0.47 | 0.95 | 21 / 45 / 22 |
| Grounding DINO tiny | all | person | 0.96 | 0.99 | 85 / 89 / 86 |
| Grounding DINO tiny | all | forklift | 0.94 | 0.97 | 89 / 95 / 92 |
| Grounding DINO tiny | ceiling | person | 0.96 | 0.98 | 48 / 50 / 49 |
| Grounding DINO tiny | ceiling | forklift | 0.94 | 1.00 | 47 / 50 / 47 |
| Grounding DINO tiny | eye_level | person | 0.95 | 1.00 | 37 / 39 / 37 |
| Grounding DINO tiny | eye_level | forklift | 0.93 | 0.93 | 42 / 45 / 45 |

#### Tracking (column C; T-12 association at iou_cm 0.5; IDF1 per class)

| class | tracks | one_to_one | id_switch | fragment | unmatched_system | identity switches | identities never matched | IDF1 | IDTP / IDFP / IDFN |
|---|---|---|---|---|---|---|---|---|---|
| person | 379 | 114 | 0 | 229 | 36 | 0 | 0 | 0.833 | 44584 / 6852 / 11067 |
| forklift | 171 | 66 | 0 | 105 | 0 | 0 | 93 | 0.244 | 8530 / 1670 / 51047 |

Bridging (D-45 item 1) and detections by ByteTrack score band:

| class | tracked points | predicted points (bridged) | runs bridged | runs lost (> 15) | frames lost in long runs | detections ≥ 0.25 | in (0.10, 0.25) | ≤ 0.10 |
|---|---|---|---|---|---|---|---|---|
| person | 51092 | 344 | 129 | 8 | 151 | 51589 | 429 | 0 |
| forklift | 9618 | 582 | 91 | 31 | 708 | 6895 | 17153 | 12426 |

#### Position accuracy (D-41), columns B and C

| column | class | evidence class | n | median (m) | P95 (m) | > 1 m | > 2 m | > 5 m |
|---|---|---|---|---|---|---|---|---|
| B | all | all | 114996 | 0.55 | 1.47 | 30.3 % | 1.1 % | 0.6 % |
| B | forklift | all | 59622 | 1.07 | 1.48 | 54.7 % | 0.1 % | 0.0 % |
| B | forklift | detected | 59577 | 1.07 | 1.48 | 54.7 % | 0.1 % | 0.0 % |
| B | forklift | inferred | 45 | 1.47 | 1.72 | 75.6 % | 0.0 % | 0.0 % |
| B | person | all | 55374 | 0.19 | 0.75 | 4.1 % | 2.2 % | 1.1 % |
| B | person | detected | 55054 | 0.19 | 0.75 | 4.1 % | 2.3 % | 1.2 % |
| B | person | inferred | 320 | 0.50 | 0.77 | 0.3 % | 0.0 % | 0.0 % |
| C | all | all | 60701 | 0.27 | 1.22 | 7.8 % | 0.9 % | 0.4 % |
| C | forklift | all | 10179 | 0.81 | 1.45 | 36.9 % | 0.0 % | 0.0 % |
| C | forklift | detected | 9609 | 0.82 | 1.44 | 36.9 % | 0.0 % | 0.0 % |
| C | forklift | inferred | 570 | 0.79 | 1.48 | 37.2 % | 0.0 % | 0.0 % |
| C | person | all | 50522 | 0.23 | 0.53 | 2.0 % | 1.1 % | 0.5 % |
| C | person | detected | 50311 | 0.23 | 0.52 | 1.9 % | 1.1 % | 0.5 % |
| C | person | inferred | 211 | 0.35 | 2.02 | 19.4 % | 5.2 % | 1.4 % |

Position availability (object-frames of the S4 run; share by null reason):

| column | class | object-frames | with a position | by null reason | position but no matched identity (not scored) |
|---|---|---|---|---|---|
| B | person | 55971 | 55374 (98.9 %) | not_observable 597 (1.1 %) | 0 |
| B | forklift | 59622 | 59622 (100.0 %) | none | 0 |
| C | person | 51436 | 51142 (99.4 %) | not_observable 294 (0.6 %) | 620 |
| C | forklift | 10200 | 10200 (100.0 %) | none | 21 |

#### Completeness (ratio of sums; Target B intervals)

| metric | basis | A oracle, simulator positions | B oracle boxes, full_camera | C detector path |
|---|---|---|---|---|
| CM-01 | detected | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.91 [0.89, 0.92] |
| CM-01 | detected_plus_inferred | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.91 [0.89, 0.93] |
| CM-03 | detected | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.12 [0.10, 0.15] |
| CM-03 | detected_plus_inferred | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.13 [0.11, 0.16] |
| CM-08 | detected | 0.00 [0.00, 0.00] | 0.01 [0.01, 0.02] | 0.00 [0.00, 0.00] |
| CM-08 | detected_plus_inferred | 0.00 [0.00, 0.00] | 0.01 [0.01, 0.02] | 0.00 [0.00, 0.00] |

#### Runtime (this laptop: Intel Core i7-5650U, 2 cores, CPU only)

| stage | total |
|---|---|
| S2 artifact build | 0.01 h (28 s) |
| S2 YOLO-World inference (sum of per-frame times) | 6.28 h (22623 s) |
| S2 wall time incl. decoding and pipe | 6.39 h (23008 s) |
| S3 ByteTrack (incl. `.venv-det` start) and S3 build | 0.54 h (1930 s) |
| S4 full_camera | 0.02 h (61 s) |
| S5 BL-2..BL-6 (5 configurations) | 0.02 h (73 s) |

### Observations (descriptive, validation only)
- **Column A agrees with M1a on the pilot subset.** BL-2 is identical in A and B because it uses image boxes only. From BL-3 on, A gives recall 0.97–1.00 and precision 0.94–0.95 (M1a, all 226 cameras: 0.97–1.00 and 0.93–0.95). Column B (camera geometry, M1a's `full_camera` unit) loses about a quarter of the reference interactions, and precision falls to 0.55–0.57. This is the event-level counterpart of the position errors M1a reported (CR-026).
- **The detector path adds a much larger loss on top (B → C).** Recall falls from 0.74 to 0.11 and precision from 0.55 to 0.22 (BL-6). The tracker produced 142 candidate events at BL-6; 31 are matched to a reference interaction. The unmatched candidates were not diagnosed in this pilot.
- **Forklift coverage.** In column C, forklifts have 10,200 object-frames against 59,622 in column B (17 %). Persons have 51,436 against 55,971 (92 %).
- **Score bands (forklift, all kept detections, 36,474):** ≥ 0.25: 6,895; in (0.10, 0.25): 17,153; ≤ 0.10: 12,426. The tracker produced 9,618 tracked forklift points: more than the 6,895 high-score detections, because ByteTrack's second stage extends existing tracks with detections in (0.10, 0.25).
- **Bridging (g_max 15):** 129 person and 91 forklift gaps were bridged (344 and 582 predicted points); 8 person and 31 forklift gaps were longer than 15 eligible frames and left lost (151 and 708 frames).
- **Per-label results** follow the event results. The O label is rare and is scored 0 in columns B and C from BL-3 on; PC in column C follows H (recall about 0.10).
- **Position availability** is not the constraint on the detector path: 99.4 % of person and 100 % of forklift object-frames in column C have a position. 620 person and 21 forklift object-frames have a position but no matched identity on that frame and are not scored.
- **CM-08** (share of system pair-frames whose clearance is not measured) is 0.00 in column C.
- **Precision of the frame-level detector** is high everywhere (0.97–1.00): the detector rarely reports objects that are not there. The weakness is missed forklifts and, downstream, forklift detections too weak for the tracker.
- **Questions for D-47 (no recommendation; D-45 item 4 forbids tuning here):** whether the forklift threshold and the tracker's thresholds should be made consistent; whether a stronger forklift detector (Grounding DINO's frame-level recall is 0.94, at about 44 times the cost) should be tried on the detector path; and whether the unmatched candidate events should be diagnosed.

### Representation choices and review flags (AR-62, open for D-47)
AR-62 records the representation details of the S2 and S3 adapters and of IDF1. Four items are review flags, because another reading could move a reported number:
- **Item 3:** a `tracked` point carries the matched detection's own box, not the tracker's filtered box. Foot points, and so column C positions, depend on this.
- **Item 5:** ByteTrack runs on Ultralytics' NumPy assignment path instead of `lap`. Ultralytics states the two give the same assignment except under exact ties.
- **Item 6:** IDF1 is computed by a port of TrackEval, not TrackEval itself (not installed).
- **Item 7:** a track born after the first frame is not reported until its second match, so its first detection is not a point. This is the tracker's standard output.

S2 output, the expensive step, does not depend on items 3 to 9. If any of them is reversed, S3 onward can be re-run in minutes.

### Not run in this pilot
- MR-01 (D-45 item 2: no MR-01 run; S2 is tolerance class).
- Grounding DINO at scale (D-45 item 0; frame-level check only).
- Any threshold or tracker tuning, fine-tuning, the test partition, SmartSpaces (D-45 item 4).
- The `forklift_turning` stratum (D-45 item 3).

### Engineering record
- **Runtime estimate (before the run, D-45 item 3e; `research/m1b/pilot_runtime_estimate.md`):** 0.378 s per frame for S2 (median, including decoding), about 6.7 h of detection and about 8 h in all. Below the 12 h limit, so no STOP.
- **S2 run:** started 19 Nov 2026 about 05:00 (first camera written 05:02). It stopped at 07:23 after 71 of 206 cameras, with no error in the log and no process left. The cause was not recorded; the last cameras before the stop ran at about 215 s instead of about 108 s, which fits the machine throttling or sleeping. The run was resumed at 10:50 under `caffeinate -i`; finished cameras were skipped (each camera's output is written atomically, so no partial camera was kept). Measured S2 time: 6.39 h of wall time, of which 6.28 h is inference (sum over cameras; it excludes the stopped period).
- **Pipeline (S2 artifact → S5):** 0.58 h for 206 cameras (S3 0.54 h, including the `.venv-det` start for each camera). Evaluation of 206 cameras: about 2 min (2 workers), much less than the 0.5 h estimated. The aggregation was run twice and gave byte-identical `pilot_results.json`. Frame-level check: YOLO-World 0.34 s and Grounding DINO 15.2 s per frame (median).
- **Tests:** full suite 2460 passed, 8 skipped (the `.venv-det`-only tracker tests), run twice: identical. In `.venv-det`: `test_tracking_*` 16/16 and `test_zs_match` 7/7. Wording linter (`rq1.export.report.lint`): one W4 hit, the disclaimer sentence "Nothing here is 'validated'" itself, as in M1a.

## Stop
**STOP (D-47).** The Owner and the Architect review the results, the questions under Observations, and AR-62. Test partition reserved (D-37).
