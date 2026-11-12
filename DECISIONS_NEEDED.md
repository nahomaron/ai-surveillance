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

## D-10 (2026-11-12) — T9 edge readings and the episode exposure fields        status: OPEN
Task: T-09   Blocking: the S5 artifact (episode rows) and per-label event counts; T-14 and T-15 when they read episode exposure
Question: (1) Four T9 passages have two readings that give different numbers in cases no Appendix N fixture covers: the closing-rate window, R5 on frames where a track is lost, the contact cue when R5 is off, and which frames set borderline flags. The agent implemented the first reading of each, provisionally. (2) The episode exposure fields (`exp_*`), `support_detected_frac` and per-label event counts are named in §5.6 but not defined, so episode rows cannot be written.
Options: (a) Approve the implemented readings (CR-009 part 1) and the proposed definitions (part 2, items 5a–5f and 6). (b) The Architect supplies other text. (c) Approve some items and return others.
Agent's recommendation: (a). Part 2 reuses the S4 exposure-profile definitions and lifecycle step 4. Details are in CR-009.
Owner decision: ______
