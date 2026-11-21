# W-02 — E-1.2.23 corrections to T23: regression and reference-protection evidence (D-49)

> **Alert source (T23.26).** AI alerts in this demo come from configuration BL-6 (detector_path_pilot_d45). On SDG validation that source covers 12 % of worker–forklift co-visible frames (CM-03); most interactions produce no alert. Workflow measures describe the workflow, not the system's accuracy. Reported figures: CM-03 0.12, EV-M1 0.11, EV-M2 0.22 (reports/M1b_pilot_report.md (m0-implementation ec63113), BL-6 column C).

**Branch:** `v02-review-ui` only. No merge into `m0-implementation`, no pull request, no force-push. **Contract:** E-1.2.23 (Appendix T T23.16–T23.27, appended verbatim). **Status:** implemented and verified on fixtures. Nothing here is empirically validated. The workflow is a B-workstream prototype (D-49.1 section 2): its measures describe the workflow, not the system's accuracy.

Hard limits kept: no stored record under `out/review/` was deleted, rewritten or reordered (SHA-256 of every file compared before and after each check); no T22 batch, reference assessment, adjudication or manager decision in any store; no S5 or S8 run; no evaluation result; nothing on the test partition.

## 1. What changed (summary)

- **Schema (the scoped part):** `adjudication.reference_class` nullable with `reference_class_null_reason`; VR-E-056 (T23.16 b); stored rows without the reason read as null (T23.16 f); `validation.reference.reference_adjudications()` and the static check of T23.16 (e).
- **V-02 store:** store registry (`out/review/registry.json`, lists `out/review/main` and `out/review/demo_20261119`); unregistered stores refuse to open; demo exclusion and exposure across all registered stores (T23.25 b, c); workflow manager rows refused at once for reference work (T23.25 d); tier printed only with the namespace (T23.16 c); attestation text extended.
- **Workflow:** safety-manager adjudications and status entries now written (FX-14a/b strict xfails removed, they pass); `am_split` / `closed_split`, `sm_confirm_duplicate`, `withdraw_recordability`; `group_resolution`; duplicate rules; recordability lifecycle and definitive I9; kind follows label; as-of views with "revised after first decision" and "undecided"; monitoring = usable ∩ processed, union area time; observability categories and I8; T23.24 combined values (view-time only, never stored); source-quality banner; demo-only establishments; no establishment sorting; T23.22 user text stored verbatim and shown in "entered by" blocks; section 5 linter terms.
- **Records:** CR-030 closed, AR-63 decided (D-49.1 section 7); **CR-031** (13 items) and **AR-64** (17 items) opened.

## 2. Tests

| Run | Command | Result |
|---|---|---|
| v02, run 1 | `.venv/bin/python -m pytest -q -p no:cacheprovider` | 2715 passed |
| v02, final code, runs 2 and 3 | same | 2715 passed, 2715 passed (identical); fixture regeneration byte-identical |
| m0-implementation (ec63113), main folder, run 1 / 2 | same, in `../ai-surveillance` | 2485 passed, 11 skipped / 2485 passed, 11 skipped |
| m0-implementation + scoped change, scratch clone, run 1 / 2 | same, in a clone of ec63113 with only the scoped files applied | 2504 passed, 13 skipped, 1 failed / identical |

The one failure in the scratch clone is `tests/m1b/test_det_env.py::test_det_env_points_inside_the_repository_and_is_ignored`: `git check-ignore` exits 128 because the clone's `out/` is a symlink to the main folder's (set up for the data). It is caused by the scratch setup, not by the change; it passes in the main folder. The 35 tests of the scoped files pass there (FX-14j, FX-14k, FX-14m and the accessor part of FX-14l; `tests/schema/test_t22_review_time.py` with the E-1.2.23 adjudication field list).

New on v02: FX-14j to FX-14ad (fixture files and retyped expected values in `tests/fixtures_t03/test_t23_fixtures.py`; application tests in `tests/workflow/test_t23_e1223.py`, `tests/workflow/test_t23_25_stores.py`, `tests/review/test_t23_16_isolation.py`; schema and accessor tests). No expected value was edited. Setups changed by the ruling: the fixture establishment is a demo one (T23.27 b), fixture coverage is processed (T23.23 a), FX-14d gains the area manager's observability step and FX-14e a group_resolution (CR-031 item 3). Assertions that pinned CR-030 holding behaviour or the reversed AR-63 item 8 were replaced (the touching-interval refusal, the "not written" notice, the refusal of human text, the CR-030 readings).

## 3. Demo views re-rendered (step 2 d)

`PYTHONPATH=src .venv/bin/python research/workflow/rerender_demo.py <scratch>` copies `out/review/demo_20261119` twice, gives each copy a throwaway Owner profile and fetches every page as the Owner, once with the code at 42957f2 and once with this code. The original store's 10 files are byte-identical before and after (`original_unchanged: true`). All 25 pages return 200 under both codes. No decision was taken.

What changed on the pages:
- every page: the T23.27 (f) statement; pages with AI alerts and the regulator view: the T23.26 banner. The store's manifest predates E-1.2.23 and records no source figure, so it reads "accuracy of the alert source: not reported" (CR-031 item 9);
- report pages (8): "grouping basis not recorded (report created before E-1.2.23)"; the T23.24 member-clearance block. The episodes record no calibration tier, so no combined value is shown ("not combined: the geometry method or calibration tier is not recorded for every member"); `min_clearance_m` is no longer listed as a field; `duration_s` is labelled "span of member episodes". The stored descriptions keep the T23 template ("Minimum measured separation … m (full_camera)"): they are records and are not rewritten;
- indicators and regulator views (8 + 8): the CR-030 "not determined" readings are gone. Monitored time is now the union of usable and processed coverage: for establishment `…4cde69`, 2026-W45, monitored area-hours 0.0056 against 0.0250 camera-hours (the old "usable, cameras with source output" reading, a sum) and 13 unprocessed cameras; the rate prints "0 in 0.0056 monitored area-hours. Absence of an alert is not absence of an event."; F1 and F2 print "not evaluated: insufficient n"; each view prints `as_of`, the truncated log length and head hash;
- setup and home: the statement; no other change.

## 4. D-49.1 section 6.2 (regression and compatibility)

| Item | What was run | Result |
|---|---|---|
| 1 | full suite twice on each branch (section 2) | **pass** on v02 (2715, twice) and on m0-implementation (2485 + 11 skipped, twice). m0 + scoped change: pass except the scratch-setup failure explained in section 2 |
| 2 | clean clones of e6072ef: (a) as committed, (b) with only the adjudication schema change, VR-E-056, the minimal-row line and the accessor applied (uncommitted, so `git rev-parse HEAD` is still e6072ef); `python -m rq1.pipeline.m0 <dir>` twice in each | **pass.** All 12 artifact IDs and payload SHA-256 prefixes equal the `reports/M0_report.md` table in all four runs; (b) equals (a) on every ID, payload hash and exported file (48 files, execution records excluded) |
| 3 | `ids.artifact.verify` (CT-FK-05 read-back) on every artifact folder under `out/m1a/` and `out/m1b/pilot/` with the E-1.2.23 schema (`research/workflow/w02_checks.py`) | **incomplete.** The full run (7,473 artifact folders, 3.8 GB; 36 SmartSpaces artifacts over 10 MB take up to 3.7 min each) was stopped by Claude Code because the computer ran low on memory, after 4,000 of 7,473 folders; its counts are written only at the end, so no full result exists. Spot checks before it, all **pass**: 20 pilot artifacts, 15 random M1a artifacts and the largest SmartSpaces artifact (`art_2f4i5s2afniuqjskvxg7klqugl`). To finish: rerun `w02_checks.py` on mains power with memory free (it uses one process per core; a run with fewer workers needs less memory). **Not done either:** the S0–S5 rebuild of three SDG cameras, because rebuilding S5 is an S5 run, which the D-49 hard limits forbid (CR-031 item 10) |
| 4 | every adjudication, assessment, status entry and report-log entry of every store under `out/review/`, read with the E-1.2.23 reader, validated; every hash chain verified (`w02_checks.py`, read-only) | **pass**, with one expected exception, see the table below |
| 5 | FX-14j–m on the m0 clone with the scoped change; FX-14j–p on v02 | **pass** (FX-14l on m0: the accessor and EV-M12 population part; its kappa and batch-draw parts need the V-02 store, which is not on m0) |
| 6 | files a scoped merge would carry | listed below; **not merged** |

Store records (item 4):

| Store | Registered | Adjudications | Assessments | Status entries | Report-log entries | Issues | Status chain | Report chain |
|---|---|---|---|---|---|---|---|---|
| `out/review/demo/store` (V-02 fixture store) | no | 9 | 17 | 9 | 0 | none | intact | — |
| `out/review/demo_20261119` (T23 demo) | yes | 0 | 0 | 0 | 8 | none | — | intact |
| `out/review/w01_fixtures/a/store` (W-01 fixture store) | no | 0 | 5 | 5 | 13 | 1 | intact | broken at seq 0 |
| `out/review/main` | yes | not created yet | | | | | | |

The W-01 fixture store's broken report chain and its `pXnding_am` entry are the deliberate FX-14g tamper made by `research/workflow/make_screenshots.py` for screenshot `10_broken_chain`; the store is fixture output. No stored candidate_review adjudication exists in any store, so no row needs the T23.16 (f) reason.

Files of the scoped merge (item 6), as applied to the scratch clone of `m0-implementation`:
- `docs/contract/RQ1_Contract_Appendix_T_E-1.2.3.md` (T23 and T23.16–T23.27; T23 is not yet on `m0-implementation`) and `CLAUDE.md` (contract line, the "Never" line, the new "Still raise a CR" item);
- `src/rq1/schema/tables.py`: the adjudication hunk only (`reference_class? reference_class`);
- `src/rq1/schema/validate.py`: VR-E-056 (`check_adjudication_class`);
- `src/rq1/schema/registry.py`: the `minimal_row("adjudication")` line;
- `src/rq1/validation/reference.py` (new: reader, accessor, EV-M12 population, static check);
- tests: `tests/schema/test_t23_16_adjudication.py`, `tests/validation/test_t23_16_reference_access.py` (new, self-contained), `tests/schema/test_t22_review_time.py` (adjudication field list).
No `src/rq1/workflow/` file and no `wf_*` table. The records (D-49, CR-030, CR-031, AR-63, AR-64) would need their own numbering note on `m0-implementation`.

## 5. D-49.1 section 6.3 (reference protection; report only)

**Stores and batches.** Registry (`out/review/registry.json`): `out/review/main` (not created) and `out/review/demo_20261119`. The only batches under `out/review/` are two fixture batches of the unregistered V-02 fixture store `out/review/demo/store` (dataset `fixture`, configuration `rcf_demo…`): a pilot of 3 targets and a batch of 8. Neither holds a target from a demo run (the demo store's 90 demo recordings), and no annotator of either batch is exposed under T23.25 (c). No batch on the SDG frame exists in any store.

**T22 frame after the demo exclusion** (BL-6 episodes of the T-21 oracle run, SDG validation, `rcf_l2jqmbmovogf6zvgwcxyrs6qvx`):

| Summary label | Episodes in the frame | After excluding the 9 demo runs (90 recordings) | CR-028 allocation for n_batch = 60 (six strata) | T22.6 / T22.14 (e) allocation now |
|---|---|---|---|---|
| CT | 7 | **0** | 7 | — (stratum absent) |
| UD | 44 | 31 | 11 | 15 |
| NM | 30 | 24 | 11 | 15 |
| PC | 212 | 151 | 11 | 15 |
| H | 17 | 15 | 11 | 15 |
| O | 9 | **0** | 9 | — (stratum absent) |
| total | 319 | 221 (98 excluded) | 60 | 60 |

With four strata the equal share is 15; no present stratum is below it, so the water-filling caps nothing and the allocation is the same for every seed. But **the demo runs hold every CT and every O episode of the frame**: a batch drawn now would have no CT and no O target. This is the "stratum falls short" condition of section 6.3 item 3. **STOP for an Owner decision (D-51; CR-031 item 13).** No batch was drawn, redrawn, discarded or resized; no quota changed.

## 6. Open points

CR-031 (13 items, nothing chosen where marked) and AR-64 (17 representation items) are in `docs/CHANGE_REQUESTS.md`; the decision request is D-51 in `DECISIONS_NEEDED.md`.
