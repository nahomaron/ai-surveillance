# RQ1 pre-registration — FROZEN (M1a, version 1)

**Status: FROZEN at G-PR.** Owner decisions D-34 and D-35 (14 Nov 2026); Architect rulings of 14 Nov 2026 (Appendix T T20). This document records the Owner's values; the agent wrote it from those decisions and chose no scientific value. Any change is a new version of this document with a stated reason, made before the affected evaluation; results under different versions are never mixed.

| Item | Value |
|---|---|
| Contract | **E-1.2.18** (E-1.2.1 FROZEN, F.1 Part A and Appendix N, Appendix T up to T20) |
| Analysis code commit | `0e95e77a72afa6d0831805c5a65812ad87bebfdf` |
| `requirements.lock` SHA-256 | `228ef036e3d741429ce8683b6035900a83aca0cd28d34661ba0233779c6e971d` |
| frozen_utc | 2026-11-15T01:47:59Z (14 Nov 2026 local time) |
| Freeze record (all IDs, run lists, criterion records) | `docs/preregistration/freeze_record.json`, built by `research/preregistration/freeze.py` from `src/rq1/pipeline/prereg.py` (reproduced twice, identical) |
| Scope | Milestone M1a (WP-14): single-camera runs with oracle perception on the synthetic datasets held on 14 Nov 2026 |

**Wording.** Results on synthetic data are "implemented" or "verified", never "validated". Synthetic data cannot reach `technically_validated` (T12.5, FT-01): every M1a fitness record is `experimental` or `not_yet_assessable`. Automated outputs are "candidate", "suspected" or "undetermined".

**Status of the parameter values.** Every base value and grid in §4 is recorded as an **exploratory design assumption (not evidence-derived; to be reviewed against literature before publication)** (D-34 item B.4), unless the row states another basis.

**No S5 or S8 run has been made on any partition.** The validation run needs a separate go-ahead from the Owner (D-34 item C.4).

---

## 1. Data and populations

| Dataset row (T16) | data_origin | Held | In M1a |
|---|---|---|---|
| SDG-Warehouse near-miss (`nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes`) | synthetic_rendered | 72 runs, 720 recordings, 300 frames each at 30 fps (10 s) | 697 cameras with usable truth (T17.4); the 23 without are outside the oracle and reference populations and the sampling frame |
| SmartSpaces `MTMC_Tracking_2026` `Warehouse_000` | synthetic_rendered | 19 recordings, 9,000 frames each (300 s) | all 19, validation |
| SmartSpaces `Warehouse_001` (Cosmos Transfer re-render of 000) | synthetic_transferred | 19 recordings, same truth and calibration as 000 | **not used in M1a; kept for M1b** (D-34 item B.10) |
| SmartSpaces `Warehouse_026`, `Warehouse_027` | real_staged | 11 recordings | none; outside this pre-registration |
| Safe and Unsafe Behaviours | real | held under D-24 | none in M1a |

**Oracle-path runs use SmartSpaces `Warehouse_000` only.** `Warehouse_001` has identical truth and calibration and is kept for M1b (D-34 item B.10).

Rules that follow from the contract: results are never pooled across data origins (VR-E-005, T16.3); SDG partitions are "held-out runs of the same synthetic layout" (T14.2); oracle tracks and references come from the same truth (T17.6), so oracle-path agreement is **rule-conformance evidence only** and is reported under "implementation conformance"; reports using reference visible support state "reference visibility: binary, dataset-defined, no minimum visible area". Oracle visible frames are dataset-visible **and** eligible frames (T20.1).

## 2. Split (X0b) — frozen

| Item | Value |
|---|---|
| X0b artifact | `art_w5v3ldr43xdsqc6l4zifmjkuuj` (payload `c01ad60b…465382`), split_manifest `spm_uvjw4v4mygzvtvwqrbjjhambh5`, label `m1a`, version 1, tier **T1**, basis metadata_only |
| Inputs | S0 `art_xwrldyhquvmorjhpjxb573tbxk` (SDG), S0 `art_k3kmwlyr3dwyaztop6bedfkxts` (Warehouse_000) |
| Leakage groups | 73: one per SDG run (72) and one for Warehouse_000. Validation 25 groups (24 SDG + SmartSpaces), test 48 |
| SDG | **24 validation / 48 test** runs |
| SmartSpaces synthetic group | **validation** |
| Draw seed | **2026111401** |
| Split-draw configuration | `sdr_nrca36qkkf72d4qenhtbx2anjh`, named in the X0b artifact's configuration IDs (AR-57 item 2) |

**Strata of the draw (D-35 option (b)).** The batch family of a run is the **first path element of its session lineage `generation_batch`** (T14.1), split at `/`; for example `warehouse_osmos_2/nearmiss/shard-15` → `warehouse_osmos_2`. The recorded `generation_batch` has 14 values; they fall into 3 families. Inside each family the validation runs are a simple random draw without replacement, runs sorted by `ext_run_id`, from one numpy PCG64 generator seeded with 2026111401, families drawn in sorted name order (AR-57 item 1). All other runs are test. Inputs are pre-system metadata only (R-4).

| Family | Runs | Validation | Test |
|---|---|---|---|
| `warehouse_osmos` | 36 | 12 | 24 |
| `warehouse_osmos_1` | 16 | 5 | 11 |
| `warehouse_osmos_2` | 20 | 7 | 13 |
| **Total** | **72** | **24** | **48** |

The run lists are in the freeze record (`split.sdg_validation_runs`, `split.sdg_test_runs`).

**Warehouse_001.** X0b v1 holds SDG and Warehouse_000 only, so the file has one data_origin (VR-E-005; Owner answer, 14 Nov 2026). Warehouse_001 is validation through its leakage edge to Warehouse_000 (T16.2). It enters at M1b as a new split version that keeps it with Warehouse_000; a split that separates them is refused (ERR-LEAKAGE).

The leakage audit X0c must be complete before any S8 run on test (R-2).

## 3. Sampling frame (V0) — frozen

Camera grouping basis for every M1a configuration: **one camera = one camera group** (AR-22). One plan per dataset row and partition (accepted AR, AR-57 item 3). Sample type RES, **census** (n_h = N_h, π = 1, weight 1). Strata: dataset row × viewpoint class (pre-system metadata). Tiling origin 0.0 s (every recording-local timeline starts at 0). Shorter last window allowed, guard clipped at the timeline end (D-7).

| Plan | Plan ID | V0 artifact | w_ref | w_guard | Strata (N_h = n_h) | Windows | Camera groups | Leakage groups | Recordings outside (T17.4) |
|---|---|---|---|---|---|---|---|---|---|
| `m1a-sdg-validation` | `spl_vlvbg6r3u2pesbeojeqqatzb4s` | `art_wiaoelxnrzaqb2ii44esa47k3f` | 10 s | 0 s | ceiling 109, eye_level 117 | 226 | 226 | 24 | 14 |
| `m1a-sdg-test` | `spl_vtjhjz6weab625yuy3u2l6wka3` | `art_hfchmhd3zbgjl24gnqaxifaoo3` | 10 s | 0 s | ceiling 235, eye_level 236 | 471 | 471 | 48 | 9 |
| `m1a-smartspaces_000-validation` | `spl_f7omx5ay2o3oh6xn3dkv6e5tyo` | `art_rvcgsenmz4onjnq5jbfu4n6wax` | 30 s | 5 s | other 190 | 190 | 19 | 1 | 0 |

Plan seed 2026111401 (a census draws nothing; AR-57 item 4). The plans read S0 and S1 coverage only (VR-E-050). Window lock (`locked_utc`, `lock_sha256`) is pending review, as the contract requires before S8.

## 4. Parameters — frozen

All 30 fps. Robustness sweeps (MR-08, MR-12) run on **validation only**, **one parameter at a time** from the base values; any combination that T15.5 refuses (ttc_max or pet_max > τ) is listed, not run. With the values below no one-at-a-time combination is refused.

### 4.1 Decode and frame quality (S1)

| Parameter | Value | Basis |
|---|---|---|
| *k_sup* | 1.5 | exploratory design assumption. The held synthetic recordings are constant frame rate (all intervals 33.333 ms), so they do not constrain it; must be re-derived from real footage before any real-data result |
| *f_untimed* | 0.05 | exploratory design assumption (no untimed frame on held data) |
| *f_sub* | 0.10 | exploratory design assumption (no substituted timestamp on held data) |
| Frame-quality rules version | **rv2** (synthetic); `rv2-provisional` for real footage | accepted by the Architect (AR-51) |

### 4.2 Substrate (S4)

| Parameter | Base | Grid |
|---|---|---|
| ***g_max*** (eligible frames) | **15** | 5, 15, 30, 60 |
| *v_min* | 0.3 m/s | 0.2, 0.3, 0.4 |
| *w_v* | 0.5 s | 0.33, 0.5, 1.0 |
| τ (prediction horizon) | 2.0 s | **2.0, 3.0, 4.0** (D-34 B.4; τ = 1.0 removed because it conflicts with T15.5) |
| Pair classes | forklift | — |
| Motion model | constant_velocity | — |
| Forklift footprint prior (SDG) | 3.03 × 1.13 m, oriented rectangle, anchor centre; yaw = box long axis (CR-023) | ± 10 % on length and width (GV-03) |
| Forklift footprint prior (SmartSpaces) | **one prior, 2.68 × 1.16 m, anchor centre** (D-34 B.5) | as above |
| Person footprint prior | disc r = 0.30 m | 0.25, 0.30, 0.35 |
| Clearance band edges | 0, 0.5, 1, 2, 4 m | — |
| *v_part* | 0.5 | — |

**Stated basis of g_max** (D-34 B.1): 15 frames = 0.5 s at 30 fps, a short-occlusion rationale. **It was not fitted to the run-length tables** of §5. g_max bridges T8.1 POW gaps and limits predicted oracle points (T18, T19, T20.1), both counted in eligible frames.

**GV-04 on SmartSpaces** is reported per forklift box size (2.68 × 1.16 m and 1.87 × 1.13 m), since one prior serves both (D-34 B.5).

### 4.3 Rule providers and episode lifecycle (S5)

All values are exploratory design assumptions (D-34 B.4).

| Parameter | Base | Grid |
|---|---|---|
| *k_img* (R1) | 0.05 | 0.03, 0.05, 0.08 |
| *d_p* (R2) | 2.0 m | 1.5, 2.0, 3.0 |
| *d_pc* (R3) | 1.0 m | 0.5, 1.0, 1.5 |
| *ttc_max* (R4; ≤ τ) | 1.5 s | 1.0, 1.5, 2.0 |
| *pet_max* (R4; ≤ τ) | 1.0 s | 0.5, 1.0, 1.5 |
| *w_e* | 1.0 s | 0.5, 1.0 |
| *e_turn* / *e_acc* / *e_dec* (R5) | 1.5 rad/s / 1.0 m/s² / 2.0 m/s² | each × 0.5, 1, 2 |
| *m_gap* / *t_min* / *w_post* | 5 frames / 0.2 s / 1.0 s | *m_gap* 3, 5, 10; *t_min* 0.1, 0.2, 0.5 |
| *d_nm* / *k_σ* / *o_max* | 0.5 m / 2.0 / 0.5 | *d_nm* 0.3, 0.5, 1.0 |
| *k_c* / *k_c_turn* (contact cue) | 3.0 m/s² / 3.0 rad/s | — |

Fixed by contract: R4 sets no borderline flag (T15.5); `pet_pred` is never reported as "PET"; the contact cue applies in every configuration (T15.6).

### 4.4 Evaluation (S8)

| Parameter | Value |
|---|---|
| *iou_m* | 0.3 |
| *iou_cm* / *n_miss* | 0.5 / 5 frames |
| ε_amb | 0.02 |
| *k_kf* | 1.0 s |
| Bootstrap replicates B | **2,000** |
| Bootstrap seed | **2026111402** |
| CI level | **0.95** |
| *n_min_units* | Target B criteria 20 leakage groups; MR-01 1 run pair |
| *iou_rep* / *s_rep* | not used in M1a (no detector stage) |

## 5. g_max evidence (T18 amendment 3), all held runs

The tables of the draft (§5.1 run lengths, §5.2 POW counts) stand, recomputed under T20.1 in `research/datasets/part3/t17_counts_*.json` (code commit 9a0674e). T20.1 changed 29 SDG object-frames, all on ineligible frames, and no POW or sensitivity count. The validation-only tables (D-34 B.8) are reported separately in `docs/preregistration/validation_truth_tables.md`; no value was re-chosen from them.

## 6. Reporting strata

| Stratum | Kind | Status |
|---|---|---|
| data origin / dataset row | per result | contract |
| viewpoint class | per recording | contract |
| calibration tier, geometry method | per pair-frame | contract |
| clearance band | per pair-frame | contract |
| support basis | per metric | contract (N6) |
| `low_light` | per recording | accepted (AR-51) |
| **`forklift_turning`** | per pair-frame, report time | **contract T20.2** |

**`forklift_turning`** (T20.2, `src/rq1/evaluation/strata.py`): **w_turn = 0.5 s, e_fturn = 5°/s** (0.0872664626 rad/s); sensitivity reports at **2 and 10°/s** (D-34 B.6). True when the folded yaw rate > e_fturn, false when ≤ e_fturn, unknown otherwise; unknown frames are a third group. It is stored in no artifact and changes no flag, label, episode or denominator. R3 and R4 results are reported for turning, straight and unknown frames separately. On the detector path it is reported only where yaw is supplied or validated (D-8).

## 7. Configurations

As drafted (all oracle perception, single camera, rv2, the grouping of §3):

| Configuration | Providers | Geometry | Role |
|---|---|---|---|
| BL-2 | R1 | image only | primary comparison with BL-3 |
| BL-3 | R2 | world | primary comparisons with BL-2 and BL-6 |
| BL-4 | R2 + R3 | world | secondary |
| BL-5 | R2 + R4 | world | secondary |
| BL-6 | R2 + R3 + R4 + R5 | world | primary comparison with BL-3 |
| BL-1 | — | — | deferred to M1b |

Event configurations use `simulator_truth` positions (zero covariance); GV-01, GV-04–GV-08 use a second run with `full_camera` geometry from the oracle boxes and the dataset calibration (`supplied_unvalidated`). Paired comparisons BL-2 vs BL-3 and BL-3 vs BL-6 by the T11.2 paired bootstrap on EV-M1, EV-M2, EV-M7. Label groups O, H, PC against definition-applied references; evasive action against the SDG `Dodge` annotation where present. No NM-versus-contact claim on SDG. Oracle-path results are never pooled with detector-path results.

## 8. Primary metrics and estimands

As drafted: primary metrics MR-01; GV-01 RMSE and GV-07 speed RMSE (`full_camera` run); CM-03 and CM-08; EV-M1 and EV-M2 per configuration; MR-08 `label_stability_frac`. All others secondary, reported in full. Target B (`new_session_performance`, cluster bootstrap over leakage groups) is the headline on SDG test, with Target A (`frame_description`) alongside. The number of leakage groups per partition and data origin is printed beside every Target B interval (T14.3).

## 9. Acceptance criteria — registered

Records in `docs/preregistration/freeze_record.json` (`acceptance_criteria`), `preregistration_ref` = "docs/preregistration_FROZEN.md, version 1", frozen_utc 2026-11-15T01:47:59Z, ci_level 0.95, frozen before any test-partition evaluation (§9.6).

| # | Record | acc_id | Metric, slice | Rule | Target | n_min_units | Estimand |
|---|---|---|---|---|---|---|---|
| 1 | C1-MR-01 | `acc_tzjtfybncoz2hlqu62w4myrw4n` | MR-01, every exact-class artifact of the M1a run (value 1.0 iff all payload hashes identical, AR-57 item 5) | exact_equal | 1.0 | 1 | frame_description |
| 2a | C2-GV-01-ceiling | `acc_eoxyzlbdojmylidna45ultqozf` | GV-01 RMSE, `full_camera`, SDG test, ceiling | ci_upper_le | 0.25 m | 20 | new_session_performance |
| 2b | C2-GV-01-eye_level | `acc_w3m4qgj3rci5f7gv3cdaujbqmq` | GV-01 RMSE, `full_camera`, SDG test, eye_level | ci_upper_le | 0.25 m | 20 | new_session_performance |
| 3 | C3-GV-07 | `acc_suetxtthdff6bf5r3y76cfsq2z` | GV-07 speed RMSE at w_v = 0.5 s, `full_camera`, SDG test | ci_upper_le | 0.15 m/s | 20 | new_session_performance |
| 4 | C4-GV-04 | `acc_kmy7qocn5vmwq6ir33mwdevv2m` | GV-04 bias (prior footprint − simulator 3D box footprint), SDG test | abs_bias_ci_within | 0.10 m | 20 | new_session_performance |

**Criteria #5–#10 of the draft are NOT registered.** Their metrics (CM-03, CM-08, EV-M1, EV-M2, MR-08, EV-M1 ceiling − eye_level) are reported without a decision (`not_assessable`: no registered criterion). Status on synthetic data is at most `experimental` (T12.5).

## 10. Limitations

1. **Truth-side statistics of the draft covered all held runs,** including runs now in test. They use no system output. After the freeze they were recomputed on validation runs only (`docs/preregistration/validation_truth_tables.md`, D-34 B.8); no value was re-chosen.
2. **g_max sets how many POWs a long occlusion produces** (T8.1, T18, AR-55 item 6). §5 gives the counts.
3. **SDG forklift speed is at most about 0.75 m/s.** With the T9.2 estimator the forklift_decel criterion (e_dec 2.0 m/s²) and the forklift part of the contact cue (k_c 3.0 m/s²) cannot be exceeded on SDG. This is reported as a coverage limitation; the thresholds are unchanged (D-34 B.11).
4. **SmartSpaces forklift footprint:** one prior for two box sizes; GV-04 reported per box size (§4.2).
5. **SmartSpaces is one leakage group,** in validation: no Target B interval and no test result on it.
6. **CR-007 / D-8** stays deferred to T-22; it does not affect the oracle path. `forklift_turning` on the detector path only where yaw is supplied or validated.
7. **Real footage** is outside this pre-registration. Before any real-data result: *k_sup* from that footage's frame intervals, the dark-frame spread report (D-25 ruling A item 6), and the D-26 values.
8. **Parameter values** of §4 are exploratory design assumptions, to be reviewed against literature before publication.
