# Pre-registration v2: results and claims (write-up, D-66)

**Status:** synthetic-data evaluation; experimental. Every automated output is a **candidate** event. No output is a near miss, collision or contact, and nothing here is validated. This is RQ1 (E1, worker–forklift exposure). E2 is not part of it.

**Sources.** Every number below is taken from a committed results file:
- `research/v2/test_results.json` and `test_report.md`: the test run, decided in D-66;
- `research/v2/reporting_rerun_results.json` and `reporting_rerun_report.md`;
- `research/v2/ie_inputs_diag_tune.json`: the diagnostic.

Configuration: `docs/preregistration_v2_FROZEN.md`, contract E-1.2.26.

## 1. Scope

- **Synthetic data only.** All cameras are simulated warehouse recordings (SDG). No result is evidence about real establishments, real workers or real footage. Monitored time is not hours worked.
- **Test partition:** 471 cameras (ceiling 235, eye level 236) in 48 leakage groups.
  - It was run once, from commit f5e7d28, through the D-63 STEP 7 gate: X0c passed, the windows were locked, the reporting run had finished, and the test detections arrived with verified hashes.
  - It is closed (D-66). It will never be run or opened again.
- **Reporting partition:** 110 cameras in 11 leakage groups, **held out from v2 tuning**.
- **The first reporting run was defective, and this is disclosed (D-65, CR-042).**
  - What was wrong: the first run (commit d20fb82) found no object state for any stitched identity on the detector path. On that path M was unknown everywhere, R4 had no speeds, and R5 and the contact cue had no input.
  - What was done: the defect was fixed under CR-042 reading 1 (each member track's stored S4 state, nothing combined across a stitch gap). All 110 reporting cameras were then re-run once, at commit 107f14b.
  - The first run stays on record with its warning.
  - **The oracle and full_camera numbers of the reporting set were seen before the re-run.** They came out identical in the re-run.
- **BL-3 = BL-6 on SDG.** Adding R4, R5 and the contact cue to BL-3 changes nothing on the oracle path, on either partition. On the reporting detector path the difference is also 0.
  - On the test detector path, EV-M1 is unchanged (0.752), and EV-M2 moves from 0.623 to 0.619. BL-6 gives four more system events (572 vs 568), and false alerts per hour go from 163.7 to 166.8.
  - Paired BL-3 − BL-6 on the test detector path: EV-M2 0.004, Target B [0.000, 0.009]; EV-M7 −3.06, Target B [−6.76, 0.00].
  - So, on these data, BL-6 adds no measurable value over BL-3.
- **Matching and intervals:**
  - Matching: N4, label group G1. The headline is at iou_m 0.3; iou_m 0.5 and 0.7 are reported as well.
  - Target A: stratified window bootstrap.
  - Target B: cluster bootstrap over leakage groups.
  - Both use B = 2,000 and seed 2026111402.
- **Limitations:** the fifteen limitations of `docs/preregistration_v2_FROZEN.md` §10 and limitations 16–20 of `research/v2/reporting_plan.md` apply to every number here.

## 2. Results on the test partition

### 2.1 Headline: BL-6, detector path (iou_m 0.3)

EV-M1 and EV-M2 are descriptive. No success threshold is set (register C12).

| Slice | EV-M1 | Target B | EV-M2 | Target B | False alerts per hour (EV-M7) | Target B |
|---|---|---|---|---|---|---|
| All cameras (471) | 0.752 | [0.689, 0.806] | 0.619 | [0.577, 0.660] | 166.8 | [140.3, 192.8] |
| Ceiling (235) | 0.932 | [0.864, 0.983] | 0.725 | [0.683, 0.768] | 127.1 | [101.1, 154.7] |
| Eye level (236) | 0.572 | [0.496, 0.641] | 0.500 | [0.432, 0.567] | 206.3 | [165.3, 247.5] |

- Counts on all 471 cameras: 471 assessable references, 354 of them matched, and 572 system candidate events, of which 218 are false alerts. These come over 1.31 h of usable time.
- At iou_m 0.5: EV-M1 0.571, EV-M2 0.470.
- At iou_m 0.7: EV-M1 0.414, EV-M2 0.341.

### 2.2 Decomposition (BL-6, iou_m 0.3)

Oracle results are never substituted for detector-path capability.

| Column | EV-M1 | Target B | EV-M2 | Target B | False alerts per hour | Target B |
|---|---|---|---|---|---|---|
| A, oracle path (simulator positions) | 0.989 | [0.980, 0.998] | 0.957 | [0.938, 0.975] | 16.1 | [9.2, 23.4] |
| B, oracle boxes, full_camera geometry | 0.983 | [0.972, 0.994] | 0.935 | [0.913, 0.957] | 24.5 | [15.8, 33.6] |
| C, detector path | 0.752 | [0.689, 0.806] | 0.619 | [0.577, 0.660] | 166.8 | [140.3, 192.8] |

The loss is almost entirely between B and C: detection and tracking. Geometry adds little, as the step from A to B shows. The detector path loses most at eye level.

### 2.3 Registered criteria (registered slice: test; 48 leakage groups, at least the 20 required)

Each target is half the threshold it decides. A failed criterion is reported as failed, and no target is moved.

| Criterion | Rule | Target | Value | Target B | Decision |
|---|---|---|---|---|---|
| C1-MR-01 (repeatability) | exact equality | 1.0 | 1.000 (471 of 471 repeats identical) | — | **met** |
| C2-GV-01, ceiling (position RMSE, full_camera) | upper interval bound ≤ target | 0.25 m | 0.434 m | [0.407, 0.463] | **not met** |
| C2-GV-01, eye level | upper interval bound ≤ target | 0.25 m | 0.775 m | [0.685, 0.862] | **not met** |
| C3-GV-07 (speed RMSE at w_v 0.5 s, full_camera) | upper interval bound ≤ target | 0.15 m/s | 0.939 m/s | [0.826, 1.041] | **not met** |
| C4-GV-04 (bias at the simulator positions) | absolute bias interval within target | 0.10 m | 0.000 m | [0.000, 0.000] | met (circular: reported, never cited as evidence) |

**Three of the five registered criteria fail.**
- Position accuracy fails on both viewpoints.
- Speed accuracy fails.

The breakdown in `test_report.md` §4 locates the failures:
- Person speed error at eye level has an RMSE of 1.81 m/s; the forklift's is 0.34 m/s.
- Person position error at eye level has an RMSE of 0.98 m (median 0.19 m), so a few large errors dominate.

No speed outlier share is reported, because no cut was stated before the data were seen (CR-041 item 3, D-66).

### 2.4 Paired comparisons (iou_m 0.3; no decision rule registered, CR-041 item 2)

| Pair | Path | EV-M1 a − b | Target B | EV-M2 a − b | Target B | EV-M7 a − b (per hour) |
|---|---|---|---|---|---|---|
| BL-2 − BL-3 | oracle | −0.246 | [−0.305, −0.191] | −0.300 | [−0.351, −0.250] | +123.9 |
| BL-3 − BL-6 | oracle | 0.000 | [0.000, 0.000] | 0.000 | [0.000, 0.000] | 0.0 |
| BL-2 − BL-3 | detector | −0.410 | [−0.466, −0.353] | −0.331 | [−0.384, −0.281] | +133.9 |
| BL-3 − BL-6 | detector | 0.000 | [0.000, 0.000] | +0.004 | [0.000, 0.009] | −3.1 |

BL-2 is the image-only baseline, R1, in which M is always unknown. It falls well below BL-3 on both paths.

### 2.5 Insufficient evidence (IE) share of candidate events (BL-6)

| Column | Test | Reporting re-run |
|---|---|---|
| A | 0.754 | 0.782 |
| B | 0.782 | 0.829 |
| C | 0.781 | 0.697 |

## 3. Reporting partition (held out from v2 tuning; re-run once after the D-65 defect correction)

| BL-6, iou_m 0.3 | EV-M1 | Target B | EV-M2 | Target B | False alerts per hour |
|---|---|---|---|---|---|
| A, oracle path | 0.991 | [0.973, 1.000] | 0.991 | [0.973, 1.000] | 3.3 |
| B, oracle boxes, full_camera | 0.982 | [0.955, 1.000] | 0.973 | [0.931, 1.000] | 9.8 |
| C, detector path | 0.736 | [0.636, 0.827] | 0.570 | [0.480, 0.672] | 199.9 |

- MR-01 = 1.0 (110 of 110 repeats identical).
- With 11 leakage groups, below the 20 required, the GV criteria are not assessable here. The registered decisions are the test ones in §2.3.

## 4. Diagnostic: why candidate events are IE (post hoc, D-66; tuning cameras only)

Scope of this diagnostic:
- Post hoc, on the 116 tuning cameras only; no test data was used.
- It selects nothing and changes no value.
- Source: `research/v2/ie_inputs_diag_tune.json`, from commit 8ad6c61.

Method:
- The S5 per-frame inputs were recomputed from the stored S4 and had to reproduce the stored S5 exactly, which they did on 116 of 116 cameras.
- Each IE candidate event (S_VIEW) was then attributed to the parts of the IE rule that held, and to the inputs that were undetermined in its episode.
- An event counts as **coverage** when Q (S4 `q_state`) is not sufficient: one object is occluded, predicted or lost, an object is truncated, or the timing is uncertain.

| BL-6, tuning | IE events / events | IE share | Coverage at the closest approach | Coverage share > o_max | Contact not assessable | K undetermined (R5 unknown) |
|---|---|---|---|---|---|---|
| A, oracle path | 92 / 119 | 0.773 | 86 | 89 | 80 | 0 |
| C, detector path | 104 / 137 | 0.759 | 76 | 89 | 32 | 5 |

| BL-6, tuning: undetermined somewhere in the IE episode | M | R4 | R5 | Contact cue | Coverage |
|---|---|---|---|---|---|
| A (92 IE events) | 1 | 1 | 1 | 0 | 92 |
| C (104 IE events) | 3 | 26 | 36 | 7 | 103 |

The counts are non-exclusive. What the diagnostic shows:
- On the oracle path every IE event fails a coverage condition. At eye level 64 of 65 candidate events are IE, which is pair evidence that is not sufficient, not missing kinematics.
- On the detector path, 102 of 104 IE events fail a coverage condition. Only 2 are IE solely because K is undetermined, through an unknown R5 (E).
- M is almost never the cause after the CR-042 fix. It is undetermined in 3 of 104 IE events on C.
- On BL-2, M is undetermined on every event by design (R1).

This is a tuning-set description only. It is not a reported result, and it changes no rule.

## 5. Claims permitted by these results

- On synthetic data (SDG test, 471 cameras), the experimental detector path finds 0.752 of the reference exposure events (EV-M1). It does so at 166.8 false candidate events per hour of usable time, and it is markedly better from ceiling cameras than at eye level.
- The same pipeline run on simulator positions (A) or oracle boxes (B) finds 0.98–0.99 of the reference events. The gap is in detection and tracking.
- The instrument is exactly repeatable: MR-01 = 1.0 on 471 test cameras.
- The instrument **does not meet** its registered position-accuracy criteria (ceiling or eye level) or its speed-accuracy criterion on this synthetic data. No claim that depends on metric position or speed accuracy at the registered tolerances is supported.
- On SDG, BL-6 is equal to BL-3 (§1). No benefit of the R4 / R5 / contact-cue additions is shown.
- Most candidate events (0.70–0.83 by column and partition) carry IE. On the tuning cameras the diagnostic attributes this almost entirely to insufficient pair coverage.

## 6. Claims not made

- Nothing about real warehouses, real workers or real footage. No safety score, ranking, recordability or OSHA claim.
- No candidate event is called a near miss, collision or contact.
- No result is called validated.
- No threshold or target was moved after the data were seen. The reporting partition is described as held out from v2 tuning, not as independent of every earlier decision, because the oracle and full_camera numbers of the first reporting run were seen before the re-run.
