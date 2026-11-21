"""Appendix T T23.28 (contract E-1.2.24; D-51, CR-031): readings of E-1.2.23 in the workflow application.

Expected values are hand-computed here from the D-51 rulings (no Appendix N value applies):
- item 1: the `split` action, also by the safety manager from pending_sm;
- item 2: group_resolution on an overturn of a reopened duplicate only for two or more members;
- item 4: the side counts beside I4 counted in reports (latest safety-manager decision per report);
- item 5: withdraw_recordability refused from not_set and from withdrawn;
- item 8: prov_class of the combined value printed from the source path of the demo manifest;
- item 9: the extra banner line of the store drawn before E-1.2.23.
"""
from __future__ import annotations

import pytest

from conftest import ROOT
from rq1.workflow import rules as R
from test_t23_e1223 import NOTE, WHY, by_time, ok, refused

PARTS_NOTE = "The two cameras show two different pairs."


def _split_form(app, rid):
    e1, e2 = app.store.headers()[rid]["member_episode_ids"]
    return {"note": PARTS_NOTE, f"part_{e1}": "1", f"part_{e2}": "2"}


# --- item 1: split ---------------------------------------------------------------------------------------------------

def test_split_transition_and_enum():
    assert R.TRANSITIONS["split"] == ("area_manager|safety_manager", ("pending_am", "pending_sm"), "closed_split")
    assert R.SPLIT_FROM == {"area_manager": "pending_am", "safety_manager": "pending_sm"}
    assert "am_split" not in R.TRANSITIONS  # no longer written; stored am_split rows are read as split by an area manager
    from rq1.schema.tables import WF_ACTIONS
    assert {"split", "am_split"} <= set(WF_ACTIONS.split(","))


def test_safety_manager_splits_a_pending_sm_report(make_wf):
    """Two members (FX-14q world): AM-1 rejects (pending_sm); SM-1 splits into {c1}, {c2}.
    Hand-computed: original closed_split; 2 new pending_am AI reports carrying split_from; the log entry is `split` with
    actor_role safety_manager; the original keeps its 2 area-manager assessments (one per member) and gains no
    assessment, adjudication or status entry; I3 n goes from 1 to 0 (the original is excluded, its parts are undecided)."""
    app = make_wf("FX-14q")
    [rid] = app.intake()
    ok(app.act("AM-1", rid, "am_reject", reason="not_hazardous", rationale=WHY))
    before = app.indicators()["ind"]
    assert (before["I3"].value.k, before["I3"].value.n) == (1, 1)
    n_assess, n_adj, n_status = len(app.store.assessments()), len(app.store.adjudications()), len(app.store.status_log._entries())
    assert n_assess == 2 and n_adj == 0
    refused(app.act("AM-1", rid, "split", **_split_form(app, rid)), b"pending_am")  # the area manager splits from pending_am only
    ok(app.act("SM-1", rid, "split", **_split_form(app, rid)))
    orig = app.store.report(rid)
    assert orig.state == "closed_split"
    last = orig.entries[-1]
    assert (last["action"], last["actor_role"], last["state_before"], last["state_after"]) == ("split", "safety_manager", "pending_sm", "closed_split")
    parts = [r for r in app.store.reports() if r.fields.get("split_from") == rid]
    assert len(parts) == 2 and {r.state for r in parts} == {"pending_am"} and {r.origin for r in parts} == {"ai"}
    assert all(r.entries[0]["action"] == "create_ai" for r in parts)
    assert sorted(m for r in parts for m in r.members) == sorted(orig.members)
    assert len(app.store.assessments()) == n_assess and len(app.store.adjudications()) == n_adj
    assert len(app.store.status_log._entries()) == n_status
    after = app.indicators()["ind"]
    assert (after["I3"].value.k, after["I3"].value.n) == (0, 0) and (after["I2"].value.k, after["I2"].value.n) == (0, 0)
    assert after["I3"].notes["split"] == 1 and after["I3"].notes["undecided"] == 2
    assert after["I1"].value == 2 and after["I4"].value.n == 0
    # each part is a new report with its own decisions
    for r in parts:
        ok(app.act("AM-1", r.report_id, "am_approve", label="nm", rationale=WHY))
    assert app.indicators()["ind"]["I2"].value.k == 2 and app.indicators()["ind"]["I7_ai"].value == 2
    assert app.store.verify() == {"report_log": [], "status_log": []}


def test_area_manager_split_is_logged_as_split(make_wf):
    app = make_wf("FX-14q")
    [rid] = app.intake()
    ok(app.act("AM-1", rid, "split", **_split_form(app, rid)))
    last = app.store.report(rid).entries[-1]
    assert (last["action"], last["actor_role"]) == ("split", "area_manager")
    refused(app.act("SM-1", rid, "split", **_split_form(app, rid)), b"closed_split")


def test_safety_manager_split_needs_two_members_and_pending_sm(make_wf):
    app = make_wf("FX-14u")  # one member per report
    app.intake()
    a, _ = (r.report_id for r in by_time(app))
    ok(app.act("AM-1", a, "am_reject", reason="not_hazardous", rationale=WHY))
    refused(app.act("SM-1", a, "split", note=NOTE), b"at least two members")


def test_split_by_a_person_who_decided_as_area_manager_is_refused(make_wf):
    app = make_wf("FX-14q")
    [rid] = app.intake()
    both = app.store.add_user("AMSM-1", ["area_manager", "safety_manager"], app.est_id, [app.area_id], "pw-AMSM-1")
    app.ids["AMSM-1"] = both["user_id"]
    ok(app.act("AMSM-1", rid, "am_reject", reason="not_hazardous", rationale=WHY))
    refused(app.act("AMSM-1", rid, "split", **_split_form(app, rid)), b"T23.1 b")


def test_stored_am_split_rows_are_read_as_split_by_an_area_manager():
    e = {"action": "am_split", "actor_user_id": "u", "state_before": "pending_am", "state_after": "closed_split"}
    assert R.entry_role(e) == "area_manager" and R.is_split(e)
    assert R.entry_role({**e, "action": "split", "actor_role": "safety_manager"}) == "safety_manager"


def test_actor_role_column_reader():
    from rq1.workflow.store import read_log_row
    old = {"action": "sm_note"}
    assert read_log_row(old) == {"action": "sm_note", "actor_role": None, "actor_role_null_reason": "not_applicable"}
    assert old == {"action": "sm_note"}  # a copy: no stored row is rewritten


def test_split_send_back_sentence_replaced():
    text = (ROOT / "docs/contract/RQ1_Contract_Appendix_T_E-1.2.3.md").read_text(encoding="utf-8")
    t2328 = " ".join(text[text.index("## T23.28"):].split())
    assert "a safety manager who finds several interactions in a pending_sm report uses `split`" in t2328


# --- item 2: group_resolution on a reopened duplicate --------------------------------------------------------------

def test_single_member_overturn_of_reopened_duplicate_needs_no_group_resolution(make_wf):
    app = make_wf("FX-14u")
    app.intake()
    a, b = (r.report_id for r in by_time(app))
    assert len(app.store.headers()[b]["member_episode_ids"]) == 1
    ok(app.act("AM-1", b, "am_duplicate", duplicate_of=a))
    ok(app.act("SM-1", b, "sm_reopen", note=NOTE))
    ok(app.act("SM-1", b, "sm_overturn", label="nm", note="A separate pass of the truck."))
    rb = app.store.report(b)
    assert rb.state == "recorded" and rb.fields["duplicate_of"] is None and "group_resolution" not in rb.fields


def test_multi_member_overturn_of_reopened_duplicate_still_needs_group_resolution(make_wf):
    app = make_wf("FX-14q")
    [rid] = app.intake()
    other = app.store.create_human({"profile_id": "owner", "pseudonym": "Owner"},
                                   {"kind": "near_miss", "area_id": app.area_id, "occurred_at": "2026-11-16T08:30", "description": "x"})
    ok(app.act("AM-1", rid, "am_duplicate", duplicate_of=other))
    ok(app.act("SM-1", rid, "sm_reopen", note=NOTE))
    refused(app.act("SM-1", rid, "sm_overturn", label="nm", note=NOTE), b"group_resolution")
    ok(app.act("SM-1", rid, "sm_overturn", label="nm", note=NOTE, group_resolution="one_interaction"))


# --- item 4: side counts beside I4 in reports ----------------------------------------------------------------------

def test_i4_side_counts_are_reports(make_wf):
    """FX-14u steps: B duplicate of A, reopen, confirm, reopen, overturn. B's latest SM decision is the overturn of a
    duplicate: 1 report; no report's latest decision is a confirmation: 0. The action count is dropped."""
    app = make_wf("FX-14u")
    app.intake()
    a, b = (r.report_id for r in by_time(app))
    ok(app.act("AM-1", b, "am_duplicate", duplicate_of=a))
    ok(app.act("AM-1", a, "am_approve", label="nm", rationale=WHY))
    ok(app.act("SM-1", b, "sm_reopen", note=NOTE))
    ok(app.act("SM-1", b, "sm_confirm_duplicate", note="Same event as the earlier alert."))
    assert app.indicators()["ind"]["I4"].notes["sm_confirm_duplicate (reports)"] == 1
    ok(app.act("SM-1", b, "sm_reopen", note=NOTE))
    ok(app.act("SM-1", b, "sm_overturn", label="nm", note="A separate pass of the truck."))
    notes = app.indicators()["ind"]["I4"].notes
    assert notes["sm_confirm_duplicate (reports)"] == 0 and notes["overturn of a duplicate (reports)"] == 1
    assert "sm_confirm_duplicate" not in notes and "overturn of a duplicate" not in notes
    assert "actions" not in repr(notes)
    page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")[1]
    assert "sm_confirm_duplicate (reports): 0" in page and "overturn of a duplicate (reports): 1" in page


# --- item 5: withdraw without a determination ----------------------------------------------------------------------

def test_withdraw_from_not_set_or_withdrawn_is_refused(make_wf):
    app = make_wf("FX-14u")
    app.intake()
    a, _ = (r.report_id for r in by_time(app))
    ok(app.act("AM-1", a, "am_approve", label="ct", rationale="The forks reach the leg."))
    assert app.store.report(a).determination == "not_set"
    refused(app.act("SM-1", a, "withdraw_recordability", reason="entered_in_error", note=NOTE), b"no recordability determination")
    ok(app.act("SM-1", a, "set_recordability", recordable="undetermined", note="Waiting for the clinic."))
    ok(app.act("SM-1", a, "withdraw_recordability", reason="entered_in_error", note=NOTE))
    refused(app.act("SM-1", a, "withdraw_recordability", reason="entered_in_error", note=NOTE), b"no recordability determination")
    assert app.store.report(a).determination == "withdrawn"


# --- item 8: prov_class from the source path -----------------------------------------------------------------------

@pytest.mark.parametrize("path,expected", [("detector_path_pilot_d45", "geometry_estimated"), ("t21_oracle", "simulator_truth"), (None, None)])
def test_prov_class_of_source_path(path, expected):
    assert R.prov_class_of(path) == expected


@pytest.mark.parametrize("path,expected", [("detector_path_pilot_d45", "geometry_estimated"), ("t21_oracle", "simulator_truth")])
def test_combined_value_prints_prov_class_of_the_demo_source(make_wf, video, path, expected):
    from test_t23_demo import FakeSource
    from rq1.workflow.demo import draw_demo
    app = make_wf("FX-14ac")

    class Source(FakeSource):
        pass
    Source.path = path
    draw_demo(app.store, Source(video), 2026111903)
    rid = next(r.report_id for r in app.store.reports() if r.origin == "ai")
    c = app.store.combined(app.store.report(rid))
    assert {m["prov_class"] for m in c["members"]} == {expected}
    page = app.client("Owner").text(f"/wf/report/{rid}")[1]
    assert expected in page
    stored = [e for e in app.store.episodes().values()]
    assert {e.get("prov_class") for e in stored} == {None}  # printed, never stored (T23.24 d)


def test_combined_value_without_a_manifest_says_not_recorded(make_wf):
    app = make_wf("FX-14ab")
    [rid] = app.intake(app.fixture["inputs"]["same"])
    assert app.store.combined(app.store.report(rid))["combined"]["prov_class"] is None
    assert R.PROV_NOT_RECORDED in app.client("AM-1").text(f"/wf/report/{rid}")[1]


# --- item 9: the old demo store's banner ---------------------------------------------------------------------------

def test_banner_of_a_pilot_store_without_recorded_figures():
    line = ("Reported figures for this source exist: CM-03 0.12, EV-M1 0.11, EV-M2 0.22 (reports/M1b_pilot_report.md); "
            "not recorded in this store's manifest.")
    old = {"source_path": "detector_path_pilot_d45", "source_configuration": "BL-6"}  # drawn before E-1.2.23: no source_quality
    text = R.source_banner(None, old)
    assert R.NO_SOURCE_FIGURE in text and text.endswith(line)
    assert line not in R.source_banner(None, {"source_path": "t21_oracle", "source_configuration": "BL-6"})
    assert line not in R.source_banner(None, None)
    assert R.lint_workflow(R.banner_block(None, old)) == []


def test_store_contract_is_e_1_2_24():
    """AR-65 item 3: stores created now record E-1.2.24, so E-1.2.23 code refuses them."""
    from rq1.review.store import CONTRACT
    assert CONTRACT == "E-1.2.24"
