"""T-15 part A: OBX export classes and content (F.1 A2 CT-X-01, 02, 03, 05; E-1.2.1 section 11; Appendix T CT-E-26,
CT-E-27 (research content scan), VR-E-040). Expected values come from the contract text or the fixtures."""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

from rq1.events import s5
from rq1.export import obx
from rq1.fixtures import identity_rows as rows
from rq1.schema.errors import ContractError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "events"))
from test_t10 import build_s5, s4_of, s5_config  # noqa: E402

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"


def fixture_inputs():
    """Tables from the M0 fixture pipeline: G1 with a person gap, so two POWs and a continuation-linked episode."""
    s1, s4 = s4_of("N2-G1", person_states={i: "missing" for i in range(10, 26)})
    built = build_s5(s1, s4)
    tables = {"pow": s4.tables["pow"], "exposure_profile": s4.tables["exposure_profile"],
              **{t: built.tables[t] for t in ("episode", "discarded_episode", "candidate_event", "event_count_summary")}}
    cfg = s5_config()
    configurations = [{**s5.rule_configuration(cfg), "config_id": s5.config_id(cfg)}]
    datasets = [rows.row("dataset_source", name="fx-m0", dataset_kind="fixture")]
    return tables, configurations, datasets


@pytest.mark.determinism
def test_ct_x_01_fixture_export(tmp_path):
    tables, configurations, datasets = fixture_inputs()
    manifest = obx.export("fixture_verification", tables, configurations, datasets, tmp_path)
    assert (manifest["export_class"], manifest["research_use"]) == ("fixture_verification", False)
    root = tmp_path / "fixture"  # EXP-1: separate root
    assert not (tmp_path / "research").exists()
    dictionary = json.loads((root / "data_dictionary.json").read_text())["schemas"]
    for table in tables:
        data = json.loads((root / "tables" / f"{table}.json").read_text())
        assert data["metadata"]["research_use"] is False and data["metadata"]["export_class"] == "fixture_verification"
        for row in data["rows"]:
            jsonschema.validate(row, dictionary[table])  # validates against the OBX schemas
    assert manifest["parts"]["4_events"] == ["candidate_event", "discarded_episode", "episode", "event_count_summary"]


@pytest.mark.determinism
def test_episode_export_carries_continuation(tmp_path):
    # Architect ruling on AR-40 item 4: OBX carries continuation_of_nk, so two linked episodes are never read as two interactions.
    tables, configurations, datasets = fixture_inputs()
    obx.export("fixture_verification", tables, configurations, datasets, tmp_path)
    episodes = json.loads((tmp_path / "fixture" / "tables" / "episode.json").read_text())["rows"]
    linked = [e for e in episodes if e["continuation_of_nk"] is not None]
    assert len(episodes) == 2 and len(linked) == 1 and linked[0]["continuation_of_id"] in {e["ep_id"] for e in episodes}


@pytest.mark.determinism
def test_ct_x_02_research_export_with_test_only_config_is_refused(tmp_path):
    tables, configurations, datasets = fixture_inputs()
    research_ds = [rows.row("dataset_source", name="real", dataset_kind="research")]
    with pytest.raises(ContractError) as exc:
        obx.export("research", tables, configurations, research_ds, tmp_path)
    assert exc.value.code == "ERR-EXPORT-CLASS" and not any(tmp_path.iterdir())  # nothing written


def test_ct_x_03_fixture_export_with_research_inputs_is_refused(tmp_path):
    cfg = {"config_id": "rcf_" + "a" * 26, "version_label": None}
    with pytest.raises(ContractError) as exc:
        obx.check_class("fixture_verification", [cfg], [])
    assert exc.value.code == "ERR-EXPORT-CLASS"
    with pytest.raises(ContractError):
        obx.check_class("fixture_verification", [{**cfg, "version_label": "TEST-ONLY"}], [rows.row("dataset_source", dataset_kind="research")])


def test_exp_2_test_partition_metrics_need_preregistration():
    cfg = {"config_id": "rcf_" + "b" * 26, "version_label": None, "preregistration_ref": None}
    ds = [rows.row("dataset_source", dataset_kind="research")]
    obx.check_class("research", [cfg], ds)  # no test-partition metric: allowed
    with pytest.raises(ContractError) as exc:
        obx.check_class("research", [cfg], ds, test_partition_config_ids={cfg["config_id"]})
    assert exc.value.code == "ERR-EXPORT-CLASS"
    obx.check_class("research", [{**cfg, "preregistration_ref": "docs/preregistration_FROZEN.md"}], ds, test_partition_config_ids={cfg["config_id"]})


@pytest.mark.determinism
def test_ct_x_05_serializer_identical_apart_from_class_fields():
    tables, _, _ = fixture_inputs()
    a, b = obx.serialize("fixture_verification", tables), obx.serialize("research", tables)
    assert set(a) == set(b)

    def strip(data):
        doc = json.loads(data)
        doc.get("metadata", doc).pop("export_class", None)
        doc.get("metadata", doc).pop("research_use", None)
        doc.pop("files", None)  # file hashes differ only because the class fields differ
        return doc
    for name in a:
        assert strip(a[name]) == strip(b[name]), name


@pytest.mark.determinism
def test_export_is_byte_deterministic(tmp_path):
    tables, configurations, datasets = fixture_inputs()
    one = obx.serialize("fixture_verification", tables)
    shuffled = {t: list(reversed(r)) for t, r in reversed(list(tables.items()))}
    assert obx.serialize("fixture_verification", shuffled) == one


@pytest.mark.determinism
def test_ct_e_27_content_scan():
    tables, _, _ = fixture_inputs()
    assert obx.check_content(tables) == []  # no forbidden names or values in the fixture pipeline's export
    bad = {**tables, "episode": [{**tables["episode"][0], "recording_id": "osha_300_log"}]}
    issues = obx.check_content(bad)
    assert any(i.rule == "VR-E-041" and i.code == "ERR-FORBIDDEN-FIELD" for i in issues)


def test_vr_e_040_in_exports():
    seg = rows.row("activity_segment", ai_activity_state="observed_no_detection")
    assert obx.check_content({"activity_segment": [seg]}) == []
    ref_state = {**seg, "ai_activity_state": "reference_verified_absent"}
    assert any(i.rule == "VR-E-040" for i in obx.check_content({"activity_segment": [ref_state]}))
    zero = {**seg, "exp_t_in_band_detected_s": [0.0, 0.0]}  # observed_no_detection must never map to zero exposure
    assert any(i.rule == "VR-E-040" and "zero exposure" in i.message for i in obx.check_content({"activity_segment": [zero]}))


def test_ct_e_26_fx_12_e2_records():
    # Revised FX-12 (Appendix T): load_state elevated, height 2.4 +- 0.3 m, mass null not_supplied; one e2_occupancy_profile; no episodes.
    expected = json.loads((FIX / "FX-12.json").read_text())["expected"]
    load = rows.row("load_state", elevation_state=expected["elevation_state"], height_m=expected["height_m"], height_sigma_m=expected["height_sigma_m"])
    load["load_mass_kg"], load["load_mass_kg_null_reason"] = None, expected["load_mass_kg_null_reason"]
    profile = rows.row("e2_occupancy_profile")
    tables = {"load_state": [load], "e2_occupancy_profile": [profile] * expected["n_e2_occupancy_profiles"]}
    assert obx.check_content(tables) == []
    assert expected["episodes"] == [] and "episode" not in tables
    assert load["load_mass_kg"] is None and load["load_mass_kg_null_reason"] == "not_supplied"
