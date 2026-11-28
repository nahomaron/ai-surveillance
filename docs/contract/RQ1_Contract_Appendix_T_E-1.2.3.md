# RQ1 Contract Appendix T — Rule, Test and Fixture Texts (E-1.2.3)

**Date:** 9 November 2026
**Status:** **Normative.** Together with E-1.2.1 (FROZEN), F.1 Part A and Appendix N, this forms contract **E-1.2.3**.
**Responds to:** CR-001 and decision D-1, raised by the implementation agent at T-01.
**Defect:** E-1.2.1 cited many rule, test and fixture IDs whose text lived only in the source packages (E, E.1, the E.1 Errata and the Clarification). The agent was right not to consult those packages.

## T0. How to use this appendix

- **Text:** this appendix supplies the normative text for every validation rule, invariant, contract test and record fixture ID cited by E-1.2.1 and F.1. It was extracted mechanically from the source packages, then reconciled with later corrections.
- **Status column:**
  - **active:** the text applies as written.
  - **amended:** the replacement text in this table applies.
  - **superseded:** do not implement.
  - **milestone Mx:** implement in that milestone, not earlier.
  - **note:** where the content now lives.
- **Precedence:** F.1 Part A and Appendix N > this appendix > E-1.2.1 body. This appendix only supplies text. If it contradicts a definition in F.1 or E-1.2.1, raise a CR.
- **Old names:** text from Package E uses some older names. Read them as:

| Old name | Current name |
|---|---|
| `video`, `video_id` | `source_file` / `recording` (`src_`, `rec_`) |
| `t_video_s` | `t_resolved_s` (per frame) and `t_*_tl_s` (intervals) |
| session time | timeline time |
| `duration_s` | `span_s` (extent) and support-based duration fields |
| `dt_s` | `support_s` |
| E-xx table numbers | the table names of E-1.2.1 §5 |
| "Section 5.0" | E-1.2.1 §2.5 |

- **Defined inside invariant rows:** tests CT-ID-01–07, CT-S-07–10, CT-T-09–13 and CT-F-09/10 are defined in the "Normative text" cells of the ID, SP, TI and FT invariants. The cell contains the invariant, then "—", then the test.
- **CL-INV-01–11:** the classification invariants are in E-1.2.1 §6.
- **New in F.1:** CT-NK, CT-X, CT-RC and CT-ID-A tests and FX-ID/FX-RC fixtures are in F.1 Part A. Appendix N fixtures are in F.1 Appendix N.

## T1. Rules, invariants, tests and fixtures

### Validation rules (VR-E)

| ID | Normative text | Source | Status |
|---|---|---|---|
| VR-E-001 | Every Parquet file carries the key-value metadata of E-1.2.1 §2.5 and no execution-specific key; its `schema_version` major is supported by the reader | E | amended |
| VR-E-002 | Every nullable field that is null has a valid `*_null_reason`; non-null fields have no reason | E | active |
| VR-E-003 | No NaN or ±Inf in any float column; no sentinel values (e.g., −1 for unknown) | E | active |
| VR-E-004 | Every ID is recomputable according to its identity class (F.1 A1): anchor, configuration, observation (from `art_` and natural key), human (UUIDv7), execution (UUIDv7) | E | amended |
| VR-E-005 | A file has exactly one `data_origin`; real and synthetic rows never share a file or an aggregate | E | active |
| VR-E-010 | Over **eligible** frames, `t_resolved_s` is strictly increasing and `frame_index` is contiguous 0…n_eligible−1; every frame has `support_s ≥ 0` (§3.2–3.3) | E | amended: Replaces the `pts`/`dt_s` form |
| VR-E-011 | All intervals satisfy start < end (half-open). `frame_index` fields lie in [0, n_frames_eligible]; timeline intervals lie inside their timeline's extent | E | amended |
| VR-E-012 | Coverage segments tile each (timeline, camera) extent exactly once (= TI-01) | E | amended: Was per-video frame tiling |
| VR-E-013 | Activity segments tile the same extent as coverage; `not_evaluated` exactly where coverage ∈ {not_recorded, gap_unobserved, unusable} (= CD-01/CD-02) | E | amended |
| VR-E-014 | World-frame quantities are non-null only if `geometry_method` ∈ {ground_plane_homography, full_camera, multi_view, simulator_truth}, the calibration is not `failed`, and the calibration tier permits the computation (§4.2) | E | amended |
| VR-E-015 | `clearance_m` null iff `clearance_state ≠ measured`; `footprint_overlap = 1` iff `clearance_m ≤ 0` when measured | E | active |
| VR-E-016 | Exposure-profile sums of E-1.2.1 §5.5 hold: Σ detected bands + Σ inferred bands + `t_clearance_unknown_s` + `t_insufficient_s` = `t_total_support_s`; the five motion fields + `t_insufficient_s` = `t_total_support_s`; tolerance 1 µs | E | amended: Field names and tolerance updated (Appendix N) |
| VR-E-017 | Every POW has exactly one exposure profile per band scheme | E | active |
| VR-E-018 | `sigma_status = calibrated` only with a GV-05 evidence reference for the stratum | E | active |
| VR-E-020 | No geometry from calibrations with `quality_state = failed` | E | active |
| VR-E-021 | Units: fields with `_m`, `_s`, `_mps`, `_rad`, `_kg` hold values in those units; dataset values converted at S0/S4 with `unit_status` recorded | E | active |
| VR-E-030 | E1 episode and candidate-event labels satisfy CL-INV-01–11 (contract §6; Appendix N1) | E | amended |
| VR-E-031 | Edge `L` (`linked_calibrated`) requires: both cameras calibrated to the same world frame with `quality_state ≠ failed`; both recordings on the same `aligned_session` timeline with non-null clock σ; √(σa² + σb²) ≤ *τ_sync*; median Mahalanobis ≤ *χ²_link* (§7) | E | amended: `assumed_zero` no longer exists |
| VR-E-032 | Candidate-event labels recomputed from event flags (never unioned) | E | active |
| VR-E-033 | ~~Superseded ("bound" removed) — E.1 §5~~ | E.1 | superseded: By LK-07 (wording is always `scenario_count`) |
| VR-E-034 | No string "observed contact" or equivalent value in any Observation-store field | E | active |
| VR-E-040 | The Observation store and OBX exports contain no `reference_verified_absent`; `observed_no_detection` never maps to zero exposure | E | active |
| VR-E-041 | Forbidden E2/RQ2 fields absent (potential energy, fall probability, impact energy, severity, safety score, indicator weight, rate per establishment, OSHA/NAICS/establishment identifiers) | E | active |
| VR-E-050 | RES sampling plans use only pre-system stratifiers; V0 run manifest shows no Observation inputs other than coverage | E | active |
| VR-E-051 | Headline metrics (EV-M1, M2, M7) and all frequency/duration/per-hour aggregates use RES windows only | E | active |
| VR-E-052 | Reference coverage spans tile each annotated camera's part of a window; `reference_verified_absent` only in exhaustive, assessable windows | E | active |
| VR-E-053 | `reference` namespace records are blind (`blind_to_system = true`, `shown_system_output = false`) | E | active |
| VR-E-054 | Reference windows locked before the first S8 run on their partition (lock time < run start) | E | active |
| VR-E-060 | Split check per tier (§8): T1 no leakage group crosses partitions; T2a as T1 plus test camera placements absent from training; T2b only declared shared sessions may cross and `shared_scene_content = true`; T3 no test-site recording in any training, tuning or selection manifest | E | amended |
| VR-E-061 | `attribution_status = verified_*` only for synthetic data with oracle runs referenced | E | active |
| VR-E-062 | Conditional metrics carry a coverage companion | E | active |
| VR-E-063 | ~~Superseded — E.1 §6.4~~ | E.1 | superseded: By FT-01–FT-11 and F.1 A4 scoped statuses |
| VR-E-070 | Every real-origin `source_file` has a retention policy and every derived clip an access class | E | amended: Table renamed |
| VR-E-071 | Real-origin clips cannot carry `publishable_synthetic_only` | E | active |

### Contract tests from Package E (CT-E)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-E-01 | Schema conformance of every produced file — all — VR-E-001–005 | E | active |
| CT-E-02 | ~~Deterministic IDs and hash-equal re-runs for exact stages — FX-01 — Identical IDs and file hashes~~ | E | superseded: By CT-ID-02 / CT-FK-04 |
| CT-E-03 | ~~Timebase from PTS — FX-10 — Durations equal PTS sums; gap visible as larger `dt_s`; no fps arithmetic~~ | E | superseded: By CT-T-01–08 |
| CT-E-04 | Coverage independent of detector — FX-10, FX-11 — Coverage identical with detector disabled (D1-AC-03) | E | active |
| CT-E-05 | Null semantics — FX-07 — All world fields null with `uncalibrated`; no sentinel values | E | active |
| CT-E-06 | Signed clearance and overlap — FX-04 — `clearance_m ≤ 0` rows have `footprint_overlap = 1` | E | active |
| CT-E-07 | Exposure sums — FX-01–FX-06 — VR-E-016 | E | active |
| CT-E-08 | Exposure present regardless of labels — FX-02, FX-06 — Profiles and episode exposure fields populated | E | active |
| CT-E-09 | Classification truth table: labels, contact states and K exactly as Appendix N1 T1–T13 | E | amended |
| CT-E-10 | Invariant property test — random flag sequences — CL-INV-01–11 hold | E | active |
| CT-E-11 | Activity-state separation — FX-11 — Obs store has no `reference_verified_absent`; export shows `observed_no_detection` with completeness companion, not zero | E | active |
| CT-E-12 | Substrate immutability — FX-01 + second config — Substrate bytes unchanged (C1-AC-01) | E | active |
| CT-E-13 | Providers vs configuration — FX-01 with R3+R4 — One episode, two provider flags (C1-AC-02) | E | active |
| CT-E-14 | Early trigger — FX-03 — Episode opens before any `P` frame (C1-AC-03) | E | active |
| CT-E-15 | Cross-camera linkage — FX-08 — S_VIEW = 2, S_LINK = 1 | E | milestone M2 |
| CT-E-16 | Counting-scenario wording — FX-09 — Wording `scenario_count`; A2 `unverified` | E | milestone M2: Expected wording is `scenario_count`, never `bound` |
| CT-E-17 | Event-level relabelling — FX-08 with O in one view, H in other — Event labels H only (CL-INV-01 at event level) | E | milestone M2 |
| CT-E-18 | Sampler isolation — V0 run — Manifest inputs exclude S2–S5 artifacts (C1-AC-08) | E | active |
| CT-E-19 | Weighting and ECS exclusion — FX-15 + RES windows — ECS absent from headline and frequency metrics; weights = 1/π | E | active |
| CT-E-20 | Matching determinism — permuted inputs — Identical `match_record` set (C1-AC-09) | E | active |
| CT-E-21 | Abstention counts as miss — synthetic abstention increase — Headline recall decreases (C1-AC-10) | E | active |
| CT-E-22 | Attribution — FX-16 — `verified_oracle_joint`, one primary stage | E | active |
| CT-E-23 | Leakage — FX-14 — ERR-LEAKAGE | E | active |
| CT-E-24 | Validation separation — any confirmed episode — Episode labels unchanged after status entries; status log hash chain verifies | E | active |
| CT-E-25 | Namespace guard — candidate-review label offered as reference — ERR-NAMESPACE | E | active |
| CT-E-26 | E2 forbidden fields and nullable metadata — FX-12 — No forbidden fields; mass null `not_supplied`; pipeline completes | E | amended: Revised FX-12: E2 has **no episodes**; the test checks `load_state` and `e2_occupancy_profile` records, nullable mass (`not_supplied`), and absence of forbidden fields |
| CT-E-27 | Export forbidden content — OBX from FX-01–FX-12 — ERR-FORBIDDEN-FIELD not raised; scan finds no forbidden names or values | E | amended: Applies to `export_class = research`; fixture exports follow CT-X-01–05 (F.1 A2) |
| CT-E-28 | Lineage: every metric row is traceable through `art_` IDs to `source_file.sha256` (`src_`) | E | amended |
| CT-E-29 | Fitness guard: synthetic-only evidence marked `technically_validated` is rejected (FT-01, FT-03) | E | amended |
| CT-E-30 | Schema evolution — minor-version reader with added column — Reads, ignores unknown column; major mismatch fails | E | active |

### Time tests (CT-T)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-T-01 | VFR — 10 s clip, frame interval alternating 33/50 ms — Durations equal support sums; no fps arithmetic | E.1 | active |
| CT-T-02 | Reordered decode — Stream with B-frames (decode order ≠ presentation) — `frame_index` follows PTS; `ts_status = reordered` where applicable; track geometry unchanged versus a re-muxed all-I-frame copy | E.1 | active |
| CT-T-03 | Duplicate PTS — Two frames share a PTS — Second has `support_s = 0`; no double-counted time | E.1 | active |
| CT-T-04 | Internal gap — 4 s dropout inside a file — One `gap_unobserved` segment of 4 s − `δ_nom`; POW across it split; exposure excludes it | E.1 | active |
| CT-T-05 | 15 undecodable frames: indexed, ineligible, `decode_ok = false`; each **timed** corrupt frame keeps its own support (`excluded_own_support`), which becomes `unusable` coverage; no detections on them | E.1 | amended: ST-1 (Clarification) replaces 'zero support' |
| CT-T-06 | Final frame — Any clip — One `final_assumed` frame; sensitivity variant changes totals by exactly `δ_nom` | E.1 | active |
| CT-T-07 | Two files from one camera, 60 s apart, **on an `aligned_session` timeline with a declared extent**: one `not_recorded` segment of 60 s; no frame indices assigned to it. Without alignment evidence the files get two `recording_local` timelines and no gap segment (CT-T-11) | E.1 | amended: TI-11 |
| CT-T-08 | Untimed stream — > *f_untimed* frames without timestamps — `ERR-TIMESTAMPS`; no artifact marked complete | E.1 | active |
| CT-T-14 | Case A clip, person and forklift detected in all eligible frames — Coverage has an `unusable` segment [33,66); POW `t_detected_s` = 0.100; `t_insufficient_s` = 0.033; reference-observable time = 0.100 | Clar | active |
| CT-T-15 | Case B clip — `timing_uncertain` region [0,66); POW detected = 0.067; nothing in [0,66) counted as detected or inferred | Clar | active |
| CT-T-16 | Case C clip (B-frames, DTS-only frame) — Frame treated as untimed; detected = 0.033 | Clar | active |
| CT-T-17 | Case D clip — Frame accepted; `substituted` share = 0.033 s reported; detected = 0.133 | Clar | active |
| CT-T-18 | Case A with the person missed on f2 (eligible, undetected) inside a POW — f2 support counted `inferred` (bridged); f1 support stays `insufficient` (ST-6) | Clar | active |
| CT-T-19 | Exposure profile on cases A–D — Detected and inferred band times contain no support from `unusable` or `timing_uncertain` intervals; Σ classes = total support | Clar | active |
| CT-T-20 | Property test: 500 random clips with random corruption, missing timestamps, duplicates and reordering — For every clip: (a) no support interval overlaps another; (b) every `unusable`/`timing_uncertain` interval is disjoint from all detected and inferred support; (c) detected support ≤ support of eligible frames; (d) system and reference observable time agree on the same frame eligibility | Clar | active |

### Split and sampling tests (CT-S)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-S-01 | Clean run — Three SDG runs, disjoint — v1 frozen; audit finds nothing; no revision | E.1 | active |
| CT-S-02 | Two recordings, metadata-unrelated, in train and test; annotation links one interaction across them. Audit violation with `discovery_basis = sampled_annotation`; v2 moves the group to train (PR-01); affected test strata get `requires_resample` (R-3); any earlier S8 result on the affected partition (validation runs only — R-2 forbids test runs before the audit) is `invalidated_leakage` | E.1 | amended: Reconciled with SP-08/R-2 |
| CT-S-03 | Monotone test — Group spanning validation and test — Moves to validation; test windows from it leave the test domain | E.1 | active |
| CT-S-04 | Revision without violation — Attempted manual revision — Rejected | E.1 | active |
| CT-S-05 | T2b declared share — Same sessions, different cameras, declared — Audit passes, `shared_scene_content = true` required | E.1 | active |
| CT-S-06 | T2b undeclared share — Extra shared session — Violation | E.1 | active |

### Identity tests from E.1 (CT-I)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-I-01 | Exact re-run — Same `art_`, identical observation IDs, different `run_` | E.1 | active |
| CT-I-02 | Tolerance re-run (simulated with a seeded score perturbation) — New `art_`, same `asp_`, comparison report present | E.1 | milestone M1: Tolerance-class re-run (S2) |
| CT-I-03 | *g_max* change — All POW IDs differ; no collisions with the prior artifact | E.1 | active |
| CT-I-04 | Recalibration — All object_state, pair_series and POW IDs change | E.1 | active |
| CT-I-05 | Same file, two cameras — Two `rec_`, one `src_` | E.1 | active |
| CT-I-06 | Within one S0 artifact, a duplicate natural key ⇒ `ERR-NATURAL-KEY`. Across S0 artifacts, an identical anchor payload is the same entity (allowed; CT-NK-04); a different payload under the same anchor ID ⇒ `ERR-ANCHOR-CONFLICT` (CT-NK-05) | E.1 | amended: Reconciled with F.1 A1 ANC-1 |
| CT-I-07 | Rule change — Substrate `art_` unchanged; S5 IDs new | E.1 | active |
| CT-I-08 | Lineage — Any metric row traces through `art_` IDs to `src_` | E.1 | active |

### Same-artifact reference tests (CT-FK)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-FK-01 | Payload needs no own IDs — Build steps 1–5 with the ID-derivation function stubbed to raise if called — `art_` produced; stub never called | Clar | active |
| CT-FK-02 | Deterministic resolution — Build the S3, S4 and S5 fixture artifacts twice with rows shuffled — All derived ID columns identical | Clar | active |
| CT-FK-03 | FK integrity — For every derived FK column, check membership in the referenced table's ID set; inject a dangling `_nk` — Full membership; injected case `ERR-FK`, no artifact marked complete | Clar | active |
| CT-FK-04 | Exact re-run — Re-execute an exact-class stage on the same inputs — Same `payload_sha256`, `art_` and every record and FK ID | Clar | active |
| CT-FK-05 | Reconstruction — Read serialized files, drop derived columns, canonicalize — Equals stored `payload_sha256`; also after re-writing Parquet with different row groups | Clar | active |
| CT-FK-06 | Nested keys (S5) — Fixture with two episodes, one `event_link`, one two-member `candidate_event` — Link and event FKs resolve to the two episode IDs; event ID unchanged when member order is permuted | Clar | active |
| CT-FK-07 | Key uniqueness — Duplicate natural key in one table — `ERR-NATURAL-KEY` | Clar | active |

### Evidence and fitness tests (CT-F)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-F-01 | Bridged gap — POW with 1 s bridged gap: 1 s in `t_inferred_s`, not in detected | E.1 | active |
| CT-F-02 | Class sums — EC-01/EC-02 on all fixtures | E.1 | active |
| CT-F-03 | CM-09 — Fixture where half the inferred time has a present reference object yields 0.5 | E.1 | active |
| CT-F-04 | Synthetic-only — All criteria met on synthetic data → `experimental` | E.1 | active |
| CT-F-05 | Straddling interval — → `inconclusive` → `experimental` | E.1 | active |
| CT-F-06 | No evidence — → `not_yet_assessable` | E.1 | active |
| CT-F-07 | Late criterion — Criterion frozen after test evaluation → rejected | E.1 | active |
| CT-F-08 | CV2 without expert result — Rejected | E.1 | active |

### Linkage tests, milestone M2 (CT-L)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CT-L-01 | FX-17 — Groups and counts as tabulated; ambiguity recorded | E.1 | active |
| CT-L-02 | FX-18 — Groups as tabulated; conflict flag on p1–q2 | E.1 | active |
| CT-L-03 | FX-17/18 permuted — Identical output | E.1 | active |
| CT-L-04 | Two calibrated cameras, one interaction (E FX-08) — S_LINK 1, S_VIEW 2 | E.1 | active |
| CT-L-05 | Episode with only `U` edges — Counted alone; `n_unresolved_identity_episodes` incremented | E.1 | active |
| CT-L-06 | Report scan — No "bound" or "confidence interval" attached to scenario counts | E.1 | active |

### Time invariants (TI)

| ID | Normative text | Source | Status |
|---|---|---|---|
| TI-01 | Per (timeline, camera), coverage segments tile the timeline extent exactly once | E.1 | amended: Errata wording |
| TI-02 | Σ `support_s` of frames in usable/usable_degraded segments = Σ `support_s` of those segments | E.1 | active |
| TI-03 | `gap_unobserved` and `not_recorded` segments have `support_s = 0` and no frames | E.1 | active |
| TI-04 | No duration in tracks, POWs, exposure profiles or episodes includes time from `gap_unobserved`, `not_recorded` or `unusable` coverage | E.1 | active |
| TI-05 | For every interval record, Σ support by evidence class ≤ `span_s` | E.1 | active |
| TI-06 | `frame_index` order is non-decreasing in `t_resolved_s` over eligible frames; duplicates have zero support | E.1 | amended |
| TI-07 | Exactly one timed frame per recording carries `final_assumed` | E.1 | amended |
| TI-08 | No POW spans a frame-less gap | E.1 | active |
| TI-09 | For any tiling of a timeline, Σ clipped support over tiles = total support — CT-T-09: a frame whose support straddles a window boundary splits proportionally; the sum over both windows equals `s_k` | Errata | active |
| TI-10 | No interval receives support from outside its bounds — CT-T-10: episode ending mid-support counts only up to its end | Errata | active |
| TI-11 | `not_recorded` only on `aligned_session` timelines within the declared extent — CT-T-11: two unaligned files ⇒ two local timelines, no gap segment | Errata | active |
| TI-12 | Linkage edges `L`/`P` only between episodes on the same `aligned_session` timeline; otherwise `U` — CT-T-12: same scene, unaligned cameras ⇒ `U` edges, S_LINK = S_VIEW | Errata | active |
| TI-13 | Camera groups and reference windows lie on one timeline — CT-T-13: attempted cross-timeline window ⇒ rejected | Errata | active |

### Split/sampling invariants (SP)

| ID | Normative text | Source | Status |
|---|---|---|---|
| SP-01 | Split v1 has no Validation-store inputs (manifest check) | E.1 | active |
| SP-02 | Every reference window references the split version current at sampling time | E.1 | active |
| SP-03 | A revision exists only with a triggering audit containing at least one violation | E.1 | active |
| SP-04 | Revisions never move a recording into test | E.1 | active |
| SP-05 | Reports use only `valid` metric results on the latest split version | E.1 | active |
| SP-06 | T2b audits accept only declared shared sessions | E.1 | active |
| SP-07 | Partition changes are never computed from metrics or labels (revision function signature has no such inputs) | E.1 | active |
| SP-08 | No S8 run on test before the latest audit has `audit_complete` — CT-S-07: attempted early run ⇒ blocked | Errata | active |
| SP-09 | Headline metrics only from a plan whose population was not altered by `sampled_annotation` discoveries after drawing — CT-S-08: counterexample fixture A3.1 ⇒ old-plan headline metrics refused; `requires_resample` set | Errata | active |
| SP-10 | `conditional_on_selection` results carry no frequency/per-hour aggregates — CT-S-09 | Errata | active |
| SP-11 | Metadata-screened leakage (R-1) leaves `design_valid` — CT-S-10: actor-roster leak found pre-split ⇒ no resample needed | Errata | active |

### Calibration invariants (CB)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CB-01 | Tier-required fields present; tier-excluded fields null with `not_applicable` | E.1 | active |
| CB-02 | `homography_img_to_floor` is invertible (non-zero determinant) | E.1 | active |
| CB-03 | `load_state.height_m` non-null only with a `full_camera` calibration and a height reference or multi-view, or with `simulator_truth` | E.1 | active |
| CB-04 | `e2_occupancy_series.method = projected_footprint` requires CB-03 conditions | E.1 | active |
| CB-05 | `object_state.geometry_method = ground_plane_homography` allowed with either tier | E.1 | active |

### Experiment-contract invariants (CC)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CC-01 | Every episode has `experiment = E1` and `classification_contract = E1_v1` | E.1 | active |
| CC-02 | No Observation-store table contains E2 outcome labels | E.1 | active |
| CC-03 | `e2_occupancy_profile` time sums equal the pair's co-observation support | E.1 | active |
| CC-04 | E2 forbidden-field list (E VR-E-041) unchanged | E.1 | active |

### Activity invariants (CD)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CD-01 | Activity segments tile `[session_start, session_end)` per camera | E.1 | active |
| CD-02 | Each activity segment lies inside one coverage segment and obeys the table above | E.1 | active |
| CD-03 | `not_evaluated` time is never reported or exported as zero activity or zero exposure | E.1 | active |

### Identity invariants (ID) — also define CT-ID-01–07

| ID | Normative text | Source | Status |
|---|---|---|---|
| ID-01 | One `src_` per distinct byte content | E.1 | active |
| ID-02 | Duplicate natural key within one artifact is rejected; across artifacts the anchor rule ANC-1 applies (F.1 A1) | E.1 | amended |
| ID-03 | `art_` is recomputable from `asp_` and `payload_sha256` (§2.3), never from file hashes | E.1 | amended: Errata A1 |
| ID-04 | Every observation ID is recomputable from table, `art_`, natural key | E.1 | active |
| ID-05 | No two records in the store share an ID (global uniqueness check) | E.1 | active |
| ID-06 | Changing any config in a spec changes `asp_` and all downstream observation IDs | E.1 | active |
| ID-07 | S5 config changes leave S4 `art_` unchanged | E.1 | active |
| ID-08 | No observation ID contains a `run_` ID | E.1 | active |
| ID-09 | Steps 1–4 never read an artifact-derived ID — CT-ID-01: run the builder with the ID library disabled through step 4; it must produce `art_` | Errata | active |
| ID-10 | Exact re-run ⇒ identical `payload_sha256`, `art_`, record IDs — CT-ID-02: run twice; compare | Errata | active |
| ID-11 | Changing `run_`, clock time or host changes no hash except `execution.json` — CT-ID-03: re-run with a faked clock and a different host name; identity block identical | Errata | active |
| ID-12 | Different payloads ⇒ different `art_` — CT-ID-04: perturb one value in one row (e.g., a score by 1e-9); `art_` differs; record IDs differ | Errata | active |
| ID-13 | Same payload under a different `asp_` ⇒ different `art_` — CT-ID-05: same rows, different config ID; `art_` differs | Errata | active |
| ID-14 | Natural keys unique per table — CT-ID-06: duplicate key ⇒ `ERR-NATURAL-KEY` | Errata | active |
| ID-15 | Parquet re-serialization changes `file_sha256` only — CT-ID-07: rewrite with different row-group size; `art_` unchanged | Errata | active |

### Linkage invariants (LK)

| ID | Normative text | Source | Status |
|---|---|---|---|
| LK-01 | No group contains two episodes joined by `D` | E.1 | active |
| LK-02 | Every pair inside an S_LINK group has an `L` edge; inside S_POSS, `L` or `P` | E.1 | active |
| LK-03 | Grouping is identical under any permutation of input order (the algorithm sorts) | E.1 | active |
| LK-04 | S_VIEW ≥ S_LINK ≥ S_POSS | E.1 | active |
| LK-05 | Every original episode appears in exactly one group per scenario and is never modified | E.1 | active |
| LK-06 | Any `L` or `P` edge between different groups sets `link_conflict` on that edge record | E.1 | active |
| LK-07 | `wording = scenario_count` everywhere | E.1 | active |
| LK-08 | Event labels are recomputed from member flags (E VR-E-032) | E.1 | active |

### Evidence-class invariants (EC)

| ID | Normative text | Source | Status |
|---|---|---|---|
| EC-01 | For every track, POW and episode: detected + inferred + insufficient = total support | E.1 | active |
| EC-02 | Exposure band times split by class sum to the unsplit totals | E.1 | active |
| EC-03 | Inferred frames never carry `prov_class = model_estimated` for positions; they are `geometry_estimated` with `inferred = true` | E.1 | active |
| EC-04 | Episode labels are computed on all frames (unchanged logic); `support_detected_frac` is reported with them | E.1 | active |
| EC-05 | OBX exports carry both primary and secondary durations | E.1 | active |

### Fitness invariants (FT) — also define CT-F-09/10

| ID | Normative text | Source | Status |
|---|---|---|---|
| FT-01 | `technically_validated` only if the decision rule returns it from stored results | E.1 | active |
| FT-02 | Every criterion used was frozen before its first test-partition evaluation | E.1 | active |
| FT-03 | `unsuitable` requires a recorded `not_met` result | E.1 | active |
| FT-04 | Missing evidence yields `not_assessable`, never `unsuitable` | E.1 | active |
| FT-05 | CV1 requires both definition and source references; CV2 requires an expert-alignment result | E.1 | active |
| FT-06 | No status above CV2 can be stored | E.1 | active |
| FT-07 | Results from `invalidated_leakage` evaluations are ignored | E.1 | active |
| FT-08 | Overrides only downgrade | E.1 | active |
| FT-09 | Every status record has a complete scope key — CT-F-09 | Errata | active |
| FT-10 | A `not_met` in scope X leaves scope Y unchanged — CT-F-10: clearance fails on uncalibrated-viewpoint scope; calibrated scope remains `experimental` | Errata | active |
| FT-11 | No unscoped `unsuitable` value exists — Schema check | Errata | active |

### Superseded clock invariants (CA)

| ID | Normative text | Source | Status |
|---|---|---|---|
| CA-01 | ~~`method = assumed_zero` ⇔ `sigma_s` null with `not_observable`~~ | E.1 | superseded: By TI-11–TI-13 (Errata A2.C; `assumed_zero` removed) |
| CA-02 | ~~`sigma_s ≥ 0` when present~~ | E.1 | superseded: By TI-11–TI-13 |
| CA-03 | ~~As above~~ | E.1 | superseded: By TI-12 and VR-E-031 (amended) |

### Record fixtures from Package E (FX)

| ID | Normative text | Source | Status |
|---|---|---|---|
| FX-01 | Synthetic pair, moving forklift, dodge (T5) — E1 positive | E | note: Record content is now the normative Appendix N1 row T5 (and N2 for geometry) |
| FX-02 | Parked forklift, walk-by (T1) — Hard negative | E | note: = Appendix N1 T1 / N2 G1 |
| FX-03 | Distant fast approach, crossing paths (T3) — PC before proximity | E | note: = Appendix N1 T3 / N2 G3 |
| FX-04 | Moving forklift, footprint overlap, no cue (T6) — UD | E | note: = Appendix N1 T6 |
| FX-05 | Stationary forklift overlap, no cue (T8) — O + review routing | E | note: = Appendix N1 T8 |
| FX-06 | Occluded closest approach (T10, T11) — IE, `K` unknown | E | note: = Appendix N1 T10, T11 |
| FX-07 | Uncalibrated camera — Null reasons, image-only path | E | active |
| FX-08 | One interaction, two calibrated cameras — `linked_calibrated`, S_LINK = 1 | E | milestone M2 |
| FX-09 | Two concurrent interactions, two uncalibrated overlapping cameras — S_POSS assumptions flagged | E | milestone M2 |
| FX-10 | VFR video with a 0.5 s PTS gap and one corrupt frame — Timebase, coverage | E | active |
| FX-11 | Three activity states over one minute on one camera: 0–20 s coverage `unusable` / AI `not_evaluated` / reference `unobservable` (unusable_footage); 20–40 s `usable` / `observed_no_detection` / `objects_present_no_interaction` (a forklift the detector missed); 40–60 s `usable` / `observed_no_detection` / `reference_verified_absent` | E | amended |
| FX-12 | E2 elevated load, person in projected footprint, no mass — Conditional E2, forbidden fields | E | amended: E2 measurement only: `load_state` (elevated, height 2.4 ± 0.3 m only under CB-03 conditions, mass null `not_supplied`) and one `e2_occupancy_profile`; no episode |
| FX-13 | Two reviewers disagree — Tier 2 adjudication | E | active |
| FX-14 | Two cameras of one interaction placed in train and test — Leakage rejection | E | active |
| FX-15 | ECS window — Exclusion from headline and frequency metrics | E | active |
| FX-16 | Injected perception + geometry error resolved only jointly — Attribution | E | active |

## T2. Linkage fixtures (milestone M2)

**FX-17 (non-transitive A–B–C).**
- Three cameras on one `aligned_session` timeline, uncalibrated, with declared overlapping fields of view.
- Edges: A–B `P`; B–C `P`; A–C `D` (time-disjoint). Order A, B, C.
- Expected:
  - S_VIEW: {A}, {B}, {C}, count 3.
  - S_LINK: {A}, {B}, {C}, count 3.
  - S_POSS: {A, B}, {C}, count 2, with `ambiguous = true` on {A, B} (B could also join {C}).

**FX-18 (conflicting multi-camera interaction).**
- Two workers p and q, one forklift, two calibrated cameras on one aligned timeline.
- Episodes: cam1 p1, q1; cam2 p2, q2.
- Edges: p1–p2 `L`; q1–q2 `L`; a spurious p1–q2 `L`; same-camera pairs `D`. Order p1, p2, q1, q2.
- Steps:
  - p1 starts G1.
  - p2 joins G1.
  - q1 is `D` to p1, so it starts G2.
  - q2 cannot join G1 (p2–q2 is `D`), so it joins G2.
- Expected: S_VIEW 4, S_LINK 2, S_POSS 2; `link_conflict = true` on the p1–q2 edge; no alternative group for q2.

## T3. Leakage counterexample fixture FX-A3.1 (CT-S-08)

**Setup:**
- Test frame: recordings A–D, each tiled into 10 windows. RES samples 2 windows per recording (π = 0.2, seed from config).
- A and B share one interaction with a training recording in 3 of their 10 windows. That link is **not** in the metadata.
- The link is discovered only if a sampled window contains the shared interaction. The annotation of that window then adds a `same_physical_interaction` edge with `discovery_basis = sampled_annotation`.

**Expected:**
- PR-01 moves the affected group to train.
- The affected test strata become `requires_resample`.
- Headline metrics from the original plan are refused (SP-09).
- A new plan drawn on the revised eligible population yields `design_valid` results.

## T4. Calibration, experiment, activity and timeline record fixtures

Verbatim from E.1 and the Errata. FX-A1 and FX-A2 are superseded and omitted.

```json
{"fixture": "FX-B1-valid-homography", "calibration_id": "cal_h1", "camera_id": "cam_03", "world_frame_id": "wf_1",
 "calibration_tier": "ground_plane_homography",
 "intrinsics_K": null, "intrinsics_K_null_reason": "not_applicable",
 "R_cam_from_world": null, "R_cam_from_world_null_reason": "not_applicable",
 "t_cam_from_world_m": null, "t_cam_from_world_m_null_reason": "not_applicable",
 "distortion_model": null, "distortion_model_null_reason": "not_supplied",
 "homography_assumes_undistorted": true,
 "homography_img_to_floor": [0.012, 0.001, -4.1, 0.0, 0.019, -6.2, 0.0, 0.0004, 1.0],
 "reproj_error_px_rmse": null, "reproj_error_px_rmse_null_reason": "not_applicable",
 "quality_state": "supplied_unvalidated", "method": "survey_points_pnp_ground_only",
 "height_reference_ids": []}
```

```json
{"fixture": "FX-B2-invalid-height-from-homography", "track_id": "trk_load_4", "frame_index": 880,
 "method": "height_reference_plane", "calibration_id": "cal_h1",
 "elevation_state": "elevated", "height_m": 2.4, "height_sigma_m": 0.3,
 "expected_error": "CB-03: height requires full_camera calibration with height reference, multi-view, or simulator truth"}
```

```json
{"fixture": "FX-C1-valid-e2-profile", "e2_profile_id": "e2p_1", "person_track_id": "trk_p2", "load_track_id": "trk_load_4",
 "method": "image_overlap_baseline", "t_coobserved_s": 6.0,
 "t_occupied_detected_s": 1.2, "t_occupied_inferred_s": 0.3,
 "t_not_occupied_s": 3.9, "t_occupancy_unknown_s": 0.6}
```

```json
{"fixture": "FX-C2-invalid-e2-episode", "episode_id": "ep_x", "experiment": "E2",
 "classification_contract": "E1_v1",
 "expected_error": "CC-01: experiment E2 not allowed in schema v1.1"}
```

```json
{"fixture": "FX-D1-valid", "activity_segment_id": "act_1", "camera_id": "cam_02", "session_id": "ses_1",
 "t_start_session_s": 0.0, "t_end_session_s": 20.0, "coverage_state": "unusable",
 "ai_activity_state": "not_evaluated"}
```

```json
{"fixture": "FX-D2-invalid", "activity_segment_id": "act_2", "camera_id": "cam_02", "session_id": "ses_1",
 "t_start_session_s": 0.0, "t_end_session_s": 20.0, "coverage_state": "unusable",
 "ai_activity_state": "observed_no_detection",
 "expected_error": "CD-02: unusable coverage requires not_evaluated"}
```

```json
{"fixture": "FX-A3-valid-local", "recording_id": "rec_b7", "timeline_id": "tl_b7", "timeline_kind": "recording_local",
 "clock_alignment_id": null, "clock_alignment_id_null_reason": "not_applicable"}
```

```json
{"fixture": "FX-A4-invalid-gap-without-alignment", "timeline_id": "tl_b7", "timeline_kind": "recording_local",
 "coverage_state": "not_recorded", "t_start_s": 120.0, "t_end_s": 180.0,
 "expected_error": "TI-11: not_recorded segments only on aligned_session timelines within a declared session extent"}
```
**FX-B3 (valid full-camera record, new).** Values are illustrative; field presence and nullability are what the test checks.

```json
{"fixture": "FX-B3-valid-full-camera", "calibration_id": "cal_f1", "camera_id": "cam_01", "world_frame_id": "wf_1",
 "calibration_tier": "full_camera", "method": "dataset_supplied", "valid_from_us": 0,
 "valid_to_us": null, "valid_to_us_null_reason": "not_applicable",
 "intrinsics_K": [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0],
 "R_cam_from_world": [1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0],
 "t_cam_from_world_m": [0.0, 3.0, 8.0],
 "distortion_model": "none", "distortion_coeffs": [],
 "homography_assumes_undistorted": false,
 "homography_img_to_floor": null, "homography_img_to_floor_null_reason": "not_computed_by_config",
 "reproj_error_px_rmse": null, "reproj_error_px_rmse_null_reason": "not_supplied",
 "heldout_ground_error_m_rmse": null, "heldout_ground_error_m_rmse_null_reason": "not_computed_by_config",
 "quality_state": "supplied_unvalidated", "height_reference_ids": []}
```

## T5. Identity test vector (CT-FK, CT-ID; reference values of E-1.2.1 §2.3)

**Spec ID:** the literal string `asp_s3example0000000000000`, used as given. This vector is exempt from ID-pattern validation; `rec_a` is likewise a literal.

**Payload, 2 tables, 7 rows (payload columns only):**

| table | row |
|---|---|
| track | `{"recording_id":"rec_a","track_local_id":1,"class":"person","start_frame":10,"end_frame_excl":13}` |
| track | `{"recording_id":"rec_a","track_local_id":2,"class":"forklift","start_frame":10,"end_frame_excl":12}` |
| track_point | `{"track_nk":["rec_a",1],"frame_index":10,"state":"tracked"}` |
| track_point | `{"track_nk":["rec_a",1],"frame_index":11,"state":"predicted"}` |
| track_point | `{"track_nk":["rec_a",1],"frame_index":12,"state":"tracked"}` |
| track_point | `{"track_nk":["rec_a",2],"frame_index":10,"state":"tracked"}` |
| track_point | `{"track_nk":["rec_a",2],"frame_index":11,"state":"tracked"}` |

**Natural keys:**
- track: `[recording_id, track_local_id]`
- track_point: `[track_nk, frame_index]`

**Ordering rule (clarified):**
- Tables go in byte-wise name order.
- Rows are sorted by the **byte-wise (UTF-8) lexicographic order of `JCS(natural_key)`**, not numeric order. For example, `[["rec_a",1],10]` sorts before `[["rec_a",1],9]`.

**Canonical stream** (`\t` is a tab; each line ends with `\n`, including the last):

```
track\t{"class":"person","end_frame_excl":13,"recording_id":"rec_a","start_frame":10,"track_local_id":1}
track\t{"class":"forklift","end_frame_excl":12,"recording_id":"rec_a","start_frame":10,"track_local_id":2}
track_point\t{"frame_index":10,"state":"tracked","track_nk":["rec_a",1]}
track_point\t{"frame_index":11,"state":"predicted","track_nk":["rec_a",1]}
track_point\t{"frame_index":12,"state":"tracked","track_nk":["rec_a",1]}
track_point\t{"frame_index":10,"state":"tracked","track_nk":["rec_a",2]}
track_point\t{"frame_index":11,"state":"tracked","track_nk":["rec_a",2]}
```

**Expected values:**

| Quantity | Value |
|---|---|
| `payload_sha256` = SHA-256(stream, UTF-8) | `2b38d32502f58662b39c32bd796a2d24e4dfc3ecd87140f1dcc9ff9568fff068` |
| `art_` = `"art_" + b32(SHA-256(JCS([asp, payload_sha256])))` | `art_pmpcesnhpbbgtw2f3fhb6zkqxk` |
| track 1 ID = `"trk_" + b32(SHA-256(JCS(["track", art, ["rec_a",1]])))` | `trk_zr3hb5b6y2jjuw7ab7aml6ymtf` |
| track 2 ID | `trk_kwwpqd3ie7pk73ai5tvu2mevrq` |
| track_point (["rec_a",1], 10) = `"tpt_" + b32(SHA-256(JCS(["track_point", art, [["rec_a",1],10]])))` | `tpt_f3lfwb6nyvogr3qwgwiv3gl6zn` |
| track_point (["rec_a",1], 11) | `tpt_zclgpfkf4k7j52hftbgoilotyu` |
| track_point (["rec_a",1], 12) | `tpt_46omowvb74tg5fe4u7zwsdj6or` |
| track_point (["rec_a",2], 10) | `tpt_mzpwebvgdvlqaxls3rwuf2ddp7` |
| track_point (["rec_a",2], 11) | `tpt_dbqp2kun3bv562njoyaz72zoy2` |
| Derived FK `track_point.track_id` | track 1 ID for the three `["rec_a",1]` points; track 2 ID for the two `["rec_a",2]` points |

- `b32(d)` = lowercase RFC 4648 base32 of the 32-byte digest, padding removed, first 26 characters.
- JCS for these values equals sorted-key, compact JSON (`separators=(",",":")`, UTF-8, no ASCII escaping). For floats a real RFC 8785 implementation is still required.

## T6. Change log

| Version | Change |
|---|---|
| E-1.2.3 | Appendix T added (CR-001 / D-1). VR-E-001/004/010–014/016/030/031/060/070, CT-E-09/26–29, CT-T-05/07, CT-S-02, CT-I-06, ID-02/03, TI-01/06/07, FX-11/12 reconciled with E.1, the Errata, the Clarification and F.1. FX-B3 added. Identity test vector made complete, with a byte-wise ordering rule. No change to definitions, units, sampling or reporting semantics |

## T7. Nominal frame interval and substituted timing (E-1.2.4; CR-003, D-4)

δ_nom (per recording), in order of precedence:
1. Declared: if the decode configuration declares `delta_nom_s` for the
   recording (from dataset documentation with an evidence reference, or
   from the fixture specification), use it.
   `delta_nom_source = declared_config`.
2. Adjacent-pair median: otherwise, take the median of Δ over pairs of
   consecutive timed, eligible frames that are adjacent in decode order,
   with no untimed, duplicate or undecodable frame between them (≥ 1 pair).
   For an even count, use the mean of the two middle values.
   `delta_nom_source = median_adjacent_pairs`.
3. All-timed median: if no such pair exists, take the median over all
   consecutive timed intervals.
   `delta_nom_source = median_all_timed`.
4. Fewer than 2 timed frames: ERR-TIMESTAMPS.

`decode_summary` gains:
- `delta_nom_source`;
- `delta_nom_declared_s?` (null `not_supplied` when undeclared);
- `delta_nom_median_s?` (the adjacent-pair median when computable).
Both values are stored for audit. No threshold compares them.

Fixtures declare δ_nom = 0.033 s; all Appendix N3 values are unchanged.

Substituted timing (f_sub):
- `substituted_support_frac` = support of eligible frames with ts_source in
  {best_effort, dts_derived} ÷ total eligible support of the recording.
- At or below f_sub: no coverage change; the fraction is reported.
- Above f_sub: the support intervals of substituted frames become
  `usable_degraded` coverage with reason `timing_substituted`. All other
  frames are unaffected, and coverage tiling splits at those boundaries.
- `usable_degraded` remains usable for activity states and every duration.

Tests:
- CT-T-21: FX-CLIP-A–D with declared δ_nom 0.033 s reproduce
  0.100 / 0.067 / 0.033 / 0.133 s exactly.
- CT-T-22: FX-CLIP-B without a declaration gives δ_nom = 0.034 s
  (`median_adjacent_pairs`, the single pair f2→f3), detected support
  0.068 s, and an unchanged uncertainty region [0, 0.066) s.
- CT-T-23: a recording with substituted share at or below f_sub has no
  degraded coverage. Above f_sub, exactly the substituted frames' support
  intervals become `usable_degraded / timing_substituted`, and total usable
  support is unchanged.

## T7.1 Corrections to decode order and to the δ_nom fallback (E-1.2.5)

1. `decode_seq` is the position of the frame's packet in demux (file / DTS)
   order. It is NOT the decoder's output order. This replaces "decoder
   output order" in E-1.2.1 §3.2. `reorder_depth` and the ±r neighbourhood
   of ST-2 are measured in this order.
2. T7 step 2 (adjacent-pair median) is replaced by:
   δ_nom = the median of Δ over consecutive pairs of timed, non-duplicate
   frames in presentation order (ordered by t_resolved_s; undecodable but
   timed frames count). Exclude any pair whose interval [t_k, t_k+1)
   overlaps an uncertainty region U_u of an untimed frame (ST-2). Use the
   mean of the two middle values for an even count.
   delta_nom_source = median_adjacent_pairs. Steps 1, 3 and 4 are
   unchanged.
3. Check values (undeclared δ_nom):
   - Case A gives 0.033 s.
   - Case B gives 0.034 s (the pair f0→f2 overlaps U = [0, 0.066) and is
     excluded), so CT-T-22 is unchanged.
   - Case C has no valid pair, so step 3 applies.

## T8. Substrate measurement definitions (E-1.2.6; CR-005, D-6)
Notation: frames are eligible frames of one recording; t = t_resolved_s;
positions are CF-W metres; boxes are CF-IMG [x1, y1, x2, y2].

T8.1 POW gap bridging
- A joint frame has track points for both the person track and the
  forklift track with state ∈ {tracked, predicted}.
- A POW starts at the first joint frame of the pair.
- A gap is a run of eligible frames that are not joint frames (either
  point missing or state = lost). The gap is bridged (POW continues) iff
  ALL hold:
  - the gap length in eligible frames ≤ g_max;
  - both tracks have joint frames after the gap;
  - no coverage segment of state not_recorded, gap_unobserved or unusable
    lies between the last joint frame before the gap and the first joint
    frame after it.
- Otherwise the POW ends after its last joint frame, and a later joint
  frame starts a new POW with continuation_of_nk set if the same two
  tracks continue.
- end_reason:
  - coverage_gap if a coverage break caused the end;
  - gap_exceeded if the gap was longer than g_max;
  - otherwise track_end_person, track_end_forklift or recording_end.
  id_switch is used only where the tracker flags one.
- Gap frames inside a bridged gap belong to the POW. Their pair evidence
  class follows E-1.2.1 §3.4 (insufficient where a point is missing or
  lost) and is listed in bridged_gaps.

T8.2 Smoothed velocity, speed, heading, yaw
- Velocity at frame k: an ordinary least-squares linear fit of x(t) and
  y(t) over the same track's frames j with |t_j − t_k| ≤ w_v/2, a non-null
  position and evidence class ∈ {detected, inferred}. The window never
  crosses a coverage break.
- Requires ≥ 3 frames spanning ≥ w_v/2; otherwise speed and heading are
  null (not_observable).
- (v_x, v_y) = the fitted slopes. speed_mps = √(v_x² + v_y²).
  heading_rad = atan2(v_y, v_x) ∈ (−π, π]. Heading is null
  (not_applicable) when speed < v_min.
- σ_vx and σ_vy are the slope standard errors (residual variance with
  n − 2 degrees of freedom). speed_sigma_mps = √((v_x σ_vx)² +
  (v_y σ_vy)²) / speed, or √((σ_vx² + σ_vy²)/2) when speed = 0.
  sigma_status = uncalibrated_model.
- Forklift yaw:
  - simulator or oracle yaw when supplied;
  - otherwise heading when speed ≥ v_min;
  - otherwise carried forward from the last defined yaw in the track,
    then backward-filled from the first.
  - If never defined: yaw null (not_observable). The forklift footprint is
    then the circumscribed disc of the prior rectangle
    (radius = ½√(length² + width²)), and the pair-frame gets
    borderline_flag footprint_orientation_unknown.
- Check: G2 positions at 10 fps with w_v = 0.5 s give speed 1.000000 m/s,
  heading 0, σ 0.

T8.3 Closing rate and time to closest approach (M-04, M-06)
- closing_rate_mps = −(the least-squares slope of clearance_m vs t) over
  the T8.2 window, using frames with clearance_state = measured
  (≥ 3 frames). Otherwise null (not_observable). Positive = approaching.
- ttca_s = t_at_min of the constant-velocity prediction over [0, τ]:
  - null (not_applicable) if the minimum is at 0 (diverging or static);
  - null (not_observable) if the minimum is at τ (beyond the horizon);
  - otherwise t_at_min.
- Check: G3 at t = 0 has a predicted minimum at τ, so ttca_s is null
  (not_observable).

T8.4 Clearance uncertainty (first-order; sigma_status = uncalibrated_model
until GV-05)
- u = the unit gradient of the signed footprint distance at the pair's
  closest points (from the forklift footprint toward the person; inside the
  footprint, the normal of the nearest edge).
- σ_c² = uᵀ(Σ_person + Σ_forklift)u + σ_dim², with
  σ_dim = ½(|u·h| σ_length + |u·h⊥| σ_width), where h is the forklift yaw
  unit vector. For a disc footprint, σ_dim = ½ max(σ_length, σ_width).
- If either covariance is null: clearance_sigma_m is null (not_estimated),
  and the contact rule uses σ = 0 (Appendix N1 note).
- Check: G1 with Σ = diag(0.05², 0.05²) for both objects and σ_dims = 0
  gives σ_c = 0.0707107 m.

T8.5 Signed image box gap (M-02)
- For person box p and forklift box f:
  dx = max(f.x1 − p.x2, p.x1 − f.x2); dy = max(f.y1 − p.y2, p.y1 − f.y2).
- If dx > 0 or dy > 0: image_gap_px = √(max(dx,0)² + max(dy,0)²).
  Otherwise image_gap_px = max(dx, dy) (≤ 0, the smaller penetration).
- image_gap_norm = image_gap_px ÷ (p.y2 − p.y1).
- Checks, with p = [100,100,140,200]:
  - f = [200,120,300,220] gives 60 px, 0.60;
  - f = [170,240,270,300] gives 50 px, 0.50;
  - f = [130,150,230,250] gives −10 px, −0.10.

T8.6 Evidence state per object-frame (precedence top-down)
- lost: no track point, or state = lost.
- occluded_predicted: state = predicted.
- truncated: the detection box is within 1 px of an image border.
- partially_visible: visibility_frac is non-null and < v_part (new
  parameter; TEST-ONLY value 0.5).
- visible: otherwise.
- t_joint_visible_s counts frames where both objects are visible or
  partially_visible.

T8.7 Evidence sufficiency Q per pair-frame
- q_state = sufficient iff ALL hold:
  - the pair evidence class is detected;
  - neither object's evidence state is truncated;
  - the frame's support is not timing_uncertain.
- Otherwise insufficient, with q_reasons listing every failing cause:
  person_occluded or forklift_occluded (predicted), truncated,
  predicted_only, timing_uncertain.
- usable_degraded coverage alone does not make Q insufficient.

New parameter v_part goes in the E-1.2.1 §14 list. Every check value above
becomes a test.

## T9. Event-engine definitions and corrections (E-1.2.7; CR-008, D-9)

T9.1 Correction to T8.2 (track ends)
The velocity window is the interval of length w_v centred on t_k, SHIFTED
(not shrunk) so that it lies inside the track's contiguous run of frames
with non-null position and evidence class ∈ {detected, inferred}, without
crossing a coverage break. It requires ≥ 3 frames. If the run is shorter
than w_v, use the whole run. All other T8.2 rules are unchanged.
Checks:
- G2 speed is still 1.000000 m/s.
- G3 has a velocity on every frame, so N2 holds as written: episode frames
  0–9, minclr 2.35 m, and ttca_s at t = 0 is null (not_observable).

T9.2 R5 evasive-action rates
For frame k, let a and b be the first and last frames inside the window of
length w_e centred on t_k (shifted as in T9.1) with non-null smoothed
values, requiring t_b − t_a ≥ w_e/2. Then:
- person_speed_change = |speed_b − speed_a| / (t_b − t_a)        [m/s²]
- forklift_decel = max(0, −(speed_b − speed_a)) / (t_b − t_a)    [m/s²]
- person_turn_rate = |wrap(heading_b − heading_a)| / (t_b − t_a) [rad/s],
  with wrap to (−π, π]. It is evaluated only if the person's speed ≥ v_min
  at both a and b; otherwise the criterion is FALSE (no turn is possible
  without motion; stopping is captured by person_speed_change).
- E(k) = (person_turn_rate > e_turn) ∨ (person_speed_change > e_acc)
         ∨ (forklift_decel > e_dec), in Kleene logic.
- A criterion is unknown when its required values are null (not_observable).
- exp_evasive_score = the maximum over I⁺ of the largest ratio of observed
  value to threshold among the three criteria.

T9.3 Contact cue (replaces "k_c" for both units)
cue = (forklift_decel > k_c) ∨ (person_speed_change > k_c)
      ∨ (person_turn_rate > k_c_turn), evaluated with T9.2 over the window
centred on the closest-approach frame (CA). New parameter: k_c_turn
(rad/s; TEST-ONLY value 3.0).

T9.4 E when R5 is disabled
If the configuration does not enable R5:
- E_ep = 0 and the new episode field e_assessed = false;
- K = (minclr < d_nm), in Kleene logic;
- such a configuration cannot produce NM, UD or CT through evasive action.
If R5 is enabled: e_assessed = true and §6 applies unchanged.
Check: G2 gives H.

T9.5 Closest-approach frame (CA)
1. Let m* be the frame of I with the minimum measured clearance (earliest
   on ties).
2. If m* is the last measured frame of I, the next frame of I is not
   measured, and closing_rate_mps at m* > 0 (or null), the approach
   continued unobserved:
   - t_CA = t(m*) + ttca_s(m*) if that is non-null, else the end of I;
   - CA = the frame of I nearest t_CA (earliest on ties);
   - ca_observed = false.
3. Otherwise CA = m* and ca_observed = true.
4. If I has no measured clearance: CA = the frame of I with the minimum
   image_gap_norm (earliest on ties), ca_observed = false. If no frame of I
   has boxes for both objects: CA = null (not_observable).
New episode field: ca_observed · bool.

T9.6 Usable frames around CA, and contact state
W_CA = frames of I⁺ with |t − t_CA| ≤ w_e/2. Contact state is evaluated in
this order:
1. not_assessable: CA is null, or no frame in W_CA has
   q_state = sufficient.
2. undetermined: Q is insufficient at CA (CA not visible), or any §6
   undetermined condition holds.
3. suspected or none_observed: otherwise, per §6 with the T9.3 cue.

T9.7 Lifecycle with unknown trigger values
A maximal run of non-true T frames (0 or 2) between true frames is bridged
iff:
- (a) its length ≤ m_gap, or
- (b) it contains no T = 0 frame and its length ≤ g_max.
Otherwise the episode closes at the last true frame. Episodes still open
only on T = 1.

T9.8 onset_sensitive
Set the onset_sensitive flag iff the episode's opening frame, or the frame
immediately before it, is a borderline frame (§6.0: |value − threshold| ≤
k_σ·σ) for P, M or any enabled C provider.

T9.9 Correction to Appendix N1
Row T10 inputs become: Q = 1×12, 0×8 (CA at frame 15); minclr 1.20 m from
frames 0–11. Expected values are unchanged: contact undetermined, K = 2,
labels PC, IE. Row T11 is unchanged (not_assessable).
Rationale: with w_e = 1.0 s at 10 fps, W_CA = frames 10–20. T10 now has
sufficient frames 10–11 in W_CA; T11 has none.

## T10. Edge readings, episode exposure fields, event counts and event-metric details (E-1.2.8; CR-009, CR-010, D-10, D-11)

T10.1 Contact-state order (replaces T9.6 steps 2–3; T9.6 step 1 and W_CA are unchanged)
Evaluate in this order and stop at the first match:
1. not_assessable (T9.6 step 1).
2. undetermined if Q is insufficient at CA.
3. suspected if overlap at CA = 1 AND the contact cue (T9.3) = true.
4. undetermined if any of the following holds: overlap at CA is 1 or unknown; clearance at CA is within k_σ·σ of 0 (σ = 0 if null); clearance at CA is null.
5. none_observed otherwise (Q sufficient, overlap = 0, clearance − k_σ·σ > 0).
Checks: N1 T6, T8 give undetermined; T7, T9 give suspected; T10 gives undetermined; T11 gives not_assessable; T1–T5 give none_observed.

T10.2 Velocity requirements (clarifies T8.2 and T9.1)
A smoothed velocity needs at least 3 frames AND a span t_last − t_first ≥ w_v/2 within the shifted window (T9.1). Both conditions apply even when the whole run is used. Otherwise speed and heading are null (not_observable). Example: at 10 fps with w_v = 0.5 s, 3 frames span 0.2 s < 0.25 s, so 4 frames are needed.

T10.3 Closing rate (amends T8.3), R5 on insufficient frames (clarifies T9.2), cue when R5 is off (clarifies T9.3, T9.4)
(a) closing_rate_mps at frame k uses the T9.1 window: length w_v centred on t_k, shifted to lie inside the POW's contiguous span without crossing a coverage break. It uses the frames of that window with clearance_state = measured. It needs ≥ 3 such frames spanning ≥ w_v/2; otherwise null (not_observable). It is defined for every pair frame of the POW, including frames whose own clearance is not measured. Result values of exactly zero are stored as +0.0.
(b) When R5 is enabled: E(k) = unknown (2) whenever either object's evidence_class at k is insufficient (lost, ineligible or timing_uncertain). Otherwise E(k) follows T9.2, with criteria that lack values unknown as stated there. When R5 is disabled, E(k) = 0 on every frame (T9.4).
(c) The contact cue (T9.3) is computed from kinematics whether or not R5 is enabled. R5 enabled controls only E, K and exp_evasive_score. If the kinematics needed for the cue are null, the cue is unknown.
Check: G3 gives closing_rate_mps 1.5 (abs tolerance 1e-9) on every frame.

T10.4 borderline_flags (extends T9.8; no label changes)
Evaluate over the frames of I (not I⁺), using σ = 0 where σ is null:
- clearance_within_k_sigma: set if on any frame of I with measured clearance, |clearance_m − d_p| ≤ k_σ·σ_c; or, for a configuration whose P provider is R1, |image_gap_norm − k_img| ≤ 0 on any frame with a non-null gap; or |pred_min_clearance_m − d_pc| ≤ k_σ·σ_pred on a frame with a prediction; or |minclr_m − d_nm| ≤ k_σ·minclr_sigma_m; or |clearance_at_CA| ≤ k_σ·σ at CA.
- speed_near_v_min: set if on any frame of I with non-null forklift speed, |speed_mps − v_min| ≤ k_σ·speed_sigma_mps.
- onset_sensitive: as T9.8.
- footprint_orientation_unknown: set if any pair frame of I carries it (AR-35 item 3).
Borderline flags never change a frame flag, a label or review_route.

T10.5 Episode exposure and support fields (all over I = [start_frame, end_frame_excl) unless stated)
All durations are clipped support of eligible frames by evidence class (ST-4, TI-09, TI-10).
- duration_detected_s, duration_inferred_s, duration_insufficient_s: Σ support of I by pair evidence class.
- support_detected_frac = duration_detected_s ÷ (duration_detected_s + duration_inferred_s + duration_insufficient_s). Null (not_applicable) if the denominator is 0.
- attr_end_frame_excl = end of I⁺ in frames.
- exp_t_in_band_detected_s, exp_t_in_band_inferred_s: per band of the configuration's band scheme (list in band order), Σ support of frames of I with measured clearance, by evidence class.
- exp_t_clearance_unknown_s: Σ support of detected or inferred frames of I whose clearance is not measured.
- Consistency: Σ exp_t_in_band_detected_s + (detected part of the clearance-unknown support) = duration_detected_s, and likewise for inferred, to 1 µs.
- exp_speed_at_ca_mps: forklift speed_mps at CA. Null (not_observable) if CA is null or speed is null.
- exp_closing_rate_max_mps: maximum over frames of I of non-null closing_rate_mps. Null (not_observable) if none.
- exp_ttca_min_s: minimum over frames of I of non-null ttca_s. If none are non-null: null with reason not_applicable if every frame's ttca_s is null for not_applicable, otherwise not_observable.
- exp_evasive_score: T9.2, over I⁺. Null (not_computed_by_config) if R5 is disabled; null (not_observable) if no ratio can be computed.
- exp_visible_frac: Σ support of eligible frames of I where both objects have evidence_state visible or partially_visible, ÷ Σ support of eligible frames of I. Null (not_applicable) if the denominator is 0.
Checks (hand-derived, abs tolerance 1e-9): G1 gives support_detected_frac 1.0, exp_speed_at_ca_mps 0.0, exp_closing_rate_max_mps 0.0, exp_ttca_min_s null (not_applicable). G2 gives exp_speed_at_ca_mps 1.0, taking CA as the earliest frame with minimum clearance. G3 gives exp_closing_rate_max_mps 1.5.

T10.6 event_count_summary
- One row per (scope, scenario, label) for scenario ∈ {S_VIEW, S_LINK, S_POSS} and label ∈ {all, O, H, PC, NM, UD, CT, IE}. Rows with zero events are written (n_events = 0).
- n_events for label `all` = number of candidate_events in that scenario and scope. For any other label = number of those events with lbl_<label> true (not by summary_label). Labels overlap, so per-label counts need not sum to `all`.
- An event belongs to the scope of its onset (§8). S5 writes scope_type ∈ {recording, timeline}. reference_window and split_partition scopes are computed at S8 and S9.
- Discarded episodes are not events.
- In single-camera runs the three scenarios give identical counts; n_ambiguous_groups = 0 and n_unresolved_identity_episodes = 0.
- assumptions: A1, A2, A3 each with status unverified. wording = scenario_count.
- A count of 0 is a count of events, never evidence of zero hazard or zero exposure; exports carry the coverage companion.
Check: G1 recording scope has all = 1, O = 1, every other label = 0, in every scenario.

T10.7 Event metrics (EV-M, resolves CR-010)
(a) Abstained: a system event is abstained iff lbl_IE is true AND none of lbl_NM, lbl_UD, lbl_CT is true. Abstention applies only to label group G2. No event is abstained in label groups G1 or any. Abstained events are excluded from sᵢ and from matching candidates, and enter EV-M3, EV-M5 and abstained_miss.
(b) cᵢ = aᵢ − (number of abstained_miss references in window i). Hence EV-M4 = 1 − EV-M5 on the same windows.
(c) P90 in EV-M8: linear interpolation (numpy percentile, method "linear") over the unweighted |onset error| and |offset error| of matched pairs. The median uses the same method. With no matched pairs the value is null (not_applicable). n is reported with the value.
(d) Weighting: EV-M3, EV-M5 and EV-M11 are RES-weighted ratios (wᵢ = 1/πᵢ) over RES windows, with unweighted values reported alongside, as for EV-M1. EV-M8 is unweighted and descriptive of the matched pairs only. For EV-M3, "abstained episodes ÷ all episodes" counts G2 abstention over all episodes; an episode belongs to the window of its onset. EV-M3's support form is Σ wᵢ abstained support ÷ Σ wᵢ POW support.

T10.8 Tests
CT-T10-01: N1 T1–T11 contact states with T10.1 (every row's contact value, including the new order).
CT-T10-02: 4 frames at 10 fps give a velocity with w_v = 0.5 s; 3 frames give null.
CT-T10-03: closing rate, G3 = 1.5 on every frame, and null with fewer than 3 measured frames in the window; a zero result is +0.0.
CT-T10-04: R5 enabled, E unknown on a lost frame; E_ep true if any true frame exists in I⁺, otherwise unknown. R5 disabled, E = 0 on every frame.
CT-T10-05: R5 disabled, the cue is still computed; a null-kinematics cue gives undetermined at overlap.
CT-T10-06: borderline_flags, one case per bullet of T10.4 (including the R1 and footprint_orientation_unknown cases), each hand-calculated and recorded in the test; a borderline frame in I⁺ but outside I sets no flag.
CT-T10-07: exposure fields on G1, G2, G3 (checks in T10.5), and the T10.5 consistency sum on every episode.
CT-T10-08: event_count_summary rows for G1 (T10.6 check), and an event with H and NM counted under `all`, H and NM.
CT-T10-09: EV-M3/M5/M11 weighted and unweighted on a hand-built two-window fixture; EV-M4 = 1 − EV-M5; P90 on 5 and on 4 values (hand values recorded); abstained definition on an event with IE and no NM/UD/CT (not abstained in G1, abstained in G2).
CT-T10-10: q_reasons on a lost object contains person_lost or forklift_lost and not *_occluded; q_state is unchanged by the new values (T10.9).

T10.9 Q reasons for lost objects (revises AR-35 item 6; descriptive enum addition, no effect on q_state)
`pair_series.q_reasons` gains the values person_lost and forklift_lost. They are listed when the object has no track point or state = lost at the frame. person_occluded and forklift_occluded are listed only for state = predicted, as T8.7 states. q_state follows T8.7 unchanged.

## T11. Borderline flags by provider; paired bootstrap scheme (E-1.2.9; CR-011, D-12)

T11.1 Provider-conditional borderline flags (clarifies T10.4; no label, frame-flag or review_route effect)
Each T10.4 bullet applies only under the stated condition:
- |clearance_m − d_p| ≤ k_σ·σ_c: only if the configuration's P provider is R2.
- |image_gap_norm − k_img| ≤ 0 (R1 bullet): only if the P provider is R1.
- |pred_min_clearance_m − d_pc| ≤ k_σ·σ_pred: only if R3 is enabled.
- |speed_mps − v_min| ≤ k_σ·speed_sigma_mps: only if R2 is enabled (the M provider, §6.0).
- |minclr_m − d_nm| ≤ k_σ·minclr_sigma_m, and |clearance_at_CA| ≤ k_σ·σ at CA: whenever the quantity is non-null (d_nm and k_σ are classification parameters).
- footprint_orientation_unknown and onset_sensitive: unchanged (T10.4, T9.8).
Parameters of a disabled provider may be recorded in the rule_configuration record (AR-40 item c) but play no role in S5 output. Changing only a disabled provider's parameters changes the rule_configuration ID and the S5 artifact ID (through the specification) but not the S5 payload_sha256.

T11.2 Paired bootstrap (clarifies N5, "Paired comparison")
The paired comparison uses the interval scheme of the estimand of the compared metric: stratified window bootstrap (Target A) for estimand frame_description, and cluster bootstrap (Target B) for new_session_performance. Both configurations share each replicate's resampled units, and the interval is that of R̂_a − R̂_b. Metrics with estimand conditional_on_selection get no paired interval.

T11.3 Tests
CT-T11-01: borderline flags, one case per bullet of T11.1: a borderline value with the provider enabled sets the flag; the same value with the provider disabled sets none. Hand-calculated and recorded in the test.
CT-T11-02: two rule configurations that differ only in a disabled provider's parameters give identical S5 payload_sha256 and different rule_configuration IDs.
CT-T11-03: a paired comparison on a new_session_performance metric uses cluster resampling (interval is wider than the window-resampled interval on a hand-built fixture with two leakage groups), and a frame_description metric uses window resampling.

## T12. Shared parameters, EV-M10, oracle-factorial attribution, completeness definitions, fitness gaps (E-1.2.10; CR-012 to CR-016, D-13 to D-17)

T12.1 Shared parameters (clarifies T11.1)
The last paragraph of T11.1 applies only to parameters read exclusively by the disabled provider: R1: k_img; R2: d_p; R3: d_pc; R4: ttc_max, pet_max; R5: e_turn, e_acc, e_dec. Two parameters are shared and always apply:
- v_min is a substrate parameter (substrate_config). It is read by S4 (heading, motion split), by R2's M flag and by R5's turn test. It has one source, substrate_config.v_min, and no copy in a provider's params.
- w_e is a classification parameter, stored in the classification block of the rule configuration. It is read by T9.3 (contact cue), T9.6 (W_CA) and R5, whether or not R5 is enabled.
A provider's params map holds only its exclusive parameters. This moves storage only: S5 payload values are unchanged, and the rule_configuration and S5 artifact IDs change.

T12.2 Event on an unobservable reference (EV-M10; resolves CR-013)
- N4 is kept literal, and match classes are unchanged. Reason: N4 has the highest precedence, and the Owner decided not to add or repurpose a class at M0. A reference that is not assessable keeps match_type unobservable_reference. A non-abstained system event that overlaps one (temporal IoU > 0, same window, no pair condition) and is matched to no reference stays a false_alert. EV-M2 and EV-M7 are unchanged headline values.
- EV-M10 is a table of system events that overlap an unobservable reference and are matched to none, split by decision (non-abstained / abstained per T10.7a) and by label (lbl_*), RES-weighted with unweighted values alongside.
- Reported with it, labelled "sensitivity_excluding_unobservable_overlap": EV-M2 and EV-M7 recomputed with those events removed from sᵢ and fᵢ. These never replace the headline values. This gives the effect your option (b) would have had, without changing N4.
- Interpretation text: "These events are neither confirmed nor refuted by the reference."
Check (w = 1): one window with s1 matched to an assessable reference, s2 overlapping an unobservable reference, s3 elsewhere with no reference, s4 abstained and overlapping the unobservable reference. EV-M2 = 1/3, sensitivity EV-M2 = 1/2, EV-M10 = 1 non-abstained and 1 abstained.

T12.3 Oracle-factorial attribution (replaces the reference to D.1 §7.2 in N9; resolves CR-014)
Applies to synthetic data with oracle runs (VR-E-061). On real data only the N9 rule tests apply and verified_* is forbidden.
1. If N9 rule 1 (evidence_unavailable) fails: primary_stage = evidence_unavailable, attribution_status = diagnostic_inferred, no factorial.
2. Stages are perception, tracking, geometry, in that order. For every subset C of the three stages (8 runs; the empty set is the system as run), substitute the oracle for the stages in C and re-run matching. Resolved(C) is:
   - for a miss or abstained_miss: the reference's record becomes matched;
   - for a false_alert or duplicate_alert: no false or duplicate alert has temporal IoU > 0 with the original event's interval.
   Resolved(∅) is false by construction. The substitution semantics belong to the oracle adapters (T-18, T-21). At M0 the factorial runner takes the resolved sets as inputs.
3. Let R = the sets with Resolved(C) true, and M = the minimal elements of R under inclusion. Monotonicity is not assumed.
   a. M empty (no substitution resolves it): primary_stage = the first failing N9 rule among rule 5 (event_reasoning) and rule 7 (reference_ambiguity); status diagnostic_inferred. If neither fails: primary_stage = unresolved, status unresolved.
   b. M non-empty: k = the smallest size in M. primary_stage = the earliest stage (pipeline order) in the union of the size-k sets of M, so ties between size-k sets go to the set containing the earliest stage. secondary_factors = the other stages appearing in any set of M, in pipeline order. attribution_status = verified_oracle_single if k = 1, else verified_oracle_joint. oracle_artifact_ids lists the runs of the sets in M.
4. rule_test_results are always stored. Where the rule-test primary stage differs from the oracle primary stage, the milestone report counts the disagreement. Sets that resolve while a superset does not are counted in the same report.
5. N9's "tests conflict" has no separate state: rules 4 and 5 are not_evaluated when their prerequisite fails (AR-42 item 4). The result is unresolved only when no test fails.
Checks: FX-16 (R = all supersets of {perception, geometry}) gives primary perception, secondary [geometry], verified_oracle_joint (CT-E-22). {perception} alone gives perception, verified_oracle_single. {perception} and {geometry} each resolving give primary perception, secondary [geometry], verified_oracle_single. M empty with rule 5 failing gives event_reasoning, diagnostic_inferred. M empty with no failing rule gives unresolved.

T12.4 Completeness definitions (resolves CR-015)
All support is clipped eligible support within the window span [t_start, t_end) (not the guard), by basis as in AR-43 item 1.
- Reference pair: a (person identity p, forklift identity f) with at least one eligible frame in the window on which both are reference co-visible. Co-visible: both present and evidence_state visible or partially_visible. Where the dataset supplies no visibility truth, presence alone counts and reports print "reference visibility assumed". A co-presence interval is a maximal run of consecutive eligible co-visible frames.
- A POW frame is attributed to pair (p, f) when both its tracks have track_identity_assoc status matched, to p and f respectively, on that frame. A POW's dominant pair is (dominant_identity_id of its person track, dominant_identity_id of its forklift track).
- CM-05: over POW frames of the basis, excluding frames where either track is ambiguous. Numerator: frames attributed to no co-visible reference pair. Denominator: all such frames. Ambiguous support is reported separately in the report's completeness table, not in the key. (Basis: the POW frames in the basis only, CR-015 item 1 reading (a).)
- CM-06: for each reference pair and band of the configuration's band scheme, AI time in band is recomputed from pair_series frames clipped to the window, using frames attributed to the pair. Reference time in band is the clipped support of co-visible frames whose reference clearance falls in the band. Reference clearance uses ref_geometry with the same footprint prior, yaw rule (T8.2) and clearance function as S4. The per-pair value is Σ_b |AI_b − ref_b|. The Bland–Altman units are (pair, band) with d = AI_b − ref_b; bias and LoA (N5) are descriptive only, with n reported and no interval claim, because bands within a pair are not independent. Without ref_geometry the value is null with reason not_supplied.
- CM-07 follows N6: for each reference co-presence interval, the number of POWs with at least one frame attributed to the pair inside it (an integer, 0 when uncovered). The report gives the counts of intervals with 0, 1 and 2 or more POWs. The "pair-window fidelity" of N10 is the share with exactly 1. F.1 A5.2's "CM-07 fragmentation" (tracks per identity) is not a CM-07 record, so that one metric ID does not carry two meanings: track-level fragmentation is carried by track_identity_summary.status = fragment and by the N10 fragmentation metric.
- CM-08: numerator, POW frames of the basis whose clearance_state is not measured; denominator, POW frames of the basis. Stratified by calibration tier. No reference is needed.
- CM-10: numerator, reference co-visible frames of a pair on which a POW whose dominant pair is (p, f) has a pair-frame with evidence class insufficient. Denominator, reference co-visible frames of the pair. Frames with no POW pair-frame at all are in neither CM-10's numerator nor CM-03's numerator (CR-015 item 4 reading (b)); CM-03 already counts them as uncovered.
- Pooling: pooled CM-k = Σ over RES windows of wᵢ·numeratorᵢ ÷ Σ wᵢ·denominatorᵢ (a ratio of sums, not a mean of ratios), with unweighted values alongside and intervals per N5. Per-identity and per-pair rows stay in the stratum.
Checks: FX-CM and FX-ID-3 keep their CM-01, CM-02 and CM-03 values. The other metrics use hand-built fixtures with values recorded in the test.

T12.5 Fitness decision gaps (amends §9.6; resolves CR-016)
- Residual status: experimental is the status for every combination that is not technically_validated, not unsuitable_under_tested_conditions (§9.6) and not not_yet_assessable. This includes a repeatability, robustness or comparability criterion that is not_met when no criterion is met or inconclusive. failing_interval records the first not_met criterion of any type, in criterion-ID order. Only accuracy and completeness not_met produce unsuitable.
- Real data: data_origin real_natural and real_staged both count as real data for §9.6. A status is always scoped by data_origin (scope key) and never carries over from real_staged to real_natural. Synthetic data never reaches technically_validated (FT-01, CT-F-04).
- Comparability characterized: at least one comparability criterion is registered and its decision is not not_assessable. It need not be met. Its decision is exported with the status.

T12.6 Tests
CT-T12-01: configurations differing only in R5-exclusive parameters with R5 disabled give the same S5 payload; a changed w_e or v_min changes the S5 output on a hand fixture where the cue, W_CA or the motion split depends on it.
CT-T12-02: EV-M10 and the sensitivity values on the T12.2 check fixture.
CT-T12-03: the factorial cases of T12.3 (FX-16, the {P}/{G} tie, empty M with and without a failing rule).
CT-T12-04: CM-05 to CM-08 and CM-10, plus pooled CM-01 over two RES windows, on hand-built fixtures extending FX-CM and FX-ID-3.
CT-T12-05: a repeatability not_met alone gives experimental with failing_interval; real_staged scope reaches technically_validated and the status stays scoped; a decided comparability criterion counts as characterized; a not_assessable one does not.

## T13. CM-10 basis; τ as a substrate parameter; completeness units (E-1.2.11; CR-017, D-18)

T13.1 CM-10 is basis-independent (amends T12.4)
CM-10 counts insufficient pair-frames. By §3.4, insufficient support belongs to neither the detected nor the detected + inferred basis, so a basis-restricted value would be zero by construction. CM-10 is therefore computed once, with the numerator and denominator of T12.4, and reported as "basis-independent". It is stored with support_basis = detected as a key placeholder. No other metric changes.
Check: a pair with 2.0 s of reference co-visible support, of which 0.5 s lies on POW pair-frames of class insufficient, gives CM-10 = 0.25 on either basis label.

T13.2 Substrate parameters (clarifies T12.1)
v_min and τ (prediction horizon) are substrate parameters, stored in substrate_config (AR-35 item 4). They are read by S4 and, through the S5 single-source rule, by S5. R3's provider params hold d_pc only. Moves no value.

T13.3 Units of CM-06 and CM-07 (clarifies T12.4)
CM-06 is a sum in seconds, and CM-07 is a count of POWs. Neither is a proportion. Reports label them "sum" and "count".

T13.4 Tests
CT-T13-01: the CM-10 check of T13.1, on both basis labels.

## T14. Leakage edge "same scene" (E-1.2.12; D-20)

T14.1 For synthetic data, a scene is a rendered scene instance: one simulation run,
 or one scene asset together with all its re-renderings. A layout or environment
 family shared across runs is recorded as shared_scene_content metadata and creates
 no leakage edge. Run, seed and render-lineage edges are unchanged (AR-31).
T14.2 Partitions built under T14.1 are reported as "held-out runs of the same
 synthetic layout". They support the held-out-sequence tier only: no unseen-camera,
 unseen-layout or unseen-site claim.
T14.3 The report states the number of leakage groups per partition and data origin
 beside every Target B interval.

## T15. R4 (time-to-collision and predicted post-encroachment) and baseline configurations (E-1.2.13; CR-018, D-27)

T15.1 Prediction. R4 uses the T8.3 constant-velocity prediction: the same footprints,
 the same yaw rule (T8.2; circumscribed disc when yaw is unknown), the same horizon τ
 (substrate_config.prediction_horizon_s). Footprints translate without rotation.
T15.2 TTC. ttc = the earliest t in [0, τ] at which predicted footprint clearance <= 0.
 ttc = 0 if clearance <= 0 at the frame. Computed by bisection on [0, t_at_min]
 (tolerance 1e-6 s). If no t in [0, τ] satisfies it, ttc is null (not_applicable)
 and the TTC part is 0. TTC part = 1 iff ttc < ttc_max.
T15.3 Predicted PET (pet_pred). For each object, its swept region over [0, τ] is the
 convex hull of its footprint at t=0 and t=τ. Conflict area A = intersection of the
 two swept regions. If A is empty, pet_pred is null (not_applicable) and the PET part
 is 0. Otherwise each object's occupancy of A is an interval [t_in, t_out] within
 [0, τ] (empty if it never enters A). If either interval is empty, pet_pred is null and
 the PET part is 0. pet_pred = max(0, t_in(second) - t_out(first)), where "first" is
 the object whose interval starts earlier (ties: the forklift is first).
 PET part = 1 iff pet_pred < pet_max. pet_pred is a predicted quantity and is never
 reported as "PET" without the suffix.
T15.4 Unknown. C_by_R4 is unknown (2) when the frame's world geometry is not
 calibrated (as written in §6.0) OR either object's velocity is null (T8.2/T9.1).
 Otherwise C_by_R4 = TTC part OR PET part.
T15.5 Configuration constraints. ttc_max <= τ and pet_max <= τ; otherwise refuse with
 ERR-SPEC. ttc_max and pet_max are R4-owned parameters (T11.1). R4 sets no borderline
 flag in this version (stated limitation).
T15.6 Baseline configurations (oracle and detector paths alike):
 BL-1 detection only, frame co-presence, no tracking: DEFERRED to M1b.
 BL-2 = R1. BL-3 = R2. BL-4 = R2 + R3. BL-5 = R2 + R4. BL-6 = R2 + R3 + R4 + R5.
 The contact cue applies in all configurations (T9.6, T10.3(c), T12.1).
 Primary comparisons: BL-2 vs BL-3, and BL-3 vs BL-6. Others are secondary.
 TTC/PET values used before G-PR are TEST-ONLY (ttc_max 1.5 s, pet_max 1.0 s).
T15.7 Outputs. pair_series gains ttc_s and pet_pred_s (nullable, reasons as above).

Fixtures required (passing and failing): head-on approach crossing within τ (ttc
found); approach whose crossing is beyond τ (ttc null); crossing paths with time gap
(pet_pred > 0, ttc null); simultaneous occupancy (pet_pred = 0); parallel paths (A
empty); null velocity -> unknown; uncalibrated -> unknown; ttc_max > τ -> ERR-SPEC;
disabled R4 parameters do not change S5 output (CT-T11-02 extended).

Source: Architect rulings of 13 Nov 2026, item B (Owner approval by forwarding them), appended verbatim.

## T16. Releases with mixed data origins (E-1.2.14; CR-020, D-29)

T16.1 A published release whose files have different data origins is registered as one
 dataset_source row per origin. The rows share the dataset name and differ in version:
 "<edition>@<revision>/<data_origin>". Each file belongs to exactly one row (VR-E-005).
 The rows share the pinned revision and the licence component.
T16.2 For leakage edges (§8, AR-31, T14), "within one dataset" means rows with the same
 dataset name. Scene, run, seed and render-parent edges apply across those rows.
T16.3 Results are never pooled across data origins (existing rule); each row's origin
 governs its fitness scope.

Tests: Warehouse_000 (synthetic) and Warehouse_001 (synthetic_transferred) register in
different rows and fall in ONE leakage group; declaring them in different partitions
raises ERR-LEAKAGE; a file listed under two rows is refused. Register 026/027 under the
real row with the D-24/D-26 conditions unchanged.
If CR-020 contains a complication this text does not cover, stop and report it.

Source: Architect rulings of 13 Nov 2026 (first set, item A; received by the agent after the second set), Owner approval by forwarding them, appended verbatim.

## T17. Oracle tracks and reference visibility from simulator truth (per camera) (E-1.2.15; CR-019, D-28)

T17.1 Visible frame. An object-frame is visible in a camera when the dataset lists a
 visible 2D box for it there (SDG: tight box; SmartSpaces: an entry in
 "2d bounding box visible"). The oracle track point is state tracked (detected, AR-29),
 box = that visible box, evidence_state by T8.6 from that box.
T17.2 Not-visible frame inside the visible span. For a frame between the object's first
 and last visible frame in that camera on which it is not visible: state predicted,
 evidence_state occluded_predicted, class inferred; position = the simulator 3D pose;
 box = the image-clipped reprojection of the object's 3D box with the camera's
 calibration. If that clipped reprojection is empty (outside the image or behind the
 camera): state lost, no point.
T17.3 Outside the visible span. Before an object's first and after its last visible
 frame in a camera there is no track point. An object never visible in a camera has no
 track in that camera. The SDG loose box is not used for any track point.
T17.4 Cameras without usable truth. A camera's annotation is simulator truth only when
 every annotation file has exactly as many lines as the video has frames and camera
 parameters exist. Otherwise the camera has no oracle track and no reference; its
 recording is used for reference-free checks only and is outside the oracle and
 reference populations. Counts are reported.
T17.5 Truth defect (SDG). When an object's loose box extends more than 120 px (native
 resolution) beyond the image-clipped reprojection of its own 3D box, the 2D truth of
 that object-frame is discarded and the frame is treated as not visible (T17.2, T17.3).
 The 3D pose is kept. Each case is logged as truth_defect. 120 px is an adapter
 data-quality parameter, not a research threshold: on the held data any value in
 (80.1, 157.3) selects the same 46 boxes. If any box has an excess in (80, 157] px,
 the adapter refuses (ERR-INVARIANT) and the case is reported. Boxes with a 3D corner
 behind the camera are not checked (stated limitation; count reported).
T17.6 Reference side. CV-SIM references use the same per-frame visibility: reference
 visible support is the T17.1 frames after T17.5. Reports state "reference visibility:
 binary, dataset-defined, no minimum visible area". Oracle tracks and references come
 from the same truth, so oracle-path agreement is rule-conformance evidence only.
T17.7 Reporting. Per dataset and run: tracked, predicted and lost frame counts,
 truth_defect count, cameras without truth, unchecked boxes.

Tests (passing and failing): visible -> tracked with the tight box; interior gap ->
predicted with the reprojected box; reprojection empty -> lost; leading and trailing
not-visible frames -> no point; never-visible object -> no track; line-count mismatch
-> no truth; the 5 eye_01 frames of run_2_seed_516797828 -> truth_defect, treated as
not visible; an excess of 100 px -> ERR-INVARIANT; SmartSpaces object absent from a
camera's visible list -> T17.2/T17.3.

Source: Architect rulings of 13 Nov 2026 (second set), item A (Owner approval by forwarding them), appended verbatim.

## T18. T17 amendments: guard band, absence length, run-length reporting (E-1.2.16; CR-022, D-31)

T17 amendments
1. T17.5 guard band. Replace "(80, 157] px" with "(90, 150] px". The 120 px threshold
   is unchanged. (Held data: ordinary boxes <= 80.1 px, defects >= 157.3 px.)
2. T17.2 absence length. A run of consecutive not-visible frames inside the visible
   span is predicted only when the run has <= g_max frames (the T8.1 parameter).
   A longer run is lost on every frame of the run (no points). The track identity
   continues when the object is visible again.
3. T17.7 adds: the distribution of not-visible run lengths per dataset and class
   (frames: min, median, P90, P99, max), for the G-PR choice of g_max.

Tests: run of g_max frames -> predicted; g_max + 1 -> lost on all its frames; the
eye_02 camera of run_22_seed_1886649344 now has an oracle track; an excess of 100 px
still raises ERR-INVARIANT; pair-level S4/S5 output on a fixture is identical before
and after amendment 2.

Source: Architect rulings of 14 Nov 2026, item B (Owner approval by forwarding them), appended verbatim.

## T19. T18 clarification: length of a not-visible run (E-1.2.17; CR-024, D-33)

T18 clarification: length of a not-visible run
 The length of a not-visible run (T18 amendment 2) is counted in eligible frames of
 the recording, as the T8.1 gap is. A run with <= g_max eligible frames is predicted
 on its eligible frames; a longer run is lost on every frame. Ineligible frames carry
 no track point in either case.

 Tests: a run of g_max + 1 camera frames of which one is ineligible -> predicted;
 a run of g_max + 1 eligible frames -> lost. Re-run the SDG and SmartSpaces counts.

Source: Architect rulings of 14 Nov 2026 (second set), item A (Owner approval by forwarding them), appended verbatim.

## T20. Visible on an eligible frame; reporting stratum forklift_turning (E-1.2.18; D-34, G-PR)

T20.1 Visible on an eligible frame (clarifies T17.2, T17.3, T19; AR-56 item 2)
 For T17.2, T17.3, T18 and T19, an object's visible frames in a camera are the frames
 on which the dataset lists it as visible AND that are eligible. The visible span runs
 from its first to its last such frame, and a not-visible run lies between two such
 frames. A dataset-visible frame that is not eligible carries no point and is part of
 the run around it.
 Test: 10 hidden, 1 visible but ineligible, 10 hidden, g_max = 15 -> one run of 20,
 lost on every frame. Re-run the counts; report any frame whose outcome changes.

T20.2 Reporting stratum forklift_turning
 For pair-frame k, let a and b be the first and last frames inside the window of length
 w_turn centred on t_k, shifted as in T9.1, on which the forklift's yaw (T8.2) is
 non-null, with t_b - t_a >= w_turn/2. forklift_yaw_rate = |fold(yaw_b - yaw_a)| /
 (t_b - t_a), where fold maps the difference to (-pi/2, pi/2]. forklift_turning is true
 when the rate > e_fturn, false when <= e_fturn, unknown when the yaw is null on the
 window or the window is too short. It is derived at report time, stored in no artifact,
 and changes no flag, label, episode or denominator. Unknown frames are reported as a
 third group. On the detector path it is reported only where yaw is supplied or
 validated (D-8).
 Tests: constant yaw -> false; 75 deg/s -> true; a half-turn jump -> false; null yaw ->
 unknown.

Source: Architect rulings of 14 Nov 2026 (G-PR), item A (Owner decision D-34 and approval by forwarding them), appended verbatim.

## T21. Interaction references from simulator truth (CV-SIM, M1a oracle path) (E-1.2.19; CR-025)

T21 Interaction references from simulator truth (CV-SIM, M1a oracle path)
T21.1 Definition source. Reference interactions are produced by applying configuration
 BL-6 (R2 + R3 + R4 + R5) with the pre-registration's base parameter values to the
 complete simulator truth of each person-forklift pair in each camera's timeline:
 simulator positions and yaw on every eligible frame on which both objects exist in the
 truth, whatever their visibility, with zero covariance, the frozen footprint priors and
 world geometry. reference_class = rule_conformance.
T21.2 Labels. Reference label groups are G1 only (O, H, PC), derived from the reference
 episode labels. No G2 (NM, UD, CT) reference exists on synthetic data.
T21.3 Assessability. A reference interaction is assessable in a camera iff both objects
 are visible (T17.1, T20.1) together on at least one eligible frame of its interval in
 that camera. Otherwise it is unobservable_reference for that camera (N4, T12.2) and is
 reported, not scored.
T21.4 Fixed reference. References are built once at the base values and do not change
 in MR-08/MR-12 sweeps; sweeps are scored against the base reference.
T21.5 Interpretation. Event metrics on the oracle path measure the effect of camera
 observability (T17-T20) and of the configuration's rules relative to BL-6, not
 perception. Reports state this beside EV-M1 to EV-M8.
T21.6 Dodge. SDG Dodge annotations are not used as references. Describe their fields in
 the qualification record; their use is a later decision.
Tests: an interaction visible throughout -> assessable, matched by BL-6 on the oracle
path; an interaction never jointly visible in a camera -> unobservable_reference; a
sweep run uses the same reference IDs as the base run; no G2 reference is produced.

Source: Architect ruling on CR-025, 14 Nov 2026, item B ("append to Appendix T as section T21, next contract version"; Owner approval by forwarding it), appended verbatim.

## T22. C-layer blind review and adjudication (E-1.2.20; CR-027, D-44)

T22. C-layer blind review and adjudication (E-1.2.20; CR-027, D-44)

T22.0 Scope. This section defines how annotator, reviewer_assessment, adjudication and validation_status_log (E-1.2.1 §5.8) are filled for E1 blind review. A/B annotation (D-23, VIA) is unchanged. A review batch is a seeded set of targets reviewed together. A reviewer has role c_layer_reviewer; an adjudicator has role adjudicator.

T22.1 Namespaces. (a) reference: blind judgments used as references (EV-M12, CV2). Every assessment has blind = true and shown_system_output = false (VR-E-053). (b) candidate_review: review of system output with that output shown; blind = false, shown_system_output = true. Never a reference, never in EV-M12, never given a reference_class. Its procedures are defined in T23. (c) No record moves between namespaces. A target may have records in both.

T22.2 Independence and exposure. (a) annotator.independence_attestation = true means the person attests that, for the recordings they assess in reference, they have not seen system output (episode lists, labels, flags, routes, per-clip results or per-clip report rows) and did not tune rule parameters by inspecting those recordings. Aggregate reports without per-clip rows and simulator-truth views (V-01) are not exposure. (b) Exposure rule: a person with a candidate_review assessment on any target of a recording is excluded from reference assessment and adjudication of every target of that recording. The tool enforces this from the stored assessments. (c) qualification_ref is non-null for every annotator: a short text such as "completed T22 handbook training and pilot batch, <date>" or "EHS professional, <years> years". Reports print a summary of qualifications, never names. (d) Annotators are pseudonymous. One annotator row per person and role. A person never adjudicates a target they assessed.

T22.3 Targets. (a) system_episode = an episode row of an S5 artifact (target_id = episode ID); the target type in single-camera milestones. (b) system_event = a candidate_event row; from M2 only. (c) ref_event = a ref_interaction row (target_id = rin_ ID); reference only; writes no status entry.

T22.4 What a blind reviewer is shown (reference). Shown: the recording's frames from max(recording start, onset − c_pad_s) to min(recording end, I⁺ end + c_pad_s), without any marker of the interval; in scenes with more than one person or more than one forklift, a neutral outline per object of the target pair (one fixed colour per object for the whole clip); playback controls; the T22.5 label definitions. Never shown: any system label, flag, provider value, clearance, speed, TTC, PET, borderline flag, review route, configuration name, status, another person's record, or the target's sampling stratum.

T22.5 The assessment. (a) Labels, judged from the video alone:

ct: the person and the forklift (including forks, mast or load) appear to touch, or the person is struck, pushed or pinned, or an abrupt reaction at the closest moment makes contact likely.
nm: no contact is seen, but the forklift (or its forks or load) was moving and came close enough that contact was avoided only by a reaction (sudden stop, swerve, step back, jump) or by a margin so small that slightly different timing could plausibly have led to contact.
ud: it may be nm or ct, but the video does not show the decisive moment (occluded, out of frame, or overlapping in the image so that contact cannot be ruled in or out).
not_hazardous: the person and the forklift are near each other but there is no conflict: forklift and forks stationary, or paths that do not conflict, or separation clearly adequate, or a barrier between them.
unsure: the reviewer can see the interaction but cannot decide among the labels above. (ud describes the video; unsure describes the reviewer's decision.) (b) confidence: f64 in {1.0, 2.0, 3.0} = low, medium, high, the reviewer's confidence in the chosen label. Other values are refused. (c) rationale: required; at least one sentence saying what was seen. (d) review_time_s: f64 seconds, nullable; wall time from first display of the clip to submission, measured by the tool. Reported descriptively only. (e) One assessment per (annotator, target, namespace). A correction is a new assessment that names the replaced one in its rationale; adjudication uses the latest per annotator.

T22.6 Reference batches. (a) Sampling frame: the episodes of one named configuration (default BL-6) in one partition (validation while D-37 stands). Strata: the episode's summary_label (CT, UD, NM, PC, H, O). Allocation: equal across the strata present, capped at stratum size, remainder by largest remainder with ties broken by the batch seed; draw without replacement inside each stratum; episodes sorted by episode ID; numpy PCG64. (b) Each target gets exactly two reference assessments, one per reviewer. Each reviewer sees the batch in their own order: a seeded shuffle whose seed is derived from the batch seed and the annotator ID. (c) Pilot: before the first batch, a pilot batch of n_pilot targets is reviewed by both reviewers and the adjudicator together, discussed, and used for handbook examples. Pilot targets are flagged, excluded from later batches, and never enter EV-M12 or agreement statistics. (d) Each batch has an immutable manifest (JCS JSON in the validation store): batch_id (rvb_<uuid7>), namespace, configuration ID, partition, strata counts, seed, target IDs, annotator IDs and roles, c_pad_s, created_utc. It cannot change once the first assessment exists.

T22.7 Adjudication. (a) Both assessments have the same label and neither is unsure: the tool writes one adjudication with final_label = that label, tier = tier1, method = agreement. (b) Otherwise: the adjudicator reviews the target under T22.4, additionally seeing both assessments (label, confidence, rationale), and gives final_label (any of the five labels): tier = tier2, method = adjudicator. (c) If no adjudicator is available, the two reviewers may agree a final label together: tier = tier2, method = consensus_meeting, counted separately in reports. (d) Tier-1 audit: a seeded share a_audit of each batch's tier1 targets is reviewed blind by the adjudicator as a third reference assessment. If the label differs, the adjudicator re-adjudicates under (b) and the target becomes tier2; the earlier tier1 adjudication stays in the store. The audit agreement rate is reported per batch. (e) method takes only the values agreement, adjudicator, consensus_meeting. assessment_ids lists every assessment considered.

T22.8 Status entries. (a) Only system_episode and system_event targets get validation_status_log entries. config_id = the rule_configuration ID of the target's S5 artifact; layer = C. (b) The target's automated G2 label is mapped lbl_nm → nm, lbl_ud → ud, lbl_ct → ct, none of the three → not_hazardous. final_label unsure → disputed; final_label equal to the mapped label → confirmed; otherwise → rejected. (c) reference: written when the adjudication is written; basis_ids = the adjudication ID. Reviewers never see the status log during a batch.

T22.9 reference_class. An adjudication in reference has reference_class = independent_expert_judgment iff every assessment in assessment_ids is blind with shown_system_output = false; every annotator involved, the adjudicator included, has independence_attestation = true and a non-null qualification_ref; and none is excluded under T22.2 (b). Otherwise it is refused in reference (ERR-SPEC).

T22.10 Agreement and reporting. (a) agreement_stat_ref = the batch_id. Per batch: Cohen's κ between the two reviewers over the five labels, and over the four labels excluding targets where either said unsure; Krippendorff's α (nominal) where an audit gives three assessments; the tier-1 audit agreement rate; counts by tier and method; review_time_s median and P90 per reviewer. (b) EV-M12 uses only reference adjudications with reference_class = independent_expert_judgment, pilot excluded; categories nm, ud, ct, not_hazardous against the mapped system label; final unsure reported separately, not in κ; Tier 1 and Tier 2 separately. (c) Reports state the reviewer qualifications summary, the namespace, the targets per stratum, and that the sample is stratified by system label, so κ describes agreement on the batch, not on all episodes. Wording rules W1–W6 apply; labels are printed as codes or as "candidate near miss", never as "near miss".

T22.11 Data scope. Fixtures and synthetic validation episodes. Synthetic results are at most experimental (T12.5). Safe and Unsafe Behaviours only under D-24 (c), D-26 and the access log, once system episodes exist on it. No C-layer review of SmartSpaces Warehouse_026/027 (D-24 b). Test-partition targets only after D-37 is lifted.

T22.12 Parameters (recorded in each batch manifest). c_pad_s = 3.0; n_batch = 60; n_pilot = 20; a_audit = 0.10; batch seed supplied by the Owner per batch.

T22.13 Schema change (minor). reviewer_assessment gains review_time_s · f64 · nullable. No other table, enum or ID rule changes.

Fixtures and tests: FX-13 (two reviewers disagree, Tier 2 adjudication): a system_episode with lbl_nm; reviewer A nm (2.0), reviewer B ud (3.0), both blind and attested; adjudicator ud → tier2, method adjudicator, final_label ud, reference_class independent_expert_judgment; status entry rejected; basis = the adjudication. FX-13a: both reviewers not_hazardous on an episode with no G2 label → tier1, agreement, status confirmed, written without an adjudicator. FX-13b: one reviewer unsure, the other nm; adjudicator unsure → tier2, status disputed; excluded from EV-M12 κ and counted under unsure. FX-13c: a reviewer with a candidate_review assessment on the same recording submits a reference assessment → refused (T22.2 b). FX-13d: a reference assessment with shown_system_output = true → refused (VR-E-053). FX-13e: a tier1 target in the audit sample where the adjudicator disagrees → a new tier2 adjudication; the tier1 record remains; audit agreement rate 0/1. FX-13f: an adjudicator with independence_attestation = false → adjudication refused in reference (T22.9). Also: batch allocation by largest remainder on a hand-made stratum table; per-reviewer order differs and is reproducible from the seed; a ref_event target writes no status.

Source: Architect protocol for CR-027 (Owner decision D-44, option (a), 19 Nov 2026; Owner approval by pasting it), appended verbatim.

## T22.14 Readings of T22 (E-1.2.21; CR-028, D-46)

T22.14 Readings of T22 (CR-028, D-46).
 (a) Audit size (T22.7 d): ceil(a_audit × number of tier1 targets of the batch).
 (b) α units (T22.10 a): Krippendorff's α (nominal) over the audited targets only, three
     assessments each. The number of audited targets is printed beside α. With fewer
     than 5 audited targets α is printed as "not computed (n < 5)".
 (c) Earlier batches (T22.6 a): a target already drawn into any batch (pilot or
     reference) on the same configuration and partition is excluded from every later
     batch. Each target is reviewed in at most one batch.
 (d) Pilot records (T22.6 c): pilot assessments are stored in reference with the batch
     flagged pilot. No adjudication, status entry or audit is written for pilot targets,
     and pilot assessments never count toward reference_class, EV-M12 or agreement.
 (e) Allocation under capping (T22.6 a): water-filling. Strata smaller than the equal
     share take their whole size; the freed places are shared equally among the other
     strata, repeated until no remaining stratum is below its share; the integer
     remainder goes by largest remainder with ties broken by the batch seed. If all
     strata are exhausted, the batch holds fewer than n_batch targets and the manifest
     says so.
 Tests: the five CR-028 examples, with the expected values stated in CR-028 for (e)
 (CT 7, UD 11, NM 11, PC 11, H 11, O 9); FX-13e unchanged; a re-draw of a target from an
 earlier batch is refused; α with 4 audited targets prints "not computed (n < 5)".

Source: Architect ruling on CR-028 (Owner decision D-46, 19 Nov 2026; Owner approval by pasting it), appended verbatim.

## T23. Reporting workflow, indicators and simulated regulator view (E-1.2.22; D-48)

T23.0 Scope and status.
 (a) T23 defines a product layer on top of the S5 outputs: AI-started and human-started
     reports, a two-level manager review, an append-only report history, indicators,
     disagreement flags and a simulated regulator view.
 (b) It is a research prototype and a proposal. No data is sent anywhere. "Regulator
     view" means a local, read-only page that shows what a regulator could see under
     the proposal.
 (c) Manager decisions are records of what managers decided. They are never references
     (T22.1 b) and never evidence that the AI was right or wrong. Accuracy claims use
     only T22 reference adjudications.
 (d) Recordability is always a human decision (T23.7). The system never decides it.

T23.1 Entities and roles.
 (a) establishment: a workplace (in the demo, a simulated one). area: a part of an
     establishment, with the cameras that watch it. Every camera belongs to at most one
     area.
 (b) Roles, held by pseudonymous users (one person = one pseudonym, AR-61 item 4):
     area_manager (one or more areas), safety_manager (one establishment), worker,
     oversight (read-only regulator view), owner (setup). One person may hold several
     roles, but never decides a report at two levels (an area manager who decided a
     report cannot act on it as its safety manager).

T23.2 AI alert intake.
 (a) Source: the episodes of one named configuration (workflow parameter
     `wf_source_config`; default BL-6) whose G2 label is NM, UD or CT. Episodes labelled
     only O, H, PC or IE create no report; they count in exposure indicators only.
 (b) Grouping: episodes on cameras of the same area whose intervals overlap after each
     is widened by t_group_s on both sides form one alert group, built transitively.
     One alert group creates one report. The report lists every member episode. This is
     a product heuristic for duplicates across cameras, not the M2 linkage contract.
 (c) Report kind: incident_draft if any member has G2 label CT; otherwise near_miss.
 (d) Pre-filled fields (all marked "pre-filled by the system", editable by the area
     manager while the report is pending):
     establishment, area, camera(s); occurred_at (earliest onset, on the simulated
     calendar in the demo); duration_s; objects involved ("person", "forklift");
     ai_label ("candidate near miss", "candidate, undetermined" or "candidate contact");
     min_clearance_m with its geometry method (null with reason if unavailable);
     evasive_action_observed (from R5, true / false / unknown); evidence clip
     reference(s) (evidence_clip rows, one per member); a templated description:
     "The system flagged a candidate <label> between a person and a forklift in <area>
     at <time>. Minimum measured separation <x> m (<method>). Review the clip before
     deciding." No free text is generated by a language model.

T23.3 Report kinds and fields.
 (a) near_miss: occurred_at, area, description, people involved (pseudonyms),
     contributing_factors (multi-select: speed, visibility, blind corner, pedestrian
     route, load obstructing view, training, procedure, other), immediate_action,
     corrective_action, notes.
 (b) incident: the near_miss fields plus the T23.7 fields.
 (c) A human may change a near_miss to an incident or back while the report is
     pending; the change is logged.

T23.4 States and actions.
 States: pending_am, pending_sm, recorded, closed_rejected, closed_duplicate.
 | Action | Who | From | To | Required |
 |---|---|---|---|---|
 | create_ai | system | — | pending_am | T23.2 |
 | create_human | any signed-in user | — | pending_am | T23.6 |
 | am_approve | area_manager of the area | pending_am | recorded | label nm or ct |
 | am_reject | area_manager of the area | pending_am | pending_sm | reason (T23.5 b) |
 | am_duplicate | area_manager of the area | pending_am | closed_duplicate | duplicate_of report |
 | sm_uphold | safety_manager | pending_sm | closed_rejected | note |
 | sm_overturn | safety_manager | pending_sm | recorded | label nm or ct, note |
 | sm_reclassify | safety_manager | recorded | closed_rejected | reason, note |
 | sm_reopen | safety_manager | closed_rejected, closed_duplicate | pending_sm | note |
 | edit_fields | area_manager (pending_am), safety_manager (pending_sm, recorded) | — | same | changed fields |
 | set_recordability | safety_manager | recorded (incident only) | same | T23.7 |
 | sm_note | safety_manager | any | same | text |
 Nothing is deleted. Every action is an entry in the report log (T23.15).

T23.5 What decisions write (AI-started reports only).
 (a) am_approve writes one reviewer_assessment in candidate_review (blind = false,
     shown_system_output = true) per member episode, with the label chosen (nm or ct),
     confidence 3.0 unless the manager lowers it, and the rationale from the form.
 (b) am_reject requires a reason from {not_hazardous, no_person_or_no_forklift,
     cannot_tell_from_video, other}; it writes one reviewer_assessment per member with
     label not_hazardous for the first two, ud for cannot_tell_from_video, unsure for
     other.
 (c) sm_uphold, sm_overturn and sm_reclassify write one adjudication per member in
     candidate_review: tier2, method adjudicator, final_label = the area manager's
     label (uphold), the safety manager's label (overturn), or not_hazardous
     (reclassify, unless the safety manager picks ud).
 (d) Status entries (validation_status_log, namespace candidate_review, layer C), per
     member episode: after am_approve, the T22.8 (b) mapping of the area manager's label
     against the episode's G2 label; after am_reject, disputed; after an sm_ action, the
     T22.8 (b) mapping of the final label. basis_ids = the assessment or adjudication.
     Status describes the AI label, not the report: an approved report can carry a
     status "rejected" when the manager chose a different label than the AI.
 (e) Human-started reports write no assessment, adjudication or status entry.

T23.6 Human-started reports.
 Any signed-in user can file a near_miss or incident report for an area: occurred_at,
 description and the T23.3 fields. It enters pending_am and follows T23.4. A
 human-started report never requires an AI alert, and an AI alert never blocks or
 replaces one (29 CFR 1904.35: a reasonable reporting procedure).

T23.7 Incidents and recordability.
 (a) Incident fields (an equivalent-form layout of the OSHA 301 case items, for manual
     transcription): date of injury or illness; time the employee began work; time of
     event, or "cannot be determined"; what the employee was doing just before; what
     happened; the injury or illness; the object or substance that directly harmed the
     employee; date of death if any; treated in an emergency room (yes/no);
     hospitalized overnight (yes/no); employee pseudonym; health care professional
     (optional).
 (b) recordability: set only by the safety_manager, on a recorded incident:
     recordable ∈ {yes, no, undetermined}; when yes, one or more criteria from {death,
     days_away, restricted_or_transfer, medical_treatment_beyond_first_aid,
     loss_of_consciousness, significant_diagnosed} (29 CFR 1904.7 general recording
     criteria), with days counts where they apply; decided_by and a note. Until it is
     set, the incident shows "recordability pending".
 (c) Export: a "301-style" JSON and CSV of one incident, headed "Equivalent-form data
     for manual transcription. Not a submission to OSHA."

T23.8 Indicators (per establishment, per area, per period).
 For a period P (an ISO week on the report's occurred_at; simulated calendar in the
 demo). Every share is printed with n and its Wilson 95 % interval (T-13 function).
 I1 AI alert reports created.
 I2 area-manager approval share: am_approve / (am_approve + am_reject) over AI reports.
 I3 area-manager rejection share: 1 − I2, same n.
 I4 safety-manager overturn share: sm_overturn / (sm_overturn + sm_uphold).
 I5 safety-manager reclassification share: sm_reclassify / recorded AI reports.
 I6 reports pending longer than t_pending_days (count, by state).
 I7 recorded near misses: AI-started and human-started counted separately; for
     AI-started, also per monitored camera-hour, where monitored time is the S1
     coverage of the area's cameras with assessable footage in P. Unmonitored time is
     never counted as zero events.
 I8 human-only signal: recorded human-started near_miss reports in an area and time
     that was monitored, with no AI alert report in that area within ±t_link_s of
     occurred_at.
 I9 recordable cases (recordable = yes) by criterion; hours worked (entered); when
     hours worked are entered, the incidence rate = cases × 200,000 / hours worked
     (BLS formula), labelled with its period. Never computed from monitored
     camera-hours.
 Indicators are computed at view time from a snapshot of the report log; each view
 prints the log length and head hash it was computed from.

T23.9 Disagreement flags.
 F1 rejection: n(I3) ≥ n_flag_min and the Wilson lower bound of I3 > θ_rej.
 F2 overturn: n(I4) ≥ n_flag_min_sm and the Wilson lower bound of I4 > θ_over.
 F3 stale: I6 > 0.
 F4 human-only: I8 ≥ k_miss.
 Each flag shows the numbers that raised it and the fixed text: "Above the set
 threshold. Possible causes include false alerts by the system, under-recording,
 or different definitions. The cause is not determined by this flag." Flags change no
 report, state or record.

T23.10 Simulated regulator view.
 Read-only, oversight and owner roles. Per establishment and period: I9 (recordable
 counts by criterion, hours, incidence rate when available); I7 and I8; I2–I5 with n
 and intervals; flags F1–F4; monitored camera-hours and the share of areas with any
 monitoring; the report-log and status-log verification results; the workflow
 parameters in force. Banner: "Simulated regulator view: a proposal. No data leaves
 this computer." Export of the view as JSON and CSV with the same banner.

T23.11 Separation from the research reference and the demo draw.
 (a) Demo draw: from the SDG validation runs, 3 runs per generation family (D-35
     families), seeded; one establishment per family (simulated names), one area per
     run (its cameras). Each run gets a simulated occurred_at offset on a 4-week
     simulated calendar (seeded). Recorded in an immutable demo manifest.
 (b) Every episode of a demo run (all of its cameras) is excluded from the T22
     sampling frame (amends T22.6 a). If any such episode is already in a T22 batch,
     the demo draw is refused (ERR-SPEC) and nothing is written.
 (c) Anyone who acts in the workflow on a demo report is exposed for those recordings
     (T22.2 b). Because demo runs are outside the T22 frame, this never affects
     reference review.

T23.12 Wording.
 Automated outputs keep W1–W6: "candidate near miss", "candidate, undetermined",
 "candidate contact". A report in state recorded with label nm may be called a
 "recorded near miss (manager-approved)" or "recorded near miss (safety-manager
 overturn)". "Near miss" never appears unqualified. "Recordable" appears only for
 recordable = yes set by a safety manager. The linter accepts these phrases in
 workflow pages and nowhere else.

T23.13 Privacy and demo data.
 Pseudonyms only. In a demo establishment every incident field is fictional and the
 page and export say "fictional demo entry". No real person's data is entered. Video
 is the synthetic dataset's own.

T23.14 Parameters (workflow settings chosen by the Owner, not research thresholds;
 stored in wf_config and printed on the regulator view).
 wf_source_config = BL-6; t_group_s = 2.0; t_pending_days = 7; θ_rej = 0.5;
 θ_over = 0.3; n_flag_min = 10; n_flag_min_sm = 5; t_link_s = 60; k_miss = 2.
 A demo store may lower n_flag_min and n_flag_min_sm; the view prints the values used.

T23.15 Schema additions (new tables, minor version; human-entered rows use UUIDv7).
 wf_config (one row per store version: the T23.14 values, created_utc).
 wf_establishment (est_id, name, demo bool).
 wf_area (area_id, est_id, name, camera_ids list).
 wf_user (user_id, pseudonym, roles list, est_id?, area_ids list; passphrase hash kept
   outside the table as in V-02).
 wf_report (report_id, kind_initial, origin enum{ai, human}, est_id, area_id,
   member_episode_ids list?, created_utc): the immutable header.
 wf_report_log (JSONL, append-only, hash-chained like validation_status_log): seq,
   entry_id, report_id, action (T23.4), actor_user_id or "system", state_before,
   state_after, field_changes (map, before and after values), label?, reason?, note?,
   linked_record_ids (assessments, adjudications, status entries), created_utc,
   prev_hash, record_hash. Current fields and state = the fold of the log.
 wf_hours (est_id, period, hours_worked, entered_by, created_utc).
 demo_manifest (JCS JSON): seed, runs, establishments, areas, calendar offsets, source
   configuration and artifact IDs.

Fixtures and tests:
 FX-14: AI near-miss alert (one NM episode); area manager approves with nm → recorded;
  one candidate_review assessment; status confirmed; I2 = 1/1.
 FX-14a: AI NM alert; area manager rejects (not_hazardous); safety manager upholds →
  closed_rejected; status disputed, then rejected; I3 = 1/1; I4 = 0/1.
 FX-14b: as FX-14a but the safety manager overturns with nm → recorded (safety-manager
  overturn); status confirmed; I4 = 1/1.
 FX-14c: AI alert with a CT member → incident_draft; approved with ct; safety manager
  sets recordable = yes (medical_treatment_beyond_first_aid); hours worked 200,000 for
  the period → incidence rate 1.0; the 301-style export carries the banner and every
  T23.7 (a) field.
 FX-14d: human-started recorded near miss in a monitored area with no AI alert within
  60 s → I8 = 1; with k_miss = 1, F4 raised.
 FX-14e: three episodes on three cameras of one area, onsets 0.0 s, 1.5 s and 3.2 s, each
  1.0 s long, t_group_s = 2.0 → one report with three members (transitive grouping);
  one assessment and one status entry per member on approval.
 FX-14f: 12 decided AI reports in one establishment and period, 10 rejected, θ_rej 0.5,
  n_flag_min 10 → F1 raised (Wilson lower bound of 10/12 ≈ 0.552); with 6 of 12
  rejected → F1 not raised.
 FX-14g: change one byte of a stored report-log entry → chain verification fails and the
  report page shows it.
 FX-14h: every workflow page and export passes the linter; "near miss" unqualified is
  refused; an automated alert reads "candidate near miss".
 FX-14i: a demo draw whose runs include an episode already in a T22 batch is refused;
  a T22 batch drawn after a demo draw contains no episode of a demo run.
 Also: role permission refusals; an area manager who decided a report cannot act on it
 as safety manager; set_recordability on a near_miss is refused.

Source: Owner decision D-48 (19 Nov 2026; Owner approval by pasting it), appended verbatim.

## T23.16–T23.27. Corrections to T23: namespace isolation, lifecycle, monitoring, grouping and reference protection (E-1.2.23; D-49)

### 2. Governing separation (Owner §4)

| Workstream | What it is | Evidence it may produce | Claims it may support |
|---|---|---|---|
| **A. Scientific instrument** | S0–S8, T21 references, T22 reference namespace, pre-registration | Measurements with uncertainty and coverage; EV, CM, GV metrics; EV-M12 | Detection, tracking, measurement and event-level reliability, within the scope of the data |
| **B. Operational reporting prototype** | T23 workflow, `candidate_review` namespace, `wf_*` tables | Records of human decisions, descriptive workflow measures | That the workflow can be operated and audited. Nothing about CV accuracy, true event rates or establishment safety |
| **C. Safety-performance measurement research** | Future, separately authorised (RQ2/RQ3) | none yet | none yet |

Rules that follow from the table:
- **B never feeds A.** This is enforced in T23.16 and T23.25.
- **Only exports cross from A to B.** A reads none of B's records.
- **C uses neither A nor B until it is authorised.**

The CM-03 forklift coverage limitation of the alert source (0.12 on pilot column C) must appear on every B page that shows AI alerts (T23.26). E2 is not affected by anything in this addendum: no E2 table, rule or plan changes.

---

### 3. Normative contract amendments (E-1.2.23)

**T23.16 Namespace isolation of adjudications** (CR-030 item 1; approved, strengthened).

(a) *Namespace.* An adjudication's namespace equals the namespace of every assessment in its `assessment_ids`. A mix is refused with ERR-SPEC.

(b) *Nullability.* This holds across all namespaces. The enum has exactly two values, `reference` and `candidate_review` [V].
- `reference_class` is nullable, with `reference_class_null_reason`.
- In `reference`, `reference_class` is required, set by T22.9, and its null reason is null.
- In `candidate_review`, `reference_class` is null and `reference_class_null_reason = not_applicable`.
- Any other combination is refused (new validation rule VR-E-056).

(c) *Tier and method semantics.* In `reference`, `tier` and `method` have the T22.7 meaning: inter-reviewer agreement or adjudication. In `candidate_review` they mean only that the record is a second-level manager decision.
- `tier2` there does not mean disagreement between independent reviewers.
- No report, page or statistic may group, count or print `tier` without first filtering on namespace.
- Pages print a `candidate_review` adjudication as "safety-manager decision", never as "Tier 2".

(d) *Exclusion.* Records of the `candidate_review` namespace must never enter:
- EV-M12;
- κ, α or any other agreement statistic (T22.10);
- an `acceptance_criterion` evaluation or a `measurement_fitness` record (§9.6);
- a reference set, `ref_*` table or reference label;
- a T22 batch;
- any S8 artifact.

(e) *Enforcement.*
- Evaluation code obtains adjudications only through one accessor, `reference_adjudications(...)`. It returns rows with `namespace = reference` and `reference_class = independent_expert_judgment`, excluding pilot targets.
- A static test fails if any module under `src/rq1/evaluation/`, `src/rq1/pipeline/` or `src/rq1/review/protocol.py` reads the adjudication or assessment files in any other way.

(f) *Stored rows.* No stored row is rewritten. A reader treats a missing `reference_class_null_reason` as null; this is valid only for `namespace = reference` rows with a non-null class. A stored `candidate_review` adjudication without a null reason is ERR-INVARIANT (none should exist under CR-030's current behaviour [V]).

**T23.17 Review indicators by report origin** (approved). I2 to I5 and flags F1 and F2 cover AI-started reports only. Human-started reports have their own line, which feeds no flag. The full specifications are in §5.

**T23.18 Period, as-of and revision** (approved (a), (b), (d) and (e); (c) and (f) replaced by T23.19 and T23.23).

(a) *Occurrence period.* A report belongs to the ISO week of its current `occurred_at`. The demo uses the simulated calendar.

(b) *As-of cutoff.* Every indicator, flag and regulator-view figure is computed from the report log truncated at `as_of`.
- The truncated log is the entries whose `created_utc` ≤ `as_of`.
- The log must be non-decreasing in `created_utc`; otherwise verification fails with ERR-INVARIANT.
- A view prints `as_of`, the truncated log length and its head hash. The same log, `as_of` and parameters give the same view (test FX-14w).

(c) *Revision against occurrence.* Moving a report between periods, kinds or states after its first decision is a **revision**: a log event about the record, not a change in what happened.
- Each cell prints "revised after first decision: n", the reports in the cell with a field, state or recordability entry after their first manager decision.
- Comparing the same cell at two `as_of` values shows revisions. It never shows new occurrences unless new reports were created.

(d) *Reports still under review.* Each share prints beside its n the number of reports in the population that are still pending in the relevant state, as "undecided: n". So a difference in completed reviews is visible and is never folded into a share.

(e) *Kind and label.* At `am_approve` and `sm_overturn`, the kind follows the label: nm → `near_miss`, ct → `incident`. The change goes in the same entry's `field_changes`.

**T23.19 Recordability lifecycle** (replaces the D-49 draft's T23.18 (c); Owner §2.3).

(a) *Separate concepts.*
- The **workflow state** is pending, recorded or closed.
- The **classification** is kind and label.
- The **recordability determination** is a human decision with its own history in the log.

None of these changes another implicitly.

(b) *Determination status.* The current determination of an incident report is the fold of its recordability entries:
- `not_set` (no entry);
- `yes` with criteria;
- `no`;
- `undetermined`;
- `withdrawn`.

(c) *New action `withdraw_recordability`.* Who: safety_manager. From: any state. Required: a reason from {classification_changed, entered_in_error, event_not_work_related, other} and a note. The previous determination stays in the log. Status becomes `withdrawn`. A later `set_recordability` may set it again.

(d) *Reopening.* `sm_reopen` leaves the determination unchanged.

(e) *Reclassifying.* `sm_reclassify` of a report whose determination is `yes` or `no` is refused (ERR-SPEC). The safety manager must first either withdraw the determination or edit the kind or label. A determination therefore never silently disagrees with a closed or reclassified report.

(f) *Effect on I9.* Only definitive cases count: current state `recorded`, current kind `incident`, and determination `yes`. The page prints these beside I9 and outside the rate:
- `not_set`;
- `undetermined`;
- `withdrawn`;
- `yes` on reports not currently recorded.

The incidence rate is labelled **provisional** whenever any incident report in the period is `not_set` or `undetermined`.

**T23.20 Duplicate and split lifecycle** (approved T23.20 of the D-49 draft, plus Owner §2.4 and §2.6).

(a) `sm_uphold` requires that the latest area-manager decision on the report is `am_reject`. Its `final_label` is the label of that assessment. Otherwise it is refused.

(b) *`am_duplicate` requires `duplicate_of`*, which must be a different report of the same establishment whose current state is not `closed_duplicate` or `closed_split`. This prevents chains and cycles.
- The link is stored in `field_changes`.
- The original report shows "duplicates: n" with links.

(c) *New action `sm_confirm_duplicate`.* Who: safety_manager. From: `pending_sm`, after `sm_reopen` of a `closed_duplicate`. To: `closed_duplicate`. Required: a note. `duplicate_of` is unchanged.

(d) *After reopening a duplicate*, the safety manager can either confirm the duplicate or overturn it. `sm_overturn` from that state:
- sets `duplicate_of` to null in `field_changes`;
- requires a `group_resolution` (T23.21 (d));
- records the report as its own event.

A report counts in I7 or I9 only while its current state is `recorded`, so a report never counts twice.

(e) *New action `am_split`.* Who: area_manager of the area. From: `pending_am`, on an AI report with at least two members. To: new terminal state `closed_split`. Required: a partition of the member episodes into two or more non-empty parts, and a note.
- One new AI report is created per part, pending_am, through a `create_ai` entry carrying `split_from`.
- No assessment, adjudication or status entry is written for the original.

(f) *Logging and failure.* Every successful action, including the three that write no scientific record, is one hash-chained log entry. A refused action writes nothing to any file and leaves state unchanged (test FX-14v).

**T23.21 Alert grouping, physical-event identity and timebase** (replaces T23.19 of the D-49 draft; (a) is approved).

(a) *Three levels.* They are kept distinct:
1. **Alert grouping** (T23.2 b): a review convenience. One group is one report, with no claim that the members show one interaction.
2. **Evidence-supported linkage**: the M2 contract (`gpw`, `aligned_session` timelines). It is not used by the workflow. Workflow grouping never writes, reads or replaces linkage records.
3. **Human resolution** (T23.20 (e), T23.21 (d)): the manager's statement of how many interactions a report shows.

(b) *Closed intervals* (approved): widened intervals that only touch are merged.

(c) *Timebase.* Episodes on different cameras are grouped only on a declared common axis.
- In the demo, the axis is the run's calendar offset plus recording-local time. The demo manifest must name the evidence: `timebase_evidence_ref = "qualification.md §2.7: one simulator clock per SDG run (dataset card); equal frame counts"` [V]. The tag is `workflow_timebase_declared`; it is not a `clock_alignment` and has no σ.
- Outside the demo, a common axis exists only through an `aligned_session` timeline. Otherwise each camera's episodes form groups on their own, and the report says "grouped per camera: no common clock".
- If the demo intake meets a run that has no evidence reference, it groups per camera.

(d) *`group_resolution` at decision.* For an AI report with two or more members, `am_approve` and `sm_overturn` require `group_resolution` ∈ {one_interaction, cannot_tell}. If the members show several interactions, the area manager uses `am_split` before deciding. A safety manager acting on such a report from `pending_sm` sends it back to the area manager with `sm_reopen`; the agent confirms this path in CR-031.

**T23.22 User-entered text** (approved; the Architect's D-49 text unchanged, with the Owner's safeguards).
- User text is stored verbatim and HTML-escaped.
- It is shown in a block marked "entered by <pseudonym>".
- It is never used as a label, a classifier input or a pre-filled field.
- The linter skips only fields marked user-entered.
- A report is never refused for its wording.
- The privacy notice (T23.13) is shown on every free-text field.

**T23.23 Monitoring and observability** (replaces the D-49 draft's T23.18 (f); Owner §2.2; CR-030 item 6).

(a) *Coverage levels, per camera and interval:*
- **usable footage:** S1 coverage state `usable`;
- **processed:** covered by exactly one S5 artifact of `wf_source_config` named in the store's source manifest. Two artifacts of that configuration covering the same camera and window give ERR-SPEC;
- **monitored:** usable and processed.

`usable_degraded` footage is reported in its own column and is not monitored. A camera with no S5 output of the source configuration is never monitored [answers CR-030 item 6 (a) and (d)].

(b) *Monitored area time.* For an area and period, this is the duration of the **union** over the area's cameras of their monitored intervals. Several cameras watching at once, or repeated processing, therefore add no time. Camera-hours (the sum) are printed as a descriptive column only and never used as a denominator.

(c) *Observability of a human-reported event.* Each human-started report gets one category:
1. **unmonitored:** no camera of the area is monitored at any instant in [occurred_at − t_link_s, occurred_at + t_link_s].
2. **monitored, not observable:** monitored, but the area manager recorded `camera_observability = not_observable` (the event was outside every camera's view, or occluded) for the cameras checked.
3. **observability undetermined:** monitored, and `camera_observability` is `undetermined` or not set. This is the default.
4. **observable, matched:** `camera_observability = observable` for at least one camera c, and some AI report of the area (any state other than `closed_split`) has a member episode on c that overlaps the window.
5. **observable, no matching AI alert:** `observable` for at least one camera, and no such member episode.

`camera_observability` is set by the area manager on a human-started report, with the camera IDs checked. It is a field of the report, not an assessment.

(d) *Interpretation.* Only category 5 is a **potential AI miss**. It is printed as a count with the reports listed and the caption "Descriptive workflow measure. A human report without a matching alert is not evidence of a detector miss; miss rates require the T22 reference method." No recall or false-negative rate is ever computed from human reports.

(e) *Zero and missing.* A rate with zero monitored time prints "not computable: no monitored time", never 0. A zero numerator prints "0 in <h> monitored area-hours. Absence of an alert is not absence of an event." Every rate prints its numerator, denominator and the unprocessed-camera count of the area.

**T23.24 Combined pre-filled values** (replaces the D-49 draft's T23.21 (b) and (c); Owner §2.5; AR-63 item 6).

(a) *Comparability.* Member clearances are combined only if every non-null member value has the same `geometry_method` and the same calibration tier. Otherwise no combined value is shown; the form says "not combined: members use different geometry methods" and lists each member's value.

(b) *The combined value.* It is the smallest comparable member clearance, labelled "smallest estimated separation among members (estimate from camera geometry, not a verified measurement)". With it the form shows:
- the source episode and camera;
- the `geometry_method`;
- `clearance_sigma_m` and `sigma_status`;
- the evidence sufficiency (`q_state` and reasons) at that pair-frame;
- `prov_class`;
- the S4 artifact ID.

(c) Each member's own values are always listed.

(d) *Use.* The combined value is a review aid. It is never stored as a measurement, never used in an indicator, flag, score, severity or ranking, never written to a reference or `ref_*` row, and never exported except as a copy of the member values with their provenance.

(e) *Template wording.* The T23.2 (d) template changes to "Smallest estimated separation <x> m (<method>, <sigma status>)". `evasive_action_observed` reads "observed by the system in at least one member" when true. `duration_s` is labelled "span of member episodes".

**T23.25 Reference protection across stores** (Owner §5; finding 1).

(a) *Store registry.* Every V-02/T23 store is listed in a registry file at `out/review/registry.json`, git-ignored and JCS. A store that is not registered refuses to open.

(b) *Demo exclusion is global.* `create_batch` in any store excludes every recording of every demo run listed by any registered store (amends T22.6 (a), T23.11 (b)). A demo draw is refused if any recording of a drawn run has a target in a batch of any registered store.

(c) *Exposure is per person, across stores and all actions.* A person (by pseudonym) is exposed for a recording when any registered store holds any of the following:
1. a `candidate_review` assessment or adjudication on a target of that recording;
2. a workflow report-log entry by that person on a report whose members include that recording;
3. a `wf_displays` entry (first display of a report page) by that person for such a report;
4. an Owner role over a store whose demo manifest includes that recording. The Owner sees every report there.

T22.2 (b) applies to every exposed person, across stores. Exposure that no store records, such as reading per-run report rows, remains under the self-attestation of T22.2 (a). The attestation text is extended to name workflow pages and W-01 per-run tables.

(d) Annotator rows created for workflow managers carry `qualification_ref` starting "workflow ". They are refused at once for any `reference` assessment or adjudication, before T22.9 applies.

(e) *Existing batches.* Before any further reference sampling or annotation, the agent runs the checks of §6.3 and reports. No batch is redrawn and no quota or estimand is changed without an Owner decision.

**T23.26 Source-quality disclosure** (Owner §4).
- The demo manifest records the alert source's configuration and path, and copies its reported coverage and event figures with their report reference. For pilot column C these are CM-03 0.12, BL-6 EV-M1 0.11 and EV-M2 0.22 (`reports/M1b_pilot_report.md`).
- Every workflow page that shows AI alerts, the regulator view and W-01 print: "AI alerts in this demo come from <source>. On SDG validation that source covers 12 % of worker–forklift co-visible frames (CM-03); most interactions produce no alert. Workflow measures describe the workflow, not the system's accuracy."
- If the source has no recorded figure, the banner says "accuracy of the alert source: not reported".

**T23.27 Scope of forbidden fields and of the demo** (CR-030 item 10; Owner §4).

(a) VR-E-041 applies to:
- E2 tables and exports (E-1.2.1);
- RQ2 observation exports;
- every A-workstream table and artifact.

It does not apply to `wf_*` tables, which are B-workstream records.

(b) `wf_establishment` with `demo = false` is refused.

(c) 301-style fields, establishment IDs and the incidence rate exist only for demo establishments.

(d) The incidence rate is computed at view time from human-entered hours and is never stored. Monitored time is never used as hours worked.

(e) No page or export sorts, scores, ranks or compares establishments.

(f) Every workflow page and export carries "Simulated demo data. Descriptive workflow measure, not a validated safety-performance measure."

(g) These limits govern the present RQ1 work only. They do not rule out separately authorised work in workstream C.

---

### 4. Schemas, interfaces and compatibility (Owner §6)

#### 4.1 Changes
| Object | Change | Branch | Class |
|---|---|---|---|
| `adjudication` | `reference_class?` + `reference_class_null_reason`; VR-E-056 | `m0-implementation` and `v02-review-ui` | minor schema change |
| VR-E-056 | new rule (T23.16 b) | both | contract |
| `wf_report_log.action` | + `sm_confirm_duplicate`, `am_split`, `withdraw_recordability` | `v02-review-ui` only | workflow |
| report states | + `closed_split` | `v02-review-ui` | workflow |
| report fields | `duplicate_of?`, `split_from?`, `group_resolution?`, `camera_observability?` with `observability_cameras` list, recordability `reason?` | `v02-review-ui` | workflow |
| `demo_manifest` | `timebase_evidence_ref`, `source_quality` {config, path, CM-03, EV-M1, EV-M2, report_ref} | `v02-review-ui` | workflow |
| `out/review/registry.json` | new (T23.25) | `v02-review-ui` | tooling file, not a contract table |
| `reference_adjudications()` | single accessor (T23.16 e) | both | interface |

#### 4.2 Readers and writers
- **Old rows, new reader:** a missing null-reason column is read as null (T23.16 f). Every stored `reference` adjudication stays valid. Nothing is rewritten, so the hash chains of `validation_status_log` and `wf_report_log` are untouched.
- **New rows, old reader:** a `candidate_review` adjudication with a null class fails the old non-null check. The `v02-review-ui` code before this change must not open a store written after it. The store records its contract version, and an older reader refuses a newer store (VR-E-001 major/minor rule [U: confirm VR-E-001 handles a minor-ahead store; if not, a version guard in the store is needed]).
- **Status log:** `candidate_review` status entries were never written under CR-030's current behaviour [V], so no existing entry is affected.

#### 4.3 Artifact identity
- **What the code does [V]:** an artifact ID depends on the artifact spec ID and the payload digest only. Adjudication rows are `human` class and cannot be built into an artifact. `SCHEMA_VERSION` appears only in artifact metadata. The contract version has never been in an artifact ID (the constant has stayed "E-1.2.4" through E-1.2.21).
- **Consequence for this change [D]:** adding a nullable column to `adjudication` cannot change any S0–S8 artifact ID or payload hash, provided no artifact table gains a column. Section 6.2 tests this; it is not taken on trust.
- **Pinned contract against a version change:** reproducibility means the same contract, code and inputs give the same IDs (MR-01). An intended version change could change identity only through the payload, which this change does not touch. If a later change does alter an artifact table, its IDs change on purpose. That change must name the affected stages and re-run them; it is never presented as reproducibility.
- **Observation, outside D-49.1:** a `SCHEMA_VERSION` constant that never changes makes artifact metadata wrong about the contract that built it. The Architect recommends a separate engineering item: record the contract version in the execution record instead, and leave the ID rule unchanged. **No change in this merge.**

---

### 5. Indicator and flag specifications (Owner §3)

**Common to every row:**
- **Type:** a descriptive workflow measure about manager decisions or recorded reports, never a measure of CV accuracy or of true event rates.
- **Period and cutoff:** P is the ISO week of `occurred_at`, and the log is truncated at `as_of` (T23.18).
- **Shares:** every share prints n, its Wilson 95 % interval and "undecided: n".
- **Exclusions:** `closed_split` originals are excluded everywhere. Their parts are counted as reports.

| ID | Intended reading | Unit | Population | Numerator / denominator | Duplicates | Reopen / reclassify | Missing or zero | Must not be read as |
|---|---|---|---|---|---|---|---|---|
| I1 | AI alert volume | report | AI reports created in P | count; also "excluding closed_duplicate" | counted, with a duplicate count beside | no effect | 0 is a count | event or hazard frequency |
| I2 / I3 | area-manager approval / rejection of AI alerts | report | AI reports in P with an area-manager decision | am_approve (I2) or am_reject (I3) / (am_approve + am_reject). `am_duplicate` and `am_split` are excluded and counted beside | excluded from n | the area manager decides once per report; later SM actions do not change I2/I3 | n = 0: "no decided reports" | precision; a false-positive rate (I3 is not a verified false positive) |
| I4 | safety-manager overturn of rejections | report | AI reports in P whose latest SM decision is uphold or overturn | latest = overturn / latest ∈ {uphold, overturn} [CR-030 item 2 (a), (d)] | `sm_confirm_duplicate` and overturns of duplicates counted beside, outside n | latest decision per report counts | n = 0 → "none" | AI correctness |
| I5 | reclassification of recorded AI reports | report | AI reports in P ever `recorded` by `as_of` | reports with ≥ 1 `sm_reclassify` / that population | duplicates never recorded → outside | a report counts once however often it is reopened | n = 0 → "none" | error rate |
| I6 | reports waiting for a decision | report | reports in a pending state at `as_of` | count with age > t_pending_days since entering the current pending state; age since creation in a second column | included | reset on each new pending state | none | backlog of hazards |
| I7 | recorded near-miss reports, by origin | report | reports with current state `recorded` and kind `near_miss`, in P | AI and human counts separately. AI rate = AI count / monitored area-hours (T23.23 b). Columns: `group_resolution = cannot_tell` count, usable, processed and monitored hours, unprocessed cameras | only `recorded` counts | follows the current state | zero time → "not computable"; zero count → "0 … absence of alert ≠ absence of event" | true near-miss frequency; a site safety level; comparable across sites |
| I8 | human reports with no matching alert on an observable camera | report | recorded human-started near_miss and incident reports in P | counts in the five T23.23 (c) categories; I8 = category 5 | only `recorded` counts | follows the current state | category 3 is shown and never folded into 4 or 5 | detector recall or miss rate |
| I9 | definitive recordable cases and their rate | case (report) | T23.19 (f) definitive cases in P | count by criterion; rate = cases × 200,000 / hours worked entered for P; labelled provisional per T23.19 (f) | duplicates never `recorded` → outside | see T23.19 | no hours → "rate not computable: hours not entered" | a validated site safety measure; comparable across establishments |
| F1 | many rejections | flag | as I3 | n(I3) ≥ n_flag_min and Wilson lower bound(I3) > θ_rej | as I3 | as I3 | not evaluated if n is below the minimum ("insufficient n") | evidence of a bad detector |
| F2 | many overturns | flag | as I4 | n(I4) ≥ n_flag_min_sm and lower bound(I4) > θ_over | as I4 | as I4 | as F1 | evidence of bad area managers |
| F3 | stale reports | flag | as I6 | I6 > 0 | | | | |
| F4 | human reports without a matching alert | flag | as I8 | I8 ≥ k_miss | | | | AI misses established |

The flag text of T23.9 is unchanged. The linter refuses "false positive", "false negative", "precision", "recall", "accuracy" and "miss rate" on workflow pages, except inside the fixed T23.9 and T23.23 (d) texts.

---

### 6. Acceptance tests and regression evidence

#### 6.1 New fixtures (tests first; expected values hand-computed)
| ID | Setup | Expected |
|---|---|---|
| FX-14a/b | as T23 | now pass. The strict-xfail marks are removed by this ruling |
| FX-14j | write a `candidate_review` adjudication with reference_class `independent_expert_judgment` | refused, VR-E-056 |
| FX-14k | `reference` adjudication with a null class | refused, VR-E-056 |
| FX-14l | store holding 1 reference adjudication (agreement) and 3 `candidate_review` adjudications | EV-M12 and κ are computed on 1 target; `reference_adjudications()` returns 1 row; a T22 batch draw ignores the 3 |
| FX-14m | static test: an evaluation module that opens `adjudication.jsonl` directly | test fails |
| FX-14n | a workflow manager annotator row submits a reference assessment | refused (T23.25 d) |
| FX-14o | stores S1 (demo with run R) and S2 (main), both registered; `create_batch` in S2 | no target of R. Demo draw in S1 after a batch in S2 holding a target of R → refused |
| FX-14p | person P approves a demo report in S1 (member recording r). In S2, P submits a reference assessment on a target of r | refused (T22.2 b across stores). Also for a P with only a `wf_displays` entry, and for the Owner of S1 |
| FX-14q | simultaneous unrelated interactions: area cameras c1 and c2, episodes [10, 12] s and [10.5, 12.5] s, different pairs | one report with 2 members. am_approve without group_resolution → refused. am_split into {c1}, {c2} → original closed_split; 2 new pending reports; after both approved nm, I7 = 2 |
| FX-14r | multiple views: same as FX-14q, approve with one_interaction | one recorded report, I7 = 1 |
| FX-14s | touching: widened intervals [0, 3] and [3, 5] | one group (closed intervals) |
| FX-14t | unaligned: two cameras of one area, recording_local timelines, no demo evidence ref, overlapping local times | two reports, each saying "grouped per camera: no common clock" |
| FX-14u | duplicate: B marked duplicate of A; reopen B; sm_confirm_duplicate | B closed_duplicate, duplicate_of = A. I7 counts A only. Marking A a duplicate of B while B is closed_duplicate → refused. Overturning B after reopen sets duplicate_of to null; I7 = 2 |
| FX-14v | each refused action (sm_uphold without am_reject; sm_reclassify with recordability yes; am_split with one part) | no file changes (byte-compare the store), state unchanged |
| FX-14w | log of 20 entries; view at as_of = time of entry 12; then 8 more entries, including a reclassify of a report in P | the view at the same as_of is identical (head hash of entry 12); the later view shows "revised after first decision: 1" |
| FX-14x | recordable yes; sm_reclassify → refused; withdraw_recordability (classification_changed) then reclassify → closed_rejected | I9 = 0, withdrawn = 1, history keeps both entries. Then reopen and overturn: determination stays `withdrawn` until set again |
| FX-14y | 2 incidents in P: one yes (definitive), one not_set; hours 100,000 | I9 = 1, rate 2.0, labelled provisional |
| FX-14z | human report in an area: (i) no monitored camera → unmonitored; (ii) monitored, observability unset → undetermined; (iii) observable c1, AI member on c1 at +30 s → matched; (iv) observable c1, AI member only on c2 → category 5, I8 = 1 | as stated |
| FX-14aa | two cameras of one area, both monitored over the same 1 h | monitored area-hours 1.0, camera-hours 2.0, rate denominator 1.0. Two S5 artifacts of the source config on one camera window → ERR-SPEC |
| FX-14ab | members with clearances 1.2 m (full_camera) and 0.8 m (homography) | not combined; both listed. Same method → 0.8 m with its source episode, camera, σ status, q_state and artifact ID |
| FX-14ac | page with AI alerts from pilot column C | banner with CM-03 0.12 and the report reference. A `wf_establishment` with demo = false → refused. No page sorts establishments (static and rendered check) |
| FX-14ad | linter: "precision 0.8" on a workflow page | page refused; the same text in a user-entered block is accepted and escaped |

#### 6.2 Regression and compatibility evidence required before the scoped merge
1. Full suite twice on both branches, with identical results.
2. M0 determinism from a clean clone: the artifact-ID table equals `reports/M0_report.md` (commit e6072ef table).
3. The reconstruction check (`ids.artifact` read-back) passes on every stored M1a and pilot artifact under the new schema. Three SDG cameras have S0–S5 rebuilt, and their IDs equal the stored ones.
4. Every stored adjudication, assessment and status entry in every store under `out/review/` validates under the new reader without being rewritten, and every hash chain verifies.
5. FX-14j–FX-14p pass on `m0-implementation` where they need no workflow code (FX-14j–m); all of them pass on `v02-review-ui`.
6. A diff of the merge shows only Appendix T, CLAUDE.md, `tables.py` (adjudication), the VR-E-056 validator, the accessor, and tests. No `src/rq1/workflow/` file and no `wf_*` table.

#### 6.3 Reference-protection checks (before any further reference sampling or annotation)
1. List every store under `out/review/`, its batches and their manifests. Report whether any existing batch holds a target from a demo run, and whether any annotator in a batch is exposed under T23.25 (c).
2. Count the BL-6 episodes of the T22 frame (T-21 oracle run) left after excluding the 9 demo runs, per summary label. Compare each with T22.6's equal allocation for n_batch = 60 and with T22.14 (e).
3. Report only: no batch is redrawn, discarded or resized, and no quota is changed. If an existing batch is affected, or a stratum falls short of its share, STOP for an Owner decision.

---

Source: Owner decision D-49 (20 Nov 2026), the Architect's D-49.1 addendum approved by the Owner as proposed (Owner approval by pasting it), appended verbatim.

## T23.28 Readings of E-1.2.23 (E-1.2.24; D-51; CR-031)

T23.28 Readings of E-1.2.23 (CR-031, D-51). These amend T23.16 to T23.27; everything else stays as written.

 (a) *Split by the safety manager* (CR-031 item 1; amends T23.20 (e) and T23.21 (d)). The split action may also be
     taken by the safety_manager from pending_sm. Its effects are the same as `am_split` from pending_am:
     - the original goes to `closed_split`;
     - one new AI report per part is created in pending_am, carrying `split_from`;
     - no assessment, adjudication or status entry is written for the original; existing ones stay.

     The action is named `split` in the log, with `actor_role` area_manager or safety_manager. The T23.21 (d) sentence
     "A safety manager acting on such a report from `pending_sm` sends it back to the area manager with `sm_reopen`; the
     agent confirms this path in CR-031." is replaced by: "a safety manager who finds several interactions in a pending_sm
     report uses `split`". Closed_split originals stay excluded everywhere (section 5), so the original's area-manager
     decision leaves I2/I3. Each new part is a new report with its own decisions.

 (b) *group_resolution after reopening a duplicate* (CR-031 item 2; amends T23.20 (d)). `group_resolution` on an
     overturn after reopening a duplicate is required only when the report has two or more members, as in T23.21 (d).

 (c) *FX-14d and FX-14e setups* (CR-031 item 3; confirmed). They add inputs that E-1.2.23 requires and change no
     expected value.
     - FX-14d. Setup under E-1.2.23: the area manager's approval records `camera_observability = observable` for camera 1.
     - FX-14e. Setup under E-1.2.23: the approval gives `group_resolution = one_interaction`.

 (d) *Withdrawing a recordability determination* (CR-031 item 5; amends T23.19 (c)). "From: any state." is replaced
     by: "From any state in which a determination `yes`, `no` or `undetermined` is current." Withdrawing from
     `not_set` or `withdrawn` is refused.

 (e) *Namespace enum* (CR-031 item 6; amends T23.16 (b)). The first sentence and the [V] tag are replaced by: "across
     all namespaces: the two in use (`reference`, `candidate_review`) as stated; an adjudication in a reserved namespace
     is refused." The enum has four values; `study_d6` and `pseudo_label` are reserved. VR-E-056 refuses an adjudication
     in a reserved namespace.

 (f) *The T23.26 banner and the linter* (CR-031 item 7; amends section 5). The banner of T23.26 is a fixed text and is
     exempt from the linter. The last sentence of section 5 reads: "The linter refuses "false positive", "false
     negative", "precision", "recall", "accuracy" and "miss rate" on workflow pages, except inside the fixed T23.9,
     T23.23 (d) and T23.26 texts."

 (g) *prov_class of the combined value* (CR-031 item 8; T23.24 (b)).
     - `geometry_estimated` when the source episodes' positions come from the camera path (`full_camera` or homography);
     - `simulator_truth` when they come from simulator positions (the T-21 oracle source).

     This is a statement about the source path, so it is printed from the path recorded in the demo manifest. It is
     never stored as a measurement (T23.24 (d)).

 Tests: the safety manager's split from pending_sm (two members: `split` → original closed_split, two new pending_am
 reports, the original's am_reject no longer in I2/I3 n); the single-member overturn of a reopened duplicate without
 `group_resolution` (accepted); withdraw from `not_set` (refused); prov_class printed per source path. FX-14d and FX-14e
 unchanged.

Source: Owner decision D-51 (21 Nov 2026), rulings on CR-031 from the Architect's review of W-02 (commit 748bafc),
approved by the Owner (Owner approval by pasting it). Items 1, 2, 3, 5, 6, 7 and 8 of the rulings, worded as stated.

## T24. Camera-path footprint centre and floor-position resolution (E-1.2.25; CR-007, CR-026, D-54)

**T24.0 Switching.** Both rules are off unless their parameters are present. A configuration record with the parameters absent is identical to its E-1.2.24 form: same fields, same configuration ID. Every E-1.2.24 artifact reproduces unchanged.

**T24.1 Footprint centre from a camera-derived floor point.**
(a) *Scope.* An object whose floor point comes from the `full_camera` tier, and whose footprint prior has `anchor = box_bottom_centre` and both T24.1 parameters present.
- A prior with `anchor = centre` keeps the E-1.2.24 behaviour: the floor point is the footprint centre.
- `anchor = rear_axle` with a camera-derived floor point is ERR-SPEC.
- The homography tier is out of scope, because its calibration carries no camera position. Its floor point remains the centre, and reports state this.

(b) *Parameters* (footprint prior, optional): `anchor_offset_m` d ≥ 0 and `anchor_taper_m` r_taper > 0. Both are present or both are absent; one alone is ERR-SPEC.

(c) *Definition.* Let P_f be the floor point of the box bottom-centre after T24.2. Let C be the camera centre (−Rᵀt) projected on the floor, and r = ‖P_f − C‖.
- If P_f is null, the centre is null.
- If r < 1e-9 m, the centre is P_f.
- Otherwise u = (P_f − C)/r, d_eff = d · min(1, r/r_taper), and the footprint centre is P_c = P_f + d_eff · u.

(d) *Downstream.* P_c replaces the floor point wherever T8 uses the object's position: velocity, speed, heading, the footprint, clearance, prediction, TTC and PET. T8.2 yaw and the footprint shape rules are unchanged. `pos_cov_m2` is unchanged.

(e) *Uncertainty.* d is a constant, so P_c carries a residual that depends on the object's orientation relative to the camera. No σ is added. Reports state the residual measured on the tuning cameras.

(f) *Provenance.* The position stays `geometry_estimated`. The footprint prior's ID covers d and r_taper.

**T24.2 Floor-position resolution gate.**
(a) *Quantity.* For a camera-derived floor point g(p) from foot pixel p = (u, v), let J(p) be the 2 × 2 Jacobian of g with respect to (u, v), in metres per pixel, and s(p) its largest singular value.
- `full_camera`: g is the ray–floor intersection.
- Homography: g(p) = (h₁·p̃ / h₃·p̃, h₂·p̃ / h₃·p̃), with p̃ = (u, v, 1).

(b) *Parameter.* `s_max_m_per_px` (geometry_config, optional; one value per pre-registration, not per site). If it is absent, the gate is off.

(c) *Rule (gate on).* For every object-frame with a foot pixel:
- s(p) is stored as `floor_resolution_m_per_px`.
- If g(p) exists and s(p) > s_max: `x_m` and `y_m` are null with null reason `not_observable`. In each pair-frame with this object, `clearance_m` is null and `clearance_state = unmeasurable_geometry_failure`.
- If g(p) does not exist (the ray is at or above the horizon, or w ≤ 0): `floor_resolution_m_per_px` is null (`not_observable`), the position is null (`not_observable`), and `clearance_state = unmeasurable_geometry_failure`.
- With the gate off, the E-1.2.24 behaviour is kept, including `unmeasurable_occluded` for horizon rays.

(d) *Scope.* Every object class and every evidence class with a foot pixel.

(e) *Downstream.* Nothing in this section imputes a null position or carries it forward.
- T8.7 Q is unchanged: a position nulled by the gate does not change `q_state`.
- CM-08 counts the pair-frame as not measured.
- The D-41 availability table lists "resolution limit (s > s_max)" and "no floor intersection" as separate rows, read from `floor_resolution_m_per_px`.
- A pair-frame without a measured clearance is never read as "no event"; it is treated like any non-measured clearance under T10.1.

(f) *Reporting.* Every report that uses the gate states s_max, and the share of object-frames nulled by class, viewpoint and data origin. It calls gated positions *unresolved*, not *wrong*.

**T24.3 Order in S4.** Foot pixel → floor point g(p) → T24.2 → T24.1 → T8.

**T24.4 Tests.** Each of the following becomes a test.
- *T24.1 checks.* C = (0, 0); L = 3.03 m, W = 1.13 m; d = 1.04 m, r_taper = 2.0 m.
  - True centre (10, 0), body axis along the sight line: P_f = (8.485, 0), P_c = (9.525, 0).
  - True centre (10, 0), body axis across the sight line: P_f = (9.435, 0), P_c = (10.475, 0).
  - P_f = (6, 8): P_c = (6.624, 8.832).
  - P_f = (0.5, 0): P_c = (0.76, 0).
  - P_f = (0, 0): P_c = P_f.
  - P_f null: P_c null.
  - Parameters absent: P_c = P_f, and the prior ID is unchanged.
  - One parameter alone: ERR-SPEC. `rear_axle` on the camera path: ERR-SPEC.
- *T24.2 checks.* Pinhole camera at H = 3 m, horizontal optical axis, f = 1000 px, principal column. With the foot pixel Δv pixels below the horizon, s = max(H/Δv, fH/Δv²). With s_max = 0.1:
  - Δv = 100: s = 0.300, gated.
  - Δv = 200: s = 0.075, kept.
  - Δv = 300: s = 0.0333, kept.
  - Δv = √30000: s = 0.1000, kept (≤).
  - Δv = 0: no intersection.
  - Homography diag(a, a, 1): s = a. a = 0.02 is kept; a = 0.15 is gated.
  - H = [[0.02, 0, 0], [0, 0.02, 0], [0, 0.01, 1]] at p = (0, 100): floor point (0, 1.0), s = 0.01.
  - The analytic s agrees with a finite-difference s within 1e-5 on random cameras.
- *Regression.* With the T24 parameters absent, every M0 fixture and the stored M1a and pilot S4 artifacts reproduce byte-identical.

Source: Owner decision D-54 (23 Nov 2026), the Architect's draft part 1 (`v2_architect_package_part1_CR007_CR026_DRAFT.md`) as corrected after the Architect checked it against E-1.2.24 on 23 Nov 2026, approved by the Owner (Owner approval by pasting it). Text as stated.

## T25. Event continuity across track fragments and POW breaks; m_gap in seconds (E-1.2.26; D-58)

**T25.0 Switching.** Each rule below is off unless its parameter is present. A configuration with the parameters absent is identical to its E-1.2.25 form (same fields, same IDs), and every E-1.2.25 artifact reproduces unchanged.

**T25.1 Track stitching (S3, detector and other non-oracle track sources only).**
(a) *Parameters* (tracker package, optional): `stitch_max_gap_s` T_s > 0; `stitch_v_max_mps` per class (person, forklift); `stitch_r_gate_m` r_g ≥ 0; `stitch_img_gate` k_img > 0. Either all are present, or none is.
(b) *Candidates.* For two tracks A and B of the same class in the same camera timeline:
- let t_A be A's last point in state `tracked`, and t_B be B's first point in state `tracked`;
- (A, B) is a candidate iff 0 < t_B − t_A ≤ T_s, no point of A lies after t_A in state `tracked` or `predicted`, and no coverage segment of state not_recorded, gap_unobserved or unusable lies between t_A and t_B.

Tracks that overlap in time are never stitched.

(c) *Gate.*
- When both endpoint points have floor positions (after T24), the gate is ‖P_B − P_A‖ ≤ v_max(class)·(t_B − t_A) + r_g, with cost = ‖P_B − P_A‖ / (v_max·(t_B − t_A) + r_g).
- Otherwise the gate is image-based: centre distance ≤ k_img · max(diagonal of A's last box, diagonal of B's first box), with cost = distance / (k_img · max diagonal).

(d) *Assignment.* Candidates passing the gate are taken in ascending cost, then ascending t_B − t_A, then track IDs by JCS order. A link is accepted iff A has no accepted successor and B has no accepted predecessor. Accepted links form chains.

(e) *Output.* Each chain gets a stitched identity `stitch_id` (identity class, F.1 A1.2, from its member track IDs). Track points keep their original track IDs, and each point carries `stitch_id`. S4 forms pairs from stitched identities. Frames between members are gaps under T8.1 (the gap bridging rule is unchanged); no point is created or imputed.

(f) *Off for oracle tracks:* simulator identities are already continuous.

**T25.2 Episode continuity across POW breaks (S5).**
(a) *Parameter* (rule_configuration.lifecycle, optional): `join_across_pow` (bool). Absent or false: off.
(b) *Rule.* Episodes e₁ and e₂ of the same pair (stitched identities under T25.1, otherwise track identities) in the same camera timeline, in different POWs, with e₂ starting after e₁ ends, are joined iff:
- gap = start(e₂) − end(e₁) ≤ m_gap_s (T25.3), or m_gap frames × δ_nom when m_gap_s is absent;
- every frame of the gap is outside both episodes' POWs, or inside them with T ≠ 1 (the gap holds no other episode of the pair);
- no coverage segment of state not_recorded, gap_unobserved or unusable lies in the gap.

Joins chain (e₁–e₂–e₃ …).

(c) *Output.*
- Each chain is one candidate_event per scenario (single-camera: S_VIEW = S_LINK = S_POSS), whose members are the episodes, in time order (`join_sequence`).
- Episodes are unchanged.
- Event fields follow the existing candidate_event rules (labels recomputed with §6 over the members, never unioned).
- New candidate_event fields: `n_members` (i64) and `unobserved_gap_s` (f64, the summed gap time between members, which is never counted as exposure or as clearance-measured time).
- The join is recorded as an event_link between consecutive members (representation per the agent's AR; meaning: same camera, same pair, continuity across a POW break).

(d) *References.* T21 references are unaffected. They are already continuous over visibility.

**T25.3 m_gap in seconds.**
- `lifecycle.m_gap_s` (optional, > 0). When present, m_gap_frames for a POW = ⌊m_gap_s / δ_nom + 1e-9⌋, with δ_nom from S1.
- When absent, `m_gap_frames` applies as in E-1.2.25.
- The same rule applies to the T21 reference build.

**T25.4 Tests.** Each of the following becomes a test.
- *T25.1:* two forklift tracks 1.0 s apart, floor distance 2.0 m, v_max 3 m/s, r_g 1.0 m → stitched (cost 0.5).
- *T25.1:* the same tracks 3.0 m apart and 0.5 s apart → not stitched (gate 2.5 m).
- *T25.1:* two candidates for one B → the lower cost wins.
- *T25.1:* overlapping tracks → not stitched.
- *T25.1:* a coverage break between the tracks → not stitched.
- *T25.1:* no floor positions → the image gate applies, with a hand value.
- *T25.2:* two episodes of one pair in consecutive POWs, gap 0.6 s, m_gap_s 1.0 → one candidate_event, n_members 2, unobserved_gap_s 0.6.
- *T25.2:* gap 1.4 s → two events.
- *T25.2:* the gap contains a T = 1 frame of the pair → not joined.
- *T25.2:* a coverage break in the gap → not joined.
- *T25.3:* m_gap_s 1.0 at δ_nom 1/30 s → 30 frames; at 0.1 s → 10 frames.
- *Regression:* with the T25 parameters absent, the M0 IDs, and the stored D-54 and D-57 artifacts at m_gap 5, reproduce byte-identical.

Source: Owner decision D-58 (24 Nov 2026), on the D-57 diagnostics (`research/m1b/d57_report.md`), reviewed by the Architect on 24 Nov 2026 and approved by the Owner (Owner approval by pasting it). Text as stated.

## T26. Post-audit scope, closure and governance (D-67)

**Status:** Research Owner-approved prospective scope and governance addendum. E-1.2.26 remains the version for historical experiments and existing scientific definitions. CR-044 governs any future versioned amendment to definitions, schemas, metrics or acceptance criteria.

1. D-66 is terminal. The 48-run SDG final test and its source or derived inputs remain permanently sealed. The D-63 once-only authorization is spent. It grants no access for development, training, tuning or further evaluation, including with an earlier checkout or alternate entry point. Preserve the frozen records, historical outputs and published summaries. Existing dataset reservations require a formal amendment and explicit Owner approval before any reallocation.
2. Current development and experiments use synthetic data only. E1, E2 and independent construct review of candidate near-miss outputs remain in scope, with separately reported evidence. E2 measures physical geometry and occupancy. An E2 hazard taxonomy or candidate rule requires separate Owner approval. Claims must stay within tested synthetic conditions and exclude real-world measurement reliability, operational readiness and natural warehouse alert frequencies. Synthetic evidence cannot promote a fitness status that requires real-world validation. Physical validation remains future work.
3. Resolve integrity issues before affected experiments. Keep historical numerical definitions, criteria, deviations and results in the record. Changes to scientific definitions or criteria require independent justification, explicit Owner approval and preregistration before any new confirmatory population access. Initiating a final confirmatory run requires separate Owner authorization.
4. Claude Code is engineering and integration lead. Codex may contribute assigned implementation and independent review. Both environments remain required for applicable engineering verification. Apply the attribution, branch coordination and contribution register rules recorded in D-67. [Decision D-67](../../DECISIONS_NEEDED.md#d-67-2026-11-27--post-audit-measurement-phase-and-agent-governance)

### T26.1. Prototype inference and preservation of standards (D-69)

Ordinary E1 and E2 prototype inference consumes video and documented deployment-equivalent inputs. Simulator object truth, visibility, identity, label and oracle geometry inputs may be used for separately identified development and evaluation. Verify a clean video-based run with those inputs and oracle caches inaccessible. This execution clarification preserves the established measurement, acceptance, architecture and verification standards. In v2 report prose, EV-M7 names the existing combined false-and-duplicate candidate numerator per usable synthetic camera-hour. The metric definition and historical values retain their original version and meaning.
