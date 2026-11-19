# V-02 compatibility audit — Reviewer and adjudication UI (Owner tooling)

Branch `v02-review-ui` (from `m0-implementation` at 636b311). Owner decision of 16 Nov 2026 (V-02 task text). Contract E-1.2.11 as listed in CLAUDE.md, with the later Appendix T sections T14–T21 already in the repository.
Written before any UI code, as item 2 requires.

**Result: STOP.** The schemas, the ID rules, the hash chain, the blindness guard and the κ / α functions already exist and V-02 can reuse them unchanged. But the protocol V-02 has to enforce is not in the contract. Seven rules that the reviewer and adjudication screens need are undefined, and each one changes a label, a status, a denominator or the blind flag (points a, c, d, e and i below). They are raised as **CR-027** and decision request **D-44**. No UI code, tests or records were written. The audit is pushed and work on V-02 stops until D-44 is decided.

Citation note: the task text calls the tables E-37, E-42, E-43 and E-44. No document in the repository uses those labels (checked by search over `docs/`, `research/`, `reports/`, `src/`). This audit identifies the tables by name, from E-1.2.1 §5.8: E-37 = `annotation_record`, E-42 = `reviewer_assessment`, E-43 = `adjudication`, E-44 = `validation_status_log`.

## Summary table

| Point | Contract reference | Existing implementation | Reuse unchanged? | Conflict / gap |
|---|---|---|---|---|
| a. Schemas | E-1.2.1 §5.8; F.1 A1.2 (human IDs), A5.1 (`reference_class` on adjudication) | `src/rq1/schema/tables.py` (`_t("annotator" …)`, `_t("annotation_record" …)`, `_t("reviewer_assessment" …)`, `_t("adjudication" …)`, `_t("validation_status_log" …)`); `schema/registry.py` (`TABLES`, `json_schema`); `schema/validate.py` `validate_row`, `validate_rows` | Yes | **Gaps G4 (confidence scale), G5 (`method` values), G7 (`reference_class` of a C-layer adjudication)**. Schema itself: no conflict |
| b. Identity | E-1.2.1 §1.1 `id` pattern, §0.1 CN-6, §2.1 ("Human-entered record: table prefix, UUIDv7"); F.1 A1.2 row "Human entry" | `validate._ID` regex; registry adds `rva_id`, `adj_id`, `anr_id`, `anc_id`; `validation/status_log.py` `StatusLog.append` (`sts_<uuid7>`) | Yes | None. No shared helper for human IDs exists; V-02 would format `<prefix>_<uuid.uuid7()>` exactly as `StatusLog.append` does |
| c. Status log | E-1.2.1 §5.8 `validation_status_log`; Appendix T CT-E-24; AR-36 item 1 | `validation/status_log.py` `StatusLog.append`, `StatusLog.verify`, `GENESIS` | Yes | **Gaps G3 (which status an adjudication writes) and G6 (`config_id` for a reference target)** |
| d. Namespace and blindness | E-1.2.1 §5.8 (`shown_system_output` false in reference), Appendix T VR-E-053, VR-E-055; F.1 A5.1 RV-01–RV-04 | `schema/vr_rules.py` `check_blind_reference`; `validation/namespace.py` `require_reference`, `check_rv_02`; `evaluation/fitness.py` (RV-03 / FT-05); `export/report.py` (RV-04) | `check_blind_reference`: yes. `require_reference`: **not applicable** to C-layer rows (see d) | **Gap G1 (blindness when the target is itself a system output)** |
| e. Targets | E-1.2.1 §5.6 (`episode`, `candidate_event`), §5.8 (`ref_interaction`, `reviewer_assessment.target_type`) | `events/s5.py` `build`; `pipeline/m0.py`; `validation/converter.py` `SimReferenceConverter.convert` | Yes (read only) | `ref_event` names no table (representation; resolvable by AR once V-02 resumes) |
| f. Agreement | F.1 Appendix N5 (T-13): "Cohen's κ; Krippendorff's α (nominal) for more than two raters" | `evaluation/estimators.py` `cohen_kappa`, `krippendorff_alpha_nominal` | Yes | `agreement_stat_ref` target undefined (nullable; question Q2) |
| g. Downstream | F.1 Appendix N4 (EV-M9, EV-M12); E-1.2.1 §9.5–9.6 (CV2), §11 part 5 | `export/obx.py` `PARTS["5_validation_summary"]`, `check_content`, `serialize`, `export`; `evaluation/fitness.py` (reads a `metric_result`, not adjudications) | Yes | EV-M9 and EV-M12 are **not implemented** anywhere; the matcher does not read adjudications. Only the OBX export reads V-02's tables. Not a conflict; the round-trip test can only use OBX, the validators and `StatusLog.verify` |
| h. D-23 / VIA | D-23 (Owner decision, 12 Nov 2026) | none (VIA is external, A/B layer) | n/a | No overlap at fixture scope. **Gap G2** (how many assessments are required) is related: D-23's 20–30 % double-annotated subset is for A/B annotation, and says nothing about C-layer review |
| i. Wording | E-1.2.1 §6 label table, §6.0 wording line; CLAUDE.md "Never"; `report.py` W1–W6 | `export/report.py` `WORDING`, `lint`, `BANNER` | Yes | Codes can be shown. **Gap G8: no reviewer-facing definition of the five reviewer labels exists** |
| j. Real-data rules | D-21, D-24, D-26, G-FQ (D-25), VR-E-070; access log (AR-54 item 5) | `registry/access_log.py` `AccessLog`; `schema/vr_rules.py` `check_retention`, `check_real_clip_access` | n/a for fixtures | None at fixture scope. Use on real data needs its own Owner decision (Q4) |

Gaps G1–G8 are listed under "Gaps" below and in CR-027.

## a. Schemas

Single schema source: `src/rq1/schema/tables.py`. Field lists below are copied from it; each matches E-1.2.1 §5.8 field for field (F.1 A5.1 adds `reference_class` to `adjudication`).

`reviewer_assessment` (prefix `rva`, store Val, stage V3, identity class human):
| Field | Type | Null |
|---|---|---|
| `rva_id` | id (UUIDv7 form) | no |
| `annotator_id` | id | no |
| `namespace` | enum{reference, candidate_review, study_d6, pseudo_label} | no |
| `target_type` | enum{ref_event, system_episode, system_event} | no |
| `target_id` | id | no |
| `label` | enum{nm, ud, ct, not_hazardous, unsure} | no |
| `confidence` | f64 (no range constraint) | no |
| `rationale` | str | no |
| `blind` | bool | no |
| `shown_system_output` | bool | no |
| `submitted_utc` | ts (`datetime`, UTC) | no |

`adjudication` (prefix `adj`, V4, human): `adj_id`; `target_type` enum as above; `target_id`; `namespace`; `final_label` enum{nm, ud, ct, not_hazardous, unsure}; `tier` enum{tier1, tier2}; `method` **str (no enum in the contract)**; `assessment_ids` list<id>; `agreement_stat_ref?` str (nullable); `prov_class` enum{human_adjudicated}; `reference_class` enum{rule_conformance, independent_perceptual_geometric, independent_expert_judgment}.

`validation_status_log` (no prefix of its own; `status_id` is `sts_<uuid7>`, AR-36): `seq` i64; `status_id`; `target_type` str; `target_id`; `config_id` id (**non-nullable**); `status` enum{unreviewed, confirmed, rejected, disputed}; `layer` str; `namespace`; `basis_ids` list<id>; `actor_id` id; `created_utc` ts; `prev_hash` str; `record_hash` str.

`annotation_record` (prefix `anc`, V1): `annotator_id`; `window_id`; `layer` enum{A, B}; `namespace`; `label_source`; FM-X1 fields; `target_kind` enum{object_presence, interaction, geometry, coverage}; `payload`; `tool`; `submitted_utc`; `blind_to_system` bool. It is A/B-layer only. V-02 writes no `annotation_record`.

`annotator` (prefix `anr`, V1): `role` enum{a_layer, b_layer, c_layer_reviewer, adjudicator, study_participant}; `qualification_ref`; `independence_attestation` bool; `pseudonym`.

Validators: `validate.validate_row(table, row)` / `validate_rows(…, raise_fatal=True)` check types, enums, nullability, ID patterns and the UTC form. They do **not** check VR-E-053 for `reviewer_assessment`; that is `vr_rules.check_blind_reference` (point d).

Findings:
- No new field, table or enum value is needed for the screens as specified, **except** where the task asks for a `method` set {agreement, consensus_meeting, adjudicator}: the contract types `method` as free `str`, so these values would be written as strings without a schema change. They are the Owner's values in the V-02 text, not contract values, and they differ from the only related contract enum (`consensus_method` {agreement, third_annotator, adjudicated, simulator} on the reference tables). Whether they are the protocol's method values is part of D-44 (G5).
- `confidence` has a type and no scale or range (G4).
- Time-on-task: `reviewer_assessment` has no field for it. None is added. Raised as question Q1.

## b. Identity

- E-1.2.1 §0.1 (CN-6) and §2.1: human-entered records use the table prefix and a UUIDv7; pattern `^[a-z0-9]{2,4}_[0-9a-f-]{36}$` (§1.1). F.1 A1.2: annotator, annotation_record, reviewer_assessment, adjudication and status-log entries are "Human entry … UUIDv7 … assigned once".
- Implemented: `validate._ID` accepts both derived and UUIDv7 forms; `StatusLog.append` generates `sts_{uuid.uuid7()}`. There is no shared generator for other human prefixes; `uuid.uuid7` needs Python ≥ 3.14 (the Owner's `.venv` is 3.15.2; this session used 3.14.6 because the locked `hypothesis` wheel does not load on the 3.15 beta available here).
- Actor / annotator IDs: `reviewer_assessment.annotator_id` and `validation_status_log.actor_id` are `id` values; the contract's only rule is that annotators are pseudonymous (`annotator.pseudonym`, "pseudonym only") and that the validation summary carries no reviewer identities (§11 item 5). An `annotator` row (`anr_<uuid7>`) would be created for each fixture reviewer and its ID used for both fields.
- Reuse unchanged: yes. No conflict.

## c. Status log

- `StatusLog(path).append(target_type=, target_id=, config_id=, status=, layer=, namespace=, basis_ids=, actor_id=, created_utc=)` writes one JCS line with `seq`, `prev_hash` (64 zeros at genesis, AR-36) and `record_hash = SHA-256(JCS(entry without record_hash))`. `verify()` returns CT-E-24 issues. The class has no update or delete method; a correction is a new entry.
- Reuse unchanged: yes.
- Gaps: the contract gives the status enum but no rule that maps an adjudication to `confirmed`, `rejected` or `disputed` (G3), and `config_id` is non-nullable although a `ref_event` target has no system configuration (G6).

## d. Namespace and blindness guards

- VR-E-053 (Appendix T): "`reference` namespace records are blind (`blind_to_system = true`, `shown_system_output = false`)". E-1.2.1 §5.8: `shown_system_output` "false in reference".
- `vr_rules.check_blind_reference(table, rows)` reads `blind_to_system` or `blind`, so it applies to `reviewer_assessment` unchanged and refuses `shown_system_output = true` or `blind = false` in `reference`. This is the guard V-02 would call.
- `namespace.require_reference(record)` cannot be used for C-layer rows: it requires `label_source ∈ {simulator_truth, human_manual}` (VR-E-055), and `reviewer_assessment` has no `label_source` field, so it would refuse every assessment. Not a conflict for V-02 (VR-E-055 concerns A/B reference tables); noted so nobody wires it in.
- RV-01–RV-04 (F.1 A5.1): RV-02 `check_rv_02`, RV-03 in `fitness.py` (CV2 needs `independent_expert_judgment`), RV-04 in `report.py`. None is changed by V-02.
- **Gap G1.** `target_type` allows `system_episode` and `system_event` in any namespace. A reviewer assessing a system episode necessarily sees which interval and which person–forklift pair the system selected. Whether that counts as "shown system output" is not stated. Readings: (a) showing the target's interval and pair is allowed and `shown_system_output = false` as long as no system label, flag, measured value or other reviewer's assessment is shown; (b) any system-selected target is system output, so `system_*` targets can only be assessed with `blind = false`, `shown_system_output = true`, outside `reference`. The readings give different blind flags, and so decide whether these assessments can ever feed `independent_expert_judgment` (F.1 A5.1, RV-03, EV-M12).

## e. Targets

- `system_episode` → `episode` rows of an S5 artifact (`ep_<26>` derived IDs; natural key `pow_id start_frame`), built by `events/s5.py` `build` and, for N2 G1–G3, by the M0 pipeline (`pipeline/m0.py`).
- `system_event` → `candidate_event` rows of the same S5 artifact (`evt_<26>`; scenario + member episodes).
- `ref_event` → no table has this name. The reference event table is `ref_interaction` (`rin_<26>`, from `SimReferenceConverter.convert` on fixtures). Mapping `ref_event` to `ref_interaction` is a representation choice (an AR when V-02 resumes).
- Resolution to records: by ID lookup in the S5 artifact tables (`episode`, `candidate_event`, and through `pow_id` the `pow` and `pair_series` rows) or in the converter output (`ref_interaction`, `ref_coverage_label`). All read-only. In blind mode only time span, camera and recording would be shown (point d, G1).
- Fixtures available on this branch: N2 G1–G3 (`fixtures/records/N2-G*.json`), FX-RC-1–6, FX-ID-1–8. **FX-13 ("Two reviewers disagree — Tier 2 adjudication", Appendix T T1, status active; listed under WP-08 tests in Package F) has no fixture file and no test** on `m0-implementation`; it was not implemented in T-11. It is the only contract fixture for C-layer adjudication.

## f. Agreement

- `estimators.cohen_kappa(a, b)` = (p_o − p_e)/(1 − p_e), `None` if p_e = 1; `estimators.krippendorff_alpha_nominal(units)`, `None` if expected disagreement is 0. Both tested in `tests/evaluation/test_t13.py` (κ 0.4, α 0.6 hand values). Reusable unchanged for the panel.
- `agreement_stat_ref?` (nullable str): the contract does not say what it references (a `metric_result` row, a report section, a file). Per-target agreement is not a statistic; κ and α are computed over targets. Question Q2; until answered V-02 would leave it null, which the schema allows.

## g. Downstream consumers

| Consumer | Reads adjudications / status log? | Effect for V-02 |
|---|---|---|
| EV-M9, EV-M12 (F.1 Appendix N4) | Not implemented (`event_metrics.py` docstring: "computed with the evaluation store"; no code) | Nothing to round-trip against. EV-M12 ("κ between automated G2 label and adjudicated expert label, Tier 1 and Tier 2 separately") depends on G2, G3 and G7 |
| Matcher (`evaluation/matching.py`) | No; it matches system events to `ref_interaction` | None |
| Fitness engine (`evaluation/fitness.py`) | No; CV2 reads one expert-alignment `metric_result` with `reference_class = independent_expert_judgment` | None directly; G7 decides whether such a result could ever exist |
| OBX export (`export/obx.py`) | Yes: part `5_validation_summary` = `validation_status_log`, `adjudication`; `check_content` runs `validate_rows`, VR-E-034, VR-E-040, VR-E-041 | V-02's records would round-trip through `obx.serialize` / `obx.export` with no code change |

So V-02's outputs would feed the existing consumers unchanged, but the only existing consumer is the OBX export. Note for the Owner: §11 item 5 says the validation summary has "no reviewer identities", while OBX exports `validation_status_log.actor_id` (a pseudonymous ID). This is existing behaviour, outside V-02, and is noted only.

## h. D-23 and VIA

D-23: the Owner annotates real footage in VIA; a second person independently annotates a seeded 20–30 % subset before seeing the first labels; Safe and Unsafe Behaviours only. That is A/B-layer work (`annotation_record`, boxes and intervals). V-02 covers C-layer assessments (`reviewer_assessment`) and adjudication only, on fixtures only. No overlap in tables or data. V-02 does not create boxes, intervals or `annotation_record` rows.
Related gap: D-23's subset rule is for annotation, and nothing in the contract or the decisions says how many C-layer assessments a target needs before it can be adjudicated (G2).

## i. Wording rules

- `report.lint` (W1 collision, W2 near miss unless "candidate"/"no", W3 contact claims, W4 validated, W5 interaction counts, W6 scores/rankings) applies to reports. The codes `nm`, `ud`, `ct`, `not_hazardous`, `unsure` do not trip any rule, so the UI can show the codes, and the fixture banner.
- **Gap G8.** The contract defines `NM`, `UD`, `CT` only as automated rules over system quantities (E-1.2.1 §6: NM = (H ∨ PC) ∧ K = 1 ∧ contact = none_observed; UD … contact = undetermined; CT = contact = suspected). It gives no reviewer-facing definition, and none at all for `not_hazardous` and `unsure`. Showing the §6 formulas to a human reviewer is not a definition a reviewer can apply (K and the contact state are system states), and spelling out `nm` as "near miss" would break W2 if the same text reached a report. A reviewer instruction written by the agent would define the labels, which is outside the agent's authority. D-23's own recommendation noted that annotation "needs a written protocol … before anyone starts"; the same applies here.

## j. Real-data rules

- D-21: real footage for testing only. D-24 (b) SmartSpaces 026/027: no annotation or reference labels of any kind; (c) Safe and Unsafe Behaviours: academic, testing only, `conditional_on_selection`, no frames, crops or faces in git, reports or exports. D-26: exploratory, results "experimental". G-FQ / D-25: `rv2-real-provisional`. Access log (`registry/access_log.py` `AccessLog`, AR-54 item 5) for every access to real footage; VR-E-070 and `check_real_clip_access` for `evidence_clip` rows.
- V-02 as specified is fixture-only: no real data is read, no access log entry is needed, no `evidence_clip` is written. No conflict.
- Question Q4: using V-02 later on real footage would need an Owner decision (D-24 b forbids labels on SmartSpaces 026/027 outright; for Safe and Unsafe Behaviours, C-layer labels are "reference labels" in the sense of D-24 and would need the access log, `evidence_clip` with redaction state, and the D-26 "experimental" wording).

## Gaps (CR-027) — each one affects measurement meaning

| # | Gap | Why it affects meaning | Readings |
|---|---|---|---|
| G1 | Blindness when `target_type` is `system_episode` / `system_event` | Decides `blind` / `shown_system_output`, hence eligibility for `independent_expert_judgment` and EV-M12 | (a) target interval and pair may be shown, still blind; (b) system targets are never blind |
| G2 | Number of independent assessments required before adjudication | Decides which targets get an adjudicated label: the EV-M12 denominator | (a) exactly two (FX-13 "two reviewers"); (b) two only on a declared subset, one elsewhere (D-23-style); (c) two or more, α for > 2 |
| G3 | Which `validation_status_log.status` an adjudication writes | `status` is reported (§11 item 5, "current status") and "reviewer-confirmed" wording depends on it (§6.0) | e.g. (a) `confirmed` if the final label is the same label group as the system label, `rejected` if not, `disputed` if tier2 or `unsure`; (b) status only for system targets; (c) another rule |
| G4 | Scale and range of `confidence` | A stored human value whose numbers differ by reading | (a) probability in [0, 1]; (b) ordinal scale (e.g. 1–5); (c) free |
| G5 | `adjudication.method` values | Method determines which disagreements are resolved how; the contract has only free `str` | (a) Owner's {agreement, consensus_meeting, adjudicator}; (b) reuse `consensus_method` values |
| G6 | `config_id` of a status-log entry for a `ref_event` target (non-nullable) | Status is per configuration; a reference has none | (a) the evaluation configuration being reviewed; (b) one status entry per system configuration; (c) a fixed "reference" configuration record |
| G7 | `reference_class` of a C-layer adjudication, and the tier rule | RV-03 / FT-05 (CV2) and EV-M12's Tier 1 / Tier 2 split | Tier: (a) tier1 iff all assessments agree, else tier2 (FX-13 gives only "disagree → Tier 2"); `unsure` agreed by both? Class: (a) `independent_expert_judgment` iff every assessment is blind and every reviewer has `independence_attestation = true`; otherwise no class fits |
| G8 | Reviewer-facing definitions of nm, ud, ct, not_hazardous, unsure | Defines the labels the reviewers assign | Needs a written C-layer protocol (Owner / Architect), not agent text |

Questions that do not block on their own: **Q1** time-on-task (no field in `reviewer_assessment`; add none unless the contract adds one); **Q2** what `agreement_stat_ref` points to (null until decided); **Q3** FX-13 is active but has no fixture or test (should it be built as part of the decision, with its expected values supplied by the Architect?); **Q4** V-02 on real data (point j).

## What can be reused when V-02 resumes (no reimplementation)

`schema.validate.validate_rows` (all records); `schema.vr_rules.check_blind_reference` (VR-E-053 refusal); `validation.status_log.StatusLog.append` / `.verify`; `evaluation.estimators.cohen_kappa` / `krippendorff_alpha_nominal`; `export.obx.check_content` / `serialize` (round trip); `export.report.lint` and the banner idea of `report.BANNER` (V-02's own banner text is the Owner's: "Fixture data. Review records are not research labels."); S5 artifacts from `pipeline/m0.py` and references from `validation.converter.SimReferenceConverter` (read only). Nothing from S5 or S8 run entry points would be imported.

## Outcome

Conflict and gaps found → CR-027 opened in `docs/CHANGE_REQUESTS.md`, decision request D-44 in `DECISIONS_NEEDED.md`, V-02 marked STOP in `WORKPLAN.md`. No UI code, tests or records written; no schema, enum, ID rule, guard or analysis function touched; `docs/preregistration_FROZEN.md` untouched.
