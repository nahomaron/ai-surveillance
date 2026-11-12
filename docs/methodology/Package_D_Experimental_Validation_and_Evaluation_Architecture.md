# Package D — Experimental Validation and Evaluation Architecture (RQ1)

**Date:** 7 November 2026
**Builds on:** Packages A, A.1, B, B.1, C, C.1.
**Purpose:** Specify how RQ1 will be evaluated in two roles: **(1)** as a computer-vision hazard-detection system, and **(2)** as a scientific instrument producing measurable observations of hazardous exposure.
**Not in scope:** implementation code, safety-indicator formulas, establishment scores, OSHA linkage, Package E or agent handoff.

**Governing principle:** the goal is to determine whether the system produces sufficiently reliable, reproducible and scientifically meaningful observations, not to make it look capable.

Parameters are written in italics without values; they are pre-registered (Section 9.1) before any test data is evaluated.

---

## 1. Evaluation architecture at a glance

| Evaluation stream | Question | Reference | Primary units | Section |
|---|---|---|---|---|
| D1 Perception | Are persons and forklifts detected and tracked? | A-layer boxes/IDs; simulator truth | Frames, tracks | 3.1–3.2 |
| D2 Spatial measurement | Are positions, clearance, speeds and paths measured correctly? | B layer | Object-frames, pair-frames | 3.3 |
| D3 Event detection | Are candidate events found, localized and classified? | A + C layers in exhaustively annotated windows | Reference events | 3.4–3.6 |
| D4 Measurement reliability | Are frequency, duration, exposure and coverage measurements consistent, repeatable and robust? | Re-runs, parameter sweeps, multi-camera agreement, B-layer durations | Windows, POWs, events | 4 |
| D5 Baselines and ablations | What does each component contribute? | Same as D1–D3 on identical splits | As above | 5 |
| D6 Human review study (conditional) | Does AI assistance improve identification or documentation compared with unaided review? | Exhaustive reference set | Reviewer × window | 6.2 |
| D7 Measurement validity for RQ2 | Which outputs are fit to be studied as indicator inputs? | D1–D4 results against criteria | Measures | 8 |

---

## 2. Research design

### 2.1 Datasets and their roles

| Source | Verified basis | Role | Not used for |
|---|---|---|---|
| SDG-Warehouse near-miss (synthetic, rendered) | P0 census: 1 worker, 1 forklift, 300 frames, 10 views, simulator positions/boxes/task states; 53/60 runs reach footprint overlap | D1, D2 (exact geometry truth), evasive-action detection, oracle-substitution attribution | Near-miss vs contact discrimination; threshold setting; any real-world claim |
| SDG-Warehouse collision scenario | V6: pallets, boxes, racks annotated in 3D (one run inspected) | E2 geometry feasibility | Person exposure (no worker in inspected run) |
| SmartSpaces synthetic warehouse scenes | Calibrated multi-camera, Person/Forklift/PalletTruck 3D boxes and IDs | D1, D2, D3 (ordinary proximity and natural interactions with A/C labels), D4 cross-camera agreement, T2 viewpoint tests | Evasive behaviour truth |
| SmartSpaces real scenes (Warehouse_026/027) | 60 s per camera, calibration, no ground truth | Qualitative transfer check; A-layer pilot labels | Any metric without new labels |
| Staged real collection (if approved) | None yet | D1–D4 on real footage; GV programme with surveyed markers; T1/T2 real tests | Independent-site claims (one site) |
| Second independent site (if obtained) | None | T3 generalization | — |
| LOCO (if licensed) | Secondary sources only | Forklift detector fine-tuning (real images) | Evaluation |

### 2.2 Partitions and independence units

| Source | Independence unit | Partition rule |
|---|---|---|
| SDG | Run (all 10 views together), stratified by generation batch | Train / validation / test by run; seed ranges recorded; batches balanced or held out (sensitivity) |
| SmartSpaces | Scene, with each Cosmos-Transfer re-render kept with its source scene | Use the dataset's own scene splits where compatible; never split a scene's cameras across partitions |
| Staged real | Session × camera, and site | Sessions assigned before collection |
| Detector fine-tuning data | Image source / run / scene | Must not contain any evaluation unit |

### 2.3 Leakage prevention

- Automatic check (C REPC-02): every evaluation video, run, scene and site is compared against all training, tuning and parameter-selection manifests; any overlap blocks the report.
- Parameter grids and rule configurations are tuned on validation partitions only.
- Exhaustive reference windows for test partitions are annotated once and locked before system test results are inspected.
- Near-duplicates: SDG runs are compared by seed and batch; SmartSpaces re-renders grouped; Event-Videos (if ever used) split by generation scenario.

### 2.4 Synthetic vs real

Synthetic and real results are never pooled. Every table carries `data_origin`. Synthetic results support engineering feasibility and measurement-method validation; only real footage supports claims about real footage, and only independent sites support generalization claims.

### 2.5 Reference construction

As specified in C.1 §4.1–4.2: independently sampled windows, exhaustive A-layer annotation (all interactions, coverage states), B-layer geometry (simulator truth or surveyed/clicked), C-layer expert judgments (blind, two reviewers, adjudication, Tier 1/Tier 2).

### 2.6 Sample size approach

Sample sizes are planned for **interval width**, not significance:

- Event-level recall and precision: enough assessable reference events per primary stratum that the 95% interval half-width is ≤ *h_target* (e.g., a proportion near 0.8 needs roughly 60–100 events for a half-width near ±0.08–0.10, before clustering adjustment).
- Cluster adjustment: intervals use the independence unit; the effective sample size is reduced by within-unit correlation, so the plan targets the number of **units**, not only events. The design effect is estimated in the pilot.
- Strata below *n_min* events are reported descriptively (counts only).

---

## 3. Detection reliability (D1–D3)

### 3.1 Object detection

| Metric | Unit | Strata | Notes |
|---|---|---|---|
| AP@0.5 and AP@0.5:0.95 per class (person, forklift; later load) | Frame boxes | Domain, viewpoint, distance band, occlusion | Occlusion from visibility estimates; SDG `occlusionRatio` = −1 so occlusion is computed from instance masks |
| Recall at fixed false positives per frame | Frames | Same | For use as an operating point in later stages |
| Score calibration (reliability diagram, ECE) | Detections | Domain | Required before treating scores as probabilities |

### 3.2 Multi-object tracking

| Metric | Notes |
|---|---|
| HOTA, IDF1, MOTA | Against simulator IDs (synthetic) or CVAT tracks (real) |
| Identity switches per track-hour | Directly affects POW splitting |
| Fragmentation; gap-length distribution | Affects bridging (*g_max*) |
| Pair-window fidelity | Fraction of reference interactions covered by a single unbroken POW |

### 3.3 Spatial measurement (GV programme, C.1 §5.1)

| Measure | Error metrics | Strata |
|---|---|---|
| Ground position | Bias, RMSE, 95th percentile (m) | Camera, distance, viewpoint, occlusion, calibration status |
| Clearance | Signed error (m); error near decision-relevant values | Same + footprint prior |
| Speed, closing rate | Error vs smoothing window | — |
| Predicted minimum clearance | Error vs horizon *τ* | Straight vs turning |
| Uncertainty calibration | Fraction within ±1σ/±2σ; standardized-error distribution | All of the above |
| Image-space vs physical | Agreement, rank correlation, decision disagreement | Viewpoint |

### 3.4 Event-level detection

Matching and denominators exactly as C.1 §4.3–4.4. Reported per outcome label, configuration, data origin and stratum:

| ID | Metric |
|---|---|
| EV-M1 | Headline recall (abstentions = misses) |
| EV-M2 | Headline precision (includes false and duplicate alerts) |
| EV-M3 | Abstention rate (episodes and time) |
| EV-M4 | Reference-event coverage |
| EV-M5 | Insufficient-evidence miss rate |
| EV-M6 | Conditional recall/precision (always with EV-M4) |
| EV-M7 | False-alert burden per usable hour (false + duplicate) |
| EV-M8 | Temporal localization: onset/offset error (s), temporal IoU |
| EV-M9 | Contact-state cross-tab vs A-layer visible contact |
| EV-M10 | System output on unobservable reference events |
| EV-M11 (new) | Duplicate-alert rate |
| EV-M12 (new) | Outcome agreement with C-layer judgments (κ between automated NM/UD/CT and adjudicated expert labels), Tier 1 and Tier 2 separately |

### 3.5 False positives and false negatives

Every miss and false alert is attributed to one stage (C.1 §4.5): evidence unavailable, perception, tracking, geometry, event reasoning, reference ambiguity. On synthetic data attribution is confirmed by oracle substitution. Results are reported as an error-budget table: the share of all errors attributable to each stage, per domain.

### 3.6 Occlusion, viewpoint and generalization

| Tier | Test | Claim permitted |
|---|---|---|
| T1 | Held-out runs/scenes/sessions | Performance on unseen sequences in represented conditions |
| T2 | Held-out camera geometries (e.g., SDG ceiling vs eye-level; SmartSpaces camera subsets; staged camera positions) | Robustness to the tested viewpoint changes |
| T3 | Independent site never used in development | Generalization to that site only — **only if such a site exists** |
| Synthetic → real | Develop on synthetic, test on staged real | Size of the domain shift |

Without T3 data, the report states that independent-site generalization was **not evaluated**.

---

## 4. Measurement reliability (D4)

The system is evaluated as an instrument: does it measure the same thing the same way, and how much do its measurements move when they should not?

| ID | Property | Design | Statistic |
|---|---|---|---|
| MR-01 | Run-to-run repeatability | Re-run S2–S8 on the same data (C.1 §5.2 classes) | Exact equality for exact stages; drift distribution for tolerance stages; any outcome flips |
| MR-02 | Cross-camera agreement | Same interaction seen by ≥ 2 calibrated cameras (SmartSpaces, staged) | Agreement of event detection (κ), duration (ICC, Bland–Altman), minimum clearance (Bland–Altman) |
| MR-03 | Agreement with reference durations | Episode duration vs A-layer duration; exposure time in clearance bands vs B-layer computation | Bland–Altman limits of agreement; ICC |
| MR-04 | Event frequency agreement | Automated candidate-event count range vs validated count per window | Ratio and difference with intervals; count-range width |
| MR-05 | Exposure-time accuracy | Joint observability, forklift moving time, time in clearance bands vs reference | Absolute and relative error per window |
| MR-06 | Coverage accounting accuracy | Automated coverage states vs annotated unusable/unobservable spans | Agreement (κ), time error |
| MR-07 | Deduplication accuracy | Automated events vs reference physical interactions across cameras | Over-/under-merge rates |
| MR-08 | Parameter sensitivity | Sweep each parameter over its pre-registered grid; one-at-a-time and joint (Latin hypercube) | Change in counts, durations, outcome labels; elasticity; stability regions |
| MR-09 | Footprint-prior sensitivity | GV-03 sweep | Change in clearance and outcomes |
| MR-10 | Calibration-error sensitivity | Perturb calibration within measured error | Change in measurements and outcomes |
| MR-11 | Uncertainty validity | GV-05 | Calibration ratio of σ |
| MR-12 | Boundary stability | Vary *m_gap*, *t_min* | Change in episode count and duration |

**Interpretation rule:** a measure whose value changes materially within its plausible parameter range (MR-08–MR-12) is labeled **parameter-sensitive** and cannot be promoted to RQ2 candidate status without a justified parameter choice.

---

## 5. Technical baselines and ablations (D5)

All comparisons use identical splits, identical reference windows and the same matching procedure. Differences are tested with paired bootstrap over independence units.

| ID | Configuration | Isolates |
|---|---|---|
| BL-1 | Detection only: frame-level co-presence of person and forklift, no tracking | Value of tracking |
| BL-2 | Detection + tracking + image-space proximity (R1) | Value of calibration |
| BL-3 | Calibrated clearance (R2) | Physical proximity |
| BL-4 | Calibrated + constant-velocity path conflict (R3) | Early conflict detection |
| BL-5 | Surrogate conflict measures (R4) | Alternative conflict model |
| BL-6 | Full configuration (R6 + contact assessor) | Combined reasoning |
| AB-1 | Detector: YOLO26 vs YOLO11 vs RF-DETR (each fine-tuned on the same training manifest) | Perception choice |
| AB-2 | Tracker: ByteTrack vs OC-SORT | Tracking choice |
| AB-3 | Oracle perception (simulator boxes) with each reasoning configuration | Upper bound of reasoning |
| AB-4 | Oracle geometry | Geometry contribution |
| AB-5 | Footprint prior variants | Shape assumption |
| AB-6 | Single camera vs multi-camera fusion | Fusion value |

Detector benchmarking reports accuracy, speed (PERF-02) and licensing obligations side by side; licensing is documented, not used to exclude a candidate from benchmarking.

---

## 6. Human validation and comparison

### 6.1 Technical validation (required)

System outputs are compared with independently established references (C.1 §4). Reviewer agreement is reported for every reference field (κ/α, boundary IoU), with Tier 1 and Tier 2 results separately. Pilot T1–T4 (B.1 §4.6) precedes the main annotation.

### 6.2 Human-review study (conditional on reviewer availability)

**Question:** Does AI-assisted review improve hazard-event identification or documentation compared with unaided video review?

| Element | Design |
|---|---|
| Participants | Qualified reviewers not involved in reference construction |
| Material | Reference windows with exhaustive labels, not seen by participants before |
| Conditions | Unaided review vs AI-assisted review (candidate list with evidence clips and uncertainty) |
| Allocation | Within-subject crossover: each reviewer sees different windows in each condition; window–condition pairing counterbalanced; order randomized |
| Washout | No window appears twice for the same reviewer |
| Outcomes | Recall of reference events; false reports; time per video hour; documentation completeness and factual accuracy scored on a pre-defined rubric by blinded raters |
| Bias controls | AI-assisted labels stored in a separate namespace; references fixed before the study; automation-bias check (do assisted reviewers miss events the AI missed more often than unaided reviewers do?) |
| Analysis | Mixed-effects models with reviewer and window as random effects; paired differences with intervals |
| Claim permitted | Effect of assistance on review performance for this material — not inspection effectiveness |

The study is not run unless enough qualified reviewers are available to estimate the condition effect with a pre-specified interval width.

---

## 7. Statistical analysis plan

| Topic | Method |
|---|---|
| Confidence intervals | Cluster (block) bootstrap over independence units; Wilson intervals for simple proportions when units are independent |
| Paired comparisons | Paired cluster bootstrap on the same reference events |
| Multiple comparisons | Primary comparisons pre-registered (BL-2 vs BL-3, BL-3 vs BL-6, AB-1); others reported as exploratory |
| Agreement | Cohen's κ / Krippendorff's α (categorical), ICC and Bland–Altman (continuous), temporal IoU (boundaries) |
| Calibration error | Reprojection error per camera; standardized position errors; σ calibration ratio |
| Sensitivity analysis | One-at-a-time and Latin-hypercube sweeps; ambiguous references counted as positive and as negative |
| Reviewer disagreement | Per-field agreement, confusion of disagreements, Tier 2 share; disagreement as a stratum |
| Failure-mode classification | Stage attribution (C.1 §4.5) plus visual cause tags (occlusion, truncation, lighting, crowding, unusual pose, unusual vehicle) |
| Missing data | Coverage states explicit; no imputation of unobserved time |
| Pre-registration | Parameter grids, primary metrics, comparisons and stopping rules frozen in a versioned analysis plan before test-set evaluation |

---

## 8. Measurement validity for future RQ2 research (D7)

### 8.1 Criteria

Each candidate measure is assessed against seven criteria. A measure is **RQ2-candidate** only if all are met on real (staged or natural) data; **experimental** if met on synthetic data only or with caveats; **not suitable** otherwise.

| Criterion | Evidence used |
|---|---|
| Operationally defined | Deterministic definition and parameter set (B.1, C.1) |
| Repeatable | MR-01, MR-02 |
| Sufficiently complete for its stated scope | MR-05, MR-06; coverage reporting |
| Traceable to evidence | Lineage tests (C AC-C-13, C.1 C1-AC-14) |
| Robust to reasonable parameter changes | MR-08–MR-12 |
| Explicit about missing or unobserved activity | Coverage states, count ranges |
| Comparable across conditions, or labeled non-comparable | Strata results by viewpoint, calibration status, site |

### 8.2 Candidate measures and current expectation

| Measure | Expected status before data (to be updated by results) | Main threat |
|---|---|---|
| Usable monitored time, coverage | Likely RQ2-candidate | Few |
| Joint observability time | Likely RQ2-candidate | Tracking fragmentation |
| Forklift moving time | Experimental until speed validated | Speed error |
| Time in clearance bands | Experimental | Geometry and footprint error |
| H / PC episode counts and durations | Experimental | Parameter sensitivity |
| NM / UD / CT candidates | Experimental; likely low yield and high UD share | Contact unobservability; expert disagreement |
| Validated event counts | Depends on review coverage | Reviewer capacity |
| Cross-site comparisons of any measure | Not suitable without T3 data | No independent sites |

---

## 9. Scientific claims ladder

| Level | Claim | Evidence required | Does not imply |
|---|---|---|---|
| 1 | The system can detect persons and forklifts in warehouse footage | D1 metrics per domain, with intervals | Measurement validity |
| 2 | The system can measure physical interactions and observable exposure conditions | D2 error within stated bounds; σ calibrated; MR-03, MR-05 | Hazard identification |
| 3 | The system can identify candidate hazardous events with quantified reliability | D3 headline and conditional metrics with coverage; EV-M12 agreement with expert judgments; on real footage for real-world wording | That candidates are true hazards; that counts are complete |
| 4 | Its observations are sufficiently consistent and traceable to investigate as potential safety indicators | D4 repeatability, robustness, completeness; D7 classification | That any indicator is valid (RQ2) |
| 5 | The system generalizes to new real-world environments | T3 independent-site results | Establishment-level safety assessment (RQ3) |

**Distinctions kept in all reporting:** engineering feasibility (Levels 1–2 on synthetic data) ≠ measurement validity (Levels 2–4 on real data) ≠ real-world operational effectiveness (not evaluated in RQ1).

### 9.1 Pre-registration and stopping rules

Before test evaluation: freeze parameter grids, configurations, primary metrics, strata, sample-size targets and the analysis code version. Stop rules: if T1 on real staged data shows headline recall below a pre-specified floor for every configuration, Levels 3–5 are reported as not supported and analysis turns to failure attribution.

---

## 10. Experiment 2 evaluation (conditional)

| Component | Evaluation | Data condition |
|---|---|---|
| E2-L1 load elevation state | Accuracy vs simulator heights (SDG collision objects) and measured fork heights (staged) | SDG collision runs (available); staging approval |
| E2-L3 image overlap baseline | Agreement with E2-L4 and with measured occupancy | Staged proxies |
| E2-L4 footprint occupancy | Error vs measured proxy positions; σ calibration | Staged proxies with height references |
| E2 human labels | A-layer elevation/position facts; C-layer judgments optional | Reviewers |

Allowed claim: geometric feasibility of footprint-occupancy measurement under calibrated staged conditions. No potential energy, fall probability or severity. If no staged data is approved, E2 is reported as a documented limitation with preserved interfaces.

---

## 11. Risks and limitations

| Risk / limitation | Effect | Response |
|---|---|---|
| No real labeled footage without approvals | Levels 3–5 untestable on real data | Report Levels 1–2 synthetic; enquiry package |
| Exhaustive annotation cost | Small real reference sets, wide intervals | Interval-based planning; prioritize primary strata |
| High UD share | Few NM/CT results | Report honestly; treat exposure measures as primary outputs |
| SDG scenario narrowness | Synthetic results optimistic | SmartSpaces and staged data for D3 |
| Single staged site | No T3 | State explicitly |
| Reviewer scarcity | D6 not run; C-layer small | Technical validation proceeds with A/B layers; C-layer as available |
| Parameter sensitivity | Measures may fail D7 | Report stability regions; avoid premature thresholds |
| Licensing of weights/data | Publication constraints | Register per component (C.1 §8.2) |

---

## 12. Acceptance criteria for Package D

| ID | Criterion |
|---|---|
| D-AC-01 | Every metric has a defined unit, denominator, reference layer and interval method |
| D-AC-02 | Every claim level maps to named evidence and data conditions |
| D-AC-03 | Splits and leakage checks defined for every source |
| D-AC-04 | Abstention, duplicates, ambiguity and coverage are reflected in headline metrics |
| D-AC-05 | Measurement-reliability tests cover frequency, duration, exposure, coverage, deduplication and uncertainty |
| D-AC-06 | Baselines and ablations run on identical splits with paired comparisons |
| D-AC-07 | Human-review study is separable and conditional |
| D-AC-08 | RQ2 measure classification criteria are explicit and evidence-based |
| D-AC-09 | No safety score, indicator formula or establishment ranking appears |

---

## 13. Decisions requested

1. **D-1** Approve the evaluation architecture, including exhaustive independent reference windows as the basis of all event-level metrics.
2. **D-2** Approve the claims ladder and the rule that synthetic results support only Levels 1–2 engineering feasibility.
3. **D-3** Approve the primary pre-registered comparisons (BL-2 vs BL-3, BL-3 vs BL-6, AB-1) and interval-based sample-size planning.
4. **D-4** Confirm whether pursuing a staged real collection (and, if possible, a second independent site) should begin now, since Levels 3–5 depend on it.
5. **D-5** Confirm whether the conditional human-review study (D6) should be planned now or deferred until reviewer availability is known.
6. **D-6** Earlier open items still awaiting your decision: detector licensing posture (C2), fine-tuning data (C3), compute (C4), annotation tools (C5), and the follow-up data steps F1/F3 (C6).

No further package will be started until you approve.
