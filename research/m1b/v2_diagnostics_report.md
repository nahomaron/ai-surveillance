# Pre-registration v2 diagnostics D1, D2, D4, D5 (D-53)

**Status: diagnostic, tuning subset, not a reported result.** Synthetic SDG validation data only; nothing is validated. Contract E-1.2.24 unchanged; no rule, parameter or pipeline code changed; Fix 1 (anchor offset) and Fix 2 (resolution gate) are not implemented. No test-partition data; the 110 reporting cameras enter only the descriptive D5 table. These numbers never appear in a report table beside columns A, B, C or C'.

Sources: `v2_camera_sets.json`, `d1_anchor_angle.json`, `d2_position_contribution.json`, `d4_detector_offset.json`, `d5_sensitivity_split.json` (each written twice, byte-identical). Percentiles: linear interpolation. "Along" = error component on the line of sight from the camera's floor point to the true centre; negative = toward the camera.

## Summary (plain language)

1. **(a) Angle.** Yes. With oracle boxes, the forklift estimate falls short toward the camera by a median of 1.35 m when the forklift is seen end-on (0–15°) and 0.58 m when seen side-on (75–90°); the footprint half-extent h(θ) falls from 1.58 to 0.73 m over the same bins.
2. A constant shift by the candidate d = 1.00 m leaves a median residual of 0.15–0.42 m and a P95 of 0.48–0.91 m across the angle bins (all frames: median 0.33, P95 0.64 m).
3. D3: 12.9 % of eye-level forklift frames and 0.0 % of ceiling frames have the estimate within 2 m of the camera.
4. **(b) Position substitution.** Column B loses 28 of 135 G1 references against A (BL-6 recall 0.79 vs 1.00). Simulator forklift positions (B-sim-F) recover 15 of the 28 (53.6 %); simulator person positions (B-sim-P) recover 8 (28.6 %).
5. Precision: B 0.50, A 0.94. B-sim-F 0.57 (14.3 % of the gap), B-sim-P 0.65 (32.2 %); unmatched events 105 → 93 (F) and 63 (P).
6. Neither substitution alone reaches A, so the person and forklift positions both contribute; forklift position contributes more to recall, person position more to precision.
7. **(c) Detector vs oracle boxes.** No, not by more than 0.2 m. On the same 16,374 forklift identity-frames (96 tuning cameras with stored S2), the median paired difference (detector − oracle) is -0.05 m overall and lies between -0.08 and -0.03 m in every viewpoint × angle bin.
8. The two sides' separate medians differ by more in one bin (eye-level 15–30°: -0.71 vs -1.14 m), where the frame distributions are spread; the paired difference there is -0.03 m.
9. D4 does not cover the 20 T-22 probe cameras (no stored S2 run; the detector was not re-run).
10. No value or rule form is recommended here; the Architect and the Owner choose.

## Step 0: camera sets

| Set | Runs | Cameras | Ceiling | Eye-level |
|---|---|---|---|---|
| Tuning (runs with a T-22 probe camera) | 13 | 116 | 54 | 62 |
| Reporting (other validation runs) | 11 | 110 | 55 | 55 |

Disjoint; population = the 226 SDG validation cameras with an ORACLE-S3. Check: ok: 116 / 110, disjoint.

## Step 1 (D1, D3): forklift along-sight error by viewing angle, oracle boxes (column B S4, 116 tuning cameras)

33,707 forklift object-frames with a position; θ = angle between the simulator yaw axis (box long axis) and the line of sight, folded to [0°, 90°]; h(θ) = 1.515 |cos θ| + 0.565 |sin θ| m (L = 3.03 m, W = 1.13 m).

**All**

| θ bin | n | Signed median (m) | P05 (m) | P95 (m) | Median h(θ) (m) |
|---|---|---|---|---|---|
| 0-15° | 6,254 | -1.35 | -1.50 | -0.32 | 1.58 |
| 15-30° | 5,435 | -1.32 | -1.49 | -0.41 | 1.61 |
| 30-45° | 5,331 | -1.20 | -1.43 | -0.09 | 1.55 |
| 45-60° | 5,507 | -0.97 | -1.23 | -0.23 | 1.38 |
| 60-75° | 5,672 | -0.73 | -0.99 | -0.52 | 1.10 |
| 75-90° | 5,508 | -0.58 | -0.89 | -0.51 | 0.73 |

**Ceiling**

| θ bin | n | Signed median (m) | P05 (m) | P95 (m) | Median h(θ) (m) |
|---|---|---|---|---|---|
| 0-15° | 2,484 | -1.44 | -1.50 | -1.23 | 1.58 |
| 15-30° | 2,308 | -1.39 | -1.50 | -0.19 | 1.61 |
| 30-45° | 2,943 | -1.24 | -1.44 | -0.02 | 1.55 |
| 45-60° | 2,475 | -1.03 | -1.23 | -0.13 | 1.37 |
| 60-75° | 2,919 | -0.77 | -1.02 | -0.53 | 1.10 |
| 75-90° | 2,961 | -0.58 | -0.93 | -0.53 | 0.73 |

**Eye-level**

| θ bin | n | Signed median (m) | P05 (m) | P95 (m) | Median h(θ) (m) |
|---|---|---|---|---|---|
| 0-15° | 3,770 | -1.23 | -1.50 | -0.32 | 1.57 |
| 15-30° | 3,127 | -1.22 | -1.49 | -0.42 | 1.61 |
| 30-45° | 2,388 | -1.11 | -1.39 | -0.15 | 1.55 |
| 45-60° | 3,032 | -0.87 | -1.20 | -0.49 | 1.38 |
| 60-75° | 2,753 | -0.68 | -0.91 | -0.44 | 1.10 |
| 75-90° | 2,547 | -0.58 | -0.84 | -0.49 | 0.73 |

**D3: estimate within 2 m of the camera (floor distance r)**

| Viewpoint | Frames | r < 2 m | Share |
|---|---|---|---|
| All | 33,707 | 2,274 | 6.7 % |
| Ceiling | 16,090 | 0 | 0.0 % |
| Eye-level | 17,617 | 2,274 | 12.9 % |

**Candidate d** = median |along| over all tuning frames = 0.987 m, rounded to 0.05 m: **1.00 m**.

Residual after a constant shift by d: |along − (−d)|

| θ bin | n | Median (m) | P95 (m) |
|---|---|---|---|
| 0-15° | 6,254 | 0.40 | 0.68 |
| 15-30° | 5,435 | 0.39 | 0.59 |
| 30-45° | 5,331 | 0.28 | 0.91 |
| 45-60° | 5,507 | 0.15 | 0.77 |
| 60-75° | 5,672 | 0.27 | 0.48 |
| 75-90° | 5,508 | 0.42 | 0.49 |
| all | 33,707 | 0.33 | 0.64 |

## Step 2 (D2): position contribution to the oracle-box loss (BL-6, G1, N4; 116 tuning cameras)

Oracle boxes and BL-6 under the frozen v1 values, evaluated against the stored T-21 BL-6 references; EV-M1 and EV-M2 from summed counts. B-tune is column B re-run through the diagnostic adapter; its S4 equals the stored column B S4 on all 116 cameras (payload hash), and the rebuilt ORACLE-S3 equals the stored one on all 116. Only position and covariance were substituted (the simulator yaw was not). Column A: stored T-21 `base` unit, same cameras. Code commit 74e7b0c; execution records beside every artifact under `out/m1b/v2diag/`.

**All** (116 cameras)

| Run | EV-M1 | EV-M2 | Assessable | Matched | Missed | Events | Unmatched events |
|---|---|---|---|---|---|---|---|
| B-tune (column B) | 0.793 | 0.505 | 135 | 107 | 28 | 212 | 105 |
| B-sim-F (simulator forklift) | 0.904 | 0.567 | 135 | 122 | 13 | 215 | 93 |
| B-sim-P (simulator person) | 0.852 | 0.646 | 135 | 115 | 20 | 178 | 63 |
| A (simulator both; stored) | 1.000 | 0.944 | 135 | 135 | 0 | 143 | 8 |

**Ceiling** (54 cameras)

| Run | EV-M1 | EV-M2 | Assessable | Matched | Missed | Events | Unmatched events |
|---|---|---|---|---|---|---|---|
| B-tune (column B) | 0.750 | 0.449 | 64 | 48 | 16 | 107 | 59 |
| B-sim-F (simulator forklift) | 0.906 | 0.569 | 64 | 58 | 6 | 102 | 44 |
| B-sim-P (simulator person) | 0.859 | 0.647 | 64 | 55 | 9 | 85 | 30 |
| A (simulator both; stored) | 1.000 | 1.000 | 64 | 64 | 0 | 64 | 0 |

**Eye-level** (62 cameras)

| Run | EV-M1 | EV-M2 | Assessable | Matched | Missed | Events | Unmatched events |
|---|---|---|---|---|---|---|---|
| B-tune (column B) | 0.831 | 0.562 | 71 | 59 | 12 | 105 | 46 |
| B-sim-F (simulator forklift) | 0.901 | 0.566 | 71 | 64 | 7 | 113 | 49 |
| B-sim-P (simulator person) | 0.845 | 0.645 | 71 | 60 | 11 | 93 | 33 |
| A (simulator both; stored) | 1.000 | 0.899 | 71 | 71 | 0 | 79 | 8 |

## Step 3 (D4): forklift offset with detector boxes (stored YOLO-World S2, frame level)

96 tuning cameras with a stored S2 (44 ceiling, 52 eye-level); **20 cameras missing** (the T-22 probe cameras: not in the pilot, no stored S2 run; the detector was not re-run). Forklift detections matched to a reference-visible forklift box as in the pilot frame metrics (IoU ≥ 0.3, one-to-one): 16,374. Position = box bottom-centre through `full_camera`. Before tracking, so no tracker setting enters.

| Viewpoint | n | Signed median (m) | P95 (m) | Median |along| (m) | P95 |along| (m) |
|---|---|---|---|---|---|
| All | 16,374 | -0.84 | -0.44 | 0.85 | 1.53 |
| Ceiling | 10,173 | -0.89 | -0.42 | 0.91 | 1.54 |
| Eye-level | 6,201 | -0.77 | -0.44 | 0.78 | 1.50 |

By θ bin, with the oracle box (stored column B S4) on the same identity-frames:

**All**

| θ bin | n | Detector signed median (m) | Detector P95 (m) | Oracle signed median, same frames (m) | Median paired difference, detector − oracle (m) |
|---|---|---|---|---|---|
| 0-15° | 2,248 | -1.40 | -0.44 | -1.30 | -0.06 |
| 15-30° | 2,631 | -1.36 | -0.11 | -1.33 | -0.03 |
| 30-45° | 2,942 | -1.23 | 0.03 | -1.22 | -0.04 |
| 45-60° | 2,856 | -1.01 | -0.47 | -0.97 | -0.06 |
| 60-75° | 2,927 | -0.78 | -0.59 | -0.73 | -0.06 |
| 75-90° | 2,770 | -0.65 | -0.50 | -0.59 | -0.06 |

**Ceiling**

| θ bin | n | Detector signed median (m) | Detector P95 (m) | Oracle signed median, same frames (m) | Median paired difference, detector − oracle (m) |
|---|---|---|---|---|---|
| 0-15° | 1,109 | -1.51 | -0.46 | -1.42 | -0.06 |
| 15-30° | 1,575 | -1.41 | 0.11 | -1.39 | -0.03 |
| 30-45° | 1,914 | -1.29 | 0.17 | -1.27 | -0.03 |
| 45-60° | 1,630 | -1.05 | -0.31 | -1.01 | -0.05 |
| 60-75° | 1,939 | -0.78 | -0.62 | -0.73 | -0.06 |
| 75-90° | 2,006 | -0.64 | -0.49 | -0.59 | -0.05 |

**Eye-level**

| θ bin | n | Detector signed median (m) | Detector P95 (m) | Oracle signed median, same frames (m) | Median paired difference, detector − oracle (m) |
|---|---|---|---|---|---|
| 0-15° | 1,139 | -1.05 | -0.43 | -1.05 | -0.07 |
| 15-30° | 1,056 | -0.71 | -0.37 | -1.14 | -0.03 |
| 30-45° | 1,028 | -0.79 | -0.26 | -0.96 | -0.06 |
| 45-60° | 1,226 | -0.97 | -0.55 | -0.94 | -0.07 |
| 60-75° | 988 | -0.76 | -0.51 | -0.66 | -0.08 |
| 75-90° | 764 | -0.68 | -0.58 | -0.58 | -0.07 |

## Step 4 (D5): pixel-sensitivity table by camera set (descriptive; stored outputs)

Definitions of `research/m1a/position_sensitivity.py` (CR-026 evidence, D-40 item 6), column B, persons and forklifts. Check: on all 226 cameras the split function reproduces the stored SDG table exactly (True). "Good" = error < 1 m (stored definition); the share with error ≤ 1 m is identical to three decimals in every row and is kept in the JSON.

**SDG tuning cameras** (116 cameras, 64,750 GV-01 points)

| s_max (m/px) | Share flagged | Errors > 10 m caught | Good points lost | P99 of kept (m) |
|---|---|---|---|---|
| 0.05 | 3.2 % | 100.0 % | 2.6 % | 1.69 |
| 0.1 | 0.6 % | 94.2 % | 0.0 % | 1.89 |
| 0.2 | 0.5 % | 84.8 % | 0.0 % | 2.03 |
| 0.5 | 0.4 % | 72.1 % | 0.0 % | 2.12 |

**SDG reporting cameras** (110 cameras, 61,615 GV-01 points)

| s_max (m/px) | Share flagged | Errors > 10 m caught | Good points lost | P99 of kept (m) |
|---|---|---|---|---|
| 0.05 | 2.2 % | 100.0 % | 1.3 % | 1.61 |
| 0.1 | 0.5 % | 100.0 % | 0.0 % | 1.65 |
| 0.2 | 0.4 % | 92.6 % | 0.0 % | 1.70 |
| 0.5 | 0.4 % | 84.8 % | 0.0 % | 1.72 |

**SmartSpaces** (1,935,170 GV-01 points): no tuning split is defined; the stored table is copied unchanged.

| s_max (m/px) | Share flagged | Errors > 10 m caught | Good points lost | P99 of kept (m) |
|---|---|---|---|---|
| 0.05 | 90.1 % | 100.0 % | 83.0 % | 3.31 |
| 0.1 | 80.7 % | 99.9 % | 66.8 % | 6.05 |
| 0.2 | 68.3 % | 99.5 % | 47.3 % | 9.05 |
| 0.5 | 44.4 % | 90.3 % | 18.1 % | 18.42 |
