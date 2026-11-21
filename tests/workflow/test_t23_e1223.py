"""Appendix T T23.16-T23.27 (contract E-1.2.23; D-49) in the workflow application: FX-14q to FX-14ad.

Every fixture runs through the app (sign-in, pages, form posts) where a person acts. Expected values are read from the
committed fixture files, whose values are retyped from the D-49.1 section 6.1 table in
tests/fixtures_t03/test_t23_fixtures.py.
"""
from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import ROOT
from rq1.schema.errors import ContractError
from rq1.workflow import rules as R

WHY = "The forklift brakes hard as the person steps out."
NOTE = "Checked the clip with the team."


def ok(resp):
    status, _, body = resp
    assert status == 303, body[:600]


def refused(resp, text: bytes = b""):
    status, _, body = resp
    assert status == 400, (status, body[:300])
    assert text in body, body[:600]


def by_time(app):
    return sorted(app.store.reports(), key=lambda r: (r.fields["occurred_at"], r.report_id))


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def post_only(app, who, rid, action, **form):
    """Open the report page first (that writes the first-display record), then snapshot, then post."""
    c = app.client(who)
    assert c.text(f"/wf/report/{rid}")[0] == 200
    before = snapshot(app.store.root)
    resp = c.post(f"/wf/report/{rid}/act", {"action": action, **form})
    return resp, before


def human(app, who="W-1", offset=1800.0, area_id=None, kind="near_miss", text="A truck reversed out of aisle 3; I stepped back."):
    when = R.utc(app.calendar + timedelta(seconds=offset))[:19]
    status, headers, body = app.client(who).post("/wf/file", {"kind": kind, "area_id": area_id or app.area_id, "occurred_at": when,
                                                             "description": text})
    assert status == 303, body[:400]
    return headers["Location"].rsplit("/", 1)[1]


def i7(app, **kw):
    return app.indicators(**kw)["ind"]["I7_ai"].value


# --- FX-14q to FX-14t: grouping, split, resolution, timebase -------------------------------------------------------

def test_fx14q_simultaneous_interactions_split_into_two_reports(make_wf):
    app = make_wf("FX-14q")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    assert len(app.store.headers()[rid]["member_episode_ids"]) == exp["members"]
    refused(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY), b"group_resolution")
    assert app.store.report(rid).state == "pending_am"
    e1, e2 = (e["ep_id"] for e in app.fixture["inputs"]["episodes"])
    ok(app.act("AM-1", rid, "split", note="Two different pairs at the same time.", **{f"part_{e1}": "1", f"part_{e2}": "2"}))
    assert app.store.report(rid).state == exp["original_state"]
    parts = [r for r in app.store.reports() if r.fields.get("split_from") == rid]
    assert len(parts) == exp["new_reports"] and {r.state for r in parts} == {exp["new_state"]}
    assert sorted(m for r in parts for m in r.header["member_episode_ids"]) == sorted([e1, e2])
    assert all(len(r.header["member_episode_ids"]) == 1 for r in parts)
    # no assessment, adjudication or status entry for the original (T23.20 e)
    assert not [e for e in app.store.assessments() if e.get("report_id") == rid]
    for r in parts:
        ok(app.act("AM-1", r.report_id, "am_approve", label="nm", rationale=WHY))
    ind = app.indicators()["ind"]
    assert ind["I7_ai"].value == exp["I7_after_both_approved"]
    assert ind["I1"].value == 2  # section 5: the closed_split original is excluded; its parts are counted
    assert app.store.verify() == {"report_log": [], "status_log": []}


def test_fx14r_one_interaction_seen_by_two_cameras(make_wf):
    app = make_wf("FX-14r")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    ok(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY, group_resolution="one_interaction"))
    r = app.store.report(rid)
    assert (r.state, r.fields["group_resolution"]) == (exp["state"], exp["group_resolution"])
    ind = app.indicators()["ind"]
    assert ind["I7_ai"].value == exp["I7"] and ind["I7_ai"].notes["group_resolution = cannot_tell"] == exp["cannot_tell"]
    refused(app.act("AM-1", rid, "split", note="x"), b"split is taken from pending_am, pending_sm")  # T23.28 (a): the action is `split`


def test_group_resolution_values_are_checked(make_wf):
    app = make_wf("FX-14r")
    [rid] = app.intake()
    refused(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY, group_resolution="several"), b"group_resolution")
    ok(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY, group_resolution="cannot_tell"))
    assert app.indicators()["ind"]["I7_ai"].notes["group_resolution = cannot_tell"] == 1


def test_fx14s_touching_widened_intervals_merge(make_wf):
    app = make_wf("FX-14s", params={"t_group_s": app_param("FX-14s")})
    assert len(app.intake()) == app.fixture["expected"]["groups"]


def app_param(fixture_id):
    return json.loads((ROOT / f"fixtures/records/{fixture_id}.json").read_text())["expected"]["t_group_s"]


def test_fx14s_grouping_rule_closed_intervals():
    eps = [{"ep_id": "a", "t_start_tl_s": 0.5, "t_end_tl_s": 2.5, "camera_id": "c1", "timeline_id": "t", "timeline_kind": "aligned_session"},
           {"ep_id": "b", "t_start_tl_s": 3.5, "t_end_tl_s": 4.5, "camera_id": "c2", "timeline_id": "t", "timeline_kind": "aligned_session"}]
    assert [len(g) for g, _ in R.group_episodes(eps, 0.5)] == [2]
    assert [len(g) for g, _ in R.group_episodes(eps, 0.49)] == [1, 1]


def test_fx14t_no_common_clock_groups_per_camera(make_wf):
    app = make_wf("FX-14t")
    exp = app.fixture["expected"]
    rids = app.intake()
    assert len(rids) == exp["reports"]
    for rid in rids:
        assert app.store.report(rid).fields["grouping_basis"] == exp["basis"]
        assert exp["basis"] in app.client("AM-1").text(f"/wf/report/{rid}")[1]


def test_common_axis_reports_say_so(make_wf):
    app = make_wf("FX-14q")
    [rid] = app.intake()
    basis = app.store.report(rid).fields["grouping_basis"]
    assert basis.startswith("grouped on a declared common axis (aligned_session")


# --- FX-14u, FX-14v: duplicates and refused actions -----------------------------------------------------------------

def test_fx14u_duplicate_lifecycle(make_wf):
    app = make_wf("FX-14u")
    exp = app.fixture["expected"]
    app.intake()
    a, b = (r.report_id for r in by_time(app))
    ok(app.act("AM-1", b, "am_duplicate", duplicate_of=a))
    refused(app.act("AM-1", a, "am_duplicate", duplicate_of=b), b"closed_duplicate")
    ok(app.act("AM-1", a, "am_approve", label="nm", rationale=WHY))
    ok(app.act("SM-1", b, "sm_reopen", note=NOTE))
    ok(app.act("SM-1", b, "sm_confirm_duplicate", note="Same event as the earlier alert."))
    rb = app.store.report(b)
    assert (rb.state, rb.fields["duplicate_of"]) == (exp["B_state_after_confirm"], a)
    assert i7(app) == exp["I7_after_confirm"]
    page = app.client("SM-1").text(f"/wf/report/{a}")[1]
    assert "duplicates: 1" in page and f'href="/wf/report/{b}"' in page
    ok(app.act("SM-1", b, "sm_reopen", note=NOTE))
    # T23.28 (b) (D-51 item 2): B has one member, so the overturn needs no group_resolution, and one is refused
    assert len(app.store.headers()[b]["member_episode_ids"]) == 1
    refused(app.act("SM-1", b, "sm_overturn", label="nm", note=NOTE, group_resolution="one_interaction"), b"two or more members")
    ok(app.act("SM-1", b, "sm_overturn", label="nm", note="A separate pass of the truck."))
    rb = app.store.report(b)
    assert rb.state == "recorded" and rb.fields["duplicate_of"] is exp["B_duplicate_of_after_overturn"]
    ind = app.indicators()["ind"]
    assert ind["I7_ai"].value == exp["I7_after_overturn"]
    assert ind["I4"].value.n == exp["I4_n"]
    # beside I4, outside n; unit = report by its latest SM decision (D-51 item 4): B's latest decision is the overturn
    assert ind["I4"].notes["sm_confirm_duplicate (reports)"] == 0
    assert ind["I4"].notes["overturn of a duplicate (reports)"] == 1


def test_duplicate_of_must_be_same_establishment_and_not_split(make_wf):
    app = make_wf("FX-14u")
    app.intake()
    a, b = (r.report_id for r in by_time(app))
    refused(app.act("AM-1", b, "am_duplicate", duplicate_of=b), b"different report")
    other = app.store.add_establishment("Other demo site", demo=True)
    area = app.store.add_area(other["est_id"], "Other area", ["cam_" + "fx14uother".ljust(26, "0")])
    rid = app.store.create_human({"profile_id": "owner", "pseudonym": "Owner"},
                                 {"kind": "near_miss", "area_id": area["area_id"], "occurred_at": "2026-11-16T09:00", "description": "x"})
    refused(app.act("AM-1", b, "am_duplicate", duplicate_of=rid), b"same establishment")


def test_fx14v_refused_actions_change_no_file(make_wf):
    app = make_wf("FX-14v")
    exp = app.fixture["expected"]
    app.intake()
    r1, r2, r3 = (r.report_id for r in by_time(app))
    assert len(app.store.headers()[r3]["member_episode_ids"]) == 2
    # (1) sm_uphold without am_reject: r1 marked duplicate, reopened -> pending_sm, latest AM decision am_duplicate
    ok(app.act("AM-1", r1, "am_duplicate", duplicate_of=r2))
    ok(app.act("SM-1", r1, "sm_reopen", note=NOTE))
    # (2) sm_reclassify with recordability yes
    ok(app.act("AM-1", r2, "am_approve", label="ct", rationale="The forks reach the leg."))
    ok(app.act("SM-1", r2, "set_recordability", recordable="yes", criteria="medical_treatment_beyond_first_aid", note="Treated."))
    cases = [(r1, "SM-1", "sm_uphold", {"note": NOTE}), (r2, "SM-1", "sm_reclassify", {"reason": "Not work related", "note": NOTE}),
             (r3, "AM-1", "split", {"note": NOTE, **{f"part_{m}": "1" for m in app.store.headers()[r3]["member_episode_ids"]}})]
    states = {r: app.store.report(r).state for r in (r1, r2, r3)}
    for rid, who, action, form in cases:
        (status, _, body), before = post_only(app, who, rid, action, **form)
        assert status == 400, (action, body[:300])
        assert snapshot(app.store.root) == before, action  # exp: store_bytes_changed is False
        assert app.store.report(rid).state == states[rid]
    assert len(cases) == len(exp["refused"]) and exp["store_bytes_changed"] is False


# --- FX-14w: as-of cutoff and revisions -----------------------------------------------------------------------------

def test_fx14w_as_of_view_is_stable_and_revisions_are_counted(make_wf):
    app = make_wf("FX-14w")
    exp = app.fixture["expected"]
    eps = app.fixture["inputs"]["episodes"]
    app.intake(eps[:6])
    reports = by_time(app)
    for k, r in enumerate(reports):
        if k == 4:
            ok(app.act("AM-1", r.report_id, "am_reject", reason="not_hazardous", rationale="The truck is parked."))
        else:
            ok(app.act("AM-1", r.report_id, "am_approve", label="nm", rationale=WHY))
    entries = app.store.report_log.entries()
    assert len(entries) == exp["as_of_entry"]
    as_of = entries[exp["as_of_entry"] - 1]["created_utc"]
    q = f"/wf/regulator.json?est={app.est_id}&period={app.period}&as_of={as_of}"
    first = json.loads(app.client("OV-1").get(q)[2])
    assert first["as_of"] == as_of and first["report_log"]["length"] == 12
    assert first["report_log"]["head_hash"] == entries[11]["record_hash"]
    assert app.indicators(as_of=as_of)["ind"]["I2"].notes["revised after first decision"] == exp["revised_before"]
    ok(app.act("SM-1", reports[0].report_id, "sm_reclassify", reason="Truck behind a barrier", note=NOTE))
    ok(app.act("SM-1", reports[1].report_id, "sm_note", note=NOTE))
    ok(app.act("SM-1", reports[2].report_id, "sm_note", note=NOTE))
    new = app.intake(eps[6:8])
    for rid in new:
        ok(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY))
    ok(app.act("SM-1", reports[3].report_id, "sm_note", note=NOTE))
    assert len(app.store.report_log.entries()) == exp["entries_total"]
    again = json.loads(app.client("OV-1").get(q)[2])
    assert again == first and exp["same_view"] is True
    late = app.indicators(as_of=app.store.report_log.entries()[-1]["created_utc"])["ind"]
    assert late["I2"].notes["revised after first decision"] == exp["revised_after"]
    assert late["I2"].value.n == 8


def test_as_of_must_follow_a_non_decreasing_log(make_wf):
    app = make_wf("FX-14")
    app.intake()
    path = app.store.root / "wf_report_log.jsonl"
    e = app.store.report_log.entries()
    app.store.clock.t -= timedelta(days=1)  # the clock goes back: the next entry is earlier than the last
    app.store.intake(app.area_id, [dict(_ep(app), ep_id="ep_" + "fx14back".ljust(26, "0"))], app.calendar)
    issues = app.store.verify()["report_log"]
    assert issues and issues[0].code == "ERR-INVARIANT" and "created_utc" in issues[0].message
    assert len(path.read_bytes().splitlines()) == len(e) + 1


def _ep(app):
    from conftest import episode
    return episode(app.fixture["inputs"]["episodes"][0], app.video)


# --- FX-14x, FX-14y: recordability lifecycle and I9 -----------------------------------------------------------------

def test_fx14x_withdraw_then_reclassify_then_overturn(make_wf):
    app = make_wf("FX-14x")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    ok(app.act("AM-1", rid, "am_approve", label="ct", rationale="The forks reach the leg."))
    ok(app.act("SM-1", rid, "set_recordability", recordable="yes", criteria="medical_treatment_beyond_first_aid", note="Treated."))
    refused(app.act("SM-1", rid, "sm_reclassify", reason="Not work related", note=NOTE), b"T23.19 (e)")
    refused(app.act("SM-1", rid, "withdraw_recordability", reason="because", note=NOTE), b"classification_changed")
    ok(app.act("SM-1", rid, "withdraw_recordability", reason="classification_changed", note="The event is being reclassified."))
    ok(app.act("SM-1", rid, "sm_reclassify", reason="Not work related", note=NOTE))
    r = app.store.report(rid)
    assert r.state == exp["state_after_withdraw_and_reclassify"] and r.determination == "withdrawn"
    assert len(r.actions("set_recordability", "withdraw_recordability")) == exp["recordability_entries"]
    ind = app.indicators()["ind"]
    assert ind["I9"].value["cases"] == exp["I9"] and ind["I9"].notes["withdrawn"] == exp["withdrawn"]
    ok(app.act("SM-1", rid, "sm_reopen", note=NOTE))
    assert app.store.report(rid).determination == "withdrawn"  # T23.19 (d)
    ok(app.act("SM-1", rid, "sm_overturn", label="ct", note="It did happen at work."))
    after = exp["after_reopen_overturn"]
    r, ind = app.store.report(rid), app.indicators()["ind"]
    assert (r.state, r.determination) == ("recorded", after["determination"])
    assert ind["I9"].value["cases"] == after["I9"] and ind["I9"].notes["withdrawn"] == after["withdrawn"]
    ok(app.act("SM-1", rid, "set_recordability", recordable="yes", criteria="medical_treatment_beyond_first_aid", note="Treated."))
    assert app.indicators()["ind"]["I9"].value["cases"] == exp["after_set_again"]["I9"]
    assert app.store.report(rid).determination == exp["after_set_again"]["determination"]


def test_fx14y_definitive_cases_and_provisional_rate(make_wf):
    app = make_wf("FX-14y")
    exp = app.fixture["expected"]
    app.intake()
    y1, y2 = (r.report_id for r in by_time(app))
    for rid in (y1, y2):
        ok(app.act("AM-1", rid, "am_approve", label="ct", rationale="The forks reach the leg."))
    ok(app.act("SM-1", y1, "set_recordability", recordable="yes", criteria="days_away", days_days_away="3", note="Three days away."))
    assert app.client("OWNER").post("/wf/setup/hours", {"est_id": app.est_id, "period": app.period,
                                                        "hours_worked": str(app.fixture["inputs"]["hours_worked"])})[0] == 303
    ind = app.indicators()["ind"]
    assert ind["I9"].value["cases"] == exp["I9"] and ind["I9"].notes["not_set"] == exp["not_set"]
    assert ind["incidence_rate"].value == exp["incidence_rate"] and ind["incidence_rate"].notes["provisional"] is exp["provisional"]
    page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]
    assert "provisional" in page


def test_no_hours_rate_not_computable(make_wf):
    app = make_wf("FX-14y")
    assert "rate not computable: hours not entered" in app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]


def test_kind_follows_label_at_decision(make_wf):
    """T23.18 (e): nm -> near_miss, ct -> incident, in the decision entry's field_changes."""
    app = make_wf("FX-14y")
    app.intake()
    y1, _ = (r.report_id for r in by_time(app))
    ok(app.act("AM-1", y1, "am_approve", label="nm", rationale=WHY))
    r = app.store.report(y1)
    assert r.fields["kind"] == "near_miss" and "kind" in r.actions("am_approve")[0]["field_changes"]


# --- FX-14z, FX-14aa: monitoring and observability ------------------------------------------------------------------

def _approve_human(app, rid, who="AM-1", **obs):
    ok(app.act(who, rid, "am_approve", label="nm", **obs))


def test_fx14z_observability_categories(make_wf):
    fx = json.loads((ROOT / "fixtures/records/FX-14z.json").read_text())
    exp, inp = fx["expected"], fx["inputs"]
    names = {"i": R.OBS_CATEGORIES[0], "ii": R.OBS_CATEGORIES[2], "iii": R.OBS_CATEGORIES[3], "iv": R.OBS_CATEGORIES[4]}
    assert {k: names[k] for k in names} == exp["cases"]
    cam1 = inp["world"]["area"]["camera_ids"][0]
    got = {}
    for case in ("i", "ii", "iii", "iv"):
        app = make_wf("FX-14z")
        if case == "i":
            a2 = inp["area2"]
            app.store.add_area(app.est_id, a2["name"], a2["camera_ids"], area_id=a2["area_id"])
            app.ids["AM-2"] = app.store.add_user("AM-2", ["area_manager"], None, [a2["area_id"]], "pw-AM-2")["user_id"]
            rid = human(app, area_id=a2["area_id"])
            _approve_human(app, rid, "AM-2", camera_observability="observable", observability_cameras=a2["camera_ids"])
        else:
            if case == "iii":
                app.intake([inp["ai_c1"]])
            if case == "iv":
                app.intake([inp["ai_c2"]])
            rid = human(app)
            obs = {} if case == "ii" else {"camera_observability": "observable", "observability_cameras": [cam1]}
            _approve_human(app, rid, **obs)
        ind = app.indicators()["ind"]
        got[case] = [k for k, v in ind["I8"].notes["categories"].items() if v][0]
        assert ind["I8"].value == (exp["I8_iv"] if case == "iv" else exp["I8_others"])
        if case == "iv":
            page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]
            assert R.MISS_CAPTION in page and rid[-12:] in page
    assert got == exp["cases"]


def test_camera_observability_is_an_area_manager_field_of_human_reports(make_wf):
    app = make_wf("FX-14")
    [ai] = app.intake()
    refused(app.act("AM-1", ai, "am_approve", label="nm", rationale=WHY, camera_observability="observable",
                    observability_cameras=app.store.areas()[app.area_id]["camera_ids"][0]), b"human-started")
    rid = human(app)
    refused(app.act("AM-1", rid, "am_approve", label="nm", camera_observability="observable"), b"camera IDs checked")
    refused(app.act("AM-1", rid, "am_approve", label="nm", camera_observability="visible", observability_cameras="x"), b"camera_observability")


def test_fx14aa_union_of_monitored_time_and_artifact_conflict(make_wf):
    app = make_wf("FX-14aa")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    ok(app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY))
    ind = app.indicators()["ind"]
    mon = ind["monitoring"].value
    assert (mon["monitored_area_h"], mon["camera_h"], mon["unprocessed_cameras"]) == \
        (exp["monitored_area_hours"], exp["camera_hours"], exp["unprocessed_cameras"])
    assert ind["I7_ai_rate"].value == exp["I7_ai_rate"] and ind["I7_ai_rate"].notes["denominator_h"] == exp["rate_denominator_h"]
    cam = app.store.areas()[app.area_id]["camera_ids"][0]
    seg = app.store.monitoring()[cam]["segments"]
    before = snapshot(app.store.root)
    with pytest.raises(ContractError) as err:
        app.store.set_monitoring(cam, seg, True, "fixture", processed=[
            {"start_utc": seg[0]["start_utc"], "end_utc": seg[-1]["end_utc"], "s5_artifact_id": "art_" + f"fx14aa{k}".ljust(26, "0")} for k in (1, 2)])
    assert err.value.code == exp["two_artifacts_one_window"] and snapshot(app.store.root) == before


def test_zero_monitored_time_is_not_computable(make_wf):
    app = make_wf("FX-14aa", monitoring=[])
    ind = app.indicators()["ind"]
    assert ind["I7_ai_rate"].value == "not computable: no monitored time"


def test_zero_count_text(make_wf):
    app = make_wf("FX-14aa")
    page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]
    assert "0 in 1.0000 monitored area-hours. Absence of an alert is not absence of an event." in page


def test_usable_degraded_is_not_monitored(make_wf):
    mon = [{"camera_id": c, "segments": [{"t_start_s": 0.0, "t_end_s": 3600.0, "coverage_state": "usable_degraded"}],
            "s5_artifact_ids": ["art_" + "fx14deg".ljust(26, "0")]} for c in json.loads((ROOT / "fixtures/records/FX-14.json").read_text())["inputs"]["world"]["area"]["camera_ids"][:1]]
    app = make_wf("FX-14aa", monitoring=mon)
    m = app.indicators()["ind"]["monitoring"].value
    assert (m["monitored_area_h"], m["usable_degraded_h"]) == (0.0, 1.0)


# --- FX-14ab: combined pre-filled values -----------------------------------------------------------------------------

def test_fx14ab_combined_values(make_wf):
    app = make_wf("FX-14ab")
    exp, inp = app.fixture["expected"], app.fixture["inputs"]
    [mixed] = app.intake(inp["mixed"])
    c = app.store.combined(app.store.report(mixed))
    assert c["combined"] is exp["mixed"]["combined"] and c["text"] == exp["mixed"]["text"] and len(c["members"]) == exp["mixed"]["listed"]
    page = app.client("AM-1").text(f"/wf/report/{mixed}")[1]
    assert exp["mixed"]["text"] in page and "1.20 m" in page and "0.80 m" in page
    [same] = app.intake(inp["same"])
    c = app.store.combined(app.store.report(same))["combined"]
    src = [e for e in inp["same"] if e["ep_id"].startswith("ep_fx14" + exp["same"]["source"])][0]
    assert c["value_m"] == exp["same"]["combined_m"] and c["ep_id"] == src["ep_id"]
    assert c["camera_id"] == inp["world"]["area"]["camera_ids"][exp["same"]["camera"]]
    assert (c["sigma_status"], c["q_state"], c["s4_artifact_id"]) == (exp["same"]["sigma_status"], exp["same"]["q_state"], src["s4_artifact_id"])
    page = app.client("AM-1").text(f"/wf/report/{same}")[1]
    assert R.COMBINED_LABEL in page and src["s4_artifact_id"] in page and src["ep_id"] in page
    r = app.store.report(same)
    assert "min_clearance_m" not in r.fields  # T23.24 (d): never stored as a measurement
    assert "Smallest estimated separation 0.80 m (full_camera, uncalibrated_model)" in r.fields["description"]


def test_t23_24_e_wording_of_evasive_action_and_duration(make_wf):
    app = make_wf("FX-14ab")
    [rid] = app.intake(app.fixture["inputs"]["same"])
    page = app.client("AM-1").text(f"/wf/report/{rid}")[1]
    assert "observed by the system in at least one member" in page and "span of member episodes" in page


# --- FX-14ac: source quality, demo-only establishments, no ranking ---------------------------------------------------

def test_fx14ac_source_banner_and_demo_only(make_wf, video):
    from test_t23_demo import FakeSource
    app = make_wf("FX-14ac")
    exp, sq = app.fixture["expected"], app.fixture["inputs"]["source_quality"]

    class Source(FakeSource):
        source_quality = sq
        timebase_evidence_ref = "qualification.md §2.7: one simulator clock per SDG run (dataset card); equal frame counts"

    page = app.client("Owner").text("/wf")[1]
    assert R.NO_SOURCE_FIGURE in page  # no demo manifest yet: the source has no recorded figure
    m = __import__("rq1.workflow.demo", fromlist=["draw_demo"]).draw_demo(app.store, Source(video), 2026111903)
    assert {k: v for k, v in m["source_quality"].items() if not k.endswith("_null_reason")} == sq
    assert m["timebase_evidence_ref"] == Source.timebase_evidence_ref
    rid = next(r.report_id for r in app.store.reports() if r.origin == "ai")
    for path in (f"/wf/report/{rid}", "/wf", f"/wf/regulator?est={app.est_id}"):
        page = app.client("Owner").text(path)[1]
        assert all(s in page for s in exp["banner_contains"]) and exp["report_ref"] in page, path
        assert R.source_banner(sq) in page
    with pytest.raises(ContractError) as err:
        app.store.add_establishment("A real site", demo=False)
    assert err.value.code == "ERR-SPEC"
    assert app.client("Owner").post("/wf/setup/est", {"name": "Real site"})[0] == 400


def test_fx14ac_establishments_are_never_sorted(make_wf):
    app = make_wf("FX-14ac")
    for k, name in enumerate(("Zeta demo site", "Alpha demo site")):
        e = app.store.add_establishment(name, demo=True)
        app.store.add_area(e["est_id"], f"Area of {name}", ["cam_" + f"fx14acz{k}".ljust(26, "0")])
    order = [e["name"] for e in app.store.establishments().values()]
    assert order == ["Fixture establishment", "Zeta demo site", "Alpha demo site"]  # registration order
    for path in (f"/wf/indicators?est={app.est_id}", f"/wf/regulator?est={app.est_id}", "/wf/setup", "/wf/file"):
        page = app.client("Owner").text(path)[1]
        pos = [page.index(n) for n in order]
        assert pos == sorted(pos), path
    src = (ROOT / "src/rq1/workflow/server.py").read_text()
    for line in src.splitlines():
        if "sorted(" in line:
            assert not re.search(r"sorted\([^)]*(establishments\(\)|ests\b|est_records|\"name\"\]\))", line), line


def test_every_page_carries_the_demo_data_statement(make_wf):
    app = make_wf("FX-14")
    app.intake()
    for path in ("/wf", "/wf/inbox"):
        assert R.DEMO_DATA_NOTE in app.client("AM-1").text(path)[1]
    data = json.loads(app.client("OV-1").get(f"/wf/regulator.json?est={app.est_id}")[2])
    assert data["statement"] == R.DEMO_DATA_NOTE


# --- FX-14ad: linter and user-entered text ----------------------------------------------------------------------------

def test_fx14ad_linter_term_list_and_user_blocks(make_wf):
    fx = json.loads((ROOT / "fixtures/records/FX-14ad.json").read_text())
    exp, inp = fx["expected"], fx["inputs"]
    assert bool(R.lint_workflow(f"<p>{inp['text']}</p>")) is exp["page_refused"]
    block = R.user_block("W-1", inp["user_text"])
    assert exp["escaped"] in block and "entered by W-1" in block
    assert (R.lint_workflow(f"<p>ok</p>{block}") == []) is exp["user_block_accepted"]
    for term in ("false positive", "false negative", "precision", "recall", "accuracy", "miss rate"):
        assert R.lint_workflow(f"<p>The {term} is high</p>"), term
    assert not R.lint_workflow(f"<p>{R.FLAG_TEXT}</p><p>{R.MISS_CAPTION}</p>")
    app = make_wf("FX-14")
    rid = human(app, text="It was a near miss; " + inp["user_text"])  # T23.22: never refused for its wording
    status, page = app.client("AM-1").text(f"/wf/report/{rid}")
    assert status == 200 and exp["escaped"] in page and "<b>precision" not in page
    assert R.PRIVACY_NOTICE in app.client("W-1").text("/wf/file")[1]


def test_user_text_is_never_a_label_or_prefilled(make_wf):
    app = make_wf("FX-14")
    rid = human(app, text="candidate contact")
    r = app.store.report(rid)
    assert r.prefilled == set() and "ai_label" not in r.fields
