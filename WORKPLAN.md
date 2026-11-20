# WORKPLAN — RQ1 single-agent implementation schedule

**Owner:** Research Owner · **Implementer:** one Claude Code agent on the Owner's MacBook Air · **Remote:** the Owner's GitHub repository
**Contract:** E-1.2.2 (E-1.2.1 FROZEN + F.1 Part A + Appendix N) · **Plan details:** Package F
**Mode change (9 Nov 2026, Owner decision):** a single agent replaces the multi-agent team. F.1 Parts B and C are superseded. Its safeguards are kept in simpler form: tests written first from the documents, no editing of expected values, determinism re-runs, a self-audit at each milestone, and Owner review at STOP points.

How to use this file:
- Work tasks **in order**. A task may start only when the tasks in its `needs` are ticked.
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

Never pre-approved: paid services, cloud upload of data, real worker footage (except the D-21 testing-only exception above), fine-tuning compute purchases, any contract change.

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
| [x] | V-02 | **T22 blind review application, part A (Owner tooling)** — branch `v02-review-ui` only, no merge into `m0-implementation`. D-44 decided (option a): protocol = Appendix T T22 (E-1.2.20). Local app (127.0.0.1): Owner setup, seeded pilot and batches (T22.6), blind reviewer screen (T22.4, T22.5), adjudication and tier-1 audit (T22.7), status entries (T22.8), reference_class (T22.9), exposure rule (T22.2 b), agreement panel (T22.10 a). T22.14 readings (CR-028 closed, D-46); AR-61 accepted; audit trail view (D-46) | D-44 | D-44 instructions, step 3 | every T22 fixture through the app, acceptance tests pass, suite twice, `research/review_ui/V-02_report.md` pushed | M |
| [x] | W-01 | **T23 reporting workflow (D-48)** — branch `v02-review-ui` only, no merge. Contract E-1.2.22 (Appendix T T23) on this branch. Workflow in the V-02 app (`src/rq1/workflow/`): AI intake and grouping, two-level review, report log, indicators and flags, simulated regulator view, Owner setup, demo draw (seed 2026111903; D-45 pilot column C). CR-030 (item 1 blocks SM adjudications), AR-63 | D-48 | D-48 steps 1-5 | every T23 fixture through the app, suite twice, `research/workflow/W-01_report.md` pushed; STOP D-49 | M |
| [~] | T-21 | **M1a run (WP-14)** (validation only, D-36, D-37; D-38 option A and T21 / CR-025 decided 14 Nov; SmartSpaces EV-M waits for D-39). Validation partition first, then test. GV-01, GV-03–08; MR-01, MR-08–12; CM-01–10; EV-M1–M8; BL-2 vs BL-3 and BL-3 vs BL-6 on oracle perception. Report rule-conformance results separately as "implementation conformance" | G-PR | Package F WP-14; Appendix N | `reports/M1a_report.md`; tag `m1a-complete` | L |
| [x] | G-M1a | **STOP — Owner reviews M1a** (D-40 DECIDED 17 Nov 2026: M1a accepted as experimental validation evidence) | T-21 | — | Owner decision recorded | — |

---

## 3. Milestone M1b — detector-based slice (after G-M1a)

| ✓ | ID | Task | Needs | Done when | Size |
|---|---|---|---|---|---|
| [S] | T-22 | **Detector benchmark (WP-15) — revised scope (D-42 option (a), 19 Nov 2026): zero-shot detectors.** Runtime check done (`feasibility.md`). Probe YOLO-World v2-s and Grounding DINO tiny, prompts exactly "person" and "forklift", on 100 SDG validation frames (5 from each of 20 validation cameras, 10 ceiling and 10 eye-level, seeded draw 2026111901), against the oracle-path simulator boxes (visible objects, clipped). Same-class matching at IoU ≥ 0.3, one-to-one by descending IoU. Recall and precision at score thresholds 0.05–0.50, the best-F1 threshold, per viewpoint, s/frame and peak memory. No S4/S5/S8 with detector output, no fine-tuning, no Ultralytics trackers, no change to the pre-registration or any analysis module. **STOP after the report** (D-45) | G-M1a; §0 approval (D-42) | `research/m1b/zero_shot_probe.md` and `.json` | M |
| [ ] | T-23 | **Tracker adapters (WP-17)** with evidence classes; identity-association fixtures | T-22 | HOTA/IDF1 against simulator IDs | M |
| [B] | T-24 | **Fine-tuning (WP-16). BLOCKED** until the Owner decides licence posture, training data and compute (C2–C4) | Owner | — | — |
| [B] | T-25 | **M1b integration (WP-18). BLOCKED** on T-24, or on a qualified pretrained forklift detector from T-22 | T-24 | — | — |

| ✓ | ID | Gate | Needs | Done when |
|---|---|---|---|---|
| [S] | G-FQ | **STOP before the first real-data task: frame-quality rules version.** The agent proposes a rules version (frozen, black, blur, exposure) for Architect review and Owner approval (AR-27 review). No real footage is decoded under `rv1` | Proposal in `DECISIONS_NEEDED.md` | Owner approves the rules version |

**Later work, not scheduled until the Owner decides:** E2 measurement (E2-W1/W2 after M1a, using T-07's findings), multi-camera linkage (M2), real-data collection (requires ethics approval), the FM-X1 annotation-efficiency experiment.

---

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

### 2026-11-16 — V-02 STOP after Phase 1 (compatibility audit; branch `v02-review-ui`)
- Did: worktree `../rq1-v02`, branch `v02-review-ui` from `m0-implementation` 636b311 (clean, level with origin), pushed with -u. WORKPLAN row V-02 added. Phase 1 audit `research/review_ui/V-02_compatibility_audit.md` (points a–j: contract reference, existing module and function, reuse, conflict).
- Finding: no schema conflict. `tables.py` schemas, UUIDv7 human IDs, `StatusLog.append` / `.verify`, `vr_rules.check_blind_reference` (VR-E-053), `estimators.cohen_kappa` / `krippendorff_alpha_nominal` and `obx` part 5 are all reusable unchanged (`namespace.require_reference` is not applicable to C-layer rows). But the C-layer protocol is undefined in eight meaning-affecting places (G1 blindness for system targets, G2 assessments required, G3 adjudication → status, G4 confidence scale, G5 method values, G6 `config_id` for reference targets, G7 tier rule and reference class, G8 reviewer-facing label definitions). EV-M9 / EV-M12 are not implemented; OBX is the only downstream reader. FX-13 is active but has no fixture or test.
- Opened: CR-027, D-44 (STOP). No UI code, tests or records written; no schema, enum, ID rule, guard or analysis function changed; `docs/preregistration_FROZEN.md` untouched; no data read beyond the repository fixtures and documents.
- Tests: 1888/1888 passed, 2 skipped (held SDG data not present in this environment), twice; no code change. Environment for this session: Linux, CPython 3.14.6 `.venv` from `requirements.lock` (the 3.15 beta available here cannot load the locked `hypothesis` wheel).
- Problems / CRs: CR-027 / D-44.
- Commit: e4388c4 (pushed)
- Next: STOP on D-44. No merge, rebase or pull request (Owner decides).

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

### 2026-11-19 — V-02 numbering: D-40 → D-44, CR-026 → CR-027 (Owner instruction of 19 Nov 2026, item 4)
- Did: the V-02 decision request and change request on this branch had the same numbers as D-40 (G-M1a) and CR-026 (foot-ray range rule) on `m0-implementation`. Renamed them to **D-44** and **CR-027**, with every reference updated: `DECISIONS_NEEDED.md`, `docs/CHANGE_REQUESTS.md`, the WORKPLAN V-02 row, `research/review_ui/V-02_compatibility_audit.md` and the V-02 Progress log entry (13 references in all). The base commit 636b311 contains none of the four numbers, so every replaced occurrence was a V-02 one. Nothing else changed.
- Tests: not run (documents only; no code change)
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-027 / D-44 still open. V-02 stays STOPPED (the Architect is rewriting its protocol).
- Next: STOP on D-44.

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

### 2026-11-19 — V-02 part A done: T22 blind review application (branch `v02-review-ui`); CR-028 opened, AR-61
- Did:
  - **Step 2:** merged `m0-implementation` (T22, E-1.2.20) into `v02-review-ui`, no rebase (e148a93). Conflicts in WORKPLAN, DECISIONS_NEEDED and CHANGE_REQUESTS were resolved by keeping both sides' entries. The D-44 / CR-027 renumbering was already on this branch (5deb106).
  - **Step 3:** built `src/rq1/review/`:
    - `protocol.py`: the T22 rules as pure functions;
    - `store.py`: the validation store under `out/review/`, append-only, every row checked by `validate_row` and VR-E-053, the existing `StatusLog`;
    - `frame.py`: the BL-6 SDG validation episodes of the T-21 run, read only;
    - `server.py`: standard-library server on 127.0.0.1, plain HTML and inline JS;
    - `__main__.py`: `init` and `serve`.
  - Covered: sign-in by pseudonymous profile with salted, hashed passphrases (not a security boundary); Owner setup of annotator rows; pilot and batches; blind reviewer screen; adjudication with the tier-1 audit; consensus meeting; status entries; reference_class; exposure rule; agreement panel (Owner only, after full adjudication). Banner on every page.
  - `src/rq1/fixtures/review_video.py`: a synthetic fixture video (shapes only).
  - `research/review_ui/make_demo.py`: drives a fixture batch end to end through the app and renders 7 screenshots with headless Chrome (installed locally; nothing installed or downloaded).
  - Report: `research/review_ui/V-02_report.md`.
- Tests: 2521/2521 (full suite), twice: identical. New in `tests/review/`:
  - 52 protocol tests (hand calculations: allocation with and without seeded ties, capping, κ five and four labels, P90);
  - 28 application tests: FX-13 and FX-13a to FX-13f through sign-in, pages and form posts; ref_event writes no status; allocation and pilot exclusion; per-reviewer order; no system output or other person's record on a reviewer's pages or JSON; the second reviewer never sees the first assessment; clip window and ranges; 127.0.0.1 only; no network URL; banner; wording rules; Owner-only pages; static import check (no S5, S8 or pipeline entry point; κ / α functions only); 2 held-data tests on the T-21 SDG frame; the report wording.
- Commit: this entry's commit (pushed)
- Problems / CRs:
  - **CR-028** (open): five T22 readings that change a number (audit size, α units, later batches, pilot records, allocation under capping). The tool runs with provisional readings, recorded in every manifest. A second non-pilot batch per configuration and partition is refused until item 3 is decided.
  - **AR-61** (proposed): 11 representation choices.
  - The original V-02 task text is not on this computer; its constraints were taken from the compatibility audit (noted in the report).
  - No SDG validation recording has more than one person or forklift, so outlines are exercised on fixtures only.
- Next: **STOP for V-02** (no merge into `m0-implementation`, no pull request). CR-028 should be decided before a real reference batch. The reporting workflow waits for T23.

### 2026-11-19 — D-46: Appendix T T22.14 recorded (contract E-1.2.21)
- Did: the Architect's CR-028 rulings appended verbatim to Appendix T as **T22.14** (contract **E-1.2.21**); CLAUDE.md contract line updated; D-46 recorded as decided. No code change on this branch: the T22.14 tests belong to the review application on `v02-review-ui`, where the code is. FX-13e is unchanged (the byte-identical fixture regeneration test passes).
- Tests: 2441/2441 (full suite), twice: identical.
- Commit: this entry's commit (pushed)
- Problems / CRs: none new. D-45 still open.
- Next: D-46 items 1 to 3 on `v02-review-ui`; then the D-45 prompt on this branch.

### 2026-11-19 — D-46 on `v02-review-ui`: T22.14 implemented, CR-028 closed, AR-61 accepted, V-02 fixes
- Did:
  - Merged `m0-implementation` (T22.14, E-1.2.21; 4ce37cc) into `v02-review-ui`, no rebase (1c9e5c8). The Progress-log conflict was resolved by keeping both entries.
  - **T22.14** in the application:
    - (a) audit size ceil, unchanged;
    - (b) α only with 5 or more audited targets, printed with its n, else "not computed (n < 5)";
    - (c) every target of any earlier batch on the same configuration and partition is excluded; a re-draw is refused; the second-batch refusal is removed;
    - (d) pilot as before;
    - (e) water-filling as before, and manifests state `n_requested`, `n_drawn`, `frame_exhausted`.
  - "Provisional" labels removed; manifests carry `readings: Appendix T T22.14 (E-1.2.21)`.
  - **CR-028** closed as superseded by T22.14. **AR-61** accepted (all eleven items).
  - **Fixes:**
    - (a) stray shell text removed from the end of `V-02_report.md`. No other V-02 file had a line that is exactly "EOF" or `.venv/bin/python -c` in Markdown. The report test now pins this.
    - (b) Owner-only **audit trail view** added: `/audit` lists targets; `/audit/<target>` shows the full status history with its basis adjudications, actors and hashes, plus the hash-chain check. Read-only; a broken chain is shown.
    - (c) the real-frame dry run lived only in a pytest temporary store, so nothing was renamed. The report says so and states that the agent's seeds must never be used for real review.
    - (d) the original V-02 items 3 to 7 as the agent understood them, each marked, are in the report. Item 6's round trip through the OBX export is now tested.
  - **Test-fixture defect found and fixed:** fixture target IDs built as `f"ep_{tag}{k}".ljust(29, "0")` collided (k = 1 and k = 10 gave the same ID), so some fixture frames held fewer targets than declared. A zero-padded counter is now used in `tests/review/` and `make_demo.py`. No expected value changed; the allocation tests now run on full-size frames and pass.
  - The one test that pinned the old second-batch refusal now checks T22.14 (c). Screenshots regenerated, with `08_owner_audit_trail.png` added.
- Tests: 2539/2539 (full suite), twice: identical. New: `tests/review/test_d46.py` (18 tests).
- Commit: this entry's commit (pushed)
- Problems / CRs: none open for V-02.
- Next: **STOP for V-02** (no merge into `m0-implementation`, no pull request). Then the D-45 prompt in the main folder.

### 2026-11-19 — W-01 done (D-48: T23 reporting workflow, contract E-1.2.22 on `v02-review-ui`); STOP at D-49
- Did:
  - **Contract:** Appendix T **T23** appended verbatim as **E-1.2.22**, and the CLAUDE.md contract line updated, **on `v02-review-ui` only**. E-1.2.22 exists on this branch until the Owner merges it into `m0-implementation`. D-48 recorded as decided.
  - **Schema:** the T23.15 tables (wf_config, wf_establishment, wf_area, wf_user, wf_report, wf_report_log, wf_hours, demo_manifest) in the single schema source, with validators.
    - Contract-driven test list updates: `EXPECTED_TABLES` (+8) and `REQUIRED_IDS` (+FX-14 to FX-14i), as for T22.
    - No existing table changed. An attempt to make `adjudication.reference_class` nullable was reverted, because it changed a pinned field list; it is now CR-030 item 1.
  - **Fixtures:** FX-14 and FX-14a to FX-14i, with T23 expected values and hand calculations. FX-14f's Wilson bound is derived in decimal arithmetic in the test (10/12: 0.5519691…; 6/12: 0.2537815…).
  - **Workflow** (`src/rq1/workflow/`), served by the V-02 application with one sign-in:
    - AI intake with transitive grouping;
    - pre-filled fields and evidence_clip rows;
    - the T23.4 state machine with role permissions and the two-level rule;
    - candidate_review assessments and status entries for area-manager decisions;
    - hash-chained report log;
    - human-started reports;
    - recordability and 301-style export;
    - indicators I1–I9 and flags F1–F4 (each view prints the log length and head hash);
    - simulated regulator view with JSON and CSV export;
    - Owner setup and demo draw.
    - Every workflow page and export passes the T23.12 linter before it is sent; 127.0.0.1 only.
  - **V-02 changes:** T23.11 (b) demo exclusion in `create_batch`; the handler class is a parameter; `serve` uses the workflow store (AR-63 item 14).
  - **Demo:** seed 2026111903 on the new store `out/review/demo_20261119/`. Source: the **D-45 detector-path pilot BL-6 S5 artifacts (column C)**, which existed when the step started; recorded in the demo manifest. Result: 9 runs, 3 establishments, 8 AI reports, 15 members; both logs intact. No manager decision was taken; the Owner plays the roles.
  - **Records:** `research/workflow/W-01_report.md` with fixture-only screenshots.
  - **CR-030** opened (10 items; item 1 blocks the safety-manager adjudications and status entries). **AR-63** written (14 items).
- Tests: 2624 passed, 2 xfailed (strict; CR-030 item 1), 0 failed (full suite), twice: identical. The fixture regeneration is byte-identical. New: `tests/workflow/` (40 tests, 2 of them strict xfails), `tests/fixtures_t03/test_t23_fixtures.py`.
- Commit: this entry's commit (pushed)
- Problems / CRs: CR-030 (open), AR-63 (open, review at D-49). Ordering note: the T23 fixtures and tests were written alongside the workflow modules, not strictly before them; every expected value comes from T23 or a recorded hand calculation.
- Next: **STOP (D-49).** No merge into `m0-implementation`.
