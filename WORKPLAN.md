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

Never pre-approved: paid services, cloud upload of data, real worker footage, fine-tuning compute purchases, any contract change.

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
| [ ] | T-15 | **Export and reports (WP-10).** Export classes, fixture banner, wording rules, status board | T-14 | F.1 A2; E-1.2.1 §11 | CT-X-01–05, CT-E-26/27/28 | S |
| [ ] | T-16 | **M0 integration and self-audit (WP-11).** Run the whole fixture pipeline twice from a clean clone; full suite; complete the self-audit (§5); write `reports/M0_report.md` (§6 template); tag `m0-verified`; push | all above | Package F §12 | All M0 tests pass; identical artifact IDs across both runs | M |
| [S] | G-M0 | **STOP — Owner reviews M0.** Recommended: share the repository with the Research Architect for an independent review before accepting | T-16 | — | Owner writes "M0 accepted" in `DECISIONS_NEEDED.md` | — |

---

## 2. Milestone M1a — oracle-perception synthetic slice (after G-M0)

| ✓ | ID | Task | Needs | Refs | Done when | Size |
|---|---|---|---|---|---|---|
| [ ] | T-17 | **Dataset qualification (WP-12).** Record source URLs, versions, licence terms and authenticity evidence **before** downloading. Download only if pre-approved in §0; otherwise **STOP**. Reproduce the census facts (1 worker, 1 forklift, 300 frames, 10 views). Verify units. Extract lineage. Report the frame-interval distribution of every downloaded recording (min, median, P99, max, VFR flag) | G-M0 | Package F WP-12 | `research/datasets/qualification.md`; licence rows; data outside git | M |
| [ ] | T-18 | **Dataset adapters (WP-13).** SDG and SmartSpaces → S0, oracle tracks, simulator references; `reference_class` set correctly | T-17 | Package F WP-13; F.1 A5.1 | Truth round-trip within 1e-6 m; reprojection check | L |
| [ ] | T-19 | **R4 and configurations BL-1–BL-6 (WP-06b)** | T-09 | E-1.2.1 §6.0 | R4 fixtures with hand-computed TTC/PET | S |
| [ ] | T-20 | **Draft the pre-registration** (proposal only): parameter grids, configurations, strata, primary metrics, acceptance criteria with targets and n_min. **Does not run test-partition evaluation** | T-18, T-19 | E-1.2.1 §9.6; D.1 | `docs/preregistration_DRAFT.md`, with this checklist: (1) *k_sup* chosen from the measured frame-interval distribution of the qualified datasets, above their natural VFR jitter; (2) camera grouping basis declared explicitly for every research configuration (AR-22); (3) frame-quality rules version (AR-27); (4) w_ref and its relation to timeline lengths (D-7) | M |
| [S] | G-PR | **STOP — Owner approves and freezes the pre-registration** (the Owner, not the agent, chooses scientific thresholds) | T-20 | — | `docs/preregistration_FROZEN.md` committed by the Owner | — |
| [ ] | T-21 | **M1a run (WP-14).** Validation partition first, then test. GV-01, GV-03–08; MR-01, MR-08–12; CM-01–10; EV-M1–M8; BL-2 vs BL-3 and BL-3 vs BL-6 on oracle perception. Report rule-conformance results separately as "implementation conformance" | G-PR | Package F WP-14; Appendix N | `reports/M1a_report.md`; tag `m1a-complete` | L |
| [S] | G-M1a | **STOP — Owner reviews M1a** | T-21 | — | Owner decision recorded | — |

---

## 3. Milestone M1b — detector-based slice (after G-M1a)

| ✓ | ID | Task | Needs | Done when | Size |
|---|---|---|---|---|---|
| [ ] | T-22 | **Detector benchmark (WP-15).** Check whether CPU PyTorch or ONNX Runtime installs on this Mac. If it doesn't → **STOP** with options. Benchmark pretrained detectors on a small frame subset; record what COCO models output on forklifts (not assumed zero); licence table | G-M1a; §0 approval | Benchmark report | M |
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
