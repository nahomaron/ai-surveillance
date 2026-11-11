# Package C.1 — Architecture and Measurement Alignment Addendum (RQ1)

**Date:** 7 November 2026
**Status:** Correction addendum to Package B.1 and Package C. Correction gate result in Section 10.
**Scope:** RQ1 only. RQ1 is treated as the development and evaluation of a **hazard observation and measurement instrument**, not only a detection benchmark. No RQ2 indicator formula, no establishment score, no OSHA linkage, no implementation code.

**Evidence conventions:** facts from inspected dataset files are cited to Packages A.1/B (e.g., "P0 census"). Everything else is a design requirement, an assumption (labeled), or a parameter (italic name, no value).

---

## 1. Summary

The five inconsistencies are resolved by one structural change and four specification changes:

| # | Issue | Resolution |
|---|---|---|
| 1 | "Rules do not create episodes" vs "configuration-specific episode streams" | A **configuration-independent observation substrate** (pair windows + measurement series + exposure profiles) is computed once. A **rule configuration** (a set of flag providers + parameters + lifecycle settings) is the only thing that creates episodes. Individual rules are flag providers inside a configuration; they never create episodes on their own. Configurations are compared on the shared substrate and against one shared reference set. |
| 2 | Near miss / contact / exposure separation | Seven outcome labels with fixed logic; contact has four automated states with no automated "observed"; **exposure measurements are retained for every pair window and every episode regardless of classification outcome**. |
| 3 | Construct mismatch with human references | Per-output reference table: reference layer, acquisition method, expected reference error, disagreement handling, and the claim each comparison can support. |
| 4 | Abstention and missed-event bias | Reference events come from **exhaustive annotation of independently sampled time windows**, not from system candidates. Explicit denominators, deterministic one-to-one matching, duplicate-alert accounting, and stage-attributed failure analysis. |
| 5 | Physical measurement validity | A geometry validation programme (position, calibration, footprint dimension sensitivity, footprint shape error, uncertainty calibration) and stage-by-stage reproducibility classes (exact vs documented tolerance). |

Part 3 additions (Section 7): a unit hierarchy from frame detections to validated events, configuration-independent exposure-opportunity measures, a separated uncertainty register, an RQ2 traceability table, and preserved E2 interfaces.

---

## 2. Revised event-generation logic (Correction 1)

### 2.1 Objects in the event pipeline

| Object | Depends on rule configuration? | Defined by | Stored as |
|---|---|---|---|
| **Pair observation window (POW)** | No | One person track and one forklift track jointly present in one camera (gaps ≤ *g_max* bridged and flagged) | `pow` table |
| **Global pair window (GPW)** | No | POWs from different cameras linked to the same physical person–forklift pair through calibrated cross-camera identity and overlapping time | `gpw` table (only where calibration links cameras) |
| **Measurement series** | No (depends on perception, tracking and geometry configuration only) | Per-frame clearance (+σ), image-space clearance, speeds, headings, predicted clearance under each declared motion model, footprint-overlap indicator, evidence state | `pair_series` table |
| **Exposure profile** | No | Per POW/GPW: durations by clearance band (fine fixed bins), forklift moving/stationary time, joint observability time, occluded time | `exposure_profile` table |
| **Condition flags** | Yes | Flag providers R1–R6 apply a configuration's parameters to the measurement series: `P`, `M`, `X`, `C` (one column per provider), `E`, `G`, `Q` | `flag_series` table, keyed by configuration |
| **Trigger** | Yes | Per configuration: `T(t) = P ∨ X ∨ C_any`, where `C_any` = OR of all path-conflict providers enabled in that configuration | Derived column |
| **Episode** | Yes | Maximal trigger interval inside one POW after the deterministic lifecycle (2.2) | `episode` table, keyed by configuration |
| **Candidate event** | Yes | Per configuration: the set of episodes of one GPW whose intervals overlap (or the single episode where no GPW exists) | `event` table, keyed by configuration |
| **Physical interaction (reference)** | No | A reference event defined by annotators in sampled windows (Section 4) | Validation store |
| **Validated event** | No (human) | A reference event with adjudicated A/C labels | Validation store |

**Key rule:** R1–R6 are *flag providers*. A provider writes a flag column. Only the event engine, running one *configuration*, turns trigger intervals into episodes. Enabling R3 and R4 together in one configuration ORs their conflict flags into one trigger, so one interaction yields one episode with two flag columns (`C_by_R3`, `C_by_R4`). Two *different configurations* produce two separate, explicitly labeled episode streams over the same substrate; they are never pooled or counted together.

### 2.2 Deterministic lifecycle (per configuration, per POW)

1. **Open** at the first frame where `T` is true.
2. **Bridge** false runs ≤ *m_gap* frames.
3. **Close** at the last true frame before a false run > *m_gap*, or at POW end.
4. **Assess attributes** (`E`, contact state) over [open, close + *w_post*], truncated at POW end.
5. **Discard** episodes shorter than *t_min* (retain in a `discarded_episode` log with reason).
6. **Split** at any POW break (track gap > *g_max* or identity switch); the following segment is a new episode with `continuation_of` pointing to the previous one.
7. **Order and IDs:** episodes are processed in (video, POW start frame, POW ID) order; `episode_id = hash(config_id, pow_id, open_frame)`.

Because `C` is a trigger evaluated at any distance, an approaching forklift opens an episode before proximity occurs (acceptance test C1-AC-03).

### 2.3 Cross-camera deduplication

- Within one configuration, episodes from POWs that belong to the same GPW and overlap in time (after clock alignment) form **one candidate event**. Event onset = earliest member onset; event end = latest member close.
- Where cameras are not calibrated to a common frame, no GPW exists. Such episodes cannot be merged automatically. They are flagged `possible_duplicate` when their cameras have overlapping declared fields of view and overlapping times.
- Event counts are reported as a **range**: `n_events_min` (merging all `possible_duplicate` groups) and `n_events_max` (merging none). The range width is itself a reported measurement-quality indicator.

### 2.4 Comparing configurations

Configurations may produce different boundaries, so they are compared on three configuration-independent bases:

1. **Against the same reference events** (Section 4), using the same matching procedure. This is the primary comparison.
2. **On the shared timeline:** per-frame flag agreement between configurations within the same POWs (frame-level Cohen's κ for each flag), and an episode-overlap map (which episodes of configuration *a* overlap which episodes of *b*).
3. **On configuration-independent exposure measures** (2.1 exposure profile), which do not depend on episode boundaries at all.

### 2.5 Preservation

The substrate (POW, GPW, measurement series, exposure profile) is retained independently of any rule configuration. Changing rules creates new flag/episode/event tables; it never modifies or deletes substrate tables.

---

## 3. Classification logic (Correction 2)

### 3.1 Contact state (automated, per episode; event-level by fusion)

| State | Assigned when |
|---|---|
| `none_observed` | Closest approach visible (`Q` sufficient), no footprint overlap, clearance − *k_σ*·σ > 0 |
| `undetermined` | Footprint overlap; **or** clearance within *k_σ*·σ of zero; **or** closest approach not visible |
| `suspected` | Footprint overlap **and** a contact cue at closest approach (abrupt deflection or stop of either track beyond parameter *k_c*) |
| `not_assessable` | No usable frames around closest approach |

No automated state means "observed contact". **Observed contact** exists only as a human A-layer fact. Event-level fusion uses only views with sufficient evidence at closest approach; agreement → shared state; disagreement → `undetermined` + review flag.

### 3.2 Outcome labels (multi-label)

| Label | Meaning | Condition |
|---|---|---|
| O | Ordinary proximity | `P` true; `X` false; `C_any` false |
| H | Potentially hazardous exposure | `X` true (proximity while forklift moving) |
| PC | Predicted movement-path conflict | `C_any` true |
| NM | Candidate near miss, no observed contact | (H or PC) and (`E` or min clearance < *d_nm*) and contact = `none_observed` |
| UD | Near miss or contact undetermined | (H or PC) and (`E` or min clearance < *d_nm*) and contact = `undetermined` |
| CT | Suspected contact | contact = `suspected` |
| IE | Insufficient evidence | `Q` insufficient at closest approach or for > *o_max* of the episode |

O, H and PC can co-occur. NM, UD and CT are mutually exclusive (they partition contact states). IE is a qualifier that can accompany any label. The summary view (CT > UD > NM > PC > H > O) is for display only and is stored alongside, never instead of, the labels.

### 3.3 When contact cannot be ruled in or out

The episode keeps `UD` (or `IE` if evidence is missing), is routed to review, and is **never** counted as NM in any automated statistic. Reports show NM and UD side by side.

### 3.4 Exposure retained regardless of outcome

Every episode stores, whatever its labels: duration; minimum clearance with σ; time below each clearance bin; forklift speed at closest approach; closing rate; time to closest approach; evasive-action score; visibility fraction. Every POW stores its exposure profile even when no episode occurs. An interaction that is not a near miss — or cannot be classified — remains fully usable for exposure analysis.

### 3.5 Automated vs human status

`automated_labels` (per configuration) and `validation_status` (`unreviewed` / `confirmed` / `rejected` / `disputed`, with layer and reviewer references) are separate fields in separate stores. Validation never overwrites automated labels; automated outputs never set validation status. Reports use the wording "candidate", "suspected" or "undetermined" for automated outputs and "reviewer-confirmed" only for adjudicated human labels — never "near miss occurred" or "collision occurred".

---

## 4. Evaluation and independent-reference workflow (Corrections 3 and 4)

### 4.1 Independent reference sampling

- **Reference windows** are drawn from the full footage by a sampling plan fixed before any system run is inspected: stratified random time windows of length *w_ref* by data origin, scene/site, camera viewpoint and (for synthetic) generation batch.
- Annotators review **every frame of each sampled window** and annotate **all** person–forklift interactions present (exhaustive annotation), whether or not the system detected anything. This is what lets reviewers find hazards the system misses entirely.
- The sampler has no access to system outputs. Candidate-driven review queues (for error analysis or the AI-assisted study) write to a separate label namespace that can never become reference data.
- Precision is computed **only inside exhaustively annotated windows**, so every system event there can be adjudicated as matched or unmatched.

### 4.2 Reference layers per automated output

| Automated output | Reference layer | How reference is obtained | Expected reference error | Disagreement handling | Claim supported by agreement |
|---|---|---|---|---|---|
| Detections, tracks | A (boxes, IDs) | Simulator boxes (synthetic); CVAT box/track annotation (real) | Synthetic: render-exact boxes, but `occlusionRatio` not computed in SDG; real: box-placement error measured by double annotation | Third annotator; IoU-based consensus box | Perception works on this domain |
| Ground position, clearance, speed | B | Simulator 3D boxes and world positions (synthetic); surveyed floor markers + double-clicked foot points on calibrated cameras (staged real) | Synthetic: footprint is an envelope, not the true shape; real: click repeatability + calibration error, both measured (Section 5) | Mean of two clicks if within *b_tol*, else third click | Geometry is measured within quantified error |
| `P`, `M`, `X` flags | B (+ A for "moving") | Apply the same flag definition to reference geometry | Inherits B error | — | Flags are computed correctly *given the definition* (not that the definition is valid) |
| `C` path-conflict flags | B | Apply the declared motion model to reference trajectories | Inherits B error | — | Prediction works under the declared model |
| `E` evasive action | A | Visible evasive action annotated; SDG `Dodge` task onset for synthetic | Annotator onset error measured; SDG dodge from frame 0 in 10/60 P0 runs (excluded) | Third annotator | Evasive behaviour is detected |
| Contact state | A | Visible contact: yes / no visible contact / can't tell | "No visible contact" ≠ no contact | Third annotator; disagreements → "can't tell" | Contact uncertainty is honestly represented |
| O / H / PC labels | A + B | Definitions applied to reference facts and geometry | As above | — | Definitions applied correctly |
| NM / UD / CT labels | C (+ A contact) | Qualified reviewers, blind, rationale recorded | Inter-rater disagreement quantified (κ/α) | Consensus meeting; unresolved → Tier 2 | System candidates **align with expert judgment**; this is not proof of real-world hazard |
| Episode boundaries | A | Annotated start/end of the interaction | Inter-annotator onset/offset differences measured | Average if within *b_tol*, else adjudicate | Temporal localization quality |
| Coverage states | A | Annotators flag unusable or unobservable spans in windows | Measured agreement | Third annotator | Coverage accounting is correct |

**Rule:** agreement with any B-layer or threshold-derived reference supports only measurement claims. Hazard-related claims require C-layer agreement and are worded as alignment with expert review.

### 4.3 Deterministic one-to-one matching

1. Candidate pairs: (system event *s*, reference event *r*) with the same person–forklift pair (global identity, or spatial overlap of both objects at the system's closest-approach frame) and temporal IoU ≥ *iou_m*.
2. Solve a maximum-weight bipartite matching (Hungarian algorithm) with weight = temporal IoU.
3. Ties: higher IoU, then earlier reference onset, then lower system event ID.
4. Unmatched system events overlapping an already-matched reference event (IoU > 0) are **duplicate alerts**; other unmatched system events are **false alerts**; unmatched reference events are **misses**.

### 4.4 States and denominators

| State | Definition | Enters |
|---|---|---|
| Missing footage | Coverage = not recorded | Coverage hours only |
| Unusable footage | Coverage = unusable | Coverage hours only |
| Unobservable reference event | Reference event annotated as not assessable | Separate count; excluded from recall denominator; system output on it reported (EV-M10) |
| Assessable reference event | Reference event with sufficient evidence | Recall denominator |
| Ambiguous reference | Tier 2 or "unsure" C-layer label | Reported separately; sensitivity analysis counting them as positive and as negative |
| System abstention | System IE episode or abstained interval where the reference is assessable | Counts as a miss in headline recall |
| False alert | Unmatched non-duplicate system event in a reference window | Precision denominator |
| Duplicate alert | See 4.3 | Precision denominator (as error) and separate duplicate rate |

- **Headline recall** = matched assessable reference events ÷ assessable reference events (abstentions = misses).
- **Headline precision** = matched system events ÷ (matched + false + duplicate system events), excluding abstentions, within reference windows.
- **Coverage** = assessable reference events receiving a non-abstained system decision ÷ assessable reference events.
- **Conditional recall/precision** = the same restricted to attempted decisions; always printed with coverage.
- **False-alert burden** = (false + duplicate alerts) ÷ usable video hours in reference windows.

### 4.5 Stage-attributed failure analysis

Each miss and each false alert is attributed to the first failing stage:

| Attribution | Test |
|---|---|
| Evidence unavailable | Reference marked unobservable or footage unusable at closest approach |
| Perception | No detection of the person or forklift within *n_miss* frames of closest approach |
| Tracking | Detections present but the pair window broken or identity switched around the event |
| Geometry | Tracks correct, but clearance/speed error beyond its σ-scaled tolerance flipped a flag |
| Event reasoning | Correct geometry, but the rule configuration did not trigger (or triggered falsely) |
| Reference ambiguity | Tier 2 reference |

On synthetic data, attribution is confirmed by **oracle substitution**: re-run downstream stages with simulator truth in place of one stage's output; if the error disappears, that stage is responsible.

---

## 5. Physical geometry and uncertainty validation (Correction 5)

### 5.1 Validation programme

| ID | What is validated | Reference | Method | Output |
|---|---|---|---|---|
| GV-01 | Ground position of persons and forklifts | SDG/SmartSpaces world positions; surveyed markers (staged) | Error distribution by camera, distance band, viewpoint, occlusion | Bias, RMSE, 95th percentile per stratum |
| GV-02 | Camera calibration | Held-out control points (staged); SDG projection consistency (reproject 3D boxes, compare with 2D boxes); SmartSpaces reprojection reports (unit undocumented) | Reprojection and ground-plane error on held-out points | Calibration error per camera |
| GV-03 | Forklift dimension sensitivity | SDG asset 3.03 × 1.13 m; SmartSpaces median 1.87 × 1.13 m | Sweep the footprint prior over a declared range; measure change in clearance and flag decisions | Sensitivity of clearance and outcomes |
| GV-04 | Footprint approximation error | Synthetic: oriented 3D box; real: no exact shape available | Compare footprint from prior vs simulator box; state that the box itself is an envelope (P0: footprint overlap in 53/60 runs) | Shape error bound; documented limitation for real data |
| GV-05 | Uncertainty calibration | Errors observed in GV-01/GV-02 | Fraction of true errors within ±1σ and ±2σ; distribution of standardized errors | Calibration ratio; σ inflation factor if under-dispersed |
| GV-06 | Image-space vs physical distance | Same pairs measured both ways | Correlation and disagreement by viewpoint | Evidence that image-space proximity is not physical distance |
| GV-07 | Speed and closing rate | Simulator kinematics (SDG speed units to be confirmed) | Error vs smoothing window | Recommended window range |
| GV-08 | Path prediction | Simulator future trajectories | Predicted vs actual minimum clearance vs horizon *τ* | Usable horizon range |

**Monte Carlo is not self-validating.** σ values produced by Monte Carlo are accepted only after GV-05 shows they are calibrated; otherwise they are inflated by the measured factor or the decision is marked borderline. Calibration is checked per stratum (viewpoint, distance, occlusion), not only globally.

### 5.2 Reproducibility by stage

| Stage | Class | Requirement |
|---|---|---|
| S0 Register | Exact | Identical manifest hashes |
| S1 Decode | Exact for the same decoder build; tolerance across builds | Frame count and PTS identical; pixel differences across FFmpeg versions documented |
| S2 Detect | Tolerance | GPU non-determinism allowed; re-run compared with cache: box IoU ≥ *iou_rep*, score difference ≤ *s_rep*, flipped detections reported |
| S3 Track | Exact given S2 artifacts | Identical tracks |
| S4 Spatial | Exact given S3 artifacts and seed on the same platform; tolerance across platforms | Monte Carlo seeded; cross-platform floating-point differences ≤ *ε_geo*, with any flag flips reported |
| S5 Events | Exact given S4 artifacts | Identical episode tables (hash-equal) |
| S6 Evidence | Exact for clip boundaries; encoded bytes may differ | Same frame ranges and hashes of decoded frames |
| S7 Validation import | Exact | Append-only, hash-chained |
| S8 Evaluate | Exact given inputs and bootstrap seed | Identical metric tables |
| Detector fine-tuning | Tolerance | Re-training is not bit-exact; weights are versioned artifacts and evaluations reference weight hashes |

---

## 6. Safety-measurement data requirements (Part 3)

### 6.1 Unit hierarchy (no unit counted as another)

| Level | Unit | Counted as |
|---|---|---|
| U1 | Frame detection | Never an event |
| U2 | Object track | Never an event |
| U3 | Pair observation window (per camera) / global pair window | Exposure opportunity, not an event |
| U4 | Continuous exposure interval (time in a clearance band within a POW) | Duration, not a count |
| U5 | Episode (per configuration, per camera) | Observation of an event |
| U6 | Candidate event (deduplicated, per configuration) | Automated count, reported as a range |
| U7 | Validated event (human-adjudicated) | Reference count |

Repeated detections in consecutive frames belong to one track and one POW; they cannot increase U5–U7 counts.

### 6.2 Exposure opportunity and coverage measures

| Measure | Definition | Caveat recorded with it |
|---|---|---|
| Usable monitored time | Coverage = observed, per camera | Camera time ≠ establishment activity |
| Field-of-view footprint | Floor area visible per camera (calibrated); else image-only flag | Unmonitored areas unknown |
| Forklift observed time | Sum of forklift track time | Only within view |
| Forklift moving / stationary time | From speed vs *v_min* | Speed estimation error (GV-07) |
| Joint observability time | Sum of POW durations | — |
| Time in clearance bands | From exposure profiles | Geometry error (GV-01) |
| Candidate hazardous interaction duration | Episode durations by label | Configuration-dependent |
| Occluded / unusable time | Coverage and evidence states | — |
| Zone context | Zone ID per position where a zone map is supplied | Only if supplied as context |

These measures describe what was observed. They are **not** complete exposure denominators for an establishment, and RQ1 does not combine them into rates.

### 6.3 Uncertainty register (never combined)

| Component | Field(s) |
|---|---|
| Detection confidence | Detector score per detection (not a probability unless calibrated, ADR in C §2.1) |
| Tracking uncertainty | Track state, gap lengths, identity-switch flags |
| Spatial measurement error | σ of positions and clearance (calibrated per GV-05) |
| Temporal boundary uncertainty | Onset/offset uncertainty from *m_gap* sensitivity and boundary agreement with references |
| Classification uncertainty | Borderline flags; outcome stability across the parameter grid |
| Human-label disagreement | Tier, κ/α per field |
| Unobserved exposure | Coverage gaps, unmonitored area flags, event-count range |

### 6.4 Experiment 2 preserved

E2 remains a conditional feasibility experiment for worker exposure to elevated objects. Preserved interfaces (Package C §10): `LoadElevationEstimator`, `FootprintOccupancyAssessor`, image-space overlap baseline, height-reference registry in calibration records, `load`/`rack` classes, SDG collision-scenario object annotations, and optional physical metadata fields (`load_mass_kg`, `load_height_m`, each with provenance and σ, nullable). No potential energy, fall probability, severity or impact computation is performed; the metadata fields exist only so that later, justified analyses are not blocked by the data model.

---

## 7. Traceability from RQ1 outputs to potential RQ2 inputs

| RQ1 output | Potential RQ2 input (not defined here) | Required companion data | Status after Package D (to be determined) |
|---|---|---|---|
| Validated event counts by label | Event frequency | Usable monitored time, coverage, event-count range | Pending measurement validity tests |
| Episode durations | Exposure duration | Boundary uncertainty | Pending |
| Time in clearance bands | Proximity exposure profile | Geometry error, calibration status | Pending |
| Forklift moving time | Activity measure | Speed error; camera coverage | Pending |
| Joint observability time | Opportunity measure | Coverage; field of view | Pending |
| NM/UD/CT candidates + review status | Candidate hazard events | Tier, κ, review coverage | Pending |
| Coverage and unusable time | Completeness indicator | — | Pending |
| Site, camera, observation period IDs | Grouping keys | Provenance; data origin | Available by design |

No row implies an indicator formula, a weighting, or a link to OSHA records. Public datasets carry no establishment identity and are flagged `data_origin` accordingly.

---

## 8. Updated decisions, licensing register and risks

### 8.1 Architecture decisions (changes)

| ADR | Change |
|---|---|
| ADR-12 (new) Observation substrate | POW/GPW, measurement series and exposure profiles are configuration-independent, immutable tables |
| ADR-13 (new) Reference sampling | Exhaustively annotated, independently sampled windows; candidate-driven labels in a separate namespace |
| ADR-14 (new) Matching | Hungarian maximum-weight one-to-one matching with deterministic tie-breaks |
| ADR-15 (new) Uncertainty acceptance | σ accepted only after empirical calibration (GV-05) |
| ADR-02 Detector | Unchanged; licensing documented per component (8.2), no family rejected for possible future commercialization |

### 8.2 Licensing obligations register (to verify at acquisition)

| Component | Known terms (source) | Obligation to track | Status |
|---|---|---|---|
| Ultralytics YOLO26 / YOLO11 code | AGPL-3.0 or Enterprise (Ultralytics licensing page) | Source disclosure for distributed or network-served derivative works | Documented |
| Ultralytics pretrained weights | Covered by Ultralytics licensing statements | Whether fine-tuned weights are derivative works | Open question |
| RF-DETR code and COCO weights | Apache-2.0 (Roboflow) | Attribution, notice | Documented; per-size weights to verify |
| Roboflow `trackers` | Apache-2.0 (PyPI page) | Attribution | Documented |
| SDG-Warehouse | Card: OpenMDW-1.1; no license file in repository (V5) | Terms in writing before publication | Open |
| SmartSpaces | Card tag CC-BY-4.0; no license file (V5) | Attribution | Open |
| LOCO | Not read | Must read before any training use | Open |
| COCO (pretraining data of detectors) | Not re-verified here | Image terms of COCO sources | Open |
| CVAT / Label Studio | Not verified this session | Confirm at install | Open |

### 8.3 Risks (changes)

| Risk | Mitigation | Type |
|---|---|---|
| Exhaustive window annotation is labour-intensive | Short windows; prioritize staged real data; synthetic windows labelled automatically for A/B layers | Schedule |
| Event-count range wide without cross-camera calibration | Report range; calibrate cameras in staged collection | Measurement limitation |
| σ under-dispersed | GV-05 inflation factor; borderline flags | Manageable |
| Footprint shape unknown for real forklifts | Dimension sweep; documented limitation | Accepted limitation |
| Oracle substitution only possible on synthetic data | Real-data attribution uses rule-based tests (4.5) without oracle | Limitation |

---

## 9. Acceptance criteria

| ID | Criterion |
|---|---|
| C1-AC-01 | Substrate tables are byte-identical before and after adding or changing a rule configuration |
| C1-AC-02 | One configuration with R3+R4 yields one episode per fixture interaction with two flag columns |
| C1-AC-03 | Fixture: distant fast approach opens an episode before any `P` frame |
| C1-AC-04 | Fixture: one interaction seen by two calibrated cameras yields one candidate event; uncalibrated yields `possible_duplicate` and an event-count range |
| C1-AC-05 | Lifecycle fixtures (bridge, split, continuation, discard) produce the specified boundaries and IDs on repeated runs |
| C1-AC-06 | Footprint-overlap fixture yields `undetermined`; no automated output contains "observed contact" |
| C1-AC-07 | Every episode and POW has exposure fields populated regardless of outcome label |
| C1-AC-08 | Reference sampler runs without read access to system outputs (permission/content check) |
| C1-AC-09 | Matching is deterministic: permuted input order gives identical matches |
| C1-AC-10 | Headline recall decreases when abstention is increased on assessable references (synthetic check) |
| C1-AC-11 | Each miss/false alert carries exactly one attribution |
| C1-AC-12 | GV-01–GV-08 produce stratified error tables; σ calibration ratio reported per stratum |
| C1-AC-13 | Reproducibility classes in 5.2 verified by re-run tests |
| C1-AC-14 | All RQ2 traceability fields (Section 7) present or null with reason |

---

## 10. Consistency review and correction gate

| # | Check across B.1, C, C.1 | Result |
|---|---|---|
| 1 | B.1 "rules don't create episodes" vs per-configuration streams | Resolved: providers vs configurations (2.1) |
| 2 | B.1 lifecycle vs C event engine contract | Consistent; C `EventEngine` input now "measurement series + configuration" |
| 3 | B.1 §5.4 greedy matching vs C.1 Hungarian | **Superseded** by Hungarian (4.3) |
| 4 | B.1 §5.2 precision denominator vs C.1 | Tightened: only inside exhaustively annotated windows; duplicates explicit |
| 5 | C §9.3 "sampling by protocol" vs C.1 exhaustive windows | Consistent; C.1 adds exhaustiveness |
| 6 | C §4.3 Monte Carlo σ vs C.1 GV-05 | Consistent; σ acceptance added |
| 7 | C §6 reproducibility vs C.1 5.2 | Refined by stage; no contradiction |
| 8 | B RQ2C-02 exposure opportunity vs C.1 6.2 | Expanded; consistent |
| 9 | Outcome labels in B.1 §3.2 vs C.1 3.2 | Identical logic; C.1 adds σ margin *k_σ* to `none_observed` |
| 10 | E2 interfaces (B §6, C §10) vs C.1 6.4 | Consistent; optional metadata fields added |
| 11 | Validation store separation (C AD-03) vs C.1 3.5 | Consistent |
| 12 | Event counts vs unit hierarchy | Consistent; counts only at U5–U7 |

**Gate result:** no fundamental contradiction remains. Open items are parameters (by design), license confirmations, and data access — none changes component boundaries or data contracts. **Package D proceeds under the conditional authorization.**

---

## 11. Sections amended or superseded

| Document § | Status | Replaced or amended by |
|---|---|---|
| B.1 §2.1–2.4 | Amended | C.1 §2.1–2.3 (substrate, providers vs configurations, GPW, count range) |
| B.1 §2.5 | Unchanged | — |
| B.1 §3.1 | Amended | C.1 §3.1 (σ margin in `none_observed`) |
| B.1 §3.4 | Superseded | C.1 §2.4 |
| B.1 §4.2 | Amended | C.1 §4.2 (acquisition method, reference error, disagreement, claim) |
| B.1 §5.1–5.2 | Amended | C.1 §4.4 (ambiguous references, duplicates, explicit denominators) |
| B.1 §5.4 | Superseded | C.1 §4.3 (Hungarian matching) |
| C §3.2 S5 | Amended | Runs per configuration over shared substrate; S4 also writes exposure profiles and GPWs |
| C §4.3 | Amended | C.1 §5.1 (σ acceptance, GV programme) |
| C §5.1 | Amended | New tables: `gpw`, `exposure_profile`, `discarded_episode`; event-count range fields |
| C §6 | Amended | C.1 §5.2 |
| C §9.3 | Amended | C.1 §4.1 |
| C §11.1 `EventEngine`, `Evaluator` | Amended | Inputs/invariants per C.1 §2 and §4 |
| C §12.3 C2 | Reframed | Licensing documented per component (C.1 §8.2) |
