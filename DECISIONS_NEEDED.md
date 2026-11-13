# Decisions needed from the Research Owner

Open requests use the template in `WORKPLAN.md` section 6. The Owner writes the decision under each entry.

## D-1 (2026-11-09) — Text of rule, test and fixture IDs is missing from the contract        status: CLOSED
Task: T-01   Blocking: T-01 (remainder), T-02 to T-06, T-08 to T-16
Question: The contract lists 34 active validation rules and most contract tests by ID only. For example, 26 of the 34 VR-E rules have no text, and the seven-row payload needed to reproduce the identity reference values is absent. How should the missing text be supplied?
Options: (a) The Research Architect consolidates the missing text into a normative appendix (E-1.2.3). (b) The Owner adds Package E, E.1, the E.1 Final Errata and the Pre-Implementation Clarification to the CLAUDE.md document list, as normative only for the text of IDs that E-1.2.2 cites, with E-1.2.2 winning any conflict.
Agent's recommendation: (b), because it unblocks work immediately and the agent can log every ID taken from those files for later audit. If the Architect prefers (a), the list in CR-001 is the scope. CR-001 is in `docs/CHANGE_REQUESTS.md` on the Owner's computer.
Owner decision: Resolved by Appendix T (E-1.2.3)

## D-2 (2026-11-09) — Progress records are git-ignored and do not reach GitHub        status: CLOSED
Task: S-02   Blocking: nothing yet; affects the independent review at G-M0
Question: `.gitignore` excludes `WORKPLAN.md`, `CLAUDE.md` and `docs/`, and the repository is public. The progress log, change requests and environment record therefore exist only on this computer, although the work loop expects them to be pushed with each task. Should they be pushed?
Options: (a) Keep them local. The agent commits only code, and the Owner shares the logs separately for review. (b) Make the repository private, then remove those ignore lines so everything is pushed. (c) Keep the repository public and track only progress files, moving them out of `docs/`.
Agent's recommendation: (b), if the contract and plan documents are not meant to be public. The agent has made no change and will not publish these documents without a decision.
Owner decision (11 Nov 2026): DECIDED. docs/ is no longer git-ignored; WORKPLAN.md, CLAUDE.md and docs/ are tracked.

## D-3 (2026-11-09) — Planned dataset download is larger than the approval text says        status: CLOSED
Task: T-07 finding, for T-17   Blocking: nothing now; needed before the WORKPLAN section 0 download approval
Question: Section 0 describes the download as about 1.5 GB. SDG-Warehouse publishes only tar shards of about 5 GB each, so the smallest whole-shard sample with annotations is about 4.6 GiB. The SmartSpaces 2026 edition is about 50 GB without depth maps. What download limit does the Owner approve?
Options: (a) One SDG near-miss artifacts shard, plus selected SmartSpaces synthetic scenes, with a total cap set by the Owner. (b) Keep about 1.5 GB, which would require reading individual files from inside remote shards; this route is untested.
Agent's recommendation: (a), with a 20 GB cap. Real-world scenes `Warehouse_026` and `Warehouse_027` would be excluded in either case.
Owner decision (9 Nov 2026): APPROVED. Cap of 22 GB in total, outside git: one SDG-Warehouse near-miss shard plus selected synthetic SmartSpaces scenes. Real-world scenes (Warehouse_026, Warehouse_027 and any other real footage) are excluded. WORKPLAN section 0 timing still applies: download only after M0 is accepted and only after T-17 records source authenticity and licence terms.

## D-4 (2026-11-10) — How the nominal frame interval and f_sub are defined        status: CLOSED
Task: T-06   Blocking: T-06, T-08 to T-16
Question: The contract uses the nominal frame interval (delta_nom) for capping and for the final frame, but never says how to obtain it. The only earlier wording, "median of the video", gives 0.084 s for Case B where Appendix N3 requires 0.067 s. Separately, f_sub has a test value but no stated effect. How should each be defined?
Options for delta_nom: (a) Median of timed intervals, and change the N3 Case B and C values. (b) A value declared in the decode configuration when known, otherwise the median of timed intervals, with fixtures declaring 0.033 s.
Options for f_sub: (c) Above f_sub, only segments containing substituted frames become usable_degraded with reason timing_substituted. (d) Above f_sub, every usable segment of the recording becomes usable_degraded.
Agent's recommendation: (b) and (c). Option (b) keeps every Appendix N3 value unchanged, and (c) avoids downgrading good footage in the same recording. Details are in CR-003, in `docs/CHANGE_REQUESTS.md` on the Owner's computer.
Owner decision (11 Nov 2026): APPROVED as contract amendment E-1.2.4, recorded as Appendix T section T7.

## D-5 (2026-11-11) — Should a changed retrieval time change a dataset's ID?        status: CLOSED
Task: AR-7 review   Blocking: nothing
Question: The Architect review of AR-7 asks that changing a supplied `retrieved_utc` change the `dataset_source` ID. Contract F.1 A1.2 computes that ID from the dataset name and version only. Under it, a changed retrieval time keeps the ID, changes the S0 artifact ID, and is reported as an anchor conflict, so a re-retrieval must register a new version. Which rule applies?
Options: (a) Keep F.1 A1.2, which is current behaviour. (b) Amend F.1 so that `retrieved_utc` is part of the dataset natural key.
Agent's recommendation: (a). Details are in CR-004.
Owner decision (12 Nov 2026): DECIDED (a). Keep F.1 A1.2: the dataset_source anchor ID is (name, version). A changed retrieved_utc changes the S0 artifact ID and raises ERR-ANCHOR-CONFLICT for the same anchor, so re-retrieval with different provenance must use a new version label. Identical bytes need no re-registration.

## D-6 (2026-11-11) — Seven substrate quantities have names but no definitions        status: CLOSED
Task: T-08   Blocking: T-08 (part B), T-09, T-12 to T-16
Question: The contract names seven measurement quantities without saying how to compute them: POW gap bridging, smoothed speed and heading, closing rate and time to closest approach, clearance uncertainty, signed image box gap, the evidence-sufficiency flag Q, and evidence state. Each affects flags, durations or labels. Do you approve the definitions proposed in CR-005, or will you supply others?
Options: (a) Approve the CR-005 proposals as an amendment, with item 4 as "σ not estimated until GV-05 evidence". (b) The Architect supplies definitions. (c) Approve some items and return others.
Agent's recommendation: (a). The proposals follow the existing wording of Packages B and E.1 where any exists. Item 4's interim choice uses the contract's own null-σ rule rather than inventing a formula. Details are in CR-005.
Owner decision (12 Nov 2026): DECIDED (b). The Architect supplied the definitions as Appendix T section T8 (contract E-1.2.6).

## D-7 (2026-11-11) — How a timeline's final, shorter window is handled        status: CLOSED
Task: T-10   Blocking: sampling of any timeline whose length is not a multiple of w_ref (T-10 fixtures avoid this)
Question: The contract tiles each timeline with windows of length w_ref, but never says what happens to the shorter remainder at the end. This changes the sampling frame. For example, a 10 s SDG run with 30 s windows would contribute no windows under option (a).
Options: (a) Complete windows only, with the remainder outside the frame. (b) A final, shorter window whose length is recorded, with the guard clipped at the end. (c) Require w_ref to divide every timeline length.
Agent's recommendation: (b). Details are in CR-006.
Owner decision (12 Nov 2026): DECIDED (b). The last window of a timeline may be shorter. window_length_s is recorded on reference_window; the guard is clipped at the timeline end; weights stay 1/π.

## D-8 (2026-11-12) — Where the forklift footprint sits relative to the tracked point        status: DEFERRED (to T-22)
Task: T-08 (not blocking M0)   Blocking: the camera-based detector path (T-22, T-23, M1b)
Question: Footprint priors declare an anchor (box_bottom_centre, rear_axle or centre), but the contract does not say how a camera-derived floor point maps to the footprint centre for the first two. This shifts clearance. M0 uses oracle centre positions, so it is unaffected.
Options: (a) The proposal in CR-007: box_bottom_centre is treated as the centre, and rear_axle uses a declared rear overhang along yaw. (b) The Architect supplies another rule.
Agent's recommendation: (a). Details are in CR-007.
Owner decision (12 Nov 2026): DEFERRED to T-22. Reopen it with GV-03/GV-04 evidence. Until then the oracle and simulator path uses the simulator footprint centre. Kept open as deferred.

## D-9 (2026-11-12) — Event-engine definitions missing from §6        status: CLOSED
Task: T-09   Blocking: T-09 part B (S5 from the pipeline), T-12 to T-16
Question: Eight event-engine inputs are named but not defined. These include evasive-action rates, the contact cue's units, the value of E when R5 is off, the closest-approach frame, and "usable frames around closest approach". There is also a conflict between Appendix N2's per-frame flags and T8.2 at track ends. Each one changes E, K, contact state or labels. Do you approve the CR-008 proposals?
Options: (a) Approve the CR-008 proposals. (b) The Architect supplies definitions. (c) Approve some items and return others.
Agent's recommendation: (a), or the Architect's text for items 3 and 4, which matter most. Details are in CR-008.
Owner decision (12 Nov 2026): DECIDED. The Architect's definitions are Appendix T section T9 (contract E-1.2.7), appended verbatim. CR-008 closed as superseded by T9. T9 corrects T8.2 (T9.1) and Appendix N1 row T10 (T9.9); these are Architect amendments, not edited expected values, and the affected tests cite T9.

## D-10 (2026-11-12) — T9 edge readings and the episode exposure fields        status: CLOSED
Task: T-09   Blocking: the S5 artifact (episode rows) and per-label event counts; T-14 and T-15 when they read episode exposure
Question: (1) Four T9 passages have two readings that give different numbers in cases no Appendix N fixture covers: the closing-rate window, R5 on frames where a track is lost, the contact cue when R5 is off, and which frames set borderline flags. The agent implemented the first reading of each, provisionally. (2) The episode exposure fields (`exp_*`), `support_detected_frac` and per-label event counts are named in §5.6 but not defined, so episode rows cannot be written.
Options: (a) Approve the implemented readings (CR-009 part 1) and the proposed definitions (part 2, items 5a–5f and 6). (b) The Architect supplies other text. (c) Approve some items and return others.
Agent's recommendation: (a). Part 2 reuses the S4 exposure-profile definitions and lifecycle step 4. Details are in CR-009.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T10 (E-1.2.8).

## D-11 (2026-11-12) — Abstention and coverage in the event metrics        status: CLOSED
Task: T-12   Blocking: nothing in M0 fixtures; the EV-M values reported at T-16 and M1a
Question: Appendix N4 does not settle four details of the event metrics: which events count as "abstained (IE-only)", how cᵢ (references receiving a non-abstained decision) is counted, the P90 definition in EV-M8, and whether EV-M5 and EV-M11 are weighted. Each changes reported numbers. The agent implemented one reading of each, provisionally.
Options: (a) Approve the implemented readings in CR-010. (b) The Architect supplies other text. (c) Approve some items and return others.
Agent's recommendation: (a). Item 1 is the only reading under which "IE-only" can occur, given CL-INV-02. Details are in CR-010.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T10 (E-1.2.8).

## D-12 (2026-11-12) — Borderline flags in configurations whose provider is not enabled        status: CLOSED
Task: T-09   Blocking: nothing (borderline flags never change labels or review routing)
Question: T10.4 sets `clearance_within_k_sigma` and `speed_near_v_min` from `d_p`, `v_min` and `d_pc` in every configuration, but those are parameters of R2 and R3. Should an R1-only configuration, or one without R3, still evaluate those bullets?
Options: (a) Yes, literally as T10.4 is written (implemented). (b) Only when the provider that owns the threshold is enabled.
Agent's recommendation: the Architect's call. Details are in CR-011.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T11 (E-1.2.9).

## D-13 (2026-11-12) — Parameters used outside the provider that owns them        status: CLOSED
Task: T-09 (T11 conformance)   Blocking: nothing in M0 fixtures; the rule_configuration record shape before G-PR
Question: T11.1 says a disabled provider's parameters play no role in S5 output. But `v_min` (R2) is also read by R5's turn criterion (T9.2), and `w_e` (R5) is also read by the contact cue and W_CA, which apply whether or not R5 is enabled (T9.6, T10.3(c)). Where do these two parameters belong?
Options: (a) Shared classification parameters, recorded outside the provider entries. (b) Separate parameters per use. (c) Amend T11.1 to name the exception.
Agent's recommendation: (a). Details are in CR-012.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T12 (E-1.2.10).

## D-14 (2026-11-12) — System events on unobservable references (EV-M10)        status: CLOSED
Task: T-14   Blocking: EV-M10; possibly EV-M2 and EV-M7 values
Question: A system event that falls on a reference marked unobservable is currently a `false_alert` (N4 literal, per the AR-39 item 6 ruling). Should it count against precision and false-alert burden, or only in EV-M10? And what does "on" mean?
Options: (a) Keep it a false alert and also count it in EV-M10. (b) Exclude it from EV-M2/EV-M7 and record it as `unobservable_reference` with the system event set. (c) A new match class (not to be added now).
Agent's recommendation: (b), "on" = temporal IoU > 0 with the same pair. Details are in CR-013.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T12 (E-1.2.10).

## D-15 (2026-11-12) — The oracle-factorial attribution rule lives only in a methodology document        status: CLOSED
Task: T-14   Blocking: CT-E-22 (FX-16) and every `verified_*` attribution
Question: Appendix N9 says oracle substitution assigns `verified_*` "as specified in D.1 §7.2", but CLAUDE.md forbids implementing from docs/methodology. May the agent implement the quoted D.1 §7.2 rule, and what happens when nothing resolves the error or two smallest sets tie? Separately, N9's "tests conflict" is undefined.
Options: (a) Confirm D.1 §7.2 as quoted in CR-014 is normative through N9, plus the two missing cases. (b) The Architect restates the rule in Appendix T. For "conflict": define it, or delete the clause.
Agent's recommendation: (a), with no resolving set → unresolved and ties → earliest stage; delete "or tests conflict". Details are in CR-014.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T12 (E-1.2.10).

## D-16 (2026-11-12) — Open details of completeness metrics CM-05 to CM-08 and CM-10        status: CLOSED
Task: T-14   Blocking: CM-05, CM-06, CM-07, CM-08, CM-10 (M1a reporting); not M0 "Done when"
Question: N6 leaves the support basis of system-side denominators, the CM-06 unit, the CM-10 treatment of frames with no POW, and aggregation open. CM-07 is defined differently in F.1 A5.2 (tracks per identity) and N6 (POWs per pair).
Options: see CR-015 (readings a/b per item).
Agent's recommendation: 1(a), 2(a), 3(c) both as strata, 4(a), 5 both per-unit and pooled.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T12 (E-1.2.10).

## D-17 (2026-11-12) — Gaps in the fitness status rule        status: CLOSED
Task: T-14   Blocking: nothing in M0; status decisions at M1a
Question: Section 9.6 gives no status when the only not_met criteria are repeatability or robustness and nothing is met or inconclusive. It also does not say whether staged real footage counts as "real data", or what "comparability is characterized" requires.
Options: see CR-016 (the stricter readings are implemented; case 1 is refused).
Agent's recommendation: case 1 → experimental; real data = real_natural only; characterized = a comparability criterion with a decision other than not_assessable.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T12 (E-1.2.10).

## D-18 (2026-11-12) — Does the support basis apply to CM-10?        status: CLOSED
Task: T-14   Blocking: nothing
Question: T12.4 applies the support basis to all completeness support, but CM-10 counts insufficient pair-frames, which neither basis contains. Applied literally, CM-10 is always zero. Should CM-10 be the same on both bases?
Options: (a) Yes, same on both bases (implemented). (b) Literal basis filter (CM-10 identically zero).
Agent's recommendation: (a). Details are in CR-017.
Owner decision (12 Nov 2026): DECIDED. Decided: Architect definitions, Appendix T section T13 (E-1.2.11).

## D-19 (2026-11-12) — G-M0: review of milestone M0        status: CLOSED
Task: G-M0   Blocking: T-17 onward (M1a)
Question: M0 is complete and tagged `m0-verified`. Do you accept M0?
Evidence: reports/M0_report.md (test matrix, artifact-ID table and determinism result from a clean clone, status board, expected-value audit, self-audit, open CRs, the 47 ARs with their review status).
Options: (a) Write "M0 accepted" here. (b) Return items for rework.
Agent's recommendation: an independent review by the Research Architect first, including the 27 ARs still pending review (AR-1 to AR-6, AR-8 to AR-21, AR-23, AR-24, AR-26, AR-29, AR-32, AR-33, AR-47).
Owner decision (12 Nov 2026): M0 ACCEPTED. The Architect reviewed the milestone report and AR-1 to AR-47 as written and accepted all pending ARs. Conditions: (1) M0_report.md names e6072ef as the commit its artifact-ID table belongs to; (2) M1a reports tie each result to its code commit; (3) "reference visibility assumed" wording is kept wherever visibility truth is missing; (4) D-8 stays deferred to T-22.

## D-20 (2026-11-12) — Leakage "same scene" for synthetic runs        status: CLOSED
Owner decision (12 Nov 2026): DECIDED (B). A leakage "scene" is the rendered scene instance: a run, or a scene plus its re-renders. A shared layout family is recorded as `shared_scene_content`, with no leakage edge. Claims are limited to held-out runs of the same synthetic layout. The Architect will supply the Appendix T text (E-1.2.12). **No split is frozen until E-1.2.12 is committed.**
Update (12 Nov 2026): the Architect's text was committed as Appendix T section T14 (E-1.2.12). The Owner added: no split is frozen until the SDG download is complete and verified.

## D-21 (2026-11-12) — Download cap and real-world footage (amends D-3)        status: CLOSED
Owner decision (12 Nov 2026): DECIDED. Cap raised to 30 GB in total. Real-world footage is permitted **for testing only** (no training or fine-tuning). Recorded in WORKPLAN §0. Note for the Owner: CLAUDE.md "Never" still says "Use real worker footage" without the D-21 exception. The agent has not edited CLAUDE.md and asks the Owner to amend that line (see D-24 item 6). Until then the agent reads D-21 as the governing exception, limited to testing.

## D-22 (2026-11-12) — SmartSpaces pallet trucks        status: CLOSED
Owner decision (12 Nov 2026): DECIDED. Pallet trucks are excluded from the E1 pair class for now. They are recorded as present, not evaluated. Planned future extension.

## D-23 (2026-11-12) — Reference annotation of real footage        status: CLOSED
Task: T-17 Part 3, T-18 onward   Blocking: every evaluation on real-origin data (no real-data evaluation until decided)
Question: Who produces the reference annotation for real footage, who reviews it as the second reviewer, and with what tool?
Facts: (1) Neither real source has E1 reference annotation. SmartSpaces `Warehouse_026/027` ship videos and calibration only. The Safe and Unsafe Behaviours labels are clip-level behaviour classes, not pair intervals or positions. (2) The SmartSpaces Croissant metadata says "manual labeling of the test set by participants is prohibited by the challenge rules" for the real-world target (qualification Part 3, 3.2). (3) Faces are visible in both sources, so annotators see identifiable people; the approvals (`approvals_ref`) must cover them. (4) Reference independence: annotators must not see system output (F.1 A5.1, `reference_class`).
Options:
- Who: (a) the Owner annotates and a second person independently annotates a declared subset (agreement reported with κ / ICC as in T-13); (b) two independent annotators on everything, with Owner adjudication; (c) no real annotation now: real footage is used only for decode, timing and frame-quality checks until resources exist.
- Tool: (d) VGG Image Annotator (VIA 3, one offline HTML file; nothing leaves the computer; a small download that needs approval); (e) CVAT self-hosted (needs Docker, a system install, not pre-approved); (f) a minimal annotation exporter built in this repository (no install; more agent work).
- SmartSpaces real scenes: (g) annotate despite the challenge statement (RQ1 is not a participant); (h) do not annotate them, and use them only for unannotated checks; (i) exclude them.
Agent's recommendation: (a) + (d) + (h). Annotation needs a written protocol (E1 interval and pair definitions taken from the contract, nothing new) before anyone starts. The agent will draft the protocol when this is decided.
Owner decision (12 Nov 2026): DECIDED. The Owner annotates. A second person independently annotates a declared, seeded subset (target 20–30 % of clips) before seeing the first annotator's labels. Tool: VIA (offline). Annotation applies to Safe and Unsafe Behaviours only. The subset is declared in `qualification.md` Part 3 (3.9).

## D-24 (2026-11-12) — STOP: approve the Part 3 download selection        status: CLOSED
Task: T-17 Part 3   Blocking: all Part 3 downloads; T-18 work on the new sources (T-18 on already-held data is independent)
Question: Do you approve the selection in `research/datasets/qualification.md` Part 3, total 25.9 GB of the 30 GB cap?
Selection: SmartSpaces `Warehouse_026` + `027` (15 files, 0.29 GB); Safe and Unsafe Behaviours v1, 4 classes (371 files, 5.77 GB, from Mendeley, SHA-256 checked); SDG artifacts shards `00336` + `00243` (6 runs, 9.66 GB; seeded draw, seed 2026111203, 10-camera runs only); 0.5 GB reserve.
Items needing your answer:
1. Approve the selection as listed, or amend it.
2. SDG eligibility: every run has 10 cameras (proposed), or ≥ 2 cameras.
3. SDG member-level option: range-read only RGB and annotations, about 70 runs instead of 6, but no published per-file hash (Part 3, 3.1). Default: no.
4. SmartSpaces real scenes and the Croissant "evaluation-only, no manual labelling" statement: download for unannotated checks (proposed), or skip.
5. Confirm the labels: SmartSpaces real `real_staged` / `staged_facility`; Safe and Unsafe Behaviours `real_natural` / `operational_facility`, production facility, not warehouse.
6. VR-E-070 values: `approvals_ref`, `retain_days`, `legal_basis_ref` for `rp_real_test_v1` (Part 3, 3.5). Real footage is downloaded but **not processed** until these exist and G-FQ (D-25) is approved. Please also amend the CLAUDE.md "Never … real worker footage" line to state the D-21 testing-only exception.
Deviation to note: the artifacts-shard mapping could not come from `runs.parquet` / `clips.parquet` alone (they index RGB shards only). The agent fetched `manifest_nearmiss_artifacts.json` (3.3 MB) and read one 512-byte header per shard (Part 3, 3.1).
Correction to note: Part 2 said 1,640 multi-camera near-miss runs (74 with fewer than 10 cameras). The index says 1,642 (76). Corrected in place, with a note.
Agent's recommendation: approve items 1 to 5 as proposed, with item 3 = no.
Owner decision (12 Nov 2026): APPROVED with changes.
 a. SDG: download only the RGB video and annotation members of each selected artifacts shard (the ~70-run option), by byte-range reads of the LFS tar. Record the agent's own SHA-256 per extracted file at download, and the byte ranges and tar header data used; integrity label "self_hashed_unverified_by_publisher". Multi-camera runs only; seeded, pre-declared draw recorded in Part 3 BEFORE download.
 b. SmartSpaces Warehouse_026/027: download. NO annotation and NO reference labels of any kind (the dataset states evaluation-only and prohibits manual labelling). Reference-free checks only: decode/timing, frame quality, detector output rates, track continuity. Never compute accuracy metrics on them.
 c. Safe and Unsafe Behaviours: download from Mendeley v1 (the 4 classes, 371 clips). Testing only, academic use only. data_origin = real_natural. Clips were curator-selected by behaviour: any result has estimand = conditional_on_selection, with no frequency, duration or per-hour aggregates. No frames, crops, faces or company name in git, reports or exports.
 d. VR-E-070 fields (approvals_ref, retention, legal basis): BLOCKING placeholders; the Owner will supply them. No processing of real footage until they are filled AND D-25 is approved. Downloading is allowed.
 Item 1 (index file and 512-byte shard headers): accepted as metadata-only inspection. Item 5 (1,642 / 76 correction): accepted.

## D-25 (2026-11-12) — G-FQ: frame-quality rules version `rv2` for real footage        status: PROVISIONAL (applied as `rv2-provisional` under D-26; Architect review pending)
Task: G-FQ (AR-27 review)   Blocking: any decoding or processing of real footage
Question: Which frame-quality rules version applies to real footage? `rv1` excludes `decode_error` only (AR-27). It must not be used on real footage.
Why it matters: an excluded frame becomes ineligible (E-1.2.1 §3.2 step 4). Its support then leaves every duration, and its coverage segment becomes `unusable`. The rules version therefore changes measured values, so it is the Architect's and the Owner's choice. Thresholds below are proposals.
Proposed `rv2` (computed per decoded frame on the 8-bit luma plane, integer arithmetic, recorded in `frame.quality_flags`):
| Flag | Proposed rule | Excluding in rv2 |
|---|---|---|
| `decode_error` | as rv1 | yes |
| `black` | 99th percentile of luma ≤ 32 | yes |
| `overexposed` | ≥ 50 % of pixels with luma ≥ 250 | yes |
| `frozen` | luma byte-identical to the previous decoded frame, inside a run of identical frames lasting ≥ 0.5 s; every frame after the first in the run is flagged | yes |
| `blurred` | not computed in rv2: no scene-independent threshold exists, and blur already acts through perception quality | — |
| `compression_damage` | not computed in rv2 (undecodable frames are `decode_error`) | — |
Before use: (1) run rv2 on all 68 held synthetic recordings and report flag counts per recording (expected 0; any flag is a false positive to explain); (2) on real footage, report flag counts per recording only. No frames are stored or shown. rv1 stays for the M0 fixtures, and their expected values are unchanged.
Options: (a) approve rv2 as proposed; (b) approve with other thresholds; (c) add `blurred` with a stated threshold.
Agent's recommendation: (a). The `frozen` rule needs the synthetic check first, because H.264 can produce byte-identical frames in static scenes. The 0.5 s run length is there to limit that.
Implemented as `rv2-provisional` (12 Nov 2026, D-26), exactly as follows, for the Architect's review (`src/rq1/decode/quality.py`, `tests/decode/test_rv2_provisional.py`):
- Luma = the decoder's 8-bit Y plane with no range conversion (limited-range black is about 16).
- P99 = nearest rank: the ceil(0.99·n)-th smallest value; black iff P99 ≤ 32.
- Overexposed iff 2 × (pixels with Y ≥ 250) ≥ n.
- Frozen: consecutive timed, decoded frames in presentation order with byte-identical Y (compared by SHA-256), in a run whose span t(last) − t(first) ≥ 0.5 s. Every frame after the first is flagged. Duplicate-timestamp frames take no part.
- Flags are sorted. Excluded frames give `excluded_own_support` and an `unusable` coverage piece with reasons `excluded_frame` plus the flags.
- Only statistics are kept, never pixels. rv1 decodes no pixels and is unchanged.
Architect review: ______   Owner decision (12 Nov 2026): awaiting Architect review; do not apply. rv1 stays in force; no real footage is processed.

## D-26 (2026-11-12) — VR-E-070 values for real footage        status: DECIDED (exploratory); values PENDING advisor
Task: any processing of real footage   Blocking: decoding, frame quality, detection and tracking on `data/raw/real/` (downloading is allowed, D-24 d)
Question: Please supply, for retention policy `rp_real_test_v1` and both real sites: `approvals_ref` = ______; `retain_days` = ______; `legal_basis_ref` = ______.
Placeholders are stored as `BLOCKING_OWNER_TO_SUPPLY`. An adapter that meets that value refuses to register a real-origin source file (VR-E-070).
Owner decision (12 Nov 2026): exploratory mode for real footage. This phase is exploratory, not a publication; the advisor will be consulted along the way.
1. VR-E-070 values (PENDING, to re-decide with the advisor; they no longer block processing): approvals_ref = "PENDING-ADVISOR (exploratory, D-26)"; retention (`rp_real_test_v1`, retain_days null, label) = "until end of exploratory phase; re-decide with advisor"; legal_basis_ref = "dataset licence + publisher consent/academic-use statement".
2. G-FQ: rv2 applied now as a PROVISIONAL rules version, version label `rv2-provisional`. Every real-data artifact and report carries "exploratory; frame-quality rules provisional". The Architect reviews rv2 later; if it changes, everything is re-run.
3. Still binding (dataset terms): SmartSpaces 026/027 no annotation or reference labels, reference-free checks only; Safe and Unsafe Behaviours academic use only, conditional_on_selection, no per-hour aggregates; no frames, crops, faces or company names in git, reports or exports; no training or fine-tuning on real footage.
4. Real-data results are reported as "experimental", never technically_validated.
   Agent note: T12.5 as written lets real_natural and real_staged reach technically_validated; only synthetic data cannot. D-26 item 4 is therefore a new restriction, not existing behaviour. It is applied without a contract change, by the §9.6 downgrade-only override: every real-origin measurement_fitness record carries override {downgrade_only, rationale "D-26 exploratory phase", actor Owner} → experimental. If the Owner wants this as a contract rule instead, it needs Appendix T text.
5. Proceed: D-24 downloads, E-1.2.12 (done, 9b35b9f), T-18, T-19 (T-19 is BLOCKED on CR-018 / D-27: R4 and BL-1 to BL-6 are not defined in the contract).

## D-27 (2026-11-12) — R4 (TTC/PET) and BL-1 to BL-6 definitions        status: OPEN
Task: T-19   Blocking: T-19; T-20 (configurations in the pre-registration)
Question: The contract names R4 and BL-1 to BL-6 but defines neither computably. The BL table exists only in Package D (methodology). Which TTC and PET definitions, which Unknown rule, and which provider set for each BL?
Options: see CR-018 (readings a/b/c per item).
Agent's recommendation: TTC and PET from the R3 constant-velocity footprint prediction within τ; Unknown also without velocity; BL-1 deferred to M1b; BL-2 to BL-6 as listed in CR-018, as Appendix T text.
Owner decision: ______
