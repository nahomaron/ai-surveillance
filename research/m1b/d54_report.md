# D-54 diagnostics: T24 on the tuning cameras, and person positions

Decision: D-54 (23 Nov 2026), with D-56. Contract E-1.2.25 (Appendix T T24). Branch `m0-implementation`.

**Diagnostic, tuning subset, not a reported result.** Synthetic SDG validation data; 116 tuning cameras only (D-54 ruling 5). Nothing was run on the 110 reporting cameras or on the test partition (D-37). Pilot columns A, B, C and C′ are unchanged and their stored artifacts were not overwritten. The T24 values and the tracker package are **selected, not frozen**. Status words: implemented / verified (fixtures) only. Nothing is empirically validated.

## Summary (plain language)

1. With oracle boxes, the forklift centre shift (T24.1) raises EV-M1 from 0.79 to 0.93 and EV-M2 from 0.50 to 0.57 (116 tuning cameras).
2. It lowers the median forklift position error from 1.06 m to 0.40 m. The share above 2 m rises from 0.1 % to 0.9 %.
3. With oracle boxes, the resolution gate (T24.2) leaves EV-M1 at 0.793 and moves EV-M2 from 0.505 to 0.510. It nulls 366 person frames (all eye level) and no forklift frame.
4. The D-56 tracker package alone (C-pkg) gives EV-M1 0.53, EV-M2 0.33 and CM-03 0.51. On the 96 cameras where column C exists, C gives 0.10, 0.17 and 0.11.
5. With T24 on as well (C-v2): EV-M1 0.58, EV-M2 0.33. The system raises more events (237 against 213), and 159 of them are unmatched.
6. On the detector path the eye-level cameras lag far behind the ceiling cameras (C-v2 EV-M1 0.39 against 0.78).
7. Fragmentation remains: with C-v2, 69 references are covered by two or more episodes, and 15 of 237 episodes carry `continuation_of_nk`.
8. Person positions with oracle boxes: median error 0.19 m. The median along-sight error is -0.13 m, about a third of the person box's half-depth (0.38 m).
9. The large person errors are in estimates 20 m or more from the camera (296 frames, median error 76 m); below 20 m the error P95 is at most 5.4 m.
10. Among the B-tune unmatched events that B-sim-P lacks, B alone is below d_pc (R3) more often than below d_p (reading 1: 8 against 4 of 15; reading 2: 20 against 4 of 50, with 25 on the same side of both). The count depends on CR-035.
11. Lost points (CR-034) do not occur on either path here, so CR-034's two readings give identical results.
12. All of this is synthetic SDG data on the tuning cameras only: diagnostic, not a reported result, and nothing here is validated.

## 1. STEP 3: column B with T24 on (oracle boxes, BL-6)

**Diagnostic, tuning subset, not a reported result.**

116 tuning cameras; oracle boxes; `full_camera`; S5 BL-6; N4 against the stored T-21 BL-6 references, label group G1, summed counts. T24 values (D-54 v2 candidates, selected, not frozen): s_max 0.1 m/px; forklift prior `anchor = box_bottom_centre`, d 1.00 m, r_taper 2.0 m. The person prior is unchanged. The ORACLE-S3 was rebuilt and equals the stored one on 116 of 116 cameras. Output: `research/m1b/d54_b_v2_tune.json`.

### 1.1 EV-M1 and EV-M2

| column | view | cameras | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events |
|---|---|---|---|---|---|---|---|
| A (stored, D-53) | all | 116 | 1.000 | 135 / 135 | 0.944 | 135 / 143 | 8 |
| A (stored, D-53) | ceiling | 54 | 1.000 | 64 / 64 | 1.000 | 64 / 64 | 0 |
| A (stored, D-53) | eye level | 62 | 1.000 | 71 / 71 | 0.899 | 71 / 79 | 8 |
| B-tune (= stored B, D-53) | all | 116 | 0.793 | 107 / 135 | 0.505 | 107 / 212 | 105 |
| B-tune (= stored B, D-53) | ceiling | 54 | 0.750 | 48 / 64 | 0.449 | 48 / 107 | 59 |
| B-tune (= stored B, D-53) | eye level | 62 | 0.831 | 59 / 71 | 0.562 | 59 / 105 | 46 |
| B-T24.2 | all | 116 | 0.793 | 107 / 135 | 0.510 | 107 / 210 | 103 |
| B-T24.2 | ceiling | 54 | 0.750 | 48 / 64 | 0.449 | 48 / 107 | 59 |
| B-T24.2 | eye level | 62 | 0.831 | 59 / 71 | 0.573 | 59 / 103 | 44 |
| B-T24.1 | all | 116 | 0.926 | 125 / 135 | 0.568 | 125 / 220 | 95 |
| B-T24.1 | ceiling | 54 | 0.953 | 61 / 64 | 0.587 | 61 / 104 | 43 |
| B-T24.1 | eye level | 62 | 0.901 | 64 / 71 | 0.552 | 64 / 116 | 52 |
| B-both | all | 116 | 0.926 | 125 / 135 | 0.571 | 125 / 219 | 94 |
| B-both | ceiling | 54 | 0.953 | 61 / 64 | 0.587 | 61 / 104 | 43 |
| B-both | eye level | 62 | 0.901 | 64 / 71 | 0.557 | 64 / 115 | 51 |

### 1.2 Forklift position error

|Estimate − simulator footprint centre| of the oracle track's identity (D1 definitions); median and P95 by linear interpolation. This is the Euclidean error. It is not D1's along-sight residual (median 0.33 m, P95 0.64 m), which T24.1 (e) asks reports to state.

| column | view | object-frames | median | P95 | > 1 m | > 2 m | > 10 m |
|---|---|---|---|---|---|---|---|
| B-tune (stored B) | all | 33707 | 1.057 m | 1.484 m | 53.3 % | 0.1 % | 0.00 % |
| B-tune (stored B) | ceiling | 16090 | 1.107 m | 1.482 m | 58.3 % | 0.3 % | 0.00 % |
| B-tune (stored B) | eye level | 17617 | 0.977 m | 1.492 m | 48.7 % | 0.0 % | 0.00 % |
| B-T24.2 | all | 33707 | 1.057 m | 1.484 m | 53.3 % | 0.1 % | 0.00 % |
| B-T24.2 | ceiling | 16090 | 1.107 m | 1.482 m | 58.3 % | 0.3 % | 0.00 % |
| B-T24.2 | eye level | 17617 | 0.977 m | 1.492 m | 48.7 % | 0.0 % | 0.00 % |
| B-T24.1 | all | 33707 | 0.399 m | 1.090 m | 5.9 % | 0.9 % | 0.00 % |
| B-T24.1 | ceiling | 16090 | 0.375 m | 0.840 m | 4.0 % | 1.4 % | 0.00 % |
| B-T24.1 | eye level | 17617 | 0.416 m | 1.211 m | 7.6 % | 0.5 % | 0.00 % |
| B-both | all | 33707 | 0.399 m | 1.090 m | 5.9 % | 0.9 % | 0.00 % |
| B-both | ceiling | 16090 | 0.375 m | 0.840 m | 4.0 % | 1.4 % | 0.00 % |
| B-both | eye level | 17617 | 0.416 m | 1.211 m | 7.6 % | 0.5 % | 0.00 % |

### 1.3 Availability by null reason (T24.2 (e), (f))

Data origin: synthetic_rendered (SDG) for every camera. s_max = 0.1 m/px. Gated positions are *unresolved*, not *wrong* (T24.2 (f)).

| column | view | class | object-frames | position | resolution limit (s > s_max) | no floor intersection | lost point | other null |
|---|---|---|---|---|---|---|---|---|
| B-tune (stored B) | all | forklift | 33707 | 33707 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-tune (stored B) | all | person | 31426 | 31043 (98.8 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 383 (1.2 %) |
| B-tune (stored B) | ceiling | forklift | 16090 | 16090 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-tune (stored B) | ceiling | person | 16200 | 16200 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-tune (stored B) | eye level | forklift | 17617 | 17617 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-tune (stored B) | eye level | person | 15226 | 14843 (97.5 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 383 (2.5 %) |
| B-T24.2 | all | forklift | 33707 | 33707 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.2 | all | person | 31426 | 30677 (97.6 %) | 366 (1.2 %) | 383 (1.2 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.2 | ceiling | forklift | 16090 | 16090 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.2 | ceiling | person | 16200 | 16200 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.2 | eye level | forklift | 17617 | 17617 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.2 | eye level | person | 15226 | 14477 (95.1 %) | 366 (2.4 %) | 383 (2.5 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.1 | all | forklift | 33707 | 33707 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.1 | all | person | 31426 | 31043 (98.8 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 383 (1.2 %) |
| B-T24.1 | ceiling | forklift | 16090 | 16090 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.1 | ceiling | person | 16200 | 16200 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.1 | eye level | forklift | 17617 | 17617 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-T24.1 | eye level | person | 15226 | 14843 (97.5 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 383 (2.5 %) |
| B-both | all | forklift | 33707 | 33707 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-both | all | person | 31426 | 30677 (97.6 %) | 366 (1.2 %) | 383 (1.2 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-both | ceiling | forklift | 16090 | 16090 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-both | ceiling | person | 16200 | 16200 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-both | eye level | forklift | 17617 | 17617 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| B-both | eye level | person | 15226 | 14477 (95.1 %) | 366 (2.4 %) | 383 (2.5 %) | 0 (0.0 %) | 0 (0.0 %) |

With the gate off, a ray with no floor intersection is "other null" (`not_observable`, as in E-1.2.24). With the gate on it is the separate row "no floor intersection", so the 383 person frames move between rows. The gate nulls no forklift frame on the oracle path.
CR-034 (lost points): ORACLE-S3 has 0 lost object-frames on these cameras. Readings (a) and (b) give identical results here (0 pair-frames would change).

## 2. STEP 3b: detector path with the D-56 package, T24 off (C-pkg) and on (C-v2)

**Diagnostic, tuning subset, not a reported result.**
These runs never enter a report table beside the pilot columns.

116 tuning cameras. S2: the stored YOLO-World detections (96 pilot S2, 20 probe-camera S2 from D-55); no new detection. S3: the D-56 package `trc_7flfpx52d2siiljxkqwcorr7nz`. Its tracker run reproduced the stored D-55 grid measures on 116 of 116 cameras. S4 `full_camera`. C-v2 uses the T24 values s_max 0.1 m/px, d 1.00 m and r_taper 2.0 m (selected, not frozen). S5 BL-6. S8 N4 against the T-21 BL-6 references, G1, A5.2 association of the detector tracks, as in the pilot. Runtime: estimated 0.22 h on 2 cameras (limit 3 h); the run took 12 min, plus 5 min of evaluation. Output: `research/m1b/d54_c_v2_tune.json`.

Standing caveat (D-56): The package accepts forklift detections down to score 0.05. Point precision 0.979 was measured on synthetic SDG data only and is not known for real footage.

Column C exists only on the 96 tuning cameras that are pilot cameras. Section 2.2 therefore restricts every column to those 96 cameras; it is stated as such.

### 2.1 All 116 tuning cameras

#### EV-M1, EV-M2 and CM-03

| column | view | cameras | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events |
|---|---|---|---|---|---|---|---|
| A (stored) | all | 116 | 1.000 | 135 / 135 | 0.944 | 135 / 143 | 8 |
| A (stored) | ceiling | 54 | 1.000 | 64 / 64 | 1.000 | 64 / 64 | 0 |
| A (stored) | eye level | 62 | 1.000 | 71 / 71 | 0.899 | 71 / 79 | 8 |
| B-tune (= stored B) | all | 116 | 0.793 | 107 / 135 | 0.505 | 107 / 212 | 105 |
| B-tune (= stored B) | ceiling | 54 | 0.750 | 48 / 64 | 0.449 | 48 / 107 | 59 |
| B-tune (= stored B) | eye level | 62 | 0.831 | 59 / 71 | 0.562 | 59 / 105 | 46 |
| C-pkg | all | 116 | 0.526 | 71 / 135 | 0.333 | 71 / 213 | 142 |
| C-pkg | ceiling | 54 | 0.719 | 46 / 64 | 0.390 | 46 / 118 | 72 |
| C-pkg | eye level | 62 | 0.352 | 25 / 71 | 0.263 | 25 / 95 | 70 |
| C-v2 | all | 116 | 0.578 | 78 / 135 | 0.329 | 78 / 237 | 159 |
| C-v2 | ceiling | 54 | 0.781 | 50 / 64 | 0.368 | 50 / 136 | 86 |
| C-v2 | eye level | 62 | 0.394 | 28 / 71 | 0.277 | 28 / 101 | 73 |

CM-03: pair coverage, pooled as sum of numerators over sum of denominators (the pilot's point value).

| column | view | CM-03 detected | CM-03 detected_plus_inferred |
|---|---|---|---|
| A (stored) | all | 1.000 | 1.000 |
| A (stored) | ceiling | 1.000 | 1.000 |
| A (stored) | eye level | 1.000 | 1.000 |
| B-tune (= stored B) | all | 1.000 | 1.000 |
| B-tune (= stored B) | ceiling | 1.000 | 1.000 |
| B-tune (= stored B) | eye level | 1.000 | 1.000 |
| C-pkg | all | 0.508 | 0.579 |
| C-pkg | ceiling | 0.688 | 0.760 |
| C-pkg | eye level | 0.304 | 0.374 |
| C-v2 | all | 0.508 | 0.579 |
| C-v2 | ceiling | 0.688 | 0.760 |
| C-v2 | eye level | 0.304 | 0.374 |

#### Extent and fragmentation (D-50 item 2 definitions, `extent_check.py`; BL-6, G1)

| column | view | unmatched events | with same-pair overlap (IoU > 0) | IoU 0 / (0, 0.1] / (0.1, 0.2] / (0.2, 0.3) / ≥ 0.3 | references matched or overlapped | covered by ≥ 2 episodes | episodes | episodes with `continuation_of_nk` | overlapping episodes linked / overlapping |
|---|---|---|---|---|---|---|---|---|---|
| A (stored) | all | 8 | 8 | 0 / 3 / 2 / 0 / 3 | 135 | 8 | 143 | 8 | 8 / 143 |
| A (stored) | ceiling | 0 | 0 | 0 / 0 / 0 / 0 / 0 | 64 | 0 | 64 | 0 | 0 / 64 |
| A (stored) | eye level | 8 | 8 | 0 / 3 / 2 / 0 / 3 | 71 | 8 | 79 | 8 | 8 / 79 |
| B-tune (= stored B) | all | 105 | 86 | 37 / 25 / 22 / 19 / 2 | 129 | 46 | 212 | 1 | 1 / 203 |
| B-tune (= stored B) | ceiling | 59 | 48 | 23 / 13 / 11 / 11 / 1 | 62 | 25 | 107 | 0 | 0 / 102 |
| B-tune (= stored B) | eye level | 46 | 38 | 14 / 12 / 11 / 8 / 1 | 67 | 21 | 105 | 1 | 1 / 101 |
| C-pkg | all | 142 | 134 | 61 / 38 / 33 / 8 / 2 | 117 | 57 | 213 | 13 | 14 / 212 |
| C-pkg | ceiling | 72 | 66 | 27 / 25 / 12 / 6 / 2 | 61 | 33 | 118 | 6 | 6 / 117 |
| C-pkg | eye level | 70 | 68 | 34 / 13 / 21 / 2 / 0 | 56 | 24 | 95 | 7 | 8 / 95 |
| C-v2 | all | 159 | 149 | 66 / 47 / 34 / 10 / 2 | 116 | 69 | 237 | 15 | 15 / 231 |
| C-v2 | ceiling | 86 | 80 | 32 / 33 / 13 / 6 / 2 | 60 | 42 | 136 | 6 | 6 / 133 |
| C-v2 | eye level | 73 | 69 | 34 / 14 / 21 / 4 / 0 | 56 | 27 | 101 | 9 | 9 / 98 |

### 2.2 The 96 tuning cameras that are pilot cameras (column C restricted to them)

#### EV-M1, EV-M2 and CM-03

| column | view | cameras | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events |
|---|---|---|---|---|---|---|---|
| A (stored) | all | 96 | 1.000 | 114 / 114 | 0.950 | 114 / 120 | 6 |
| A (stored) | ceiling | 44 | 1.000 | 54 / 54 | 1.000 | 54 / 54 | 0 |
| A (stored) | eye level | 52 | 1.000 | 60 / 60 | 0.909 | 60 / 66 | 6 |
| B-tune (= stored B) | all | 96 | 0.772 | 88 / 114 | 0.524 | 88 / 168 | 80 |
| B-tune (= stored B) | ceiling | 44 | 0.722 | 39 / 54 | 0.459 | 39 / 85 | 46 |
| B-tune (= stored B) | eye level | 52 | 0.817 | 49 / 60 | 0.590 | 49 / 83 | 34 |
| C (pilot, stored) | all | 96 | 0.096 | 11 / 114 | 0.172 | 11 / 64 | 53 |
| C (pilot, stored) | ceiling | 44 | 0.148 | 8 / 54 | 0.195 | 8 / 41 | 33 |
| C (pilot, stored) | eye level | 52 | 0.050 | 3 / 60 | 0.130 | 3 / 23 | 20 |
| C-pkg | all | 96 | 0.526 | 60 / 114 | 0.355 | 60 / 169 | 109 |
| C-pkg | ceiling | 44 | 0.741 | 40 / 54 | 0.421 | 40 / 95 | 55 |
| C-pkg | eye level | 52 | 0.333 | 20 / 60 | 0.270 | 20 / 74 | 54 |
| C-v2 | all | 96 | 0.579 | 66 / 114 | 0.347 | 66 / 190 | 124 |
| C-v2 | ceiling | 44 | 0.796 | 43 / 54 | 0.394 | 43 / 109 | 66 |
| C-v2 | eye level | 52 | 0.383 | 23 / 60 | 0.284 | 23 / 81 | 58 |

CM-03: pair coverage, pooled as sum of numerators over sum of denominators (the pilot's point value).

| column | view | CM-03 detected | CM-03 detected_plus_inferred |
|---|---|---|---|
| A (stored) | all | 1.000 | 1.000 |
| A (stored) | ceiling | 1.000 | 1.000 |
| A (stored) | eye level | 1.000 | 1.000 |
| B-tune (= stored B) | all | 1.000 | 1.000 |
| B-tune (= stored B) | ceiling | 1.000 | 1.000 |
| B-tune (= stored B) | eye level | 1.000 | 1.000 |
| C (pilot, stored) | all | 0.112 | 0.118 |
| C (pilot, stored) | ceiling | 0.154 | 0.160 |
| C (pilot, stored) | eye level | 0.067 | 0.072 |
| C-pkg | all | 0.508 | 0.579 |
| C-pkg | ceiling | 0.698 | 0.769 |
| C-pkg | eye level | 0.299 | 0.369 |
| C-v2 | all | 0.508 | 0.579 |
| C-v2 | ceiling | 0.698 | 0.769 |
| C-v2 | eye level | 0.299 | 0.369 |

#### Extent and fragmentation (D-50 item 2 definitions, `extent_check.py`; BL-6, G1)

| column | view | unmatched events | with same-pair overlap (IoU > 0) | IoU 0 / (0, 0.1] / (0.1, 0.2] / (0.2, 0.3) / ≥ 0.3 | references matched or overlapped | covered by ≥ 2 episodes | episodes | episodes with `continuation_of_nk` | overlapping episodes linked / overlapping |
|---|---|---|---|---|---|---|---|---|---|
| A (stored) | all | 6 | 6 | 0 / 2 / 2 / 0 / 2 | 114 | 6 | 120 | 6 | 6 / 120 |
| A (stored) | ceiling | 0 | 0 | 0 / 0 / 0 / 0 / 0 | 54 | 0 | 54 | 0 | 0 / 54 |
| A (stored) | eye level | 6 | 6 | 0 / 2 / 2 / 0 / 2 | 60 | 6 | 66 | 6 | 6 / 66 |
| B-tune (= stored B) | all | 80 | 66 | 27 / 20 / 17 / 14 / 2 | 108 | 34 | 168 | 1 | 1 / 163 |
| B-tune (= stored B) | ceiling | 46 | 38 | 18 / 10 / 9 / 8 / 1 | 52 | 20 | 85 | 0 | 0 / 83 |
| B-tune (= stored B) | eye level | 34 | 28 | 9 / 10 / 8 / 6 / 1 | 56 | 14 | 83 | 1 | 1 / 80 |
| C (pilot, stored) | all | 53 | 53 | 30 / 15 / 8 / 0 / 0 | 43 | 18 | 64 | 1 | 1 / 65 |
| C (pilot, stored) | ceiling | 33 | 33 | 18 / 9 / 6 / 0 / 0 | 28 | 11 | 41 | 1 | 1 / 41 |
| C (pilot, stored) | eye level | 20 | 20 | 12 / 6 / 2 / 0 / 0 | 15 | 7 | 23 | 0 | 0 / 24 |
| C-pkg | all | 109 | 101 | 43 / 32 / 24 / 8 / 2 | 98 | 44 | 169 | 8 | 9 / 168 |
| C-pkg | ceiling | 55 | 49 | 19 / 21 / 7 / 6 / 2 | 51 | 26 | 95 | 4 | 4 / 94 |
| C-pkg | eye level | 54 | 52 | 24 / 11 / 17 / 2 / 0 | 47 | 18 | 74 | 4 | 5 / 74 |
| C-v2 | all | 124 | 115 | 50 / 39 / 24 / 9 / 2 | 97 | 56 | 190 | 9 | 9 / 185 |
| C-v2 | ceiling | 66 | 61 | 24 / 28 / 7 / 5 / 2 | 50 | 34 | 109 | 4 | 4 / 107 |
| C-v2 | eye level | 58 | 54 | 26 / 11 / 17 / 4 / 0 | 47 | 22 | 81 | 5 | 5 / 78 |

### 2.3 Position error (detector path, D-41 definitions as the pilot)

|Estimate − simulator position| of the A5.2-matched identity on the frame (B: the oracle track's identity). Shares above 1, 2 and 5 m, as in the pilot. 116 cameras.

| column | view | class | object-frames | median | P95 | > 1 m | > 2 m | > 5 m |
|---|---|---|---|---|---|---|---|---|
| B-tune (stored B) | all | forklift | 33707 | 1.057 m | 1.484 m | 53.3 % | 0.1 % | 0.0 % |
| B-tune (stored B) | all | person | 31043 | 0.188 m | 1.015 m | 5.0 % | 2.9 % | 1.5 % |
| B-tune (stored B) | ceiling | forklift | 16090 | 1.107 m | 1.482 m | 58.3 % | 0.3 % | 0.0 % |
| B-tune (stored B) | ceiling | person | 16200 | 0.199 m | 0.698 m | 3.6 % | 0.6 % | 0.0 % |
| B-tune (stored B) | eye level | forklift | 17617 | 0.977 m | 1.492 m | 48.7 % | 0.0 % | 0.0 % |
| B-tune (stored B) | eye level | person | 14843 | 0.173 m | 2.415 m | 6.6 % | 5.5 % | 3.2 % |
| C-pkg | all | forklift | 22258 | 0.907 m | 1.542 m | 45.7 % | 0.1 % | 0.0 % |
| C-pkg | all | person | 28431 | 0.237 m | 0.564 m | 2.4 % | 1.3 % | 0.6 % |
| C-pkg | ceiling | forklift | 13565 | 0.955 m | 1.551 m | 48.3 % | 0.0 % | 0.0 % |
| C-pkg | ceiling | person | 14827 | 0.232 m | 0.502 m | 1.3 % | 0.0 % | 0.0 % |
| C-pkg | eye level | forklift | 8693 | 0.847 m | 1.510 m | 41.7 % | 0.1 % | 0.0 % |
| C-pkg | eye level | person | 13604 | 0.246 m | 0.655 m | 3.6 % | 2.6 % | 1.2 % |
| C-v2 | all | forklift | 22258 | 0.465 m | 0.806 m | 2.9 % | 0.6 % | 0.0 % |
| C-v2 | all | person | 28299 | 0.237 m | 0.540 m | 2.0 % | 0.8 % | 0.1 % |
| C-v2 | ceiling | forklift | 13565 | 0.423 m | 0.655 m | 2.5 % | 0.6 % | 0.0 % |
| C-v2 | ceiling | person | 14827 | 0.232 m | 0.502 m | 1.3 % | 0.0 % | 0.0 % |
| C-v2 | eye level | forklift | 8693 | 0.498 m | 0.899 m | 3.5 % | 0.6 % | 0.0 % |
| C-v2 | eye level | person | 13472 | 0.245 m | 0.590 m | 2.7 % | 1.7 % | 0.3 % |

### 2.4 Availability by null reason, C-pkg and C-v2 (T24.2 (e), (f))

Data origin: synthetic_rendered (SDG). s_max = 0.1 m/px. Gated positions are *unresolved*, not *wrong*.

| column | view | class | object-frames | position | resolution limit (s > s_max) | no floor intersection | other null |
|---|---|---|---|---|---|---|---|
| C-pkg | all | forklift | 23294 | 23294 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-pkg | all | person | 28836 | 28678 (99.5 %) | 0 (0.0 %) | 0 (0.0 %) | 158 (0.5 %) |
| C-pkg | ceiling | forklift | 13698 | 13698 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-pkg | ceiling | person | 14915 | 14915 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-pkg | eye level | forklift | 9596 | 9596 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-pkg | eye level | person | 13921 | 13763 (98.9 %) | 0 (0.0 %) | 0 (0.0 %) | 158 (1.1 %) |
| C-v2 | all | forklift | 23294 | 23184 (99.5 %) | 110 (0.5 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-v2 | all | person | 28836 | 28520 (98.9 %) | 158 (0.5 %) | 158 (0.5 %) | 0 (0.0 %) |
| C-v2 | ceiling | forklift | 13698 | 13698 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-v2 | ceiling | person | 14915 | 14915 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-v2 | eye level | forklift | 9596 | 9486 (98.9 %) | 110 (1.1 %) | 0 (0.0 %) | 0 (0.0 %) |
| C-v2 | eye level | person | 13921 | 13605 (97.7 %) | 158 (1.1 %) | 158 (1.1 %) | 0 (0.0 %) |

CR-034 (lost points): the detector S3 stores no lost points (0 lost object-frames). Readings (a) and (b) give identical results here too.

## 3. STEP 4: person-position diagnostic

**Diagnostic, tuning subset, not a reported result.**

116 tuning cameras; stored outputs: column B (oracle boxes, `full_camera`), column A, and the D-53 step 2 runs B-tune and B-sim-P. Classified only; no rule is recommended. Output: `research/m1b/d54_person_position.json`. Units: metres. Along: negative = toward the camera. Across is unsigned (D1).

### 3.1 (a) Person position error in column B

| group | object-frames | along median (signed) | along P05 | along P95 | |along| median | |across| median | error median | error P95 |
|---|---|---|---|---|---|---|---|---|
| all | 31043 | -0.130 | -0.362 | 1.000 | 0.163 | 0.039 | 0.188 | 1.015 |
| r: 0-2 | 410 | -0.231 | -0.445 | 0.338 | 0.303 | 0.079 | 0.339 | 0.476 |
| r: 10-20 | 2827 | 0.034 | -0.236 | 5.406 | 0.206 | 0.072 | 0.242 | 5.418 |
| r: 2-5 | 7157 | -0.116 | -0.368 | 0.110 | 0.132 | 0.026 | 0.146 | 0.428 |
| r: 5-10 | 20353 | -0.142 | -0.360 | 0.269 | 0.163 | 0.038 | 0.189 | 0.543 |
| r: >=20 | 296 | 76.114 | 15.533 | 642.293 | 76.114 | 1.231 | 76.157 | 642.434 |
| viewpoint: ceiling | 16200 | -0.142 | -0.365 | 0.671 | 0.167 | 0.055 | 0.199 | 0.698 |
| viewpoint: eye_level | 14843 | -0.107 | -0.351 | 2.408 | 0.154 | 0.029 | 0.173 | 2.415 |
| evidence state: occluded_predicted | 131 | -0.523 | -0.792 | -0.211 | 0.523 | 0.019 | 0.523 | 0.793 |
| evidence state: truncated | 7964 | -0.101 | -0.338 | 2.751 | 0.130 | 0.036 | 0.149 | 2.767 |
| evidence state: visible | 22948 | -0.140 | -0.364 | 0.897 | 0.170 | 0.041 | 0.194 | 0.908 |
| box clipped at bottom: False | 30662 | -0.130 | -0.362 | 1.024 | 0.163 | 0.039 | 0.188 | 1.034 |
| box clipped at bottom: True | 381 | -0.072 | -0.302 | 0.708 | 0.158 | 0.097 | 0.184 | 0.710 |

r = floor distance from the camera's floor point to the estimate. "Clipped at bottom" = oracle box bottom edge on the last pixel row (y2 ≥ H − 1).

### 3.2 (b) Along-sight error against the simulator person box

- Median signed along-sight error -0.130 m; median |along| 0.163 m (31043 object-frames).
- Simulator person box half-depth along the line of sight (half the projected extent of the 3D box's floor face): median 0.384 m (P05 0.266, P95 0.653). Half floor length median 0.328 m; half floor width median 0.266 m. Frames without a 3D box: 0.

### 3.3 (c) B-tune unmatched events with no counterpart in B-sim-P

B-tune unmatched 105, B-sim-P unmatched 63. D-54 does not define "counterpart" (**CR-035**), so both readings are given and neither is chosen. Neither reading gives 42, because B-sim-P also has unmatched events with no B-tune counterpart. Cause class: the BL-6 threshold the B value is below at the closest-approach frame while the B-sim-P value is not (d_p 2.0 m for the clearance, R2; d_pc 1.0 m for the predicted minimum clearance, R3).

**Reading 1** (a B-sim-P G1 event of the same pair with temporal IoU > 0):

- Events: **15** (by viewpoint: ceiling 9, eye_level 6).
- Cause class at the closest-approach frame: B below d_p and d_pc, B-sim-P not: 1; B clearance below d_p only, B-sim-P not: 4; B predicted minimum below d_pc only, B-sim-P not: 8; same side of d_p and d_pc in B and B-sim-P: 2.
- Providers fired (B-tune episode): R2: 3; R2+R3: 2; R2+R3+R4: 3; R3: 1; R3+R4: 6. R1 is not in BL-6.
- Episode start: clearance crosses d_p 5, clearance crosses d_pc 0, predicted minimum crosses d_pc 10; no neighbouring pair-frame 0.
- Episode end: clearance crosses d_p 6, clearance crosses d_pc 0, predicted minimum crosses d_pc 8; no neighbouring pair-frame 0.
- Person error at the closest-approach frame: along median -0.125 m (P05 -0.524, P95 0.110); |across| median 0.129 m.
- Clearance at that frame, median: B 1.970 m, B-sim-P 2.323 m, A 1.709 m; B − B-sim-P median -0.039 m (P05 -0.465, P95 0.131).

**Reading 2** (an unmatched B-sim-P G1 event of the same pair with temporal IoU > 0):

- Events: **50** (by viewpoint: ceiling 33, eye_level 17).
- Cause class at the closest-approach frame: B below d_p and d_pc, B-sim-P not: 1; B clearance below d_p only, B-sim-P not: 4; B predicted minimum below d_pc only, B-sim-P not: 20; same side of d_p and d_pc in B and B-sim-P: 25.
- Providers fired (B-tune episode): R2: 11; R2+R3: 9; R2+R3+R4: 23; R3: 1; R3+R4: 6. R1 is not in BL-6.
- Episode start: clearance crosses d_p 21, clearance crosses d_pc 1, predicted minimum crosses d_pc 30; no neighbouring pair-frame 3.
- Episode end: clearance crosses d_p 34, clearance crosses d_pc 3, predicted minimum crosses d_pc 14; no neighbouring pair-frame 5.
- Person error at the closest-approach frame: along median -0.210 m (P05 -0.579, P95 0.226); |across| median 0.066 m.
- Clearance at that frame, median: B 1.363 m, B-sim-P 1.480 m, A 1.181 m; B − B-sim-P median -0.099 m (P05 -0.523, P95 0.246).

### 3.4 (d) References B-sim-P matches and B-tune does not

At the closest-approach frame of the B-sim-P event. Cause class: the threshold the B-sim-P value is below while the B value is not.

- Events: **8** (by viewpoint: ceiling 7, eye_level 1).
- Cause class at the closest-approach frame: B-sim-P below d_p and d_pc, B not: 1; B-sim-P clearance below d_p only, B not: 2; same side of d_p and d_pc in B-sim-P and B: 5.
- Providers fired (B-sim-P episode): R2: 2; R2+R3: 2; R2+R3+R4: 4. R1 is not in BL-6.
- Episode start: clearance crosses d_p 6, clearance crosses d_pc 0, predicted minimum crosses d_pc 1; no neighbouring pair-frame 1.
- Episode end: clearance crosses d_p 7, clearance crosses d_pc 0, predicted minimum crosses d_pc 0; no neighbouring pair-frame 1.
- Person error at the closest-approach frame: along median 0.055 m (P05 -0.214, P95 1.363); |across| median 0.196 m.
- Clearance at that frame, median: B 1.674 m, B-sim-P 1.197 m, A 0.420 m; B − B-sim-P median 0.188 m (P05 -0.002, P95 1.367).
- B-tune events of the same pair overlapping these references: 1, 1, 2, 2, 1, 2, 2, 2.

