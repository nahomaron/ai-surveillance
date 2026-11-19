# V-02 report: T22 blind review application (part A)

Branch `v02-review-ui`. Contract E-1.2.21: Appendix T section T22 (Owner decision D-44, option (a)) and its readings T22.14 (D-46), 19 Nov 2026.
Status: **implemented** and **verified on fixtures** (98 tests in `tests/review/`, 2 of them on the held T-21 SDG outputs). Not used for any research result. Synthetic data only; any result from it is at most experimental (T12.5).

## In short

- A local web application on `http://127.0.0.1:8765/` for the T22 C-layer blind review:
  - Owner setup of annotator rows;
  - seeded pilot and reference batches;
  - the blind reviewer screen;
  - adjudication and the tier-1 audit;
  - status entries;
  - the agreement panel;
  - the audit trail view.
- It reads the S5 artifacts of the T-21 SDG validation run (configuration BL-6, validation partition) as its sampling frame. It runs no stage.
- Records go to a validation store under `out/review/<name>/` (git-ignored). Nothing is written to any analysis artifact.
- The five readings that CR-028 raised are decided in T22.14 and implemented as written. CR-028 is closed.
- The eleven representation choices (AR-61) were accepted under D-46.

## How to run a batch end to end

All commands are run from the repository root, with the project `.venv`.

1. **Owner profile** (once per store):
   `PYTHONPATH=src .venv/bin/python -m rq1.review init --owner <pseudonym>`. It asks for the passphrase twice on the terminal. The default store is `out/review/main`; `--store` chooses another.
2. **Start the application:**
   `PYTHONPATH=src .venv/bin/python -m rq1.review serve`. Open `http://127.0.0.1:8765/`.
   The server binds to 127.0.0.1 only, so other computers cannot reach it. It reads `out/m1a/run1/sdg` and refuses any recording that is not an SDG validation recording of the frozen X0b split.
3. **Annotators** (Owner → *Annotators*): create one row per person and role:
   - two `c_layer_reviewer` rows and one `adjudicator` row;
   - each with a pseudonym (never a real name), a qualification text (T22.2 c), the independence attestation (T22.2 a), and that person's local passphrase.
4. **Pilot** (Owner → *Batches*): the Owner's seed, the two reviewers, the adjudicator, tick *Pilot*.
   - The pilot draws n_pilot = 20 targets.
   - Both reviewers and the adjudicator review it together and discuss it.
   - Pilot assessments are stored in reference, with the batch flagged pilot. No adjudication, status entry or audit is written for pilot targets (T22.14 d).
5. **Reference batch** (Owner → *Batches*): a new seed from the Owner, same form, *Pilot* unticked.
   - The tool draws n_batch = 60 targets by T22.6 (a) with water-filling (T22.14 e).
   - It excludes every target already drawn into any batch on the same configuration and partition (T22.14 c).
   - It writes the immutable manifest (JCS JSON, `rvb_<uuid7>`). The manifest states `n_requested`, `n_drawn` and `frame_exhausted`, so a batch smaller than 60 says so.
6. **Blind review:** each reviewer signs in on the shared computer, opens *Blind review* and works through the items in their own seeded order.
   - Each item plays the recording's own video between the T22.4 start and end, with no marker of the interval.
   - The reviewer chooses one of the five labels (definitions as T22.5 a), a confidence (low, medium, high = 1.0, 2.0, 3.0) and a rationale.
   - When both reviewers have the same label and neither said `unsure`, the tool writes the tier-1 adjudication and its status entry at once (T22.7 a, T22.8).
7. **Audit:** when every target has both assessments, the tool draws the audit sample: ceil(0.10 × tier-1 targets) (T22.14 a).
   - The adjudicator assesses these targets blind under *Blind review*.
   - If the adjudicator's label differs, the target reopens for adjudication. The tier-1 record stays.
8. **Adjudication:** the adjudicator opens *Adjudication*. Each waiting case shows:
   - the clip;
   - both assessments (label, confidence, rationale, no names);
   - the adjudicator's own audit assessment, where there is one.

   The adjudicator records the final label (tier 2, method adjudicator). Without an adjudicator, the two reviewers record a consensus-meeting label after both have finished the batch (T22.7 c).
9. **Agreement panel** (Owner → batch → *Agreement panel*) opens when the batch is fully adjudicated. α is printed with its number of audited targets, and as "not computed (n < 5)" below five (T22.14 b).
10. **Audit trail** (Owner → *Audit trail*) is read-only:
    - it lists every target with status entries;
    - for each target it shows the full status history in log order, each entry with its basis adjudication (final label, tier, method, number of assessments, reference class), actor and hashes;
    - it shows the hash-chain check (CT-E-24). *Status log check* shows the whole log.

Sign-in separates the sessions of people who share the computer. It is **not a security boundary**: anyone with access to the user account can read `out/review/`. Passphrases are stored salted and hashed (PBKDF2-SHA256), in the store, outside git.

## Dry run on the real sampling frame

The pilot of 20 and the batch of 60 on the 319 BL-6 episodes were built only inside the held-data test `test_end_to_end_batch_on_the_sdg_frame`. That test writes to a pytest temporary directory that is deleted afterwards. No store with real-frame batches was kept, so none was renamed. The only store under `out/review/` is `out/review/demo/`, the fixture store of the screenshots.

The test seeds (101 and 202) were chosen by the agent. **They must never be used for real review.** The Owner creates the real store, pilot and batches, with the Owner's own seeds.

## Screenshots (fixtures)

All screenshots come from `research/review_ui/make_demo.py`. They show:
- a fixture store;
- the synthetic fixture video (shapes on a grey floor, two "persons" and one "forklift", so the T22.4 outlines apply);
- the FX-13 annotator rows;
- eight fixture targets, run end to end through the application.

The review times on the panel are near zero because the demo is scripted.

| Page | File |
|---|---|
| Sign-in | `screenshots/01_sign_in.png` |
| Owner: annotator rows | `screenshots/02_owner_annotators.png` |
| Owner: batches and the batch form | `screenshots/03_owner_batches.png` |
| Reviewer: blind item (clip, outlines, controls, definitions) | `screenshots/04_reviewer_item.png` |
| Adjudicator: case with both assessments | `screenshots/05_adjudication_case.png` |
| Owner: agreement panel | `screenshots/06_owner_agreement.png` |
| Owner: status log check | `screenshots/07_owner_status_log.png` |
| Owner: audit trail of one target (tier 1 confirmed, then tier 2 rejected after the audit) | `screenshots/08_owner_audit_trail.png` |

![Blind item](screenshots/04_reviewer_item.png)

## What the application enforces

| Rule | Where | Test |
|---|---|---|
| Reference assessments are blind; `shown_system_output = true` is refused (VR-E-053) | `store.submit` | `test_fx13d_unblind_reference_assessment_is_refused` |
| Exposure rule: a candidate_review assessment on any target of the recording excludes that person from reference assessment and adjudication (T22.2 b) | `store.exposed` | `test_fx13c_…`, `test_exposed_adjudicator_cannot_adjudicate` |
| Labels, confidence {1.0, 2.0, 3.0}, rationale required (T22.5) | `protocol.check_*` | `test_confidence_and_rationale_are_checked_through_the_form` |
| One assessment per (annotator, target, namespace); corrections name the replaced one (T22.5 e) | `store.submit` | `test_a_correction_…`, `test_a_reviewer_cannot_assess_a_target_twice_…` |
| Tier rule, methods, assessment_ids (T22.7) | `store._after_assessment`, `adjudicate`, `consensus` | FX-13, FX-13a, FX-13b, FX-13e |
| reference_class independent_expert_judgment, else ERR-SPEC (T22.9) | `store._reference_class` | `test_fx13f_…` |
| Status entries: mapping, config_id, layer C, basis = the adjudication; none for ref_event (T22.8, T22.3 c) | `store._write_adjudication` | FX-13 to FX-13e, `test_ref_event_target_writes_no_status` |
| Allocation by water-filling, draw, manifest, per-reviewer order (T22.6, T22.14 e) | `protocol.allocate`, `draw`, `reviewer_order` | `test_allocation_*`, `test_t22_14_e_allocation_example`, `test_per_reviewer_order_…` |
| Audit size ceil(a_audit × tier-1 targets) (T22.14 a) | `protocol.audit_count` | `test_t22_14_a_audit_size`, FX-13e |
| α over the audited targets only, n printed, "not computed (n < 5)" (T22.14 b) | `protocol.alpha`, `server.render_agreement` | `test_t22_14_b_*` |
| Earlier batch targets excluded; a re-draw is refused (T22.14 c) | `store.create_batch` | `test_t22_14_c_*` |
| Pilot: stored in reference, no adjudication, status or audit (T22.14 d) | `store.submit`, `_maybe_draw_audit` | `test_t22_14_d_*`, `test_pilot_writes_no_adjudication_or_status` |
| A reviewer never sees a system label, flag, value, route, status, configuration, stratum or another person's record (T22.4) | `server` pages and `/api/item` | `test_reviewer_pages_and_json_carry_no_system_output`, `test_second_reviewer_never_sees_the_first_assessment` |
| Agreement panel: Owner only, after full adjudication (T22.10) | `server.get_agreement` | `test_agreement_panel_only_after_full_adjudication`, `test_owner_pages_are_owner_only` |
| Audit trail: Owner only, read-only, full history, chain check, a broken chain shown | `server.get_audit_*` | `test_audit_trail_*` |
| Review records pass the OBX export checks and round-trip through its serializer (part 5) | `export.obx` (unchanged) | `test_review_records_round_trip_through_the_obx_export` |
| 127.0.0.1 only; no network URL; banner on every page; wording rules W1–W6 | `server` | `test_server_binds_to_localhost_only`, `test_every_page_has_the_banner_and_no_network_url` |
| No S5 or S8 run entry point is imported (only the κ / α functions) | static check | `test_review_package_imports_no_s5_or_s8_entry_point` |

Every T22 fixture (FX-13, FX-13a to FX-13f) runs through the application's own path: sign-in, the reviewer and adjudicator pages, their form posts, the store and the status log. Expected values come from the committed fixture files, built on `m0-implementation` with values retyped from T22. FX-13e is unchanged by T22.14.

## Original V-02 items 3 to 7, as the agent understood them

The original V-02 text (Owner, 16 Nov 2026) was given in a cloud session and is not on this computer. The items below are reconstructed from the V-02 compatibility audit (`V-02_compatibility_audit.md`) and from D-46. They are the agent's understanding, not the text, and are given for the Architect to compare.

| Item | As understood | Outcome |
|---|---|---|
| 3 | Screens: a reviewer screen writing `reviewer_assessment`, an adjudication screen writing `adjudication` and status entries, and an audit trail view (full status history per target, read-only, with the hash-chain check) | Reviewer and adjudication screens: **replaced by T22** (T22.4–T22.9), done. Audit trail view: **done** (D-46 item 3 b) |
| 4 | Records and rules: the existing tables (E-37 / E-42 / E-43 / E-44 = annotation_record, reviewer_assessment, adjudication, validation_status_log), human UUIDv7 IDs, the namespace and blindness guards (VR-E-053), method values agreement / consensus_meeting / adjudicator, time on task | Tables, IDs, guards: **done**, reused unchanged. Methods: **replaced by T22** (T22.7 e, same three values). Time on task: **replaced by T22** (T22.13 `review_time_s`). `annotation_record`: **not applicable** (A/B layer, D-23) |
| 5 | Data and wording: fixture data only, no real footage, banner "Fixture data. Review records are not research labels.", wording rules | Data scope: **replaced by T22** (T22.11: fixtures and SDG validation episodes). Banner: **replaced by T22** (the D-44 banner text). Wording rules: **done** (W1–W6 on every page) |
| 6 | Acceptance tests written first: FX-13, blindness, refusal of a non-blind reference record, round trip of the records through the existing consumers (OBX export, validators, `StatusLog.verify`), static check that no S5 or S8 run entry point is imported | **Done**. The FX-13 family follows T22. The OBX round trip was added under D-46 |
| 7 | Deliverables: code, tests, a V-02 report, Progress log, push to `v02-review-ui`, no merge or pull request | **Done** (this report) |

## Data scope (T22.11)

- **Sampling frame:** the 319 BL-6 episodes of the T-21 SDG validation run, all under one rule configuration. Strata: CT 7, UD 44, NM 30, PC 212, H 17, O 9.
- **Excluded:** the test partition, SmartSpaces, real footage and Safe and Unsafe Behaviours.
- **No outlines on real batches:** every SDG validation recording has exactly one person and one forklift track, so no T22.4 outline is drawn on them. Outlines are exercised by the fixture video only.

## Open points

- **EV-M12 (T22.10 b):** not implemented. The panel covers T22.10 (a) and (c).
- **The candidate_review namespace (T23):** no screen. The store can hold such records so that the exposure rule can be enforced.
- **Original items 3 to 7:** the table above is a reconstruction, for the Architect to check against the original text.
