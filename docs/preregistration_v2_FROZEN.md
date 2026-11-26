# RQ1 pre-registration — FROZEN (version 2)

**Status: FROZEN under Owner decision D-61 (26 Nov 2026).** The values come from the Owner and Architect's value-by-value review of 25–26 Nov 2026, recorded verbatim in `docs/preregistration/v2_notes.md` ("Owner decision D-61"). The agent wrote this document from that decision and chose no scientific value. Version 1 (`docs/preregistration_FROZEN.md`) and its records are unchanged. Results under different versions are never mixed.

| Item | Value |
|---|---|
| Contract | **E-1.2.26** (E-1.2.1 FROZEN, F.1 Part A and Appendix N, Appendix T up to T25) |
| Analysis code commit | `226ea7b0c07f105c0f64881a9e6019633193121f` |
| `requirements.lock` SHA-256 | `228ef036e3d741429ce8683b6035900a83aca0cd28d34661ba0233779c6e971d` |
| frozen_utc | 2026-11-26T14:29:25Z |
| Freeze record (all IDs, reference sets, criterion records) | `docs/preregistration/freeze_record_v2.json`, built by `research/preregistration/freeze_v2.py` from `research/preregistration/v2_values.py` and `src/rq1/pipeline/prereg_v2.py` (built twice, identical) |
| Scope | E1 instrument quality on synthetic data: the SDG reporting cameras (110), the X0b test partition (48 SDG runs, 471 cameras), and D-60 tier 1 (blocked on CR-039 for references) |

**Wording.** All results are synthetic-data evaluations: "experimental", "implemented" or "verified", never "validated". Automated outputs are "candidate", "suspected" or "undetermined". Tuning-subset results are "diagnostic, not reported results". The parameter values are **design anchors or labelled assumptions, never validated thresholds** (D-61 §1.8 item 4).

**Governing principle (D-61).** Every v1 value was an exploratory design assumption (v1 §4). The Owner chose not to accept road-traffic literature values unexamined. Each value below was challenged and is now either anchored to a stated reason or kept as a labelled assumption.

**No S2 or later system stage has been run on the 110 reporting cameras or on the test partition** at the freeze. The v2 references were built from simulator truth only (T21.1), which D-61 allows.

---

## 1. Data and populations

As in v1 §1. Two things are added:
- the D-59 SmartSpaces scenes, registered in the split addendum X0b-A1 (D-60): tier 1 `test_layout_holdout`, 45 cameras in 6 layouts; tier 2 `reserve`, 73 cameras;
- the v2 camera sets on SDG validation (D-50 item 3): **tuning** 13 runs / 116 cameras (values may be chosen here, by tracking measures only) and **reporting** 11 runs / 110 cameras (evaluated once, after this freeze).

All held SDG and SmartSpaces recordings are 30 fps (δ_nom = 1/30 s; D-61 STEP 0). The Safe and Unsafe Behaviours clips (about 25 fps) are outside this pre-registration (CR-038).

## 2. Split — frozen (unchanged)

X0b v1 is unchanged: `art_w5v3ldr43xdsqc6l4zifmjkuuj`; 24 validation and 48 test SDG runs; Warehouse_000 validation. The addendum X0b-A1 is `art_xu3yvoyvpsukx257kmo5p37zxs` (D-60). The leakage audit X0c must be complete before any S8 run on test (R-2).

## 3. Sampling frame (V0) — frozen (unchanged)

The v1 plans stand (v1 §3): `m1a-sdg-validation`, `m1a-sdg-test` and `m1a-smartspaces_000-validation`. The window lock (`locked_utc`, `lock_sha256`) is prepared for the Architect's review before S8 on test (D-61 STEP 6).

## 4. Parameters — frozen (D-61 §1.1–1.5)

### 4.0 Two kinds of numbers

- **Definition numbers** decide what counts as a hazardous encounter. These are τ, ttc_max, pet_max, d_p, d_pc, v_min, the R5 thresholds, k_c, k_c_turn, d_nm, m_gap_s, t_min, w_post, the footprints and o_max.
  - References are BL-6 with these same base values, applied to simulator truth (T21.1). A definition number is therefore **never chosen by an event score**. This extends D-58 ruling 1 from m_gap to all of them.
- **Instrument numbers** decide how well the camera system measures. These are g_max, w_v, w_e, the tracker package, the T25.1 stitching values, the T24 values and the detector thresholds.
  - They may be chosen on the 116 tuning cameras by **tracking measures only**.
- **Real-warehouse meaning.** Definition numbers describe danger in a real warehouse, not SDG behaviour. A rule that cannot fire on SDG (for example, forklift top speed is about 0.75 m/s) is reported as a coverage limitation; its threshold is not lowered to fit the data.

**The anchor is one human perception–reaction time of 1.5 s.**
- It is used in collision-warning work: NHTSA ESV paper 18ESV-000381, https://www.nhtsa.gov/sites/nhtsa.gov/files/18esv-000381.pdf.
- It is consistent with the FHWA SSAM TTC threshold of 1.5 s.
- **Status:** a design anchor taken from road-traffic human factors. It is not validated for warehouses.

### 4.1 Decode and frame quality (S1)

Unchanged from v1 §4.1 (k_sup 1.5, f_untimed 0.05, f_sub 0.10, rv2).

### 4.2 Base values (D-61 §1.3)

The "Change" column is relative to v1; "keep" means the v1 value stands with a new basis.

| Parameter | v1 | **v2** | Change | Basis |
|---|---|---|---|---|
| τ | 2.0 s | **2.0 s** | keep | Horizon must be ≥ ttc_max and pet_max (T15.5). A longer horizon extends straight-line paths through aisle turns and creates conflicts that would not occur. Design assumption |
| ttc_max | 1.5 s | **1.5 s** | keep | One reaction time (§4.0). In road traffic it is the SSAM convention, and sites vary (one study derived 1.15 s). On slow SDG data R4 adds little beyond R3; that is reported as a finding |
| pet_max | 1.0 s | **1.5 s** | **changed** | Same reaction-time argument as TTC. Road usage spans about 1–2 s. Design anchor |
| d_p (R2) | 2.0 m | **3.0 m** | **changed** | WorkSafe Victoria: a 3 m minimum exclusion zone from a forklift at walking pace (https://www.worksafe.vic.gov.au/safety-alerts/workers-fatally-injured-forklifts). Consistent with the stopping distance at walking pace (1.5 m/s × 1.5 s + 1.5²/(2 × 3.9) ≈ 2.5 m). The 3.9 m/s² is the NZTA minimum for unladen service braking: stop within 4 m from 20 km/h (https://vehicleinspection.nzta.govt.nz/virms/in-service-wof-and-cof/forklifts/brakes/service-brake-and-parking-brake). **Limitation:** WorkSafe does not say whether the 3 m is measured from the truck body or from the load |
| d_pc (R3) | 1.0 m | **1.0 m** | keep | Inner "danger" zone: paths predicted to pass within about one step, leaving no room to step aside. Commercial systems use two zones, an outer warning zone and an inner danger zone. The stride figure (about 0.7–0.8 m for an adult) is unsourced; cite it or label it an assumption |
| v_min | 0.3 m/s | **0.3 m/s** | keep | A forklift is "moving" if, within one reaction time, it can close half of d_pc: 0.5 m ÷ 1.5 s ≈ 0.33 m/s. Design anchor |
| w_v | 0.5 s | **0.5 s** | keep | Instrument. M1a GV-07 (forklift, oracle boxes, full_camera): RMSE 0.32 m/s at 0.5 s against 0.28 m/s at 1.0 s. The error is dominated by bias, so a longer window adds lag for little gain. These M1a numbers cover all 24 validation runs, from before the tuning/reporting split; they are used for understanding the instrument, not for selection |
| m_gap_s (T25.3) | 5 frames | **1.5 s** | **changed** | Two close moments are one encounter if the pair separates for less than one reaction time. At 30 fps, ⌊1.5 / (1/30) + 1e-9⌋ = 45 frames. **The D-57 sweep was seen**; it is not the basis (D-58 ruling 1) |
| t_min | 0.2 s | **0.2 s** | keep | About the fastest simple human reaction; shorter episodes are flicker. Textbook range, unsourced: cite it or label it an assumption |
| w_post | 1.0 s | **1.5 s** | **changed** | A reaction to a close call can come up to one reaction time after it |
| w_e | 1.0 s | **1.0 s** | keep | Instrument (measuring window). Longer would blur short swerves |
| e_acc | 1.0 m/s² | **1.0 m/s²** | keep | Re-anchored to the T9.2 measurement (an average over a window of w_e = 1 s): the person loses about 1 m/s within a second, i.e. nearly stops from walking pace |
| e_dec | 2.0 m/s² | **1.0 m/s²** | **changed** | Under T9.2 the window average caps measured deceleration at about v₀ / w_e. A full emergency stop from 1.5 m/s reads at most 1.5 m/s², so 2.0 could never fire at walking pace, even on real footage. New meaning: the forklift loses about 1 m/s within a second |
| e_turn | 1.5 rad/s | **1.5 rad/s** | keep | About a quarter-turn or more within a second. **Limitation:** routine 90° corner turns also exceed it, so expect false evasive flags. The turning-zone idea (register C5) is future work, not in v2 |
| k_c | 3.0 m/s² | **1.5 m/s²** | **changed** | Same window cap as e_dec. At overlap, the forklift or the person loses all of walking-pace speed within the window |
| k_c_turn | 3.0 rad/s | **3.0 rad/s** | keep | At overlap, the person's direction reverses (about 170° in a second), as when knocked back |
| d_nm | 0.5 m | **0.5 m** | keep | Tighter than d_pc: a gap that a walking-pace forklift closes in about 0.33 s, close to the fastest reaction. Detector-path position error (median about 0.33 m, P95 about 0.64 m after T24, tuning cameras) is of the same size; report this |
| k_σ | 2.0 | **2.0** | keep | The two-σ (about 95 %) convention. Currently inert, because σ is zero (oracle) or null (detector); state as a limitation. **D-61 STEP 0 finding:** inert for clearance and contact; not inert for the `speed_near_v_min` borderline flag, because `speed_sigma_mps` (the T9.1 fit's standard error) is non-null on the detector path (§10 item 5) |
| o_max | 0.5 | **0.5** | keep | Majority rule; design assumption |
| k_img (R1, BL-2 only) | 0.05 | **0.05** | keep | Unchanged; baseline only |
| g_max | 15 frames | **45 frames (1.5 s)** | **changed** | Instrument. An interruption shorter than one reaction time breaks neither the encounter (m_gap_s) nor the observation window. Gap frames stay insufficient evidence and nothing is imputed (T8.1). This lies outside the register's 0.25–1.0 s comparison range; the tuning comparison is replaced by this reasoning. References are unaffected: truth exists on every eligible frame |
| Forklift footprints | SDG 3.03 × 1.13; SmartSpaces 2.68 × 1.16 (one prior) | **unchanged** | keep | Basis corrected: the **dataset's own 3D box sizes**. SmartSpaces uses one prior for two boxes (2.68 × 1.16 and 1.87 × 1.13 m), because the detector cannot tell them apart; report per box size. Whether forks are inside the box is unverified; carried loads are not. Real sites need footprints for their actual trucks |
| Person footprint | disc r 0.30 m | **0.30 m** | keep | SmartSpaces median person box 0.59 × 0.55 m gives a half-width of about 0.29 m (`research/datasets/qualification.md`) |
| T24 (D1, D2) | — | d 1.00 m, r_taper 2.0 m, SmartSpaces d × 0.923, s_max 0.1 m/px | frozen as tuning selections | D-54, D-57 ruling 1 |
| Clearance band edges | 0, 0.5, 1, 2, 4 m | **0, 0.5, 1, 2, 3, 4 m** | **3 m added** | Descriptive only. Every threshold (d_nm, d_pc, d_p) is now an edge |
| iou_m (N4) | 0.3 | **0.3**; also report 0.5 and 0.7 | keep + report | The lenient end of the thresholds commonly reported in temporal action-detection benchmarks (convention, unsourced). The question is whether the encounter was caught, not its exact boundaries. N4 is unchanged |
| forklift_turning | 5°/s, w_turn 0.5 s; 2 and 10°/s | **unchanged** | keep | Report-only stratum. Exists on the oracle path only (needs yaw) |

Unchanged from v1 and not reviewed (no basis change): k_sup, f_untimed, f_sub, v_part, iou_cm, n_miss, ε_amb, k_kf, bootstrap B 2,000, seed 2026111402, CI 0.95, n_min_units, w_ref, w_guard.

Fixed by contract (unchanged): R4 sets no borderline flag (T15.5); `pet_pred` is never reported as "PET"; the contact cue applies in every configuration (T15.6). T25.2 does not apply to references (T25.2 d).

### 4.3 Sensitivity grids (D-61 §1.4)

Grids are run on validation only, one parameter at a time from the v2 base, and scored against the v2 base references (T21.4). For definition numbers a sweep measures **disagreement with the frozen definition**, not accuracy; reports say so. The T15.5 check passes for every grid value (ttc_max and pet_max ≤ τ).

| Parameter | Grid |
|---|---|
| τ | 2.0, 3.0, 4.0 |
| ttc_max | 1.0, 1.5, 2.0 |
| pet_max | 1.0, 1.5, 2.0 |
| d_p | 2.0, 3.0, 4.0 |
| d_pc | 0.5, 1.0, 1.5 |
| v_min | 0.2, 0.3, 0.4 |
| w_v | 0.33, 0.5, 1.0 |
| m_gap_s | 1.0, 1.5, 2.0 |
| t_min | 0.1, 0.2, 0.5 |
| w_post | 1.0, 1.5, 2.0 |
| w_e | 0.5, 1.0 |
| e_turn, e_acc, e_dec | each × 0.5, 1, 2 |
| d_nm | 0.3, 0.5, 1.0 |
| g_max | 15, 30, 45, 60 frames |
| person r | 0.25, 0.30, 0.35 |
| forklift footprint | ± 10 % on length and width |
| iou_m (report columns) | 0.3, 0.5, 0.7 |
| e_fturn | 2, 5, 10 °/s |

### 4.4 Engineering selections frozen with v2 (D-61 §1.5)

These are tuning-subset selections, not literature values.

- **Detector:** YOLO-World v2-s, zero-shot, person 0.20, forklift 0.05 (D-45). Fine-tuning (register E1/E4/E6) is **not in v2**.
- **Tracker:** package `trc_7flfpx52d2siiljxkqwcorr7nz` (D-55/D-56).
  - **OC-SORT was not compared.** This is a stated limitation (Owner, register D3).
  - Standing caveat (D-56 ruling 6): the point precision of 0.979 was measured on SDG only.
- **T25.1 stitching:** the D-58 STEP 3 selection (= D-61 STEP 3): **T_s 5 s, r_g 0.5 m**, v_max person 2.5 m/s, forklift 4.0 m/s, k_img 1.0 (`research/m1b/d58_stitch_grid.json`). The grid was run on detector S3 bridged at g_max 15, as D-58 STEP 3 was written.
- **T25.2:** `join_across_pow` = true, with m_gap_s 1.5 s.
- **T25.3:** `lifecycle.m_gap_s` = 1.5.

Configuration IDs (detector, tracker with T25.1, substrate, geometry, rules, evaluation) are in the freeze record, `configurations`.

### 4.5 Evaluation (S8)

As v1 §4.4. iou_m 0.3 decides, and 0.5 and 0.7 are reported beside it.

## 5. g_max evidence

The v1 run-length tables (v1 §5) stand. The v2 g_max (45 frames) rests on the reasoning in §4.2, not on a tuning comparison.

## 6. Reporting strata

As v1 §6. The clearance bands gain the 3 m edge.

## 7. Configurations

As v1 §7, at the v2 values, with T25.2 on for the system configurations. Headline and paired comparisons: §8.

## 8. Criteria and headline (D-61 §1.6)

- **Registered criteria:** targets unchanged; the basis is new. Each measurement error should be at most **half the threshold it decides**.
  - GV-01 0.25 m = d_nm ÷ 2. This applies to both registered GV-01 records (2a ceiling and 2b eye_level).
  - GV-07 0.15 m/s = v_min ÷ 2.
  - Rules, slices and estimands as in v1 §9: MR-01, GV-01 (ceiling, eye_level), GV-07, GV-04.
- **GV-04 is circular.** The prior is the dataset box, so GV-04 is reported but never cited as evidence.
- **GV-01 and GV-07 are expected to fail.** The tuning data has already been seen, so targets are **not moved**. Failures are reported as failures.
- **Added, descriptive (no decision):**
  - GV-01 and GV-07 in the D-41 form (median, P95, outlier share);
  - position availability by null reason, printed beside every GV-01 value;
  - GV-01 and GV-07 on **detector boxes**.
- **EV-M1 and EV-M2 stay descriptive** (register C12), with confidence intervals. No success threshold is set, and the paper says why.
- **Headline:** BL-6 on the detector path. The oracle and full_camera columns are decomposition. The paired comparisons registered in v1 (BL-2 vs BL-3, BL-3 vs BL-6, oracle path) are kept. The same pairs on the detector path are reported without a decision rule. Oracle results are never substituted for detector-path capability.

## 9. Acceptance criteria — registered (version 2)

Records are in `docs/preregistration/freeze_record_v2.json` (`acceptance_criteria`, `criteria_basis`). `preregistration_ref` = "docs/preregistration_v2_FROZEN.md, version 2", frozen_utc 2026-11-26T14:29:25Z, ci_level 0.95. They were frozen before any evaluation on the reporting cameras or the test partition.

| # | Record | acc_id | Metric, slice | Rule | Target | Basis (D-61 §1.6) | n_min_units | Estimand |
|---|---|---|---|---|---|---|---|---|
| 1 | C1-MR-01 | `acc_rxxug4rzkc4nsmsjl6xzbwnvuz` | MR-01, every exact-class artifact of the run | exact_equal | 1.0 | repeatability: every exact-class artifact identical (unchanged from v1) | 1 | frame_description |
| 2a | C2-GV-01-ceiling | `acc_l6g2wirorbntuaa7lbkvpm2f5i` | GV-01 RMSE, `full_camera`, SDG test, ceiling | ci_upper_le | 0.25 m | 0.25 m = d_nm / 2 (d_nm 0.5 m) | 20 | new_session_performance |
| 2b | C2-GV-01-eye_level | `acc_o3biw66r6oqdyu6jqy3yb44y6b` | GV-01 RMSE, `full_camera`, SDG test, eye_level | ci_upper_le | 0.25 m | 0.25 m = d_nm / 2 (d_nm 0.5 m) | 20 | new_session_performance |
| 3 | C3-GV-07 | `acc_vfdi27q4w33r4zktddowteokzv` | GV-07 speed RMSE at w_v = 0.5 s, `full_camera`, SDG test | ci_upper_le | 0.15 m/s | 0.15 m/s = v_min / 2 (v_min 0.3 m/s) | 20 | new_session_performance |
| 4 | C4-GV-04 | `acc_6ezopessdb56i3rlbeszmzploq` | GV-04 bias (prior footprint − simulator 3D box footprint), SDG test | abs_bias_ci_within | 0.1 m | 0.10 m (unchanged); GV-04 is circular (the prior is the dataset box): reported, never cited as evidence | 20 | new_session_performance |

Criteria #5–#10 of the v1 draft remain unregistered. EV-M1 and EV-M2 are descriptive (§8).

## 9a. References and reporting order (D-61 §1.7)

- References are rebuilt once with the v2 base values (T21.1), for every partition, from simulator truth only. This creates a **new reference set**; T21.4 then applies to it.
- The v1 base references and all stored artifacts stay unchanged and are never overwritten.
- After the freeze, in this order and once each:
  1. the 110 reporting cameras;
  2. the X0b test (48 SDG runs), **before 1 Dec 2026** (Owner, register F1);
  3. tier 1 (after D-60).
- **Consequence recorded (Owner accepted):** a detector fine-tuned after 1 Dec will have no untouched SDG test. It is evaluated only on held-out data not yet used.

**v2 reference sets built** (SDG, simulator truth, BL-6 at the v2 values, T25.2 off; `out/v2/references/`; IDs and hashes per camera in the freeze record):

| Set | Cameras | References | Assessable (G1) | Reference S4 configuration | Reference S5 configuration | Set SHA-256 |
|---|---|---|---|---|---|---|
| tuning | 116 | 116 | 116 | `sbc_5h5zcuzay643ohdiqy6bztul4k`, `gcf_x3qktt7qr753qhjs5htbjxf7yi` | `rcf_rtzb7byuqwozw3ykztzwg7a5fg` | `494fffa85e80939e631113ee85c8164d7cc7ee9a0baef2b647d612b18951583c` |
| reporting | 110 | 110 | 110 | `sbc_5h5zcuzay643ohdiqy6bztul4k`, `gcf_x3qktt7qr753qhjs5htbjxf7yi` | `rcf_rtzb7byuqwozw3ykztzwg7a5fg` | `0df9be5ba4da4b22b81668c3d196ea0b8356ea8e2917c63208fa2106eebbb5f4` |
| test | 471 | 473 | 471 | `sbc_5h5zcuzay643ohdiqy6bztul4k`, `gcf_x3qktt7qr753qhjs5htbjxf7yi` | `rcf_rtzb7byuqwozw3ykztzwg7a5fg` | `b0fb7b30be88f80b0693e8f5cab3cc59ace175c57e0a1952df338e48452ee290` |

Built twice, independently (`v2_references.py run` and `verify`): artifact IDs and payload hashes identical on 697 of 697 cameras. The tuning set equals the D-61 STEP 4 diagnostic set in reference count on 116 of 116 cameras (that set carries a diagnostic label and is stored apart).

SmartSpaces references (Warehouse_000, and the tier-1 cameras) are **not built**: T21.1 is infeasible on scene-wide truth (D-39), and the v2 T21 amendment promised in D-40 item 3 does not exist (**CR-039**). The tier-1 evaluation waits on it.

## 10. Limitations (D-61 §4, with the STEP 0 findings)

1. The 1.5 s anchor and the walking-pace braking figure come from road traffic and vehicle inspection rules. They are not validated for warehouses.
2. SDG forklifts move at ≤ about 0.75 m/s. e_dec and the forklift side of the contact cue cannot fire, and R4 adds little beyond R3.
3. Speed error (about 0.5 m/s, P5–P95) is larger than v_min, so the H/O split is unreliable on camera footage.
4. Position error is about the size of d_nm, so NM-by-distance on camera footage is noisy.
5. k_σ and the borderline flags are inert while σ is not estimated. **STEP 0 finding:** on the detector path `pos_cov_m2`, σ_c and `minclr_sigma_m` are null on every row, so `clearance_within_k_sigma` never fires. But `speed_sigma_mps` (the T9.1 fit's standard error) is non-null on 99 % of object states, so `speed_near_v_min` fires (313 of 450 C-v2 episodes on the tuning cameras). Borderline flags never change a label or a route (T10.4, T11.1).
6. e_turn also fires on routine corner turns.
7. GV-04 is circular. The footprints may exclude forks; carried loads are excluded.
8. OC-SORT was not compared. Tracker precision is known on SDG only.
9. No NM, UD or CT references exist on synthetic data, so those labels are demo-workflow output, not measured accuracy.
10. NM, UD and CT labels can only be checked by managers, and that check has not been validated (G1–G3 deferred).
11. **Routing (STEP 0):** under the §6 `review_route` flag an O episode is routed in the OI-1 case (overlap, no X or C) **and whenever it carries IE**. In the T23 workflow (v02-review-ui) O episodes never create a manager report: only G2 NM, UD and CT do (T23.2 a).
12. The T25.1 stitching values were selected on detector S3 bridged at g_max 15 (D-58 STEP 3 as written); v2 runs at g_max 45.
13. g_max is a frame count; on recordings that are not 30 fps, 45 frames is not 1.5 s (CR-038). No such recording is in v2.
14. SmartSpaces v2 references are not built (CR-039).
15. The truth-side and tuning-side numbers that informed the review (M1a GV-07, the D-57 sweep, the D-58 check, pilot numbers) were seen; they are disclosed, not used as a basis for definition numbers.
