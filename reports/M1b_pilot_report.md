# M1b detector-path pilot report — validation partition (T-25p)

**Status: complete for D-47 review; revised on the Owner's instruction of 19 Nov 2026 (report and evaluation code only; no stage re-run, nothing tuned).** All 206 pilot cameras ran through S2 → S5 and were evaluated; the frame-level check ran on both models.

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
- **Wording linter** (`rq1.export.report.lint`): one W4 hit, the disclaimer sentence "Nothing here is 'validated'" itself.

## Stop
**STOP (D-47).** The Owner and the Architect review the results, the limitations, AR-62 and the options in D-47. The test partition stays reserved (D-37).
