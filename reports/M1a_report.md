# M1a report — validation partition (T-21)

**Status: INTERIM.** SDG validation complete, including MR-01. SmartSpaces Warehouse_000 base and full_camera runs in progress. SmartSpaces EV-M waits for D-39. Every number below is **experimental**: synthetic data, oracle perception, validation partition only (D-36, D-37). Nothing here is "validated". Automated outputs are **candidate** events and **scenario counts**. No test-partition recording was processed.

Contract E-1.2.19. Pre-registration version 1 (`docs/preregistration_FROZEN.md`). Run code: commit `d800a5c` (phase 1, artifacts); evaluation code in `research/m1a/` (commit `59e31f0` and later). Results file: `research/m1a/results_sdg.json`.

## Plain-language summary (one page)

**What was run.** The 226 SDG validation camera recordings (24 simulated scenes, 10 s each, one worker and one forklift per scene) went through the measurement pipeline. Tracking was replaced by the simulator's own knowledge of where each object is in the image ("oracle perception"). Five rule configurations were compared, BL-2 to BL-6:
- BL-2 uses only image boxes.
- BL-3 uses floor distance.
- BL-4 adds a predicted-closest-approach rule.
- BL-5 adds time-to-collision and post-encroachment rules.
- BL-6 uses all of them plus evasive-action cues.

**What they were compared with.** The yardstick is not human labelling. It is BL-6 applied to the simulator's complete ground truth (Appendix T, T21). The comparison therefore shows how much is lost through what a camera can see and through each configuration's simpler rules. It says nothing about how well a real detector would do.

**Repeatability.** Re-running everything from the same code reproduced all 56,726 artifact IDs exactly (MR-01 = 1.0).

**Main findings (SDG, validation).**
1. **Image boxes alone perform poorly.**
   - BL-2 finds 54 % of the reference interactions (recall 0.54).
   - Only 47 % of its candidate events correspond to one (precision 0.47).
   - It produces about 300 false candidate events per hour of video.
2. **Floor geometry fixes most of this.**
   - BL-3: recall 0.97, precision 0.93.
   - The BL-2 vs BL-3 gap (−0.43 in recall) is far outside its 95 % interval.
3. **Adding the prediction rule helps a little more.**
   - BL-4 and BL-6: recall 0.997, precision 0.95, about 27 false candidates per hour.
   - BL-3 to BL-6: +0.02 in recall and precision. The interval excludes zero when windows are resampled, but not when whole scenes are resampled.
4. **R4 and R5 change labels inside an interaction, not whether it is found.**
   - BL-5 equals BL-3, and BL-6 equals BL-4, on every interaction-level count.
   - R4 does add the "predicted conflict" (PC) label to 275 of 319 episodes (BL-5 against BL-3), and R5 raises the near-miss (NM) labels from 21 to 30 (BL-6 against BL-4).
   - The interaction-level comparison (label group G1) cannot see these changes by design.
5. **Camera geometry is the weak spot.**
   - Using the dataset calibration and the bottom of each box, object positions are typically within 1.5 m (95th percentile).
   - On eye-level cameras, 0.65 % of person positions are wildly wrong (tens of metres to about 5 km). They dominate the root-mean-square error (94 m for persons at eye level, 0.41 m from the ceiling).
   - The pre-registered acceptance target (RMSE ≤ 0.25 m) applies to the test partition only and was not evaluated. These validation numbers suggest it will not be met as the metric is defined.
   - Speeds derived from these positions inherit the same outliers.
6. **Results depend on some thresholds.**
   - Changing the proximity distance d_p from 2 m to 3 m changes 66 of 319 episodes.
   - A ±10 % change in the assumed forklift length changes labels in 7–22 % of episodes.
   - Most other parameters change little.
7. **Some quantities could not be computed on these data** (positional uncertainty coverage, calibration perturbation), because the datasets supply no uncertainty.

**What is not here yet.**
- SmartSpaces results (running).
- SmartSpaces interaction metrics: the reference construction needs about 200 hours there (decision D-39).

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

GV-04 (m):

| stratum | n | bias [B] | RMSE | SD | P5 | P95 |
|---|---|---|---|---|---|---|
| 3.03x1.13|all | 58635 | 0.0003 [0.0002, 0.0003] | 0.0004 | 0.0003 | -0.0001 | 0.0006 |
| 3.03x1.13|detected | 58287 | 0.0003 [0.0002, 0.0003] | 0.0004 | 0.0003 | -0.0001 | 0.0006 |
| 3.03x1.13|inferred | 348 | 0.0002 [0.0001, 0.0002] | 0.0004 | 0.0003 | -0.0001 | 0.0006 |

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

### Observations (descriptive, validation only)

- **EV-M4 = 1, and EV-M3 is high.**
  - EV-M3 is G2 abstention (about 0.69 of episodes).
  - No G2 reference exists on synthetic data (T21.2). G1 is never abstained (T10.7(a)), so EV-M4 = 1 − EV-M5 = 1.
- **The three unobservable references** (T21.3) are reported, not scored.
- **CM on the oracle path is 1 or 0 by construction** for CM-01–CM-04, CM-08 and CM-10:
  - The oracle tracks are the reference-visible objects.
  - CM-05 (detected + inferred) 0.006 is the share of predicted (inferred) POW frames that have no reference-visible counterpart.
  - CM-09 = 0 because predicted oracle points have no reference box (T17.6).
- **GV-04 ≈ 0.0003 m.** The SDG prior footprint equals the simulator box (3.03 × 1.13 m). The residual is the rounding of the box dimensions read from the 3D corners.
- **GV-01 extremes:**
  - 816 object-frames (0.65 %) exceed 5 m. All are persons on eye-level cameras, in 44 cameras.
  - This pattern fits a box bottom edge near the horizon line (for example a lower body hidden behind something, since the visible box is used). The cause has not been checked frame by frame.
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
