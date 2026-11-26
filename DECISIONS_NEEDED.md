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
Evidence added 14 Nov 2026 (Architect ruling A, from CR-023 / D-32), for the T-22 decision: the T8.2 heading fallback is about 77° off the forklift's body axis during SDG pivot turns (median 77.5° on 7,860 turning frames; within 10.5° on all 8,647 straight frames). Details in CR-007.
Evidence added 17 Nov 2026 (G-M1a, D-40 item 7): on SDG validation the full_camera forklift position error has median 1.12 m (ceiling) and 0.99 m (eye level), P99 about 1.5 m, and no outliers (no tracked forklift above 10 m; `research/m1a/position_diagnosis_sdg.json`). This is consistent with the bottom-centre foot point lying at the near edge of the footprint rather than at its centre (forklift box 3.03 × 1.13 m). Input for the T-22 decision.

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

## D-25 (2026-11-12) — G-FQ: frame-quality rules version `rv2` for real footage        status: DECIDED (`rv2` for synthetic M1a, S_flat = 2); real footage `rv2-real-provisional`, dark-frame spread report pending
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
Step (1) result (12 Nov 2026, `research/datasets/part3/rv2_synthetic_check.json`): `rv2-provisional` on the 68 synthetic recordings held when D-25 was written (30 SDG sample videos, 9,000 frames; 38 SmartSpaces synthetic Warehouse_001 videos, 342,000 frames). **0 flags on every recording; 351,000 / 351,000 frames eligible.** Luma P99 ranged 62–235, far from both thresholds (black ≤ 32; overexposed needs half the pixels ≥ 250). No frozen run was found. The 690 SDG member videos downloaded later were checked the same way (`rv2_synthetic_check_members.json`): **not 0.** 57 of 690 recordings (41 of 69 runs) carry flags; 202,639 / 207,000 frames are eligible; 4,361 `black`, 40 `frozen`, 0 `overexposed`. Patterns (agent inspection of a few synthetic frames, not stored):
  - Whole-video `black`, 13 recordings in 2 runs (`…run_43_seed_631373023`, `…run_6_seed_1833142794`; 3,899 frames). Very dark red-lit scenes: worker and forklift are visible when the frame is brightened. Under the D-25 intent (a frame with no usable content) these are **false positives** of the P99 ≤ 32 threshold.
  - Partial `black`, 44 recordings, 462 frames (1–136 per recording), mostly `eye_01` (39 of 57). Some are dim but readable frames (false positives); some are fully black even when brightened ×6 (e.g. `…run_18…eye_00`, frames 21–102, consistent with an eye-level camera occluded by a passing object: **true positives**).
  - All 40 `frozen` frames lie inside black stretches (identical all-black frames); none is frozen and not black.
  Question for the Architect's review: the `black` threshold treats very dark but content-bearing frames as excluded. Options include a lower P99 threshold, or keeping 32 and recording these synthetic runs as low-light conditions. The agent changes nothing: `rv2-provisional` stays as written, and synthetic evaluation stays on `rv1` unless a configuration says otherwise.
Architect review (13 Nov 2026; Owner approval by forwarding it):
1. `black` becomes a no-content rule: black iff P99(Y) ≤ 32 AND (P99(Y) − P1(Y)) ≤ S_flat, P1 and P99 by the same nearest-rank method. S_flat is set from the spread of the frames now flagged black: (a) report the distribution for (i) the two red-lit runs, (ii) frames already judged truly blank, (iii) all others; (b) if (i) and (ii) separate cleanly, set S_flat to a round value in the gap and re-run all 758 synthetic recordings; (c) if not, change nothing and report back.
2. Recordings with median frame P99 ≤ 32 that the new rule does not flag get the condition tag `low_light` (robustness stratum, not an exclusion).
3. `frozen` and `overexposed` accepted as written; `blurred` not computed (accepted).
4. Once (1b) succeeds: rename to `rv2`, apply it to all M1a recordings, synthetic and real. rv1 stays for the M0 fixtures; their expected values are unchanged. Real-data reports still carry "exploratory" (D-26).
5. D-26 item 4: the downgrade-only override (AR-48) is accepted as the mechanism; no contract text needed.

S_flat evidence, item 1a (13 Nov 2026, `research/datasets/part3/rv2_sflat_evidence.json`, script `rv2_sflat_evidence.py`; statistics only). Spread = P99(Y) − P1(Y), nearest rank (P1 = the ceil(0.01·n)-th smallest value), over all 4,361 frames flagged `black` in the 690 SDG member videos:
| Group | Frames | min | P5 | median | P95 | max |
|---|---|---|---|---|---|---|
| (i) red-lit runs `run_43_seed_631373023`, `run_6_seed_1833142794` (15 recordings) | 3,952 | 0 | 4 | 9 | 14 | 16 |
| (ii) judged truly blank: `run_18_seed_1313717419.eye_00`, black frames in seq 21–102 | 50 | 0 | 0 | 0 | 7 | 14 |
| (iii) all others (41 recordings) | 359 | 0 | 0 | 10 | 14 | 16 |
(i) and (ii) overlap over 0–14. They **do not separate cleanly**, so under item 1c nothing is changed.
Where the overlap comes from (statistics only):
- Group (ii): 37 of 50 frames are exactly flat (P1 = P99 = 16, limited-range black). The other 13 are the edges of the blank stretch (seq 74–81 and 97–102), where P99 rises 18 → 35 and the spread 2 → 14: the occluder entering or leaving. The D-25 judgment was recorded as a range, so these edge frames fall in group (ii).
- Group (i): the 13 whole-video red-lit recordings (3,899 frames) have spread 3–16 on every frame, so none of them is flat. The spread 0–2 frames of group (i) come from the two partial recordings: `run_6…eye_01` seq 0–20 is exactly flat (P1 = P99 = 16; apparently the same kind of blank stretch as run_18), and isolated frames with P99 = 17 (spread 1) occur in `run_6…eye_01` and `run_43…eye_01`.
- So the overlap is between groups as defined, not obviously between flat and content-bearing frames. Re-grouping by frame (for example, only exactly flat frames as (ii)) would be a new judgment, so the agent leaves it to the Architect.
Not applied, since they depend on 1b: items 2 and 4. `rv2-provisional` stays as written; rv1 stays in force for synthetic evaluation; no real footage is processed. Applied: none of the rules. Recorded: items 3 and 5 accepted. Code change: `LumaStats` now also carries P1 (nearest rank); it changes no flag (`tests/decode/test_rv2_provisional.py::test_p1_nearest_rank_is_statistics_only`).
Owner decision (13 Nov 2026): Architect review recorded; item 1 returned to the Architect under 1c. Status: OPEN (S_flat not set).
Architect review, second ruling (Architect rulings of 13 Nov 2026, item A, "D-25 rv2"; Owner approval by forwarding them):
1. black iff P99(Y) ≤ 32 AND (P99 − P1) ≤ 2, nearest rank. This sets S_flat = 2.
2. `low_light` is a recording-level tag "when median frame P99 <= 32 and the frame is not black"; a stratum, never an exclusion.
3. frozen and overexposed unchanged; blurred not computed.
4. Version `rv2` for ALL M1a synthetic recordings; rv1 stays for the M0 fixtures only.
5. Re-run the 758-recording check; report counts per flag and the low_light list.
6. Real footage uses `rv2-real-provisional` (same rule). Before any real-data result, report the per-frame spread distribution of dark frames (P99 ≤ 32) on each real recording, statistics only. If dark real frames sit at spread 3–6 in clearly blank stretches, raise it here; the agent does not change the threshold.
Applied (13 Nov 2026): `src/rq1/decode/quality.py` versions `rv2` and `rv2-real-provisional` (same rule); `rv2-provisional` kept, superseded, only so the recorded evidence files above reproduce; rv1 unchanged (M0 fixture expected values unchanged). Tests `tests/decode/test_rv2.py` (hand values: flat and spread boundaries 2/3, P99 32/33, overexposed, frozen, dark content stays eligible, low_light cases). Representation details (the reading of "median frame P99 … not black", where the tag is kept): AR-51.
Re-run result, item 5 (`research/datasets/part3/rv2_check_synthetic.json`, script `rv2_check.py`; statistics only): `rv2` on all 758 synthetic recordings (30 SDG sample videos, 690 SDG member videos, 38 SmartSpaces Warehouse_001 videos), 558,000 frames.
| Flag | Frames | Recordings |
|---|---|---|
| `black` | 161 (was 4,361 under rv2-provisional) | 16 |
| `frozen` | 40 (unchanged) | 2 |
| `overexposed` | 0 | 0 |
| `decode_error` | 0 | 0 |
- Eligible 557,839 / 558,000 frames. All flags are in the 690 member videos; the 30 SDG samples and 38 SmartSpaces videos have 0 flags (P99 ≥ 62 on every frame).
- `black` by recording: `run_18_seed_1313717419.eye_00` 41 (the judged-blank stretch), `run_2_seed_487012118.eye_02` 34, `run_6_seed_1833142794.eye_01` 32, `run_6_seed_1495571596.eye_01` 11, `run_47_seed_1695863875.eye_01` 11, `run_12_seed_1489170790.eye_02` 8, `run_23_seed_905230252.eye_02` 6, `run_43_seed_631373023.eye_01` 3, `run_12_seed_695326786.eye_01` 3, `run_11_seed_1899586412.eye_01` 3, `run_1_seed_1944808407.eye_01` 3, `run_13_seed_1363227761.eye_01` 2, and 1 each in `run_1_seed_1489524600.eye_01`, `run_4_seed_2076866610.eye_01`, `run_1_seed_1315993226.eye_01`, `run_8_seed_404177405.eye_01`.
- `frozen`: `run_18_seed_1313717419.eye_00` 21 and `run_2_seed_487012118.eye_02` 19, the same 40 frames as before; each recording has more `black` frames than `frozen` ones (41 ≥ 21, 34 ≥ 19). Per-frame overlap was not recorded in this run.
- `low_light`, 13 recordings: exactly the 13 whole-video red-lit recordings of item 1a, none of which is now black on any frame: `run_43_seed_631373023` ceiling_01, ceiling_02, ceiling_04, eye_00, eye_02, eye_03, eye_04 (median P99 20–27) and `run_6_seed_1833142794` ceiling_01, ceiling_02, ceiling_04, eye_00, eye_02, eye_03 (median P99 21–30). The `eye_01` cameras of both runs are not tagged (median P99 47) and carry partial `black` (3 and 32 frames).
- The low_light reading: the other plausible reading (median over all decoded frames, tag unless every frame is black) gives the same 13 recordings, so the choice in AR-51 changes no tag on these data.
- For the record (no change made): frames with P99 ≤ 32 and spread 3–16 are now eligible. Among them are 9 of the 50 dark frames of the judged-blank stretch in `run_18…eye_00` (its edges, spread 3–14, occluder entering or leaving; the other 41 are black) and dark non-flat frames in the partial recordings, e.g. `run_6_seed_1495571596.eye_01` has 65 dark frames, 11 black, 54 at spread 3–16.
Real footage, item 6: not yet run. Gate: no real-data result is produced before the per-recording dark-frame spread report under `rv2-real-provisional`.
Status: DECIDED for synthetic M1a (`rv2`); real footage under `rv2-real-provisional`, item 6 report pending.
Architect, 13 Nov 2026 (Owner approval by forwarding): the rv2 re-run (1620d65) ACCEPTED; AR-51 ACCEPTED as written. Asked: for the 40 frozen frames, how many are also black under rv2, and the spread of any that are not.
Frozen/black overlap (`research/datasets/part3/rv2_frozen_overlap.json`, script `rv2_frozen_overlap.py`; statistics only): **all 40 frozen frames are also `black` under rv2**; every one is exactly flat (P1 = P99 = 16, spread 0). `run_18_seed_1313717419.eye_00`: 21 frames, decode_seq 53–73; `run_2_seed_487012118.eye_02`: 19 frames, decode_seq 181–199. No frozen frame is not black, so there is nothing to list. Nothing changed.

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

## D-27 (2026-11-12) — R4 (TTC/PET) and BL-1 to BL-6 definitions        status: CLOSED
Task: T-19   Blocking: T-19; T-20 (configurations in the pre-registration)
Question: The contract names R4 and BL-1 to BL-6 but defines neither computably. The BL table exists only in Package D (methodology). Which TTC and PET definitions, which Unknown rule, and which provider set for each BL?
Options: see CR-018 (readings a/b/c per item).
Agent's recommendation: TTC and PET from the R3 constant-velocity footprint prediction within τ; Unknown also without velocity; BL-1 deferred to M1b; BL-2 to BL-6 as listed in CR-018, as Appendix T text.
Owner decision (13 Nov 2026, Architect rulings item B; Owner approval by forwarding them): DECIDED. Appended verbatim to Appendix T as section T15, contract **E-1.2.13**. TTC as CR-018 1(a); predicted PET (`pet_pred`, never reported as "PET" without the suffix) from the swept regions (convex hull of the footprints at 0 and τ); Unknown when uncalibrated or either velocity is null; ttc_max ≤ τ and pet_max ≤ τ or ERR-SPEC; no R4 borderline flag in this version. BL-1 DEFERRED to M1b; BL-2 = R1, BL-3 = R2, BL-4 = R2 + R3, BL-5 = R2 + R4, BL-6 = R2 + R3 + R4 + R5; contact cue in all. TTC/PET values before G-PR are TEST-ONLY (1.5 s, 1.0 s). T-19 unblocked.

## D-28 (2026-11-13) — SDG oracle tracks: 2D box, not-visible frames, incomplete annotation, faulty truth boxes        status: CLOSED
Task: T-18 part B   Blocking: the SDG ORACLE-S3 artifacts and the CV-SIM references built from them (and so T-21); not S0 registration or the truth reading
Question: Which SDG 2D box feeds an oracle track point; what state an annotated but not-visible object-frame gets; whether a camera with incomplete annotation has truth; and how a 2D truth box that contradicts the object's own 3D box is handled?
Options: see CR-019 (readings per item). Evidence for item 4: over the 72 held runs, 46 boxes (all on camera `eye_01`) miss their own 3D box by ≥ 157 px; one inspected case encloses a foreground pallet stacker instead of the forklift. 483 others miss by ≤ 80 px (person mesh vs box), with nothing in between.
Agent's recommendation: tight box when visible; not visible → `predicted` with the loose box; incomplete annotation → no truth for that camera; inconsistent 2D box (excess > 120 px) → `predicted` with the reprojected 3D hull, logged as a truth defect.
Owner decision (13 Nov 2026, Architect rulings second set, item A; Owner approval by forwarding): DECIDED as Appendix T section T17 (E-1.2.15). Visible = the dataset's visible box (SDG tight); not visible inside the visible span → predicted with the image-clipped reprojected 3D box, or lost when that is empty; no point outside the visible span; the loose box is never a track point; cameras without complete annotation and camera parameters have no truth; loose-box excess > 120 px → truth_defect, treated as not visible; an excess in (80, 157] px → ERR-INVARIANT.

## D-29 (2026-11-13) — data_origin of a dataset whose scenes differ in origin (SmartSpaces)        status: CLOSED (Appendix T T16, E-1.2.14)
Task: T-18 part C   Blocking: SmartSpaces S0 registration (Warehouse_000, Warehouse_001) and the real Warehouse_026/027 registration; not the SmartSpaces calibration and truth reading, not SDG S0
Question: The SmartSpaces release holds a rendered scene (000), its Cosmos Transfer re-render (001, `synthetic_transferred`) and real scenes (026/027). `dataset_source` has one data_origin and one anchor (name, version), while VR-E-005 needs one origin per file. Which representation applies?
Options: see CR-020. (a) one dataset row per origin, told apart by the version label; (b) one row with a chosen origin, sites carry each scene's origin; (c) contract change.
Agent's recommendation: (a).
Owner decision (13 Nov 2026, Architect rulings second set, item C; Owner approval by forwarding): option (a), version labels "<edition>@<revision>/<data_origin>" ("CR-020 ruling (T16) confirmed against the CR text"). Agent note: the T16 section (E-1.2.14) itself has not reached the agent; Appendix T carries a placeholder. Only the quoted sentence is applied.

## D-30 (2026-11-13) — Leakage edge between a scene and its re-render across dataset rows (SmartSpaces)        status: CLOSED (T16.2)
Task: T-18   Blocking: freezing any split that contains SmartSpaces recordings; nothing else
Question: Under CR-020 option (a), Warehouse_000 and its Cosmos Transfer re-render Warehouse_001 are separate dataset rows, and the scene and render-lineage edges only link recordings of the same dataset. The current rule gives no edge between them, although T14.1 makes them one scene. Should those edges apply across dataset rows of the same release (same name and `<edition>@<revision>`)? The T16 text, which the agent has not received, may already say.
Options: see CR-021. (a) edges apply across rows of the same release; (b) declared by hand at freeze; (c) no edge.
Agent's recommendation: (a).
Owner decision (13 Nov 2026, T16.2, Owner approval by forwarding): option (a). "Within one dataset" means rows with the same dataset name; scene, run, seed and render-parent edges apply across those rows.

## D-31 (2026-11-13) — T17.5 refusal band and the held 80.1 px box        status: CLOSED (Appendix T T18, E-1.2.16)
Task: T-18   Blocking: oracle tracks and references of one SDG camera (`…run_22_seed_1886649344`, `eye_02`); nothing else
Question: T17.5 refuses any loose-box excess in (80, 157] px, but the largest ordinary excess on the held data is 80.1 px (a person box), inside that band. As written, that camera is refused. Keep it refused, or set the band's lower bound above 80.1?
Options: see CR-022. (a) as written; (b) band (81, 157] or (80.1, 157.3).
Agent's recommendation: (b), with the bound stated by the Architect.
Owner decision (14 Nov 2026, Architect rulings item B; Owner approval by forwarding): guard band (90, 150] px, threshold 120 px unchanged. Appended verbatim to Appendix T as section T18, contract **E-1.2.16**, together with the absence-length rule (a not-visible run inside the visible span is predicted only when it has ≤ g_max frames; a longer run is lost on every frame) and the run-length reporting for the G-PR choice of g_max.

## D-32 (2026-11-13) — SDG forklift yaw: the motion-direction check is not concentrated        status: CLOSED
Task: T-18 / T-21   Blocking: SDG S4 (forklift footprint orientation) and everything built on it in the M1a run; not S0, S1, ORACLE-S3 or SmartSpaces
Question: The Architect's check on AR-52 item 2 passes on SmartSpaces (99.8 % of moving-forklift frames within 15° of the adopted yaw). On SDG it does not: 53.6 % within 15°, 35.3 % beyond 75°. The off-axis frames are pivot turns at 75°/s, where the footprint centre swings across the body axis; on straight frames 100 % are within 15°. Use the SDG box yaw, or not?
Options: see CR-023. (a) use the box yaw; (b) T8.2 fallback (heading, then disc); (c) circumscribed disc for all SDG forklift frames.
Agent's recommendation: (a). Until decided, SDG yaw is withheld in code.
Owner decision (14 Nov 2026, Architect rulings item A; Owner approval by forwarding): option (a), no contract text. SDG forklift yaw = the box long-axis yaw ("simulator yaw when supplied", T8.2). The motion-direction check is withdrawn as an acceptance test and kept as evidence. SDG S4 unblocked. The heading-fallback finding is added to CR-007 / D-8; a `forklift_turning` per-frame stratum is proposed in T-20.


## D-33 (2026-11-14) — T18 absence length: counted in the camera's frames or in eligible frames?        status: CLOSED (Appendix T T19, E-1.2.17)
Task: T-18   Blocking: nothing now; decide before the M1a run (T-21)
Question: T18 amendment 2 predicts a not-visible run only when it "has <= g_max frames (the T8.1 parameter)". T17 counts frames of the camera as the truth lists them; T8.1 counts eligible frames. A run that contains a frame that is not eligible (a black frame, for example) can be lost under one count and predicted under the other. Which count applies?
Options: see CR-024. (a) decoded frames of the camera (implemented, as T17 reads); (b) eligible frames (as T8.1).
Agent's recommendation: (a). The number of held runs on which the two differ is in the Progress log and in `t17_counts_*.json`.
Owner decision (14 Nov 2026, Architect rulings second set, item A; Owner approval by forwarding): option (b), eligible frames, as the T8.1 gap is. Appended verbatim to Appendix T as section T19, contract **E-1.2.17**. Counts re-run.

## D-34 (2026-11-14) — G-PR: approve and freeze the pre-registration        status: CLOSED (14 Nov 2026); frozen after D-35, see the Progress log
Task: G-PR   Blocking: T-21 (M1a run) and everything after it
Question: `docs/preregistration_DRAFT.md` is the agent's proposal. Please choose the values in its "Owner" columns and commit the result as `docs/preregistration_FROZEN.md`. Points that need an explicit choice: (1) g_max (§5; evidence only, no value recommended); (2) the split: SDG validation/test sizes, the draw seed, and where the single SmartSpaces leakage group goes (§2); (3) w_ref per dataset and the census sampling (§3.2); (4) the rule and lifecycle parameters of §4.3, for which the held data give no basis; (5) the SmartSpaces forklift footprint (two box sizes, one prior per class; §4.2); (6) whether the `forklift_turning` stratum needs contract text, and its window and threshold (§6.1); (7) the acceptance-criterion targets and n_min_units (§9); (8) whether the truth-side statistics should be recomputed on validation runs only after the split is frozen (§10 item 1); (9) bootstrap replicates and seed (§4.4).
Options: (a) freeze with the Owner's values; (b) return the draft with changes for a second version.
Agent's recommendation: none on the scientific values. On procedure: decide (6) and AR-56 item 2 with the Architect before the freeze, because both change what is computed.
Owner decision (14 Nov 2026, G-PR; pasting the G-PR text = Owner decision D-34 and approval of the Architect rulings in it):
- **A. Architect rulings.** T20 appended verbatim to Appendix T, contract **E-1.2.18**: T20.1 (visible = dataset-visible AND eligible; revises AR-56 item 2) and T20.2 (report-time stratum `forklift_turning`). Remaining items of AR-53, AR-54, AR-55 and AR-56 (item 2 as revised by T20.1): ACCEPTED.
- **B. Owner values** for `docs/preregistration_FROZEN.md` (draft values stand unless listed): (1) g_max = 15 frames, grid 5, 15, 30, 60, stated basis 0.5 s short-occlusion rationale, not fitted to the run-length tables; (2) split SDG 24 validation / 48 test, seeded draw stratified by generation batch, seed 2026111401; SmartSpaces group validation; tier T1; (3) sampling as drafted (w_ref 10 s SDG, 30 s SmartSpaces; census; one camera = one group); (4) §4.1–4.4 base values accepted, each recorded as "exploratory design assumption (not evidence-derived; to be reviewed against literature before publication)"; τ grid 2.0, 3.0, 4.0; one-at-a-time sweeps; combinations T15.5 refuses are listed, not run; (5) SmartSpaces forklift footprint: one prior, 2.68 × 1.16 m, anchor centre; GV-04 reports the bias per forklift box size; (6) forklift_turning: w_turn = 0.5 s, e_fturn = 5°/s, sensitivity at 2 and 10°/s; (7) criteria #1 MR-01 exact_equal, #2 GV-01 RMSE ci_upper_le 0.25 m, #3 GV-07 speed RMSE ci_upper_le 0.15 m/s, #4 GV-04 abs_bias_ci_within 0.10 m; n_min as drafted; #5–#10 not registered, reported without a decision; (8) after the split freeze, §5 and §6.1 truth-side tables on validation runs only, beside the all-runs tables; nothing re-chosen; (9) bootstrap B = 2,000, seed 2026111402, CI 0.95; (10) oracle-path runs on SmartSpaces Warehouse_000 only, Warehouse_001 kept for M1b; (11) §10 note: SDG forklift speed ≤ about 0.75 m/s, so forklift_decel (e_dec 2.0 m/s²) and the forklift part of the contact cue (k_c 3.0 m/s²) cannot be exceeded; coverage limitation, thresholds unchanged.
- **C. Procedure.** Implement T20, suite twice, re-run counts; write the frozen document, register the four criteria, freeze the split and the sampling plan; B.8 tables; STOP before T-21 (no S8 run on any partition without a separate go-ahead). "If any value above cannot be applied as written, stop and report before freezing."
- **Applied:** A and C.1 (see the Progress log entry of 14 Nov 2026). **Not applied:** C.2 and C.3. Item B.2 cannot be applied as written (D-35), so nothing is frozen: no `preregistration_FROZEN.md`, no split, no sampling plan, no criterion records.

## D-35 (2026-11-14) — Split draw: "stratified by generation batch" cannot be applied as written        status: CLOSED
Task: G-PR (D-34 item B.2)   Blocking: the freeze (C.2), the validation-only tables (C.3), T-21
Question: The recorded `generation_batch` (T14.1 lineage, S0) has **14 values** over the 72 SDG runs, of sizes 22, 15, 14, 4, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1 (`warehouse_osmos/nearmiss-1` 22, `warehouse_osmos_1/nearmiss` 15, `warehouse_osmos/nearmiss` 14, `warehouse_osmos_2/nearmiss/shard-15` 4, `…/shard-03` 4, `…/shard-00` 3, `…/shard-02` 2, `…/shard-31` 2, and six single-run shards). A one-third validation share is a whole number in only 2 of the 14 strata (15 and 3). Reaching exactly 24 validation runs needs an allocation rule that the G-PR text does not give, and the choice decides which runs are in test. Two plausible readings give different partitions, so the agent does not choose (CLAUDE.md).
Options (validation counts per stratum; the rest is test; inside each stratum the validation runs are a simple random draw without replacement, seed 2026111401, runs sorted by ext_run_id, numpy PCG64):
- (a) **14 recorded batches, largest remainder.** Quotas N/3: floors give 19; the three strata with remainder 2/3 (14 → 5, 2 → 1, 2 → 1) take 3 more; the last 2 go to 2 of the 9 strata tied at remainder 1/3 (22, 4, 4 and the six singletons), chosen by the seeded draw. Uses the field as recorded; for the small batches the seed, not the stratification, decides.
- (b) **3 batch families** (first path element of `generation_batch`: `warehouse_osmos` 36 runs, `warehouse_osmos_2` 20, `warehouse_osmos_1` 16), largest remainder: 12 / 7 / 5 = 24, no tie. Every stratum has 16 or more runs, and the allocation needs no seed. The family is derived from the recorded field, not recorded as its own field.
- (c) **No stratification:** a simple random draw of 24 of the 72 runs.
- (d) another rule stated by the Owner.
Agent's recommendation: (b). It is the only option whose allocation is fixed without a tie-break, and each stratum is large enough to balance something. (a) is closest to the words but leaves 2 of the 24 places to a 9-way tie.
Everything else in D-34 can be applied as written (checked 14 Nov 2026): the τ grid {2, 3, 4} with ttc_max ≤ 2.0 and pet_max ≤ 1.5 in one-at-a-time sweeps from the base values gives **no** combination that T15.5 refuses; the four criteria map onto `acceptance_criterion` records (criterion #2 "per viewpoint class" becomes one record per class, an AR at the freeze); the sampling plan needs one plan per dataset row and partition because w_ref and w_guard differ (an AR at the freeze).
Owner decision (14 Nov 2026): option (b). Strata = the 3 batch families (first path element of generation_batch): warehouse_osmos 12 validation of 36, warehouse_osmos_2 7 of 20, warehouse_osmos_1 5 of 16. Inside each family: simple random draw without replacement, seed 2026111401, runs sorted by ext_run_id, numpy PCG64. The derivation is recorded in `docs/preregistration_FROZEN.md` and in the X0b split record (AR-57 item 2). The two freeze-time ARs (criterion #2 = one record per viewpoint class; one sampling plan per dataset row and partition) are accepted. Continue D-34 from C.2.
Owner answer (14 Nov 2026, during the freeze), on VR-E-005 (one data_origin per file) against the Warehouse_000 / 001 leakage group: X0b v1 holds SDG and Warehouse_000 only; Warehouse_001 is validation through its leakage edge (T16.2) and enters at M1b as a new split version (AR-57 item 9).

## D-36 (2026-11-14) — STOP after the freeze: go-ahead for the M1a validation run        status: CLOSED (approved for validation only)
Task: T-21   Blocking: T-21 (M1a run) and everything after it
Question: The pre-registration is frozen (`docs/preregistration_FROZEN.md`, version 1; X0b `art_w5v3ldr43xdsqc6l4zifmjkuuj`; three V0 plans; five acceptance-criterion records; freeze record `docs/preregistration/freeze_record.json`). D-34 item B.8 is done (`docs/preregistration/validation_truth_tables.md`): the stated basis of g_max, e_fturn and the footprint priors still holds on the validation runs; nothing re-chosen. By D-34 item C.4 and the Owner's session override (14 Nov 2026), no S5 or S8 run has been made on any partition and T-21 has not started. May the agent start the validation run of T-21?
Options: (a) go ahead with the validation partition only (then STOP again before test); (b) hold.
Agent's recommendation: none; the Owner decides. Before any S8 on test, the X0c leakage audit must be complete (R-2) and the reference windows locked.
Owner decision (14 Nov 2026): APPROVED for the VALIDATION partition only. Procedure: (1) before running, estimate wall-clock time and peak memory for (a) BL-2 to BL-6 on all validation windows and (b) the full one-at-a-time sweep grid; if (a) exceeds 4 hours or memory is at risk, propose a reduced plan and stop for approval; (2) order: base configurations (SDG, then SmartSpaces Warehouse_000), then the full_camera geometry run (GV metrics), then the MR-08/MR-12 sweeps; (3) every result tied to its code commit and pre-registration v1, "verified" or "experimental", oracle-path agreement under implementation conformance; (4) report: a one-page plain-language summary, then the full technical report; (5) anything that needs a frozen value or a contract definition changed: stop and raise it, do not adjust; (6) when validation is done, STOP; no X0c audit or test-partition work until a go-ahead referencing pre-registration v2.

## D-37 (2026-11-14) — Test-partition reservation        status: IN FORCE (Owner decision)
Task: T-21 and later   Blocking: all test-partition work
Owner decision (14 Nov 2026):
- The test partition is reserved. Nothing runs on test-partition recordings: no S4, S5 or S8 artifact is built for them, and no metric, count or statistic of system output is computed on them.
- The test partition will be evaluated once, under a pre-registration version 2 to be frozen after the Owner's literature review. Version 1 is the exploratory parameter set for validation only.
- The frozen split (X0b `art_w5v3ldr43xdsqc6l4zifmjkuuj`) and sampling plans stay as they are and are reused by version 2.
Agent's enforcement: the M1a run driver refuses any recording whose partition in the frozen split is not `validation` (ERR-LEAKAGE), and this is tested.

## D-38 (2026-11-14) — T-21 validation run exceeds 4 hours: reduced plan for approval        status: DECIDED (option A; detail and T21 ruling recorded below)
Task: T-21   Blocking: T-21
Question: D-36 step 1 estimate (`research/m1a/runtime_estimate.md`): (a) BL-2 to BL-6 on all validation windows takes about **88 h** serial (SDG about 2 h; SmartSpaces Warehouse_000 about 86 h, because it has 3.19 million person–forklift pair-frames against about 68,000 on SDG, at about 50 ms per pair-frame in S4, 70 % of it in the R4 `pet_pred` search). (b) The one-at-a-time sweeps take about 16 h serial on SDG (about 5 h with 3 workers) and are infeasible on SmartSpaces (about 700 h). SmartSpaces S4 needs an estimated 1–2 GB per camera, so its cameras must run one at a time on this 8 GB machine. Which plan?
Options:
- (A) **SDG complete, SmartSpaces after a speed-up.** (1) Speed up the R4 surrogate as an engineering change (an Agent Resolution): every ttc / pet_pred value bit-identical to the current code on all T15 fixtures, on a random-case equivalence test and on every SDG validation pair-frame; then re-measure. (2) SDG validation in full: base BL-2 to BL-6, full_camera run, all sweeps (about 6 h wall clock now, less after (1)). (3) SmartSpaces Warehouse_000: base BL-2 to BL-6 and the full_camera run only, one camera at a time, if the re-measured time is under a bound you set. SmartSpaces sweeps are listed as not run in v1.
- (B) **SDG only in v1.** SDG as in (A)(2); SmartSpaces deferred to v2. No code change.
- (C) **(A) without the speed-up:** SmartSpaces base only, running about 3.5 days in the background.
Agent's recommendation: (A), with the bound for (A)(3) set by you (for example 12 h). The window census is frozen, so no plan subsamples SmartSpaces windows.
Also open and needed before EV-M results: **CR-025** (how the O/H/PC references are built from truth). S3–S5, CM, GV and the MR metrics do not depend on it. GV-01 and GV-03–GV-08 and the S8 driver for real data are not yet built. They are implemented from the F.1 N7 table as part of T-21, with an AR for any representation detail.
Owner decision (14 Nov 2026): option (A), as recommended. The run is to start in a new session when the laptop can be left running for about 12 hours; the agent takes about 12 h as the bound for (A)(3) unless the Owner states another. Order: (1) R4 speed-up (AR, bit-identical values), re-measure; (2) SDG validation in full; (3) SmartSpaces Warehouse_000 base and full_camera runs, one camera at a time, if within the bound. CR-025 stays open: EV-M results wait for it.
Owner decision D-38 detail and Architect ruling on CR-025 (14 Nov 2026, pasted = approval):
- A.1 R4 `pet_pred` search speed-up, code only, as an AR revising the AR-49 item 1 method. Acceptance on the fixtures, randomized cases and ALL SDG validation pair-frames: every C_by_R4 value and every downstream S5 flag, label and episode boundary identical to the current code; ttc_s and pet_pred_s within 1e-6 s; null and null reasons identical. Bit-identity not required. Any larger difference: stop and report.
- A.2 SDG validation in full: base configurations, full_camera run, all sweeps.
- A.3 Re-measure SmartSpaces. If base + full_camera <= 12 h, run them one camera at a time; otherwise stop and report. SmartSpaces sweeps not run in v1 (stated in the report).
- B. CR-025: Appendix T T21 (contract E-1.2.19), appended verbatim.
- C. GV metrics and S8 from F.1 N7 within T-21; representation details as an AR.
- D. Test partition still reserved (D-37).
- Owner session instruction: long jobs write each completed camera's results to disk, and a restart resumes without recomputing finished work.

## D-39 (2026-11-15) — SmartSpaces: the T21 references are not feasible as specified; what replaces SmartSpaces EV-M in v1?        status: DECIDED (option (a) for v1; T21 amendment for v2)
Task: T-21   Blocking: SmartSpaces EV-M1–EV-M8, CM-02 (reference-moving frames) and CM-06 (reference clearance) on SmartSpaces. Not blocking: SmartSpaces base and full_camera runs (running under D-38 A.3), SmartSpaces GV and the other CM metrics, everything on SDG.
Question: D-38 A.3 re-measurement (machine idle; `research/m1a/runtime_estimate.md` addendum): SmartSpaces base + full_camera ≈ **8.5 h** for the 19 cameras (≤ 12 h, so they run, one camera at a time). But T21.1 builds references from "every eligible frame on which both objects exist in the truth, whatever their visibility", and the SmartSpaces truth is scene-wide: every camera's truth holds all 60 persons and 9 forklifts on every frame they exist. That gives **4.44 million reference pair-frames per camera, 84.4 million over 19 cameras** (`research/m1a/smartspaces_reference_pair_frames.json`), about **200 h** at the measured 8.7 ms per pair-frame, and more memory per camera than this 8 GB machine has. Which plan?
Options:
- (a) **SmartSpaces EV-M not run in v1.** Report SmartSpaces GV, CM-01, CM-03–CM-05, CM-07–CM-10, MR-01 (base runs); list EV-M1–EV-M8, CM-02 and CM-06 on SmartSpaces as "not run in v1 (T21 reference infeasible on this machine)". SDG carries all EV-M results.
- (b) **Architect amendment of T21 for scene-wide truth:** e.g. restrict reference pairs in a camera to pairs that are both visible (T20.1) in that camera at least once, or to pair-frames within a stated distance; then re-estimate. Changes reference meaning, so it is a contract decision.
- (c) **Run T21 as written in the background** (about 8–9 days serial; one camera at a time; memory-bound, may not complete on 8 GB).
Agent's recommendation: (a) for v1, and (b) put to the Architect for v2. Under (b), "both visible at least once in the camera" would cut the pairs to those T21.3 can ever make assessable.
Also for review (no work waits on it): AR-58 (accepted under D-38 A.1, evidence recorded) and the four AR-59 review flags: item 2 (T21.1 reference without visibility in Q), item 5 (GV-04 at full_camera positions), item 6 (GV-07 against simulator speed at the same w_v), item 7 (GV-08 realized minimum from the same run, null past the POW end).
Owner decision (G-M1a, 17 Nov 2026, D-40 item 3): option (a) for v1: SmartSpaces EV-M1–EV-M8, CM-02 and CM-06 are not run in v1. For v2 the Architect will amend T21 to restrict reference pairs in a camera to pairs that are jointly visible (T20.1) in that camera at least once.

## D-40 (2026-11-17) — STOP at G-M1a: Owner review of the M1a validation results        status: DECIDED (M1a accepted as experimental validation evidence; rulings 1–9)
Task: G-M1a   Blocking: T-22 and all M1b work; any test-partition work (also D-37)
Question: The M1a validation run is complete (`reports/M1a_report.md`, plain-language page first):
- SDG: EV-M, CM, GV, sweeps and MR-01 = 1.0.
- SmartSpaces Warehouse_000: CM and GV.
- The position-error diagnosis is done (Architect, 17 Nov 2026).
Does the Owner accept M1a as reported, and in what order should the open items be decided?
Open items for this gate:
1. **D-39** (SmartSpaces EV-M; recommendation (a) for v1).
2. **CR-026** (range condition for full_camera foot rays; proposal only).
   - Rays at or above the horizon are already null (`not_observable`). Rays that meet the floor far away give numeric positions.
   - A 50 m limit removes only wrong SDG positions, but also 239,502 SmartSpaces positions that are correct within 1 m.
   - Recommendation: a per-site range registered with the calibration, and a new null reason.
3. **AR-58** (accepted under D-38 A.1), **AR-59** review flags 2, 5, 6, 7, and **AR-60** (speed-only; the optional check on the two largest SmartSpaces cameras was skipped on the Architect's instruction).
4. **Hidden feet at moderate range** (CR-026 stated limitation): whether the foot-point source on occluded bottom edges needs its own CR before M1b.
Agent's recommendation: decide D-39 and CR-026 first. GV-01 / GV-07 / GV-08 cannot be read as calibration quality until CR-026 is settled. No acceptance criterion was evaluated (validation only).
Owner decision (G-M1a, 17 Nov 2026):
1. M1a ACCEPTED as experimental validation evidence, subject to item 2 (report wording).
2. Report wording: BL-4/BL-6 vs BL-3 → "agree more closely with the BL-6 reference definition (T21.5)"; plain-language sentence on reference dependence (BL-2 vs BL-3 least reference-dependent; BL-3 vs BL-6 partly circular); note beside BL-2: R1/R2 disagreement 51 % SDG, 4 % SmartSpaces, so the BL-2 finding is viewpoint-dependent and not yet tested on SmartSpaces.
3. D-39: option (a) for v1; T21 amendment (jointly visible pairs) for v2.
4. AR-59 item 2 ACCEPTED; item 5 REVISED (GV-04 at simulator positions, re-report); item 6 ACCEPTED; item 7 ACCEPTED, and GV-08 also reported against simulator truth. AR-58 and AR-60 ACCEPTED.
5. Descriptive per-label (O, H, PC) recall and precision per configuration on SDG.
6. CR-026: no fixed range rule; kept open; pixel-sensitivity and person height-consistency diagnostics added; the Architect writes the rule for v2/M1b.
7. D-8 / CR-007: SDG forklift full_camera median error about 1 m, no outliers.
8. Pre-registration v2 note (recorded below as D-41).
9. M1b feasibility: CPU detector runtime on this Intel Mac, model licences, FPS on 10 SDG frames (no download over 1 GB without approval); then STOP.

## D-41 (2026-11-17) — Note for pre-registration v2: how position accuracy is stated        status: RECORDED (no change to v1)
Source: Owner, G-M1a (D-40 item 8).
- GV-01 RMSE is outlier-dominated on both datasets: SDG 44.8 m, of which 99.9 % of the squared error comes from 0.3 % of points; SmartSpaces 12.5 km.
- Pre-registration v2 should state position accuracy as **median, P95 and outlier share** (share above stated distances).
- **Position availability** (share of object-frames with a numeric position, by null reason) should be reported separately.
- Pre-registration v1 and its frozen criteria are unchanged.

## D-42 (2026-11-17) — STOP after the M1b feasibility probe: go-ahead for T-22?        status: DECIDED (19 Nov 2026)
Task: T-22   Blocking: T-22 (detector benchmark) and all later M1b work
Question: The D-40 item 9 probe is done (`research/m1b/feasibility.md`).
- **Runtimes:** PyTorch 2.2.2 CPU and ONNX Runtime 1.19.2 install and run on this Intel Mac. They live in a separate Python 3.9 environment, `.venv-det`, because no wheels exist for the project's Python 3.15.
- **Speed** on 10 SDG validation frames (1920 × 1080): YOLOX-nano 34.3 FPS; SSDlite320 7.1; YOLOX-s 3.9; Faster R-CNN MobileNetV3 1.1; Faster R-CNN ResNet50 v2 0.12.
- **Licences:** torchvision code BSD-3 (weights trained on COCO, no separate licence stated); YOLOX Apache-2.0; Ultralytics AGPL-3.0 (not used).
- COCO has no forklift class. On these frames the models emitted person and a few other labels (truck, tv, boat, suitcase …), not matched to objects.
Options:
- (a) Go ahead with T-22 (benchmark on an SDG and SmartSpaces validation frame subset with truth matching, licence table), using `.venv-det` as a pre-approved environment.
- (b) Hold M1b until the Architect has written the CR-026 rule and pre-registration v2 has started.
Agent's recommendation: none; the Owner decides. The weight licences need the Owner's check before any use beyond research. A separate interpreter (`.venv-det`, Python 3.9) for detector code is an environment decision; it should be recorded in WORKPLAN §0 if accepted.
Owner decision (19 Nov 2026, with Architect instructions):
1. **Option (a), with a revised T-22 scope: zero-shot detectors.** YOLO-World v2-s (Ultralytics) and Grounding DINO tiny (IDEA-Research), with exactly the prompts "person" and "forklift". Probe protocol fixed before any detector is run (WORKPLAN T-22 row; `research/m1b/zero_shot_probe.md`).
2. `.venv-det` (Python 3.9, PyTorch 2.2.2 CPU) is accepted and recorded in WORKPLAN §0.
3. New installs go into `.venv-det` only: `ultralytics` and `transformers` at the newest versions supporting Python 3.9 and torch 2.2.2, pinned in `research/m1b/requirements_detector.txt`.
4. Downloads: each below 1 GB, into git-ignored `out/m1b/weights/`, with source URL, SHA-256 and licence recorded in `research/m1b/` and `NOTICE.md`.
5. Not allowed: changing the frozen pre-registration or any analysis module; running S4, S5 or S8 with detector output (that waits for the Architect's detector-path pilot spec); fine-tuning; Ultralytics trackers. STOP after the probe report.

Owner answers to two questions the agent asked before downloading (19 Nov 2026):
- **Budget.** The datasets already held 29.24 GB of the 30 GB cap, and the feasibility weights 0.31 GB. The new weights (about 1.07 GB) did not fit. Owner: model weights count toward the cap, and the cap is raised to **31.5 GB** for this task.
- **CLIP package.** YOLO-World's text encoder needs the Ultralytics CLIP fork, which is installed from git and is not on PyPI. Owner: install it into `.venv-det`, pinned by commit (`7ffa84b3bfa40c42ecc1c77147a855e69cb2dd40`).

## D-43 (2026-11-19) — Licence for the repository        status: DECIDED (19 Nov 2026)
Source: Owner, 19 Nov 2026.
Decision:
- (a) `LICENSE` at the repository root: the unmodified GNU AGPL-3.0 text, from https://www.gnu.org/licenses/agpl-3.0.txt (SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0`).
- (b) `NOTICE.md` lists the third-party material the repository refers to but does not contain, each with its licence:
  - the SDG near-miss data (OpenMDW-1.1);
  - SmartSpaces `MTMC_Tracking_2026` (CC BY 4.0);
  - Safe and Unsafe Behaviours (CC BY 4.0; no frames, crops or faces in this repository, D-24 c);
  - every detector weight file used, with its source URL and SHA-256.
  It states that no dataset files or weights are in the repository.
- (c) Reason for the record: the working system uses an AGPL-3.0 detector (Ultralytics YOLO-World, D-42). The Owner may relicense the project's own code later.

## D-44 (2026-11-16) — STOP: V-02 needs a written C-layer review and adjudication protocol        status: DECIDED (19 Nov 2026)
Task: V-02   Blocking: V-02 only (off the critical path; nothing on `m0-implementation` waits on it)
Question: The V-02 compatibility audit (`research/review_ui/V-02_compatibility_audit.md`, branch `v02-review-ui`) found no schema conflict: the tables, UUIDv7 IDs, the hash-chained status log, the VR-E-053 blindness guard and the κ / α functions all exist and can be reused unchanged. But the protocol the screens must enforce is not in the contract (CR-027, gaps G1–G8). Without it the agent would be inventing labels, statuses and blind rules. How should V-02 proceed?
Options:
- (a) The Owner / Architect supply the C-layer protocol as contract text (Appendix T section), covering G1–G8; V-02 then resumes as specified.
- (b) The Owner rules on G1–G8 directly in this entry for V-02 fixture use only (a tooling decision, not a contract change), records marked "fixture; protocol provisional"; the contract text follows later.
- (c) Narrow V-02 to what needs no protocol: reviewer screen writing `reviewer_assessment` only (G1, G4, G8 still needed), no adjudication or status entries; or (d) hold V-02.
Readings the agent would propose if asked (not applied): G1 (a) interval and pair may be shown, blind stays true if no system label, flag, measured value or other assessment is shown; G2 (a) two; G4 (a) [0, 1]; G5 (a) the Owner's three values; G7 tier1 iff both labels equal and neither is `unsure`, else tier2; class `independent_expert_judgment` iff both assessments blind and both reviewers attested independent. G3, G6 and G8 have no reading in the text.
Also: Q1 time-on-task (no field; add none?), Q2 what `agreement_stat_ref` points to, Q3 build FX-13 with Architect-supplied expected values?, Q4 V-02 on real footage (D-24 b forbids labels on SmartSpaces 026/027).
Agent's recommendation: (a), or (b) if the Owner wants the tool before the contract text. The agent recommends not starting the adjudication screen under (c), because its status entries are the part most likely to be reported.
Owner decision (19 Nov 2026): **option (a).** The Architect's C-layer protocol is Appendix T section **T22** (contract **E-1.2.20**), appended verbatim; pasting it was the Owner's approval of T22 and of the steps that follow.
- On `m0-implementation`: T22 appended to Appendix T; CLAUDE.md contract line updated to E-1.2.20; T22.13 schema change (`reviewer_assessment.review_time_s · f64 · nullable`) in the schema source with its validator test; fixtures FX-13 and FX-13a to FX-13f with the expected values T22 states. No other code change on this branch.
- On `v02-review-ui`: merge `m0-implementation` (no rebase), then build V-02 as the T22 blind review application (part A). The original V-02 items 3 to 7 still apply; where they differ, T22 wins. No merge back into `m0-implementation`, no pull request.
- Not in this decision: the reporting workflow (candidate_review procedures); the Architect issues it as T23.
- Entry copied from branch `v02-review-ui` on 19 Nov 2026 so both branches agree.

Note on numbering: D-44 and CR-027 were opened on branch `v02-review-ui` (the V-02 entries, renumbered from D-40 and CR-026 on 19 Nov 2026) and are copied here with their decision (19 Nov 2026). The next free numbers are D-46 and CR-028 on both branches.

## D-45 (2026-11-19) — STOP after the T-22 zero-shot probe        status: DECIDED (19 Nov 2026)
Task: T-22   Blocking: the detector-path pilot (S4/S5/S8 with detector output), T-23 and all later M1b work
Question: The zero-shot probe is done (`research/m1b/zero_shot_probe.md` and `.json`).
- Data: 100 SDG validation frames; 93 person and 97 forklift reference boxes; IoU ≥ 0.3; best-F1 threshold. Descriptive only.
- **Grounding DINO tiny:**
  - person: recall 0.95, precision 1.00 (threshold 0.45);
  - forklift: recall 0.89, precision 0.96 (threshold 0.45);
  - speed: 16.5 s per frame (median), P90 19.7 s; peak memory 2.3 GB.
- **YOLO-World v2-s:**
  - person: recall 0.90, precision 0.98 (threshold 0.20);
  - forklift: recall 0.63, precision 0.92 (threshold 0.05, the lowest tested; recall 0.38 at 0.10);
  - speed: 0.35 s per frame, P90 0.37 s; peak memory 1.8 GB.
- Forklifts on eye-level cameras are the weak case for both models: recall 0.51 for YOLO-World and 0.83 for Grounding DINO.
- **Scale.** All 67,800 SDG validation frames would take about 6.6 h with YOLO-World and about 13 days of serial CPU time with Grounding DINO on this laptop.
- **Choices to review.** The instruction did not fix seven choices (draw procedure, frame spacing, model settings, Grounding DINO class assignment without NMS, tie rules, timing). They are listed in the report for the Architect.
Options: for the Owner and Architect (detector-path pilot spec, choice of detector, prompts or thresholds for the pilot). The agent makes no recommendation. Nothing was fine-tuned or tracked, and no detector output entered the pipeline.
Owner decision (19 Nov 2026, with the Architect's detector-path pilot spec; pasting it = approval):
0. **Rulings on the probe.**
   - The seven agent choices in `zero_shot_probe.md` are ACCEPTED as recorded. The probe is not re-run.
   - The probe thresholds are the pilot's fixed values, with no further tuning: YOLO-World v2-s person 0.20 and forklift 0.05; Grounding DINO tiny 0.45 for both.
   - The 20 probe cameras are excluded from everything in the pilot, so the pilot results do not depend on the threshold choice.
   - Grounding DINO is not run at scale; it is used only in the frame-level check (item 3c).
1. **T-23 tracker adapter** (WP-17, reduced to the pilot):
   - ByteTrack via `trackers` if it installs in `.venv-det`, otherwise Ultralytics' built-in ByteTrack; default parameters, recorded, not tuned.
   - Input: S2 rows; output: S3 rows. Matched → tracked/detected. A bridge of at most g_max = 15 eligible frames → predicted/inferred; longer → lost. No point on ineligible frames. Foot point = bottom-centre.
   - One track class per detection class.
   - Tests: fixtures; IDF1 against simulator IDs; switches and fragments via the T-12 association.
2. **S2 stage:** YOLO-World v2-s, Ultralytics defaults, classes "person" and "forklift", the item 0 thresholds, every eligible frame; reproducibility class tolerance; no MR-01 run.
3. **T-25p pilot** on the SDG validation cameras with an ORACLE-S3, minus the 20 probe cameras (expected 206):
   - pipeline S1 → S2 → S3 → S4 full_camera → S5 BL-2..BL-6 → S8 against the T21 references; no yaw, T8.2 fallbacks; no forklift_turning stratum;
   - frame-level check: 100 frames, seed 2026111902, both models;
   - report `reports/M1b_pilot_report.md` with columns A / B / C;
   - runtime estimate first; STOP if over 12 h.
4. **Do not:** change the frozen pre-registration or any analysis module beyond the new S2/S3 adapters; tune any threshold or tracker parameter; touch the test partition; register an acceptance criterion; claim transfer to real footage. A contract gap on the detector path → CR, and that part stops.
5. Full suite twice in the main `.venv`; detector and tracker tests in `.venv-det`. Progress log, commit and push after T-23, the S2 stage and T-25p. STOP at the end (D-47).


## D-46 (2026-11-19) — Architect rulings on CR-028 and AR-61; two V-02 fixes        status: DECIDED (19 Nov 2026)
Source: Owner, 19 Nov 2026 (pasting the instruction = approval).
Decision:
1. **CR-028** (opened on `v02-review-ui`): decided. The readings are Appendix T section **T22.14**, contract **E-1.2.21**, appended verbatim on this branch: (a) audit size ceil(a_audit × tier-1 targets); (b) α over the audited targets only, "not computed (n < 5)" below 5; (c) a target drawn into any batch on the same configuration and partition is excluded from every later batch; (d) pilot assessments stored in reference, with no adjudication, status entry or audit; (e) water-filling allocation, with a batch below n_batch stated in the manifest. CR-028 is closed on `v02-review-ui` as superseded by T22.14.
2. **AR-61** (on `v02-review-ui`): all eleven items accepted as written.
3. **V-02 fixes** on `v02-review-ui`: stray shell text in the report; an Owner-only audit trail view (status history per target, with the hash-chain check); the real-frame dry run, if stored outside a fixture store, renamed and marked as never for real review; the original V-02 items 3 to 7 as the agent understood them, each marked, in the report.
4. Only the contract text goes into `m0-implementation`; the code stays on `v02-review-ui`.
Numbering: D-46 is used here; CR-028 and AR-61 are on `v02-review-ui`. Next free: D-47, CR-029, AR-62.


## D-47 (2026-11-19) — STOP after the T-25p detector-path pilot        status: DECIDED (19 Nov 2026)
Task: T-25p   Blocking: all later M1b work on the detector path
Question: The pilot is done and revised on the Owner's instruction of 19 Nov 2026 (`reports/M1b_pilot_report.md`; `research/m1b/pilot_results.json`, `pilot_frame_check.json`, `pilot_tracker_loss.json`, `pilot_license_components.json`). 206 SDG validation cameras, 24 leakage groups, 282 assessable T21 references. Descriptive, validation only.
- **Events (G1, BL-6; Target B intervals in the report).** Columns A and B are re-aggregated on the same 206 cameras.
  - A (oracle, simulator positions): recall 1.00, precision 0.95.
  - B (oracle boxes, full_camera): 0.74, 0.55.
  - C (YOLO-World + ByteTrack together, full_camera): 0.11, 0.22. BL-2 in C: 0.03, 0.10.
- **Where recall is lost (frame level, same references and matcher).**
  - Forklift: S2 0.61 → tracked points 0.16 → with predicted points 0.17.
  - Person: 0.92 → 0.91 → 0.92.
  - 99 % of forklift detections match a forklift; 27 % of those became tracked points.
- **Tracker threshold coupling** (installed `byte_tracker.py`): new tracks need ≥ 0.25 (line 500); the low-score second stage only continues tracks in the Tracked state (line 448); a lost track is revived only by a detection ≥ 0.25. Share of matched detections that were tracked, by band:
  - forklift: ≥ 0.25 86 %; [0.10, 0.25) 21 %; [0.05, 0.10) 0 %;
  - person: ≥ 0.25 99 %; [0.20, 0.25) 28 %.
- **Tracking.** Person IDF1 0.83, CM-01 0.91. Forklift IDF1 0.24, 93 identities never matched. CM-03 0.12.
- **Probe overlap.** 96 of the 206 pilot cameras, and 10 of the 20 frame-check cameras, share a run with a probe camera.
- **Frame-level check.** YOLO-World person 0.94, forklift 0.59. Grounding DINO tiny 0.96, 0.94, at 15.2 s per frame (YOLO-World 0.34 s).
- **Licence records.** The CLIP text encoder had no `license_component` row in the S2 artifact; the row is now recorded only (`pilot_license_components.json`). Adding it to the artifact would change the S2 artifact IDs.
- **Review:** AR-62 (items 3, 5, 6, 7 are review flags).

Options: for the Owner and Architect. None of these was run.
- (a) A post-hoc **exploratory** S3-onward re-run, with the tracker thresholds aligned to the detector thresholds. It would be reported beside column C, never replacing it. It needs no new detection: about 40 min.
- (b) Fix the detector and tracker thresholds **as a pair** in pre-registration v2.
- (c) Try a stronger forklift detector on the detector path. Grounding DINO costs about 44 times as much per frame.
- (d) Diagnose the 111 unmatched BL-6 candidate events in column C.
- (e) Stop the detector path here.

Agent's recommendation: none; the Owner decides. Nothing was tuned; the test partition was not touched.
Owner decision (19 Nov 2026; pasting it = approval):
0. Pilot report `f83a241` ACCEPTED as experimental validation evidence (synthetic, validation only). AR-62: all nine items ACCEPTED, with the report additions already made (IDF1 pooling stated; birth-frame and score-band counts reported).
1. **C' exploratory re-run** (S3 onward only; C's stored S2 reused, no S2 re-run).
   - One ByteTrack per class, as in C. Per class: track_high_thresh = new_track_thresh = the class's detector threshold (person 0.20, forklift 0.05); track_low_thresh = min(0.10, detector threshold), so for forklifts the second stage receives nothing. All other parameters are the installed defaults.
   - The rule is fixed before the run; no other value is tried.
   - Reported as "C' (post-hoc, exploratory)" beside C, never replacing it. Same tables as C, plus tracks started, tracks with no matched identity (false tracks) and identity switches.
   - The new tracker configuration is recorded in every S3 run configuration (new S3 IDs).
2. **CR-007 / D-8 evidence** (diagnosis only): on column B, the forklift position error decomposed along and across the camera's viewing direction on the floor (median, P95, by viewpoint); B's EV-M1/EV-M2 for pairs with forklift error below and above 1 m. Added to CR-007 for the Architect. No anchor rule is chosen.
3. **N9 diagnosis** of the 111 unmatched BL-6 events in C (and in C'): rule tests in pipeline order; primary stage counts. Descriptive only.
4. **Not now:** Grounding DINO on the detector path (revisit after C'); fine-tuning (T-24 stays blocked); any test-partition work (D-37); any change to the frozen pre-registration v1.
5. **Operations.**
   - Long runs only on mains power, with no other agent running on the laptop.
   - Every `.venv-det` command sets YOLO_CONFIG_DIR to a git-ignored folder in the repository; added to the run scripts.
   - Check and record whether Ultralytics' settings had sync enabled during the S2 and frame-check runs, and whether the network was reachable. Recorded in the Progress log; nothing in the results changes.
   - The next S2 build (pre-registration v2) carries the CLIP and Grounding DINO license_component rows inside the artifact.
6. Tests: full suite twice; detector-environment tests. Progress log, commit, push. Report: a new section for C' and items 2-3, plus a short addendum to the plain-language page. STOP and open the next free D number for review. A part that needs a contract definition gets a CR and is skipped.

## D-50 (2026-11-19) — STOP after the D-47 follow-up (C', N9, CR-007 evidence)        status: DECIDED (19 Nov 2026)
Task: T-25p (D-47 items 1-3)   Blocking: further detector-path work
Numbering: opened as "D-49" at `bbba908`, renumbered to D-50 by the Owner (D-50 item 0) to avoid the T23 branch's D-49. D-48 is cited by the Owner for the T23 agent's run during S2 and is not used in this file. No D-49 exists on `v02-review-ui` (pushed branch and worktree checked 19 Nov 2026), so nothing there was changed.
Question: the D-47 follow-up is in `reports/M1b_pilot_report.md` (section "D-47 follow-up"; addendum on the plain-language page). Results: `research/m1b/pilot_results_cprime.json`, `pilot_tracker_loss_cprime.json`, `pilot_n9.json`, `cr007_evidence.json`. Descriptive, validation only.
- **C' (post-hoc, exploratory; the rule fixed in D-47).**
  - BL-6 EV-M1 0.07 (21/282), EV-M2 0.15 (21/141), against C 0.11 and 0.22.
  - Forklift: tracked-point recall 0.12 (C 0.16); tracks started 230 (171); fragments 158 (105); predicted points 1,908 (582); IDF1 0.217 (0.244).
  - False tracks: person 49 (36), forklift 3 (0). Identity switches: 0 in both.
  - **Mechanism:** with fuse_score on (unchanged by the rule), the first stage needs IoU × score ≥ 0.2 (`matching.py:145`, `byte_tracker.py:529-531`). A forklift detection scoring below 0.2 can start a track but cannot continue one. C's score-free second stage, which used to carry them, receives nothing under C'.
- **N9, rules 1-3** (rules 4 and 5 not evaluated: CR-029).
  - C: 111 unmatched BL-6 events: tracking 2, not attributed 109.
  - C': 120 unmatched: perception 1, tracking 1, not attributed 118.
  - In C, 110 of the 111 overlap a reference interaction of the same pair with temporal IoU between 0 and 0.3.
- **CR-007 evidence** (column B forklift error): along the line of sight, median −1.01 m; across, 0.09 m. The event split by forklift error is confounded by viewpoint and scene (BL-2 differs too).
- **New CR:** CR-029 (inputs of N9 rules 4 and 5 on the detector path; 5 open points).
- **Operations:** Ultralytics sync was off during S2 and the frame-level check, and the network was reachable. `YOLO_CONFIG_DIR` is now set by every `.venv-det` command.

Options: for the Owner and Architect; none of these was run.
- (a) Define CR-029 so that rules 4 and 5 can attribute the 109 unattributed events.
- (b) A further exploratory tracker setting, e.g. fuse_score off. This would be a new post-hoc variant, which the D-47 rule excluded.
- (c) Decide the CR-007 anchor with this evidence.
- (d) Revisit Grounding DINO on the detector path (D-47 item 4: "revisit after C'").
- (e) Close the detector-path pilot here.

Agent's recommendation: none; the Owner decides.
Owner decision (19 Nov 2026; pasting it = approval):
0. This entry is renumbered from D-49 to D-50 wherever it is cited (report, Progress log). The T23 agent's D-49, if it exists on `v02-review-ui`, stays unchanged.
1. The detector-path pilot (T-25p) is **CLOSED** as exploratory validation evidence. No further tracker variant (including fuse_score off) is run on the 206 pilot cameras. Columns A, B, C and C' stay as reported.
2. One more descriptive table, from stored outputs only (no stage re-run), for C and C':
   - per unmatched BL-6 event: the temporal IoU with the best same-pair reference, as counts by IoU band 0, (0, 0.1], (0.1, 0.2], (0.2, 0.3);
   - per matched or overlapped reference: the number of same-pair system episodes overlapping it, and how many are linked by continuation_of_nk;
   - EV-M1/EV-M2 with "any temporal overlap, same pair" as the match condition, labelled "descriptive, not the N4 metric".
   N4 and the reported metrics are unchanged.
3. For pre-registration v2 (recorded in the v2 notes; v1 unchanged):
   - detector thresholds and tracker parameters (fuse_score included) are fixed as one package, chosen only on a tuning subset: all cameras of the runs that contain a T-22 probe camera. v2 results are reported on the other validation runs and on test.
   - The episode-extent / fragmentation question from item 2 is listed for the Architect.
4. Architect: CR-007 (anchor rule; the evidence is now sufficient) and CR-029 (N9 rules 4-5 on the detector path), together with CR-026, as v2 inputs. No rule is implemented now.
5. Not now: Grounding DINO on the detector path; fine-tuning (T-24); the test partition (D-37).
6. Tests, Progress log, commit, push. STOP.

<!-- D-51 STEP 4 (c), 21 Nov 2026: the entries below are copied unchanged from `v02-review-ui`, with their decisions. Numbers D-48, D-49, D-51, CR-030, CR-031, AR-63 and AR-64 are shared by both branches; D-50, CR-029 and AR-62 are this branch's. Next free numbers on both branches: D-52, CR-032, AR-66. -->

## D-48 (2026-11-19) — Reporting workflow, indicators and simulated regulator view (T23)        status: DECIDED (19 Nov 2026)
Source: Owner, 19 Nov 2026 (pasting the instruction = approval of T23 and of its steps).
Decision: Appendix T section **T23** appended verbatim on `v02-review-ui` as contract **E-1.2.22**. Build the workflow (`src/rq1/workflow/`) in the V-02 application, with the T23.15 tables and the FX-14 to FX-14i fixtures. Run the T23.11 demo draw with seed 2026111903 on a new store, using the D-45 pilot BL-6 S5 artifacts if they exist, otherwise the T-21 oracle ones. Write W-01_report.md; STOP at D-49. No merge into `m0-implementation`. Undefined points that change a count, a state or a statistic go to a CR; nothing is chosen.
Numbering on this branch: D-48 (this), D-49 (the STOP), CR-030 and AR-63 (CR-029 and AR-62 are used on `m0-implementation`).

## D-49 (2026-11-19) — STOP after W-01: Owner review of the T23 reporting workflow        status: DECIDED (20 Nov 2026)
Task: W-01 (D-48)   Blocking: further workflow work; the merge of E-1.2.22 into `m0-implementation`
Question: the T23 workflow is implemented and verified on fixtures. Report: `research/workflow/W-01_report.md`; screenshots in `research/workflow/screenshots/` (fixtures only).
- **Demo** (seed 2026111903, source the D-45 detector-path pilot, column C):
  - new store `out/review/demo_20261119/`;
  - 3 simulated establishments, 9 areas, 8 AI reports (15 member episodes);
  - no manager decision has been taken;
  - the store has no Owner profile yet: run `python -m rq1.review init --store out/review/demo_20261119 --owner <pseudonym>`, then serve; steps in the report.
- **CR-030** (10 items) lists what T23 leaves undefined. Nothing was chosen.
  - Item 1 **blocks** the adjudications and status entries of safety-manager decisions on AI reports (T23.5 c, d). The schema requires adjudication.reference_class, and T22.1 (b) says candidate_review has none. Two FX checks are strict xfails until it is ruled.
  - Items 2 to 9: indicators print "not determined" with every reading's value where the readings differ, or the action is refused.
  - Item 10: VR-E-041 and the CLAUDE.md "Never" list against T23's establishment IDs and 301-style fields.
- **AR-63** (14 items) are representation choices for review. Items 5, 6 and 8 change displayed wording or pre-filled values: the mixed-label ai_label, the group aggregation of clearance and evasive action, and the refusal of human text with unqualified wording.
- **Pinned test lists updated for contract additions:** `EXPECTED_TABLES` (+8 T23.15 tables) and `REQUIRED_IDS` (+FX-14 to FX-14i), as was done for T22.

Options: for the Owner and Architect.
- (a) Rule on CR-030 (item 1 first), then a follow-up implements the rulings.
- (b) Accept or reverse AR-63 items.
- (c) Merge E-1.2.22 (contract text only) into `m0-implementation`.
- (d) Play the demo roles and give feedback.
Agent's recommendation: none; the Owner decides.

Owner decision D-49 (20 Nov 2026): rulings on CR-030 and AR-63, contract **E-1.2.23** (Appendix T T23.16 to T23.27). Source: the Architect's D-49.1 addendum, approved by the Owner as proposed (pasting it = approval of the contract text and of the steps), including (1) only `usable` coverage counts as monitored, with `usable_degraded` shown separately, and (2) the `am_split` action and the `group_resolution` field.
- On `v02-review-ui`: T23.16–T23.27 appended verbatim to Appendix T; CLAUDE.md contract line, the "Never" line on safety scores (D-49.1 §8) and a new "Still raise a CR" item.
- CR-030 closed and AR-63 decided item by item (D-49.1 §7): AR-63 item 6 revised (T23.24), item 8 reversed (T23.22), items 1, 9, 10, 11, 12, 13, 14 accepted with additions, items 2, 3, 4, 5, 7 accepted.
- Tests first (FX-14a/b xfails removed; FX-14j–FX-14ad), then the T23.16–T23.27 implementation; the store registry with `out/review/main` and `out/review/demo_20261119`; re-render of the demo views (read-only); W-02 regression and reference-protection evidence (§6.2, §6.3) in `research/workflow/W-02_report.md`.
- Limits: no merge into `m0-implementation`, no pull request, no force-push or history rewrite; no stored record rewritten; no T22 batch, reference assessment, adjudication or manager decision; no S5/S8 run, no evaluation result, nothing on the test partition. The scoped merge is asked at D-51.
- Undefined points that change a count, a state or a statistic go to CR-031 (opened in any case for the T23.21 (d) path).
Numbering: the next STOP is D-51 (D-50 is used on `m0-implementation`); the next CR is CR-031.

## D-51 (2026-11-20) — STOP after W-02: E-1.2.23 implemented; reference-protection finding; scoped merge?        status: DECIDED (21 Nov 2026)
Task: W-02 (D-49)   Blocking: any further reference sampling or annotation (D-49.1 section 6.3); the scoped merge into `m0-implementation`; further workflow work
Question: E-1.2.23 (T23.16–T23.27) is implemented and verified on fixtures on `v02-review-ui`. Report: `research/workflow/W-02_report.md`.
- **Tests:** v02 full suite twice, identical; FX-14a/b pass (xfails removed); FX-14j–FX-14ad pass. No expected value edited; FX-14d and FX-14e setups gained one step each (CR-031 item 3).
- **Section 6.2:** M0 determinism reproduced at e6072ef with and without the adjudication change (12 IDs equal the M0 report); read-back of the stored M1a and pilot artifacts **incomplete** (stopped by low memory after 4,000 of 7,473 folders; 36 spot checks pass; rerun needed); every stored record of every store under `out/review/` validates under the new reader and every chain verifies, except the deliberately tampered W-01 fixture store. The S0–S5 rebuild of three SDG cameras was **not done** (an S5 run; forbidden by the D-49 limits; CR-031 item 10).
- **Section 6.3 finding (STOP):** the 9 demo runs of `out/review/demo_20261119` hold every CT (7) and every O (9) episode of the BL-6 T22 frame. After the T23.25 (b) exclusion the frame has CT 0, UD 31, NM 24, PC 151, H 15, O 0, so a batch of 60 would have four strata of 15 and no CT or O target. No existing batch is affected (the only batches are fixture batches); no annotator is exposed.
- **CR-031** (13 items, for the Owner and Architect), including item 1, the T23.21 (d) path a safety manager cannot take (sm_reopen does not leave pending_sm). **AR-64** (17 representation items, two marked REVIEW).
- The re-rendered demo pages show "accuracy of the alert source: not reported", because the demo store's manifest predates T23.26 (CR-031 item 9).
Options:
- (a) Rule on the frame finding (CR-031 item 13): accept a four-stratum batch, redraw the demo on a new store so CT and O stay in the frame, another frame, or hold.
- (b) Rule on CR-031 items 1–12; accept or reverse AR-64 items.
- (c) **Scoped merge** into `m0-implementation`: the contract text (T23 and T23.16–T23.27), CLAUDE.md, the adjudication schema change, VR-E-056, `src/rq1/validation/reference.py` and their tests only; no `src/rq1/workflow/` file and no `wf_*` table (file list in the report, section 4). Yes / no.
- (d) Authorise or drop the S0–S5 rebuild of three SDG cameras (§6.2 item 3).
Agent's recommendation: none; the Owner decides.
Numbering: D-51 here (D-50 is used on `m0-implementation`); CR-031 and AR-64 on `v02-review-ui`. Next free on this branch: D-52, CR-032, AR-65.

Owner decision D-51 (21 Nov 2026): rulings on CR-031 and AR-64, the T22 frame finding, the artifact read-back rerun and the scoped merge. Source: the Architect's review of W-02 (commit 748bafc), approved by the Owner (pasting it = approval of the rulings and of the steps).
- **Frame finding (CR-031 item 13): option (d), hold reference sampling.** No T22 batch is drawn until a later Owner decision. A four-stratum batch (option a) is refused: it would change what EV-M12 can say. When sampling resumes, the preferred route is option (b), a new demo draw on a new store whose runs leave CT and O episodes in the frame; the old demo store's runs may leave the exclusion list only if no person has acted on or viewed that store (STEP 3 c).
- **CR-031** closed item by item (CHANGE_REQUESTS.md): items 1, 2, 3, 5, 6, 7 and 8 become Appendix T **T23.28** (contract **E-1.2.24**); item 4 unit = report; item 9 keep the old demo store, one banner line added; item 10 the S0–S5 rebuild is dropped from section 6.2 item 3, the read-back must be completed; item 11 guard confirmed, CLAUDE.md "Never" line added; item 12 fixture stores stay unregistered.
- **AR-64:** all 17 items accepted, including items 14 and 15 (REVIEW).
- **Scoped merge into `m0-implementation`: approved, gated** on the read-back rerun passing in full (STEP 2).
- Hard limits unchanged from D-49: no S5 or S8 run, no new evaluation result, nothing on the test partition; no T22 batch, reference assessment, adjudication or manager decision; no demo draw; no stored record deleted, rewritten or reordered; no force-push, history rewrite or pull request. Undefined points that change a count, a state or a statistic go to CR-032.
Numbering: the CR-007/CR-026 v2 draft moves to E-1.2.25. Next free on this branch: D-52, CR-032, AR-66 (AR-65 is the D-51 implementation).

## D-53 (2026-11-23) — Pre-freeze diagnostics D1, D2 and D5 for the v2 rules (CR-007, CR-026)        status: DECIDED (23 Nov 2026)
Source: Owner, 23 Nov 2026; the Architect's v2 draft part 1 (diagnostics section), checked against E-1.2.24 on 23 Nov 2026 (pasting it = approval of the steps).
Decision (summary): evidence only, on `m0-implementation`. Step 0 camera sets (tuning 116 / reporting 110); step 1 D1 (and D3) on the stored column B S4; step 2 D2 (B-tune, B-sim-F, B-sim-P; oracle boxes, BL-6, N4, G1; labelled diagnostic); step 3 D4 on stored S2 detections; step 4 D5 split by camera set; step 5 report and STOP at D-54. Fix 1 (anchor offset) and Fix 2 (resolution gate) are not implemented. Hard limits: no contract change, no new parameter, no rule in `src/rq1/`; scripts in `research/m1b/` only; nothing on the test partition; the 110 reporting cameras only in the descriptive D5 table; no new detection, tracker run or pilot column; no stored record changed; CR-033 for anything undefined.
Carried out: see D-54 and the Progress log entry of 23 Nov 2026. CR-033 was not needed.

## D-54 (2026-11-23) — STOP after the D-53 diagnostics: results for the Owner        status: DECIDED (23 Nov 2026)
Task: D-53 (pre-freeze diagnostics)   Blocking: pre-registration v2 values and rule forms for CR-007 (anchor) and CR-026 (resolution); no other task
Question: the diagnostic results are in `research/m1b/v2_diagnostics_report.md` (diagnostic, tuning subset, not a reported result). Results only:
- **D1 (oracle boxes, 116 tuning cameras, 33,707 forklift frames).** Signed along-sight error by θ bin, 0–15° to 75–90°: −1.35, −1.32, −1.20, −0.97, −0.73, −0.58 m; median h(θ) 1.58 to 0.73 m. Candidate d = 1.00 m (median |along| 0.987 m). Residual after a constant d: median 0.15–0.42 m and P95 0.48–0.91 m by bin; all frames median 0.33, P95 0.64 m.
- **D3.** Estimate within 2 m of the camera: eye-level 12.9 %, ceiling 0.0 %.
- **D2 (BL-6, G1, 135 assessable references).** EV-M1 / EV-M2: B-tune 0.793 / 0.505; B-sim-F 0.904 / 0.567; B-sim-P 0.852 / 0.646; A 1.000 / 0.944. B-sim-F recovers 15 of the 28 references B misses; B-sim-P recovers 8. B-tune equals the stored column B on all 116 cameras (S4 payload hash). Only position and covariance were substituted; the simulator yaw was not.
- **D4 (detector boxes, 96 tuning cameras; 20 probe cameras have no stored S2).** 16,374 matched forklift frames: signed median −0.84 m, P95 −0.44 m. Paired with the oracle box on the same frames: median difference −0.05 m overall, −0.08 to −0.03 m in every viewpoint × θ bin.
- **D5.** At s_max 0.05 / 0.1 / 0.2 / 0.5 m/px, share flagged: tuning 3.2 / 0.6 / 0.5 / 0.4 %, reporting 2.2 / 0.5 / 0.4 / 0.4 %. Errors > 10 m caught: tuning 100 / 94 / 85 / 72 %, reporting 100 / 100 / 93 / 85 %. SmartSpaces copied unchanged.
Options: for the Architect and the Owner. Values and rule forms (d, a θ-dependent offset, a range or sensitivity gate) are chosen in pre-registration v2; none was implemented.
Agent's recommendation: none; the Owner decides.
Owner decision (D-54, 23 Nov 2026): rulings on the D-53 diagnostics. T24 (forklift anchor shift and floor-resolution gate) is adopted as contract **E-1.2.25** and implemented opt-in. A person-position diagnostic is authorised; a combined detector-path diagnostic on the tuning cameras is also authorised. Source: the Architect's draft part 1 (`v2_architect_package_part1_CR007_CR026_DRAFT.md`), as corrected after the Architect checked it against E-1.2.24 on 23 Nov 2026; `research/m1b/v2_diagnostics_report.md`; `research/m1b/v2_tracker_report.md`. Pasting it = Owner approval of the rulings and of the steps.
1. **Fix 1 (CR-007 / D-8) adopted as T24.1:** a constant shift d away from the camera, for forklifts on the `full_camera` tier only. v2 candidate values d = 1.00 m and r_taper = 2.0 m for the SDG prior; the SmartSpaces prior uses d × 0.923 (scaled, not fitted); recorded in v2_notes as **selected, not frozen**. The residual is reported, never hidden (D1: median 0.33 m, P95 0.64 m). Detector boxes and oracle boxes use the same d (D4: paired difference about −0.05 m).
2. **Fix 2 (CR-026) adopted as T24.2:** one global s_max, v2 candidate value 0.1 m/px (D5 on the tuning cameras: 94.2 % of errors above 10 m caught, 0.0 % of good points lost); **selected, not frozen**. A gated position reuses the existing codes: position null reason `not_observable`, clearance_state `unmeasurable_geometry_failure`. The marker is a stored sensitivity value (T24.2 (c)). No new null-reason value.
3. **Persons:** the D2 finding (with simulator person positions, unmatched events fall from 105 to 63) is investigated (STEP 4) before any person rule is written.
4. CR-007 and CR-026 are closed as superseded by T24.
5. **Iteration is allowed.** Every diagnostic re-run uses the 116 tuning cameras only. The 110 reporting cameras are evaluated once, after v2 is frozen. The test partition stays reserved under D-37.
Steps: 0 state check; 1 records (this entry, CRs, Appendix T T24, CLAUDE.md, v2_notes); 2 T24 implementation, tests first (T24.4); 3 B-v2 on the tuning cameras (oracle boxes; B-T24.2, B-T24.1, both); 3b C-pkg and C-v2 on the tuning cameras (detector path; runtime estimate, stop above 3 h); 4 person-position diagnostic; 5 report and STOP. Hard limits: nothing on the 110 reporting cameras or the test partition; pilot columns A, B, C, C′ and their stored artifacts unchanged; no new detection; no tracker change beyond the D-56 package; no stored record deleted, rewritten or reordered; no force-push; undefined points that change a count, a state or a statistic go to the next free CR.

## D-55 (2026-11-23) — Select the v2 detector + tracker package on the tuning subset        status: DECIDED (23 Nov 2026)
Source: Owner, 23 Nov 2026; Architect draft `v2_architect_package_part2_tracker_DRAFT.md` (T1 ByteTrack retuned, T2 BoT-SORT comparator; grid and selection rule as drafted), approved by the Owner (pasting it = approval of the steps).
Decision (summary): on `m0-implementation`, tracking measures only, on the 116 tuning cameras. Step 1 S2 for the 20 probe cameras (pilot S2 configuration, licence rows per D-47 item 5); step 2 BoT-SORT adapter (ReID off, camera-motion compensation off, NumPy assignment) and `tracker_id` in the S3 run configuration (column C unchanged); step 3 runtime estimate (stop above 6 h); step 4 grid of 36 forklift configurations per tracker; step 5 selection by the fixed rule; step 6 fragmentation check; step 7 report and STOP. Hard limits: no S4, S5, S8 or EV metric; nothing on the 110 reporting cameras or the test partition; columns A, B, C, C′ unchanged; detector as D-45; no contract change. The winner is selected, not frozen. D-54 stays open.
Carried out: see D-56 and the Progress log entry of 23 Nov 2026. CR-033 opened (readings; `tracker_id` for column C); AR-66 proposed.

## D-56 (2026-11-23) — STOP after the D-55 tracker selection: result for the Owner        status: DECIDED (23 Nov 2026)
Task: D-55 (tracker selection)   Blocking: freezing the v2 package in pre-registration v2; no other task (D-54 independent)
Question: the selection result is in `research/m1b/v2_tracker_report.md` (tuning subset, synthetic SDG, selection evidence, not a reported result). Result only:
- **Selected package:** `trc_7flfpx52d2siiljxkqwcorr7nz`, T1 ByteTrack. Forklift: track_high 0.05, new_track 0.05, track_low 0.05, fuse_score false, track_buffer 90, match 0.8; person: column C ByteTrack defaults.
- **Against column C settings (116 cameras):** forklift IDF1 0.250 → 0.774; forklift coverage by tracked points 0.160 → 0.593; point precision 1.000 → 0.979; person IDF1 0.846 in both (same person tracker).
- **T2 BoT-SORT winner** `trc_iwm5ndlac27qun2gouwrtoroun` (the same grid point): IDF1 0.775, inside the 0.01 band. The package was decided at the first tie-break, coverage: 19,981 against 19,980 matched forklift references of 33,677 (one reference frame). Under the secondary reading of CR-033 item 2 (tracked and predicted points) the same rule selects the BoT-SORT configuration instead.
- **Guards:** all 72 configurations passed (precision ≥ 0.95; person IDF1 equal by construction). fuse_score false was decisive: every fuse_score true configuration has IDF1 ≤ 0.36.
- **Fragmentation (tracking level):** package 112 of 116 forklift identities covered, 7 by two or more tracks (median 1, P90 1, max 2); column C 66 covered, 26 by two or more (median 1, P90 2, max 4). Longest bridged gap 15 frames (= g_max) in both.
- **Readings to confirm (CR-033):** items 2–4 (tracked point = state `tracked`; fragments definition; inclusive band; `gmc_method` counted as a changed parameter, which did not decide anything here).
Options: confirm the package for pre-registration v2; or change a CR-033 reading (item 2(b) would select the BoT-SORT configuration); or another instruction.
Agent's recommendation: none; the Owner decides.
Owner decision (D-56, 23 Nov 2026): Source: the Architect's draft part 1 (`v2_architect_package_part1_CR007_CR026_DRAFT.md`), as corrected after the Architect checked it against E-1.2.24 on 23 Nov 2026; `research/m1b/v2_diagnostics_report.md`; `research/m1b/v2_tracker_report.md`. Pasting it = Owner approval of the rulings and of the steps.
- The package `trc_7flfpx52d2siiljxkqwcorr7nz` (T1 ByteTrack; forklift track_high, new_track and track_low 0.05, fuse_score false, track_buffer 90, match 0.8; person = column C ByteTrack defaults) is **confirmed for pre-registration v2. It is selected, not frozen.**
- CR-033 items 1 to 4 are confirmed **as applied** (primary reading). A reading is never changed after the result is known. CR-033 is closed.
- Reports state that the T1 and T2 winners are indistinguishable on the tuning cameras: IDF1 0.774 vs 0.775; coverage 19,981 vs 19,980 of 33,677 reference frames.
- Standing caveat for every report using the package: it accepts forklift detections down to score 0.05. Point precision 0.979 was measured on synthetic SDG data only and is not known for real footage.
- AR-66 is accepted as written (Architect: representation and engineering only).

## D-57 (2026-11-23) — STOP after the D-54 diagnostics: T24 on the tuning cameras, person positions        status: DECIDED (24 Nov 2026)
Task: D-54 STEPS 2–5   Blocking: freezing pre-registration v2 (T24 values, person rule, if any); any run on the reporting cameras; no other task
Question: the results are in `research/m1b/d54_report.md` (diagnostic, tuning subset, not a reported result). Results only:
- **T24 implemented opt-in (E-1.2.25).** All T24.4 checks are tests. With the parameters absent, stored S4 of M1a A, M1a B and pilot C is byte-identical on 96 tuning cameras, and the 12 M0 IDs are reproduced at e6072ef.
- **B-v2 (oracle boxes, BL-6, 116 cameras), EV-M1 / EV-M2:**
  - B-tune 0.793 / 0.505;
  - B-T24.2 0.793 / 0.510;
  - B-T24.1 0.926 / 0.568;
  - B-both 0.926 / 0.571;
  - A 1.000 / 0.944.
  - Forklift error median 1.06 → 0.40 m, P95 1.48 → 1.09 m; share > 2 m 0.1 % → 0.9 %.
  - The gate nulls 366 person frames (eye level) and no forklift frame.
- **Detector path (116 cameras), EV-M1 / EV-M2 / CM-03 detected:**
  - C-pkg 0.526 / 0.333 / 0.51;
  - C-v2 0.578 / 0.329 / 0.51.
  - Ceiling C-v2 0.781 / 0.368; eye level 0.394 / 0.277.
  - On the 96 pilot cameras, column C gives 0.096 / 0.172 / 0.11.
  - C-v2 unmatched events: 159 of 237 (149 with same-pair overlap); 69 references covered by ≥ 2 episodes; 15 of 237 episodes carry `continuation_of_nk`.
  - The gate puts 110 forklift and 158 person frames at the resolution limit, all eye level.
- **Persons (column B):**
  - median error 0.19 m; along median −0.13 m; box half-depth median 0.38 m;
  - 296 frames at r ≥ 20 m have median error 76 m.
  - Unmatched B-tune events with no B-sim-P counterpart: 15 (reading 1) or 50 (reading 2). B alone is below d_pc more often than below d_p.
  - The 8 references B-sim-P recovers: in 3, the B-sim-P clearance is below d_p and B's is not (1 of these is also below d_pc); 5 are on the same side of both thresholds.
- **Readings to decide:**
  - CR-034 (T24.2 on `lost` points): no effect on these data.
  - CR-035 (STEP 4 (c) counterpart).
  - AR-67 (representation of T24).
Options: for the Owner and the Architect: freeze the T24 values as selected, change them, add a person rule, or another instruction.
Agent's recommendation: none; the Owner decides.
Owner decision (D-57, 24 Nov 2026): Source: `research/m1b/d54_report.md`, reviewed by the Architect (24 Nov 2026) and approved by the Owner. Pasting it = Owner approval of the rulings and of the steps.
Rulings:
1. **T24 values are kept as selected:** s_max 0.1 m/px; forklift prior `anchor = box_bottom_centre`, d 1.00 m, r_taper 2.0 m; SmartSpaces d × 0.923. They are frozen together with pre-registration v2, not now.
2. **No person rule.** The person error has no systematic offset (median along-sight error −0.13 m, against a box half-depth of 0.38 m). The large person errors are at r ≥ 20 m, which T24.2 addresses.
3. **CR-034: reading (a) is confirmed.** The gate applies where E-1.2.24 forms a camera floor point (`tracked`, `predicted`). For `lost` points, `floor_resolution_m_per_px` is null (`not_applicable`). CR-034 is closed.
4. **CR-035:** a diagnostic-only question. Both readings stay reported side by side; none is chosen, and no reported value depends on it. CR-035 is closed.
5. **AR-67 is accepted as written** (Architect: representation and engineering only, with regression evidence).
6. **Next lever: split episodes.** In C-v2, 149 of 159 unmatched events overlap a reference of the same pair, and 69 references are covered by two or more episodes. This step diagnoses why episodes split, and sweeps the existing lifecycle parameter m_gap.
   - **N4 matching is unchanged.** The way events are scored against references never changes to fit the output.
   - **This is a value change, not a rule change.** m_gap already exists (`rule_configuration.lifecycle.m_gap_frames`, T9.7). Joining across POWs or across tracks would need new contract text: it is **not** authorised here.
7. **Fine-tuning stays after 1 Dec** (T-24 remains blocked for this submission).
8. All of this stays on the **116 tuning cameras**. Nothing runs on the 110 reporting cameras or on the test partition (D-37).
Steps (summary): STEP 0 state check (clean, level with origin, mains power); STEP 1 records; STEP 2 split diagnosis on the stored D-54 outputs of C-v2 and B-both (mechanism (i) same POW, (ii) different POWs of the same tracks, (iii) different tracks of the same identities; gap; for (i) T = 0 / unknown share, last flag, clearance against d_p and d_pc, Q state) → `research/m1b/d57_split_diagnosis.json`; STEP 3 m_gap sweep {5, 15, 30, 60} frames, S5 onward on the stored D-54 S4 artifacts, for C-v2, B-both and A, with the pre-declared selection rule on C-v2 (EV-M1 ≥ EV-M1(5) − 0.02; highest EV-M2; tie within 0.005 → smaller m_gap; "selected under D-57, not frozen"; checked against item C7 before the v2 freeze); runtime estimate on 2 cameras, STOP above 2 h → `research/m1b/d57_mgap_sweep.json`; STEP 4 `research/m1b/d57_report.md`, full suite twice, next free D number, STOP.
Hard limits: nothing on the 110 reporting cameras or the test partition; pilot columns A, B, C, C′ and the stored D-54 artifacts unchanged; no new detection, no tracker change, no change to N4, the label rules or any contract text; no stored record deleted, rewritten or reordered; anything undefined that changes a count, a state or a statistic → next free CR, skip the item, continue.

## D-58 (2026-11-24) — STOP after the D-57 diagnostics: why episodes split, and the m_gap sweep        status: DECIDED (24 Nov 2026)
Task: D-57 STEPS 2–4   Blocking: freezing m_gap for pre-registration v2; any rule that joins episodes across POWs or tracks; any run on the reporting cameras; no other task
Question: the results are in `research/m1b/d57_report.md` (diagnostic, tuning subset, not a reported result). Results only:
- **Why episodes split (stored D-54 outputs; a split = two consecutive episodes covering the same reference):**
  - C-v2: 115 splits. (i) same POW 43; (ii) other POW, same tracks 30; (iii) other tracks 42. **(ii) + (iii) = 72 of 115 (63 %): most splits on the detector path are not lifecycle splits, and m_gap cannot fix them.** Joining them would need a contract rule (not drafted).
  - B-both: 87 splits. (i) 81; (ii) 6; (iii) 0.
  - (i) gaps, C-v2: median 10 frames (0.33 s), P75 15, P90 26.8, max 41. B-both: median 14, P75 27, P90 41, max 63 (30 fps).
  - In (i) gaps, T is 0 on 97 % (C-v2) and 93 % (B-both) of frames: the clearance is at or above d_p, not unknown. Before the gap, P (mostly with X) is true at a clearance between d_pc and d_p.
- **m_gap sweep, EV-M1 / EV-M2 at 5, 15, 30, 60:**
  - C-v2: 0.578 / 0.329, 0.607 / 0.410, 0.630 / 0.459, 0.622 / 0.462.
  - B-both: 0.926 / 0.571, 0.889 / 0.702, 0.867 / 0.848, 0.859 / 0.943.
  - A: 1.000 / 0.944, 0.933 / 0.947, 0.933 / 0.947, 0.874 / 0.944.
  - The pre-declared rule selects **m_gap = 30 frames (about 1.0 s): selected under D-57, not frozen**, to be checked against item C7.
- **The oracle check is not clean.** At 30, EV-M1 falls on B-both (0.926 → 0.867) and on A (1.000 → 0.933), while EV-M2 rises.
  - The references are built once at m_gap 5 and stay fixed (T21.1, T21.4). A joined episode can span two references and match only one.
  - On A, all 9 lost references share an episode with another reference.
- **Checks:** at m_gap 5 the rebuilt S5 equals the stored S5 payload on 116 of 116 cameras for each configuration, and the EV values equal D-54.
- **AR-68** proposed (representation and engineering).
Options: for the Owner and the Architect: carry m_gap 30 to the C7 check; or keep m_gap 5; or address the reference lifecycle (T21.4) or a cross-POW / cross-track join rule in contract text; or another instruction.
Agent's recommendation: none; the Owner decides.
Owner decision (D-58, 24 Nov 2026): rulings on the D-57 diagnostics. m_gap becomes part of the event definition, stated in seconds. A rule for joining split events across POW breaks and track fragments is adopted as contract E-1.2.26 (T25), implemented opt-in and checked on the tuning cameras. Source: `research/m1b/d57_report.md`, reviewed by the Architect on 24 Nov 2026 and approved by the Owner. Pasting it = Owner approval of the rulings and of the steps.
Rulings:
1. **(a) m_gap defines an event; it is not a tuning knob.** It is stated in seconds (`m_gap_s`, T25.3) and applies to the system and the references alike. Its v2 value comes from the literature (item C7) or a stated design choice, never from an event score. The D-57 sweep value (30 frames) is **not** a v2 candidate; the D-57 sweep is kept as a sensitivity study only. At the v2 freeze, references are rebuilt once with the frozen `m_gap_s` (T21.4 then applies to the new reference set).
2. **(b) Splits are tackled now** with T25: T25.1 joins track fragments of one physical object (a tracking-level rule, selected by tracking measures, like D-55); T25.2 joins episodes of the same pair across a POW break. Justification, from the reference definition and not from a score: references are built from complete simulator truth on every eligible frame, whatever the visibility (T21.1), so a reference interaction does not break when the camera loses an object. A system split caused only by lost observation or a new track ID is a measurement artefact; a split where the pair was observed apart remains a real split.
3. **N4 matching, the label rules and EV definitions are unchanged.** Joining happens before matching, never inside it.
4. **(c)** After this task: v2 freeze with the literature values, then one run on the reporting cameras, then the demo build.
Six-question check (master instruction §10): 1 objective unchanged; 2 **yes**, the event count unit changes (one physical interaction observed in pieces is counted once); 3 no leakage (tuning cameras only; values chosen by tracking measures or from the event definition); 4 joined events are reported as joined, with their unobserved time; 5 within E1 instrument quality, E2 not affected; 6 scientific, hence this Owner decision.
Contract text: T25 appended verbatim to Appendix T (contract E-1.2.26).
Steps (summary): STEP 0 state check, incl. which S5 row N4 matches in single-camera runs (candidate_event: continue; episode: CR and STOP before STEP 3); STEP 1 records; STEP 2 T25.4 tests then code, full suite twice, M0 determinism and T25.4 regression; STEP 3 stitching grid on the 116 tuning cameras (T_s {1, 2, 3, 5} s × r_g {0.5, 1, 2} m, v_max person 2.5 / forklift 4.0 m/s, k_img 1.0, plus off; guard point precision per class ≥ 0.95; objective forklift + person IDF1; within 0.01 of best, then fewer forklift fragments per identity, then smaller T_s, then smaller r_g; selected, not frozen) → `research/m1b/d58_stitch_grid.json`; STEP 4 event check (C-v2, C-v2+T25, B-both+T25, A+T25; (α) m_gap 5 frames with the stored base references, (β) m_gap_s 1.0 with a diagnostic reference set rebuilt with m_gap_s 1.0, "diagnostic, not the v2 reference"; 1.0 s is a placeholder, not a v2 candidate; estimate on 2 cameras, STOP above 3 h) → `research/m1b/d58_events_tune.json`; STEP 5 `research/m1b/d58_report.md`, full suite twice, next free D number, STOP.
Hard limits: nothing on the 110 reporting cameras or the test partition (D-37); pilot columns and stored D-54/D-57 artifacts unchanged and never overwritten; no new detection; no change to N4, the label rules, the EV definitions or the stored base references (the β reference set is a separate diagnostic set); no stored record deleted, rewritten or reordered; no force-push; anything undefined that changes a count, a state or a statistic → next free CR, skip the item, continue.

## D-59 (2026-11-24) — Owner instruction: raise the download cap to 60 GB and add non-duplicate data        status: DECIDED (24 Nov 2026)
Owner instruction (24 Nov 2026, in session): "raise the cap up 60GB and download whatever unique data set you can get … update the plan for testing and maybe tuning with that extra data set … give me [a] report so that i could show it to the architect".
Applied as: WORKPLAN §0 row D-59 (60 GB in total, synthetic `MTMC_Tracking_2026` scenes with ground truth, no re-render, no depth maps, pinned revision `d38193b`); selection, screen and draw in `research/datasets/qualification.md` Part 5, written before download; CR-036 opened for how the new scenes join the frozen split. The testing and tuning plan is a proposal for the Architect (D-60), not applied.

## D-60 (2026-11-24) — STOP after the D-59 download: how the new SmartSpaces scenes are used        status: DECIDED (25 Nov 2026)
Task: T-26d   Blocking: T-26r, T-26s, T-26e (anything on the D-59 scenes beyond the checks already done); not D-58, not the v2 work
Question: the results and the proposal are in `research/datasets/part5/d59_report.md` (implemented: downloaded, hash-checked, screened; no system output). Results only:
- 11 scenes, 118 cameras, 300 s each (022: 309 s), SHA-256 equal for every file. Tier 1: 010, 011, 016, 017, 018, 019, 022 (45 cameras, 6 layouts not held before). Tier 2: 002, 004, 006, 020 (73 cameras, the layout of `Warehouse_000`).
- Screen rejected 008, 009, 012, 013, 014, 015 (no forklift). Held 51.45 GB of 60 GB.
Points to decide:
1. CR-036 main question: separate frozen addendum, test-only, tuning-only, or re-freeze.
2. CR-036 items 1–2: `layout_id` (scene asset or map identity) and `generation_batch` (val folder).
3. Roles of tier 1 and tier 2 (the agent's proposal: tier 1 held-out-layout test only; tier 2 option T2-b, a seeded 2 / 2 tuning / test draw).
4. Compute for the detector path (about 100 h in full; options in report §6).
5. Whether to qualify a further source within the 8.05 GB of headroom (report §7).
Agent's recommendation: report §6 (a proposal; the Architect and the Owner decide).
Owner decision (D-60, 25 Nov 2026): roles of the D-59 scenes (CR-036), their registration and split addendum, and a Colab GPU detection job for the held-out-layout scenes. Source: `research/datasets/part5/d59_report.md`, reviewed by the Architect on 25 Nov 2026 and approved by the Owner. Pasting it = Owner approval of the rulings and of the steps below. Recorded verbatim:

**When:** after the D-58 task has reached its STOP. One agent at a time on the laptop. Run on mains power.
**Where:** main folder, branch m0-implementation.

Rulings:
1. **Tier 1 is a held-out-layout test, and nothing else.** Tier 1 = scenes 010, 011, 016, 017, 018, 019 and 022 (45 cameras, 6 layouts never held before).
   - It is never used for tuning, threshold choice, diagnostics or demo material.
   - It is evaluated **once**, with the frozen v2 package, after the v2 reporting run.
   - It is reported per scene and per layout, descriptively, beside the X0b test result.
   - The claim it permits: "held-out synthetic warehouse layouts". Real-world generalisation is not claimed.
2. **Tier 2 is reserve.** Tier 2 = scenes 002, 004, 006 and 020 (73 cameras, `Warehouse_000` layout).
   - These scenes are registered, but assigned to no partition and used for nothing until a later Owner decision (planned: v3 tuning after 1 Dec).
   - Options T2-a, T2-b and T2-c stay open.
3. **CR-036 is resolved as a split addendum.** A new split version, `X0b-A1`, records the D-59 scenes **without changing any X0b assignment**: tier 1 → partition `test_layout_holdout`; tier 2 → `reserve`. It is frozen, like X0b (hash, freeze time), before any system output exists on these scenes (R-4: metadata only). Warehouse_001 still joins X0b later as planned (AR-57 note); it is not part of this task.
4. **CR-036 items 1 and 2:** `layout_id` = the SHA-256 of the scene's `map.png` (Git-LFS hash, as in Part 5). `generation_batch` = the dataset's `val` folder name and revision, `MTMC_Tracking_2026@d38193b`. Both are metadata, recorded in S0. They are leakage-group keys: every camera of a layout is in the same group.
5. **Colab GPU detection is approved** for the tier-1 videos only (S2 detection; nothing downstream of S2 runs on Colab).
   - **Cloud upload approved:** the Owner uploads the 45 tier-1 videos to the Owner's own Google Drive (synthetic, CC BY 4.0; no real footage, no worker data). This is the one exception to WORKPLAN §0 "never pre-approved: cloud upload", and it covers these files only.
   - The detector is the frozen D-45 detector: YOLO-World v2-s, the same weights, prompts and thresholds (person 0.20, forklift 0.05).
   - **Before** any tier-1 detection is used, an equivalence check (STEP 4) must pass.
   - Detection on tier 1 may run before the v2 freeze, because it produces no evaluation. **Before the single post-freeze evaluation, no one looks at tier-1 outputs beyond the integrity checks below**: no metrics, no images with boxes, no per-camera counts beyond the totals needed for integrity.
6. **Compute for tier 2:** not now.

Six-question check: (1) the objective is unchanged; (2) no measurement definition changes; (3) strengthens independence: a new held-out layout, assigned before any output exists; (4) adds one permitted claim, "held-out synthetic layout", with its limit stated; (5) adds a GPU job, but it saves CPU time; E2 is not affected; (6) scientific (partition roles), so this is an Owner decision.

Steps:
- **STEP 0: state check.** D-58 is at its STOP. The tree is clean and level with origin. Mains power is connected.
- **STEP 1: records.** Mark D-60 DECIDED with this text. Resolve CR-036 per rulings 3–4. Add to WORKPLAN §0: "D-60: cloud upload of the 45 tier-1 D-59 videos to the Owner's Google Drive; Colab GPU for S2 on those videos only." Commit and push.
- **STEP 2: registration (S0) of all 11 D-59 scenes.** Metadata only: `synthetic_rendered`, with `layout_id` and `generation_batch` per ruling 4, the calibration, and coverage. Same S0 procedure as the earlier SmartSpaces scenes. No decoding of frames beyond what S0/S1 already require. Commit and push.
- **STEP 3: split addendum `X0b-A1`.** Leakage groups use `layout_id` (one group per layout). Tier 1 → `test_layout_holdout`; tier 2 → `reserve`. X0b assignments stay unchanged (a test checks this). Freeze with the event time stored as in X0b (`frozen_utc`, outside the hashes, AR-7). The X0c audit passes. Commit and push.
- **STEP 4: Colab detection package and equivalence check.** (a) `research/colab/s2_detect.ipynb` and a small installable runner: installs pinned versions (the same Ultralytics version as `.venv-det`, 8.4.215; torch and CUDA as Colab provides, recorded); checks the SHA-256 of the model weights and of every input video against a manifest; decodes frames with the same PyAV path and frame eligibility as S1, using the same prompts and thresholds; writes per-camera raw detection files in the same format as `out/m1b/pilot/s2raw/`, plus a manifest with SHA-256 per file, device name, versions, wall time and frame counts; is resumable per camera (skips cameras already finished in Drive). (b) `research/colab/tier1_manifest.json`: the 45 video files with paths, sizes, SHA-256, and the total size the Owner must upload. (c) Equivalence check, before tier 1: the Owner runs the notebook on 2 tuning cameras that already have CPU S2 (one ceiling and one eye-level camera, the lowest camera ID in each; their videos are uploaded too; they are synthetic tuning data). The agent compares the Colab output with the stored CPU S2. Pass criteria: every CPU detection with score ≥ threshold + 0.02 has a Colab detection of the same class with IoU ≥ 0.95; the score difference of matched pairs has P99 ≤ 0.02; detection counts per class differ by ≤ 2 %. Report the result. If it fails: STOP and report. Do not loosen the criteria. (d) `research/colab/HOWTO.md` for the Owner, in plain steps (upload; open the notebook from GitHub in Colab, GPU runtime, mount Drive; run the 2-camera check and send the output folder back; run tier 1 and re-run after any disconnect; download the output folder to the stated path). Commit and push. Then STOP for the Owner to run the 2-camera check. Open the next free D number with the HOWTO path and the upload size.
- **STEP 5: after the Owner returns the outputs (next session, on the Owner's word).** Verify every file against the Colab manifest, and every input hash. If the equivalence check passed and the tier-1 run is complete: build S2 artifacts for the 45 tier-1 cameras. The execution record carries the device, the versions and the Colab manifest hash. The S2 configuration is the D-45 one; if the device must enter the configuration ID, record it under an AR and say so. Integrity checks only: every eligible frame has a detection record (possibly empty), there is no missing camera, and there are no duplicate frames. Report totals only. Commit and push. Open the next free D number. STOP.

Hard limits: tier-1 data: no tuning, no metric, no diagnostic, no image or clip with system output, and no demo use before the single post-freeze evaluation. Tier-2 data: registration and split assignment only. Nothing on the 110 reporting cameras or the X0b test partition (D-37). No change to the frozen detector, the tracker package or any contract value. Never delete, rewrite or reorder a stored record. No force-push. If something is undefined that changes a count, a state, a partition or a statistic: open the next free CR, skip that item, continue.


## D-61 (2026-11-25) — STOP after the D-58 T25 check: stitching selection and event-level results        status: DECIDED (26 Nov 2026)
Task: T-27 (D-58 STEPS 2–5)   Blocking: the v2 freeze (T25 values; m_gap_s from item C7); any run on the reporting cameras; the demo build; no other task (independent of D-60)
Question: the results are in `research/m1b/d58_report.md` (diagnostic, tuning subset, not a reported result). Results only:
- **T25 implemented opt-in (E-1.2.26).** Every T25.4 check is a test. With the parameters absent, the stored D-54 S4 / S5 and D-57 m_gap 5 S5 of C-v2, B-both and A are byte-identical on 116 of 116 tuning cameras, and the 12 M0 IDs are reproduced (W-02, AR-69 item 11).
- **Stitching (T25.1), tracking measures only:** the pre-declared rule selects **T_s 5 s, r_g 0.5 m (selected, not frozen)**. That is the largest T_s of the grid.
  - Person IDF1 0.846 → 0.919; forklift 0.774 → 0.780.
  - Fragments per identity: person 1.72 → 1.17; forklift 1.06 → 1.02.
  - Point precision unchanged (0.979 / 0.995). 77 links: 71 person, 6 forklift.
- **Event check, EV-M1 / EV-M2 (G1, N4 unchanged):**
  - α (m_gap 5 frames): C-v2 0.578 / 0.329; C-v2+T25 0.600 / 0.411; B-both+T25 0.926 / 0.571; A+T25 1.000 / 0.944.
  - Under α, T25.2 joins nothing on any path. The join limit (5 frames) is below the shortest POW-break gap (g_max + 1 = 16 frames). The α gain comes from stitching alone.
  - β (m_gap_s 1.0 s for the system and a diagnostic reference set rebuilt with 1.0 s): C-v2 0.653 / 0.438; C-v2+T25 0.677 / 0.525; B-both 0.935 / 0.841; B-both+T25 0.935 / 0.847; A 1.000 / 0.932; A+T25 1.000 / 0.961.
  - Joined events under β: C-v2+T25 21 (15.6 s unobserved); B-both+T25 1; A+T25 4.
  - The oracle check is clean under β: A keeps EV-M1 1.000; B-both 0.935, against 0.926 under α.
- **Splits remaining** (D-57 mechanisms (i) / (ii) / (iii), on events): C-v2 under α 43 / 30 / 42; C-v2+T25 under α 11 / 53 / 16; under β 0 / 36 / 16. A+T25 under β 0 / 5 / 0.
- **Open for review:** CR-037 (contact state, IE and A5.2 pair of a joined event; primary readings applied). The two pair readings agree on every event here. AR-69 proposed (representation of T25).
Agent's recommendation: none; the Owner decides.
Owner decision (D-61, 26 Nov 2026): pre-registration v2 values, T25 selection, freeze. Source: the value-by-value review between the Owner and the Architect, 25–26 Nov 2026, of the decision register `PwP_Consolidated_Decisions_For_Claude_2026-11-24.md` (items C1–C13, D3, F1–F3) and the literature-review questions (`architecture/decisions_for_literature_review_2026-11-21.md` §C). The repository state was checked at `m0-implementation` 8d254b6. Pasting it = Owner approval of the rulings and the steps.
- **§1 Rulings** (1.1 two kinds of numbers; 1.2 the 1.5 s anchor; 1.3 v2 base values; 1.4 sensitivity grids; 1.5 engineering selections; 1.6 criteria and headline; 1.7 references and reporting order; 1.8 six-question check) are recorded **verbatim** in `docs/preregistration/v2_notes.md`, section "Owner decision D-61". In short: definition numbers are never chosen by an event score; instrument numbers only by tracking measures on the 116 tuning cameras. Changed from v1: pet_max 1.5 s, d_p 3.0 m, m_gap_s 1.5 s, w_post 1.5 s, e_dec 1.0 m/s², k_c 1.5 m/s², g_max 45 frames (1.5 s), clearance band edge 3 m added; iou_m 0.5 and 0.7 reported beside 0.3.

§2–§4, verbatim (headings demoted one level to sit inside this entry):

#### 2. Steps for the agent

**Hard limits for the whole task:**
- No S2 or later system stage on the 110 reporting cameras or the test partition. The only exceptions are reference building from truth (STEP 5) and the X0c audit (STEP 6).
- No change to N4, the label rules, the EV definitions or any v1 record.
- No stored artifact deleted, rewritten or reordered.
- No force-push.
- Anything undefined that changes a count, a state or a statistic: open the next free CR, skip the item and continue.

**STEP 0 — state check.**
- Report the HEAD commit and whether D-58 STEP 2 (T25 tests and code) is done.
- Confirm all held data is 30 fps (δ_nom = 1/30 s), so that m_gap_s 1.5 → 45 frames and g_max 45 frames ↔ 1.5 s.
- Report whether `speed_sigma_mps`, `σ_c` and `minclr_sigma_m` are ever non-null on the detector path. These decide whether k_σ and the borderline flags can fire.
- Report which labels and states route an episode to manager review in T23, and confirm that an O episode is routed only in the OI-1 case.
- Report only; change nothing.

**STEP 1 — records.**
- Add D-61 to `DECISIONS_NEEDED.md` as DECIDED.
- Append §1 of this prompt to `docs/preregistration/v2_notes.md`, verbatim.

**STEP 2 — D-58 STEP 2** (T25.4 tests, then code; full suite twice; M0 determinism; T25.4 regression), as written in D-58, if not already done.

**STEP 3 — D-58 STEP 3**, the stitching grid on the 116 tuning cameras, exactly as written in D-58:
- T_s {1, 2, 3, 5} s × r_g {0.5, 1, 2} m;
- v_max person 2.5 m/s, forklift 4.0 m/s; k_img 1.0; plus off;
- guard: point precision per class ≥ 0.95;
- objective: forklift + person IDF1;
- tie rule: within 0.01 of best, then fewer forklift fragments per identity, then smaller T_s, then smaller r_g.
- Output: `research/m1b/d58_stitch_grid.json`.

**STEP 4 — replaces D-58 STEP 4.**
- The (α)/(β) design and the 1.0 s placeholder are dropped.
- Run one diagnostic event check on the 116 tuning cameras only, for C-v2+T25 and A+T25, at the v2 base values (§1.3) with the STEP 3 stitching selection.
- Score it against a tuning-camera reference set built with the v2 base values. That reference set is labelled diagnostic and stored separately from the STEP 5 references.
- Report EV-M1, EV-M2, n_members, unobserved_gap_s, and the IE share caused by the new g_max.
- This check selects nothing. First estimate the runtime on 2 cameras; STOP if the estimate is above 3 h.
- Output: `research/m1b/d61_events_tune.json`.

**STEP 5 — freeze.**
- Write `docs/preregistration_v2_FROZEN.md`: v1's structure, with §4 replaced by §1.3–1.5 of this prompt (values, grids and the basis text).
- Build the v2 freeze record: contract version, analysis commit, `requirements.lock` SHA-256, all configuration IDs (detector, tracker package with T25.1, substrate, rules, evaluation), criteria records, `frozen_utc`. Build it twice; the two must be identical.
- Build the v2 reference sets for tuning, reporting and test from simulator truth (T21.1), and record their IDs and hashes in the freeze record.
- Copy the §1.6 and §1.7 text into the pre-registration.

**STEP 6 — test readiness. Prepare only; run no test.**
- Run the X0c leakage audit (R-2).
- Prepare the reference-window lock (`locked_utc`, `lock_sha256`) for the Architect's review.
- Record a pass/fail table for each item:
  - X0c complete;
  - windows lockable;
  - freeze record reproducible;
  - test run IDs and hashes match X0b v1 (48 runs, 471 cameras);
  - detector and tracker weights hashed;
  - SDG licence row present for every component used;
  - Colab runtime estimate for S2 on 471 cameras.
- Then run the full suite twice and STOP with the next free D number for the Owner.

**Wording in every output:** "candidate", "experimental", "synthetic-data evaluation"; tuning results are "diagnostic, not reported results"; never "validated".

---

#### 3. Register traceability (A1–I4 → this decision)

| Register | Where handled |
|---|---|
| A1–A5, B1–B12 | Not affected. RQ1-only; MSHA excluded; E2 measurement-only |
| C1–C13 | §1.3–1.6 (values revised from the register's "retain" where the review found a reason) |
| D1, D2 | §1.3 T24 row |
| D3 | §1.5 (ByteTrack; OC-SORT not compared) |
| D4 | STEP 3–4 (stitching chosen by tracking measures; N4 unchanged) |
| D5–D8 | Unchanged deferrals |
| E1–E6 | Not in v2; fine-tuning after 1 Dec. **E2 data roles remain UNDECIDED** (Owner withdrawal stands); the partner memo is a separate document |
| F1–F3 | §1.6–1.7 |
| G1–G3, H1–H4 | Deferred; not test blockers |
| I1–I4 | Wording rules above. The report names which camera set each pilot number uses (0.11 / 0.22 = all pilot cameras, 282 references; 0.10 / 0.17 = 96 tuning cameras) |

#### 4. Limitations to carry into the paper (from this review)

1. The 1.5 s anchor and the walking-pace braking figure come from road traffic and vehicle inspection rules. They are not validated for warehouses.
2. SDG forklifts move at ≤ about 0.75 m/s. e_dec and the forklift side of the contact cue cannot fire, and R4 adds little beyond R3.
3. Speed error (about 0.5 m/s, P5–P95) is larger than v_min, so the H/O split is unreliable on camera footage.
4. Position error is about the size of d_nm, so NM-by-distance on camera footage is noisy.
5. k_σ and the borderline flags are inert while σ is not estimated (to be confirmed in STEP 0).
6. e_turn also fires on routine corner turns.
7. GV-04 is circular. The footprints may exclude forks; carried loads are excluded.
8. OC-SORT was not compared. Tracker precision is known on SDG only.
9. No NM, UD or CT references exist on synthetic data, so those labels are demo-workflow output, not measured accuracy.
10. NM, UD and CT labels can only be checked by managers, and that check has not been validated (G1–G3 deferred).

## D-62 (2026-11-25) — STOP after D-60 STEP 4: the Owner runs the Colab equivalence check        status: DECIDED (26 Nov 2026): equivalence PASS; tier-1 run skipped (D-63 ruling 5)
Task: T-26c (D-60 STEPS 0–4)   Blocking: T-26g (STEP 5) and every use of tier-1 detections; nothing else (independent of D-61)
Question: the Colab package is ready. Please run it as described in **`research/colab/HOWTO.md`**.
- **Upload size:** **5.94 GB** in total.
  - Equivalence check: 2 tuning videos, 34,708,143 bytes (0.03 GB), list in `research/colab/equivalence_manifest.json`.
  - Tier 1: 45 videos, 5,908,702,565 bytes (5.91 GB), list in `research/colab/tier1_manifest.json`.
  - The notebook also downloads the two weight files (0.38 GB) once into Drive.
- **Order:**
  1. Run the 2-camera equivalence check first, and send back `out/colab/equivalence/`.
  2. The agent compares it with the stored CPU S2 against C1–C3 (D-60 STEP 4 (c), not loosened) and reports pass or fail.
  3. Only after a pass, run tier 1 and send back `out/colab/tier1/`.
- **Done so far:**
  - S0/S1 of the 11 D-59 scenes: 118 recordings, all calibrated, every frame eligible.
  - X0b-A1 frozen: art_xu3yvoyvpsukx257kmo5p37zxs, test_layout_holdout 45 recordings / 6 groups, reserve 73 / 1; X0b unchanged.
  - X0c: 0 violations.
- **For review:** AR-70 (D-60 representation). In particular:
  - item 3: the per-layout grouping, stricter than T14.1;
  - item 5: an R-2 gate for `test_layout_holdout` is needed before T-26e;
  - item 6: the equivalence readings.
- **One order deviation:** STEP 3 was frozen before the S1 decode of STEP 2 finished. The freeze reads S0 only.
Agent's recommendation: none; the Owner runs the check.
Owner decision (26 Nov 2026): the Owner ran the 2-camera equivalence job on Colab and placed `out/colab/equivalence/` on the laptop. The tier-1 run (order 3) is skipped before 1 Dec 2026 (D-63 ruling 5, CR-039 DEFERRED).
**Result (D-63 STEP 4): PASS** on every reading of C1–C3 (D-60 STEP 4 (c), AR-70 item 6, not loosened); `research/colab/equivalence_result.json`.
- Integrity: the job-manifest SHA-256 equals the one the Colab manifest records. Both output files equal their manifest and `.done.json` SHA-256, and both input-video SHA-256 equal the job manifest. Tesla T4, CUDA 13.0, torch 2.14.1+cu130, ultralytics 8.4.215, av 19.0.2, runner commit 713448e.
- Frames: the CPU and Colab files list the same 300 eligible frames on each camera.
- C1: every CPU box with score ≥ threshold + 0.02 has a one-to-one Colab partner of the same class with IoU ≥ 0.95. There are 0 unmatched boxes, per camera and class.
- C2: the largest P99 of |Δscore| over the matched pairs is 1.43 × 10⁻⁵ (forklift, both cameras, ≥ threshold + 0.02); for person it is 3.0 × 10⁻⁶. The limit is 0.02.
- C3: counts ≥ threshold are equal on every camera and class. Person: 243 / 243 (ceiling) and 302 / 302 (eye level). Forklift: 225 / 225 and 92 / 92. Both cameras together: 545 / 545 and 317 / 317.
- Timing: 27.9 s for 600 frames, so 0.047 s per frame including decoding.



## D-63 (2026-11-26) — STOP after D-61 STEPS 4–6: pre-registration v2 frozen; test readiness prepared        status: DECIDED (26 Nov 2026)
Task: T-28e, T-28f, T-28t (D-61 STEPS 4–6)   Blocking: the reporting-camera run (D-61 §1.7 order 1), the X0b test run (order 2, before 1 Dec 2026), the window lock; nothing else (independent of D-62)
Question: pre-registration v2 is frozen (`docs/preregistration_v2_FROZEN.md`, `docs/preregistration/freeze_record_v2.json`, frozen_utc 2026-11-26T14:29:25Z, analysis commit 226ea7b). Results only. Status: candidate, experimental, synthetic-data evaluation; tuning results are diagnostic, not reported results.
- **STEP 0 findings (details in the Progress log, 26 Nov):**
  1. Not all held data is 30 fps. The Mendeley clips run at about 25 fps. Every v2 recording is 30 fps, but g_max in frames is ambiguous off 30 fps: **CR-038**.
  2. `speed_sigma_mps` is non-null on the detector path, so `speed_near_v_min` fires (313 of 450 C-v2 episodes). σ_c and minclr σ are null, so `clearance_within_k_sigma` never fires. Limitation 5 is corrected in the pre-registration.
  3. Under `review_route`, an O episode is routed in the OI-1 case **and whenever it carries IE**. In T23, O episodes never reach a manager.
- **STEP 4 (116 tuning cameras; diagnostic v2 references; selects nothing):**
  - C-v2+T25: EV-M1 / EV-M2 **0.733 / 0.620** (ceiling 1.000 / 0.771, eye level 0.500 / 0.463).
  - A+T25: **1.000 / 0.975**.
  - **No event was joined** (n_members 1 everywhere, unobserved_gap_s 0). With g_max 45 a POW break needs a gap of at least 46 frames (1.53 s), which exceeds m_gap_s 1.5 s, so **T25.2 can never join under v2**. Same-unit splits across POWs remain: 12 on the detector path, 3 on A.
  - IE share caused by g_max 45: detector path +0.065 (0.788 against 0.723 at g_max 15); A +0.000.
- **STEP 5:**
  - v2 references from simulator truth: tuning 116, reporting 110, test 471 cameras (473 references). Built twice, identical on 697 of 697.
  - The freeze record was built twice and is byte-identical.
  - **SmartSpaces references are not built (CR-039).** The T21 amendment promised for v2 (D-40 item 3) does not exist, so the tier-1 evaluation is blocked.
- **STEP 6 readiness** (`docs/preregistration/test_readiness_v2.json`):
  - pass: X0c (art_2wiixxn5…, 0 violations); windows lockable; freeze record reproducible; test run IDs and hashes equal X0b v1 (48 runs, 471 cameras); weights hashed; licence rows present;
  - **open:** Colab estimate for S2 on 471 cameras. CPU ≈ 15.2 h; GPU time unknown until D-62 returns.
- **For decision or review:**
  1. The definition of `lock_sha256`, proposed in AR-71 item 11 (`window_lock_proposal_v2.json`). Then the lock time.
  2. Whether T25.2 being structurally inert under v2 is intended (both values are the Owner's; the agent changed nothing).
  3. The T25.1 values were selected at g_max 15 (D-58 STEP 3 as written).
  4. CR-038, CR-039, AR-71.
  5. Go-ahead for the reporting-camera run. It needs S2 on the 110 reporting cameras: about 3.6 h CPU (33,000 frames × 0.388 s), or Colab after D-62.
Agent's recommendation: none; the Owner and the Architect decide.
Owner decision (D-63, 26 Nov 2026): rulings on the v2 freeze stop; rationale addendum; window lock; reporting run; test detections. Source: the Owner and Architect review of the D-63 stop (commit 309408d), 26 Nov 2026, and the literature report `reports/v2_parameter_rationale_2026-11-26.md` (project document). Pasting it = Owner approval of the rulings and the steps. Nothing in this decision changes a frozen number; `docs/preregistration_v2_FROZEN.md` and `freeze_record_v2.json` stay byte-identical. §1 verbatim (headings demoted to sit inside this entry); the §3 addendum text is in `docs/preregistration/v2_rationale_addendum_D63.md`:

#### 1. Rulings

1. **Window lock: AR-71 item 11 is accepted as the definition of `lock_sha256`.** For each window of V0 `m1a-sdg-test`, the hash is the SHA-256 of the JCS form of:
   - the window's natural key and bounds;
   - the reference-set label;
   - the camera's v2 reference S5 (ID and payload hash);
   - the reference entries overlapping [t_start, t_guard_end).

   The lock is applied in STEP 3, before any S3 or later stage on test.

2. **T25.2 is inert by design under v2.**
   - With g_max = m_gap_s = 1.5 s, a POW break needs a gap above 1.5 s, while a join needs one ≤ 1.5 s, so no join can occur.
   - A track that changes ID after a gap is handled by T25.1 stitching, after which the gap is bridged. Every gap ≤ 1.5 s is bridged; every longer gap separates two encounters by definition (D-61 §1.3).
   - Values are unchanged. The code stays; `join_across_pow` stays true in the configuration. Record T25.2 as "inert under v2" in the limitations and the methods text.

3. **The T25.1 stitching selection stands.** It was selected by IDF1 on S3 points (`d58_stitch_grid.json`: "IDF1 at iou_cm 0.5 over every S3 point"). g_max acts only after tracking, so the selection does not depend on it.
   - Limitation to state: the selected T_s = 5 s is the top of the grid, so longer gaps were not tried.

4. **CR-038: reading (b).** g_max means 1.5 s and is converted per recording as ⌊1.5 / δ_nom + 1e-9⌋, as m_gap_s is.
   - At 30 fps this equals 45 frames. Every v2 recording is 30 fps, so no v2 configuration ID, artifact or result changes.
   - The seconds-valued representation is implemented only before the first S4 on a recording that is not 30 fps, under its own CR. **Do not change any v2 configuration now.**
   - CR-038 status: DECIDED (reading b; implementation deferred).

5. **CR-039: tier 1 is deferred past 1 Dec 2026.**
   - The T21 jointly-visible amendment for SmartSpaces is not written for this submission.
   - SmartSpaces event-level results are explicitly excluded from the submission, with the reason stated (register D6).
   - The tier-1 Colab run (D-62 order 3) is not needed before 1 Dec; skip it.
   - CR-039 status: DEFERRED.
   - The D-60 tier-1 manifest, X0b-A1 and the reserve stay frozen and untouched.

6. **AR-71 items 1–10 are accepted.** Item 11 is accepted under ruling 1.

7. **Reporting cameras: go-ahead.** Run once, on the frozen v2 configuration (D-61 §1.7, order 1), after the D-62 equivalence check passes.

8. **Test detections may run early.** S2 (detection only) on the 471 test cameras may run on Colab in the same session as the reporting S2.
   - The test S2 output is hashed on arrival and otherwise left untouched: not opened, counted, plotted or summarised.
   - No S3 or later stage runs on test before:
     - the reporting run has finished (STEP 5);
     - the window lock is applied (STEP 3).
   - This reorders compute only; the order in which results are produced and seen stays reporting → test.

9. **The rationale addendum** (STEP 2) corrects the stated *reasons* for twelve v2 values, using the literature report. It changes no value, grid, rule or criterion. It is recorded before any reporting or test result exists. The frozen file is not edited.

##### Six-question check (master instruction §10)

1. **Research objective:** no change.
2. **Meaning of measurements:** no change. Rulings 2–4 change no value. CR-038 keeps the meaning "1.5 s". Ruling 5 removes a result set from the submission, and that is stated, not hidden.
3. **Validation independence:** strengthened. The lock is applied before test S3. Test S2 output is sealed until after the reporting run. Every result is produced once.
4. **Permitted claims:** wording becomes more cautious (addendum). No SmartSpaces event-level claim.
5. **Scope:** reduced (tier 1 deferred).
6. **Type of decision:** scientific (rulings 1, 2, 4, 5, 8, 9) and representation (rulings 3, 6). **E2 is not affected.**


## D-64 (2026-11-26) — STOP after D-63 STEP 4: the Owner runs the Colab job `reporting_test`; reporting S2 already exists        status: DECIDED (26 Nov 2026): option (a)
Task: T-29q (D-63 STEPS 0–4)   Blocking: T-29p (STEP 5, reporting run), T-29h (STEP 6), T-29t (STEP 7)
Question: D-63 STEPS 0–4 are done. The Colab job is ready (**`research/colab/HOWTO.md`, section "D-63"**). **But first, a correction to my D-63 stop report.**

**Correction (item 5 of the D-63 stop was wrong).** I wrote that the reporting run "needs S2 on the 110 reporting cameras: about 3.6 h CPU". In fact, **stored CPU S2 already exists for all 110 reporting cameras.** It comes from the T-25p pilot of 19 Nov, which covered the 206 SDG validation cameras outside the probe, so every reporting camera.
- Its S2 configuration IDs are exactly the frozen v2 detector IDs, `inf_cetfxtbdg72cqgfm6teibcxsyd` and `mdl_ty3jrnwz5jjdv56nwtkcos4yqs` (110 of 110), the IDs `freeze_record_v2.json` lists.
- Its frame lists equal the S1 eligible frames (110 of 110).
- The 116 tuning cameras use the same pilot S2 lineage.
- The v1 pilot also ran S3–S5 on these cameras before the D-53 tuning/reporting split. Those pilot numbers were reported over all pilot cameras, and that is already disclosed (register I1–I4).
- Ruling 7 and STEP 4 rest on my wrong figure, so I have not started the reporting run. The choice is yours.

**Done in this session (D-63 STEPS 0–4):**
- STEP 1: records (D-63 DECIDED; CR-038 DECIDED (b), deferred; CR-039 DEFERRED; AR-71 ACCEPTED). Limitations 16–19 are in the Progress log and in `research/v2/reporting_plan.md`.
- STEP 2: addendum `docs/preregistration/v2_rationale_addendum_D63.md` (SHA-256 43e937e5…, commit e70f28b, 2026-11-26T15:43:35Z); record `v2_addendum_record.json`. The frozen files are byte-identical.
- STEP 3: window lock. 471 of 471 windows of V0 `m1a-sdg-test` are locked in the new artifact **art_venollyxzeuqvumbo7jow2vtjt** (locked_utc 2026-11-26T15:47:13Z). It was built twice, and the ID, payload and files are identical. Every lock_sha256 equals the D-61 proposal. V0 is unchanged, and VR-E-054 now passes. Record: `docs/preregistration/window_lock_v2.json`. Representation: AR-72 (proposed).
- STEP 4: D-62 DECIDED, **PASS** (details there). Colab job `reporting_test`, `research/colab/reporting_test_manifest.json`:
  - **581 videos, 9.51 GB upload**: reporting 110 (1.81 GB), test 471 (7.70 GB, of which 30 are under `data/derived/sdg_rgb_sample/`, as S0 registers them);
  - **Drive space about 9.9 GB** (15.8 GB if the tier-1 videos are also in Drive: remove them first on a 15 GB plan);
  - **runtime about 2.3 h on a T4** (0.4 h reporting, 1.8 h test), from the equivalence timing.
  - The upload links are already staged under `out/colab_upload/rq1_colab/data/` (upload `raw/sdg` and `derived` only).
  - The tier-1 skip note is in the HOWTO.

**Options for the reporting S2:**
- **(a) Use the stored CPU S2 for the reporting run.** It has the frozen v2 S2 IDs and the same lineage as the tuning results. STEP 5 can start at once on your word, with no upload for it. Colab then runs **test only**: 471 videos, 7.70 GB, about 1.8 h. I would add a test-only manifest (`test_manifest.json`, same cameras and format) before you upload.
- **(b) As ordered.** Colab S2 for all 581. The reporting run uses the new GPU S2, which is equivalent under D-62 but not byte-identical to the stored S2. The stored reporting S2 stays unused.
- (A CPU re-run of the reporting S2 is not needed under either option.)

Agent's recommendation: (a). The frozen v2 package was specified on this S2 lineage. A second S2 adds no independence, because detection does not depend on anything seen. It also leaves two S2 sets for the same cameras. You decide.
Owner decision (D-64, 26 Nov 2026): "D-64: option (a), add the test-only manifest".
- The reporting run (D-63 STEP 5) uses the stored CPU S2 of the 110 reporting cameras (T-25p pilot; frozen v2 S2 IDs `inf_cetfxtbdg72cqgfm6teibcxsyd` / `mdl_ty3jrnwz5jjdv56nwtkcos4yqs`). No Colab S2 is made for the reporting cameras.
- Colab runs the 471 test cameras only: job `test`, `research/colab/test_manifest.json` (471 videos, 7,703,586,524 bytes, 141,190 frames; entry for entry the test set of `reporting_test_manifest.json`, same detector block). Staged in the new folder `out/colab_upload_test/rq1_colab/data/` (441 `raw/sdg`, 30 `derived/sdg_rgb_sample`). HOWTO section "D-64": Drive space about 8.1 GB, about 1.8 h on a T4.
- `reporting_test` is kept as the D-63 STEP 4 record and marked "do not run". The D-63 upload approval (WORKPLAN §0) covers the test videos, a subset of it.
