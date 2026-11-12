"""T-03. Expected numbers below are retyped from Appendix N and T, not imported from the generator."""
import copy
import hashlib
import json
import math
from pathlib import Path

import pytest

from rq1.fixtures import records
from rq1.schema.errors import ContractError

ROOT = Path(__file__).resolve().parents[2] / "fixtures"
REQUIRED_IDS = {f"N1-T{i}" for i in range(1, 14)} | {"N2-G1", "N2-G2", "N2-G3", "FX-TIE", "FX-W", "FX-CM"} \
    | {f"FX-ID-{i}" for i in range(1, 9)} | {f"FX-RC-{i}" for i in range(1, 7)} \
    | {"FX-A3.1", "FX-B1", "FX-B2", "FX-B3", "FX-C1", "FX-C2", "FX-D1", "FX-D2", "FX-A3", "FX-A4", "FX-12", "FX-11", "TEST-ONLY-PARAMETERS"}


def load(fixture_id):
    return json.loads((ROOT / "records" / f"{fixture_id}.json").read_text(encoding="utf-8"))


@pytest.mark.determinism
def test_every_required_fixture_exists():
    assert {p.stem for p in (ROOT / "records").glob("*.json")} == REQUIRED_IDS


@pytest.mark.determinism
def test_generator_output_matches_committed_files(tmp_path):
    records.build_all(tmp_path)
    for path in sorted((ROOT / "records").glob("*.json")):
        assert (tmp_path / "records" / path.name).read_bytes() == path.read_bytes(), path.name
    assert (tmp_path / "manifest.json").read_bytes() == (ROOT / "manifest.json").read_bytes()


@pytest.mark.determinism
def test_manifest_hashes_match_files():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert set(manifest["fixtures"]) == {f"records/{i}.json" for i in REQUIRED_IDS}
    for path, digest in manifest["fixtures"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path


@pytest.mark.determinism
@pytest.mark.parametrize("fixture_id", sorted(REQUIRED_IDS))
def test_each_fixture_cites_its_source_and_is_test_only(fixture_id):
    fixture = load(fixture_id)
    assert fixture["id"] == fixture_id and fixture["source"].strip()
    assert fixture["version_label"] == "TEST-ONLY"


# Appendix N1, retyped: (contact, K, labels, summary by the section 6 precedence).
N1 = {
    "T1": ("none_observed", 0, ["O"], "O"), "T2": ("none_observed", 0, ["H"], "H"), "T3": ("none_observed", 0, ["PC"], "PC"),
    "T4": ("none_observed", 0, ["H", "PC"], "PC"), "T5": ("none_observed", 1, ["H", "NM"], "NM"), "T6": ("undetermined", 1, ["H", "UD"], "UD"),
    "T7": ("suspected", 1, ["H", "CT"], "CT"), "T8": ("undetermined", 1, ["O"], "O"), "T9": ("suspected", 1, ["O", "CT"], "CT"),
    "T10": ("undetermined", 2, ["PC", "IE"], "PC"), "T11": ("not_assessable", 2, ["H", "IE"], "H"),
}


@pytest.mark.determinism
@pytest.mark.parametrize("row", sorted(N1))
def test_n1_expected_values(row):
    expected = load(f"N1-{row}")["expected"]
    contact, k, labels, summary = N1[row]
    assert (expected["contact_state"], expected["K"], expected["labels"], expected["summary_label"]) == (contact, k, labels, summary)


@pytest.mark.determinism
def test_n1_t8_routes_to_review():
    assert load("N1-T8")["expected"]["review_route"] is True


@pytest.mark.determinism
def test_n1_t12_two_episodes_and_t13_discard():
    t12 = load("N1-T12")["expected"]["episodes"]
    assert [(e["start_frame"], e["end_frame_excl"], e["span_s"], e["labels"]) for e in t12] == [(0, 3, 0.3, ["H"]), (13, 20, 0.7, ["H"])]
    assert load("N1-T13")["expected"]["discarded"] == [{"start_frame": 0, "end_frame_excl": 1, "span_s": 0.1, "discard_reason": "shorter_than_t_min"}]
    assert load("N1-T13")["expected"]["episodes"] == []


@pytest.mark.determinism
def test_run_length_expansion():
    assert records.expand("1×3,0×2") == [1, 1, 1, 0, 0]
    t5 = load("N1-T5")["inputs"]
    assert records.expand(t5["E"]) == [0] * 8 + [1] * 3 + [0] * 9
    assert len(records.expand(load("N1-T12")["inputs"]["P"])) == 20


@pytest.mark.determinism
def test_n2_g2_values():
    expected = load("N2-G2")["expected"]
    assert len(expected["clearance_m"]) == 50
    assert expected["clearance_m"][0] == pytest.approx(1.7518, abs=5e-5)  # N2: "1.7518 at x = -2.5"
    assert min(expected["clearance_m"]) == pytest.approx(1.10, abs=1e-9)
    assert expected["episodes"] == [{"start_frame": 0, "end_frame_excl": 50, "labels": ["H"], "minclr_m": 1.1}]
    assert set(expected["P"]) == {1} and set(expected["M"]) == {1} and set(expected["C_by_R3"]) == {0}


@pytest.mark.determinism
def test_n2_g1_values():
    expected = load("N2-G1")["expected"]
    assert set(expected["clearance_m"]) == {1.1} and set(expected["M"]) == {0}
    assert expected["episodes"][0]["duration_detected_s"] == 5.0 and expected["episodes"][0]["labels"] == ["O"]


@pytest.mark.determinism
def test_n2_g3_values():
    expected = load("N2-G3")["expected"]
    assert expected["clearance_m"][-1] == pytest.approx(2.35, abs=1e-9)
    assert expected["pred_min_clearance_m"][0] == pytest.approx(0.70, abs=1e-9)
    assert expected["pred_min_clearance_m"][-1] == pytest.approx(0.70 - 1.5 * 0.9, abs=1e-9)
    assert set(expected["P"]) == {0} and set(expected["C_by_R3"]) == {1}
    assert expected["episodes"] == [{"start_frame": 0, "end_frame_excl": 10, "labels": ["PC"], "minclr_m": 2.35}]


@pytest.mark.determinism
def test_fx_tie():
    fixture = load("FX-TIE")
    assert fixture["expected"]["matches"] == [["s1", "r1"]] and fixture["expected"]["misses"] == ["r2"]


@pytest.mark.determinism
def test_fx_w():
    expected = load("FX-W")["expected"]
    assert expected["weighted_recall"] == 0.71875 and expected["unweighted_recall"] == 0.70
    assert expected["n_eff"] == pytest.approx(3.3793103448, abs=1e-9)


@pytest.mark.determinism
def test_fx_cm():
    assert load("FX-CM")["expected"] == {"CM-01": 0.6, "CM-03": 0.6}


@pytest.mark.determinism
def test_fx_id_expectations():
    assert load("FX-ID-1")["expected"]["tracks"]["A"] == {"status": "one_to_one", "matched_frames": 50, "dominant_share": 1.0}
    a = load("FX-ID-2")["expected"]["tracks"]["A"]
    assert (a["n_identities"], a["n_switches"], a["status"], a["dominant_identity"]) == (2, 1, "id_switch", "p1")
    three = load("FX-ID-3")["expected"]
    assert three["tracks"]["A"]["status"] == three["tracks"]["B"]["status"] == "fragment" and three["missed_reference_frames"]["p1"] == [20, 25]
    assert three["CM-01"]["p1"] == 0.9
    assert load("FX-ID-4")["expected"]["CM-01"]["p2"] == 0
    assert load("FX-ID-5")["expected"]["tracks"]["A"]["status"] == "unmatched_system"
    assert load("FX-ID-6")["expected"]["ambiguous_frames"] == [10, 15]
    assert load("FX-ID-7")["expected"]["event_pair"] == ["p1", "f1"]
    eight = load("FX-ID-8")["expected"]
    assert (eight["event_pair"], eight["match_type"], eight["primary_stage"]) == (None, "false_alert", "perception")


@pytest.mark.determinism
def test_fx_id_6_box_iou_hand_calculation():
    fixture = load("FX-ID-6")["inputs"]
    box = {s["object"]: s["box"] for s in fixture["segments"] if s["start"] == 10}
    def iou(a, b):
        w = max(0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = w * h
        return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)
    assert iou(box["A"], box["p1"]) == pytest.approx(0.60) and iou(box["A"], box["p2"]) == pytest.approx(0.59)


@pytest.mark.determinism
def test_fx_rc_expected_spans():
    assert load("FX-RC-1")["expected"]["unobservable_spans"] == [{"t_start_tl_s": 10.0, "t_end_tl_s": 11.5, "reason": "unusable_footage", "excluded_support_s": 1.5}]
    two = load("FX-RC-2")["expected"]["unobservable_spans"][0]
    assert (two["t_start_tl_s"], two["t_end_tl_s"], two["reason"], two["frame_bounds"]) == (20.1, 23.0, "gap_unobserved", None)
    three = load("FX-RC-3")["expected"]["unobservable_spans"][0]
    assert (three["t_start_tl_s"], three["t_end_tl_s"], three["reason"], three["frame_bounds"]) == (25.0, 35.0, "not_recorded", None)
    assert load("FX-RC-4")["expected"]["CM-02_numerator"] == 0
    assert load("FX-RC-5")["expected"]["ref_activity_state"] == "reference_verified_absent"
    assert load("FX-RC-6")["expected"]["rejected_by"] == ["RC-02", "RC-03"]


@pytest.mark.determinism
@pytest.mark.parametrize("fixture_id,key,value", [
    ("FX-B2", "expected_error", "CB-03: height requires full_camera calibration with height reference, multi-view, or simulator truth"),
    ("FX-C2", "expected_error", "CC-01: experiment E2 not allowed in schema v1.1"),
    ("FX-D2", "expected_error", "CD-02: unusable coverage requires not_evaluated"),
    ("FX-A4", "expected_error", "TI-11: not_recorded segments only on aligned_session timelines within a declared session extent"),
])
def test_appendix_t4_verbatim_errors(fixture_id, key, value):
    assert load(fixture_id)["record"][key] == value


@pytest.mark.determinism
def test_fx_c1_times_sum_to_coobserved():
    r = load("FX-C1")["record"]
    assert math.isclose(r["t_occupied_detected_s"] + r["t_occupied_inferred_s"] + r["t_not_occupied_s"] + r["t_occupancy_unknown_s"], r["t_coobserved_s"])


@pytest.mark.determinism
def test_fx_a3_1_setup():
    fixture = load("FX-A3.1")
    assert fixture["inputs"]["windows_per_recording"] == 10 and fixture["inputs"]["pi"] == 0.2
    assert fixture["expected"]["headline_from_original_plan"] == "refused"


@pytest.mark.determinism
def test_fx_12_is_measurement_only():
    expected = load("FX-12")["expected"]
    assert expected["episodes"] == [] and expected["load_mass_kg_null_reason"] == "not_supplied"
    assert expected["height_m"] == 2.4 and expected["height_sigma_m"] == 0.3


@pytest.mark.determinism
def test_test_only_values():
    v = load("TEST-ONLY-PARAMETERS")["parameters"]
    assert (v["k_sup"], v["d_p"], v["k_img"], v["m_gap"], v["t_min"], v["w_post"], v["d_nm"], v["k_sigma"], v["iou_cm"], v["eps_amb"]) == (1.5, 2.0, 0.05, 5, 0.2, 1.0, 0.5, 2.0, 0.5, 0.02)
    assert v["v_part"] == 0.5  # Appendix T T8.6 (E-1.2.6)
    assert v["k_c_turn"] == 3.0  # Appendix T T9.3 (E-1.2.7)


@pytest.mark.determinism
def test_n1_t10_inputs_follow_t9_9():
    # Appendix T T9.9 (E-1.2.7, Architect amendment) corrects the T10 inputs; the expected values are unchanged.
    t10, t11 = load("N1-T10"), load("N1-T11")
    assert (t10["inputs"]["Q"], t10["inputs"]["clearance_frames"], t10["inputs"]["ca_frame"], t10["inputs"]["minclr_m"]) == ("1×12,0×8", [0, 12], 15, 1.2)
    assert (t11["inputs"]["Q"], t11["inputs"]["clearance_frames"], t11["inputs"]["ca_frame"]) == ("1×10,0×10", [0, 10], 15)
    assert "T9.9" in t10["source"]


@pytest.mark.determinism
def test_generator_refuses_inconsistent_expected_labels():
    fixture = copy.deepcopy(records.FIXTURES["N1-T5"])
    fixture["expected"]["labels"] = ["H", "UD"]
    with pytest.raises(ContractError) as exc:
        records.check_fixture(fixture)
    assert exc.value.code == "ERR-INVARIANT"


@pytest.mark.determinism
def test_generator_refuses_wrong_k():
    fixture = copy.deepcopy(records.FIXTURES["N1-T5"])
    fixture["expected"]["K"] = 0
    with pytest.raises(ContractError):
        records.check_fixture(fixture)


@pytest.mark.determinism
def test_generator_refuses_wrong_weighted_arithmetic():
    fixture = copy.deepcopy(records.FIXTURES["FX-W"])
    fixture["expected"]["weighted_recall"] = 0.75
    with pytest.raises(ContractError):
        records.check_fixture(fixture)
