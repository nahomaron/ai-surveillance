# W-01 — T23 reporting workflow: implementation report (D-48)

Branch `v02-review-ui` only, not merged into `m0-implementation`. Contract **E-1.2.22** (Appendix T T23) exists on this branch only until the Owner merges it. Status: **implemented and verified on fixtures**. Nothing here is empirically validated. The demo runs on synthetic SDG data, and no manager decision was taken by the agent.

## What was built

One local application: the V-02 server and sign-in, extended with the T23.1 roles. It binds to 127.0.0.1 only, uses no network URL, and every workflow page passes the T23.12 wording linter before it is sent.

| Screen | Who | Path |
|---|---|---|
| Area manager inbox: pending reports of the person's areas; report page with pre-filled fields, evidence clip(s), the AI label as "candidate …", approve / reject / mark duplicate, edit fields | area_manager | `/wf/inbox`, `/wf/report/<id>` |
| Safety manager queue: rejected reports (uphold or overturn), incidents waiting for recordability, recorded reports (reclassify), closed reports (reopen); recordability form | safety_manager | `/wf/queue` |
| File a report (near_miss or incident) | any signed-in workflow user, Owner | `/wf/file` |
| Report page: current fields (pre-filled ones marked), full history from the report log, hash-chain result of the report log and the status log; 301-style export for incidents | per report | `/wf/report/<id>`, `…/301.json`, `…/301.csv` |
| Indicators I1–I9 and flags F1–F4 per establishment, area and ISO week, with the log length and head hash used | area_manager, safety_manager, owner | `/wf/indicators` |
| Simulated regulator view (read-only) with JSON and CSV export | oversight, owner | `/wf/regulator` |
| Owner setup: establishments, areas, users, hours worked, workflow parameters, demo draw | owner | `/wf/setup` |

Code: `src/rq1/workflow/`:
- `rules.py`: T23 as pure functions.
- `store.py`: tables, report log, actions.
- `server.py`: pages.
- `demo.py`: the T23.11 draw.
- `clips.py`: evidence-clip frame hashes.

Schema: the T23.15 tables in `src/rq1/schema/tables.py`. Tests: `tests/workflow/` and `tests/fixtures_t03/test_t23_fixtures.py`.

## How to run the demo end to end

From the repository root:

1. **Owner profile on the demo store** (the agent did not create one; you choose the passphrase):
   `PYTHONPATH=src .venv/bin/python -m rq1.review init --store out/review/demo_20261119 --owner <your pseudonym>`
2. **Start the application:**
   `PYTHONPATH=src .venv/bin/python -m rq1.review serve --store out/review/demo_20261119 --root .`
   Then open http://127.0.0.1:8765/ and sign in as the Owner.
3. **Workflow setup** (`/wf/setup`):
   - Create the users you will play, pseudonyms only. For example, one area manager for the areas of one establishment, one safety manager for that establishment, a worker and an oversight user. Use another area manager for the other establishments, or give one person several roles. A person who decided a report as area manager cannot act on it as safety manager.
   - Optionally enter hours worked per establishment and ISO week (2026-W45 to W48 on the simulated calendar).
   - Optionally lower n_flag_min / n_flag_min_sm for the demo; a new wf_config row is written and the views print the values used.
4. **Play the roles.** Sign out and sign in as each user:
   - area manager: inbox, then open a report, watch the clip, and approve, reject or mark duplicate;
   - safety manager: queue;
   - worker: file a report;
   - oversight: regulator view.
5. **Check the logs.** Every report page shows both hash-chain results. `PYTHONPATH=src .venv/bin/python -m rq1.workflow summary --store out/review/demo_20261119` prints the manifest summary and the verification.

## Demo manifest summary (seed 2026111903)

- **Store:** `out/review/demo_20261119/` (new; git-ignored).
- **Manifest:** `demo_manifest.json`, demo_id `dmo_01a1f6f5-dea5-7395-bb4a-6129ddfb8409`.
- **Source:** `detector_path_pilot_d45`. The BL-6 S5 artifacts of the D-45 detector-path pilot, column C (`out/m1b/pilot`), existed when the step started, so they were used, not the T-21 oracle artifacts. Column C' is post-hoc and was not used.
- **Draw:** 3 runs per D-35 family, giving 3 simulated establishments and 9 areas (one per run, all of its cameras). Calendar: 4 weeks from Monday 2026-11-02 (2026-W45 to W48).

| Family | Establishment | Run | Cameras (with pilot output) | AI reports | Members |
|---|---|---|---|---|---|
| warehouse_osmos | Simulated warehouse North | 91fb07… run 1 | 9 (8) | 1 | 3 |
| warehouse_osmos | Simulated warehouse North | a3ccff… run 3 | 10 (1) | 0 | 0 |
| warehouse_osmos | Simulated warehouse North | a76048… run 1 | 10 (8) | 1 | 1 |
| warehouse_osmos_1 | Simulated warehouse South | 469b20… run 31 | 10 (7) | 1 | 1 |
| warehouse_osmos_1 | Simulated warehouse South | 77ac50… run 1 | 10 (9) | 1 | 2 |
| warehouse_osmos_1 | Simulated warehouse South | e2edf6… run 4 | 10 (10) | 1 | 1 |
| warehouse_osmos_2 | Simulated warehouse East | 4b43e5… run 4 | 10 (9) | 1 | 1 |
| warehouse_osmos_2 | Simulated warehouse East | 91ca0b… run 2 | 10 (9) | 1 | 4 |
| warehouse_osmos_2 | Simulated warehouse East | b3eced… run 2 | 10 (8) | 1 | 2 |

- **Totals:** 8 AI reports, all kind near_miss: 2 "candidate near miss", 3 "candidate, undetermined", 3 mixed. They have 15 member episodes and 15 evidence_clip rows. No CT member, so no incident_draft.
- **Logs:** report log 8 entries, intact; status log empty, intact.
- **T23.11 (b):** the demo store has no T22 batch, so the draw was not refused. Any later T22 batch in this store excludes these runs' recordings. The main V-02 store (`out/review/main`) is a separate store and is not linked to this demo.
- **Monitored camera-hours:** printed as "not determined" in 7 of 8 establishment-weeks (CR-030 item 6). Most areas include T-22 probe cameras that the pilot did not process.

## Screenshots (fixtures only)

`research/workflow/screenshots/`, made by `research/workflow/make_screenshots.py` from FX-14c, four FX-14f episodes and one human-started report, with n_flag_min lowered to 3. No SDG footage is shown; the fixture video is the generated test clip.

1. `01_area_manager_inbox.png`
2. `02_report_pending_ai.png`: clip, pre-filled fields, decision forms.
3. `03_report_recorded.png`: "recorded near miss (manager-approved)", status links.
4. `04_safety_manager_queue.png`
5. `05_incident_recordability.png`: incident with recordability yes, 301-style export links.
6. `06_indicators_flags.png`
7. `07_regulator_view.png`
8. `08_file_a_report.png`
9. `09_owner_setup.png`
10. `10_broken_chain.png`: one byte changed in the report log; the page shows BROKEN (FX-14g).

## Fixtures and tests

- FX-14 to FX-14i: `fixtures/records/FX-14*.json`. Expected values are from T23; hand calculations are in each file.
- FX-14f: the Wilson lower bound of 10/12 is derived in the test with 60-digit decimal arithmetic, z = 1.959964 (the T-13 Z95): 0.551969…, which is 0.552 at three places. It equals `estimators.wilson` to 1e-12. The bound for 6/12 is 0.2538…, so F1 is not raised.
- Acceptance tests run every fixture through sign-in, pages and form posts, and also check:
  - role refusals;
  - the two-level rule;
  - set_recordability refused on a near_miss;
  - oversight read-only;
  - a crawl of every workflow page for five roles through the linter, and for links to anything but 127.0.0.1;
  - log verification after a session.
- **Strict xfails (CR-030 item 1):** FX-14a "status disputed, then **rejected**" and FX-14b "status **confirmed**". These need the candidate_review adjudication that the schema cannot hold yet.

## Limits

- **Blocked (CR-030 item 1).** Safety-manager decisions on AI reports change the state and the report log but write no adjudication and no status entry. The report page says so.
- **Not determined (CR-030 items 2 to 9).** Where an indicator has two readings that differ, the page prints "not determined" with every reading's value. Some actions are refused rather than choosing a reading: exact-touch grouping, multiple timelines, and sm_uphold without a rejection.
- **Demo timing.** I6 ages use the computer clock, so no demo report is stale until 7 real days pass (CR-030 item 4).
- **Demo data.** Synthetic: every establishment, area, calendar date and incident entry is fictional ("fictional demo entry"). Video is the SDG dataset's own.
- **Prototype security.** Sign-in separates people on one computer; it is not a security boundary. Nothing is sent anywhere.
- **Manager decisions** are records of what managers decided, never references or accuracy evidence (T23.0 c). Recordability is set only by a safety manager.
