# M0 report — deterministic contract verification

**Contract:** E-1.2.11 (E-1.2.1 FROZEN + F.1 Part A and Appendix N + Appendix T, sections T7 to T13).
**Branch:** `m0-implementation`. **Pipeline and clean-clone runs at commit:** `e6072ef` (environment digest `228ef036e3d74142…`, the SHA-256 of `requirements.lock`).
**Status:** STOP at G-M0. Everything below runs on fixtures and synthetic data. Nothing here is empirically validated.

## 1. Tasks

| Task | State |
|---|---|
| S-01, S-02 | done |
| T-01 to T-06, T-08 to T-15 | done |
| T-07 (E2 feasibility, document only) | done |
| T-16 (this report) | done; tag `m0-verified` |
| Blocked tasks | none |
| G-M0 | STOP: waiting for the Owner |

T-09, earlier blocked by CR-008 and CR-009, is done (Appendix T T9, T10). T-14, earlier blocked by CR-014, is done (T12).

## 2. Test matrix

Full suite: **1704 tests, all passing**, run twice from a clean clone with the locked environment (27.3 s each). The `determinism` marker selects 1463 of them.

| Area (tests/…) | Tests | Main contract coverage |
|---|---|---|
| schema | 508 | T-01: schemas, all active VR rules (one pass and one fail case each), CT-E-01/05/30 |
| ids | 56 | T-02: CT-ID-01–07, CT-FK-01–07, CT-NK-01–08, CT-I-01/03–08, the T5 reference vector |
| fixtures_t03 | 84 | T-03: every record fixture cites its source; Appendix N values present |
| clips | 17 | T-04: deterministic clips, including `fx_m0_pipeline` |
| registry | 30 | T-05: FX-A3/A4, FX-B1–B3, CT-I-05/06, CT-NK-04/05 |
| decode | 34 | T-06: CT-T-01–13, CT-T-14–17, CT-T-20(a,b), CT-T-21/22, N3 A–D |
| substrate | 65 | T-08: T8 checks, CT-T-14–19, CT-T-20(c,d), CT-F-01/02, CT-E-05–08, N2 G1–G3, T9.1, CT-T10-02/03/10 |
| events | 630 | T-09: N1 T1–T13 exact, CL-INV property tests, CT-E-09/10/12/13/14, T9 checks, CT-T10-01 to 08, CT-T11-01/02, CT-T12-01, S5 CT-FK-02/04, CT-I-07 |
| splits | 24 | T-10: CT-S-01–10, CT-E-18/19/23, D-7, estimator simulation |
| validation | 55 | T-11: CT-E-24/25, CT-RC-01–03, VR-E-052/053/055 |
| evaluation | 153 | T-12 to T-14: CT-ID-A1/A2, CT-E-20/21/22/29, FX-TIE, FX-W, FX-CM, CT-F-03 to CT-F-10, CT-T10-09, CT-T11-03, CT-T12-02 to 05, CT-T13-01 |
| export | 42 | T-15: CT-X-01 to 05, CT-E-26/27/28 (export level), VR-E-040, wording rules, RV-02/RV-04 |
| pipeline | 6 | T-16: whole fixture pipeline, N2 G2 end to end, CT-E-26 and CT-E-28 end to end, two-run identity |

Other checks:
- **Network:** the suite also passed with sockets blocked (1704 passed). No test needs network access or a downloaded dataset.
- **Environment:** the installed packages equal `requirements.lock` exactly (pip itself aside), and `rq1` is not installed into the environment, so each checkout runs its own `src`.

## 3. Artifact IDs and determinism

The M0 fixture pipeline (`python -m rq1.pipeline.m0 <dir>`) runs: clips → S0 → S1 → oracle S3 → S4 → S5 → X0b → V0 → CV-SIM → X0c → S8 → S8f → S4-E2 → S9 fixture export and report. It ran twice in separate processes from the clean clone.

| Stage | Artifact ID | Payload SHA-256 | Run 2 |
|---|---|---|---|
| S0 | `art_ssuxduiqkuxa3oenikwtlvbcuw` | `b63d385906dac4e3…` | identical |
| S1 | `art_kltorhksj2a2liumirrqaggiro` | `bc37e5872ced07c7…` | identical |
| S3 | `art_gxosgtydriicepknahjzrupdlw` | `ddb8e27e038c78fe…` | identical |
| S4 | `art_jinotbatu3tal5nd4afd4cftrb` | `def7e25b7e84f83b…` | identical |
| S5 | `art_6br6zoxutqqalez4klatbgvmom` | `33a3056ce6ab263e…` | identical |
| X0b | `art_3mwnq2hapecen5z4vtnmc5nevk` | `41ab34b1a0c94ee2…` | identical |
| V0 | `art_hqsbhvbjscbqqai3fxufas76s4` | `b81f7e639ecbbac7…` | identical |
| CV-SIM | `art_nyo23q77blump3uodaj3r4t472` | `409ddc0994258eab…` | identical |
| X0c | `art_ib4ze477pjvmh2nla4j6ei224o` | `57161cf2c4f5aa03…` | identical |
| S8 | `art_vhf3spwfnwgj2hsicpcvtmqnnn` | `20bfed11e6e54b2b…` | identical |
| S8f | `art_ei3dqotdckd76bia4uriuwbhak` | `06f7b527bac88872…` | identical |
| S4-E2 | `art_ya6ctkbhkzwzkdw73e4ifq3z7w` | `3a85273252205997…` | identical |

Configuration IDs (TEST-ONLY records):

| Prefix | ID |
|---|---|
| bsc | `bsc_r7piqzqv3uvx4nxlzxx3o6idxz` |
| dcf | `dcf_2aju3lsiyzb5gnoxq6hxceitd5` |
| evc | `evc_ycmv6reaavxtwajx5okca6wn6k` |
| gcf | `gcf_26nijqjysdqxufchytil5spas6` |
| orc | `orc_obpkbayep2bhz56h7cbkpl3ybu` |
| rcf | `rcf_3a33tvsgta2k6cihqhkimtydpt` |
| sbc | `sbc_xavxzbgkl3vzfyro4qsetagw6e` |

**Determinism result:** identical. All 12 artifact IDs and payload hashes, and the SHA-256 of every exported file, are equal across the two runs. Artifact IDs include the code commit and environment digest in their specification (AR-47 item 2), so they belong to commit `e6072ef`.

**End-to-end results on the fixture scene (Appendix N2 G2):**
- One episode, frames [0, 50), label H, minimum clearance 1.10 m, 5.0 s detected support, matched to its reference in label groups G1 and `any`.
- CT-E-28: S8, S8f and S4-E2 all trace to `source_file`.
- CT-E-26: the FX-12 E2 records export with mass null `not_supplied` and no forbidden content.

## 4. Status board

| Item | Status | Scope |
|---|---|---|
| Schemas, validators, identity and artifact builder (T-01, T-02) | Verified | fixtures |
| Registration, decode and coverage (T-05, T-06) | Verified | fixtures and generated clips |
| Oracle tracks and substrate S4 (T-08) | Verified | fixtures (N2, T8 checks) |
| Event engine S5 (T-09) | Verified | fixtures (N1, N2, T9–T13 checks) |
| Splits, sampling, validation store (T-10, T-11) | Verified | fixtures |
| Matching, metrics, estimators, completeness, attribution, fitness (T-12 to T-14) | Verified | fixtures |
| OBX export and reports (T-15) | Verified | fixture export |
| M0 integration pipeline (T-16) | Verified | one generated clip, oracle tracks |
| Empirically validated (scope) | none | — |

Nothing is empirically validated. Every result in this report comes from fixtures, generated clips or simulator-style oracle data.

## 5. Expected-value audit (`git log -p` on the fixture files)

No `expected` block in `fixtures/records/` has changed since its first commit (`f9994ac`, T-03). Every change to those files:

| Commit | File | Change | Authority |
|---|---|---|---|
| 193cd58 | TEST-ONLY-PARAMETERS.json | `v_part = 0.5` added; no value changed | Appendix T T8.6 (D-6, E-1.2.6) |
| 82341cb | N1-T10.json | inputs: Q = 1×12, 0×8; clearance frames 0–11; source cites T9.9; expected unchanged | Appendix T T9.9 (D-9, E-1.2.7, Architect amendment) |
| 82341cb | N1-T1 to T9, T11 | inputs gain `clearance_frames` (the measured frames N1 states); expected unchanged | T9.9 harness change (D-9) |
| 82341cb | TEST-ONLY-PARAMETERS.json | `k_c_turn = 3.0` added; no value changed | Appendix T T9.3 (D-9, E-1.2.7) |
| e6072ef | clips_manifest.json | `fx_m0_pipeline` entry added; existing entries byte-identical | T-16 integration clip (AR-47 item 1) |

Test assertions changed because a contract amendment changed a rule (each cites its section):
- T9.1: G3 episode [1, 9) → [0, 10); end-frame velocities; `t_motion_unknown_s`.
- T10.4: onset flags.
- T10.6: counts.
- T10.7: EV-M3.
- T11.1: the R1 borderline cases.
- T12.1: the CT-T11-02 R3 case.
- T12.5: the residual status.
- AR-44 item 2 as revised: flip_rate_le.
- The AR-42 ruling: the registered table set.

One recorded hand value was my own arithmetic slip and was corrected before its first commit: the Wilson 8/10 upper bound, 0.943315 → 0.9433178. It was later re-derived with `decimal` (Progress log).

## 6. Self-audit checklist (WORKPLAN §5)

- [x] Full suite passes from a clean clone with the locked environment (twice, 1704/1704).
- [x] Two complete runs produce identical artifact IDs for exact-class stages (section 3).
- [x] Every Appendix N expected value is asserted by at least one test: N1 T1–T13, N2 G1–G3, N3 A–D, N4 FX-TIE, N5 FX-W, N6 FX-CM. None was edited after its first commit (section 5). N7–N10 define M1a metrics with no M0 values.
- [x] No TEST-ONLY configuration appears in a research export or report: no research export exists; the class guard refuses one (CT-X-02).
- [x] Reports use only permitted wording and the three-status board (the report linter runs on every report; the M0 fixture report passed).
- [x] Open CRs and blockers are listed (section 7).
- [x] No data files, videos or secrets are committed (`git ls-files`: no media or archive files; the largest tracked file is text, about 97 KB).

One process incident: commit `37be0c8` was pushed while the suite failed at collection, and was fixed in the next commit (`d1dc51f`). Work-loop step 7 now gates every commit on the test run.

## 7. Open CRs and blockers

- CR-007 (footprint anchor on the camera-based path): DEFERRED to T-22 by D-8. It does not affect M0.
- Every other CR (CR-001 to CR-017) is closed.

## 8. Agent Resolutions

47 ARs in total; 20 Architect-reviewed, 27 pending: AR-1, AR-2, AR-3, AR-4, AR-5, AR-6, AR-8, AR-9, AR-10, AR-11, AR-12, AR-13, AR-14, AR-15, AR-16, AR-17, AR-18, AR-19, AR-20, AR-21, AR-23, AR-24, AR-26, AR-29, AR-32, AR-33, AR-47.

| AR | Title | Status |
|---|---|---|
| AR-1 | `version` column on `clock_alignment` and `calibration` | pending |
| AR-2 | Column types where the contract lists names only | pending |
| AR-3 | ID prefixes the contract does not give | pending |
| AR-4 | Storage form of `<table>_nk` | pending |
| AR-5 | Fields of `decode_config`, `geometry_config`, `sampling_plan_config` | pending |
| AR-6 | Configuration field names given only in prose; `version_label` | pending |
| AR-7 | `ts` columns in artifact tables and their JCS form | Architect-reviewed (11 Nov 2026; revised) |
| AR-8 | Which values count as sentinels (VR-E-003) | pending |
| AR-9 | `label_source` on `ref_geometry` | pending |
| AR-10 | VR-E-019 does not exist | pending |
| AR-11 | Scope of VR-E-041 and `stage_error.severity` | pending |
| AR-12 | Where the VR-E-070 ID applies | pending |
| AR-13 | Inputs for VR-E-018 and VR-E-021 | pending |
| AR-14 | Schema version string | pending |
| AR-15 | Rounding of microsecond keys | pending |
| AR-16 | ART-ISO prefixes and the error for schema violations | pending |
| AR-17 | Scope of CT-I-03, 04, 07, 08 at T-02 | pending |
| AR-18 | Integers beyond the range RFC 8785 can hash | pending |
| AR-19 | Test-only value for `n_miss` | pending |
| AR-20 | Design details of FX-ID box fixtures | pending |
| AR-21 | Delivering timestamp faults to the decoder; Case A–D layouts | pending |
| AR-22 | Default camera groups | Architect-reviewed (11 Nov 2026; accepted) |
| AR-23 | Fixture records without key fields | pending |
| AR-24 | Representation of the T7 declaration and the final-frame variant | pending |
| AR-25 | "Decode order" is bitstream order; presentation index is decoder output order | Architect-reviewed (11 Nov 2026; accepted) |
| AR-26 | PyAV does not expose FFmpeg's best-effort timestamp | pending |
| AR-27 | Exclusion rules version `rv1`; VFR flag; packet-to-frame matching | Architect-reviewed (11 Nov 2026; reviewed) |
| AR-28 | Fixture value of *f_untimed* for Cases B and C | Architect-reviewed (11 Nov 2026; accepted) |
| AR-29 | Oracle `tracked` points count as detected | pending |
| AR-30 | Frame-level activity state | Architect-reviewed (12 Nov 2026; accepted) |
| AR-31 | Metadata leakage edges | Architect-reviewed (12 Nov 2026; accepted) |
| AR-32 | Initial partition assignment | pending |
| AR-33 | Mechanics of the RES draw and bootstrap percentiles | pending |
| AR-34 | T2b audits and declared shared sessions | Architect-reviewed (12 Nov 2026; accepted) |
| AR-35 | Schema and labelling details needed to implement T8 | Architect-reviewed (12 Nov 2026; accepted, part revised) |
| AR-36 | Status-log and CV-SIM conventions | Architect-reviewed (12 Nov 2026; accepted) |
| AR-37 | Reading Appendix N1 rows at flag level | Architect-reviewed (12 Nov 2026; accepted) |
| AR-38 | Representation and reading choices for T9 (T-09) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-39 | Association and matching details (T-12) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-40 | Representation details of the S5 artifact under T10 (T-09) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-41 | Mechanics of the Target B and paired bootstraps and the null cases of N5 estimators (T-13) | Architect-reviewed (12 Nov 2026; accepted, part revised) |
| AR-42 | Attribution rule inputs and the match-run inputs digest (T-14) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-43 | Completeness record details (T-14) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-44 | Fitness-engine representation details (T-14) | Architect-reviewed (12 Nov 2026; accepted, part revised) |
| AR-45 | Representation details of the T12 conformance (T-14) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-46 | OBX file format and report wording mechanics (T-15) | Architect-reviewed (12 Nov 2026; accepted) |
| AR-47 | M0 integration run details (T-16) | pending |

## 9. Usage and time notes

- **Calendar:** 9 to 12 November 2026, in single-agent sessions. Token and cost use were not measured by the agent.
- **Run times on the Owner's MacBook Air:** full suite about 27 s; M0 pipeline about 1.4 s per run; clip generation is included in the pipeline.
- **Contract amendments during M0:** E-1.2.3 to E-1.2.11 (Appendix T T1–T13), driven by CR-001 to CR-017.

## 10. Decisions needed

- **G-M0:** the Owner reviews M0 and writes "M0 accepted" in `DECISIONS_NEEDED.md`. Recommended: an independent review by the Research Architect, including the 27 pending ARs.
- **D-8:** deferred to T-22; reopen with GV-03/GV-04 evidence.
- **Before M1a:** the §0 download approval applies only after M0 is accepted, and only after T-17 records source authenticity and licence terms.
