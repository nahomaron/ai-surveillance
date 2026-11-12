# Package F.1 — Implementation-Readiness Contract Corrections and Autonomous AI Engineering Execution Protocol

**Date:** 9 November 2026
**Amends:** Frozen contract E-1.2.1 → **E-1.2.2** (Part A, plus Appendix N); Package F (Parts B and C).
**Status:** For review at Gate F.1. No coding agent, download or paid service has been started.
**Revision 9 Nov 2026 (r2):** The Research Owner decided that the whole implementation is carried out with **Claude Code only**. All Codex and mixed-provider material is removed from Part C.

| Part | Content | Nature |
|---|---|---|
| A | Five contract corrections and normative Appendix N | Required for scientific validity and implementability |
| B | AI engineering organization and governance | Required execution protocol |
| C | Local orchestration feasibility and Gate A0 test | Engineering assessment; nothing in it is verified until A0 runs |

---

# Part A — Contract corrections (E-1.2.1 → E-1.2.2)

## A1. Record identity and natural keys

### A1.1 Defects

| # | Defect | Effect |
|---|---|---|
| 1 | `completeness_record` key omits `support_basis` | Detected and detected+inferred records for the same window, metric and stratum collide (`ERR-NATURAL-KEY`, or silent loss if the check is weak) |
| 2 | `match_record` key omits configuration, scenario and label group | Records collide when one evaluation covers several of these |
| 3 | `metric_result` key omits estimand, weighting, sample type, definition version, support basis and split | Weighted and unweighted values (or two estimands) collide |
| 4 | §2.1 defines `rec_` without the artifact, while §2.2 derives every record ID from `art_` | Contradictory precedence; registration IDs would change whenever an S0 artifact gains a file |
| 5 | Single-configuration artifacts (S2 model, S5 rule configuration) are assumed but never stated | Keys of `detection`, `flag_series`, `episode` and others would collide if an artifact held two configurations |

### A1.2 Corrected identity classes

| Class | Tables | ID | Stability |
|---|---|---|---|
| **Anchor** (registry) | dataset_source, license_component, site, session, camera, source_file, recording, timeline, clock_alignment, camera_group, world_frame, calibration, context_map | `id(prefix, [table, nk])`, where every reference inside `nk` uses the parent's **anchor ID**. `src_` = `b32(SHA-256(bytes))` | Independent of any artifact. The same entity has the same ID in every S0 artifact |
| **Configuration** (content-addressed) | footprint_prior, substrate_config, clearance_band_scheme, rule_configuration, decode_config, geometry_config, acceptance_criterion, sampling_plan_config | `id(prefix, JCS(content))` | Changes iff the content changes |
| **Observation** (artifact-scoped) | All S1–S9, V0, CV-SIM, X0, S8, S8f records | `H(table, art_, nk)` (E-1.2.1 §2.3) | Changes with the artifact |
| **Human entry** | annotator, annotation_record, reviewer_assessment, adjudication, status log entries, human-defined physical identities | UUIDv7 | Assigned once |
| **Execution** | run | UUIDv7 | Per execution |

**Precedence:** anchor and configuration IDs are computed before any artifact exists, so they may appear in payloads as ordinary input references. An S0 artifact still has an `art_` for lineage, but its records carry anchor IDs.

**ANC-1 (anchor conflict):** two S0 artifacts that emit the same anchor ID with different payload columns raise `ERR-ANCHOR-CONFLICT`. Corrections create a new version field value, never an overwrite.

**ART-ISO (single-configuration artifacts):**

| Stage | One artifact contains exactly one |
|---|---|
| S2 | Model (weights hash) and inference configuration |
| S3 | Tracker configuration (or one oracle source) |
| S4 | Geometry configuration and substrate configuration (several band schemes allowed) |
| S5 | Rule configuration |
| S8 | Split version and evaluation configuration; may cover several S5 artifacts, so keys include `config_id` |

A spec that violates ART-ISO raises `ERR-SPEC`.

**NK-RULE:** a natural key must contain every dimension that can vary among records of its table **within one artifact**.

### A1.3 Revised natural keys (all other keys in E-1.2.1 §2.4 unchanged)

| Table | Revised natural key |
|---|---|
| site | (dataset_id, site_label) |
| session | (site_id, session_label) |
| camera | (site_id, camera_label) |
| recording | (src_id, session_id, camera_id, registration_label) |
| timeline | (kind, anchor_id), with anchor = session_id or recording_id |
| clock_alignment | (recording_id, method, version) |
| camera_group | (timeline_id, sorted camera_ids) |
| world_frame | (site_id, label, version) |
| calibration | (camera_id, tier, method, valid_from_us, version) |
| context_map | (site_id, version) |
| completeness_record | (window_id, metric_id, **support_basis**, **config_id?**, stratum) |
| match_record | (window_id, **config_id, scenario, label_group**, ref_event_id?, system_event_id?) |
| error_attribution | (match_nk) unchanged; inherits the new match key |
| metric_result | (metric_id, **definition_version, config_id?, scenario?, label?, support_basis?, sample_type, estimand, weighted**, slice) |
| ref_object_presence | (window_id, camera_id, physical_identity_id) |
| ref_interaction | (window_id, person_identity_id, forklift_identity_id, t_onset_us) |
| ref_geometry | (window_id, physical_identity_id, camera_id, frame_index) |
| ref_coverage_label | (window_id, camera_id, t_start_us) (see A3) |
| track_identity_assoc (new, A5) | (window_id, camera_id, frame_index, track_id?, physical_identity_id?) |
| track_identity_summary (new, A5) | (window_id, track_id) |

A null in a key is serialized as JCS `null`. `match_record` uses this for misses (system ID null) and false alerts (reference ID null). Each of those keys stays unique because each reference or system event appears in at most one such record per (config, scenario, label group).

### A1.4 Tests

| Test | Fixture | Pass condition |
|---|---|---|
| CT-NK-01 | Completeness for one window on both support bases | Two distinct IDs; no ERR-NATURAL-KEY |
| CT-NK-02 | One S8 artifact over two S5 configs × two scenarios × two label groups | 8 distinct match-record sets; no collision |
| CT-NK-03 | Weighted and unweighted recall, two estimands | Four distinct metric_result IDs |
| CT-NK-04 | Register dataset A; then register A + B in a new S0 artifact | Every anchor ID of A unchanged |
| CT-NK-05 | Same anchor key with a different payload | ERR-ANCHOR-CONFLICT |
| CT-NK-06 | S5 spec with two rule configurations | ERR-SPEC |
| CT-NK-07 | Property test: random record sets per table, varying every non-key column | Uniqueness holds iff key fields differ; re-run gives identical IDs |
| CT-NK-08 | FK integrity across classes (observation → anchor, observation → configuration, same-artifact `_nk`) | All references resolve (extends CT-FK-03) |

**Affected WPs:** WP-01 (ID classes, ANC-1, ART-ISO), WP-03 (anchor keys), WP-08 and WP-09 (keys).

---

## A2. Fixture export versus research export

**Defect:** M0 needs S9 to run on TEST-ONLY configurations, while E-1.2.1 refused them in exports (CT-F-11).

**Correction:**

| Field | Location | Values |
|---|---|---|
| `dataset_kind` | dataset_source | {fixture, research} |
| `export_class` | OBX manifest and every exported file's metadata | {fixture_verification, research} |
| `research_use` | Same | bool; false for fixture_verification |

| Rule | |
|---|---|
| EXP-1 | A `fixture_verification` export requires **every** configuration to be TEST-ONLY **and** every dataset to be `fixture`. It is written to a separate root (`out/fixture/`) |
| EXP-2 | A `research` export requires **no** TEST-ONLY configuration and **no** fixture dataset. For any test-partition metric, the configuration must carry a `preregistration_ref` |
| EXP-3 | Mixed inputs are rejected in both directions (`ERR-EXPORT-CLASS`) |
| EXP-4 | Reports from fixture exports carry the fixed banner "FIXTURE VERIFICATION — NOT RESEARCH RESULTS" and cannot use research report templates |
| EXP-5 | Both export classes run the same serializer and schema validators; only the class guard differs |

| Test (replaces CT-F-11) | Pass condition |
|---|---|
| CT-X-01 | M0 fixture export succeeds, validates against OBX schemas and has `research_use = false` |
| CT-X-02 | Research export containing a TEST-ONLY config → ERR-EXPORT-CLASS |
| CT-X-03 | Fixture export containing a non-TEST-ONLY config or a research dataset → ERR-EXPORT-CLASS |
| CT-X-04 | Fixture report has the banner; research template on a fixture export is refused |
| CT-X-05 | Byte-level serializer output is identical between classes apart from the class fields (EXP-5) |

**Affected WPs:** WP-02 (fixture datasets marked), WP-10, WP-11.

---

## A3. Reference coverage on the timeline

**Defect:** `ref_coverage_label` used frame boundaries, so `not_recorded` and `gap_unobserved` time (which has no frames) could not be labelled.

**Revised `ref_coverage_label`:**

| Field | Type | Rule |
|---|---|---|
| window_id, camera_id, timeline_id | id | |
| t_start_tl_s, t_end_tl_s | f64 | Half-open. Spans tile `[t_start_tl_s, t_guard_end_tl_s)` of the window for each camera |
| start_frame?, end_frame_excl? | i64 | Null `not_applicable` when the span contains no eligible frame |
| ref_activity_state | enum | not_annotated, unobservable, reference_verified_absent, objects_present_no_interaction, interaction_present |
| unobservable_reason? | enum{not_recorded, gap_unobserved, unusable_footage, outside_view, occluded_region, other} | Required iff `unobservable` |
| eligible_support_s | f64 | Clipped support of eligible frames in the span |
| prov_class, label_source | | |

| Invariant | Rule |
|---|---|
| RC-01 | Spans tile each (window, camera) interval exactly once |
| RC-02 | Where system coverage is `not_recorded`, `gap_unobserved` or `unusable`, the reference state is `unobservable` with the matching reason. Annotators see only eligible frames (ST-5) |
| RC-03 | `reference_verified_absent` only in exhaustive windows, on spans with `eligible_support_s > 0`, and only from `simulator_truth` or `human_manual` sources |
| RC-04 | Durations of verified absence, presence and interaction are Σ clipped eligible support, never span length |
| RC-05 | No Observation-store table can write reference states; zero AI detections never produce `reference_verified_absent` (VR-E-040 retained) |

**Fixtures** (10 fps, one window of 30 s plus 5 s guard on an aligned timeline):

| ID | Content | Expected spans |
|---|---|---|
| FX-RC-1 | Frames 100–114 corrupt inside the window | `unobservable/unusable_footage` over [10.0, 11.5); support 1.5 s excluded from all reference durations |
| FX-RC-2 | Internal dropout of 3.0 s after frame 200 (δ_max 0.15 s) | `unobservable/gap_unobserved` over [20.1, 23.0); no frame bounds |
| FX-RC-3 | Camera not recording for 25–35 s while the session continues | `unobservable/not_recorded` over [25, 35); no frame bounds |
| FX-RC-4 | Usable span; simulator shows a forklift present; system detects nothing | Reference `objects_present_no_interaction`; system `observed_no_detection`; CM-02 numerator 0 |
| FX-RC-5 | Usable span with nothing present (simulator) | `reference_verified_absent`; system `observed_no_detection`; reports show "verified absent" from the Validation store only |
| FX-RC-6 (invalid) | `reference_verified_absent` over a `gap_unobserved` span | Rejected (RC-02/RC-03) |

| Test | Pass condition |
|---|---|
| CT-RC-01 | FX-RC-1–5 produce exactly the listed spans and durations |
| CT-RC-02 | FX-RC-6 rejected |
| CT-RC-03 | Property test: random coverage timelines → RC-01–RC-04 hold |

**Affected WPs:** WP-08 (schema, CV-SIM), WP-09 (completeness denominators), WP-02 (fixtures).

---

## A4. Normative completeness

**Defect:** E-1.2.1 pointed to C.1, D and D.1 for formulas, and lacked several fixture values.

**Correction:** **Appendix N** (end of this document) is normative and forms part of E-1.2.2. It contains every formula, denominator, estimator, interval method, fixture input, expected output and tolerance needed by M0 and M1. Earlier packages are design rationale only.

Rules:
- If Appendix N and an earlier package differ, Appendix N governs.
- If Appendix N is silent, the gap is raised as a change request (Part B §B7). Agents never infer a definition.
- Library reference implementations named in Appendix N (pycocotools for AP; TrackEval for HOTA, IDF1 and MOTA) are normative for those metrics. Their versions are pinned in the environment, and their licences are recorded.

**Affected WPs:** WP-02, WP-09, WP-14, WP-15, WP-17. QA (Part B) recomputes every fixture expectation independently.

---

## A5. Reference classes and physical-identity association

### A5.1 Reference classes

| `reference_class` | Produced by | Supports | Never supports |
|---|---|---|---|
| `rule_conformance` | Applying the system's own operational definitions (P, X, C, O/H/PC labels) to simulator truth or reference geometry | Claims that the implementation applies the definitions correctly ("implementation conformance") | Detection-validity or construct claims; any construct status |
| `independent_perceptual_geometric` | Simulator object truth (boxes, IDs, positions, task states such as `Dodge`), or human A/B annotation | Perception, tracking, geometry, completeness and evasive-action detection claims | Hazard meaning |
| `independent_expert_judgment` | Blind, adjudicated C-layer reviewers with independence attestation | CV-2 expert alignment | Injury prediction (CV-3, out of RQ1 scope) |

Field additions: `reference_class` on ref_object_presence, ref_interaction, ref_geometry, ref_coverage_label, adjudication; also on `metric_result` and `match_record` (the class of the reference used).

| Invariant | Rule |
|---|---|
| RV-01 | O/H/PC references produced by CV-SIM from synthetic truth are `rule_conformance` |
| RV-02 | A `metric_result` with `reference_class = rule_conformance` has `claim_level ∈ {none}`. Its report section is titled "Implementation conformance" |
| RV-03 | `construct_status = CV2` requires an expert-alignment result with `reference_class = independent_expert_judgment` |
| RV-04 | Reports never present rule-conformance agreement as hazard identification or construct evidence |

**Consequence for M1a:** WP-14's EV-M results for O/H/PC on synthetic data are **implementation conformance**. Perception, geometry, completeness and evasive-action results against simulator object truth are **independent perceptual-geometric** evidence (synthetic scope).

### A5.2 Physical-identity association (system tracks ↔ reference identities)

**Inputs:** per window and camera, the system track points on eligible frames, and the reference objects (ref_object_presence keyframes, linearly interpolated between keyframes, or simulator boxes on every frame).

**Frame-level association (deterministic):**
1. For each eligible frame, candidates are system boxes and reference boxes of the **same class**.
2. Weight = IoU, quantized to integer micro-units. Pairs with IoU < *iou_cm* are excluded.
3. Solve the maximum-weight one-to-one assignment on canonically sorted inputs (system: track natural key; reference: physical_identity_id).
4. **Ambiguity:** an assigned pair is `ambiguous` if, for either side, a second candidate has IoU within *ε_amb* of the assigned IoU and ≥ *iou_cm*. Ambiguous frames count in neither matched nor unmatched time; they are reported separately.
5. Record `track_identity_assoc` rows with status ∈ {matched, ambiguous, unmatched_system, missed_reference}.

**Track-level summary (`track_identity_summary`):**
- `dominant_identity_id` = the identity with the largest matched support over the track; ties go to the lower identity ID.
- `dominant_share` = that support ÷ the track's matched support.
- `n_identities`, `n_switches` (changes of matched identity between consecutive matched frames).
- `status`:

| Status | Rule |
|---|---|
| `one_to_one` | `n_identities = 1` and the identity is covered by no other track in the window |
| `id_switch` | `n_identities ≥ 2` |
| `fragment` | `n_identities = 1`, but the identity is matched by ≥ 2 tracks |
| `unmatched_system` | No matched frames |

- Reference identities with no matched frames are listed as `missed_reference`.

**Use downstream:**

| Consumer | Rule |
|---|---|
| CM-01/02 | Matched support = support of `matched` frames only (per D.1: same identity for the frame) |
| CM-07 fragmentation | Number of tracks matched to an identity's co-presence interval |
| Event matching (§9.1) | A system event's pair = the frame-level associations of its person and forklift tracks at `closest_approach_frame`. If either is not `matched` there, the track's `dominant_identity_id` is used. If neither exists, the pair is **unknown**: the event cannot match a reference, is counted as a false alert, and gets diagnostic attribution `tracking` or `perception` (rule tests, Appendix N9) |
| Tracking metrics | HOTA, IDF1 and MOTA computed by TrackEval on the same frame-level association inputs |

**Fixtures** (10 fps, 50 frames, synthetic boxes, *iou_cm* 0.5, *ε_amb* 0.02):

| ID | Scenario | Expected |
|---|---|---|
| FX-ID-1 | One person, one system track, boxes identical | 50 matched; one_to_one; dominant_share 1.0 |
| FX-ID-2 | Track A follows p1 for frames 0–24, then p2 for frames 25–49 (identity switch) | A: n_identities 2, n_switches 1, status id_switch, dominant identity p1 (tie on support 2.5 s each → lower ID) |
| FX-ID-3 | p1 covered by track A (frames 0–19) and track B (frames 25–49); frames 20–24 undetected | A and B fragment; p1 missed_reference on frames 20–24; CM-01 = 4.5/5.0 = 0.9 |
| FX-ID-4 | p2 present, never detected | missed_reference on all frames; CM-01 for p2 = 0 |
| FX-ID-5 | System track on empty floor | unmatched_system |
| FX-ID-6 | p1 and p2 overlap on frames 10–14 so that both have IoU 0.60 and 0.59 with track A | Frames 10–14 ambiguous; excluded from matched and unmatched time |
| FX-ID-7 | Event whose person track is ambiguous at the closest-approach frame and has dominant identity p1 | Event pair resolved to (p1, forklift) via dominant identity |
| FX-ID-8 | Event whose person track is unmatched_system | Pair unknown → false alert; attribution primary_stage = perception (no reference person within *n_miss* frames) |

| Test | Pass condition |
|---|---|
| CT-ID-A1 | FX-ID-1–8 produce exactly the expected statuses, counts and shares |
| CT-ID-A2 | Permuting input order gives identical association tables |
| CT-ID-A3 | RV-01–RV-04 enforced on M1a fixture reports |

**Affected WPs:** WP-08 (reference_class), WP-09 (association, matching, CM), WP-10 (report sections), WP-14.

---

## A6. E-1.2.2 amendment register

| Section of E-1.2.1 | Change | Source |
|---|---|---|
| §2.1, §2.4 | Identity classes; anchor keys; revised keys; ART-ISO; ANC-1 | A1 |
| §5.1 dataset_source | `dataset_kind` | A2 |
| §5.8 reference tables | `reference_class`; `ref_coverage_label` timeline form | A3, A5 |
| §5.9 | match_record, metric_result, completeness_record keys; `reference_class`; new `track_identity_assoc`, `track_identity_summary` | A1, A5 |
| §9.1 | Event-pair resolution via identity association | A5 |
| §10.3 | ERR-ANCHOR-CONFLICT, ERR-SPEC, ERR-EXPORT-CLASS | A1, A2 |
| §11 | Export classes | A2 |
| §12 | Tests CT-NK-01–08, CT-X-01–05, CT-RC-01–03, CT-ID-A1–A3; CT-F-11 superseded | A1–A5 |
| §14 | New parameters *ε_amb*, *n_miss*, *B* (bootstrap replicates) | A5, N |
| New Appendix N | Normative formulas and fixtures | A4 |

No change alters event definitions, units, coordinate frames, sampling or leakage rules, acceptance criteria or reporting semantics.

---

# Part B — Autonomous AI engineering organization

## B1. Hierarchy

| Level | Role | Authority | May not |
|---|---|---|---|
| 1 | **Research Owner** (you) | Scientific scope, methodology, acceptance criteria, resources and spending, measurement-meaning contract changes, milestone gates, external data transmission, irreversible operations | — |
| 2 | **Research Architect** (Claude, in this research thread) | Maintains the contract; answers change requests; proposes amendments; audits milestone reports for methodological consistency | Assign engineering tasks; change approved objectives; approve its own material amendments |
| 3 | **Principal Software Engineer** (team lead agent) | Decomposes milestones; sole routine task assigner; reviews; reassigns; coordinates integration; reports; approves ordinary engineering decisions | Write or edit production code, tests or fixtures; change the contract; select scientific thresholds; suppress QA findings; merge to main |
| 4 | Specialized agents | Execute assigned tasks within their allowed paths | Work without a task card; change files outside their scope; change the contract |

## B2. Roles, scopes and tool permissions

| Role | Owns (writable paths) | Read | Tools | Activated in |
|---|---|---|---|---|
| **Principal** | `mgmt/principal/**` only (task cards, ledger entries, reviews, reports) | Whole repo, logs, test output | Read, Grep, Glob; Bash limited to `git status/diff/log/show`, `git worktree list`, the test runner (read-only execution), ledger tool; Agent/dispatch | A0 onward |
| **Platform & Data Engineer** | `src/rq1/{schema,ids,registry,export}/**`, `tests/unit/{schema,ids,registry,export}/**` | Contract, repo | Read, Edit, Write, Bash (python, pytest, git in own worktree) | M0 |
| **CV & Measurement Engineer** | `src/rq1/{decode,perception,tracking,spatial,substrate,events,adapters}/**`, matching unit-test paths | Same | Same | M0 (decode, substrate, events); M1 |
| **Evaluation & Research SW Engineer** | `src/rq1/{splits,sampling,validation,evaluation,fitness}/**`, matching unit-test paths | Same | Same | M0 |
| **Integration & Build Engineer** | `pyproject.toml`, lockfile, `ci/**`, `bin/**`, merges to `integration/*` and `main` | Same | Bash (git merge, environment build), Edit on owned paths | A0 onward |
| **Independent QA & Contract Verification** | `tests/contract/**`, `tests/qa/**`, `fixtures/expected/**` (independent recomputation), `mgmt/qa/**` | Whole repo | Read, Edit/Write on owned paths, Bash (pytest, python) | A0 onward |
| **E2 Data Feasibility Analyst** | `research/e2/**` (reports only) | Public dataset pages and cards; downloaded metadata only after approval | Read, WebSearch/WebFetch; Bash for metadata inspection; **no dataset downloads without RT approval** | Parallel with M0 |

Fixture **inputs** are written by the owning engineer (WP-02, Platform). Fixture **expected outputs** are written by QA independently from Appendix N. A fixture passes only when the implementation, QA's expectation and Appendix N's stated values all agree.

## B3. Task cards and ledger

**Task card** (`mgmt/principal/tasks/T-<milestone>-<nnn>.md`; immutable once assigned, amended only by appended revisions):

```
id: T-M0-004            milestone: M0          wp: WP-04
title: S1 timestamp resolution and support
assignee: cv-engineer   reviewer: principal     qa: qa-verifier
contract: E-1.2.2 §3.2–3.6, Appendix N3
scope: decode.resolve_timestamps, decode.assign_support, coverage builder
non_goals: quality-model tuning; S2+
inputs: fixtures/clips/* (manifest hash ...)
outputs: S1 artifacts for all CT-T clips
allowed_paths: src/rq1/decode/**, tests/unit/decode/**
depends_on: [T-M0-003]
acceptance: CT-T-01..20 (frame/coverage parts), CT-E-04, CT-RC-01 (coverage part)
evidence: pytest JUnit XML; artifact-id table; reproducibility re-run log
limits: CPU only; max wall time 2 h per attempt; no network
escalate_if: contract silent or conflicting (→ CR); test infeasible; >2 failed QA rounds
```

**Ledger:** append-only JSON Lines, hash-chained, one file per role so that no role can edit another's entries:

```
mgmt/ledger/principal.jsonl   mgmt/ledger/<worker>.jsonl   mgmt/ledger/qa.jsonl   mgmt/ledger/integration.jsonl
```

Each line:

```json
{"seq": 12, "ts": "2026-11-12T14:03:11Z", "actor": "qa-verifier", "task": "T-M0-004", "event": "qa_failed",
 "ref": "mgmt/qa/T-M0-004/round1.md", "commit": "3f2a9c1", "prev_hash": "…", "hash": "…"}
```

Event types: created, assigned, started, submitted, review_passed, review_failed, qa_assigned, qa_passed, qa_failed, correction_assigned, integrated, blocked, escalated, interrupted, resumed, cr_opened, cr_resolved.

Current state is derived by replaying all ledgers in timestamp order (`mgmt/bin/ledger status`). Nothing stores state outside the ledgers and cards, so a session can resume from files alone.

**State machine:**

```
Assigned → In progress → Submitted → Principal reviewed → QA verified → Integrated
                ↑             │review_failed     │qa_failed
                └──── Correction ←───────────────┘
Any state → Blocked (dependency/CR) | Escalated (Level 1/2) | Interrupted → (resume) previous state
```

## B4. Git strategy

| Branch or tree | Purpose | Who writes |
|---|---|---|
| `main` | Verified, integrated state at milestone boundaries | Integration engineer, only after QA pass **and** principal approval |
| `integration/<milestone>` | Accumulates QA-verified tasks | Integration engineer |
| `task/<task-id>` in its own worktree (`../wt/<task-id>`) | One task, one assignee | Assignee only |
| `qa/<task-id>` worktree | QA tests and recomputations for that task | QA only |
| `mgmt` (separate repository) | Ledgers, cards, reviews, reports, CRs | Per-role subdirectories |

Rules:
- One task per worktree. Tasks that need the same files are serialized by the principal.
- Every integration re-runs the full test suite on `integration/<milestone>`, and a regression returns the offending task to Correction.
- Merges are non-fast-forward with the task ID in the message.
- No force-push or history rewrite (irreversible operations need Level 1).

## B5. Review, QA and integration procedure

1. **Submission.** The assignee pushes the task branch and writes a submission report (template B9.1) into its own ledger.
2. **Principal review.** The principal checks the diff for scope (allowed paths), interfaces against the contract, required tests present, evidence complete and no contract change. It writes a review (B9.2). Failure → correction assignment.
3. **QA.** QA works in a separate worktree. It runs contract tests, recomputes expected values independently, runs determinism re-runs and checks invariants, then writes a QA report (B9.3).
   - QA may raise an **escalation** directly to Levels 1 and 2 (`mgmt/qa/escalations/`). The principal cannot close QA escalations.
4. **Integration.** The integration engineer merges into `integration/<m>`, runs the full suite and records commit hashes. A failure reverts the merge and returns the task to Correction.
5. **Milestone gate.** The principal produces the milestone report (B9.4); QA attaches its independent verification summary. The Research Architect audits methodology; the Research Owner approves or rejects the gate.

Integration means "verified and merged". It never means empirically validated.

## B6. Failure recovery and reassignment

| Situation | Action |
|---|---|
| Worker fails QA twice on the same task | Principal reassigns to another qualified worker (or a fresh session of the same role) with the QA reports attached; the original branch is preserved |
| Worker session crashes or the run is interrupted | The ledger shows `started` without `submitted`. On resume, the principal marks the task `interrupted`, inspects the worktree, and either resumes the worker session (if the runtime supports resume) or reassigns with the branch as a starting point |
| Principal session interrupted | A new principal session runs `ledger status`, reads open cards, and continues. No state lives only in conversation memory |
| Repeated environment failure | Integration engineer gets an environment task; dependent tasks marked `blocked` |
| Contract ambiguity | Task `blocked`; CR opened (B7) |

## B7. Escalation and change control

| Matter | Decides |
|---|---|
| Engineering choice inside the contract (internal function design, refactoring, test structure) | Principal |
| New dependency | Principal proposes; licence entry required; Research Owner approves if the licence carries obligations or there is cost |
| Contract ambiguity without measurement-meaning effect | Research Architect resolves (minor E-1.2.x), notifies the Research Owner |
| Anything affecting definitions, units, frames, reference independence, sampling or leakage, acceptance criteria, E2 taxonomy, claims or reporting semantics | Research Architect proposes; **Research Owner approves** before implementation |
| Spending, paid services, downloads of restricted data, external transmission, irreversible operations | Research Owner |
| QA versus principal disagreement | Escalated to Levels 1–2; QA findings are never deleted |

**CR file** (`mgmt/cr/CR-<nnn>.md`): raised_by, task, contract section, problem, evidence, proposed resolution, meaning-affecting (yes/no), affected tables and tests, decision, approver, resulting contract version.

## B8. WP-to-role mapping and team activation

| WP | Responsible role | QA focus |
|---|---|---|
| WP-00 schemas/validators | Platform & Data | VR failing fixtures |
| WP-01 identity | Platform & Data | Reference values, CT-NK, CT-FK |
| WP-02 fixtures (inputs) | Platform & Data (clips: CV) | **QA writes expected outputs** |
| WP-03 S0 | Platform & Data | Anchor stability |
| WP-04 S1 | CV & Measurement | CT-T property tests |
| WP-05 S4 | CV & Measurement | Durations, evidence classes |
| WP-06/06b S5 | CV & Measurement | Truth table, invariants |
| WP-07 splits/sampling | Evaluation & Research SW | Estimator simulation |
| WP-08 validation store | Evaluation & Research SW | Namespaces, RC, reference classes |
| WP-09 evaluation/fitness | Evaluation & Research SW | Appendix N recomputation |
| WP-10 export/reporting | Platform & Data | EXP rules, wording |
| WP-11 M0 integration | Integration & Build | Full-suite determinism |
| WP-12 dataset qualification | E2/Data Analyst (read-only checks) + Integration (download after approval) | Licence and authenticity evidence |
| WP-13 adapters | CV & Measurement | Truth round-trip |
| WP-14 M1a integration | Integration + Evaluation | Pre-registration compliance |
| WP-15 detector benchmark | CV & Measurement | CF-IMG mapping, licence table |
| WP-16 fine-tuning (blocked) | CV & Measurement | Leakage of training manifests |
| WP-17 trackers | CV & Measurement | Identity association fixtures |
| WP-18 M1b integration | Integration + Evaluation | Oracle-vs-detector comparison |
| E2 feasibility (parallel) | E2 Data Feasibility Analyst | — (report to the Research Architect) |

**Activation:**

| Phase | Active | Rationale |
|---|---|---|
| A0 | Principal, one worker (Platform), QA, Integration | Minimum for the ten-step test |
| M0 first wave | Principal, Platform, QA, Integration (+ E2 analyst, read-only) | WP-00–03 are sequential |
| M0 second wave | Add CV and Evaluation once WP-03 is integrated | WP-04/05/06 and WP-07/08 are independent |
| M1 | As needed; E2 analyst continues | — |

The principal records per-task wall time, model usage reported by the runtime, QA rounds and defects found. The M0 report compares delivery speed and defect detection of parallel against sequential waves, so that the value of multiple agents is measured, not assumed.

## B9. Mandatory report templates

**B9.1 Submission (worker):** task ID; commit; files changed (must be inside `allowed_paths`); tests added and run, with results file paths; acceptance criteria mapped to evidence; deviations (none, or a CR ID); known limitations; time and usage.

**B9.2 Principal review:** task ID; commit reviewed; scope check; contract-conformance check per section; evidence completeness; decision (pass / return), with specific defects; no code suggestions beyond describing the defect.

**B9.3 QA report:** task ID; commit; environment digest; tests run (contract, QA, determinism re-run); independent recomputation results vs expected values (with tolerances); invariant checks; verdict; escalation (yes/no).

**B9.4 Milestone report:** milestone; contract version; task table (state, rounds, assignee); test matrix with counts; artifact ID table and re-run equality; open CRs and blockers; the three-status board (Implemented / Verified / Empirically validated with scope); resource use; multi-agent efficiency measures; items needing Level 1 decisions. Every claim links to a file or commit.

---

# Part C — Local execution and orchestration feasibility

## C1. Environment facts and checks

| Item | Status |
|---|---|
| Computer | **Verified (desktop bridge, 9 Nov 2026):** macOS, x64 (Intel), MacBook Air. No folders connected to this session, so nothing else was inspected |
| CPU, RAM, disk, Python, git, FFmpeg and Claude Code versions | **Unverified.** Gate A0 step 0 collects them (C4) |
| GPU | Assume none (Intel MacBook Air). M0 and M1a are CPU work |
| Risk to verify early | As far as I know, recent PyTorch releases no longer ship macOS **x86_64** wheels. This could constrain detector adapters (WP-15) and fine-tuning (WP-16) on this computer. To check at A0; it does not affect M0 |
| Usage and spend | Claude Code consumes subscription usage or API credit. Any API-billed use needs your approval; `claude -p --output-format json` reports estimated cost per run |

## C2. Documented capabilities (checked 9 November 2026)

| Capability | Claude Code (documented) |
|---|---|
| Non-interactive runs | `claude -p` with `--output-format json` or `stream-json`; the result carries `session_id` and estimated cost; exit code is non-zero on failure |
| Resume | `--resume <session_id>` or `--continue` |
| Tool and permission control | `--allowedTools` / `--disallowedTools` (rule syntax, e.g. `Bash(git diff *)`), `--permission-mode` (e.g. `dontAsk`, `acceptEdits`), `--permission-prompts none` for unattended runs, `--max-budget-usd` |
| Reproducible startup | `--bare` skips local hooks, skills, plugins and CLAUDE.md; context is supplied by flags (`--append-system-prompt-file`, `--settings`, `--agents`) |
| Subagents | Defined in `.claude/agents/*.md` with `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `hooks`, `isolation: worktree`; nesting up to three levels (configurable); background execution; up to 20 concurrent by default |

**Not documented, therefore unverified until A0:**
- Per-subagent path-scoped write permissions. This is achievable in principle with a `PreToolUse` hook in the subagent's `hooks` and must be demonstrated.
- Subagent survival across an interruption of the principal session. Assume it does not survive.

## C3. Options

| Option | How it works | Pros | Cons |
|---|---|---|---|
| **O1. Principal session + subagents** | Principal = interactive Claude Code session, restricted by settings (no Edit/Write outside `mgmt/principal/`). Workers and QA = project subagents (`.claude/agents/`) with `isolation: worktree`, role-specific tools and path-guard hooks | No custom code; documented worktree isolation; one ledger convention | Subagents live inside the principal session, so an interruption ends in-flight work (recoverable from the ledger and branches) |
| **O2. Principal + headless worker processes** | Principal starts workers as separate `claude -p … --output-format json` processes in their worktrees, through a small dispatch script that pins flags and writes outputs into the ledger; workers resume with `--resume <session_id>` | Workers survive a principal interruption; resumable by session ID; cost and exit codes captured per worker | Needs a dispatch script (≈100 lines, written as an Integration task); long runs must be started in the background |
| **O3. Custom orchestrator (Agent SDK)** | A Python service drives the agents, queues and state | Most control | Large engineering effort; not justified for 1–6 agents |

## C4. Recommendation and Gate A0

**Start with O1.** It needs no custom orchestration code, and every element it relies on is documented. Persistence comes from the ledger and git, not from agent memory.

If A0 shows that O1 cannot meet steps 9–10 (interruption recovery), move to **O2**. Its dispatch script becomes an Integration task with its own review and QA, so the principal still writes no code. O3 is not recommended.

**A0 step 0: environment inventory** (read-only; run by the Integration engineer or by you; nothing installed without approval):
- `sw_vers`, `sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize`, `df -h ~`
- `python3 --version`, `git --version`, `ffmpeg -version`
- `claude --version`, `claude --help`
- Whether a PyTorch build exists for this platform

**Gate A0 test.** The bounded task is **T-A0-001**: implement the JCS-plus-SHA-256 helper `ids.b32_id(prefix, obj)` reproducing the §2.3 reference value for track 1, with one unit test. QA **deliberately** uses the A1 fixture variant with a float field (`1e-7`), which a naive `json.dumps` implementation serializes wrongly. This produces a genuine failure rather than a staged one.

| Step | Demonstration | Evidence required |
|---|---|---|
| 1 | Principal receives T-A0-001 (card written by the Research Owner or Architect) | Card and `created` ledger entry |
| 2 | Principal assigns it to the Platform worker | `assigned` entry; worktree `task/T-A0-001` exists |
| 3 | Worker submits changed files and test output | Submission report; commit hash; JUnit XML |
| 4 | Principal reviews without editing | Review file; `git log` shows no principal commits in `src/`; hook log shows any blocked write attempts |
| 5 | Principal assigns QA | `qa_assigned` entry; QA worktree |
| 6 | QA finds the float-serialization failure | QA report with the failing case; `qa_failed` entry |
| 7 | Principal reassigns the correction | `correction_assigned` entry referencing the QA report |
| 8 | QA passes; Integration merges into `integration/A0` | `qa_passed`, `integrated` entries; merge commit; full suite passes |
| 9 | Controlled interruption: the Research Owner kills the principal session between steps 6 and 7; a new session runs `ledger status` and continues | Ledger shows `interrupted` and `resumed`; the task state is correct after the restart |
| 10 | Reproducible history and report | `ledger replay` reproduces the state; milestone report B9.4 generated from files |

**Pass criteria:**
- All ten steps have file evidence.
- The principal has zero writes outside `mgmt/principal/`.
- QA's failure record cannot be modified by the principal.
- Replaying the ledger on a fresh clone gives the same task state.


---

# Appendix N — Normative formulas and fixtures (part of E-1.2.2)

Tolerances unless stated otherwise:
- IDs, counts and labels: exact.
- Durations: exact to 1 µs (sums of resolved support).
- Floats from closed formulas: absolute 1e-9.
- Geometry: absolute 1e-6 m.
- Bootstrap intervals: identical for the same seed and B. Across implementations, endpoints within 0.01 for B = 2000 (test B = 200).

## N1. Episode-level classification fixtures (flag level)

Common: 10 fps; POW of 20 eligible frames (0–19), all `detected`. TEST-ONLY values from Package F §3. Run-length notation `1×20`. Contact inputs are given at the closest-approach (CA) frame.

| ID | P | M | C_any | E | Q | minclr (m), σ | Overlap at CA | Contact cue | Expected contact | Expected K | Expected labels |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 1×20 | 0×20 | 0×20 | 0×20 | 1×20 | 1.10, 0.05 | no | no | none_observed | 0 | O |
| T2 | 1×20 | 1×20 | 0×20 | 0×20 | 1×20 | 1.10, 0.05 | no | no | none_observed | 0 | H |
| T3 | 0×20 | 2×20 | 1×20 | 0×20 | 1×20 | 2.35, 0.05 | no | no | none_observed | 0 | PC |
| T4 | 1×20 | 1×20 | 1×20 | 0×20 | 1×20 | 0.80, 0.05 | no | no | none_observed | 0 | H, PC |
| T5 | 1×20 | 1×20 | 0×20 | 0×8,1×3,0×9 | 1×20 | 0.60, 0.05 | no | no | none_observed | 1 | H, NM |
| T6 | 1×20 | 1×20 | 0×20 | 0×20 | 1×20 | −0.05, 0.05 | yes | no | undetermined | 1 | H, UD |
| T7 | 1×20 | 1×20 | 0×20 | 0×20 | 1×20 | −0.10, 0.05 | yes | yes | suspected | 1 | H, CT |
| T8 | 1×20 | 0×20 | 0×20 | 0×20 | 1×20 | −0.05, 0.05 | yes | no | undetermined | 1 | O (review_route = true) |
| T9 | 1×20 | 0×20 | 0×20 | 0×20 | 1×20 | −0.10, 0.05 | yes | yes | suspected | 1 | O, CT |
| T10 | 0×20 | 2×20 | 1×20 | 2×20 | 1×10,0×10 (CA at frame 15) | 1.20 (frames 0–9 only), 0.05 | unknown | no | undetermined | 2 | PC, IE |
| T11 | 1×20 | 1×20 | 0×20 | 2×20 | 1×10,0×10 (CA at frame 15) | 1.05 (frames 0–9), 0.05 | unknown | no | not_assessable (no usable frames within ±*w_e*/2 of CA) | 2 | H, IE |
| T12 | 1×3,0×10,1×7 | 1×20 | 0×20 | 0×20 | 1×20 | 1.10, 0.05 | no | no | — | — | **Two episodes** (gap of 10 > *m_gap* 5): [0,3) span 0.3 s and [13,20) span 0.7 s; both H |
| T13 | 1×1,0×19 | 1×20 | 0×20 | 0×20 | 1×20 | — | — | — | — | — | Episode [0,1), span 0.1 s < *t_min* 0.2 → `discarded_episode` |

Notes:
- T6 and T8: −0.05 ≤ 0 means overlap. That gives `undetermined`, which overrides the σ test.
- T7: overlap plus cue gives `suspected`.
- **σ rule (normative):** if σ is null, the σ margin uses σ = 0 and `sigma_status = not_estimated` is recorded.

## N2. Geometry-to-flag fixtures (calibrated ground plane, oracle positions)

Common to all three fixtures:
- 10 fps.
- Person: disc of radius 0.30 m. Forklift: oriented rectangle 2.0 × 1.0 m, centred, yaw 0, moving along +x.
- Clearance = distance from the person centre to the rectangle − 0.30.
- σ = 0.05 m on positions; speeds are exact.

| ID | Setup | Expected per frame | Expected episode |
|---|---|---|---|
| G1 (T1) | Person (0, 1.90); forklift at (0, 0), v = 0; 50 frames | clearance 1.10; P = 1; M = 0; C_by_R3 = 0 (predicted 1.10 ≥ 1.0) | One episode [0,50), detected duration 5.000 s (final frame δ_nom), labels O |
| G2 (T2) | Person (0, 1.90); forklift x(t) = −2.5 + 1.0·t, t ∈ {0, 0.1, …, 4.9} | clearance = 1.10 for \|x\| ≤ 1; otherwise √((\|x\|−1)² + 1.96) − 0.30 (e.g. 1.7518 at x = −2.5). P = 1 on all frames; M = 1; C_by_R3 = 0 | One episode [0,50), labels H, minclr 1.10 |
| G3 (T3) | Person (5.0, 0); forklift x(t) = 1.5·t, 10 frames (t ≤ 0.9) | clearance = 3.70 − 1.5t (≥ 2.35); P = 0; constant-velocity predicted minimum over τ = 2 s = 0.70 − 1.5t (< 1.0); C_by_R3 = 1 | One episode [0,10), labels PC, minclr 2.35 |

## N3. Support and duration fixtures

FX-CLIP-A–D as in the clarification §2.3 (expected detected support 0.100 / 0.067 / 0.033 / 0.133 s with frames at 0, 33, 66, 100 ms). Exact expected values: A 0.100000, B 0.067000, C 0.033000, D 0.133000. These assume δ_nom = 0.033 s and the final frame credited δ_nom (100 → 133 ms).

## N4. Matching and denominators

- **Temporal IoU** = |A ∩ B| ÷ |A ∪ B| on timeline intervals.
- **Onset error** = system onset − reference onset (s).
- **Weight** = round(IoU × 10⁶); candidates require IoU ≥ *iou_m*, matching pair identity (A5.2) and the same label group.
- **Solver:** `scipy.optimize.linear_sum_assignment(maximize=True)` on a matrix with rows = references sorted by (t_onset_us, ref_event_id) and columns = system events sorted by natural key. Ties are resolved by an integer composite weight. For row r and column c (0-based), the weight is `W = round(IoU·10⁶)·K + b(r, c)`, with `b(r, c) = (n_rows − r)·(n_cols + 1) + (n_cols − c)` and `K = n_rows²·(n_cols + 1) + 1`. Total IoU therefore dominates; among equal-IoU solutions, earlier references, then lower system keys, are preferred. This composite weight is the normative tie rule and replaces the prose tie order of E-1.2.1 §9.1.
- **Classes:** unmatched system events with IoU > 0 to a matched reference → `duplicate_alert`; other unmatched system events → `false_alert`; unmatched references → `miss`; references with only abstained (IE-only) system overlap → `abstained_miss`.
- **FX-TIE:** r1 [0,1) s, r2 [1,2) s, s1 [0.5,1.5) s. IoU(s1, r1) = IoU(s1, r2) = 0.5/1.5 = 0.3333. Expected: s1 → r1; r2 = miss.

**Per window i:**
- aᵢ = assessable references
- mᵢ = matched references
- sᵢ = non-abstained system events
- m⁽ˢ⁾ᵢ = matched system events
- fᵢ = false + duplicate alerts
- uᵢ = usable eligible support hours
- cᵢ = assessable references receiving a non-abstained decision

**Metric formulas:**

| Metric | Formula |
|---|---|
| EV-M1 headline recall | Σwᵢmᵢ ÷ Σwᵢaᵢ |
| EV-M2 headline precision | Σwᵢm⁽ˢ⁾ᵢ ÷ Σwᵢsᵢ |
| EV-M4 coverage | Σwᵢcᵢ ÷ Σwᵢaᵢ |
| EV-M6 conditional recall | Σwᵢmᵢ ÷ Σwᵢcᵢ (always printed with EV-M4) |
| EV-M7 false-alert burden | Σwᵢfᵢ ÷ Σwᵢuᵢ (per hour) |
| EV-M3 abstention rate | Abstained episodes ÷ all episodes; abstained support ÷ POW support |
| EV-M5 IE miss rate | abstained_miss ÷ assessable |
| EV-M8 localization | Median and P90 of \|onset error\| and \|offset error\| over matched pairs; mean temporal IoU |
| EV-M9 contact cross-tab | 4 × 3 table: automated contact state × A-layer visible contact |
| EV-M10 | Counts of system decisions on unobservable references |
| EV-M11 duplicate rate | Duplicate ÷ (matched system + duplicate) |
| EV-M12 | Cohen's κ between automated G2 label (NM/UD/CT/none) and adjudicated expert label, Tier 1 and Tier 2 separately (requires the `independent_expert_judgment` class) |

For RES windows, wᵢ = 1/πᵢ; unweighted versions set wᵢ = 1.

## N5. Estimators, intervals and the weighted fixture

| Item | Normative definition |
|---|---|
| Horvitz–Thompson total | T̂ = Σ wᵢ yᵢ |
| Ratio | R̂ = Σ wᵢ yᵢ ÷ Σ wᵢ xᵢ |
| Kish n_eff | (Σ wᵢ)² ÷ Σ wᵢ² |
| Target A interval | Stratified window bootstrap: in each stratum h, draw n_h windows with replacement; recompute R̂; B replicates; percentile interval (2.5%, 97.5%); RNG = numpy PCG64 seeded from the evaluation config |
| Target B interval | Cluster bootstrap: draw leakage groups with replacement (stratified by data origin), carry window weights, recompute R̂; same percentiles |
| Wilson (independent units only) | (p̂ + z²/2n ± z√(p̂(1−p̂)/n + z²/4n²)) ÷ (1 + z²/n), z = 1.959964 |
| Bland–Altman | dⱼ = system − reference; bias = mean(d); LoA = bias ± 1.96·SD(d) (n − 1 denominator) |
| ICC | ICC(2,1), two-way random effects, absolute agreement, single measure (Shrout & Fleiss) |
| Cohen's κ | (p_o − p_e) ÷ (1 − p_e); Krippendorff's α (nominal) for more than two raters |
| Paired comparison | Paired bootstrap over the same windows or clusters; difference of R̂ |

**FX-W (weighted recall):**
- Strata h1 (N = 10, n = 2, π = 0.2, w = 5) and h2 (N = 4, n = 2, π = 0.5, w = 2).
- Windows (a, m): h1 = (3, 2), (1, 1); h2 = (2, 2), (4, 2).

Expected:
- Weighted recall = (5·3 + 2·4) ÷ (5·4 + 2·6) = 23/32 = **0.71875**.
- Unweighted = 7/10 = **0.70**.
- Kish n_eff over the four windows = 196/58 = **3.3793103448**.

## N6. Completeness metrics (D.1 CM, normative)

Support s(·) is clipped eligible support (E-1.2.1 §3.4); "matched" means a `track_identity_assoc` status of `matched` for the same identity on that frame. Each metric is computed on both bases: detected only, and detected + inferred.

| ID | Numerator | Denominator |
|---|---|---|
| CM-01 | s(person frames matched to the reference identity) | s(reference person-visible frames) |
| CM-02 | Same for forklifts (also restricted to reference moving frames) | s(reference forklift-visible frames) |
| CM-03 | s(reference pair co-visible frames covered by a POW whose tracks are matched to that pair) | s(reference pair co-visible frames) |
| CM-04 | Reference pairs with ≥ 1 such POW frame | Reference pairs |
| CM-05 | s(POW frames not matched to any reference pair) | s(POW frames) |
| CM-06 | Σ over bands \|AI time-in-band − reference time-in-band\| per pair; report bias and LoA (Bland–Altman) | — |
| CM-07 | Number of POWs covering a reference pair's co-presence interval | Per interval |
| CM-08 | s(POW frames with `clearance_state ≠ measured`) | s(POW frames) |
| CM-09 | s(inferred frames whose track is matched to a present reference object) | s(inferred frames) |
| CM-10 | s(reference co-presence frames where the system pair-frame is `insufficient`) | s(reference co-presence frames) |

**FX-CM:** reference person visible on 100 frames at 10 fps (10.0 s). The system track is matched on 60 frames and missing on 40 → CM-01 = **0.600**. With the forklift always matched, CM-03 = 0.600 (D1-AC-04).

## N7. Geometry validation (GV)

| ID | Definition |
|---|---|
| GV-01 | eⱼ = ‖p̂ⱼ − pⱼ‖ (m); report mean bias vector, RMSE, P95, per stratum |
| GV-02 | Reprojection RMSE (px) of reference 3D points; ground error (m) on held-out floor points |
| GV-03 | Δclearance and label flip rate when the footprint length and width are swept over the declared range |
| GV-04 | Clearance from the prior footprint minus clearance from the simulator 3D box footprint |
| GV-05 | d²ⱼ = eⱼᵀ Σⱼ⁻¹ eⱼ (2D). Coverage at χ²₂ quantiles 2.2789 (68.27%) and 6.1801 (95.45%). Inflation factor = √(median(d²) ÷ 1.3863), applied if > 1 |
| GV-06 | Spearman ρ between `image_gap_norm` and `clearance_m`; disagreement rate between R1-P and R2-P |
| GV-07 | Speed error (m/s), bias and RMSE, per smoothing window *w_v* |
| GV-08 | Predicted minimum clearance at horizon τ minus realized minimum clearance over [t, t + τ] |

## N8. Reliability (MR)

| ID | Definition |
|---|---|
| MR-01 | Exact stages: byte-identical payload hashes. S2: box IoU of matched boxes ≥ *iou_rep*, \|Δscore\| ≤ *s_rep*, flips counted |
| MR-02 | Cross-camera agreement (M2 only): κ on event detection, ICC(2,1) and Bland–Altman on duration and minimum clearance |
| MR-03 | Bland–Altman and ICC(2,1): episode duration vs reference duration; time-in-band vs B-layer time-in-band |
| MR-04 | Scenario count ÷ validated count per window (ratio estimator, Target A interval) |
| MR-06 | κ between automated coverage state and reference coverage state, on 0.1 s time cells |
| MR-07 | A1, A2, A3 violation rates against reference physical interactions (M2) |
| MR-08 | For each parameter grid point g: change in counts, durations and label sets relative to the base configuration. `label_stability_frac` = share of grid points with an identical label set for the episode (episodes matched across configurations by temporal IoU ≥ *iou_m* within the same POW). Elasticity = (ΔY/Y) ÷ (Δθ/θ) at adjacent grid points |
| MR-09, MR-10 | As MR-08 for the footprint sweep and for calibration perturbation (homography perturbed by its estimated covariance, 100 draws, seeded) |
| MR-11 | = GV-05 |
| MR-12 | As MR-08 for *m_gap* and *t_min* |

## N9. Error attribution rule tests (diagnostic, in pipeline order)

1. **evidence_unavailable:** the reference is unobservable at the closest-approach frame, or coverage there is not usable.
2. **perception:** no system detection of the person or forklift with IoU ≥ *iou_cm* within ±*n_miss* frames of the reference closest-approach frame.
3. **tracking:** detections are present, but the identity association at the reference CA frame is not `matched` for both objects, or a POW break lies within the reference interval.
4. **geometry:** association is correct, but \|clearance error\| > *k_σ*·σ, or speed error flips M, at a frame where the flag decision differs from the reference-geometry decision.
5. **event_reasoning:** flags computed from reference geometry would trigger (or not) differently from the configuration's output given correct flags.
6. **linkage:** M2 only.
7. **reference_ambiguity:** the reference is Tier 2 or unsure.

The first failing test is `primary_stage`; later failing tests become `secondary_factors`. If no test fails, or tests conflict, the result is `unresolved`. On synthetic data, oracle substitution (2³ combinations of perception, tracking and geometry) assigns `verified_*` as specified in D.1 §7.2.

## N10. Detection and tracking metrics

| Metric | Normative implementation |
|---|---|
| AP@0.5, AP@0.5:0.95 | COCO 101-point interpolation (pycocotools), per class |
| Recall at fixed FP per frame | Operating point at the score threshold giving *fp_target* false positives per frame |
| ECE | 15 equal-width confidence bins; Σ (n_b/N)·\|acc_b − conf_b\| |
| HOTA, IDF1, MOTA, ID switches, fragmentation | TrackEval implementations, with the A5.2 frame-level association inputs and IoU threshold *iou_cm* |
| Pair-window fidelity | Reference interactions covered by exactly one POW ÷ reference interactions |

---

## Gate F.1 — decisions requested

1. **F1-A:** Approve the contract corrections A1–A5 and Appendix N as E-1.2.2.
2. **F1-B:** Approve the governance protocol (Part B), including QA's direct escalation channel and the principal's write restriction.
3. **F1-C:** Approve starting Gate A0 with **O1** (Claude Code principal and subagents), falling back to O2 only if interruption recovery fails.
4. **F1-D:** Authorize A0 step 0, the read-only environment inventory. It needs one project folder connected to this session (or you run the commands and send me the output).
5. **F1-E:** Confirm the billing route for agent usage (subscription or API key) and any usage cap.

I've stopped here. No coding agents, downloads or paid services have been started.

**Sources (Part C):** [Claude Code — run programmatically (headless)](https://code.claude.com/docs/en/headless.md) · [Claude Code — subagents](https://code.claude.com/docs/en/sub-agents.md)
