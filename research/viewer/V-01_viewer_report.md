# V-01 — Truth replay viewer (Owner tooling, read-only)

**Status: implemented and verified on fixtures** (acceptance tests of the V-01 task text, item 6). Pages generated for the
held validation-partition recordings (below). This is a viewing aid: it produces **no result, metric, flag, label, episode
or artifact** that enters any evaluation, and nothing in it counts as part of T-21. It is off the critical path, changes
no contract text, and does not unblock T-21.

| Item | Value |
|---|---|
| Branch | `v01-truth-viewer`, created from `m0-implementation` at `145c315` (T-21 BLOCKED on D-38 / CR-025) |
| V-01 commit | `e76b45a` (code, tests, report, WORKPLAN); this line was added in the follow-up commit "V-01: record final commit in the viewer report" |
| Branch history note | `007dd15` "D-38 decided (option A); session end" on this branch is a commit by the agent in another tab, made while the shared working directory had this branch checked out; it carries the D-38 record and swept in the first draft of the viewer files. The same D-38 record is on `m0-implementation` as `f90c5bd` (identical edits to `DECISIONS_NEEDED.md` and `WORKPLAN.md`), so a merge applies them once. No history was rewritten. |
| Contract | E-1.2.18 (no change) |
| Pre-registration | `docs/preregistration_FROZEN.md`, version 1, SHA-256 `b2d8e6ce53aff1b2c5f48cf3e50915c980b32f75f224fdf0ae36881311c341a3` |
| Split | X0b `art_w5v3ldr43xdsqc6l4zifmjkuuj` (frozen; verified by reconstruction before use) |
| Packages | `requirements.lock` only; nothing installed |
| Tests | `tests/viewer/test_v01_viewer.py` (18) and `tests/viewer/test_v01_marks.py` (11, item 5b); full suite 1892/1892, twice |

## How to run

From the repository root, in `.venv`:

```
PYTHONPATH=src python -m rq1.viewer --rec <rec_id> [--rec <rec_id> ...]
PYTHONPATH=src python -m rq1.viewer --all-validation [--dataset sdg|smartspaces]
```

Pages go to `out/viewer/` (git-ignored): one file per recording, named `<dataset>__<run>__<camera>.html`, plus
`out/viewer/index.html` with `--all-validation`. Open a page in any browser by double-clicking it: it is self-contained
(embedded JSON and plain JavaScript on a canvas; no server, no network, no external file). The exit status is 2 when any
recording is refused.

Refusals (ERR-SPEC): any recording when no frozen split exists (no freeze record, or its X0b artifact missing or not
reconstructing); any recording whose leakage group is not in the validation partition, or that is not in the split
(SmartSpaces `Warehouse_001`, outside X0b v1); a recording without usable simulator truth (T17.4) or with truth refused
(T17.5); an S1 artifact that does not verify or whose decode configuration is not the frozen §4.1 values. The partition
check runs before any data is read. D-37 (test partition reserved) is respected: nothing is built for a test recording.

Cost: an SDG page takes about 1 s (about 150 KB). A SmartSpaces page is about 20 MB; the first SmartSpaces camera of a run
takes about 60 s and 1.8 GB of memory (parsing the 280 MB `ground_truth.json`, which is then cached for the other cameras).

## What a page shows

- **Banner** on every page and on the index: "Truth replay, validation partition, simulator truth. Not a system output.
  Thresholds are display settings."
- **Header:** dataset row, run, camera, recording ID, viewpoint class, `low_light` tag (rv2, AR-51), partition, split
  artifact, code commit (with `+uncommitted` when the working tree had changes), contract version, pre-registration SHA-256,
  number of frames.
- **Top-down floor view** in metres (world frame, x right, y up) with a 1 m grid (thinned to 5 m or 10 m when zoomed far out,
  and labelled so) and a scale bar. Pan by dragging, zoom with the scroll wheel; "follow pair" centres the selected pair.
  - Forklift: the oriented prior footprint (pre-registered size; SDG 3.03 × 1.13 m, SmartSpaces 2.68 × 1.16 m), solid fill;
    the circumscribed disc when the S4 yaw is null (T8.2). The dataset 3D box footprint as a dashed outline.
  - Person: the disc of radius r = 0.30 m.
  - Clearance line between the footprints, labelled in metres: the S4 signed footprint distance. Drawn for the selected
    pair, and for every other pair whose clearance is within the d_p slider (checkbox).
  - Rings at d_p and d_pc around the forklift footprint (offset of the footprint by that clearance: a person disc touching
    the ring has that clearance).
  - Velocity arrows (length = 1 s of travel) labelled in m/s, and a faint constant-velocity "ghost" of each footprint at
    t + τ (translated, yaw unchanged, as T15.1).
  - Per-object state: visible (oracle point `tracked`); not visible with a predicted oracle point (dashed outline, "pred");
    not visible and lost (dashed hollow marker at the simulator position, "lost", no clearance); ineligible frame (grey
    cross at the simulator position). The side panel lists every object's state and speed on the current frame.
- **Timeline** (click to jump): clearance of the selected pair with lines at d_p, d_pc and 0; person and forklift speed;
  forklift yaw rate (deg/s) shaded by `forklift_turning` (T20.2: amber true, green false, grey unknown) with a line at
  e_fturn; oracle-state strips for the person and the forklift (visible, predicted, lost, ineligible), not-visible runs
  longer than the g_max slider outlined in red, and a strip of ineligible frames.
- **Controls:** play / pause (space), 0.25×–2×, frame slider and arrow keys, pair selector (default: the pair with the
  smallest clearance in the recording, a display choice only), sliders for d_p, d_pc, τ, g_max and e_fturn starting at the
  pre-registered values (2.0 m, 1.0 m, 2.0 s, 15 frames, 5°/s) with a reset button. **Sliders change the drawing only.**
  The g_max slider does not rebuild the oracle points (they are built at the pre-registered 15); it only outlines runs
  longer than its value. The e_fturn slider re-shades the timeline from the T20.2 rate with the same rule (true when the
  rate > e_fturn); at 5°/s the stored T20.2 states are shown.

## Where the numbers come from (nothing re-implemented)

| Shown | Source |
|---|---|
| Oracle points and their states | `adapters.oracle_truth.camera_tracks` at g_max = 15 (T17–T19, T20.1), its per-frame outcomes; `s3_truth`; `substrate.oracle.OracleTrackSource` (in memory only) |
| Simulator truth per frame | the T-18 driver's readers `Annotations`, `sdg_frames`, `smartspaces_frames` (`research/datasets/part3/t17_oracle.py`), unchanged |
| Positions, speed, velocity, forklift yaw | the S4 builder's object-state code (`SubstrateBuilder._object_states`, T8.2 as corrected by T9.1), simulator-truth positions; no POW, pair series, exposure profile or activity segment is built |
| Clearance | `substrate.geometry.clearance` (prior rectangle) or `disc_clearance` with `circumscribed_radius` (null yaw), applied as the S4 builder applies them to a pair-frame |
| Yaw rate, `forklift_turning` | `evaluation.strata.forklift_turning` (T20.2), w_turn 0.5 s, e_fturn 5°/s |
| Not-visible runs | `oracle_truth.not_visible_spans`, `not_visible_runs` (camera frames and eligible frames) |
| Eligibility, timestamps | the held S1 artifacts (verified by reconstruction) |

Not called: the S5 rule providers, the episode lifecycle, S8. The viewer package imports no `rq1.events` module and no
`rq1.evaluation` module except `rq1.evaluation.strata` (static check in the tests).

## Acceptance tests (V-01 item 6) — `tests/viewer/test_v01_viewer.py`

| Test | Pins |
|---|---|
| `test_refuses_a_test_partition_recording`, `test_refuses_a_recording_absent_from_the_split`, `test_frozen_split_on_disk_…` | ERR-SPEC for a test-partition recording and for one outside the split; the frozen X0b on disk |
| `test_refuses_everything_when_no_frozen_split_exists`, `test_refuses_when_the_freeze_record_names_a_split_artifact_that_is_missing` | ERR-SPEC with no frozen split |
| `test_clearance_and_speeds_equal_the_s4_outputs_on_the_same_frames` | embedded speeds = S4 `object_state.speed_mps`, embedded clearance = S4 `pair_series.clearance_m`, from a full S4 build on the same frames, within 1e-9; hand values (forklift 1 m/s; clearance 1.2 m on frames 25–45) |
| `test_t20_1_case_renders_as_one_lost_run_of_20_frames` | the T20.1 case (a dataset-visible ineligible frame joins the run): one lost run of 20 frames, no positions on it; the forklift's ineligible frame shown as ineligible |
| `test_t20_2_cases_give_the_expected_shading` | constant yaw → false; 75°/s → true (rate 75°/s); half-turn jump → false; null yaw → unknown |
| `test_same_inputs_give_byte_identical_html`, held-data test | byte-identical HTML twice (fixture and a held SDG recording) |
| `test_html_has_no_network_url_no_test_only_value_and_the_banner`, held-data test | no network URL or external resource, no TEST-ONLY value, the banner, the wording rules |
| `test_viewer_imports_no_s5_or_s8_module` | static import check |
| `test_slider_start_values_are_the_frozen_values` | slider start values and S4 inputs read back from `docs/preregistration_FROZEN.md` |
| `test_s1_decode_record_must_carry_the_frozen_values`, `test_embedded_json_cannot_close_the_script_element` | S1 reuse condition; embedding safety |

## Decisions taken in this task (Owner, V-01 session, 14 Nov 2026)

1. **T20.2 import.** The only T20.2 code is `rq1.evaluation.strata` (S8 package), which imports `wrap` from
   `rq1.events.providers` (S5). Owner decision: the viewer imports `rq1.evaluation.strata` as the one named exception
   (report-time, stores nothing, runs no S8); the static check forbids every other `rq1.evaluation` module and all of
   `rq1.events` in the viewer's own imports. Importing `strata` loads `rq1.events.providers` and `rq1.events.engine`
   transitively; the only function reached there is `wrap` (through `strata.fold`). No analysis code was changed.
2. **S1 reuse.** The held S1 artifacts were decoded before the freeze under a decode record labelled as test parameters,
   with the same numbers as the frozen §4.1 values (k_sup 1.5, f_untimed 0.05, f_sub 0.10, rv2). Owner decision: reuse
   them. The viewer accepts an S1 artifact only when its decode configuration ID (`dcf_xv2ryouaw22oljgqmrpylb4uqz`, all
   259 validation recordings) rebuilds from a record with exactly the frozen numbers; the label never reaches a page.

## Recordings generated

`PYTHONPATH=src python -m rq1.viewer --all-validation` on 14 Nov 2026 (259 validation-partition recordings held with an
S1 artifact: 240 SDG cameras of the 24 validation runs, 19 SmartSpaces `Warehouse_000` cameras):

| Dataset row | Pages written | Refused | Size |
|---|---|---|---|
| SDG (24 validation runs) | **226** | 14: no usable simulator truth (T17.4), the same 14 cameras the frozen V0 plan `m1a-sdg-validation` lists as outside | about 150 KB each |
| SmartSpaces `Warehouse_000` | **19** | 0 | about 20 MB each |
| **Total** | **245** (+ `index.html`) | 14 | 481 MB in `out/viewer/` (git-ignored) |

No test-partition recording was requested or built. These pages were generated from the working tree before the V-01
commit, so their header shows `145c315…+uncommitted`; regenerate after checkout for a clean header (the content is
otherwise the same).

## Owner marking mode (item 5b, D-36 follow-up, 14 Nov 2026)

- **Use:** the "Marking mode" button on a page (or open the page with `#mark` at the end of its address). Per clip:
  "Would you send this clip for review? yes / no / unsure", and a free-text note.
- **What is shown in marking mode:** the footprints (forklift prior footprint and dataset 3D box outline, person disc;
  predicted points keep their dashed outline), the frame scrubber with play controls, and the time. Hidden: rings, the
  clearance line and its label, velocity arrows and speed labels, ghosts, the timeline (with its threshold lines and turning
  shading), the sliders, the lost and ineligible markers, the pair options and the numeric side panel. The 1 m grid and the
  scale bar stay, so that distances can still be judged by eye. Each overlay is drawn by its own function, and every call is
  behind the marking-mode switch (`test_marking_mode_gates_every_overlay_in_the_page_script`); checked in headless Chrome.
- **Where marks go:** `out/viewer/owner_marks.json` (git-ignored), labelled "exploratory, Owner impression, not a
  reference label", `read_by: "no stage"`. A page opened from disk cannot write a file by itself, so:
  - in Chrome (and other Chromium browsers), "Save to owner_marks.json…" asks once for the file
    (pick `out/viewer/owner_marks.json`), and merges this clip's mark into it;
  - in any browser, "Download this mark" saves `owner_mark_<rec_id>.json`; then
    `PYTHONPATH=src python -m rq1.viewer --import-marks ~/Downloads/owner_mark_*.json` merges the files into
    `out/viewer/owner_marks.json` (a later mark of the same clip replaces the earlier one).
  The import refuses (ERR-SPEC) a file whose label, question or schema differ, an answer other than yes / no / unsure, a
  non-text field, or a clip outside the validation partition of the frozen split.
- **Fields per clip:** answer, note, run, camera, dataset row, and the code commit of the page. No timestamp is stored.
- **Read by no stage:** only `src/rq1/viewer/marks.py` names the file; no other module of `rq1` does, and the page builder
  does not read it (`test_marks_are_read_by_no_stage`). Nothing in it feeds a reference, label, metric or configuration.
- Tests: `tests/viewer/test_v01_marks.py` (11).

## Known limits

1. **Truth only, display only.** Every page is simulator truth through the oracle path. Agreement between what a page
   shows and any later system output on the oracle path is rule-conformance evidence only (T17.6), and nothing on a page
   is a result. Synthetic data: nothing here is "empirically validated".
2. **Clearance outside POWs.** S4 stores clearance only on POW frames; the viewer computes it with the same functions on
   every eligible frame where both objects have a position. On POW frames the values are equal (tested); elsewhere there is
   no S4 value to compare with.
3. **SmartSpaces footprint prior.** One prior, 2.68 × 1.16 m, serves both SmartSpaces forklift box sizes (D-34 B.5). On a
   1.87 × 1.13 m forklift the solid prior is larger than the dashed dataset box (by 0.81 m in length); clearance uses the
   prior, as S4 does.
4. **Pallet trucks** (SmartSpaces) are drawn by their dataset box only and pair with nobody (pair classes: forklift). Their
   speeds use the S4 object-state code with the forklift prior's ID; the prior does not enter those values.
5. **Lost and ineligible object-frames** are drawn at the simulator position for orientation (rounded to 0.1 mm); they
   carry no oracle point, so no clearance and no speed are shown for them.
6. **g_max slider** only outlines runs; the points are not rebuilt at another g_max (that would be a T-18 sensitivity run,
   not a display). The e_fturn slider re-applies the T20.2 threshold to the stored rate in the browser; at 5°/s the stored
   states are used.
7. **Dataset row label.** The T16 row name of SDG contains the dataset's own words "near-miss"; under the wording rules the
   pages show the row by its dataset ID ("SDG-Warehouse, nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes
   (synthetic_rendered)").
8. **Optional items.** Item 5a (camera frame beside the floor view) was not built. Item 5b was built (D-36 follow-up; see
   "Owner marking mode" below).
9. **Browser checks.** The JavaScript is not exercised by the test suite (no JavaScript runtime in `requirements.lock`). It
   was checked for syntax and rendered in headless Chrome on one SDG and one SmartSpaces page, with no page error.
   SmartSpaces pages (about 20 MB, 9,000 frames) take a few seconds to open.
10. **Code commit in the header** is the commit the generator ran from; pages generated from a working tree with changes
    say `+uncommitted`. Regenerate after committing for a clean header.

## Viewing note for the Owner (not a finding, not a CR)

On SDG `1f153860933aed78a2e3_run_20_seed_139404633` / `ceiling_00` the forklift's box long axis (its T8.2 yaw, CR-023)
turns at a median 65°/s (maximum 75°/s) over the 10 s, and its centre moves at about 0.8 m/s almost at right angles to that
axis (median folded angle between the S4 heading and the yaw 84°). That is what rotation about a point about 0.6 m from the
box centre, on the long axis, looks like. It bears on how `forklift_turning` and R5 `e_turn` (1.5 rad/s = 86°/s) behave on
SDG. Whether other runs show the same motion was not checked here; the pages are the place to look.
