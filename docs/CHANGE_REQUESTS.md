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

## CR-007 (2026-11-12) — Footprint anchor on the camera-based path   status: DEFERRED (D-8, to T-22); evidence added 14 Nov 2026

**Raised by:** implementation agent. **Task:** T-08 (not blocking M0); blocks the detector path (T-22, T-23, M1b).
**Contract sections:** E-1.2.1 §5.2 `footprint_prior.anchor` · enum{box_bottom_centre, rear_axle, centre}; §5.5.
**Meaning-affecting:** yes. It shifts the forklift footprint, and so clearance.

**Problem.** A calibrated camera gives the floor point under the box's bottom centre (`foot_point_px`). The contract does not say how that point relates to the footprint rectangle for `box_bottom_centre` or `rear_axle` anchors, for example how far behind or below the centre it lies, and along which axis given yaw. Oracle positions are footprint centres, so the M0 fixtures are unaffected. The builder currently treats the projected point as the footprint centre, which is correct only for `anchor = centre`.
**Proposed resolution:** for `box_bottom_centre`, use the projected point as the footprint centre (the bottom-centre of a ground-contact box approximates the footprint's image centre). For `rear_axle`, place the centre at `length/2 − rear_overhang` ahead along yaw, with `rear_overhang` added to the prior. If yaw is unknown, use the circumscribed disc as in T8.2.
**Decision:** DEFERRED to T-22 (D-8, 12 Nov 2026). Reopen with GV-03/GV-04 evidence. Until then the oracle and simulator path uses the simulator footprint centre.   **Approver:** Research Owner
**Evidence added for the T-22 decision (Architect ruling A of 14 Nov 2026, from CR-023):** on SDG the T8.2 heading fallback (yaw = direction of travel of the footprint centre) is about 77° off the body axis during pivot turns. Over the 67 runs checked, 7,860 of 16,507 moving-forklift frames (≥ 0.3 m/s) are turning frames (yaw rate ≥ 5°/s over 10 frames); on them the angle between the direction of travel and the box long axis has median 77.5°, P99 81.3°, and 74 % lie beyond 75°. On straight frames (8,647) it is within 10.5° on every frame. SmartSpaces turning frames: median 2.5°, P99 11.3°. Source: `research/datasets/part3/yaw_motion_check.json`. A camera-based path without a supplied yaw would therefore orient the forklift rectangle almost across the body during such turns; the anchor rule and the yaw fallback should be decided together.

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

## AR-53 — Representation details of T17 oracle tracks and the SmartSpaces S0 (T-18)   status: item 3 ACCEPTED (Architect, 14 Nov 2026; per-dataset evidence recorded below); other items pending review
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

## AR-54 — T16 mechanics, the real SmartSpaces rows and the access log (T-18)   status: item 3 ACCEPTED (Architect, 14 Nov 2026: no calibration for 026/027); other items pending review
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

## AR-55 — Representation details of the T18 amendments and the count rebuild (T-18)   status: item 6 ACCEPTED as pinned (Architect, 14 Nov 2026); item 4's frame unit superseded by T19; other items pending review
- **Gaps and choices** (none changes a T17 or T18 rule):
  1. **What a run is.** A maximal sequence of consecutive frames, between two visible frames of the object in the camera, on which it is not visible. Frames without a truth record, truth-defect frames (T17.5, "treated as not visible") and frames whose reprojection is empty all count. Inside a run of at most g_max frames T17.2 still applies frame by frame (empty reprojection → lost). Leading and trailing not-visible frames are outside the span and are no run (T17.3).
  2. **Counts.** `lost` stays the number of all lost frames (T17.7); `lost_long_run` is the part of it in runs longer than g_max.
  3. **g_max as input.** `camera_tracks` takes g_max as a required argument; a negative value is refused (ERR-SPEC); g_max = 0 makes every run lost. The oracle configuration record (`orc_`) of the driver now carries g_max, because the oracle points depend on it. The driver uses the TEST-ONLY g_max (15); the artifacts are TEST-ONLY and are rebuilt under the frozen pre-registration.
  4. **Run-length statistics (T18 amendment 3).** Lengths in decoded frames (CR-024). Median, P90 and P99 are nearest-rank (the value at rank ⌈q·n⌉ of the sorted lengths), so each is an observed length. The files also keep the full histogram and, for the test value of g_max, the runs and frames above it.
  5. **Rebuild without decoding again.** T18 changes nothing in S0 or S1. The rebuild reuses each recording's S1 artifact of the first run after verifying it (file hashes, payload reconstruction, same decode configuration and S0 input); the new S3 artifacts carry contract label E-1.2.16 and name that S1 artifact as input. The S0 and S1 artifacts keep the label E-1.2.15 under which they were built. The count files record the S1 code commit per camera.
  6. **The before/after test. Review flag.** "Pair-level S4/S5 output on a fixture is identical before and after amendment 2" holds, and is tested, for a fixture whose not-visible run has g_max frames (S3, S4 and S5 artifact IDs identical). For a run of g_max + 1 frames the output is not identical, and cannot be under T8.1: before, the predicted points were joint frames and one POW covered the run; after, the run is a gap longer than g_max, the POW ends with `gap_exceeded` and a second POW continues it. Both cases are pinned in `tests/events/test_t18_oracle_absence.py`. If the Architect expected identity for long runs too, this item becomes a CR. **Architect ruling (14 Nov 2026): ACCEPTED as pinned.** Identity of S4/S5 output is required only for runs ≤ g_max. For longer runs the new behaviour is intended: the POW ends with `gap_exceeded` and a continuation POW starts. The Architect's earlier statement that no pair-level result changes is withdrawn.
- **No meaning effect:** items 1–5 are representation, parsing or build mechanics of T18 as written (the one unit question is CR-024); item 6 reports a consequence of T18 and T8.1 and changes nothing.
- **Files/tests:** `adapters/oracle_truth.py`, `research/datasets/part3/t17_oracle.py`; `tests/adapters/test_t17_oracle_truth.py` (`test_t18_*`), `tests/events/test_t18_oracle_absence.py`. **Reverse:** item 2: drop the key; item 4: change `run_length_summary`; item 5: run the driver without the two reuse arguments.

## AR-56 — Representation details of T19 and the POW sensitivity counts (T-18, T-20)
- **Gaps and choices** (none changes a T17, T18 or T19 rule):
  1. **Counts.** In a run of at most g_max eligible frames, an ineligible frame gets no point and is counted as `not_eligible_in_run` (neither predicted nor lost). In a longer run every frame, eligible or not, is counted as lost ("lost on every frame") and in `lost_long_run`. A visible frame that is not eligible still yields a tracked point in `camera_tracks`; `s3_truth` leaves it out, as before (AR-53 item 6), and the driver counts it (`points_on_ineligible_frames`).
  2. **Where a run ends. Review flag.** A run lies between two frames on which the dataset lists the object as visible (T17.2), whether or not those frames are eligible; T19 changes how its length is counted, not where it ends. So two runs of 10 eligible frames on either side of a visible but ineligible frame are two runs of 10, although S4 then sees 20 consecutive eligible frames without a point (a T8.1 gap of 20). The other reading (a run ends only at an eligible visible frame) would make the oracle run equal to the T8.1 gap in every case. The driver counts the eligible frames whose outcome would differ (`frames_in_runs_merged_across_ineligible_visible`); the totals are in the Progress log. If the count on held data is not 0, or the Architect prefers the other reading, this item becomes a CR. Pinned by `test_t19_a_visible_frame_that_is_not_eligible_still_ends_a_run_ar_56`.
  3. **Run-length statistics** are in eligible frames (the unit of the rule). A run whose frames are all ineligible has length 0 and is kept in the table.
  4. **POW sensitivity counts (ruling C).** For g ∈ {5, 15, 30, 60} the driver builds the oracle points with g_max = g and then the T8.1 POWs of every person–forklift pair of each camera with the same g (`pows.build`, eligible frames and coverage of the recording's S1 artifact), and counts the POWs and those with `end_reason = gap_exceeded`. No geometry, no S4 artifact, no rule, no reference. Reprojections are computed once per camera and reused across the four values (`cache`).
  5. **Labels.** The rebuilt S3 artifacts carry contract label E-1.2.17; S0 and S1 keep E-1.2.15 (AR-55 item 5).
- **No meaning effect:** items 1 and 3–5 are counting and build mechanics; item 2 is flagged.
- **Files/tests:** `adapters/oracle_truth.py`, `research/datasets/part3/t17_oracle.py`; `tests/adapters/test_t17_oracle_truth.py` (`test_t19_*`, `test_reprojection_cache_gives_the_same_tracks`). **Reverse:** item 2: build runs from eligible visible frames in `camera_tracks`.
