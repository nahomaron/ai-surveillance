# RQ1 Contract Reference — Frozen Release E-1.2.1

**Date:** 8 November 2026
**Status:** **FROZEN** for Package F implementation. Changes only through the change-control protocol (Package F §9).
**Consolidates:** Package E (E-1.0.0), E.1 (E-1.1.0), E.1 Final Errata (E-1.2.0) and the Pre-Implementation Contract Clarification (E-1.2.1). Measurement and evaluation rules from C.1, D and D.1 are restated wherever a contract depends on them.
**Use:** Implementation agents build from **this document only**. The earlier packages remain the design rationale. Where this document is silent, raise a change request; do not consult superseded text.
**Scope:** RQ1 instrument. No safety score, indicator formula, OSHA linkage or establishment ranking.

---

## 0. Consolidation notes

### 0.1 Clarifications made while merging (no new design)

| ID | Clarification | Why |
|---|---|---|
| CN-1 | Every interval uses one time field family: `timeline_id` plus `t_*_tl_s` (timeline seconds). This replaces the separate video-time and session-time pairs | The errata made the timeline the unit of alignment; on a `recording_local` timeline, timeline time equals video time |
| CN-2 | Time components of natural keys are integer microseconds (`*_us`, round half to even) | Floats in hashed keys are fragile |
| CN-3 | `clock_alignment.sigma_s` is non-null and ≥ 0. Records exist only for recordings on `aligned_session` timelines | The errata removed `assumed_zero`; the E.1 nullable rule is now moot |
| CN-4 | Decode statistics move from `recording` (S0) to a new `decode_summary` (S1) | Registration must not depend on decoding |
| CN-5 | The run manifest is the per-execution `execution.json`, plus an append-only run register | The errata moved execution data out of payloads |
| CN-6 | Records in the validation store produced by deterministic converters (simulator truth) use derived IDs; records entered by humans use UUIDv7 | Synthetic references are reproducible artifacts |
| CN-7 | Test and rule IDs keep their source IDs. Superseded ones are listed in §12.3 | Traceability to the reviews |
| CN-8 | Reports describe a test population as having "passed the available leakage screening", never as "leakage-free" | Review of the E.1 errata, §3 |
| CN-9 | `image_gap_norm` = signed box gap ÷ **person box height** (Package B M-02). Package E had used image height | Restores the approved measurement definition |
| CN-10 | Flag providers R1–R6 restated as per-frame providers (§6.0). R6 is the approved D.1 label rule run with R3, R4 and R5 enabled, not a separate flag column. Duration conditions ("for ≥ t") are enforced only by the lifecycle's *t_min* | Package B rules were never consolidated; C.1 made rules flag providers |

### 0.2 Superseded content (do not implement)

`assumed_zero` clock method; frame time in decode order; `dt_s`-based durations; median duration of the final frame; `not_recorded` segments tiled by frame index; mandatory K/R/t for ground-plane calibrations; E2 episodes and `e2_labels`; activity segments limited to usable footage; `video_id` derived from file hash as recording identity; `run_id`/`created_utc` inside data files; artifact identity from file hashes; event-count wording `bound`; the claim that original inclusion probabilities stay valid after test revision; unscoped `unsuitable`.

---

## 1. Conventions

### 1.1 Types

| Notation | Arrow type | Rule |
|---|---|---|
| `str` | utf8 | |
| `id` | utf8 | `^[a-z0-9]{2,4}_[a-z0-9]{26}$` (derived) or `^[a-z0-9]{2,4}_[0-9a-f-]{36}$` (UUIDv7) |
| `i32`, `i64` | int32, int64 | |
| `f64` | float64 | NaN and ±Inf are forbidden (VR-E-003) |
| `bool` | boolean | |
| `tri` | int8 | 0 false, 1 true, 2 unknown (Kleene). Never null |
| `enum{…}` | dictionary<int32, utf8> | Unknown value ⇒ `ERR-UNKNOWN-ENUM` |
| `list<T>`, `struct{…}`, `map<K,V>` | | |
| `ts` | timestamp[us, UTC] | Processing time; allowed only in `execution.json` and human-entry records |
| `?` | nullable | Requires sibling `<field>_null_reason` |

### 1.2 Units and suffixes

`_m`, `_s`, `_mps`, `_rad`, `_kg`, `_px`, `_m2`, `_us` (integer microseconds), `_frac` (0–1), `_ratio`. SI throughout.

### 1.3 Enumerations

| Enum | Values |
|---|---|
| `data_origin` | real_natural, real_staged, synthetic_rendered, synthetic_transferred |
| `prov_class` | human_observed, human_measured, human_judged, human_adjudicated, model_estimated, geometry_estimated, rule_derived, simulator_truth, dataset_supplied, externally_supplied |
| `null_reason` | not_applicable, not_observable, uncalibrated, upstream_failure, not_supplied, not_computed_by_config, withheld_privacy, pending_review, out_of_scope_rq1 |
| `sigma_status` | calibrated, inflated, uncalibrated_model, not_estimated |
| `timeline_kind` | aligned_session, recording_local |
| `coverage_state` | not_recorded, gap_unobserved, unusable, usable_degraded, usable |
| `ai_activity_state` | not_evaluated, observed_no_detection, objects_detected_no_pair, pair_detected |
| `ref_activity_state` | not_annotated, unobservable, reference_verified_absent, objects_present_no_interaction, interaction_present |
| `evidence_class` | detected, inferred, insufficient |
| `evidence_state` | visible, partially_visible, occluded_predicted, truncated, lost |
| `geometry_method` | none, image_only, ground_plane_homography, full_camera, multi_view, simulator_truth, reference_survey, reference_click |
| `calibration_tier` | full_camera, ground_plane_homography (no record = uncalibrated) |
| `contact_state` | none_observed, undetermined, suspected, not_assessable (major-versioned; no "observed contact" value) |
| `sample_type` | RES, ECS |
| `namespace` | reference, candidate_review, study_d6, pseudo_label (reserved; FM-X1 only) |
| `label_source` | simulator_truth, human_manual, human_corrected_from_model, model_only |
| `scenario` | S_VIEW, S_LINK, S_POSS |

### 1.4 Missing values

- A null value always carries a reason; a non-null value carries none (VR-E-002).
- No sentinel values (VR-E-003).
- Tri-state flags use `tri`.
- `not_evaluated`, `gap_unobserved`, `not_recorded` and `unusable` are never reported or exported as zero activity or zero exposure (VR-E-040, CD-03).

### 1.5 Canonical serialization

- Canonical JSON is **RFC 8785 (JCS)**, including JCS number serialization.
- Use a JCS implementation; general JSON encoders format floats differently (for example `1e-07` vs `1e-7`).
- Lists that the contract defines as sets are sorted by the canonical JSON of their elements.

---

## 2. Identity

### 2.1 Identity kinds

| Kind | Prefix | Definition |
|---|---|---|
| Source content | `src_` | `b32(SHA-256(file bytes))` |
| Recording instance | `rec_` | `id("rec", [src_id, session_id, camera_id, registration_label])` |
| Artifact specification | `asp_` | `b32(SHA-256(JCS(spec)))`, where `spec` = {stage, schema_bundle, code_commit, environment_digest, config_ids (sorted), input_artifact_ids (sorted), seeds} |
| Immutable artifact | `art_` | `b32(SHA-256(JCS([asp_id, payload_sha256])))` |
| Record | table prefix | `b32(SHA-256(JCS([table, art_id, natural_key])))` |
| Execution attempt | `run_` | UUIDv7 per execution |
| Human-entered record | table prefix | UUIDv7 |

`b32(d)` = lowercase RFC 4648 base32 of digest `d`, padding removed, first 26 characters. `id(prefix, x)` = `prefix + "_" + b32(SHA-256(JCS(x)))`.

### 2.2 Column classes

- **Payload columns** are hashed. They include each record's natural-key fields and every reference: references to **input** artifacts use the input record's ID; references within the **same** artifact use a `<table>_nk` column holding the referenced natural key.
- **Derived ID columns** are not hashed. They are the record's own ID and each resolved same-artifact reference (`<table>_id`, computed from `<table>_nk`).

### 2.3 Construction sequence

1. Compute `asp_` from the spec.
2. Execute; emit rows with payload columns only.
3. Check integrity: natural keys are unique per table (`ERR-NATURAL-KEY`), and every `<table>_nk` matches exactly one row of that table in this payload (`ERR-FK`).
4. Compute `payload_sha256`. Tables go in name order; within a table, rows are sorted by `JCS(natural_key)`; the hash is SHA-256 over the stream of lines `table + "\t" + JCS(row_payload_columns) + "\n"`.
5. Compute `art_` from `asp_` and `payload_sha256`.
6. Derive record IDs and same-artifact reference IDs (§2.1).
7. Serialize files and compute integrity-only `file_sha256`. Write `manifest.json` with `complete: true` **last**, and write `execution.json` separately.

**Reconstruction check:** drop the derived columns from the stored files, repeat steps 3–4, and require the result to equal the stored `payload_sha256` (CT-FK-05).

**Reference value (worked example, CT-FK fixtures):** spec ID literal `asp_s3example0000000000000`, with the seven-row track and track-point payload of the clarification §1.3, gives `payload_sha256 = 2b38d32502f58662b39c32bd796a2d24e4dfc3ecd87140f1dcc9ff9568fff068`, `art_pmpcesnhpbbgtw2f3fhb6zkqxk` and track 1 ID `trk_zr3hb5b6y2jjuw7ab7aml6ymtf`. Implementations must reproduce these values.

### 2.4 Natural keys and references

| Table | Prefix | Store / stage | Natural key | Same-artifact references (`_nk`) | Input references (IDs) |
|---|---|---|---|---|---|
| dataset_source | dsr | Obs / S0 | (name, version) | | license_component_id |
| license_component | lic | Gov / S0 | (component, version) | | |
| site | sit | Obs / S0 | (dataset_nk, site_label) | dataset_nk | |
| session | ses | Obs / S0 | (site_nk, session_label) | site_nk | |
| camera | cam | Obs / S0 | (site_nk, camera_label) | site_nk | |
| source_file | src | Obs / S0 | (sha256) | | |
| recording | rec | Obs / S0 | (src_nk, session_nk, camera_nk, registration_label) | src_nk, session_nk, camera_nk | |
| timeline | tl | Obs / S0 | (kind, anchor_nk) — anchor = session (aligned) or recording (local) | anchor_nk | |
| clock_alignment | clk | Obs / S0 | (recording_nk, method, version) | recording_nk, timeline_nk | |
| camera_group | cgp | Obs / S0 | (timeline_nk, sorted camera_nks) | | |
| world_frame | wf | Obs / S0 | (site_nk, label, version) | | |
| calibration | cal | Obs / S0 | (camera_nk, tier, method, valid_from_us, version) | camera_nk, world_frame_nk | |
| context_map | ctx | Obs / S0 | (site_nk, version) | | |
| decode_summary | dsm | Obs / S1 | (recording_id) | | recording_id |
| frame | — (no ID; keyed) | Obs / S1 | (recording_id, decode_seq) | | recording_id |
| coverage_segment | cov | Obs / S1 | (timeline_id, camera_id, t_start_us) | | timeline_id, camera_id, recording_id |
| detection | det | Obs / S2 | (recording_id, frame_index, det_index) | | recording_id |
| track | trk | Obs / S3 | (recording_id, track_local_id) | | recording_id |
| track_point | tpt | Obs / S3 | (track_nk, frame_index) | track_nk | detection_id |
| object_state | ost | Obs / S4 | (track_id, frame_index) | | track_id, calibration_id |
| pow | pow | Obs / S4 | (person_track_id, forklift_track_id, start_frame) | continuation_of_nk | track IDs |
| pair_series | psr | Obs / S4 | (pow_nk, frame_index) | pow_nk | |
| exposure_profile | exp | Obs / S4 | (subject_type, subject_nk, band_scheme_id) | subject_nk | band_scheme_id |
| activity_segment | act | Obs / S4 | (timeline_id, camera_id, t_start_us) | | coverage_segment_id |
| gpw | gpw | Obs / S4 (M2) | (sorted member pow_nks) | member pow_nks | |
| flag_series | — (keyed) | Obs / S5 | (pow_id, frame_index) | | pow_id |
| episode | ep | Obs / S5 | (pow_id, start_frame) | continuation_of_nk | pow_id |
| discarded_episode | dep | Obs / S5 | (pow_id, start_frame) | | pow_id |
| event_link | lnk | Obs / S5 | (episode_a_nk, episode_b_nk) | both | |
| candidate_event | evt | Obs / S5 | (scenario, sorted member_episode_nks) | members | |
| event_count_summary | ecs | Obs / S5 | (scope_type, scope_id, scenario, label) | | |
| load_state | lds | Obs / S4-E2 | (track_id, frame_index, method) | | track_id |
| e2_occupancy_series | e2s | Obs / S4-E2 | (person_track_id, load_track_id, frame_index, method) | | |
| e2_occupancy_profile | e2p | Obs / S4-E2 | (person_track_id, load_track_id, method) | | |
| sampling_plan | spl | Val / V0 | (plan_label, version) | | split_version_id |
| reference_window | rwn | Val / V0 | (plan_nk, camera_group_id, window_index) | plan_nk | |
| simulator-truth reference records (E-38–E-41) | as table | Val / CV-SIM | (window_id, table-specific key) | | window_id |
| split_manifest | spm | Eval / X0b | (split_label, version) | | |
| leakage_audit | lka | Eval / X0c | (split_version_id, audit_seq) | | |
| match_record | mat | Eval / S8 | (window_id, ref_event_id, system_event_id) | | |
| error_attribution | era | Eval / S8 | (match_nk) | match_nk | oracle artifact IDs |
| completeness_record | cmr | Eval / S8 | (window_id, metric_id, stratum) | | |
| metric_result | mtr | Eval / S8 | (metric_id, slice, config_id, scenario, label) | | |
| acceptance_criterion | acc | Eval / pre-reg | (criterion_label, version) | | |
| measurement_fitness | fit | Eval / S8f | (scope key, §9.6) | | metric_result IDs |

### 2.5 Files

- **Parquet key-value metadata:** `schema_id`, `schema_version`, `artifact_id`, `data_origin`, `payload_sha256`. Nothing execution-specific.
- **`manifest.json`:** `artifact_spec_id`, `spec`, `payload_sha256`, `artifact_id`, `files` [{path, file_sha256, rows}], `data_origin`, `reproducibility_class` ∈ {exact, tolerance}, `complete`.
- **`execution.json`:** `run_id`, `artifact_spec_id`, `artifact_id?` (null `upstream_failure` if the run failed), `stage`, `started_utc`, `ended_utc`, `host`, `platform` {cpu, gpu?, driver?}, `status` ∈ {complete, failed}, `compared_to_artifact_id?`, `tolerance_report_ref?`, `logs_ref`.
- **Run register** (Governance): append-only JSONL of execution records.

### 2.6 Reproducibility classes

| Stage | Class | Same spec ⇒ |
|---|---|---|
| S0, S1, S3, S4, S5, S6, V0, X0, S8, S8f, S9, CV-SIM | exact | Same `art_` and all record IDs (S1 for the same decoder build; S4 on the same platform) |
| S2 detection, detector fine-tuning | tolerance | Possibly a new `art_`; a comparison report links the artifacts (box IoU ≥ *iou_rep*, score Δ ≤ *s_rep*, flips listed) |

---

## 3. Time

### 3.1 Timelines

| Kind | Requirement | Gaps | Cross-recording relations |
|---|---|---|---|
| `aligned_session` | Every member recording has a `clock_alignment` with method ∈ {hardware_sync, dataset_supplied_sync, shared_visual_event, contiguous_file_sequence}, non-null σ and an `evidence_ref`; the session extent is declared from metadata | `not_recorded` allowed inside the declared extent (TI-11) | Allowed (camera groups, shared windows, linkage) |
| `recording_local` | Default | None; the extent equals the recording's support extent | None; any linkage edge is `U` (TI-12) |

Timeline time: `t_tl = t_video × (1 + drift_ppm·10⁻⁶) + offset_s` on aligned timelines; `t_tl = t_video` on local timelines.

### 3.2 Timestamp resolution and eligibility (S1)

1. Decode every frame; assign `decode_seq` in decoder output order.
2. Resolve the timestamp in priority order: PTS → container best-effort → DTS-derived (ST-3):
   - DTS-derived is accepted only if `reorder_depth = 0`.
   - Best-effort is accepted if it equals the PTS, or if `reorder_depth = 0` and it is consistent with its PTS-timed neighbours.
   - Otherwise the frame is **untimed**.
   - `reorder_depth` = max |presentation index − decode index| over PTS-timed frames.
3. Mark duplicates: for equal `t_resolved_s`, the lowest `decode_seq` is kept.
4. A frame is `eligible` iff it is timed **and** `decode_ok` **and** not a duplicate **and** has no exclusion quality flag (rules version).
5. `frame_index` = presentation index over eligible frames, ordered by (`t_resolved_s`, `decode_seq`); null otherwise.
6. Reject the video (`ERR-TIMESTAMPS`) if the untimed fraction exceeds *f_untimed*.

### 3.3 Observation support (ST-1, ST-2)

- **Support is assigned over every timed frame**, eligible or not:
  - `S_k = [t_k, t_k + s_k)`, where `s_k = Δ_k` (to the next timed frame) if `Δ_k ≤ δ_max = k_sup · δ_nom`.
  - Otherwise `s_k = δ_nom` (`capped`), and the remainder becomes a `gap_unobserved` segment.
  - The last timed frame gets `δ_nom` (`final_assumed`); the sensitivity variant uses 0.
- **Excluded timed frames** keep their own support (`excluded_own_support`), which becomes `unusable` coverage (`excluded_frame`). Neighbours never absorb it.
- **Untimed frames:** for each untimed frame *u*, `U_u = [min t, max t)` over the timed frames within ±*r* decode positions (*r* = max(1, reorder_depth)). All support inside `U_u` becomes `timing_uncertain`: evidence class `insufficient`, coverage `unusable` (`untimed_frame`).
- **Duplicates** get support 0.

### 3.4 Durations, clipping and evidence classes (ST-4–ST-6)

- Every duration over `[a, b)` = Σ |S_k ∩ [a, b)| over **eligible** frames of the relevant evidence class (clipping, TI-09/10).
- Interval extents (`span_s`, `t_start_tl_s`, `t_end_tl_s`) describe extent only.
- An object-frame is `detected` if `state = tracked` with a detection. It is `inferred` if `state = predicted` on an **eligible** frame (bridged gap or prediction). It is `insufficient` if `state = lost`, the frame is ineligible, or its support is `timing_uncertain`.
- A pair-frame is `detected` if both objects are detected; `insufficient` if either is insufficient; `inferred` otherwise.
- Detected and inferred time never include `unusable`, `timing_uncertain`, `gap_unobserved` or `not_recorded` support.
- The **primary exposure quantity** is detected support. Detected + inferred is reported as a labelled secondary quantity.
- Reference annotation uses the same frame eligibility and support: keyframes are allowed only on eligible frames (ST-5).

### 3.5 Coverage and activity

- Coverage segments tile each (timeline, camera) extent exactly once (TI-01). They are computed **without detector output** (D1-AC-03).
- Activity segments tile the same extent:
  - `not_evaluated` exactly where coverage ∈ {not_recorded, gap_unobserved, unusable}.
  - Otherwise one of the three detection states (CD-01–03).

### 3.6 Intervals

All intervals are half-open. A frame interval `[f_start, f_end_excl)` has the time extent `[t(f_start), t(f_last) + s_last)`, where `f_last` is the last eligible frame in the interval.

---

## 4. Space

### 4.1 Coordinate frames

| Code | Definition |
|---|---|
| CF-IMG | Native decoded image. Origin at the top-left **corner**; x right, y down; pixel centre at (i+0.5, j+0.5); boxes `[x1, y1, x2, y2]` with x1 < x2, y1 < y2. Model adapters map their outputs back to CF-IMG |
| CF-IMG-U | Undistorted image coordinates, same convention |
| CF-CAM | OpenCV camera frame, metres |
| CF-W(site) | Right-handed, metres, z up, floor z = 0; yaw on (−π, π], counter-clockwise from +x |
| CF-DS(dataset) | Native dataset frame, registered to CF-W by `transform_from_dataset` with `unit_status` |

### 4.2 Calibration tiers and permitted computations

| Computation | full_camera | ground_plane_homography | uncalibrated |
|---|---|---|---|
| Floor position of a ground-contact point; clearance; speed; heading | ✓ | ✓ | ✗ (image-space baseline only) |
| Cross-camera linkage in one world frame | ✓ (aligned timeline) | ✓ (aligned timeline) | ✗ |
| Elevated-object height (E2) | Only with a height reference or multi-view | ✗ | ✗ |
| Projected elevated-load footprint (E2-L4) | Only with a height reference | ✗ | ✗ |
| Reprojection of 3D boxes (GV-02) | ✓ | ✗ | ✗ |

---

## 5. Schemas

Each table lists fields as **field · type · semantics**. Fields marked `?` are nullable and need a reason (§1.4). Fields from §2.2 (derived IDs) are implied: every table has its own `<prefix>_id`.

### 5.1 Registration (S0)

**dataset_source:** name, version · str; data_origin; source_url · str; retrieved_utc · ts; license_component_id; annotation_levels · list<enum{objects, tracks, world_geometry, zones, events, none}> (as verified); unit_status · enum{verified, assumed, unknown}; notes_ref? · str.

**license_component (Gov):** component, version · str; component_type · enum{dataset, model_code, model_weights, library, tool}; license_label · str; terms_location · enum{license_file, card_only, website, written_agreement, unknown}; obligations · list<str> (empty only if verified); license_status · enum{verified, card_only_unverified, open_question, not_read}; verified_utc? · ts; decision_ref? · str.

**site:** dataset_nk; site_label · str (pseudonymous); data_origin; site_kind · enum{synthetic_scene, staged_facility, operational_facility}; independent_of_development · bool; approvals_ref? · str (required for real origins, VR-E-070). **No establishment, employer, NAICS or OSHA identifier field.**

**session:** site_nk; session_label · str; scripted · bool; scenario_ref? · str; **lineage** · struct{ext_run_id?, scene_id?, render_parent?, seed?, generation_batch?, actor_roster_ref?, layout_id?, script_id?, collection_day?}. These are the R-1 leakage-screening fields; record every one known.

**camera:** site_nk; camera_label · str; mount_height_m? · f64 (externally_supplied); viewpoint_class · enum{ceiling, high_oblique, eye_level, other}; fov_polygon_w? · list<[f64, f64]>; declared_overlap_camera_nks · list.

**source_file:** sha256 · str; size_bytes · i64; container, codec · str; uri · str (access-controlled); privacy_state · enum{synthetic_no_persons, contains_identifiable_persons, redacted_derivative}; retention_policy_id.

**recording:** src_nk, session_nk, camera_nk; registration_label · str; timeline_nk.

**timeline:** kind · timeline_kind; anchor_nk; extent_start_tl_s?, extent_end_tl_s? · f64 (required for aligned, from metadata; null `not_applicable` for local, whose extent comes from `decode_summary`); extent_source · enum{session_metadata, recording_extent}.

**clock_alignment:** recording_nk, timeline_nk; method · enum{hardware_sync, dataset_supplied_sync, shared_visual_event, contiguous_file_sequence}; offset_s, drift_ppm · f64; sigma_s · f64 ≥ 0; evidence_ref · str; prov_class.

**camera_group:** timeline_nk; camera_nks (sorted); grouping_basis · enum{declared_overlap, calibrated_overlap, whole_session}.

**world_frame:** site_nk; label, version · str; origin_description · str; transform_from_dataset? · list<f64>[16] (row-major, CF-DS → CF-W); unit_status; prov_class.

**calibration:**

| Field | Type | full_camera | ground_plane_homography |
|---|---|---|---|
| camera_nk, world_frame_nk | | req | req |
| calibration_tier | enum | req | req |
| method | enum{dataset_supplied, checkerboard_plus_survey, survey_points_pnp, survey_points_pnp_ground_only} | req | req |
| valid_from_us, valid_to_us? | i64 (timeline µs) | req / opt | req / opt |
| intrinsics_K | list<f64>[9] | req | null `not_applicable` |
| R_cam_from_world | list<f64>[9] | req | null `not_applicable` |
| t_cam_from_world_m | list<f64>[3] | req | null `not_applicable` |
| distortion_model | enum{none, opencv_radtan5, opencv_fisheye4} | req | opt (null `not_supplied`) |
| distortion_coeffs | list<f64> | req | opt |
| homography_assumes_undistorted | bool | false | true if no distortion model |
| homography_img_to_floor | list<f64>[9] | opt | req, invertible (CB-02) |
| reproj_error_px_rmse | f64? | opt (`not_supplied`) | null `not_applicable` |
| heldout_ground_error_m_rmse | f64? | `not_computed_by_config` until GV-02 | same |
| quality_state | enum{validated_gv02, supplied_unvalidated, failed} | req | req |
| height_reference_ids | list | may be non-empty | must be empty for E2 height use |

**context_map:** site_nk; version; zones · list<struct{zone_id, label, polygon_w}>; height_references · list<struct{height_ref_id, label, kind enum{rack_beam, marker_pole, surveyed_point}, position_w, height_m, sigma_m}>; prov_class = externally_supplied.

### 5.2 Configuration records (JSON, content-addressed)

**footprint_prior:** class; label; shape · enum{disc, oriented_rect}; radius_m?, length_m?, width_m?; anchor · enum{box_bottom_centre, rear_axle, centre}; source · str; sigma_length_m, sigma_width_m.

**substrate_config:** *g_max* (frames); pair classes (forklift, optionally pallet_truck); *v_min*; *k_sup* (consumed by S1 via the decode config); `motion_models`.

**clearance_band_scheme:** edges_m (strictly increasing); bands · list<struct{lower_m?, upper_m?}>.

**rule_configuration:** experiment = E1; providers · list<struct{provider_id enum{R1…R6}, enabled, params map<str, f64>}>; lifecycle {m_gap_frames, t_min_s, w_post_s}; classification {d_nm_m, k_sigma, k_c, o_max_frac}; motion_models; substrate_config_id; band_scheme_id; preregistration_ref? (`not_applicable` if exploratory).

Parameter **values** exist only in configuration records.

### 5.3 Decode and coverage (S1)

**decode_summary:** recording_id; decoder_build · str; width_px, height_px · i32; time_base_num, time_base_den · i64; n_frames_decoded, n_frames_timed, n_frames_eligible · i64; reorder_depth · i32; vfr_detected · bool; delta_nom_s · f64; substituted_support_frac, untimed_frac · f64; extent_start_tl_s, extent_end_tl_s · f64; rejected · bool.

**frame:** recording_id; decode_seq · i64; frame_index? · i64 (eligible only); pts? · i64; ts_source · enum{pts, best_effort, dts_derived, none}; ts_status · enum{ok, duplicate, reordered, substituted, untimed}; t_resolved_s? · f64 (video time); t_tl_s? · f64; decode_ok · bool; quality_flags · list<enum{frozen, black, overexposed, blurred, compression_damage, decode_error}>; eligible · bool; support_start_tl_s? · f64; support_s · f64 ≥ 0; support_status · enum{measured, capped, final_assumed, substituted, excluded_own_support, timing_uncertain, zero_duplicate, zero_untimed}.

**coverage_segment:** timeline_id, camera_id; recording_id? (`not_applicable` for not_recorded); t_start_tl_s, t_end_tl_s · f64; start_frame?, end_frame_excl? · i64; coverage_state; support_s · f64 (0 for not_recorded / gap_unobserved); unusable_reasons · list<enum{quality flags…, excluded_frame, untimed_frame, timing_substituted}>; rules_version · str.

### 5.4 Perception (S2, S3)

**detection:** recording_id; frame_index; det_index · i32 (order by class, −score, x1, y1); class · enum{person, forklift, pallet_truck, load, rack, fork, other}; bbox_xyxy_px · list<f64>[4]; truncated · bool; score · f64 in [0, 1] (not a probability); score_calibrated? (`not_computed_by_config`); model_component_id.

**track:** recording_id; track_local_id · i64; class; start_frame, end_frame_excl · i64; span_s; t_detected_s, t_inferred_s, t_insufficient_s · f64 (sum ≤ span, EC-01); n_gaps, max_gap_frames · i32; id_switch_suspect · bool.

**track_point:** track_nk; frame_index; detection_id? (`not_observable` when predicted); bbox_xyxy_px; state · enum{tracked, predicted, lost}; foot_point_px · list<f64>[2]; evidence_class.

### 5.5 Spatial and substrate (S4)

**object_state:** track_id; frame_index; geometry_method; calibration_id?, world_frame_id? (`uncalibrated`); x_m?, y_m? (CF-W); pos_cov_m2? · [σxx, σxy, σyy]; sigma_status; yaw_rad?, yaw_sigma_rad? (forklifts; persons `not_applicable`); footprint_prior_id; speed_mps?, speed_sigma_mps?, heading_rad?; smoothing_window_s; evidence_state; evidence_class; visibility_frac? (`not_computed_by_config`).

**pow:** person_track_id, forklift_track_id; start_frame, end_frame_excl; recording_id, timeline_id, camera_id; t_start_tl_s, t_end_tl_s, span_s; t_detected_s, t_inferred_s, t_insufficient_s; bridged_gaps · list<struct{start_frame, end_frame_excl}> (eligible frames only); end_reason · enum{track_end_person, track_end_forklift, gap_exceeded, id_switch, coverage_gap, recording_end}; continuation_of_nk?. A POW never spans a frame-less gap (TI-08).

**pair_series:** pow_nk; frame_index; clearance_m? (signed footprint distance; ≤ 0 means overlap); clearance_sigma_m?; sigma_status; clearance_state · enum{measured, unmeasurable_uncalibrated, unmeasurable_occluded, unmeasurable_geometry_failure}; footprint_overlap · tri; image_gap_px · f64 (signed; **not a distance**); image_gap_norm · f64 (÷ person box height, CN-9); closing_rate_mps?; ttca_s?; predicted · list<struct{motion_model_id, horizon_s, pred_min_clearance_m, sigma_m, t_at_min_s}>; q_state · enum{sufficient, insufficient}; q_reasons · list<enum{person_occluded, forklift_occluded, truncated, low_quality_frame, predicted_only, timing_uncertain}>; evidence_class.

**exposure_profile** (one per POW and band scheme, whether or not episodes exist):

| Field | Rule |
|---|---|
| subject_type · enum{pow, gpw}; subject_nk; band_scheme_id | |
| t_total_support_s | Support over the subject's frames |
| t_in_band_detected_s, t_in_band_inferred_s · list<f64> | Measured-clearance support per band |
| t_clearance_unknown_s | Detected or inferred support with unmeasurable clearance |
| t_insufficient_s | Insufficient support |
| **Sum** | Σ detected + Σ inferred + unknown + insufficient = total (EC-02) |
| t_moving_detected_s, t_moving_inferred_s, t_stationary_detected_s, t_stationary_inferred_s, t_motion_unknown_s | With t_insufficient_s, sum to total; motion uses *v_min* |
| t_joint_visible_s | Both objects visible or partially visible (detected class) |
| sigma_status; calibration_tier · enum{calibrated_validated, calibrated_unvalidated, uncalibrated} | Comparability keys |

**activity_segment:** timeline_id, camera_id; t_start_tl_s, t_end_tl_s; coverage_segment_id; coverage_state (copied); ai_activity_state; support_s; perception_artifact_id? (`not_applicable` when not_evaluated).

**gpw (M2):** member_pow_nks; timeline_id; t_start_tl_s, t_end_tl_s; link_median_mahalanobis; n_overlap_frames; calibration_ids; clock_alignment_ids; link_method_version.

### 5.6 Events (S5; E1 only)

**flag_series:** pow_id; frame_index; P, M, X, E, G, Q, C_any, T · tri; C_by_provider · map<enum{R3, R4, R5}, tri>. `T = P ∨ X ∨ C_any` in Kleene logic; episodes open only on `T = 1`.

**episode:**

| Group | Fields |
|---|---|
| Keys and context | pow_id, start_frame, end_frame_excl, attr_end_frame_excl; experiment = E1; classification_contract = E1_v1; recording_id, camera_id, timeline_id; continuation_of_nk? |
| Time | t_start_tl_s, t_end_tl_s, span_s; duration_detected_s, duration_inferred_s, duration_insufficient_s; support_detected_frac |
| Flags | P_ep, X_ep, C_ep · bool; C_ep_by_provider · map; E_ep · tri; K · tri |
| Clearance | minclr_m?, minclr_sigma_m?, minclr_frame?; closest_approach_frame? |
| Contact | contact_state |
| Labels | lbl_O, lbl_H, lbl_PC, lbl_NM, lbl_UD, lbl_CT, lbl_IE · bool; summary_label · enum{CT, UD, NM, PC, H, O}; review_route · bool; borderline_flags · list<enum{clearance_within_k_sigma, speed_near_v_min, onset_sensitive}>; label_stability_frac? |
| Exposure (always populated) | exp_t_in_band_detected_s, exp_t_in_band_inferred_s · list; exp_t_clearance_unknown_s; exp_speed_at_ca_mps?, exp_closing_rate_max_mps?, exp_ttca_min_s?, exp_evasive_score?; exp_visible_frac |

**discarded_episode:** pow_id, start_frame, end_frame_excl, span_s, discard_reason · enum{shorter_than_t_min}.

**event_link (M2):** episode_a_nk, episode_b_nk (a < b by JCS); edge · enum{L, P, D, U}; time_offset_s?, clock_sigma_s?, median_mahalanobis?; n_overlap_frames; basis · list<enum{calibrated_geometry, declared_fov_overlap, same_camera, fov_disjoint, time_disjoint, metadata_missing, different_timeline}>; link_conflict · bool; linkage_version.

**candidate_event:** scenario; member_episode_nks; t_onset_tl_s?, t_end_tl_s?; P_ev, X_ev, C_ev · bool; E_ev, K_ev · tri; minclr_ev_m?; contact_state_ev; lbl_* (recomputed with §6 rules, never unioned); summary_label; review_route; grouping_algorithm_version; join_sequence · list; edges_used · list<struct{a_nk, b_nk, edge}>; alternative_groups · map<member_nk, list<group_nk>>; ambiguous · bool; unresolved_members · list. In single-camera milestones every scenario contains one-member events.

**event_count_summary:** scope_type · enum{reference_window, recording, timeline, split_partition}; scope_id; scenario; label (enum or `all`); n_events, n_ambiguous_groups, n_unresolved_identity_episodes · i64; assumptions · list<struct{assumption enum{A1, A2, A3}, status enum{unverified, sample_supported}, evidence_ref?}>; wording = `scenario_count` (the only value).

### 5.7 E2 measurement (conditional; no episodes)

**load_state:** track_id (class load); frame_index; method · enum{image_heuristic, height_reference_plane, simulator_truth, reference_measured}; calibration_id?; elevation_state · enum{on_floor, carried_low, elevated, in_rack, unknown}; height_m?, height_sigma_m? (non-null only under CB-03); height_reference_id?; carrier_forklift_track_id?; load_mass_kg? with load_mass_prov = externally_supplied and load_mass_sigma_kg; evidence_class.

**e2_occupancy_series:** person_track_id, load_track_id, frame_index, method · enum{image_overlap_baseline, projected_footprint} (projected requires CB-03); occupancy · tri; region_polygon_w?; margin_m?; person_position_sigma_m?; q_state; evidence_class.

**e2_occupancy_profile:** person_track_id, load_track_id, method; t_coobserved_s; t_occupied_detected_s, t_occupied_inferred_s, t_not_occupied_s, t_occupancy_unknown_s (sum = t_coobserved_s, CC-03 of E.1).

**Forbidden in all E2 tables and exports:** potential energy, fall probability, impact energy, falling-object trajectory, severity, risk score (VR-E-041).

### 5.8 Validation store

| Table | Fields |
|---|---|
| **sampling_plan** | plan_label, version; sample_type; split_version_id; population_definition_ref; supersedes_plan_id?; frame_definition {camera_group_ids, w_ref_s, w_guard_s, tiling_origin_tl_s}; frame_sha256; strata · list<{stratum_id, definition, N_h, n_h}>; stratifier_inputs (pre-system metadata or declared detector-independent proxy only); seed; frozen_utc; ecs_selection_basis? (required iff ECS) |
| **reference_window** | plan_nk; camera_group_id; timeline_id; window_index; t_start_tl_s, t_end_tl_s, t_guard_end_tl_s; stratum_id; sample_type; inclusion_prob?, weight? (null iff ECS); exhaustive · bool; annotation_status · enum{planned, in_progress, double_annotated, adjudicated, locked}; locked_utc?, lock_sha256?; split_version_id, partition_at_sampling, leakage_group_id |
| **annotator** | UUIDv7; role · enum{a_layer, b_layer, c_layer_reviewer, adjudicator, study_participant}; qualification_ref; independence_attestation · bool; pseudonym only |
| **annotation_record** | UUIDv7; annotator_id; window_id; layer · enum{A, B}; namespace; label_source; teacher_model_id?, teacher_version?, prompt?, thresholds? (FM-X1 only); target_kind · enum{object_presence, interaction, geometry, coverage}; payload; tool; submitted_utc; blind_to_system · bool |
| **ref_object_presence** | window_id; camera_id; class; physical_identity_id; presence_intervals · list<{start_frame, end_frame_excl}>; keyframes · list<{frame_index, bbox_xyxy_px, evidence_state}> (eligible frames only); keyframe_interval_s; consensus_method · enum{agreement, third_annotator, adjudicated, simulator}; source_record_ids; prov_class ∈ {human_observed, simulator_truth}; label_source |
| **ref_interaction** | window_id (contains onset); person_identity_id, forklift_identity_id; per_camera · list<{camera_id, start_frame, end_frame_excl, assessable}>; t_onset_tl_s, t_offset_tl_s; assessability · enum{assessable, not_assessable}; visible_contact · enum{yes, no_visible_contact, cant_tell}; evasive_action · enum{yes, no, cant_tell}; evasive_onset_tl_s?; boundary_agreement_iou?; consensus_method; source_record_ids; prov_class; label_source |
| **ref_geometry** (B) | window_id; physical_identity_id; camera_id; frame_index; x_m, y_m, sigma_m; method · enum{simulator_truth, reference_survey, reference_click}; click_count; click_spread_m?; world_frame_id; interp_method |
| **ref_coverage_label** | window_id; camera_id; start_frame, end_frame_excl; ref_activity_state; reason?. Tiles each camera's part of the window; `reference_verified_absent` only in exhaustive, assessable windows (VR-E-052) |
| **reviewer_assessment** (C) | UUIDv7; annotator_id; namespace; target_type · enum{ref_event, system_episode, system_event}; target_id; label · enum{nm, ud, ct, not_hazardous, unsure}; confidence; rationale; blind; shown_system_output (false in reference); submitted_utc |
| **adjudication** | target_type, target_id, namespace; final_label; tier · enum{tier1, tier2}; method; assessment_ids; agreement_stat_ref?; prov_class = human_adjudicated |
| **validation_status_log** | Append-only JSONL hash chain: seq, status_id (UUIDv7), target_type, target_id, config_id, status · enum{unreviewed, confirmed, rejected, disputed}, layer, namespace, basis_ids, actor_id, created_utc, prev_hash, record_hash = SHA-256(JCS(entry without record_hash)) |

**Reference namespace rule:** `label_source ∈ {simulator_truth, human_manual}` only (VR-E-055).

### 5.9 Evaluation store

| Table | Fields |
|---|---|
| **split_manifest** | split_label, version; parent_version_id?; basis · enum{metadata_only, metadata_plus_reference_identity}; tier · enum{T1, T2a, T2b, T3, synthetic_to_real}; leakage_groups · list<{leakage_group_id, member_recording_ids, edge_types}>; assignments · list<{leakage_group_id, partition}>; t2b_shared_sessions?; shared_scene_content · bool; training_manifest_hashes; frozen_utc; revision? {audit_id, moved_groups, rule = PR-01} |
| **leakage_audit** | split_version_id; audit_seq; tier; edges_added · list<{recording_a, recording_b, edge_type, evidence_ref}>; violations · list<{leakage_group_id, partitions}>; discovery_basis · enum{metadata, sampled_annotation}; audit_complete · bool |
| **match_record** | window_id; config_id; scenario; ref_event_id?, system_event_id?; match_type · enum{matched, duplicate_alert, false_alert, miss, abstained_miss, unobservable_reference}; temporal_iou?; onset_error_s?, offset_error_s?; label_group · enum{G1, G2, any} |
| **error_attribution** | match_nk; primary_stage · enum{evidence_unavailable, perception, tracking, geometry, event_reasoning, linkage, reference_ambiguity, unresolved}; secondary_factors · list; attribution_status · enum{verified_oracle_single, verified_oracle_joint, diagnostic_inferred, unresolved}; oracle_artifact_ids; rule_test_results |
| **completeness_record** | window_id; metric_id · enum{CM-01…CM-10}; support_basis · enum{detected, detected_plus_inferred}; stratum · map; numerator, denominator; value? (`not_applicable` if denominator 0); interp_method; iou_cm; k_kf_s |
| **metric_result** | metric_id, definition_version; split_version_id; config_id?, scenario?, label?; slice · map; sample_type; estimand · enum{frame_description, new_session_performance, conditional_on_selection}; estimand_validity · enum{design_valid, requires_resample, conditional_on_selection}; validity · enum{valid, invalidated_leakage}; leakage_screening_status = `passed_available_screening`; weighted · bool; value?; ci_low?, ci_high?, ci_level?; interval_method · enum{stratified_window_bootstrap, cluster_bootstrap, wilson, bland_altman, none}; n_units, n_events, eff_n; counts_only?; shared_scene_content · bool; claim_level · enum{L1…L5, none}; coverage_companion_id? (required for conditional metrics) |
| **acceptance_criterion** | criterion_label, version; output_id; criterion_type · enum{technical_accuracy, completeness, repeatability, parameter_robustness, comparability}; metric_id; slice; rule · enum{ci_upper_le, ci_lower_ge, abs_bias_ci_within, exact_equal, flip_rate_le}; target; ci_level; estimand; n_min_units; preregistration_ref; frozen_utc |
| **measurement_fitness** | scope {output_id, measurement_definition_version, data_origin, condition_stratum, calibration_tier, config_id, intended_use enum{observation_description, exposure_duration_measurement, candidate_event_screening, rq2_candidate_input}, criterion_ids}; per-criterion decision · enum{met, not_met, inconclusive, not_assessable}; measurement_status · enum{technically_validated, experimental, unsuitable_under_tested_conditions, not_yet_assessable}; failing_interval?; construct_status · enum{CV0, CV1, CV2}; construct_evidence {definition_evidence_ref?, source_refs?, expert_alignment_result_id?}; parameter_sensitive · bool; override? {downgrade_only, rationale, actor}; interpretation_note (fixed text) |

### 5.10 Governance

**execution record and run register** (§2.5). **evidence_clip:** recording_id, start_frame, end_frame_excl, purpose · enum{review, reference_annotation, report_figure}, decoded_frame_sha256 · list, encoding, redaction_state · enum{none, faces_blurred, other}, access_class · enum{restricted_research, team_internal, publishable_synthetic_only}, retention_policy_id, expires_utc?. **retention_policy:** label, applies_to, retain_days?, deletion_method, legal_basis_ref? (provisional, D-4). **access_log:** append-only hash chain {actor, action enum{read, export, delete, policy_change}, target, purpose, time}. **stage_error:** run_id, error_index, code, severity · enum{data_recorded, stage_fatal}, recording_id?, frame_range?, message, contract_ref.

---

## 6. E1 classification (per episode)

### 6.0 Flag providers (per pair-frame; Kleene values)

| Flag | Provider | Rule | Unknown (2) when |
|---|---|---|---|
| G | substrate | 1 if `clearance_state = measured`; 0 if `unmeasurable_uncalibrated` | Any other unmeasurable state |
| Q | substrate | 1 if `q_state = sufficient`, else 0 | Never |
| P | **R1** image-space (uncalibrated configs) | `image_gap_norm < k_img` | Either box missing |
| P | **R2** ground clearance (calibrated configs) | `clearance_m < d_p` | `clearance_m` null |
| M | R2 | `speed_mps` (forklift, smoothed over *w_v*) `> v_min` | Speed null, including every R1-only configuration |
| X | engine | `P ∧ M` | Kleene |
| C_by_R3 | **R3** constant-velocity conflict | `pred_min_clearance_m < d_pc` for the constant-velocity model within horizon *τ* | No prediction (uncalibrated or insufficient history) |
| C_by_R4 | **R4** surrogate conflict | Time-to-collision `< ttc_max` **or** post-encroachment time `< pet_max`, from constant-velocity footprint paths | Uncalibrated |
| C_any | engine | OR over the enabled conflict providers | Kleene |
| E | **R5** evasive action (M-07) | Within window *w_e* centred on the frame: person heading-rate > *e_turn*, **or** person speed change > *e_acc*, **or** forklift deceleration > *e_dec* | Kinematics null on frames of the window |
| — | **R6** | Not a flag. A configuration "with R6" enables R3, R4 and R5 and applies the §6 labels; the D.1 label rule supersedes Package B's R6 formula | — |

**Rules for flags and configurations:**
- A configuration has exactly one P provider.
- Borderline frames (`|value − threshold| ≤ k_σ·σ` for P, M or C) set the episode's `borderline_flags`; the frame's flag value stays the point-estimate result.
- `exp_evasive_score` = maximum over the episode of the largest ratio of observed value to threshold among the three E criteria.
- The contact cue (for `suspected`) = forklift deceleration or person heading change within *w_e* of closest approach exceeding *k_c*.
- **R1-only configurations (BL-2)** cannot produce H; they are compared with BL-3 on episode detection over label group G1 `any`.


**Episode lifecycle (per configuration, per POW):**
1. Open on the first frame with `T = 1`.
2. Bridge false runs of ≤ *m_gap* frames.
3. Close at the last true frame (`end_frame_excl = last + 1`) or at POW end.
4. Assess attributes over *I⁺* = [open, min(close + *w_post*, POW end)).
5. Discard episodes shorter than *t_min* into `discarded_episode`.
6. Split at a POW break, linking the parts with `continuation_of`.

**Episode-level quantities:**
- `P_ep`, `X_ep`, `C_ep` = ∃ a true frame in *I*.
- `E_ep` = ∃ a true frame in *I⁺*; `unknown` if evasive action cannot be assessed.
- `minclr` = minimum over measurable frames of *I*.
- `K = E_ep ∨ (minclr < d_nm)` in Kleene logic.
- `X(t) = P(t) ∧ M(t)`.

**Contact state:**

| State | Condition |
|---|---|
| none_observed | Closest approach visible (`Q` sufficient), no overlap, and clearance − *k_σ*·σ > 0 |
| undetermined | Overlap; **or** clearance within *k_σ*·σ of 0; **or** closest approach not visible |
| suspected | Overlap **and** a contact cue beyond *k_c* at closest approach |
| not_assessable | No usable frames around closest approach |

**Labels:**

| Label | Rule |
|---|---|
| O | `P_ep ∧ ¬X_ep ∧ ¬C_ep` |
| H | `X_ep` |
| PC | `C_ep` |
| NM | `(H ∨ PC) ∧ K = 1 ∧ contact = none_observed` |
| UD | `(H ∨ PC) ∧ K = 1 ∧ contact = undetermined` |
| CT | `contact = suspected` |
| IE | `Q` insufficient at closest approach, **or** insufficient for > *o_max* of *I*, **or** contact = not_assessable, **or** (`K = 2` ∧ (H ∨ PC)) |

- **Summary label:** CT > UD > NM > PC > H > O.
- **Review routing:** an episode is routed to review if contact ∈ {undetermined, suspected} or it carries any of NM, UD, CT, IE. This includes the approved OI-1 case: a stationary-forklift overlap stays O and is routed.

**Invariants CL-INV-01–11** (D.1 §1.4) apply to every episode and candidate event:
- O ⇔ (P_ep ∧ ¬H ∧ ¬PC).
- O ∨ H ∨ PC.
- H ⇒ P_ep.
- At most one of NM/UD/CT.
- Label–contact correspondence.
- (NM ∨ UD) ⇒ (H ∨ PC).
- not_assessable ⇒ IE ∧ no G2 label.
- K unknown ∧ (H ∨ PC) ⇒ IE ∧ ¬NM ∧ ¬UD.
- Labels are a pure function of their inputs.
- No "observed contact" value exists.
- The summary label is derived from the labels.

Wording: automated outputs are "candidate", "suspected" or "undetermined"; "reviewer-confirmed" is used only for adjudicated labels.

---

## 7. Cross-camera linkage and counting (M2)

- **Edges:**
  - `D` (precedence over all others): same camera, time-disjoint beyond clock σ, incompatible calibrated positions, or different timelines.
  - `L`: `linked_calibrated` and eligible. Both clocks have σ, `sqrt(σa² + σb²) ≤ τ_sync`, and the median Mahalanobis distance ≤ *χ²_link*.
  - `P`: declared overlapping fields of view on the same aligned timeline.
  - `U`: otherwise.
- **Order:** episodes are sorted by (t_onset_us with nulls last, camera_id, episode natural key).
- **Grouping:**
  - S_VIEW: singletons.
  - S_LINK: greedy clique with allowed edges {L}. Each episode joins the earliest-created group whose every member has an allowed edge to it; otherwise it starts a new group.
  - S_POSS: the same rule applied to S_LINK groups as units, with allowed edges {L, P}.
- **After grouping:** record `alternative_groups` per member and set `ambiguous`. Every L/P edge between different groups sets `link_conflict`.
- **Guarantees:** S_VIEW ≥ S_LINK ≥ S_POSS by construction. Original episodes are never modified. Counts are reported as `scenario_count` with assumptions A1–A3; MR-07 results attach as `sample_supported` evidence, never as a bound.

---

## 8. Sampling, splits and leakage

**Sampling frame:**
- Non-overlapping windows of *w_ref* tile each camera group's timeline.
- Annotation covers all cameras of the group plus the guard *w_guard*.
- An event belongs to the window of its onset; durations are clipped to the window.

**RES and ECS:**
- RES uses stratified simple random sampling without replacement, with pre-system strata only; π = n_h/N_h and the weight is 1/π.
- Selection based on system outputs makes a window ECS.
- ECS is never used in headline metrics or in frequency, duration or per-hour aggregates.

**Estimators:**
- Horvitz–Thompson totals and ratio estimators (recall, precision, per-hour rates); unweighted values reported alongside; Kish effective n.
- Target A (sampled period): stratified window bootstrap.
- Target B (new sessions): cluster bootstrap over leakage groups.

**Aggregate meaning:**
- Natural real footage: describes the sampled recording period only.
- Staged footage: describes the script.
- Synthetic footage: describes the generator design.
- Nothing describes the establishment.

**Dependency sequence:**
1. S0 registration, including session lineage (R-1).
2. X0a preliminary leakage groups from metadata.
3. X0b split v1 frozen.
4. V0 sampling plan and windows.
5. Annotation.
6. X0c leakage audit.
7. **S8 on test is blocked until the latest audit has `audit_complete = true` (R-2).**

**Leakage groups** are the connected components over edges: same session, same physical interaction, same scene/run/render lineage, same scripted instance (roster + layout + script + day) and training use.

**PR-01:** a leakage group spanning partitions moves to the least evaluative partition (train > validation > test).

**R-3:**
- If the discovery basis is `sampled_annotation`, the affected test strata are marked `requires_resample`.
- Draw a fresh plan on the revised eligible population. Old-plan windows are excluded from headline metrics (usable as ECS).
- If resampling is infeasible, report as `conditional_on_selection` with no frequency or per-hour aggregates.

**R-4:** every revision records its audit, edges, rule, populations and plan versions. Its inputs never include metrics, label counts or system outputs.

**Tiers:**
- T1: no spanning group.
- T2a: T1 plus test camera placements absent from training.
- T2b: only the declared shared sessions may span, and `shared_scene_content = true` is required.
- T3: no recording from the test site in any training, tuning or selection manifest.

**Reporting:** a population is described as "passed the available leakage screening"; undiscovered relationships remain a stated limitation.

---

## 9. Evaluation

**9.1 Matching.**
- Candidate pairs share the same person–forklift pair and have temporal IoU ≥ *iou_m*.
- Assignment is a maximum-weight one-to-one Hungarian matching with weight = IoU, quantized to integer micro-units.
- Inputs are canonically sorted. Ties are broken by higher IoU, then earlier reference onset, then lower system natural key.
- Unmatched system events that overlap a matched reference are `duplicate_alert`; other unmatched system events are `false_alert`; unmatched references are `miss`.
- An abstention on an assessable reference is `abstained_miss`.

**9.2 Denominators.**
- Headline recall = matched ÷ assessable references (abstentions count as misses).
- Headline precision = matched ÷ (matched + false + duplicate), inside exhaustive windows.
- Coverage is reported with every conditional metric.
- False-alert burden = (false + duplicate) ÷ usable support hours.
- Ambiguous references (Tier 2 or unsure) are reported separately, with sensitivity analysis.

**9.3 Metric catalogue.**
- D1 perception: AP, recall at fixed false positives, score calibration (ECE).
- Tracking: HOTA, IDF1, MOTA, ID switches, fragmentation, pair-window fidelity.
- GV-01–08: geometry.
- EV-M1–M12: events.
- MR-01–12: reliability.
- CM-01–10: completeness. CM-01–03 are computed on both support bases; CM-09 is inferred-time agreement; CM-10 is the insufficient-time share.

Metric definitions are those of D §3–4 as amended by D.1 §2.4, and they are versioned through `definition_version`.

**9.4 Error attribution.**
- Every miss or false alert gets exactly one `primary_stage` (`unresolved` allowed).
- On synthetic data, oracle substitution runs over the 2³ combinations; the status is `verified_*`.
- On real data, rule-based tests run in pipeline order; the status is `diagnostic_inferred` or `unresolved`.
- `verified_*` is forbidden on real data.

**9.5 Construct status.**
- CV1 requires a versioned definition and cited source references.
- CV2 additionally requires an expert-alignment metric result: system outputs against independent, adjudicated C-layer judgments from attested-independent reviewers.
- Nothing above CV2 can be stored.
- Fixed interpretation note: "Agreement with expert judgment does not show that the measure predicts injuries."

**9.6 Fitness decision (per scope).**
- **Criterion decisions:**
  - `met`: the interval satisfies the rule.
  - `not_met`: the interval excludes the target in the failing direction.
  - `inconclusive`: the interval straddles the target.
  - `not_assessable`: no valid result, n below `n_min_units`, an invalidated split, or no registered criterion.
- **Status:**
  - `technically_validated`: every registered accuracy, completeness, repeatability and robustness criterion is `met` on real data, test partition, valid split and RES windows, with at least one criterion of each type; comparability is characterized.
  - `unsuitable_under_tested_conditions`: at least one accuracy or completeness criterion is `not_met`, and the failing interval is recorded.
  - `experimental`: any other result with at least one `met` or `inconclusive`.
  - `not_yet_assessable`: all criteria are `not_assessable`.
- Overrides can only downgrade. Scopes are never merged. Criteria must be frozen before the first test-partition evaluation.

---

## 10. Stages, interfaces and errors

### 10.1 Stages

| Stage | Consumes | Produces | Class |
|---|---|---|---|
| S0 Register | Files, dataset metadata, licence audit | §5.1 tables, timelines, clock alignments | exact |
| S1 Decode & coverage | recording, timeline, clock_alignment, decode config | decode_summary, frame, coverage_segment | exact (same build) |
| S2 Detect | frames, weights (config) | detection | tolerance |
| S3 Track | detection | track, track_point | exact |
| ORACLE-S3 | Simulator truth or fixture tracks | track, track_point (prov simulator_truth) | exact |
| S4 Spatial & substrate | S3, calibration, context, priors, coverage, substrate config | object_state, pow, pair_series, exposure_profile, activity_segment (gpw in M2; E2 tables later) | exact |
| S5 Events | S4, rule_configuration | flag_series, episode, discarded_episode, candidate_event, event_count_summary (event_link in M2) | exact |
| S6 Evidence | episodes, frames | evidence_clip | exact (frame ranges) |
| X0a/X0b | S0 metadata, training manifests | split_manifest v1 | exact |
| V0 Sample | split, coverage, camera groups | sampling_plan, reference_window | exact |
| CV-SIM | Simulator truth, windows | Validation-store reference tables (prov simulator_truth) | exact |
| V1–V4 | Clips, windows | Human annotation, assessments, adjudications, status log | append-only |
| X0c Audit | split, reference identities | leakage_audit, possibly a new split version | exact |
| S8 Evaluate | Obs + Val + split + plan + acceptance criteria | match_record, error_attribution, completeness_record, metric_result | exact |
| S8f Fitness | metric_result, acceptance_criterion | measurement_fitness | exact |
| S9 Export | Obs + Eval | OBX bundle (§11) | exact |

**Access rules:**
- V0 has **no read access** to S2–S5 outputs.
- S8 on test is blocked until R-2 is satisfied.
- S5 never writes substrate tables.

### 10.2 Interfaces (Python protocols; record types from §5)

`Registrar.register(sources, metadata) -> S0Artifact` · `Decoder.decode(recording, timeline, cfg) -> S1Artifact` · `DetectorAdapter.detect(frames) -> list[Detection]` (CF-IMG, raw scores) · `Tracker.run(detections, cfg) -> S3Artifact` · `OracleTrackSource.tracks(truth) -> S3Artifact` · `GeometryEstimator.estimate(track_point, calibration | None, prior) -> ObjectState` · `SubstrateBuilder.build(s3, s1, s0, cfg) -> S4Artifact` · `FlagProvider.flags(pair_series, object_states, params) -> FlagColumns` · `EventEngine.run(s4, rule_cfg) -> S5Artifact` · `SplitBuilder.freeze(metadata) -> SplitManifest` · `LeakageAuditor.audit(split, identities) -> LeakageAudit` · `SplitBuilder.revise(split, audit) -> SplitManifest` (applies PR-01 only) · `ReferenceSampler.draw(frame, plan_cfg) -> V0Artifact` · `SimReferenceConverter.convert(truth, windows) -> ValArtifact` · `Matcher.match(windows, refs, events, iou_m) -> list[MatchRecord]` · `Evaluator.evaluate(…) -> S8Artifact` · `FitnessEngine.decide(results, criteria) -> list[MeasurementFitness]` · `Exporter.export(…) -> OBX`.

The ID library (`ids.build_artifact`) implements §2.3. No interface takes undocumented dictionaries.

### 10.3 Errors

| Code | Severity | Behaviour |
|---|---|---|
| ERR-TIMESTAMPS | fatal | Untimed fraction > *f_untimed* |
| ERR-DECODE-FRAME | data_recorded | Frame indexed, ineligible, `unusable` |
| ERR-CALIB-MISSING | data_recorded | World fields null `uncalibrated`; calibrated providers write unknown flags |
| ERR-CALIB-FAILED | fatal | Calibration with `quality_state = failed` used |
| ERR-CALIB-TIER | fatal | Computation not permitted for the tier (§4.2) |
| ERR-SCHEMA-MAJOR, ERR-UNKNOWN-ENUM | fatal | |
| ERR-NATURAL-KEY, ERR-FK | fatal | §2.3 step 3 |
| ERR-INVARIANT | fatal | Any CL/TI/EC/LK/ID invariant violated |
| ERR-LEAKAGE | fatal | Split or audit violation for the tier |
| ERR-AUDIT-PENDING | fatal | S8 on test before R-2 |
| ERR-NAMESPACE | fatal | Non-reference or non-permitted label source used as reference |
| ERR-FORBIDDEN-FIELD | fatal | Forbidden E2/RQ2 field or value |
| ERR-ECS-AGGREGATE | fatal | ECS used in a headline or frequency aggregate |

A fatal error leaves no complete artifact. `data_recorded` errors go to `stage_error`.

---

## 11. RQ2 observation export (OBX)

**Parts:**
1. Provenance (pseudonymous).
2. Coverage and activity.
3. Substrate with exposure profiles, including calibration tier and σ status.
4. Episodes and events per configuration, with scenario labels and assumptions.
5. Validation summary: current status, adjudicated labels, no reviewer identities.
6. Completeness on both support bases.
7. Uncertainty register.
8. Fitness snapshot by scope.
9. Data dictionary.

**Guarantees:**
- Every measure carries its scoped measurement status and construct status.
- Detected and detected + inferred durations are exported side by side.
- Grouping keys: site, session, camera, camera group, timeline period, configuration, data origin.

**Excluded:** rates per establishment, indices, scores, rankings, OSHA or NAICS identifiers, injury data, employer names, worker identities, appearance features, and E2 physics-of-harm quantities.

---

## 12. Validation rules, tests and fixtures

### 12.1 Validation rules (active)

- **E:** VR-E-001–005, 010–021, 030–034, 040–041, 050–054, 060–062, 070–071. Amendments:
  - VR-E-010 now reads "resolved timestamps strictly increasing over eligible frames".
  - VR-E-033 is superseded by LK-07.
  - VR-E-063 is superseded by FT-01–11.
  - New VR-E-055: reference namespace label sources.
- **Invariant families:**
  - TI-01–13 (time).
  - ST-1–6 (support rules, tested via CT-T-14–20).
  - SP-01–11 (splits and sampling).
  - CB-01–05 (calibration).
  - CC-01–04 (experiment contract).
  - CD-01–03 (activity).
  - ID-01–15 (identity).
  - LK-01–08 (linkage).
  - EC-01–05 (evidence classes).
  - FT-01–11 (fitness).
  - CL-INV-01–11 (classification).

### 12.2 Contract tests (active)

| Group | Tests | Milestone |
|---|---|---|
| Schema and general | CT-E-01, 05, 06, 07, 08, 11, 12, 13, 14, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 30 | M0 |
| Coverage independence | CT-E-04 | M0 |
| Classification | CT-E-09, CT-E-10 (D1-AC-01/02) | M0 |
| Time | CT-T-01–20 | M0 |
| Splits and sampling | CT-S-01–10 | M0 |
| Identity | CT-I-01–08, CT-ID-01–07, CT-FK-01–07 | M0 |
| Evidence and fitness | CT-F-01–10 | M0 |
| Calibration, experiment, activity fixtures | FX-B1–B3, FX-C1/C2, FX-D1/D2, FX-A3/A4 | M0 |
| E2 forbidden fields | CT-E-26 (revised FX-12: load_state + occupancy profile, no episodes) | M0 |
| Linkage | CT-L-01–06, CT-E-15, CT-E-16 (wording = scenario_count), CT-E-17 | M2 |
| Re-run tolerance (S2) | CT-I-02 | M1 |

Equivalent tests have a single owner: CT-I-01 ≡ CT-ID-02 ≡ CT-FK-04 (exact re-run).

Also active:
- **CT-F-11:** export and report generation refuse any configuration labelled `TEST-ONLY` (Package F §3).
- **D.1 acceptance criteria D1-AC-01–19** are verified through the tests above. The Package F work packages name the test that covers each criterion. D1-AC-12/13 (linkage wording) belong to M2, except the wording scan, which runs in M0.

### 12.3 Superseded tests and fixtures

CT-E-02 (replaced by CT-ID-02); CT-E-03 (replaced by CT-T-01–08); E.1 FX-A1/FX-A2 and CA-01–03 (replaced by FX-A3/A4 and TI-11–13).

### 12.4 Fixture catalogue

| ID | Content |
|---|---|
| FX-01–06 | Classification truth-table cases T1–T11 (D.1 §1.5) |
| FX-07 | Uncalibrated camera |
| FX-08, FX-09, FX-17, FX-18 | Linkage (M2) |
| FX-10 | VFR, PTS gap, corrupt frame |
| FX-11 | Three activity states over one minute |
| FX-12 | E2 elevated load, measurement only |
| FX-13 | Reviewer disagreement → Tier 2 |
| FX-14 | Cross-partition leakage |
| FX-15 | ECS window |
| FX-16 | Joint perception + geometry error (oracle) |
| FX-CLIP-A–D | Clarification §2.3 cases (0/33/66/100 ms) |
| FX-A3.1 | Leakage counterexample (errata A3.1) |
| FX-FK | Identity worked example (§2.3 reference values) |

---

## 13. Versioning

- **Minor:** optional column; descriptive enum value.
- **Major:** invariant enum change (contact_state, labels, activity states, sample_type, evidence_class, experiment); unit, frame, timebase or ID derivation change; column removal or rename.
- Migrations write new artifacts with lineage; nothing is migrated in place.
- Parameter changes create new configuration IDs, never schema changes.
- **Adding E2 episodes requires a major version and an approved classification contract `E2_v1`.**

---

## 14. Named parameters (no values in this contract)

*k_sup*, *f_untimed*, *f_sub*, *g_max*, *v_min*, *w_v*, *k_img*, *d_p*, *d_pc*, *ttc_max*, *pet_max*, *w_e*, *e_turn*, *e_acc*, *e_dec*, *m_gap*, *t_min*, *w_post*, *d_nm*, *k_σ*, *k_c*, *o_max*, *τ*, *iou_m*, *iou_cm*, *k_kf*, *w_ref*, *w_guard*, *n_min*, *τ_sync*, *χ²_link*, *iou_rep*, *s_rep*, *ε_geo*, *b_tol*, *m_e2*.

Research values are pre-registered by the researcher. Fixture values for tests are defined in Package F §3 and marked **TEST-ONLY**.
