# Package D.1 — Evaluation and Measurement Validity Correction Addendum (RQ1)

**Date:** 7 November 2026
**Status:** Correction addendum to Packages C.1 and D, responding to the user's conditional approval of 7 November 2026. Correction gate result in Section 9.
**Scope:** RQ1 only — a hazard observation and measurement instrument. No RQ2 indicator formula, safety score, weighting, OSHA linkage or establishment ranking.
**Precedence after this addendum:** D.1 > C.1 > D > C > B.1 > B > A.1 > A for the sections listed in Section 10.
**Open user decisions carried forward:** D-4, D-5 and C2–C6 have no specific answers yet. Dependent items use the working positions from the RQ1 handoff brief and are marked *provisional (pending D-x)*.

Conventions as in C.1: parameters are italic names without values; nothing below is an empirical result.

---

## 1. Correction 1 — Event-classification logic

### 1.1 The defect

C.1 §3.2 defines O = `P ∧ ¬X ∧ ¬C_any`, H = `X`, PC = `C_any`, and then states that O, H and PC can co-occur. Under those definitions O is logically incompatible with H and with PC. The definitions are correct; the co-occurrence sentence is wrong. The meanings of O, H and PC are **not** changed here.

### 1.2 Episode-level evaluation (previously implicit)

Flags are per frame; labels are per episode. Each label is evaluated over named intervals:

| Symbol | Interval | Definition |
|---|---|---|
| *I* | Episode interval [open, close) | Trigger interval after the C.1 §2.2 lifecycle |
| *I⁺* | Attribute interval [open, min(close + *w_post*, POW end)) | Used for `E` and contact state (C.1 §2.2 step 4) |
| `P_ep`, `X_ep`, `C_ep` | *I* | ∃ frame in *I* with `P`, `X`, `C_any` true respectively |
| `E_ep` | *I⁺* | ∃ frame in *I⁺* with `E` true |
| `minclr` | *I* | Minimum clearance over frames in *I* with measurable clearance; `unknown` if none |
| `K` | — | Proximity-severity condition `E_ep ∨ (minclr < d_nm)`, evaluated in three-valued (Kleene) logic. `E_ep` is `unknown` when evasive action cannot be assessed (`Q` insufficient over the relevant part of *I⁺*); `(minclr < d_nm)` is `unknown` when `minclr` is unknown. `K = true` if either operand is true; `K = false` only if both are false; otherwise `unknown` |

Per-frame identity carried over from B.1/C.1: `X(t) = P(t) ∧ M(t)`. Hence `X_ep ⇒ P_ep`.

### 1.3 Corrected classification matrix

Labels fall into three groups with different logical structure.

| Group | Labels | Structure |
|---|---|---|
| G1 Exposure type | O, H, PC | **O is exclusive** of H and PC. **H and PC may coexist.** Every episode has at least one G1 label (the trigger `T = P ∨ X ∨ C_any` guarantees it). |
| G2 Contact outcome | NM, UD, CT | **Mutually exclusive; at most one.** May be empty. |
| G3 Qualifier | IE | Independent; may accompany any G1/G2 combination. |

| Label | Corrected rule |
|---|---|
| O | `P_ep ∧ ¬X_ep ∧ ¬C_ep` |
| H | `X_ep` |
| PC | `C_ep` |
| NM | `(H ∨ PC) ∧ K = true ∧ contact = none_observed` |
| UD | `(H ∨ PC) ∧ K = true ∧ contact = undetermined` |
| CT | `contact = suspected` (independent of G1, as in C.1) |
| IE | `Q` insufficient at the closest-approach frame, **or** insufficient for > *o_max* of *I*, **or** contact = `not_assessable`, **or** `K = unknown` while `(H ∨ PC)` |

The last IE clause is new: it prevents an episode whose near-miss condition cannot be evaluated from silently becoming "H only".

### 1.4 Testable invariants

| ID | Invariant |
|---|---|
| CL-INV-01 | `O ⇔ (P_ep ∧ ¬H ∧ ¬PC)` |
| CL-INV-02 | `O ∨ H ∨ PC` for every episode |
| CL-INV-03 | `H ⇒ P_ep` |
| CL-INV-04 | At most one of NM, UD, CT |
| CL-INV-05 | `NM ⇒ contact = none_observed`; `UD ⇒ contact = undetermined`; `CT ⇔ contact = suspected` |
| CL-INV-06 | `(NM ∨ UD) ⇒ (H ∨ PC)` |
| CL-INV-07 | `contact = not_assessable ⇒ IE ∧ ¬NM ∧ ¬UD ∧ ¬CT` |
| CL-INV-08 | `K = unknown ∧ (H ∨ PC) ⇒ IE ∧ ¬NM ∧ ¬UD` |
| CL-INV-09 | Labels are a pure function of (episode flags, contact state, `minclr`, parameters); recomputation from stored inputs reproduces stored labels |
| CL-INV-10 | No automated field anywhere takes the value "observed contact" |
| CL-INV-11 | The summary label (CT > UD > NM > PC > H > O) is derivable from the label set and never stored without it |

### 1.5 Truth table (representative)

| # | Scenario | `P_ep` | `X_ep` | `C_ep` | `E_ep` | `minclr` vs *d_nm* | Contact | `Q` at CA | Labels |
|---|---|---|---|---|---|---|---|---|---|
| T1 | Walk past a parked forklift | T | F | F | F | ≥ | none_observed | ok | O |
| T2 | Worker beside a moving forklift | T | T | F | F | ≥ | none_observed | ok | H |
| T3 | Distant fast approach, paths cross, no proximity yet | F | F | T | F | ≥ (see note) | none_observed | ok | PC |
| T4 | Moving forklift, predicted crossing, close | T | T | T | F | ≥ | none_observed | ok | H, PC |
| T5 | As T2 plus worker dodges | T | T | F | T | ≥ | none_observed | ok | H, NM |
| T6 | Moving forklift, footprints overlap, no cue | T | T | F | F | < | undetermined | ok | H, UD |
| T7 | Moving forklift, overlap + abrupt stop | T | T | F | any | < | suspected | ok | H, CT |
| T8 | Footprint overlap with stationary forklift, no cue | T | F | F | F | < | undetermined | ok | O (contact state stored; routed to review, §1.6) |
| T9 | Stationary forklift, overlap + cue | T | F | F | F | < | suspected | ok | O, CT |
| T10 | Path conflict predicted while visible; approach then occluded, closest approach not visible | F | F | T | unknown | ≥ (from visible frames) | undetermined | insufficient | PC, IE (no UD: `K` unknown) |
| T11 | Proximity while moving, then no usable frames around closest approach | T | T | F | unknown | ≥ (from measurable frames) | not_assessable | insufficient | H, IE |

Note on T3: `minclr` is computed over all frames in *I* with measurable clearance, not only `P` frames. In T3 clearance is measurable, so `minclr ≥ d_nm` and `K = false`; the episode is PC only. `K = unknown` arises when evasive action cannot be assessed and the measurable clearance does not already make `K` true (T10, T11), or when clearance is unmeasurable throughout *I* and no evasive action is observed.

### 1.6 Consequence recorded, not changed

T8 shows that, under the unchanged definitions, a footprint overlap with a **stationary** forklift without a contact cue yields only O, with `contact_state = undetermined`. This is a deliberate consequence of keeping meanings. To avoid hiding such cases, review routing (not labelling) is extended: **any episode with `contact_state ∈ {undetermined, suspected}` enters the candidate review queue regardless of labels.** Whether stationary-forklift overlaps deserve their own label is listed as open item OI-1 for the user.

### 1.7 Impact, data requirements, acceptance, assumptions

- **Impacted:** C.1 §3.2 (co-occurrence sentence replaced by §1.3), C.1 §3.3 (IE clause added), D §3.4 EV-M12 (κ computed per G2 group, with G1 agreement reported separately).
- **Data requirements:** episode records store `P_ep`, `X_ep`, `C_ep`, `E_ep`, `minclr` (nullable with reason), `K` (true/false/unknown), contact state, each label as a separate boolean, and the summary label.
- **Acceptance:** D1-AC-01 every truth-table row is a fixture producing exactly the listed labels; D1-AC-02 CL-INV-01–11 hold on all episodes of every test run (property-based test over random flag sequences).
- **Assumptions:** `M` is defined from speed with σ; borderline `M` frames are flagged (C.1 §6.3) but not re-labelled.

---

## 2. Correction 2 — Observation-denominator bias

### 2.1 The defect

POWs exist only where both a person and a forklift are detected and tracked. A perception or tracking failure removes observation time from every exposure measure, and the loss is invisible in the system's own outputs. Measured exposure can therefore fall because the detector got worse, not because exposure fell.

### 2.2 Four distinct quantities

| Layer | Quantity | Source | Independent of the detector? | Exists where |
|---|---|---|---|---|
| L-COV Camera coverage | When and where usable footage exists | Decode checks and image-quality tests on frames (freeze, black, blur, exposure, compression damage); declared field of view | **Yes** — must not use detections | All footage |
| L-REF Actual observable activity | Persons, forklifts, co-presence and interactions visible to annotators | Exhaustive A/B annotation | Yes | Reference windows only |
| L-AI AI-detected activity | Tracks, POWs, GPWs | S2–S4 | No | All usable footage |
| L-MEAS Measured exposure | Exposure profiles, episode measures | S4–S5 on L-AI | No | All usable footage |

Time quantities preserved separately, never substituted for one another:

| Quantity | AI version | Reference version |
|---|---|---|
| Monitored camera-hours | — (L-COV only) | Annotated unusable spans (MR-06) |
| Worker observation time | Σ person track time | Σ annotated person-visible time |
| Forklift observed time (and moving time) | Σ forklift track time | Σ annotated forklift-visible time |
| Pair interaction (co-presence) time | Σ POW time | Σ annotated person–forklift co-visible time per pair |

### 2.3 Three activity states (never merged)

| State | Meaning | Who may assert it |
|---|---|---|
| `unobserved` | No usable footage (not recorded, unusable, outside field of view) | L-COV |
| `observed_no_detection` | Usable footage; the system found no relevant objects or pairs | L-AI |
| `reference_verified_absent` | Inside an exhaustively annotated, assessable reference window, annotators recorded no relevant objects or no interaction | L-REF only |

The system never emits `reference_verified_absent`. `observed_no_detection` is never exported or reported as zero exposure.

### 2.4 Completeness measurement against reference windows

Annotation requirement added to C.1 §4.1: reference windows annotate **every person and forklift present** (presence intervals per object, with keyframe boxes at interval *k_kf* and cross-camera identity), not only interactions. This is what makes completeness measurable.

| ID | Metric | Definition (per window, aggregated with §4 weights) |
|---|---|---|
| CM-01 | Person track-time completeness | AI person track time matched to reference persons ÷ reference person-visible time |
| CM-02 | Forklift track-time completeness | Same for forklifts; also for reference forklift moving time |
| CM-03 | Co-presence time completeness | Reference pair co-visible time covered by a POW of the matched pair ÷ reference pair co-visible time |
| CM-04 | Pair completeness | Reference pairs with ≥ 1 POW ÷ reference pairs (missed co-presence count reported) |
| CM-05 | Spurious pair time | POW time not matching any reference pair ÷ POW time |
| CM-06 | Exposure-duration error | AI time-in-band minus B-layer time-in-band, per pair and per window; bias and limits of agreement |
| CM-07 | Fragmentation | POWs per reference pair co-presence interval |
| CM-08 | Unknown-clearance share | Time inside POWs where clearance is unmeasurable ÷ POW time |

Object matching for CM-01/02: per frame, Hungarian matching of AI boxes to reference keyframe boxes (interpolated between keyframes) at IoU ≥ *iou_cm*; track time counts as matched only when the AI track maps to the same reference identity for the frame. Interpolation error is a declared limitation; keyframe density *k_kf* is chosen in the pilot.

All CM metrics are reported with intervals (§4.3), by stratum (distance, viewpoint, occlusion, crowding, lighting, data origin), and alongside L-MEAS outputs in every report.

### 2.5 What RQ1 does and does not do with completeness

RQ1 **reports** completeness ratios and their uncertainty with each exposure measure, and exports them (Package E). RQ1 does **not** adjust, impute or rescale exposure for missed activity, and does not compute rates. Any completeness adjustment is an RQ2 design decision.

### 2.6 Impact, data requirements, acceptance, assumptions

- **Impacted:** C.1 §4.1 (object-presence annotation added), C.1 §6.2 (four layers; AI vs reference versions), D §4 MR-05 (replaced by CM-01–08 for exposure completeness), D §8 (completeness criterion uses CM metrics).
- **Data requirements:** detector-independent coverage segments; `ai_activity_state` per usable segment; reference object-presence and co-presence tables; completeness records per window.
- **Acceptance:** D1-AC-03 coverage states are computed with the detector disabled and are byte-identical with it enabled; D1-AC-04 a fixture where the detector misses a person for 40% of reference co-presence yields CM-03 ≈ 0.6 (within interpolation tolerance) and unchanged L-COV hours; D1-AC-05 no report table shows an L-MEAS quantity without its CM companion.
- **Assumptions:** annotators see what is visible on screen; occluded persons that annotators cannot see are outside "observable activity" and are a further, unmeasured gap (stated in every report).
- **Cost risk:** object-presence annotation increases window labour. Mitigation: presence intervals plus sparse keyframes rather than per-frame boxes; simulator truth replaces it on synthetic data.

---

## 3. Correction 3 — Leakage-safe partitioning

### 3.1 The defect

D §2.2 lists "session × camera" as a staged-data partition unit. Two cameras recording the same physical event could then sit in training and test, inflating apparent generalization.

### 3.2 Leakage groups

Partition assignment is made on **leakage groups**, the connected components of a graph whose nodes are recordings and whose edges are any of:

| Edge | Example |
|---|---|
| Same session (concurrent recording at one site) | All cameras of a staged session |
| Same physical interaction (reference cross-camera identity) | Two views of one approach |
| Same source scene or run | SDG run's 10 views; SmartSpaces scene and its re-renders |
| Same scripted scenario instance re-performed with identical actors and layout within a day | Staged repeats *(definition provisional, pending D-4)* |
| Shared frames used for detector fine-tuning or parameter tuning | Any image of a session in a training manifest |

**Rule PART-01:** for T1, every leakage group lies entirely in one partition. This replaces "session × camera" with "session (all cameras)" as the minimum staged-data unit.

### 3.3 Generalization tiers, restated

| Tier | Design | Shared content | Claim permitted |
|---|---|---|---|
| T1 Unseen events/sessions | Partition by leakage group | None | Performance on new sessions in represented conditions |
| T2a Unseen viewpoints, strict | Test cameras occupy positions or geometries absent from training **and** belong to leakage groups absent from training | None | Robustness to the tested viewpoint change on new events |
| T2b Unseen viewpoints, shared content | Train on some cameras of a session, test on other cameras of the **same** sessions | **Disclosed:** same physical events | Viewpoint transfer only; **not** independent-event or independent-site generalization |
| T3 Independent facilities | Site never used in development | None | Generalization to that site |

Consequences: SDG ceiling-vs-eye-level views of the same runs and SmartSpaces camera subsets of the same scenes are **T2b**, not T2a, and every result table carries `shared_scene_content = true`. T2a on synthetic data requires disjoint runs/scenes **and** disjoint camera placements.

### 3.4 Impact, data requirements, acceptance, assumptions

- **Impacted:** D §2.2 (staged unit), D §2.3 (leakage check runs on leakage groups), D §3.6 (T2 split into T2a/T2b).
- **Data requirements:** recording-level links (session, scene/run, physical-interaction identity, training use); split manifest records leakage-group IDs and tier design with disclosure flag.
- **Acceptance:** D1-AC-06 automated check finds zero leakage groups spanning partitions for T1/T2a; D1-AC-07 any T2b report lacking the disclosure flag fails report generation; D1-AC-08 seeded fixture with one interaction filmed by two cameras placed in different partitions is rejected.
- **Assumptions:** physical-interaction links between sessions are rare; if sessions share actors and layouts, sensitivity analysis groups by day.

---

## 4. Correction 4 — Sampling design and estimation

### 4.1 Sampling frame

- The frame is the set of all **non-overlapping windows** of length *w_ref* tiling the recorded timeline of each *camera group* (all cameras of a session whose views may overlap). Windows are defined in session time and annotated on **all cameras of the group** so that cross-camera identity and deduplication are observable.
- Windows partition the recorded timeline, so every recorded second belongs to exactly one window. Unusable footage stays in the frame (its time is annotated as unusable).
- **Boundary rule:** a reference event belongs to the window containing its reference onset. Annotators annotate a guard margin *w_guard* after the window end so events that start inside are fully bounded. System events are assigned by their onset; matching uses the guarded interval. Durations are clipped to the window for duration totals.

### 4.2 Sample types

| Type | Selection | Known inclusion probability | Supports |
|---|---|---|---|
| **RES** Representative evaluation sample | Stratified simple random sampling without replacement; strata use **only pre-system metadata** (data origin, site, session, camera group, time block, generation batch) or a pre-declared detector-independent activity proxy | Yes: π = *n_h* / *N_h* | Headline metrics; design-weighted totals, durations and per-hour rates **for the sampled recording period** |
| **ECS** Enriched challenge set | Rare-event oversampling by scenario request, annotator search, or system candidates | No (or not design-based) | Conditional performance on those scenario types only |

Oversampling active strata is allowed **inside RES** when the stratifier is detector-independent and π is recorded; it remains RES and is weighted. Any selection that uses system outputs makes the window ECS.

ECS results are never pooled with RES, never enter headline metrics, and never enter frequency, duration or per-hour aggregates.

### 4.3 Estimators

Weights *wᵢ* = 1/πᵢ.

| Quantity | Estimator |
|---|---|
| Total reference events in the frame | Horvitz–Thompson Σ *wᵢ yᵢ* |
| Reference events per usable hour (frame) | Ratio Σ *wᵢ yᵢ* / Σ *wᵢ uᵢ* |
| Headline recall | Σ *wᵢ mᵢ* / Σ *wᵢ aᵢ* (matched / assessable references) |
| Headline precision | Σ *wᵢ m⁽ˢ⁾ᵢ* / Σ *wᵢ sᵢ* (matched / all non-abstained system events) |
| False-alert burden | Σ *wᵢ fᵢ* / Σ *wᵢ uᵢ* |
| Exposure durations | Weighted totals and ratios of reference and AI durations |

Unweighted values are reported beside weighted ones. The Kish effective sample size from unequal weights is reported and used in the D §2.6 interval planning.

**Two inference targets, two variance methods:**

| Target | Variance |
|---|---|
| A. Describe the sampled recording period (sessions fixed) | Stratified bootstrap of windows within strata |
| B. Expected performance on new sessions like these | Cluster bootstrap over independence units (leakage groups), carrying weights |

### 4.4 When aggregates describe something, and when they do not

| Aggregate | Describes the sampled recording period? | Describes the establishment? |
|---|---|---|
| RES-weighted counts, durations, per-hour rates on natural real footage | Yes, with intervals | **No** — monitored cameras and periods are not a sample of the establishment's activity |
| Same on **staged** real footage | Describes the **staged script**, not workplace frequency | No |
| Same on synthetic footage (SDG, SmartSpaces) | Describes the **generator's scenario design**; SDG near-miss frequencies are design artefacts | No |
| Any ECS aggregate | No | No |
| Per-event metrics (localization, clearance error, contact cross-tab) | Conditional on event type, from either sample | No |

### 4.5 Impact, data requirements, acceptance, assumptions

- **Impacted:** C.1 §4.1 (frame, tiling, boundary rule, sample types), C.1 §4.4 (weighted denominators), D §2.6 (effective sample size), D §3.4 EV-M7 (weighted), D §4 MR-04/MR-05 (RES only), D §7 (two variance methods).
- **Data requirements:** sampling plan record (frame hash, strata, *N_h*, *n_h*, seed, freeze timestamp); per-window stratum, π, weight, sample type; window guard margin; event-to-window assignment.
- **Acceptance:** D1-AC-09 simulation check — on a synthetic population with known totals, the weighted estimator's bootstrap intervals cover the truth at approximately nominal rate across repeated samples; D1-AC-10 report generation refuses to compute frequency, duration or per-hour aggregates from ECS windows; D1-AC-11 frame tiling covers every recorded second exactly once.
- **Assumptions:** windows of length *w_ref* are long relative to typical interactions so boundary assignment errors are rare; measured in the pilot.

---

## 5. Correction 5 — Cross-camera event counting

### 5.1 Physical event identity

| Link state (per episode pair, same configuration) | Required evidence |
|---|---|
| `linked_calibrated` | Both cameras calibrated to one world frame; clocks aligned within *τ_sync* (with σ); time overlap; person and forklift positions agree over the overlap (median Mahalanobis distance using reported σ ≤ *χ²_link*) |
| `possible_duplicate` | No common calibration; declared overlapping fields of view; time overlap within clock uncertainty |
| `distinct` | Non-overlapping fields of view, or time-disjoint beyond clock uncertainty, or calibrated positions incompatible |
| `unknown` | Insufficient metadata to decide |

Every link record keeps its evidence (time offset, position discrepancy, σ, calibration IDs, linkage method version). Per-camera episodes are always retained; linkage never deletes or rewrites them.

**Consistency rule:** if a merge group would contain two episodes from the **same camera** that overlap in time with different POW pairs, it is invalid (they are distinct interactions by construction); the group is split along those episodes and flagged `link_conflict`.

### 5.2 Counting scenarios (replace the min/max range)

| Scenario | Merges | Count equals the number of physical interactions observed **only if** |
|---|---|---|
| S-VIEW | None (per-camera episodes) | Each interaction is seen by one camera only (A3 trivially) and A1 holds |
| S-LINK (default automated count) | `linked_calibrated` groups | A1 + A2 + A3-calibrated hold |
| S-POSS | `linked_calibrated` + `possible_duplicate` groups, pairwise-overlap rule (no transitive chains through non-overlapping members) | A1 + A2 + A3 hold for possible duplicates |

Assumptions: **A1** no episode spans two physical interactions; **A2** no link joins episodes of different interactions; **A3** all episodes of one interaction are linked.

S-VIEW is ≥ S-LINK ≥ S-POSS by construction, but S-POSS is **not** a lower bound on the true count: false merges (e.g., two workers near one forklift seen by overlapping uncalibrated cameras) reduce it below the truth. Scenario values are therefore reported as **labelled alternative counts with their assumptions**, never as a confidence interval or a bound. The word "bound" may be used for a scenario only in a stratum where MR-07 has measured zero A1/A2 violations, and then with that evidence cited.

Physical interactions seen by no camera are counted by none of the scenarios; that gap belongs to completeness (§2), not to deduplication.

### 5.3 Impact, data requirements, acceptance, assumptions

- **Impacted:** C.1 §2.3 (range replaced by scenarios), C.1 C1-AC-04 (expects scenarios), D §4 MR-04 (scenarios vs validated counts), MR-07 (now measures A1, A2, A3 violation rates).
- **Data requirements:** `event_link` records with state and evidence; candidate-event records per scenario; per-scenario count summaries with assumption labels.
- **Acceptance:** D1-AC-12 fixtures: one interaction in two calibrated cameras → S-LINK = 1, S-VIEW = 2; two concurrent interactions in overlapping uncalibrated cameras → S-POSS may be 1 and is reported with assumption A2 flagged unverified; same-camera conflict fixture → `link_conflict`; D1-AC-13 no report or export contains the words "confidence interval" or "bound" attached to scenario counts without MR-07 evidence.
- **Assumptions:** clock alignment σ is measurable for staged collections (provisional, pending D-4).

---

## 6. Correction 6 — Measurement validity and fitness

### 6.1 Five criteria

| Criterion | Question | Evidence in RQ1 |
|---|---|---|
| Technical accuracy | Is the intended physical or temporal quantity computed correctly? | GV-01–08, MR-03, CM-06 against B/A layers |
| Completeness | How much of the observable activity is captured? | CM-01–08, MR-06 |
| Repeatability | Same value under equivalent conditions? | MR-01, MR-02, MR-08–12 |
| Construct validity | Does it plausibly represent the safety construct named? | Definition review (CV-1) and C-layer expert alignment (CV-2) only |
| Comparability | Comparable across periods, camera configurations, sites? | Stratified results; calibration tier; T2a/T3 |

**Construct-validity ceiling in RQ1.** CV-0 none; CV-1 definitional (the measure operationalizes a stated, sourced hazard condition — sources to be cited in the thesis, not asserted here); CV-2 agreement with blinded expert judgment on the same footage; CV-3 association with injury or incident outcomes — **out of RQ1 scope** (RQ3). Accurate proximity duration, for example, is at most CV-1 until experts judge the episodes; it never establishes hazardous exposure by itself.

### 6.2 Status definitions (two axes)

**Measurement status** (accuracy, completeness, repeatability, comparability):

| Status | Rule |
|---|---|
| Technically validated | Accuracy, completeness and repeatability meet pre-registered criteria **on real footage** with intervals; comparability characterized by stratum (or declared non-comparable) |
| Experimental | Evidence only on synthetic data, or criteria met with caveats, or parameter-sensitive (D §4 rule) |
| Unsuitable | Fails a criterion in a way RQ1 cannot repair |
| Not yet assessable | Required evidence not yet produced |

**Construct status:** CV-0 / CV-1 / CV-2, as above. A measure is offered to RQ2 as a *candidate input* only when measurement status = technically validated, with its construct status shown.

### 6.3 Measurement-fitness assessment (current state: no tests run)

| RQ1 output | Accuracy evidence | Completeness evidence | Repeatability evidence | Construct (ceiling in RQ1; what stays unverified) | Comparability | **Current status** | Plausible ceiling in RQ1 *(hypothesis)* |
|---|---|---|---|---|---|---|---|
| Usable monitored camera-time | MR-06 vs annotated unusable spans | N/A (defines scope) | MR-01 | CV-1 as observation scope; says nothing about hazard | Comparable if quality tests identical | Not yet assessable | Technically validated |
| Worker observation time (AI) | CM-01 | CM-01 | MR-01, MR-02 | CV-0 (activity, not hazard) | Viewpoint-dependent | Not yet assessable | Validated on staged real |
| Forklift observed / moving time (AI) | CM-02; GV-07 for moving | CM-02 | MR-01, MR-08 (*v_min*) | CV-1 (activity exposure) | Depends on speed error by viewpoint | Not yet assessable | Experimental → validated if GV-07 met |
| Pair co-presence (POW) time | CM-03, CM-05 | CM-03, CM-04 | MR-01, MR-02 | CV-1 (opportunity for interaction) | Depends on tracking fragmentation | Not yet assessable | Validated on staged real |
| Time in clearance bands | CM-06, GV-01, GV-05 | CM-03, CM-08 | MR-08–MR-10 | CV-1; hazard meaning needs context (barriers, controlled operations) — unverified | Requires same calibration tier and footprint prior | Not yet assessable | Experimental (footprint, calibration sensitivity) |
| Minimum clearance per episode | GV-01, GV-04 | — | MR-09, MR-10 | CV-1 | Calibration tier | Not yet assessable | Experimental |
| Closing rate / time to closest approach | GV-07, GV-08 | — | MR-08 | CV-1 (conflict surrogate) | Horizon and smoothing must match | Not yet assessable | Experimental |
| H / PC episode counts and durations | EV-M1/M2/M8 | CM-04 + recall | MR-08, MR-12 | CV-2 possible via C-layer | Same configuration only | Not yet assessable | Experimental (parameter sensitivity expected) |
| NM / UD / CT candidates | EV-M1/M2, EV-M12 | Recall | MR-08 | CV-2 at most; "candidate", never "occurred" | Same configuration only | Not yet assessable | Experimental; likely high UD share |
| Contact state | EV-M9 | — | MR-01 | CV-1 (uncertainty representation) | — | Not yet assessable | Experimental |
| Evasive-action flag | A-layer onset agreement | Recall of annotated evasions | MR-08 | CV-2 possible | — | Not yet assessable | Experimental |
| Validated event counts | Reference process (κ/α) | Review coverage | Inter-rater agreement | CV-2 | Same protocol, reviewers' expertise | Not yet assessable | Depends on reviewer capacity *(pending D-5)* |
| Event-count scenarios (S-VIEW/LINK/POSS) | MR-07 | — | MR-01 | CV-0 (bookkeeping) | Calibration tier | Not yet assessable | Validated for S-LINK where calibrated |
| Completeness ratios (CM-01–08) | Annotation agreement | — | Annotator agreement | CV-0 (instrument property) | Stratum-specific | Not yet assessable | Validated (they are reference-based) |
| Image-space proximity | GV-06 | — | MR-01 | CV-0 as physical distance | Not comparable across viewpoints | Not yet assessable | **Unsuitable as physical distance** (expected); retained as baseline |
| E2 load elevation state | E2-L1 vs simulator/measured heights | — | MR-01 | CV-1 | — | Not yet assessable | Experimental, conditional |
| E2 footprint-occupancy time | E2-L4 vs measured proxies | Staged only | MR-01 | CV-1; no fall probability or severity | Calibrated staged only | Not yet assessable | Experimental, conditional *(pending D-4)* |

This table replaces D §8.2 as the reporting format; "expected status" values remain hypotheses until tests run.

### 6.4 Impact, data requirements, acceptance, assumptions

- **Impacted:** D §8.1 (seven criteria regrouped into five plus status axes; the seven remain as sub-checks), D §8.2 (replaced), D §9 claims ladder Level 4 (uses measurement status + construct status).
- **Data requirements:** `measurement_fitness` records per output × data origin × stratum, each criterion with status, evidence references and unverified items.
- **Acceptance:** D1-AC-14 every exported measure carries both statuses; D1-AC-15 no measure is labelled "technically validated" without real-footage evidence references; D1-AC-16 no construct status above CV-2 can be stored.

---

## 7. Correction 7 — Error attribution

### 7.1 Revised record

Each miss and false alert carries:

| Field | Values |
|---|---|
| `primary_stage` | evidence_unavailable, perception, tracking, geometry, event_reasoning, linkage, reference_ambiguity, **unresolved** |
| `secondary_factors` | Zero or more stages, plus visual cause tags (occlusion, truncation, lighting, crowding, unusual pose, unusual vehicle, viewpoint, clock misalignment) |
| `attribution_status` | `verified_oracle_single`, `verified_oracle_joint`, `diagnostic_inferred`, `unresolved` |
| `evidence` | Oracle runs referenced, rule-based tests and their outcomes |

`linkage` is new (deduplication errors). `unresolved` is a valid primary value; errors are not forced into a stage.

### 7.2 Procedure

1. **Synthetic (oracle available):** substitute simulator truth for perception, tracking and geometry in all 2³ combinations (*AB-3/AB-4 extended*). The error is *resolved* by a set if it disappears.
   - If one or more single-stage substitutions resolve it, `primary_stage` = earliest such stage; other resolving stages become secondary; status `verified_oracle_single`.
   - If only a combination resolves it, `primary_stage` = earliest stage in the smallest resolving set; the rest secondary; status `verified_oracle_joint`.
   - If none resolves it, the error is in event reasoning, linkage or the reference; apply step 2.
2. **Real data (no oracle):** rule-based tests of C.1 §4.5 in pipeline order; first failing test gives `primary_stage`; any further failing tests become secondary; status `diagnostic_inferred`. If tests conflict or none fails, `unresolved`.
3. **Reporting:** the error budget gives primary-stage shares (summing to 1, including `unresolved`) and, separately, the frequency of each contributing factor (may exceed 1 in total). Verified and inferred attributions are shown in separate columns.

### 7.3 Impact, data requirements, acceptance, assumptions

- **Impacted:** C.1 §4.5 and C1-AC-11 ("exactly one attribution" → exactly one primary value, possibly `unresolved`), D §3.5 (error-budget format), D §5 AB-3/AB-4 (factorial oracle runs).
- **Data requirements:** `error_attribution` records as in 7.1, linked to oracle run IDs.
- **Acceptance:** D1-AC-17 every miss/false alert has exactly one `primary_stage` value; D1-AC-18 fixture with injected perception **and** geometry errors where only the joint substitution resolves yields `verified_oracle_joint`; D1-AC-19 no real-data record carries a `verified_*` status.
- **Assumptions:** oracle substitution cost is 8× the downstream run per synthetic error; acceptable at expected synthetic error counts; can be sampled if not.

---

## 8. Summary of new and changed acceptance criteria

| ID | Criterion |
|---|---|
| D1-AC-01–02 | Classification truth table and invariants CL-INV-01–11 |
| D1-AC-03–05 | Detector-independent coverage; completeness fixture; CM companions in reports |
| D1-AC-06–08 | Leakage groups; T2b disclosure; two-camera leakage fixture |
| D1-AC-09–11 | Weighted-estimator coverage simulation; ECS exclusion; frame tiling |
| D1-AC-12–13 | Counting-scenario fixtures; no "interval/bound" language without evidence |
| D1-AC-14–16 | Fitness statuses on every measure; validated requires real evidence; construct ceiling |
| D1-AC-17–19 | Primary/secondary/unresolved attribution; joint oracle fixture; no verified status on real data |

---

## 9. Internal consistency review and correction gate

Each correction is checked for whether it resolves the defect **substantively** (changes a rule, a computation or a test), not only by renaming.

| # | Check | Substantive change? | Result |
|---|---|---|---|
| 1 | O vs H/PC co-occurrence | Rule rewritten; new IE clause; invariants and fixtures | Resolved. Residual: stationary-forklift overlap is O only (OI-1), handled by review routing |
| 2 | NM/UD/CT exclusivity vs CT independent of G1 | Unchanged meanings; CL-INV-04/05 enforce | Consistent |
| 3 | Denominator bias | New detector-independent coverage, reference object presence, CM metrics, three activity states | Resolved as measurement; correction of exposure left to RQ2 by design |
| 4 | Completeness metrics need reference objects but C.1 windows annotated only interactions | Annotation scope extended in §2.4 | Resolved; cost risk recorded |
| 5 | Leakage across cameras | Leakage-group partitioning; T2a/T2b | Resolved; D §3.6 SDG/SmartSpaces viewpoint tests reclassified as T2b |
| 6 | Weighted metrics vs C.1 one-to-one matching | Matching unchanged; weights applied after matching, per window | Consistent |
| 7 | Exhaustive windows annotated on all cameras of a group vs annotation cost | Required for deduplication and completeness | Consistent; cost risk shared with item 4 |
| 8 | Count range vs scenarios | Range removed; assumption-labelled scenarios; MR-07 measures assumptions | Resolved |
| 9 | Fitness table vs D §8 "RQ2-candidate" | Replaced by two-axis status; "candidate input" only when technically validated | Consistent |
| 10 | Claims ladder Level 4 | Now references measurement and construct status | Consistent |
| 11 | Attribution "exactly one" vs multi-cause | Primary + secondary + unresolved; verified vs inferred | Resolved |
| 12 | Stopping rule (D §9.1) vs weighted recall | Floor applies to weighted headline recall on RES | Consistent |
| 13 | Synthetic frequencies | Declared design artefacts; never frequency claims | Consistent with D §2.4 |
| 14 | Provisional items (D-4, D-5, C2–C6) | Marked provisional; none alters a rule above | No contradiction |

**Gate result: PASS — no critical contradiction introduced.** Package E proceeds under the user's conditional authorization.

**Open items for the user (non-blocking):**
- **OI-1** Should a footprint overlap with a stationary forklift receive its own label, or stay O with review routing (current)?
- **OI-2** Accept the added annotation scope (object presence on all cameras of a window group)? It is required for completeness and deduplication metrics.
- **OI-3** D-4, D-5, C2–C6 remain on working positions.

---

## 10. Sections amended or superseded

| Document § | Status | By |
|---|---|---|
| C.1 §2.3 | Superseded (count range) | D.1 §5 |
| C.1 §3.2 | Amended (co-occurrence, episode-level evaluation, `K`) | D.1 §1 |
| C.1 §3.3 | Amended (IE clause, review routing) | D.1 §1.3, §1.6 |
| C.1 §4.1 | Amended (frame, tiling, boundary, RES/ECS, object presence) | D.1 §2.4, §4 |
| C.1 §4.4 | Amended (weighted denominators) | D.1 §4.3 |
| C.1 §4.5 | Superseded | D.1 §7 |
| C.1 §6.2 | Amended (four layers, AI vs reference time) | D.1 §2 |
| C.1 C1-AC-04, C1-AC-11 | Amended | D1-AC-12, D1-AC-17 |
| D §2.2–2.3 | Amended (leakage groups) | D.1 §3 |
| D §2.6 | Amended (effective sample size) | D.1 §4.3 |
| D §3.4 EV-M7, EV-M12 | Amended | D.1 §4.3, §1.7 |
| D §3.5 | Amended | D.1 §7.2 |
| D §3.6 | Amended (T2a/T2b) | D.1 §3.3 |
| D §4 MR-04, MR-05, MR-07 | Amended | D.1 §2.4, §4, §5 |
| D §7 | Amended (two variance targets) | D.1 §4.3 |
| D §8 | Superseded | D.1 §6 |
| D §9 Level 4 | Amended | D.1 §6.2 |
