"""D-46: Appendix T T22.14 (contract E-1.2.21) readings in the V-02 application, the Owner-only audit trail view
(original V-02 item 3), and the round trip of the review records through the OBX export (original V-02 item 6).

Expected values are the CR-028 examples as T22.14 states them, or hand calculations recorded beside each test.
"""
from __future__ import annotations

import json
import re

import pytest

from conftest import SEED, clip_target, filler, load_fixture
from rq1.export import obx
from rq1.review import protocol as P
from rq1.review.frame import FixtureFrame
from rq1.review.server import render_agreement
from rq1.review.store import Store
from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError


# --- T22.14 (a) audit size: ceil(a_audit x tier-1 targets) ------------------------------------------------------------------

@pytest.mark.parametrize("n_tier1,n_audit", [(40, 4), (15, 2), (1, 1), (10, 1), (0, 0)])
def test_t22_14_a_audit_size(n_tier1, n_audit):
    # CR-028 item 1 examples: 40 -> 4; 15 -> ceil(1.5) = 2. FX-13e: 1 -> 1. 10 -> exactly 1.
    assert P.audit_count(n_tier1, 0.10) == n_audit


# --- T22.14 (b) alpha over the audited targets only; "not computed (n < 5)" -----------------------------------------------

def test_t22_14_b_alpha_needs_five_audited_targets():
    four = [["nm", "nm", "ud"], ["nm", "nm", "nm"], ["ud", "ud", "ud"], ["ct", "ct", "nm"]]
    assert P.alpha(four) is None
    five = four + [["not_hazardous", "not_hazardous", "not_hazardous"]]
    assert P.alpha(five) == pytest.approx(P.krippendorff_alpha_nominal(five))


def _panel(n_audited, alpha):
    return {"agreement_stat_ref": "rvb_x", "namespace": "reference", "configuration": "BL-6", "partition": "validation",
            "targets_per_stratum": {"NM": 4}, "n_targets": 4, "kappa_five_labels": 0.5, "kappa_four_labels": 0.5, "n_four_label_targets": 4,
            "alpha_audited": alpha, "n_audited": n_audited, "audit_agree": n_audited, "audit_agreement_rate": 1.0 if n_audited else None,
            "counts_by_tier_method": {"tier1 / agreement": 4}, "superseded_tier1": 0, "final_unsure": 0,
            "review_time_s_median_p90": {"reviewer 1": (1.0, 2.0)}, "qualifications": ["q"], "statements": ["s"]}


def test_t22_14_b_alpha_with_four_audited_targets_prints_not_computed():
    html = render_agreement(_panel(4, None))
    row = re.search(r"Krippendorff.*?</tr>", html).group(0)
    assert "not computed (n &lt; 5)" in row and "n = 4" in row and "provisional" not in html


def test_t22_14_b_alpha_value_is_printed_with_its_n():
    row = re.search(r"Krippendorff.*?</tr>", render_agreement(_panel(6, 0.25))).group(0)
    assert "0.250" in row and "n = 6" in row


# --- T22.14 (c) earlier batches excluded; (e) water-filling; short batches stated -------------------------------------------

def _store_and_people(tmp_path):
    fx = load_fixture("FX-13")
    store = Store(tmp_path / "s", kdf_iterations=1000)
    for a in fx["inputs"]["annotators"]:
        store.add_annotator(a["pseudonym"], a["role"], a["qualification_ref"], True, "pw", anr_id=a["anr_id"])
    rev = [a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "c_layer_reviewer"]
    return store, rev


def _pad(prefix: str, tag: str, k: int) -> str:
    """A 26-character ID body: the tag, then k zero-padded (so k = 1 and k = 10 differ)."""
    return f"{prefix}_{tag}{k:0{26 - len(tag)}d}"


def _frame(video, cfg, sizes):
    out = []
    for s, n in sizes.items():
        for k in range(n):
            out.append(clip_target({"target_type": "system_episode", "target_id": _pad("ep", s.lower(), k),
                                    "recording_id": _pad("rec", s.lower(), k), "config_id": cfg, "g2_label": None,
                                    "summary_label": s}, video))
    return FixtureFrame(out, config_id=cfg)


def test_t22_14_e_allocation_example():
    # CR-028 item 5, as T22.14 (e) states it.
    sizes = {"CT": 7, "UD": 44, "NM": 30, "PC": 212, "H": 17, "O": 9}
    assert P.allocate(sizes, 60, seed=1) == {"CT": 7, "UD": 11, "NM": 11, "PC": 11, "H": 11, "O": 9}


def test_t22_14_c_every_later_batch_excludes_all_earlier_targets(tmp_path, video):
    store, rev = _store_and_people(tmp_path)
    cfg = "rcf_" + "e" * 26
    frame = _frame(video, cfg, {"NM": 40, "PC": 60, "UD": 30})
    pilot = store.create_batch(frame, 1, rev, None, pilot=True)
    first = store.create_batch(frame, 2, rev, None, pilot=False)
    second = store.create_batch(frame, 3, rev, None, pilot=False)  # no longer refused (CR-028 item 3 decided)
    sets = [set(m["target_ids"]) for m in (pilot, first, second)]
    assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])
    assert (len(sets[0]), len(sets[1]), len(sets[2])) == (20, 60, 50)  # 130 targets: 20 + 60 + the 50 left
    # Second batch: 50 left over three strata, below 60 -> every stratum is exhausted.
    assert second["n_requested"] == 60 and second["n_drawn"] == 50 and second["frame_exhausted"] is True
    assert first["n_drawn"] == 60 and first["frame_exhausted"] is False
    with pytest.raises(ContractError, match="no targets left"):
        store.create_batch(frame, 4, rev, None, pilot=False)


def test_t22_14_c_a_redraw_of_an_earlier_target_is_refused(tmp_path, video, monkeypatch):
    store, rev = _store_and_people(tmp_path)
    cfg = "rcf_" + "f" * 26
    frame = _frame(video, cfg, {"NM": 30, "PC": 30})
    pilot = store.create_batch(frame, 1, rev, None, pilot=True)
    real_draw = P.draw

    def leaky(frame_rows, n, seed, exclude=()):  # a draw that ignores the exclusion
        alloc, ids = real_draw(frame_rows, n, seed)
        return alloc, sorted(set(ids) | {pilot["target_ids"][0]})

    monkeypatch.setattr(P, "draw", leaky)
    with pytest.raises(ContractError, match="T22.14"):
        store.create_batch(frame, 2, rev, None, pilot=False)
    assert len(store.batch_ids()) == 1


def test_t22_14_c_other_configuration_is_not_excluded(tmp_path, video):
    store, rev = _store_and_people(tmp_path)
    a = _frame(video, "rcf_" + "g" * 26, {"NM": 5})
    b = _frame(video, "rcf_" + "h" * 26, {"NM": 5})  # same target IDs, other configuration
    store.create_batch(a, 1, rev, None, pilot=True)
    assert len(store.create_batch(b, 1, rev, None, pilot=True)["target_ids"]) == 5


def test_manifests_name_t22_14_and_no_provisional_reading(tmp_path, video):
    store, rev = _store_and_people(tmp_path)
    m = store.create_batch(_frame(video, "rcf_" + "k" * 26, {"NM": 3}), 1, rev, None, pilot=True)
    assert "provisional_readings" not in m and m["readings"] == "Appendix T T22.14 (E-1.2.21)"


# --- T22.14 (d) pilot records -------------------------------------------------------------------------------------------------

def test_t22_14_d_pilot_assessments_are_stored_without_adjudication(make_app, video):
    fx = load_fixture("FX-13")
    app = make_app(targets=filler(fx["inputs"]["target"]["config_id"], video, n=2), annotators=fx["inputs"]["annotators"], with_pilot=False)
    reviewers = [a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "c_layer_reviewer"]
    adj = next(a["anr_id"] for a in fx["inputs"]["annotators"] if a["role"] == "adjudicator")
    app.batch = app.store.create_batch(app.frame, SEED, reviewers, adj, pilot=True)["batch_id"]
    for who in ("R-A", "R-B"):
        app.assess(who, "nm", 2.0, "The forklift stops close.")
        app.assess(who, "ud", 2.0, "The racking hides the person.")
    rows = [e["row"] for e in app.store.assessments() if e["batch_id"] == app.batch]
    assert len(rows) == 4 and all(r["namespace"] == "reference" for r in rows)
    assert app.store.manifest(app.batch)["pilot"] is True
    assert app.store.adjudications() == [] and app.store.status_log._entries() == [] and app.store.audit(app.batch) is None
    assert app.store.needs_adjudication(app.batch) == []


# --- audit trail view (original V-02 item 3) -----------------------------------------------------------------------------------

def _fx13e_done(make_app):
    app = make_app("FX-13e")
    app.assess("R-A", "nm", 3.0, "The person jumps back as the forks pass.")
    app.assess("R-B", "nm", 2.0, "The forklift passes very close and the person steps back.")
    app.assess("ADJ", "ud", 2.0, "The person leaves the frame just before the forks reach them.")
    app.decide("ADJ", "ud")
    return app


def test_audit_trail_shows_the_full_status_history_and_chain_check(make_app):
    app = _fx13e_done(make_app)
    target = app.fixture["inputs"]["target"]["target_id"]
    owner = app.client("Owner")
    status, listing = owner.text("/audit")
    assert status == 200 and target in listing and "intact" in listing
    status, page = owner.text(f"/audit/{target}")
    assert status == 200 and "Hash chain (CT-E-24): intact" in page
    rows = re.findall(r'<tr class="entry">(.*?)</tr>', page, re.S)
    assert len(rows) == 2
    assert "confirmed" in rows[0] and "tier1" in rows[0] and "agreement" in rows[0]
    assert "rejected" in rows[1] and "tier2" in rows[1] and "adjudicator" in rows[1]
    for entry in app.store.status_log._entries():
        assert entry["record_hash"] in page and entry["basis_ids"][0] in page
    assert "<form" not in page.split("</header>", 1)[1]  # read-only


def test_audit_trail_reports_a_broken_chain(make_app):
    app = _fx13e_done(make_app)
    path = app.store.status_log.path
    lines = path.read_text().splitlines()
    entry = json.loads(lines[0])
    entry["status"] = "rejected"
    lines[0] = canonical_json(entry).decode()
    path.write_text("\n".join(lines) + "\n")
    status, page = app.client("Owner").text(f"/audit/{app.fixture['inputs']['target']['target_id']}")
    assert status == 200 and "BROKEN" in page


def test_audit_trail_is_owner_only(make_app):
    app = _fx13e_done(make_app)
    target = app.fixture["inputs"]["target"]["target_id"]
    for who in ("R-A", "R-B", "ADJ"):
        c = app.client(who)
        assert c.get("/audit")[0] == 403 and c.get(f"/audit/{target}")[0] == 403
    assert app.client().get("/audit")[0] == 303


# --- round trip through the OBX export (original V-02 item 6) -------------------------------------------------------------------

def test_review_records_round_trip_through_the_obx_export(make_app):
    app = _fx13e_done(make_app)
    tables = {"adjudication": [e["row"] for e in app.store.adjudications()],
              "validation_status_log": app.store.status_log._entries()}
    assert obx.check_content(tables) == []
    files = obx.serialize("fixture_verification", tables)
    for table, rows in tables.items():
        data = json.loads(files[f"tables/{table}.json"])
        assert data["metadata"]["part"] == "5_validation_summary"
        assert sorted(map(canonical_json, data["rows"])) == sorted(map(canonical_json, rows))
