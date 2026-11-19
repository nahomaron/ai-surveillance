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

## D-45 (2026-11-19) — STOP after the T-22 zero-shot probe        status: OPEN
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
Owner decision: ______

