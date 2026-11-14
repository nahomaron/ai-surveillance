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
