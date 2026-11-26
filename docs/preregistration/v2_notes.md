# Notes for pre-registration v2

Pre-registration v1 (`docs/preregistration_FROZEN.md`) and its frozen criteria are unchanged. This file collects what the Owner has recorded for v2, with its source. It is a record, not a pre-registration.

## Position accuracy (D-41, 17 Nov 2026)
- State position accuracy as **median, P95 and outlier share** (the share above stated distances). GV-01 RMSE is dominated by outliers.
- Report **position availability** separately: the share of object-frames with a numeric position, by null reason.

## Licence rows in the S2 artifact (D-47 item 5, 19 Nov 2026)
- The next S2 build carries the `license_component` rows of every weight file it loads inside the artifact: the CLIP ViT-B/32 text encoder (`lic_ym5owzhkkwvjzayaewgzuzhpyc`) and, if it is used, Grounding DINO tiny (`lic_bim7wazyo5z6kh4iiks4hvky2q`). They sit beside the YOLO-World row. The rows are in `research/m1b/pilot_license_components.json`.

## Detector and tracker as one package (D-50 item 3, 19 Nov 2026)
- The detector thresholds and **all** tracker parameters, `fuse_score` included, are fixed as **one package**.
- **Tuning subset:** the package is chosen only on all cameras of the runs that contain a T-22 probe camera. That is 13 of the 24 SDG validation runs: 116 cameras (54 ceiling, 62 eye-level), counted on 19 Nov 2026.
- **Reporting:** v2 results are reported on the other validation runs (11 runs, 110 cameras: 55 ceiling, 55 eye-level) and on test (D-37 still reserves the test partition).
- **Why** (T-25p pilot, `reports/M1b_pilot_report.md`):
  - D-45 fixed the forklift detector threshold at 0.05, while ByteTrack's defaults start tracks at 0.25. That cost most forklift tracks (column C).
  - Aligning the start thresholds alone (C') made it worse, because `fuse_score` needs IoU × score ≥ 0.2 to continue a track.
  - The parameters interact, so they cannot be chosen one at a time.

## Questions for the Architect
- **Episode extent and fragmentation** (D-50 item 2; `research/m1b/pilot_extent.json`). On the detector path (C, BL-6), 141 of 142 events overlap a reference interaction of the same pair, but only 31 match under N4 (temporal IoU ≥ 0.3).
  - 55 of the 111 unmatched events overlap with IoU ≤ 0.1.
  - 38 of the 100 references found by overlap are covered by two or more separate episodes, and only 4 of those 145 episodes are linked by `continuation_of_nk`.
  - Should v2 define how fragmented episodes of one pair are joined, or how an event's extent is compared, on the detector path? This is a question only; N4 is unchanged.
- **Inputs for v2, for the Architect** (D-50 item 4; no rule is implemented now):
  - CR-007: the footprint anchor. The evidence is now sufficient: the forklift error lies along the line of sight, −1.01 m, against 0.09 m across.
  - CR-029: N9 rules 4 and 5 on the detector path.
  - CR-026: a range condition for full_camera foot rays.

## Tracker package selected (D-55, 23 Nov 2026)
- Selected package `trc_7flfpx52d2siiljxkqwcorr7nz`: person ByteTrack at the installed defaults (column C); forklift ByteTrack with track_high_thresh 0.05, new_track_thresh 0.05, track_low_thresh 0.05, fuse_score false, track_buffer 90, match_thresh 0.8 (`research/m1b/v2_tracker_report.md`). **Selected under D-55, not frozen.**
- **Confirmed for pre-registration v2 (D-56, 23 Nov 2026). Selected, not frozen.** Package `trc_7flfpx52d2siiljxkqwcorr7nz`: T1 ByteTrack; forklift track_high_thresh, new_track_thresh and track_low_thresh 0.05, fuse_score false, track_buffer 90, match_thresh 0.8; person = column C ByteTrack at the installed defaults. CR-033 items 1 to 4 confirmed as applied (primary reading).
- Reports state that the T1 and T2 winners are indistinguishable on the tuning cameras: IDF1 0.774 vs 0.775; coverage 19,981 vs 19,980 of 33,677 reference frames.
- **Standing caveat (D-56 ruling 6), for every report that uses the package. Selected, not frozen.** The package accepts forklift detections down to score 0.05. Point precision 0.979 was measured on synthetic SDG data only and is not known for real footage.

## T24 candidate values (D-54, 23 Nov 2026; contract E-1.2.25)
- **T24.1 footprint centre (forklift, `full_camera` only). Selected, not frozen.** SDG forklift prior: `anchor = box_bottom_centre`, `anchor_offset_m` d = 1.00 m, `anchor_taper_m` r_taper = 2.0 m. SmartSpaces forklift prior: d × 0.923 (scaled, not fitted), r_taper 2.0 m. Residual reported, never hidden (D1, tuning cameras: median 0.33 m, P95 0.64 m). Detector and oracle boxes use the same d (D4: paired difference about −0.05 m). The person prior is unchanged.
- **T24.2 resolution gate. Selected, not frozen.** One global `s_max_m_per_px` = 0.1 (D5, tuning cameras: 94.2 % of errors above 10 m caught, 0.0 % of good points lost). Gated positions use null reason `not_observable` and clearance_state `unmeasurable_geometry_failure`; no new null reason.
- Iteration is allowed on the 116 tuning cameras only. The 110 reporting cameras are evaluated once, after v2 is frozen; the test partition stays reserved (D-37).
- **D-57 ruling 1 (24 Nov 2026).** The T24 values are kept as selected: s_max 0.1 m/px; forklift prior `anchor = box_bottom_centre`, d 1.00 m, r_taper 2.0 m; SmartSpaces d × 0.923. They are frozen together with pre-registration v2, not now. CR-034 reading (a) confirmed (the gate applies to `tracked` and `predicted` points; `lost` points carry `floor_resolution_m_per_px` null, `not_applicable`).
- **No person rule (D-57).** The person error has no systematic offset (median along-sight error −0.13 m, against a box half-depth of 0.38 m); the large person errors are at r ≥ 20 m, which T24.2 addresses.

## Event definition: m_gap and T25 (D-58, 24 Nov 2026; contract E-1.2.26)
- **m_gap: event definition in seconds, value from literature item C7, applied to system and references; D-57 sweep value not a candidate (D-58).** The D-57 sweep is kept as a sensitivity study only. At the v2 freeze, references are rebuilt once with the frozen `m_gap_s` (T21.4 then applies to the new reference set).
- **T25 adopted; values selected below are not frozen.** T25.1 (track stitching, S3, non-oracle tracks) and T25.2 (episode continuity across POW breaks, S5) are opt-in. Joined events are reported as joined, with their unobserved time (`unobserved_gap_s`).

## Owner decision D-61 (26 Nov 2026): pre-registration v2 values, T25 selection, freeze — §1 Rulings (verbatim)

Source: the value-by-value review between the Owner and the Architect, 25–26 Nov 2026, of the decision register `PwP_Consolidated_Decisions_For_Claude_2026-11-24.md` (items C1–C13, D3, F1–F3) and the literature-review questions (`architecture/decisions_for_literature_review_2026-11-21.md` §C). The repository state was checked at `m0-implementation` 8d254b6.

**Governing principle.** Every v1 value was an exploratory design assumption (v1 §4). The Owner chose not to accept road-traffic literature values unexamined. Each value below was challenged and is now either anchored to a stated reason or kept as a labelled assumption.

---

## 1. Rulings

### 1.1 Two kinds of numbers (applies to every value)

- **Definition numbers** decide what counts as a hazardous encounter. These are τ, ttc_max, pet_max, d_p, d_pc, v_min, the R5 thresholds, k_c, k_c_turn, d_nm, m_gap_s, t_min, w_post, the footprints and o_max.
  - References are BL-6 with these same base values, applied to simulator truth (T21.1). A definition number is therefore **never chosen by an event score**. This extends D-58 ruling 1 from m_gap to all of them.
- **Instrument numbers** decide how well the camera system measures. These are g_max, w_v, w_e, the tracker package, the T25.1 stitching values, the T24 values and the detector thresholds.
  - They may be chosen on the 116 tuning cameras by **tracking measures only**.
- **Real-warehouse meaning.** Definition numbers describe danger in a real warehouse, not SDG behaviour. A rule that cannot fire on SDG (for example, forklift top speed is about 0.75 m/s) is reported as a coverage limitation; its threshold is not lowered to fit the data.

### 1.2 The anchor

**The anchor is one human perception–reaction time of 1.5 s.**
- It is used in collision-warning work: NHTSA ESV paper 18ESV-000381, https://www.nhtsa.gov/sites/nhtsa.gov/files/18esv-000381.pdf.
- It is consistent with the FHWA SSAM TTC threshold of 1.5 s.
- **Status:** a design anchor taken from road-traffic human factors. It is not validated for warehouses.

### 1.3 v2 base values

The "Change" column is relative to v1; "keep" means the v1 value stands with a new basis.

| Parameter | v1 | **v2** | Change | Basis (to be written into v2 §4) |
|---|---|---|---|---|
| τ | 2.0 s | **2.0 s** | keep | Horizon must be ≥ ttc_max and pet_max (T15.5). A longer horizon extends straight-line paths through aisle turns and creates conflicts that would not occur. Design assumption |
| ttc_max | 1.5 s | **1.5 s** | keep | One reaction time (§1.2). In road traffic it is the SSAM convention, and sites vary (one study derived 1.15 s). On slow SDG data R4 adds little beyond R3; that is reported as a finding |
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
| k_σ | 2.0 | **2.0** | keep | The two-σ (about 95 %) convention. Currently inert, because σ is zero (oracle) or null (detector); state as a limitation |
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

### 1.4 Sensitivity grids

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

### 1.5 Engineering selections frozen with v2

These are tuning-subset selections, not literature values.

- **Detector:** YOLO-World v2-s, zero-shot, person 0.20, forklift 0.05 (D-45). Fine-tuning (register E1/E4/E6) is **not in v2**.
- **Tracker:** package `trc_7flfpx52d2siiljxkqwcorr7nz` (D-55/D-56).
  - **OC-SORT was not compared.** This is a stated limitation (Owner, register D3).
  - Standing caveat (D-56 ruling 6): the point precision of 0.979 was measured on SDG only.
- **T25.1 stitching:** selected in STEP 3 below.
- **T25.2:** `join_across_pow` = true, with m_gap_s 1.5 s.
- **T25.3:** `lifecycle.m_gap_s` = 1.5.

### 1.6 Criteria and headline

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

### 1.7 References and reporting order

- References are rebuilt once with the v2 base values (T21.1), for every partition, from simulator truth only. This creates a **new reference set**; T21.4 then applies to it.
- The v1 base references and all stored artifacts stay unchanged and are never overwritten.
- After the freeze, in this order and once each:
  1. the 110 reporting cameras;
  2. the X0b test (48 SDG runs), **before 1 Dec 2026** (Owner, register F1);
  3. tier 1 (after D-60).
- **Consequence recorded (Owner accepted):** a detector fine-tuned after 1 Dec will have no untouched SDG test. It is evaluated only on held-out data not yet used.

### 1.8 Six-question check (master instruction §10)

1. **Research objective:** unchanged (RQ1, E1).
2. **Meaning of measurements:** **yes.**
   - The event definition changes: pet_max, d_p, m_gap_s and w_post. These change which encounters count and how they are counted.
   - The R5 and k_c changes change the NM, UD and CT labels, which are routed to managers.
   - g_max changes POW structure.
   - The references are rebuilt with the new definition.
3. **Validation independence:** no new leakage.
   - Definition values are reasoned, not scored.
   - T25.1 is selected on tuning cameras by tracking measures.
   - Reporting and test are untouched until after the freeze.
   - The D-57 sweep and the M1a numbers that were seen are disclosed.
4. **Permitted claims:** wording unchanged (W1–W6). The anchors are design anchors, never "validated thresholds".
5. **Scope:** within E1 instrument quality. **E2 is not affected** (measurement-only, register A4).
6. **Type of decision:** scientific; hence this Owner decision.
