# RQ1 pre-registration — DRAFT (T-20)

**Status: DRAFT, a proposal by the implementation agent. Nothing here is frozen.** The Research Owner chooses every research value and freezes the result as `docs/preregistration_FROZEN.md` (STOP G-PR). Until then every configuration in the repository is TEST-ONLY.

- **Contract:** E-1.2.17 (E-1.2.1 FROZEN, F.1 Part A and Appendix N, Appendix T up to T19).
- **Scope:** milestone M1a (WP-14): single-camera runs with oracle perception on the synthetic datasets held on 14 Nov 2026.
- **No test-partition evaluation has been run.** No split is frozen. The evidence cited below is of two kinds only: (i) container and timestamp statistics of the recordings, and (ii) truth-side statistics of the datasets' own annotation (visibility, pose, yaw), computed over all held runs. No system output and no metric against a reference was computed. Because (ii) covers runs that will later be in the test partition, it is listed in §10 as a stated limitation.
- **Wording.** Results from synthetic data and fixtures are "implemented" or "verified", never "validated". Synthetic data cannot reach `technically_validated` (T12.5, FT-01), so every M1a fitness record is `experimental` or `not_yet_assessable`.
- **How to read the tables.** "Proposed" is the agent's proposal with its reason. "Owner" is the Owner's value; an empty cell means the proposal is not yet accepted. TEST-ONLY values (Package F §3) are shown for orientation only and are not research values.

Checklist of the WORKPLAN T-20 row: (1) *k_sup* → §4.1; (2) camera grouping basis → §3.1; (3) frame-quality rules version → §4.1; (4) *w_ref* and timeline lengths → §3.2; (5) not-visible run-length table → §5; (6) `forklift_turning` stratum → §6.

---

## 1. Data and populations

| Dataset row (T16) | data_origin | Held | In the M1a oracle and reference populations |
|---|---|---|---|
| SDG-Warehouse near-miss, multi-camera runs | synthetic_rendered | 72 runs, 720 recordings (10 cameras per run: 5 ceiling, 5 eye-level), 300 frames each at 30 fps (10 s) | 697 cameras with usable truth (T17.4) and an oracle track; 23 cameras without usable truth are outside |
| SmartSpaces `MTMC_Tracking_2026` `Warehouse_000` | synthetic_rendered | 19 recordings, 9,000 frames each (300 s) | all 19 |
| SmartSpaces `Warehouse_001` (Cosmos Transfer re-render of 000) | synthetic_transferred | 19 recordings, same truth and calibration as 000 | all 19 |
| SmartSpaces `Warehouse_026`, `Warehouse_027` | real_staged | 11 recordings | **none.** No annotation or reference labels (D-24 b); reference-free checks only; exploratory (D-26) |
| Safe and Unsafe Behaviours | real | held under D-24 | **none in M1a** (`conditional_on_selection`, no per-hour aggregates) |

Rules that follow from the contract and are not choices:
- Results are never pooled across data origins (VR-E-005, T16.3). Every table is per dataset row.
- SDG cameras without usable truth (T17.4) are outside the oracle and reference populations. Their recordings are used for reference-free checks only. The count is reported with every result.
- `Warehouse_000` and `Warehouse_001` are one leakage group (T14.1, T16.2).
- SDG partitions are "held-out runs of the same synthetic layout" (T14.2): no unseen-camera, unseen-layout or unseen-site claim.
- Oracle tracks and references come from the same truth (T17.6). Oracle-path agreement with the reference is **rule-conformance evidence only** and is reported under "implementation conformance".
- Reports that use reference visible support state: "reference visibility: binary, dataset-defined, no minimum visible area".

## 2. Split (X0b) — proposal

Leakage groups (T14.1, AR-31): one per SDG run (72 groups); one for the two SmartSpaces synthetic scenes together.

| Item | Proposed | Reason | Owner |
|---|---|---|---|
| Partitions used in M1a | validation and test only; no training partition | M1a trains nothing. Validation is where MR-08/MR-12 parameter sweeps and any debugging happen; test is evaluated once, after the freeze | |
| SDG assignment | 24 runs validation, 48 runs test, drawn by a seeded simple random draw over the 72 runs, stratified by generation batch | 48 clusters keep the Target B cluster bootstrap usable; the draw uses pre-system metadata only (R-4) | |
| Draw seed | ______ | the Owner supplies it at the freeze so the agent cannot tune it | |
| SmartSpaces 000 + 001 | validation | one leakage group cannot span partitions (PR-01) and gives no Target B interval; as validation data it still exercises the many-object case (up to 58 people and 9 forklifts in a frame) | |
| Alternative for SmartSpaces | test, reported with Target A intervals only and the statement "one leakage group" (T14.3) | if the Owner wants a many-object test result | |
| Tier | T1 | no group spans partitions; T2a/T3 claims are not available on this data (T14.2) | |

The leakage audit (X0c) must be complete before any S8 run on test (R-2).

## 3. Sampling frame (V0) — proposal

### 3.1 Camera grouping basis (AR-22)

| Configuration family | Grouping basis | Owner |
|---|---|---|
| All M1a research configurations | **one camera = one camera group** (the grouping registered at S0: 720 SDG groups, 19 per SmartSpaces scene). M1a is single-camera; cross-camera groups belong to M2 | |

The grouping defines the sampling frame. Changing it after the plan is frozen needs a new plan version (Architect note on AR-22).

### 3.2 *w_ref*, *w_guard* and timeline lengths (D-7)

Timeline lengths: SDG recordings are 10.0 s; SmartSpaces recordings are 300.0 s. Under D-7 (b) the last window of a timeline may be shorter than *w_ref*, and the guard is clipped at the timeline end.

| Parameter | TEST-ONLY | Proposed | Reason | Owner |
|---|---|---|---|---|
| *w_ref* (SDG) | 30 s | **10 s** | one window per recording, equal to the timeline. With 30 s every SDG window would be a "shorter last window" of 10 s, which gives the same windows but a frame definition that does not describe them | |
| *w_ref* (SmartSpaces) | 30 s | 30 s | 10 windows per camera, 190 per scene | |
| *w_guard* | 5 s | 0 s on SDG (the window is the whole timeline, so the guard is always clipped to nothing); 5 s on SmartSpaces | an event belongs to the window of its onset and durations are clipped to the window (§8) | |
| Sample type and size | — | RES with n_h = N_h (a census of windows, π = 1, weight 1) in every stratum | simulator truth costs no annotation effort; weighted and unweighted values then coincide, and the Target A interval describes the held recordings | |
| Sampling strata (pre-system only) | — | dataset row × viewpoint class (SDG: ceiling, eye_level; SmartSpaces: `other`, AR-53 item 9) | pre-system metadata only (§8) | |

## 4. Parameters — proposal

All 30 fps. "Grid" is the set of values for the robustness sweeps MR-08 and MR-12, run on **validation** only; the first value listed is the proposed base value.

### 4.1 Decode and frame quality (S1)

| Parameter | TEST-ONLY | Proposed base | Grid | Evidence and reason | Owner |
|---|---|---|---|---|---|
| *k_sup* | 1.5 | 1.5 | — | **Checklist item 1.** Every held synthetic recording is constant frame rate: all frame intervals are 33.333 ms (min = median = P99 = max; 0 of 68 recordings flagged VFR; qualification §2.5), and all 690 SDG member videos have 300 packets. There is no natural VFR jitter, so these datasets do not constrain *k_sup* from below: any value above 1 gives the same support on them. 1.5 caps support at 50 ms and matters only on real footage, where it must be re-derived from that footage's interval distribution before any real-data result | |
| *f_untimed* | 0.05 | 0.05 | — | not constrained by the held data: all 558,000 frames of the 758 held synthetic recordings are timed from the container `pts` (S1 under rv2) | |
| *f_sub* | 0.10 | 0.10 | — | not constrained by the held data: no substituted timestamp occurs | |
| Frame-quality rules version | rv1 (fixtures) | **rv2** for synthetic data; `rv2-provisional` for real footage | — | **Checklist item 3.** rv2 was accepted by the Architect (AR-51, 13 Nov 2026): black = dark and flat. On the 758 held synthetic recordings it flags 161 black frames in 16 recordings and 40 frozen frames (all also black); 13 red-lit recordings carry the `low_light` tag and stay eligible. Real-data artifacts carry "exploratory; frame-quality rules provisional" (D-26) | |

### 4.2 Substrate (S4)

| Parameter | TEST-ONLY | Proposed base | Grid | Evidence and reason | Owner |
|---|---|---|---|---|---|
| *g_max* (frames) | 15 | **no value proposed; see §5** | 5, 15, 30, 60 (the values of the §5 sensitivity counts) | the not-visible run-length tables and the POW counts of §5. *g_max* has two roles: the T8.1 POW gap bridge and the T18/T19 limit on predicted oracle points, both counted in eligible frames | |
| *v_min* | 0.3 m/s | 0.3 m/s | 0.2, 0.3, 0.4 | truth speeds: the SDG forklift moves at 0.75 m/s whenever it moves (0.75–0.82 m/s at the footprint centre during pivots) and the SDG worker reaches 1.8–2.2 m/s (qualification §2.3). 0.3 m/s lies well below every moving speed found | |
| *w_v* | 0.5 s | 0.5 s | 0.33, 0.5, 1.0 | 15 frames at 30 fps; GV-07 is reported per *w_v* | |
| τ (prediction horizon) | 2.0 s | 2.0 s | 1.0, 2.0, 3.0 | at 0.75 m/s the forklift covers 1.5 m in 2 s; τ also bounds *ttc_max* and *pet_max* (T15.5) | |
| Pair classes | forklift | forklift | — | pallet trucks are present in SmartSpaces but are not an E1 pair class (D-22) | |
| Motion model | constant_velocity | constant_velocity | — | the only model in the contract | |
| Forklift footprint prior (SDG) | 2.0 × 1.0 m | **3.03 × 1.13 m**, oriented rectangle, anchor centre | GV-03 sweep: ± 10 % on length and width | the dataset's own 3D box (all 20,081 boxes checked; AR-52 item 2). Yaw = box long axis (CR-023) | |
| Forklift footprint prior (SmartSpaces) | — | per box class: 2.68 × 1.16 m and 1.87 × 1.13 m, anchor centre | as above | the two forklift box sizes in the scene (80,626 boxes). **Open point:** one prior per class is what `footprint_prior` holds; two sizes in one scene need either two priors chosen per object or one enclosing prior. The Owner chooses; using the per-object size would need an Architect ruling | |
| Person footprint prior | disc r = 0.30 m | disc r = 0.30 m | 0.25, 0.30, 0.35 | SmartSpaces person boxes are 0.59 × 0.55 m (median), so 0.30 m is about half the box width | |
| Clearance band edges | 0, 0.5, 1, 2, 4 m | 0, 0.5, 1, 2, 4 m | — | descriptive bands for exposure profiles and CM-06; no threshold meaning | |
| *v_part* | 0.5 | 0.5 | — | T8.6 partial-visibility split by box position; no visibility fraction is supplied by either dataset | |

### 4.3 Rule providers and episode lifecycle (S5)

The agent proposes the TEST-ONLY values as **starting points for the Owner's choice**, not as recommendations with evidence: the held data give no basis for choosing a proximity or conflict threshold, and a choice made by looking at event counts on these runs would be tuning. The grids are for MR-08 and MR-12.

| Parameter | TEST-ONLY | Proposed base | Grid | Owner |
|---|---|---|---|---|
| *k_img* (R1) | 0.05 | 0.05 | 0.03, 0.05, 0.08 | |
| *d_p* (R2) | 2.0 m | 2.0 m | 1.5, 2.0, 3.0 | |
| *d_pc* (R3) | 1.0 m | 1.0 m | 0.5, 1.0, 1.5 | |
| *ttc_max* (R4; ≤ τ) | 1.5 s | 1.5 s | 1.0, 1.5, 2.0 | |
| *pet_max* (R4; ≤ τ) | 1.0 s | 1.0 s | 0.5, 1.0, 1.5 | |
| *w_e* | 1.0 s | 1.0 s | 0.5, 1.0 | |
| *e_turn* / *e_acc* / *e_dec* (R5) | 1.5 rad/s / 1.0 m/s² / 2.0 m/s² | same | each × 0.5, 1, 2 | |
| *m_gap* / *t_min* / *w_post* | 5 frames / 0.2 s / 1.0 s | same | MR-12: *m_gap* 3, 5, 10; *t_min* 0.1, 0.2, 0.5 | |
| *d_nm* / *k_σ* / *o_max* | 0.5 m / 2.0 / 0.5 | same | *d_nm* 0.3, 0.5, 1.0 | |
| *k_c* / *k_c_turn* (contact cue) | 3.0 m/s² / 3.0 rad/s | same | — | |

Fixed by contract, not choices: R4 sets no borderline flag (T15.5); `pet_pred` is never reported as "PET"; the contact cue applies in every configuration (T15.6); automated outputs are "candidate", "suspected" or "undetermined".

### 4.4 Evaluation (S8)

| Parameter | TEST-ONLY | Proposed base | Reason | Owner |
|---|---|---|---|---|
| *iou_m* | 0.3 | 0.3 | matching threshold; EV-M8 reports localization separately | |
| *iou_cm* / *n_miss* | 0.5 / 5 frames | same | association and the N9 perception test | |
| ε_amb | 0.02 | 0.02 | ambiguity margin of the identity association | |
| *k_kf* | 1.0 s | 1.0 s | CM interpolation limit | |
| Bootstrap replicates B | 200 | **2,000** | 200 is a fixture value; percentile limits at 2.5 % and 97.5 % need more replicates | |
| Bootstrap seed | 1 | ______ | supplied by the Owner at the freeze | |
| CI level | 0.95 | 0.95 | N5 | |
| *n_min* (`n_min_units`) | 10 | Target B criteria: **20 leakage groups**; Target A criteria: **30 windows** | with fewer units the decision is `not_assessable` (§9.6). Both numbers are floors proposed for discussion, not derived from data; under the §2 proposal the SDG test partition would have 48 groups | |
| *iou_rep* / *s_rep* (MR-01, S2) | 0.95 / 0.01 | not used in M1a | no detector stage on the oracle path | |

## 5. *g_max* and the not-visible run lengths (T18 amendment 3)

**No value of *g_max* is recommended here** (Architect ruling C of 14 Nov 2026). The tables are evidence for the Owner's choice.

What *g_max* does, by the contract:
- **T8.1 (POW gap bridging).** A gap of at most *g_max* eligible frames without a joint frame is bridged and the POW continues; a longer gap ends the POW with `gap_exceeded`, and a later joint frame starts a continuation POW.
- **T18 amendment 2 and T19 (oracle points).** A run of consecutive not-visible frames inside an object's visible span is predicted (inferred evidence) only when it has at most *g_max* eligible frames; a longer run is lost on every frame.

Source: `research/datasets/part3/t17_counts_sdg.json` and `t17_counts_smartspaces.json` (code commit 63aed8b, contract E-1.2.17, S1 under rv2). Truth-side counts only: no geometry, no rule, no reference, no metric.

### 5.1 Not-visible run lengths (T18 amendment 3; eligible frames, T19)

A run is a maximal sequence of frames between two visible frames of one object in one camera on which the dataset does not list it as visible. Percentiles are nearest-rank. 30 frames = 1 s.

| Dataset | Class | Runs | Frames in runs | Min | Median | P90 | P99 | Max |
|---|---|---|---|---|---|---|---|---|
| SDG (72 runs, 697 cameras) | forklift | 160 | 344 | 0 | 1 | 1 | 38 | 68 |
| SDG | person | 388 | 4,848 | 0 | 3 | 38 | 122 | 141 |
| SmartSpaces `Warehouse_000` (19 cameras; `Warehouse_001` identical) | forklift | 692 | 128,867 | 1 | 27 | 434 | 2,789 | 3,951 |
| SmartSpaces `Warehouse_000` | person | 6,625 | 1,578,245 | 1 | 19 | 606 | 3,373 | 8,009 |
| SmartSpaces `Warehouse_000` | pallet truck (not an E1 pair class) | 585 | 6,587 | 1 | 6 | 23 | 46 | 502 |

A minimum of 0 is a run whose frames are all ineligible (SDG black frames under rv2).

Share of runs, and share of the not-visible frames in runs, that lie in runs of at most the given length (runs / frames):

| Dataset | Class | ≤ 5 | ≤ 15 | ≤ 30 | ≤ 60 | ≤ 150 | ≤ 300 |
|---|---|---|---|---|---|---|---|
| SDG | forklift | 94.4 % / 38.4 % | 96.9 % / 51.5 % | 98.8 % / 69.2 % | 99.4 % / 80.2 % | 100 % / 100 % | 100 % / 100 % |
| SDG | person | 58.0 % / 7.1 % | 76.5 % / 21.4 % | 86.1 % / 37.9 % | 96.1 % / 72.0 % | 100 % / 100 % | 100 % / 100 % |
| SmartSpaces | forklift | 21.5 % / 0.3 % | 41.8 % / 1.4 % | 52.3 % / 2.6 % | 61.4 % / 4.6 % | 80.9 % / 15.2 % | 87.7 % / 22.9 % |
| SmartSpaces | person | 28.6 % / 0.3 % | 46.3 % / 1.0 % | 57.2 % / 2.0 % | 65.7 % / 3.6 % | 74.7 % / 7.4 % | 81.9 % / 14.0 % |

The two datasets differ in kind. SDG absences are short occlusions in a 10 s clip (the longest is 141 frames, 4.7 s). In SmartSpaces most not-visible time lies in very long runs (an object leaves a camera's view for minutes and returns), so no *g_max* in the range considered turns more than a few per cent of those frames into predicted points.

### 5.2 Number of POWs and of POWs ended by `gap_exceeded` (sensitivity evidence, counts only)

For each value, the oracle points were built with *g_max* = that value and the T8.1 POWs of every person–forklift pair of each camera were built with the same value. The full histograms are in the count files.

| Dataset | *g_max* (frames) | POWs | POWs ended by `gap_exceeded` |
|---|---|---|---|
| SDG (697 cameras, one pair each) | 5 | 864 | 167 |
| SDG | 15 | 790 | 93 |
| SDG | 30 | 750 | 53 |
| SDG | 60 | 710 | 13 |
| SmartSpaces `Warehouse_000` (19 cameras; `Warehouse_001` identical) | 5 | 18,084 | 16,619 |
| SmartSpaces `Warehouse_000` | 15 | 13,907 | 12,439 |
| SmartSpaces `Warehouse_000` | 30 | 11,447 | 9,973 |
| SmartSpaces `Warehouse_000` | 60 | 9,522 | 8,040 |

For orientation, at the TEST-ONLY value of 15 the oracle point counts are: SDG tracked 390,484, predicted 1,166, lost 4,076 (4,027 of them in runs longer than 15), and 89 ineligible frames inside shorter runs with no point; SmartSpaces per scene tracked 1,924,956, predicted 19,109, lost 1,694,590 (1,693,891 in runs longer than 15).

AR-56 item 2 (review flag): the number of eligible frames whose outcome would differ if a visible but ineligible frame did not end a run is **0** in both datasets at *g_max* = 15.

| Parameter | TEST-ONLY | Owner |
|---|---|---|
| *g_max* (frames, eligible) | 15 | |

## 6. Reporting strata

| Stratum | Kind | Definition | Status |
|---|---|---|---|
| data origin / dataset row | per result | T16 | contract |
| viewpoint class | per recording | S0 camera `viewpoint_class` | contract |
| calibration tier, geometry method | per pair-frame | §4.2; exports carry `geometry_method` | contract |
| clearance band | per pair-frame | the band scheme of §4.2 | contract |
| support basis | per metric | detected; detected + inferred | contract (N6) |
| `low_light` | per recording | rv2 tag (AR-51) | accepted |
| **`forklift_turning`** | **per pair-frame** | **new, proposed below** | **to be decided at G-PR** |

### 6.1 Proposal: `forklift_turning` (Architect ruling on CR-023, 14 Nov 2026)

Purpose: report R3 and R4 results separately for frames on which the forklift is turning and frames on which it is not. R3 and R4 predict with a constant velocity and a footprint that does not rotate (T8.3, T15.1). During a pivot turn the forklift's footprint centre moves across its body axis (CR-023), so the prediction is furthest from the motion exactly there.

**Proposed definition** (the T9.2 construction applied to the forklift's yaw):
- For pair-frame k, let a and b be the first and last frames inside the window of length *w_turn* centred on t_k, shifted as in T9.1, on which the forklift's `object_state` yaw (T8.2) is non-null, with t_b − t_a ≥ *w_turn*/2.
- forklift_yaw_rate = |wrap_π(yaw_b − yaw_a)| / (t_b − t_a) in rad/s, where wrap_π folds the difference to (−π/2, π/2]. The fold is proposed because the footprint rectangle is unchanged by a half-turn and the SmartSpaces truth contains half-turn jumps of the supplied rotation (below).
- `forklift_turning` = true when forklift_yaw_rate > *e_fturn*; false when it is ≤ *e_fturn*; **unknown** when the yaw is null on the window or the window is too short. Unknown frames are reported as a third group and never added to either.
- It is a reporting stratum only. It changes no flag, label, episode or denominator.

| Parameter | Proposed | Alternatives | Owner |
|---|---|---|---|
| *w_turn* | 0.5 s (= *w_v*) | 1.0 s (= *w_e*) | |
| *e_fturn* | **5°/s (0.087 rad/s)** | 2°/s, 10°/s as a sensitivity report | |

**Evidence** (`research/datasets/part3/yaw_rate_distribution.json`; truth yaw of every forklift frame, unfolded difference, nearest-rank percentiles; statistics only):

| Dataset | Window | Forklift frames | < 1°/s | 1 to < 5°/s | 5 to < 20°/s | 20 to < 120°/s | ≥ 120°/s | P50 | P90 | P99 | Max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SDG (67 runs with a `ceiling_00` annotation) | 0.5 s | 20,081 | 55.9 % (11,226) | 0.8 % (164) | 2.8 % (568) | 40.5 % (8,123) | 0 | 0.0 | 75.0 | 75.0 | 84.4 |
| SDG | 1.0 s | 20,081 | 50.3 % (10,105) | 1.7 % (350) | 5.7 % (1,146) | 42.2 % (8,480) | 0 | 0.0 | 75.0 | 75.0 | 83.1 |
| SmartSpaces `Warehouse_000` (9 forklifts) | 0.5 s | 80,626 | 79.5 % (64,082) | 0.9 % (718) | 4.4 % (3,550) | 15.0 % (12,100) | 0.2 % (176) | 0.0 | 24.1 | 26.0 | 337.5 |
| SmartSpaces `Warehouse_000` | 1.0 s | 80,604 | 77.7 % (62,648) | 1.3 % (1,054) | 6.8 % (5,485) | 13.8 % (11,129) | 0.4 % (288) | 0.0 | 24.1 | 25.1 | 180.0 |

Rates in degrees per second.

Reading: both datasets are two-peaked. Most frames have no rotation at all, and turning happens at one simulator-specific rate (about 75°/s in SDG, about 24°/s in SmartSpaces), with short ramps between. Any *e_fturn* between about 2 and 20°/s separates the two peaks in both datasets; the proposed 5°/s puts under 1 % (0.5 s window: 0.8 % in SDG, 0.9 % in SmartSpaces) of frames between 1°/s and the threshold. SmartSpaces also has 176 frames (0.5 s window) with an apparent rate of 120°/s or more; the largest is 337.5°/s, which is a 180° change within the window, i.e. a half-turn jump of the supplied rotation and not a motion. The fold removes these.

Points the Owner or Architect must settle for this stratum:
1. Whether the stratum needs contract text (a new per-frame field or a derived report key). The agent implements nothing until that is decided.
2. On the detector path the yaw may come from the T8.2 heading fallback, which CR-007 / D-8 shows to be about 77° off during SDG pivots. A turning stratum computed from that yaw would be unreliable there; this belongs to the T-22 decision.

## 7. Configurations

All on oracle perception (ORACLE-S3 from simulator truth, T17–T19), single camera, frame-quality rules rv2, the grouping of §3.1.

| Configuration | Providers (T15.6) | Geometry | Role |
|---|---|---|---|
| BL-2 | R1 | image only | primary comparison with BL-3 |
| BL-3 | R2 | world | primary comparisons with BL-2 and BL-6 |
| BL-4 | R2 + R3 | world | secondary |
| BL-5 | R2 + R4 | world | secondary |
| BL-6 | R2 + R3 + R4 + R5 | world | primary comparison with BL-3 |
| BL-1 | — | — | deferred to M1b (T15.6) |

| Choice | Proposed | Reason | Owner |
|---|---|---|---|
| Geometry source for the event configurations | `simulator_truth` positions (zero covariance, AR-36 item 4) | isolates the rules from geometry error; this is the "AB-3 upper bound" of WP-14 | |
| Geometry source for GV-01, GV-04–GV-08 | a second run with `full_camera` geometry from the oracle boxes and the dataset calibration (`supplied_unvalidated`) | with simulator positions the position error is zero by construction, so GV-01 would say nothing. WP-14 asks for "geometry from oracle boxes vs simulator positions" | |
| Paired comparisons | BL-2 vs BL-3 and BL-3 vs BL-6, paired bootstrap of T11.2 on EV-M1, EV-M2 and EV-M7 | T15.6, WP-14 | |
| Label groups reported | O, H, PC against definition-applied references; evasive action against the SDG `Dodge` annotation where present | WP-14. **No NM-versus-contact claim on SDG** (WP-14 non-goal) | |

Oracle-path results are never pooled with detector-path results (Architect review of AR-35).

## 8. Primary metrics and estimands

| Family | Metrics | Estimand and interval | Reported as |
|---|---|---|---|
| Reliability | MR-01 (exact stages: identical payload hashes on a second run) | exact | verified / not verified |
| Geometry | GV-01, GV-03, GV-04, GV-05 (= MR-11), GV-06, GV-07, GV-08 | descriptive per stratum; Bland–Altman where N7 says so | measurement of the `full_camera` geometry path against simulator positions |
| Completeness | CM-01–CM-10 on both support bases (CM-10 basis-independent, T13.1; CM-06 a sum, CM-07 a count, T13.3) | ratio of sums over RES windows (T12.4); Target A and Target B intervals | on the oracle path: implementation conformance |
| Events | EV-M1–EV-M8, with EV-M10 and its sensitivity values beside EV-M2 and EV-M7 (T12.2) | Target B (`new_session_performance`, cluster bootstrap over leakage groups) as the headline on SDG test; Target A (`frame_description`) alongside | implementation conformance (same truth on both sides, T17.6) |
| Robustness | MR-08, MR-09, MR-10, MR-12 on the grids of §4 | `label_stability_frac`, elasticity; **validation partition only** | parameter sensitivity |

Proposed **primary** metrics (the ones acceptance criteria are written on): MR-01; GV-01 RMSE and GV-07 speed RMSE (`full_camera` run); CM-03 and CM-08; EV-M1 and EV-M2 per configuration; MR-08 `label_stability_frac`. All others are secondary and reported in full.

T14.3: the number of leakage groups per partition and data origin is printed beside every Target B interval.

## 9. Acceptance criteria — proposal

Each row becomes one `acceptance_criterion` record (§5.9) with `preregistration_ref` and `frozen_utc` set at the freeze. Criteria must be frozen before the first test-partition evaluation (§9.6). **The targets are the Owner's to choose.** Where the agent has no evidence for a number it proposes none.

| # | output_id | Type | Metric, slice | Rule | Target (proposed) | n_min_units | Estimand | Owner |
|---|---|---|---|---|---|---|---|---|
| 1 | all exact stages | repeatability | MR-01, every exact-class artifact of the run | exact_equal | identical payload hashes | 1 run pair | — | |
| 2 | object positions | technical_accuracy | GV-01 RMSE, `full_camera`, per viewpoint class | ci_upper_le | ______ m | 20 groups | new_session_performance | |
| 3 | speed | technical_accuracy | GV-07 RMSE at the base *w_v* | ci_upper_le | ______ m/s | 20 groups | new_session_performance | |
| 4 | clearance | technical_accuracy | GV-04 bias (prior footprint − simulator 3D box footprint) | abs_bias_ci_within | ______ m | 20 groups | new_session_performance | |
| 5 | POW coverage | completeness | CM-03, detected + inferred basis | ci_lower_ge | ______ | 20 groups | new_session_performance | |
| 6 | clearance availability | completeness | CM-08 | ci_upper_le | ______ | 20 groups | new_session_performance | |
| 7 | E1 episodes, per BL configuration | technical_accuracy | EV-M1 (headline recall), label group O/H/PC | ci_lower_ge | ______ | 20 groups | new_session_performance | |
| 8 | E1 episodes, per BL configuration | technical_accuracy | EV-M2 (headline precision) | ci_lower_ge | ______ | 20 groups | new_session_performance | |
| 9 | E1 episodes | parameter_robustness | MR-08 label flip rate over the §4.3 grid (validation) | flip_rate_le | ______ | 30 windows | frame_description | |
| 10 | E1 episodes | comparability | EV-M1 difference ceiling − eye_level | abs_bias_ci_within | ______ | 20 groups per class | new_session_performance | |

Notes for the Owner's choice:
- Criteria 5, 7 and 8 on the oracle path compare the truth with itself through the rules. A value below 1 there points to a rule or implementation property (for example T18 lost runs, eligibility, lifecycle parameters), not to perception error. Targets for them describe conformance, not accuracy.
- Whatever the targets, the status on synthetic data is at most `experimental` (T12.5).
- A criterion left without a target is not registered, and its metric is reported without a decision (`not_assessable`: no registered criterion).

## 10. Limitations and open decisions that the freeze depends on

1. **Truth-side statistics cover all held runs,** including runs that the §2 draw will put in test. They use no system output, but *g_max*, *e_fturn* and the footprint priors would be chosen with knowledge of test-partition truth. The Owner may instead ask for these statistics on the validation runs only, after the split is frozen.
2. **AR-56 item 2** (review flag): a not-visible run ends at any frame the dataset lists as visible, eligible or not. §5 gives the number of frames on which the other reading would differ.
3. ***g_max* sets how many POWs a long occlusion produces.** For a not-visible run longer than *g_max* the POW ends with `gap_exceeded` and a continuation POW starts (T8.1, T18; Architect ruling on AR-55 item 6). §5 gives the counts.
4. **SmartSpaces forklift footprint** (§4.2): two box sizes, one prior per class.
5. **`forklift_turning`** (§6.1): needs a decision on contract text.
6. **CR-007 / D-8** stays deferred to T-22; it does not affect the oracle path.
7. **Real footage** is outside this pre-registration. Before any real-data result: *k_sup* from that footage's frame intervals, the dark-frame spread report (D-25 ruling A item 6), and the D-26 values.

## 11. What is frozen at G-PR

The Owner's values for §2–§9; the contract version; the analysis code commit and `requirements.lock` digest (the agent fills these in on the commit the Owner approves); the split draw seed and the bootstrap seed; the list of acceptance criteria. After the freeze, any change is a new version of this document with a stated reason, made before the affected evaluation, and results under an older version are not mixed with results under a newer one.
