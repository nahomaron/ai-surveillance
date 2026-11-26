# D-58: event continuity (T25) on the tuning cameras

**Diagnostic, tuning subset, not a reported result.**

Source data: synthetic SDG validation, the 116 tuning cameras only (D-50 item 3). Nothing here is validated. Nothing ran on the 110 reporting cameras or the test partition (D-37). Contract E-1.2.26 (Appendix T T25), v1 base values otherwise; tracker package D-56 and T24 values D-54 (selected, not frozen). Outputs: `research/m1b/t25_regression.json`, `research/m1b/d58_stitch_grid.json`, `research/m1b/d58_events_tune.json`.

## Summary

1. T25 is implemented opt-in (contract E-1.2.26). With its parameters absent, every stored D-54 and D-57 artifact rebuilds byte-identical on 116 of 116 tuning cameras, and the 12 M0 IDs are reproduced.
2. Track stitching (T25.1), chosen by tracking measures only: **T_s 5 s, r_g 0.5 m, selected, not frozen** (at the edge of the grid). Person IDF1 0.846 → 0.919; forklift 0.774 → 0.780.
3. Detector path, EV-M1 / EV-M2 under α (m_gap 5 frames): C-v2 0.578 / 0.329 → C-v2+T25 0.600 / 0.411. All of this gain comes from stitching.
4. Under α, T25.2 joins nothing on any path. A POW break needs a gap above g_max (15 frames), and the α join limit is 5 frames. T25.2 can act only when m_gap_s is at least (g_max + 1) × δ_nom, which is 0.53 s here.
5. Under β (1.0 s for system and references alike): C-v2 0.653 / 0.438; C-v2+T25 0.677 / 0.525, with 21 joined events holding 15.6 s of unobserved time.
6. The oracle check is clean under β: A EV-M1 stays 1.000 and B-both is 0.935 (α 0.926). This fits D-57's explanation: there, m_gap changed on the system side only.
7. Remaining C-v2+T25 splits under β: (i) 0, (ii) 36, (iii) 16. They were 43 / 30 / 42 on C-v2 under α: stitching turns (iii) into (ii). The (ii) splits that remain are not joined at 1.0 s (the gap is longer, or a T = 1 frame or a coverage break lies in it).
8. CR-037 (the contact state, IE and pair of a joined event) is open. Both pair readings give the same pair for every event, and the label rule questions do not touch G1.
9. N4, the label rules, the EV definitions and the stored base references are unchanged. The β set is a separate diagnostic set. Nothing ran on the 110 reporting cameras or the test partition.

## 1. STEP 2: implementation and regression

T25.1 (`rq1.tracking.stitching`; S4 pairs stitched identities), T25.2 (`rq1.events.candidates.join_chains`, `joined_events`, `continuity_links`) and T25.3 (`rq1.events.engine.m_gap_frames`) are implemented opt-in. Every T25.4 check is a test (`tests/substrate/test_t25_stitching.py`, `tests/events/test_t25_join.py`). Representation: AR-69. Open meaning questions: CR-037.

| configuration | S4 | S5 (D-54) | S5 (D-57 m_gap 5) |
|---|---|---|---|
| C-v2 | 116 / 116 | 116 / 116 | 116 / 116 |
| B-both | 116 / 116 | 116 / 116 | 116 / 116 |
| A | 116 / 116 | 116 / 116 | 116 / 116 |

Byte-identical rebuilds (payload SHA-256 and artifact ID) with the T25 parameters absent. M0 (W-02 method, AR-69 item 11): the 12 IDs and payload hashes equal the M0 report, in two runs. The fixture export's `data_dictionary.json` lists the two new optional `candidate_event` properties (AR-69 item 10).

## 2. STEP 3: track stitching (T25.1), selected by tracking measures

**Diagnostic, tuning subset, not a reported result.**

Input: the D-56 package tracks (stored D-54 detector S3) on the 116 tuning cameras; floor positions from the stored C-v2 S4 (T24 on; AR-69 item 9). v_max person 2.5 m/s, forklift 4.0 m/s and k_img 1.0 are fixed design values (D-58), not fitted. Measures: D-55 definitions on stitched identities (primary variant: tracked points). Stitching creates no point, so point precision is the same in every row.

| configuration | T_s (s) | r_g (m) | links forklift / person | gate floor / image | forklift IDF1 | person IDF1 | objective | forklift fragments / identity | person fragments / identity | point precision forklift / person |
|---|---|---|---|---|---|---|---|---|---|---|
| off | – | – | 0 / 0 | 0 / 0 | 0.7744 | 0.8457 | 1.6201 | 1.062 | 1.724 | 0.979 / 0.995 |
| Ts1_rg0.5 | 1 | 0.5 | 1 / 39 | 27 / 13 | 0.7754 | 0.8658 | 1.6412 | 1.054 | 1.422 | 0.979 / 0.995 |
| Ts1_rg1 | 1 | 1 | 1 / 42 | 31 / 12 | 0.7754 | 0.8707 | 1.6462 | 1.054 | 1.397 | 0.979 / 0.995 |
| Ts1_rg2 | 1 | 2 | 1 / 45 | 34 / 12 | 0.7754 | 0.8720 | 1.6474 | 1.054 | 1.371 | 0.979 / 0.995 |
| Ts2_rg0.5 | 2 | 0.5 | 2 / 64 | 48 / 18 | 0.7791 | 0.9087 | 1.6878 | 1.045 | 1.216 | 0.979 / 0.995 |
| Ts2_rg1 | 2 | 1 | 2 / 64 | 50 / 16 | 0.7791 | 0.9133 | 1.6925 | 1.045 | 1.216 | 0.979 / 0.995 |
| Ts2_rg2 (kept) | 2 | 2 | 2 / 68 | 54 / 16 | 0.7791 | 0.9211 | 1.7003 | 1.045 | 1.181 | 0.979 / 0.995 |
| Ts3_rg0.5 | 3 | 0.5 | 2 / 67 | 52 / 17 | 0.7791 | 0.9132 | 1.6923 | 1.045 | 1.198 | 0.979 / 0.995 |
| Ts3_rg1 (kept) | 3 | 1 | 2 / 66 | 53 / 15 | 0.7791 | 0.9161 | 1.6952 | 1.045 | 1.198 | 0.979 / 0.995 |
| Ts3_rg2 (kept) | 3 | 2 | 2 / 69 | 56 / 15 | 0.7791 | 0.9205 | 1.6996 | 1.045 | 1.172 | 0.979 / 0.995 |
| Ts5_rg0.5 **(selected)** | 5 | 0.5 | 6 / 71 | 58 / 19 | 0.7802 | 0.9189 | 1.6991 | 1.018 | 1.172 | 0.979 / 0.995 |
| Ts5_rg1 (kept) | 5 | 1 | 6 / 70 | 59 / 17 | 0.7802 | 0.9201 | 1.7003 | 1.018 | 1.181 | 0.979 / 0.995 |
| Ts5_rg2 (kept) | 5 | 2 | 6 / 73 | 62 / 17 | 0.7802 | 0.9249 | 1.7052 | 1.018 | 1.155 | 0.979 / 0.995 |

**Rule (pre-declared):** guard point precision ≥ 0.95 per class (all 13 pass); objective forklift + person IDF1 (best 1.7052); keep within 0.01 of the best (Ts2_rg2, Ts3_rg1, Ts3_rg2, Ts5_rg0.5, Ts5_rg1, Ts5_rg2); then fewer forklift fragments per identity, then smaller T_s, then smaller r_g. **Selected: Ts5_rg0.5 (T_s 5 s, r_g 0.5 m), selected under D-58, not frozen.**

T_s 5 s is the largest value of the grid: the selection sits at the grid edge. Checks: stitching off reproduces the stored D-55 measures on 116 of 116 cameras.

By viewpoint (off → selected):

| view | cameras | forklift IDF1 | person IDF1 | forklift fragments / identity | person fragments / identity | links forklift / person |
|---|---|---|---|---|---|---|
| all | 116 | 0.7744 → 0.7802 | 0.8457 → 0.9189 | 1.062 → 1.018 | 1.724 → 1.172 | 6 / 71 |
| ceiling | 54 | 0.9037 → 0.9108 | 0.8477 → 0.9244 | 1.019 → 1.000 | 1.556 → 1.148 | 1 / 23 |
| eye level | 62 | 0.6327 → 0.6372 | 0.8435 → 0.9130 | 1.103 → 1.034 | 1.871 → 1.194 | 5 / 48 |

**Plainly:** stitching joins 71 person and 6 forklift fragments. Person IDF1 rises 0.846 → 0.919; forklift IDF1 0.774 → 0.780. Forklift identities are rarely fragmented (1.06 fragments per identity without stitching), so there are few forklift links to make.

## 3. STEP 4: event-level check (diagnostic)

**Diagnostic, tuning subset, not a reported result.**

All configurations: BL-6, N4 (unchanged), label group G1. B-both and A without T25 are added for comparison. T25.1 is off on the oracle paths (T25.1 f). C-v2+T25 uses the STEP 3 winner (Ts5_rg0.5; 77 links: 6 forklift, 71 person).

Event definitions: **α**: m_gap 5 frames for the system and the stored base references (T21). **β**: m_gap_s 1.0 s for the system and for a reference set rebuilt from simulator truth with m_gap_s 1.0 (T21.1 procedure). The β set is **diagnostic, not the v2 reference**; 1.0 s is a placeholder for this check only, not a v2 candidate. With T25.2 on under α, the join limit is 5 frames × δ_nom (0.17 s at 30 fps).

References:

| definition | references | assessable, G1 |
|---|---|---|
| α (m_gap 5 frames) | 137 | 135 |
| β (m_gap_s 1.0 s) | 125 | 124 |

### 3.1 EV-M1 and EV-M2 (all 116 cameras)

| configuration | definition | EV-M1 | EV-M2 | assessable references | matched references | system events (G1) | matched events |
|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | 0.578 | 0.329 | 135 | 78 | 237 | 78 |
| C-v2 | β (m_gap_s 1.0 s) | 0.653 | 0.438 | 124 | 81 | 185 | 81 |
| C-v2+T25 | α (m_gap 5 frames) | 0.600 | 0.411 | 135 | 81 | 197 | 81 |
| C-v2+T25 | β (m_gap_s 1.0 s) | 0.677 | 0.525 | 124 | 84 | 160 | 84 |
| B-both | α (m_gap 5 frames) | 0.926 | 0.571 | 135 | 125 | 219 | 125 |
| B-both | β (m_gap_s 1.0 s) | 0.935 | 0.841 | 124 | 116 | 138 | 116 |
| B-both+T25 | α (m_gap 5 frames) | 0.926 | 0.571 | 135 | 125 | 219 | 125 |
| B-both+T25 | β (m_gap_s 1.0 s) | 0.935 | 0.847 | 124 | 116 | 137 | 116 |
| A | α (m_gap 5 frames) | 1.000 | 0.944 | 135 | 135 | 143 | 135 |
| A | β (m_gap_s 1.0 s) | 1.000 | 0.932 | 124 | 124 | 133 | 124 |
| A+T25 | α (m_gap 5 frames) | 1.000 | 0.944 | 135 | 135 | 143 | 135 |
| A+T25 | β (m_gap_s 1.0 s) | 1.000 | 0.961 | 124 | 124 | 129 | 124 |

CR-037 item 3: the two pair readings (a) and (b) give the same pair for every event (0 events differ over all rows), so every EV value above holds under both readings; no value depends on a choice.

### 3.2 EV-M1 and EV-M2, ceiling (54 cameras)

| configuration | definition | EV-M1 | EV-M2 | assessable references | matched references | system events (G1) | matched events |
|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | 0.781 | 0.368 | 64 | 50 | 136 | 50 |
| C-v2 | β (m_gap_s 1.0 s) | 0.847 | 0.505 | 59 | 50 | 99 | 50 |
| C-v2+T25 | α (m_gap 5 frames) | 0.797 | 0.468 | 64 | 51 | 109 | 51 |
| C-v2+T25 | β (m_gap_s 1.0 s) | 0.864 | 0.593 | 59 | 51 | 86 | 51 |
| B-both | α (m_gap 5 frames) | 0.953 | 0.587 | 64 | 61 | 104 | 61 |
| B-both | β (m_gap_s 1.0 s) | 0.932 | 0.887 | 59 | 55 | 62 | 55 |
| B-both+T25 | α (m_gap 5 frames) | 0.953 | 0.587 | 64 | 61 | 104 | 61 |
| B-both+T25 | β (m_gap_s 1.0 s) | 0.932 | 0.887 | 59 | 55 | 62 | 55 |
| A | α (m_gap 5 frames) | 1.000 | 1.000 | 64 | 64 | 64 | 64 |
| A | β (m_gap_s 1.0 s) | 1.000 | 1.000 | 59 | 59 | 59 | 59 |
| A+T25 | α (m_gap 5 frames) | 1.000 | 1.000 | 64 | 64 | 64 | 64 |
| A+T25 | β (m_gap_s 1.0 s) | 1.000 | 1.000 | 59 | 59 | 59 | 59 |

### 3.3 EV-M1 and EV-M2, eye level (62 cameras)

| configuration | definition | EV-M1 | EV-M2 | assessable references | matched references | system events (G1) | matched events |
|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | 0.394 | 0.277 | 71 | 28 | 101 | 28 |
| C-v2 | β (m_gap_s 1.0 s) | 0.477 | 0.360 | 65 | 31 | 86 | 31 |
| C-v2+T25 | α (m_gap 5 frames) | 0.423 | 0.341 | 71 | 30 | 88 | 30 |
| C-v2+T25 | β (m_gap_s 1.0 s) | 0.508 | 0.446 | 65 | 33 | 74 | 33 |
| B-both | α (m_gap 5 frames) | 0.901 | 0.557 | 71 | 64 | 115 | 64 |
| B-both | β (m_gap_s 1.0 s) | 0.938 | 0.803 | 65 | 61 | 76 | 61 |
| B-both+T25 | α (m_gap 5 frames) | 0.901 | 0.557 | 71 | 64 | 115 | 64 |
| B-both+T25 | β (m_gap_s 1.0 s) | 0.938 | 0.813 | 65 | 61 | 75 | 61 |
| A | α (m_gap 5 frames) | 1.000 | 0.899 | 71 | 71 | 79 | 71 |
| A | β (m_gap_s 1.0 s) | 1.000 | 0.878 | 65 | 65 | 74 | 65 |
| A+T25 | α (m_gap 5 frames) | 1.000 | 0.899 | 71 | 71 | 79 | 71 |
| A+T25 | β (m_gap_s 1.0 s) | 1.000 | 0.929 | 65 | 65 | 70 | 65 |

### 3.4 System events, members and unobserved time (all cameras)

Joined events are reported as joined, with their unobserved time (the summed gaps between members; never counted as exposure or as clearance-measured time, T25.2 c).

| configuration | definition | system events (all labels) | member episodes | members per event | events with 1 / 2 / 3 / ≥ 4 members | joined events | unobserved time (s) |
|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | 237 | 237 | 1.000 | 237 / 0 / 0 / 0 | 0 | 0.0 |
| C-v2 | β (m_gap_s 1.0 s) | 185 | 185 | 1.000 | 185 / 0 / 0 / 0 | 0 | 0.0 |
| C-v2+T25 | α (m_gap 5 frames) | 197 | 197 | 1.000 | 197 / 0 / 0 / 0 | 0 | 0.0 |
| C-v2+T25 | β (m_gap_s 1.0 s) | 160 | 182 | 1.137 | 139 / 20 / 1 / 0 | 21 | 15.6 |
| B-both | α (m_gap 5 frames) | 219 | 219 | 1.000 | 219 / 0 / 0 / 0 | 0 | 0.0 |
| B-both | β (m_gap_s 1.0 s) | 138 | 138 | 1.000 | 138 / 0 / 0 / 0 | 0 | 0.0 |
| B-both+T25 | α (m_gap 5 frames) | 219 | 219 | 1.000 | 219 / 0 / 0 / 0 | 0 | 0.0 |
| B-both+T25 | β (m_gap_s 1.0 s) | 137 | 138 | 1.007 | 136 / 1 / 0 / 0 | 1 | 0.9 |
| A | α (m_gap 5 frames) | 143 | 143 | 1.000 | 143 / 0 / 0 / 0 | 0 | 0.0 |
| A | β (m_gap_s 1.0 s) | 133 | 133 | 1.000 | 133 / 0 / 0 / 0 | 0 | 0.0 |
| A+T25 | α (m_gap 5 frames) | 143 | 143 | 1.000 | 143 / 0 / 0 / 0 | 0 | 0.0 |
| A+T25 | β (m_gap_s 1.0 s) | 129 | 133 | 1.031 | 125 / 4 / 0 / 0 | 4 | 3.1 |

### 3.5 Unmatched events by best same-pair temporal IoU (all cameras)

Unmatched = false or duplicate alerts (G1). Band = best temporal IoU with a same-pair assessable G1 reference (`extent_check` bands).

| configuration | definition | unmatched | (0, 0.1] | (0.1, 0.2] | (0.2, 0.3) | 0 | >= 0.3 | with same-pair overlap |
|---|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | 159 | 66 | 47 | 34 | 10 | 2 | 149 |
| C-v2 | β (m_gap_s 1.0 s) | 104 | 39 | 32 | 22 | 3 | 8 | 101 |
| C-v2+T25 | α (m_gap 5 frames) | 116 | 38 | 43 | 27 | 7 | 1 | 109 |
| C-v2+T25 | β (m_gap_s 1.0 s) | 76 | 24 | 26 | 16 | 2 | 8 | 74 |
| B-both | α (m_gap 5 frames) | 94 | 44 | 21 | 17 | 7 | 5 | 87 |
| B-both | β (m_gap_s 1.0 s) | 22 | 6 | 4 | 5 | 3 | 4 | 19 |
| B-both+T25 | α (m_gap 5 frames) | 94 | 44 | 21 | 17 | 7 | 5 | 87 |
| B-both+T25 | β (m_gap_s 1.0 s) | 21 | 6 | 3 | 5 | 3 | 4 | 18 |
| A | α (m_gap 5 frames) | 8 | 0 | 3 | 2 | 0 | 3 | 8 |
| A | β (m_gap_s 1.0 s) | 9 | 1 | 3 | 2 | 0 | 3 | 9 |
| A+T25 | α (m_gap 5 frames) | 8 | 0 | 3 | 2 | 0 | 3 | 8 |
| A+T25 | β (m_gap_s 1.0 s) | 5 | 1 | 2 | 0 | 0 | 2 | 5 |

### 3.6 Remaining splits (the D-57 mechanisms, on events)

A split = two consecutive same-pair events covering one assessable G1 reference. (i) the boundary members are in one POW; (ii) other POWs of the same pair units (tracks, or stitched identities); (iii) other units.

| configuration | definition | view | references with ≥ 2 events | splits | (i) | (ii) | (iii) |
|---|---|---|---|---|---|---|---|
| C-v2 | α (m_gap 5 frames) | all | 69 | 115 | 43 | 30 | 42 |
| C-v2 | α (m_gap 5 frames) | ceiling | 42 | 73 | 31 | 18 | 24 |
| C-v2 | α (m_gap 5 frames) | eye level | 27 | 42 | 12 | 12 | 18 |
| C-v2 | β (m_gap_s 1.0 s) | all | 54 | 75 | 1 | 30 | 44 |
| C-v2 | β (m_gap_s 1.0 s) | ceiling | 30 | 43 | 1 | 18 | 24 |
| C-v2 | β (m_gap_s 1.0 s) | eye level | 24 | 32 | 0 | 12 | 20 |
| C-v2+T25 | α (m_gap 5 frames) | all | 54 | 80 | 11 | 53 | 16 |
| C-v2+T25 | α (m_gap 5 frames) | ceiling | 31 | 49 | 8 | 33 | 8 |
| C-v2+T25 | α (m_gap 5 frames) | eye level | 23 | 31 | 3 | 20 | 8 |
| C-v2+T25 | β (m_gap_s 1.0 s) | all | 40 | 52 | 0 | 36 | 16 |
| C-v2+T25 | β (m_gap_s 1.0 s) | ceiling | 24 | 30 | 0 | 22 | 8 |
| C-v2+T25 | β (m_gap_s 1.0 s) | eye level | 16 | 22 | 0 | 14 | 8 |
| B-both | α (m_gap 5 frames) | all | 64 | 87 | 81 | 6 | 0 |
| B-both | α (m_gap 5 frames) | ceiling | 33 | 40 | 40 | 0 | 0 |
| B-both | α (m_gap 5 frames) | eye level | 31 | 47 | 41 | 6 | 0 |
| B-both | β (m_gap_s 1.0 s) | all | 16 | 17 | 10 | 7 | 0 |
| B-both | β (m_gap_s 1.0 s) | ceiling | 4 | 4 | 4 | 0 | 0 |
| B-both | β (m_gap_s 1.0 s) | eye level | 12 | 13 | 6 | 7 | 0 |
| B-both+T25 | α (m_gap 5 frames) | all | 64 | 87 | 81 | 6 | 0 |
| B-both+T25 | α (m_gap 5 frames) | ceiling | 33 | 40 | 40 | 0 | 0 |
| B-both+T25 | α (m_gap 5 frames) | eye level | 31 | 47 | 41 | 6 | 0 |
| B-both+T25 | β (m_gap_s 1.0 s) | all | 16 | 16 | 10 | 6 | 0 |
| B-both+T25 | β (m_gap_s 1.0 s) | ceiling | 4 | 4 | 4 | 0 | 0 |
| B-both+T25 | β (m_gap_s 1.0 s) | eye level | 12 | 12 | 6 | 6 | 0 |
| A | α (m_gap 5 frames) | all | 8 | 8 | 0 | 8 | 0 |
| A | α (m_gap 5 frames) | ceiling | 0 | 0 | 0 | 0 | 0 |
| A | α (m_gap 5 frames) | eye level | 8 | 8 | 0 | 8 | 0 |
| A | β (m_gap_s 1.0 s) | all | 9 | 9 | 0 | 9 | 0 |
| A | β (m_gap_s 1.0 s) | ceiling | 0 | 0 | 0 | 0 | 0 |
| A | β (m_gap_s 1.0 s) | eye level | 9 | 9 | 0 | 9 | 0 |
| A+T25 | α (m_gap 5 frames) | all | 8 | 8 | 0 | 8 | 0 |
| A+T25 | α (m_gap 5 frames) | ceiling | 0 | 0 | 0 | 0 | 0 |
| A+T25 | α (m_gap 5 frames) | eye level | 8 | 8 | 0 | 8 | 0 |
| A+T25 | β (m_gap_s 1.0 s) | all | 5 | 5 | 0 | 5 | 0 |
| A+T25 | β (m_gap_s 1.0 s) | ceiling | 0 | 0 | 0 | 0 | 0 |
| A+T25 | β (m_gap_s 1.0 s) | eye level | 5 | 5 | 0 | 5 | 0 |

Checks: C-v2 under α equals D-54 (EV values and counts: True) and its splits equal D-57 ({'i': 43, 'ii': 30, 'iii': 42} = {'i': 43, 'ii': 30, 'iii': 42}). The β reference procedure at m_gap 5 reproduces the stored reference S5 payload and reference list on 116 of 116 cameras. Two independent runs gave identical per-camera results and artifact IDs on 116 of 116 cameras.

## 4. Limits

- Synthetic SDG data, tuning subset: these values select and diagnose; they are not reported results and are not validated.
- The stitching winner and the β value 1.0 s are not frozen. The v2 m_gap_s comes from the literature (item C7) or a stated design choice, never from these scores (D-58 ruling 1).
- The D-56 caveat holds: the package accepts forklift detections down to score 0.05; point precision is known on synthetic SDG data only.
- Joined events are candidate events. Their members and unobserved time are part of the record; no automated output is called a near miss, collision or contact.
