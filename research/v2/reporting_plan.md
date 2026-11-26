# v2 reporting plan (D-61 §1.6–1.7, D-63)

Status: candidate, experimental, synthetic-data evaluation. Nothing in this file is a result. It lists what the single v2 reporting run (110 reporting cameras) and the single X0b test run (471 test cameras) produce, and the limitations that every report carries. The values, criteria and references are those of `docs/preregistration_v2_FROZEN.md` and `docs/preregistration/freeze_record_v2.json` (SHA-256 `6f7ca439…`), which this file does not change. Where this file and the frozen pre-registration differ, the frozen file applies; on stated *reasons*, `docs/preregistration/v2_rationale_addendum_D63.md` applies.

## Order (D-61 §1.7, D-63 rulings 5, 7, 8)

1. The 110 reporting cameras, once, on the frozen v2 configuration, after the D-62 equivalence check passes (D-63 STEP 5).
2. The X0b test (48 SDG runs, 471 cameras), once, before 1 Dec 2026, after the window lock (D-63 STEP 3), the reporting run and the R-2 audit (D-63 STEP 7). Test S2 may run early on Colab; its output is hashed on arrival and not opened, counted, plotted or summarised until STEP 7 (D-63 ruling 8).
3. Tier 1 (SmartSpaces held-out layouts): **deferred past 1 Dec 2026** (CR-039, D-63 ruling 5). SmartSpaces event-level results are excluded from this submission because no v2 SmartSpaces reference set exists: T21.1 is infeasible on scene-wide truth and the T21 jointly-visible amendment is not written (register D6).

## Tables (D-61 §1.6; D-63 STEP 5 item 3)

Each partition's run produces the same tables, in `research/v2/<partition>_results.json` and `research/v2/<partition>_report.md`:

1. **Headline:** BL-6 on the detector path.
2. **Decomposition:** oracle and full_camera columns. Oracle results are never substituted for detector-path capability.
3. **Registered criteria** with pass or fail as computed: MR-01; GV-01 ceiling and GV-01 eye_level (0.25 m); GV-07 (0.15 m/s); GV-04, labelled circular (reported, never cited as evidence). A failed criterion is reported as failed; targets are not moved.
4. **Descriptive GV:** GV-01 and GV-07 in the D-41 form (median, P95, outlier share), position availability by null reason beside every GV-01 value, and GV-01 / GV-07 on detector boxes.
5. **EV-M1 / EV-M2** with confidence intervals (bootstrap B 2,000, seed 2026111402, CI 0.95), at iou_m 0.3 (N4), 0.5 and 0.7, per viewpoint. Descriptive; no success threshold.
6. **The IE share**, the `speed_near_v_min` counts, and the registered paired comparisons (BL-2 vs BL-3, BL-3 vs BL-6, oracle path, with their decision rules), plus the same pairs on the detector path without a decision rule.

## Limitations carried into every report

The fifteen limitations of `preregistration_v2_FROZEN.md` §10 (D-61 §4 with the STEP 0 findings), and, added under D-63:

16. **T25.2 is inert under v2** (D-63 ruling 2). With g_max = m_gap_s = 1.5 s, a POW break needs a gap above 1.5 s while a join needs a gap ≤ 1.5 s, so no join can occur. A track that changes ID after a gap is handled by T25.1 stitching, after which the gap is bridged; every gap ≤ 1.5 s is bridged, and every longer gap separates two encounters by definition (D-61 §1.3). The code stays and `join_across_pow` stays true in the configuration. The methods text states this.
17. **The T25.1 stitching gap T_s = 5 s is at the top of its grid** ({1, 2, 3, 5} s; D-63 ruling 3), so longer gaps were not tried. The selection was made by IDF1 on S3 points, which g_max does not affect (it acts only after tracking), so limitation 12 does not make the selection depend on g_max.
18. **g_max means 1.5 s** (CR-038, reading (b)). It equals 45 frames on every v2 recording (all 30 fps); the seconds-valued representation is implemented only before the first S4 on a recording that is not 30 fps.
19. **SmartSpaces event-level results are excluded** from this submission (CR-039 deferred).
20. **Stated reasons corrected by the D-63 addendum:** the 1.5 s anchor is a typical, not conservative, reaction time; no TTC threshold is validated for forklift–pedestrian encounters; the half-threshold accuracy rule is a minimum feasibility floor, looser than metrology practice. Unverified: whether the dataset forklift boxes include the forks (if not, clearance at the fork end is overstated by up to about 1.1 m); ISO 3691, ISO 6292, ANSI B56.1, HSE L117 texts and SSAM defaults were not inspected.
