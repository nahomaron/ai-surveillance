# M1b detector-path pilot report — validation partition (T-25p)

**Status: accepted at D-47 (19 Nov 2026) as experimental validation evidence (synthetic, validation only). The D-47 follow-up (C', N9, CR-007 evidence) and the D-50 extent table are added below. The pilot is CLOSED (D-50) as exploratory validation evidence.** Revised earlier on the Owner's instruction of 19 Nov 2026 (report and evaluation code only; no stage re-run, nothing tuned). All 206 pilot cameras ran through S2 → S5 and were evaluated; the frame-level check ran on both models.

Every number in this report is **experimental**: synthetic data (SDG), validation partition only (D-36, D-37), one zero-shot detector at fixed thresholds, one tracker at default parameters. Nothing here is "validated", and nothing here is a claim about real footage (D-45 item 4). Automated outputs are **candidate** events and **scenario counts**. No test-partition recording was processed. No acceptance criterion is registered or evaluated (D-45 item 4).

Contract E-1.2.21. Pre-registration version 1 (`docs/preregistration_FROZEN.md`), unchanged. Specification: D-45 (Owner decision with the Architect's detector-path pilot spec, 19 Nov 2026).
- **Run code.** S2 detection: commit `ac40508` for the first 71 cameras, `533d2ff` for the other 135 (the difference is one added file that no run imports; see Engineering record). Pipeline (S2 artifact → S5) and the evaluation (`evaluate_pilot.py`) and frame-level check: commit `533d2ff` on all 206 cameras. Revision analyses (`tracker_loss.py`, the extended `pilot_report_tables.py`): the commit of this revision.
- **Results.** `research/m1b/pilot_results.json`, `pilot_frame_check.json`, `pilot_tracker_loss.json`, `pilot_license_components.json`.

## Plain-language summary (one page)

**What was run.** The pilot asks what changes when the simulator's knowledge of where each object is in the image ("oracle perception", used in M1a) is replaced by an off-the-shelf detector and tracker. It uses 206 of the 226 SDG validation camera recordings (24 simulated scenes, 10 s each, one worker and one forklift per scene).
- The 20 cameras used to choose the detector thresholds in the T-22 probe are left out, so the pilot does not reuse the frames those thresholds were chosen on.
- Other cameras of the same simulated runs are in the pilot: 96 of the 206 pilot cameras, and 10 of the 20 frame-check cameras, share a run (one leakage group per run) with a probe camera. They show the same scene from another viewpoint.

The detector path:
- **Detector:** YOLO-World v2-s, used zero-shot with the prompts "person" and "forklift". It was not trained on this data. Thresholds are the probe's: person 0.20, forklift 0.05.
- **Tracker:** ByteTrack (Ultralytics' built-in version) with its default parameters, one tracker per class.
- **The rest of the pipeline is the M1a pipeline, unchanged:** floor positions from the dataset calibration and the bottom-centre of each box (`full_camera`), then the five rule configurations BL-2 to BL-6 at the frozen base values.

**What it is compared with.** The yardstick is the same as in M1a: BL-6 applied to the simulator's complete ground truth (Appendix T, T21), stored once per camera and not rebuilt. Three columns are reported on the same 206 cameras:
- **A, oracle path with simulator positions:** the M1a `base` unit, re-aggregated on these 206 cameras.
- **B, oracle boxes with camera geometry:** the M1a `full_camera` unit, re-aggregated on these 206 cameras.
- **C, detector path:** detector and tracker together, with camera geometry (this pilot). Column C measures the detector and the tracker as one system, including the coupling between the detector thresholds and the tracker's thresholds described below.

B to C is the effect of replacing oracle boxes by detector-and-tracker boxes. A to B is the effect of camera geometry, already reported in M1a.

**The tracker threshold coupling (both classes).** ByteTrack's default settings use detections in three ways (installed Ultralytics 8.4.215, `ultralytics/trackers/byte_tracker.py`):
- **A new track** starts only from a detection scoring at least 0.25 (`new_track_thresh`, line 500).
- **A track that is currently tracked** can be continued by a detection scoring above 0.10 and below 0.25 in a second matching stage (lines 338 and 448). That stage only considers tracks in the Tracked state (line 448).
- **A lost track**, one that missed a frame, is matched only in the first stage, which uses detections scoring at least 0.25 (lines 295, 303 and 337). So a lost track is revived only by a detection ≥ 0.25 (`track_high_thresh`).

The D-45 thresholds are below 0.25 for both classes: person 0.20 and forklift 0.05. So:
- Person detections in [0.20, 0.25), and forklift detections in [0.10, 0.25), can neither start a track nor revive a lost one. They can only extend a track that is being followed at that moment.
- Forklift detections in [0.05, 0.10] are never used by the tracker.

Neither threshold was tuned (D-45 items 0, 1 and 4).

**Main findings (SDG, validation, descriptive).**
1. **On the detector path, few reference interactions are found.**
   - Column C, BL-3 to BL-6: recall 0.11 (30–31 of 282 reference interactions), precision 0.22. BL-2: recall 0.03 (9 of 282), precision 0.10.
   - With oracle boxes and the same camera geometry (column B): recall 0.74–0.75, precision 0.55–0.57. With simulator positions (column A): recall 0.97–1.00, precision 0.94–0.95.
2. **Most of the loss happens at the tracker, for forklifts.**
   - Persons, frame-level recall at each stage: 0.92 for the detections, 0.91 for the tracked points, and 0.92 with the tracker's predicted points added. Tracks cover 91 % of person-visible frames (CM-01); IDF1 0.83.
   - Forklifts, the same stages: 0.61, then **0.16**, then 0.17.
   - The forklift detections are almost all real: 36,073 of 36,474 (99 %) match a forklift's box. Only 9,613 of those became tracked points (27 %).
   - Forklift IDF1 is 0.24; 93 forklift identities are never matched by any track.
   - An interaction needs both objects tracked, so only 12 % of the frames in which a worker and a forklift are both visible are covered by a matched system pair (CM-03 0.12, against 1.00 on the oracle path).
3. **The loss follows the tracker's score thresholds.** Of the forklift detections that match a forklift, the share that became tracked points was:
   - 86 % for scores ≥ 0.25;
   - 21 % for scores in [0.10, 0.25);
   - 0 % for scores below 0.10 (12,043 matched detections, all unused by design).
   Persons: 99 % for scores ≥ 0.25 and 28 % in [0.20, 0.25). Only 429 person detections fall in [0.20, 0.25), against 29,579 forklift detections below 0.25. Column C therefore measures this detector–tracker pair together. The pilot does not show what a differently configured tracker would give (nothing was tuned).
4. **Forklifts seen at eye level are the weakest case,** as in the probe. Detection recall is 0.43 at eye level and 0.78 from the ceiling. Tracked-point recall is 0.13 and 0.19.
5. **Where the detector path does give a position, it is no worse than with oracle boxes.**
   - Persons: median error 0.23 m, P95 0.53 m, 0.5 % above 5 m. Column B: 0.19 m, 0.75 m, 1.1 %.
   - Forklifts: median 0.81 m, P95 1.45 m. Column B: 1.07 m, 1.48 m.
   - Column C scores only object-frames whose track is matched to an identity: 50,522 of 51,142 person and 10,179 of 10,200 forklift object-frames with a position. The forklifts kept by the tracker are mostly the high-scoring ones, so B and C do not cover the same objects.
   - Bridged person points (predicted by the tracker over a gap) are less accurate: P95 2.02 m.
6. **No identity switches** were found for either class. Fragmentation is common: 229 of 379 person tracks and 105 of 171 forklift tracks are fragments of an identity.
7. **The frame-level check (20 pilot cameras, 100 frames) repeats the probe's picture.**
   - YOLO-World: person recall 0.94, forklift 0.59.
   - Grounding DINO tiny: person 0.96, forklift 0.94 (eye level 0.93), at about 15 s per frame against 0.34 s for YOLO-World.
   - Half of these cameras share a run with a probe camera (see above).
8. **Runtime.** Detection took 6.39 h of wall time for 61,749 frames, against an estimate of 6.7 h. Of that, 0.42 h was a slow period (7 cameras at about 215 s each) just before the machine went down. Everything after detection took 0.58 h, and the evaluation about 2 min.

**Addendum (D-47, 19 Nov 2026): C', the N9 diagnosis and the CR-007 evidence.** Details in the section "D-47 follow-up" below. Column C remains the pilot result; C' is post-hoc and exploratory and never replaces it.
- **Aligning the tracker's thresholds with the detector's (C') made forklift tracking worse, not better.**
  - BL-6 recall 0.07 and precision 0.15, against 0.11 and 0.22 for C.
  - Share of real forklifts covered by a tracked point: 0.12, against 0.16.
  - The reason is in the tracker's code. With `fuse_score` on (a default the C' rule leaves unchanged), the first matching stage needs overlap × score ≥ 0.2. So a forklift detection scoring below 0.2 can start a track but cannot continue one.
  - C' starts more forklift tracks (230 against 171) and breaks them more often (158 fragments against 105). It produces three times as many bridged points, and fewer tracked ones.
  - Persons barely change, apart from 13 more false tracks (49 against 36). No identity switches in either column.
- **Why the detector path raises false alerts (N9, rules 1–3).**
  - Of the 111 unmatched BL-6 events in C, the rules attribute only 2 (both to tracking). In the other 109, both tracks are correctly matched to the scene's worker and forklift.
  - 110 of the 111 overlap in time a reference interaction of the same pair, but with temporal IoU below 0.3: right pair, roughly right time, wrong extent.
  - Rules 4 (geometry) and 5 (event reasoning) need definitions for the detector path first (CR-029). C' looks the same: 120 unmatched events; 1 perception, 1 tracking, 118 not attributed by rules 1–3.
- **The forklift position offset (CR-007 evidence).** With oracle boxes and camera geometry (column B), the forklift error of about 1 m lies almost entirely along the camera's line of sight, toward the camera. Along: median −1.01 m; across: 0.09 m. This fits the box's bottom-centre marking the footprint's near edge rather than its centre. Added to CR-007 for the Architect; no rule chosen.
- **D-50: right pair, wrong extent.** Counted by any temporal overlap with the same pair (descriptive, not the N4 metric), 141 of the 142 BL-6 events in C overlap a real interaction. Half of the unmatched ones overlap it by a temporal IoU of 0.1 or less, and 38 of the 100 references found are split over two or more episodes that are rarely linked. The pilot is closed (D-50); the extent question goes to the Architect for v2.

## Technical report

### Scope and method
- **Population (D-45 item 3a):** the SDG validation cameras with an ORACLE-S3, minus the 20 probe cameras (`research/m1b/zero_shot_probe.json`, selection).
  - **206 cameras:** 99 `sdg:ceiling` and 107 `sdg:eye_level`, one 10 s window each, 61,749 eligible frames. Test: `tests/m1b/test_pilot_population.py`.
  - Leakage groups (runs): 24.
  - References (T21): 284, of which 282 assessable.
- **Overlap with the probe (Owner revision item 3).**
  - The 20 probe cameras come from 13 of the 24 runs.
  - 96 of the 206 pilot cameras belong to one of those 13 runs. In the frame-level check, 10 of the 20 cameras do, spread over 14 runs.
  - The pilot does not reuse the frames the thresholds were chosen on, but about half of it shows the same simulated scenes from other cameras.
- **S1:** the stored `rv2` artifact of each camera, reused from T-21.
- **S2 (D-45 item 2; T-23s):** YOLO-World v2-s on every eligible frame.
  - Weights `yolov8s-worldv2.pt`, SHA-256 in `research/m1b/zero_shot_weights.json`; AGPL-3.0 (D-43).
  - Prompts set once with `set_classes(["person", "forklift"])`. The text embeddings come from the CLIP ViT-B/32 text encoder (`ViT-B-32.pt`, MIT).
  - Ultralytics defaults (imgsz 640, NMS IoU 0.7, max_det 300), CPU.
  - Raw boxes at score ≥ 0.05 are stored per camera. The class thresholds (person 0.20, forklift 0.05) are applied when the `detection` artifact is built.
  - Reproducibility class: tolerance; no MR-01 run (D-45 item 2).
- **S3 (D-45 item 1; T-23):** Ultralytics ByteTrack (8.4.215), the installed `bytetrack.yaml` defaults: track_high_thresh 0.25, track_low_thresh 0.10, new_track_thresh 0.25, match_thresh 0.8, track_buffer 30, fuse_score on.
  - One tracker per class; one update per eligible frame.
  - A matched frame gives a `tracked` / `detected` point carrying the detection box (AR-62 item 3).
  - A gap of at most g_max = 15 eligible frames is bridged with the tracker's predicted box (`predicted` / `inferred`); longer gaps are `lost`. No point on ineligible frames.
  - Foot point = bottom-centre of the box.
  - The Apache-2.0 `trackers` package could not be installed without breaking `.venv-det`, so the D-45 fallback applies. Assignment uses Ultralytics' NumPy solver because `lap` is not installed (AR-62 item 5).
  - How the thresholds act (installed `byte_tracker.py`, SHA-256 `7d4a16b9…c7d32d`):
    - `_split_detections`, lines 337–338: high = score ≥ 0.25; low = 0.10 < score < 0.25.
    - First association, lines 303–307: tracked and lost tracks against high detections.
    - Second association, line 448: only tracks in the Tracked state, against low detections.
    - Unconfirmed tracks, lines 462ff.: high detections only.
    - New tracks, line 500: score ≥ 0.25.
    - So a lost track is revived only by a detection ≥ 0.25.
- **S4:** `full_camera` geometry from the S3 boxes and the dataset calibration, pre-registration v1 base values. No yaw is supplied, so the T8.2 heading and footprint fallbacks apply as the builder implements them. No `forklift_turning` stratum (D-45 item 3).
- **S5:** BL-2 to BL-6 at the frozen base values.
- **S8 (evaluation):** against the stored T21 references of each camera (`rule_conformance`, label group G1, T21.3 assessability), unchanged from T-21.
  - **Columns A and B are re-aggregated on the same 206 cameras.** Their per-camera counts are computed from the stored M1a `base` and `full_camera` artifacts of these cameras. Their point values and Target B intervals are recomputed on this subset, never copied from the 226-camera M1a report.
  - Association: F.1 A5.2, iou_cm 0.5, eps_amb 0.02. System boxes are the column's S3 points (not lost); reference boxes are the reference-visible boxes (T17.6). Columns A and B share the oracle association; column C associates the detector tracks.
  - Event matching, EV counts and completeness use the T-21 functions unchanged.
  - Intervals: Target B (`new_session_performance`), cluster bootstrap over leakage groups, B 2000, 95 %, seed 2026111402 as in T-21 (pre-registration v1 section 4.4). Shown without a decision.
- **Detection (frame level), column C only:** every eligible pilot frame.
  - References: the reference-visible boxes clipped to the image (the probe's reference).
  - Detections: the S2 rows after thresholds.
  - Matcher: the probe matcher (same class, IoU ≥ 0.3, one-to-one by descending IoU).
- **Detector-to-tracker breakdown (Owner revision item 2d; `research/m1b/tracker_loss.py`, read-only over the stored artifacts):** the same references and matcher.
  - Each kept detection is classed by score band ([thr, 0.10), [0.10, 0.25), ≥ 0.25), by whether it matches a reference box, and by whether it became a `tracked` S3 point (via `detection_id`).
  - Frame-level recall is computed for S2 detections, tracked points, and tracked + predicted points.
  - A score of exactly 0.10 is counted in [0.10, 0.25) here, but ByteTrack's low band excludes it (line 338).
  - Hand-computed test: `tests/m1b/test_tracker_loss.py`.
- **Tracking, column C only:**
  - T-12 association statuses and identity switches.
  - IDF1 per class against simulator identities (`research/m1b/idf1.py`, a port of TrackEval's Identity metric; AR-62 item 6).
  - IDF1 is pooled over the 206 cameras by summing IDTP, IDFP and IDFN per class (n in the table).
- **Position (D-41):** median, P95 and the shares above 1, 2 and 5 m of the error to the simulator position, for columns B and C, by class and evidence class.
  - Availability is reported separately: the share of object-frames with a position, and the counts by null reason.
  - Column B scores every object-frame with a position. Column C scores an object-frame only when its track is matched to an identity on that frame (A5.2 `matched`). The denominators and the unscored count are in the tables.
- **Frame-level check (D-45 item 3c):** 100 frames, 5 evenly spaced eligible frames from each of 20 pilot cameras (10 ceiling, 10 eye-level), seed 2026111902, by the probe's selection procedure (`research/m1b/frame_check.py`).
  - Both models at the fixed D-45 thresholds: YOLO-World person 0.20 and forklift 0.05; Grounding DINO tiny 0.45 for both.
  - No threshold is chosen here.

### Results (generated by `research/m1b/pilot_report_tables.py` from `pilot_results.json`, `pilot_frame_check.json` and `pilot_tracker_loss.json`)

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

IDF1 is pooled over the 206 cameras by summing IDTP, IDFP and IDFN per class, then IDF1 = IDTP / (IDTP + 0.5 IDFP + 0.5 IDFN). n below: reference boxes (IDTP + IDFN) and system points (IDTP + IDFP).

| class | tracks | one_to_one | id_switch | fragment | unmatched_system | identity switches | identities never matched | IDF1 | IDTP / IDFP / IDFN | n references / system points |
|---|---|---|---|---|---|---|---|---|---|---|
| person | 379 | 114 | 0 | 229 | 36 | 0 | 0 | 0.833 | 44584 / 6852 / 11067 | 55651 / 51436 |
| forklift | 171 | 66 | 0 | 105 | 0 | 0 | 93 | 0.244 | 8530 / 1670 / 51047 | 59577 / 10200 |

Bridging (D-45 item 1):

| class | tracked points | predicted points (bridged) | runs bridged | runs lost (> 15) | frames lost in long runs |
|---|---|---|---|---|---|
| person | 51092 | 344 | 129 | 8 | 151 |
| forklift | 9618 | 582 | 91 | 31 | 708 |

#### Detections by score band, reference match and tracking (column C, all pilot frames; `tracker_loss.py`)

Bands: class threshold (person 0.20, forklift 0.05) to 0.10, 0.10 to 0.25, 0.25 and above (ByteTrack's default track_low_thresh and track_high_thresh). Matched: matched to a reference-visible box by the probe matcher (IoU ≥ 0.3) among all S2 detections of the frame. Tracked: the detection became a `tracked` S3 point.

| class | band | detections | matched, tracked | matched, not tracked | unmatched, tracked | unmatched, not tracked | share of matched that were tracked |
|---|---|---|---|---|---|---|---|
| person | [thr, 0.10) | 0 (empty: the class threshold is above 0.10) | — | — | — | — | — |
| person | [0.10, 0.25) | 429 | 51 | 128 | 24 | 226 | 28.5 % |
| person | >= 0.25 | 51589 | 50638 | 305 | 379 | 267 | 99.4 % |
| forklift | [thr, 0.10) | 12426 | 0 | 12043 | 0 | 383 | 0.0 % |
| forklift | [0.10, 0.25) | 17153 | 3654 | 13482 | 5 | 12 | 21.3 % |
| forklift | >= 0.25 | 6895 | 5959 | 935 | 0 | 1 | 86.4 % |

Frame-level recall stage by stage (same references and matcher; matched references / reference boxes):

| viewpoint | class | reference boxes | S2 detections (after thresholds) | tracked S3 points | tracked + predicted S3 points |
|---|---|---|---|---|---|
| all | person | 55651 | 0.92 (51122) | 0.91 (50712) | 0.92 (50972) |
| all | forklift | 59577 | 0.61 (36073) | 0.16 (9618) | 0.17 (10193) |
| ceiling | person | 29357 | 0.92 (27018) | 0.91 (26842) | 0.92 (26930) |
| ceiling | forklift | 29536 | 0.78 (23169) | 0.19 (5635) | 0.20 (5934) |
| eye_level | person | 26294 | 0.92 (24104) | 0.91 (23870) | 0.91 (24042) |
| eye_level | forklift | 30041 | 0.43 (12904) | 0.13 (3983) | 0.14 (4259) |

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

Denominators: column B scores every object-frame with a position (oracle tracks carry their identity). Column C scores an object-frame only when its track is matched to an identity on that frame (A5.2 `matched`):

| column | class | object-frames with a position | scored (error computed) | with a position, no matched identity (not scored) |
|---|---|---|---|---|
| B | person | 55374 | 55374 | 0 |
| B | forklift | 59622 | 59622 | 0 |
| C | person | 51142 | 50522 | 620 |
| C | forklift | 10200 | 10179 | 21 |

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
- **Column A on the pilot subset is close to M1a on all 226 cameras.** BL-2 is identical in A and B because it uses image boxes only. From BL-3 on, A gives recall 0.97–1.00 and precision 0.94–0.95 on the 206 cameras (M1a, 226 cameras: 0.97–1.00 and 0.93–0.95).
- **Column B (camera geometry) loses about a quarter of the reference interactions,** and precision falls to 0.55–0.57. This is the event-level counterpart of the position errors M1a reported (CR-026).
- **The detector path adds a much larger loss on top (B → C).** At BL-6, recall falls from 0.74 to 0.11 and precision from 0.55 to 0.22. Column C produced 142 candidate events at BL-6; 31 are matched to a reference interaction. The unmatched candidates were not diagnosed in this pilot.
- **Forklift coverage.** In column C, forklifts have 10,200 object-frames against 59,622 in column B (17 %). Persons have 51,436 against 55,971 (92 %).
- **Detections the tracker did not use.**
  - Forklift, score ≥ 0.25: 935 detections that match a forklift did not become tracked points (14 %). Expected sources are each new track's first detection, which ByteTrack does not report (AR-62 item 7), and short-lived unconfirmed tracks. Not diagnosed further.
  - Forklift, [0.10, 0.25): 13,482 matched detections were not tracked. The band can only extend a track in the Tracked state, by IoU (line 448), so these are frames with no forklift track being followed, or where that match failed. Not diagnosed further.
  - Forklift, [0.05, 0.10): 12,043 matched detections; the tracker never uses this band.
- **Bridging (g_max 15).**
  - Bridged: 129 person and 91 forklift gaps (344 and 582 predicted points).
  - Left lost, being longer than 15 eligible frames: 8 person and 31 forklift gaps (151 and 708 frames).
  - Predicted points add little recall: forklift 0.16 → 0.17.
- **Per-label results follow the event results.** The O label is rare and is scored 0 in columns B and C from BL-3 on; PC in column C follows H (recall about 0.10).
- **Position availability is not the constraint on the detector path.** In column C, 99.4 % of person and 100 % of forklift object-frames have a position.
- **CM-08** (share of system pair-frames whose clearance is not measured) is 0.00 in column C.
- **Frame-level precision is high everywhere (0.97–1.00):** the detector rarely reports objects that are not there.

### Limitations (D-45 item 3d)
- **Synthetic data only.** SDG validation partition, one simulator, one worker and one forklift per scene. Nothing here transfers to real footage (D-45 item 4).
- **Zero-shot detector at probe thresholds.**
  - YOLO-World v2-s, not trained on these data.
  - The thresholds come from a 100-frame probe on 20 cameras (T-22). The pilot excludes those cameras, but 96 of its 206 cameras share a run with them.
- **No yaw on the detector path.** The T8.2 heading and footprint fallbacks apply, and there is no `forklift_turning` stratum (D-45 item 3).
- **CR-026 is open,** so far-range positions (shallow foot rays) are reported as computed, not filtered.
- **The footprint anchor is still deferred (D-8 / CR-007),** so the foot point (bottom-centre of the box) is used as the footprint centre.
- **The reference is BL-6-defined (T21).** BL-3 vs BL-6 comparisons are partly circular against it (T21.5), so results from BL-4/BL-6 "agree more closely with the BL-6 reference definition", nothing more. BL-2 vs BL-3 is the least reference-dependent comparison.
- **The BL-2 finding is viewpoint-dependent.** R1 and R2 disagree on 51 % of SDG pair-frames but 4 % on SmartSpaces, and BL-2 has not been scored on SmartSpaces (D-40 item 2).
- **S2 is tolerance class.** No MR-01 run, so repeatability of the detector output is not measured.
- **Tracker.** Ultralytics ByteTrack, not the `trackers` package; NumPy assignment solver, not `lap`; default parameters, whose thresholds are coupled to the detector thresholds as described above (AR-62 item 5).
- **IDF1** comes from a port of TrackEval, not TrackEval itself (AR-62 item 6).
- **One camera at a time.** No multi-camera linkage. Target B intervals rest on 24 leakage groups.

### Representation choices and review flags (AR-62, open for D-47)
AR-62 records the representation details of the S2 and S3 adapters and of IDF1. Four items are review flags, because another reading could move a reported number:
- **Item 3:** a `tracked` point carries the matched detection's own box, not the tracker's filtered box. Foot points, and so column C positions, depend on this.
- **Item 5:** ByteTrack runs on Ultralytics' NumPy assignment path instead of `lap`. Ultralytics states the two give the same assignment except under exact ties.
- **Item 6:** IDF1 is computed by a port of TrackEval, not TrackEval itself (not installed).
- **Item 7:** a track born after the first frame is not reported until its second match, so its first detection is not a point. This is the tracker's standard output.

S2 output, the expensive step, does not depend on items 3 to 9. If any of them is reversed, everything from the S2 artifact onward can be re-run without new detection. Measured on this pilot, that is 0.58 h for 206 cameras (about 10 s per camera: S3 9.4 s including the `.venv-det` start, S4 and S5 0.65 s, the S2 artifact 0.14 s), plus about 2 min for the evaluation and 20 s for the tracker breakdown: about 40 min in all.

### Not run in this pilot
- **MR-01:** not run (D-45 item 2); S2 is tolerance class.
- **Grounding DINO at scale:** not run (D-45 item 0); it was used in the frame-level check only.
- **Excluded by D-45 item 4:** any threshold or tracker tuning, fine-tuning, the test partition, SmartSpaces.
- **The `forklift_turning` stratum:** not used (D-45 item 3).

### Licence records (Owner revision item 6)
Every weight file loaded in the pilot has a `license_component` row and a `NOTICE.md` entry. The rows are listed in `research/m1b/pilot_license_components.json`, built with `rq1.perception.s2.weights_component`.

| file | used in | licence | `lic_id` | in an artifact |
|---|---|---|---|---|
| `yolov8s-worldv2.pt` | S2; frame-level check | AGPL-3.0 | `lic_o5ewu7z62ba22gjdgwsxvtitky` | yes: the `license_component` row of every pilot S2 artifact |
| `ViT-B-32.pt` (CLIP text encoder of YOLO-World) | S2 (prompt embeddings); frame-level check | MIT | `lic_ym5owzhkkwvjzayaewgzuzhpyc` | no. Its SHA-256 is in the S2 run configuration (`text_encoder_sha256`). **This row was missing and is added as a record only:** putting it in the S2 artifact would change the S2 artifact IDs, which this revision does not allow. |
| `grounding-dino-tiny/model.safetensors` (and its tokenizer and config files) | frame-level check | Apache-2.0 | `lic_bim7wazyo5z6kh4iiks4hvky2q` | no: the frame-level check builds no artifact (record only) |

`NOTICE.md` already listed all three files, under the T-22 probe. Its "used in" column now names the pilot as well.

### Engineering record
- **Runtime estimate** (before the run, D-45 item 3e; `research/m1b/pilot_runtime_estimate.md`): 0.378 s per frame for S2 (median, including decoding), about 6.7 h of detection and about 8 h in all. Below the 12 h limit, so no STOP.
- **S2 run, start and stop.**
  - The run started on 19 Nov 2026 at about 05:00; the first camera was written at 05:02.
  - The last camera written before the stop was saved at 07:23 (camera 71 of 206). The log shows no error.
- **Why it stopped: the machine went down.**
  - It booted again at 10:14:47 (`sysctl kern.boottime`). `last shutdown` records no shutdown that day, so this was not a clean shutdown. No panic report was written, and the unified log gives no shutdown cause.
  - The power log (`pmset -g log`) has its last entry at 07:17 and nothing between 07:17 and 10:35. It records no sleep event during the run.
  - The machine was on battery: the 04:31 entry reads "Using Batt (Charge: 100)", and a battery-health warning was logged at 07:07 ("Warning level: 3").
  - The cause is not established. Possible causes: loss of power on battery, or a forced restart.
- **Slow period before the stop.**
  - The 7 cameras saved from 07:01:50 to 07:23 took 1,502 s, about 215 s each, against about 108 s normally.
  - Another agent session (the T23 agent, D-48) was running on the same 2-core laptop during the S2 run. CPU competition from it is a possible cause of the slow cameras, next to thermal throttling.
  - The power log also shows a `caffeinate` assertion (PID 10450), held from about 03:50 until at least 07:17. It was started before the S2 run, and the log does not record which process it belonged to.
- **Resume.** The run was restarted at 10:50 under `caffeinate -i`. Finished cameras were skipped; each camera's output is written atomically, so no partial camera was kept.
- **S2 runtime** (sum of per-camera wall times, decoding and pipe included; the stopped period is excluded):

| period | cameras | wall time | mean per camera |
|---|---|---|---|
| before the slow period (05:00–06:58) | 64 | 7,044 s (1.96 h) | 110.1 s |
| slow period (06:58–07:23) | 7 | 1,502 s (0.42 h) | 214.6 s |
| after the resume (10:50–14:52) | 135 | 14,462 s (4.02 h) | 107.1 s |
| **total** | **206** | **23,008 s (6.39 h)** | 111.7 s |

  Pure inference (the sum of per-frame times) was 6.28 h.
- **The two S2 commits.** `git diff --stat ac40508 533d2ff`:

  ```
   research/m1b/pilot_report_tables.py | 115 ++++++++++++++++++++++++++++++++++++
   1 file changed, 115 insertions(+)
  ```

  No run imports that script, so the 71 cameras at `ac40508` and the 135 at `533d2ff` ran identical detector code.
- **Pipeline** (S2 artifact → S5): 0.58 h for 206 cameras, all at commit `533d2ff`. Of this, S3 took 0.54 h, including the `.venv-det` start for each camera.
- **Evaluation:** about 2 min for 206 cameras on 2 workers, against 0.5 h estimated. The aggregation was run twice and gave a byte-identical `pilot_results.json`.
- **Frame-level check:** YOLO-World 0.34 s and Grounding DINO 15.2 s per frame (median).
- **Tests:** full suite 2465 passed, 8 skipped (`.venv-det`-only tracker tests), run twice: identical. In `.venv-det`: `test_tracking_*` 16/16, `test_zs_match` 7/7. `tracker_loss.py` was run twice and gave byte-identical JSON.
- **Wording linter** (`rq1.export.report.lint`, run again after D-50): two W4 hits, both quoting the disclaimer: the sentence "Nothing here is 'validated'" itself, and this line. No other hit.

## D-47 follow-up: C' (post-hoc, exploratory), N9 diagnosis and CR-007 evidence

Owner decision D-47 (19 Nov 2026). Nothing in columns A, B or C changed. The f83a241 sections above are unchanged apart from this section, the addendum to the plain-language page, and the status line.

### Method
- **C' (D-47 item 1), post-hoc and exploratory.**
  - S3 onward was re-run on column C's stored S2 artifacts; there was no detection and no S2 rebuild, so C and C' share every S2 artifact ID.
  - One ByteTrack per class. Per class: track_high_thresh = new_track_thresh = the detector threshold (person 0.20, forklift 0.05); track_low_thresh = min(0.10, detector threshold), i.e. person 0.10 and forklift 0.05. For forklifts, ByteTrack's low band (0.05 < s < 0.05) is empty, so its second stage receives nothing.
  - All other parameters are the installed defaults, including fuse_score on and match_thresh 0.8. The rule was fixed by the Owner before the run, and no other value was tried.
  - The per-class parameters are recorded in every C' S3 run configuration (`params_by_class`), so every C' S3, S4 and S5 artifact has a new ID.
  - Run: commit `99a1306`, 206 cameras, on mains power with no other agent running. Evaluation at commit `8e7802c`, with the same functions as column C (`evaluate_pilot.py`; column C was re-checked byte-identical after the change).
- **What the code does at low scores (installed Ultralytics 8.4.215).**
  - With fuse_score on, the first-stage cost is 1 − IoU × score (`matching.py` `fuse_score`, line 145; `byte_tracker.py` lines 529–531), and a match needs cost ≤ match_thresh 0.8. So a detection must score ≥ 0.2 even at IoU 1.
  - Unconfirmed tracks use the same fused cost with threshold 0.7 (lines 462ff.).
  - Under C', a forklift detection scoring below 0.2 can therefore start a track but cannot continue one.
  - The adapter test `test_tracking_bytetrack.py::CPrime` shows it on a one-box fixture: at score 0.06, one point on the first frame, then none. The first version of that test's hand reasoning omitted fuse_score; it was corrected from the code before the pilot run (Progress log).
- **N9 (D-47 item 3):** `research/m1b/n9_pilot.py`, on every unmatched G1 event (false or duplicate alert) of BL-6 in C and in C'. Rules in pipeline order:
  1. Evidence unavailable: coverage at the event's CA frame not usable.
  2. Perception: AR-42 item 1 (one of the event's tracks has no reference object of its class with IoU ≥ 0.5 within ±5 frames of the CA frame).
  3. Tracking: the two tracks are not both `matched` at the CA frame (FX-ID-8).

  Rules 4 (geometry) and 5 (event reasoning) are `not_evaluated`: their inputs are not defined for a detector-path event (CR-029, open). Rule 7 does not apply (no reference). So "unresolved" here means "not attributed by rules 1–3". No oracle factorial (T12.3) was run.
- **N9 descriptive cross-check (not an N9 rule):** the largest temporal IoU between the unmatched event and any G1 reference interaction of the same identity pair.
- **CR-007 evidence (D-47 item 2):** `research/m1b/cr007_evidence.py`, column B (the stored `full_camera` S4).
  - Forklift error = estimate − simulator footprint centre, split along and across two directions: the line of sight (camera floor point C = −Rᵀt → true position), and the optical axis projected on the floor. Hand-computed tests: `tests/m1b/test_cr007_evidence.py`.
  - EV-M1/EV-M2 of column B for cameras whose median forklift error is below 1 m and at or above 1 m. Every pilot camera has exactly one worker and one forklift, so a camera is one pair.
- **Reproducibility.** All four results files were written twice, byte-identical. The C' tracker was re-run on 3 cameras from the stored inputs, with identical output.

### Results (generated by `research/m1b/d47_report_tables.py`)

Cameras: C 206, C' 206; the same S2 artifacts; references as in the pilot (282 assessable).

#### Events: EV-M1 and EV-M2 (G1, Target B intervals), C and C' (post-hoc, exploratory)

| configuration | column | EV-M1 | Target B | matched / assessable | EV-M2 | Target B | matched / system | candidate events |
|---|---|---|---|---|---|---|---|---|
| BL-2 | C | 0.03 | [0.00, 0.06] | 9 / 282 | 0.10 | [0.02, 0.18] | 9 / 92 | 92 |
| BL-2 | C' | 0.02 | [0.00, 0.05] | 7 / 282 | 0.09 | [0.00, 0.16] | 7 / 80 | 80 |
| BL-3 | C | 0.11 | [0.06, 0.16] | 30 / 282 | 0.22 | [0.12, 0.34] | 30 / 137 | 137 |
| BL-3 | C' | 0.07 | [0.03, 0.11] | 20 / 282 | 0.15 | [0.07, 0.24] | 20 / 136 | 136 |
| BL-4 | C | 0.11 | [0.06, 0.16] | 31 / 282 | 0.22 | [0.12, 0.34] | 31 / 141 | 141 |
| BL-4 | C' | 0.07 | [0.03, 0.12] | 21 / 282 | 0.15 | [0.07, 0.25] | 21 / 140 | 140 |
| BL-5 | C | 0.11 | [0.06, 0.16] | 30 / 282 | 0.22 | [0.12, 0.33] | 30 / 139 | 139 |
| BL-5 | C' | 0.07 | [0.03, 0.11] | 20 / 282 | 0.14 | [0.07, 0.23] | 20 / 138 | 138 |
| BL-6 | C | 0.11 | [0.06, 0.16] | 31 / 282 | 0.22 | [0.12, 0.33] | 31 / 142 | 142 |
| BL-6 | C' | 0.07 | [0.03, 0.12] | 21 / 282 | 0.15 | [0.07, 0.25] | 21 / 141 | 141 |

#### Per-label recall and precision (O, H, PC; descriptive)

| configuration | column | O recall | O precision | H recall | H precision | PC recall | PC precision |
|---|---|---|---|---|---|---|---|
| BL-2 | C | 0.00 | 0.00 | 0.00 | — | 0.00 | — |
| BL-2 | C' | 0.00 | 0.00 | 0.00 | — | 0.00 | — |
| BL-3 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.00 | — |
| BL-3 | C' | 0.00 | 0.00 | 0.07 | 0.17 | 0.00 | — |
| BL-4 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.10 | 0.24 |
| BL-4 | C' | 0.00 | 0.00 | 0.07 | 0.18 | 0.07 | 0.19 |
| BL-5 | C | 0.00 | 0.00 | 0.11 | 0.23 | 0.09 | 0.33 |
| BL-5 | C' | 0.00 | 0.00 | 0.07 | 0.17 | 0.06 | 0.25 |
| BL-6 | C | 0.00 | 0.00 | 0.11 | 0.24 | 0.10 | 0.24 |
| BL-6 | C' | 0.00 | 0.00 | 0.07 | 0.18 | 0.07 | 0.19 |

#### Tracking (T-12 association at iou_cm 0.5; IDF1 pooled over cameras by summed IDTP / IDFP / IDFN)

Tracks started = tracks reported by the tracker. False tracks = tracks whose T-12 status is `unmatched_system` (never matched to an identity).

| class | column | tracks started | one_to_one | fragment | id_switch (status) | false tracks | identity switches | identities never matched | IDF1 | n references / system points |
|---|---|---|---|---|---|---|---|---|---|---|
| person | C | 379 | 114 | 229 | 0 | 36 | 0 | 0 | 0.833 | 55651 / 51436 |
| person | C' | 394 | 114 | 231 | 0 | 49 | 0 | 0 | 0.832 | 55651 / 51452 |
| forklift | C | 171 | 66 | 105 | 0 | 0 | 0 | 93 | 0.244 | 59577 / 10200 |
| forklift | C' | 230 | 69 | 158 | 0 | 3 | 0 | 73 | 0.217 | 59577 / 9095 |

Bridging (g_max 15):

| class | column | tracked points | predicted points | runs bridged | runs lost (> 15) | frames lost in long runs |
|---|---|---|---|---|---|---|
| person | C | 51092 | 344 | 129 | 8 | 151 |
| person | C' | 51085 | 367 | 141 | 7 | 135 |
| forklift | C | 9618 | 582 | 91 | 31 | 708 |
| forklift | C' | 7187 | 1908 | 575 | 61 | 1314 |

#### Frame-level recall stage by stage (same references and matcher as the pilot)

| viewpoint | class | reference boxes | S2 detections | C tracked | C tracked + predicted | C' tracked | C' tracked + predicted |
|---|---|---|---|---|---|---|---|
| all | person | 55651 | 0.92 | 0.91 | 0.92 | 0.91 | 0.92 |
| all | forklift | 59577 | 0.61 | 0.16 | 0.17 | 0.12 | 0.15 |
| ceiling | person | 29357 | 0.92 | 0.91 | 0.92 | 0.91 | 0.92 |
| ceiling | forklift | 29536 | 0.78 | 0.19 | 0.20 | 0.14 | 0.18 |
| eye_level | person | 26294 | 0.92 | 0.91 | 0.91 | 0.91 | 0.91 |
| eye_level | forklift | 30041 | 0.43 | 0.13 | 0.14 | 0.10 | 0.12 |

C' detections by score band, reference match and tracking (bands as in the pilot; the C' thresholds differ from the band edges):

| class | band | detections | matched, tracked | matched, not tracked | unmatched, tracked | unmatched, not tracked | share of matched that were tracked (C → C') |
|---|---|---|---|---|---|---|---|
| person | [0.10, 0.25) | 429 | 12 | 167 | 19 | 231 | 28.5 % → 6.7 % |
| person | >= 0.25 | 51589 | 50655 | 288 | 399 | 247 | 99.4 % → 99.4 % |
| forklift | [thr, 0.10) | 12426 | 25 | 12018 | 2 | 381 | 0.0 % → 0.2 % |
| forklift | [0.10, 0.25) | 17153 | 1072 | 16064 | 0 | 17 | 21.3 % → 6.3 % |
| forklift | >= 0.25 | 6895 | 6088 | 806 | 0 | 1 | 86.4 % → 88.3 % |

#### Position (D-41), C and C' (scored on frames whose track is matched to an identity)

| column | class | n scored | median (m) | P95 (m) | > 1 m | > 2 m | > 5 m | with a position, not scored |
|---|---|---|---|---|---|---|---|---|
| C | person | 50522 | 0.23 | 0.53 | 2.0 % | 1.1 % | 0.5 % | 620 |
| C | forklift | 10179 | 0.81 | 1.45 | 36.9 % | 0.0 % | 0.0 % | 21 |
| C' | person | 50505 | 0.23 | 0.52 | 2.0 % | 1.1 % | 0.5 % | 649 |
| C' | forklift | 9073 | 0.82 | 1.44 | 37.1 % | 0.0 % | 0.0 % | 22 |

#### Completeness (ratio of sums; Target B intervals)

| metric | basis | C | C' |
|---|---|---|---|
| CM-01 | detected | 0.91 [0.89, 0.92] | 0.91 [0.89, 0.92] |
| CM-01 | detected_plus_inferred | 0.91 [0.89, 0.93] | 0.91 [0.89, 0.93] |
| CM-03 | detected | 0.12 [0.10, 0.15] | 0.09 [0.07, 0.11] |
| CM-03 | detected_plus_inferred | 0.13 [0.11, 0.16] | 0.12 [0.09, 0.14] |
| CM-08 | detected | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| CM-08 | detected_plus_inferred | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |

#### N9 rule tests on the unmatched BL-6 events (rules 1-3; rules 4 and 5 not evaluated, CR-029)

"unresolved" here means not attributed by rules 1-3.

| column | unmatched events | false_alert | duplicate_alert | evidence_unavailable | perception | tracking | unresolved | ceiling: perception / tracking / unresolved | eye level: perception / tracking / unresolved |
|---|---|---|---|---|---|---|---|---|---|
| C | 111 | 103 | 8 | 0 | 0 | 2 | 109 | 0 / 0 / 64 | 0 / 2 / 45 |
| C' | 120 | 113 | 7 | 0 | 1 | 1 | 118 | 0 / 0 / 78 | 1 / 1 / 40 |

Descriptive cross-check (not an N9 rule): overlap in time with a reference interaction of the same identity pair.

| column | pair unresolved | no reference of the pair | reference of the pair, no overlap | overlap, temporal IoU < 0.3 (iou_m) | overlap ≥ 0.3 |
|---|---|---|---|---|---|
| C | 0 | 0 | 1 | 110 | 0 |
| C' | 0 | 0 | 3 | 116 | 1 |

#### CR-007 / D-8 evidence: column B forklift position error along and across the viewing direction

Error = estimate − simulator footprint centre. Line of sight: from the camera's floor point to the true position; along < 0 means the estimate lies between the camera and the true centre. Optical axis: the camera's axis projected on the floor.

| viewpoint | n | error median / P95 (m) | line of sight: along, signed median | along |·| median / P95 | across median / P95 | share beyond the truth | optical axis: along signed median | across median / P95 | camera-to-object distance median (m) |
|---|---|---|---|---|---|---|---|---|---|
| all | 59622 | 1.07 / 1.48 | -1.01 | 1.02 / 1.46 | 0.09 / 0.58 | 2.9 % | -0.96 | 0.12 / 0.88 | 6.97 |
| ceiling | 29536 | 1.13 / 1.48 | -1.10 | 1.11 / 1.48 | 0.06 / 0.26 | 3.6 % | -1.08 | 0.08 / 0.45 | 7.95 |
| eye_level | 30086 | 0.99 / 1.48 | -0.88 | 0.88 / 1.42 | 0.12 / 0.79 | 2.1 % | -0.73 | 0.19 / 1.09 | 5.65 |

Column B events for cameras (one worker–forklift pair each: True) by median forklift error:

| group | cameras (ceiling / eye level) | configuration | EV-M1 | matched / assessable | EV-M2 | matched / system |
|---|---|---|---|---|---|---|
| below 1m | 90 (36 / 54) | BL-2 | 0.47 | 58 / 124 | 0.41 | 58 / 142 |
| below 1m | 90 (36 / 54) | BL-3 | 0.71 | 88 / 124 | 0.48 | 88 / 182 |
| below 1m | 90 (36 / 54) | BL-4 | 0.73 | 90 / 124 | 0.47 | 90 / 192 |
| below 1m | 90 (36 / 54) | BL-5 | 0.72 | 89 / 124 | 0.47 | 89 / 188 |
| below 1m | 90 (36 / 54) | BL-6 | 0.72 | 89 / 124 | 0.47 | 89 / 191 |
| at or above 1m | 116 (63 / 53) | BL-2 | 0.60 | 95 / 158 | 0.54 | 95 / 175 |
| at or above 1m | 116 (63 / 53) | BL-3 | 0.76 | 120 / 158 | 0.65 | 120 / 186 |
| at or above 1m | 116 (63 / 53) | BL-4 | 0.77 | 121 / 158 | 0.63 | 121 / 191 |
| at or above 1m | 116 (63 / 53) | BL-5 | 0.76 | 120 / 158 | 0.63 | 120 / 189 |
| at or above 1m | 116 (63 / 53) | BL-6 | 0.77 | 121 / 158 | 0.63 | 121 / 191 |

#### C' runtime (this laptop, mains power, no other agent)

| stage | total |
|---|---|
| s3_track | 0.28 h (1019 s) |
| s4 | 0.01 h (30 s) |
| s5 | 0.01 h (47 s) |

### Observations (descriptive, validation only)
- **C' lowers the event metrics at every configuration.** BL-6 recall is 0.07 (21 of 282) against 0.11 (31), and precision 0.15 against 0.22. The Target B intervals of C and C' overlap.
- **Forklift tracking under C'.** Tracks started rose from 171 to 230. Fragments rose from 105 to 158, and bridged gaps from 91 to 575. Predicted points rose from 582 to 1,908, and tracked points fell from 9,618 to 7,187. Identities never matched fell from 93 to 73: more forklifts are touched by some track, but for less time.
- **Of the matched forklift detections in [0.10, 0.25), 6.3 % were tracked under C', against 21.3 % under C.** C's second stage, which ignores score, used to extend tracks with them. Under C' they reach only the score-fused first stage. Detections ≥ 0.25 are tracked slightly more often (88.3 % against 86.4 %).
- **Cost of starting tracks at low score.** False tracks: person 49 (C: 36), forklift 3 (C: 0). Identity switches: 0 in both columns. CM-03 (detected) fell from 0.12 to 0.09.
- **Persons are almost unaffected:** per-frame recall at each stage, CM-01 0.91, IDF1 0.832 against 0.833. Only 429 person detections fall in [0.20, 0.25).
- **N9.**
  - C: 111 unmatched events, of which 103 are false alerts and 8 duplicates. Rule 1: 0. Rule 2 (perception): 0. Rule 3 (tracking): 2. Not attributed by rules 1–3: 109.
  - C': 120 unmatched events; perception 1, tracking 1, not attributed 118.
  - In C, 110 of the 111 overlap a reference interaction of the same pair with temporal IoU above 0 and below 0.3; one has no overlap. The unmatched events are therefore not phantom pairs. They are the right worker and forklift at about the right time, with an extent that does not match the reference's. Whether geometry (rule 4) or event reasoning (rule 5) causes that waits for CR-029.
- **CR-007 evidence.**
  - Column B forklift error lies along the line of sight: signed median −1.01 m (ceiling −1.10, eye level −0.88), against 0.09 m across. Only 2.9 % of estimates lie beyond the true centre.
  - The camera split shows higher B event metrics for cameras with forklift error ≥ 1 m (BL-6 0.77 / 0.63) than below 1 m (0.72 / 0.47). BL-2, which uses no floor geometry, differs in the same direction (0.60 / 0.54 against 0.47 / 0.41), so the split reflects viewpoint and scene differences, not the effect of the offset.
- **Not done (D-47 item 4):** Grounding DINO on the detector path, fine-tuning, the test partition, and any change to pre-registration v1.

### Operations record (D-47 item 5)
- **Ultralytics sync.**
  - The repository's settings file (`out/m1b/ultralytics_config/Ultralytics/settings.json`, git-ignored) has had `"sync": false` since the T-22 probe set it at 02:13 on 19 Nov.
  - Every detector run goes through `zero_shot_probe.ultralytics_settings()`, which sets `sync` to false and asserts it before a model is loaded. That covers the S2 run (`s2_yolo_world.py` → `zero_shot_probe.yolo_world`) and the frame-level check.
  - Sync was therefore off during both runs. The file was last written at 15:09, during the frame-level check, still with `sync: false`.
- **Network.** It was reachable during both runs: the power log shows network-access assertions during the S2 run (06:32), and this session was online during the frame-level check.
  - Hugging Face telemetry was disabled (`HF_HUB_DISABLE_TELEMETRY=1`).
  - Grounding DINO was loaded with `snapshot_download` of the pinned revision, which most likely made a metadata request to huggingface.co (not verified). That call sends no project data.
  - Nothing in the results changes.
- **YOLO_CONFIG_DIR.** Every `.venv-det` command now gets the in-repository folder through `pilot_common.DET_ENV`, set before any Ultralytics import. Tests: `tests/m1b/test_det_env.py`. The two earlier slips (T-23 and the f83a241 revision), which created a settings file in the home folder, came from ad hoc commands outside the run scripts; both files were deleted.
- **Power and other agents.** The C' run was on mains power, with no other agent session running (checked before the run).
- **License rows.** Recorded for the next S2 build (pre-registration v2): the CLIP text encoder and Grounding DINO `license_component` rows go inside the artifact (`research/m1b/pilot_license_components.json` holds them now).

## D-50: episode extent and fragmentation on the detector path (descriptive)

Owner decision D-50 (19 Nov 2026). Computed from stored outputs only, with no stage re-run (`research/m1b/extent_check.py` → `pilot_extent.json`; hand-computed tests in `tests/m1b/test_extent_check.py`). N4 and every reported metric are unchanged. The pilot is closed with this table.

- **Scope:** BL-6, label group G1, columns C and C'. References are the assessable G1 references, and events the deciding G1 system events, both as in N4. Pairs are resolved as for N4.
- **Best same-pair IoU:** for each unmatched event (false or duplicate alert), the largest temporal IoU with a reference of the same identity pair (0 if there is none).
- **Overlapping episodes:** for each reference that is N4-matched or overlapped by a same-pair BL-6 episode, the number of such episodes, and how many of them carry `continuation_of_nk`.
- **"Any temporal overlap, same pair"** is descriptive, not the N4 metric:
  - a reference is found when any same-pair event overlaps it;
  - an event is supported when it overlaps any same-pair reference;
  - there is no one-to-one rule and no iou_m.

#### Unmatched BL-6 events: temporal IoU with the best same-pair reference

| column | unmatched events | 0 | (0, 0.1] | (0.1, 0.2] | (0.2, 0.3) | >= 0.3 |
|---|---|---|---|---|---|---|
| C | 111 | 1 | 55 | 36 | 19 | 0 |
| C' | 120 | 3 | 60 | 36 | 20 | 1 |

#### References matched (N4) or overlapped by a same-pair episode: overlapping same-pair BL-6 episodes

| column | references | of which N4-matched | 1 episode | 2 | 3 | 4 or more | with 2 or more | N4-matched with 2 or more | episodes overlapping | of which linked by continuation_of_nk |
|---|---|---|---|---|---|---|---|---|---|---|
| C | 100 | 31 | 62 | 31 | 7 | 0 | 38 | 8 | 145 | 4 |
| C' | 97 | 21 | 62 | 28 | 6 | 1 | 35 | 6 | 140 | 5 |

#### EV-M1 / EV-M2 with "any temporal overlap, same pair" (descriptive, not the N4 metric)

| column | references found / assessable | recall (descriptive) | events supported / events | precision (descriptive) | N4 EV-M1 / EV-M2 (reported) |
|---|---|---|---|---|---|
| C | 100 / 282 | 0.35 | 141 / 142 | 0.99 | 0.11 / 0.22 |
| C' | 97 / 282 | 0.34 | 138 / 141 | 0.98 | 0.07 / 0.15 |

**Observations (descriptive, validation only).**
- **Almost every detector-path event is about a real interaction of the right pair.** Under "any temporal overlap, same pair", 141 of the 142 BL-6 events in C overlap one (0.99; C' 0.98). Under N4 only 31 match (EV-M2 0.22).
- **The events are much shorter than the interactions they overlap.** Half of the unmatched events in C (55 of 111) reach a temporal IoU of 0.1 or less, and none reaches 0.3.
- **Interactions are split into several episodes, which are rarely linked.**
  - 38 of the 100 references found by overlap are covered by two or more separate same-pair episodes.
  - Only 4 of the 145 overlapping episodes carry `continuation_of_nk`.
  - The cause was not diagnosed: fragmented forklift tracks (column C: 105 of 171 forklift tracks are fragments) are one candidate.
- **Recall is limited even under overlap.** 100 of the 282 references (0.35) are overlapped at all, in line with the forklift tracking coverage (CM-03 0.12).
- **These counts do not change N4.** The question is listed for the Architect in `docs/preregistration/v2_notes.md`.

## Stop
**D-47 decided (19 Nov 2026):** the pilot is accepted and AR-62 is accepted. **D-50 decided (19 Nov 2026):** the detector-path pilot is CLOSED as exploratory validation evidence. Columns A, B, C and C' stay as reported, and no further tracker variant is run on these cameras. CR-007, CR-029 and CR-026 go to the Architect as inputs for pre-registration v2 (`docs/preregistration/v2_notes.md`). **STOP.** The test partition stays reserved (D-37).
