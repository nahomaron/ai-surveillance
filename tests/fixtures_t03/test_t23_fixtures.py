"""Appendix T T23 (contract E-1.2.22; D-48): fixtures FX-14 and FX-14a to FX-14i.

Expected values below are retyped from the T23 "Fixtures and tests" paragraph (and the T23.5 / T22.8 rules applied by
hand where the paragraph names only the outcome; each fixture's `hand_calculation`). They are not imported from the
generator. The application runs these fixtures in tests/workflow/.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "records"


def load(fixture_id):
    return json.loads((ROOT / f"{fixture_id}.json").read_text(encoding="utf-8"))


def test_fx14():
    e = load("FX-14")["expected"]
    assert (e["state"], e["statuses"], e["I2"], len(e["assessments"])) == ("recorded", ["confirmed"], [1, 1], 1)
    assert e["assessments"][0]["namespace"] == "candidate_review"


def test_fx14a_and_b():
    a, b = load("FX-14a")["expected"], load("FX-14b")["expected"]
    assert (a["state"], a["statuses"], a["I3"], a["I4"]) == ("closed_rejected", ["disputed", "rejected"], [1, 1], [0, 1])
    assert (b["state"], b["statuses"], b["I4"], b["wording"]) == ("recorded", ["disputed", "confirmed"], [1, 1],
                                                                 "recorded near miss (safety-manager overturn)")


def test_fx14c():
    e = load("FX-14c")["expected"]
    assert (e["kind_initial"], e["hours_worked"], e["incidence_rate"]) == ("incident_draft", 200000.0, 1.0)
    assert e["I9_by_criterion"] == {"medical_treatment_beyond_first_aid": 1}
    assert e["export_banner"] == "Equivalent-form data for manual transcription. Not a submission to OSHA."
    assert len(e["incident_fields"]) == 12


def test_fx14d_e_f():
    d, e, f = load("FX-14d")["expected"], load("FX-14e")["expected"], load("FX-14f")["expected"]
    assert (d["I8"], d["F4_k_miss_1"]) == (1, True)
    assert [x["t_start_tl_s"] for x in load("FX-14e")["inputs"]["episodes"]] == [0.0, 1.5, 3.2]
    assert (e["reports"], e["members"], e["assessments_n"]) == (1, 3, 3)
    assert (f["theta_rej"], f["n_flag_min"], f["rejected_10"]["wilson_lower_approx"], f["rejected_10"]["F1"], f["rejected_6"]["F1"]) == \
        (0.5, 10, 0.552, True, False)


def test_all_t23_fixtures_present():
    for k in ("FX-14", "FX-14a", "FX-14b", "FX-14c", "FX-14d", "FX-14e", "FX-14f", "FX-14g", "FX-14h", "FX-14i"):
        fx = load(k)
        assert fx["source"].startswith("Appendix T T23") and fx["version_label"] == "TEST-ONLY" and fx["hand_calculation"]


# --- E-1.2.23 (D-49): FX-14j to FX-14ad, retyped from the D-49.1 section 6.1 table ----------------------------------

E1223 = ["FX-14" + c for c in "jklmnopqrstuvwxyz"] + ["FX-14aa", "FX-14ab", "FX-14ac", "FX-14ad"]


def test_e1223_fixtures_present_and_sourced():
    for k in E1223:
        fx = load(k)
        assert fx["source"].startswith("Appendix T T23.16-T23.27 (E-1.2.23)") and fx["version_label"] == "TEST-ONLY"
        assert fx["hand_calculation"]


def test_fx14j_to_n():
    assert load("FX-14j")["expected"] == {"refused": True, "rule": "VR-E-056"}
    assert load("FX-14j")["inputs"]["row"]["namespace"] == "candidate_review"
    assert load("FX-14j")["inputs"]["row"]["reference_class"] == "independent_expert_judgment"
    assert load("FX-14k")["expected"] == {"refused": True, "rule": "VR-E-056"}
    assert (load("FX-14k")["inputs"]["row"]["namespace"], load("FX-14k")["inputs"]["row"]["reference_class"]) == ("reference", None)
    e = load("FX-14l")["expected"]
    assert (e["reference_adjudications"], e["ev_m12_targets"], e["kappa_targets"], e["candidate_review_adjudications"]) == (1, 1, 1, 3)
    assert load("FX-14m")["expected"] == {"violation_found": True, "tree_clean": True}
    assert load("FX-14n")["expected"] == {"refused": True, "rule": "T23.25 (d)"}
    assert load("FX-14n")["inputs"]["qualification_ref"].startswith("workflow ")


def test_fx14o_p():
    assert load("FX-14o")["expected"]["targets_of_R_in_S2_batch"] == 0
    e = load("FX-14p")["expected"]
    assert {k for k, v in e.items() if v.startswith("refused")} == {"approved_then_reference", "display_only_then_reference",
                                                                     "owner_of_s1_then_reference"}


def test_fx14q_to_u():
    q, r = load("FX-14q"), load("FX-14r")
    assert [(x["t_start_tl_s"], x["t_end_tl_s"]) for x in q["inputs"]["episodes"]] == [(10.0, 12.0), (10.5, 12.5)]
    assert (q["expected"]["reports"], q["expected"]["members"], q["expected"]["new_reports"], q["expected"]["I7_after_both_approved"]) == (1, 2, 2, 2)
    assert q["expected"]["original_state"] == "closed_split"
    assert (r["expected"]["I7"], r["expected"]["group_resolution"]) == (1, "one_interaction")
    s = load("FX-14s")
    widened = [(x["t_start_tl_s"] - 0.5, x["t_end_tl_s"] + 0.5) for x in s["inputs"]["episodes"]]
    assert widened == [(0.0, 3.0), (3.0, 5.0)] and s["expected"]["groups"] == 1
    t = load("FX-14t")
    assert t["expected"] == {"reports": 2, "basis": "grouped per camera: no common clock"}
    assert {x["timeline_kind"] for x in t["inputs"]["episodes"]} == {"recording_local"}
    u = load("FX-14u")["expected"]
    assert (u["I7_after_confirm"], u["I7_after_overturn"], u["B_duplicate_of_after_overturn"]) == (1, 2, None)


def test_fx14v_to_y():
    assert load("FX-14v")["expected"]["store_bytes_changed"] is False and len(load("FX-14v")["expected"]["refused"]) == 3
    w = load("FX-14w")["expected"]
    assert (w["entries_total"], w["as_of_entry"], w["revised_before"], w["revised_after"]) == (20, 12, 0, 1)
    x = load("FX-14x")["expected"]
    assert (x["I9"], x["withdrawn"], x["after_reopen_overturn"]["determination"], x["after_set_again"]["I9"]) == (0, 1, "withdrawn", 1)
    y = load("FX-14y")
    assert y["inputs"]["hours_worked"] == 100000.0
    assert (y["expected"]["I9"], y["expected"]["incidence_rate"], y["expected"]["provisional"]) == (1, 1 * 200_000 / 100_000, True)


def test_fx14z_to_ad():
    z = load("FX-14z")["expected"]
    assert z["cases"] == {"i": "unmonitored", "ii": "observability undetermined", "iii": "observable, matched",
                          "iv": "observable, no matching AI alert"} and z["I8_iv"] == 1
    aa = load("FX-14aa")["expected"]
    assert (aa["monitored_area_hours"], aa["camera_hours"], aa["rate_denominator_h"], aa["I7_ai_rate"]) == (1.0, 2.0, 1.0, 1.0)
    ab = load("FX-14ab")
    assert ab["expected"]["mixed"]["text"] == "not combined: members use different geometry methods"
    assert ab["expected"]["same"]["combined_m"] == min(m["minclr_m"] for m in ab["inputs"]["same"]) == 0.8
    ac = load("FX-14ac")
    assert ac["inputs"]["source_quality"]["cm03"] == 0.12 and ac["expected"]["figures"] == {"cm03": 0.12, "ev_m1": 0.11, "ev_m2": 0.22}
    assert load("FX-14ad")["expected"]["escaped"] == "&lt;b&gt;precision 0.8&lt;/b&gt;"
