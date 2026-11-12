"""T-16: the M0 fixture pipeline end to end (WP-11). Expected values come from Appendix N2 G2, Appendix T FX-12 (CT-E-26),
CT-E-28 and F.1 A2 (fixture export)."""
import json
from pathlib import Path

import pytest

from rq1.pipeline import m0

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    one, two = tmp_path_factory.mktemp("m0_one"), tmp_path_factory.mktemp("m0_two")
    return (m0.run(one), one), (m0.run(two), two)


@pytest.mark.determinism
def test_two_runs_are_identical(runs):
    (a, _), (b, _) = runs
    assert a["artifacts"] == b["artifacts"]  # every artifact ID and payload hash (exact-class stages)
    assert a["export_files"] == b["export_files"]  # every exported file, byte for byte (SHA-256)
    assert set(a["artifacts"]) == {"S0", "S1", "S3", "S4", "S5", "X0b", "V0", "CV-SIM", "X0c", "S8", "S8f", "S4-E2"}


@pytest.mark.determinism
def test_n2_g2_end_to_end(runs):
    (result, work), _ = runs
    expected = json.loads((FIX / "N2-G2.json").read_text())["expected"]["episodes"][0]
    episodes = json.loads((work / "out" / "fixture" / "tables" / "episode.json").read_text())["rows"]
    assert len(episodes) == 1
    ep = episodes[0]
    assert (ep["start_frame"], ep["end_frame_excl"]) == (expected["start_frame"], expected["end_frame_excl"])
    assert [n for n in ("O", "H", "PC", "NM", "UD", "CT", "IE") if ep[f"lbl_{n}"]] == expected["labels"] == ["H"]
    assert ep["minclr_m"] == pytest.approx(expected["minclr_m"], abs=1e-6)
    assert ep["duration_detected_s"] == pytest.approx(5.0, abs=1e-6)  # 50 frames x 0.1 s, decoded from the clip
    assert [list(t) for t in result["summary"]["match_types"]] == [["G1", "matched"], ["any", "matched"]] and result["summary"]["misses_and_false_alerts"] == 0


@pytest.mark.determinism
def test_ct_e_28_lineage_end_to_end(runs):
    (result, _), _ = runs
    assert result["lineage_untraced"] == []  # S8, S8f and S4-E2 reach source_file through S5, S4, S3, S1, S0


@pytest.mark.determinism
def test_ct_e_26_end_to_end(runs):
    (_, work), _ = runs
    expected = json.loads((FIX / "FX-12.json").read_text())["expected"]
    root = work / "out" / "fixture" / "tables"
    load = json.loads((root / "load_state.json").read_text())["rows"]
    profiles = json.loads((root / "e2_occupancy_profile.json").read_text())["rows"]
    assert len(load) == 1 and len(profiles) == expected["n_e2_occupancy_profiles"]
    assert (load[0]["elevation_state"], load[0]["height_m"], load[0]["height_sigma_m"]) == (expected["elevation_state"], expected["height_m"], expected["height_sigma_m"])
    assert (load[0]["load_mass_kg"], load[0]["load_mass_kg_null_reason"]) == (None, "not_supplied")
    # The export ran its forbidden-content scan (it raises otherwise); E2 produced no episode.
    assert all(e["pow_id"] for e in json.loads((root / "episode.json").read_text())["rows"])


@pytest.mark.determinism
def test_s8_specification_carries_evaluation_config(runs):
    (result, _), _ = runs
    assert result["configurations"]["evc"].startswith("evc_")
    assert result["artifacts"]["S8"]["rows"]["match_record"] == 2 and result["artifacts"]["S8"]["rows"]["completeness_record"] == 7


@pytest.mark.determinism
def test_fixture_export_and_report(runs):
    (result, work), _ = runs
    manifest = json.loads((work / "out" / "fixture" / "manifest.json").read_text())
    assert (manifest["export_class"], manifest["research_use"], manifest["contract"]) == ("fixture_verification", False, "E-1.2.11")
    assert not (work / "out" / "research").exists()
    text = (work / "out" / "fixture" / "M0_fixture_report.md").read_text()
    assert text.splitlines()[0] == "FIXTURE VERIFICATION — NOT RESEARCH RESULTS"
    assert "## Implementation conformance" in text and "claim level none" in text
    assert result["summary"]["cm01"] == {"detected": 1.0, "detected_plus_inferred": 1.0}
