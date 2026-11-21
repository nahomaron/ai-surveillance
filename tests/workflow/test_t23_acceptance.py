"""T23 acceptance tests (D-48 step 3; Appendix T T23, contract E-1.2.22).

Every T23 fixture runs through the application: sign-in, the workflow pages and their form posts, the store, the report
log and the status log. Expected values are read from the committed fixture files, whose values are retyped from the T23
text in tests/fixtures_t03/test_t23_fixtures.py.

CR-030 item 1 was ruled by D-49 (T23.16, contract E-1.2.23): candidate_review adjudications have a null reference_class
with reason not_applicable. The strict-xfail marks of the FX-14a and FX-14b safety-manager checks are removed by that
ruling (D-49.1 section 6.1).
"""
from __future__ import annotations

import json
import re
from datetime import timedelta
from decimal import Decimal, getcontext

import pytest

from conftest import ROOT, links
from rq1.evaluation.estimators import Z95, wilson
from rq1.schema import validate
from rq1.workflow import rules as R


def cr_rows(app, kind="assessments"):
    rows = app.store.assessments() if kind == "assessments" else app.store.adjudications()
    return [e["row"] for e in rows if e["row"]["namespace"] == "candidate_review"]


def statuses(app):
    return [e["status"] for e in app.store.status_log._entries() if e["namespace"] == "candidate_review"]


def only_report(app):
    [r] = app.store.reports()
    return r


# --- FX-14 to FX-14c ---------------------------------------------------------------------------------------------------

def test_fx14_approve_nm_recorded_confirmed(make_wf):
    app = make_wf("FX-14")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    status, page = app.client("AM-1").text("/wf/inbox")
    assert status == 200 and rid in page and "candidate near miss" in page
    app.run_steps(rid)
    r = only_report(app)
    assert r.state == exp["state"] and r.wording() == exp["wording"]
    rows = cr_rows(app)
    assert [(a["label"], a["confidence"], a["namespace"], a["blind"], a["shown_system_output"]) for a in rows] == \
        [(x["label"], x["confidence"], x["namespace"], x["blind"], x["shown_system_output"]) for x in exp["assessments"]]
    assert all(validate.validate_row("reviewer_assessment", a) == [] for a in rows)
    assert rows[0]["review_time_s"] is not None and rows[0]["review_time_s"] > 0  # first display -> submission
    assert statuses(app) == exp["statuses"]
    entry = app.store.status_log._entries()[0]
    assert entry["basis_ids"] == [rows[0]["rva_id"]] and entry["layer"] == "C" and entry["config_id"] == app.fixture["inputs"]["episodes"][0]["config_id"]
    i2 = app.indicators()["ind"]["I2"]
    assert (i2.value.k, i2.value.n) == tuple(exp["I2"])
    status, page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")
    assert status == 200 and "1/1 = 1.000" in page
    assert app.store.verify() == {"report_log": [], "status_log": []}


def test_fx14a_reject_then_uphold_states_and_indicators(make_wf):
    app = make_wf("FX-14a")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    app.run_steps(rid)
    r = only_report(app)
    assert r.state == exp["state"]
    assert [a["label"] for a in cr_rows(app)] == [x["label"] for x in exp["assessments"]]
    assert statuses(app)[:1] == exp["statuses"][:1]  # disputed after am_reject (T23.5 d)
    ind = app.indicators()["ind"]
    assert (ind["I3"].value.k, ind["I3"].value.n) == tuple(exp["I3"])
    assert (ind["I4"].value.k, ind["I4"].value.n) == tuple(exp["I4"])
    status, page = app.client("SM-1").text(f"/wf/report/{rid}")
    assert "safety-manager decision" in page and "tier2" not in page.lower().replace("tier 2", "")  # T23.16 (c)


def test_fx14a_uphold_writes_adjudication_and_rejected_status(make_wf):
    app = make_wf("FX-14a")
    [rid] = app.intake()
    app.run_steps(rid)
    assert statuses(app) == app.fixture["expected"]["statuses"]
    assert [a["final_label"] for a in cr_rows(app, "adjudications")] == ["not_hazardous"]


def test_fx14b_overturn_recorded_and_i4(make_wf):
    app = make_wf("FX-14b")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    app.run_steps(rid)
    r = only_report(app)
    assert r.state == exp["state"] and r.wording() == exp["wording"]
    i4 = app.indicators()["ind"]["I4"]
    assert (i4.value.k, i4.value.n) == tuple(exp["I4"])
    _, page = app.client("SM-1").text(f"/wf/report/{rid}")
    assert exp["wording"] in page


def test_fx14b_overturn_status_confirmed(make_wf):
    app = make_wf("FX-14b")
    [rid] = app.intake()
    app.run_steps(rid)
    assert statuses(app) == app.fixture["expected"]["statuses"]


def test_fx14c_incident_recordability_rate_and_301_export(make_wf):
    app = make_wf("FX-14c")
    exp = app.fixture["expected"]
    [rid] = app.intake()
    assert app.store.headers()[rid]["kind_initial"] == exp["kind_initial"]
    _, page = app.client("SM-1").text(f"/wf/report/{rid}")
    assert "candidate contact" in page
    app.run_steps(rid)
    r = only_report(app)
    assert (r.fields["kind"], r.state) == (exp["kind"], exp["state"])
    assert statuses(app) == exp["statuses"]
    ind = app.indicators()["ind"]
    assert ind["I9"].value["cases"] == exp["I9_cases"]
    assert {k: v for k, v in ind["I9"].value["by_criterion"].items() if v} == exp["I9_by_criterion"]
    assert ind["hours_worked"] == exp["hours_worked"] and ind["incidence_rate"].value == exp["incidence_rate"]
    c = app.client("SM-1")
    status, page = c.text(f"/wf/report/{rid}")
    assert R.RECORDABLE_BADGE in page
    status, _, raw = c.get(f"/wf/report/{rid}/301.json")
    data = json.loads(raw)
    assert status == 200 and data["banner"] == exp["export_banner"]
    assert sorted(data["fields"]) == exp["incident_fields"] and all(data["fields"][k] == v for k, v in app.fixture["inputs"]["incident"].items() if v)
    status, _, raw = c.get(f"/wf/report/{rid}/301.csv")
    text = raw.decode()
    assert status == 200 and text.splitlines()[0] == exp["export_banner"]
    import csv as _csv
    items = {row[0] for row in _csv.reader(text.splitlines()) if row}
    assert all(label in items for _, label, _ in R.INCIDENT_FIELDS)
    reg = json.loads(app.client("OV-1").get(f"/wf/regulator.json?est={app.est_id}&period={app.period}")[2])
    assert reg["banner"] == R.REGULATOR_BANNER and reg["indicators"]["incidence_rate"]["value"] == "1.0000"


# --- FX-14d to FX-14g ---------------------------------------------------------------------------------------------------

def test_fx14d_human_only_signal_and_f4(make_wf):
    app = make_wf("FX-14d")
    exp = app.fixture["expected"]
    rid = app.run_steps()
    r = only_report(app)
    assert r.origin == "human" and r.state == exp["state"]
    assert statuses(app) == exp["statuses"] and cr_rows(app) == []  # T23.5 (e)
    got = app.indicators()
    assert got["ind"]["I8"].value == exp["I8"] and got["flags"]["F4"].value is exp["F4_k_miss_2"]
    assert app.indicators(k_miss=1)["flags"]["F4"].value is exp["F4_k_miss_1"]
    # an AI alert report in the area within 60 s removes the human-only signal
    app.intake([_ai_near(app, 1830.0)])
    assert app.indicators()["ind"]["I8"].value == 0
    assert rid


def _ai_near(app, onset):
    e = json.loads((ROOT / "fixtures/records/FX-14.json").read_text())["inputs"]["episodes"][0]
    return {**e, "ep_id": "ep_" + "fx14dnear".ljust(26, "0"), "t_start_tl_s": onset, "t_end_tl_s": onset + 1.0}


def test_fx14e_transitive_grouping_one_report_three_members(make_wf):
    app = make_wf("FX-14e")
    exp = app.fixture["expected"]
    rids = app.intake()
    assert len(rids) == exp["reports"]
    assert len(app.store.headers()[rids[0]]["member_episode_ids"]) == exp["members"]
    assert len(only_report(app).fields["evidence_clip_ids"]) == 3 and len(app.store.clips()) == 3
    app.run_steps(rids[0])
    assert len(cr_rows(app)) == exp["assessments_n"] and statuses(app) == exp["statuses"]
    assert {a["target_id"] for a in cr_rows(app)} == {e["ep_id"] for e in app.fixture["inputs"]["episodes"]}


def _wilson_lower_decimal(k: int, n: int) -> Decimal:
    """Wilson lower bound with the T-13 z (Z95 = 1.959964), in decimal arithmetic (60 digits)."""
    getcontext().prec = 60
    z, k, n = Decimal(str(Z95)), Decimal(k), Decimal(n)
    p = k / n
    centre = p + z * z / (2 * n)
    half = z * (p * (1 - p) / n + z * z / (4 * n * n)).sqrt()
    return (centre - half) / (1 + z * z / n)


def test_fx14f_rejection_flag(make_wf):
    app = make_wf("FX-14f")
    exp = app.fixture["expected"]
    rids = app.intake()
    assert len(rids) == exp["reports"]
    order = sorted(rids, key=lambda r: app.store.report(r).fields["occurred_at"])
    for k, rid in enumerate(order):
        if k < 10:
            app.act("AM-1", rid, "am_reject", reason="not_hazardous", rationale="The truck is parked.")
        else:
            app.act("AM-1", rid, "am_approve", label="nm", rationale="The truck brakes hard.")
    got = app.indicators()
    i3 = got["ind"]["I3"].value
    assert (i3.k, i3.n) == tuple(exp["rejected_10"]["I3"])
    lower = _wilson_lower_decimal(10, 12)
    # hand calculation: p = 5/6, z^2 = 3.841458..., centre = 0.99339..., half = 0.26472..., denominator 1.32012...
    assert lower.quantize(Decimal("0.001")) == Decimal(str(exp["rejected_10"]["wilson_lower_approx"]))
    assert abs(Decimal(str(i3.interval[0])) - lower) < Decimal("1e-12")
    assert got["flags"]["F1"].value is exp["rejected_10"]["F1"]
    status, page = app.client("SM-1").text(f"/wf/indicators?est={app.est_id}&period={app.period}")
    assert R.FLAG_TEXT in page and "10/12 = 0.833" in page


def test_fx14f_six_of_twelve_does_not_raise(make_wf):
    app = make_wf("FX-14f")
    exp = app.fixture["expected"]
    order = sorted(app.intake(), key=lambda r: app.store.report(r).fields["occurred_at"])
    for k, rid in enumerate(order):
        if k < 6:
            app.act("AM-1", rid, "am_reject", reason="other", rationale="Cannot decide.")
        else:
            app.act("AM-1", rid, "am_approve", label="nm", rationale="The truck brakes hard.")
    got = app.indicators()
    i3 = got["ind"]["I3"].value
    assert (i3.k, i3.n) == tuple(exp["rejected_6"]["I3"])
    assert _wilson_lower_decimal(6, 12) < Decimal("0.5") and got["flags"]["F1"].value is exp["rejected_6"]["F1"]
    assert abs(Decimal(str(wilson(6, 12)[0])) - _wilson_lower_decimal(6, 12)) < Decimal("1e-12")


def test_fx14g_one_changed_byte_breaks_the_chain_and_the_page_shows_it(make_wf):
    app = make_wf("FX-14g")
    [rid] = app.intake()
    app.run_steps(rid)
    assert app.store.report_log.verify() == []
    path = app.store.root / "wf_report_log.jsonl"
    data = bytearray(path.read_bytes())
    i = data.rindex(b'"state_after":"recorded"') + len('"state_after":"rec')
    data[i] = ord("X")
    path.write_bytes(bytes(data))
    assert app.store.report_log.verify() != []
    _, page = app.client("SM-1").text(f"/wf/report/{rid}")
    assert "Report log hash chain: <strong>BROKEN" in page


# --- FX-14h: wording ------------------------------------------------------------------------------------------------

def test_fx14h_linter_rules():
    exp = json.loads((ROOT / "fixtures/records/FX-14h.json").read_text())["expected"]
    assert R.lint_workflow("<p>A near miss in aisle 3</p>")  # unqualified: refused
    assert not R.lint_workflow(f"<p>{exp['ai_label']}</p>")
    for phrase in exp["accepted"]:
        assert not R.lint_workflow(f"<p>{phrase}</p>")
    assert R.lint_workflow("<p>Recordable</p>") and not R.lint_workflow(f"<p>{R.RECORDABLE_BADGE}</p>")
    assert not R.lint_workflow(f"<p>{R.EXPORT_301_BANNER}</p><p>{R.FLAG_TEXT}</p><p>{R.REGULATOR_BANNER}</p>")
    assert R.lint_workflow("<p>collision</p>") and R.lint_workflow("<p>OSHA said so</p>")


def test_fx14h_human_text_is_stored_verbatim_and_shown_in_a_user_block(make_wf):
    """AR-63 item 8 is reversed by T23.22 (D-49): a report is never refused for its wording; the text is stored verbatim,
    HTML-escaped and shown in an "entered by <pseudonym>" block that the linter skips."""
    app = make_wf("FX-14h")
    c = app.client("W-1")
    status, headers, body = c.post("/wf/file", {"kind": "near_miss", "area_id": app.area_id, "occurred_at": "2026-11-16T09:00",
                                                "description": "It was a near miss."})
    assert status == 303
    [r] = app.store.reports()
    assert r.fields["description"] == "It was a near miss."
    status, page = c.text(f"/wf/report/{r.report_id}")
    assert status == 200 and "entered by W-1" in page


def crawl(app, pseudonym: str, start: str = "/wf") -> dict[str, str]:
    c = app.client(pseudonym)
    seen, todo = {}, [start]
    while todo:
        path = todo.pop()
        if path in seen or not path.startswith("/wf") or path.startswith("/wf/clip/"):
            continue
        status, _, raw = c.get(path)
        seen[path] = raw.decode("utf-8", "replace")
        assert status in (200, 403), (path, status, seen[path][:400])
        if path.endswith((".json", ".csv")):
            continue
        todo += [link for link in links(seen[path]) if link not in seen]
    return seen


def test_fx14h_every_workflow_page_and_export_passes_the_linter(make_wf):
    app = make_wf("FX-14c")
    [rid] = app.intake()
    app.run_steps(rid)
    app.intake([_ai_near(app, 600.0)])
    app.client("W-1").post("/wf/file", {"kind": "near_miss", "area_id": app.area_id, "occurred_at": "2026-11-16T08:20",
                                        "description": "A truck reversed out of aisle 3; I stepped back."})
    pages = {}
    for who in ("AM-1", "SM-1", "W-1", "OV-1", "Owner"):
        pages.update({f"{who} {k}": v for k, v in crawl(app, who).items()})
    assert len(pages) > 20
    for name, text in pages.items():
        exempt = (R.source_banner(app.store.source_quality()),)  # T23.26: a fixed banner the pages must print
        issues = R.lint_workflow(text, html_page=not name.split("?")[0].endswith((".json", ".csv")), exempt=exempt)
        assert issues == [] or name.endswith(".json"), (name, issues)
        assert not re.search(r"(https?:)?//(?!127\.0\.0\.1)[a-z0-9.-]+\.[a-z]{2,}", text.replace("http://www.w3.org", "")), name
    any_ai = [v for k, v in pages.items() if "/wf/inbox" in k]
    assert any("candidate near miss" in v for v in any_ai)


# --- FX-14i is in test_t23_demo.py ------------------------------------------------------------------------------------

# --- roles and permissions (T23.1, T23.4, T23.7, T23.10) -------------------------------------------------------------

def test_area_manager_cannot_act_outside_their_areas(make_wf):
    app = make_wf("FX-14")
    other = app.store.add_area(app.est_id, "Other area", ["cam_" + "fx14other".ljust(26, "0")])
    app.store.add_user("AM-2", ["area_manager"], None, [other["area_id"]], "pw-AM-2")
    app.ids["AM-2"] = next(u for u, v in app.store.users().items() if v["pseudonym"] == "AM-2")
    [rid] = app.intake()
    c = app.client("AM-2")
    assert c.text(f"/wf/report/{rid}")[0] == 403
    status, _, body = c.post(f"/wf/report/{rid}/act", {"action": "am_approve", "label": "nm", "rationale": "Seen."})
    assert status == 400 and b"only an area manager of the report" in body
    assert only_report(app).state == "pending_am"


def test_only_the_safety_manager_sets_recordability_and_not_on_a_near_miss(make_wf):
    app = make_wf("FX-14c")
    [rid] = app.intake()
    app.act("AM-1", rid, "am_approve", label="ct", rationale="The forks reach the leg.")
    for who in ("AM-1", "W-1", "OV-1"):
        status, _, body = app.client(who).post(f"/wf/report/{rid}/act", {"action": "set_recordability", "recordable": "yes",
                                                                       "criteria": "death", "note": "x"})
        assert status in (400, 403), who
    assert only_report(app).recordability is None
    app2 = make_wf("FX-14")
    [nm] = app2.intake()
    app2.act("AM-1", nm, "am_approve", label="nm", rationale="Brakes hard.")
    status, _, body = app2.act("SM-1", nm, "set_recordability", recordable="yes", criteria="death", note="x")
    assert status == 400 and b"recorded incident only" in body


def test_area_manager_who_decided_cannot_act_as_its_safety_manager(make_wf):
    app = make_wf("FX-14a")
    app.store.add_user("AMSM", ["area_manager", "safety_manager"], app.est_id, [app.area_id], "pw-AMSM")
    app.ids["AMSM"] = next(u for u, v in app.store.users().items() if v["pseudonym"] == "AMSM")
    [rid] = app.intake()
    assert app.act("AMSM", rid, "am_reject", reason="not_hazardous", rationale="Parked truck.")[0] == 303
    status, _, body = app.act("AMSM", rid, "sm_overturn", label="nm", note="Changed my mind.")
    assert status == 400 and b"T23.1 b" in body
    assert app.act("SM-1", rid, "sm_overturn", label="nm", note="The truck was moving.")[0] == 303


def test_oversight_is_read_only(make_wf):
    app = make_wf("FX-14")
    [rid] = app.intake()
    c = app.client("OV-1")
    assert c.text(f"/wf/regulator?est={app.est_id}")[0] == 200
    for path, data in ((f"/wf/report/{rid}/act", {"action": "am_approve", "label": "nm", "rationale": "x"}),
                       ("/wf/setup/hours", {"est_id": app.est_id, "period": app.period, "hours_worked": "1"})):
        assert c.post(path, data)[0] in (400, 403)
    assert c.text("/wf/inbox")[0] == 403 and c.text("/wf/queue")[0] == 403 and c.text("/wf/setup")[0] == 403
    assert only_report(app).state == "pending_am" and app.store.hours(app.est_id, app.period) is None


def test_regulator_view_is_not_open_to_managers_and_has_the_banner(make_wf):
    app = make_wf("FX-14")
    assert app.client("AM-1").text(f"/wf/regulator?est={app.est_id}")[0] == 403
    _, page = app.client("Owner").text(f"/wf/regulator?est={app.est_id}")
    assert R.REGULATOR_BANNER in page and "Workflow parameters in force" in page
    _, _, csv_raw = app.client("OV-1").get(f"/wf/regulator.csv?est={app.est_id}")
    assert csv_raw.decode().splitlines()[0] == R.REGULATOR_BANNER


def test_t22_reviewer_profiles_have_no_workflow_access(make_wf):
    app = make_wf("FX-14")
    anr = app.store.add_annotator("R-A", "c_layer_reviewer", "completed T22 handbook training", True, "pw-ra")
    from conftest import Client
    c = Client(app.port)
    c.post("/login", {"profile": anr["anr_id"], "passphrase": "pw-ra"})
    assert c.text("/wf")[0] == 403


def test_manager_records_expose_the_person_for_reference_review(make_wf):
    """T23.11 (c): acting on a workflow report writes a candidate_review assessment, so the T22.2 (b) exposure rule
    applies to that person (identified by pseudonym) for the recording."""
    app = make_wf("FX-14")
    [rid] = app.intake()
    app.act("AM-1", rid, "am_approve", label="nm", rationale="Brakes hard.")
    anr = app.store.add_annotator("AM-1", "adjudicator", "EHS professional, 5 years", True, "pw")
    rec = app.fixture["inputs"]["episodes"][0]["recording_id"]
    assert app.store.exposed(anr["anr_id"], rec)


def test_server_binds_127_only():
    from rq1.workflow.server import make_server as mk
    from rq1.schema.errors import ContractError
    with pytest.raises(ContractError):
        mk(None, {}, host="0.0.0.0")


def test_logs_verify_after_a_full_session(make_wf):
    app = make_wf("FX-14e")
    [rid] = app.intake()
    app.run_steps(rid)
    app.act("SM-1", rid, "sm_note", note="Discussed at the weekly meeting.")
    app.act("SM-1", rid, "sm_reclassify", reason="Truck was behind a barrier", label="not_hazardous", note="Seen on site.")
    app.act("SM-1", rid, "sm_reopen", note="New footage angle.")
    assert only_report(app).state == "pending_sm"
    status, _, body = app.act("SM-1", rid, "sm_uphold", note="x")
    assert status == 400 and b"T23.20 (a)" in body  # no area-manager rejection to uphold
    assert app.store.verify() == {"report_log": [], "status_log": []}
    for e in app.store.report_log.entries():
        assert validate.validate_row("wf_report_log", e) == []
