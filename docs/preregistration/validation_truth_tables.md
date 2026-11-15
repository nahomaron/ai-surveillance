# Truth-side tables on the validation runs (D-34 item B.8)

**What this is.** The pre-registration draft's §5 (not-visible run lengths, POW counts) and §6.1 (forklift yaw rate) tables, recomputed on the **validation partition** of the frozen split (`art_w5v3ldr43xdsqc6l4zifmjkuuj`) and shown beside the all-runs tables. Also shown: the forklift 3D-box sizes behind the footprint priors. **Truth-side statistics only:** no S5 or S8 run, no system output, no metric against a reference. **No value was re-chosen** (D-34 B.8).

Sources: `docs/preregistration/validation_truth_tables.json`, built by `research/preregistration/validation_truth_tables.py` from the T17.7 counts under T20.1 (code commit 9a0674e, contract E-1.2.18) and the SDG `ceiling_00` annotation files. The yaw estimator is the draft's, unchanged. The all-runs columns reproduce the draft's figures exactly. Percentiles are nearest-rank. Run lengths are counted in eligible frames (T19, T20.1); 30 frames = 1 s.

**SmartSpaces.** The whole synthetic leakage group is validation, and the draft's SmartSpaces tables were computed on Warehouse_000 truth. Its validation tables are therefore **identical to the all-runs tables** (recomputed from the per-camera counts: same values). They are not repeated below.

**SDG validation partition:** 24 runs, 240 cameras, 226 with an oracle track (14 without usable truth, T17.4). For yaw and box size: 23 of the 24 runs have a `ceiling_00` annotation (all-runs: 67 of 72).

## 1. Not-visible run lengths, SDG (§5.1)

| Class | Partition | Runs | Frames in runs | Min | Median | P90 | P99 | Max |
|---|---|---|---|---|---|---|---|---|
| forklift | validation | 51 | 84 | 0 | 1 | 1 | 17 | 17 |
| forklift | all runs | 162 | 344 | 0 | 1 | 1 | 38 | 68 |
| person | validation | 131 | 1,265 | 0 | 2 | 27 | 79 | 141 |
| person | all runs | 388 | 4,848 | 0 | 3 | 38 | 122 | 141 |

Share of runs / share of not-visible frames in runs of at most the given length:

| Class | Partition | ≤ 5 | ≤ 15 | ≤ 30 | ≤ 60 | ≤ 150 |
|---|---|---|---|---|---|---|
| forklift | validation | 94.1 % / 53.6 % | 98.0 % / 79.8 % | 100 % / 100 % | 100 % / 100 % | 100 % / 100 % |
| forklift | all runs | 94.4 % / 38.4 % | 96.9 % / 51.5 % | 98.8 % / 69.2 % | 99.4 % / 80.2 % | 100 % / 100 % |
| person | validation | 64.1 % / 9.6 % | 82.4 % / 27.6 % | 90.8 % / 45.9 % | 97.7 % / 77.2 % | 100 % / 100 % |
| person | all runs | 58.0 % / 7.1 % | 76.5 % / 21.4 % | 86.1 % / 37.9 % | 96.1 % / 72.0 % | 100 % / 100 % |

(The all-runs forklift row has 162 runs, not the draft's 160: T20.1 adds two runs of length 0, see the Progress log of 14 Nov 2026. Percentiles and shares are unchanged.)

## 2. POWs and POWs ended by `gap_exceeded`, SDG (§5.2; sensitivity evidence, counts only)

| g_max | Validation: POWs | Validation: ended by gap_exceeded | All runs: POWs | All runs: ended by gap_exceeded |
|---|---|---|---|---|
| 5 | 275 | 49 | 864 | 167 |
| **15** | **249** | **23** | **790** | **93** |
| 30 | 237 | 11 | 750 | 53 |
| 60 | 228 | 2 | 710 | 13 |

## 3. Forklift yaw rate, SDG (§6.1)

Rates in degrees per second; share of forklift frames (count).

| Window | Partition | Frames | < 1 | 1 to < 5 | 5 to < 20 | 20 to < 120 | ≥ 120 | P50 | P90 | P99 | Max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 s | validation | 6,881 | 58.8 % (4,047) | 0.9 % (60) | 2.9 % (198) | 37.4 % (2,576) | 0 | 0.0 | 75.0 | 75.0 | 84.4 |
| 0.5 s | all runs | 20,081 | 55.9 % (11,226) | 0.8 % (164) | 2.8 % (568) | 40.5 % (8,123) | 0 | 0.0 | 75.0 | 75.0 | 84.4 |
| 1.0 s | validation | 6,881 | 53.2 % (3,660) | 1.8 % (125) | 5.6 % (386) | 39.4 % (2,710) | 0 | 0.0 | 75.0 | 75.0 | 83.1 |
| 1.0 s | all runs | 20,081 | 50.3 % (10,105) | 1.7 % (350) | 5.7 % (1,146) | 42.2 % (8,480) | 0 | 0.0 | 75.0 | 75.0 | 83.1 |

## 4. Forklift 3D-box size, SDG

| Partition | Boxes | Size (long × short) |
|---|---|---|
| validation | 6,881 | 3.03 × 1.13 m on every box |
| all runs | 20,081 | 3.03 × 1.13 m on every box |

## 5. Does the stated basis still hold?

| Value | Stated basis | On the validation runs |
|---|---|---|
| g_max = 15 frames | a 0.5 s short-occlusion rationale, **not fitted** to the run-length tables (D-34 B.1) | The basis does not rest on these tables, so they cannot overturn it, and nothing in them contradicts it. On validation, 98.0 % of forklift runs and 82.4 % of person runs are at most 15 frames (all runs: 96.9 % and 76.5 %). The longest validation runs are 17 frames (forklift) and 141 frames (person). **Holds.** |
| e_fturn = 5°/s (w_turn = 0.5 s) | lies between the two peaks of the truth yaw rate (no rotation; turning at about 75°/s in SDG, 24°/s in SmartSpaces); under 1 % of frames between 1°/s and the threshold | SDG validation is two-peaked as before: P50 0, P90 = P99 = 75°/s; 0.9 % of frames (60) between 1 and 5°/s (all runs 0.8 %). SmartSpaces identical by construction (0.9 %). **Holds.** |
| SDG forklift footprint 3.03 × 1.13 m | the dataset's own 3D box | every one of the 6,881 validation boxes is 3.03 × 1.13 m. **Holds.** |
| SmartSpaces forklift footprint 2.68 × 1.16 m (one prior) | one of the two box sizes in Warehouse_000 (D-34 B.5) | Warehouse_000 is the validation group: identical by construction (box sizes 2.68 × 1.16 m and 1.87 × 1.13 m). **Holds** as stated; GV-04 reports the bias per box size. |
