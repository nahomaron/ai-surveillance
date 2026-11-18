# M1a report — validation partition (T-21)

**Status: complete for G-M1a review.** SDG validation complete, including MR-01. SmartSpaces Warehouse_000 complete (base and full_camera; CM and GV). SmartSpaces EV-M waits for D-39. Position-error diagnosis done; the proposed range rule is CR-026 (not implemented). Every number below is **experimental**: synthetic data, oracle perception, validation partition only (D-36, D-37). Nothing here is "validated". Automated outputs are **candidate** events and **scenario counts**. No test-partition recording was processed.

Contract E-1.2.19. Pre-registration version 1 (`docs/preregistration_FROZEN.md`). Run code: commit `d800a5c` (phase 1, artifacts); evaluation code in `research/m1a/` (commit `59e31f0` and later). Results files: `research/m1a/results_sdg.json`, `research/m1a/results_smartspaces.json` (SmartSpaces evaluation at commit `7812832`, AR-60); diagnosis `research/m1a/position_diagnosis_{sdg,smartspaces}.json`, `research/m1a/position_cutoffs.json`.

## Plain-language summary (one page)

**What was run.** The 226 SDG validation camera recordings (24 simulated scenes, 10 s each, one worker and one forklift per scene) went through the measurement pipeline. Tracking was replaced by the simulator's own knowledge of where each object is in the image ("oracle perception"). Five rule configurations were compared, BL-2 to BL-6:
- BL-2 uses only image boxes.
- BL-3 uses floor distance.
- BL-4 adds a predicted-closest-approach rule.
- BL-5 adds time-to-collision and post-encroachment rules.
- BL-6 uses all of them plus evasive-action cues.

**What they were compared with.** The yardstick is not human labelling. It is BL-6 applied to the simulator's complete ground truth (Appendix T, T21). The comparison therefore shows how much is lost through what a camera can see and through each configuration's simpler rules. It says nothing about how well a real detector would do.

**How much the comparisons depend on the yardstick.** The BL-2 vs BL-3 contrast is the least reference-dependent comparison. BL-3 vs BL-6 is partly circular, because the reference is BL-6 itself (T21.5).

**Repeatability.** Re-running everything from the same code reproduced all 56,726 artifact IDs exactly (MR-01 = 1.0).

**Main findings (SDG, validation).**
1. **Image boxes alone perform poorly.**
   - BL-2 finds 54 % of the reference interactions (recall 0.54).
   - Only 47 % of its candidate events correspond to one (precision 0.47).
   - It produces about 300 false candidate events per hour of video.
   - This finding depends on the viewpoint. R1 (image boxes) and R2 (floor distance) disagree on 51 % of pair-frames on SDG but only 4 % on SmartSpaces (GV-06), and BL-2 has not yet been scored on SmartSpaces (D-39).
2. **Floor geometry fixes most of this.**
   - BL-3: recall 0.97, precision 0.93.
   - The BL-2 vs BL-3 gap (−0.43 in recall) is far outside its 95 % interval.
3. **With the prediction rule, results agree more closely with the BL-6 reference definition (T21.5).**
   - BL-4 and BL-6: recall 0.997, precision 0.95, about 27 false candidates per hour.
   - BL-3 to BL-6: +0.02 in recall and precision, as agreement with the BL-6 reference definition. The interval excludes zero when windows are resampled, but not when whole scenes are resampled.
4. **R4 and R5 change labels inside an interaction, not whether it is found.**
   - BL-5 equals BL-3, and BL-6 equals BL-4, on every interaction-level count.
   - R4 does add the "predicted conflict" (PC) label to 275 of 319 episodes (BL-5 against BL-3), and R5 raises the near-miss (NM) labels from 21 to 30 (BL-6 against BL-4).
   - The interaction-level comparison (label group G1) cannot see these changes by design.
5. **Camera geometry is the weak spot.**
   - Using the dataset calibration and the bottom of each box, object positions are typically within 1.5 m (95th percentile).
   - On eye-level cameras, 0.65 % of person positions are wildly wrong (tens of metres to about 5 km). They dominate the root-mean-square error (94 m for persons at eye level, 0.41 m from the ceiling).
   - The diagnosis (below) found the cause. Those are points where the visible box ends above the person's feet, on a camera ray only a few degrees below the horizon. There, a few pixels become tens of metres.
   - The pre-registered acceptance target (RMSE ≤ 0.25 m) applies to the test partition only and was not evaluated. These validation numbers suggest it will not be met as the metric is defined.
   - Speeds derived from these positions inherit the same outliers.
6. **Results depend on some thresholds.**
   - Changing the proximity distance d_p from 2 m to 3 m changes 66 of 319 episodes.
   - A ±10 % change in the assumed forklift length changes labels in 7–22 % of episodes.
   - Most other parameters change little.
7. **Some quantities could not be computed on these data** (positional uncertainty coverage, calibration perturbation), because the datasets supply no uncertainty.

**SmartSpaces (one simulated warehouse, 19 cameras, 190 windows of validation).**
- Only coverage (CM) and geometry (GV) results are available. The interaction metrics (EV-M) need a reference that would take about 200 hours to build there (decision D-39, open).
- **Coverage on the oracle path:** CM-01 = 1.00. CM-03 = 0.57 and CM-04 = 0.63: much of the time, objects that exist in the scene are not seen by a given camera. CM-05 = 0.017 (inferred frames without a reference-visible counterpart).
- **Candidate episodes (BL-6):** 574. Of these, 297 are labelled H, 466 PC, 158 NM and 116 undetermined (UD). These are scenario counts, not verified events.
- **Camera positions are unusable as they stand.**
  - The median error is 0.76 m, but 34 % of positions are more than 10 m off, and the root-mean-square error is about 12.5 km.
  - The forklift footprint prior is close to the simulator box (GV-04 bias −0.001 m, at simulator positions). The 1.87 × 1.13 m pallet trucks are measured with the 2.68 × 1.16 m forklift prior (bias −0.28 m).

**Why the camera positions fail (diagnosis, both datasets).** A position is found by following the camera ray through the bottom of the object's box down to the floor.
- **When the bottom of the box is the object's floor contact, this works.** Feet visible and box away from the image edge: median 0.30 m and P99 0.93 m on SmartSpaces. Points filled in from the simulator's 3D box ("predicted"): P99 1.6 m on both datasets.
- **It fails when the feet or wheels are hidden.** Then the visible box ends higher in the image, at something like a rack, a pallet or another person. On a ray only a few degrees below the horizon, a box bottom 10–50 pixels too high moves the point tens of metres away (SmartSpaces median 20 m).
- **The two datasets differ.**
  - SmartSpaces cameras look far across a large hall: 37 % of objects are more than 50 m away, and half of all rays meet the floor beyond 50 m.
  - SDG cameras look down at a small area, so only 0.3 % are affected. Those few points still carry 99.9 % of the SDG squared error.
- **Rays at or above the horizon (9,506 points) already get no position.** Rays that meet the floor far away do get one: there is no distance limit.
- **CR-026 asks the Architect for a rule.** A fixed range rule was not adopted (D-40): 50 m removes only wrong SDG positions, but also 239,502 correct SmartSpaces positions.
- **Two candidate signals were tested.**
  - *How many metres one pixel of error is worth at the foot point.* On SDG this separates almost perfectly: a 0.1 m/px limit catches 97 % of the errors above 10 m and loses 0.02 % of good points. On SmartSpaces, a limit catching 90 % also loses 18 % of good points.
  - *A second position from the head, assuming a 1.75 m height.* It is a weak check, because the head ray is even shallower than the foot ray.
- The Architect will write the rule for v2/M1b.
- Nothing was changed; the GV numbers are reported as computed.

**Decisions (G-M1a, 17 Nov 2026, D-40).** M1a is accepted as experimental validation evidence. D-39: SmartSpaces EV-M is not run in v1. AR-58, AR-60 and AR-59 items 2, 6 and 7 are accepted; AR-59 item 5 is revised (GV-04 now at simulator positions, below). CR-026 stays open with added diagnostics; the Architect will write the rule for v2/M1b.

## Technical report — SDG validation

### Scope and method
- **Population:** `m1a-sdg-validation` (V0 `art_wiaoelxnrzaqb2ii44esa47k3f`): a census of 226 windows (one 10 s window per camera), 24 leakage groups, strata `sdg:ceiling` (109) and `sdg:eye_level` (117), weight 1.
- **Perception:** ORACLE-S3 (T17–T20, g_max 15).
- **Geometry:** event configurations use `simulator_truth` positions. GV uses the `full_camera` run (oracle foot points through the dataset calibration).
- **References (T21):** BL-6 at base values on complete truth; G1 only; assessable per T21.3; the same reference IDs for every sweep (T21.4). `reference_class = rule_conformance`.
- **Interpretation (T21.5):** event metrics on the oracle path measure the effect of camera observability (T17–T20) and of the configuration's rules relative to BL-6, not perception.
- **Intervals:**
  - Target A (`frame_description`): stratified window bootstrap.
  - Target B (`new_session_performance`): cluster bootstrap over leakage groups.
  - Both use B 2000, seed 2026111402, 95 %.
  - Target B is the pre-registered headline for **test**; on validation both are shown, without a decision. No acceptance criterion is evaluated on validation.
- **Representation choices:** AR-59. Its review flags concern GV-04, GV-07 and GV-08, and the T21.1 reference evidence state.

### Results (generated by `research/m1a/report_tables.py` from `results_sdg.json`)

Cameras (windows) 226, leakage groups 24, strata sdg:ceiling, sdg:eye_level. References (T21): 306 (303 assessable, 3 unobservable_reference).

| Config | Episodes | Events | EV-M1 recall [A; B] | EV-M2 precision [A; B] | EV-M7 false alerts / h [A; B] | EV-M4 | EV-M11 | EV-M8 onset med / P90 (s) | mean IoU | matched / miss / false / dup |
|---|---|---|---|---|---|---|---|---|---|---|
| BL-2 | 351 | 351 | 0.541 [0.492, 0.594]; [0.465, 0.636] | 0.467 [0.418, 0.520]; [0.400, 0.533] | 298.1 [255.2, 342.6]; [236.7, 367.3] | 1.000 | 0.261 | 1.87 / 3.00 | 0.503 | 164 / 139 / 129 / 58 |
| BL-3 | 319 | 319 | 0.974 [0.955, 0.990]; [0.926, 1.000] | 0.925 [0.895, 0.952]; [0.873, 0.963] | 38.3 [23.9, 54.2]; [18.2, 67.3] | 1.000 | 0.075 | 0.37 / 0.67 | 0.883 | 295 / 8 / 0 / 24 |
| BL-4 | 319 | 319 | 0.997 [0.990, 1.000]; [0.990, 1.000] | 0.947 [0.922, 0.969]; [0.924, 0.968] | 27.1 [15.9, 39.9]; [16.5, 38.8] | 1.000 | 0.053 | 0.00 / 0.00 | 0.956 | 302 / 1 / 0 / 17 |
| BL-5 | 319 | 319 | 0.974 [0.955, 0.990]; [0.926, 1.000] | 0.925 [0.895, 0.952]; [0.873, 0.963] | 38.3 [23.9, 54.2]; [18.2, 67.3] | 1.000 | 0.075 | 0.37 / 0.67 | 0.883 | 295 / 8 / 0 / 24 |
| BL-6 | 319 | 319 | 0.997 [0.990, 1.000]; [0.990, 1.000] | 0.947 [0.922, 0.969]; [0.924, 0.968] | 27.1 [15.9, 39.9]; [16.5, 38.8] | 1.000 | 0.053 | 0.00 / 0.00 | 0.956 | 302 / 1 / 0 / 17 |

EV-M3 (G2 abstention; episodes form / support form): BL-2 0.798 / 0.354; BL-3 0.687 / 0.457; BL-4 0.687 / 0.488; BL-5 0.687 / 0.457; BL-6 0.683 / 0.486

By viewpoint stratum (EV-M1 / EV-M2 / EV-M7):

| Config | sdg:ceiling | sdg:eye_level |
|---|---|---|
| BL-2 | 0.526 / 0.526 / 241.1 | 0.557 / 0.421 / 351.3 |
| BL-3 | 0.968 / 0.968 / 16.5 | 0.980 / 0.885 / 58.5 |
| BL-4 | 1.000 / 1.000 / 0.0 | 0.993 / 0.897 / 52.4 |
| BL-5 | 0.968 / 0.968 / 16.5 | 0.980 / 0.885 / 58.5 |
| BL-6 | 1.000 / 1.000 / 0.0 | 0.993 / 0.897 / 52.4 |

Paired differences (T11.2), first minus second:

| Comparison | Difference | Target A 95 % | Target B 95 % |
|---|---|---|---|
| BL-2 - BL-3 EV-M1 | -0.432 | [-0.485, -0.380] | [-0.513, -0.335] |
| BL-2 - BL-3 EV-M2 | -0.458 | [-0.505, -0.407] | [-0.510, -0.402] |
| BL-2 - BL-3 EV-M7 | 259.8 | [220.1, 302.7] | [207.5, 318.3] |
| BL-3 - BL-6 EV-M1 | -0.023 | [-0.040, -0.007] | [-0.072, 0.000] |
| BL-3 - BL-6 EV-M2 | -0.022 | [-0.038, -0.008] | [-0.067, 0.000] |
| BL-3 - BL-6 EV-M7 | 11.2 | [3.2, 19.2] | [0.0, 34.8] |

Completeness (pooled ratio of sums; Target B interval):

| Metric | Value | Target B 95 % |
|---|---|---|
| CM-01 detected | 1.000 | [1.000, 1.000] |
| CM-01 detected_plus_inferred | 1.000 | [1.000, 1.000] |
| CM-02 detected | 1.000 | [1.000, 1.000] |
| CM-02 detected_plus_inferred | 1.000 | [1.000, 1.000] |
| CM-03 detected | 1.000 | [1.000, 1.000] |
| CM-03 detected_plus_inferred | 1.000 | [1.000, 1.000] |
| CM-04 detected | 1.000 | [1.000, 1.000] |
| CM-04 detected_plus_inferred | 1.000 | [1.000, 1.000] |
| CM-05 detected | 0.000 | [0.000, 0.000] |
| CM-05 detected_plus_inferred | 0.006 | [0.004, 0.008] |
| CM-06 detected | Σ\|AI − ref\| time in band per pair: mean 0.000 s, P95 0.000 s, max 0.000 s, 226 pairs | — |
| CM-06 detected_plus_inferred | Σ\|AI − ref\| time in band per pair: mean 0.000 s, P95 0.000 s, max 0.000 s, 226 pairs | — |
| CM-07 detected | intervals 0 / 1 / 2+ POWs: 0 / 352 / 0; pair-window fidelity 1.000 | — |
| CM-07 detected_plus_inferred | intervals 0 / 1 / 2+ POWs: 0 / 352 / 0; pair-window fidelity 1.000 | — |
| CM-08 detected | 0.000 | [0.000, 0.000] |
| CM-08 detected_plus_inferred | 0.000 | [0.000, 0.000] |
| CM-09 detected | — | — |
| CM-09 detected_plus_inferred | 0.000 | [0.000, 0.000] |
| CM-10 basis-independent | 0.000 | [0.000, 0.000] |

Geometry, full_camera run (226 cameras with a calibration).

GV-01 position error (m):

| class / evidence / viewpoint | n | RMSE [B] | P95 | bias x | bias y |
|---|---|---|---|---|---|
| all|all|all | 126365 | 44.844 [13.792, 69.001] | 1.467 | 0.164 | -0.635 |
| all|all|ceiling | 65024 | 0.843 [0.827, 0.859] | 1.465 | -0.149 | 0.007 |
| all|all|eye_level | 61341 | 64.359 [19.776, 98.973] | 1.477 | 0.497 | -1.315 |
| forklift|all|all | 65415 | 1.070 [1.055, 1.087] | 1.480 | -0.182 | 0.007 |
| forklift|all|ceiling | 32536 | 1.121 [1.098, 1.144] | 1.483 | -0.270 | 0.045 |
| forklift|all|eye_level | 32879 | 1.017 [1.000, 1.034] | 1.471 | -0.095 | -0.030 |
| forklift|detected|ceiling | 32536 | 1.121 [1.098, 1.144] | 1.483 | -0.270 | 0.045 |
| forklift|detected|eye_level | 32828 | 1.017 [0.999, 1.034] | 1.470 | -0.095 | -0.030 |
| forklift|inferred|eye_level | 51 | 1.390 [1.298, 1.471] | 1.719 | -0.119 | 0.204 |
| person|all|all | 60950 | 64.561 [19.867, 99.279] | 0.837 | 0.536 | -1.324 |
| person|all|ceiling | 32488 | 0.406 [0.357, 0.450] | 0.649 | -0.029 | -0.031 |
| person|all|eye_level | 28462 | 94.476 [29.023, 144.743] | 1.709 | 1.180 | -2.799 |
| person|detected|ceiling | 32351 | 0.405 [0.356, 0.450] | 0.648 | -0.027 | -0.032 |
| person|detected|eye_level | 28255 | 94.821 [29.171, 145.303] | 1.728 | 1.189 | -2.820 |
| person|inferred|ceiling | 137 | 0.499 [0.449, 0.552] | 0.669 | -0.336 | 0.167 |
| person|inferred|eye_level | 207 | 0.556 [0.496, 0.614] | 0.797 | -0.060 | 0.074 |

GV-04 (m), **revised under D-40 item 4 (AR-59 item 5)**: at simulator positions, prior footprint minus simulator 3D-box footprint, on the measured pair-frames of the simulator_truth run (`research/m1a/gv_revised_sdg.json`). The earlier values, at full_camera positions (bias 0.0003 m, n 58,635), are superseded.

| stratum | n | bias [B] | RMSE | SD | P5 | P95 |
|---|---|---|---|---|---|---|
| 3.03x1.13|all | 59246 | 0.0004 [0.0003, 0.0004] | 0.0005 | 0.0003 | -0.0001 | 0.0006 |
| 3.03x1.13|detected | 58898 | 0.0004 [0.0003, 0.0004] | 0.0005 | 0.0003 | -0.0001 | 0.0006 |
| 3.03x1.13|inferred | 348 | 0.0001 [0.0000, 0.0002] | 0.0003 | 0.0003 | -0.0001 | 0.0006 |

GV-07 (m/s):

| stratum | n | bias [B] | RMSE | SD | P5 | P95 |
|---|---|---|---|---|---|---|
| w_v=0.33|all|all | 126343 | 4.3673 [1.7099, 8.0463] | 188.8543 | 188.8045 | -0.5305 | 1.1327 |
| w_v=0.33|forklift|all | 65415 | -0.0326 [-0.0461, -0.0191] | 0.3412 | 0.3397 | -0.5414 | 0.5493 |
| w_v=0.33|forklift|detected | 65364 | -0.0328 [-0.0464, -0.0192] | 0.3405 | 0.3390 | -0.5411 | 0.5483 |
| w_v=0.33|forklift|inferred | 51 | 0.1904 [-0.1219, 0.5652] | 0.8426 | 0.8290 | -0.6445 | 2.1433 |
| w_v=0.33|person|all | 60928 | 9.0914 [3.5804, 16.6546] | 271.9528 | 271.8031 | -0.5050 | 2.2601 |
| w_v=0.33|person|detected | 60590 | 8.9330 [3.3501, 16.5853] | 272.5847 | 272.4405 | -0.5054 | 2.0594 |
| w_v=0.33|person|inferred | 338 | 37.4859 [18.6497, 61.9451] | 110.8165 | 104.4384 | -0.3418 | 230.2550 |
| w_v=0.5|all|all | 126321 | 3.2250 [1.2126, 6.1848] | 127.1590 | 127.1186 | -0.5042 | 0.9318 |
| w_v=0.5|forklift|all | 65401 | -0.0493 [-0.0617, -0.0372] | 0.3230 | 0.3192 | -0.5562 | 0.5404 |
| w_v=0.5|forklift|detected | 65350 | -0.0495 [-0.0618, -0.0372] | 0.3223 | 0.3185 | -0.5561 | 0.5392 |
| w_v=0.5|forklift|inferred | 51 | 0.1431 [-0.1296, 0.4494] | 0.8135 | 0.8088 | -0.6072 | 2.0075 |
| w_v=0.5|person|all | 60920 | 6.7402 [2.5925, 12.7844] | 183.1067 | 182.9842 | -0.3698 | 2.0126 |
| w_v=0.5|person|detected | 60582 | 6.5904 [2.4189, 12.7353] | 183.4998 | 183.3829 | -0.3691 | 1.8350 |
| w_v=0.5|person|inferred | 338 | 33.5987 [14.5987, 52.4303] | 87.7480 | 81.1808 | -0.6416 | 302.2586 |
| w_v=1.0|all|all | 126269 | 2.1008 [0.7180, 4.1140] | 66.0327 | 65.9995 | -0.4546 | 0.6648 |
| w_v=1.0|forklift|all | 65376 | -0.0773 [-0.0883, -0.0665] | 0.2828 | 0.2721 | -0.5210 | 0.4250 |
| w_v=1.0|forklift|detected | 65328 | -0.0773 [-0.0882, -0.0665] | 0.2828 | 0.2720 | -0.5210 | 0.4247 |
| w_v=1.0|forklift|inferred | 48 | -0.0880 [-0.2068, 0.0056] | 0.3568 | 0.3494 | -0.6277 | 0.5605 |
| w_v=1.0|person|all | 60893 | 4.4392 [1.5740, 8.5588] | 95.0871 | 94.9842 | -0.2106 | 1.5283 |
| w_v=1.0|person|detected | 60565 | 4.4040 [1.5191, 8.5637] | 95.3171 | 95.2161 | -0.2095 | 1.4413 |
| w_v=1.0|person|inferred | 328 | 10.9293 [3.8313, 17.8464] | 30.8699 | 28.9145 | -0.3785 | 62.8706 |

GV-08 (m):

| stratum | n | bias [B] | RMSE | SD | P5 | P95 |
|---|---|---|---|---|---|---|
| all | 44468 | 0.5987 [0.4254, 0.8065] | 12.6101 | 12.5960 | -0.5732 | 1.6346 |
| detected | 44184 | 0.6046 [0.4297, 0.8139] | 12.6504 | 12.6361 | -0.5599 | 1.6400 |
| inferred | 284 | -0.3135 [-0.4632, -0.0998] | 0.8503 | 0.7918 | -1.9126 | 0.3234 |

GV-08 against simulator truth (m), **added under D-40 item 4 (AR-59 item 7)**. Full_camera constant-velocity predicted minimum minus the realised minimum of the simulator_truth clearance series (simulator positions, prior footprint) on the same tracks and frames (`gv_revised_sdg.json`). The same-run GV-08 above is kept.

| stratum | n | bias [B] | RMSE | SD | P5 | P95 |
|---|---|---|---|---|---|---|
| all | 44468 | 0.6945 [0.3998, 1.0415] | 26.5770 | 26.5682 | -1.1202 | 2.1874 |
| detected | 44184 | 0.6997 [0.4026, 1.0498] | 26.6622 | 26.6533 | -1.1194 | 2.1962 |
| inferred | 284 | -0.1220 [-0.2596, -0.0146] | 0.7512 | 0.7425 | -1.3236 | 1.2850 |

GV-05 / MR-11: not computable: the full_camera positions carry no positional covariance (pos_cov_m2 null, not_supplied). GV-06: Spearman ρ(image_gap_norm, clearance_m) = 0.150 over 58635 pair-frames; R1-P vs R2-P disagreement 0.513 (30093 of 58635).

Sweeps (one at a time; totals over cameras; Δ against base):

| Grid point | BL-2 episodes (Δ) / EV-M1 | BL-3 episodes (Δ) / EV-M1 | BL-4 episodes (Δ) / EV-M1 | BL-5 episodes (Δ) / EV-M1 | BL-6 episodes (Δ) / EV-M1 |
|---|---|---|---|---|---|
| d_nm=0.3 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| d_nm=1.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| d_p=1.5 | 351 (+0) / 0.541 | 301 (-18) / 0.842 | 343 (+24) / 0.901 | 301 (-18) / 0.842 | 343 (+24) / 0.901 |
| d_p=3.0 | 351 (+0) / 0.541 | 253 (-66) / 0.782 | 253 (-66) / 0.782 | 253 (-66) / 0.782 | 253 (-66) / 0.782 |
| d_pc=0.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 326 (+7) / 0.997 | 319 (+0) / 0.974 | 326 (+7) / 0.997 |
| d_pc=1.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 317 (-2) / 0.970 | 319 (+0) / 0.974 | 317 (-2) / 0.970 |
| e_acc=0.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| e_acc=2.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| e_dec=1.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| e_dec=4.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| e_turn=0.75 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| e_turn=3.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| fork_length_scale=0.9 | 351 (+0) / 0.541 | 327 (+8) / 0.884 | 328 (+9) / 0.911 | 327 (+8) / 0.884 | 328 (+9) / 0.911 |
| fork_length_scale=1.1 | 351 (+0) / 0.541 | 328 (+9) / 0.944 | 328 (+9) / 0.967 | 328 (+9) / 0.944 | 328 (+9) / 0.967 |
| fork_width_scale=0.9 | 351 (+0) / 0.541 | 311 (-8) / 0.944 | 311 (-8) / 0.967 | 311 (-8) / 0.944 | 311 (-8) / 0.967 |
| fork_width_scale=1.1 | 351 (+0) / 0.541 | 325 (+6) / 0.947 | 325 (+6) / 0.970 | 325 (+6) / 0.947 | 325 (+6) / 0.970 |
| g_max=30 | 341 (-10) / 0.551 | 309 (-10) / 0.974 | 309 (-10) / 0.997 | 309 (-10) / 0.974 | 309 (-10) / 0.997 |
| g_max=5 | 371 (+20) / 0.521 | 337 (+18) / 0.974 | 338 (+19) / 0.997 | 337 (+18) / 0.974 | 338 (+19) / 0.997 |
| g_max=60 | 334 (-17) / 0.571 | 303 (-16) / 0.974 | 303 (-16) / 0.997 | 303 (-16) / 0.974 | 303 (-16) / 0.997 |
| k_img=0.03 | 347 (-4) / 0.531 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| k_img=0.08 | 345 (-6) / 0.561 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| m_gap=10 | 328 (-23) / 0.564 | 301 (-18) / 0.917 | 291 (-28) / 0.914 | 301 (-18) / 0.917 | 291 (-28) / 0.914 |
| m_gap=3 | 358 (+7) / 0.538 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| person_radius_m=0.25 | 351 (+0) / 0.541 | 318 (-1) / 0.911 | 319 (+0) / 0.937 | 318 (-1) / 0.911 | 319 (+0) / 0.937 |
| person_radius_m=0.35 | 351 (+0) / 0.541 | 318 (-1) / 0.944 | 318 (-1) / 0.967 | 318 (-1) / 0.944 | 318 (-1) / 0.967 |
| pet_max=0.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| pet_max=1.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| t_min=0.1 | 364 (+13) / 0.541 | 326 (+7) / 0.974 | 319 (+0) / 0.997 | 326 (+7) / 0.974 | 319 (+0) / 0.997 |
| t_min=0.5 | 314 (-37) / 0.541 | 308 (-11) / 0.944 | 310 (-9) / 0.970 | 308 (-11) / 0.944 | 310 (-9) / 0.970 |
| tau=3.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 309 (-10) / 0.970 | 319 (+0) / 0.997 | 309 (-10) / 0.970 |
| tau=4.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 306 (-13) / 0.957 | 315 (-4) / 0.960 | 298 (-21) / 0.934 |
| ttc_max=1.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| ttc_max=2.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| v_min=0.2 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| v_min=0.4 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| w_e=0.5 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 319 (+0) / 0.997 | 319 (+0) / 0.974 | 319 (+0) / 0.997 |
| w_v=0.33 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 327 (+8) / 0.997 | 319 (+0) / 0.974 | 327 (+8) / 0.997 |
| w_v=1.0 | 351 (+0) / 0.541 | 319 (+0) / 0.974 | 302 (-17) / 0.947 | 319 (+0) / 0.974 | 302 (-17) / 0.947 |

MR-08 mean label_stability_frac (share of episodes fully stable):

| Family | BL-2 | BL-3 | BL-4 | BL-5 | BL-6 |
|---|---|---|---|---|---|
| all | 0.990 (0.735) | 0.968 (0.577) | 0.962 (0.567) | 0.957 (0.520) | 0.962 (0.586) |
| d_nm | 1.000 (1.000) | 0.956 (0.912) | 0.961 (0.922) | 0.956 (0.912) | 0.995 (0.991) |
| d_p | 1.000 (1.000) | 0.803 (0.727) | 0.815 (0.718) | 0.795 (0.712) | 0.818 (0.724) |
| d_pc | 1.000 (1.000) | 1.000 (1.000) | 0.961 (0.922) | 1.000 (1.000) | 0.961 (0.922) |
| e_acc | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 0.975 (0.950) |
| e_dec | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) |
| e_turn | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) |
| fork_length_scale | 0.976 (0.966) | 0.886 (0.818) | 0.887 (0.828) | 0.848 (0.752) | 0.903 (0.859) |
| fork_width_scale | 1.000 (1.000) | 0.951 (0.931) | 0.948 (0.925) | 0.936 (0.900) | 0.948 (0.925) |
| g_max | 0.979 (0.954) | 0.984 (0.969) | 0.981 (0.962) | 0.978 (0.950) | 0.981 (0.962) |
| k_img | 0.966 (0.932) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) |
| m_gap | 0.976 (0.952) | 0.972 (0.944) | 0.961 (0.922) | 0.972 (0.944) | 0.961 (0.922) |
| person_radius_m | 1.000 (1.000) | 0.933 (0.893) | 0.929 (0.887) | 0.917 (0.862) | 0.934 (0.897) |
| pet_max | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 0.986 (0.972) | 1.000 (1.000) |
| t_min | 0.947 (0.895) | 0.983 (0.966) | 0.986 (0.972) | 0.983 (0.966) | 0.986 (0.972) |
| tau | 1.000 (1.000) | 1.000 (1.000) | 0.962 (0.956) | 0.933 (0.922) | 0.945 (0.922) |
| ttc_max | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) | 1.000 (1.000) |
| v_min | 1.000 (1.000) | 0.975 (0.950) | 0.975 (0.950) | 0.975 (0.950) | 0.975 (0.950) |
| w_e | 0.952 (0.952) | 0.931 (0.931) | 0.931 (0.931) | 0.931 (0.931) | 0.912 (0.912) |
| w_v | 1.000 (1.000) | 0.986 (0.972) | 0.962 (0.925) | 0.959 (0.918) | 0.953 (0.906) |

GV-03 footprint sweep: label flip rate per configuration; Δclearance (m):

- fork_length_scale=0.9: BL-2 0.023, BL-3 0.141, BL-4 0.132, BL-5 0.216, BL-6 0.122; Δclearance bias 0.0989, P5 0.0000, P95 0.1515
- fork_length_scale=1.1: BL-2 0.026, BL-3 0.088, BL-4 0.094, BL-5 0.088, BL-6 0.072; Δclearance bias -0.0949, P5 -0.1515, P95 0.0000
- fork_width_scale=0.9: BL-2 0.000, BL-3 0.031, BL-4 0.034, BL-5 0.060, BL-6 0.034; Δclearance bias 0.0266, P5 0.0000, P95 0.0565
- fork_width_scale=1.1: BL-2 0.000, BL-3 0.066, BL-4 0.069, BL-5 0.069, BL-6 0.069; Δclearance bias -0.0260, P5 -0.0565, P95 0.0000

MR-10: not computable: no calibration covariance is supplied for the dataset calibrations (calibration_tier supplied_unvalidated).

### Per-label agreement with the BL-6 reference definition (descriptive; D-40 item 5)

Source: `research/m1a/ev_by_label_sdg.json` (`research/m1a/ev_by_label.py`).
- **Method:** for each label L, the references carrying L are matched with the system candidate events carrying L. The matcher is the same (pair condition, iou_m 0.3, N4 assignment).
- **Measures:** recall_L = matched / assessable references with L; precision_L = matched / events with L.
- **Status:** descriptive, not pre-registered, no decision.
- **Intervals:** Target A only. They are not computable (—) when resamples contain no reference with the label (O: 9 references).
- **Reading (T21.5):** values measure agreement with the BL-6 reference definition, not correctness.

| Config | O recall | O precision | H recall | H precision | PC recall | PC precision |
|---|---|---|---|---|---|---|
| BL-2 | 0.222 (2/9) | 0.006 [0.000, 0.015] (2/351) | 0.000 (0/294) | — (0/0) | 0.000 (0/278) | — (0/0) |
| BL-3 | 1.000 (9/9) | 1.000 (9/9) | 0.973 [0.954, 0.990] (286/294) | 0.923 [0.892, 0.951] (286/310) | 0.000 (0/278) | — (0/0) |
| BL-4 | 1.000 (9/9) | 1.000 (9/9) | 0.997 [0.989, 1.000] (293/294) | 0.945 [0.919, 0.968] (293/310) | 0.996 [0.989, 1.000] (277/278) | 0.945 [0.920, 0.969] (277/293) |
| BL-5 | 1.000 (9/9) | 1.000 (9/9) | 0.973 [0.954, 0.990] (286/294) | 0.923 [0.892, 0.951] (286/310) | 0.932 [0.903, 0.959] (259/278) | 0.942 [0.913, 0.969] (259/275) |
| BL-6 | 1.000 (9/9) | 1.000 (9/9) | 0.997 [0.989, 1.000] (293/294) | 0.945 [0.919, 0.968] (293/310) | 0.996 [0.989, 1.000] (277/278) | 0.945 [0.920, 0.969] (277/293) |

- **BL-2:** labels every candidate O and never H or PC. Its H and PC recall is 0 by construction, and its 351 O events match 2 of the 9 O references.
- **PC:** appears only with R4 (BL-4, BL-5, BL-6). BL-5's PC agreement (0.93) is below BL-4/BL-6 (0.996).
- Most references carry H (294 of 303 assessable) and PC (278); O is rare (9).

### Observations (descriptive, validation only)

- **EV-M4 = 1, and EV-M3 is high.**
  - EV-M3 is G2 abstention (about 0.69 of episodes).
  - No G2 reference exists on synthetic data (T21.2). G1 is never abstained (T10.7(a)), so EV-M4 = 1 − EV-M5 = 1.
- **The three unobservable references** (T21.3) are reported, not scored.
- **CM on the oracle path is 1 or 0 by construction** for CM-01–CM-04, CM-08 and CM-10:
  - The oracle tracks are the reference-visible objects.
  - CM-05 (detected + inferred) 0.006 is the share of predicted (inferred) POW frames that have no reference-visible counterpart.
  - CM-09 = 0 because predicted oracle points have no reference box (T17.6).
- **GV-04 ≈ 0.0004 m (revised, at simulator positions).** The SDG prior footprint equals the simulator box (3.03 × 1.13 m). The residual is the rounding of the box dimensions read from the 3D corners.
- **GV-08 against simulator truth:** bias 0.69 m, P5 −1.12 m, P95 2.19 m. The RMSE (26.6 m) comes from the predictions, which use the full_camera positions and their outliers.
- **GV-01 extremes:**
  - 816 object-frames (0.65 %) exceed 5 m. All are persons on eye-level cameras, in 44 cameras.
  - Cause (position-error diagnosis below): shallow foot rays combined with a visible box that ends above the 3D box bottom.
    - All 480 SDG positions on rays less than 2° below the horizon, and all 386 beyond 50 m, are more than 10 m off.
    - Tracked points whose box ends more than 200 px above the 3D box bottom have a median error of 2.9 m and P90 100 m.
  - Forklift positions: RMSE about 1.0–1.1 m, P95 1.48 m, with no extremes.
- **GV-07:** forklift speed error RMSE 0.28–0.34 m/s, decreasing with w_v. The person values carry the GV-01 extremes.
- **Label counts** (episodes, all 226 cameras): BL-3 H 310 / PC 0 / NM 24; BL-4 H 310 / PC 293 / NM 21; BL-5 H 310 / PC 275 / NM 24; BL-6 H 310 / PC 293 / NM 30. From BL-3 on, every configuration puts the same episodes in G1, so EV-M (G1) cannot separate them.
- **GV-06:** Spearman ρ between normalised image gap and floor clearance is 0.15. R1-P and R2-P disagree on 51 % of pair-frames. This agrees with the BL-2 vs BL-3 gap.

### Not run or not computable in v1
- **SDG:** GV-02 (no held-out floor points); GV-05 / MR-11 and MR-10 (no covariance supplied); MR-02 to MR-07 (outside M1a).
- **SmartSpaces:** sweeps (D-38 A.3); EV-M and CM-02 / CM-06 (D-39).
- **MR-01 (criterion C1-MR-01, registered for the M1a run):** **1.0** on SDG validation. A second run from the same commit (`d800a5c`) reproduced every artifact ID of all four units on all 226 cameras: 904 unit records, 56,726 artifact IDs, 0 differences (`research/m1a/mr01_sdg.json`). SmartSpaces MR-01: not run (one run within the 12 h bound).

### Engineering record
- **AR-58**, D-38 A.1 acceptance met on all 118,534 SDG validation pair-frames (both geometries):
  - pet_pred_s within 9.35e-7 s;
  - every flag, label and episode boundary identical.
- **Runtime:** SDG phase 1 took 62 min for 226 cameras (2 workers); evaluation took about 30 min.

## Technical report — SmartSpaces validation (Warehouse_000)

### Scope and method
- **Population:** `m1a-smartspaces_000-validation` (V0 `art_rvcgsenmz4onjnq5jbfu4n6wax`): 190 windows over 19 cameras (9,000 frames each), one leakage group (Warehouse_000; D-34 B.10), stratum `smartspaces_000:other`.
- **Perception:** ORACLE-S3 (T17–T20, g_max 15). Classes person, forklift, pallet_truck (D-22). Pallet trucks use the forklift prior 2.68 × 1.16 m.
- **Runs:** base (S3, S4 simulator_truth, S5 BL-2..BL-6) and full_camera (S4 + S5), code `ddfac38`. Evaluation at `7812832` (AR-60: speed only, outputs identical).
- **Not run:** EV-M1–EV-M8, CM-02 and CM-06 (no T21 reference; D-39 open), sweeps (D-38 A.3), and MR-01 (one run only). Also GV-07 at w_v 0.33 / 1.0: the simulator-side speeds at those values come from the sweeps.
- **Intervals:** there is one leakage group, so Target B intervals are degenerate and not informative. Target A resamples the 190 windows.

### Results (`research/m1a/results_smartspaces.json`)

**Completeness** (oracle path; detected = detected only, +inf = detected + inferred; Target A 95 % interval):

| metric | detected | +inf |
|---|---|---|
| CM-01 | 1.000 [1.000, 1.000] | 1.000 |
| CM-03 | 0.567 [0.557, 0.577] | 0.567 |
| CM-04 | 0.632 [0.602, 0.665] | 0.632 |
| CM-05 | 0.000 | 0.017 [0.015, 0.021] |
| CM-07 (pair-window fidelity) | 0.610 (27,300 one-to-one, 17,475 none, 0 several) | same |
| CM-08 | 0.000 | 0.000 |
| CM-09 | not computable (denominator 0) | 0.000 |
| CM-10 | 0.000 | — |

**Scenario counts** (episodes; all 19 cameras; candidates, not verified):

| config | episodes | O | H | PC | NM | UD | IE |
|---|---|---|---|---|---|---|---|
| BL-2 | 1,692 | 1,692 | 0 | 0 | 0 | 0 | 211 |
| BL-3 | 427 | 131 | 296 | 0 | 42 | 107 | 32 |
| BL-4 | 564 | 52 | 297 | 456 | 78 | 116 | 40 |
| BL-5 | 484 | 102 | 297 | 255 | 61 | 115 | 35 |
| BL-6 | 574 | 52 | 297 | 466 | 158 | 116 | 50 |

**Geometry (full_camera):**

| GV-01 | n | RMSE | P95 | bias x / y |
|---|---|---|---|---|
| person, detected | 1,407,444 | 53.0 m | 99.6 m | 4.66 / −5.32 m |
| person, inferred | 15,225 | 0.88 m | 1.32 m | −0.06 / 0.29 m |
| forklift, detected | 272,221 | 33,382 m | 103 m | −134 / −355 m |
| forklift, inferred | 1,761 | 0.68 m | 1.18 m | −0.12 / 0.17 m |
| pallet truck, detected | 236,396 | 16.7 m | 45.8 m | −0.37 / −0.78 m |
| pallet truck, inferred | 2,123 | 0.82 m | 1.12 m | 0.15 / 0.03 m |

- **GV-04** (revised under D-40 item 4: at simulator positions, prior footprint − simulator box footprint; `research/m1a/gv_revised_smartspaces.json`): 2.68 × 1.16 m boxes bias -0.0009 m (n 360,398); 1.87 × 1.13 m boxes (pallet trucks under the forklift prior) bias -0.279 m, P5 -0.40, P95 -0.03 m (n 2,833,391). The earlier values at full_camera positions (−0.0007 m and −0.281 m) are superseded.
- **GV-05 / MR-11:** not computable (no positional covariance supplied).
- **GV-06:** Spearman ρ 0.35 between normalised image gap and floor clearance; R1-P and R2-P disagree on 4.0 % of 3,137,274 pair-frames.
- **GV-07** (w_v 0.5, speed minus simulator speed): RMSE person 60.6 m/s, pallet truck 15.6 m/s, forklift 76,472 m/s. The GV-01 outliers carry over into speed.
- **GV-08** (predicted minus realised minimum clearance): bias 54.1 m, P5 −11.4 m, P95 30.7 m, RMSE 12,249 m. Against simulator truth (D-40 item 4): bias 67.6 m, P5 -11.1 m, P95 83.0 m, RMSE 12,250 m (n 2,511,500); the predictions carry the full_camera outliers.
- **Intervals:** all GV intervals on SmartSpaces are degenerate (one stratum, one leakage group, summed per cluster).

### Observations (descriptive, validation only)
- **CM-03 and CM-04 are well below 1.** SmartSpaces truth is scene-wide, so each camera's truth holds every object in the warehouse, and most of them are out of that camera's view at any time. CM-08 = CM-10 = 0 and CM-01 = 1 hold by construction on the oracle path, as on SDG.
- **BL-2 vs BL-3:** BL-2 opens 1,692 episodes against 427 for BL-3, although R1-P and R2-P disagree on only 4 % of all pair-frames (GV-06). Without a reference (D-39), these counts cannot be scored.
- **The full_camera geometry fails on detected points and works on inferred ones.** The next section explains why.

## Position-error diagnosis (validation, SDG and SmartSpaces; Architect, 17 Nov 2026)

**Method.**
- The script `research/m1a/position_diagnosis.py` covers every full_camera S4 object_state row whose S3 point is tracked or predicted. It reads stored statistics only: no pixel is decoded and nothing is changed.
- Each position is recomputed from the foot point and the calibration. All 2,071,041 recomputed positions equal the stored ones (0 mismatches).
- The error statistics are on the GV-01 population: a numeric position and a truth pose on that frame. SDG has 126,365 such points, SmartSpaces 1,935,170.
- The rule evidence is in `research/m1a/position_cutoffs.py`.
- **Definitions:**
  - **Bottom-edge offset:** the bottom edge of the image-clipped reprojected 3D box minus the bottom edge of the visible box, in CF-IMG pixels, on tracked points.
  - **Border:** the box is within 1 px of an image edge.
  - **Ray angle:** the foot ray's angle below the horizon.
  - **Range:** the horizontal distance from the camera centre to where the ray meets the floor.

**1. Point state** (median / P90 / P99 / share > 2 m / share > 10 m):

| | SDG | SmartSpaces |
|---|---|---|
| tracked | 0.56 / 1.40 / 2.60 m / 1.3 % / 0.49 % (n 125,970) | 0.76 / 59.2 / 210 m / 44 % / 35 % (n 1,916,061) |
| predicted | 0.53 / 1.05 / 1.71 m / 0 / 0 (n 395) | 0.78 / 1.16 / 1.58 m / 0.35 % / 0 (n 19,109) |

**2. Class and viewpoint** (tracked; median / P99 / share > 10 m):
- SDG person ceiling 0.20 / 1.85 m / 0. SDG person eye_level 0.17 / 85.1 m / 2.2 %.
- SDG forklift ceiling 1.12 / 1.53 m / 0. SDG forklift eye_level 0.99 / 1.56 m / 0.
- The forklift medians near 1 m reflect where the foot point sits: the bottom-centre of the box is not the footprint centre.
- SmartSpaces (`other`): person 0.50 / 207 m / 33 %; forklift 6.70 / 220 m / 45 %; pallet truck 0.72 / 64.6 m / 31 %.
- Predicted points of every class: P99 ≤ 2.44 m, none above 10 m.

**3. Bottom-edge offset** (tracked; median / P99 / share > 10 m):

| offset | SDG | SmartSpaces |
|---|---|---|
| −2 to 2 px | 0.52 / 1.99 m / 0 (7,234) | 0.31 / 2.36 m / 0 (492,362) |
| 2–10 px | 0.31 / 1.44 m / 0 (17,671) | 0.26 / 16.0 m / 3.3 % (531,789) |
| 10–50 px | 0.57 / 1.51 m / 0 (73,063) | 20.3 / 249 m / 68 % (671,750) |
| 50–200 px | 0.74 / 4.18 m / 0.5 % (26,404) | 33.9 / 259 m / 86 % (217,546) |
| > 200 px | 2.89 / 761 m / 30 % (1,597) | 9.4 / 33.5 m / 37 % (2,614) |

- A person's 3D box extends beyond the body, so its lowest projected corner usually lies a few pixels below the feet even when they are visible. Offsets of a few pixels therefore do not mean the feet are hidden.
- On steep SDG views a 10–50 px offset costs little; on SmartSpaces' shallow views it costs tens of metres.
- Tracked points with an offset under 2 px and not on a border: SmartSpaces median 0.30 m, P99 0.93 m (469,218 points); SDG 0.25 m / 0.41 m (912).

**4. Box touching an image border** (tracked; median / P99 / share > 10 m): SDG touching 0.83 / 2.85 m / 0.55 %, not touching 0.26 / 2.45 m / 0.42 %. SmartSpaces touching 0.99 / 82.9 m / 11 %, not touching 0.76 / 212 m / 36 %. Border contact is not the driver.

**5. Ray geometry at the foot point:**

| | SDG | SmartSpaces |
|---|---|---|
| rays at or above the horizon (floor met behind the camera) | 611 | 8,895 |
| parallel to the floor | 0 | 0 |
| met in front beyond 50 m / 100 m / 1 km | 386 / 230 / 17 | 974,217 / 303,325 / 493 |
| met in front less than 1° below the horizon | 350 | 136,944 |

- **By ray angle** (median error): SDG below 1° 100 m, 1–2° 36 m, 2–5° 5.4 m, 5° and above ≤ 0.9 m. SmartSpaces below 1° 111 m, 1–2° 35 m, 2–5° 1.0 m, 5–10° 0.28 m. No SmartSpaces ray is steeper than 45°.
- All rays at or above the horizon are tracked points.
- SDG: positions beyond 50 m are 0.31 % of GV-01 points and carry 99.9 % of the squared error. RMSE is 44.8 m with them and 1.34 m without.

**6. Distance from the camera to the true position** (median / P99 / share > 10 m):
- SDG: every object is within 20 m. 0–5 m 0.52 / 2.31 m / 0.46 %; 5–10 m 0.56 / 2.83 m / 0.52 %; 10–20 m 0.75 / 2.23 m / 0.37 %.
- SmartSpaces: 0–5 m 1.46 / 3.84 m / 0; 5–10 m 0.24 / 9.5 m / 0.9 %; 10–20 m 0.24 / 32.8 m / 3.7 %; 20–50 m 0.50 / 98.2 m / 27 %; over 50 m 15.5 / 265 m / 56 % (725,201 points, 37 %).

**How the code handles rays that do not meet the floor in front of the camera** (`geometry.full_camera_to_floor`, `builder._object_states`):
- A ray parallel to the floor (|d_z| < 1e-12), or one meeting it at s ≤ 0 (behind the camera), returns None.
- The builder then writes x_m = y_m = null with null reason `not_observable`. In this run that is 611 SDG and 8,895 SmartSpaces points, all at or above the horizon.
- **There is no range limit.** Every ray below the horizon gives a numeric position; 17 SDG and 493 SmartSpaces rays meet the floor more than 1 km away.

**Conclusion.**
- The large errors come from tracked points whose visible box ends above the object's floor contact, on shallow rays where a pixel corresponds to metres. This is what happens when the visible box is used as the foot point.
- Rays at or above the horizon are already null. Rays that meet the floor far away produce numbers.
- **CR-026** proposes a range condition (not implemented). The evidence there shows that one fixed range does not suit both datasets, and that hidden feet at moderate range are a separate question.
- Status: experimental (synthetic, oracle perception, validation only).

### Further diagnostics for CR-026 (D-40 item 6)
Source: `research/m1a/position_sensitivity.py` → `research/m1a/position_sensitivity_{sdg,smartspaces}.json`. Validation only, statistics only; nothing in the pipeline changed. The full tables are in CR-026.
- **(a) Pixel sensitivity** (largest singular value of the floor-intersection Jacobian, m per px of foot-point error):
  - SDG median 0.009, P99 0.07 m/px. SmartSpaces median 0.45, P99 19 m/px.
  - SDG errors stay small below 0.1 m/px (median ≤ 0.62 m) and grow steeply above it (median 96 m at ≥ 1 m/px).
  - On SmartSpaces, a limit of 0.1 / 0.2 / 0.5 m/px catches 99.9 / 99.5 / 90.3 % of errors > 10 m but nulls 66.8 / 47.3 / 18.1 % of the points that are within 1 m. On SDG, 0.1 m/px catches 96.8 % for 0.02 %.
- **(b) Height consistency** (persons; head ray at H = 1.75 m, also 1.6 and 1.9 m):
  - At a 2 m cut-off it flags 5.6 % of SDG persons with bottom offset ≤ 2 px against 28.4 % with > 10 px. On SmartSpaces it flags 72.9 % against 88.0 %.
  - The head-based estimate itself has a median error of 0.47 m on SDG and 3.6 m on SmartSpaces.
  - Not a usable stand-alone rule on these data.

## Stop
**G-M1a decided (D-40, 17 Nov 2026):** M1a is accepted as experimental validation evidence. Open: CR-026 (rule for v2/M1b, Architect). Test partition reserved (D-37). M1b feasibility: see `research/m1b/feasibility.md`.
