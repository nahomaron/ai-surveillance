# WORKPLAN — RQ1 implementation schedule

**Owner:** Research Owner · **Engineering lead:** Claude Code · **Independent auditor and contributor:** Codex
**Contract:** See `CLAUDE.md` for the normative E-1.2.26 documents and the D-67 prospective scope addendum · **Plan details:** Package F
**Active mode (27 Nov 2026, D-67):** Claude Code and Codex may contribute under the D-67 roles and [agent contribution register](docs/AGENT_CONTRIBUTIONS.md).

**Historical mode (9 Nov 2026, Owner decision):** a single agent replaces the multi-agent team. F.1 Parts B and C are superseded. Its safeguards are kept in simpler form: tests written first from the documents, no editing of expected values, determinism re-runs, a self-audit at each milestone, and Owner review at STOP points.

How to use this file:
- Follow task dependencies. In M1c, independent E1 and E2 design and qualification can proceed in parallel while integrity corrections are underway.
- Status markers: `[ ]` open · `[~]` in progress · `[x]` done · `[B]` blocked (reason in the log) · `[S]` STOP — waiting for the Owner.
- Size is a rough guide: S ≈ one session, M ≈ 2–3 sessions, L ≈ 4+ sessions.

---

## 0. Owner pre-approvals (the Owner ticks these before the first session)

| Approval | Ticked |
|---|---|
| Create `.venv` and `pip install` the packages named in S-01 into it | [-] |
| After M0 is accepted: download one SDG-Warehouse near-miss shard and selected synthetic SmartSpaces scenes, **22 GB cap in total, outside git**, **after** recording source authenticity and licence terms in T-17. Real-world scenes (`Warehouse_026`, `Warehouse_027` and any other real footage) are excluded (Owner decision D-3, 9 Nov 2026) | [-] |
| Install CPU-only PyTorch or ONNX Runtime for the detector benchmark (T-22), if available for this platform | [-] |
| **Amendment D-21 (12 Nov 2026):** download cap raised to **30 GB in total**, outside git. Real-world footage is permitted **for testing only** (no training or fine-tuning), stored under `data/raw/real/`, after it is recorded in `qualification.md` Part 3 and the Owner approves the selection (D-24); no processing of real footage before G-FQ (D-25) | [-] |
| **D-42 (19 Nov 2026):** detector environment `.venv-det` (macOS system Python 3.9.6, PyTorch 2.2.2 CPU; git-ignored; outside `requirements.lock`) accepted. New installs into `.venv-det` only, pinned in `research/m1b/requirements_detector.txt`: `ultralytics` and `transformers` (newest versions supporting Python 3.9 and torch 2.2.2: 8.4.215 and 4.57.6, with their dependencies), and the Ultralytics CLIP fork from git pinned by commit (Owner answer, 19 Nov 2026). Downloads: YOLO-World v2-s weights with the CLIP ViT-B/32 text encoder, and IDEA-Research/grounding-dino-tiny (safetensors), each below 1 GB, into git-ignored `out/m1b/weights/` | [-] |
| **D-42 budget (Owner answer, 19 Nov 2026):** model weights count toward the download cap; the cap is raised from 30 GB to **31.5 GB** in total for this task | [-] |
| **D-59 (24 Nov 2026, Owner instruction):** download cap raised to **60 GB in total** (60 × 10⁹ bytes, weights and everything held counted), outside git. Purpose: data that does **not** duplicate what is held. Scope: synthetic `PhysicalAI-SmartSpaces` `MTMC_Tracking_2026` scenes with ground truth that are not re-renders of a scene selected or held, without depth maps, at the pinned revision `d38193b` (CC BY 4.0, licence row unchanged), selected and hashed in `qualification.md` Part 5 **before** download. No real footage, no new source, no training use, no partition or split change: how the new data enters tuning or testing is proposed to the Architect, not decided by the agent | [-] |
| **D-60 (25 Nov 2026, Owner decision):** cloud upload of the 45 tier-1 D-59 videos to the Owner's Google Drive; Colab GPU for S2 on those videos only. Also covered (D-60 STEP 4 c): the videos of the 2 tuning cameras of the equivalence check (synthetic tuning data). The Owner uploads; the agent sends nothing off this computer. Nothing downstream of S2 runs on Colab | [-] |
| **D-63 (26 Nov 2026, Owner decision, rulings 7–8 and STEP 4):** cloud upload of the 110 v2 reporting-camera videos and the 471 X0b test-camera videos (SDG, synthetic) to the Owner's Google Drive; Colab GPU for S2 (detection only) on those videos, after the D-62 equivalence check passes. The Owner uploads; the agent sends nothing off this computer. Nothing downstream of S2 runs on Colab. Test S2 output is hashed on arrival and otherwise not opened before D-63 STEP 7 | [-] |

Never pre-approved: paid services, cloud upload of data (except the D-60 and D-63 rows above), real worker footage (except the D-21 testing-only exception above), fine-tuning compute purchases, any contract change.

**Owner setup before the first session:**
1. Update Claude Code (installed via MacPorts) and check `claude --version`.
2. Create the GitHub repository and connect the local repository to it (`git remote add origin …`).
3. Copy the documents into the repository: `CLAUDE.md` and `WORKPLAN.md` (root); the frozen contract and F.1 into `docs/contract/`; Package F into `docs/plan/`; C.1, D, D.1 into `docs/methodology/`.
4. Start Claude Code in the repository and give it the kickoff prompt from §7.

---

## 1. Milestone M0 — deterministic contract verification (CPU, no datasets)

| ✓ | ID | Task | Needs | Contract refs | Done when | Size |
|---|---|---|---|---|---|---|
| [x] | S-01 | **Environment.** Check that binary wheels exist for numpy, scipy, pyarrow, av (PyAV), opencv-python-headless, jsonschema, hypothesis, pytest and an RFC 8785 library on the current Python. Create `.venv` and install. Record versions in `docs/ENVIRONMENT.md`. If wheels are missing and Python 3.12 is not pre-approved → **STOP** | — | Package F §2 | Imports succeed; lock file committed | S |
| [x] | S-02 | **Skeleton.** Package layout, pytest configuration, `out/` and data paths git-ignored, `PROGRESS` section started, `DECISIONS_NEEDED.md`, `docs/CHANGE_REQUESTS.md` | S-01 | Package F §2 | `pytest` runs (0 tests); first push | S |
| [x] | T-01 | **Schemas and validators (WP-00).** One schema source for every table; validators for all active VR rules; each rule has one failing fixture | S-02 | E-1.2.1 §1, §5, §10.3, §12.1; F.1 A6 | CT-E-01, CT-E-05, CT-E-30; VR failing-fixture coverage report | M |
| [x] | T-02 | **Identity (WP-01).** Anchor, configuration, observation, human and execution ID classes; artifact builder (7-step sequence); same-artifact references; reconstruction check | T-01 | E-1.2.1 §2; F.1 A1 | CT-ID-01–07, CT-FK-01–07, CT-NK-01–08, CT-I-01/03–08; reproduces `art_pmpcesnhpbbgtw2f3fhb6zkqxk` and `trk_zr3hb5b6y2jjuw7ab7aml6ymtf` | M |
| [x] | T-03 | **Record fixtures (WP-02 part 1).** From Appendix N: N1 (T1–T13), N2 (G1–G3), FX-TIE, FX-W, FX-CM, FX-ID-1–8, FX-RC-1–6, FX-A3.1, FX-B/C/D, FX-12. Every expected value is copied from Appendix N or derived in a written hand calculation | T-02 | Appendix N; F.1 A3, A5 | Fixture manifest with hashes; each expected-value file cites its source | M |
| [x] | T-04 | **Clip fixtures (WP-02 part 2).** Use PyAV (no FFmpeg CLI) to generate FX-CLIP-A–D, VFR, B-frame, duplicate-PTS, untimed, corrupt-packet, dropout and two-file clips | T-03 | E-1.2.1 §3; Appendix N3 | Clips deterministic (same bytes on re-run); manifest updated | M |
| [x] | T-05 | **Registration S0 (WP-03).** Anchors, timelines, clock alignments, tiered calibrations; ANC-1 conflict check | T-02 | E-1.2.1 §3.1, §4, §5.1; F.1 A1 | FX-A3/A4, FX-B1–B3, CT-I-05/06, CT-NK-04/05 | M |
| [x] | T-06 | **Decode S1 (WP-04).** Timestamp resolution, eligibility, reorder depth, support (ST-1–ST-6), coverage tiling | T-04, T-05 | E-1.2.1 §3.2–3.6 | CT-T-01–13, CT-T-14–17 (frame/coverage parts), CT-T-20 (a, b), CT-E-04; expected support A/B/C/D = 0.100/0.067/0.033/0.133 s | L |
| [x] | T-07 | **E2 feasibility research (read-only, document only).** Check dataset cards and public metadata for scenes with workers **and** elevated loads in the same scene, height references, calibration, temporal coverage and licence. Mark each finding verified, unverified, missing, or needs collection. **No downloads** | S-02 | Package F §6 | `research/e2/E2_feasibility_report.md` pushed | S |
| [x] | T-08 | **Substrate S4 with oracle tracks (WP-05).** Oracle track source, geometry, POWs, pair series, exposure profiles, activity segments, evidence classes | T-06 | E-1.2.1 §3.4–3.5, §4.2, §5.4–5.5 | CT-E-06/07/08/11, CT-F-01/02, CT-T-14–19 (durations), CT-T-20 (c, d), FX-D1/D2, N2 G1–G3 flags and clearances | L |
| [x] | T-09 | **Events S5 (WP-06).** Providers R1, R2, R3, R5; G, Q; lifecycle; contact state; labels; single-camera events; counts | T-08 | E-1.2.1 §5.6, §6, §6.0 | CT-E-09/10/12/13/14; N1 T1–T13 exact; CL-INV property test | M |
| [x] | T-10 | **Splits and sampling (WP-07).** Leakage groups, split freeze, audit, PR-01, R-1–R-4, RES/ECS plans, window tiling, audit gate | T-05, T-06 | E-1.2.1 §8; errata rules | CT-S-01–10, CT-E-18/19/23; estimator simulation (D1-AC-09) | M |
| [x] | T-11 | **Validation store (WP-08).** Reference tables with `reference_class`; timeline reference coverage; status log hash chain; namespace guards; simulator-reference converter | T-02, T-10 | E-1.2.1 §5.8; F.1 A3, A5.1 | CT-E-24/25, CT-RC-01–03, VR-E-052/053/055 | M |
| [x] | T-12 | **Evaluation part 1 (WP-09a).** Identity association, matching with composite tie weights, match classes, EV-M metrics | T-09, T-11 | F.1 A5.2; Appendix N4 | CT-ID-A1/A2, CT-E-20/21, FX-TIE (s1→r1, r2 miss) | M |
| [x] | T-13 | **Evaluation part 2 (WP-09b).** Weighted estimators, Kish n_eff, stratified and cluster bootstrap, Wilson, Bland–Altman, ICC(2,1), κ | T-12 | Appendix N5 | FX-W: 0.71875 weighted, 0.70 unweighted, n_eff 3.3793103448 | M |
| [x] | T-14 | **Evaluation part 3 (WP-09c).** Completeness CM-01–10, error attribution (rule tests and oracle factorial), acceptance criteria, scoped fitness engine | T-13 | Appendix N6, N9; E-1.2.1 §9.4–9.6 | FX-CM CM-01 = 0.600; FX-ID-3 CM-01 = 0.9; CT-E-22/29, CT-F-03–10, CT-ID-A3 | M |
| [x] | T-15 | **Export and reports (WP-10).** Export classes, fixture banner, wording rules, status board | T-14 | F.1 A2; E-1.2.1 §11 | CT-X-01–05, CT-E-26/27/28 | S |
| [x] | T-16 | **M0 integration and self-audit (WP-11).** Run the whole fixture pipeline twice from a clean clone; full suite; complete the self-audit (§5); write `reports/M0_report.md` (§6 template); tag `m0-verified`; push | all above | Package F §12 | All M0 tests pass; identical artifact IDs across both runs | M |
| [x] | G-M0 | **STOP — Owner reviews M0.** Recommended: share the repository with the Research Architect for an independent review before accepting | T-16 | — | Owner writes "M0 accepted" in `DECISIONS_NEEDED.md` | — |

---

## 2. Milestone M1a — oracle-perception synthetic slice (after G-M0)

| ✓ | ID | Task | Needs | Refs | Done when | Size |
|---|---|---|---|---|---|---|
| [x] | T-17 | **Dataset qualification (WP-12).** Record source URLs, versions, licence terms and authenticity evidence **before** downloading. Download only if pre-approved in §0; otherwise **STOP**. Reproduce the census facts (1 worker, 1 forklift, 300 frames, 10 views). Verify units. Extract lineage. Report the frame-interval distribution of every downloaded recording (min, median, P99, max, VFR flag) | G-M0 | Package F WP-12 | `research/datasets/qualification.md`; licence rows; data outside git | M |
| [x] | T-17b | **Qualification Part 3 (D-20 to D-22).** Record SDG shard→run map and a seeded draw, SmartSpaces real scenes, Safe and Unsafe Behaviours, FieldWorkArena exclusion, real-data rules, budget ≤ 30 GB — **before** any download | T-17 | VR-E-070; D-21 | `qualification.md` Part 3; D-23, D-24, D-25 opened | S |
| [S] | G-DL | **STOP — Owner approves the Part 3 selection (D-24)**, then download with SHA checks | T-17b | — | Owner decision in D-24 | — |
| [x] | T-18 | **Dataset adapters (WP-13).** SDG and SmartSpaces → S0, oracle tracks, simulator references; `reference_class` set correctly | T-17 | Package F WP-13; F.1 A5.1 | Truth round-trip within 1e-6 m; reprojection check | L |
| [x] | T-19 | **R4 and configurations BL-1–BL-6 (WP-06b)** — under T15 (E-1.2.13; CR-018 / D-27 closed); BL-1 deferred to M1b | T-09 | E-1.2.1 §6.0 | R4 fixtures with hand-computed TTC/PET | S |
| [x] | T-20 | **Draft the pre-registration** (proposal only): parameter grids, configurations, strata, primary metrics, acceptance criteria with targets and n_min. **Does not run test-partition evaluation** | T-18, T-19 | E-1.2.1 §9.6; D.1 | `docs/preregistration_DRAFT.md`, with this checklist: (1) *k_sup* chosen from the measured frame-interval distribution of the qualified datasets, above their natural VFR jitter; (2) camera grouping basis declared explicitly for every research configuration (AR-22); (3) frame-quality rules version (AR-27); (4) w_ref and its relation to timeline lengths (D-7); (5) the not-visible run-length table per dataset and class (T18 amendment 3), for the choice of g_max; (6) a proposed per-frame stratum `forklift_turning` (|yaw rate| above a stated value; CR-023 ruling), so R3/R4 results are reported for turning and straight frames separately | M |
| [x] | G-PR | **STOP — Owner approves and freezes the pre-registration** (the Owner, not the agent, chooses scientific thresholds) — frozen 14 Nov 2026 (D-34, D-35; written by the agent with the Owner's values, on the Owner's instruction) | T-20 | — | `docs/preregistration_FROZEN.md` committed by the Owner | — |
| [x] | G-VAL | **STOP — Owner go-ahead for the M1a validation run (D-36).** Approved for validation only (14 Nov 2026); test reserved (D-37) | G-PR | — | Owner decision in D-36 | — |
| [~] | T-21 | **M1a run (WP-14)** (validation only, D-36, D-37; D-38 option A and T21 / CR-025 decided 14 Nov; SmartSpaces EV-M waits for D-39). Validation partition first, then test. GV-01, GV-03–08; MR-01, MR-08–12; CM-01–10; EV-M1–M8; BL-2 vs BL-3 and BL-3 vs BL-6 on oracle perception. Report rule-conformance results separately as "implementation conformance" | G-PR | Package F WP-14; Appendix N | `reports/M1a_report.md`; tag `m1a-complete` | L |
| [x] | G-M1a | **STOP — Owner reviews M1a** (D-40 DECIDED 17 Nov 2026: M1a accepted as experimental validation evidence) | T-21 | — | Owner decision recorded | — |

---

## 3. Milestone M1b — detector-based slice (after G-M1a)

| ✓ | ID | Task | Needs | Done when | Size |
|---|---|---|---|---|---|
| [x] | T-22 | **Detector benchmark (WP-15) — revised scope (D-42 option (a), 19 Nov 2026): zero-shot detectors.** Runtime check done (`feasibility.md`). Probe YOLO-World v2-s and Grounding DINO tiny, prompts exactly "person" and "forklift", on 100 SDG validation frames (5 from each of 20 validation cameras, 10 ceiling and 10 eye-level, seeded draw 2026111901), against the oracle-path simulator boxes (visible objects, clipped). Same-class matching at IoU ≥ 0.3, one-to-one by descending IoU. Recall and precision at score thresholds 0.05–0.50, the best-F1 threshold, per viewpoint, s/frame and peak memory. No S4/S5/S8 with detector output, no fine-tuning, no Ultralytics trackers, no change to the pre-registration or any analysis module. **STOP after the report** (D-45) | G-M1a; §0 approval (D-42) | `research/m1b/zero_shot_probe.md` and `.json` | M |
| [x] | T-23 | **Tracker adapters (WP-17)**, reduced to the D-45 pilot (item 1): Ultralytics ByteTrack per class (default parameters), S2 rows → S3 rows, bridges of ≤ g_max = 15 eligible frames predicted/inferred, longer lost; fixtures with dropouts, noise, an ineligible frame, a fragment and a swap; T-12 association; IDF1 (TrackEval port, AR-62) | T-22, D-45 | tests in `.venv-det` and main suite; HOTA not required (D-45) | M |
| [x] | T-23s | **S2 detector stage (WP-15 adapter; D-45 item 2):** YOLO-World v2-s, Ultralytics defaults, "person" 0.20 / "forklift" 0.05, every eligible frame; `detection` rows with license_component; tolerance class | T-23 | S2 tests; runtime measured on one camera | S |
| [x] | T-25p | **Detector-path pilot (D-45 item 3):** 206 SDG validation cameras (probe cameras excluded); S1 → S2 → S3 → S4 full_camera → S5 BL-2..BL-6 → S8 vs T21; 100-frame two-model check (seed 2026111902); `reports/M1b_pilot_report.md` (columns A/B/C). **STOP (D-47)** | T-23s | report pushed | M |
| [B] | T-24 | **Fine-tuning (WP-16). BLOCKED** until the Owner decides licence posture, training data and compute (C2–C4) | Owner | — | — |
| [B] | T-25 | **M1b integration (WP-18). BLOCKED** on T-24, or on a qualified pretrained forklift detector from T-22 | T-24 | — | — |
| [x] | T-26d | **D-59 download (Owner, 24 Nov 2026):** cap 60 GB; qualification Part 5 before download; ground-truth screen; 11 SmartSpaces 2026 scenes (118 cameras: 7 scenes in 6 new layouts, 4 new scenarios in the held layout), hash-checked; frame-count and interval checks | D-59 | `research/datasets/part5/d59_report.md` | M |
| [x] | G-D60 | **STOP — Architect and Owner decide how the D-59 scenes are used (D-60, CR-036):** split mechanism, `layout_id` and `generation_batch`, roles of tier 1 and tier 2, compute. Proposal in `d59_report.md` §6. Independent of D-58; nothing on the new scenes until decided | T-26d | D-60 decided | — |
| [ ] | T-26q | rv2 frame-quality statistics on the 118 D-59 recordings (statistics only, as qualification 3.12). Tier 1: totals only (D-60 hard limits) | T-26d | counts recorded in Part 5 | S |
| [x] | T-26r | **D-60 STEP 2:** S0 registration of the 11 D-59 scenes (`synthetic_rendered`; `layout_id` = SHA-256 of `map.png`; `generation_batch` per ruling 4; calibration) and S1 coverage | G-D60 | S0 and S1 artifacts; summary JSON | S |
| [x] | T-26s | **D-60 STEP 3:** split addendum `X0b-A1` (one leakage group per layout; tier 1 `test_layout_holdout`, tier 2 `reserve`; X0b unchanged), frozen before any system output; X0c audit | T-26r | split artifact; freeze record | S |
| [x] | T-26c | **D-60 STEP 4:** Colab S2 package (`research/colab/`: notebook, runner, `tier1_manifest.json`, `HOWTO.md`); equivalence-check comparator for 2 tuning cameras | T-26s | package pushed; D-62 opened | S |
| [x] | G-D62 | **STOP — the Owner runs the 2-camera equivalence check on Colab (D-62)** and, on a pass, tier 1 | T-26c | outputs returned | — |
| [B] | T-26g | **Deferred past 1 Dec 2026 (D-63 ruling 5; the equivalence part was done in T-29q, D-62 PASS).** **D-60 STEP 5:** verify the Colab outputs; equivalence result; S2 artifacts for the 45 tier-1 cameras; integrity checks (totals only); next D; STOP | G-D62 | S2 artifacts; integrity totals | S |
| [B] | T-26e | Evaluation on the D-59 scenes in the roles D-60 sets: tier 1 once, with the frozen v2 package, after the v2 reporting run, per scene and per layout, descriptive; tier 2 nothing until a later Owner decision | T-26g; v2 freeze | results per D-60 | L |
| [x] | T-27 | **D-58 (Owner, 24 Nov 2026): T25 (E-1.2.26) opt-in** — T25.1 track stitching, T25.2 episode continuity across POW breaks, T25.3 m_gap in seconds; T25.4 tests; regression (stored D-54 / D-57 artifacts, M0 IDs); stitching grid on the 116 tuning cameras (tracking measures only); event-level check α / β (diagnostic) | D-58 | `research/m1b/d58_report.md` | M |
| [x] | G-D61 | **STOP — Owner and Architect review the D-58 results (D-61):** stitching values (selected, not frozen), CR-037, AR-69. Blocks the v2 freeze, the reporting-camera run and the demo build; independent of D-60 | T-27 | D-61 decided | — |
| [x] | T-28r | **D-61 STEPS 0–1 (Owner, 26 Nov 2026):** state check (report only); D-61 DECIDED; §1 verbatim in `v2_notes.md`. STEPS 2–3 were already done under D-58 (T-27: 2f4ad7e, 66809cd) | G-D61 | records pushed | S |
| [x] | T-28e | **D-61 STEP 4:** one diagnostic event check on the 116 tuning cameras, C-v2+T25 and A+T25 at the v2 base values (§1.3) with the D-58 stitching selection, scored against a separately stored diagnostic v2 tuning reference set; EV-M1, EV-M2, n_members, unobserved_gap_s, IE share caused by g_max 45. Selects nothing. Estimate on 2 cameras; STOP above 3 h | T-28r | `research/m1b/d61_events_tune.json` | M |
| [x] | T-28f | **D-61 STEP 5:** `docs/preregistration_v2_FROZEN.md` (v1 structure, §4 = D-61 §1.3–1.5, §1.6–1.7 text); v2 freeze record built twice, identical; v2 reference sets (tuning, reporting, test) from simulator truth (T21.1), IDs and hashes in the record | T-28e | freeze record; v2 references | M |
| [x] | T-28t | **D-61 STEP 6:** test readiness, prepare only: X0c audit (R-2); reference-window lock prepared (`locked_utc`, `lock_sha256`) for the Architect; pass/fail table; full suite twice; next D; STOP | T-28f | readiness table; next D opened | S |
| [x] | G-D63 | **STOP — Owner and Architect review the v2 freeze and test readiness (D-63):** window-lock definition (AR-71 item 11), CR-038, CR-039, AR-71; go-ahead for the reporting-camera run (D-61 §1.7 order 1). Nothing on the reporting cameras or test until decided | T-28t | D-63 decided | — |
| [x] | T-29r | **D-63 STEPS 0–1 (Owner, 26 Nov 2026):** state check; D-63 DECIDED (§1 verbatim); CR-038 DECIDED (b, deferred), CR-039 DEFERRED, AR-71 ACCEPTED; T25.2 inert and T_s grid-edge limitations in the Progress log and `research/v2/reporting_plan.md` | G-D63 | records pushed | S |
| [x] | T-29a | **D-63 STEP 2:** rationale addendum `docs/preregistration/v2_rationale_addendum_D63.md` (§3 verbatim) and `v2_addendum_record.json` (SHA-256, commit time, before any reporting or test S3 output). Frozen files unchanged | T-29r | addendum and record pushed | S |
| [x] | T-29l | **D-63 STEP 3:** window lock (AR-71 item 11) on every window of V0 `m1a-sdg-test`, as a new lock artifact referencing V0 (V0 not rewritten); built twice, identical | T-29a | lock artifact; lock record | S |
| [x] | T-29q | **D-63 STEP 4:** D-62 equivalence (C1–C3, D-60 STEP 4 c, not loosened); D-62 DECIDED pass/fail; on pass the Colab job `reporting_test` (110 + 471 videos, manifest, HOWTO with upload size, Drive space, runtime, tier-1 skip note); STOP (next D) | T-29l | job pushed; D opened | S |
| [x] | G-D64 | **STOP — the Owner runs the Colab job `reporting_test` (D-64), or chooses option (a): the reporting run from the stored CPU S2, with Colab for test only** (decided 26 Nov 2026: option (a)) | T-29q | D-64 decided; outputs returned | — |
| [x] | T-29m | **D-64 (a):** test-only Colab job `test` (`research/colab/test_manifest.json`, 471 test cameras, the test set of `reporting_test` entry for entry), own staging folder, notebook accepts it, HOWTO section "D-64" | G-D64 | manifest pushed | S |
| [x] | T-29p | **D-63 STEP 5:** reporting run once (S3–S8, frozen v2), D-61 §1.6 tables, `research/v2/reporting_results.json` / `reporting_report.md`; full suite twice | G-D64 (stored CPU S2 of the 110 reporting cameras, D-64 a) | report pushed | M |
| [x] | T-29h | **D-63 STEP 6:** test S2 arrival: hashes verified against the Colab manifest (`test_manifest.json`, D-64) and recorded; outputs not opened | T-29m; Owner returns test S2 | hashes recorded | S |
| [x] | T-29t | **D-63 STEP 7:** test run once (S3–S8, frozen v2), same tables, `research/v2/test_results.json` / `test_report.md`; STOP (next D) | T-29l, T-29p, T-29h, R-2 | report pushed; D opened | M |
| [x] | T-29u | **D-66 diagnostic (post hoc):** IE events on A and C, 116 tuning cameras: which rule input was undetermined (M, R4, R5, contact cue, coverage); `research/v2/ie_inputs_diag_tune.json`; selects nothing, no test data | D-66 | result pushed | S |
| [x] | T-29w | **D-66 write-up claims:** `research/v2/writeup_v2.md` from the test values (three failed criteria, false alerts per hour), scope statements as D-66 orders | D-66, T-29u | write-up pushed | S |

| ✓ | ID | Gate | Needs | Done when |
|---|---|---|---|---|
| [S] | G-FQ | **STOP before the first real-data task: frame-quality rules version.** The agent proposes a rules version (frozen, black, blur, exposure) for Architect review and Owner approval (AR-27 review). No real footage is decoded under `rv1` | Proposal in `DECISIONS_NEEDED.md` | Owner approves the rules version |

**Deferred tracks:** multi-camera linkage (M2), real-data collection and physical validation, and the FM-X1 annotation-efficiency experiment. Synthetic E2 measurement is scheduled in §3a.

---

## 3a. Milestone M1c — Measurement improvement and synthetic scientific evaluation

Active under D-67 and D-69. See the [measurement plan](docs/plan/Measurement_Improvement_and_Scientific_Validation_Plan.md) for exit evidence, resource estimates and priorities. E1 and E2 design and reference qualification start in parallel. Execute each experiment only after its integrity and data dependencies pass. D-66 is terminal for the original final test and supersedes old pre-approvals to process or upload it. Real-world work is deferred under D-67.

| Status | Task | Work and owner | Needs | Exit evidence |
|---|---|---|---|---|
| [x] | T-30 | Codex records approved scope, audit attribution, plan, work packages and change control. | D-67 | Plan, CRs, Appendix T26 and contribution register cross-checked. |
| [~] | T-31 | WP-21 integrity corrections and development allocation. Codex implemented the first corrections under D-69. Claude Code coordinates integration, independent review and the detailed allocation. | D-67 / D-69 / CR-043 | Six integrity checks documented, no closed-lineage opens, both environments verified, approved-only development manifests inspected for leakage. |
| [ ] | T-32 | WP-22 analytical references and paired component comparisons for both viewpoints. | Design may start now. Execution requires affected T-31 gates. | Reference fixture checks, accuracy and coverage tables, bounded comparison and reviewed architecture rationale. |
| [ ] | T-33 | WP-23 E1 and WP-24 E2 comparative prototypes in parallel. | Design may start now. T-31/T-32 evidence governs execution and selection. | Uncached E1/E2 vision outputs with truth inaccessible, independent E2 measurements, paired detector × geometry comparisons and model, tracker and rule evidence. |
| [ ] | T-34 | WP-25 blinded candidate construct review. | Protocol and reviewer feasibility, appropriate footage, relevant isolation gates. | Agreement and disagreement assessment or documented unassessed status. |
| [S] | T-35 | WP-26 academic evidence package and separate confirmatory gate. Continue academic reporting meanwhile. | CR-044 / D-68 for any final confirmatory access and run. | Report with tested claims, failures, supporting comparison record, reproducibility instructions and real-world future work. |

## 4. Rules at a glance

- **Blocked by a contract question:** add an entry to `docs/CHANGE_REQUESTS.md`, mark the task `[B]`, and continue with the next task that does not depend on it.
- **Test fails against an Appendix N value:** fix the code. If you believe the document is wrong, open a CR and stop that task. **Never edit the expected value.**
- **Any STOP:** write it in `DECISIONS_NEEDED.md`, push, and stop dependent work.
- **Push:** at the end of every task and every session, and at every milestone (with a tag).

## 5. Milestone self-audit checklist

- [ ] Full suite passes from a clean clone with the locked environment.
- [ ] Two complete runs produce identical artifact IDs for exact-class stages.
- [ ] Every Appendix N expected value is asserted by at least one test, and none was edited after first commit (check with `git log -p` on the expected-value files).
- [ ] No fixture (TEST-ONLY) configuration appears in any research export or report.
- [ ] Reports use only the permitted wording and the three-status board.
- [ ] Open CRs and blockers are listed in the milestone report.
- [ ] No data files, videos or secrets are committed.

## 6. Templates

**Progress log entry** (append below, newest last):

```
### <date> — <task-id> <status>
- Did: …
- Tests: <passed>/<total> (full suite), determinism re-run: identical | differs (explain)
- Commit: <hash> (pushed)
- Problems / CRs: …
- Next: <task-id>
```

**Decision request** (`DECISIONS_NEEDED.md`):

```
## D-<n> (<date>) — <title>        status: OPEN
Task: <task-id>   Blocking: <task-ids>
Question: …
Options: (a) … (b) …   Agent's recommendation: …
Owner decision: ______
```

**Milestone report** (`reports/<milestone>_report.md`):
- Contract version.
- Tasks completed and blocked.
- Test matrix with counts.
- Artifact-ID table and determinism result.
- Status board: Implemented / Verified / Empirically validated (scope).
- Open CRs.
- Usage and time notes.
- Decisions needed.

## 7. Kickoff prompt (the Owner pastes this into the first session)

> Read CLAUDE.md and WORKPLAN.md, then the contract documents they list. Start at the first open task in WORKPLAN.md and follow the work loop. Log progress in WORKPLAN.md, commit and push after every task, and stop at any STOP or when the Owner's approval is needed.

**Kickoff prompt for later sessions:**

> Continue the RQ1 implementation: read CLAUDE.md, check the Progress log and DECISIONS_NEEDED.md, then resume the next open task in WORKPLAN.md.

---

## Progress log

_(the agent appends entries here)_

### 2026-11-09 — S-01 done
- Did: Checked wheels on CPython 3.15.2 and 3.14.3 (all present). Created `.venv` on 3.15.2 under the §0 approval. Recorded versions in `docs/ENVIRONMENT.md`. Lock reinstalled identically in a clean environment.
- Tests: no suite yet; imports and smoke calls passed for all nine packages
- Commit: af2e6fc (pushed, branch `m0-implementation`)
- Problems / CRs: `docs/`, `WORKPLAN.md` and `CLAUDE.md` are git-ignored and the repository is public, so these records stay local (D-2).
- Next: S-02

### 2026-11-09 — S-02 done
- Did: Package layout, pytest configuration, data paths ignored, `DECISIONS_NEEDED.md`, `docs/CHANGE_REQUESTS.md`.
- Tests: 0/0 (pytest runs, nothing collected), determinism re-run: not applicable
- Commit: 3a5666d (pushed)
- Problems / CRs: none
- Next: T-01

### 2026-11-09 — T-01 BLOCKED (part A pushed)
- Did: Part A only. One schema source for 64 tables with Arrow and JSON Schema generators, JCS wrapper, error registry, and the 7 VR rules with enforceable text, each with a passing and a failing fixture. Coverage report in `reports/T-01_vr_coverage.md`.
- Not done: 26 VR rules and CT-E-01, 05, 30 have no text in the normative documents, so "Done when" cannot be met. VR-E-040 is deferred to T-15.
- Tests: 318/318 (full suite), determinism re-run: identical (318/318; coverage report byte-identical)
- Commit: b96a882 (pushed)
- Problems / CRs: CR-001 (blocking; D-1), CR-002 (schema gaps, provisional handling marked in code).
- Next: T-07, the only task independent of T-01. T-02 onward wait for D-1.

### 2026-11-09 — T-07 done
- Did: Reviewed public dataset cards and repository metadata only; no dataset files downloaded. Report in `research/e2/E2_feasibility_report.md`. No reviewed dataset documents a worker and an elevated load in one scene with a height reference; E2-W3 needs collection.
- Tests: 318/318 (full suite), determinism re-run: identical (318/318)
- Commit: db58389 (pushed)
- Problems / CRs: D-3 raised: the SDG shard size means the §0 "~1.5 GB" estimate is too small. SmartSpaces has two real-world scenes that must be excluded.
- Next: STOP for now. All remaining M0 tasks depend on T-01, which waits for D-1 (CR-001).

### 2026-11-09 — Owner decisions recorded
- D-1 resolved by Appendix T (contract E-1.2.3); CR-001 closed. D-3 approved (22 GB cap, §0 row updated). D-2 stays open: `.gitignore` and repository visibility unchanged. Agent authority section added to CLAUDE.md.

### 2026-11-09 — T-01 done
- Did: All 33 active VR rules with one passing and one failing fixture; Parquet read/write; CT-E-01, 05, 30. CT-E-05 is at record level and is re-checked on FX-07 in T-08. VR-E-040's zero-exposure clause is enforced in T-15. Part A expectations for VR-E-070 and the coverage listing were changed because Appendix T amended the rule text.
- Tests: 488/488 (full suite), determinism re-run: identical (488/488; coverage report byte-identical)
- Commit: ecb0985 (pushed)
- Problems / CRs: CR-002 closed by AR-1 to AR-10; AR-11 to AR-15 are new. AR-7 flagged for Architect attention.
- Next: T-02

### 2026-11-09 — T-02 done
- Did: ID classes, ART-ISO, ANC-1, seven-step builder, reconstruction check, lineage trace. Reproduces `art_pmpcesnhpbbgtw2f3fhb6zkqxk` and every Appendix T T5 record ID.
- Tests: 529/529 (full suite), determinism re-run: identical (529/529)
- Commit: b36e61b (pushed)
- Problems / CRs: AR-16, AR-17. CT-I-03, 04, 07, 08 are builder-level until the stages exist.
- Next: T-03

### 2026-11-10 — T-01/T-02 completeness audit
- Did: Checked every Owner decision of 9 Nov against the files: all recorded correctly. Found and fixed: execution.json not matching its schema; no failed-run record; integers above 2^53 crashing the serializer (AR-18); CT-E-01 not applying VR-E-004 to produced artifacts; AR-2, AR-5, AR-6 lacking exact pinning tests.
- Still partial, by design: VR-E-021 checks unit suffixes only (AR-13); VR-E-040 zero-exposure clause waits for T-15; CT-E-05 is record-level until FX-07 runs in T-08; CT-I-03/04/07/08 are builder-level until T-08, T-09, T-14, T-16 (AR-17).
- Commit: 34b1f60 (pushed)
- Next: T-03

### 2026-11-10 — T-03 done
- Did: 46 record fixtures (N1, N2, FX-TIE, FX-W, FX-CM, FX-ID, FX-RC, FX-A3.1, FX-B/C/D, FX-A3/A4, FX-11, FX-12, TEST-ONLY parameters), each citing its source; manifest with hashes; generator refuses inconsistent labels, K and arithmetic.
- Tests: 627/627 (full suite), determinism re-run: identical (generator output byte-compared to committed files)
- Commit: f9994ac (pushed)
- Problems / CRs: AR-19, AR-20. Expected-value files must not change after this commit.
- Next: T-04

### 2026-11-10 — T-04 done
- Did: 14 PyAV-generated clips (FX-CLIP-A–D, VFR, B-frame, duplicate-PTS, dropout, corrupt-packet, two-file, untimed, FX-10), byte-deterministic for this decoder build; `fixtures/clips_manifest.json`.
- Tests: 643/643 (full suite), determinism re-run: identical
- Commit: b404438 (pushed)
- Problems / CRs: AR-21 (timestamp faults are applied by an overlay at demux, because containers repair missing timestamps).
- Next: T-05

### 2026-11-10 — T-05 done
- Did: Registrar with anchor IDs, local and aligned timelines, clock alignments, tiered calibration checks (CB-01, CB-02), CB-03, TI-11, ANC-1 across registrations.
- Tests: 673/673 (full suite), determinism re-run: identical
- Commit: 168811f (pushed)
- Problems / CRs: AR-22, AR-23.
- Next: T-06 is blocked.

### 2026-11-10 — T-06 BLOCKED
- Why: CR-003 and D-4. delta_nom has no definition, and the only earlier wording contradicts Appendix N3 for Cases B and C. f_sub has no stated effect. Both change measured durations or coverage, so they are outside the agent's authority.
- Note for T-06: PyAV exposes only `pts` and `dts` on frames, not FFmpeg's best-effort timestamp. Handle this under an AR when T-06 starts.
- Carry forward: CT-E-05 re-run on FX-07 in T-08; CT-I-03/04/07/08 at pipeline level (AR-17); VR-E-040 export clause in T-15.
- Next: Waiting for D-4. No M0 task is independent of T-06; T-10 needs T-06 and T-11 onward depend on it.

### 2026-11-11 — Owner decisions recorded
- D-2 decided: docs/, WORKPLAN.md and CLAUDE.md are tracked (commits 9ae27b4 and 8bc287d; the first missed two files because a scripted .gitignore edit failed, and the second completes it).
- D-4 approved as contract E-1.2.4: Appendix T section T7 appended verbatim, CR-003 closed, CLAUDE.md contract version updated. T-06 resumed.

### 2026-11-11 — T-06 done
- Did: Timestamp resolution, reorder depth, eligibility, δ_nom per T7 (declared, then adjacent-pair median, then all-timed median), support with capping, exclusion and uncertainty regions, f_sub degradation, coverage tiling per (timeline, camera), S1 artifact. FX-CLIP-A–D reproduce 0.100/0.067/0.033/0.133 s; CT-T-22 gives 0.034 s and 0.068 s.
- Tests: 702/702 (full suite), determinism re-run: identical (S1 artifact IDs equal across runs)
- Commit: 75b0705 (pushed)
- Problems / CRs: AR-24 to AR-28. The AR-5 pinning test was updated because E-1.2.4 adds decode_config fields. Note: with the T7 fixture δ_nom of exactly 0.033 s, δ_max is 0.0495 s (Package F §3 quotes 50 ms), so the 50 ms intervals of the CT-T-01 VFR clip are capped with 17 ms gaps.
- Not yet done here: duration assertions of CT-T-14–19 and CT-T-20 (c, d) belong to T-08.
- Next: T-08 (needs T-06, now done). T-10 also needs T-05 and T-06, both done.

### 2026-11-11 — Architect review of AR-7 and AR-22 applied
- AR-22 accepted; its note is recorded and added to the T-20 row.
- AR-7 revised and applied: event-time columns (`frozen_utc` ×3, `locked_utc`) are stored but outside every hash; the `*_utc` format is exactly YYYY-MM-DDTHH:MM:SS.ffffffZ; VR-E-054 reads stored event times. SP-01, SP-08 and FT-02 must do the same when written (T-10, T-14).
- One requested test conflicts with F.1 A1.2 (anchor IDs come from the natural key only), so it was implemented to F.1 and raised as CR-004 / D-5.
- Tests: 718/718 (full suite), determinism re-run: identical
- T-06 was already complete (7bc0036) under E-1.2.4 and still passes. Next: T-08.

### 2026-11-11 — Architect review of the T-06 Agent Resolutions applied (contract E-1.2.5)
- AR-28 and AR-25 accepted; AR-27 acknowledged (STOP G-FQ added before the first real-data task); VFR fixture kept, with the 17 ms gaps asserted. Appendix T T7.1 appended verbatim; CLAUDE.md reads E-1.2.5.
- Code: `decode_seq` is demux order; δ_nom step 2 is the presentation-order pair median excluding pairs that overlap an uncertainty region. T7.1 check values pass (A 0.033 s, B 0.034 s, C falls back to step 3).
- `test_ct_t_21_declared_source_recorded` now expects a stored pair median of 0.033 s for Case A instead of 0.034 s. The old figure was the agent's derivation under the replaced T7 step 2, not an Appendix value; the new one is the T7.1 check value.
- T-17 and T-20 rows extended with the review's reporting and pre-registration items.
- Tests: 723/723 (full suite), determinism re-run: identical
- Next: T-08, then T-10.

### 2026-11-11 — T-08 BLOCKED (part A in progress)
- Why: CR-005 / D-6. Seven substrate quantities have no computable definition (POW gap bridging, speed/heading smoothing, closing rate/TTCA, clearance σ, signed image box gap, Q, evidence_state). `pair_series` rows cannot be written without items 5 and 6, which are non-nullable.
- Part A (defined parts) proceeds now; T-10 is independent of T-08 and follows.
- Part A done (dddd25d, pushed): oracle S3 source with evidence classes, support-based durations by class (CT-T-14–17 durations, CT-T-20 c/d, EC-01), activity segments (CD-01–03, FX-D1/D2, CT-E-11 store part), signed footprint distance and constant-velocity prediction (N2 clearances and predicted minima, CT-E-06). AR-29, AR-30.
- Tests: 742/742 (full suite), determinism re-run: identical
- Remaining for part B after D-6: POW construction with bridging (CT-T-18, CT-F-01), speed and motion split, pair_series and exposure_profile rows (CT-E-07, CT-E-08, CT-T-19), N2 M flag, S4 artifact, CT-E-05 on FX-07, CT-I-03/04 at pipeline level.
- Next: T-10.

### 2026-11-11 — T-10 done
- Did: Metadata leakage edges and groups, split freeze with declared partitions, X0c audit, PR-01 revision, R-3 affected strata and result invalidation, R-2 gate (SP-08 reads `frozen_utc`), SP-01 (Validation-store inputs and event times), window tiling, seeded stratified RES draw, ECS windows, plan and window rows, Horvitz–Thompson ratio with stratified window bootstrap (D1-AC-09 coverage simulation).
- Tests: 764/764 (full suite), determinism re-run: identical
- Commit: 9fccccf (pushed)
- Problems / CRs: AR-31 to AR-34. CR-006 / D-7 open: a timeline extent that is not a multiple of w_ref is refused (ERR-SPEC) until the final-window rule is decided. This does not affect M0 fixtures, but blocks sampling of the 10 s SDG runs in M1a.
- Not here: SP-05 (reports, T-15); SP-06 is covered by CT-S-05/06.
- Next: T-08 part B waits for D-6. T-11 needs T-02 and T-10, both done, so T-11 is next.

### 2026-11-12 — Owner decisions D-5, D-6, D-7 and Architect review recorded (contract E-1.2.6)
- D-5 (a): F.1 A1.2 kept; CR-004 closed. D-6 (b): Appendix T section T8 appended verbatim, CR-005 closed as superseded by T8, CLAUDE.md reads E-1.2.6. D-7 (b): shorter last window; CR-006 closed; w_ref item added to the T-20 checklist.
- AR-30, AR-31 accepted; AR-34 accepted with change.
- Note: T8 adds v_part to the §14 parameter list by its own text; the frozen E-1.2.1 file is not edited. Its TEST-ONLY value (0.5) goes into the TEST-ONLY parameters fixture.
- T-08 resumed.
- Follow-up to finished work (T-10, T-03): D-7 applied (shorter last window, `window_length_s` on `reference_window`, guard clipped; the CR-006 rejection test is replaced by the D-7 tests). AR-34 change applied (`edges_added` records every discovered edge; `revise` takes recordings' metadata to apply the same exclusion; the SP-07 test lists that parameter). D-5 citation added to `test_supplied_retrieved_utc_is_hashed`. `v_part = 0.5` added to the TEST-ONLY parameters fixture; no existing fixture value changed. Tests: 766/766 twice.

### 2026-11-12 — T-08 done (contract E-1.2.6)
- Did: T8.1 POW bridging and splitting (bridged gaps, gap_exceeded, coverage_gap, track and recording ends, continuation links; TI-08); T8.2 least-squares kinematics, heading, yaw fill and circumscribed-disc fallback; T8.3 closing rate and TTCA; T8.4 clearance σ; T8.5 signed image box gap; T8.6 evidence state; T8.7 Q; ground-plane and full-camera floor positions; pair series, exposure profiles, activity segments; S4 artifact.
- Tests: 802/802 (full suite), determinism re-run: identical (S4 artifact ID equal across builds)
- Commit: c85ff84 (pushed)
- Contract tests now covered: CT-T-18, CT-T-19, CT-F-01, CT-E-05 (FX-07), CT-E-06 to 08, CT-I-03 and CT-I-04 at pipeline level, N2 clearances and predicted minima through S4, every T8 check value.
- Note on the T8.3 check: inside S4, frame 0 of G3 has no T8.2 velocity (half-window span 0.2 s < 0.25 s), so no prediction exists at t = 0. The check is tested with the exact G3 velocity, and at frame 1, where S4 also gives the minimum at τ (ttca not_observable).
- Problems / CRs: AR-35 (schema nullability and labels for T8). CR-007 / D-8 open: footprint anchor on the camera-based path; M0 unaffected.
- Not here: the N2 flags P, M and C_by_R3 belong to S5 (T-09) and will be tested there from these substrate values.
- Next: T-11, then T-09.

### 2026-11-12 — T-11 done
- Did: Append-only status log with SHA-256 hash chain and verification; namespace and blindness guards (ERR-NAMESPACE); RV-02 check; RC-01 to RC-05 checks; SimReferenceConverter producing timeline-form `ref_coverage_label`, `ref_object_presence`, `ref_geometry` and `ref_interaction` with A5.1 reference classes.
- Tests: 857/857 (full suite), determinism re-run: identical
- Commit: 9b9b1d5 (pushed)
- Problems / CRs: AR-36.
- Next: T-09.

### 2026-11-12 — T-09 BLOCKED (part A done)
- Why: CR-008 / D-9. Eight event-engine inputs are undefined (R5 rates, contact-cue units, E when R5 is off, closest-approach frame, "usable frames around CA", unknown-T runs in the lifecycle, onset_sensitive). Appendix N2's per-frame M and C_by_R3 conflict with T8.2 at the first and last frame; for G3 this also changes the episode to [1, 9) with minclr 2.50 m.
- Part A done (9850a53, pushed): Kleene logic; providers R1, R2, R3, G, Q; lifecycle with m_gap, t_min, w_post; episode quantities; K; contact state; labels, IE, review routing; N1 T1–T13 exact at flag level; CL-INV property test (CT-E-10); CT-E-12 (substrate unchanged), CT-E-13 (R3 plus stub R4), CT-E-14 (early trigger); N2 interior-frame flags. AR-37.
- Tests: 1180/1180 (full suite), determinism re-run: identical
- Part B after D-9: R5 and contact cue from kinematics, CA frame, S5 artifact (flag_series, episode, discarded_episode, candidate_event, event_count_summary), episode exposure fields, N2 episodes end to end.
- Next: no M0 task is independent of T-09 (T-12 needs T-09 and T-11). Waiting for D-9.

### 2026-11-12 — Owner decisions D-8 and D-9 recorded (contract E-1.2.7)
- D-8 deferred to T-22: reopen with GV-03/GV-04 evidence. Until then, the oracle and simulator path uses the simulator footprint centre. CR-007 marked deferred.
- D-9 decided: Appendix T section T9 appended verbatim, CLAUDE.md reads E-1.2.7, CR-008 closed as superseded by T9.
- T9.9: the N1 T10 inputs were changed in the fixture generator (Q = 1×12, 0×8; clearance on frames 0–11). Expected values are unchanged and the fixture source cites T9.9. A `clearance_frames` input now records N1's measured frames for every row. `k_c_turn = 3.0` was added to the TEST-ONLY parameters fixture and to the Package F §3 table. As with v_part, T9.3 adds k_c_turn to the §14 parameter list by its own text, and the frozen E-1.2.1 file is not edited.
- Commit: 82341cb (pushed)

### 2026-11-12 — T-09 BLOCKED (part B done except the S5 artifact)
- Did: T9.1 shifted velocity window in S4. T9.2 R5 rates and E. T9.3 contact cue with k_c_turn. T9.4 R5 disabled. T9.5 CA with `ca_observed`. T9.6 W_CA and contact order. T9.7 lifecycle with unknown runs. T9.8 onset_sensitive and §6.0 borderline frames. Episode durations over I and `exp_evasive_score`. flag_series rows. Single-camera candidate events (S_VIEW = S_LINK = S_POSS) and `label = all` count summaries. N2 G1–G3 run end to end through S4 and S5 with N2's expected episodes, labels, minclr and the G1 detected duration of 5.000 s. Every T9 check is a test.
- Tests changed because T9 amends the contract (each cites T9): the T-08 tests that expected null velocity at track ends, the G3 episode [1, 9) with 2.50 m (now N2's [0, 10) with 2.35 m), interior-only N2 flag checks (now every frame), and `t_motion_unknown_s` 0.2 → 0.0. The old values were the agent's own derivations under T8.2, not Appendix values.
- Tests: 1420/1420 (full suite), determinism re-run: identical (1420/1420; regenerated fixtures byte-identical)
- Problems / CRs: AR-38. CR-009 / D-10: four T9 edge readings are implemented provisionally. The episode exposure fields, `support_detected_frac` and per-label counts are undefined, and they block the S5 artifact.
- Remaining after D-10: S5 artifact assembly (episode rows with exposure fields, keys and context), per-label counts, and S5 artifact-ID determinism.
- Commit: 29ac44a (pushed)
- Next: T-12. It needs T-09, but none of the blocked items (matching uses event intervals, pair identity and label groups).

### 2026-11-12 — T-12 done
- Did: A5.2 frame-level association (same-class IoU, quantized weights, sorted inputs, ε_amb ambiguity), track summaries (dominant identity, share, switches, one_to_one / id_switch / fragment / unmatched_system), missed identities, matched support, and event-pair resolution (CA frame, then dominant identity, else unknown). N4 matching with the composite tie weight, pair and label-group conditions, and all six match classes. EV-M1, M2, M3, M4, M5, M6, M7, M8 and M11.
- Contract tests: CT-ID-A1 (FX-ID-1–8; FX-ID-8's attribution stage belongs to T-14), CT-ID-A2 (permutations), FX-TIE (s1 → r1, r2 miss), CT-E-20, CT-E-21. FX-W reproduced through EV-M1 (0.71875 weighted, 0.70 unweighted).
- Tests: 1499/1499 (full suite), determinism re-run: identical (1499/1499)
- Commit: 293af60 (pushed)
- Problems / CRs: AR-39. CR-010 / D-11: four readings in the event metrics are implemented provisionally. None of them is in T-12's "Done when".
- Not here: EV-M9, EV-M10 and EV-M12 need A-layer and expert inputs (T-14), and so does CM-01 (T-14). The S8 artifact is assembled in T-14/T-16.
- Next: T-13 (needs T-12, done).

### 2026-11-12 — Owner decisions D-10 and D-11 recorded (contract E-1.2.8)
- D-10 and D-11 decided: Appendix T section T10 appended verbatim, CLAUDE.md reads E-1.2.8, CR-009 and CR-010 closed as superseded by T10. E-1.2.1 and Appendix N not edited; T10 adds no parameters.
- Architect rulings recorded under AR-35 to AR-39. Follow-ups carried: AR-35 item 7 and AR-36 item 4 at T-17/T-18; AR-39 item 6 CR at T-14 (EV-M10).

### 2026-11-12 — T-09 done (contract E-1.2.8)
- Code changed to conform to T10:
  - T10.3(a) closing rate uses the T9.1 shifted window inside the POW, with ≥ 3 measured frames spanning ≥ w_v/2, on every pair frame; an exact zero is stored as +0.0.
  - T10.3(b) E is unknown on insufficient pair frames when R5 is enabled.
  - T10.3(c) R5 rates are computed whether or not R5 is enabled, so the cue no longer depends on R5.
  - T10.1 a null clearance at CA gives undetermined.
  - T10.4 borderline flags over I, with the minclr and CA bullets; the T9.8 onset test now uses the frame's P/M/enabled-C borderline, kept separate from the T10.4 frame bullets.
  - T10.5 exposure fields over I; `exp_evasive_score` over I⁺ with the T10.5 null reasons.
  - T10.6 counts by `lbl_` flags for all, O, H, PC, NM, UD, CT and IE, zero rows included.
  - T10.7(a) abstention only in G2; T10.7(c) P90 and median by numpy "linear", with n; T10.7(d) EV-M3 weighted, by window.
  - T10.9 `person_lost` / `forklift_lost` in q_reasons.
  - Architect ruling on AR-39 item 3: the matcher takes the label-group mapping as an input.
- S5 artifact: flag_series, episode, discarded_episode, candidate_event, event_count_summary. Rule-configuration record and ID. Episode continuation links.
- Contract tests: CT-T10-01 to CT-T10-10, CT-FK-02, CT-FK-04 and CT-I-07 for S5, and the T10.5 consistency sum on five scenarios. S5 artifact IDs are identical across two processes (G1 art_z47m7gvrzibivwi4f4dxlifahn, G2 art_a4p2grbbt7st5n3eol3yjxibl6, G3 art_vrne63gxuixh7mptkpc7eukyjv).
- Tests changed because T10 amends a rule (each cites T10): onset_sensitive (T10.4 over I); count summaries (T10.6: eight labels, overlapping); EV-M3 (T10.7(a,d)).
- Tests: 1558/1558 (full suite), determinism re-run: identical (1558/1558)
- Problems / CRs: AR-40. CR-011 / D-12 (non-blocking): T10.4 bullets that read parameters of providers that are not enabled.
- Commit: d56e5e5 (pushed)
- Next: T-13.

### 2026-11-12 — T-13 done
- Did: N5 estimators. HT total, ratio and Kish (from T-10) are now asserted on FX-W. Added: Target B cluster bootstrap (leakage groups within data origin, weights carried, seeded PCG64), paired bootstrap difference, Wilson (z = 1.959964), Bland–Altman (n − 1 SD), ICC(2,1) (Shrout & Fleiss), Cohen's κ, Krippendorff's α (nominal).
- Done when: FX-W gives 0.71875 weighted, 0.70 unweighted and n_eff 3.3793103448. Also: Wilson 8/10, Bland–Altman, ICC(2,1) on the Shrout & Fleiss Table 2 data (0.29), κ and α by hand, and same-seed bootstrap identity.
- Tests: 1567/1567 (full suite), determinism re-run: identical (1567/1567)
- Commit: 2ef1c5d (pushed)
- Problems / CRs: AR-41. One recorded hand value (Wilson upper bound) was corrected from 0.943315 to 0.9433178 before the first commit; it was my own arithmetic slip, not an Appendix value, and the corrected arithmetic is written in the test.
- Next: T-14.

### 2026-11-12 — Owner decision D-12 recorded (contract E-1.2.9)
- D-12 decided: Appendix T section T11 appended verbatim, CLAUDE.md reads E-1.2.9, CR-011 closed as superseded by T11 (reading (b)). E-1.2.1 and Appendix N not edited.
- Architect rulings recorded under AR-40 and AR-41. Future ARs use one labelling scheme.
- Also committed here: the Owner's own edits to CLAUDE.md step 4 and the WORKPLAN §6 template (determinism subset, `pytest -m determinism`). The `determinism` marker is not yet defined or applied to any test.
- NOT YET DONE (session stopped at the usage limit): T11.1 code change with CT-T11-01/02; T11.2 paired bootstrap with CT-T11-03; Wilson re-derivation with `decimal`; the `determinism` pytest marker; T-14. The code still implements T10.4 literally (reading (a)), which T11.1 replaces.
- Next: STEP 2 of the D-12 prompt, then T-14.

### 2026-11-12 — Process: `determinism` marker (Owner process change, not a contract change)
- Did: registered `determinism` in pyproject.toml (strict markers on). Marked 331 of 416 test functions (1401 of 1570 collected tests): every test that builds, hashes or serializes an artifact, every fixture test, every seeded property test; when unsure, marked (Arrow serialization, schema generation, ID formats, key rounding, the VR coverage report, configuration-field pins, matcher tests that order by JCS). Guard `tests/test_determinism_guard.py`: a module importing the artifact builder or a stage that calls it, the ID library or the fixture package, reading `fixtures/records`, or importing a guarded test module's helpers, must mark every test or list it in EXCEPTIONS with a reason (69 pure-formula exceptions). The guard was probed with a temporary unmarked test and failed as intended.
- Modules with no marked test: tests/evaluation/test_t10_metrics.py (pure EV-M formulas; not guarded), tests/test_determinism_guard.py (static analysis).
- Timing: full suite 27.5 s wall clock; determinism subset 32.7 s. The subset gives no saving now, because almost all run time is in artifact-building and seeded tests.
- Tests: 1570/1570 (full suite once); determinism subset: 1401 tests, passed

### 2026-11-12 — T11.1 conformance (contract E-1.2.9)
- Did: the T10.4 frame bullets in `providers.flag_frames` now apply only under their T11.1 condition: d_p and v_min only with R2, k_img only with R1, d_pc only with R3. The minclr, CA, footprint and onset bullets are unchanged. CT-T11-01 (one case per bullet, provider enabled and disabled) and CT-T11-02 (four disabled-provider parameter sets on G2 and G3: identical S5 payload_sha256, different rule_configuration and artifact IDs).
- Tests changed because T11.1 amends T10.4 (each cites T11.1): test_ct_t10_06_clearance_against_d_p[R1] and test_ct_t10_06_speed_near_v_min[R1] now expect no flag. The R2 cases keep their hand values.
- Problems / CRs: CR-012 / D-13. v_min and w_e are read outside their provider, so CT-T11-02 tests only parameters owned by one provider alone.

### 2026-11-12 — T11.2 conformance (contract E-1.2.9)
- Did: `estimators.paired_bootstrap_difference` replaces the window-only paired bootstrap (AR-41 item 3, revised by T11.2). The scheme follows the estimand: frame_description resamples windows within strata (Target A), new_session_performance resamples leakage groups within data origin (Target B), and conditional_on_selection returns no interval. Both configurations share each replicate's units.
- CT-T11-03 on a hand-built two-group fixture: cluster interval (−1, 1), window interval (−2/3, 2/3), both derived by hand in the test; conditional metric gives none. The T-13 paired test was moved to the new interface; its expected values are unchanged.

### 2026-11-12 — Wilson 8/10 re-derivation (D-12 prompt, step 2)
- Did: `test_wilson` now derives the N5 Wilson bounds in Python `decimal` at 15 digits, independently of the estimator code, and records every intermediate value: low 0.490162469122133, high 0.943317849062234. The estimator must agree within 1e-12, tighter than the previous 1e-6.
- The earlier correction stands: the first recorded upper bound (0.943315, T-13) was the agent's arithmetic slip, corrected to 0.9433178 before the T-13 commit. The decimal derivation confirms the corrected value.

### 2026-11-12 — T11 conformance verified
- Tests: 1591/1591 (full suite once); determinism subset re-run: 1421 tests, identical (passed twice; S5 artifact IDs G1 art_z47m7gvrzibivwi4f4dxlifahn, G2 art_a4p2grbbt7st5n3eol3yjxibl6, G3 art_vrne63gxuixh7mptkpc7eukyjv in both runs, unchanged from before T11)
- Commits: 08e7bcb (marker), f02d046 (T11.1), 3c161e0 (T11.2), 63b2e0f (Wilson), all pushed
- Problems / CRs: CR-012 / D-13 open, non-blocking.
- Next: T-14.

### 2026-11-12 — T-14 in progress (part A: attribution, match-run digest)
- Did: CR-013 / D-14 (EV-M10 options; no new match class). CR-014 / D-15: N9 cites D.1 §7.2 for the oracle-factorial status rule, which CLAUDE.md forbids implementing from methodology; "tests conflict" is undefined. Implemented: N9 diagnostic rule tests in pipeline order (primary, secondary, unresolved), rules 1, 2 (miss and false alert), 3, 4, 5 and 7, the 2^3 oracle substitution runner (outcomes only), and the VR-E-061 check. FX-ID-8 is attributed to perception. The match-run inputs digest includes the label-group mapping.
- Waiting: CT-E-22 (verified_oracle_joint on FX-16) for D-15; EV-M10 for D-14.
- Problems / CRs: AR-42, CR-013, CR-014.

### 2026-11-12 — T-14 in progress (part B: completeness)
- Did: CM-01, CM-02 (with the moving restriction), CM-03, CM-04 and CM-09 on both support bases, per identity or pair; completeness_record rows. FX-CM gives CM-01 = 0.600 and CM-03 = 0.600; FX-ID-3 gives CM-01 = 0.9; CT-F-03 gives CM-09 = 0.5.
- Problems / CRs: AR-43. CR-015 / D-16: CM-05 to CM-08 and CM-10 are underdetermined (basis of system denominators, CM-06 unit, CM-07 defined two ways in F.1, CM-10 frames without a POW, aggregation).

### 2026-11-12 — T-14 BLOCKED (parts A to C done; CT-E-22 waits for D-15)
- Did (part C): scoped fitness engine. Criterion decisions by rule from stored results; section 9.6 status per scope; FT-02 reads acceptance_criterion.frozen_utc against the first test-partition evaluation time supplied from the execution record (never the clock); construct status CV0–CV2 with FT-05, FT-06 and RV-03; stored-status checks (FT-01, FT-03, FT-08); measurement_fitness rows with the fixed interpretation note.
- Contract tests now covered: FX-CM (CM-01 = CM-03 = 0.600), FX-ID-3 (CM-01 = 0.9), CT-F-03 to CT-F-10, CT-E-29, FX-ID-8 (perception). CT-ID-A3: RV-01, RV-02 (T-11) and RV-03 enforced; RV-04 is report wording (T-15).
- Why blocked: CT-E-22 (FX-16, verified_oracle_joint) needs the oracle-factorial status rule (CR-014 / D-15). Also open: CR-013 / D-14 (EV-M10), CR-015 / D-16 (CM-05 to CM-08, CM-10), CR-016 / D-17 (fitness gaps).
- Tests: 1620/1620 (full suite once); determinism subset re-run: 1429 tests, identical (passed twice)
- Problems / CRs: AR-44, CR-016.
- Next: T-15 needs T-14. Its export classes, banner and wording do not depend on D-14 to D-17; starting it under the blocked parent needs the Owner's word.

### 2026-11-12 — Process change (Owner decision): full-suite re-run restored
- CLAUDE.md work-loop step 4 and the WORKPLAN §6 template again say: run the full suite a second time; exact-class outputs must be identical. Reason: the determinism subset gave no saving (full suite 27.5 s, subset 32.7 s).
- Kept: the registered `determinism` marker and the marks on tests. Removed: the guard test `tests/test_determinism_guard.py` and its exception list.

### 2026-11-12 — Owner decisions D-13 to D-17 recorded (contract E-1.2.10)
- Appendix T section T12 appended verbatim; CLAUDE.md reads E-1.2.10; CR-012 to CR-016 closed as superseded by T12; D-13 to D-17 closed. E-1.2.1 and Appendix N not edited.
- Architect rulings recorded under AR-42 (evc record to be defined), AR-43 and AR-44 (flip_rate_le revised).

### 2026-11-12 — T12.1 conformance (contract E-1.2.10)
- Did: rule_configuration providers hold only exclusive parameters (R1 k_img, R2 d_p, R3 d_pc, R5 e_turn/e_acc/e_dec); w_e moves to the classification block (`w_e_s`); v_min and tau come from the substrate_config record, which S5Config now carries; S5 refuses a runtime v_min, tau or w_e that differs from its single source, and an S4 artifact built with another substrate_config (ERR-SPEC). CT-T12-01.
- Tests changed because T12.1 amends T11.1 (each cites T12.1): the CT-T11-02 R3 case now varies d_pc only (tau is substrate_config.prediction_horizon_s). S5 artifact IDs change, as T12.1 states (the rule_configuration and the test S4 configuration IDs change); payload values do not.
- Correction: commit 37be0c8 was pushed while the full suite failed at collection (`tests/events/test_t12.py` clashed with `tests/evaluation/test_t12.py`; test directories have no `__init__.py`). My command chain committed because `tail` succeeded. The module is renamed `test_t12_shared_parameters.py`; full suite 1623/1623. From now on I check the pytest exit status, not the tail line, before committing.

### 2026-11-12 — T12.2 conformance: EV-M10
- Did: `matching.unobservable_overlap` (events overlapping a not-assessable reference, matched to none, non-abstained or abstained per T10.7(a)); `event_metrics.ev_m10` (by decision and by label, RES-weighted and unweighted, with the T12.2 interpretation note); `sensitivity_excluding_unobservable_overlap` for EV-M2 and EV-M7. N4 classes unchanged; headline EV-M2 and EV-M7 unchanged. CT-T12-02 reproduces the T12.2 check (EV-M2 1/3, sensitivity 1/2, EV-M10 1 + 1).

### 2026-11-12 — T12.3 conformance: oracle-factorial attribution
- Did: `attribution.oracle_attribution` (T12.3 steps 1–5: evidence_unavailable first, minimal resolving sets, primary = earliest stage of the smallest sets, single or joint, oracle run IDs of M, rule-test results always stored, disagreement and non-monotone sets reported); `prerequisites` makes rules 4 and 5 not_evaluated when rule 3 (rule 4) fails. CT-E-22 (FX-16: perception, [geometry], verified_oracle_joint) and CT-T12-03 pass.

### 2026-11-12 — T12.4 conformance: completeness
- Did: reference pairs derived from co-visible frames; POW-frame attribution to pairs; CM-05 (ambiguous support reported separately), CM-06 (per-pair sum of band differences, descriptive Bland–Altman over (pair, band) units, null not_supplied without reference geometry), CM-07 (POWs per co-presence interval, 0/1/2+ summary, pair-window fidelity), CM-08 (per calibration tier), CM-10 (dominant-pair POWs), pooled ratio of sums with unweighted alongside; `visibility_assumed` flag for reports. CT-T12-04 on fixtures extending FX-CM and FX-ID-3; FX-CM and FX-ID-3 values unchanged.
- Problems / CRs: CR-017 / D-18 (CM-10 basis; reading (a) implemented, non-blocking).

### 2026-11-12 — T-14 done (contract E-1.2.10)
- Did (T12.5 and rulings): residual status experimental; failing_interval from the first not_met of any type; real_staged counts as real data, scoped by data_origin; comparability characterized = a registered comparability criterion with a decision. AR-44 item 2 as revised: without an interval a criterion is not_assessable, except exact_equal and the full-enumeration metrics MR-01, MR-08, MR-09, MR-12 ([v, v]). `evaluation_config` record (prefix evc) with label_group_mapping_sha256 (AR-42 ruling); a changed mapping changes the evc ID and the S8 specification. CT-T12-05.
- T-14 "Done when": FX-CM CM-01 = 0.600; FX-ID-3 CM-01 = 0.9; CT-E-22 (FX-16 verified_oracle_joint); CT-E-29; CT-F-03 to CT-F-10; CT-ID-A3 (RV-01, RV-02, RV-03 here; RV-04 report wording in T-15).
- Tests changed because T12 or a ruling amends a rule (each cites it): the flip_rate_le case (AR-44 item 2 as revised), the residual-status test (T12.5, replacing the refusal), the CT-T11-02 R3 case (T12.1), the registered table set (evaluation_config, AR-42 ruling).
- Tests: 1651/1651 (full suite), determinism re-run: identical (1651/1651; S5 artifact IDs G1 art_jzci6rz3ipltxf3uhbpz2bzg7j, G2 art_dminksfz6xnn522tniwk4aj732, G3 art_hxo7uxntshvq2l23y223pger6f in both runs; they differ from the pre-T12 IDs because the rule_configuration changed (T12.1) and the test S4 now uses the real substrate_config ID)
- Problems / CRs: AR-45. CR-017 / D-18 (CM-10 basis), non-blocking.
- Next: T-15.

### 2026-11-12 — T-15 in progress (part A: OBX export)
- Did: `export/obx.py`. Export-class guard EXP-1 to EXP-3 (ERR-EXPORT-CLASS both ways; preregistration_ref for test-partition metrics); one serializer for both classes (JCS files with metadata, sorted rows, data dictionary = JSON Schema per table, manifest with SHA-256 per file); shared validators (schema, forbidden names and values, VR-E-034, VR-E-040 including the zero-exposure clause carried from T-01); fixture exports written under `fixture/`. Episodes carry continuation_of_nk into OBX (AR-40 item 4 ruling). Lineage check for CT-E-28.
- Contract tests: CT-X-01, CT-X-02, CT-X-03, CT-X-05, CT-E-26 (FX-12 E2 records), CT-E-27 (content scan), VR-E-040.

### 2026-11-12 — T-15 done
- Did (part B): `export/report.py`. Fixture and research templates (EXP-4 banner; mixed templates refused), wording linter (W1–W6, RV-04), Implementation-conformance section with RV-02 check and fixed caveat, candidate-event counts as scenario_count (never physical interactions; continuation chains named), EV-M10 section with the sensitivity label and note beside the headline values, completeness section printing "reference visibility assumed", three-status board.
- Contract tests: CT-X-01 to CT-X-05, CT-E-26, CT-E-27, CT-E-28 (export level), VR-E-040 (both clauses), LK-07 wording.
- Tests: 1684/1684 (full suite), determinism re-run: identical (1684/1684)
- Problems / CRs: AR-46.
- Next: T-16 (M0 integration and self-audit).

### 2026-11-12 — Process rule (Owner decision, no contract change)
- CLAUDE.md work loop step 7 added: never commit or push in a command chain that does not stop on a failed test run; use `pytest ... && git commit ... && git push` or check the exit status; a push with a failing suite is recorded in the Progress log (as was done for 37be0c8).

### 2026-11-12 — Owner decision D-18 recorded (contract E-1.2.11)
- Appendix T section T13 appended verbatim; CLAUDE.md reads E-1.2.11; D-18 and CR-017 closed. Architect rulings recorded under AR-45 (CM-06/CM-07 labels) and AR-46 (linter pass cases; zero-exposure check extended to not_evaluated).

### 2026-11-12 — T13 conformance
- Did: CM-10 stored once with support_basis = detected as a placeholder (`cm10_records`); reports print "basis-independent" (T13.1), CT-T13-01. CM-06 and CM-07 printed as "sum (s)" and "count" (T13.3; AR-45 item 3 ruling). Linter pass cases added; W2 now also allows "no near miss(es)" so that the required pass string "no near misses were observed" passes (AR-46 item 4 ruling). VR-E-040 zero-exposure check extended to not_evaluated (CD-03), with a failing and a passing test for each state (AR-46 item 7 ruling). T13.2 needed no code change: v_min and tau already come from substrate_config (T12.1 tests).

### 2026-11-12 — T-16 in progress: M0 fixture pipeline
- Did: `rq1.pipeline.m0` runs clips → S0 → S1 → oracle S3 → S4 → S5 → X0b → V0 → CV-SIM → X0c → S8 (with evaluation_config) → S8f → S4-E2 (FX-12 records) → S9 (fixture export and report) on a new 50-frame, 10 fps clip `fx_m0_pipeline` (clip manifest gained one entry; no existing clip changed). It reproduces Appendix N2 G2 end to end (one episode [0, 50), H, minclr 1.10 m, 5.0 s detected, matched to its reference); CT-E-26 and CT-E-28 end to end; two runs in separate processes give identical artifact IDs, payload hashes and export file hashes. CV-SIM converter gained `label_group_mapping` (AR-39 item 3 ruling).
- A scene defect found on the first run: the oracle boxes lay outside the 64 × 64 px clip, so they were `truncated` and the episode was IE. Boxes moved inside the frame; the engine was not changed.

### 2026-11-12 — T-16 done; STOP at G-M0
- Did: M0 fixture pipeline end to end; clean clone of commit e6072ef run with the locked environment: full suite twice (1704/1704 each, 27.3 s) and pipeline twice (12 artifact IDs, payload hashes and all export-file hashes identical). Suite also passes with sockets blocked: no test needs network or a downloaded dataset. Installed packages equal requirements.lock (pip aside); rq1 not installed, so the clone ran its own src. Expected-value audit with git history: no `expected` block changed after its first commit; every input or parameter change listed with its authority in reports/M0_report.md section 5. Self-audit §5 complete. reports/M0_report.md written from the §6 template (status board: everything implemented or verified, nothing empirically validated; 47 ARs, 27 pending review).
- Tests: 1704/1704 (full suite), determinism re-run: identical (1704/1704; pipeline artifact IDs identical across two clean-clone runs)
- Problems / CRs: AR-47. CR-007 deferred (D-8). No other open CR.
- Next: STOP. G-M0: the Owner reviews M0. Do not start M1a.

### 2026-11-12 — G-M0 passed (D-19)
- Owner decision: M0 ACCEPTED. The Architect accepted all 27 pending ARs as written (recorded under each AR); every AR from AR-1 to AR-47 is now reviewed. reports/M0_report.md updated: acceptance recorded, artifact-ID table tied to commit e6072ef.
- Conditions carried into M1a: (1) done in M0_report.md; (2) every M1a report states the code commit each result belongs to; (3) "reference visibility assumed" stays wherever visibility truth is missing (report builder prints it; T-17 records whether each dataset has visibility truth, per the AR-36 ruling); (4) D-8 stays deferred to T-22.
- Next: T-17 (dataset qualification). Per §0, downloads are allowed now that M0 is accepted, but only after T-17 records source authenticity and licence terms; real-world scenes stay excluded (D-3).

### 2026-11-12 — T-17 in progress: Part 1 recorded before download
- Did: pinned both repositories (same revisions as T-07), read and pinned both licence texts (OpenMDW-1.1, CC BY 4.0), recorded authenticity evidence and licence rows, and fixed the selection before any download: SDG near-miss artifacts shard 00538 (seeded draw, seed 20261112, 546 of 547 shards eligible under 6 GiB), SDG metadata indexes, SmartSpaces 2026 Warehouse_000 and its re-rendering Warehouse_001 without depth maps. Planned 10.2 GB of the 22 GB cap. `research/datasets/qualification.md` Part 1.

### 2026-11-12 — T-17 done
- Did: downloaded the Part 1 selection (47 files, 10.18 GB of the 22 GB cap, all matching their Git-LFS SHA-256) into git-ignored `data/raw/`; no real-world scene. Census reproduced on the SDG shard (3 runs: 1 worker, 1 forklift, 300 frames, 10 views each). Units: metres (SDG metersPerSceneUnit 1.0; SmartSpaces box scales) and m/s by derivation. Lineage fields recorded, including the tier-join suffix rule and the Warehouse_001 ← 000 render parent. Frame intervals of all 68 recordings: constant 33.333 ms, no VFR. Visibility truth: per-camera visible / not visible only, no fraction, in both datasets. Five card discrepancies recorded for T-18. `research/datasets/qualification.md` Part 2.
- Tests: 1704/1704 (full suite), determinism re-run: not applicable (no code change; research record and data only)
- Problems / CRs: none. For T-18: forklift class `robot` (identify by prim name); SmartSpaces field names with spaces; SDG run-ID suffix join; AR-35 item 7 (world frame and calibration tier from the dataset's declared frame) and AR-36 item 4 (visibility) apply.
- Next: T-18 (dataset adapters).
- Correction (12 Nov 2026): `research/datasets/qualification.md` was never committed. The `.gitignore` pattern `datasets/` (meant for downloaded data) also matched `research/datasets/`. Commit 0776312 therefore contained only the Progress-log line, and the earlier statement that Part 1 was "pushed before download" was wrong. Part 1 was written in this repository before any download began, but it was not in git until now, so git cannot prove that order. Fix: data rules in `.gitignore` are anchored to the repository root (`/out/`, `/data/`, `/datasets/`); only `research/datasets/` became visible. The record (Parts 1 and 2) is committed in the next commit.

### 2026-11-12 — Owner decisions D-20, D-21, D-22 recorded
- D-20 (B): leakage "scene" = rendered scene instance (run, or scene plus re-renders); layout family → `shared_scene_content`, no edge; no split frozen until the Architect commits E-1.2.12. D-21: cap 30 GB; real footage for testing only (§0 amended; CLAUDE.md "Never" line left for the Owner to amend). D-22: pallet trucks present, not evaluated.

### 2026-11-12 — T-17b done; STOP at G-DL (D-24)
- Did: `qualification.md` Part 3, written before any Part 3 download. SDG: the run indexes name RGB shards only, so the agent fetched `manifest_nearmiss_artifacts.json` (3.3 MB, git-blob hash checked) and read the first tar header of each of the 547 artifacts shards. This gave a shard→run map, checked against the held shard 00538. All artifacts runs are multi-camera; 477 shards hold only 10-camera runs. Seeded draw (PCG64, seed 2026111203, 475 eligible): shards 00336 and 00243, 6 runs, 9.66 GB. SmartSpaces `Warehouse_026/027`: 15 files, 0.29 GB, videos + calibration + a VGGT reprojection report, no ground truth. The Croissant metadata states individual written consent, but also "evaluation-only" and "manual labeling … prohibited by the challenge rules" (raised in D-23 and D-24). Safe and Unsafe Behaviours: Mendeley v1 pinned (DOI 10.17632/xjmtb22pff.1, CC BY 4.0); consent statement recorded; faces visible, not blurred; both HF mirrors byte-identical to Mendeley (691/691 SHA-256); 4 classes, 371 files, 5.77 GB. FieldWorkArena excluded (gated, custom terms). Real-data rules and the VR-E-070 retention proposal recorded. Budget: 25.9 GB of 30 GB. Selection lists with every hash: `research/datasets/part3/`.
- Correction: Part 2 multi-camera count 1,640/74 → 1,642/76 (corrected in place, with a note).
- Opened: D-23 (real-data annotation), D-24 (STOP: selection approval), D-25 (G-FQ: proposed frame-quality rules version rv2, for Architect review).
- Tests: 1704/1704 (full suite), determinism re-run: not applicable (no code change; research record only)
- Problems / CRs: none. Deviation from "parquets only" recorded in Part 3 §3.1 and D-24.
- Next: STOP for D-24. Independent of it: T-18 adapters on held synthetic data (SDG 00538, SmartSpaces 000/001), and T-19. No split freeze before E-1.2.12 (D-20).

### 2026-11-12 — Owner decisions D-23, D-24 recorded; contract E-1.2.12 (Appendix T section T14)
- D-24 approved with changes: SDG member-level byte-range download (self-hashed, `self_hashed_unverified_by_publisher`); SmartSpaces 026/027 reference-free only (no labels of any kind, no accuracy metrics); Safe and Unsafe Behaviours: real_natural, academic and testing use only, estimand conditional_on_selection; VR-E-070 values BLOCKING (D-26 opened). D-23: Owner annotates; a second person annotates a seeded 20–30 % subset blind to the first annotator; tool VIA; Safe and Unsafe Behaviours only. D-25 awaits the Architect. CLAUDE.md "Never" line amended by the Owner (D-21 exception).
- Appendix T section T14 appended verbatim; CLAUDE.md reads E-1.2.12.

### 2026-11-12 — T14 conformance
- Did: T14.1 needed no engine change. Edges come from `scene_id`, `ext_run_id`, `render_parent` and `seed` (AR-31); a layout family in `layout_id` or `generation_batch` creates no edge on its own. Adapter rule for T-18: a synthetic `scene_id` is the run or scene asset, never the layout family. T14.2 and T14.3: `report.target_b_section` prints the T14 scope and, beside every cluster-bootstrap interval, the leakage-group counts per partition and data origin; it refuses a group member with no data origin. The linter rejects unseen-camera, -layout or -site claims in a T14-scoped report.
- Contract tests: CT-T14-1 (layout family gives no edge; run, seed and render-lineage edges unchanged), CT-T14-2, CT-T14-3 (`tests/splits/test_t14.py`, 7 tests).
- Tests: 1711/1711 (full suite), determinism re-run: identical (1711/1711)
- Next: Part 3 addendum (SDG member-level draw, before download), then downloads, then T-18 and T-19.

### 2026-11-12 — Owner decision D-26 recorded; G-FQ applied provisionally (`rv2-provisional`)
- D-26: exploratory phase for real footage. The VR-E-070 values are recorded as pending the advisor and no longer block. rv2 is applied as `rv2-provisional`; dataset terms stay binding; real-data results are reported as experimental. The agent noted in D-26 that T12.5 itself allows real data to reach technically_validated, so item 4 is applied by the §9.6 downgrade-only override (AR-48), not as existing behaviour.
- Did: `decode/quality.py` (black, overexposed, frozen on the luma plane; statistics only, no pixels kept); the PyAV reader supplies luma statistics only for rules versions that need them; `resolve` applies the flags after timestamps (frozen needs time spans). rv1 is unchanged, and so are all M0 values. Fitness helper and report line for D-26 (AR-48). The exact rv2 semantics are written into D-25 for the Architect.
- A test-fixture defect was found and fixed before the first commit: the hand-made "frozen" image was itself black under the rule. The input was changed; no expected value was edited.
- Tests: 1726/1726 (full suite), determinism re-run: identical (1726/1726)
- Problems / CRs: AR-48. CR-018 / D-27 (T-19 BLOCKED).
- Still to do before any real-data run: the D-25 step-1 check, rv2-provisional on all held synthetic recordings (expected 0 flags).

### 2026-11-12 — T-18 in progress (part A: SDG camera → full_camera calibration)
- Did: `adapters/sdg_camera.py` converts USD row-vector view and projection to OpenCV K, R, t (pinhole only, metres only, static camera required); full_camera, dataset_supplied, supplied_unvalidated. The derivation is in the test docstring, with hand values. The OpenCV projection equals the USD projection to 1e-6 px on random points.
- Data check (held shard 00538, run f1d9…, 10 cameras): 5,503 boxes in front of the camera. The reprojected 3D-box hull contains the dataset's own 2D loose box for 5,498 of them; 5 exceed it by more than 2 px (worst 416 px); 129 boxes have corners behind the camera. The 5 are to be explained in part B.
- Tests: full suite run below with the commit
- Next: T-18 part B (SDG oracle tracks and S0 registration from the artifacts; forklift by prim name; run-ID suffix join; T14.1 lineage: `ext_run_id` = run, `scene_id` = run, layout family in `layout_id`).

### 2026-11-13 — G-FQ: Architect review of D-25 recorded; S_flat evidence (item 1a) does not separate, nothing changed (1c)
- Did: recorded the Architect review in D-25. `LumaStats` also keeps P1 (nearest rank, same method as P99); no flag uses it yet. Computed P99 − P1 for the 4,361 `black` frames of the 690 SDG member videos (`research/datasets/part3/rv2_sflat_evidence.json`): red-lit runs 0–16 (median 9), judged blank 0–14 (median 0), others 0–16. Groups (i) and (ii) overlap, so S_flat is not set and the rules are not changed (item 1c). Items 2 and 4 (low_light tag, rename to rv2 and apply to all M1a recordings) are not applied because they depend on 1b. Items 3 and 5 recorded as accepted. The 13 whole-video red-lit recordings have spread ≥ 3 on every frame; the overlap comes from the blank-stretch edge frames in group (ii) and an exactly flat stretch in `run_6…eye_01` (group i). Details in D-25.
- Tests: 1732/1732 (full suite), determinism re-run: identical (1732/1732)
- Problems / CRs: none new; D-25 item 1 back to the Architect.
- Next: STOP on D-25 item 1 (S_flat). Independent of it: T-18 part B on synthetic data under rv1.

### 2026-11-13 — Architect rulings of 13 Nov 2026 recorded (contract E-1.2.13)
- B: CR-018 / D-27 decided; Appendix T section T15 appended verbatim; CLAUDE.md reads E-1.2.13. C: AR-48 accepted. A (D-25 rv2): recorded with its implementation in the next entry.

### 2026-11-13 — T-19 done (contract E-1.2.13)
- Did: R4 under T15. `substrate/surrogate.py`: ttc by bisection on [0, t_at_min] of the T8.3 prediction; pet_pred from swept regions (hull of footprint at 0 and τ), occupancy intervals, forklift first on ties. S4 `pair_series` gains `ttc_s` and `pet_pred_s` (T15.7). S5 `r4_c`: Unknown when uncalibrated or either speed null, else TTC part OR PET part; no R4 borderline flag. T15.5 (ttc_max, pet_max ≤ τ) refused with ERR-SPEC. `events/baselines.py`: BL-2 to BL-6 provider sets, BL-1 deferred to M1b, primary comparisons BL-2 vs BL-3 and BL-3 vs BL-6.
- Contract tests: every T15 fixture (head-on ttc found; crossing beyond τ ttc null; time-gap crossing pet_pred 0.6 s with ttc null; simultaneous occupancy pet_pred 0 with ttc 0.2693774 s; parallel paths A empty; null velocity and uncalibrated give Unknown; ttc_max or pet_max > τ gives ERR-SPEC; CT-T11-02 extended to R4), plus the disc footprint, ttc 0 at overlap, no R4 borderline flag, BL table (`tests/events/test_t15.py`, 22 tests). Hand values are written in the tests.
- **Expected values changed by the contract (for Owner review):** two tests listed the rule_configuration providers without R4. E-1.2.13 makes R4 a recorded provider with ttc_max and pet_max, so both lists now include R4 (comment cites E-1.2.13). No value was changed to make code pass. As a result every rule_configuration ID, including the M0 pipeline's, differs from the IDs printed in `reports/M0_report.md` (AR-49 item 7).
- Tests: 1766/1766 (full suite), determinism re-run: identical (1766/1766)
- Problems / CRs: AR-49.
- Next: rv2 (D-25 ruling A) and the 758-recording re-run; then T-18 part B.


### 2026-11-13 — T-18 in progress (part B: SDG truth reading; oracle tracks BLOCKED on CR-019 / D-28)
- Did: `adapters/sdg_truth.py` reads one camera's truth. Annotation line k is tied to decode_seq k, and a line count different from the video's frame count is refused. The forklift is found by prim name and a person by label `character`. The pose is the 3D-box floor centre and yaw is the box's x axis (AR-50; D-8 and T8.2 as written). Loose and tight 2D boxes are read as supplied, and the reprojection check is now code (`hull_excess`).
- Data check over all 72 held SDG runs (709 cameras, 405,075 object boxes; `research/datasets/part3/sdg_truth_check.json`):
  - `metro_agent_data.world_position` is stale in 32 runs and is otherwise the prim origin, 0.63 m off the forklift's footprint centre. So it is not used (AR-50 item 2).
  - Annotation line count ≠ video frames on 9 cameras in 3 runs; 1 camera lacks members.
  - 529 loose boxes extend more than 2 px beyond their reprojected 3D box, in two groups with nothing between 80.1 and 157.3 px. 483 boxes at ≤ 80 px are mostly persons (animated mesh larger than the fixed 3D box). 46 boxes at ≥ 157 px are all on camera `eye_01`; the inspected case (part A's 5 boxes, frame 136) is a forklift box that encloses a foreground pallet stacker. That explains part A's 5.
- Raised: CR-019 / D-28. The oracle-track box (tight or loose), the state of not-visible frames, cameras with incomplete annotation, and the threshold and handling of faulty truth boxes all change measured values. SDG ORACLE-S3 and CV-SIM artifacts wait for it.
- Tests: `tests/adapters/test_sdg_truth.py` (7 tests: hand-value floor pose and yaw wrap, classes, parsing, line-count refusal, truth round trip through the calibration within 1e-6 m, hull excess). Full suite: in the commit below.
- Problems / CRs: AR-50, CR-019 (D-28).
- Next: rv2 (D-25 ruling A) result; then T-18 part C, independent of CR-019: S0 registration of SDG recordings (T14.1 lineage: `ext_run_id` = run, `scene_id` = run, layout family in `layout_id`) and the SmartSpaces adapter.

### 2026-11-13 — G-FQ: D-25 ruling A applied (`rv2`, S_flat = 2, `low_light` tag); 758-recording re-run
- Did: `rv2` (synthetic M1a) and `rv2-real-provisional` (real): black iff P99 ≤ 32 and P99 − P1 ≤ 2; frozen and overexposed unchanged. `low_light` recording tag (median P99 of the non-black frames ≤ 32), never an exclusion. `rv2-provisional` kept, superseded, so the evidence files reproduce; rv1 unchanged for the M0 fixtures. Re-run on all 758 synthetic recordings (558,000 frames, `research/datasets/part3/rv2_check_synthetic.json`): black 161 frames in 16 recordings (was 4,361), frozen 40 in 2 (unchanged), overexposed 0; eligible 557,839. `low_light`: 13 recordings, exactly the whole-video red-lit ones in `run_43_seed_631373023` and `run_6_seed_1833142794`; both readings of the tag rule give the same list. Recorded as the Architect review in D-25.
- Tests: `tests/decode/test_rv2.py` (hand values). 1772/1772 (full suite), determinism re-run: identical (1772/1772)
- Problems / CRs: AR-51. Pending gate: before any real-data result, the dark-frame spread report per real recording (ruling A item 6).
- Next: T-18 part C, independent of CR-019: S0 registration of SDG recordings (T14.1 lineage) and the SmartSpaces adapter.

### 2026-11-13 — G-FQ: rv2 re-run and AR-51 accepted; frozen/black overlap (Architect item 2)
- Did: recorded the acceptance in D-25 and on AR-51. Under rv2, all 40 frozen frames are also black, exactly flat (P1 = P99 = 16): `run_18_seed_1313717419.eye_00` seq 53–73 (21), `run_2_seed_487012118.eye_02` seq 181–199 (19). No frozen frame is not black; nothing changed (`research/datasets/part3/rv2_frozen_overlap.json`).
- Tests: no code change; full suite 1772/1772.
- Next: T-18 part C.

### 2026-11-13 — T-18 in progress (part C: SmartSpaces calibration and truth; SDG S0 registered; SmartSpaces S0 BLOCKED on CR-020 / D-29)
- Did: `adapters/smartspaces.py` reads a scene's calibration (full_camera from K and E; the supplied `cameraMatrix`/`homography` map map-image coordinates and are not read) and its truth (frame id k = decode_seq k, refused otherwise; classes incl. pallet_truck per D-22; footprint centre; forklift yaw = long axis = rotation + π/2). `adapters/registration.py` builds the S0 registration of SDG runs: one site (layout family), a camera per run and view, session = run, T14.1 lineage (ext_run_id = scene_id = RGB run id, seed, generation batch, layout family), recording-local timelines, a synthetic retention record. All 72 held SDG runs registered as one S0 artifact `art_vv6sr4v7drrylwgkdd3subizsb` (720 recordings, all h264; 708 calibrations; 12 cameras without camera parameters registered uncalibrated): `research/datasets/part3/s0_sdg_summary.json`, artifact in git-ignored `out/s0_sdg/`.
- Data check, SmartSpaces (`research/datasets/part3/smartspaces_truth_check.json`): Warehouse_001's calibration and truth are byte-identical to 000's; 9,000 truth frames = 9,000 video frames on all 19 cameras; 99.86 % of 1,924,956 visible boxes per scene lie within 2 px of the reprojected 3D box under K·E, the rest are persons (≤ 26.7 px), forklifts ≤ 0.49 px; all 80,626 forklift boxes long along local y; box floors within −0.06 … +0.14 m of z = 0. SDG: forklifts long along local x on all 20,081 boxes checked; box floor at z ≈ 0.
- Raised: CR-020 / D-29 (dataset_source.data_origin when a release's scenes differ in origin: SmartSpaces 000 rendered, 001 transferred, 026/027 real). SmartSpaces S0 waits for it. CR-019 gained the SmartSpaces evidence: only its item 2 (not-visible frames) arises there.
- Tests: `tests/adapters/test_smartspaces.py` (hand projection, floor round trip within 1e-6 m, yaw wrap, classes, frame-id refusal, hull excess hand values), `tests/adapters/test_registration.py` (lineage, refusals, S0 tables, determinism, one leakage group per run). 1790/1790 (full suite), determinism re-run: identical (1790/1790)
- Problems / CRs: AR-52 (review flag: item 2, forklift yaw), CR-020 (D-29).
- Next: STOP. The rest of T-18 (SDG and SmartSpaces oracle tracks and CV-SIM references; SmartSpaces S0) waits for CR-019 / D-28 and CR-020 / D-29. T-20 needs T-18; M1b starts after G-M1a. No independent task remains.

### 2026-11-13 — T-18 in progress (T16 and T17 implemented; oracle build running; session stopped at the usage limit)
- Rulings recorded: T17 (E-1.2.15; CR-019 / D-28 closed) and T16 (E-1.2.14; CR-020 / D-29 closed), both appended verbatim. The T16 set reached the agent after the T17 set; its item D ("do not proceed on the SDG oracle tracks") predates T17 and is treated as superseded by it. AR-49, AR-50, AR-52 and T-18 part C accepted.
- Did: `adapters/oracle_truth.py` (T17.1–T17.6: tracked / predicted / lost, exact image-clipped reprojection, T17.5 defect and refusal band, CF-IMG box mapping, S3 and CV-SIM inputs); T16.2 in `splits/leakage.py` (edges across dataset rows with the same name); T16.1 refusal of a file under two rows in the registrar; registrar now stores supplied lineage null reasons. SDG S0 re-registered (`art_xwrldyhquvmorjhpjxb573tbxk`); SmartSpaces 000 / 001 registered, one S0 each. Yaw-against-motion check run (`research/datasets/part3/yaw_motion_check.json`).
- Raised: AR-53 (review flag item 3: dataset boxes are inclusive pixel indices, mapped to CF-IMG by +1 on the right and bottom edges); CR-022 / D-31 (T17.5 band (80, 157] catches the held 80.1 px box; that camera is refused as written). CR-021 / D-30 closed by T16.2.
- Not done at the time of that commit (all completed in the next entry): the T17.7 counts, the real 026/027 registration, the CR for ruling B, and the AR-53 wording.
- Tests: 1816/1816 (full suite), determinism re-run: identical (1816/1816)
- Next: finish the four items above, then record the T17.7 counts.

### 2026-11-13 — T-18: T17.7 counts; real 026/027 registered (T16); ruling B checked, CR-023 / D-32 opened
- **T17.7 counts** (`research/datasets/part3/t17_counts_sdg.json`, `t17_counts_smartspaces.json`; S1 under rv2 with TEST-ONLY decode parameters; artifacts in git-ignored `out/`; per-run rows are in the files):
  - SDG, 72 runs, 720 cameras, 216,000 frames (215,839 eligible): **tracked 389,884; predicted 4,992; lost 339; truth_defect 46** (15 runs, all camera `eye_01`); unchecked boxes (a 3D corner behind the camera) 8,199. **Cameras without truth 23** (12 without camera parameters; 11 with an annotation file shorter than the video), in 5 runs. **1 camera refused under T17.5** (`…run_22_seed_1886649344.eye_02`, excess 80.1 px; CR-022). **696 cameras have an ORACLE-S3 artifact**, each with 1 forklift and 1 person track. 168 track points fall on frames that are not eligible under rv2 and are left out. Object-frames outside the visible span (no point): 3,525.
  - SmartSpaces, per scene (identical truth in 000 and 001), 19 cameras, 9,000 frames each, all eligible: **tracked 1,924,956; predicted 927,728; lost 785,971**; no defect check (SDG only); cameras without truth 0. 685 tracks per scene over the 19 cameras (600 person, 58 forklift, 27 pallet truck); 816 object-camera pairs never visible (no track); 9,163,526 object-frames outside the visible span.
  - For the Architect's attention: on SmartSpaces a third of all oracle points are `predicted` (inferred). T17.2 as written turns every absence between an object's first and last appearance in a camera into predicted points wherever its 3D box projects into the image, however long the absence. No rule was changed.
- **Real scenes (T16):** Warehouse_026 (4 cameras) and 027 (7) registered under `MTMC_Tracking_2026@…/real_staged`, one S0 each, D-24 b / D-26 conditions unchanged, no calibration registered (AR-54 item 3, review flag). No frame decoded; the 11 codec probes are the first entries of the access log (`data/derived/real/access_log.jsonl`, chain verified). Summary: `research/datasets/part3/s0_smartspaces_real_summary.json`. The dark-frame spread report (D-25 ruling A item 6) is still due before any real-data result.
- **Ruling B (yaw):** SmartSpaces passes (99.8 % within 15°). SDG is not concentrated (53.6 % within 15°, 35.3 % beyond 75°; the off-axis frames are pivot turns), so CR-023 / D-32 is raised and SDG yaw is withheld in code.
- Tests: `test_t16_*`, `test_real_scenes_*`, `test_sdg_yaw_is_withheld_by_default_cr_023`, `tests/registry/test_access_log.py`. 1821/1821 (full suite), determinism re-run: identical (1821/1821)
- Problems / CRs: AR-54; CR-023 (D-32); open from before: CR-022 (D-31).
- Next: T-18 is complete except what CR-022 and CR-023 decide (one refused camera; SDG yaw) and the O/H/PC interaction references, which need frozen rule parameters (T-21). T-20 (pre-registration draft) is the next task.


### 2026-11-14 — T-18 done (T18 and T19 implemented; counts rebuilt); T-20 done (draft delivered); STOP at G-PR
- **Rulings recorded (two sets, 14 Nov 2026; Owner approval by forwarding).** First set: CR-023 / D-32 closed (SDG forklift yaw = box long-axis yaw, "simulator yaw when supplied"; the motion-direction check is evidence only; SDG S4 unblocked); T18 (E-1.2.16) appended verbatim (guard band (90, 150] px; not-visible runs longer than g_max are lost; run-length reporting), CR-022 / D-31 closed; AR-53 item 3 and AR-54 item 3 accepted; item D of the earlier set superseded by T17. Second set: T19 (E-1.2.17) appended verbatim (run length in eligible frames), CR-024 / D-33 closed; AR-55 item 6 accepted as pinned; ruling C on the T-20 draft. Neither CR-022 nor CR-023 held a point the rulings do not cover.
- **AR-55 item 6, Architect ruling:** "Identity of S4/S5 output is required only for runs <= g_max. For longer runs the new behaviour is intended: the POW ends with gap_exceeded and a continuation POW starts. The Architect's earlier statement that no pair-level result changes is withdrawn." The T8.1 text beside it (Appendix T, verbatim):
  > - A joint frame has track points for both the person track and the forklift track with state ∈ {tracked, predicted}.
  > - A gap is a run of eligible frames that are not joint frames (either point missing or state = lost). The gap is bridged (POW continues) iff ALL hold: the gap length in eligible frames ≤ g_max; both tracks have joint frames after the gap; no coverage segment of state not_recorded, gap_unobserved or unusable lies between the last joint frame before the gap and the first joint frame after it.
  > - Otherwise the POW ends after its last joint frame, and a later joint frame starts a new POW with continuation_of_nk set if the same two tracks continue.
  > - end_reason: … gap_exceeded if the gap was longer than g_max.

  **One line: T8.1 treats a predicted point as presence (a frame with a predicted point is a joint frame); only a missing or lost point makes a frame part of a gap.**
- Did: `adapters/oracle_truth.py`: guard band (90, 150] px; SDG forklift yaw passed; `camera_tracks` takes g_max and the ineligible frames, a run of more than g_max eligible frames is lost on every frame, ineligible frames of shorter runs get no point; run-length helpers; optional reprojection cache. `research/datasets/part3/t17_oracle.py`: g_max in the oracle configuration record, run-length distribution, verified reuse of the stored S1 artifacts (nothing decoded again: 758 of 758 reused), POW sensitivity counts. Finding added to CR-007 / D-8 (heading fallback about 77° off during SDG pivots). Per-dataset evidence for inclusive pixel boxes added to AR-53 (`box_convention_evidence.json`). Truth-side forklift yaw-rate distribution for the `forklift_turning` proposal (`yaw_rate_distribution.json`).
- **T17.7 counts under T19** (code commit 63aed8b, TEST-ONLY g_max = 15, S1 under rv2; `t17_counts_sdg.json`, `t17_counts_smartspaces.json`; ORACLE-S3 artifacts in git-ignored `out/t19_*`, contract label E-1.2.17):
  - SDG: **697 cameras with an oracle track** (was 696; `…run_22_seed_1886649344.eye_02` now included), 0 refused, 23 without truth; tracked 390,484; predicted 1,166; lost 4,076 (4,027 in runs longer than g_max); 89 ineligible frames in shorter runs without a point; truth_defect 46; unchecked boxes 8,199; 29 tracked points on ineligible frames left out.
  - SmartSpaces, per scene (000 and 001 identical): tracked 1,924,956; **predicted 19,109 (was 927,728); lost 1,694,590** (1,693,891 in runs longer than g_max); 685 tracks over the 19 cameras, as before.
  - Run lengths (eligible frames; min, median, P90, P99, max): SDG forklift 0, 1, 1, 38, 68 (160 runs); SDG person 0, 3, 38, 122, 141 (388 runs); SmartSpaces per scene forklift 1, 27, 434, 2,789, 3,951 (692 runs); person 1, 19, 606, 3,373, 8,009 (6,625 runs); pallet truck 1, 6, 23, 46, 502 (585 runs).
  - POWs and POWs ended by gap_exceeded at g_max 5 / 15 / 30 / 60 (sensitivity evidence, counts only): SDG 864 / 790 / 750 / 710 POWs with 167 / 93 / 53 / 13 ended by gap_exceeded; SmartSpaces per scene 18,084 / 13,907 / 11,447 / 9,522 with 16,619 / 12,439 / 9,973 / 8,040.
  - CR-024 evidence (first rebuild, reading "camera frames", commit 6f7fb07, kept in git history): 1 SDG run of 548 would have had the other outcome. AR-56 item 2 diagnostic: 0 frames in both datasets.
- **T-20:** `docs/preregistration_DRAFT.md` delivered: data and populations, split, sampling frame, parameters with grids, §5 g_max evidence (run-length tables for both datasets and the POW counts; no value recommended), reporting strata with the `forklift_turning` proposal and its evidence, configurations, primary metrics, acceptance criteria (targets left to the Owner), limitations, and the six checklist items. No test-partition evaluation was run; no split is frozen.
- Tests: `test_t18_*`, `test_t19_*`, `test_sdg_forklift_yaw_is_the_box_yaw_cr_023`, `tests/events/test_t18_oracle_absence.py`. 1838/1838 (full suite), determinism re-run: identical (1838/1838)
- Commits: 6f7fb07 (T18), 63aed8b (T19), and this entry's commit (counts, draft); all pushed.
- Problems / CRs: AR-55, AR-56 (item 2 is a review flag; 0 frames affected on held data). No open CR except CR-007 (deferred to T-22).
- Next: **STOP at G-PR (D-34).** T-21 needs the frozen pre-registration; T-22 and later need G-M1a. No independent task remains.

### 2026-11-14 — G-PR: D-34 recorded; T20 (E-1.2.18) appended and implemented; counts re-run; freeze HELD on D-35
- **Rulings recorded (G-PR text, 14 Nov 2026 = Owner decision D-34).** T20 appended verbatim to Appendix T (contract **E-1.2.18**; CLAUDE.md updated). Remaining items of AR-53, AR-54, AR-55 and AR-56 ACCEPTED (AR-56 item 2 as revised by T20.1). Owner values B.1–B.11 recorded in D-34.
- **T20.1** (`adapters/oracle_truth.py`): visible frames = dataset-visible AND eligible; span and runs follow them; a dataset-visible ineligible frame carries no point and belongs to the run around it. The E-1.2.17 reading stays only as the `legacy_e_1_2_17` diagnostic that lists changed outcomes; `merged_run_frames` (AR-56 item 2 diagnostic) removed. Tests: the T20.1 Architect test (one run of 20, lost on all 21 frames), span ending at the last eligible visible frame, object visible only on ineligible frames, short run with a visible ineligible frame. `test_t19_a_visible_frame_that_is_not_eligible_still_ends_a_run_ar_56` pinned the reading T20.1 reverses and was replaced (contract change, not an edited expectation). One hand count in a new test was wrong as first written (5 eligible frames, written as 6) and was corrected before commit.
- **T20.2** (`evaluation/strata.py`, report time, no artifact): `forklift_turning` with the T9.1 run and shifted window, fold to (−π/2, π/2], true / false / unknown, `turning_reportable` for D-8. Tests: the four Architect tests (constant → false; 75°/s → true; half-turn jump → false; null yaw → unknown) plus too-short window, shift at the track end, strict threshold, fold range.
- **Counts re-run under T20.1** (code commit 9a0674e, TEST-ONLY g_max = 15, S1 reused and verified; ORACLE-S3 in git-ignored `out/t20_*`; `t17_counts_*.json`, field `t20_1_changes` per camera and `t20_1_transitions`):
  - SDG: **29 object-frames change outcome, all forklift, all on ineligible frames; 0 eligible frames change.** 6 go from tracked to no point inside a run (`run_6_seed_1495571596.eye_01`, seq 29–30, 32–35); 23 go from tracked to outside the span (`run_23_seed_905230252.eye_02` seq 0–5; `run_6_seed_1833142794.eye_01` seq 6–22). These 29 tracked points were already left out of S3 (ineligible), so no S3 track point, POW count or sensitivity count changes. Totals: tracked 390,484 → 390,455; not_eligible_in_run 89 → 95; outside_span 3,525 → 3,548; points on ineligible frames 29 → 0; predicted, lost and the POW sensitivity counts unchanged. Forklift runs 160 → 162 (two new runs of length 0 in `run_6_seed_1495571596.eye_01`; percentiles unchanged).
  - SmartSpaces: no change (all frames eligible).
- **Freeze not done.** D-34 item B.2 ("seeded draw stratified by generation batch", 24/48) cannot be applied as written: the recorded `generation_batch` has 14 values (22, 15, 14, 4, 4, 3, 2, 2 and six singletons), so the allocation needs a rule that decides partition membership. Raised **D-35** with options; nothing is frozen (no `preregistration_FROZEN.md`, split, sampling plan or criterion records), and the B.8 validation-only tables wait for the split. All other D-34 values were checked and can be applied as written (no τ-grid combination is refused by T15.5).
- Tests: 1852/1852 (full suite), determinism re-run: identical (1852/1852)
- Commits: 9a0674e (T20), this entry's commit (counts, records); pushed.
- Next: **STOP on D-35.** On its answer: freeze (C.2), validation-only truth tables (C.3), then STOP before T-21 until the Owner's separate go-ahead for the validation run.

### 2026-11-14 — G-PR done: pre-registration frozen (version 1); B.8 truth tables on validation; STOP at G-VAL (D-36)
- **Decisions recorded.** D-35 option (b) (3 batch families, 12 / 7 / 5 validation runs), the two freeze-time ARs accepted; Owner answer on VR-E-005: X0b v1 = SDG + Warehouse_000, Warehouse_001 validation by its leakage edge and added at M1b. Owner session override: after C.2 only B.8, then STOP; no T-21, no S5 or S8 on any partition.
- **Code** (commit 0e95e77): `splits/draw.py` (batch family, per-family draw), `pipeline/prereg.py` (Owner values as data; criterion records), `sampling.plan_rows(population_definition_ref=…)` (M0 default unchanged), `research/preregistration/freeze.py`. AR-57 (items 3, 7 accepted; 9 Owner-decided; others pending review).
- **Frozen** (`docs/preregistration_FROZEN.md`, `docs/preregistration/freeze_record.json`; contract E-1.2.18; code 0e95e77; requirements.lock 228ef036…971d; frozen_utc 2026-11-15T01:47:59Z): X0b `art_w5v3ldr43xdsqc6l4zifmjkuuj` (spm_uvjw4v4mygzvtvwqrbjjhambh5; 739 recordings, 73 leakage groups: validation 25, test 48; SDG 24 / 48 runs); V0 `m1a-sdg-validation` (226 windows), `m1a-sdg-test` (471), `m1a-smartspaces_000-validation` (190), census, strata dataset row × viewpoint class; criteria C1-MR-01, C2-GV-01-ceiling, C2-GV-01-eye_level, C3-GV-07, C4-GV-04 registered; #5–#10 not registered. The freeze script was run twice: identical record and artifact IDs.
- **B.8** (`docs/preregistration/validation_truth_tables.md`): SDG validation forklift runs P99 17, max 17 (all runs 38, 68); person P99 79, max 141; POWs at g_max 15: 249, 23 ended by gap_exceeded; yaw two-peaked, 0.9 % of frames in 1–5°/s (0.5 s window); every validation forklift box 3.03 × 1.13 m. SmartSpaces: validation = all runs. Stated basis of g_max, e_fturn and the footprint priors holds; nothing re-chosen. All-runs columns reproduce the draft.
- Tests: 1863/1863 (full suite), determinism re-run: identical (1863/1863)
- Problems / CRs: AR-57. Open: CR-007 (deferred to T-22).
- Next: **STOP at G-VAL (D-36).**

### 2026-11-14 — T-21 BLOCKED before running: D-36 step 1 estimate exceeds 4 h (D-38); CR-025 opened
- Decisions recorded: D-36 approved for validation only; D-37 test-partition reservation in force; AR-57 accepted in full (Owner note on item 9: at M1b raise a CR on how new recordings join a frozen split).
- Did: timing probe on one SDG validation camera and a pair-frame count on SmartSpaces Warehouse_000 (`research/m1a/runtime_estimate.md`, `runtime_probe.py`, `smartspaces_pair_frames.py`; validation recordings only, nothing written to `out/`, no S8). (a) about 88 h serial (SDG about 2 h, SmartSpaces about 86 h: 3.19 M pair-frames at about 50 ms each in S4, 70 % in R4 `pet_pred`); (b) SDG sweeps about 16 h serial, SmartSpaces sweeps infeasible; SmartSpaces S4 about 1–2 GB per camera.
- Raised: D-38 (reduced plan; recommendation (A)); CR-025 (construction of the O/H/PC references from truth; blocks EV-M only).
- Tests: no code change (1863/1863 at 566fe76).
- Next: STOP on D-38 and CR-025.

### 2026-11-14 — Session end: D-38 decided (option A)
- Owner chose option (A). Next session (when the laptop can run unattended for about 12 h): R4 surrogate speed-up as an AR with bit-identical values; re-measure; SDG validation in full (base BL-2 to BL-6, full_camera run, sweeps); then SmartSpaces Warehouse_000 base and full_camera runs if within about 12 h. Build the GV metrics and the S8 driver for real data on the way. CR-025 open: no EV-M results until it is decided. D-37: nothing on the test partition.

### 2026-11-15 — T-21 in progress: D-38 A.1 accepted (AR-58); SDG validation run complete; SmartSpaces base + full_camera running; D-39 opened
- **Decisions recorded.** D-38 detail (A.1–A.3, C, D) and the Architect ruling on CR-025: T21 appended verbatim to Appendix T (**contract E-1.2.19**; CLAUDE.md updated); CR-025 closed.
- **A.1 R4 speed-up (AR-58).** Same golden-section and bisection schedule; the shape gap is evaluated against the Minkowski difference (one polygon per occupancy); both golden-section loops stop at their fixed point (bit-identical). Also, with no value changing: per-table caches in hashing, S4 and S5 index tables instead of scanning them per pair or per POW (quadratic on SmartSpaces). A pre-existing **S5 crash** on any recording with an ineligible frame (sort on a null `frame_index`) was found on SDG validation cameras and fixed (AR-58 item 6; also applied to the old-code copy used for the check). **Acceptance met on all SDG validation pair-frames** (old code = commit 5780320 + item 6, against the new code; `research/m1a/r4_equivalence_summary.json`): 226 cameras × 59,267 pair-frames × 2 geometries; pet_pred_s differs on 1,725 values, max 9.35e-7 s; every other pair-series field, every null reason, every flag_series row (all C_by_R4) and every episode (labels, boundaries) of BL-2..BL-6 identical. Speed: SDG camera pipeline 6.0 s → 2.6 s; SmartSpaces S4 now ~8.7 ms per pair-frame.
- **A.2 SDG validation run** (`research/m1a/run_m1a.py`, commit d800a5c; resumable per camera and unit; artifacts in git-ignored `out/m1a/run1/sdg/`): 226 cameras, base (S3, S4 simulator_truth, S5 BL-2..BL-6), full_camera (S4 + S5 BL-2..BL-6; S4 at w_v 0.33 / 1.0), T21 reference, and all sweeps (15 S4-level and 23 S5-only grid points, each under BL-2..BL-6): 62 min, no error. MR-01 repeat run (IDs only) running from a worktree at d800a5c. S8 evaluation (`evaluate_m1a.py`, `aggregate_m1a.py`; GV from `evaluation/gv.py`, from F.1 N7) running. AR-59: representation details of T21, GV and the evaluation, with four review flags (items 2, 5, 6, 7).
- **A.3 SmartSpaces re-measured** (idle machine): base + full_camera ≈ 8.5 h for 19 cameras (≤ 12 h) → running one camera at a time, smallest first (commit ddfac38). SmartSpaces sweeps not run in v1. **T21 references on SmartSpaces are not feasible**: the truth is scene-wide, 4.44 M reference pair-frames per camera, 84 M in all, about 200 h → **D-39** (recommendation: SmartSpaces EV-M not run in v1; Architect amendment for v2).
- **T21.6:** SDG `Dodge` fields described in `qualification.md` Part 4 (a per-frame task state, `metro_agent_data.current_task_name`; in 53 of 69 runs, from frame 0 in 18); not used as a reference.
- Tests: `tests/substrate/test_ar58_r4_speedup.py`, `tests/events/test_ar58_s5_index.py`, `tests/m1a/` (D-37 refusal, T21.1 tracks, the four T21 tests), `tests/evaluation/test_gv.py`. Full suite 1890/1890 at 59e31f0. Two test expectations of my own were wrong as first written and corrected before commit (`visible_frames` lists never-visible objects; GV-08 window past the series end).
- Problems / CRs: AR-58, AR-59 (proposed); D-39 open.
- Next: finish the SDG evaluation and MR-01; write the SDG part of `reports/M1a_report.md` (plain-language page first); SmartSpaces truth tables (`truth_unit.py`) and evaluation after its run; then STOP at G-M1a with D-39.

### 2026-11-15 — T-21: SDG validation evaluated; MR-01 = 1.0; interim report; SmartSpaces running unattended
- **SDG S8** (`research/m1a/results_sdg.json`; interim `reports/M1a_report.md`, plain-language page first): 306 T21 references (303 assessable, 3 unobservable_reference). EV-M1 / EV-M2 (G1): BL-2 0.541 / 0.467; BL-3 0.974 / 0.925; BL-4 = BL-6 0.997 / 0.947; BL-5 = BL-3 (R4 and R5 change PC / NM labels but not G1 membership). BL-2 − BL-3 EV-M1 −0.432 (Target B [−0.513, −0.335]); BL-3 − BL-6 −0.023 (Target A [−0.040, −0.007], Target B [−0.072, 0.000]). GV-01 full_camera: forklift RMSE 1.07 m (P95 1.48 m); persons: ceiling 0.41 m, eye_level 94 m, driven by 816 object-frames (0.65 %) above 5 m, all persons on eye-level cameras (cause not verified). GV-05, MR-10, MR-11 not computable (no covariance). All sweeps reported (MR-08 label stability, GV-03).
- **MR-01 = 1.0** on SDG: a second run from commit d800a5c (temporary detached worktree, removed) reproduced all 904 unit records and 56,726 artifact IDs (`research/m1a/mr01_sdg.json`).
- **SmartSpaces:** base + full_camera run one camera at a time, smallest first (commit ddfac38; 7 of 19 cameras done at 02:33). `research/m1a/finish_smartspaces.sh` waits for it, then builds truth tables, evaluates (CM per window, GV; no EV-M, D-39) and aggregates; every step resumes. First camera checked: person position error median 0.30 m, but 20 % above 10 m (not a frame mismatch: median offset < 3 cm).
- Tests: no change since 8217dff (1890 + the T21 tests).
- Next: when the SmartSpaces run and finisher end, write the SmartSpaces part of the report; then **STOP at G-M1a** (D-39 open; AR-58 / AR-59 review flags).

### 2026-11-17 — T-21: SmartSpaces evaluation stopped by the Owner; speed-only fix (AR-60); not restarted
- Did: the SmartSpaces evaluation had finished 6 of 19 cameras; camera 7 (`rec_gbhz7…`) ran about 34 h without finishing (time grew much faster than camera size). On the Owner's instruction the evaluator and `finish_smartspaces.sh` were stopped (17 Nov, 04:30); camera 7's partial work is lost, the 6 finished `eval.pkl.gz` and all 19 truth tables are kept. Stale watcher shells from earlier sessions also killed. Cause found in S8 helpers that rescan whole tables per frame or per pair (`completeness`, `association.summarize`, `gv.realized_min`); fixed with per-window indexes, same computation order (**AR-60**).
- Equivalence: 501 seeded random cases repr-identical to frozen pre-AR-60 copies (`tests/evaluation/test_ar60_eval_index.py`); real data, 3 SDG and 2 SmartSpaces cameras re-evaluated into a scratch folder, outputs repr-identical to the stored ones (`research/m1a/ar60_equivalence.jsonl`); `rec_a4xz…` 7 min → 25 s. The check on the two largest finished cameras (`rec_dazuru…`, `rec_bg7m…`) was not run (laptop resting).
- Tests: 2391/2391 (full suite), determinism re-run: identical (2391/2391)
- Commit: this entry's commit (pushed)
- Problems / CRs: AR-60 (proposed). D-39 open.
- Next: (optional) AR-60 check on `rec_dazuru…` and `rec_bg7m…`; restart with `PYTHONPATH=src .venv/bin/python research/m1a/evaluate_m1a.py smartspaces run1 cameras 1 && … aggregate` (finished cameras are skipped); then the SmartSpaces part of the report; then STOP at G-M1a.

### 2026-11-17 — T-21: SmartSpaces evaluation resumed and complete (AR-60 code)
- Did: restarted `evaluate_m1a.py smartspaces run1 cameras 1` then `aggregate` at code 7812832 (AR-60). The 6 finished cameras were skipped; the other 13 (including `rec_gbhz7…`, which had run 34 h before AR-60) were evaluated in about 1 h in all (05:47). `research/m1a/results_smartspaces.json`: 19 cameras, 190 windows, one leakage group (Target B not informative), status experimental (synthetic, oracle perception, validation partition); EV-M, CM-02, CM-06 not run (D-39); sweeps not run (D-38 A.3).
- Results (headline): CM-01 1.000; CM-03 0.567; CM-04 0.632; CM-05 0.000 detected / 0.017 detected+inferred; CM-08 0.000; CM-10 0.000. BL-6: 574 episodes (H 297, PC 466, NM 158, UD 116, O 52, IE 50). GV-04 1.87×1.13 m prior bias −0.28 m, 2.68×1.16 m −0.001 m. GV-06 ρ 0.35, R1/R2 disagreement 4 %.
- **For review, GV-01 / GV-07 / GV-08 on full_camera:** heavy-tailed. GV-01 RMSE: forklift 33,275 m (P95 103 m); person 53 m (P95 99 m); pallet truck 17 m. The inferred points are small (RMSE 0.68–0.88 m), but the detected points are large. This matches the first-camera check (20 % of person errors above 10 m). Cause not verified. A likely candidate is the ground projection of box foot points near the horizon on SmartSpaces cameras. Nothing was changed.
- Tests: 2391/2391 (full suite)
- Commit: this entry's commit (pushed)
- Problems / CRs: D-39 open; AR-60 proposed (optional check on `rec_dazuru…`, `rec_bg7m…` still not run).
- Next: diagnose the full_camera GV-01 tail (counts only, no rule change); SmartSpaces part of `reports/M1a_report.md`; then STOP at G-M1a.

### 2026-11-17 — T-21: position-error diagnosis; SmartSpaces report section; CR-026; STOP at G-M1a (D-40)
- Did (Architect instruction of 17 Nov 2026; validation only, statistics only, nothing decoded, no definition or frozen value changed):
  - `research/m1a/position_diagnosis.py`: per full_camera point (tracked or predicted) on all 226 SDG and 19 SmartSpaces validation cameras. Recomputed positions equal the stored ones (0 mismatches on 2,071,041 points). Breakdown by state, class × viewpoint, bottom-edge offset, border, ray angle and outcome, range, and true distance → `research/m1a/position_diagnosis_{sdg,smartspaces}.json`.
  - `research/m1a/position_cutoffs.py`: range and angle limits as evidence → `position_cutoffs.json`.
  - The optional AR-60 check on the two largest cameras was skipped (Architect).
- Findings:
  - Predicted points: P99 ≤ 1.71 m on both datasets.
  - Tracked points with the bottom edge within 2 px and not on a border: SmartSpaces P99 0.93 m.
  - The errors come from visible boxes ending above the 3D box bottom, on shallow rays (median error 111 m below 1°, 35 m at 1–2°).
  - Rays at or above the horizon (SDG 611, SmartSpaces 8,895) are already null (`not_observable`). Rays meeting the floor beyond 50 m give numbers (SDG 386 = 99.9 % of the squared error; SmartSpaces 974,217 = 50 %, and 37 % of SmartSpaces objects are truly beyond 50 m).
- Raised: **CR-026** (range condition for foot rays; proposal only, not implemented); **D-40** (G-M1a stop).
- Report: `reports/M1a_report.md`: status, plain-language page (SmartSpaces and the diagnosis summary), SmartSpaces technical section, diagnosis section, Stop.
- Tests: 2391/2391 (full suite; no src change)
- Commit: this entry's commit (pushed)
- Problems / CRs: D-39, CR-026, D-40 open; AR-58 / AR-59 flags / AR-60 for review.
- Next: **STOP at G-M1a (D-40).** T-22 and all M1b work need G-M1a; test partition reserved (D-37). No independent task remains.

### 2026-11-17 — G-M1a decided (D-40); rulings 1–9 carried out; M1b feasibility probe; STOP (D-42)
- Decisions recorded:
  - D-40 (M1a accepted as experimental validation evidence);
  - D-39 (option (a) for v1; T21 amendment for v2);
  - AR-58 and AR-60 ACCEPTED; AR-59 items 2, 6 and 7 ACCEPTED, item 5 REVISED;
  - D-41 (pre-registration v2 note on GV-01 reporting);
  - D-8 / CR-007 evidence (SDG forklift full_camera median about 1 m, no outliers).
- Did:
  - **Report wording** (item 2): BL-4/BL-6 vs BL-3 now "agree more closely with the BL-6 reference definition (T21.5)"; added the sentence on reference dependence and the BL-2 viewpoint note (R1/R2 disagreement 51 % SDG, 4 % SmartSpaces).
  - **AR-59 item 5 revised / item 7 addition** (`research/m1a/gv_revised.py` → `gv_revised_{sdg,smartspaces}.json`):
    - GV-04 at simulator positions: SDG +0.0004 m; SmartSpaces −0.0009 m (2.68 × 1.16 m) and −0.279 m (pallet trucks under the forklift prior). The prior clearance equals the stored base clearance on all 3,252,035 pair-frames.
    - GV-08 against simulator truth: SDG bias 0.69 m (P5 −1.12, P95 2.19 m). The earlier GV-04 values are superseded in the report.
  - **Per-label (O, H, PC) recall and precision on SDG** (item 5; `research/m1a/ev_by_label.py` → `ev_by_label_sdg.json`; descriptive). BL-2 never labels H or PC; PC appears only with R4; BL-4 = BL-6 (PC 0.996 / 0.945).
  - **CR-026 diagnostics** (item 6; `research/m1a/position_sensitivity.py` → `position_sensitivity_{sdg,smartspaces}.json`; rows checked against posdiag; Jacobian checked by finite differences):
    - (a) Sensitivity at 0.1 m/px: SDG catches 96.8 % of errors > 10 m and loses 0.02 % of points within 1 m. On SmartSpaces, 0.5 m/px catches 90.3 % and loses 18.1 %.
    - (b) The head-height check separates weakly.
    - CR-026 stays open; no rule implemented.
  - **M1b feasibility** (item 9; `research/m1b/feasibility.md`, `detector_probe.py`, `detector_probe.json`, `requirements_detector.txt`):
    - Environment: `.venv-det` from system Python 3.9.6 (no wheels for 3.14 / 3.15), git-ignored; PyTorch 2.2.2 CPU and ONNX Runtime 1.19.2 run.
    - Weights: 310 MB in git-ignored `out/m1b/weights/`; no download over 1 GB.
    - FPS on 10 SDG validation frames: YOLOX-nano 34.3, SSDlite 7.1, YOLOX-s 3.9, FRCNN-MobileNet 1.1, FRCNN-R50 0.12.
- Tests: 2391/2391 (full suite; no src change)
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-026 open (Architect, v2/M1b); D-42 open.
- Next: **STOP (D-42).** T-22 proper waits for the Owner's go-ahead; test partition reserved (D-37).


### 2026-11-19 — D-43 licence; D-42 decided; T-22 zero-shot probe; STOP (D-45)
- **D-43 (item 1):** `LICENSE` holds the unmodified AGPL-3.0 text from gnu.org (SHA-256 `0d96a4ff…abcb0`). `NOTICE.md` lists, without containing any of them:
  - SDG (OpenMDW-1.1), SmartSpaces `MTMC_Tracking_2026` (CC BY 4.0) and Safe and Unsafe Behaviours (CC BY 4.0; no frames, crops or faces, D-24 c);
  - all 8 detector and text-encoder weight files used, with source URL, SHA-256 and licence.
- **D-42 (item 2):** decided, option (a); T-22 row revised (zero-shot scope); `.venv-det` recorded in WORKPLAN §0.
  - Installs, `.venv-det` only: ultralytics 8.4.215 and transformers 4.57.6 (newest for Python 3.9 + torch 2.2.2). `opencv-python` pinned to 4.10.0.84, because 4.11 has no macOS 12 x86_64 wheel. Pinned in `requirements_detector.txt`; no existing package changed.
  - Two Owner answers before downloading (recorded in D-42 and §0):
    - the 30 GB cap would have been exceeded, so the Owner raised it to 31.5 GB, with weights counted;
    - the Ultralytics CLIP fork is installed from git, pinned at `7ffa84b`.
  - Downloads: 1,070,205,099 bytes (YOLO-World v2-s, CLIP ViT-B/32, Grounding DINO tiny), hashes checked. Held total 30.62 GB of 31.5 GB.
  - One slip, corrected: CLIP first landed in an un-ignored `./weights/` folder. It was moved to `out/m1b/weights/` before any commit; Ultralytics now reads its settings from `out/m1b/ultralytics_config`.
- **Probe:**
  - Scripts: `research/m1b/zero_shot_frames.py` (seeded selection 2026111901 and reference boxes, main `.venv`), `zero_shot_probe.py` (`.venv-det`), `zs_match.py`.
  - Data: 100 frames from 20 SDG validation cameras (10 ceiling, 10 eye-level); 93 person and 97 forklift references.
  - Best-F1, descriptive:
    - Grounding DINO: person recall 0.95 / precision 1.00, forklift 0.89 / 0.96, at 16.5 s per frame;
    - YOLO-World: person 0.90 / 0.98, forklift 0.63 / 0.92 at the lowest threshold (0.05), at 0.35 s per frame.
  - Report: `research/m1b/zero_shot_probe.md`, plain-language summary first, with 7 choices for Architect review. Nothing validated; no S4, S5 or S8 run, no fine-tuning, no tracker, no other prompt; pre-registration and analysis modules untouched.
- Tests: 2406/2406 (full suite, main `.venv`), twice: identical. Probe matcher tests 7/7 in `.venv-det`. New tests: `tests/m1b/test_zs_frames.py` (seed reproducibility, committed record, refusal of test-partition recordings) and `tests/m1b/test_zs_match.py` (hand-computed 3-box toy case).
- **Item 4:** done on `v02-review-ui` (commit 5deb106, pushed): D-40 → D-44 and CR-026 → CR-027, in the new `../rq1-v02` worktree.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. D-45 open (STOP). CR-026 still open.
- Next: **STOP (D-45).** The detector-path pilot waits for the Architect's spec; test partition reserved (D-37).

### 2026-11-19 — D-44 decided: Appendix T T22 recorded (contract E-1.2.20), step 1 of the D-44 instructions done
- Did:
  - **D-44:** decided, option (a). The Architect's C-layer blind review and adjudication protocol is appended verbatim to Appendix T as section **T22**, contract **E-1.2.20**. The CLAUDE.md contract line is updated.
  - D-44 is recorded as decided and CR-027 is closed as superseded by T22, in `DECISIONS_NEEDED.md` and `docs/CHANGE_REQUESTS.md`. Both entries were copied from `v02-review-ui` with their decision, so the two branches agree. Next free numbers on both branches: D-46, CR-028.
  - **T22.13:** `reviewer_assessment.review_time_s · f64 · nullable` added to the schema source (`src/rq1/schema/tables.py`), with its `_null_reason` sibling (section 1.1 rule). Test: `tests/schema/test_t22_review_time.py`, which also pins the annotator, adjudication and validation_status_log fields as unchanged.
  - **Fixtures FX-13 and FX-13a to FX-13f:** generated by `src/rq1/fixtures/records.py`, with the expected values T22 states and a hand calculation in each fixture. `check_fixture` recomputes the T22.8 (b) status mapping and the T22.7 tier and method pairs from each fixture's inputs. Test: `tests/fixtures_t03/test_t22_fixtures.py`, with expected values retyped from T22. Every annotator and assessment row is schema-valid, and the existing VR-E-053 check flags only the FX-13d row. FX-13e's re-adjudication final label (ud) is a fixture input. Its status entry (rejected) follows from T22.8 (b) and (c). The existing fixtures are byte-unchanged.
  - No other code change on this branch. V-02 is built on `v02-review-ui` (steps 2 and 3).
- Tests: 2441/2441 (full suite), twice: identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. D-45 is still open (T-22 STOP), as is CR-026.
- Next: step 2 of the D-44 instructions (merge `m0-implementation` into `v02-review-ui`), then V-02 under T22 on that branch. On `m0-implementation`: **STOP (D-45)**.

### 2026-11-19 — D-46: Appendix T T22.14 recorded (contract E-1.2.21)
- Did: the Architect's CR-028 rulings appended verbatim to Appendix T as **T22.14** (contract **E-1.2.21**); CLAUDE.md contract line updated; D-46 recorded as decided. No code change on this branch: the T22.14 tests belong to the review application on `v02-review-ui`, where the code is. FX-13e is unchanged (the byte-identical fixture regeneration test passes).
- Tests: 2441/2441 (full suite), twice: identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. D-45 still open.
- Next: D-46 items 1 to 3 on `v02-review-ui`; then the D-45 prompt on this branch.

### 2026-11-19 — D-45 decided; T-23 done (tracker adapter)
- **D-45** decided (Owner, with the Architect's detector-path pilot spec): recorded in `DECISIONS_NEEDED.md` and in `research/m1b/zero_shot_probe.md` (rulings section). The seven probe choices are accepted; the probe thresholds become the pilot's fixed values; the 20 probe cameras are excluded from the pilot. T-22 ticked; rows T-23s (S2 stage) and T-25p (pilot) added.
- **T-23:**
  - `trackers` (Apache-2.0) does not install: every release needs numpy ≥ 2.0.2, which breaks torch 2.2.2 in `.venv-det`. Nothing was installed. Following the D-45 fallback, the adapter uses Ultralytics' built-in ByteTrack with the installed `bytetrack.yaml` defaults, recorded in the run configuration.
  - `lap` is not installed, so Ultralytics' NumPy assignment path is used (AR-62 item 5).
  - Code:
    - `src/rq1/tracking/bytetrack.py` (`.venv-det`; one tracker per class; the tracker steps per eligible frame; it logs matched and lost-predicted boxes);
    - `bridging.py` (pure; the D-45 rule at g_max = 15, counted in eligible frames);
    - `s3.py` (main env; `track` / `track_point` rows with `detection_id`; foot point = bottom-centre).
  - The S2 row builder `src/rq1/perception/s2.py` is included because the S3 tests use it; the detector run itself is T-23s.
  - Fixtures: `src/rq1/fixtures/oracle_detections.py`, TEST-ONLY. FX-TRK-1 has dropouts of 5, 15 eligible frames (with an ineligible frame inside), 20 and 40 frames, plus 1 px seeded noise. FX-TRK-2 is a position swap.
  - IDF1: `research/m1b/idf1.py`, a port of TrackEval's Identity metric (TrackEval is not installed; AR-62 item 6).
  - **AR-62** opened (9 items; items 3, 5, 6 and 7 are review flags).
- Tests:
  - 2457/2457 passed, 8 skipped (the ByteTrack unit tests, which run only in `.venv-det`), full suite twice: identical.
  - `.venv-det`: `test_tracking_*` 16/16 and `test_zs_match` OK.
  - New tests in `tests/m1b/`: `test_tracking_bridging.py`, `test_tracking_bytetrack.py`, `test_s3_detector_path.py` (runs the tracker through `.venv-det` and checks the T-12 association: one_to_one, fragment, id_switch; IDF1 toy 0.444444 and swap 0.5 by hand), `test_s2_detector.py`.
- Commit: this entry's commit (pushed)
- Problems / CRs: AR-62 (open, for D-47). One slip, corrected: two test imports of Ultralytics without `YOLO_CONFIG_DIR` created a settings file in the home folder. It was deleted (no prediction ran, nothing was sent), and the adapter now sets the folder before any import.
- Next: T-23s (S2 stage; runtime estimate on one camera before the pilot).

### 2026-11-19 — T-23s done (S2 detector stage); T-25p in progress (S2 run started)
- Did:
  - **S2 stage.** `research/m1b/s2_frames.py` (main `.venv`, PyAV, the S1 decoder) streams the eligible frames of a recording to `research/m1b/s2_yolo_world.py` (`.venv-det`).
    - The detector path is exactly the probe's: YOLO-World v2-s, classes "person" and "forklift", Ultralytics defaults, score floor 0.05.
    - Raw boxes are stored per camera. The D-45 thresholds (person 0.20, forklift 0.05) are applied when `rq1.perception.s2` builds the `detection` artifact (tolerance class; `license_component` row for the weights, AR-62 item 2).
    - The run refuses a dirty source tree and records the code commit.
  - **Runtime estimate** (item 3e; `research/m1b/pilot_runtime_estimate.md`):
    - one camera: 0.378 s per frame (median), 118.5 s wall time;
    - 206 cameras, 61,749 eligible frames: about 6.7 h of detection and about 8 h in all;
    - below 12 h, so no STOP.
  - **Population** (item 3a): 206 cameras (99 ceiling, 107 eye-level) = 226 − 20 probe cameras (`tests/m1b/test_pilot_population.py`).
  - **Pilot code**, committed before the run:
    - `run_pilot.py` (S2 artifact → ByteTrack → S3 → S4 full_camera → S5 BL-2..BL-6);
    - `evaluate_pilot.py` (columns A, B, C; EV-M1/M2 with Target B; per-label O/H/PC; detection; T-12 tracking with IDF1; D-41 position; CM-01/03/08);
    - `frame_check.py` (item 3c: seed 2026111902, 20 pilot cameras).
  - `zero_shot_frames.extract` and `zero_shot_probe.run` gained optional seed, exclusion and output-path arguments; their defaults are unchanged.
  - Smoke run on one camera in a scratch folder (deleted). Finding for the report: ByteTrack's default thresholds (0.25 / 0.1 / new track 0.25) lie above the D-45 forklift threshold (0.05), so many forklift detections never reach a track. Not tuned (D-45 item 4); a descriptive score-band count is added to the evaluation.
  - S2 run over the 206 cameras started in the background (resumable; `out/m1b/pilot/s2_run.log`).
- Tests: 2460/2460 passed, 8 skipped (`.venv-det`-only), full suite twice: identical. The commit of the S2 run scripts (7123f5e) was made after the new test alone, before a full-suite run; the full suite then passed twice on the next commit.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. AR-62 open.
- Next: T-25p (wait for S2; pipeline; frame check; evaluation; report; STOP D-47).

### 2026-11-19 — T-25p done (detector-path pilot); STOP at D-47
- Did:
  - **S2** finished on all 206 cameras. The run stopped at 07:23 after 71 cameras (no error; cause not recorded, probably sleep or throttling) and was resumed at 10:50 under `caffeinate -i`; finished cameras were skipped. S2 commits: `ac40508` (first 71), `533d2ff` (the rest; the only difference is `pilot_report_tables.py`, which no run imports). 6.39 h wall time.
  - **Pipeline** (`run_pilot.py`, S2 artifact → S3 ByteTrack → S4 full_camera → S5 BL-2..BL-6) on all 206 cameras at commit `533d2ff`; 0.58 h.
  - **Frame-level check** (item 3c): 100 frames, 20 pilot cameras, seed 2026111902; YOLO-World forklift recall 0.59, Grounding DINO 0.94 (`research/m1b/pilot_frame_check.json`).
  - **Evaluation** (`evaluate_pilot.py`, columns A/B/C) → `research/m1b/pilot_results.json`; aggregation run twice, byte-identical.
  - **Report** `reports/M1b_pilot_report.md` (tables from `pilot_report_tables.py`). Headline (descriptive): column C recall 0.11 and precision 0.22 at BL-3..BL-6 against B 0.74 / 0.55 and A 0.97–1.00 / 0.94–0.95. Forklift tracking is the bottleneck: tracks on 16 % of forklift-visible frames, IDF1 0.24; 81 % of forklift detections score below ByteTrack's 0.25 start threshold. Nothing tuned (D-45 item 4).
  - `research/m1b/pilot_report_tables.py` committed earlier (`533d2ff`).
- Tests: 2460/2460 passed, 8 skipped (`.venv-det`-only), full suite twice: identical. `.venv-det`: `test_tracking_*` 16/16, `test_zs_match` 7/7.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. AR-62 open (D-47). CR-026 open.
- Next: **STOP (D-47).** Test partition reserved (D-37).

### 2026-11-19 — T-25p report revised (Owner instruction of 19 Nov 2026); STOP at D-47
- Did (report and evaluation code only; no stage re-run, nothing tuned):
  - **Limitations** section added (item 1).
  - **Threshold coupling** (item 2), checked in the installed `ultralytics/trackers/byte_tracker.py` (8.4.215):
    - the low-score second association matches only tracks in the Tracked state (line 448);
    - lost tracks are matched only in the first stage against detections ≥ 0.25 (lines 295, 303, 337);
    - new tracks need ≥ 0.25 (line 500).
    - Stated for both classes; the single-camera ratio dropped.
  - New `research/m1b/tracker_loss.py` (read-only over the stored artifacts) → `pilot_tracker_loss.json`. Bands × reference match × tracked, and frame-level recall per stage: forklift S2 0.61 → tracked 0.16 → with predicted 0.17; person 0.92 → 0.91 → 0.92.
  - **Probe overlap** (item 3): 96 of 206 pilot cameras and 10 of 20 frame-check cameras share a run with a probe camera.
  - **Engineering record** (item 4):
    - The machine went down after 07:23: boot 10:14:47, no clean shutdown recorded, power log silent 07:17–10:35, on battery with a battery-health warning at 07:07. Cause not established.
    - The T23 agent (D-48) is listed as a possible cause of the slow period, next to throttling.
    - S2 runtime split: slow period 7 cameras, 1,502 s.
    - `git diff --stat ac40508 533d2ff` quoted.
    - Re-run time from the S2 artifact onward: about 40 min (measured stages).
  - **Evaluation details** (item 5): stated that A and B are re-aggregated on the 206 cameras with Target B recomputed; IDF1 pooled by summed IDTP/IDFP/IDFN, n printed; position denominators and unscored C points printed (`pilot_report_tables.py`).
  - **Licences** (item 6):
    - The CLIP ViT-B/32 text encoder had **no `license_component` row** in the S2 artifact (its SHA-256 is in the run configuration only). It is added as a record only in `research/m1b/pilot_license_components.json`, because adding it to the artifact would change the S2 artifact IDs.
    - Grounding DINO tiny: row recorded likewise (the frame-level check builds no artifact).
    - `NOTICE.md` "used in" updated; all three files were already listed there.
  - **D-47** rewritten with the revision results. Options (a) exploratory S3-onward re-run with aligned tracker thresholds, reported beside column C, and (b) detector and tracker thresholds fixed as a pair in pre-registration v2 are listed; neither was run.
- Tests: 2465/2465 passed, 8 skipped (`.venv-det`-only), full suite twice: identical. `.venv-det`: `test_tracking_*` 16/16, `test_zs_match` 7/7. New `tests/m1b/test_tracker_loss.py` (5; hand-computed toy case, band boundaries, threshold guard). `tracker_loss.py` run twice: byte-identical JSON. Wording linter on the report: one W4 hit, the disclaimer sentence itself.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new; no item needed a CR. One slip, corrected: importing Ultralytics without `YOLO_CONFIG_DIR` (to locate `byte_tracker.py`) created `~/Library/Application Support/Ultralytics/settings.json` at 16:01. It was deleted with its folder. Only the import ran, with no prediction, so nothing was sent.
- Next: **STOP (D-47).**

### 2026-11-19 — D-47 decided; C', N9 and CR-007 evidence done; STOP at D-50 (opened as D-49, renumbered by the Owner)
- Did:
  - **D-47** recorded; AR-62 marked ACCEPTED.
  - **C'** (item 1). Adapter: `bytetrack.aligned_params` / `cprime_params` and an optional `params_by_class`; without it the configuration equals `default_config()`, so C is unchanged.
    - Driver: `run_pilot.py --cprime`, which reuses C's S2 artifact.
    - Ran on all 206 cameras at `99a1306`: 1,110 s, on mains power, no other agent.
    - Evaluation variant in `evaluate_pilot.py` and `tracker_loss.py --cprime`. After the change, column C's aggregate is byte-identical and one camera's evaluation is equal.
    - Result: BL-6 recall 0.07 against C 0.11. Forklift tracking is worse: fuse_score (default, kept) blocks scores below 0.2 from continuing a track.
  - **N9** (item 3): `n9_pilot.py`, rules 1-3 (FX-ID-8 / AR-42 readings). Rules 4 and 5 not evaluated, and **CR-029** opened. C: 2 tracking, 109 not attributed; C': 1 perception, 1 tracking, 118 not attributed.
  - **CR-007 evidence** (item 2): `cr007_evidence.py`. The forklift error in column B lies along the line of sight (−1.01 m) rather than across it (0.09 m). Added to CR-007.
  - **Operations** (item 5): `pilot_common.DET_ENV` (YOLO_CONFIG_DIR inside the repository) passed to every `.venv-det` subprocess; the frame_check docstring and the s3 detector-path test updated.
    - **Sync check:** the in-repository Ultralytics settings had `sync: false` from 02:13 on 19 Nov (set and asserted by `zero_shot_probe.ultralytics_settings()` before any model load, the path of both the S2 run and the frame-level check). The file was last written at 15:09 with `sync: false`.
    - **Network:** reachable during both runs (power-log network assertions at 06:32; this session online during the frame-level check). Hugging Face telemetry was off. Grounding DINO's `snapshot_download` most likely made a metadata request to huggingface.co (not verified; no project data sent).
    - Nothing in the results changed.
  - **Report:** "D-47 follow-up" section (`d47_report_tables.py`) and a plain-language addendum. Status line updated.
  - **D-50** opened (first numbered D-49; renumbered to D-50 by the Owner to avoid the T23 branch's D-49).
- **Hand-reasoning correction, recorded:** the first version of `test_tracking_bytetrack.py::CPrime::test_cprime_low_score_forklift_starts_but_cannot_continue` expected 10 tracked points. It omitted fuse_score. The test failed against the installed Ultralytics code, and the reasoning was redone from `matching.fuse_score` (line 145) and `byte_tracker.get_dists` (lines 529-531). The expected value became [1, 0, ..., 0], with the reasoning in the docstring, before any pilot run. The expected value comes from the tracker's documented arithmetic, not from the run's output.
- Tests: 2481/2481 passed, 11 skipped (`.venv-det`-only), full suite twice: identical. `.venv-det`: `test_tracking_*` 19/19, `test_zs_match` 7/7. New tests: `test_cprime_rule.py` (4), `test_det_env.py` (3), `test_n9_pilot.py` (5), `test_cr007_evidence.py` (4), `test_tracking_bytetrack.py::CPrime` (3). All D-47 results files written twice: byte-identical; the C' tracker re-run on 3 cameras gave identical output. No settings file in the home folder.
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-029 opened (N9 rules 4 and 5 on the detector path).
- Next: **STOP (D-50).**


### 2026-11-19 — D-50 decided; T-25p CLOSED; extent table; v2 notes; STOP
- Did:
  - **Renumbering (item 0):** the detector-path entry opened as "D-49" at `bbba908` is now **D-50** in `DECISIONS_NEEDED.md`, the report and this log. No D-49 exists on `v02-review-ui` (pushed branch and worktree checked), so nothing there was touched.
  - **T-25p CLOSED (item 1)** as exploratory validation evidence and ticked. Columns A, B, C and C' are unchanged, and no further tracker variant is run.
  - **Extent table (item 2):** `research/m1b/extent_check.py` → `pilot_extent.json`, from stored outputs only, written twice byte-identical.
    - Results: C 141/142 events overlap a same-pair reference (descriptive precision 0.99) and 100/282 references are overlapped (0.35); N4 EV-M1/EV-M2 are 0.11/0.22.
    - 55 of 111 unmatched events have best same-pair IoU ≤ 0.1.
    - 38 of 100 overlapped references span two or more episodes; 4 of 145 episodes carry continuation_of_nk.
    - Report section "D-50" added, plus one addendum bullet on the plain-language page.
  - **Pre-registration v2 notes (item 3):** new `docs/preregistration/v2_notes.md`, collecting D-41, D-47 item 5 (licence rows in S2) and D-50 item 3.
    - Detector and tracker are fixed as one package, including fuse_score.
    - Tuning subset: all cameras of the 13 runs with a probe camera (116 cameras). Reporting on the other 11 validation runs (110 cameras) and on test.
    - The extent / fragmentation question is listed for the Architect. v1 is unchanged.
  - **Architect inputs (item 4):** CR-007, CR-029 and CR-026 marked as pre-registration v2 inputs for the Architect. No rule implemented.
- Tests: 2485/2485 passed, 11 skipped (`.venv-det`-only), full suite twice: identical. `.venv-det`: `test_tracking_*` 19/19, `test_zs_match` 7/7. New: `tests/m1b/test_extent_check.py` (4, hand-computed). `pilot_extent.json` written twice: byte-identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. Wording linter: one W5 hit ("100 interactions") reworded to "100 references"; the remaining two W4 hits quote the disclaimer.
- Next: **STOP.** Not now (D-50 item 5): Grounding DINO on the detector path, fine-tuning (T-24), the test partition (D-37).


### 2026-11-23 — D-53 pre-freeze diagnostics D1–D5 done; STOP at D-54
- Did (evidence only; contract E-1.2.24 unchanged; no rule, parameter or `src/rq1/` change; scripts in `research/m1b/`; on mains power, one agent):
  - **Step 0:** `v2_sets.py` → `v2_camera_sets.json`: tuning 13 runs / 116 cameras (54 ceiling, 62 eye-level), reporting 11 runs / 110 cameras (55 / 55), disjoint. Commit a586133.
  - **Step 1 (D1, D3):** `d1_anchor_angle.py` → `d1_anchor_angle.json` from the stored column B S4.
    - Signed along-sight error −1.35 m (0–15°) to −0.58 m (75–90°). Candidate d = 1.00 m. Residual median 0.15–0.42 m by bin.
    - Estimate within 2 m of the camera: eye-level 12.9 %, ceiling 0 %. Commit d7d5539.
  - **Step 2 (D2):** diagnostic adapter `d2_position_contribution.py`. The unchanged `SubstrateBuilder` takes simulator positions for one class and `full_camera` for the rest, so no S4 code changed.
    - Only position and covariance are substituted; the simulator yaw is removed from the substituted records.
    - Estimate on 2 cameras: 2 s per camera, 125 MB peak. The full run took 3 min (peak 104 MB) at 74e7b0c.
    - Checks: the rebuilt ORACLE-S3 equals the stored one, and the B-tune S4 payload equals the stored column B S4, on all 116 cameras.
    - Artifacts and `execution.json` records are in `out/m1b/v2diag/` (register.jsonl, 696 records).
    - EV-M1 / EV-M2: B-tune 0.793 / 0.505, B-sim-F 0.904 / 0.567, B-sim-P 0.852 / 0.646, A 1.000 / 0.944. Commits 74e7b0c, f6a9261.
  - **Step 3 (D4):** `d4_detector_offset.py` on the stored pilot S2. Covers 96 tuning cameras; the 20 T-22 probe cameras have no S2 run and the detector was not re-run.
    - Signed median −0.84 m. Median paired difference to the oracle box on the same frames: −0.05 m (−0.08 to −0.03 m by bin). Commit dd9cb33.
    - In step 5 a `paired_by_theta` block was added to the JSON; the earlier keys are unchanged (checked).
  - **Step 4 (D5):** `d5_sensitivity_split.py` re-aggregates the stored `posdiag`/`possens` files by camera set.
    - On all 226 cameras it reproduces the stored SDG table exactly. SmartSpaces is copied unchanged.
    - The share of good points lost is also given with error ≤ 1 m: identical to three decimals. Commit ad4981b.
  - **Step 5:** `v2_diagnostics_report.py` → `v2_diagnostics_report.md` (tables per step, 10-line summary, no recommendation). D-53 recorded and **D-54** opened.
- Tests: 2522/2522 passed, 11 skipped (`.venv-det`-only), full suite twice: identical. New tests: `test_v2_sets.py` (3), `test_d1_anchor_angle.py` (5; θ = 0 → 1.515, θ = 90° → 0.565), `test_d2_position_contribution.py` (4), `test_d4_detector_offset.py` (2), `test_d5_sensitivity_split.py` (1), all hand-computed. Every results JSON and the report written twice: byte-identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: none; CR-033 not needed. Wording linter: one W4 hit, the disclaimer sentence.
- Next: **STOP (D-54).**


### 2026-11-23 — D-55 tracker selection on the tuning subset; STOP at D-56
- Did (tracking measures only; no S4, S5, S8 or EV metric; tuning cameras only; columns A, B, C, C′ unchanged; detector as D-45; contract E-1.2.24 unchanged; on mains power, one agent):
  - **Step 0:** tree clean and level with origin at 607c897; 116 tuning cameras loaded.
  - **Step 1:** S2 for the 20 T-22 probe cameras.
    - The S2 configuration IDs equal the pilot's (`inf_cetfxtbdg72cqgfm6teibcxsyd`, `mdl_ty3jrnwz5jjdv56nwtkcos4yqs`).
    - Detector run at 607c897: 108–144 s per camera (first 119.6 s, limit 5 min). Raw output in `out/m1b/pilot/s2raw/` (new files only).
    - `v2_probe_s2.py` built 20 S2 artifacts with the YOLO-World and CLIP licence rows inside them (D-47 item 5). They are in `out/m1b/v2trk/artifacts/`, with 20 execution records in `register.jsonl`.
    - One camera, `rec_ll34ml5evz6l5pz536yifkpcna`, has 2 forklift detections in 300 frames.
  - **Step 2:** `src/rq1/tracking/botsort.py` (BoT-SORT; `with_reid: false`; compensation off with the installed option `gmc_method: none`; same `lap` stub). `src/rq1/tracking/grid.py` is the batch runner; `src/rq1/tracking/s3_config.py` adds `tracker_id`.
    - Adding the field would change column C's configuration ID, so column C keeps its stored configuration (**CR-033** item 1).
    - Keys recorded in `research/m1b/botsort_keys.json`. Commit d94902d.
  - **Step 3:** estimate 13.2 s per camera, 0.43 h for 72 configurations × 116 cameras (limit 6 h).
    - The first version gave negative per-job times from process-start noise; it was fixed with a warm-up process and 5 repeats per job.
    - Commit f55008a.
  - **Step 4:** grid run twice in independent folders (`out/m1b/v2trk/grid/`, `grid_run2/`), 1,531 s and 1,497 s.
    - `v2_tracker_grid.json` (73 rows: column C plus 72) is byte-identical from both runs.
    - Column C's tracker run reproduced the stored column C person and forklift logs on all 96 cameras that have one.
  - **Step 5:** `v2_tracker_select.py` → `v2_tracker_selection.json`.
    - All 72 configurations pass the guards.
    - T1 winner `trc_7flfpx52d2siiljxkqwcorr7nz`. T2 winner `trc_iwm5ndlac27qun2gouwrtoroun` (the same grid point: 0.05/0.05/0.05, fuse_score false, buffer 90).
    - Package = T1, decided at coverage by 1 reference frame (19,981 vs 19,980 of 33,677). Under the secondary reading (CR-033 item 2(b)) the package would be the T2 configuration.
  - **Step 6:** fragmentation for the package and for column C (`v2_tracker_fragmentation.json`).
  - **Step 7:** `v2_tracker_report.md`; one line in `docs/preregistration/v2_notes.md`; D-55 recorded; **D-56** opened.
- Results: forklift IDF1 0.250 → 0.774, coverage 0.160 → 0.593, precision 1.000 → 0.979, person IDF1 0.846 unchanged; package 7 of 112 covered forklift identities have two or more tracks (column C 26 of 66).
- Tests: 2541/2541 passed, 17 skipped (`.venv-det`-only), full suite twice: identical. `.venv-det`: `test_tracking_*` 25/25, `test_zs_match` OK. New tests:
  - `test_tracking_botsort.py` (6: installed defaults except the two switched-off options; hand-built 10-frame two-object fixture tracked identically twice);
  - `test_s3_config.py` (4: column C ID reproduced; a stored S3 artifact rebuilt to the same ID);
  - `test_v2_tracker_select.py` (7: 9-row hand table with a guard failure, a tie in the band and each tie-break; no-pass STOP);
  - `test_v2_tracker_grid.py` (6: hand-computed measures and pool, configurations);
  - `test_s2_detector.py` (+2: licence rows).
  - Every results file was regenerated twice: byte-identical. No settings file in the home folder.
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-033 opened (item 1 `tracker_id` for column C; items 2–4 the readings used, for the Owner). AR-66 proposed. Report status line first named the schema bundle E-1.2.21 as the contract; corrected to E-1.2.24 before commit.
- Next: **STOP (D-56).**

### 2026-11-23 — D-54 / D-56: T24 (E-1.2.25) implemented opt-in; B-v2, C-pkg / C-v2 and person diagnostics on the tuning subset; STOP at D-57
- Did (tuning cameras only; nothing on the 110 reporting cameras or the test partition; columns A, B, C, C′ and their stored artifacts unchanged; no new detection; tracker = the D-56 package only; on mains power after the first check found the computer on battery; one agent):
  - **Step 0:** tree clean and level with origin at ee20291. D-55 at its STOP. First check on battery: stopped and asked; continued on AC power.
  - **Step 1 (1765670):** D-54 and D-56 recorded as DECIDED. CR-007 and CR-026 closed (superseded by T24). CR-033 closed (confirmed as applied). AR-66 accepted. T24 appended to Appendix T verbatim (contract E-1.2.25); CLAUDE.md contract line updated. `v2_notes.md`: T24 candidate values, the package and the ruling-6 caveat, each "selected, not frozen".
  - **Step 2 (91992e2):** T24.4 tests first (`tests/substrate/test_t24.py` 37, `tests/schema/test_t24_schema.py` 9), then the code.
    - The geometry is in `substrate/geometry.py`: analytic s(p) for `full_camera` and for the homography, and the T24.1 centre. The builder in `substrate/builder.py` applies the gate, then the shift, in the T24.3 order.
    - Schema: the four fields carry the new mark `@absent_ok` (AR-67). An absent field writes no Parquet column and enters no hash.
    - Regression: stored S4 of M1a A, M1a B and pilot C rebuild payload- and ID-identical on 96 of 96 tuning cameras that are pilot cameras (`t24_regression.json`).
    - M0 (W-02 method): a clean clone of e6072ef with the T24 source change. Two runs give the 12 IDs and payload prefixes of the M0 report; all 48 exported files equal the unpatched run.
    - Two test-side corrections, recorded in the tests: (1) a hand formula in the builder-level cases used the principal-column formula for off-axis feet; corrected to the off-axis formula `s_hand`, with the T24.4 values unchanged. (2) `test_ar5_config_table_columns` gains `s_max_m_per_px`, the field T24.2 (b) adds.
  - **Step 3 (ad171de; results 4a8b4b7):** `d54_b_v2.py` on 116 cameras (3 min run, 2 min evaluation) → `d54_b_v2_tune.json`.
  - **Step 3b (5bdaa53):** `d54_c_v2.py`. Estimate 0.22 h (limit 3 h); run 12 min, evaluation 5 min → `d54_c_v2_tune.json`. The package's tracker run reproduced the stored D-55 grid measures on 116 of 116 cameras.
  - **Step 4:** `d54_person_position.py` → `d54_person_position.json`.
  - **Step 5:** `d54_report.py` → `research/m1b/d54_report.md`. All five results files were regenerated twice: byte-identical.
- Results (diagnostic, tuning subset, not a reported result):
  - B: EV-M1 / EV-M2: B-tune 0.793 / 0.505; B-T24.2 0.793 / 0.510; B-T24.1 0.926 / 0.568; B-both 0.926 / 0.571; A 1.000 / 0.944. Forklift median error 1.06 → 0.40 m.
  - Detector path: C-pkg 0.526 / 0.333 (CM-03 0.51); C-v2 0.578 / 0.329. On the 96 pilot cameras, column C gives 0.096 / 0.172 (CM-03 0.11).
  - Person median error in column B 0.19 m; median along −0.13 m against a box half-depth of 0.38 m.
- Tests: 2617 passed, 17 skipped (`.venv-det` only), full suite twice: identical. New: `test_t24.py` 37, `test_t24_schema.py` 9, `test_d54_b_v2.py` 10, `test_d54_c_v2.py` 2, `test_d54_person_position.py` 17.
- Commit: this entry's commit (pushed)
- Problems / CRs:
  - CR-034 (T24.2 on `lost` points; reading (a) used): zero lost object-frames on both paths here, so the readings agree.
  - CR-035 (STEP 4 (c) "counterpart"; both readings reported: 15 or 50).
  - AR-67 proposed.
- Next: **STOP (D-57).**

### 2026-11-24 — D-57: rulings recorded; split diagnosis and m_gap sweep on the tuning subset; STOP at D-58
- Did (tuning cameras only; nothing on the 110 reporting cameras or the test partition; pilot columns A, B, C, C′ and the stored D-54 / T-21 artifacts only read, never written; no new detection, no tracker change, N4, label rules and contract text unchanged; one agent):
  - **Step 0:** tree clean and level with origin at c715ac0. The first check found the computer on battery: stopped and asked; continued on AC power.
  - **Step 1 (5615b6a):** D-57 DECIDED. CR-034 closed (reading (a)). CR-035 closed (diagnostic only; both readings stay). AR-67 accepted. `v2_notes.md`: ruling 1 (T24 values kept, frozen with v2) and "no person rule (D-57)".
  - **Step 2 (fd2e3e8):** `d57_split.py` on the stored D-54 outputs of C-v2 and B-both → `d57_split_diagnosis.json`. Check: C-v2 references with ≥ 2 episodes = 69, as in D-54.
  - **Step 3:** `d57_mgap.py`. Estimate 2 s per camera, 0.06 h serial (limit 2 h); sweep 2.5 min with 3 workers → `d57_mgap_sweep.json`. At m_gap 5 the rebuilt S5 payload equals the stored S5 on 116 of 116 cameras for C-v2, B-both and A, and the EV values equal D-54. A shared-reference measure was added after the sweep: it reads the saved sweep artifacts and rebuilds nothing.
  - **Step 4:** `d57_report.py` → `research/m1b/d57_report.md`. All three results files were regenerated twice: byte-identical.
- Results (diagnostic, tuning subset, not a reported result):
  - Splits, C-v2: 115 splits. (i) same POW 43, (ii) POW break 30, (iii) track fragmentation 42. So (ii) + (iii) = 63 %: **most splits on the detector path are not lifecycle splits**, and m_gap cannot join them.
  - Splits, B-both: 87 splits. (i) 81, (ii) 6, (iii) 0.
  - (i) gaps: median 10 frames on C-v2 and 14 on B-both (30 fps). T is 0 on 97 % of gap frames on C-v2, i.e. the clearance is at or above d_p; it is not unknown.
  - Sweep, EV-M1 / EV-M2 at m_gap 5, 15, 30, 60:
    - C-v2: 0.578 / 0.329, 0.607 / 0.410, 0.630 / 0.459, 0.622 / 0.462.
    - B-both: 0.926 / 0.571, 0.889 / 0.702, 0.867 / 0.848, 0.859 / 0.943.
    - A: 1.000 / 0.944, 0.933 / 0.947, 0.933 / 0.947, 0.874 / 0.944.
  - Selection (pre-declared, C-v2): **m_gap 30, selected under D-57, not frozen.** 30 and 60 tie within 0.005; the smaller wins. To be checked against item C7.
  - The oracle check is not clean: at 30, EV-M1 falls on B-both (0.926 → 0.867) and on A (1.000 → 0.933). On A, all 9 lost references share a joined episode with another reference. The references are fixed at m_gap 5 (T21.1, T21.4).
- Tests: 2646 passed, 17 skipped (`.venv-det` only), full suite twice: identical. New: `tests/m1b/test_d57.py` 29.
- Commit: this entry's commit (pushed)
- Problems / CRs: AR-68 proposed (version_label of the non-v1 sweep values; S5 from stored S4; layout; STEP 2 readings; rounding allowance in the selection rule). No CR: nothing undefined changed a count, a state or a statistic of the contract.
- Next: **STOP (D-58).**

### 2026-11-24 — D-59: cap 60 GB; 11 non-duplicate SmartSpaces scenes downloaded and checked; STOP at D-60
- Did (no system run on any data; X0b, the 116 tuning and 110 reporting cameras, the test partition and the D-58 stop untouched; one agent):
  - **Step 1 (699836e):** Owner instruction recorded (D-59; §0 row, cap 60 GB). Qualification Part 5 written before download: same source and revision as Part 1 (`d38193b`, CC BY 4.0); uniqueness from Git-LFS hashes (re-renders have identical ground truth; layouts from `map.png`); 17 candidates in two tiers with every SHA-256 (`part5/candidates.json`); screen rule; tier-2 draw seed 2026112459. CR-036 opened.
  - **Step 2 (0b98265):** screen files of the 17 candidates (51 files, 2.64 GB, 0 mismatches). 11 qualify; 008, 009, 012, 013, 014, 015 have no forklift. All four tier-2 scenes fit; the draw did not bind. Selection recorded before any video download.
  - **Step 3:** 118 videos (18.20 GB, 0 mismatches). Frame counts equal ground truth, constant 33.333 ms, 0 VFR, every camera calibrated (`part5/intervals.json`). Report `research/datasets/part5/d59_report.md` with a proposed testing and tuning plan (not applied). Plan rows T-26d, G-D60, T-26q, T-26r, T-26s, T-26e added.
- Results: tier 1: 7 scenes in 6 new layouts, 45 cameras. Tier 2: 4 new scenarios in `Warehouse_000`'s layout, 73 cameras. Held 51.45 GB of 60 GB.
- Tests: suite run before each commit (2646 passed, 17 skipped). Step 1's run was piped into `tail` without `pipefail`, so the chain would not have stopped on a failure; it passed, and later runs use `pipefail`. No code under `src/` changed.
- Commit: this entry's commit (pushed)
- Problems / CRs:
  - CR-036: how recordings added after the freeze join the split; also `layout_id` and `generation_batch` for the new scenes. S0 registration waits on it.
  - Python `urllib` hung on Hub requests on this machine (no connection opened); the D-59 scripts use `curl` instead.
- Next: **STOP (D-60)**, independent of D-58. T-26q (frame-quality statistics) may run meanwhile.

### 2026-11-25 — D-58: T25 (E-1.2.26) implemented opt-in; stitching selection and event-level check on the tuning subset; STOP at D-61
- Did (tuning cameras only; nothing on the 110 reporting cameras or the test partition; pilot columns and stored D-54 / D-57 / T-21 artifacts only read, never written; no new detection; N4, label rules, EV definitions and the stored base references unchanged; on mains power; one agent):
  - **Step 0:** tree clean and level with origin at d67caf6; mains power. N4 matches S_VIEW **candidate_event** rows in single-camera runs (`research/m1a/evaluate_m1a.py` `system_events`, `rq1.pipeline.m0`), so T25.2 events enter matching without a change: continued.
  - **Step 1 (8d254b6):** D-58 DECIDED. T25 appended to Appendix T verbatim (contract E-1.2.26); CLAUDE.md contract line updated. `v2_notes.md`: m_gap is an event definition in seconds (value from item C7, system and references; D-57 sweep value not a candidate); "T25 adopted; values selected below are not frozen". Records only; committed without a suite run (no code changed).
  - **Step 2 (2f4ad7e):** T25.4 tests first (`tests/substrate/test_t25_stitching.py` 24, `tests/events/test_t25_join.py` 18), then the code: `rq1.tracking.stitching` (T25.1), stitched units in `substrate/builder.py` (S4 pairs stitched identities), `candidates.join_chains` / `joined_events` / `continuity_links` and the T25 branch of `events/s5.py` (T25.2), `engine.m_gap_frames` (T25.3), `stitch` key in `s3_config.trc_id`, three `@absent_ok` schema fields.
    - Regression (`research/m1b/t25_regression.py` → `t25_regression.json`): with the T25 parameters absent, the stored D-54 S4, D-54 S5 and D-57 m_gap 5 S5 of C-v2, B-both and A rebuild byte-identical (payload and artifact ID) on 116 of 116 tuning cameras.
    - M0 (W-02, AR-69 item 11): T25 diff of the M0 files applied to a clean clone of e6072ef with the T24 `@absent_ok` machinery; two runs give the 12 IDs and payload hashes of the M0 report and equal the unpatched run; 46 of 48 exported files equal, the other two are the data dictionary (two new optional properties) and the export manifest that hashes it. The current tree applied whole to e6072ef does not give the M0 S4 ID (it did not before T25 either: post-M0 amendments changed S4); T25 code and HEAD code give identical M0 artifacts.
  - **Step 3 (66809cd):** `d58_stitch.py` → `d58_stitch_grid.json`. 13 configurations, 40 s with 3 workers. Stitching off reproduces the stored D-55 measures on 116 of 116 cameras; a second independent run was identical on 116 of 116.
  - **Step 4 (driver 15f2bf5):** `d58_events.py` → `d58_events_tune.json`. Estimate 2.4 s per camera, 0.08 h serial (limit 3 h); run 3 min with 3 workers. Checks: C-v2 under α equals D-54 and its splits equal D-57 (43 / 30 / 42); the β reference procedure at m_gap 5 reproduces the stored reference S5 and list on 116 of 116; a second independent run gave identical results and artifact IDs on 116 of 116.
  - **Step 5:** `d58_report.py` → `research/m1b/d58_report.md`. All three results files and the report regenerated twice: byte-identical.
- Results (diagnostic, tuning subset, not a reported result):
  - Stitching selected (pre-declared rule): T_s 5 s, r_g 0.5 m, **selected under D-58, not frozen** (largest T_s of the grid). Person IDF1 0.846 → 0.919, forklift 0.774 → 0.780; 77 links (71 person, 6 forklift).
  - EV-M1 / EV-M2, α: C-v2 0.578 / 0.329 → C-v2+T25 0.600 / 0.411. Under α T25.2 joins nothing on any path (join limit 5 frames < the shortest POW-break gap, g_max + 1 = 16 frames).
  - β (m_gap_s 1.0, system and diagnostic references): C-v2 0.653 / 0.438; C-v2+T25 0.677 / 0.525 (21 joined events, 15.6 s unobserved); B-both 0.935 / 0.841, B-both+T25 0.935 / 0.847; A 1.000 / 0.932, A+T25 1.000 / 0.961.
  - CR-037 pair readings (a) and (b) agree on every event.
- Tests: 2695 passed, 17 skipped (`.venv-det` only), full suite twice: identical. New: `test_t25_stitching.py` 24, `test_t25_join.py` 18, `test_d58_stitch.py` 4, `test_d58_events.py` 3.
- Commit: this entry's commit (pushed)
- Problems / CRs:
  - CR-037 opened (contact state, IE and A5.2 pair of a joined event; primary readings applied; STEP 4 is G1 and reports both pair readings).
  - AR-69 proposed (representation of T25).
- Next: **STOP (D-61).** Independent of D-60; T-26q may run meanwhile.

### 2026-11-25 — D-60 STEPS 0–4 (T-26r, T-26s, T-26c) done; STOP at D-62
- Did (D-59 scenes and 2 tuning cameras only; nothing on the 110 reporting cameras or the X0b test partition; no system output on any D-59 scene; frozen detector, tracker package and contract values unchanged; on mains power; one agent):
  - **Step 0:** D-58 at its STOP (D-61); tree clean and level with origin; mains power.
  - **Step 1 (365a80b):** D-60 DECIDED (verbatim). CR-036 closed (ruling 3: addendum X0b-A1). WORKPLAN §0 row D-60. Plan rows T-26r, T-26s, T-26c, G-D62, T-26g; T-26e reworded.
  - **Step 2 (658dbdb, 869fc97, c9b679f):** S0 of the 11 scenes: 11 artifacts, 118 recordings, all calibrated. Video and map SHA-256 equal Part 5. `layout_id` = map.png SHA-256; `generation_batch` = `MTMC_Tracking_2026/<train|val>@d38193b` (AR-70 items 1–2). Tier 1: 45 cameras in 6 layouts; tier 2: 73 in Warehouse_000. S1 (rv2, t17 DCF): 1,063,080 frames decoded, all eligible (tier 1 406,080; tier 2 657,000). Summaries in `research/datasets/part5/s0_d59_summary.json` and `s1_d59_summary.json`.
  - **Step 3 (dbe74a0, 3f4a56e):** X0b-A1 frozen, art_xu3yvoyvpsukx257kmo5p37zxs (spm_dsvquawt4nzul2bmrifqk7e4ye), frozen_utc 2026-11-26T02:00:46Z (outside the hashes, AR-7). 7 leakage groups (one per layout): test_layout_holdout 6 groups / 45 recordings; reserve 1 / 73. X0c art_xi2kr6kyjwy44xvgi6l5t56fyn: 915 edges (111 same_layout, 804 same_session), 0 violations. X0b verified unchanged (payload c01ad60b…); no recording or source file is shared; no tier-1 layout was held before. Re-run identical. Record `docs/preregistration/freeze_record_X0b-A1.json`.
  - **Step 4 (74839be, this commit):** `research/colab/`: `s2_detect.ipynb`, the installable runner `rq1_colab` (pinned Ultralytics 8.4.215, PyAV 19.0.2 and CLIP at 7ffa84b; weight and input SHA-256 checks; S1 eligible frames; s2raw format; resumable per camera; Colab manifest), `equivalence.py` (C1–C3), `make_manifests.py`, `equivalence_manifest.json` (2 videos, 34,708,143 bytes, 600 frames), `tier1_manifest.json` (45 videos, 5,908,702,565 bytes, 406,080 frames) and `HOWTO.md`. Laptop check of the runner on CPU: 6 frames of the stored CPU S2; boxes identical, score differences ≤ 1e-6.
- Tests: 2722 passed, 17 skipped (`.venv-det` only), full suite twice: identical (2721 / 18 before `tier1_manifest.json` existed). New: `test_d60_registration.py` 6, `test_d60_addendum.py` 6, `tests/colab/` 15 (tier-1 manifest test now runs).
- Commit: this entry's commit (pushed)
- Problems / CRs:
  - Order deviation: STEP 3 was frozen while the STEP 2 S1 decode was still running. The freeze reads S0 only, and S1 is not system output, so the split does not depend on it. The order still differs from the Owner's steps.
  - AR-70 proposed (D-60 representation, 9 items). For the Architect: the one-group-per-layout `same_layout` chain is stricter than T14.1 and applies to X0b-A1 only (item 3). PR-01 refuses `test_layout_holdout` and `reserve`, and an R-2 gate for `test_layout_holdout` must be added before T-26e (item 5). The equivalence criteria use the stricter reading in each case (item 6).
  - Slip, corrected: a hand count in `test_one_group_per_layout` left out the `same_layout` edge type of a single-scene layout group. The hand calculation was corrected (recorded in the test); the code was not changed.
- Next: **STOP (D-62).** The Owner runs the 2-camera equivalence check on Colab. T-26g (STEP 5) only on the Owner's word.

### 2026-11-26 — D-61 decided; STEPS 0–1 (T-28r) done; STEPS 2–3 already done under D-58
- Did (records only; no code, no run on any camera; nothing on the 110 reporting cameras or the test partition):
  - **Step 0 (report only):**
    - HEAD fe48352, then fast-forwarded to 713448e (the Owner's Colab edit of `research/colab/s2_detect.ipynb`). The laptop is on battery, not mains.
    - **D-58 STEP 2 is done** (2f4ad7e: T25.4 tests, code, regression, M0). **D-58 STEP 3 is done** (66809cd): `research/m1b/d58_stitch_grid.json` holds exactly the grid D-61 STEP 3 restates, with the same guard, objective and tie rule. It selects T_s 5 s, r_g 0.5 m. Stitching is S3 and does not depend on any value D-61 changes, so STEPS 2–3 are not re-run.
    - **Frame rates (declared stream rate of every held video):** SDG 690 / 690, SmartSpaces synthetic 156 / 156 (D-59 scenes included) and SmartSpaces real 026/027 11 / 11 are all 30 fps. **Safe and Unsafe Behaviours: 0 of 371 are 30 fps** (21.53–25.25 fps, median 24.83, mostly variable-rate). So "all held data is 30 fps" does **not** hold. Every recording that D-61 STEPS 3–6 touch is 30 fps, so m_gap_s 1.5 s → 45 frames and g_max 45 frames ↔ 1.5 s there. Off 30 fps the two g_max readings differ: **CR-038**.
    - **σ on the detector path** (stored D-54 C-v2 S4 / S5, 116 tuning cameras):
      - `speed_sigma_mps` is non-null on 103,153 of 104,260 object states. It is the T9.1 fit's standard error (`kinematics.Fit.speed_sigma`), not a position σ.
      - `pos_cov_m2`, σ_c (`clearance_sigma_m`) and `minclr_sigma_m` are null on every row (0 of 104,260 / 37,120 / 450).
      - So `clearance_within_k_sigma` cannot fire (it fires 0 times). **`speed_near_v_min` does fire:** on 313 of 450 C-v2 episodes, and on 426 of 649 B-both episodes.
      - k_σ is therefore inert for clearance and contact, but **not** for the speed borderline flag. D-61 §4 limitation 5 needs this correction.
      - Borderline flags never change a label, a frame flag or review_route (T10.4, T11.1).
    - **Routing:**
      - **T23 manager review** (T23.2 a, v02-review-ui only) takes episodes of `wf_source_config` (default BL-6) whose G2 label is NM, UD or CT. CT makes an incident draft; otherwise it is a near-miss report. **O, H, PC and IE never create a report**, so an O episode never reaches a manager, not even in the OI-1 case.
      - The separate **`review_route` flag** (E-1.2.1 §6; `events/labels.py`) is set when contact ∈ {undetermined, suspected} or the episode carries NM, UD, CT or IE. An O episode is therefore routed in the OI-1 case (overlap, no X or C), **and also whenever it carries IE**.
      - Stored C-v2: of the routed O episodes, 2 are OI-1 overlaps (undetermined, no IE, minclr −0.77 and −0.24 m), and 14 carry IE (undetermined 5, not_assessable 8, none_observed 1). B-both: 3 routed O episodes, all not_assessable with IE.
      - So **"an O episode is routed only in the OI-1 case" is not confirmed** for `review_route`. It holds for T23 in the stronger form: O is never routed to managers.
  - **Step 1:** D-61 DECIDED. §1 verbatim in `docs/preregistration/v2_notes.md`, and §2–§4 verbatim in the D-61 entry (headings demoted one level). Plan rows T-28r, T-28e, T-28f, T-28t added.
- Tests: not run (records only, no code changed).
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-038 opened (g_max off 30 fps; no effect on any D-61 step).
- Next: T-28e (D-61 STEP 4): runtime estimate on 2 cameras, then the diagnostic event check.

### 2026-11-26 — D-61 STEPS 4–6 (T-28e, T-28f, T-28t): diagnostic event check, pre-registration v2 frozen, test readiness prepared; STOP at D-63
- Did (nothing on the 110 reporting cameras or the test partition beyond reference building from simulator truth and the X0c audit, both allowed by D-61; no S2 anywhere; N4, label rules, EV definitions, v1 records and stored artifacts unchanged; on battery power; one agent):
  - **Step 4 (5e95a2b driver, 226ea7b results):** `research/m1b/d61_events.py` → `research/m1b/d61_events_tune.json`. Values come from `research/preregistration/v2_values.py` (§1.3–1.5).
    - Estimate: 9.65 s per camera, 0.31 h serial (limit 3 h). The run took 32 min of camera time with 3 workers.
    - Checks, 116 of 116 each: the tracker re-run reproduces D-55 (both classes); the detector S3 at g_max 15 equals the stored D-54 S3; the rebuilt reference S3 equals T-21.
    - The diagnostic v2 tuning reference set is in `out/m1b/d61/reference_diag/`, apart from STEP 5. It holds 116 references, all assessable G1.
  - **Results (diagnostic, tuning subset, not a reported result; synthetic-data evaluation):**
    - C-v2+T25: EV-M1 / EV-M2 **0.733 / 0.620** (85 of 116 references; 85 of 137 events). Ceiling 1.000 / 0.771; eye level 0.500 / 0.463.
    - A+T25: **1.000 / 0.975** (116 of 116; 116 of 119 events).
    - CR-037 readings (a) and (b) agree on every event.
    - **n_members 1 on every event; joined events 0; unobserved_gap_s 0.** T25.2 cannot join under v2: a POW break needs a gap of more than g_max = 45 frames, so at least 46 frames (1.53 s), while the join limit is m_gap_s 1.5 s.
    - Remaining splits are mechanisms (i) / (ii) / (iii): C-v2+T25 1 / 12 / 18; A+T25 0 / 3 / 0. The (ii) splits (same units, other POW) are the ones T25.2 was meant to join.
    - **IE share** (IE events / all S_VIEW events): C-v2+T25 0.788 (108 / 137) at g_max 45 against 0.723 (102 / 141) at g_max 15, every other value v2, so **+0.065** comes from g_max. A+T25 0.773 at both g_max values (+0.000).
    - Stitching: 77 links at g_max 45.
  - **Step 5:**
    - Freeze time taken once: **frozen_utc 2026-11-26T14:29:25Z** (`rq1.pipeline.prereg_v2`). Analysis commit **226ea7b**.
    - v2 references (`research/preregistration/v2_references.py`) for SDG, built from simulator truth at the v2 values with T25.2 off: tuning 116 cameras / 116 references; reporting 110 / 110; test 471 / 473 (471 assessable G1). A second independent build gave identical IDs and payload hashes on 697 of 697 cameras.
    - `docs/preregistration/freeze_record_v2.json` (`freeze_v2.py`): built twice, byte-identical (SHA-256 6f7ca439…). It holds the configuration IDs:
      - detector: inf_/mdl_ IDs and weight hashes;
      - tracker: package trc_7flfpx52; g_max 45 trc_osh5tvmg; with T25.1 trc_y7gue6tdq;
      - substrate sbc_5h5zcuzay…, geometry, rules (system BL-6 rcf_2bvkpre4…, reference rcf_rtzb7byu…), and evaluation configurations per set and iou_m;
      - the v2 criteria (new acc IDs, targets unchanged) and the reference sets.
    - `docs/preregistration_v2_FROZEN.md`: v1 structure; §4 = D-61 §1.1–1.5; §8 / §9a = §1.6 / §1.7 verbatim; limitations with the STEP 0 findings.
  - **Step 6 (`readiness_v2.py` → `docs/preregistration/test_readiness_v2.json`):**
    - X0c of X0b v1: art_2wiixxn5g34mcsiqvmurotacuz, 3,411 same_session edges, 0 violations, audit_complete — **pass**.
    - Windows lockable: 471 windows, with a proposed lock_sha256 per window in `window_lock_proposal_v2.json`; nothing locked — **pass** (definition pending, AR-71 item 11).
    - Freeze record reproducible — **pass**.
    - Test run IDs and hashes equal X0b v1 (48 runs, 471 cameras = V0 m1a-sdg-test = the v2 test reference set) — **pass**.
    - Weights hashed (YOLO-World, CLIP equal published; ByteTrack loads no weights) — **pass**.
    - Licence rows (SDG dataset, YOLO-World, CLIP verified; software libraries have no rows, listed) — **pass**.
    - Colab estimate — **open**: CPU 0.388 s per frame × 141,300 frames ≈ 15.2 h; Colab GPU time not measured (D-62 pending).
- Tests: 2740 passed, 17 skipped (`.venv-det` only), full suite twice: identical. New: `test_d61_events.py` 10, `test_v2_references.py` 6, `test_prereg_v2.py` 2.
- Commit: 5e95a2b, 226ea7b, this entry's commit (pushed)
- Problems / CRs:
  - CR-039 opened: no SmartSpaces v2 references; the T21 amendment promised in D-40 item 3 does not exist; tier 1 is blocked.
  - AR-71 proposed (11 items).
  - The T25.1 selection was made at g_max 15 (D-58 STEP 3 as written) and runs at g_max 45 in v2.
  - The `test_readiness` module was renamed to `readiness_v2.py` before its first commit, so that pytest does not collect it.
- Next: **STOP (D-63).** D-62 (Colab) is still open and independent.

### 2026-11-26 — D-63 decided; STEPS 0–2 (T-29r, T-29a): state check, records, rationale addendum
- Did (no system stage run; nothing on reporting or test; frozen files unchanged: `preregistration_v2_FROZEN.md` SHA-256 906aea9a…, `freeze_record_v2.json` 6f7ca439…):
  - **STEP 0 (report only):** HEAD 309408d on m0-implementation, tree clean. D-62 OPEN. `out/colab/equivalence/` present (placed by the Owner): `colab_manifest.json` complete, 2 of 2 cameras, 600 frames, Tesla T4, CUDA 13.0, torch 2.14.1+cu130, ultralytics 8.4.215, av 19.0.2, runner commit 713448e, wall time 27.9 s.
  - **STEP 1:** D-63 DECIDED with §1 verbatim; CR-038 DECIDED (reading (b), implementation deferred); CR-039 DEFERRED; AR-71 ACCEPTED (items 1–10; item 11 as the lock definition). WORKPLAN §0 row for the D-63 cloud upload (reporting and test videos; rulings 7–8, STEP 4). Plan rows T-29*. `research/v2/reporting_plan.md`: order, tables, limitations (no separate v2 reporting-plan file existed; the tables and order were in the frozen §8 / §9a, which is not edited).
  - **STEP 2:** `docs/preregistration/v2_rationale_addendum_D63.md` (§3 verbatim); its SHA-256 and commit time in `docs/preregistration/v2_addendum_record.json` (next commit).
- **Limitations (v2), added under D-63** (beside the 15 in `preregistration_v2_FROZEN.md` §10):
  16. **T25.2 is inert under v2** (ruling 2): with g_max = m_gap_s = 1.5 s a POW break needs a gap above 1.5 s and a join one ≤ 1.5 s, so no join can occur. T25.1 stitching handles a changed ID; every gap ≤ 1.5 s is bridged; every longer gap separates two encounters by definition. The code stays; `join_across_pow` stays true. Stated in the methods text.
  17. **T_s = 5 s is the top of the stitching grid** (ruling 3): longer gaps were not tried. The selection (IDF1 on S3 points) does not depend on g_max.
  18. g_max means 1.5 s (CR-038 (b)); 45 frames on every v2 recording.
  19. SmartSpaces event-level results are excluded from this submission (CR-039 deferred).
- Tests: see the STEP 2 commit (documents only).
- Commit: this entry's commit (pushed)
- Problems / CRs: none.
- Next: T-29a record, T-29l (window lock).

### 2026-11-26 — D-63 STEPS 2–4 (T-29a, T-29l, T-29q): addendum record, window lock, D-62 PASS, Colab job `reporting_test`; STOP at D-64
- Did (no S2 or later system stage run; nothing opened on reporting or test outputs, none exist from v2; frozen files unchanged):
  - **STEP 2 (39fe80f):** `docs/preregistration/v2_addendum_record.json`: addendum SHA-256 43e937e5…, commit e70f28b, 2026-11-26T15:43:35Z, after the v2 freeze (14:29:25Z), before any v2 reporting or test S3 output. It discloses the stored pilot S2 and v1 S3–S5 on the reporting cameras (below).
  - **STEP 3 (a079afb code, 37052b6 record):** `research/preregistration/lock_v2.py`. The new V0-stage lock artifact **art_venollyxzeuqvumbo7jow2vtjt** (payload c1b7a2d8…) holds V0's plan row and the 471 windows of `m1a-sdg-test`: `annotation_status = locked`, `locked_utc` 2026-11-26T15:47:13Z, `lock_sha256` per AR-71 item 11. Inputs: V0 and the 471 v2 test reference S5.
    - Built twice: ID, payload and file hashes identical. 471 of 471 hashes equal the D-61 proposal.
    - V0 is unchanged (manifest bytes and reconstruction). VR-E-054 passes on the locked rows.
    - Record: `docs/preregistration/window_lock_v2.json`. AR-72 proposed.
  - **STEP 4:** D-62 DECIDED, **PASS** (`research/colab/equivalence_result.json`). Hashes all equal. C1: 0 unmatched. C2: P99 ≤ 1.43e-5. C3: counts equal. Frames equal.
    - Colab job `reporting_test`: `make_manifests.py reporting_test` → `research/colab/reporting_test_manifest.json` (581 videos, 9.51 GB, 174,140 eligible frames; every video re-hashed against its S0 row).
    - The notebook accepts the job (3-line change). HOWTO section "D-63": upload size, Drive space, about 2.3 h on a T4, the tier-1 skip note. Upload links staged.
  - **Finding: the D-63 stop item 5 was wrong.** Stored CPU S2 exists for all 110 reporting cameras (T-25p pilot), with the frozen v2 S2 IDs (110 of 110) and frame lists equal to S1 (110 of 110). Raised at D-64 as option (a); the reporting run is not started.
- Tests: 2746 passed, 17 skipped (full suite twice, identical). New: `tests/m1a/test_window_lock_v2.py` 5; `tests/colab/test_package.py` + 1 (`reporting_test`).
- Commit: 39fe80f, a079afb, 37052b6, this entry's commit (pushed)
- Problems / CRs: AR-72 proposed (lock representation). T-26g deferred (D-63 ruling 5).
- Next: **STOP (D-64).** The Owner chooses (a) or (b) and runs Colab.

### 2026-11-26 — D-64 decided (option a); T-29m: test-only Colab manifest
- Did (no S2 or later stage run; no reporting or test output opened; frozen files unchanged):
  - D-64 DECIDED, option (a): the reporting run (STEP 5) uses the stored CPU S2 of the 110 reporting cameras; Colab runs test only.
  - `make_manifests.py test` → `research/colab/test_manifest.json`: 471 videos, 7,703,586,524 bytes (7.70 GB), 141,190 eligible frames, decision D-64; the cameras are the test set of `reporting_test_manifest.json` entry for entry (videos re-hashed against S0). `reporting_test_manifest.json` unchanged.
  - `stage test` builds hard links in a new folder `out/colab_upload_test/rq1_colab/data/` (441 + 30), so the upload holds test videos only. Notebook accepts `JOB = "test"`. HOWTO section "D-64": about 8.1 GB Drive space, about 1.8 h on a T4; `reporting_test` marked "do not run".
- Tests: 2747 passed, 17 skipped (full suite twice, identical). New: `tests/colab/test_package.py` + 1 (`test`).
- Problems / CRs: none. Engineering only (job name, folder), set by the Owner's decision; no AR.
- Next: T-29p (STEP 5, reporting run from the stored CPU S2), independent of the Owner's Colab test run. T-29h waits for `out/colab/test/`.

### 2026-11-27 — T-29h (D-63 STEP 6): test S2 arrival verified by hashes; outputs not opened
- Did (no S3 or later stage run; no test output decompressed, parsed, counted or summarised, D-63 ruling 8):
  - The Owner returned the Colab job `test` in `out/colab/test/`: 471 `.json.gz`, 471 `.done.json`, `colab_manifest.json`, `pip_freeze_610ff296df3f.txt`.
  - New `research/colab/arrival.py`. It reads only the runner's bookkeeping (sidecars and manifest: hashes, sizes, frame counts, environment) and the raw bytes of each output for SHA-256. Checks: job name; `job_manifest_sha256` equals SHA-256 of `research/colab/test_manifest.json` (f9fc3a4b…); manifest complete (471 of 471); weights SHA-256 equal to the job's detector block; output, sidecar and manifest sets equal the job's 471 cameras, no extras; per file, the hash and size in the sidecar and the manifest equal the file, frame count equals the job's `n_eligible`, input video hash equals the job.
  - Result: **PASS, 471 of 471, no problems.** Runner commit 610ff29, Tesla T4. Record: `docs/preregistration/test_s2_arrival_v2.json` (colab_manifest SHA-256 807d46b9…, 471 output hashes).
- Tests: new `tests/colab/test_arrival.py` 10 (clean pass; a guard that fails if any gzip read happens; 8 defects each fail). Full suite at 610ff29 plus these files: 2751 passed, 17 skipped, 6 errors in `tests/pipeline/test_m0.py` (see Problems). Re-run twice at 40e4170 (this entry's commit): 2757 passed, 17 skipped, both runs identical; the 6 errors are gone with the new commit hash (CR-040).
- Commit: 40e4170, this note's commit (pushed)
- Problems / CRs: **CR-040.** The M0 fixture IDs include the HEAD commit. At 610ff29 the derived ID `exp_ppb4v7enmipxsy2zp7jjoshaf5` contains the substring `osha`, so the VR-E-041 value scan (`obx.check_content`) rejects the fixture export (6 errors). The failure depends on the commit, so the T-29m run (made before its commit) did not see it. This is a latent defect: a substring scan over random base32 IDs. Not fixed: exempting IDs from VR-E-041 changes how a contract rule applies.
- Next: T-29p (STEP 5, reporting run from the stored CPU S2). T-29t then waits only on T-29p.

### 2026-11-27 — CR-040 DECIDED and implemented (VR-E-041 skips generated-ID hash bodies)
- Did: Architect ruling, Owner-approved (27 Nov 2026), reading (a) narrowly. `src/rq1/export/obx.py`: `GENERATED_ID` (`^([a-z0-9]{2,4})_[a-z2-7]{26}$`); `_strings` yields only the prefix of a whole value in that format, so its base32 hash body is not scanned. Field names, free text, labels, notes and all other values are scanned as before. No other rule changes; no frozen v2 value or result touched.
- Tests: `tests/export/test_obx.py` + 9 (`test_cr_040_*`: the 610ff29 ID `exp_ppb4v7enmipxsy2zp7jjoshaf5` passes; "osha" in `summary_label`, in a `*_null_reason` free-text field, in non-ID-format values (wrong body length, non-base32 character, ID plus text, fragment in the prefix) and in an ID-shaped field name each still fails). Full suite twice: 2766 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-040 DECIDED.
- Next: T-29p (D-63 STEP 5, reporting run), then T-29t (STEP 7, test run).

### 2026-11-27 — T-29p part 1 (D-63 STEP 5): v2 partition runner, aggregation and report; verified on the 116 tuning cameras; CR-041
- Did (nothing run on the reporting or test cameras):
  - `research/v2/run_v2.py`: per camera, column A (ORACLE-S3 g_max 45 → S4 simulator_truth → S5 BL-2..BL-6, T25.2 on), B (same S3 → S4 full_camera T24 → S5 BL-2, BL-3, BL-6), C (stored S2 → D-56 tracker package re-run → bridged g_max 45 → T24 floor → T25.1 stitched S3 → S4 full_camera T24 → S5 BL-2, BL-3, BL-6). Label "preregistration-v2". It stops on a camera unless every configuration ID equals the freeze record, the stored v2 reference (S5 ID, payload and list hash) equals the freeze record, the person tracker re-run reproduces the stored pilot log (where one exists), and every event has one member with equal CR-037 readings (limitation 16). Scored against the frozen v2 references, N4, G1, iou_m 0.3 / 0.5 / 0.7. GV-01 and GV-07 on B and C (availability by null reason), GV-04 as revised by D-40 item 4 (simulator positions), IE share, borderline-flag counts, exact-class artifact IDs and hashes (MR-01). `test` refused (T-29t).
  - `research/v2/aggregate_v2.py` (Target A / B intervals, B 2,000, seed 2026111402; T11.2 paired comparisons; registered criteria through `fitness.decide_criterion`) and `research/v2/report_v2.py` (the D-61 §1.6 tables).
  - **Verification on the 116 tuning cameras** (development output `out/v2/dev/`, diagnostic, not a reported result): BL-6 EV counts at iou_m 0.3, IE share and stitch links equal the D-61 STEP 4 results on 116 of 116 cameras for both the detector path (C-v2+T25) and the oracle path (A+T25); configuration IDs equal the freeze record 116 of 116; references equal 116 of 116; person tracker log reproduced 96 of 96 (the 20 probe cameras have no stored pilot log); GV-04 recomputed prior clearance equals the stored clearance on 30,548 of 30,548 pair-frames; MR-01 repeat 1.0 (116 of 116 digests equal). Runtime about 15 s per camera.
  - Found and fixed during development (before any reporting output): GV-04 first used the pre-D-40 definition (full_camera positions); now the D-40 item 4 definition.
- Tests: new `tests/m1b/test_run_v2.py` 9, `tests/m1b/test_aggregate_v2.py` 6 (hand values). Full suite twice: 2781 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: **CR-041** (open): registered-criterion slice is test (reporting prints "not the registered decision"); no paired-comparison decision rule exists (differences and intervals only); no GV-07 outlier cut (median and P95 only). Presentation only; no number depends on it.
- Next: T-29p part 2: the reporting run, once, from this commit.

### 2026-11-27 — T-29p part 2 (D-63 STEP 5): reporting run once; detector-path defect found (CR-042); STOP at D-65
- Did: `run_v2.py run reporting 3` from the clean commit d20fb82 (110 / 110 cameras, no stop), `repeat reporting 3` (MR-01), `aggregate_v2.py reporting` (built twice, byte-identical) and `report_v2.py reporting` → `research/v2/reporting_results.json`, `research/v2/reporting_report.md`. Checks: configs equal the freeze 110 / 110; references 110 / 110; person tracker log reproduced 110 / 110; MR-01 1.0; GV-04 prior check 29,173 pair-frames, 0 mismatches.
- **Defect (CR-042):** while checking `speed_near_v_min` (oracle 97 of 110 episodes, detector 0 of 142, against 313 of 450 at D-61 STEP 0) I found that the S5 providers look up object states by the pair unit ID; on the stitched detector path the pair units are `sti_` IDs and the object states `trk_` IDs, so 0 of 19,750 detector-path pair-frames find either object's state. Column C (headline) has M unknown everywhere, no R4 speeds, no R5 or contact-cue input. Columns A and B are correct. The D-58 / D-61 tuning diagnostics share the defect. The report carries a defect banner; nothing in it was edited.
- Not affected and recorded in D-65: MR-01 met; A and B BL-6 EV values; GV-01, GV-07, GV-04 on B (not the registered decision: slice test, CR-041; not_assessable: 11 groups < 20).
- Tests: full suite twice before this commit: 2781 passed, 17 skipped in 65.26s (0:01:05); 2781 passed, 17 skipped in 62.69s (0:01:02).
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-042 (open), D-65 (open). T-29p BLOCKED; T-29t blocked by it.
- Next: **STOP (D-65).** Nothing else on this branch is independent of it.

### 2026-11-27 — D-65 decided (a); CR-042 fix (reading 1), guard, tuning verification; AR-73
- Did (nothing run on the reporting or test cameras in this entry):
  - D-65 DECIDED (a) and CR-042 DECIDED (reading 1) recorded. **AR-73** proposed: S5 gets the stitch membership from the stitched S3 (`providers.stitch_members`; `s5.build(..., members=)`; `S4Index(..., members=)`), and the S5 spec lists that S3 as an input. Rate runs are prepared per member track, so no window spans a stitch. S4 unchanged.
  - Run guard in `research/v2/run_v2.py` (`m_input_check`, `M_MISSING_MAX` 0.05): STOP if, on any column and R2 baseline, M is unknown on more than 5 % of pair-frames where both objects have a stored state (found from the S3 points, independently of S5) and the forklift speed is known.
  - `research/m1b/d61_events.py` passes the membership (output now `out/m1b/d61_cr042/`, `research/m1b/d61_events_tune_cr042.json`; the defective `out/m1b/d61/` and `d61_events_tune.json` are kept).
  - The re-run is the partition `reporting_rerun` (same 110 cameras and references; `out/v2/run/reporting_rerun/`, `research/v2/reporting_rerun_*`), with the D-65 disclosure in the results and the report.
  - **Tuning verification** (116 cameras, `out/v2/dev/`, diagnostic; the defective dev run is kept in `out/v2/dev_defective_cr042/`): the guard passes, M unknown on 0 of 30,548 (A, B) and 0 of 20,272 (C) pair-frames with both states. Against the defective dev run: every A and B artifact payload identical (812, 464), C S3 and S4 identical (348), C S5 changed on 313 of 348. C|BL-6: EV-M1 0.733 and EV-M2 0.620 unchanged; IE share 0.788 → 0.759; `speed_near_v_min` 0 → 117 episodes.
- Tests: new `tests/substrate/test_cr042_stitched_states.py` 4 (membership; a stitched pair-frame with member state gets an M input, and the defect gives none; every object-state input equals the member's own frame by frame, `closing_rate` being the S4 pair-series value; no rate run spans the stitch on adjacent members); `test_run_v2.py` + 1 (guard), `test_aggregate_v2.py` + 1. Full suite twice: 2787 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed). The reporting re-run and the D-61 re-production run from it.
- Problems / CRs: AR-73 proposed.
- Next: reporting re-run (all 110, once, this commit), MR-01 repeat; D-61 STEP 4 re-production; mark d58/d61 superseded; then T-29t.

### 2026-11-27 — T-29p done (D-63 STEP 5, D-65 a): reporting re-run once at 107f14b
- Did: `run_v2.py run reporting_rerun 3` (110 / 110, no STOP) and `repeat reporting_rerun 3`, both at 107f14b; `aggregate_v2.py reporting_rerun` (built twice, byte-identical); `report_v2.py reporting_rerun` → `research/v2/reporting_rerun_results.json`, `research/v2/reporting_rerun_report.md`, with the D-65 disclosure (first run defective and why; A and B numbers, and the defective C numbers, seen before the re-run). The first run stays on record (`reporting_results.json`, `reporting_report.md`, warning banner).
- Checks: configs equal the freeze 110 / 110; references 110 / 110; person log 110 / 110; CR-042 guard: M unknown on 0 of 29,159 (A, B) and 0 of 19,211 (C) pair-frames with both states; GV-04 prior check 29,173, 0 mismatches; **MR-01 1.0 (C1-MR-01 met)**.
- Results (synthetic-data evaluation, experimental; candidate events): headline C|BL-6 at iou_m 0.3: EV-M1 0.736 (Target B [0.636, 0.827]), EV-M2 0.570 ([0.480, 0.672]); ceiling EV-M1 0.964, eye_level 0.509. Decomposition: A EV-M1 0.991 / EV-M2 0.991; B 0.982 / 0.973. GV-01 (B) RMSE ceiling 0.468 m, eye_level 0.573 m; GV-07 (B) 0.817 m/s; GV-04 0.000 (circular). C2–C4: not the registered decision (slice test, CR-041), not_assessable (11 groups < 20).
- Against the first run: A and B EV tables and all GV identical; C EV-M1 / EV-M2 unchanged; C|BL-6 IE share 0.768 → 0.697; `speed_near_v_min` on C|BL-3 / BL-6 0 → 116 episodes.
- Tests: full suite at 107f14b twice (previous entry). This commit adds results and records only.
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-041 open (presentation); AR-73 proposed.
- Next: D-61 STEP 4 re-production (running), mark d58 / d61 superseded; then T-29t (test run).

### 2026-11-27 — D-65 follow-ups done; T-29t part 1 (D-63 STEP 7): gated test path, test S2 builder, verified on validation; AR-74
- Did (nothing opened, built or run on the test partition in this entry):
  - **D-61 STEP 4 re-produced with the CR-042 fix** (diagnostic, selects nothing), from 107f14b: `research/m1b/d61_events_tune_cr042.json`, artifacts `out/m1b/d61_cr042/`. Checks 116 / 116 (reference S3 equals T-21; tracker reproduces D-55 for both classes; detector S3 at g_max 15 equals D-54). C-v2+T25 EV-M1 0.733, EV-M2 0.620 (unchanged); IE share at g_max 45 0.788 → 0.759; A+T25 unchanged. Disclosure: while it ran, `research/m1a/m1a_common.py` gained `load_for_test_run` (an added function only; nothing the run calls changed).
  - `d58_events_tune.json` and `d61_events_tune.json` marked superseded as defective (CR-042) with a `superseded` field; files kept, no other byte changed.
  - **Test path** (D-63 STEP 7): `research/v2/test_access.py`: `gate()` reads the committed records (X0c pass with 0 violations; lock artifact verifies and equals `window_lock_v2.json`, 471 / 471 locked; reporting re-run 110 cameras with MR-01 1.0; test S2 arrival pass, 471) and refuses otherwise; `CameraView` builds the camera fields from truth with the locked windows. `m1a_common.load_for_test_run(ctx, rec, gate)` is the only test loader for system stages (refused without a full gate; refused for non-test cameras). `run_v2.py`: partition `test` opens only through the gate; S2 built from the sealed Colab file (hash equal to the arrival record; weights, eligible frames and size checked) by `s2_from_raw`; **AR-74**: the inference record names the device that ran it (`cuda (Tesla T4, Colab)`), model ID unchanged.
  - **Verified on validation data only:** `s2_from_raw` reproduces the stored pilot S2 artifact ID from its raw output on 5 / 5 cameras; the truth-built `CameraView` (V2RUN_VIEW=fresh) gives results identical in every field to the stored-view dev run on 116 / 116 tuning cameras (`out/v2/dev_freshview/`).
- Tests: new `tests/m1b/test_test_access.py` 2; `test_run_v2.py`: `test_partition_guard_refuses_test` replaced by `test_partition_guard` (D-63 STEP 7 opens `test` through the gate; the refusal is now the gate's, tested in `test_test_access.py`) and `test_test_inference_differs_only_by_device` added. Full suite twice: 2790 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed). The test run runs from it.
- Problems / CRs: AR-73, AR-74 proposed; CR-041 open.
- Next: T-29t part 2: the test run, once, from this commit; MR-01 repeat; tables; STOP (next D).

### 2026-11-27 — T-29t part 2 (D-63 STEP 7): test run once, 471 cameras, from f5e7d28; MR-01 1.0; STOP at D-66
- Did: the test partition ran once through the D-63 STEP 7 gate (all four items held), S3–S8 with the frozen v2 configuration, from commit f5e7d28 (the CR-042 fix commit line; nothing changed between that commit and the run). The first camera was run alone as a smoke check (its numbers were not looked at) and was skipped by the full run, which did the other 470. MR-01 repeat: 471 / 471 re-run, 0 differing. `aggregate_v2.py test` run twice: byte-identical `research/v2/test_results.json`; `research/v2/test_report.md` rendered from it.
- Checks: configuration IDs equal the freeze record 471 / 471; references equal 471 / 471; M-input guard 0 missing on every column (A, B 124,741 pair-frames with both states; C 83,524); GV-04 prior mismatches 0; 288 stitch links.
- Results (synthetic-data evaluation; experimental; candidate events): headline C|BL-6, iou_m 0.3: EV-M1 0.752 (Target B [0.689, 0.806]), EV-M2 0.619 ([0.577, 0.660]); ceiling 0.932 / 0.725, eye_level 0.572 / 0.500. A|BL-6 0.989 / 0.957; B|BL-6 0.983 / 0.935. Registered criteria (48 leakage groups ≥ 20): C1-MR-01 met; C2-GV-01 ceiling 0.434 m [0.407, 0.463] not_met; C2-GV-01 eye_level 0.775 m [0.685, 0.862] not_met; C3-GV-07 0.939 m/s [0.826, 1.041] not_met; C4-GV-04 met (circular, not evidence).
- Tests: no code change. Full suite twice: 2790 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed).
- Problems / CRs: AR-73, AR-74 proposed; CR-041 open.
- Next: STOP at D-66 (nothing on this branch is independent of it).


### 2026-11-27 — D-66 recorded; T-29u part 1: IE-input diagnostic code (post hoc, tuning only)
- Did: D-66 recorded (option a; the test partition is closed). CR-041 DECIDED (readings a, a, a as applied); AR-73, AR-74 ACCEPTED. Tasks T-29u (diagnostic) and T-29w (write-up) added. `research/v2/ie_inputs_diag.py`: per tuning camera, reads the stored dev-run S4 (and, on C, the stitched S3) with verified IDs, recomputes the S5 per-frame inputs as `s5.build` does (frozen rule configuration IDs checked), STOPs unless the recomputed episodes equal the stored S5, then attributes each S_VIEW IE event to the IE clauses that held and the inputs that were undetermined. No test data is read.
- Tests: new `tests/m1b/test_ie_inputs_diag.py` (5, hand-calculated). Full suite twice: 2795 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed). The diagnostic runs from it.
- Next: T-29u part 2 (run, 116 cameras), then T-29w.

### 2026-11-27 — T-29u part 2 and T-29w (D-66): IE-input diagnostic run on 116 tuning cameras; write-up
- Did: `ie_inputs_diag.py run` from 8ad6c61 on the 116 tuning cameras (no test data read): recomputed S5 inputs equal the stored S5 on 116 / 116 (no STOP), rule configuration IDs equal the freeze record; `aggregate` twice, byte-identical: `research/v2/ie_inputs_diag_tune.json` (diagnostic, post hoc, selects nothing). IE shares equal the dev run (A|BL-6 0.773, C|BL-6 0.759). BL-6: every IE event on A (92) and 102 of 104 on C fail a coverage clause (Q not sufficient at the closest approach and / or above o_max of the span); 2 on C are IE only through K undetermined (R5 unknown); M undetermined in 1 (A) and 3 (C) IE events.
  - `research/v2/writeup_v2.md`: claims from the test values (three failed criteria, false alerts per hour), scope as D-66 orders (synthetic data only; BL-3 = BL-6 on SDG, with the test detector-path EV-M2 difference of 0.004 stated; the defective first reporting run disclosed; reporting set "held out from v2 tuning"); the diagnostic in §4.
- Tests: no code change since 8ad6c61. Full suite twice: 2795 passed, 17 skipped, identical.
- Commit: this entry's commit (pushed).
- Problems / CRs: none open from D-66.
- Next: nothing ordered after D-66 on this branch; waiting for the Owner.

### 2026-11-27 — T-30 done (Codex)

- Recorded D-67, the post-audit roadmap, WP-21–WP-26, T26, CR-043/044 and decision gate D-68. Added the centralized agent contribution register.
- Reconciled the three registered oracle-box RMSE failures with the matched-subset detector RMSE and the oracle-position rule results using the published reports. Reviewed the current gate, reference comparison, state guard and recent history. This documentation change runs no experiments.
- Verification: documentation links and Git diff checked. See the contribution register for attribution and independent review status.
- Next: Claude Code coordinates WP-21 and the parallel development-only reference and experiment designs. T-35's confirmatory branch stays at D-68.

### 2026-11-27 — T-31 part 1 (Codex, D-69)

- Integrated the accepted plan with D-69 and T26.1, keeping original commit `0392e82` and the existing criteria. CR-043 records the active entry-point, reference, state, reporting and cache changes. AR-75 records the development cache and input-audit representation.
- On one allowlisted ceiling tuning camera with 10 s usable support, B scored 600 of 600 object-frames against position and speed references, and C scored 562 of 600 for each. At BL-6 and temporal IoU 0.3, C matched 1 of 1 rule references and emitted 1 candidate with zero false and duplicate candidates. These are isolation and reporting smoke checks with stored S2. They provide no comparative, human-judgment or scientific acceptance evidence.
- Main suite passed twice with 2,808 passed and 17 detector-only skips on each run. The separate detector suite passed all 32 tests. Seven direct command checks, including the CPU detector launcher, refused unavailable partitions or recordings. The main suite uses independent replacements for the two sealed SDG content regression cases. The detector suite uses temporary Python 3.9-compatible pytest outside the detector environment and excludes the unrelated main-suite conftest. The archived v2 result data and both frozen registrations retain their original bytes.
- T-31 remains in progress. Archive custody and inspection of other entry points and aliases, Claude Code's independent review, and the detailed development allocation remain open. Approval gates for training allocations, spending, definition changes, reserved datasets and confirmatory work remain in D-69 and D-68.
