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

## AR-2 — Column types where the contract lists names only
- **Gap:** 25 tables in §5.8–5.10 and F.1 A5 give field names without types. **Options:** (a) infer from suffix conventions (§1.2) and enums, (b) block. **Choice:** (a). Counts are `i64`, durations and ratios `f64`, references `id`, free references `str`.
- **No meaning effect:** storage types only; no value or formula is set. **Files/tests:** `schema/tables.py`, list in `reports/T-01_vr_coverage.md`; `test_generates_valid_arrow_and_json_schema`, `test_every_table_round_trips_through_parquet`. **Reverse:** edit the type lines.

## AR-3 — ID prefixes the contract does not give
- **Gap:** F.1 A1.2 computes `id(prefix, …)` for configurations, and §2.1 gives human records a table prefix, but no prefix is listed for these tables. **Options:** (a) assign short unique prefixes, (b) use one generic prefix. **Choice:** (a): `fpp sbc bsc rcf dcf gcf spc rop rin rgm rcl tia tis anr anc rva adj rtp alg ecl ser`.
- **No meaning effect:** the prefix labels the ID and is not hashed by `id()`. **Files/tests:** `schema/tables.py`; `test_ar3_prefixes`. **Reverse:** rename the prefix; IDs change only in their label.

## AR-4 — Storage form of `<table>_nk`
- **Gap:** Appendix T T5 fixes the payload value as a JSON array (`["rec_a",1]`) but not its Parquet column type. A natural key is heterogeneous, so it has no single Arrow list type. **Options:** (a) store JCS text in a utf8 column and decode on read, (b) one Arrow struct per table. **Choice:** (a).
- **No meaning effect:** hashing always uses the decoded array, so `payload_sha256` is unaffected; CT-FK-05 reconstruction checks it. **Files/tests:** `schema/registry.py`; `test_nk_is_json_array_in_json_schema_and_text_in_arrow`, `test_nested_values_round_trip`. **Reverse:** swap `_encode`/`_decode`.

## AR-5 — Fields of `decode_config`, `geometry_config`, `sampling_plan_config`
- **Gap:** F.1 A1.2 lists these configuration tables with no fields. **Options:** (a) define containers holding only parameters named in §5.2, §8 and §14, (b) block. **Choice:** (a). No default values exist; all values come from configuration records.
- **No meaning effect:** containers only; parameter definitions are unchanged. **Files/tests:** `schema/tables.py`; `test_every_contract_table_is_registered`. **Reverse:** edit the definitions.

## AR-6 — Configuration field names given only in prose; `version_label`
- **Gap:** §5.2 names some fields in prose, and Package F §3 requires `version_label = "TEST-ONLY"` without listing it in §5.2. **Options:** (a) use the §14 parameter names and add a nullable `version_label`, (b) free-form maps. **Choice:** (a).
- **No meaning effect:** naming only. It enables the T-15 TEST-ONLY guard. **Files/tests:** `schema/tables.py`; `test_minimal_row_is_valid_and_loads_into_arrow`. **Reverse:** rename.

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

## AR-9 — `label_source` on `ref_geometry`
- **Gap:** VR-E-055 constrains reference records, but §5.8 gives `ref_geometry` no such column. **Options:** (a) add it, (b) exempt the table. **Choice:** (a), the stricter option that keeps the namespace guard complete.
- **No meaning effect:** provenance only. **Files/tests:** `schema/tables.py`; `test_ar9_ref_geometry_has_label_source`. **Reverse:** remove the line.

## AR-10 — VR-E-019 does not exist
- **Gap:** §12.1 gives the range 010–021, but Appendix T has no VR-E-019. **Evidence:** Package E, Validation rules table, goes from VR-E-018 (line 871) straight to VR-E-020 (line 872), so this is a numbering gap, not lost text. **Options:** (a) treat as non-existent, (b) raise a CR. **Choice:** (a).
- **No meaning effect:** no rule is added or removed. **Files/tests:** `schema/coverage.py`; `test_coverage_lists_every_active_rule_exactly_once`. **Reverse:** add the rule to `ACTIVE`.

## AR-11 — Scope of VR-E-041 and `stage_error.severity`
- **Gap:** Appendix T forbids "severity" while §5.10 defines `stage_error.severity` (an error-handling level). **Options:** (a) forbid the field names everywhere with that one exemption, (b) check E2 tables only. **Choice:** (a), the stricter option.
- **No meaning effect:** the exempted column is not a harm quantity. **Files/tests:** `schema/registry.py`; `test_no_forbidden_field_in_any_table`. **Reverse:** remove the exemption.

## AR-12 — Where the VR-E-070 ID applies
- **Gap:** E-1.2.1 §5.1 cites VR-E-070 for `site.approvals_ref`; Appendix T amends VR-E-070 to source-file retention and clip access. **Options:** (a) apply Appendix T to the ID and keep the §5.1 requirement under its own check, (b) drop the site check. **Choice:** (a), so no requirement is lost. Check name: `SITE-APPROVALS`.
- **No meaning effect:** both requirements are enforced. **Files/tests:** `schema/validate.py`, `schema/vr_rules.py`; `test_site_approvals_still_required_for_real_origins`. **Reverse:** rename the rule tag.

## AR-13 — Inputs for VR-E-018 and VR-E-021
- **Gap:** VR-E-018 needs "a GV-05 evidence reference for the stratum", and no table holds one. VR-E-021 requires SI units, which a validator cannot infer from a number. **Options:** (a) pass GV-05 evidence as a validator argument keyed by calibration ID, and check unit suffixes, (b) add columns. **Choice:** (a).
- **No meaning effect:** validators only; `sigma_status` is unchanged. **Files/tests:** `schema/vr_rules.py`; VR-E-018 and VR-E-021 cases. **Reverse:** change the arguments.

## AR-14 — Schema version string
- **Gap:** VR-E-001 and CT-E-30 need a major-version test, but no format for `schema_version` is stated. **Options:** (a) use the contract version with Package F §9's rule (E-1.2.x minor, E-1.3 major), (b) separate numbering. **Choice:** (a).
- **No meaning effect:** compatibility handling only. **Files/tests:** `schema/errors.py`; `test_schema_major_uses_package_f_section_9`. **Reverse:** change `_major`.

## AR-15 — Rounding of microsecond keys
- **Gap:** CN-2 says round half to even, but not whether on the exact binary value or a float product. **Options:** (a) exact `Decimal`, (b) `round(x * 1e6)`. **Choice:** (a), which does not depend on floating-point multiplication.
- **No meaning effect:** natural-key components only; durations do not use this. **Files/tests:** `ids/core.py`; `test_ar15_time_keys_use_exact_half_even_microseconds`. **Reverse:** change `to_us`.

## AR-16 — ART-ISO prefixes and the error for schema violations
- **Gap:** ART-ISO needs each spec's configurations to be recognizable, but tracker, oracle, model, inference and evaluation configurations have no prefix. §10.3 has no code for a generic schema violation found while building. **Options:** (a) prefixes `trc`, `orc`, `mdl`, `inf`, `evc`, and use `ERR-INVARIANT` for schema violations, (b) add typed spec fields and a new error code. **Choice:** (a), which leaves the §2.1 spec shape and the §10.3 code list unchanged.
- **No meaning effect:** labels and error reporting only. **Files/tests:** `ids/artifact.py`; `test_ct_nk_06_art_iso`, `test_ar16_schema_violation_uses_err_invariant`. **Reverse:** change `ART_ISO` or the raised code.

## AR-17 — Scope of CT-I-03, 04, 07, 08 at T-02
- **Gap:** these tests describe pipeline behaviour (a real `g_max` change, recalibration, rule change, metric lineage) but T-02 precedes S4, S5 and S8. **Options:** (a) test the identity behaviour at builder level now and re-exercise it when those stages exist, (b) defer T-02. **Choice:** (a). The re-runs are scheduled in T-08, T-09, T-14 and T-16.
- **No meaning effect:** test scheduling only. **Files/tests:** `tests/ids/test_identity.py`. **Reverse:** move the tests.

## AR-18 — Integers beyond the range RFC 8785 can hash
- **Gap:** `i64` columns can hold values above 2⁵³−1, but RFC 8785 (I-JSON) cannot serialize them, and the contract's hash requires JCS. **Options:** (a) reject such values as a schema violation, (b) hash them as strings. **Choice:** (a). It fails visibly, and no contract quantity needs that range (timestamps in microseconds reach about 285 years; published dataset seeds are far smaller).
- **No meaning effect:** rejects an unrepresentable record and changes no valid value. **Files/tests:** `schema/validate.py`; `test_ar18_integers_outside_i_json_range_are_rejected`, `test_ar18_is_a_contract_error_not_a_serializer_crash`. **Reverse:** change the check and add a string form to `canonical.py`.

## AR-19 — Test-only value for `n_miss`
- **Gap:** F.1 A6 adds *n_miss* to §14, and FX-ID-8 mentions it, but Package F §3 gives no test value. **Options:** (a) a labelled TEST-ONLY value of 5 frames, (b) block FX-ID-8. **Choice:** (a). FX-ID-8 has no reference person on any frame, so its result does not depend on the value.
- **No meaning effect:** TEST-ONLY; never a research threshold. If a later fixture's result depends on this value, it needs a CR. **Files/tests:** `fixtures/records.py`; `test_test_only_values`, `test_fx_id_expectations`. **Reverse:** edit the parameter.

## AR-20 — Design details of FX-ID box fixtures
- **Gap:** F.1 A5.2 states expected results but not box coordinates or, for FX-ID-2, when p1 and p2 are present. **Options:** (a) simple constant boxes with each person present only while tracked, (b) both persons present throughout, which would add missed frames that F.1 does not list. **Choice:** (a). FX-ID-6 uses boxes hand-computed to give IoU 0.60 and 0.59.
- **No meaning effect:** fixture inputs only; expected statuses, counts and shares are F.1's. **Files/tests:** `fixtures/records.py`; `test_fx_id_6_box_iou_hand_calculation`, `test_fx_id_expectations`. **Reverse:** change the segments and regenerate.

## AR-21 — Delivering timestamp faults to the decoder; Case A–D layouts
- **Gap:** T-04 asks for clips with missing or duplicate timestamps, but every container tested (Matroska, NUT, AVI, MP4, MPEG-TS) repairs or rejects them on write. Appendix T cites Cases A–D without giving their layout. **Evidence:** Clarification §2.3 worked-example table (cases A–D, including "depth 2" and neighbours for case C) and §2.4 ("an encoder plus deliberate corruption or timestamp stripping"). **Options:** (a) real encoded clips plus a `.faults.json` overlay applied to packets at demux, (b) hand-written container bytes, (c) synthetic frame records with no decoder. **Choice:** (a). The real decoder then sees those timestamp states. Corrupt packets remain real corrupted bytes in the file.
- **No meaning effect:** fixture delivery only; timestamp rules are unchanged. **Limit:** a file that natively lacks a timestamp is not exercised, because none could be produced. **Files/tests:** `fixtures/clips.py`; `tests/clips/test_clip_fixtures.py`. **Reverse:** replace the overlay with crafted files.

## AR-22 — Default camera groups
- **Gap:** §8 tiles windows per camera group, and §5.1 defines `camera_group`, but nothing says which groups S0 creates when none are declared. **Options:** (a) one `whole_session` group per timeline holding its cameras, (b) require declared groups. **Choice:** (a), using an existing enum value. Declared groups can be added later as a new version of the registration.
- **No meaning effect at M0:** fixtures use single-camera or whole-session groups. **Review flag:** for real multi-camera data, group choice affects sampling windows, so research configurations must declare groups explicitly. **Files/tests:** `registry/registrar.py`; `test_ar22_one_whole_session_camera_group_per_timeline`. **Reverse:** remove the default.
- **Architect review (11 Nov 2026): ACCEPTED as written.** Note: "The grouping defines the sampling frame. Changing groups after a sampling plan is frozen requires a new plan version. Research configurations declare the grouping basis explicitly; add this item to the T-20 pre-registration draft." Applied: the T-20 row in WORKPLAN.md now lists the item.

## AR-23 — Fixture records without key fields
- **Gap:** Appendix T FX-B1 and FX-B3 omit fields needed to build a row (`version`, and `valid_from_us` in FX-B1), and FX-B3 states that "field presence and nullability are what the test checks". **Options:** (a) add these in the test adapter, (b) amend the fixture. **Choice:** (a). The committed fixture stays verbatim.
- **No meaning effect:** key fields of a test record only. **Files/tests:** `tests/registry/test_registrar.py` (`_calibration`). **Reverse:** edit the adapter.

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

## AR-25 — "Decode order" is bitstream order; presentation index is decoder output order
- **Gap:** §3.2 says `decode_seq` follows decoder output order, yet computes `reorder_depth` from "presentation index − decode index". A conforming decoder outputs frames in presentation order, so if "decode index" meant output order, the depth would always be 0. **Evidence:** CT-T-16 (Appendix T) requires 0.033 s for Case C, which needs depth 2. Clarification §2.3 case C ("depth 2", decode neighbours f0, f2, f3) confirms. **Options:** (a) decode index = bitstream (packet) order and presentation index = rank in decoder output order, (b) both from output order. Only (a) reproduces CT-T-16; (b) gives 0.067 s. **Choice:** (a). The same meaning applies to ST-2 "±r decode positions" and T7 "adjacent in decode order".
- **No meaning effect beyond the contract:** it is the only reading consistent with the normative values. **Review flag:** T7 adjacency in bitstream order means B-frame streams contribute few adjacent pairs; if none exist, T7 step 3 applies. **Files/tests:** `decode/timestamps.py`, `decode/video.py`; `test_case_c`, `test_ct_t_02_b_frames_follow_pts`. **Reverse:** change `rank` and `index` in `resolve`.
- **Architect review (11 Nov 2026): ACCEPTED.** The `decode_seq` wording is corrected by Appendix T T7.1 (E-1.2.5): `decode_seq` is demux (file/DTS) order, not decoder output order, and `reorder_depth` and the ST-2 neighbourhood use that order. T7.1 also replaces the T7 step 2 adjacency rule with a presentation-order median excluding pairs that overlap an uncertainty region, which removes the B-frame concern above. **Applied:** `decode_seq` = demux position. The presentation index for `reorder_depth` is the decoder output position, which still counts untimed frames; ranking by PTS alone would give Case B depth 1 instead of the Clarification's 0.

## AR-26 — PyAV does not expose FFmpeg's best-effort timestamp
- **Gap:** §3.2 resolves PTS, then the container best-effort timestamp, then DTS-derived. PyAV frames expose only `pts` and `dts`. **Options:** (a) skip the best-effort step, (b) reimplement FFmpeg's guess. **Choice:** (a). Without a PTS, FFmpeg's best-effort value is the DTS, and DTS-derived acceptance (depth 0) is never stricter than best-effort acceptance (depth 0 and consistent). The resolved time is therefore the same, and the frame is labelled `dts_derived`, never `best_effort`. T7's substituted share counts both sources, so it is also unchanged.
- **No meaning effect:** identical times, eligibility and support. **Files/tests:** `decode/timestamps.py`; `test_case_d`. **Reverse:** add a best-effort branch if PyAV exposes it.

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

## AR-33 — Mechanics of the RES draw and bootstrap percentiles
- **Gap:** §8 and N5 fix stratified SRSWOR with π = n_h/N_h and PCG64 seeded from configuration, but not the draw order or the percentile interpolation. **Choice:** windows sorted by (stratum, camera group, window index); strata drawn in sorted order from one `numpy.random.Generator(PCG64(seed))` using `choice(N_h, n_h, replace=False)`. Bootstrap percentiles use numpy's default linear interpolation. `frame_sha256` = SHA-256 of the JCS window list.
- **No meaning effect:** the design, π and weights are as specified; only which equally probable sample occurs depends on these details. Results are reproducible for the pinned numpy. **Files/tests:** `sampling/plan.py`, `evaluation/estimators.py`; `test_res_draw_is_seeded_and_reproducible`. **Reverse:** change the draw loop.

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

## CR-007 (2026-11-12) — Footprint anchor on the camera-based path   status: DEFERRED (D-8, to T-22)

**Raised by:** implementation agent. **Task:** T-08 (not blocking M0); blocks the detector path (T-22, T-23, M1b).
**Contract sections:** E-1.2.1 §5.2 `footprint_prior.anchor` · enum{box_bottom_centre, rear_axle, centre}; §5.5.
**Meaning-affecting:** yes. It shifts the forklift footprint, and so clearance.

**Problem.** A calibrated camera gives the floor point under the box's bottom centre (`foot_point_px`). The contract does not say how that point relates to the footprint rectangle for `box_bottom_centre` or `rear_axle` anchors, for example how far behind or below the centre it lies, and along which axis given yaw. Oracle positions are footprint centres, so the M0 fixtures are unaffected. The builder currently treats the projected point as the footprint centre, which is correct only for `anchor = centre`.
**Proposed resolution:** for `box_bottom_centre`, use the projected point as the footprint centre (the bottom-centre of a ground-contact box approximates the footprint's image centre). For `rear_axle`, place the centre at `length/2 − rear_overhang` ahead along yaw, with `rear_overhang` added to the prior. If yaw is unknown, use the circumscribed disc as in T8.2.
**Decision:** DEFERRED to T-22 (D-8, 12 Nov 2026). Reopen with GV-03/GV-04 evidence. Until then the oracle and simulator path uses the simulator footprint centre.   **Approver:** Research Owner

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

## CR-011 (2026-11-12) — T10.4 bullets that read parameters of providers not enabled   status: OPEN

**Raised by:** implementation agent. **Task:** T-09 (non-blocking: borderline flags never change a frame flag, a label or review_route).
**Contract sections:** Appendix T T10.4; E-1.2.1 §5.2 (`rule_configuration.providers` params).
**Meaning-affecting:** yes, for the reported `borderline_flags` only.

**Problem.** T10.4 conditions only the image-gap bullet on the P provider ("for a configuration whose P provider is R1"). The clearance (`d_p`), speed (`v_min`) and prediction (`d_pc`) bullets carry no condition. But `d_p` and `v_min` are R2 parameters and `d_pc` is an R3 parameter. In an R1-only configuration (BL-2), or a configuration without R3, those thresholds belong to providers that are not enabled. There are two readings:
(a) **Literal.** Apply every bullet in every configuration, using the configuration's values of `d_p`, `v_min` and `d_pc` even when their provider is disabled.
(b) **Apply each bullet only when its provider is enabled:** the clearance and speed bullets with R2, the prediction bullet with R3.
**Implemented meanwhile:** (a), the text as written, pinned by `test_ct_t10_06_clearance_against_d_p[R1]` and `test_ct_t10_06_speed_near_v_min[R1]`. AR-40 item 3 puts those parameters in the configuration ID under either reading.
**Decision:** ______   **Approver:** ______

## AR-41 — Mechanics of the Target B and paired bootstraps and the null cases of N5 estimators (T-13)
- **Gaps and choices:**
  1. **Target B.** "Stratified by data origin" is implemented as follows: in each origin, draw as many leakage groups as that origin has, with replacement. Every window of a drawn group enters with its own weight, once per draw. Origins and groups are sorted before the PCG64 draws, so input order cannot change the interval.
  2. **Percentile intervals** (Targets A and B, paired) use numpy's default linear method, as T10.7(c) does for EV-M8.
  3. **Paired comparison** uses the Target A scheme. Both configurations share each replicate's resampled windows, and the interval is that of R̂_a − R̂_b.
  4. **Null cases** (returned as None, to be stored as null `not_applicable`): Wilson with n = 0; Bland–Altman with n < 2; Cohen's κ with p_e = 1; Krippendorff's α with zero expected disagreement. For α, units with fewer than two values are not pairable, as Krippendorff's standard definition states.
- **No meaning effect:** each choice applies the N5 definition mechanically. Item 1 is the standard stratified cluster bootstrap. **Review flag:** item 1. **Files/tests:** `evaluation/estimators.py`; `tests/evaluation/test_t13.py`. **Reverse:** edit the named functions.
