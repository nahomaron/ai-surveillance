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
