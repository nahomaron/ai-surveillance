# Change requests

Contract gaps and conflicts, raised by the implementation agent (CLAUDE.md, Package F section 9). Nothing here changes the contract until it is approved.

## CR-001 (2026-11-09) — Rule, test and fixture text is not in the normative documents   status: CLOSED

**Raised by:** implementation agent. **Task:** T-01, and everything that depends on it.
**Contract sections:** E-1.2.1 §2.3, §12.1, §12.2, §12.4; F.1 A6 and Appendix N3; Package F §5.
**Meaning-affecting:** yes, because these items define what counts as a pass.

**Problem.** E-1.2.1 says implementers build "from this document only" and must not consult superseded text. F.1 A4 says Appendix N contains everything M0 needs. However, the items below are cited as required but are stated only by ID. No text for them exists in any document on the CLAUDE.md list.

| Family | Required by | Text available |
|---|---|---|
| VR-E rules (34 active) | T-01 | 8 have some text: VR-E-002, 003, 010, 040, 041, 052, 055, 070. No text for the other 26: 001, 004, 005, 011–021, 030–032, 034, 050, 051, 053, 054, 060–062, 071 |
| CT-E-01, 05, 30 | T-01 "Done when" | ID only |
| CT-ID-01–07, CT-FK-01–07, CT-I-01/03–08 | T-02 | ID only (CT-FK-05 has one sentence in §2.3) |
| Worked example payload ("seven-row track and track-point payload of the clarification §1.3") | T-02 "Done when" | Payload absent. Only its output hashes are given, so the reference values cannot be reproduced |
| Form of a `<table>_nk` column value | T-02 | Not stated. It affects every payload hash |
| FX-A3, FX-A4, FX-B1–B3, FX-C1/C2, FX-D1/D2, FX-A3.1 | T-03, T-05, T-08 | ID only |
| FX-CLIP-A–D ("clarification §2.3") | T-03, T-04, T-06 | N3 gives expected values and frame times, but not which interval each case measures |
| CT-T-01–20, including parts (a)–(d) of CT-T-20 | T-06, T-08 | ID only |
| CT-S-01–10, CT-E-18/19/23 | T-10 | ID only |
| CT-E-04, 06–14, 20–22, 24–29, CT-F-01–10 | T-06 to T-15 | ID only |
| Invariants TI-01–13, SP-01–11, CB-01–05, CC-01–04, CD-01–03, ID-01–15, LK-01–08, EC-01–05, FT-01–11 | T-05 onward | Partial. Some are named beside a sentence, most are ID only |
| D.1 CL-INV numbering, D1-AC-01–19 | T-09 onward | CL-INV is listed in E-1.2.1 §6 without numbers. D1-AC items are ID only in the normative set |

**Evidence.** A text search of `docs/contract/` and `docs/plan/` finds these IDs only in lists of tests. `docs/methodology/` contains none of the VR or CT IDs.

**Likely source (not opened).** The parent folder holds `Package_E_Data_Schemas_and_Interface_Contracts.md`, `Package_E1_Implementation_Critical_Contract_Correction_Addendum.md`, `Package_E1_Final_Errata_and_Foundation_Model_Feasibility_Note.md` and `Package_E1_Pre_Implementation_Contract_Clarification.md`. The agent did not read them: they are not on the CLAUDE.md document list, and E-1.2.1 forbids consulting superseded text.

**Proposed resolution** (see DECISIONS_NEEDED.md D-1).
- (a) The Research Architect consolidates the missing text into a normative Appendix (E-1.2.3). This is the cleanest record but takes longest.
- (b) The Owner adds those four files to the CLAUDE.md list as normative **only for the text of rule, test and fixture IDs**, and E-1.2.2 wins any conflict. This restores progress at once. The agent would log each ID it takes from them.

**Affected tasks:** T-01 (remainder) and T-02 onward through T-16, because every one of them depends on T-01.
**Decision:** Resolved by Appendix T (E-1.2.3).   **Approver:** Research Owner, 9 Nov 2026 (D-1).   **Resulting contract version:** E-1.2.3

## CR-002 (2026-11-09) — Schema-level gaps found while building the schema source   status: CLOSED (AR-1 to AR-10; item 10 by Appendix T T5)

**Raised by:** implementation agent. **Task:** T-01 part A.
**Contract sections:** E-1.2.1 §1.1, §2.3, §2.4, §5; F.1 A1.2; Package F §3.
**Meaning-affecting:** to be judged by the Research Architect. Items 3, 4 and 7 affect artifact hashes.

Part A proceeds with the provisional handling below. Each item is marked in code (`~` or `types_inferred`) and listed in `reports/T-01_vr_coverage.md`.

| # | Gap | Provisional handling |
|---|---|---|
| 1 | `clock_alignment` and `calibration` natural keys include `version`, but §5.1 lists no such field | Added `version · str`, provisional |
| 2 | 25 tables in §5.8–§5.10 and F.1 A5 list field names without types | Types inferred and marked at table level |
| 3 | No prefixes are given for configuration tables, reference tables or the A5 tables, although F.1 A1.2 computes `id(prefix, …)` for configurations | Own-ID column named `<table>_id`, no prefix. Must be settled before configuration IDs exist (T-02) |
| 4 | The form of a `<table>_nk` value is not stated (also in CR-001) | Stored as a string, provisional. It changes every payload hash |
| 5 | F.1 A1.2 lists `decode_config`, `geometry_config` and `sampling_plan_config`, but no fields are defined | Not registered |
| 6 | §5.2 names several configuration fields in prose only, and `version_label` (Package F §3) is not in §5.2 | Field names taken from the prose, marked provisional |
| 7 | §1.1 allows `ts` only in `execution.json` and human-entry records, yet §5.1, §5.8 and §5.9 use `retrieved_utc`, `verified_utc`, `frozen_utc` and `locked_utc` in artifact tables. The JCS form of a `ts` value is not stated | Typed as `ts`. Payload hashing for these columns is open |
| 8 | VR-E-003 forbids sentinel values, but no sentinel values are listed | NaN and infinity are checked. The sentinel clause has no check |
| 9 | VR-E-055 applies to reference records, but §5.8 gives `ref_geometry` no `label_source` | Added `label_source`, provisional |
| 10 | The worked-example spec ID `asp_s3example0000000000000` has 22 characters after the prefix, where derived IDs have 26 | No code effect yet. It may be a transcription error, or intentional because it is only a literal |

**Decision:** ______   **Approver:** ______   **Resulting contract version:** ______

---

# Agent Resolutions

Made under the "Agent authority to close contract gaps" section of CLAUDE.md. All are reviewed at the G-M0 stop. Each states the gap, options, choice, why measurement meaning is unaffected, files and tests, and how to reverse it. CR-002 items map to AR numbers of the same number, except item 10, which Appendix T T5 settles (the literal is exempt from ID-pattern validation).

## AR-1 — `version` column on `clock_alignment` and `calibration`
- **Gap:** F.1 A1.3 keys include `version`; §5.1 lists no such field. **Options:** (a) add `version · str`, (b) integer. **Choice:** (a), matching `world_frame.version`.
- **No meaning effect:** an identifier for corrections only (ANC-1). **Files/tests:** `schema/tables.py`; `test_ar1_version_columns_are_strings`. **Reverse:** change the type in `tables.py`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-2 — Column types where the contract lists names only
- **Gap:** 25 tables in §5.8–5.10 and F.1 A5 give field names without types. **Options:** (a) infer from suffix conventions (§1.2) and enums, (b) block. **Choice:** (a). Counts are `i64`, durations and ratios `f64`, references `id`, free references `str`.
- **No meaning effect:** storage types only; no value or formula is set. **Files/tests:** `schema/tables.py`, list in `reports/T-01_vr_coverage.md`; `test_generates_valid_arrow_and_json_schema`, `test_every_table_round_trips_through_parquet`. **Reverse:** edit the type lines.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-3 — ID prefixes the contract does not give
- **Gap:** F.1 A1.2 computes `id(prefix, …)` for configurations, and §2.1 gives human records a table prefix, but no prefix is listed for these tables. **Options:** (a) assign short unique prefixes, (b) use one generic prefix. **Choice:** (a): `fpp sbc bsc rcf dcf gcf spc rop rin rgm rcl tia tis anr anc rva adj rtp alg ecl ser`.
- **No meaning effect:** the prefix labels the ID and is not hashed by `id()`. **Files/tests:** `schema/tables.py`; `test_ar3_prefixes`. **Reverse:** rename the prefix; IDs change only in their label.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-4 — Storage form of `<table>_nk`
- **Gap:** Appendix T T5 fixes the payload value as a JSON array (`["rec_a",1]`) but not its Parquet column type. A natural key is heterogeneous, so it has no single Arrow list type. **Options:** (a) store JCS text in a utf8 column and decode on read, (b) one Arrow struct per table. **Choice:** (a).
- **No meaning effect:** hashing always uses the decoded array, so `payload_sha256` is unaffected; CT-FK-05 reconstruction checks it. **Files/tests:** `schema/registry.py`; `test_nk_is_json_array_in_json_schema_and_text_in_arrow`, `test_nested_values_round_trip`. **Reverse:** swap `_encode`/`_decode`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-5 — Fields of `decode_config`, `geometry_config`, `sampling_plan_config`
- **Gap:** F.1 A1.2 lists these configuration tables with no fields. **Options:** (a) define containers holding only parameters named in §5.2, §8 and §14, (b) block. **Choice:** (a). No default values exist; all values come from configuration records.
- **No meaning effect:** containers only; parameter definitions are unchanged. **Files/tests:** `schema/tables.py`; `test_every_contract_table_is_registered`. **Reverse:** edit the definitions.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-6 — Configuration field names given only in prose; `version_label`
- **Gap:** §5.2 names some fields in prose, and Package F §3 requires `version_label = "TEST-ONLY"` without listing it in §5.2. **Options:** (a) use the §14 parameter names and add a nullable `version_label`, (b) free-form maps. **Choice:** (a).
- **No meaning effect:** naming only. It enables the T-15 TEST-ONLY guard. **Files/tests:** `schema/tables.py`; `test_minimal_row_is_valid_and_loads_into_arrow`. **Reverse:** rename.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-7 — `ts` columns in artifact tables and their JCS form
- **Gap:** §1.1 restricts `ts` to `execution.json` and human entries, but §5.1, §5.8 and §5.9 declare `retrieved_utc`, `verified_utc`, `frozen_utc` and `locked_utc` on artifact tables. The JCS form is unstated. **Options:** (a) keep the specific field declarations, treat values as supplied inputs, hash as RFC 3339 UTC text, (b) drop them from payloads. **Choice:** (a). Pipelines must take these from configuration or metadata and never from the clock, which keeps exact-class stages reproducible.
- **No meaning effect:** provenance timestamps enter no measurement. **Review flag:** this settles an inconsistency inside E-1.2.1, so the Architect may prefer (b). **Files/tests:** `schema/canonical.py`; `test_ar7_timestamps_round_trip_in_rfc3339_jcs_form`. **Reverse:** exclude those columns from the payload stream.
- **Architect review (11 Nov 2026): REVISED.** (1) Supplied provenance times (`retrieved_utc`, `verified_utc` and any other `*_utc` describing a source, given as input) stay payload columns, taken only from configuration or metadata. Event times (`frozen_utc`, `locked_utc` and any `*_utc` recording when a pipeline or human action happened) form a third column class, "event-time columns": stored, but outside the payload hash, the artifact ID and every record ID, and dropped by the reconstruction check. Their values come from the execution record or the human-entry record. (2) Every hashed or stored `*_utc` value uses exactly `YYYY-MM-DDTHH:MM:SS.ffffffZ`; any other format is a validation error. (3) VR-E-054, SP-01, SP-08 and FT-02 read the event-time columns. (4) Tests as listed in the review.
- **Applied (11 Nov 2026):** event-time columns are `sampling_plan.frozen_utc`, `split_manifest.frozen_utc`, `acceptance_criterion.frozen_utc` and `reference_window.locked_utc` (with its null reason), marked `@event` in `schema/tables.py`. The builder validates and stores them but leaves them out of the payload; configuration IDs and VR-E-004 also exclude them. Strings must match the canonical format (rule `UTC-FORMAT`); datetimes serialize to it. VR-E-054 is tested on stored windows. SP-01, SP-08 and FT-02 do not exist yet; T-10 and T-14 must read the event-time columns. Human-entry tables (`submitted_utc`, `created_utc`) are not artifact tables and are unchanged. Tests: `tests/schema/test_event_time.py`, `test_ar7_timestamps_round_trip_in_rfc3339_jcs_form` (updated by Architect decision, not an edited expected value).
- **Not applied as worded:** "changing a supplied `retrieved_utc` changes the `dataset_source` ID". Under F.1 A1.2, which takes precedence, the anchor ID is `id(prefix, [table, (name, version)])`, so it cannot change. The test instead pins that the payload hash and S0 artifact ID change and that ANC-1 raises `ERR-ANCHOR-CONFLICT`. See CR-004.
- **Owner decision D-5 (12 Nov 2026):** the review test is replaced by "changing retrieved_utc leaves the dataset_source ID unchanged, changes the S0 payload hash, and registering both versions raises ERR-ANCHOR-CONFLICT". The Architect withdrew the earlier specification. `test_supplied_retrieved_utc_is_hashed` already asserts exactly this; only its citation changes.

## AR-8 — Which values count as sentinels (VR-E-003)
- **Gap:** Appendix T says "no sentinel values (e.g., −1 for unknown)" and gives no list. −1 is legitimate in signed columns (`x_m`, `offset_s`, `image_gap_px`). **Options:** (a) reject negatives in columns that cannot be negative, (b) reject −1 everywhere. **Choice:** (a), as (b) would reject valid measurements.
- **No meaning effect:** rejects invalid records and changes no valid value. In signed world columns, CT-E-05 catches sentinels through VR-E-014. **Files/tests:** `schema/validate.py`; `test_ar8_sentinel_applies_only_to_non_negative_columns`. **Reverse:** edit `_NON_NEGATIVE`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-9 — `label_source` on `ref_geometry`
- **Gap:** VR-E-055 constrains reference records, but §5.8 gives `ref_geometry` no such column. **Options:** (a) add it, (b) exempt the table. **Choice:** (a), the stricter option that keeps the namespace guard complete.
- **No meaning effect:** provenance only. **Files/tests:** `schema/tables.py`; `test_ar9_ref_geometry_has_label_source`. **Reverse:** remove the line.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-10 — VR-E-019 does not exist
- **Gap:** §12.1 gives the range 010–021, but Appendix T has no VR-E-019. **Evidence:** Package E, Validation rules table, goes from VR-E-018 (line 871) straight to VR-E-020 (line 872), so this is a numbering gap, not lost text. **Options:** (a) treat as non-existent, (b) raise a CR. **Choice:** (a).
- **No meaning effect:** no rule is added or removed. **Files/tests:** `schema/coverage.py`; `test_coverage_lists_every_active_rule_exactly_once`. **Reverse:** add the rule to `ACTIVE`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-11 — Scope of VR-E-041 and `stage_error.severity`
- **Gap:** Appendix T forbids "severity" while §5.10 defines `stage_error.severity` (an error-handling level). **Options:** (a) forbid the field names everywhere with that one exemption, (b) check E2 tables only. **Choice:** (a), the stricter option.
- **No meaning effect:** the exempted column is not a harm quantity. **Files/tests:** `schema/registry.py`; `test_no_forbidden_field_in_any_table`. **Reverse:** remove the exemption.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-12 — Where the VR-E-070 ID applies
- **Gap:** E-1.2.1 §5.1 cites VR-E-070 for `site.approvals_ref`; Appendix T amends VR-E-070 to source-file retention and clip access. **Options:** (a) apply Appendix T to the ID and keep the §5.1 requirement under its own check, (b) drop the site check. **Choice:** (a), so no requirement is lost. Check name: `SITE-APPROVALS`.
- **No meaning effect:** both requirements are enforced. **Files/tests:** `schema/validate.py`, `schema/vr_rules.py`; `test_site_approvals_still_required_for_real_origins`. **Reverse:** rename the rule tag.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-13 — Inputs for VR-E-018 and VR-E-021
- **Gap:** VR-E-018 needs "a GV-05 evidence reference for the stratum", and no table holds one. VR-E-021 requires SI units, which a validator cannot infer from a number. **Options:** (a) pass GV-05 evidence as a validator argument keyed by calibration ID, and check unit suffixes, (b) add columns. **Choice:** (a).
- **No meaning effect:** validators only; `sigma_status` is unchanged. **Files/tests:** `schema/vr_rules.py`; VR-E-018 and VR-E-021 cases. **Reverse:** change the arguments.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-14 — Schema version string
- **Gap:** VR-E-001 and CT-E-30 need a major-version test, but no format for `schema_version` is stated. **Options:** (a) use the contract version with Package F §9's rule (E-1.2.x minor, E-1.3 major), (b) separate numbering. **Choice:** (a).
- **No meaning effect:** compatibility handling only. **Files/tests:** `schema/errors.py`; `test_schema_major_uses_package_f_section_9`. **Reverse:** change `_major`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-15 — Rounding of microsecond keys
- **Gap:** CN-2 says round half to even, but not whether on the exact binary value or a float product. **Options:** (a) exact `Decimal`, (b) `round(x * 1e6)`. **Choice:** (a), which does not depend on floating-point multiplication.
- **No meaning effect:** natural-key components only; durations do not use this. **Files/tests:** `ids/core.py`; `test_ar15_time_keys_use_exact_half_even_microseconds`. **Reverse:** change `to_us`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-16 — ART-ISO prefixes and the error for schema violations
- **Gap:** ART-ISO needs each spec's configurations to be recognizable, but tracker, oracle, model, inference and evaluation configurations have no prefix. §10.3 has no code for a generic schema violation found while building. **Options:** (a) prefixes `trc`, `orc`, `mdl`, `inf`, `evc`, and use `ERR-INVARIANT` for schema violations, (b) add typed spec fields and a new error code. **Choice:** (a), which leaves the §2.1 spec shape and the §10.3 code list unchanged.
- **No meaning effect:** labels and error reporting only. **Files/tests:** `ids/artifact.py`; `test_ct_nk_06_art_iso`, `test_ar16_schema_violation_uses_err_invariant`. **Reverse:** change `ART_ISO` or the raised code.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-17 — Scope of CT-I-03, 04, 07, 08 at T-02
- **Gap:** these tests describe pipeline behaviour (a real `g_max` change, recalibration, rule change, metric lineage) but T-02 precedes S4, S5 and S8. **Options:** (a) test the identity behaviour at builder level now and re-exercise it when those stages exist, (b) defer T-02. **Choice:** (a). The re-runs are scheduled in T-08, T-09, T-14 and T-16.
- **No meaning effect:** test scheduling only. **Files/tests:** `tests/ids/test_identity.py`. **Reverse:** move the tests.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-18 — Integers beyond the range RFC 8785 can hash
- **Gap:** `i64` columns can hold values above 2⁵³−1, but RFC 8785 (I-JSON) cannot serialize them, and the contract's hash requires JCS. **Options:** (a) reject such values as a schema violation, (b) hash them as strings. **Choice:** (a). It fails visibly, and no contract quantity needs that range (timestamps in microseconds reach about 285 years; published dataset seeds are far smaller).
- **No meaning effect:** rejects an unrepresentable record and changes no valid value. **Files/tests:** `schema/validate.py`; `test_ar18_integers_outside_i_json_range_are_rejected`, `test_ar18_is_a_contract_error_not_a_serializer_crash`. **Reverse:** change the check and add a string form to `canonical.py`.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-19 — Test-only value for `n_miss`
- **Gap:** F.1 A6 adds *n_miss* to §14, and FX-ID-8 mentions it, but Package F §3 gives no test value. **Options:** (a) a labelled TEST-ONLY value of 5 frames, (b) block FX-ID-8. **Choice:** (a). FX-ID-8 has no reference person on any frame, so its result does not depend on the value.
- **No meaning effect:** TEST-ONLY; never a research threshold. If a later fixture's result depends on this value, it needs a CR. **Files/tests:** `fixtures/records.py`; `test_test_only_values`, `test_fx_id_expectations`. **Reverse:** edit the parameter.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-20 — Design details of FX-ID box fixtures
- **Gap:** F.1 A5.2 states expected results but not box coordinates or, for FX-ID-2, when p1 and p2 are present. **Options:** (a) simple constant boxes with each person present only while tracked, (b) both persons present throughout, which would add missed frames that F.1 does not list. **Choice:** (a). FX-ID-6 uses boxes hand-computed to give IoU 0.60 and 0.59.
- **No meaning effect:** fixture inputs only; expected statuses, counts and shares are F.1's. **Files/tests:** `fixtures/records.py`; `test_fx_id_6_box_iou_hand_calculation`, `test_fx_id_expectations`. **Reverse:** change the segments and regenerate.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-21 — Delivering timestamp faults to the decoder; Case A–D layouts
- **Gap:** T-04 asks for clips with missing or duplicate timestamps, but every container tested (Matroska, NUT, AVI, MP4, MPEG-TS) repairs or rejects them on write. Appendix T cites Cases A–D without giving their layout. **Evidence:** Clarification §2.3 worked-example table (cases A–D, including "depth 2" and neighbours for case C) and §2.4 ("an encoder plus deliberate corruption or timestamp stripping"). **Options:** (a) real encoded clips plus a `.faults.json` overlay applied to packets at demux, (b) hand-written container bytes, (c) synthetic frame records with no decoder. **Choice:** (a). The real decoder then sees those timestamp states. Corrupt packets remain real corrupted bytes in the file.
- **No meaning effect:** fixture delivery only; timestamp rules are unchanged. **Limit:** a file that natively lacks a timestamp is not exercised, because none could be produced. **Files/tests:** `fixtures/clips.py`; `tests/clips/test_clip_fixtures.py`. **Reverse:** replace the overlay with crafted files.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-22 — Default camera groups
- **Gap:** §8 tiles windows per camera group, and §5.1 defines `camera_group`, but nothing says which groups S0 creates when none are declared. **Options:** (a) one `whole_session` group per timeline holding its cameras, (b) require declared groups. **Choice:** (a), using an existing enum value. Declared groups can be added later as a new version of the registration.
- **No meaning effect at M0:** fixtures use single-camera or whole-session groups. **Review flag:** for real multi-camera data, group choice affects sampling windows, so research configurations must declare groups explicitly. **Files/tests:** `registry/registrar.py`; `test_ar22_one_whole_session_camera_group_per_timeline`. **Reverse:** remove the default.
- **Architect review (11 Nov 2026): ACCEPTED as written.** Note: "The grouping defines the sampling frame. Changing groups after a sampling plan is frozen requires a new plan version. Research configurations declare the grouping basis explicitly; add this item to the T-20 pre-registration draft." Applied: the T-20 row in WORKPLAN.md now lists the item.

## AR-23 — Fixture records without key fields
- **Gap:** Appendix T FX-B1 and FX-B3 omit fields needed to build a row (`version`, and `valid_from_us` in FX-B1), and FX-B3 states that "field presence and nullability are what the test checks". **Options:** (a) add these in the test adapter, (b) amend the fixture. **Choice:** (a). The committed fixture stays verbatim.
- **No meaning effect:** key fields of a test record only. **Files/tests:** `tests/registry/test_registrar.py` (`_calibration`). **Reverse:** edit the adapter.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## CR-003 (2026-11-10) — How δ_nom is obtained, and what *f_sub* does   status: CLOSED

**Raised by:** implementation agent. **Task:** T-06, and everything that depends on it (T-08 to T-16).
**Contract sections:** E-1.2.1 §3.3, §5.3, §14; Appendix N3; Appendix T TI-02, CT-T-04, CT-T-06, CT-T-17; Package F §3.
**Meaning-affecting:** yes. It changes measured durations.

**Problem 1: no definition of δ_nom.** §3.3 uses δ_nom for capping and for the final frame, and §5.3 stores `delta_nom_s`, but E-1.2.3 never says how it is obtained from a recording. N3 says its expected values "assume δ_nom = 0.033 s".

E.1 Addendum line 62 (superseded, read as evidence only) says "`δ_nom` the median `Δ` of the video". Applied to the timed frames of the N3 cases, with *k_sup* = 1.5:

| Candidate | Case A | Case B | Case C | Case D | Agrees with N3? |
|---|---|---|---|---|---|
| N3 required | 0.100 | 0.067 | 0.033 | 0.133 | — |
| (a) Median Δ of timed frames | 0.100 | 0.084 (δ_nom 50 ms) | 0.050 | 0.133 | **No** for B and C |
| (b) Value declared in `decode_config`, 0.033 for fixtures | 0.100 | 0.067 | 0.033 | 0.133 | Yes, by construction |
| (c) Container nominal rate (1/30 s) | 0.1003 | 0.0673 | 0.0333 | 0.1333 | **No**: N3 requires exact values to 1 µs |

**Problem 2: *f_sub* has no stated behaviour.** E-1.2.3 names *f_sub* and sets a test value, but no rule uses it, and no rule says when coverage is `usable_degraded`. E.1 Final Errata line 74 (superseded) says "above *f_sub* the coverage state becomes `usable_degraded` with reason `timing_substituted`", per video. Case D's substituted share is 0.033/0.133 ≈ 0.25, above the test value 0.10. It is unclear whether every usable segment of the recording degrades or only segments containing substituted frames.

**Proposed resolution** (DECISIONS_NEEDED.md D-4).
1. δ_nom: a value declared in `decode_config` when one is known, otherwise the median Δ of timed frames. Fixtures declare 0.033 as TEST-ONLY.
2. *f_sub*: adopt the Errata rule. Apply it only to segments containing substituted frames, so that good footage in the same recording is not downgraded.

**Affected tests:** CT-T-04, 06, 14–20, FX-CLIP-A–D, FX-10.
**Decision:** Approved (D-4). δ_nom: declared, else adjacent-pair median, else all-timed median. *f_sub*: only substituted frames' support becomes `usable_degraded`. Normative text: Appendix T section T7.   **Approver:** Research Owner, 11 Nov 2026.   **Resulting contract version:** E-1.2.4

## AR-24 — Representation of the T7 declaration and the final-frame variant
- **Gap:** T7 lets the decode configuration declare `delta_nom_s` "for the recording" with an evidence reference, and §3.3 defines a sensitivity variant for the final frame. Neither has a field. **Options:** (a) `decode_config.delta_nom_declarations: list<{recording_id, delta_nom_s, evidence_ref}>` and `final_frame_support: enum{delta_nom, zero}`, (b) a map keyed by recording. **Choice:** (a), which carries the evidence reference T7 requires. `delta_nom_median_s` is null `not_applicable` when no adjacent pair exists.
- **No meaning effect:** containers for values T7 and §3.3 define. **Files/tests:** `schema/tables.py`; `test_ar5_config_table_columns` (updated for E-1.2.4), `test_ct_t_21_declared_source_recorded`, `test_ct_t_06_final_frame_sensitivity`. **Reverse:** change the fields.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-25 — "Decode order" is bitstream order; presentation index is decoder output order
- **Gap:** §3.2 says `decode_seq` follows decoder output order, yet computes `reorder_depth` from "presentation index − decode index". A conforming decoder outputs frames in presentation order, so if "decode index" meant output order, the depth would always be 0. **Evidence:** CT-T-16 (Appendix T) requires 0.033 s for Case C, which needs depth 2. Clarification §2.3 case C ("depth 2", decode neighbours f0, f2, f3) confirms. **Options:** (a) decode index = bitstream (packet) order and presentation index = rank in decoder output order, (b) both from output order. Only (a) reproduces CT-T-16; (b) gives 0.067 s. **Choice:** (a). The same meaning applies to ST-2 "±r decode positions" and T7 "adjacent in decode order".
- **No meaning effect beyond the contract:** it is the only reading consistent with the normative values. **Review flag:** T7 adjacency in bitstream order means B-frame streams contribute few adjacent pairs; if none exist, T7 step 3 applies. **Files/tests:** `decode/timestamps.py`, `decode/video.py`; `test_case_c`, `test_ct_t_02_b_frames_follow_pts`. **Reverse:** change `rank` and `index` in `resolve`.
- **Architect review (11 Nov 2026): ACCEPTED.** The `decode_seq` wording is corrected by Appendix T T7.1 (E-1.2.5): `decode_seq` is demux (file/DTS) order, not decoder output order, and `reorder_depth` and the ST-2 neighbourhood use that order. T7.1 also replaces the T7 step 2 adjacency rule with a presentation-order median excluding pairs that overlap an uncertainty region, which removes the B-frame concern above. **Applied:** `decode_seq` = demux position. The presentation index for `reorder_depth` is the decoder output position, which still counts untimed frames; ranking by PTS alone would give Case B depth 1 instead of the Clarification's 0.

## AR-26 — PyAV does not expose FFmpeg's best-effort timestamp
- **Gap:** §3.2 resolves PTS, then the container best-effort timestamp, then DTS-derived. PyAV frames expose only `pts` and `dts`. **Options:** (a) skip the best-effort step, (b) reimplement FFmpeg's guess. **Choice:** (a). Without a PTS, FFmpeg's best-effort value is the DTS, and DTS-derived acceptance (depth 0) is never stricter than best-effort acceptance (depth 0 and consistent). The resolved time is therefore the same, and the frame is labelled `dts_derived`, never `best_effort`. T7's substituted share counts both sources, so it is also unchanged.
- **No meaning effect:** identical times, eligibility and support. **Files/tests:** `decode/timestamps.py`; `test_case_d`. **Reverse:** add a best-effort branch if PyAV exposes it.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-27 — Exclusion rules version `rv1`; VFR flag; packet-to-frame matching
- **Gap:** eligibility excludes frames with an "exclusion quality flag (rules version)", but no rules version is defined. Image-quality detection is a WP-04 non-goal ("exclusion rules are configuration"). `vfr_detected` has no definition. The decoder reports frames, not packets, so undecodable frames must be found by matching. **Choice:** `rv1` excludes `decode_error` only, and no other quality flag is computed. `vfr_detected` = spread of the intervals used for δ_nom exceeds one time-base tick. Frames are matched to packets by PTS, then DTS, then untimed order. A packet that raises, or whose frame never appears, is undecodable.
- **No meaning effect at M0:** no fixture has frozen, black, overexposed or blurred frames. **Review flag:** before real footage, the Owner should approve a rules version with quality flags. **Files/tests:** `decode/timestamps.py`, `decode/video.py`; `test_ct_t_05_fifteen_undecodable_frames`, `test_ct_t_01_vfr_durations_are_support_sums`. **Reverse:** add a rules version.
- **Architect review (11 Nov 2026): ACKNOWLEDGED.** Before any real footage, the agent proposes a frame-quality rules version (frozen, black, blur, exposure) for Architect review and Owner approval. **Applied:** STOP G-FQ added to WORKPLAN before the first real-data task; the rules version is on the T-20 pre-registration checklist.
- **Architect review (11 Nov 2026), VFR fixture (33/50 ms alternation): KEEP as is.** The 17 ms `gap_unobserved` segments are correct contract behaviour. **Applied:** `test_ct_t_01_vfr_durations_are_support_sums` asserts them explicitly, citing this review.

## AR-28 — Fixture value of *f_untimed* for Cases B and C
- **Gap:** Cases B and C have one untimed frame in four (25%), so §3.2 step 6 rejects them at the test value 0.05. However, N3, CT-T-15, CT-T-16 and CT-T-22 expect results from them. Package F §3 assigns 0.05 to CT-T-08 and CT-T-17, and §9 allows test-only values to change within the fixture work. **Options:** (a) a TEST-ONLY *f_untimed* of 0.5 for these two clips, (b) longer clips, which would change the N3 values. **Choice:** (a). Expected values are unchanged. A test pins that 0.05 still rejects Case B.
- **No meaning effect:** TEST-ONLY; rejection behaviour is unchanged. **Files/tests:** `tests/decode/test_s1.py` (`FIXTURE_F_UNTIMED`); `test_ar28_case_b_is_rejected_at_the_ct_t_08_value`. **Reverse:** remove the override.
- **Architect review (11 Nov 2026): ACCEPTED** (fixture-specific TEST-ONLY *f_untimed* for the 4-frame clips).

## CR-004 (2026-11-11) — Should a supplied provenance time change an anchor ID?   status: CLOSED

**Raised by:** implementation agent, applying the Architect review of AR-7. **Contract sections:** F.1 A1.2 (anchor IDs, ANC-1), §2.4.
**Meaning-affecting:** no measurement effect. It affects identity rules only, which are above the agent's authority because the review and F.1 A1.2 disagree.

**Problem.** The review asks for a test where changing `retrieved_utc` changes the `dataset_source` ID. F.1 A1.2 defines the anchor ID from the natural key (name, version) alone, so the ID is independent of other payload columns. A changed payload under the same anchor raises `ERR-ANCHOR-CONFLICT`, and corrections "create a new version field value, never an overwrite".

**Current behaviour (implemented and tested):** the payload hash and the S0 `art_` change, the `dsr_` ID does not, and registering both raises `ERR-ANCHOR-CONFLICT`. A re-retrieval must therefore register a new `version`.

**Options.** (a) Keep F.1 A1.2: re-retrieval is a new version, as now. (b) Add `retrieved_utc` to the `dataset_source` natural key, which needs an F.1 amendment.
**Agent's recommendation:** (a). It keeps one anchor ID per dataset version and makes silent changes visible through ANC-1.
**Decision:** D-5 (a), 12 Nov 2026: keep F.1 A1.2; re-retrieval with different provenance uses a new version label.   **Approver:** Research Owner

## CR-005 (2026-11-11) — Substrate quantities named but not defined (T-08)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-08, which blocks T-09 and later.
**Contract sections:** E-1.2.1 §3.4, §5.5 (`object_state`, `pow`, `pair_series`, `exposure_profile`), §6.0 (R1, R2, M, Q, E); Appendix T CT-F-01, CT-T-18.
**Meaning-affecting:** yes. Each item changes flags, durations or labels.

E-1.2.5 names these quantities but gives no computable definition. The source documents were read as evidence only: Package E §E-22 to E-25, the E.1 Addendum, and Package B M-02 to M-06 and UNC-01 to UNC-03.

| # | Quantity | What the contract says | Evidence elsewhere | Proposed definition |
|---|---|---|---|---|
| 1 | POW gap bridging (`bridged_gaps`, `gap_exceeded`) | *g_max* in frames; "bridging on eligible frames only" (Package F WP-05); ST-6 via CT-T-18 | E.1 Addendum l.101: "bridges a track gap ≤ *g_max* only across frames that exist (supported frames in which the object was not detected)" | A gap is a run of eligible frames inside the co-presence span on which either object has no `tracked` detection. If the run has ≤ *g_max* frames and no coverage gap inside it, it is bridged (frames classed by §3.4); otherwise the POW ends (`gap_exceeded`) and a new POW starts after it |
| 2 | Speed, heading and `speed_sigma_mps` "smoothed over *w_v*" (R2 M flag, R5, motion split of exposure) | Name only | B M-03: "smoothed ground speed"; B §3: "smoothed derivative of ground position over window *w_v*" | Least-squares line fit of floor position against timeline time over frames in a centred window of width *w_v* (detected or inferred frames with measured positions). Speed and heading come from the slope; σ from the fit residuals. Null when fewer than 3 frames are in the window or the camera is uncalibrated |
| 3 | `closing_rate_mps`, `ttca_s` | Names | B M-04: −dc/dt smoothed over *w_v*; Package E: positive = approaching; TTCA under constant velocity, null `not_applicable` if diverging | Closing rate = −slope of clearance by the item 2 fit. TTCA = `t_at_min_s` of the constant-velocity prediction; null `not_applicable` when clearance is not decreasing |
| 4 | `clearance_sigma_m`, `pos_cov_m2`, `sigma_status` | Fields; N1 σ rule (null σ ⇒ margin uses 0 and `not_estimated`) | B UNC-02/03: "propagate", "combine", no formula | Until GV-05 evidence exists, `clearance_sigma_m` is null and `sigma_status = not_estimated`, so the N1 σ rule applies. A propagation formula would be approved later as a separate amendment. Alternatively, now: σ_c = √(σ_person² + σ_forklift² + σ_footprint²) along the separation direction |
| 5 | `image_gap_px` (R1 P flag); non-nullable | "signed box gap"; ÷ person box height (CN-9) | E: "signed box-to-box gap in CF-IMG; ≤ 0 means box overlap" | Disjoint boxes: Euclidean distance between their nearest points. Overlapping boxes: minus the smaller of the x-overlap and y-overlap |
| 6 | `q_state`, `q_reasons` (Q flag, IE label, contact `none_observed`); non-nullable | Enum values only | E: "B.1 `Q` definition"; B.1: "closest approach visible", qualitative | `insufficient` if either object's pair-frame class is not `detected` (`predicted_only` or occluded), a box touches the image border (`truncated`), the frame's support is `timing_uncertain`, or the frame has a quality flag (`low_quality_frame`); otherwise `sufficient` |
| 7 | `evidence_state` (feeds `t_joint_visible_s`) | Enum values only | E: "both `visible` or `partially_visible`" | Oracle tracks supply it. On the detector path: `truncated` if the box touches the border, `occluded_predicted` if predicted, `lost` if lost, otherwise `visible`. `partially_visible` only when `visibility_frac` is computed |

**Affected tests:** CT-T-18, CT-F-01, CT-E-06 to 08 (pair-series rows), N2 M flag (speed), and all S5 tests downstream.
**What proceeds meanwhile (T-08 part A):** oracle S3 tracks and evidence classes, support-based durations and evidence-class sums, activity segments, signed footprint distance and constant-velocity predicted clearance. None of these depend on the items above.
**Decision:** superseded by T8 (Appendix T, contract E-1.2.6; D-6 (b), 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.6

## AR-29 — Oracle `tracked` points count as detected
- **Gap:** §3.4 classes an object-frame as `detected` if `state = tracked` "with a detection". ORACLE-S3 (§10.1) produces tracks from simulator truth or fixtures, with no S2 detection. **Options:** (a) oracle `tracked` points are `detected`, with the truth standing in for the detection, (b) oracle frames are never detected. **Choice:** (a). Under (b), ORACLE-S3 could never produce detected time, which would defeat its purpose as the perception upper bound (Package F M1a).
- **No meaning effect:** applies only to oracle tracks, whose `prov_class` is `simulator_truth`; `detection_id` is null `not_applicable`. **Files/tests:** `substrate/oracle.py`; `test_oracle_s3_tracks_and_evidence_classes`. **Reverse:** change `object_class` for oracle input.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-30 — Frame-level activity state
- **Gap:** §3.5 and CD-01 to CD-03 define where `not_evaluated` applies but not how the three detection states are assigned. **Options:** (a) read the enum names: `pair_detected` when a person and a pair-class object are both `tracked` on the frame, `objects_detected_no_pair` when any object is `tracked`, otherwise `observed_no_detection`; (b) tie `pair_detected` to an open POW. **Choice:** (a). Predicted objects are not detections. Segments follow frame support inside each usable coverage segment and merge equal neighbours.
- **No meaning effect expected:** a POW requires co-present tracks, so (a) and (b) differ only on frames inside a bridged POW gap, which CR-005 item 1 has yet to define. **Review flag:** if the Architect prefers (b), it can follow CR-005. **Files/tests:** `substrate/activity.py`; `test_activity_segments_tile_coverage`. **Reverse:** change `_state`.
- **Architect review (12 Nov 2026): ACCEPTED.**

## CR-006 (2026-11-11) — Windows that do not fill *w_ref* at the end of a timeline   status: CLOSED

**Raised by:** implementation agent. **Task:** T-10. **Contract sections:** E-1.2.1 §8 (sampling frame), §5.8 (`frame_definition`, `reference_window`).
**Meaning-affecting:** yes. It changes the sampling frame (N_h, π and weights).

**Problem.** §8 says "non-overlapping windows of *w_ref* tile each camera group's timeline", but not what happens when the extent is not a multiple of *w_ref*. Nor does it say whether the guard may run past the extent. No source document addresses this; D.1 §4 assumes windows are long relative to interactions. The choice matters: an SDG run lasts 10 s, so with the TEST-ONLY *w_ref* = 30 s, rule (a) below puts no SDG window in the frame at all.

**Options.** (a) Complete windows only, with the remainder outside the frame and reported. (b) A final, shorter window whose length is recorded. Its π is unchanged, but its duration enters every per-hour estimator. (c) Require *w_ref* to divide each timeline extent, and refuse otherwise.
**Agent's recommendation:** (b), with the guard clipped at the extent end. Under (a), short synthetic sessions would disappear from the frame.
**Interim behaviour (no invented rule):** the tiler raises `ERR-SPEC` when the extent is not a multiple of *w_ref*. All T-10 fixtures use exact multiples.
**Decision:** D-7 (b), 12 Nov 2026: the last window may be shorter; `window_length_s` recorded on `reference_window`; guard clipped at the timeline end; weights stay 1/π.   **Approver:** Research Owner

## AR-31 — Metadata leakage edges
- **Gap:** §8 lists the edges as "same session, same physical interaction, same scene/run/render lineage, same scripted instance (roster + layout + script + day) and training use", but does not map them to fields. **Evidence:** D.1 §3.2 ("same source scene or run: SDG run's 10 views; SmartSpaces scene and its re-renders"); Package E E-45 edge enum (`same_session`, `same_physical_interaction`, `same_scene_or_run`, `same_scripted_instance`, `training_use`); E.1 Errata R-1 ("run, scene and render lineage, plus seeds").
- **Choice:** `same_session` when `session_id` is equal. `same_scene_or_run` when, within one dataset, `scene_id`, `ext_run_id`, `render_parent` or `seed` is equal, or one recording's `render_parent` equals the other's `scene_id`. `same_scripted_instance` when roster, layout, script and collection day are all non-null and equal. `training_use` links every recording in a training manifest, and that group must be in `train`. `same_physical_interaction` comes only from the X0c audit. Null fields create no edge.
- **No meaning effect beyond the contract:** implements the listed edges. **Review flag:** including `seed` and render parentage is the conservative reading. Extra edges only merge groups, so data moves to less evaluative partitions. **Files/tests:** `splits/leakage.py`; `tests/splits/test_splits.py`. **Reverse:** edit `metadata_edges`.
- **Architect review (12 Nov 2026): ACCEPTED.**

## AR-32 — Initial partition assignment
- **Gap:** `SplitBuilder.freeze(metadata)` must assign leakage groups to partitions, but no assignment method is given. A random split with target fractions would be a design choice. **Choice:** partitions are declared per recording in the split configuration, as researcher input. A group whose members carry different declarations is a T1 violation (VR-E-060) and raises `ERR-LEAKAGE` at freeze. PR-01 is not applied at freeze, because it is defined only for audit revisions.
- **No meaning effect:** an input, plus an existing rule. **Files/tests:** `splits/builder.py`; `test_ct_e_23_two_cameras_of_one_interaction_across_partitions`. **Reverse:** add an assignment method.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-33 — Mechanics of the RES draw and bootstrap percentiles
- **Gap:** §8 and N5 fix stratified SRSWOR with π = n_h/N_h and PCG64 seeded from configuration, but not the draw order or the percentile interpolation. **Choice:** windows sorted by (stratum, camera group, window index); strata drawn in sorted order from one `numpy.random.Generator(PCG64(seed))` using `choice(N_h, n_h, replace=False)`. Bootstrap percentiles use numpy's default linear interpolation. `frame_sha256` = SHA-256 of the JCS window list.
- **No meaning effect:** the design, π and weights are as specified; only which equally probable sample occurs depends on these details. Results are reproducible for the pinned numpy. **Files/tests:** `sampling/plan.py`, `evaluation/estimators.py`; `test_res_draw_is_seeded_and_reproducible`. **Reverse:** change the draw loop.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## AR-34 — T2b audits and declared shared sessions
- **Gap:** under T2b, "only the declared shared sessions may span" (§8), and CT-S-05 expects an audit to pass when the same interaction is seen by cameras of a declared shared session in different partitions. The audit record has no field to mark such an edge as expected. **Options:** (a) the audit leaves edges inside one declared shared session out of `edges_added` and out of violation detection, (b) record them with a new edge type. **Choice:** (a). Leakage groups for T2b are built without same-session edges for declared sessions, and undeclared spanning sessions raise `ERR-LEAKAGE` at freeze (SP-06, CT-S-06).
- **No meaning effect:** implements SP-06 and CT-S-05 as written. **Review flag:** R-4 asks that revisions record their edges; expected T2b edges are not recorded because they trigger no revision. **Files/tests:** `splits/builder.py`; `test_ct_s_05_t2b_declared_share`, `test_ct_s_06_t2b_undeclared_share`. **Reverse:** add an edge type.
- **Architect review (12 Nov 2026): ACCEPTED WITH CHANGE.** Edges inside a declared T2b shared session are recorded in `leakage_audit.edges_added` but not listed as violations. **Applied:** see the T-10 follow-up commit; `revise` receives the recordings' metadata so that it applies the same exclusion (SP-07 still holds: metadata only, no metrics or labels).

## AR-35 — Schema and labelling details needed to implement T8
- **Gaps and choices** (all representation; T8 values are unchanged):
  1. `pair_series.image_gap_px` and `image_gap_norm` become nullable (null `not_observable`), because R1's P is unknown "when either box missing" (§6.0) and T8.1 gap frames can lack a box.
  2. `pair_series.predicted[].sigma_m` becomes nullable (null `not_computed_by_config`), because no rule defines the uncertainty of a predicted minimum.
  3. T8.2 gives the pair-frame a `footprint_orientation_unknown` borderline flag, but `pair_series` has no flag field. It gains `borderline_flags`, and the episode `borderline_flags` enum gains the same value so S5 can carry it.
  4. The T8.3 horizon τ is stored as `substrate_config.prediction_horizon_s`, because S4 computes the prediction and S5 may not write substrate. T8.6's *v_part* is stored in `geometry_config.v_part`.
  5. With a null covariance, `clearance_sigma_m` is null with reason `not_supplied`. `not_estimated` is a `sigma_status` value, not a null reason.
  6. T8.7 lists occlusion reasons for predicted objects. A lost or missing object is also reported as `person_occluded` or `forklift_occluded`; `q_state` itself follows T8.7 exactly.
  7. Oracle positions: `geometry_method = simulator_truth`, `calibration_id` null `not_applicable`, `world_frame_id` null `not_supplied`. The exposure profile's `calibration_tier` is `calibrated_unvalidated`, the conservative choice.
- **No meaning effect:** nullability, field placement and labels only. **Review flag:** items 6 and 7. **Files/tests:** `schema/tables.py`, `substrate/*`; `tests/substrate/test_part_b.py`, `test_ar5_config_table_columns`, `test_ar6_named_configuration_fields` (updated for the new fields). **Reverse:** edit the definitions.
- **Architect review (12 Nov 2026):** items 1–5 ACCEPTED. Item 6 REVISED by T10.9: a lost or missing object is listed as `person_lost` / `forklift_lost`, not `*_occluded`; q_state is unchanged. Item 7 ACCEPTED for M0. At T-18, set `world_frame_id` and `calibration_tier` for oracle data from the dataset's declared frame and calibration, and raise a CR if the dataset supplies none. Oracle-path results are never pooled with detector-path results; exports carry `geometry_method`.

## CR-007 (2026-11-12) — Footprint anchor on the camera-based path   status: CLOSED (superseded by Appendix T T24.1, E-1.2.25; Owner decision D-54, 23 Nov 2026); earlier OPEN for the Architect as a pre-registration v2 input (D-50 item 4), DEFERRED (D-8); evidence added 14 Nov, 17 Nov and 19 Nov 2026

**Raised by:** implementation agent. **Task:** T-08 (not blocking M0); blocks the detector path (T-22, T-23, M1b).
**Contract sections:** E-1.2.1 §5.2 `footprint_prior.anchor` · enum{box_bottom_centre, rear_axle, centre}; §5.5.
**Meaning-affecting:** yes. It shifts the forklift footprint, and so clearance.

**Problem.** A calibrated camera gives the floor point under the box's bottom centre (`foot_point_px`). The contract does not say how that point relates to the footprint rectangle for `box_bottom_centre` or `rear_axle` anchors, for example how far behind or below the centre it lies, and along which axis given yaw. Oracle positions are footprint centres, so the M0 fixtures are unaffected. The builder currently treats the projected point as the footprint centre, which is correct only for `anchor = centre`.
**Proposed resolution:** for `box_bottom_centre`, use the projected point as the footprint centre (the bottom-centre of a ground-contact box approximates the footprint's image centre). For `rear_axle`, place the centre at `length/2 − rear_overhang` ahead along yaw, with `rear_overhang` added to the prior. If yaw is unknown, use the circumscribed disc as in T8.2.
**Decision:** DEFERRED to T-22 (D-8, 12 Nov 2026). Reopen with GV-03/GV-04 evidence. Until then the oracle and simulator path uses the simulator footprint centre.   **Approver:** Research Owner
**Evidence added for the T-22 decision (Architect ruling A of 14 Nov 2026, from CR-023):** on SDG the T8.2 heading fallback (yaw = direction of travel of the footprint centre) is about 77° off the body axis during pivot turns. Over the 67 runs checked, 7,860 of 16,507 moving-forklift frames (≥ 0.3 m/s) are turning frames (yaw rate ≥ 5°/s over 10 frames); on them the angle between the direction of travel and the box long axis has median 77.5°, P99 81.3°, and 74 % lie beyond 75°. On straight frames (8,647) it is within 10.5° on every frame. SmartSpaces turning frames: median 2.5°, P99 11.3°. Source: `research/datasets/part3/yaw_motion_check.json`. A camera-based path without a supplied yaw would therefore orient the forklift rectangle almost across the body during such turns; the anchor rule and the yaw fallback should be decided together.
- Evidence added 17 Nov 2026 (G-M1a, D-40 item 7): on SDG validation the full_camera forklift position error has median 1.12 m (ceiling) and 0.99 m (eye level), P99 about 1.5 m, and no outliers (no tracked forklift above 10 m; `research/m1a/position_diagnosis_sdg.json`). This is consistent with the bottom-centre foot point lying at the near edge of the footprint rather than at its centre (forklift box 3.03 × 1.13 m). Input for the T-22 decision.

- **Evidence added 19 Nov 2026 (D-47 item 2; diagnosis only, no anchor rule chosen; `research/m1b/cr007_evidence.py` → `cr007_evidence.json`).** Column B of the T-25p pilot: oracle boxes with `full_camera` geometry, 206 SDG validation cameras, 59,622 forklift object-frames. Error = estimate − simulator footprint centre, split along and across the line of sight (camera floor point → true position):
  - **All:** along, signed median −1.01 m (|along| median 1.02 m, P95 1.46 m); across, median 0.09 m (P95 0.58 m). Only 2.9 % of estimates lie beyond the true centre.
  - **Ceiling:** along −1.10 m; across 0.06 m (P95 0.26 m).
  - **Eye level:** along −0.88 m; across 0.12 m (P95 0.79 m).
  - The optical-axis split gives the same picture: along −0.96 m, across 0.12 m.
  - So the error lies almost entirely along the line of sight, toward the camera, by about 1 m. That lies between the prior's half-width (0.58 m) and half-length (1.34 m), which fits the box's bottom-centre landing near the footprint's near edge rather than its centre (the `box_bottom_centre` → centre offset this CR asks about). It is not proof of the anchor, since the forklift's orientation to the camera varies.
  - **EV split** (column B; one worker–forklift pair per camera, split by the camera's median forklift error):
    - below 1 m (90 cameras; 36 ceiling, 54 eye level): BL-6 EV-M1 0.72 (89/124), EV-M2 0.47 (89/191);
    - 1 m or more (116 cameras; 63 ceiling, 53 eye level): EV-M1 0.77 (121/158), EV-M2 0.63 (121/191).
    - BL-2 uses no floor geometry, yet it also differs between the groups (0.47 / 0.41 against 0.60 / 0.54). The split is therefore confounded by viewpoint and scene; it does not isolate the effect of the forklift offset on events.

**Ruling (D-54, 23 Nov 2026; the Architect's draft part 1 as corrected against E-1.2.24, approved by the Owner):** closed as superseded by Appendix T **T24.1** (contract E-1.2.25): a constant shift d away from the camera, for forklifts on the `full_camera` tier only, implemented opt-in. v2 candidate values d = 1.00 m, r_taper = 2.0 m (SDG prior); SmartSpaces prior d × 0.923 (scaled, not fitted); selected, not frozen (`docs/preregistration/v2_notes.md`). The residual is reported (D1: median 0.33 m, P95 0.64 m). Detector and oracle boxes use the same d (D4: paired difference about −0.05 m).

## AR-36 — Status-log and CV-SIM conventions
- **Gaps and choices:**
  1. The status log's first `prev_hash` is 64 zeros. `status_id` uses the prefix `sts`. Entries are stored as JCS JSON lines.
  2. CV-SIM presence intervals, keyframes and geometry cover the window plus its guard, because annotation covers the guard (§8). Spans tile [t_start, t_guard_end) per A3.
  3. In a non-exhaustive window, usable time with nothing present is `not_annotated`, never `reference_verified_absent` (RC-03).
  4. Simulator geometry has `sigma_m = 0`, `interp_method = none` and a keyframe on every eligible frame, with `evidence_state = visible`. The simulator supplies no occlusion state; that is a T-18 adapter detail.
  5. CV-SIM `ref_interaction` rows take onset and offset from the simulator's interaction intervals, with `visible_contact = cant_tell`, because synthetic data cannot support contact claims (Package F WP-13 non-goals). Their `reference_class` is `rule_conformance` (RV-01). An interaction belongs to the window of its onset.
- **No meaning effect:** representation and fixture conventions; reference semantics follow A3 and A5.1. **Review flag:** item 4 (visibility), for real use. **Files/tests:** `validation/*`; `tests/validation/test_store.py`. **Reverse:** edit the converter.
- **Architect review (12 Nov 2026):** items 1–3 and 5 ACCEPTED. Item 4 ACCEPTED for M0 fixtures. At T-17, record whether each dataset supplies visibility or occlusion truth. At T-18 the adapter sets `evidence_state` from it when present. Where it is absent, every report that uses reference visible support (CM-01–03, CM-10) must state "reference visibility assumed". Raise a CR if that choice changes a CM denominator.

## CR-008 (2026-11-12) — Event-engine inputs that §6 names but does not define (T-09)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-09. Part A (defined parts) proceeds; part B waits.
**Contract sections:** E-1.2.1 §6.0, §6 (lifecycle, contact state, labels); Appendix N1, N2; Appendix T T8.2.
**Meaning-affecting:** yes. Each item changes E, K, contact state or labels.

| # | Gap | Effect | Proposed resolution |
|---|---|---|---|
| 1 | R5 needs "person heading-rate", "person speed change" and "forklift deceleration" within *w_e*, with no estimator | E flag, K, NM, `exp_evasive_score` | Use T8.2 smoothed values. heading-rate = |Δheading| / *w_e* over the window ends (wrapped to (−π, π]); speed change = |Δspeed| / *w_e*; deceleration = −Δspeed / *w_e*. Null if either end is null |
| 2 | The contact cue compares "forklift deceleration or person heading change" with one threshold *k_c* (3.0 m/s²), although heading change is in radians | Contact `suspected`, label CT | Apply *k_c* to forklift deceleration only (item 1 estimator, over *w_e* centred on CA), and add a separate threshold for person heading change if wanted |
| 3 | The value of E when R5 is not enabled (BL configurations without R6) | K is unknown everywhere, so IE replaces NM and UD. N2 G2 would get IE, against its expected H | With R5 disabled, E = 0 and `E_ep = false`, recorded as "not assessed by configuration"; or K uses only the clearance term |
| 4 | Closest-approach frame | Contact state, Q at CA, IE, `exp_speed_at_ca_mps` | In N1 T10/T11 CA (frame 15) lies outside the measured-clearance frames, so CA is not simply the minimum measured clearance. Proposal: minimum measured clearance in *I*; if the minimum image gap occurs on a frame where clearance is not measurable, that frame; null if neither exists (then `not_assessable`) |
| 5 | "No usable frames around closest approach" (`not_assessable`) | T10 (`undetermined`) and T11 (`not_assessable`) have the same flags around CA, so the distinction must come from this definition | Usable = pair-frame evidence class ≠ `insufficient` on eligible frames within ±*w_e*/2 of CA |
| 6 | Lifecycle step 2 "bridge false runs ≤ *m_gap*": whether unknown (T = 2) runs bridge or close | Episode boundaries | Treat any run with T ≠ 1 as the gap; ≤ *m_gap* bridges, longer closes |
| 7 | N2 G1–G3 expect M and C_by_R3 on every frame, but T8.2 gives no velocity on the first and last frame (half-window span 0.2 s < *w_v*/2), so M and C_by_R3 are unknown there | Per-frame flags at two frames per fixture. Episode labels are unchanged, but episode extent and minimum clearance can change: G3 gives [1, 9) with minclr 2.50 m instead of [0, 10) with 2.35 m | Amend N2 to expect unknown (2) on the edge frames, or let T8.2 accept a one-sided window at the ends of a track |
| 8 | `onset_sensitive` borderline flag | Borderline reporting | Set when moving the open frame by ±1 frame changes whether the episode survives *t_min* |

**Interim (part A):** providers R1, R2, R3, G, Q and the Kleene combinations; lifecycle; episode quantities; K, contact state and labels from explicit closest-approach inputs; CL-INV; N1 T1–T13 at flag level; CT-E-10, 12, 13, 14; N2 interior-frame flags. No S5 artifact is produced from S4 until items 1 to 5 are decided.
**Decision:** superseded by T9 (Appendix T, contract E-1.2.7; D-9, 12 Nov 2026). T9 also corrects T8.2 (T9.1) and Appendix N1 row T10 (T9.9).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.7

## AR-37 — Reading Appendix N1 rows at flag level
- **Gap:** N1 gives "contact inputs at the closest-approach (CA) frame" but names a CA frame only for T10 and T11. T11's `not_assessable` rests on its stated condition "(no usable frames within ±*w_e*/2 of CA)", which the flag columns cannot express (CR-008 item 5). **Choice:** where N1 gives no CA frame (T1–T9), CA is the first frame of minimum clearance; since clearance is constant in those rows, any frame gives the same result. T11's stated condition is passed as the "usable around CA" input; every other row has usable frames. In T10 and T11, clearance is measured on frames 0–9 only, as the rows state.
- **No meaning effect:** test-harness reading of N1. The expected values are N1's, unchanged. **Files/tests:** `tests/events/test_engine_part_a.py` (`run_n1`, `n1_frames`). **Reverse:** edit the harness once CR-008 items 4 and 5 are decided.
- **Architect review (12 Nov 2026):** ACCEPTED.

## AR-38 — Representation and reading choices for T9 (T-09)
- **Gaps and choices:**
  1. **E per frame when R5 is off.** T9.4 sets `E_ep = 0`. The `flag_series.E` value is not stated. It is written as 0, so that `E_ep` still follows the §6 rule (∃ a true frame) and the two agree.
  2. **Contact-state order.** T9.6 step 2 says "any §6 undetermined condition", and §6 lists overlap as one. Read literally, that would make `suspected` (overlap ∧ cue) unreachable, which contradicts Appendix N1 T7 and T9. Appendix N takes precedence over Appendix T. The order implemented is: not_assessable (T9.6 step 1); undetermined if Q is insufficient at CA (step 2, first clause); suspected if overlap = 1 and cue = 1; undetermined for the other §6 conditions (overlap unknown, overlap without a cue, clearance within k_σ·σ of 0); otherwise none_observed. **Review flag.**
  3. **Readings of T9 text.** (a) T9.1 keeps T8.2's "spanning ≥ w_v/2", because "All other T8.2 rules are unchanged". A run spanning less than w_v/2 therefore gives null speed. (b) A "contiguous run" is a run of consecutive eligible frames of the recording. (c) In T9.5 step 2, "the next frame of I is not measured" requires that such a frame exists. If m* is the last frame of I, CA = m* and is observed. (d) In the Appendix N1 harness, the CA frame, overlap and cue are row inputs (AR-37). Usable frames around CA are no longer an input: T9.6 derives them from Q.
  4. **Borderline labels.** A borderline P (R2 clearance against d_p) or C (R3 predicted clearance against d_pc) frame is recorded as `clearance_within_k_sigma`, and a borderline M frame as `speed_near_v_min`. R1's image gap has no σ, so it is borderline only when it equals k_img, and it uses the same label. `footprint_orientation_unknown` is carried from `pair_series` (AR-35 item 3).
  5. **Single-camera events.** `grouping_algorithm_version = single_camera_v1`. `join_sequence` holds the JCS text of each member's natural key. Events are listed by scenario, then in the §7 order. A null `t_onset_tl_s`, `t_end_tl_s` or `minclr_ev_m` has reason `not_observable`. An `unverified` assumption has `evidence_ref` null with reason `not_applicable`.
  6. **Schema and interfaces.** `episode` gains `e_assessed` and `ca_observed` (bool, not nullable). `rule_configuration.classification` gains `k_c_turn` (f64). `flag_frames` takes the S1 coverage segments, so that R5 windows do not cross coverage breaks.
- **No meaning effect:** items 1, 4, 5 and 6 are representation. Items 2 and 3 implement the contract text, using precedence where the two documents conflict. **Review flag:** items 2 and 3(a). **Files/tests:** `events/engine.py`, `events/labels.py`, `events/providers.py`, `events/candidates.py`, `schema/tables.py`; `tests/events/test_t9.py`, `tests/events/test_engine_part_a.py`, `tests/substrate/test_part_b.py::test_t9_1_keeps_the_t8_2_span_requirement`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 3(b)–(d), 4, 5 and 6 ACCEPTED. Item 2 ACCEPTED, superseded by T10.1. Item 3(a) ACCEPTED, made normative by T10.2.

## CR-009 (2026-11-12) — T9 edge readings and episode exposure fields (T-09)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-09 (S5 artifact).
**Contract sections:** E-1.2.1 §5.6 (episode "Exposure (always populated)", `support_detected_frac`, `event_count_summary.label`), §6 lifecycle step 4; Appendix T T8.3, T9.1–T9.4.
**Meaning-affecting:** yes. Every item changes a measured value, a flag or a count.

**Part 1. Two readings each; the first reading is implemented provisionally and pinned by a test. None of them occurs in an Appendix N fixture.**

| # | Question | Implemented reading | Other reading |
|---|---|---|---|
| 1 | T8.3 computes the closing rate "over the T8.2 window". Does T9.1's shift apply to it (inside the pair's run of measured frames)? | No. T9.1 corrects "the velocity window", so the T8.3 window stays centred and needs ≥ 3 measured frames | Yes, shifted inside the run of measured frames. This changes values at run ends, and so the T9.5 sign test and `exp_closing_rate_max_mps` |
| 2 | R5 at a frame where the object belongs to no run (for example, the person is lost inside a bridged gap) | Unknown. The window cannot be shifted into a run, so the required values are null | Use the centred window, with a and b taken on either side of the gap |
| 3 | Contact cue when R5 is disabled. T9.3 has no condition, but T9.4 says such a configuration "cannot produce … CT through evasive action" | The cue is still evaluated (literal T9.3), so CT remains possible | No cue, so contact is never `suspected` |
| 4 | Over which frames borderline frames set the episode's `borderline_flags` | I⁺, by lifecycle step 4 ("assess attributes over I⁺") | I, the frames that set P_ep, X_ep and C_ep |

**Part 2. Undefined; blocks the S5 artifact.** §5.6 names the fields below and Package E gives only types. The episode row cannot be written without them, because the exposure fields are not nullable.

| # | Field | Proposed definition |
|---|---|---|
| 5a | Interval of the `exp_*` fields | I⁺ (lifecycle step 4; T9.2 already uses I⁺ for `exp_evasive_score`) |
| 5b | `exp_t_in_band_detected_s`, `exp_t_in_band_inferred_s`, `exp_t_clearance_unknown_s` | The S4 `exposure_profile` definitions, restricted to I⁺ and using the configuration's `band_scheme_id` |
| 5c | `exp_speed_at_ca_mps` | Forklift `speed_mps` at CA (C.1 §3.4 says "forklift speed at closest approach"); null if CA or the speed is null |
| 5d | `exp_closing_rate_max_mps`, `exp_ttca_min_s` | Maximum closing rate and minimum non-null TTCA over I⁺; null if there are none |
| 5e | `exp_visible_frac` | Support where both objects are visible or partially_visible (T8.6) ÷ total support, over I⁺ |
| 5f | `duration_*_s`, `support_detected_frac` | Support-based durations by pair evidence class (§3.4) over I; `support_detected_frac` = detected ÷ (detected + inferred + insufficient) |
| 6 | `event_count_summary.label` other than `all` | Count events whose `summary_label` equals the label, so counts partition `all`. The alternative is to count events with that `lbl_*` flag set, which overlaps and includes IE |

**What proceeds meanwhile:** T9.1–T9.9 in full; flag_series rows; episodes, including durations over I and `exp_evasive_score`; discarded episodes; single-camera candidate events; `label = all` counts. T-12 does not use any item above.
**Decision:** superseded by T10 (Appendix T, contract E-1.2.8; D-10 and D-11, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.8

## AR-39 — Association and matching details (T-12)
- **Gaps and choices:**
  1. **Ambiguous rivals (A5.2 step 4).** "Within ε_amb" is the absolute difference of the quantized IoUs, and the rival must itself have IoU ≥ *iou_cm*. An unassigned rival (FX-ID-6's p2) is recorded as `ambiguous` with the assigned counterpart, not as `missed_reference` or `unmatched_system`, because "ambiguous frames count in neither matched nor unmatched time".
  2. **Frame-level solver.** The solver uses the quantized IoU on canonically sorted inputs, exactly as A5.2 states. N4's composite tie weight applies to event matching only. Sorting makes the frame assignment deterministic (CT-ID-A2).
  3. **Label groups.** A system event belongs to G1 if it has O, H or PC, to G2 if it has NM, UD or CT, and to `any` always (EV-M12 defines G2 as NM/UD/CT). `ref_interaction` has no label field, so a reference's groups are an input set by the reference producer (CV-SIM or annotation). `any` includes every reference.
  4. **Abstained events** produce no match record. Their effect is the `abstained_miss` class. "Overlap" for `duplicate_alert` and `abstained_miss` is temporal IoU > 0, with no pair condition, as N4 states.
  5. **`reference_class`** on every match record, false alerts included, is the class of the window's references. The field is not nullable.
  6. **References that are not assessable** get `unobservable_reference`. A system event on such a reference stays a `false_alert`, as N4 literally states. EV-M10 counts it separately (T-14).
  7. **Out of scope here.** FX-ID-8's `primary_stage = perception` is error attribution (N9, T-14). CM-01 for FX-ID-3/4 is T-14; T-12 tests its numerator (the matched support).
- **No meaning effect:** items 1, 2, 3 and 5 are representation or follow the A5.2/N4 text literally. Items 4 and 6 apply N4 literally. **Review flag:** items 3 and 6. **Files/tests:** `evaluation/association.py`, `evaluation/matching.py`; `tests/evaluation/test_t12.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 2, 4 and 5 ACCEPTED. Item 3 ACCEPTED: the matcher takes a mapping ref_event_id → set of label groups as an input, not a schema field. The mapping is part of the match-run inputs hash; for simulator-converter references, the converter produces it. Item 6 ACCEPTED for M0: N4 is kept literal, so EV-M2 and EV-M7 are unchanged. No `unobservable_reference` classification is added beyond what exists. At T-14, when EV-M10 is built, raise a CR with the options.

## CR-010 (2026-11-12) — Abstention and coverage denominators in the event metrics (T-12)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-12 (no test in its "Done when" depends on these items).
**Contract sections:** F.1 Appendix N4 (classes, cᵢ, EV-M3/M5/M8/M11); E-1.2.1 §9.2.
**Meaning-affecting:** yes. Each item changes an EV-M value. The first reading is implemented provisionally and pinned by a test.

| # | Question | Implemented reading | Other reading |
|---|---|---|---|
| 1 | What is an "abstained (IE-only)" system event? | IE and no label of the evaluated group. Every event has O, H or PC (CL-INV-02), so a literal "IE is its only label" never occurs. In G1 and `any` nothing abstains; in G2 an IE event without NM/UD/CT abstains | Any event with IE abstains in every group, as EV-M3 counts "abstained episodes" |
| 2 | cᵢ, "assessable references receiving a non-abstained decision" | cᵢ = aᵢ − abstained_missᵢ. A plain miss is a decision ("nothing here"), so EV-M4 = 1 − EV-M5 | cᵢ = assessable references overlapped by a non-abstained system event |
| 3 | P90 in EV-M8 | Linear interpolation between order statistics (Hyndman–Fan type 7, numpy's default) | Another quantile definition, for example nearest rank |
| 4 | Weighting of EV-M5 and EV-M11, which N4 writes without Σwᵢ | The same weighted-ratio form as the other metrics (w = 1 gives the printed formula) | Always unweighted counts |

**Decision:** superseded by T10 (Appendix T, contract E-1.2.8; D-10 and D-11, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.8

## AR-40 — Representation details of the S5 artifact under T10 (T-09)
- **Gaps and choices:**
  1. **Nullable fields.** `episode.support_detected_frac` and `episode.exp_visible_frac` become nullable, because T10.5 gives each a null case (`not_applicable` when the denominator is 0) and §5.6 had listed them as non-nullable.
  2. **`label_stability_frac`** is null at S5 with reason `not_computed_by_config`. MR-08 (F.1) computes it at evaluation, across configurations.
  3. **The `rule_configuration` record** lists R1, R2, R3 and R5, each with its `enabled` flag and parameters, whether enabled or not. Without this, an R1-only configuration's S5 output would depend on `d_p`, `v_min` and `d_pc` (read by T10.4) while its configuration ID did not. The ID is the content address of that record. `preregistration_ref` is null (`not_applicable`, exploratory), and `version_label` is null (`not_applicable`) when absent.
  4. **`episode.continuation_of_nk`** (lifecycle step 6) links an episode that starts at the first frame of a POW whose `continuation_of` POW has an episode ending at that POW's last frame. Otherwise it is null (`not_applicable`).
  5. **Null reasons.** `minclr_sigma_m` copies the null reason of `clearance_sigma_m` at the minimum frame. `minclr_m`, `minclr_frame` and `closest_approach_frame` are null with `not_observable`.
  6. **T10.3(b)** tests the pair evidence class: it is `insufficient` exactly when an object is insufficient or the frame is timing-uncertain (§3.4), which is the T10.3(b) condition.
  7. **The matcher** takes the label-group mapping `ref_event_id → groups` as an argument (Architect ruling on AR-39 item 3). A reference without an entry is refused with ERR-SPEC. The mapping enters the match-run inputs hash when the S8 artifact is assembled (T-14/T-16).
  8. **Count scopes.** S5 writes the processed recording and its timeline. An event's scope is its member episode's recording and timeline (its onset, T10.6).
  9. **Borderline comparisons.** The R1 image-gap equality (|gap − k_img| ≤ 0) uses the same 1e-9 numerical tolerance as the other borderline comparisons.
- **No meaning effect:** items 1, 2, 3, 5, 6, 7 and 8 are representation, or restate T10. **Review flag:** items 4 and 9. **Files/tests:** `events/s5.py`, `events/engine.py`, `events/providers.py`, `evaluation/matching.py`, `schema/tables.py`; `tests/events/test_t10.py`, `tests/evaluation/test_t12.py::test_ar_39_item_3_label_groups_are_an_input_mapping`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** ACCEPTED in full. Item 3 (the review's item c): ACCEPTED; the record shape follows §5.2, and S5 output must not depend on a disabled provider's parameters (T11.1, CT-T11-02). Item 4 (item d): ACCEPTED; T-15 must carry `continuation_of_nk` into the OBX export and must not describe one episode count as one physical interaction. Item 9 (item i): ACCEPTED. Future ARs use one labelling scheme and cite the same labels in review flags.

## CR-011 (2026-11-12) — T10.4 bullets that read parameters of providers not enabled   status: CLOSED

**Raised by:** implementation agent. **Task:** T-09 (non-blocking: borderline flags never change a frame flag, a label or review_route).
**Contract sections:** Appendix T T10.4; E-1.2.1 §5.2 (`rule_configuration.providers` params).
**Meaning-affecting:** yes, for the reported `borderline_flags` only.

**Problem.** T10.4 conditions only the image-gap bullet on the P provider ("for a configuration whose P provider is R1"). The clearance (`d_p`), speed (`v_min`) and prediction (`d_pc`) bullets carry no condition. But `d_p` and `v_min` are R2 parameters and `d_pc` is an R3 parameter. In an R1-only configuration (BL-2), or a configuration without R3, those thresholds belong to providers that are not enabled. There are two readings:
(a) **Literal.** Apply every bullet in every configuration, using the configuration's values of `d_p`, `v_min` and `d_pc` even when their provider is disabled.
(b) **Apply each bullet only when its provider is enabled:** the clearance and speed bullets with R2, the prediction bullet with R3.
**Implemented meanwhile:** (a), the text as written, pinned by `test_ct_t10_06_clearance_against_d_p[R1]` and `test_ct_t10_06_speed_near_v_min[R1]`. AR-40 item 3 puts those parameters in the configuration ID under either reading.
**Decision:** superseded by T11 (Appendix T, contract E-1.2.9; D-12, 12 Nov 2026): reading (b), each bullet applies only when its provider is enabled.   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.9

## AR-41 — Mechanics of the Target B and paired bootstraps and the null cases of N5 estimators (T-13)
- **Gaps and choices:**
  1. **Target B.** "Stratified by data origin" is implemented as follows: in each origin, draw as many leakage groups as that origin has, with replacement. Every window of a drawn group enters with its own weight, once per draw. Origins and groups are sorted before the PCG64 draws, so input order cannot change the interval.
  2. **Percentile intervals** (Targets A and B, paired) use numpy's default linear method, as T10.7(c) does for EV-M8.
  3. **Paired comparison** uses the Target A scheme. Both configurations share each replicate's resampled windows, and the interval is that of R̂_a − R̂_b.
  4. **Null cases** (returned as None, to be stored as null `not_applicable`): Wilson with n = 0; Bland–Altman with n < 2; Cohen's κ with p_e = 1; Krippendorff's α with zero expected disagreement. For α, units with fewer than two values are not pairable, as Krippendorff's standard definition states.
- **No meaning effect:** each choice applies the N5 definition mechanically. Item 1 is the standard stratified cluster bootstrap. **Review flag:** item 1. **Files/tests:** `evaluation/estimators.py`; `tests/evaluation/test_t13.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 2 and 4 (the review's items a, b, d) ACCEPTED. Item 3 (item c): REVISED by T11.2; the paired comparison follows the estimand of the compared metric.

## CR-012 (2026-11-12) — `v_min` and `w_e` are read outside the provider that owns them (T11.1)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-09 follow-up (T11 conformance). Non-blocking for M0 fixtures.
**Contract sections:** Appendix T T11.1 ("Parameters of a disabled provider … play no role in S5 output"), T9.2, T9.6, T10.3(c); E-1.2.1 §6.0, §5.2; Package F §3.
**Meaning-affecting:** yes. The answer decides which configuration changes may change S5 output.

**Problem.** T11.1 says a disabled provider's parameters play no role in S5 output, and CT-T11-02 tests that. Two parameters are read outside their provider:
1. **`v_min`.** §6.0 makes it R2's M threshold, and T11.1 lists the speed bullet under R2. But T9.2 also reads it in R5: the turn criterion is evaluated "only if the person's speed ≥ v_min". In a configuration with R1 as the P provider (R2 disabled) and R5 enabled, changing `v_min` can change E, K and the labels.
2. **`w_e`.** Package F §3 lists it with R5's thresholds, and the `rule_configuration` record (AR-40 item 3) files it under R5. But the contact cue (T9.3), which T10.3(c) requires whether or not R5 is enabled, and W_CA (T9.6) both read it. In a configuration with R5 disabled, changing `w_e` can change the contact state.

The code reads the single values in `RuleParams` and `Params` (`providers.r5_rates`, `engine._episode`). CT-T11-02 therefore tests only parameters that one provider owns alone: `d_p`, `k_img`, `d_pc`, `tau`, `e_turn`, `e_acc` and `e_dec`.

**Options.**
(a) `v_min` and `w_e` are shared classification parameters. They are recorded outside the provider entries, and T11.1's statement then holds for every parameter a provider owns. This is a representation change to the record and changes no value.
(b) Each use gets its own parameter (for example an R5 `v_min_turn`, and a contact-window length separate from R5's `w_e`). This adds parameters to §14 and to the TEST-ONLY table.
(c) Keep the record as it is, and amend T11.1 to name `v_min` and `w_e` as read outside their provider.
**Agent's recommendation:** (a). Nothing changes in the code until a decision is made.
**Decision:** superseded by T12 (Appendix T, contract E-1.2.10; D-13 to D-17, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.10

## CR-013 (2026-11-12) — How a system event on an unobservable reference is counted (EV-M10)   status: CLOSED

**Raised by:** implementation agent, as the Architect's ruling on AR-39 item 6 requires. **Task:** T-14.
**Contract sections:** F.1 Appendix N4 (classes; EV-M2, EV-M7, EV-M10); E-1.2.1 §9.2; `match_record.match_type`.
**Meaning-affecting:** yes. It changes EV-M2 (precision), EV-M7 (false-alert burden) and EV-M10.

**Problem.** N4 classes every unmatched system event that does not overlap a matched reference as `false_alert`, including an event that falls on a reference marked unobservable (not assessable). EV-M10 counts "system decisions on unobservable references", but N4 does not say whether such an event is also a false alert, nor what "on" means. Following AR-39 item 6, the code keeps N4 literal (`false_alert`), and no new match class has been added.

**Options.**
(a) **Keep N4 literal (current).** The event is a `false_alert` in EV-M2 and EV-M7, and is also counted in EV-M10. A decision the reference cannot judge then counts against precision.
(b) **Exclude from EV-M2 and EV-M7 without a new class.** The event stays out of sᵢ and fᵢ and is counted only in EV-M10. Its `match_record` would need a type: either `unobservable_reference` with `system_event_id` set (reusing the existing class), or no record at all with a separate count.
(c) **New match class** (for example `decision_on_unobservable`). The Architect said not to add this now; it is listed for completeness.
For (a), (b) and (c), "on" also needs a definition: temporal IoU > 0 (as for `duplicate_alert`) or IoU ≥ *iou_m*; and the same pair (A5.2) or any pair.
**Agent's recommendation:** (b), reusing `unobservable_reference` with `system_event_id` set, "on" as IoU > 0 with the same pair. A decision on footage the reference cannot judge is not evidence of a false alarm.
**What proceeds meanwhile:** nothing changes. EV-M10 is not computed until this is decided.
**Decision:** superseded by T12 (Appendix T, contract E-1.2.10; D-13 to D-17, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.10

## CR-014 (2026-11-12) — Oracle-factorial decision rule and "tests conflict" in error attribution (T-14)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-14 (CT-E-22, FX-16).
**Contract sections:** F.1 Appendix N9; E-1.2.1 §9.4; Appendix T CT-E-22, FX-16, VR-E-061; CLAUDE.md "Documents and precedence" item 4.
**Meaning-affecting:** yes. It decides `primary_stage`, `secondary_factors` and `attribution_status`.

**Problem.**
1. N9 ends: "On synthetic data, oracle substitution (2³ combinations of perception, tracking and geometry) assigns `verified_*` as specified in D.1 §7.2." The rule itself (which resolving set gives which status, and which stage becomes primary) appears only in D.1 §7.2, which is in `docs/methodology/`. CLAUDE.md says never to implement from that folder, while Appendix N, the highest-precedence document, cites it. D.1 §7.2 reads: "If one or more single-stage substitutions resolve it, `primary_stage` = earliest such stage; other resolving stages become secondary; status `verified_oracle_single`. If only a combination resolves it, `primary_stage` = earliest stage in the smallest resolving set; the rest secondary; status `verified_oracle_joint`." It also defines "resolved" as "it disappears", meaning the miss or false alert is no longer present in the substituted run. It does not say what happens when no combination resolves the error, or when two smallest resolving sets tie.
2. N9's diagnostic rule says "If no test fails, or tests conflict, the result is `unresolved`". "Conflict" is not defined.
**Options.** For 1: (a) the Architect confirms that N9's citation makes the quoted D.1 §7.2 rule normative, and states the two missing cases (no resolving set; tied smallest sets); or (b) the rule is restated in Appendix T. For 2: (c) define conflict, for example a later test failing while an earlier one could not be evaluated; or (d) delete the clause, so that only "no test fails" gives `unresolved`.
**Agent's recommendation:** (a), with "no resolving set → `unresolved`" and "ties → the set whose earliest stage is earliest in pipeline order"; and (d).
**What proceeds meanwhile:** the 2³ substitution runner (which combinations resolve the error), the N9 diagnostic tests in pipeline order with primary and secondary stages, and the VR-E-061 guard. The step from oracle outcomes to a `verified_*` status, and therefore CT-E-22, waits. Until then "tests conflict" is not detected: only "no test fails" gives `unresolved`.
**Decision:** superseded by T12 (Appendix T, contract E-1.2.10; D-13 to D-17, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.10

## AR-42 — Attribution rule inputs and the match-run inputs digest (T-14)
- **Gaps and choices** (numbered items only, as the Architect asked):
  1. **Rule 2 for a false alert.** N9 rule 2 is written for a miss: "no system detection … within ±*n_miss* frames of the reference closest-approach frame". A false alert has no reference closest-approach frame. For a false alert, rule 2 fails when one of the event's system tracks has no reference object of its class with IoU ≥ *iou_cm* within ±*n_miss* frames of the event's own CA frame. This is the reading stated in F.1 A5.2 FX-ID-8 ("no reference person within *n_miss* frames"), and FX-ID-8 then gives `perception`, as expected.
  2. **Rule 1, "coverage there is not usable".** `usable` and `usable_degraded` count as usable. T7 keeps `usable_degraded` time in usable coverage, with a reason.
  3. **Match-run inputs digest.** SHA-256 over the JCS form of a match run's inputs: references, system events, the label-group mapping, the label group, *iou_m* and the reference class. Lists are sorted by JCS, so input order does not change it. The S8 artifact will record it when assembled (T-16). The contract defines no fields for the evaluation configuration (`evc`), so the digest is not yet stored in a record.
  4. **Rule-test results.** `rule_test_results` maps each evaluated stage to `fail`, `pass` or `not_evaluated`. `not_evaluated` covers tests that cannot run, such as linkage before M2, or geometry without reference geometry. A stage that is not evaluated never becomes primary or secondary.
  5. **Rule 4 (geometry) and rule 5 (event reasoning)** take their comparisons as inputs: per frame, whether the decision differs, the clearance error, σ, and M from the system and from the reference; and whether each run triggers. The comparisons need reference geometry, which arrives with the M1a adapters (T-18, T-21).
- **No meaning effect:** items 3, 4 and 5 are representation. Item 1 applies the F.1 FX-ID-8 text, and item 2 applies T7. **Review flag:** items 1 and 2. **Files/tests:** `evaluation/attribution.py`, `evaluation/matching.py`; `tests/evaluation/test_t14_attribution.py`, `tests/evaluation/test_t12.py::test_label_group_mapping_is_part_of_the_match_run_inputs_digest`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 2, 4 and 5 ACCEPTED. Item 3 ACCEPTED, with a storage rule: `evc` (prefix `evc`, AR-16) is defined as a content-addressed configuration record holding iou_m, iou_cm, ε_amb, n_miss, B, seed, reference_class and label_group_mapping_sha256, so a changed mapping changes the S8 specification. This is representation under the agent's AR authority.

## CR-015 (2026-11-12) — Completeness metrics CM-05 to CM-08 and CM-10 are not fully determined (T-14)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-14 (no test in "Done when" depends on these metrics).
**Contract sections:** F.1 Appendix N6; F.1 A5.2 "Use downstream".
**Meaning-affecting:** yes. Each item changes a CM value.

| # | Metric | Gap | Readings |
|---|---|---|---|
| 1 | CM-05, CM-08 (denominator s(POW frames)) | "Each metric is computed on both bases", but these denominators are system-side | (a) POW frames in the basis only (detected; or detected + inferred). (b) All POW frames on both bases, with the basis filtering only the numerator |
| 2 | CM-06 | "Σ over bands \|AI − reference time-in-band\| per pair; report bias and LoA" names no interval or band scheme, and does not say whether the per-pair Σ is the Bland–Altman unit | (a) Per reference pair over the window, using the configuration's band scheme; Bland–Altman over pairs of the signed per-band differences. (b) The per-pair Σ of absolute differences as the only output |
| 3 | CM-07 | A5.2 says "Number of **tracks** matched to an identity's co-presence interval"; N6 says "Number of **POWs** covering a reference pair's co-presence interval". Both are F.1, at the same precedence | (a) N6 (POWs per pair). (b) A5.2 (tracks per identity). (c) Both, as two strata |
| 4 | CM-10 | On a reference co-presence frame with no system pair-frame (no POW covers it), is the pair-frame "insufficient"? | (a) Yes: missing evidence counts as insufficient. (b) No: only POW frames with pair evidence class `insufficient` count |
| 5 | Aggregation | N6 gives no aggregation across identities or pairs; F.1 A5.2 FX-ID-3 states CM-01 per identity | Per identity or pair (implemented, `stratum`), and/or pooled Σnum ÷ Σden per window |

**What proceeds meanwhile:** CM-01, CM-02 (with the moving-frame restriction as a stratum), CM-03, CM-04 and CM-09, per identity or pair and on both bases. FX-CM, FX-ID-3 and CT-F-03 pass.
**Agent's recommendation:** 1(a), 2(a), 3(c), 4(a), 5 both.
**Decision:** superseded by T12 (Appendix T, contract E-1.2.10; D-13 to D-17, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.10

## AR-43 — Completeness record details (T-14)
- **Gaps and choices** (numbered items only):
  1. **The basis applies to system evidence.** On the `detected` basis, a matched frame counts only if the matched track's point (CM-01/02/09) or the POW pair-frame (CM-03/04) is `detected`. Reference-side denominators are the same on both bases. CM-09 counts only inferred frames, so its `detected`-basis value is null with `not_applicable`.
  2. **`completeness_record.config_id`** is null with `not_applicable` for track-level completeness, which no rule configuration produces.
  3. **Units.** CM-09 counts track-frames, so two inferred tracks on one frame count twice. CM-01 and CM-02 are reported per reference identity, and CM-03 per pair, with the identity or pair in `stratum`. Pooled values wait for CR-015 item 5.
  4. **CM-02's "also restricted to reference moving frames"** is a second record with stratum `{"reference_motion": "moving"}`. Which frames count as moving is an input: reference motion per frame.
- **No meaning effect:** items 2 and 4 are representation. Items 1 and 3 follow N6's text ("matched" by frame, support by basis). **Review flag:** items 1 and 3. **Files/tests:** `evaluation/completeness.py`; `tests/evaluation/test_t14_completeness.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1–4 ACCEPTED. Pooled values follow T12.4.

## CR-016 (2026-11-12) — Gaps in the section 9.6 fitness status rule (T-14)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-14 (no M0 fixture reaches these cases).
**Contract sections:** E-1.2.1 §9.6; Appendix T FT-01 to FT-04.
**Meaning-affecting:** yes. These decide `measurement_status`.

| # | Gap | Implemented meanwhile | Other reading |
|---|---|---|---|
| 1 | No status covers this case: no criterion `met` or `inconclusive`, not all `not_assessable`, and every `not_met` is a repeatability or robustness criterion | Refused with ERR-SPEC; no status is stored | `experimental`; or `unsuitable_under_tested_conditions` for any not_met |
| 2 | `technically_validated` needs "real data": does `real_staged` count? | Only `real_natural` (the stricter reading) | `real_natural` and `real_staged` |
| 3 | "comparability is characterized" | At least one comparability criterion whose decision is not `not_assessable` (stricter) | A comparability metric result exists, with or without a registered criterion |

**Decision:** superseded by T12 (Appendix T, contract E-1.2.10; D-13 to D-17, 12 Nov 2026).   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.10

## AR-44 — Fitness-engine representation details (T-14)
- **Gaps and choices** (numbered items only):
  1. **Error code.** Violations of FT-02, FT-05, FT-06, FT-08 and FT-09/11 raise ERR-INVARIANT; §10.3 has no fitness-specific code.
  2. **Rule semantics.** `ci_upper_le`: met if ci_high ≤ target, not_met if ci_low > target, else inconclusive. `ci_lower_ge`: the mirror. `abs_bias_ci_within`: the target is a half-width; met if the interval lies inside [−t, t], not_met if it lies wholly outside, else inconclusive. `exact_equal`: compares the stored value. `flip_rate_le`: uses the interval when stored, else the value. A rule that needs an interval when none is stored gives `not_assessable`.
  3. **Partition and test time.** A metric result carries its partition as context, because `metric_result` has no partition field. The time of the first test-partition evaluation is supplied from the execution record, never the clock (AR-7 review), and a criterion must be frozen strictly before it.
  4. **Override ranking.** Ranks run not_yet_assessable < unsuitable_under_tested_conditions < experimental < technically_validated. A stored status different from the rule's needs an override with `downgrade_only` and a lower rank. A downgrade to unsuitable still needs a recorded not_met (FT-03).
  5. **`failing_interval`** is the interval of the first failing accuracy or completeness criterion, in criterion-ID order.
- **No meaning effect:** items 1, 3 and 5 are representation. Item 2 restates §9.6's three outcomes for each rule enum. **Review flag:** items 2 and 4. **Files/tests:** `evaluation/fitness.py`; `tests/evaluation/test_t14_fitness.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 3, 4 and 5 ACCEPTED. Item 2 REVISED for `flip_rate_le`: without a stored interval the decision is not_assessable, except `exact_equal` and the full-enumeration metrics MR-01, MR-08, MR-09 and MR-12, which use the degenerate interval [v, v]. MR-10 needs an interval.

## CR-017 (2026-11-12) — Support basis of CM-10 (T12.4)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-14 (T12.4 conformance). Non-blocking.
**Contract sections:** Appendix T T12.4 ("All support is … by basis as in AR-43 item 1"; CM-10); AR-43 item 1.
**Meaning-affecting:** yes, for CM-10 on the `detected` and `detected_plus_inferred` bases.

**Problem.** T12.4 applies the basis of AR-43 item 1 to all support: system evidence counts only if its class is in the basis. CM-10's numerator is the reference co-visible frames on which the pair's POW has an `insufficient` pair-frame. `insufficient` belongs to neither basis, so applying the basis to the numerator would make CM-10 zero on both bases, whatever the data.
**Readings.** (a) The basis does not apply to CM-10, and its value is the same on both bases. (b) The basis filter applies literally, which makes CM-10 identically zero.
**Implemented meanwhile:** (a), the only reading under which CM-10 measures anything. It is pinned by `test_cm_10[detected]` and `test_cm_10[detected_plus_inferred]`. Nothing else depends on it.
**Decision:** superseded by T13 (Appendix T, contract E-1.2.11; D-18, 12 Nov 2026): CM-10 is basis-independent, stored with support_basis = detected as a key placeholder.   **Approver:** Research Owner, on the Architect's definitions.   **Resulting contract version:** E-1.2.11

## AR-45 — Representation details of the T12 conformance (T-14)
- **Gaps and choices** (numbered items only):
  1. **Single sources (T12.1).** `S5Config` carries the `substrate_config` record; its content-addressed ID goes into the rule configuration. S5 refuses with ERR-SPEC a runtime `v_min`, τ or `w_e` that differs from its single source, and an S4 artifact not built with that `substrate_config`. In the classification block, `w_e` is stored as `w_e_s` (unit suffix, AR-13).
  2. **EV-M10 table (T12.2).** Totals are given per decision and per `decision:label`, as RES-weighted Horvitz–Thompson sums with unweighted sums alongside, and the T12.2 interpretation note is attached to the table.
  3. **Completeness units (T12.4).** CM-05 and CM-08 count POW frames, so a frame covered by two POWs counts twice. A POW frame is attributed to at most one pair, because association is one-to-one per frame. When S8 assembles records, CM-06 and CM-07 map into `completeness_record` as follows: value = numerator = the per-pair sum (CM-06, seconds) or the POW count of one interval (CM-07), with denominator 1.0; stratum = the pair, plus the interval's start frame for CM-07.
  4. **Reference clearance for CM-06** is an input. The reference adapter (T-18) computes it from `ref_geometry` with the S4 clearance function, footprint prior and yaw rule.
  5. **`evaluation_config`.** Fields `iou_m`, `iou_cm`, `eps_amb`, `n_miss`, `bootstrap_B`, `seed`, `reference_class` and `label_group_mapping_sha256`; the hash is SHA-256 of the JCS form of {ref_event_id: sorted groups}. `version_label` is nullable.
  6. **Oracle diagnostics (T12.3.4).** The disagreement between rule-test and oracle primary stages, and the non-monotone resolving sets, are returned beside the attribution record for the milestone report. They are not stored in `error_attribution`.
  7. **`failing_interval` for a value-only `not_met`** (`exact_equal`, or a full-enumeration metric) is the degenerate interval [v, v].
  8. **Prerequisites (T12.3.5).** Rule 4 is not evaluated when rule 3 fails ("association is correct"). Rule 5 is not evaluated when rule 3 or rule 4 fails ("given correct flags").
- **No meaning effect:** items 1, 2, 4, 5 and 6 are representation. Item 3 follows the T12.4 definitions, item 7 the T12.5 failing-interval rule, and item 8 N9's own wording. **Review flag:** items 3, 7 and 8. **Files/tests:** `events/s5.py`, `evaluation/matching.py`, `evaluation/event_metrics.py`, `evaluation/attribution.py`, `evaluation/completeness.py`, `evaluation/fitness.py`, `schema/tables.py`; `tests/events/test_t12_shared_parameters.py`, `tests/evaluation/test_t12_*.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1, 2 and 4–8 (the review's a, b, d–h) ACCEPTED. Item 3 (c) ACCEPTED, with the label rule: CM-06 and CM-07 values are labelled "sum" and "count" in reports, never "proportion" (T13.3).

## AR-46 — OBX file format and report wording mechanics (T-15)
- **Gaps and choices** (numbered items only):
  1. **Wording errors.** A report that breaks a wording rule is refused with ERR-INVARIANT; §10.3 has no wording code.
  2. **Report construction.** Reports are Markdown assembled only from fixed section builders, then linted. Fixed sentences written by the builders (the banner, the RV-04 caveat, the EV-M10 note) are exempt from the linter.
  3. **Template guard.** A fixture template on a research export is refused, as well as a research template on a fixture export (EXP-3 "both directions"; EXP-4).
  4. **Wording rules.** W1: no "collision". W2: "near miss" only as "candidate near miss". W3: no claim of observed, confirmed or occurred contact (VR-E-034 pattern, plus "contact occurred/detected/happened"). W4: "validated" only as `technically_validated` or "empirically validated (scope)". W5: no "physical interaction(s)" and no "<number> interactions" (Architect ruling on AR-40 item 4). W6: no safety or risk score, ranking, OSHA, NAICS or establishment rate. RV-04: inside "Implementation conformance", no "hazard identification", "identifies hazards", "construct" or "validity".
  5. **OBX files.** Each table is one JCS file `{"metadata": {export_class, research_use, table, part, contract}, "rows": [...]}`, with rows sorted by JCS. `data_dictionary.json` holds each exported table's JSON Schema (the OBX schemas). `manifest.json` lists the §11 parts and the SHA-256 of every file. Fixture exports go under `fixture/`, research exports under `research/`. The §11 parts map to tables as listed in `export/obx.py`.
  6. **Forbidden content in values (CT-E-27).** String values, including map keys, are scanned for the VR-E-041 name fragments as case-insensitive substrings.
  7. **VR-E-040 zero-exposure clause.** A row with `ai_activity_state = observed_no_detection` must not carry an exposure field (`exp_*`, `t_in_band*`) equal to zero.
  8. **Status board.** "Empirically validated" needs a scope and data origin `real_natural` or `real_staged`; otherwise it is refused.
  9. **CT-E-26 and CT-E-28** are asserted at export level: the FX-12 E2 records and a lineage chain S0 → S5 → S8. The end-to-end run is T-16.
- **No meaning effect:** items 1, 2, 3, 5 and 9 are representation. Items 4, 6, 7 and 8 enforce existing rules (CLAUDE.md wording, VR-E-041, VR-E-040, the three statuses) mechanically. **Review flag:** items 4, 6 and 7. **Files/tests:** `export/obx.py`, `export/report.py`; `tests/export/test_obx.py`, `tests/export/test_report.py`. **Reverse:** edit the named functions.
- **Architect review (12 Nov 2026):** items 1–3, 5, 6, 8 and 9 (the review's a–c, e, f, h, i) ACCEPTED. Item 4 (d) ACCEPTED, with pass-case tests for the linter. Item 7 (g) ACCEPTED, extended: the zero-exposure check also covers rows with `ai_activity_state = not_evaluated` (CD-03), with a failing and a passing test for each state.

## AR-47 — M0 integration run details (T-16)
- **Gaps and choices** (numbered items only):
  1. **Integration clip.** One clip fixture, `fx_m0_pipeline` (50 frames, 100 ms apart, 64 × 64 px), is added to the clip generator so that the pipeline decodes a real container carrying the Appendix N2 G2 scene. Every existing clip is byte-identical (manifest diff: one added entry). The scene's oracle boxes lie inside the frame and clear of the border.
  2. **Specification provenance.** Each stage's `code_commit` is the git HEAD, and `environment_digest` is the SHA-256 of `requirements.lock`. Artifact IDs therefore belong to one commit and one environment. Both clean-clone runs used the same commit (`e6072ef`) and environment.
  3. **Null reasons.** The pipeline fills a missing null reason of a nullable S8 column with `not_applicable` when the value is null, for example the CI fields of a one-window metric result with `interval_method = none`.
  4. **E2 at M0.** No E2 measurement stage exists at M0. The S4-E2 artifact holds the revised FX-12 records (load_state and one e2_occupancy_profile), built and exported through the same builder and validators, so CT-E-26 runs through artifact building, lineage and export, not through E2 measurement.
  5. **CV-SIM mapping.** `converter.label_group_mapping` derives each `ref_interaction`'s label groups from the simulator truth's labels (G1 for O/H/PC, G2 for NM/UD/CT), as the Architect's ruling on AR-39 item 3 requires.
  6. **M0 configuration IDs.** The oracle, decode, geometry, footprint, band-scheme, substrate, rule and evaluation configurations are content-addressed records with `version_label = TEST-ONLY`, built from the TEST-ONLY parameters fixture. The fitness scope has no registered criterion, so its status is `not_yet_assessable` (FT-04).
- **No meaning effect:** fixture and run representation only; no measured value changes. **Review flag:** items 2 and 4. **Files/tests:** `pipeline/m0.py`, `fixtures/clips.py`, `validation/converter.py`; `tests/pipeline/test_m0.py`, `tests/clips/test_clip_fixtures.py`. **Reverse:** remove the clip and the pipeline module.
- **Architect review (12 Nov 2026, G-M0):** ACCEPTED as written (D-19).

## CR-018 (2026-11-12) — R4 (TTC/PET) and configurations BL-1 to BL-6 are not defined computably (T-19)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-19 (WP-06b). **Contract sections:** E-1.2.1 §6.0 (C_by_R4 row; "R1-only configurations (BL-2)"); Appendix T T8 (constant-velocity prediction, ttca), T11.1 and T12 (R4 parameters ttc_max, pet_max); Package F WP-06b (plan only).
**Meaning-affecting:** yes. Each item below changes C flags, episodes and labels, and the BL mapping decides which providers each compared configuration enables (primary comparisons BL-2 vs BL-3 and BL-3 vs BL-6).

**What the contract says.** R4: "Time-to-collision < ttc_max **or** post-encroachment time < pet_max, from constant-velocity footprint paths. Unknown when uncalibrated." The configurations BL-1 to BL-6 are named in Package F and defined only in the Package D baselines table: BL-1 detection only, frame co-presence, no tracking; BL-2 R1; BL-3 R2; BL-4 R3; BL-5 R4; BL-6 R6 + contact assessor. Package D is methodology and must not be implemented from. Package F gives test values ttc_max = 1.5 s, pet_max = 1.0 s.

| # | Gap | Readings that give different numbers | Proposed definition |
|---|---|---|---|
| 1 | TTC | (a) earliest time in [0, τ] at which the constant-velocity predicted footprint clearance (the R3 / T8 prediction, same footprints) is ≤ 0; (b) the same without the τ bound; (c) centre-point TTC (distance / closing rate) | (a). TTC = 0 if clearance ≤ 0 at the frame. Found by bisection on [0, t_at_min] (the signed distance between convex footprints under linear relative motion is convex in t), tolerance 1e-6 s. No crossing within τ → TTC null, `C_by_R4` TTC part = 0 |
| 2 | PET | (a) predicted PET: the conflict area is the intersection of the two footprints' swept regions over [0, τ]; PET = time the second object first enters it − time the first object last leaves it; (b) observed PET from actual future trajectories (post hoc); (c) PET at the crossing point of the two centre paths | (a), to match "from constant-velocity footprint paths". Swept regions that do not intersect → PET null, PET part = 0. Simultaneous occupancy → PET = 0 |
| 3 | Unknown | (a) only when uncalibrated, as written; (b) also when no velocity is available (insufficient history), as R3 | (b). Without velocity no path exists; otherwise R4 would report 0 where it cannot evaluate |
| 4 | BL-1 | No §6.0 provider computes "frame co-presence without tracking", and S5 runs on POWs built from tracks | Architect to define, or defer BL-1 to M1b |
| 5 | BL-2 to BL-6 provider sets | No contract text | BL-2 = R1; BL-3 = R2; BL-4 = R2 + R3; BL-5 = R2 + R4; BL-6 = R2 + R3 + R4 + R5 with the §6 labels ("with R6"). The contact cue applies whether or not R5 is enabled (T9.6, T10.3(c), T12.1), so "+ contact assessor" adds nothing |

**What proceeds meanwhile:** nothing in T-19. T-18 is independent.
**Agent's recommendation:** 1(a), 2(a), 3(b), 4 defer BL-1 to M1b, 5 as proposed, as Appendix T text.
**Decision:** (13 Nov 2026) 1(a), 2(a) as predicted PET `pet_pred`, 3(b), 4 BL-1 deferred to M1b, 5 as proposed; plus ttc_max, pet_max ≤ τ (ERR-SPEC) and no R4 borderline flag. Text: Appendix T section T15 (E-1.2.13), D-27.   **Approver:** Research Architect; Owner (by forwarding)

## AR-48 — How D-26 (exploratory real-data phase) is carried in records and reports   status: ACCEPTED (Architect rulings, 13 Nov 2026, item C)
- **Gap:** D-26 requires every real-data artifact and report to carry "exploratory; frame-quality rules provisional", and real-data results to be reported as experimental. No contract field holds such a note, and T12.5 lets real data reach technically_validated.
- **Options:** (a) add a note field to artifacts, which is a schema change; (b) carry the state through existing fields and fixed report text; (c) amend T12.5, which is a contract change.
- **Choice:** (b).
  1. Every S1 artifact on real footage is built with `rules_version = "rv2-real-provisional"` (was `rv2-provisional` before the D-25 ruling of 13 Nov 2026; AR-51), which is stored on every coverage segment and in the decode configuration record. Downstream artifacts reference S1 by ID.
  2. Reports: a manifest flag `exploratory` makes `report.render` print the fixed line first. A report whose manifest lists a real `data_origin` without the flag is refused (ERR-INVARIANT).
  3. Fitness: `fitness.exploratory_fitness_row` stores a real-origin technically_validated decision as experimental, with the §9.6 downgrade-only override {downgrade_only, rationale "D-26 exploratory phase…", actor Owner}. `check_record` accepts it (FT-01, FT-08). Lower statuses are never raised.
- **No meaning effect beyond D-26:** no measured value, label or denominator changes. The status change is a contract-permitted downgrade ordered by the Owner. The rv2 thresholds themselves are D-25 (provisional, under Architect review), not part of this AR.
- **Files/tests:** `decode/quality.py`, `evaluation/fitness.py`, `export/report.py`; `tests/evaluation/test_d26_exploratory.py`. **Reverse:** drop the manifest flag and the helper once the exploratory phase ends or the Architect writes T12.5 text.

## AR-49 — Representation details of R4 and the baseline configurations (T-19, T15)   status: ACCEPTED (Architect, 13 Nov 2026, incl. item 7: a contract-driven change under E-1.2.13, not an edited expected value)
- **Gaps and choices** (none changes a T15 value, flag rule, unit or horizon):
  1. **Numerical method for pet_pred bounds.** T15.2 fixes bisection (1e-6 s) for ttc; T15.3 names no method for t_in / t_out. Choice: the same bisection, between a golden-section minimiser of the shape gap (as T8.3 already uses) and the interval ends; touching counts as meeting. Each bisection returns its inside end (the side where the condition holds), so ttc is within 1e-6 s above the exact crossing. Considered: closed-form polygon/capsule intersection (more code, same values within tolerance).
  2. **Occupancy of A.** An object's footprint lies inside its own swept region, so it meets A = S_person ∩ S_forklift exactly when it meets the other object's swept region. The code tests that equivalent condition (no explicit intersection polygon). Same intervals by set identity.
  3. **Null reasons when R4 cannot be evaluated.** T15.7 gives `not_applicable` for computed-but-absent values only. When no prediction exists, `ttc_s` and `pet_pred_s` are null with `uncalibrated` (pair-frame `clearance_state = unmeasurable_uncalibrated`) or otherwise `not_observable`, as `clearance_m` and `ttca_s` do. R4 decides Unknown from calibration and the two speeds (T15.4), not from these reasons; a calibrated frame with both speeds but no ttc/pet is refused (ERR-INVARIANT).
  4. **When T15.5 is checked.** In every configuration, R4 enabled or not (the text is unconditional). Disabled-provider parameters still play no role in S5 output (T11.1; CT-T11-02 extended passes).
  5. **Ties in T15.3.** "First" uses exact comparison of t_in, forklift first on equality. When the starts are equal the intervals overlap, so pet_pred = 0 either way.
  6. **BL-1** is refused with ERR-SPEC "deferred to M1b"; BL-2 to BL-6 change only the provider switches (`events/baselines.py`); all parameter values come from the caller.
  7. **R4 in `rule_configuration`.** Always recorded, `{"provider_id": "R4", "enabled", "params": {"pet_max", "ttc_max"}}`, as T12.1 lists them. Consequence: every rule_configuration ID changes, including the M0 pipeline's (its S5 artifact and episode IDs differ from those printed in `reports/M0_report.md`, which stays a record of M0 under E-1.2.11). Two test expectations that listed the providers without R4 (`test_t10.py::test_ar_40_item_3…`, `test_t12_shared_parameters.py::test_rule_configuration_holds_only_exclusive_parameters`) were updated to include R4, citing E-1.2.13 in the test. That is a contract change, not a code fix, and is reported for the Owner's review.
- **Files/tests:** `substrate/surrogate.py`, `substrate/geometry.py` (`predicted_clearance`), `substrate/builder.py`, `schema/tables.py` (`pair_series.ttc_s`, `pet_pred_s`), `events/providers.py` (`r4_c`, `check_r4`), `events/s5.py`, `events/baselines.py`, `pipeline/m0.py`; `tests/events/test_t15.py`.
- **Reverse:** items 1–2: swap the solver (values move within 1e-6 s); item 3: change two reason strings; item 4: guard `check_r4` by `"R4" in conflict`; item 7: record R4 only when enabled (would break CT-T11-02 extended).

## AR-50 — SDG truth reading (T-18 part B)   status: ACCEPTED (Architect, 13 Nov 2026; item 3 yaw subject to the AR-52 motion-direction check)
- **Gaps and choices:**
  1. **Line ↔ frame.** `object_detection.jsonl` line k is the truth of decoded frame k in presentation order (`decode_seq` k). It is never keyed by `frame_index`, which renumbers eligible frames only and would shift under an excluding rules version. Parsing refuses a camera whose line count differs from its video's frame count (ERR-INVARIANT). What such a camera may still be used for is CR-019 item 3.
  2. **Pose source.** The pose is the per-frame 3D-box transform (USD row vectors), and the footprint centre is the centre of the box's floor face: the "simulator footprint centre" that D-8 / CR-007 prescribes for the oracle path. `metro_agent_data.world_position` is not read. Data check over the 72 held runs (ceiling_00): in 32 runs it never changes while the boxes move (distance to the box floor centre median 1.0–1.1 m, max 4.2 m: a stale initial pose); in the other 40 it moves and sits at the prim origin (person: median 0.08 m from the box floor centre; forklift: median 0.63 m, max 0.91 m, because the forklift's origin is not at its footprint centre). It is therefore neither always current nor ever the footprint centre of the forklift, so there is no second plausible source.
  3. **Yaw.** The direction of the box's local x axis, atan2(T01, T00) in (−π, π]; "simulator yaw when supplied" (T8.2). The footprint rectangle is symmetric under a half-turn, so the axis sign cannot change a clearance.
  4. **Classes.** The forklift is the prim `/World/Robots/forklift/Forklift` (qualification Part 2: its label class is `robot`); a person is an agent with label class `character`; anything else is not an E1 pair object. An agent without a 3D box has no pose and is left out of the truth (counted in the data check).
- **No meaning effect:** items 1 and 4 are parsing; items 2 and 3 apply D-8 and T8.2 as written. **Files/tests:** `adapters/sdg_truth.py`; `tests/adapters/test_sdg_truth.py`; data check `research/datasets/part3/sdg_truth_check.py`. **Reverse:** edit the module.

## AR-51 — Representation details of `rv2` and the `low_light` tag (D-25 Architect ruling, 13 Nov 2026)   status: ACCEPTED (Architect, 13 Nov 2026)
- **Gaps and choices:**
  1. **Reading of "median frame P99 <= 32 and the frame is not black".** Choice: the median of P99 over the recording's decoded frames that are not `black`; the tag is set when it is ≤ 32; no tag when every decoded frame is black (there is no non-black frame to describe). Median of an even count = mean of the two middle values, compared exactly. Considered: the median over all decoded frames, with the tag unless the whole recording is black. On the 758 synthetic recordings both readings give the same 13 recordings (D-25), so the choice changes no tag on the data held; if real footage separates them, the agent raises it in D-25 rather than choosing.
  2. **Where the tag lives.** `low_light` is a stratum, not a frame flag, and no S1 field holds it. Choice: computed by `quality.condition_tags` and returned on `timestamps.Resolved.condition_tags`; not written into S1 artifacts, so S1 IDs are unchanged. Stratified reports read it from there when they are built. Considered: a new S1 field (a schema change, for the Architect).
  3. **Version labels.** `rv2` (synthetic M1a) and `rv2-real-provisional` (real) share one rule set (`NO_CONTENT_VERSIONS`). The superseded `rv2-provisional` (black iff P99 ≤ 32) is kept, selectable only explicitly, so the D-25 evidence files (`rv2_synthetic_check*.json`, `rv2_sflat_evidence.json`) reproduce. `frame_flags` now needs the rules version as an argument (no default).
  4. **AR-48 item 1** now reads `rv2-real-provisional` for real S1 artifacts, per the ruling.
- **No meaning effect:** the flag rule, thresholds and the tag rule are the ruling's; items 2–4 are storage and naming; item 1 is checked to give the same tags on all data held.
- **Files/tests:** `decode/quality.py`, `decode/timestamps.py`; `tests/decode/test_rv2.py`, `tests/decode/test_rv2_provisional.py` (now passes the version explicitly; no expected value changed); check `research/datasets/part3/rv2_check.py`. **Reverse:** item 1: change the frame filter in `condition_tags`; item 2: add an S1 field; item 3: drop `RV2_PROVISIONAL` once the evidence files are no longer needed.

## CR-019 (2026-11-13) — SDG oracle tracks: which 2D box, not-visible frames, incomplete annotation, faulty truth boxes (T-18)   status: CLOSED

**Raised by:** implementation agent. **Task:** T-18 part B (oracle tracks, WP-13). **Contract sections:** E-1.2.1 §10.1 (ORACLE-S3), §3.4 (evidence classes), §5.5; Appendix T T8.5 (image gap), T8.6 (evidence state), T8.7 (Q); AR-29 (oracle `tracked` = detected); AR-36 item 4 and its Architect ruling ("the adapter sets evidence_state from [visibility truth] when present").
**Meaning-affecting:** yes. Each item changes oracle track points, and so image_gap (R1 P), evidence classes (detected / inferred durations), Q, POW gap bridging and the reference visible support.

**What the data supply** (SDG artifacts tier, per camera and frame): a `loose` 2D box (full projected extent) for every annotated object, and a `tight` 2D box (visible pixels) only when the object is visible in that camera; `occlusionRatio` = −1 everywhere (qualification Part 2, §2.6). No other visibility truth.

| # | Gap | Readings that give different numbers | Agent's proposal |
|---|---|---|---|
| 1 | Box of an oracle track point | (a) `tight`, the visible extent, as a perfect detector would report; (b) `loose`, the full extent including occluded parts | (a) where the object is visible |
| 2 | State of an object-frame with no `tight` box (annotated, not visible in this camera) | (a) `predicted`: the object exists and the simulator knows where; evidence `occluded_predicted`, class inferred; box = `loose`; (b) `lost`: no point; (c) `tracked` with the loose box | (a). It matches the tracker meaning of occlusion and keeps detected time = visible time |
| 3 | Camera whose annotation line count ≠ video frame count | (a) no simulator truth for that camera; the recording is used for reference-free checks only; (b) align by some other key | (a), as proposed in qualification Part 3 §3.10 |
| 4 | Truth 2D box inconsistent with the object's own 3D box (loose box extends beyond the image-clipped reprojected 3D hull by more than a threshold) | (a) keep it; (b) keep the 3D pose, replace the 2D truth: state `predicted`, box = clipped reprojected hull, logged as a truth defect; (c) drop the point (`lost`). And the threshold: 2 px flags 529 boxes; any value in (80.1, 157.3) px flags 46 | (b), threshold 120 px (a round value in the gap) |

**Evidence for item 4.** Held shard 00538, run `…fb11684081300a3c4725_run_2_seed_516797828`, camera `eye_01`: five frames (decode_seq 136, 176, 199, 213, 226) where the forklift's loose and tight boxes enclose a different object, a walk-behind pallet stacker in the foreground near the bottom image edge. On the neighbouring frames (for example 130 and 140) the forklift's box agrees with its 3D box. The agent looked at one synthetic frame (136) with both boxes drawn; nothing was stored. Excess 300–416 px.
Over all 72 held runs (709 cameras, 405,075 annotated object boxes, `research/datasets/part3/sdg_truth_check.json`), 529 loose boxes extend more than 2 px beyond the clipped reprojected hull (8,500 more have a 3D corner behind the camera and are not checked). Their excess splits with a clean gap:
| Excess (px) | (2,5] | (5,10] | (10,20] | (20,40] | (40,60] | (60,80] | (80,100] | (100,150] | (150,300] | (300,1300] |
|---|---|---|---|---|---|---|---|---|---|---|
| Boxes | 124 | 81 | 113 | 110 | 40 | 10 | 1 | 0 | 5 | 41 |
- ≤ 80.1 px: 483 boxes, mostly persons (eye-level and ceiling cameras). This is consistent with the person's 3D box (fixed extents) being smaller than the animated mesh that the 2D box encloses. Not a labelling fault in the sense of item 4.
- ≥ 157 px: 46 boxes, **all on camera `eye_01`**, persons and forklifts, in about 15 runs, consistent with the stacker case above.
So a 2 px threshold would label hundreds of ordinary person boxes as defects. A threshold in the 80–157 px gap, or a rule tied to that camera, separates the two groups on these data. The threshold is the Architect's choice.
- Item 3 data: 9 cameras (3 runs) have annotation line counts ≠ video frame counts; 1 camera lacks members (`…run_5_seed_177568880.ceiling_01`).
- SmartSpaces (T-18 part C, `research/datasets/part3/smartspaces_truth_check.json`): item 1 does not arise (one box per camera, the visible one); **item 2 applies** (an object present in the scene's truth but absent from a camera's visible list); item 3 does not arise (frame ids 0–8,999 = the 9,000 video frames of every camera); item 4: no group like `eye_01`: of 1,924,956 visible boxes per scene, 99.86 % lie within 2 px of the reprojected 3D box, every box beyond that is a person (max 26.7 px, the animated mesh), forklifts ≤ 0.49 px.
**What proceeds meanwhile:** SDG truth reading (AR-50), S0 registration of the SDG recordings, SmartSpaces adapters. Not built until decided: the SDG ORACLE-S3 artifacts and CV-SIM references that depend on items 1–4.
**Agent's recommendation:** 1(a), 2(a), 3(a), 4(b) at 120 px.
**Decision:** (13 Nov 2026) Appendix T section T17 (E-1.2.15), D-28: 1(a); 2 predicted with the image-clipped reprojected 3D box inside the visible span (not the loose box), lost when empty, no point outside the span; 3(a) and camera parameters required; 4 excess > 120 px → truth_defect treated as not visible, excess in (80, 157] px → ERR-INVARIANT.   **Approver:** Research Architect; Owner (by forwarding)

## AR-52 — SmartSpaces calibration and truth reading; SDG S0 registration (T-18 part C)   status: ACCEPTED (Architect, 13 Nov 2026). Item 2: the motion-direction check is withdrawn as an acceptance test and kept as evidence; the long-axis yaw is used for both datasets (CR-023, decided 14 Nov 2026)
- **Gaps and choices:**
  1. **SmartSpaces calibration.** `calibration.json` supplies K (`intrinsicMatrix`), E = [R | t] (`extrinsicMatrix`, OpenCV, metres), and a `cameraMatrix` and `homography` that are not K·E (they map the dataset's map-image coordinates: `scaleFactor`, `translationToGlobalCoordinates`). Choice: full_camera from K and E, `distortion_model = none` (rendered pinhole, none supplied), `dataset_supplied`, `supplied_unvalidated` until GV-02; the map-image matrices are not read. Evidence: with K·E, 1,922,286 of 1,924,956 visible 2D boxes per scene (99.86 %) lie within 2 px of the image-clipped projection of the object's own 3D box; with `cameraMatrix`, most projected box centres fall behind the camera. Considered: ground_plane_homography from `homography` (wrong frame).
  2. **Forklift yaw = the direction of the box's long horizontal axis.** T8.2 uses "simulator or oracle yaw when supplied", else the heading; the prior rectangle's length lies along yaw. SmartSpaces forklifts are long along their local y axis on all 80,626 forklift boxes (1.16 × 2.68 m and 1.13 × 1.87 m), so yaw = rotation_z + π/2, wrapped to (−π, π]; SDG forklifts are long along local x on all 20,081 boxes checked (3.03 × 1.13 m), so AR-50's local-x yaw is the same rule. A box with equal horizontal extents is refused. **Review flag:** a literal reading "yaw = the supplied rotation" would turn the SmartSpaces forklift footprint 90° against its own 3D box and make yaw jump by 90° where a track falls back to heading; the agent does not consider it plausible. If the Architect does, this item becomes a CR. No value uses it yet: oracle tracks wait for CR-019.
  3. **SmartSpaces frame alignment.** Truth frame id k is decoded frame k (decode_seq k) of every camera of the scene (qualification 2.7); `parse_frames` refuses any id set other than 0 … n − 1. Data: 9,000 ids = 9,000 video frames on all 19 cameras of both scenes.
  4. **SmartSpaces classes and pose.** `Person` → person, `Forklift` → forklift, `PalletTruck` → pallet_truck (present, not an E1 pair class, D-22). Footprint centre = (x, y) of `3d location` (the box centre; D-8 simulator footprint centre). Box corners rotate about z only: roll and pitch are 0 on forklifts and pallet trucks and ≤ 1.3e-5 rad on persons.
  5. **SDG S0.** Site = the release's one layout family (`synthetic_scene`, `independent_of_development = false`). Camera poses differ between runs (ceiling_00 at 10.0, 10.03 or 10.5 m), so a camera is one view of one run, labelled `<RGB run id>.<view>` (`ceiling_*` → ceiling, `eye_*` → eye_level). One world frame, the declared stage frame (identity `transform_from_dataset`, metres, `dataset_supplied`); its floor is z = 0 within the data (forklift box floor −0.002 m; person median −0.001 m). Session = run. Timelines are `recording_local` (no clock alignment registered; the multi-camera `aligned_session` for M2 needs a σ and is not built here). `privacy_state = synthetic_no_persons` (rendered characters), a retention record `rp_synthetic_public_v1` for synthetic public data (VR-E-070 restricts only real files), `height_reference_ids = []`. Cameras without camera parameters (12, in the two partly annotated runs of qualification 3.8) are registered without a calibration (uncalibrated).
  6. **retrieved_utc.** One dataset_source row per (name, version) (D-5); the SDG holding arrived in two parts at the same pinned revision, so retrieved_utc = the arrival of its last file, 2026-11-13T01:57:47Z.
  7. **Lineage (T14.1).** ext_run_id = scene_id = the RGB-tier run id (artifact folder name minus its 20-character hash, the tier-join rule); seed from `runs.parquet` (checked against the run id); generation_batch = the index's source path without bucket and run folder (e.g. `warehouse_osmos_2/nearmiss/shard-15`); layout_id = the layout family (no edge on its own); render_parent null `not_applicable`; scenario_ref = `nearmiss`. Index rows that disagree with the run (id, kind, seed, path) are refused.
- **No meaning effect:** items 1, 3 and 4 read the supplied data as verified above; item 2 is flagged for review; items 5–7 are registration representation; T14.1 edges are as written (one leakage group per run). Result: one S0 artifact for 72 runs, 720 recordings, 708 calibrations (`research/datasets/part3/s0_sdg_summary.json`).
- **Files/tests:** `adapters/smartspaces.py`, `adapters/registration.py`; `tests/adapters/test_smartspaces.py`, `tests/adapters/test_registration.py`; data checks `research/datasets/part3/smartspaces_truth_check.py`, `s0_register_sdg.py`. **Reverse:** item 2: change `forklift_yaw`; items 5–7: edit `sdg_metadata` and re-register (S0 IDs change).

## CR-020 (2026-11-13) — dataset_source.data_origin when a dataset's scenes differ in origin (T-18 part C)   status: DECIDED (a); T16 section text not yet received

**Raised by:** implementation agent. **Task:** T-18 part C (SmartSpaces S0). **Contract sections:** E-1.2.1 §3.1 (`dataset_source.data_origin`, `site.data_origin`), §2 (manifest `data_origin`), Appendix T VR-E-005 (one data_origin per file; real and synthetic never share a file or aggregate), T12.5, T14.3; F.1 A1.2 (dataset anchor = name, version; D-5).
**Meaning-affecting:** yes. data_origin is a fitness scope key (T12.5), stratifies Target B group counts (T14.3) and decides what may be pooled (VR-E-005).

**Problem.** One PhysicalAI-SmartSpaces release (`MTMC_Tracking_2026` at d38193b) holds scenes of three origins: `Warehouse_000` rendered in Omniverse (`synthetic_rendered`), `Warehouse_001` its Cosmos Transfer re-rendering (`synthetic_transferred`; card, and byte-identical truth and calibration), and `Warehouse_026/027` real captures (`real_staged`, D-24). `site` carries a data_origin, but `dataset_source` carries exactly one, and its anchor is (name, version), so every S0 artifact that registers any of these scenes must carry the same dataset row. VR-E-005 also requires one data_origin per file, so the three origins need separate S0 artifacts, each with that shared row.

| Option | Effect |
|---|---|
| (a) One dataset_source per origin, told apart by the version label, e.g. `MTMC_Tracking_2026@d38193b/synthetic_rendered`, `…/synthetic_transferred`, `…/real_staged` | every S0 file is single-origin; the release is three dataset rows with one licence row |
| (b) One dataset row whose data_origin is that of a chosen part; the site carries each scene's origin | an S0 file for Warehouse_001 or 026 would hold rows of two origins (VR-E-005), unless the rule is read per site |
| (c) Contract change: dataset_source.data_origin becomes a list or is dropped in favour of site.data_origin | schema change |

**What proceeds meanwhile:** SmartSpaces calibration and truth reading (AR-52); SDG S0 (single origin, registered). **Not built until decided:** SmartSpaces S0 for Warehouse_000/001, and the real 026/027 registration.
**Agent's recommendation:** (a).
**Decision:** (13 Nov 2026) option (a), version labels "<edition>@<revision>/<data_origin>" (Architect rulings second set, item C, citing T16 / E-1.2.14, whose section text the agent has not received).   **Approver:** Research Architect; Owner (by forwarding)

## AR-53 — Representation details of T17 oracle tracks and the SmartSpaces S0 (T-18)   status: ACCEPTED (item 3: Architect, 14 Nov 2026; remaining items: G-PR rulings, 14 Nov 2026, D-34)
- **Gaps and choices** (none changes a T17 rule):
  1. **"Behind the camera" in T17.2.** A 3D box that straddles the camera plane is cut at a near plane z_cam = 0.001 m and the part in front is projected; the reprojection is empty only when nothing lies in front or nothing falls in the image. Considered: empty as soon as one corner is behind (would turn close, partly visible-range objects into `lost`).
  2. **Image clipping.** The convex hull of the projected vertices is clipped exactly to the image rectangle (polygon clipping, then its bounding box); a result without area is empty.
  3. **Box coordinates → CF-IMG. Review flag.** Both datasets give 2D boxes as inclusive pixel indices: maxima are 1919 and 1079 on 1920 × 1080 images, and one-pixel boxes with x1 = x2 or y1 = y2 exist (SDG tight boxes: 117 of 379,570; SmartSpaces visible boxes: 98,702 of 1,924,956). CF-IMG (E-1.2.1 §5) is corner-origin with x1 < x2 and y1 < y2, and "adapters map their outputs back to CF-IMG". So a dataset box [x0, y0, x1, y1] is the CF-IMG box [x0, y0, x1 + 1, y1 + 1]; reprojected boxes are clipped to [0, W] × [0, H]. Without this, T17.1 ("box = that visible box") cannot be stored for those boxes (schema: x1 < x2). It moves every oracle box's right and bottom edge by 1 px against the raw numbers. The T17.5 excess stays in dataset coordinates, as the ruling's figures (80.1, 157.3, 46 boxes) were computed. Considered: treating zero-extent boxes as not visible (contradicts T17.6 "no minimum visible area").
  4. **Frame without a truth record inside the visible span** → `lost` (no pose to reproject).
  5. **T17.5 order and scope.** Every loose box is checked, visible or not. An excess in the guard band ((80, 157] px as first written; (90, 150] px since T18) is refused before the 120 px rule is applied. The refusal is per camera: that camera gets no oracle track, the driver records the case and continues (CR-022).
  6. **To S3 and S4.** Points on frames without a `frame_index` (not eligible under the rules version) are left out; a track left without points is dropped; `local_id` = 1… in sorted identity order; simulator positions carry a zero covariance (AR-36 item 4); yaw is passed for forklifts only. SmartSpaces pallet trucks become tracks of class `pallet_truck` (present, not an E1 pair class, D-22).
  7. **CV-SIM references.** `reference_objects` gives the T17.6 objects (present on T17.1 frames after T17.5, with the visible box and the simulator position). O/H/PC interaction references apply the definitions with rule parameters, which do not exist before the pre-registration is frozen (G-PR); they are built in the M1a run (T-21) from these objects.
  8. **T16.** The T16 text is in Appendix T verbatim (it reached the agent after T17). As T16.1 says: one dataset_source per data_origin, version `MTMC_Tracking_2026@<full revision hash>/<data_origin>`, one shared licence component whose own version has no origin suffix. T16.2 and the T16.1 refusal: AR-54.
  9. **SmartSpaces S0.** One S0 artifact per scene (VR-E-005). Site = scene; session = scene; lineage: ext_run_id = scene name, scene_id = the scene asset (`Warehouse_000` for both scenes, T14.1), render_parent = `Warehouse_000` on `Warehouse_001`, seed null `not_supplied`, generation_batch `MTMC_Tracking_2026/train`. `viewpoint_class = other` (the dataset states none; **review flag**: it may be a stratum). Timelines `recording_local`, as for SDG (AR-52 item 5).
  10. **Registrar fix.** `_fill_struct` ignored a supplied null reason inside `session.lineage` and stored `not_supplied`; it now honours it, as `_fill` does. SDG sessions therefore store `render_parent` null `not_applicable` as AR-52 item 7 says; the SDG S0 ID changed (now `art_xwrldyhquvmorjhpjxb573tbxk` at contract label E-1.2.15). M0 supplies no lineage reasons and is unchanged.
  11. **Driver parameters.** The T17 run decodes with `rv2` and the TEST-ONLY values of k_sup, f_untimed, f_sub; its S1 and S3 artifacts are TEST-ONLY and are rebuilt under the frozen pre-registration.
  12. **Yaw against motion.** The Architect's check (ruling on AR-52 item 2) was run; its result is in CR-023, decided 14 Nov 2026: the check is evidence only, and the SDG box yaw is used.
- **Item 3, evidence per dataset (Architect ruling C, 14 Nov 2026;** `research/datasets/part3/box_convention_evidence.json`, all annotated objects, 1920 × 1080 images**):**

  | Dataset, field | Boxes | Non-integer | Largest x1, y1 | Boxes with x1 = 1919 | Boxes with y1 = 1079 | x0 = x1 | y0 = y1 | x1 < x0 or y1 < y0 |
  |---|---|---|---|---|---|---|---|---|
  | SDG `bounding_box_2d_tight_fast` (679 annotation files) | 381,470 | 0 | 1919, 1079 | 23,153 | 20,622 | 112 | 43 | 0 |
  | SDG `bounding_box_2d_loose_fast` | 388,318 | 0 | 1919, 1079 | 23,223 | 20,684 | 18 | 4 | 0 |
  | SmartSpaces `2d bounding box visible`, Warehouse_000 (001 identical) | 1,924,956 | 0 | 1919, 1079 | 20,022 | 18,906 | 61,497 | 73,565 | 0 |

  In each dataset every value is an integer, boxes cut by the right or bottom image border stop at W − 1 or H − 1 and never reach W or H, and boxes one pixel wide or high have equal minimum and maximum. All three facts fit inclusive pixel indices and none fits half-open edges. (The counts differ slightly from the E1-object counts quoted in item 3 because this table covers every annotated object.)
- **No meaning effect:** items 1, 2, 4–7, 9–11 are representation or parsing of T17 as written; item 3 applies the contract's CF-IMG definition to the datasets' convention and is flagged; item 8 applies only the quoted ruling.
- **Files/tests:** `adapters/oracle_truth.py`, `adapters/registration.py`, `registry/registrar.py`; `tests/adapters/test_t17_oracle_truth.py`, `tests/adapters/test_registration.py`; drivers `research/datasets/part3/t17_oracle.py`, `s0_register_smartspaces.py`, `yaw_motion_check.py`. **Reverse:** item 3: drop `cf_img` and the clip bound; item 1: change `NEAR_M` or the rule in `clipped_reprojection`.

## CR-021 (2026-11-13) — No leakage edge between a scene and its re-render once they are separate dataset rows (T-18)   status: CLOSED (Appendix T T16.2)

**Raised by:** implementation agent. **Task:** T-18 (SmartSpaces S0). **Contract sections:** E-1.2.1 §8 (leakage edges), AR-31, Appendix T T14.1; CR-020 option (a) (T16, text not received).
**Meaning-affecting:** yes (leakage rule).

**Problem.** Under CR-020 option (a), `Warehouse_000` (`…/synthetic_rendered`) and `Warehouse_001` (`…/synthetic_transferred`) are two dataset_source rows. The scene and render-lineage edges (`same_scene_or_run`) are created only between recordings of the **same dataset** (AR-31: scene, run and seed identifiers are dataset-local). With the registered rows, `leakage.metadata_edges` gives **no edge** between the two scenes; if both had one dataset row it gives `same_scene_or_run`. T14.1 says a scene asset and all its re-renderings are one scene, so the two must fall in one leakage group. The T16 text may already cover this; the agent has not received it.

| Option | Effect |
|---|---|
| (a) Scene, run, seed and render-parent edges apply across dataset_source rows that share the dataset name and the `<edition>@<revision>` part of the version label | 000 and 001 fall in one group; SDG is unaffected |
| (b) The edge is declared by hand when the split is frozen (as a `training_use`-style declared edge) | depends on the operator remembering it |
| (c) As written: no edge | a scene and its re-render could be split across partitions |

**What proceeds meanwhile:** everything except freezing a split that contains SmartSpaces recordings. **Agent's recommendation:** (a). The agent changes nothing in `splits/leakage.py` until decided.
**Decision:** (13 Nov 2026) covered by T16.2, received after this CR was written: "within one dataset" means rows with the same dataset name; implemented in `splits/leakage.py` (`dataset_name`), tests `test_t16_*`.   **Approver:** Research Architect; Owner (by forwarding)

## CR-022 (2026-11-13) — T17.5 refusal band (80, 157] px catches one ordinary held box at 80.1 px (T-18)   status: CLOSED (Appendix T T18 amendment 1, E-1.2.16)

**Raised by:** implementation agent. **Task:** T-18 (SDG ORACLE-S3). **Contract section:** Appendix T T17.5.
**Meaning-affecting:** yes (which cameras have oracle tracks and references).

**Problem.** T17.5 states that any threshold in (80.1, 157.3) selects the same 46 boxes, and that an excess in (80, 157] px is refused with ERR-INVARIANT. The held data contain one box inside that band: the largest ordinary excess, 80.1 px (person, run `a7530aa436c6e2eeb59c_run_22_seed_1886649344`, camera `eye_02`, decode_seq 206; listed in CR-019's table under (80, 100]). The adapter is implemented as written, so that camera is refused: it has no oracle track and no reference, and it is reported. The other 9 cameras of the run are unaffected.

| Option | Effect on the held data |
|---|---|
| (a) Keep T17.5 as written | this one camera stays outside the oracle and reference populations (reported as refused) |
| (b) Refusal band (81, 157] px, or (80.1, 157.3) as in the sentence before it | no camera refused; the 80.1 px box is an ordinary person box (animated mesh larger than the fixed 3D box) |

**What proceeds meanwhile:** all other cameras. **Agent's recommendation:** (b) with a stated bound; the agent does not move the bound itself.
**Decision:** (14 Nov 2026) guard band (90, 150] px; the 120 px threshold is unchanged (Appendix T T18 amendment 1, appended verbatim). Implemented in `oracle_truth.REFUSE_BAND_PX`; tests `test_t17_5_refusal_band`, `test_the_eye_02_camera_of_run_22_seed_1886649344_has_an_oracle_track`. The CR text holds no point the ruling does not cover.   **Approver:** Research Architect; Owner (by forwarding)

## AR-54 — T16 mechanics, the real SmartSpaces rows and the access log (T-18)   status: ACCEPTED (item 3: Architect, 14 Nov 2026, no calibration for 026/027; remaining items: G-PR rulings, 14 Nov 2026, D-34)
- **Gaps and choices:**
  1. **T16.2 in code.** `leakage._edge_type` compares `dataset_name` (falling back to `dataset_id` when a caller supplies none, which is the pre-T16 behaviour for a single row). Callers of `SplitBuilder.freeze` pass the dataset_source name with each recording.
  2. **T16.1 refusal.** The registrar keeps src_id → dataset_source row across its registrations and refuses a file listed under a second row (ERR-INVARIANT), within one registration or across them. Registering the same file again under its own row is allowed (identical bytes, D-5).
  3. **Real scenes 026 / 027.** Registered under `…/real_staged`, one S0 artifact per scene (11 recordings): `real_staged`, `staged_facility`, `contains_identifiable_persons`, `approvals_ref` and retention values exactly the D-26 pending values, `annotation_levels = [none]` (D-24 b), `unit_status = unknown`. **No calibration and no world frame are registered**, so the scenes are uncalibrated for RQ1: the supplied `calibration.json` comes with a model-estimated reprojection report in unstated "units" and no truth to check it against; registering it would be a calibration-tier statement on real footage. **Review flag.** `scripted = false` and `independent_of_development = false` (neither is stated by the publisher; no claim is made). `viewpoint_class = other`.
  4. **No pixel is decoded for registration.** SHA-256 and size come from the download log (checked against the publisher's hashes at download); the size on disk is compared without reading. The only read is the codec probe of the container header.
  5. **Access log.** `registry/access_log.py`: append-only JSON lines with the status log's hash-chain form (AR-36 item 1); fields of the Gov table `access_log` plus `prev_hash` and `record_hash`; event time supplied by the caller. It lives at `data/derived/real/access_log.jsonl` (git-ignored, with the real data). The 11 probes are its first entries.
- **No meaning effect:** items 1–2 implement T16 as written; item 3 applies D-24 / D-26 as recorded and makes the conservative choice where the publisher is silent; items 4–5 are governance mechanics.
- **Files/tests:** `splits/leakage.py`, `registry/registrar.py`, `registry/access_log.py`, `adapters/registration.py`; `tests/adapters/test_registration.py` (`test_t16_*`, `test_real_scenes_*`), `tests/registry/test_access_log.py`; `research/datasets/part3/s0_register_smartspaces_real.py`. **Reverse:** item 3: add the calibration rows and re-register.

## CR-023 (2026-11-13) — SDG forklift yaw fails the motion-direction check as stated (AR-52 item 2, AR-50 item 3)   status: CLOSED (option (a), no contract text)

**Raised by:** implementation agent, as the Architect's ruling on AR-52 item 2 requires ("if it concentrates near 90 deg, or is not concentrated, raise a CR and do not use yaw"). **Contract sections:** Appendix T T8.2 (forklift yaw), T8.3, T15.1; AR-50 item 3, AR-52 item 2.
**Meaning-affecting:** yes (forklift footprint orientation, so clearance, R3 and R4).

**The check** (`research/datasets/part3/yaw_motion_check.json`, statistics only): for every forklift frame whose truth speed is ≥ 0.3 m/s (displacement of the footprint centre over 10 frames), the angle between the direction of motion and the adopted yaw, modulo 180°, folded to [0°, 90°].

| Dataset | Frames | Median | P90 | P99 | Within 15° | Beyond 75° |
|---|---|---|---|---|---|---|
| SmartSpaces (yaw = rotation + 90°) | 40,511 | 0.2° | 4.2° | 6.3° | 99.8 % | 0 % |
| SmartSpaces, literal rotation (for comparison) | 40,511 | 89.8° | 90.0° | 90.0° | 0 % | 99.8 % |
| **SDG (yaw = box local x axis), 67 runs** | 16,507 | 0.0° | 77.5° | 78.8° | **53.6 %** | **35.3 %** |

SmartSpaces is concentrated near 0: its yaw stands. **SDG is not concentrated**: two groups, at 0° and at about 77.5°.
**What the two SDG groups are** (same file): split by yaw rate over the same 10 frames. Straight frames (yaw rate < 5°/s; 8,647): 100 % within 15°, maximum 10.5°. Turning frames (7,860): median 77.5°, and the yaw rate is 75°/s wherever the motion is across the axis. The simulated forklift pivots while its footprint centre moves at 0.75–0.82 m/s, so during a turn the centre travels across the long axis. The 3D box itself is consistent with the images (part B: the forklift's 2D boxes agree with its reprojected 3D box).

| Option | Effect |
|---|---|
| (a) Use the SDG box yaw: the check is passed on straight frames, and turning frames are a property of the simulated motion, not of the axis | oriented-rectangle footprint on every SDG forklift frame |
| (b) Do not use SDG yaw: T8.2 falls back to heading (which is about 77° off the body axis during pivots), then carry-forward, then the circumscribed disc | footprint orientation wrong during turns, or a disc (larger, conservative) |
| (c) Do not use SDG yaw and force the circumscribed disc for SDG forklifts | conservative clearance everywhere; `footprint_orientation_unknown` on every pair-frame |

**Until decided:** SDG yaw is not used. `oracle_truth.sdg_obs` withholds it by default (`test_sdg_yaw_is_withheld_by_default_cr_023`), so nothing downstream receives an SDG yaw. Note for T-21: under (b) the heading fallback would be active, which this evidence shows is misleading during pivots; the agent builds no SDG S4 until this is decided.
**Agent's recommendation:** (a).
**Decision:** (14 Nov 2026) option (a), no contract text. SDG forklift yaw = the box long-axis yaw (AR-50 item 3, AR-52 item 2), which is "simulator yaw when supplied" under T8.2. The motion-direction check is withdrawn as an acceptance test for yaw (body orientation and direction of travel differ during pivot turns); its result is kept as evidence. SDG S4 is unblocked. Also ruled: (1) the heading-fallback finding is added to CR-007 / D-8 for the T-22 decision (done); (2) a per-frame stratum `forklift_turning` (|yaw rate| above a stated value) is proposed in T-20 so that R3/R4 results can be reported for turning and straight frames separately. Implemented: `oracle_truth.sdg_obs` passes the forklift yaw (`test_sdg_forklift_yaw_is_the_box_yaw_cr_023` replaces the withholding test). The CR text holds no point the ruling does not cover.   **Approver:** Research Architect; Owner (by forwarding)


## CR-024 (2026-11-14) — T18 amendment 2: is the run length counted in the camera's frames or in eligible frames? (T-18)   status: CLOSED (Appendix T T19, E-1.2.17: eligible frames)

**Raised by:** implementation agent. **Task:** T-18 (T18 implementation). **Contract sections:** Appendix T T18 amendment 2, T17.1–T17.2, T8.1.
**Meaning-affecting:** yes in principle (which frames have predicted points). See the count on the held data below.

**Problem.** T18 amendment 2 predicts a not-visible run "only when the run has <= g_max frames (the T8.1 parameter)". T17 defines visibility per frame of the camera as the truth lists it (every decoded frame). T8.1 counts its gap "in eligible frames". A run that contains a frame that is not eligible (for example a black frame under rv2) is one frame longer in the first count than in the second, so a run of g_max + 1 decoded frames with one ineligible frame is lost under one reading and predicted under the other.

| Option | Effect |
|---|---|
| (a) Decoded frames of the camera, as T17 counts frames (implemented) | the oracle track does not depend on the frame-quality rules version |
| (b) Eligible frames, as T8.1 counts its gap | the oracle run rule and the POW gap rule use the same count; the oracle points then depend on the decode configuration |

**Count on the held data** (TEST-ONLY g_max = 15, rules version rv2; `t17_counts_sdg.json`, code commit 6f7fb07): SDG has 548 not-visible runs inside visible spans; 52 of them contain at least one frame that is not eligible, and **1 run** would get the other outcome under (b). (The SmartSpaces run on reading (a) was stopped when the ruling arrived; all its frames are eligible, so the two readings cannot differ there.)

**Implemented meanwhile:** (a), as the T17 text reads. `t17_oracle.py` counts, per camera, the runs whose outcome would differ under (b) at the TEST-ONLY g_max and the runs that contain an ineligible frame; the totals are in `t17_counts_*.json` (`runs_differing_if_eligible_frames`, `runs_with_ineligible_frame`) and in the Progress log.
**Agent's recommendation:** (a).
**Decision:** (14 Nov 2026) option (b): the run length is counted in eligible frames of the recording, as the T8.1 gap is; a run with ≤ g_max eligible frames is predicted on its eligible frames, a longer run is lost on every frame, and ineligible frames carry no track point in either case (Appendix T T19, appended verbatim). Implemented in `oracle_truth.camera_tracks` (`ineligible`), tests `test_t19_*`; counts re-run.   **Approver:** Research Architect; Owner (by forwarding)

## AR-55 — Representation details of the T18 amendments and the count rebuild (T-18)   status: ACCEPTED (item 6 as pinned, Architect, 14 Nov 2026; item 4's frame unit superseded by T19; remaining items: G-PR rulings, 14 Nov 2026, D-34)
- **Gaps and choices** (none changes a T17 or T18 rule):
  1. **What a run is.** A maximal sequence of consecutive frames, between two visible frames of the object in the camera, on which it is not visible. Frames without a truth record, truth-defect frames (T17.5, "treated as not visible") and frames whose reprojection is empty all count. Inside a run of at most g_max frames T17.2 still applies frame by frame (empty reprojection → lost). Leading and trailing not-visible frames are outside the span and are no run (T17.3).
  2. **Counts.** `lost` stays the number of all lost frames (T17.7); `lost_long_run` is the part of it in runs longer than g_max.
  3. **g_max as input.** `camera_tracks` takes g_max as a required argument; a negative value is refused (ERR-SPEC); g_max = 0 makes every run lost. The oracle configuration record (`orc_`) of the driver now carries g_max, because the oracle points depend on it. The driver uses the TEST-ONLY g_max (15); the artifacts are TEST-ONLY and are rebuilt under the frozen pre-registration.
  4. **Run-length statistics (T18 amendment 3).** Lengths in decoded frames (CR-024). Median, P90 and P99 are nearest-rank (the value at rank ⌈q·n⌉ of the sorted lengths), so each is an observed length. The files also keep the full histogram and, for the test value of g_max, the runs and frames above it.
  5. **Rebuild without decoding again.** T18 changes nothing in S0 or S1. The rebuild reuses each recording's S1 artifact of the first run after verifying it (file hashes, payload reconstruction, same decode configuration and S0 input); the new S3 artifacts carry contract label E-1.2.16 and name that S1 artifact as input. The S0 and S1 artifacts keep the label E-1.2.15 under which they were built. The count files record the S1 code commit per camera.
  6. **The before/after test. Review flag.** "Pair-level S4/S5 output on a fixture is identical before and after amendment 2" holds, and is tested, for a fixture whose not-visible run has g_max frames (S3, S4 and S5 artifact IDs identical). For a run of g_max + 1 frames the output is not identical, and cannot be under T8.1: before, the predicted points were joint frames and one POW covered the run; after, the run is a gap longer than g_max, the POW ends with `gap_exceeded` and a second POW continues it. Both cases are pinned in `tests/events/test_t18_oracle_absence.py`. If the Architect expected identity for long runs too, this item becomes a CR. **Architect ruling (14 Nov 2026): ACCEPTED as pinned.** Identity of S4/S5 output is required only for runs ≤ g_max. For longer runs the new behaviour is intended: the POW ends with `gap_exceeded` and a continuation POW starts. The Architect's earlier statement that no pair-level result changes is withdrawn.
- **No meaning effect:** items 1–5 are representation, parsing or build mechanics of T18 as written (the one unit question is CR-024); item 6 reports a consequence of T18 and T8.1 and changes nothing.
- **Files/tests:** `adapters/oracle_truth.py`, `research/datasets/part3/t17_oracle.py`; `tests/adapters/test_t17_oracle_truth.py` (`test_t18_*`), `tests/events/test_t18_oracle_absence.py`. **Reverse:** item 2: drop the key; item 4: change `run_length_summary`; item 5: run the driver without the two reuse arguments.

## AR-56 — Representation details of T19 and the POW sensitivity counts (T-18, T-20)   status: ACCEPTED (G-PR rulings, 14 Nov 2026, D-34), item 2 as revised by T20.1 (E-1.2.18): a run lies between two dataset-visible eligible frames; the E-1.2.17 reading is kept only as the `legacy_e_1_2_17` diagnostic that lists changed outcomes
- **Gaps and choices** (none changes a T17, T18 or T19 rule):
  1. **Counts.** In a run of at most g_max eligible frames, an ineligible frame gets no point and is counted as `not_eligible_in_run` (neither predicted nor lost). In a longer run every frame, eligible or not, is counted as lost ("lost on every frame") and in `lost_long_run`. A visible frame that is not eligible still yields a tracked point in `camera_tracks`; `s3_truth` leaves it out, as before (AR-53 item 6), and the driver counts it (`points_on_ineligible_frames`).
  2. **Where a run ends. Review flag.** A run lies between two frames on which the dataset lists the object as visible (T17.2), whether or not those frames are eligible; T19 changes how its length is counted, not where it ends. So two runs of 10 eligible frames on either side of a visible but ineligible frame are two runs of 10, although S4 then sees 20 consecutive eligible frames without a point (a T8.1 gap of 20). The other reading (a run ends only at an eligible visible frame) would make the oracle run equal to the T8.1 gap in every case. The driver counts the eligible frames whose outcome would differ (`frames_in_runs_merged_across_ineligible_visible`); the totals are in the Progress log. If the count on held data is not 0, or the Architect prefers the other reading, this item becomes a CR. Pinned by `test_t19_a_visible_frame_that_is_not_eligible_still_ends_a_run_ar_56`.
  3. **Run-length statistics** are in eligible frames (the unit of the rule). A run whose frames are all ineligible has length 0 and is kept in the table.
  4. **POW sensitivity counts (ruling C).** For g ∈ {5, 15, 30, 60} the driver builds the oracle points with g_max = g and then the T8.1 POWs of every person–forklift pair of each camera with the same g (`pows.build`, eligible frames and coverage of the recording's S1 artifact), and counts the POWs and those with `end_reason = gap_exceeded`. No geometry, no S4 artifact, no rule, no reference. Reprojections are computed once per camera and reused across the four values (`cache`).
  5. **Labels.** The rebuilt S3 artifacts carry contract label E-1.2.17; S0 and S1 keep E-1.2.15 (AR-55 item 5).
- **No meaning effect:** items 1 and 3–5 are counting and build mechanics; item 2 is flagged.
- **Files/tests:** `adapters/oracle_truth.py`, `research/datasets/part3/t17_oracle.py`; `tests/adapters/test_t17_oracle_truth.py` (`test_t19_*`, `test_reprojection_cache_gives_the_same_tracks`). **Reverse:** item 2: build runs from eligible visible frames in `camera_tracks`.

## AR-57 — Representation details of the G-PR freeze (X0b, V0, acceptance criteria; D-34, D-35)   status: ACCEPTED in full (Owner, 14 Nov 2026). Note on item 9 (Owner): adding Warehouse_001 to a frozen split is not a PR-01 revision (SP-03 requires an audit violation); at M1b, raise a CR on how new recordings join a frozen split before doing it
- **Gaps and choices** (none changes a measured value, partition count, criterion target or rule):
  1. **Draw mechanics.** D-35 fixes the strata, counts, seed, sort order and generator. Not stated: the order in which families draw from the generator. One PCG64 generator seeded once with 2026111401; families in sorted name order; `rng.choice(N_f, n_f, replace=False)` on the runs sorted by ext_run_id (`splits/draw.py`, same mechanism as `sampling.draw_res`). Alternative: a fresh generator per family. Pinned by `tests/splits/test_draw.py`.
  2. **Where the derivation lives in the X0b record.** `split_manifest` has fixed columns (E-1.2.1 §5) and no free field. The derivation of the family is a split-draw configuration record (`sdr_` ID = id(record), `prereg.SPLIT_DRAW_RECORD`) named in the X0b artifact's `config_ids`, with the seed in its `seeds`; the record itself is in `docs/preregistration/freeze_record.json` and `src/rq1/pipeline/prereg.py`. So the X0b artifact ID changes if the derivation text changes.
  3. **One sampling plan per dataset row and partition** (ACCEPTED): `m1a-sdg-validation`, `m1a-sdg-test`, `m1a-smartspaces_000-validation`. `plan_rows` gains `population_definition_ref` (default unchanged, so M0 IDs are unchanged); M1a plans state the partition, the dataset row and "camera groups with usable truth (T17.4)".
  4. **Census seed.** A census draws nothing, but the plan record needs a seed: the split seed 2026111401.
  5. **MR-01 as a value.** `exact_equal` compares a value with the target: MR-01 = 1.0 when every exact-class payload hash of the second run equals the first, else 0.0; target 1.0. `estimand` is required: `frame_description` (no interval is used, §9.6 / AR-44).
  6. **frozen_utc** is a supplied event time taken once from the clock at the freeze, 2026-11-15T01:47:59Z (14 Nov local time), written as a constant so that payloads stay deterministic (as AR-7).
  7. **Criterion #2 = one record per viewpoint class** (ACCEPTED): `C2-GV-01-ceiling`, `C2-GV-01-eye_level`. Slices are string maps: dataset row, partition `test`, geometry method, statistic, viewpoint class / w_v.
  8. **Frame.** The SDG recordings without usable truth (T17.4; 23) are outside the frame; their IDs are listed per plan in the freeze record. This follows T17.4 (outside the oracle and reference populations).
  9. **X0b v1 = SDG + Warehouse_000** (Owner answer, 14 Nov 2026): one data_origin per file (VR-E-005). Warehouse_001 is validation through its leakage edge to Warehouse_000 (T16.2) and enters at M1b as a new split version that keeps it with Warehouse_000 (a split that separates them raises ERR-LEAKAGE, `test_t16_scene_and_its_re_render_are_one_leakage_group`).
  10. **Manifest data_origin** of the X0b and V0 artifacts: `synthetic_rendered` (all their recordings).
- **Files/tests:** `splits/draw.py`, `pipeline/prereg.py`, `sampling/plan.py`, `research/preregistration/freeze.py`; `tests/splits/test_draw.py`, `tests/pipeline/test_prereg.py`. **Reverse:** items 1, 2, 4–6, 10 change only IDs; re-run the freeze script.

## CR-025 (2026-11-14) — How CV-SIM builds the O/H/PC interaction references from simulator truth (T-21)   status: CLOSED (Appendix T T21, E-1.2.19: readings 1(a), 2(a), 2(c); Dodge not used as a reference)
**Raised by:** implementation agent. **Task:** T-21 (M1a validation run). **Contract sections:** F.1 A5.1 (`reference_class = rule_conformance`: "applying the system's own operational definitions (P, X, C, O/H/PC labels) to simulator truth or reference geometry"; RV-01); T17.6 (reference visible support); E-1.2.1 §5.8 (`ref_interaction`); Package F WP-14 ("EV-M1–M8 for O/H/PC against definition-applied references"; plan, not contract).
**Meaning-affecting:** yes. The reference interactions are the denominator of EV-M1 and the matching target of EV-M2–M8.
**Problem.** `SimReferenceConverter` takes `truth["interactions"]` as given. For M0 they were written by hand. For SDG and SmartSpaces nothing in the contract says how they are produced. Readings that give different numbers:
1. **Which positions and frames.** (a) The full simulator pose on every frame of the object's presence (no visibility limit). (b) Only the reference-visible frames of T17.6. (c) The same oracle points the system sees (tracked + predicted), which makes reference and system identical by construction.
2. **Which definitions and parameters.** (a) One reference set from the base v1 parameters with every provider (P = R2, X = R3 + R4, C as BL-6), used for every BL configuration. (b) One reference per configuration, with that configuration's providers. For the MR-08/MR-12 sweeps: (c) the reference stays at the base values, or (d) moves with the swept parameter.
3. **Evasive action.** WP-14 compares R5 to the SDG `Dodge` annotation "where present". The mapping from `Dodge` records to `ref_interaction` labels or windows is not defined.
**Not blocked by this CR:** S3–S5 on validation, CM-01–CM-10 (reference visibility is defined by T17.6), GV-01 and GV-03–GV-08 (simulator positions), MR-01, MR-08–MR-12 (label stability between configurations).
**Agent's recommendation:** 1(a) with 2(a) and 2(c). The reference applies the definitions to the complete truth, so EV-M then measures what the oracle path loses (visibility, T18 lost runs, eligibility, lifecycle). 1(c) would make EV-M = 1 by construction. For item 3: no recommendation; the `Dodge` fields need to be described first.

## AR-58 — Faster R4 pet_pred search and speed-only changes in S4 and S5 (T-21; D-38 A.1, revises the AR-49 item 1 method)   status: ACCEPTED (G-M1a, D-40) (Owner-authorised under D-38 A.1). **D-38 A.1 acceptance met** on all SDG validation pair-frames (15 Nov 2026; `research/m1a/r4_equivalence_summary.json`): 226 cameras, 59,267 pair-frames in each of the two geometries; pet_pred_s differs on 1,725 values, max 9.35e-7 s; every other pair_series field (ttc_s included) and every null reason identical; every flag_series row (all C_by_R4 values) and every episode (labels, boundaries) of BL-2 to BL-6 identical; only derived IDs differ
- **Gap.** At the AR-49 method's cost (about 50 ms per pair-frame in S4, 70 % in the R4 `pet_pred` search) the SmartSpaces run does not fit (D-38). D-38 A.1 authorises a code-only speed-up, with the acceptance rule: on the fixtures, randomized cases and all SDG validation pair-frames, every C_by_R4 value and every downstream S5 flag, label and episode boundary identical to the code before it; ttc_s and pet_pred_s within 1e-6 s; nulls and null reasons identical; bit-identity not required.
- **Choices:**
  1. **pet_pred search (`substrate/surrogate.py`).** The method of AR-49 item 1 is kept (golden-section minimiser of the shape gap, then bisection to 1e-6 s on each side, inside end returned, touching counts), with two changes: (i) gap(F + v t, G) is evaluated as the distance from the point v t to the Minkowski difference G − F (one convex polygon built once per occupancy) minus both radii, which is the same quantity (dist(F + d, G) = dist(d, G − F) for convex F, G); (ii) the golden-section loop stops when its bracket stops changing (a fixed point: every later iteration would repeat it, so (ii) alone is bit-identical). (i) changes float rounding only, so a bisection step can fall on the other side of a boundary within about 1e-15 of it; values then differ by less than the 1e-6 s tolerance. Considered: closed-form ray–polygon intersection (exact boundaries, but each bound would move by up to 1e-6 s against the AR-49 values, and pet_pred, a difference of two bounds, by up to 2e-6 s, outside the D-38 tolerance). The AR-49 method is kept unchanged and unused in `substrate/surrogate_ar49.py` for the equivalence tests.
  2. **T8.3 minimiser (`geometry.predict_min_clearance`).** The same fixed-point exit. Bit-identical (pinned by a test that writes out the 200-iteration loop).
  3. **Artifact hashing (`ids/artifact.py`, `schema/registry.py`).** The payload-column set of a table and the forbidden-name check are cached per (table, column); the schema registry is static. Hash input bytes unchanged.
  4. **S4 builder (`substrate/builder.py`).** Each track's eligible point states and the classes tracked on each frame are indexed once, instead of scanning every track point for each person–forklift pair and for each frame (quadratic on SmartSpaces); the frames of a POW are sliced from one sorted list. Same rows, same order.
  5. **S5 (`events/providers.py`, `events/s5.py`).** An `S4Index` built once per S5 build replaces the per-POW scans of the pow, object_state and pair_series tables; each track's T9.1 runs are prepared once; the T9.2 rates are computed only on the POW's own frames (each frame's rates depend on that frame alone). `flag_frames` without an index behaves as before.
  6. **S5 crash fix (`events/s5.py`).** S5 sorted every S1 frame by `frame_index`, which is null on an ineligible frame, so S5 failed on any recording with an ineligible frame (found on SDG validation cameras; no fixture had one). Ineligible frames now sort after the eligible ones; only eligibility and the recording are read from that list. The same one-line fix is applied to the copy of the old code used for the equivalence check, so that both sides run on those cameras.
- **No meaning effect:** no definition, parameter, unit, tolerance or rule changes; items 2–6 change no value; item 1 changes ttc_s / pet_pred_s by at most the T15.2 tolerance, and the D-38 A.1 acceptance check decides whether any flag, label or episode boundary moved.
- **Files/tests:** files above; `tests/substrate/test_ar58_r4_speedup.py` (2,000 seeded random cases and the T15 fixture geometries against `surrogate_ar49`: nulls identical, |Δ| ≤ 1e-6 s; C_by_R4 identical on 1,000 cases × 3 pet_max; both fixed-point exits bit-identical; Minkowski gap = polygon gap to 1e-12 m), `tests/events/test_ar58_s5_index.py` (indexed `flag_frames` equal to the scans on the N2 and T15 fixtures for four provider sets; S5 on a recording with an ineligible frame). SDG check: `research/m1a/r4_equivalence.py` (old tree = commit 5780320 + item 6), summary `research/m1a/r4_equivalence_summary.json`.
- **Reverse:** restore `surrogate.py` from `surrogate_ar49.py` (values move back within 1e-6 s); remove the caches and indexes (no value changes); item 6 cannot be reversed without restoring the crash.
- **G-M1a ruling (17 Nov 2026, D-40 item 4):** ACCEPTED.

## AR-59 — Representation details of the T21 references, GV metrics and the M1a evaluation (T-21; D-38 item C, T21)   status: DECIDED (G-M1a, D-40: items 2, 6, 7 accepted; item 5 revised) — items 2, 5, 6 and 7 are REVIEW FLAGS (a reading that could change a number)
- **Gaps and choices:**
  1. **Oracle track ↔ object key.** ORACLE-S3 tracks carry no physical identity. The evaluation recovers it from the T17 construction: `camera_tracks` keeps the objects with a T20.1 visible frame, `s3_truth` numbers them 1.. in str order; the T21 reference S3 numbers every object with a pose on an eligible frame the same way. Every mapping is checked against the track class (a mismatch stops the run). Association (A5.2) then runs as in M0: system boxes = ORACLE-S3 points (not lost), reference boxes = its tracked points (identical to T17.6 `reference_objects`); event pairs by `association.event_pair`.
  2. **REVIEW FLAG — T21.1 "whatever their visibility".** Each reference object gets a `tracked` (detected) point on every eligible frame with a pose, with a box inside the image that is never truncated, so visibility does not enter the reference through the T8.6 evidence state or T8.7 Q; visibility enters only through T21.3 assessability. The box carries no image measurement (only R1 reads boxes; BL-6 does not use R1). The other reading — the dataset's own visibility deciding Q on the reference — would make the reference depend on visibility, which T21.1 excludes.
  3. **Reference geometry for CM.** CM-02's reference-moving frames: forklift speed > v_min in the T21 reference S4 (simulator positions, base w_v). CM-06's reference clearance: the T21 reference S4 pair-series clearance. Reference interaction IDs `rin_` are content IDs over recording, pair keys, frame interval and the reference S5 artifact ID, so every sweep grid point is scored against the same IDs (T21.4).
  4. **Sweeps.** The pre-registration does not say which configuration a grid point runs under; every grid point runs under BL-2 to BL-6 (no choice made). Grid-point artifacts are stored as one bundle per camera (gzip pickle of complete artifacts: spec, tables, IDs; any of them can be rebuilt and checked against its ID); base, full_camera and reference artifacts are artifact directories. S5 also runs on the full_camera S4 (for GV-06).
  5. **REVIEW FLAG — GV-04.** "Clearance from the prior footprint minus clearance from the simulator 3D box footprint": both clearances at the full_camera positions and yaw of the pair-frame (pre-registration section 7 puts GV-04 on the full_camera run), the second with the length and width of the forklift's simulator box floor on that frame. It isolates the footprint shape. Other reading: the second clearance at the simulator pose (then GV-04 also contains position error, which GV-01 already reports).
  6. **REVIEW FLAG — GV-07.** Speed error = full_camera speed minus simulator_truth speed at the same w_v (both from the S4 velocity fit, T8.3), so the error is that of the positions, not of the smoothing. Other reading: against an unsmoothed simulator speed (finite differences), which would add the smoothing bias to the error.
  7. **REVIEW FLAG — GV-08.** Realized minimum clearance over [t, t + τ] = the minimum measured clearance of the same POW on the same (full_camera) run over frames with t_k in [t, t + τ]; null when [t, t + τ] runs past the POW's last frame (not observed). This isolates the constant-velocity prediction. Other reading: realized clearance from simulator truth (then GV-08 also contains the geometry error).
  8. **EV-M3 and EV-M7 inputs.** EV-M3 support form: episode support = episode span, POW support = POW span (T10.7(d) names no support field). EV-M7 u = clipped eligible support of the window (s → h). Windows: the frozen V0 windows (SDG: one per camera, 10 s, weight 1); weighted and unweighted values coincide in a census.
  9. **Summaries.** Percentiles by numpy "linear" (as EV-M8, T10.7); GV-01 per class × evidence class × viewpoint and pooled; RMSE intervals from the bootstrap of the mean square (square root of its percentile bounds); bias intervals from the bootstrap of the mean. Target A = stratified window bootstrap, Target B = cluster bootstrap over leakage groups (N5), B 2000, seed 2026111402.
  10. **MR-08 label stability.** A base episode is matched, at each grid point, to the same-pair episode of highest temporal IoU (ties: earliest start) if IoU ≥ iou_m; stable iff the label sets are identical. Reported per parameter family and over all grid points; GV-03 label flip rate = 1 − stability at one footprint grid point. Elasticity between the base and each neighbour, on totals over cameras.
  11. **Not computable on these data (reported, not estimated):** GV-05 / MR-11 (the full_camera positions carry no covariance), MR-10 (no calibration covariance), CM-09 on the detected basis (no inferred frames by definition). On the oracle path CM-09 is 0 by construction (predicted points have no reference box, T17.6).
- **No meaning effect claimed for items 1, 3, 4, 8–11** (representation, storage, summaries). Items 2, 5, 6, 7 are readings of the contract text and are flagged; each reverses by one function.
- **Files/tests:** `research/m1a/run_m1a.py` (`unit_reference`), `research/m1a/m1a_common.py` (`reference_tracks`, `visible_frames`, `truth_table`), `research/m1a/evaluate_m1a.py`, `research/m1a/aggregate_m1a.py`, `src/rq1/evaluation/gv.py`; `tests/m1a/test_t21_references.py` (the four T21 tests), `tests/m1a/test_m1a_driver.py`, `tests/evaluation/test_gv.py`.
- **Reverse:** per item, in the named function.
- **G-M1a rulings (17 Nov 2026, D-40 item 4):**
  - item 2 ACCEPTED (complete-truth reference, as T21.1);
  - item 5 REVISED: GV-04 is computed at simulator positions (same positions, prior footprint vs simulator 3D-box footprint) and re-reported (`research/m1a/gv_revised.py`, `gv_revised_{sdg,smartspaces}.json`); the earlier full_camera-position values are superseded;
  - item 6 ACCEPTED;
  - item 7 ACCEPTED, and GV-08 is also reported against the simulator-truth clearance series (same files).

## AR-60 — Speed-only indexes in the S8 completeness, association summary and GV-08 helpers (T-21; same kind as AR-58)   status: ACCEPTED (G-M1a, D-40). Equivalence: 501 seeded random cases identical to the pre-AR-60 code; 5 real cameras (3 SDG, 2 SmartSpaces) give repr-identical evaluation outputs (`research/m1a/ar60_equivalence.jsonl`)
- **Gap.** The SmartSpaces evaluation (`evaluate_m1a.py … cameras`, CM per window and GV) grew much faster than camera size: 35 min for `rec_dazuru…`, 5.4 h for `rec_bg7m…`, and `rec_gbhz7…` was still not finished after about 34 h (stopped by the Owner on 17 Nov 2026). Cause: helpers that rescan whole tables on every call: `completeness._covered` rebuilt the matched-frame index once per (pair, frame); `_attributed` scanned all association rows once per POW frame (CM-05, CM-06, CM-07; CM-07 once more per co-presence interval); `reference_pairs` / `_covisible` / `_units` were rebuilt per metric and basis; `association.summarize` scanned the matched rows once per track (CM-10); `gv.realized_min` copied the rest of the POW series for every frame (GV-08). The contract says nothing about how these are computed.
- **Options:** (a) leave as is (about 70 h or more for the remaining 13 cameras, rough extrapolation); (b) build each lookup once per window and keep the same computation order; (c) parallelise. Chose (b).
- **Choice.** `WindowFrames` carries a private `_index` dict (not part of equality, repr or the constructor), filled on first use with: frame → {identity: track} and frame → {track: identity} over matched rows (built in row order, so a later row of a frame overrides an earlier one, as before); identity → visible frames (`_covisible` = sorted intersection); frame → {(person track, forklift track)} of the POWs whose pair-frame is in the basis (`_covered`); the POW frames of each basis, and the same grouped by attributed pair in the same order (CM-06 sums in the old order; CM-07 counts distinct POWs per interval from frame → POWs). `summarize` groups matched rows by track once. `realized_min` stops at the first frame past the horizon (its series is in time order, as its docstring requires). `evaluate_camera` accepts an optional output path (used only by the equivalence check).
- **No meaning effect:** no definition, parameter, unit, order of summation or rule changes; outputs identical (tests and real-data check above). The window's input fields must not be mutated after a metric has been computed on it; no caller does.
- **Files/tests:** `src/rq1/evaluation/completeness.py`, `association.py`, `gv.py`, `research/m1a/evaluate_m1a.py`; `tests/evaluation/test_ar60_eval_index.py` against frozen copies in `tests/evaluation/reference_pre_ar60/` (commit 636b311); `research/m1a/ar60_equivalence.py` (re-evaluates finished cameras into a scratch folder and compares; never overwrites `out/`).
- **Reverse:** restore the three modules from `tests/evaluation/reference_pre_ar60/` (no value changes).
- **G-M1a ruling (17 Nov 2026, D-40 item 4):** ACCEPTED.

## AR-62 — Representation details of the detector-path S2 and S3 adapters and of IDF1 (T-23, S2 stage; D-45 items 1 and 2)   status: ACCEPTED (D-47, 19 Nov 2026: all nine items; the report states IDF1 pooling and reports the birth-frame and score-band counts)
- **Gap.** D-45 fixes the detector, thresholds, tracker and the bridging rule. Some representation details are left open: the class order of det_index, the license_component row of the weights, which box a `tracked` point carries, local track IDs, how ByteTrack runs without the `lap` package, how IDF1 is computed without TrackEval, and which frames of a new track the tracker reports.
- **Choices.**
  1. **det_index "order by class"** (E-1.2.1 section 5.4): class rank in the `object_class` enum (person before forklift), then descending score, x1, y1. Alternative: alphabetical (forklift first). It is an identifier only; no value depends on it. Test: `tests/m1b/test_s2_detector.py`.
  2. **license_component of the weights:** component = file name, version = `sha256:<hex>`, component_type model_weights, licence label from `NOTICE.md` (AGPL-3.0 for `yolov8s-worldv2.pt`), terms_location license_file, the source URL in `obligations`, licence_status verified, decision_ref D-43. `model_component_id` = its anchor ID (F.1 A1.2). Test: `test_s2_detector.py`.
  3. **REVIEW FLAG: the box of a `tracked` point** is the matched detection's own box (`bbox_xyxy_px` of the `detection` row its `detection_id` names). A `predicted` point carries the tracker's Kalman-predicted box for that frame. Basis: T8.6 classes a track point as truncated when "the detection box is within 1 px of an image border", so the box on a tracked point is the detection box. Alternative: the tracker's filtered (Kalman-updated) box on matched frames too. That would move the foot points and so the full_camera positions slightly. Test: `tests/m1b/test_s3_detector_path.py`.
  4. **Local track IDs:** 1.. over class rank (person, forklift), then first frame, then tracker ID. Identifier only.
  5. **REVIEW FLAG: ByteTrack without `trackers` or `lap`.**
     - The Apache-2.0 `trackers` package (2.0.0 and 2.0.1) needs numpy >= 2.0.2. torch 2.2.2 in `.venv-det` is built against numpy 1.x, so installing it would break the detector environment. D-45 item 1 therefore falls back to Ultralytics' built-in ByteTrack (8.4.215, AGPL-3.0 accepted under D-43).
     - Ultralytics imports the optional `lap` package for its assignment step. `lap` is not installed and its install is not pre-approved. The adapter uses Ultralytics' own documented alternative, `linear_assignment(..., use_lap=False)`, which calls `ultralytics.utils.ops.linear_sum_assignment` (a NumPy port of SciPy's solver). A stub `lap` module satisfies the import and raises if it is ever called.
     - Ultralytics states that the two solvers return the same minimum-cost assignment and can differ only under exact ties. lapjv's `cost_limit` and the NumPy path's `min(cost, thresh)` treat costs at the threshold slightly differently.
     - Tracker parameters are the installed `bytetrack.yaml` defaults, recorded in every S3 run configuration. Tests: `tests/m1b/test_tracking_bytetrack.py` (`test_config_is_the_installed_default`, `test_numpy_assignment_path`).
  6. **REVIEW FLAG: IDF1.** F.1 names TrackEval as normative for IDF1. TrackEval is not installed (not pre-approved). `research/m1b/idf1.py` is a line-for-line port of TrackEval's `Identity.eval_sequence`, with box IoU as similarity and threshold iou_cm = 0.5 (F.1 A5.2), per class. Hand-computed tests: `test_s3_detector_path.py` (toy case 0.444444; swap fixture 0.5).
  7. **REVIEW FLAG: frames the tracker reports.**
     - A `tracked` point is a frame on which ByteTrack reports the track, i.e. matched to a detection that frame. ByteTrack does not report a track started after the first frame until its second match, so the first detection of such a track is not a point. This is the tracker's standard output; adding that frame afterwards would be a change to the tracker.
     - The tracker steps once per eligible frame, and ineligible frames are not shown to it. Bridges are therefore counted in eligible frames, as T19 and T8.1 count gaps, and a Kalman step spans any ineligible frames between two eligible ones.
     - Test: `test_tracking_bytetrack.py` (`test_f1_fragment_after_long_dropout`: the new track's first point is the frame after it reappears).
  8. **Predicted box with no area:** no point, counted as `predicted_degenerate`. A predicted point needs a valid CF-IMG box (`@bbox`). This is expected to be rare; its count is reported.
  9. **`track.n_gaps` / `max_gap_frames`:** counted over all frame indices of the track span, as the oracle source (`rq1.substrate.oracle`) counts them. Descriptive fields only; not used by S4.
- **No meaning effect claimed for items 1, 2, 4, 8 and 9.** Items 3, 5, 6 and 7 are flagged because another reading could move a reported number. None of them changes a definition, parameter, threshold or rule in E-1.2.21. Every rule D-45 fixes is applied as written.
- **Files:** `src/rq1/perception/s2.py`, `src/rq1/tracking/{bridging,bytetrack,s3}.py`, `src/rq1/fixtures/oracle_detections.py`, `research/m1b/idf1.py`; tests in `tests/m1b/`.
- **Reverse:** item 3, use the tracker box on matched frames in `bytetrack.run_class`; item 5, install `lap` (Owner approval) and remove the stub and patch; item 6, install TrackEval (Owner approval) and compare; item 7, add each track's birth detection in `bridging`. S2 output (the expensive step) is unaffected by items 3–9, so S3 onward can be re-run in minutes.

## CR-026 (2026-11-17) — full_camera foot rays: a range condition for a floor position (T-21, G-M1a diagnosis)   status: CLOSED (superseded by Appendix T T24.2, E-1.2.25; Owner decision D-54, 23 Nov 2026); earlier OPEN (no fixed range rule, D-40 item 6), pre-registration v2 input together with CR-007 and CR-029 (D-50 item 4)
**Raised by:** implementation agent, on the Architect's instruction of 17 Nov 2026 ("if (5) shows that such rays produce numeric positions, raise a CR"). **Task:** T-21. **Contract sections:** E-1.2.1 §2 null-reason enum (closed list: not_applicable, not_observable, uncalibrated, upstream_failure, not_supplied, not_computed_by_config, withheld_privacy, pending_review, out_of_scope_rq1); `object_state.x_m?`, `y_m?`; track_point `foot_point_px`; GV-01 (F.1 N7).
**Meaning-affecting:** yes. The rule changes which object-frames have a position, so it changes every S4 quantity built on positions (clearance, speed, R2–R5 flags), GV-01, GV-07, GV-08 and their denominators.
**Current behaviour (`geometry.full_camera_to_floor`, `substrate/builder.py` `_object_states`).**
- The foot point is the bottom-centre of the track box.
- The ray through the foot point is intersected with z = 0. When |d_z| < 1e-12 (parallel), or when the intersection parameter is s ≤ 0 (the floor is met behind the camera, which for a camera above the floor means a ray at or above the horizon), the function returns None.
- The builder then writes x_m = y_m = null with null reason `not_observable`.
- **There is no range limit.** Any ray below the horizon gives a numeric position, however far away.
**Evidence** (validation only; full_camera S4 of run1; recomputed positions equal the stored ones on all 2,071,041 points; `research/m1a/position_diagnosis_{sdg,smartspaces}.json`, `research/m1a/position_cutoffs.json`):
- **Rays at or above the horizon:** SDG 611, SmartSpaces 8,895, all tracked points. All are null (`not_observable`); none produce a number. Parallel rays: 0.
- **Rays meeting the floor in front beyond 50 m:** SDG 386 (0.31 % of GV-01 points; 230 beyond 100 m; 17 beyond 1 km), SmartSpaces 974,217 (50 %; 303,325 beyond 100 m; 493 beyond 1 km, whose errors reach P99 2,989 km). **These produce numeric positions.**
- SDG: those 386 points carry 99.9 % of the GV-01 squared error. RMSE 44.8 m with them, 1.34 m without. No SDG object is more than 20 m from its camera.
- SmartSpaces: the scene is large. 725,201 GV-01 points (37 %) are truly more than 50 m from the camera, and predicted points beyond 50 m (12,317) are accurate (predicted P99 1.58 m overall).
- The large errors come from tracked points whose visible box ends above the 3D box's bottom edge (feet hidden; SmartSpaces median error 20 m at 10–50 px, 34 m at 50–200 px), on shallow rays (median 111 m below 1°, 35 m at 1–2°, 1.0 m at 2–5°). Tracked points with the bottom edge within 2 px and not on a border: SmartSpaces median 0.30 m, P99 0.93 m.
**What a limit would remove** (GV-01 points nulled, of which error ≤ 1 m / > 10 m; error of the kept points):

| rule | SDG nulled (≤ 1 m / > 10 m) | SDG kept P99, RMSE | SmartSpaces nulled (≤ 1 m / > 10 m) | SmartSpaces kept P99, RMSE |
|---|---|---|---|---|
| none | 0 | 2.60 m, 44.8 m | 0 | 209 m, 12,520 m |
| range > 20 m | 559 (0 / 555) | 1.83 m, 0.92 m | 1,662,833 = 86 % (778,777 / 663,700) | 6.2 m, 1.18 m |
| range > 50 m | 386 (0 / 386) | 1.99 m, 1.34 m | 974,217 = 50 % (239,502 / 625,376) | 17.1 m, 3.77 m |
| range > 100 m | 230 (0 / 230) | 2.19 m, 2.96 m | 303,325 = 16 % (16 / 300,682) | 46.7 m, 13.0 m |
| angle < 2° | 480 (0 / 480) | 1.89 m, 1.01 m | 435,336 = 22 % (29,089 / 393,824) | 41.1 m, 10.5 m |
| angle < 3° | 538 (0 / 536) | 1.85 m, 0.94 m | 734,871 = 38 % (119,445 / 566,264) | 23.7 m, 5.46 m |

**Proposed rule (for the Architect to word and parameterise):** a full_camera (and ground-plane homography) floor position exists only when the foot ray meets the floor in front of the camera at a horizontal range ≤ R_max; otherwise x_m, y_m are null with a stated reason.
**Open choices (each changes numbers):**
1. **The value of R_max, and where it lives.** A single fixed value does not fit both datasets:
   - 50 m removes only wrong SDG positions;
   - on SmartSpaces, 50 m removes 239,502 positions that are correct within 1 m, and 100 m still leaves P99 47 m.
   - Options: (a) a fixed contract value; (b) a per-site parameter tied to the floor extent of the calibrated area (registered with the calibration); (c) a ray-angle limit instead of, or in addition to, R_max. (c) is a proxy for the metres-per-pixel sensitivity at the foot point, but it depends on camera height.
2. **The null reason.** The enum is closed:
   - (a) reuse `not_observable`, as for rays at or above the horizon today;
   - (b) add a new value (e.g. `out_of_range`) by amendment.
3. **Scope.** Should the rule also cover the homography tier (`homography_to_floor` returns None only when w ≤ 0)?

**Stated limitation:** no range rule fixes the mid-range SmartSpaces errors from hidden feet (kept P99 17 m at R_max 50 m). They come from the foot point (visible-box bottom), not from the ray. That is a separate question (foot-point source when the bottom edge is occluded) and is not proposed here.
**Agent's recommendation:** 1(b) with 2(b), so the null is distinguishable from not-visible. Decide 3 together with 1.
**Not implemented.** No code, value or definition changed. Until decided, GV-01, GV-07 and GV-08 are reported as computed, with this diagnosis beside them.
- **Owner ruling (G-M1a, 17 Nov 2026, D-40 item 6):** a fixed range rule is NOT adopted. CR-026 stays open; the Architect writes the rule for v2/M1b. Two further diagnostics were run (validation only, statistics only, nothing in the pipeline changed): `research/m1a/position_sensitivity.py` → `research/m1a/position_sensitivity_{sdg,smartspaces}.json`. Rows are identical to `position_diagnosis.py` (count and errors checked on every camera). The analytic Jacobian matches finite differences (relative difference 2e-6).
- **(a) Pixel sensitivity** = largest singular value of the 2 × 2 Jacobian of the floor intersection with respect to the foot pixel (m of ground displacement per px).
  - Distribution over GV-01 points: SDG median 0.009, P90 0.029, P99 0.070 m/px; SmartSpaces median 0.449, P90 3.22, P99 19.2 m/px.
  - Error by sensitivity (median error): SDG below 0.1 m/px ≤ 0.62 m, 0.1–0.2 m/px 7.8 m, 0.5–1 m/px 28 m, ≥ 1 m/px 96 m. SmartSpaces below 0.2 m/px ≤ 0.44 m, 0.2–0.5 m/px 0.43 m (P90 11.9 m), 0.5–1 m/px 5.1 m, ≥ 1 m/px 39 m.
  - Limits (points with sensitivity above the limit would be null). Each cell gives: flagged share / share of errors > 2 m caught / share of errors > 10 m caught / share of good points (< 1 m) lost. Kept P99 is the 99th percentile error of the points that remain.

| limit (m/px) | SDG | SDG kept P99 | SmartSpaces | SmartSpaces kept P99 |
|---|---|---|---|---|
| 0.05 | 2.7 % / 53.9 % / 100.0 % / 1.96 % | 1.65 m | 90.1 % / 99.0 % / 100.0 % / 82.98 % | 3.31 m |
| 0.1 | 0.5 % / 41.1 % / 96.8 % / 0.02 % | 1.74 m | 80.7 % / 97.6 % / 99.9 % / 66.79 % | 6.05 m |
| 0.2 | 0.4 % / 33.6 % / 88.2 % / 0.00 % | 1.83 m | 68.3 % / 93.5 % / 99.5 % / 47.34 % | 9.05 m |
| 0.5 | 0.4 % / 29.3 % / 77.7 % / 0.00 % | 1.89 m | 44.4 % / 78.0 % / 90.3 % / 18.12 % | 18.42 m |

  - Denominators: SDG 1,639 errors > 2 m, 618 > 10 m, 87,777 good. SmartSpaces 845,977 > 2 m, 663,815 > 10 m, 1,023,492 good.
  - Reading: sensitivity separates almost perfectly on SDG (0.1 m/px: 96.8 % of the > 10 m errors caught, 0.02 % of good points lost). On SmartSpaces every limit trades off: 0.5 m/px catches 90 % and loses 18 %; 0.2 m/px catches 99.5 % and loses 47 %. Many correct SmartSpaces positions lie at high sensitivity (far objects), so sensitivity alone cannot tell them from the wrong ones.
- **(b) Height consistency (tracked persons).** A second position comes from the box top-centre and a head-height prior H (ray meets z = H). The disagreement is its horizontal distance from the foot-based position. Each cell gives the share flagged among bottom-edge offset ≤ 2 px / > 10 px:
  - SDG at cut 2 m: H 1.6: 9.6 % / 20.4 % · H 1.75: 5.6 % / 28.4 % · H 1.9: 29.9 % / 39.1 %.
  - SmartSpaces at cut 2 m: H 1.6: 81.1 % / 88.5 % · H 1.75: 72.9 % / 88.0 % · H 1.9: 64.6 % / 90.0 %.
  - At H = 1.75 m and cut-offs 0.5 / 1 / 2 / 5 m: SDG 29.3 % / 48.6 % ; 24.3 % / 39.7 % ; 5.6 % / 28.4 % ; 2.9 % / 15.9 %; SmartSpaces 95.1 % / 97.0 % ; 88.2 % / 93.1 % ; 72.9 % / 88.0 % ; 37.8 % / 78.5 %.
  - The head-based estimate's own error at H = 1.75 m: SDG median 0.47 m, P90 9.0 m; SmartSpaces median 3.63 m, P90 25.0 m.
  - Reading: a weak separator, especially on SmartSpaces, where even feet-visible persons disagree by a median 3.6 m. The head ray is geometrically weaker than the foot ray. With the camera at height C_z, a head-height error ΔH moves the head-based point by about distance · ΔH / (C_z − H). SmartSpaces cameras are 2.0–4.8 m high and objects far away. On SDG, camera heights range from 1.0 m to 6.6 m, so some cameras sit below head height. This explanation follows from the geometry; it was not checked point by point.
- **Agent's summary for the Architect:** (a) is the stronger candidate. Sensitivity alone works where scenes are compact (SDG). Where they are large (SmartSpaces) it would also null many correct far positions; there it would need a signal of bottom-edge visibility, which a real detector does not supply directly. (b) is not usable as a stand-alone rule on these data. No rule implemented.

**Ruling (D-54, 23 Nov 2026):** closed as superseded by Appendix T **T24.2** (contract E-1.2.25): one global s_max, v2 candidate value 0.1 m/px (D5, tuning cameras: 94.2 % of errors above 10 m caught, 0.0 % of good points lost); selected, not frozen. A gated position reuses the existing codes (position null reason `not_observable`, clearance_state `unmeasurable_geometry_failure`); the marker is the stored sensitivity value `floor_resolution_m_per_px` (T24.2 (c)); no new null-reason value.

## CR-027 (2026-11-16) — The C-layer review and adjudication protocol is not defined (V-02)   status: CLOSED (superseded by Appendix T T22, E-1.2.20; Owner decision D-44 option (a), 19 Nov 2026)
**Raised by:** implementation agent. **Task:** V-02 (Reviewer and adjudication UI, Owner tooling; branch `v02-review-ui`). **Contract sections:** E-1.2.1 §5.8 (`reviewer_assessment`, `adjudication`, `validation_status_log`), §6 (label rules), §6.0 wording line ("reviewer-confirmed" only for adjudicated labels), §9 (ambiguous references "Tier 2 or unsure"; CV2), §11 item 5; F.1 A5.1 (`independent_expert_judgment`, RV-03), Appendix N4 (EV-M12, Tier 1 and Tier 2 separately); Appendix T T1 VR-E-053, FX-13 ("Two reviewers disagree — Tier 2 adjudication", active).
**Meaning-affecting:** yes. Each item decides a label, a status, a blind flag or which targets enter the EV-M12 denominator.
**Problem.** The tables exist and are implemented (T-01, T-11), but the procedure that fills them is not in the contract. V-02's reviewer and adjudication screens would have to enforce it. Details and readings: `research/review_ui/V-02_compatibility_audit.md`, section "Gaps".
- G1. Blindness for `system_episode` / `system_event` targets: may a blind reviewer in `reference` see the system-selected interval and pair?
- G2. How many independent assessments a target needs before it can be adjudicated (FX-13 implies two; D-23's subset rule covers A/B annotation only).
- G3. Which `validation_status_log.status` (confirmed, rejected, disputed) an adjudication writes, and against what.
- G4. Scale and range of `reviewer_assessment.confidence` (f64, no range).
- G5. Values of `adjudication.method` (contract: free `str`; V-02 text: agreement, consensus_meeting, adjudicator).
- G6. `config_id` (non-nullable) of a status-log entry whose target is a reference event.
- G7. The tier rule beyond "disagreement → Tier 2", and the `reference_class` of a C-layer adjudication.
- G8. Reviewer-facing definitions of nm, ud, ct, not_hazardous and unsure (the contract defines NM/UD/CT only as automated rules over system states).
**Not blocked by this CR:** everything on `m0-implementation`; the V-02 parts that need no protocol (status-log viewer and chain check, agreement arithmetic) are implemented already and are not worth building alone.
**Also noted (not blocking):** FX-13 is active and listed under WP-08 tests (Package F), but has no fixture or test; Q1 time-on-task has no field; Q2 `agreement_stat_ref` target undefined; Q4 V-02 on real footage needs its own decision.
**Agent's recommendation:** see D-44. Readings (a) in each row of the audit's gap table are the most direct readings of the text, but G3, G6 and G8 have no reading in the text at all and need Architect wording.
- **Closed (19 Nov 2026):** superseded by Appendix T **T22** (E-1.2.20), the Architect's protocol, approved by the Owner under D-44 option (a). G1 → T22.4; G2 → T22.6 (b); G3 → T22.8; G4 → T22.5 (b); G5 → T22.7 (e); G6 → T22.3 (c) and T22.8 (a) (ref_event targets write no status entry); G7 → T22.7 and T22.9; G8 → T22.5 (a). Q1 → T22.13 (`review_time_s`); Q2 → T22.10 (a) (`agreement_stat_ref` = batch_id); Q3 → FX-13, FX-13a to FX-13f as stated in T22; Q4 → T22.11. Entry copied from branch `v02-review-ui` so both branches agree.

## CR-029 (2026-11-19) — N9 rules 4 (geometry) and 5 (event reasoning) for an unmatched event on the detector path   status: OPEN for the Architect as a pre-registration v2 input (D-50 item 4; no rule implemented now)
**Raised by:** implementation agent. **Task:** T-25p, D-47 item 3. **Contract sections:** F.1 Appendix N9 rules 4 and 5; Appendix T T12.3; AR-42 item 5 (accepted: the rules take their comparisons as inputs).
**Meaning-affecting:** yes. The inputs decide which unmatched events get primary_stage geometry or event_reasoning instead of unresolved.
**Gap.** AR-42 item 5 fixes the form of the inputs: per frame, whether the decision differs, the clearance error, σ and M from the system and from the reference; and whether each run triggers. It notes that the comparisons need reference geometry, which "arrives with the M1a adapters". No text defines these inputs for a detector-path event that has no reference. Open points:
1. **Reference geometry for a detector-path pair.** Readings: (a) the simulator positions of the identities matched to the event's tracks, i.e. the column-A substrate of the same identity pair; (b) the T21 reference substrate (complete truth); (c) column B (oracle boxes, camera geometry), which isolates perception from geometry.
2. **"The flag decision"** compared per frame. Readings: (a) the pair-frame flag set the configuration uses (BL-6: R2-R5 and the evasive cue); (b) only the flag that made the event's label; (c) the episode-level decision.
3. **Frames.** Readings: (a) the event interval; (b) the event interval plus the guard; (c) the CA frame only.
4. **σ when the substrate supplies none** (`full_camera`, no covariance): rule 4 with σ = 0 fails on any non-zero clearance error where the decision differs. Readings: (a) apply as written (σ = 0); (b) rule 4 not evaluated when σ is null.
5. **Rule 5 for a false alert.** "Flags computed from reference geometry would trigger differently from the configuration's output given correct flags." Readings: (a) the configuration (BL-6) run on the reference-geometry flags of the same pair over the event interval produces no overlapping event; (b) T21 has no reference interaction of the pair overlapping the event. With BL-6-defined references, (b) makes rule 5 fail for almost every false alert (T21.5 circularity).
**Evidence:** N9 rules 1-3 on column C attribute only 2 of the 111 unmatched BL-6 events (both tracking). The other 109 have both tracks matched to the scene's worker and forklift at the event's CA frame. A descriptive cross-check (not an N9 rule) counts how many overlap a reference interaction of the same pair with temporal IoU below iou_m (`research/m1b/pilot_n9.json`, `same_pair_reference`).
**What proceeds meanwhile:** rules 1-3 are applied (FX-ID-8 reading, AR-42 items 1, 2 and 4). Rules 4 and 5 are `not_evaluated`, so "unresolved" in the pilot report means "not attributed by rules 1-3".
**Agent's recommendation:** none; the Architect defines. For reference: 1(a) and 2(a) need no new data, and 1(c) would need no new run either.

<!-- D-51 STEP 4 (c), 21 Nov 2026: the entries below are copied unchanged from `v02-review-ui`, with their decisions. Numbers D-48, D-49, D-51, CR-030, CR-031, AR-63 and AR-64 are shared by both branches; D-50, CR-029 and AR-62 are this branch's. Next free numbers on both branches: D-52, CR-032, AR-66. -->

## CR-030 (2026-11-19) — T23 points that change a count, a state or a statistic (W-01, D-48)   status: CLOSED (superseded by Appendix T T23.16–T23.27, E-1.2.23; Owner decision D-49, 20 Nov 2026)
Numbered CR-030 / AR-63 on `v02-review-ui` to avoid the numbers used on `m0-implementation` (CR-029, AR-62). Opened on `v02-review-ui`; contract E-1.2.22 (Appendix T T23) exists only on this branch until the Owner merges it. **Nothing below was chosen.** Where an indicator depends on an item, the application computes every reading listed and prints the value only when all readings agree; otherwise it prints "not determined: readings differ (CR-030 item n; ...)" with each reading's value (`rules.Readings`). Where a state or record depends on an item, the action is refused (ERR-SPEC, naming the item) or the record is not written.
1. **candidate_review adjudications cannot be stored (blocks part of T23.5 c, d).** T23.5 (c) writes one adjudication per member in candidate_review after sm_uphold, sm_overturn and sm_reclassify. T22.1 (b): candidate_review is "never given a reference_class". The schema source has `adjudication.reference_class` non-null (F.1 A5.1 field addition; nullability inferred, AR-era `True` flag), and `tests/schema/test_t22_review_time.py` pins the adjudication field list. Making it nullable would add a `reference_class_null_reason` column and change that pinned list, so the agent did not do it (CLAUDE.md: a mismatch with a test is a CR, never an edited expectation). **Now:** the SM actions change the state and write the report-log entry; no adjudication and no status entry is written; the report page says so (`store.CR030_1`). The FX-14a "then rejected" and FX-14b "status confirmed" checks are strict xfails. **Options:** (a) `adjudication.reference_class` nullable, null with `not_applicable` outside reference, required non-null in reference (VR check), the pinned list updated by the ruling; (b) a reference_class value for manager adjudications (none of the three fits A5.1); (c) another table for candidate_review adjudications.
2. **I4 scope and unit.** I2 says "over AI reports", I4 does not: (a) AI reports only, (b) all reports. After sm_reopen a report can be decided twice by the SM: (c) count actions, (d) the latest decision per report.
3. **I5 denominator and unit.** "recorded AI reports": (a) AI reports that reached `recorded` in P, (b) AI reports in `recorded` now (only sm_reclassify leaves `recorded`, so (b) excludes every reclassified report); numerator (c) reports reclassified, (d) reclassify actions. The readings agree when no report was reclassified.
4. **I6 age.** Pending since (a) the report's creation, (b) entering the current pending state. Also: the age is measured on the computer clock; demo reports are created at wall time (their occurred_at is on the simulated calendar), so no demo report is stale until 7 real days pass.
5. **I7 "recorded near misses".** (a) state recorded and kind near_miss, (b) state recorded and label nm (T23.12 names "recorded near miss" by label). They differ when a near_miss is approved with ct or an incident with nm.
6. **Monitored time (I7 rate, I8, share of areas with any monitoring).** "assessable footage": (a) coverage_state usable, (b) usable and usable_degraded. Cameras of an area with no S5 output of `wf_source_config`, e.g. the 20 T-22 probe cameras that the D-45 pilot did not process: (c) monitored (they have footage), (d) not monitored (the AI did not watch them; "unmonitored time is never counted as zero events"). In the demo, 8 of 9 areas include such cameras, so the I7 rate and I8 print as not determined where the readings differ.
7. **Alert grouping (T23.2 b).** (a) Whether widened intervals that only touch (end = start) overlap: such inputs are refused. (b) The time axis across cameras. SDG cameras have `recording_local` timelines; the demo places every camera of a run on the simulated calendar with the run's one offset (T23.11 a) and groups on that axis. The agent reads T23.11 (a) this way, but it is a timebase question: please confirm. Outside the demo, intake refuses an area whose episodes are on more than one timeline.
8. **I9 after reclassification.** An incident set recordable = yes and later reclassified (closed_rejected): (a) count only incidents now recorded, (b) count every incident whose latest recordability is yes. The same for the incidence rate.
9. **sm_uphold without an area-manager rejection.** After sm_reopen of a closed_duplicate (no AM label) or of a reclassified approval (the AM label is an approval), "final_label = the area manager's label" is undefined or would close an approved report as upheld. **Now:** sm_uphold is refused unless the area manager's latest decision is am_reject.
10. **Wording and VR-E-041 (for the Architect).** VR-E-041 lists "OSHA/NAICS/establishment identifiers" among forbidden fields; T23.15 adds `est_id` and `wf_establishment`. The name check passes (the demo manifest field is named `est_records`, not `establishments`, for that reason). Please confirm that VR-E-041 applies to Observation-store, E2 and RQ2 outputs and not to the T23 workflow tables. The CLAUDE.md "Never" list (OSHA linkage, establishment rankings) also overlaps with T23.7 (301-style fields) and I9. The agent implemented exactly what T23 states and nothing more (no ranking across establishments; the 301 banner says it is not a submission). The Owner may want the CLAUDE.md wording updated.

**Rulings (D-49, 20 Nov 2026; D-49.1 §7):**
1. candidate_review adjudication class → `reference_class` nullable with null reason `not_applicable`; namespace isolation (T23.16). Tests FX-14a, b, j–n.
2. I4 scope and unit → AI reports only; the latest SM decision per report (T23.17, §5). FX-14a, b, u.
3. I5 → AI reports ever recorded by `as_of`; report unit (T23.18, §5). FX-14w, x.
4. I6 → age since entering the current pending state, at `as_of`; age since creation in a second column. Demo ages run on log time, so demo reports become stale only after 7 real days: accepted as a known demo limit (§5). FX-14w.
5. I7 → by kind; the kind follows the label at decision (T23.18 e). FX-14q, r.
6. Monitored time → `usable` only (`usable_degraded` shown apart); an unprocessed camera is not monitored; area time is the union; observability categories (T23.23). FX-14z, aa.
7. Grouping → closed intervals (touching merges); demo axis with a stated evidence reference, otherwise per camera; grouping is not linkage (T23.21). FX-14q–t.
8. I9 after reclassify → recordability lifecycle; definitive cases only (T23.19). FX-14x, y.
9. sm_uphold without a rejection → refused; `sm_confirm_duplicate` added (T23.20). FX-14u, v.
10. VR-E-041 and CLAUDE.md → scope stated; demo-only limits; CLAUDE.md text of D-49.1 §8 (T23.27). FX-14ac.

## CR-031 (2026-11-20) — E-1.2.23 points that change a count, a state or a statistic, or that need confirmation (W-02, D-49)   status: CLOSED (Owner decision D-51, 21 Nov 2026; items 1, 2, 3, 5, 6, 7, 8 became Appendix T T23.28, contract E-1.2.24)
Opened on `v02-review-ui` (D-49 asked for it in any case for the T23.21 (d) path). **Nothing below was chosen** unless the item says what the code does now and why it is the literal text.
1. **T23.21 (d): the safety manager's path for a multi-member report in pending_sm (required by D-49).** T23.21 (d) says the safety manager "sends it back to the area manager with sm_reopen", but T23.4 defines sm_reopen only from closed_rejected and closed_duplicate to pending_sm, and am_split is taken only from pending_am. No action returns a pending_sm report to pending_am. **Now:** sm_overturn on a report with two or more members requires `group_resolution` ∈ {one_interaction, cannot_tell} (the first sentence of T23.21 d); there is no send-back, so a report whose members show several interactions can only be upheld or overturned by the safety manager. **Options:** (a) sm_reopen also from pending_sm to pending_am; (b) a new action (pending_sm → pending_am) with a note; (c) the safety manager may use am_split; (d) the safety manager may not overturn a multi-member report.
2. **T23.20 (d) group_resolution on an overturn after reopening a duplicate.** T23.20 (d) requires a group_resolution "(T23.21 (d))" for every such overturn, while T23.21 (d) defines it for AI reports with two or more members. **Now:** required for every overturn of a reopened duplicate, one-member and human-started reports included (the literal T23.20 d). Confirm, or limit it to two or more members.
3. **FX-14d and FX-14e setups under E-1.2.23.** Two T23 fixtures needed an added setup step so that their T23 expected values still hold; no expected value was changed:
   - FX-14d (I8 = 1, F4 with k_miss = 1): under T23.23 (c) an unset camera_observability is category 3, so I8 would be 0. The area manager's approval now records `camera_observability = observable` for camera 1.
   - FX-14e (one report of three members, approved): T23.21 (d) refuses am_approve without `group_resolution`; the step now gives `one_interaction`.
   - The fixture world's establishment is now `demo = true` (T23.27 b) and each fixture camera's coverage is processed by one S5 artifact (T23.23 a).
   Confirm these setups, or rule that the T23 fixture text itself changes.
4. **Unit of the side counts beside I4.** Section 5: "sm_confirm_duplicate and overturns of duplicates counted beside, outside n", without a unit, while I4 counts the latest decision per report. **Now:** both are printed: reports by their latest safety-manager decision, and actions. Choose one.
5. **withdraw_recordability without a determination.** T23.19 (c) lets the safety manager withdraw "from any state". Withdrawing from `not_set` (or again from `withdrawn`) would move a report out of `not_set`, which removes the "provisional" label of the incidence rate (T23.19 f). **Now:** refused when the determination is `not_set` or `withdrawn` ("there is no recordability determination to withdraw"). Confirm, or allow it.
6. **T23.16 (b) "the enum has exactly two values [V]".** The E-1.2.1 `namespace` enum has four values (reference, candidate_review, study_d6, pseudo_label; the last two reserved). **Now:** VR-E-056 refuses an adjudication in study_d6 or pseudo_label ("any other combination is refused"); none exists. Confirm.
7. **The T23.26 banner and the section 5 term list.** The banner T23.26 requires on every page with AI alerts contains "accuracy" ("…not the system's accuracy"), and so does its "accuracy of the alert source: not reported" variant, while the linter refuses "accuracy" except inside the fixed T23.9 and T23.23 (d) texts. **Now:** the banner is exempt as a fixed text (it must be printed verbatim). Confirm.
8. **prov_class of the combined value (T23.24 b).** S4 `pair_series` rows carry no `prov_class`, and neither do S5 episodes. **Now:** the form prints "prov_class: not recorded on the S4 rows". Which class applies (for example geometry_estimated or model_estimated) is a provenance statement the agent does not choose.
9. **The demo store `out/review/demo_20261119` was drawn before E-1.2.23** and is not modified (D-49). Consequences on its re-rendered pages (W-02 report, section 3):
   - its manifest has no `source_quality`: the banner reads "accuracy of the alert source: not reported", although the pilot column C figures exist;
   - its manifest has no `timebase_evidence_ref`, yet its 8 reports were grouped across cameras on the demo calendar axis; under T23.21 (c) a run without the reference groups per camera. The stored grouping is a record and is not redone; the pages say "grouping basis not recorded (report created before E-1.2.23)";
   - its episodes carry no calibration tier, σ or q_state: no combined value is shown (AR-64 item 14);
   - its stored descriptions keep the T23 template ("Minimum measured separation … m (full_camera)").
   **Options:** (a) keep the store as it is; (b) a new demo draw on a new store with the E-1.2.23 manifest (the old store stays, registered); (c) a registry-held supplement for the old store's manifest. Not chosen.
10. **§6.2 item 3, the S0–S5 rebuild of three SDG cameras.** Rebuilding S5 is an S5 run, which the D-49 hard limits forbid ("No S5 or S8 run"). **Not done.** The read-back check of the stored M1a and pilot artifacts is incomplete (stopped for low memory; W-02 report section 4). Owner: authorise the rebuild separately, or drop that part of item 3.
11. **§4.2 [U] VR-E-001 and a minor-ahead store.** VR-E-001 is a Parquet-metadata rule (`schema_version` major); it does not cover the JSONL validation store. A version guard is added (AR-64 item 6): stores created from now on record their contract and newer stores are refused. The code before this change has no guard, so it could still open a store written after it, and the existing stores record no version. Confirm the guard and the residual risk (for example: never run the pre-E-1.2.23 code against `out/review/`).
12. **Unregistered fixture stores.** D-49 registered `out/review/main` and `out/review/demo_20261119` only. `out/review/demo/store` (V-02 fixture store, with fixture batches) and `out/review/w01_fixtures/a/store` (W-01 fixture store) are not registered and now refuse to open; their contents are listed in the W-02 report. Register them, or leave them as fixture output.
13. **§6.3: excluding the demo runs empties two strata of the T22 frame (STOP condition of §6.3 item 3).** The BL-6 frame of the T-21 oracle run has CT 7, UD 44, NM 30, PC 212, H 17, O 9 episodes. The 9 demo runs of `out/review/demo_20261119` hold 98 of them, including every CT and every O episode: after T23.25 (b) the frame has CT 0, UD 31, NM 24, PC 151, H 15, O 0. T22.6 then allocates 60 over the four strata present (15 each; no stratum below the share, so T22.14 (e) caps nothing), against the six-stratum allocation of CR-028 (CT 7, UD 11, NM 11, PC 11, H 11, O 9). A reference batch drawn now would contain no CT and no O episode. Nothing was drawn, redrawn or changed. **Options (Owner):** (a) accept a four-stratum batch; (b) a new demo draw (new store, new seed) that leaves CT and O episodes in the frame, the current demo store being retired from the registry by an Owner decision; (c) another frame (configuration, run or dataset); (d) hold reference sampling.

**Rulings (D-51, 21 Nov 2026; the Architect's review of W-02, approved by the Owner):**
1. **Option (c).** The split action may also be taken by the safety_manager from pending_sm, with the effects of `am_split` from pending_am (original → closed_split; one new pending_am AI report per part with `split_from`; nothing written for the original, existing records stay). The action is named `split` in the log, with `actor_role` area_manager or safety_manager. The T23.21 (d) send-back sentence is replaced. T23.28 (a); tests in `tests/workflow/test_t23_28_d51.py`.
2. `group_resolution` on an overturn after reopening a duplicate only for two or more members; T23.20 (d) amended. T23.28 (b).
3. FX-14d and FX-14e setups **confirmed**; a "Setup under E-1.2.23" note for each in T23.28 (c).
4. Side counts beside I4: **unit = report** (latest safety-manager decision per report); the action count is dropped.
5. Withdraw from `not_set` or `withdrawn`: **refusal confirmed**; T23.19 (c) amended. T23.28 (d).
6. The [V] tag in T23.16 (b) was wrong: the enum has four values, `study_d6` and `pseudo_label` reserved; VR-E-056's refusal **confirmed**; T23.16 (b) amended. T23.28 (e).
7. The T23.26 banner is a fixed text, **exempt from the linter**; section 5 amended. T23.28 (f).
8. `prov_class` of the combined value: `geometry_estimated` for the camera path, `simulator_truth` for simulator positions (the T-21 oracle source), printed from the source path of the demo manifest, never stored. T23.28 (g).
9. Old demo store: **option (a), kept as it is**, with one added banner line: "Reported figures for this source exist: CM-03 0.12, EV-M1 0.11, EV-M2 0.22 (reports/M1b_pilot_report.md); not recorded in this store's manifest."
10. The S0–S5 rebuild of three SDG cameras is **dropped** from section 6.2 item 3. The M0 clean-clone determinism is the identity evidence; the artifact read-back is the compatibility evidence and must be completed (D-51 STEP 2).
11. Store version guard **confirmed**; residual risk accepted with the CLAUDE.md "Never" line "Run code from before E-1.2.23 against `out/review/`."
12. Unregistered fixture stores: **left unregistered** (throwaway fixture output, rebuilt by their scripts with their own registry).
13. **Option (d): hold reference sampling.** No T22 batch until a later Owner decision; option (a) refused; option (b) preferred when sampling resumes.

## AR-63 — Representation choices of the T23 reporting workflow (W-01, D-48)   status: DECIDED (D-49, 20 Nov 2026: item 6 revised, item 8 reversed, the rest accepted; see the ruling list at the end of this entry)
Representation and engineering only; no label, state, status, denominator, count or statistic depends on them (those are CR-030). Code: `src/rq1/workflow/`, small changes in `src/rq1/review/`; tests: `tests/workflow/`, `tests/fixtures_t03/test_t23_fixtures.py`. Evidence read: none beyond E-1.2.22. Items marked **REVIEW** change displayed wording.
1. **Store.** The workflow store is the V-02 store folder (one sign-in). T23.15 tables are JSONL files `wf_*.jsonl` and `demo_manifest.json` (JCS), each row validated before writing. candidate_review assessments go into the V-02 `reviewer_assessment.jsonl` with the envelope {batch_id: null, report_id, recording_id, row}, so the T22.2 (b) exposure rule sees them (T23.11 c). Status entries go into the V-02 status log. Helper files that are not contract tables: `wf_episode.jsonl` (member episode descriptions for clips and status entries), `wf_monitoring.jsonl` (calendar-placed S1 coverage per camera, with whether the camera has source output), `wf_displays.jsonl` (first display of a report to a person). `evidence_clip.jsonl` and `retention_policy.jsonl` hold E-1.2.1 rows.
2. **Schema types (inferred).** No table prefix. ID columns are named as T23.15 names them, with UUIDv7 values and the prefixes `est_`, `area_`, `usr_`, `rpt_`, `wfe_`, `wfc_` and `dmo_`. wf_config adds `wfc_id` and `store_version`. demo_manifest fields: `demo_id, seed, source_configuration, source_path, source_root, runs[], est_records[], areas[], calendar_start_utc, calendar_days, created_utc`.
3. **field_changes.** map<str, struct{before: str, after: str}>, each value its canonical JSON text. A creation entry lists every field it sets (before = null).
4. **Kinds.** `kind_initial` ∈ {near_miss, incident_draft, incident}. The current `kind` field of an incident_draft report is `incident` (an AI-drafted incident), so set_recordability applies once it is recorded (FX-14c).
5. **REVIEW: ai_label of a group and the description.** A group whose members have different G2 labels shows every distinct label in CT, NM, UD order, joined by " and " (no precedence chosen). In the template, <label> is the ai_label with its leading "candidate" written once ("a candidate, undetermined between …").
6. **REVIEW: pre-filled values of a group.**
   - min_clearance_m is the smallest non-null member value.
   - The geometry method is the single `object_state.geometry_method` of the member's S4 artifact.
   - A null clearance reads "Minimum measured separation not available (<null reasons>)".
   - evasive_action_observed is true if any member's E_ep is true, unknown if any is unknown, otherwise false.
   - duration_s is the latest end minus the earliest onset.
7. **Evidence clips.** One `evidence_clip` row per member, purpose review, over the T22.4 clip window of the episode (c_pad_s = 3.0). decoded_frame_sha256 is the SHA-256 of each decoded frame's luma plane (as S1). access_class is publishable_synthetic_only, redaction none, with one retention_policy row for the store. The browser gets a random token, as in AR-61 item 10.
8. **REVIEW: human text.** Free text that would break W1–W6 or T23.12 on a page ("near miss" unqualified, "recordable", "collision", …) is refused at entry with a message, so no workflow page can show it.
9. **Recordability input.** Days counts are asked for days_away and restricted_or_transfer. A note is required. decided_by is the safety manager's user ID.
10. **Manager annotator rows.** An area manager's candidate_review assessments use an annotator row with role c_layer_reviewer; a safety manager's would use role adjudicator. Both have independence_attestation = false, qualification_ref "workflow area_manager (T23): manager decision record, not a reference reviewer", and the person's pseudonym. An existing row with the same pseudonym and role is reused (AR-61 item 4). These rows have no passphrase and are not offered at sign-in.
11. **Demo draw.**
    - One numpy PCG64 generator seeded with the demo seed draws 3 runs per D-35 family without replacement (runs sorted, families sorted). It then draws one offset per run, in whole seconds in [0, 28 days − 1 h).
    - The calendar starts on Monday 2026-11-02 00:00 UTC (ISO weeks 2026-W45 to W48).
    - Establishments are named "Simulated warehouse North/South/East".
    - An area holds every camera of its run.
    - Family = first path element of `session.lineage.generation_batch`.
    - The workflow parameters are the T23.14 defaults (the demo store does not lower n_flag_min).
12. **Permissions details.**
    - A report page is visible to the area managers of its area, the safety manager of its establishment, its filer and the Owner.
    - The Owner may file a report (actor `owner`).
    - T22 annotator profiles have no workflow pages.
    - A person who decided a report as area manager can take no safety-manager action on it, notes and edits included.
    - Edits may change area or establishment; permissions follow the current fields (the fold).
    - am_approve and am_reject on AI reports require a rationale, because the assessment needs one (T22.5 c).
    - review_time_s runs from the person's first display of the report page.
13. **Wording linter.**
    - It checks the visible text of each workflow page, and the string values of JSON exports (keys are field names).
    - The T23 fixed texts and the two "recorded near miss (…)" forms are exempt. "Recordable" is accepted only inside the `recordable-yes` badge, which is printed only for recordable = yes set by the safety manager.
    - A workflow response that fails is not sent (HTTP 500).
14. **V-02 changes.**
    - `FixtureFrame`/`SdgFrame.episodes()` also return `recording_id`.
    - `Store.create_batch` excludes demo-run targets (T23.11 b) and records `excluded_demo_targets` in the manifest.
    - `ReviewServer` takes a handler class.
    - Video streaming is a helper (`_stream`).
    - `python -m rq1.review serve` serves the workflow too, on a `WorkflowStore`.
    - Annotator rows without a passphrase are not listed at sign-in.

**Reverse:** each item is local to `src/rq1/workflow/` (items 1 to 13) or a few lines in `src/rq1/review/` (item 14). No stored contract field of an existing table changes.

**Rulings (D-49, 20 Nov 2026; D-49.1 §7):**
1. Store layout: accepted, plus the store registry (T23.25). FX-14o, p.
2. Schema types: accepted.
3. field_changes: accepted.
4. Kinds: accepted (consistent with T23.18 e). FX-14c.
5. Mixed ai_label: accepted (the CT, NM, UD order is presentational).
6. Combined values: **revised** by T23.24 (comparable-only, smallest estimated separation with its provenance). FX-14ab.
7. Evidence clips: accepted.
8. Refusal of human text: **reversed** by T23.22 (stored verbatim, escaped, shown in an "entered by" block; never refused for wording). FX-14ad.
9. Recordability input: accepted, plus `withdraw_recordability` (T23.19). FX-14x.
10. Manager annotator rows: accepted, plus the early guard of T23.25 (d). FX-14n.
11. Demo draw: accepted, plus `timebase_evidence_ref` and `source_quality` (T23.21 c, T23.26). FX-14t, ac.
12. Permissions: accepted; the Owner of a demo store is exposed for its runs (T23.25 c). FX-14p.
13. Linter: accepted, amended by T23.22 and the §5 term list. FX-14ad.
14. V-02 changes: accepted; the batch exclusion becomes cross-store (T23.25 b). FX-14o.

## AR-64 — Representation choices of the E-1.2.23 implementation (W-02, D-49)   status: ACCEPTED (D-51, 21 Nov 2026: all 17 items, including the REVIEW items 14 and 15)
Representation and engineering only; no measured value, label, denominator, estimator or acceptance criterion depends on them (points that could change a count, a state or a statistic are CR-031). Code: `src/rq1/review/registry.py` (new), `src/rq1/validation/reference.py` (new), `src/rq1/review/store.py`, `src/rq1/review/server.py`, `src/rq1/schema/{tables,validate,registry}.py`, `src/rq1/workflow/`. Tests: `tests/schema/test_t23_16_adjudication.py`, `tests/validation/test_t23_16_reference_access.py`, `tests/review/test_t23_16_isolation.py`, `tests/workflow/test_t23_e1223.py`, `tests/workflow/test_t23_25_stores.py`. Evidence read: none beyond E-1.2.23. Items marked **REVIEW** change displayed wording.
1. **Store registry (T23.25 a).** `out/review/registry.json` is JCS: `{"registry", "stores": [{"path"}]}`; a path inside `out/review/` is stored relative to it, any other path absolute. Registering is idempotent and never removes an entry. `Store(..., registry=)` takes a registry (default: that file) and refuses, before creating or reading anything, a store that is not listed (ERR-SPEC). CLI: `python -m rq1.review register --store <path>`; `python -m rq1.workflow demo` registers the new store first. Registered now: `out/review/main` (not yet created) and `out/review/demo_20261119`. Note: `out/` in this worktree is a symlink to the main folder's `out/`, so both worktrees share the one registry file.
2. **Fixture stores of the screenshot scripts.** `research/review_ui/make_demo.py` and `research/workflow/make_screenshots.py` build throwaway fixture stores (fixture video and IDs) with a registry file of their own inside their folder, so they never enter `out/review/registry.json`. The scripts were not run in W-02 (they delete and rebuild their folder).
3. **VR-E-056** is checked in `validate.validate_row` with code ERR-NAMESPACE (as VR-E-053 and VR-E-055). `registry.minimal_row("adjudication")` sets `reference_class` to the first enum value so the minimal row stays valid.
4. **Reader of stored rows (T23.16 f).** `validation.reference.read_adjudication_row` returns a copy with the missing reason as null; `Store.adjudications()` reads through it. No row is rewritten.
5. **Accessor (T23.16 e).** `validation.reference.reference_adjudications(store_root)` reads the V-02 layout (AR-61 item 5); pilot rows are excluded by batch and by target. `ev_m12_population` returns the EV-M12 input population (current adjudication per target, mapped system label, unsure counted apart), not a metric. The static check `direct_read_violations` flags `adjudication.jsonl`, `reviewer_assessment.jsonl`, `.adjudications(` and `.assessments(` in the scanned modules; paths absent on a branch are skipped.
6. **Store contract version (D-49.1 section 4.2).** A store created by this code writes `store_contract.json` `{"contract": "E-1.2.23"}`; the code refuses a store that records a newer contract. Existing stores get no file (not modified). See CR-031 item 11.
7. **candidate_review adjudications (T23.5 c, T23.16).** Envelope `{batch_id: null, report_id, recording_id, annotator_id, row}`; `assessment_ids` = the area manager's latest candidate_review assessment of that member in the report (empty for an overturn after reopening a duplicate, where the area manager wrote none). The safety manager's annotator row has role adjudicator and `qualification_ref` starting "workflow " (AR-63 item 10).
8. **Monitoring rows (T23.23 a).** `wf_monitoring.jsonl` rows gain `processed: [{start_utc, end_utc, s5_artifact_id}]`; a row written before E-1.2.23 is read as processed over its whole coverage by one artifact when `has_source_output` is true. Two different artifacts over one window are refused at write time (ERR-SPEC), and again when read.
9. **Episode rows.** `wf_episode.jsonl` rows gain `calendar_start_utc` and, from the demo source, the T23.24 (b) provenance at the minimum-clearance pair-frame: `calibration_tier` (S0 index), `clearance_sigma_m`, `sigma_status`, `q_state`, `q_reasons` (S4 `pair_series` row joined on the `pow_nk` of the episode's `pow_id` and `minclr_frame`), `s4_artifact_id`; `prov_class` is null (CR-031 item 8).
10. **Report fields.** New fields in `field_changes`: `grouping_basis` (pre-filled), `split_from`, `duplicate_of`, `group_resolution`, `camera_observability` and `observability_cameras`. `min_clearance_m`, its reason and `geometry_method` are no longer stored for new reports (T23.24 d); old reports keep them in the log and the page no longer shows them.
11. **am_split form.** One `part_<episode>` field per member with a part number; parts in order of their number; each new report is pre-filled afresh from its members, keeps the members' existing evidence_clip rows and the original's grouping basis, and carries `split_from`.
12. **as_of (T23.18 b).** The truncated log is the entries whose canonical UTC text is ≤ `as_of`; human-entered hours are truncated the same way; default `as_of` is the current time. Verification reports a decreasing `created_utc` as ERR-INVARIANT.
13. **Linter (T23.22, section 5).** Skipped: `<blockquote class="user-entered">` blocks, the `<div class="source-banner">` block, and the text inside the editing forms' text areas. In exports, the keys of user-entered fields (`description`, `notes`, incident text fields, `note`, `rationale`) are not linted, and the T23.26 banner string is exempt.
14. **REVIEW: combined value without a recorded tier.** When a member with a clearance has no recorded geometry method or calibration tier (episodes drawn before E-1.2.23), no combined value is shown: "not combined: the geometry method or calibration tier is not recorded for every member". The templated description then reads "Smallest estimated separation: not combined (...)" or "Smallest estimated separation not available (<reasons>)".
15. **REVIEW: display.** Hour figures print with four decimals; F1 and F2 below their minimum n print "not evaluated: insufficient n (n < minimum)"; the regulator export adds `as_of`, `statement`, `source_banner` and per-indicator `notes`; establishments are listed in registration order on every page; the privacy notice reads "Privacy (T23.13): pseudonyms only. No data of a real person is entered; in a demo establishment every entry is fictional."; the T23.25 (c) attestation text names workflow pages and W-01 per-run tables; the source banner is followed by "Reported figures: CM-03 0.12, EV-M1 0.11, EV-M2 0.22 (<report reference>)"; a source with no figure reads "AI alerts in this demo come from <source>; accuracy of the alert source: not reported. Workflow measures describe the workflow, not the system's accuracy."
16. **Demo source constants.** `SDG_TIMEBASE_REF` is the T23.21 (c) text; `PILOT_C_QUALITY` copies the BL-6 column C figures with `report_ref` "reports/M1b_pilot_report.md (m0-implementation ec63113), BL-6 column C"; the T-21 oracle source records no figure.
17. **camera_observability** is given by the area manager with `am_approve` or `am_reject`, or with `edit_fields` while pending_am; it is refused on AI reports.

**Reverse:** items 1 to 6 are local to the new modules and a few lines in `review/store.py`; items 7 to 17 are local to `src/rq1/workflow/`. No stored row of any store is changed.

**Ruling (D-51, 21 Nov 2026):** all 17 items accepted, including the two REVIEW items (14, 15). Item 9's null `prov_class` is now printed per source path (T23.28 g, AR-65); item 6's constant moves to E-1.2.24 (AR-65).

## CR-033 (2026-11-23) — D-55 tracker selection: `tracker_id` for column C, and the readings of the D-55 measures   status: CLOSED (Owner decision D-56, 23 Nov 2026: items 1 to 4 confirmed as applied)
**Raised by:** implementation agent. **Task:** D-55 steps 2, 4 and 5. **Sections:** F.1 A1.2 (configuration class), A5.2; D-55 (Owner, 23 Nov 2026). Numbering: CR-032 stays reserved for D-51 (W-02 scope); CR-033 was named for D-53 and not used there.
**Meaning-affecting:** items 2 to 4 yes (they fix which numbers the selection rule reads); item 1 no.
1. **`tracker_id` and column C's IDs (D-55 step 2).** Column C's S3 configuration ID `trc_i4ljlcifrwgephzz4cgjkmo5ej` hashes the whole recorded tracker configuration (`run_pilot.py`), so adding a `tracker_id` field would change it and every column C S3 artifact ID. As D-55 step 2 directs, `rq1.tracking.s3_config.run_config` returns column C's configuration unchanged when every class is ByteTrack at the installed defaults; every other configuration records `tracker_id` (and the tracker class and full parameters) per class. Pinned by `tests/m1b/test_s3_config.py` (ID reproduced; a stored S3 artifact rebuilt to the same ID). Options for v2: (a) keep: an absent `tracker_id` means ByteTrack; (b) record `tracker_id` for every v2 run, column C staying as stored.
2. **"Tracked point" and the matcher (coverage, precision, fragments).** D-55 cites `pilot_tracker_loss.json` and "A5.2 matching at IoU ≥ 0.3". A5.2 itself is the one-to-one weighted association at iou_cm 0.5 with ambiguity handling; `pilot_tracker_loss.json` uses the probe matcher (`zs_match`, IoU ≥ 0.3, one-to-one by descending score, references clipped to the image). Used: the `pilot_tracker_loss.json` matcher. "Tracked point" readings: (a) a point in state `tracked` (the `tracked` stage of `pilot_tracker_loss.json`); (b) every S3 point, tracked or predicted (its `tracked_predicted` stage). **Used: (a) for the selection.** (b) is computed and reported beside it, and the selection is repeated under (b) as a sensitivity (`v2_tracker_selection.json`, `sensitivity_secondary_reading`). IDF1 is the pilot's (`idf1.py`, iou_cm 0.5, every S3 point).
3. **Fragments per forklift reference identity.** Used: per reference identity on a camera, the number of distinct forklift tracks whose points (reading of item 2) are matched to it on some frame; the mean over the identities covered by at least one track (identities never covered are counted apart, not as 0). Step 6 adds median, P90 (nearest rank) and max over the same identities.
4. **Selection details.** (a) "Within 0.01 of the best": IDF1 ≥ best − 0.01, inclusive (a 1e-12 allowance for rounding only). (b) "Parameters changed from the installed defaults": keys of the tracker's own installed yaml whose value differs; for BoT-SORT `gmc_method: none` counts as one change (it differs from `sparseOptFlow`), `with_reid: false` does not (installed default). This matters only if T1 and T2 winners tie on IDF1 band, coverage and fragments. (c) Person IDF1 guard: the person tracker is the column C ByteTrack in every configuration, run once per camera, so the guard holds with equality for every row.
**What proceeds meanwhile:** the grid and the selection run with the readings above; the D-56 STOP reports the result under them, and the sensitivity under item 2(b).
**Agent's recommendation:** none; the Owner confirms or changes the readings at D-56.

**Ruling (D-56, 23 Nov 2026):** items 1 to 4 confirmed **as applied** (primary reading, item 2 (a)). A reading is never changed after the result is known. Closed.

## AR-66 — Engineering choices of the D-55 tracker selection   status: ACCEPTED (D-56, 23 Nov 2026: as written; the Architect: representation and engineering only)
Representation and engineering only; no measured value, label, denominator or rule depends on them (the readings that do are CR-033).
1. **BoT-SORT adapter.** `src/rq1/tracking/botsort.py` reuses `bytetrack.run_class` through a new optional `tracker_class` argument (default BYTETracker, so every ByteTrack output is unchanged; the `.venv-det` ByteTrack tests pass unchanged). Camera-motion compensation is switched off with the installed option `gmc_method: none` (GMC method None, identity warp, skipped in `_pre_first_associate`); re-identification with `with_reid: false`. The adapter refuses any other value of the two.
2. **Batch runner.** `src/rq1/tracking/grid.py` runs many jobs (one class, one tracker, one parameter set each, a fresh tracker instance per job) in one `.venv-det` process per camera; the person job runs once per camera and is shared by every configuration.
3. **S2 licence rows (D-47 item 5).** `rq1.perception.s2.build` takes an optional `license_rows`; when given, the artifact carries a `license_component` table (YOLO-World and the CLIP text encoder rows of `pilot_license_components.json`) beside `detection`. Omitted, the payload is unchanged, so earlier S2 IDs are unchanged. Used for the 20 probe cameras only.
4. **Layout.** Probe S2 artifacts in `out/m1b/v2trk/artifacts/` with `execution.json` appended to `out/m1b/v2trk/register.jsonl`; per-camera S2 records in `out/m1b/v2trk/s2/`; per-camera grid results in `out/m1b/v2trk/grid/`. The raw detector output goes to `out/m1b/pilot/s2raw/` as for the pilot (new files only). No S3 artifact is built for the grid configurations: the measures are computed from the bridged points the S3 builder would store (`bridging.points_from_log`, g_max 15).
5. **Configuration ID** of a grid configuration = `s3_config.trc_id(run_config(...))`, the dict the pilot hashes for S3.
**Reverse:** delete the new modules and the `tracker_class` / `license_rows` arguments; nothing stored depends on them except the new `out/m1b/v2trk/` outputs.

**Ruling (D-56, 23 Nov 2026):** accepted as written (the Architect: representation and engineering only).

## CR-034 (2026-11-23) — T24.2 on track points in state `lost`   status: CLOSED (Owner decision D-57 ruling 3, 24 Nov 2026: reading (a) confirmed)
**Raised by:** implementation agent. **Task:** D-54 STEP 2. **Sections:** Appendix T T24.2 (c), (d) (E-1.2.25); E-1.2.1 §5.4 `track_point.foot_point_px` (non-nullable); the S4 builder's E-1.2.24 rule that a `lost` point has no position.
**Meaning-affecting:** yes. It decides which pair-frames get `unmeasurable_geometry_failure` rather than `unmeasurable_occluded`, so it changes the clearance_state counts that CM-08 by state and the D-41 availability table read.
**Gap.** T24.2 (c) applies to "every object-frame with a foot pixel". Every `track_point` carries `foot_point_px`, including points in state `lost`, where it is the box the S3 builder carries forward. E-1.2.24 never forms a floor point for a `lost` point (its position is null whatever the pixel).
- **(a) Used.** The gate applies where E-1.2.24 forms a camera floor point: points in state `tracked` or `predicted`. For a `lost` point, `floor_resolution_m_per_px` is null with reason `not_applicable`; its position and the pair-frame's clearance_state are as in E-1.2.24 (`unmeasurable_occluded`).
- **(b)** The gate also applies to `lost` points: s is computed from the carried-forward pixel, and a `lost` point whose pixel is gated or has no floor intersection makes the pair-frame `unmeasurable_geometry_failure`.
- Positions, clearances and every event are the same under both readings: a `lost` point has no position either way. Only state counts and the `floor_resolution_m_per_px` value of `lost` rows differ. STEP 3 reports the number of `lost` object-frames, so the size of the difference is visible.
**Pinned by:** `tests/substrate/test_t24.py::test_t24_2_lost_points_are_outside_the_gate_cr_034`.
**Agent's recommendation:** none; the Owner decides.

**Ruling (D-57 ruling 3, 24 Nov 2026):** reading (a) is confirmed. The gate applies where E-1.2.24 forms a camera floor point (`tracked`, `predicted`). For `lost` points, `floor_resolution_m_per_px` is null (`not_applicable`). CR-034 is closed.

## AR-67 — Representation choices of the T24 implementation (E-1.2.25, D-54 STEP 2)   status: ACCEPTED (D-57 ruling 5, 24 Nov 2026: as written; the Architect: representation and engineering only, with regression evidence)
Representation and engineering only. With the T24 parameters absent, no measured value, label, state or ID changes (pinned below). The readings that change a count are in CR-034.
1. **"May be absent" fields (T24.0).** A new schema mark `@absent_ok` (`schema/tables.py`) on `footprint_prior.anchor_offset_m`, `footprint_prior.anchor_taper_m`, `geometry_config.s_max_m_per_px` and `object_state.floor_resolution_m_per_px`; a null-reason sibling inherits it (`types.with_reasons`). A row may omit such a field, and an omitted field is the E-1.2.24 form:
   - the validator accepts its absence, but refuses a value without its null-reason column or the reverse;
   - `registry.to_arrow` writes no Parquet column for it when no row has it, and refuses a table where some rows have it and others do not (ValueError);
   - `minimal_row` and the JSON Schema `required` list leave it out;
   - IDs and payload hashes already cover only the keys present (`ids.artifact._canonical_row`), so an absent field enters no hash.
   Options considered: a nullable column always written (rejected: it would change every E-1.2.24 Parquet file and the read-back payload); a second table (rejected: T24.2 (c) names an object_state field).
2. **Gate parameter in the builder.** `SubstrateConfig.s_max` (default None = gate off) carries `geometry_config.s_max_m_per_px`. Callers that do not set it build exactly as before.
3. **`floor_resolution_m_per_px` where no camera floor point is attempted (gate on):** simulator positions `not_applicable`; no calibration (`image_only`) `uncalibrated`; `lost` points per CR-034 (a). Clearance null reason under `unmeasurable_geometry_failure` is `not_observable`, as for `unmeasurable_occluded` (T24.2 (c) names only the state).
4. **Distortion.** s(p) on `full_camera` is the analytic Jacobian of the ray–floor intersection (`geometry._full_camera_jacobian`). With a distortion model, the undistortion step is differentiated by central differences (step 1e-3 px). No stored calibration has distortion (the SDG and SmartSpaces adapters write `distortion_model = none`), so no current value depends on this.
5. **Rounding allowance.** The gate refuses s > s_max + 1e-12 m/px, so that s = s_max computed with rounding error is kept as T24.4 requires (Δv = √30000 gives s = 0.10000000000000006). Same allowance as CR-033 item 4 (a).
6. **Prior checks.** Every footprint prior is checked when S4 starts: one T24.1 parameter alone, d < 0 or r_taper ≤ 0 is ERR-SPEC (T24.1 (b)); `anchor = rear_axle` with a calibration supplied (a camera-derived floor point) is ERR-SPEC (T24.1 (a)). No stored configuration uses `rear_axle`.
7. **Regression evidence.** `research/m1b/t24_regression.py` rebuilds stored S4 artifacts with the T24 code and no T24 parameter. Result in `research/m1b/t24_regression.json`: M1a A, M1a B and pilot C, each on 96 of 96 tuning cameras that are pilot cameras, all payload-identical and ID-identical. M0, using the method of W-02 §6.2 item 2: a clean clone of e6072ef with the T24 source change applied (one context conflict in `builder.py` resolved to e6072ef's lines plus the T24 lines). Two runs give all 12 artifact IDs and payload prefixes of `reports/M0_report.md`, and every exported file (48, execution records excluded) equals the unpatched run.
**Pinned by:** `tests/schema/test_t24_schema.py` (items 1, 2), `tests/substrate/test_t24.py` (items 3–6).
**Reverse:** remove the `@absent_ok` lines and the four fields, the `SubstrateConfig.s_max` field and the T24 branches in `substrate/builder.py` and `substrate/geometry.py`. Nothing stored depends on them except the new `out/m1b/v2t24/` outputs.

**Ruling (D-57 ruling 5, 24 Nov 2026):** accepted as written (the Architect: representation and engineering only, with regression evidence).

## CR-035 (2026-11-23) — D-54 STEP 4 (c): "no counterpart in B-sim-P"   status: CLOSED (Owner decision D-57 ruling 4, 24 Nov 2026: diagnostic only; both readings stay reported side by side, none chosen)
**Raised by:** implementation agent. **Task:** D-54 STEP 4 (c). **Sections:** D-54 STEP 4 (c) (Owner, 23 Nov 2026); diagnostic only, no contract quantity.
**Meaning-affecting:** yes, for the diagnostic. It decides which B-tune unmatched events are classified (15 or 50). No contract value, label or reported result depends on it.
**Gap.** STEP 4 (c) takes "each B-tune unmatched event with no counterpart in B-sim-P (about 42)". It does not define a counterpart. 42 is the net difference of the unmatched totals (105 − 63), not a count of events.
- **Reading 1.** A counterpart is a B-sim-P G1 system event of the same identity pair whose interval overlaps (temporal IoU > 0), matched or not. **15** events have none.
- **Reading 2.** A counterpart is such an event that is itself unmatched in B-sim-P. **50** events have none: the 15 above, plus 35 whose overlapping B-sim-P event is matched.
- Neither reading gives 42, because B-sim-P also has unmatched events with no B-tune counterpart.
**What proceeds meanwhile:** `research/m1b/d54_person_position.json` and the D-54 report give both readings side by side. Every event carries both flags.
**Agent's recommendation:** none; the Owner decides.

**Ruling (D-57 ruling 4, 24 Nov 2026):** a diagnostic-only question. Both readings stay reported side by side; none is chosen, and no reported value depends on it. CR-035 is closed.

## AR-68 — Engineering choices of the D-57 split diagnosis and m_gap sweep   status: PROPOSED (for review at the next stop)
Representation and engineering only. No measured value, label, matching rule or contract value changes; N4 and the label rules are untouched, and the only value varied is the one D-57 names (`rule_configuration.lifecycle.m_gap_frames`).
1. **version_label of the sweep configurations.** The rule_configuration of m_gap 5 keeps `version_label = "preregistration-v1"`, so its ID is the stored v1 BL-6 ID. The other values carry `"D-57 diagnostic m_gap <n> (not frozen)"`, so no configuration with a non-v1 value is labelled v1. Each value already has its own ID through `lifecycle.m_gap_frames`; the label only avoids a misleading name. Options considered: "preregistration-v1" for all (rejected: wrong label); null (rejected: indistinguishable from configurations that have no label).
2. **S5 from stored S4.** The stored S4 tables and manifest spec are passed to `s5.build` as read back (`d57_split.load_art`); nothing is rebuilt upstream. Check: at m_gap 5 the rebuilt S5 payload_sha256 must equal the stored D-54 / T-21 S5 payload on every camera, and the pooled EV values must equal `d54_c_v2_tune.json` / `d54_b_v2_tune.json`; otherwise the aggregate stops.
3. **Layout.** STEP 2 per-camera records in `out/m1b/d57/split/`; STEP 3 S5 artifacts in `out/m1b/d57/artifacts/` (register `out/m1b/d57/register.jsonl`), per-camera results in `out/m1b/d57/mgap/`. Stored D-54 and T-21 artifacts are only read.
4. **STEP 2 readings (diagnostic definitions, stated in `d57_split.py`).** "Covering" is the D-50 definition (same resolved identity pair, temporal IoU > 0). Consecutive episodes are taken in (t_start, t_end, pow_id, start_frame) order. A gap is b.t_start − a.t_end, so it is negative when the episodes overlap (5 C-v2 splits, all mechanism (iii); none in B-both). Clearance categories use the providers' strict "<" at d_pc and d_p.
5. **Rounding allowance in the selection rule.** The EV-M1 floor and the 0.005 tie are compared with a 1e-12 allowance (as AR-67 item 5), so a difference of exactly 0.005 counts as a tie.
**Pinned by:** `tests/m1b/test_d57.py`.
**Reverse:** delete `research/m1b/d57_split.py`, `research/m1b/d57_mgap.py`, their outputs and `out/m1b/d57/`; nothing else depends on them.

## CR-036 (2026-11-24) — How recordings downloaded after the split freeze join (or stay outside) the frozen split   status: CLOSED (Owner decision D-60 rulings 3–4, 25 Nov 2026: reading (a), a separate frozen addendum `X0b-A1`)
**Raised by:** implementation agent, as the Owner asked at AR-57 item 9 ("at M1b raise a CR on how new recordings join a frozen split"). **Task:** D-59. **Sections:** E-1.2.1 §8 (split freeze, leakage), Appendix T T14 (E-1.2.12), D-20, D-37; the frozen split X0b `art_w5v3ldr43xdsqc6l4zifmjkuuj`.
**Meaning-affecting:** yes. It decides populations and denominators of tuning and reported results, and whether held-out-layout claims become possible.
**Gap.** D-59 adds up to 16 SmartSpaces 2026 scenes (qualification Part 5) after the split was frozen. The contract defines the freeze and the leakage groups, but not how scenes registered after the freeze are assigned. The agent must not assign them. Readings the Architect may choose between (none drafted as contract text):
- **(a) Separate frozen addendum split.** The new scenes get their own pre-registered split (seeded, by leakage group), frozen before any system output on them; X0b stays as it is. Tier-1 (new-layout) scenes can then support a held-out-layout result that X0b cannot.
- **(b) Test-only addendum.** All new scenes are reserved for testing, like D-37; no tuning use.
- **(c) Tuning-only addendum.** The new scenes widen the tuning subset; reported results stay on X0b.
- **(d) Re-freeze.** A new split version over held and new data (invalidates comparisons with results made on X0b; R-3).
**Lineage inputs the S0 registration would need (also for the Architect):**
1. `layout_id`. `registration.smartspaces_metadata` sets it to the scene name (or the render parent). Map evidence (qualification 5.2): 002, 004, 006, 020 have a `map.png` byte-identical to `Warehouse_000`'s, and 017/018 share one map. Readings: (i) layout_id = scene asset, as now (each scene its own layout); (ii) layout_id = map identity (002/004/006/020 with 000; 017 with 018). It changes which scenes are reported as `shared_scene_content` (D-20), so the agent does not choose.
2. `generation_batch` is fixed to `MTMC_Tracking_2026/train`; 020 and 022 are in the published `val` split. Readings: published split folder, or one batch for the edition.
**What proceeds meanwhile:** download, hash checks, ground-truth screen, and the frame-interval and frame-count checks only. **S0 registration waits** for items 1 and 2. No detector, tracker or S4+ run on the new scenes; nothing touches X0b, the 116 tuning or 110 reporting cameras, or the test partition.
**Agent's recommendation:** none; the Owner and the Architect decide (D-60).
**Resolution (D-60, 25 Nov 2026).** Main question: reading (a). A new split version `X0b-A1` records the 11 D-59 scenes without changing any X0b assignment: tier 1 (010, 011, 016, 017, 018, 019, 022) → partition `test_layout_holdout`; tier 2 (002, 004, 006, 020) → `reserve` (no role until a later Owner decision). Frozen like X0b (hash, freeze time) before any system output exists on these scenes (R-4). Leakage groups of the addendum use `layout_id` (one group per layout). Item 1: `layout_id` = the SHA-256 of the scene's `map.png` (Git-LFS hash, as in Part 5), reading (ii). Item 2: `generation_batch` = the `val` folder name and the revision, `MTMC_Tracking_2026@d38193b` (representation of the folder in the string: AR at STEP 2). Warehouse_001 still joins X0b later as planned (AR-57 note); not part of D-60.

## CR-037 (2026-11-25) — Event-level contact state, IE and pair resolution of a T25.2 joined event   status: OPEN
**Raised by:** implementation agent. **Task:** D-58 STEP 2 (T25.2) and STEP 4. **Sections:** Appendix T T25.2 (c) (E-1.2.26), E-1.2.1 §5.6 (candidate_event: "lbl_* (recomputed with §6 rules, never unioned)"), §6, T10.1, F.1 A5.2 ("Use downstream": a track's identity at the CA frame).
**Meaning-affecting:** yes. Items 1 and 2 change G2 labels and IE of joined events; item 3 changes which reference a joined event can match (EV-M1, EV-M2).
**Gap.** Before T25 every single-camera event had one member, so the event fields were the episode's. T25.2 makes multi-member events and says their fields "follow the existing candidate_event rules (labels recomputed with §6 over the members, never unioned)". The flags are implied: P_ev, X_ev, C_ev = any member; E_ev = Kleene OR; minclr_ev = min of the members' measured minclr; K_ev = E_ev ∨ (minclr_ev < d_nm) (applied; listed here for confirmation, with CT-E-17 as the contract test). Not stated:
1. **contact_state_ev.** §6 evaluates the contact state at the closest approach (T9.5, T10.1) of an episode. For an event of several episodes: (a) the state of the member holding the event's closest approach (lowest measured minclr; without one, the first member with a CA frame; else the first member); (b) the most severe member state (suspected > undetermined > none_observed > not_assessable); (c) T10.1 re-evaluated over the event's frames.
2. **lbl_IE.** (a) IE of the closest-approach member, plus K_ev unknown with H or PC (CL-INV-08); (b) any member IE; (c) the §6 IE conditions re-evaluated over the event (Q share over the summed member spans).
3. **A5.2 pair of a joined event, and of an episode of stitched identities.** A5.2 resolves "each track's identity at the CA frame". (a) At the closest-approach member's CA frame, with the member track that has a point there (else the member at the episode's first frame); (b) each member resolved at its own CA frame, and the event's pair is that pair if all members agree, otherwise unknown (no match, a false alert).
**Applied meanwhile (primary reading, not chosen):** 1(a), 2(a), 3(a), in `rq1.events.candidates.joined_events` and the D-58 drivers. With one member, every reading equals the E-1.2.25 event.
**Reported:** STEP 4 is G1 only (lbl_O, lbl_H, lbl_PC), which items 1 and 2 do not touch. For item 3 the D-58 event check reports EV-M1 and EV-M2 under 3(a) and 3(b) side by side (as CR-035), with the number of events where they differ; no reported value depends on a choice.
**Agent's recommendation:** none; the Owner and the Architect decide.

## AR-69 — Representation choices of the T25 implementation (E-1.2.26, D-58 STEP 2)   status: PROPOSED (for review at the next stop)
Representation and engineering only. No measured value, label rule, matching rule or contract value changes. With the T25 parameters absent every artifact is byte-identical (`research/m1b/t25_regression.json`: stored D-54 S4 and S5 and D-57 m_gap 5 S5 of C-v2, B-both and A on 116 of 116 tuning cameras; M0 12 IDs by W-02, item 11). The open meaning questions are in CR-037.
1. **stitch_id** = id("sti", [member tracks' natural keys [recording_id, track_local_id] in chain order]), new prefix `sti`. Every track of a stitched S3 gets one (a single-track chain too), so S4 sees one kind of unit. Natural keys, not `trk_` IDs: a `trk_` ID is artifact-scoped (§2.3) and changes in any new S3 artifact, so "points keep their original track IDs" (T25.1 e) is kept as the natural key `track_nk`. Options: from `trk_` IDs (rejected: circular, the stitched artifact's IDs depend on the payload holding the stitch_id); a stitch only for chains of ≥ 2 (rejected: two kinds of unit in S4).
2. **S3 configuration ID.** The four T25.1 parameters enter `trc_id` under the key `stitch` (`s3_config.trc_id(config, g_max, stitch)`); absent, the hashed dict is the E-1.2.25 one (T25.0). The stitched S3 artifact is built by `stitching.apply` from the unstitched one (same tracks and points, `stitch_id` added, derived IDs recomputed).
3. **S4 units.** With `stitch_id` on the points, S4 pairs stitched identities: `pow.person_track_id` / `forklift_track_id` hold the stitch_id (the field type is `id`; the prefix `sti` tells them apart); units are ordered by their first member's local ID; the unit's point and object state on a frame are its member's; `object_state` stays per original track (kinematics never cross members). Every point or none carries `stitch_id`, else ERR-SPEC.
4. **Schema.** `track_point.stitch_id`, `candidate_event.n_members` (i64) and `candidate_event.unobserved_gap_s` (f64, ≥ 0) are `@absent_ok` (AR-67 mechanism): written only when the rule is on. With T25.2 on every event carries them; an unjoined event has n_members 1 and unobserved_gap_s 0.0.
5. **event_link of a T25.2 join** (T25.2 c leaves the representation to an AR): one row per consecutive member pair, episode_a_nk < episode_b_nk by JCS (§5.6); `edge = U`; `basis = [same_camera]`; time_offset_s, clock_sigma_s, median_mahalanobis null (`not_applicable`); n_overlap_frames 0; link_conflict false; `linkage_version = "T25.2_pow_continuity_v1"`. `U` because §7's `D` would assert incompatibility and `L`/`P` would claim a cross-camera linkage; `U` is never an allowed grouping edge, so no §7 grouping can use it. The event's `edges_used` stays empty (no §7 edge was used). Options: a new enum value (rejected: a schema enum change for a meaning T25.2 already gives through linkage_version).
6. **grouping_algorithm_version** = `single_camera_t25_2_v1` on every event of an S5 run with T25.2 on (`single_camera_v1` otherwise).
7. **rule_configuration.lifecycle** carries `m_gap_s` and `join_across_pow` only when present; `join_across_pow = false` is present (its own configuration ID) and off. The record is hashed, not stored as a table, so the `lifecycle` struct line in `tables.py` is unchanged.
8. **Readings of edge cases (engineering tolerances).** T25.1: endpoint times are the frames' `t_tl_s`; "between t_A and t_B" is the T8.1 test `pows._break_between` on the endpoint frames; overlap = A's last point (any state) not before B's first point; 0 < Δt is Δt > 1e-9; gate and T_s comparisons allow 1e-9; the image gate applies when either endpoint lacks a floor position; a class without `stitch_v_max_mps` is ERR-SPEC; v_max > 0 required. T25.2: consecutive episodes of a pair in (t_start, start_frame, nk) order; "e₂ starting after e₁ ends" is gap ≥ −1e-9; gap ≤ max + 1e-9; the T = 1 test covers frame indices [end_frame_excl(e₁), start_frame(e₂)) in both POWs' flag series; the coverage test is on (t_end(e₁), t_start(e₂)) with the T8.1 1e-9 allowance; unobserved_gap_s = Σ max(0, gap). T25.3: δ_nom is the recording's `decode_summary.delta_nom_s`; m_gap_s ≤ 0 is ERR-SPEC.
9. **Floor positions for the T25.1 gate** in the D-58 drivers are the `object_state` x_m, y_m of the S4 built from the unstitched S3 with the run's T24 configuration (the stored C-v2 S4), read, not recomputed: "after T24" as T25.1 (c) states.
10. **Export dictionary.** `data_dictionary.json` of the fixture export lists the two new optional `candidate_event` properties; its hash and the export manifest change. No artifact, data file or ID changes.
11. **M0 check (W-02 adaptation).** `e6072ef` predates `s3_config.py` and the T24 schema mark, so the T25 diff of the files M0 uses (events, substrate, schema) was applied there together with the T24 `@absent_ok` machinery (91992e2: registry, validate, types, files, artifact) and a 4-line call-site adaptation (the HEAD point-state index, which `e6072ef` lacks). Two runs: the 12 IDs and payload hashes equal the M0 report and the unpatched run; 46 of 48 exported files equal; the other two are item 10's dictionary and the export manifest that hashes it.
**Pinned by:** `tests/substrate/test_t25_stitching.py`, `tests/events/test_t25_join.py`.
**Reverse:** remove `rq1/tracking/stitching.py`, `stitched_units` in `substrate/builder.py`, the T25 branch in `events/s5.py` and `events/candidates.py`, `engine.m_gap_frames`, the `stitch` key in `s3_config.trc_id` and the three schema fields; with the parameters absent nothing else changes.

## AR-70 — Representation choices of the D-60 registration, split addendum and Colab S2 package (D-60 STEPS 2–4)   status: PROPOSED (for review at the next stop)
Representation and engineering only. No measured value, label, partition role, grouping rule, detector setting or contract value changes; the roles, the grouping by layout and the criteria are the Owner's (D-60). Pinned by `tests/adapters/test_d60_registration.py`, `tests/splits/test_d60_addendum.py`, `tests/colab/test_runner.py`, `tests/colab/test_equivalence.py`.
1. **`generation_batch` string** (ruling 4: "the dataset's `val` folder name and revision, `MTMC_Tracking_2026@d38193b`"): `MTMC_Tracking_2026/<train|val>@d38193b`, the published folder of each scene and the revision as the ruling writes it (`registration.d59_generation_batch`). Options: the literal `MTMC_Tracking_2026@d38193b` for all 11 (drops the folder the ruling names); the folder without the revision (drops the revision). No effect on any group or partition: `generation_batch` is not a leakage-edge field (`leakage.SCENE_FIELDS`, `SCRIPT_FIELDS`), and its batch family (first path element, used only by the X0b draw strata) is `MTMC_Tracking_2026` under every option. The stored Warehouse_000 / 001 S0 keep `MTMC_Tracking_2026/train` (never rewritten).
2. **`layout_id`** = the lower-case hex SHA-256 of `map.png`, hashed from the file on disk and checked equal to `candidates.json` (the Git-LFS SHA-256) before registration (`registration.map_layout_id`). Without the D-60 arguments `smartspaces_metadata` returns the T-18 input unchanged.
3. **Layout grouping** (STEP 3: "one group per layout"): edge type `same_layout`, one chain per `layout_id` over the sorted recording IDs, passed to `builder.freeze` through a new optional `extra_edges` (absent: the metadata groups, X0b unchanged). It is not added to `leakage.SCRIPT_FIELDS`, which would change the T14.1 rule that X0b was built under. Every X0b-A1 group lists `same_layout`, a single-scene layout too. The X0c audit of X0b-A1 receives every metadata and layout edge among its recordings, discovery basis `metadata`.
4. **Split record:** `split_label` `X0b-A1`, version `1`, tier `T1` (no spanning group), basis `metadata_only`, `parent_version_id` null `not_applicable` (it is not a PR-01 revision of X0b), `shared_scene_content` false (as X0b; that the tier-2 layout equals Warehouse_000's map is recorded in the freeze record, `x0b_checks`). X0b's artifact ID is an input artifact of X0b-A1, and the addendum rule is hashed as an `sdr` configuration (`d60.ADDENDUM_RECORD`). `frozen_utc` is a constant taken once at the freeze (AR-57 item 6), outside the hashes (AR-7). Freeze record: `docs/preregistration/freeze_record_X0b-A1.json`.
5. **Partitions `test_layout_holdout` and `reserve`:** PR-01 orders train > validation > test only, so `builder.revise` refuses a revision involving them with ERR-SPEC (a CR is needed first, none now: the audit has no violation). The listing sort key puts them after the PR-01 partitions. The R-2 gate (`check_s8_allowed`) guards `test` only; a gate for `test_layout_holdout` is to be added before T-26e, when the first S8 on tier 1 is built.
6. **Equivalence check readings** (STEP 4 c; the criteria themselves are unchanged and never loosened): pairs per frame and class, one-to-one, greedy by IoU descending, CPU boxes with score ≥ class threshold against every Colab box of the file; C1 on those pairs for CPU boxes ≥ threshold + 0.02; C2 as |Δscore| with numpy's default linear P99 on two sets (pairs of CPU boxes ≥ threshold, and ≥ threshold + 0.02), both ≤ 0.02; C3 on boxes ≥ threshold, per class, per camera and for both cameras together, |Δn| ≤ 0.02 · n_cpu; the frame lists must be equal. Where the ruling left a choice the stricter reading is taken, and the check passes only when every reading passes.
7. **Equivalence cameras** ("the lowest camera ID in each"): the lexicographically lowest S0 `camera_id` per viewpoint class among the 116 v2 tuning cameras (all have CPU S2): ceiling `cam_3awgzo42lghuqxh37yba5a5an3` (`rec_67do32mc4zwrtblayv5nixp4c2`), eye level `cam_2jf7haavqijxqwi7diqbxanwvk` (`rec_4vmkmof7sgq7fbjqm6zb64xpko`).
8. **Colab package:** job manifests (`format` `rq1-colab-job-1`) carry each camera's eligible frames from its stored S1 `frame` table as runs [decode_seq, length, frame_index]; the weights are not uploaded, the notebook fetches them on Colab from the published URLs of `zero_shot_weights.json` and checks size and SHA-256; the raw file has every key of the CPU file plus `device_name`, `cuda`, `av`, `input_sha256`, with `predict.device` the Colab device and `code_commit` the runner's installed commit; a camera is finished when its `.done.json` sidecar's SHA-256 equals its output file.
9. **S1 of the D-59 recordings:** the decode configuration of the T-17 S1 runs (`part3/t17_oracle.py` DECODE_RECORD, the S1 the tuning cameras use); `retrieved_utc` of the 11 S0 = the arrival time of the last D-59 file (file mtime, 2026-11-25T03:28:56Z), one constant as T-18 did.
**Reverse:** items 1–2: drop the two arguments (scenes then register under the T-18 lineage); item 3: drop `extra_edges` and `d60.layout_edges`; items 4–9: the D-60 modules and scripts only (`rq1/pipeline/d60.py`, `research/datasets/part5/s0_s1_d59.py`, `research/preregistration/freeze_x0b_a1.py`, `research/colab/`).

## CR-038 (2026-11-26) — g_max for recordings that are not 30 fps: 45 frames or 1.5 s?   status: DECIDED (Owner decision D-63 ruling 4, 26 Nov 2026: reading (b); implementation deferred)
**Source:** D-61 STEP 0 ("Confirm all held data is 30 fps (δ_nom = 1/30 s), so that m_gap_s 1.5 → 45 frames and g_max 45 frames ↔ 1.5 s") and D-61 §1.3 (g_max "45 frames (1.5 s)").
**Finding (STEP 0, declared stream rate, every held video):** SDG 690 / 690 at 30/1; SmartSpaces synthetic (incl. the D-59 scenes) 156 / 156 at 30/1; SmartSpaces real `Warehouse_026/027` 11 / 11 at 30/1. **Safe and Unsafe Behaviours (Mendeley, real, testing only, reference-free): 0 of 371 at 30 fps.** Declared average rates lie between 21.53 and 25.25 fps (median 24.83; 25/1 on 66 clips, 24.83 on 156, 24.8 on 57, the rest scattered), so most clips are variable-rate.
**Gap:** m_gap_s is in seconds and converts per recording (T25.3: ⌊m_gap_s / δ_nom + 1e-9⌋), so it keeps 1.5 s at any rate. g_max is a frame count (T8.1 POW break, `pows.build(g_max)`). On a 25 fps clip, 45 frames is 1.8 s, and 1.5 s would be 37 frames. The ruling gives both numbers, and they disagree off 30 fps. The two readings give different POW structure, IE shares and event counts on those clips.
**Readings:** (a) g_max = 45 frames on every recording (the stored parameter); (b) g_max = ⌊1.5 s / δ_nom + 1e-9⌋ per recording (needs a seconds-valued parameter, which is a contract representation change).
**Effect now:** none. No D-61 step runs on the Mendeley clips, and every recording that D-61 STEPS 3–6 touch is 30 fps, where (a) = (b) = 45 frames. The freeze record states g_max as 45 frames, with δ_nom 1/30 s on every recording it covers.
**Agent's recommendation:** none; the Owner and the Architect decide before any S4 on a recording that is not 30 fps.
**Resolution (D-63 ruling 4, 26 Nov 2026):** reading (b). g_max means 1.5 s and is converted per recording as ⌊1.5 / δ_nom + 1e-9⌋, as m_gap_s is. At 30 fps this equals 45 frames; every v2 recording is 30 fps, so no v2 configuration ID, artifact or result changes. The seconds-valued representation is implemented only before the first S4 on a recording that is not 30 fps, under its own CR. No v2 configuration is changed now.

## CR-039 (2026-11-26) — v2 references on SmartSpaces (Warehouse_000, D-60 tier 1): the T21 amendment promised for v2 does not exist   status: DEFERRED (Owner decision D-63 ruling 5, 26 Nov 2026: tier 1 deferred past 1 Dec 2026)
**Source:** D-61 §1.7 ("References are rebuilt once with the v2 base values (T21.1), for every partition") and STEP 5 ("for tuning, reporting and test"); the reporting order includes "tier 1 (after D-60)". D-39 / D-40 item 3: T21.1 is infeasible on SmartSpaces scene-wide truth (about 4.44 million reference pair-frames per camera, about 200 h, more memory than this machine has). "For v2 the Architect will amend T21 to restrict reference pairs in a camera to pairs that are jointly visible (T20.1) in that camera at least once."
**Gap:** Appendix T has no such amendment (searched up to T25, E-1.2.26). Without it, T21.1 as written still applies and remains infeasible. A restriction ("jointly visible at least once", or another) changes which references exist, and so the EV-M denominators. That is a reference-meaning change for the Architect, not an agent resolution.
**Done under D-61:** the v2 reference sets are built for the SDG tuning (116), reporting (110) and test (471) cameras only. `m1a_common.Context.reference_camera` refuses SmartSpaces (pinned by `tests/m1a/test_v2_references.py`).
**Affected later:** the tier-1 evaluation (T-26e, D-60 ruling 1) needs references on the 45 tier-1 SmartSpaces cameras, and so does any SmartSpaces EV-M in v2. It is blocked until T21 is amended.
**Agent's recommendation:** none; the Architect drafts the amendment, and the Owner decides.
**Resolution (D-63 ruling 5, 26 Nov 2026):** DEFERRED past 1 Dec 2026. The T21 jointly-visible amendment for SmartSpaces is not written for this submission. SmartSpaces event-level results are excluded from the submission, with the reason stated (register D6). The tier-1 Colab run (D-62 order 3) is skipped before 1 Dec. The D-60 tier-1 manifest, X0b-A1 and the reserve stay frozen and untouched.

## AR-71 — Representation choices of the D-61 v2 values, the STEP 4 diagnostic check and the v2 freeze (D-61 STEPS 4–5)   status: ACCEPTED (Owner decision D-63 rulings 1 and 6, 26 Nov 2026: items 1–10 accepted; item 11 accepted as the definition of `lock_sha256`)
Representation and engineering only. Every value is the Owner's (D-61 §1.3–1.6). No rule, label, matching rule, EV definition or v1 record changes. Pinned by `tests/m1b/test_d61_events.py`, `tests/m1a/test_v2_references.py`, `tests/validation/test_prereg_v2.py`.
1. **m_gap_frames in the lifecycle record.** §5.2 still carries `m_gap_frames` beside `m_gap_s` (T25.3). It holds **45** = ⌊1.5 / (1/30) + 1e-9⌋, the value T25.3 gives at δ_nom 1/30 s. Every recording v2 covers has that δ_nom (D-61 STEP 0). At run time S5 derives the frame count from m_gap_s and the recording's δ_nom (`s5.build`), so the stored 45 never overrides it. Options: keep the v1 value 5 in the record (rejected: it misdescribes the run); null (rejected: the field is required).
2. **One values module.** `research/preregistration/v2_values.py` holds the §1.3–1.5 values as data. The v1 dicts in `m1a_common.py` are unchanged. `m1a_common.substrate_config`, `s4` and `s5_config` take the band edges, the version label and the T25 fields as keyword arguments. With the defaults, every v1 configuration ID is unchanged (`test_v1_defaults_unchanged` checks the stored T-21 BL-6 S5 configuration ID).
3. **Tracker package ID and g_max.** `trc_7flfpx52d2siiljxkqwcorr7nz` is the D-56 package. Its ID hashes g_max 15 (`s3_config.trc_id`). The v2 S3 configuration IDs (g_max 45; g_max 45 with the T25.1 values) are recorded beside it in the freeze record. The tracker parameters are the package's, unchanged.
4. **T24 for SmartSpaces.** `v2_values.t24_config(cfg, ds)`: the forklift prior gets d = 1.00 × 0.923 m on SmartSpaces (D-54; scaled, not fitted). r_taper is 2.0 m and s_max 0.1 m/px. The pallet_truck prior is unchanged, since pallet trucks are not evaluated (D-22). For SDG the function equals `d54_b_v2.run_config(gate=True, shift=True)` (test).
5. **"IE share caused by the new g_max"** (STEP 4). The IE share is the S_VIEW events carrying `lbl_IE`, divided by all S_VIEW events. The part caused by g_max is the share at g_max 45 minus the share at g_max 15, with every other value at v2, on the same cameras. The g_max 15 runs are counterfactual, built in memory, never stored and never scored. It is a diagnostic description, and it defines no measure.
6. **Diagnostic reference set** (STEP 4). This is the T21.1 procedure at the v2 values, with the label "D-61 diagnostic v2 tuning reference set: diagnostic, not the v2 reference (STEP 5)", stored under `out/m1b/d61/reference_diag/`. It is apart from the STEP 5 set in `out/v2/references/`.
7. **Detector-path association** in STEP 4 keeps the D-58 instrument: reference boxes from the stored T-21 base oracle S3 (`evaluate_pilot.ref_boxes`). The A+T25 association uses the new g_max 45 oracle S3.
8. **Test-partition reference loader.** `Context.reference_camera` and `load_for_reference` serve SDG validation and test recordings for T21.1 reference building only (D-61 §1.7 and the STEP 5 hard-limit exception). `Context.camera` still refuses test with ERR-LEAKAGE.
9. **v2 criteria records** (`rq1.pipeline.prereg_v2`). They are the v1 records #1–#4 with version "2", the v2 `preregistration_ref` and the v2 `frozen_utc`, which gives new acc IDs. The half-threshold basis is held in `BASIS` and the freeze record, not in an acceptance_criterion field.
10. **Freeze record content.** Configuration IDs:
    - detector: the S2 configuration IDs of the tuning S2, and the weight hashes, published and on disk;
    - tracker: item 3;
    - substrate, geometry and rule configurations per dataset: system BL-2 to BL-6 with T25.2 on, and reference BL-6 with T25.2 off;
    - evaluation_config per reference set and iou_m 0.3 / 0.5 / 0.7, seed 2026111402, n_miss 5. The label-group mapping is from the v2 references, with `rin` IDs formed as in `d58_events.references_from`.

    The record also holds a per-set hash over (rec_id, S3/S4/S5 IDs and payload hashes, reference-list hash) and a per-camera listing.
11. **Window lock: proposal only** (STEP 6). The contract names `locked_utc` and `lock_sha256` but does not define what the hash covers. The proposal: per window of V0 `m1a-sdg-test`, SHA-256 of the JCS form of the window's natural key and bounds, the reference-set label, the camera's v2 reference S5 (ID and payload hash) and the reference entries overlapping [t_start, t_guard_end) (`readiness_v2.window_lock_hash`; `docs/preregistration/window_lock_proposal_v2.json`). Nothing is locked, no V0 artifact is rewritten, and `locked_utc` stays null (`pending_review`). The Architect accepts or replaces the definition before the lock.
    **D-63 ruling 1:** accepted as written. The lock is applied in D-63 STEP 3, as a new lock artifact referencing V0, before any S3 or later stage on test.
**Reverse:** remove `v2_values.py`, `v2_references.py`, `freeze_v2.py`, `prereg_v2.py`, `d61_events.py`, `readiness_v2.py`, the keyword arguments and `reference_camera` / `load_for_reference` in `m1a_common.py`; nothing stored before D-61 changes.

## AR-72 — Representation of the v2 reference-window lock (D-63 STEP 3)   status: PROPOSED (for review at the next stop)
Representation and engineering only. The hash content is AR-71 item 11, accepted by the Owner (D-63 ruling 1); no window, bound, reference, label or count changes. Pinned by `tests/m1a/test_window_lock_v2.py`.
1. **Lock artifact.** The lock is a new artifact of stage `V0` (the stage of `reference_window`, the table that holds the lock fields). It holds a copy of V0's `sampling_plan` row, needed because `reference_window.plan_nk` is a same-artifact key (§2.4), and the 471 windows of V0 `m1a-sdg-test`, with three fields set: `annotation_status = locked`, `locked_utc`, `lock_sha256` (their null reasons become null). Every other field is as stored in V0. Inputs: the V0 artifact (art_hfchmhd3…) and the 471 v2 test reference S5 artifacts that the hashes cover. No configuration ID; no seed. Schema bundle E-1.2.26. V0 is not rewritten: its manifest bytes and its reconstruction are checked unchanged after the build. Options: rewriting V0 (refused by D-63 STEP 3); a new table type (rejected: a schema change for fields the contract already has).
2. **Window record IDs.** `rwn_` and `spl_` IDs are observation IDs scoped to their artifact (§2.3), so the lock artifact's window and plan IDs differ from V0's. The natural keys (`plan_nk`, `camera_group_id`, `window_index`) are unchanged, and windows are joined by natural key.
3. **Transition.** `planned → locked` directly: the v2 test references come from simulator truth (T21.1), with no human annotation, so `in_progress`, `double_annotated` and `adjudicated` do not occur. A window that is not `planned` is refused (ERR-SPEC).
4. **locked_utc** = 2026-11-26T15:47:13Z, one constant taken once at the lock (AR-57 item 6), an event column outside the payload hash (AR-7). Both builds use it, so the payload and files are identical.
5. **Check against the proposal.** Every lock hash is checked equal to the D-61 STEP 6 proposal (`window_lock_proposal_v2.json`), and the count of differences is recorded (`docs/preregistration/window_lock_v2.json`).
**Reverse:** delete the lock artifact folder (git-ignored) and the record; V0 is unaffected. Any S8 on test then fails VR-E-054 again.

## CR-040 (2026-11-27) — VR-E-041 value scan hits random content-hashed IDs (`osha` inside an `exp_` ID)   status: OPEN
- Found at T-29h. `rq1.export.obx.check_content` scans every string value of every exported row for the VR-E-041 / section 11 forbidden fragments (CT-E-27), including artifact and row IDs. IDs are base32 content hashes and include `code_commit`, so any commit can produce an ID containing a forbidden fragment by chance. At commit 610ff29 the M0 fixture produced `exp_ppb4v7enmipxsy2zp7jjoshaf5`, and `tests/pipeline/test_m0.py` errors (6) with ERR-FORBIDDEN-FIELD.
- Readings: (a) VR-E-041 applies to names and human-readable values, not to opaque ID values; exempt fields of ID type (prefix `xxx_` + base32) from the value scan. (b) The scan covers every value as written; ID generation must then avoid the fragments (for example re-encode or salt), which changes ID derivation. (c) Leave as is; a commit that trips it is re-committed.
- Why a CR and not an AR: (a) narrows the scope of a contract validation rule; (b) changes artifact-ID derivation. Neither changes a measured value, but the scope of VR-E-041 is the contract's.
- Agent's recommendation: (a), with a test that a forbidden word in a non-ID value is still rejected.
- Affected: `src/rq1/export/obx.py` (`check_content`, `_strings`), `tests/pipeline/test_m0.py`, `tests/export/*`.

