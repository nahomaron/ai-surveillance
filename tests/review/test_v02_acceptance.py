"""V-02 part A acceptance tests (D-44 step 3; Appendix T T22, contract E-1.2.20). Written before the application.

Every T22 fixture runs through the application's own code path: sign-in, the reviewer and adjudicator pages and their
form posts, the store and the status log. Expected values are read from the committed fixture files, whose values are
retyped from T22 in tests/fixtures_t03/test_t22_fixtures.py.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, SEED, clip_target, filler, load_fixture
from rq1.export.report import lint
from rq1.review import protocol as P
from rq1.review.frame import FixtureFrame
from rq1.review.server import BANNER, make_server
from rq1.review.store import Store
from rq1.schema import validate
from rq1.schema.errors import ContractError


def adjudications(app):
    return [e["row"] for e in app.store.adjudications() if e["batch_id"] == app.batch]


def statuses(app):
    return app.store.status_log._entries()


def assessments(app):
    return [e["row"] for e in app.store.assessments() if e["batch_id"] == app.batch]


def check_against_fixture(app, expected):
    got = adjudications(app)
    assert len(got) == len(expected["adjudications"])
    for row, want in zip(got, expected["adjudications"]):
        for key in ("target_type", "target_id", "namespace", "final_label", "tier", "method", "prov_class", "reference_class"):
            assert row[key] == want[key], key
        assert row["agreement_stat_ref"] == app.batch  # T22.10 (a): the batch_id of the run (fixture: a fixed example ID)
        assert validate.validate_row("adjudication", row) == []
    sts = statuses(app)
    assert len(sts) == len(expected["status_entries"])
    for entry, want in zip(sts, expected["status_entries"]):
        for key in ("target_type", "target_id", "config_id", "status", "layer", "namespace"):
            assert entry[key] == want[key], key
        assert entry["basis_ids"] == [got[want["basis_adjudication"]]["adj_id"]]
    assert app.store.status_log.verify() == []


# --- the T22 fixtures through the app ---------------------------------------------------------------------------------

def test_fx13_disagreement_goes_to_tier2(make_app):
    app = make_app("FX-13")
    fx = app.fixture
    assert app.assess("R-A", "nm", 2.0, "The forklift brakes hard as the person steps into the aisle.")[0] == 303
    assert adjudications(app) == []  # one assessment: nothing to adjudicate yet
    assert app.assess("R-B", "ud", 3.0, "The racking hides the person at the closest moment.")[0] == 303
    assert adjudications(app) == [] and app.store.needs_adjudication(app.batch) == [fx["inputs"]["target"]["target_id"]]
    assert app.decide("ADJ", "ud")[0] == 303
    check_against_fixture(app, fx["expected"])
    rows = assessments(app)
    assert adjudications(app)[0]["assessment_ids"] == [r["rva_id"] for r in rows]
    assert [(r["label"], r["confidence"], r["blind"], r["shown_system_output"]) for r in rows] == [("nm", 2.0, True, False), ("ud", 3.0, True, False)]
    assert all(r["review_time_s"] is not None and r["review_time_s"] > 0 for r in rows)  # T22.5 (d), measured by the tool


def test_fx13a_agreement_is_tier1_without_adjudicator(make_app):
    app = make_app("FX-13a")
    assert app.store.adjudicator(app.batch) is None
    app.assess("R-A", "not_hazardous", 3.0, "The forklift is parked with forks down while the person walks past.")
    app.assess("R-B", "not_hazardous", 2.0, "The forklift does not move while the person is near it.")
    check_against_fixture(app, app.fixture["expected"])
    assert statuses(app)[0]["actor_id"] == app.batch  # written by the tool, no adjudicator (AR-61 item 6)
    assert app.store.fully_adjudicated(app.batch)


def test_fx13b_unsure_is_disputed_and_outside_kappa(make_app):
    app = make_app("FX-13b")
    app.assess("R-A", "unsure", 1.0, "I can see both paths but cannot tell whether the forklift had to stop.")
    app.assess("R-B", "nm", 2.0, "The forklift stops sharply about a metre from the person.")
    app.decide("ADJ", "unsure")
    check_against_fixture(app, app.fixture["expected"])
    panel = app.store.agreement(app.batch)
    assert panel["final_unsure"] == 1  # counted under unsure
    assert panel["n_four_label_targets"] == 0 and panel["kappa_four_labels"] is None  # not in the four-label kappa


def test_fx13c_exposure_rule_refuses_the_reference_assessment(make_app):
    app = make_app("FX-13c")
    fx = app.fixture
    prior = fx["inputs"]["prior_records"][0]
    app.store.import_candidate_review(prior, recording_id=fx["inputs"]["other_targets"][0]["recording_id"])
    status, _, body = app.assess("R-A", "nm", 2.0, "The forklift swerves away from the person at the aisle end.")
    assert status == 400 and b"ERR-SPEC" in body and b"T22.2 (b)" in body
    assert assessments(app) == [] and adjudications(app) == [] and statuses(app) == []
    assert fx["expected"]["stored_assessments"] == 0


def test_fx13d_unblind_reference_assessment_is_refused(make_app):
    app = make_app("FX-13d")
    status, _, body = app.assess("R-A", "nm", 2.0, "The forklift stops close to the person.", {"shown_system_output": "true"})
    assert status == 400 and b"VR-E-053" in body
    assert assessments(app) == [] and app.fixture["expected"]["stored_assessments"] == 0


def test_fx13e_audit_disagreement_reopens_tier1(make_app):
    app = make_app("FX-13e")
    app.assess("R-A", "nm", 3.0, "The person jumps back as the forks pass.")
    app.assess("R-B", "nm", 2.0, "The forklift passes very close and the person steps back.")
    assert [a["tier"] for a in adjudications(app)] == ["tier1"]
    audit = app.store.audit(app.batch)
    assert audit["target_ids"] == app.fixture["inputs"]["audit_sample"] and audit["n_tier1"] == 1
    assert not app.store.fully_adjudicated(app.batch)
    app.assess("ADJ", "ud", 2.0, "The person leaves the frame just before the forks reach them.")  # blind third assessment
    app.decide("ADJ", "ud")
    check_against_fixture(app, app.fixture["expected"])
    tier1, tier2 = adjudications(app)
    assert tier2["assessment_ids"] == [r["rva_id"] for r in assessments(app)]  # all three considered
    panel = app.store.agreement(app.batch)
    assert (panel["n_audited"], panel["audit_agree"], panel["audit_agreement_rate"]) == (1, 0, 0.0)
    assert panel["superseded_tier1"] == 1


def test_fx13f_unattested_adjudicator_is_refused(make_app):
    app = make_app("FX-13f")
    app.assess("R-A", "nm", 2.0, "The forklift stops just short of the person.")
    app.assess("R-B", "ct", 2.0, "The forks appear to touch the person's leg.")
    status, _, body = app.decide("ADJ", "ct")
    assert status == 400 and b"ERR-SPEC" in body and b"T22.9" in body
    assert adjudications(app) == [] and statuses(app) == []


def test_ref_event_target_writes_no_status(make_app, video):
    fx = load_fixture("FX-13a")
    t = dict(fx["inputs"]["target"], target_type="ref_event", target_id="rin_" + "r" * 26)
    app = make_app(targets=[clip_target(t, video)], annotators=fx["inputs"]["annotators"])
    app.assess("R-A", "nm", 2.0, "The forklift stops close to the person.")
    app.assess("R-B", "nm", 2.0, "The forklift stops close to the person and backs off.")
    [adj] = adjudications(app)
    assert (adj["target_type"], adj["tier"]) == ("ref_event", "tier1")
    assert statuses(app) == []


# --- T22.6: allocation, order, pilot ----------------------------------------------------------------------------------------

def _pad(prefix: str, tag: str, k: int) -> str:
    """A 26-character ID body: the tag, then k zero-padded (so k = 1 and k = 10 differ)."""
    return f"{prefix}_{tag}{k:0{26 - len(tag)}d}"


def _strata_frame(video, config_id, sizes):
    out = []
    for s, n in sizes.items():
        for k in range(n):
            t = {"target_type": "system_episode", "target_id": _pad("ep", s.lower(), k), "recording_id": _pad("rec", s.lower(), k),
                 "config_id": config_id, "g2_label": None, "summary_label": s}
            out.append(clip_target(t, video))
    return out


def test_batches_follow_the_allocation_and_exclude_the_pilot(tmp_path, video):
    fx = load_fixture("FX-13")
    store = Store(tmp_path / "s", kdf_iterations=1000)
    for a in fx["inputs"]["annotators"]:
        store.add_annotator(a["pseudonym"], a["role"], a["qualification_ref"], True, "pw", anr_id=a["anr_id"])
    rev = [a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "c_layer_reviewer"]
    cfg = "rcf_" + "c" * 26
    sizes = {"CT": 7, "UD": 44, "NM": 30, "PC": 212, "H": 17, "O": 9}  # the T-21 BL-6 validation strata
    frame = FixtureFrame(_strata_frame(video, cfg, sizes), config_id=cfg)
    with pytest.raises(ContractError, match="pilot"):
        store.create_batch(frame, 7, rev, None, pilot=False)
    pilot = store.create_batch(frame, 7, rev, None, pilot=True)
    # 20 over six strata: share 3.33, none capped; floors 3 x 6 = 18, remainder 2 to two strata chosen by the seed.
    assert sum(pilot["strata_counts"].values()) == 20 and sorted(pilot["strata_counts"].values()) == [3, 3, 3, 3, 4, 4]
    batch = store.create_batch(frame, 8, rev, None, pilot=False)
    assert not set(batch["target_ids"]) & set(pilot["target_ids"])
    left = {s: sizes[s] - pilot["strata_counts"][s] for s in sizes}
    # 60 over the strata left after the pilot: CT (4 or 3) and O (6 or 5) are below 10 and capped; the rest share the remainder.
    assert batch["strata_counts"]["CT"] == left["CT"] and batch["strata_counts"]["O"] == left["O"]
    assert sum(batch["strata_counts"].values()) == 60
    assert batch["strata_counts"] == P.allocate(left, 60, 8)
    for key in ("batch_id", "namespace", "configuration", "partition", "strata_counts", "seed", "target_ids", "annotators", "c_pad_s", "created_utc"):
        assert key in batch  # T22.6 (d)
    assert batch["parameters"] == P.PARAMS and batch["c_pad_s"] == 3.0  # T22.12
    raw = (tmp_path / "s" / "batches" / batch["batch_id"] / "manifest.json").read_bytes()
    assert raw.startswith(b"{") and b"\n" not in raw  # JCS JSON
    # T22.14 (c) (D-46 replaced the provisional refusal of a second batch): later batches exclude every earlier target.
    second = store.create_batch(frame, 9, rev, None, pilot=False)
    assert not set(second["target_ids"]) & (set(batch["target_ids"]) | set(pilot["target_ids"]))


def test_per_reviewer_order_differs_and_is_reproducible_from_the_seed(make_app, video):
    fx = load_fixture("FX-13")
    cfg = fx["inputs"]["target"]["config_id"]
    app = make_app(targets=filler(cfg, video, n=12, prefix="ord"), annotators=fx["inputs"]["annotators"])
    a, b = app.store.order(app.batch, app.ids["R-A"]), app.store.order(app.batch, app.ids["R-B"])
    assert sorted(a) == sorted(b) and a != b
    m = app.store.manifest(app.batch)
    assert a == P.reviewer_order(m["target_ids"], m["seed"], app.ids["R-A"])
    # Same seed, same people, fresh store: the same order.
    again = make_app(targets=filler(cfg, video, n=12, prefix="ord"), annotators=fx["inputs"]["annotators"])
    assert again.store.order(again.batch, again.ids["R-A"]) == a


def test_pilot_writes_no_adjudication_or_status(make_app, video):
    fx = load_fixture("FX-13a")
    app = make_app(targets=filler(fx["inputs"]["target"]["config_id"], video, n=2), annotators=fx["inputs"]["annotators"], with_pilot=False)
    reviewers = [a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "c_layer_reviewer"]
    app.batch = app.store.create_batch(app.frame, SEED, reviewers, None, pilot=True)["batch_id"]
    for who in ("R-A", "R-B"):
        app.assess(who, "nm", 2.0, "The forklift stops close to the person.")
    assert adjudications(app) == [] and statuses(app) == [] and len(assessments(app)) == 2
    with pytest.raises(ContractError):
        app.store.agreement(app.batch)


# --- what a reviewer can see (T22.4) ---------------------------------------------------------------------------------------

PLANTED = {"config": "rcf_" + "q" * 26, "rec": "rec_" + "v" * 26, "target": "ep_" + "w" * 26}


def _planted_app(make_app, video):
    fx = load_fixture("FX-13")
    t = {"target_type": "system_episode", "target_id": PLANTED["target"], "recording_id": PLANTED["rec"], "config_id": PLANTED["config"],
         "g2_label": "lbl_nm", "summary_label": "NM"}
    target = clip_target(t, video)
    target.update({"review_route": True, "borderline_flags": ["speed_near_v_min"], "minclr_m": 0.4321, "ttc_s": 0.8765})
    return make_app(targets=[target], annotators=fx["inputs"]["annotators"])


FORBIDDEN = [r"\blbl_", r"\bNM\b", r"\bUD\b", r"\bCT\b", r"\bPC\b", "BL-6", "rcf_", r"\bconfirmed\b", r"\brejected\b", r"\bdisputed\b",
             "review_route", "borderline", "speed_near", "minclr", "0.4321", "0.8765", r"\bttc", r"\bTTC\b", r"\bPET\b", "stratum", "strata",
             PLANTED["config"], PLANTED["rec"], PLANTED["target"], "summary_label", "g2_label", "rule_configuration"]


def _reviewer_responses(app, pseudonym):
    c = app.client(pseudonym)
    out = []
    for path in ("/home", f"/review/{app.batch}", f"/review/{app.batch}/1", f"/api/item/{app.batch}/1"):
        status, headers, raw = c.get(path)
        out.append((path, status, raw.decode("utf-8", "replace")))
    return c, out


def test_reviewer_pages_and_json_carry_no_system_output(make_app, video):
    app = _planted_app(make_app, video)
    secret_a = "Rationale-of-reviewer-A-ZQX"
    app.assess("R-A", "nm", 2.0, f"The forklift stops. {secret_a}")
    for who in ("R-B", "R-A"):
        _, responses = _reviewer_responses(app, who)
        for path, status, text in responses:
            assert status in (200, 303), (who, path, status)
            for pattern in FORBIDDEN:
                assert not re.search(pattern, text), (who, path, pattern)
            if who == "R-B":
                assert secret_a not in text and app.ids["R-A"] not in text and "R-A" not in text, path
    _, _, raw = app.client("R-B").get(f"/api/item/{app.batch}/1")
    data = json.loads(raw)
    assert set(data) == {"item", "of", "clip", "start_s", "end_s", "fps", "width", "height", "outlines", "submitted"}
    assert data["submitted"] is None


def test_second_reviewer_never_sees_the_first_assessment(make_app, video):
    app = _planted_app(make_app, video)
    app.assess("R-A", "ct", 3.0, "Forks touch the leg: unique-text-AAA.")
    c, responses = _reviewer_responses(app, "R-B")
    assert all("unique-text-AAA" not in text and "Your assessment" not in text for _, _, text in responses)
    assert json.loads(responses[-1][2])["submitted"] is None
    app.assess("R-B", "nm", 2.0, "Close pass, unique-text-BBB.")
    _, after = _reviewer_responses(app, "R-B")
    assert all("unique-text-AAA" not in text for _, _, text in after)  # not after both are submitted either (T22.4)
    _, a_after = _reviewer_responses(app, "R-A")
    assert all("unique-text-BBB" not in text for _, _, text in a_after)


def test_clip_window_and_outlines_reach_the_player(make_app):
    app = make_app("FX-13")
    _, _, raw = app.client("R-A").get(f"/api/item/{app.batch}/1")
    data = json.loads(raw)
    assert (data["start_s"], data["end_s"]) == P.clip_window(3.0, 5.0, 0.0, 10.0, 3.0) == (0.0, 8.0)
    assert [o["colour"] for o in data["outlines"]] == ["#ffffff", "#8fd3ff"]


def test_clip_is_served_with_ranges_to_its_viewer_only(make_app, video):
    app = make_app("FX-13")
    a = app.client("R-A")
    clip = json.loads(a.get(f"/api/item/{app.batch}/1")[2])["clip"]
    status, headers, raw = a.get(clip, headers={"Range": "bytes=0-99"})
    assert status == 206 and len(raw) == 100 and headers["Content-Range"] == f"bytes 0-99/{video.stat().st_size}"
    assert raw == video.read_bytes()[:100]
    assert app.client("R-B").get(clip)[0] == 404  # another person's clip token
    assert app.client().get(clip)[0] == 404  # signed out


# --- server, pages, roles ----------------------------------------------------------------------------------------------------

def test_server_binds_to_localhost_only(tmp_path):
    store = Store(tmp_path / "s", kdf_iterations=1000)
    server = make_server(store, {})
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()
    for host in ("0.0.0.0", "", "localhost", "::"):
        with pytest.raises(ContractError):
            make_server(store, {}, host=host)


def _all_pages(app):
    owner = app.client("Owner")
    pages = [("anon", "/", app.client().text("/")[1])]
    for path in ("/home", "/setup", "/batches", f"/batch/{app.batch}", "/statuslog", f"/batch/{app.batch}/agreement"):
        pages.append(("owner", path, owner.text(path)[1]))
    for who in ("R-A", "R-B", "ADJ"):
        c = app.client(who)
        for path in ("/home", f"/review/{app.batch}/1", f"/api/item/{app.batch}/1", f"/adjudicate/{app.batch}", f"/adjudicate/{app.batch}/1"):
            pages.append((who, path, c.text(path)[1]))
    return pages


def test_every_page_has_the_banner_and_no_network_url(make_app):
    app = make_app("FX-13")
    app.assess("R-A", "nm", 2.0, "The forklift brakes hard as the person steps into the aisle.")
    app.assess("R-B", "ud", 3.0, "The racking hides the person at the closest moment.")
    app.decide("ADJ", "ud")
    app.store.agreement(app.batch)  # fully adjudicated: the panel renders too
    for who, path, text in _all_pages(app):
        assert not re.search(r"(https?|wss?|ftp)://|src=\"//|href=\"//", text, re.I), (who, path)
        if not path.startswith("/api/"):
            assert BANNER in text, (who, path)
        assert lint(re.sub(r"<[^>]+>", " ", text)) == [], (who, path)  # wording rules W1-W6


def test_owner_pages_are_owner_only(make_app):
    app = make_app("FX-13")
    for who in ("R-A", "ADJ"):
        c = app.client(who)
        for path in ("/setup", "/batches", f"/batch/{app.batch}", "/statuslog", f"/batch/{app.batch}/agreement"):
            assert c.get(path)[0] == 403, (who, path)
        assert c.post("/setup", {"pseudonym": "X", "role": "adjudicator", "qualification_ref": "q", "passphrase": "p"})[0] == 403
    assert app.client().get("/setup")[0] == 303  # signed out: back to sign-in


def test_agreement_panel_only_after_full_adjudication(make_app):
    app = make_app("FX-13")
    owner = app.client("Owner")
    assert owner.get(f"/batch/{app.batch}/agreement")[0] == 400
    app.assess("R-A", "nm", 2.0, "The forklift brakes hard as the person steps into the aisle.")
    app.assess("R-B", "ud", 3.0, "The racking hides the person at the closest moment.")
    assert owner.get(f"/batch/{app.batch}/agreement")[0] == 400
    app.decide("ADJ", "ud")
    status, text = owner.text(f"/batch/{app.batch}/agreement")
    assert status == 200 and "Cohen" in text and "stratified" in text and app.batch in text
    assert "completed T22 handbook training" in text and "R-A" not in text  # qualifications, never names


def test_sign_in_and_stored_passphrases(make_app):
    app = make_app("FX-13")
    status, _, _ = app.client().post("/login", {"profile": app.ids["R-A"], "passphrase": "wrong"})
    assert status == 401
    raw = (app.store.root / "profiles.json").read_text()
    assert "pw-R-A" not in raw and "owner-pass" not in raw and '"salt"' in raw


def test_confidence_and_rationale_are_checked_through_the_form(make_app):
    app = make_app("FX-13")
    for conf, rationale in (("2.5", "The forklift stops."), ("high", "The forklift stops."), ("2.0", "   ")):
        c = app.client("R-A")
        status, _, _ = c.post(f"/review/{app.batch}/1", {"label": "nm", "confidence": conf, "rationale": rationale})
        assert status == 400
    assert assessments(app) == []


def test_a_correction_replaces_the_assessment_before_adjudication(make_app):
    app = make_app("FX-13")
    app.assess("R-A", "nm", 2.0, "The forklift brakes hard.")
    first = assessments(app)[0]
    c = app.client("R-A")
    assert c.post(f"/review/{app.batch}/1", {"label": "ud", "confidence": "1.0", "rationale": "Looking again."})[0] == 400  # must name it
    assert c.post(f"/review/{app.batch}/1", {"label": "ud", "confidence": "1.0", "replaces": first["rva_id"],
                                             "rationale": f"Replaces {first['rva_id']}: the racking hides the contact point."})[0] == 303
    app.assess("R-B", "ud", 2.0, "The racking hides the person.")
    [adj] = adjudications(app)  # the latest per annotator agree: tier1 on ud
    assert (adj["tier"], adj["final_label"]) == ("tier1", "ud") and first["rva_id"] not in adj["assessment_ids"]


def test_exposed_adjudicator_cannot_adjudicate(make_app):
    app = make_app("FX-13")
    fx = app.fixture
    t = fx["inputs"]["target"]
    row = {"rva_id": "rva_" + "z" * 26, "annotator_id": app.ids["ADJ"], "namespace": "candidate_review", "target_type": "system_episode",
           "target_id": "ep_" + "y" * 26, "label": "nm", "confidence": 2.0, "rationale": "Seen with the system output shown.", "blind": False,
           "shown_system_output": True, "review_time_s": None, "review_time_s_null_reason": "not_supplied", "submitted_utc": "2026-11-19T08:00:00.000000Z"}
    app.store.import_candidate_review(row, recording_id=t["recording_id"])
    app.assess("R-A", "nm", 2.0, "The forklift brakes hard.")
    app.assess("R-B", "ud", 3.0, "The racking hides the person.")
    status, _, body = app.decide("ADJ", "ud")
    assert status == 400 and b"T22.2 (b)" in body and adjudications(app) == []


def test_a_reviewer_cannot_assess_a_target_twice_or_outside_the_batch(make_app):
    app = make_app("FX-13")
    app.assess("R-A", "nm", 2.0, "The forklift brakes hard.")
    c = app.client("R-A")
    assert c.post(f"/review/{app.batch}/1", {"label": "nm", "confidence": "2.0", "rationale": "Again."})[0] == 400
    assert c.post(f"/review/{app.batch}/2", {"label": "nm", "confidence": "2.0", "rationale": "No such item."})[0] == 400
    assert app.client("ADJ").get(f"/review/{app.batch}/1")[0] == 400  # no blind item before the audit is drawn


# --- static check (original V-02 text): no S5 or S8 run entry points ---------------------------------------------------------

def test_review_package_imports_no_s5_or_s8_entry_point():
    allowed = {"rq1.evaluation.estimators"}  # kappa and alpha only (T22.10 a)
    pkg = ROOT / "src" / "rq1" / "review"
    files = sorted(pkg.glob("*.py"))
    assert files
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                modules = [f"{node.module}.{a.name}" if node.module in ("rq1", "rq1.evaluation", "rq1.pipeline") else node.module for a in node.names]
            for name in modules:
                assert not (name == "rq1.events" or name.startswith("rq1.events.")), (path.name, name)
                assert not (name == "rq1.pipeline" or name.startswith("rq1.pipeline.")), (path.name, name)
                assert not name.startswith(("research", "run_m1a", "evaluate_m1a")), (path.name, name)
                if name == "rq1.evaluation" or name.startswith("rq1.evaluation."):
                    assert name in allowed, (path.name, name)
    source = "\n".join(p.read_text() for p in files)
    assert not re.search(r"import_module\([\"'](rq1\.(events|evaluation|pipeline)|research)", source)


# --- held data: the T-21 SDG validation run (skipped where the git-ignored outputs are not on the machine) -------------------

HELD = all((ROOT / p).exists() for p in ("out/m1a/run1/sdg", "out/s0_sdg/index.json", "out/t17_sdg", "data/raw/sdg"))


@pytest.mark.skipif(not HELD, reason="T-21 SDG validation outputs not present")
def test_sdg_frame_is_the_bl6_validation_episodes(tmp_path):
    from rq1.review.frame import SdgFrame
    frame = SdgFrame(ROOT)
    eps = frame.episodes()
    counts = {s: sum(1 for e in eps if e["stratum"] == s) for s in P.STRATA}
    assert counts == {"CT": 7, "UD": 44, "NM": 30, "PC": 212, "H": 17, "O": 9}  # BL-6, T-21 SDG validation run
    assert frame.config_id.startswith("rcf_") and frame.partition == "validation" and frame.dataset == "sdg"
    for e in eps[:: max(1, len(eps) // 12)]:
        d = frame.describe(e["target_id"])
        assert Path(d["video"]).exists() and 0.0 <= d["clip_start_s"] < d["clip_end_s"] <= 10.0 + 1e-9
        assert d["outlines"] == []  # every SDG validation recording has one person and one forklift: no outline (T22.4)
        assert d["g2_label"] in (None, "lbl_nm", "lbl_ud", "lbl_ct")


@pytest.mark.skipif(not HELD, reason="T-21 SDG validation outputs not present")
def test_end_to_end_batch_on_the_sdg_frame(tmp_path):
    from rq1.review.frame import SdgFrame
    store = Store(tmp_path / "s", kdf_iterations=1000)
    fx = load_fixture("FX-13")
    for a in fx["inputs"]["annotators"]:
        store.add_annotator(a["pseudonym"], a["role"], a["qualification_ref"], True, "pw", anr_id=a["anr_id"])
    rev = [a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "c_layer_reviewer"]
    adj = next(a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "adjudicator")
    frame = SdgFrame(ROOT)
    pilot = store.create_batch(frame, 101, rev, adj, pilot=True)
    batch = store.create_batch(frame, 202, rev, adj, pilot=False)
    assert len(pilot["target_ids"]) == 20 and len(batch["target_ids"]) == 60
    assert batch["strata_counts"]["CT"] == 7 - pilot["strata_counts"]["CT"]  # CT is capped at what the pilot left
    assert not set(pilot["target_ids"]) & set(batch["target_ids"])
    assert batch["configuration"] == {"name": "BL-6", "config_id": frame.config_id}


def test_v02_report_follows_the_wording_rules():
    text = (ROOT / "research/review_ui/V-02_report.md").read_text(encoding="utf-8")
    assert lint(text) == []
    assert "not a security boundary" in text and "T22.14" in text and "AR-61" in text
    assert not any(line.strip() == "EOF" for line in text.splitlines()) and ".venv/bin/python -c" not in text  # D-46 item 3 a
    assert "must never be used for real review" in text  # D-46 item 3 c
    for name in re.findall(r"screenshots/([\w.]+\.png)", text):
        assert (ROOT / "research/review_ui/screenshots" / name).exists(), name
