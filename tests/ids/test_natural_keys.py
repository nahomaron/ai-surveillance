"""CT-NK-01-08 (F.1 A1.4)."""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rq1.fixtures import identity_rows as rows
from rq1.ids import anchors, artifact, core
from rq1.ids.artifact import Spec
from rq1.schema import registry
from rq1.schema.errors import ContractError

WIN = "rwn_" + "a" * 26
C1, C2 = "rcf_" + "a" * 26, "rcf_" + "b" * 26
EVC, SPM = "evc_" + "a" * 26, "spm_" + "a" * 26
S8 = Spec("S8", "E-1.2.3", "fixture", "fixture", (EVC, SPM), (), {})


def _build(table, table_rows):
    built = artifact.build_artifact(S8, {table: table_rows})
    return [r[registry.TABLES[table].prefix + "_id"] for r in built.tables[table]]


@pytest.mark.determinism
def test_ct_nk_01_completeness_both_support_bases():
    a = rows.row("completeness_record", window_id=WIN, metric_id="CM-01", support_basis="detected")
    b = rows.row("completeness_record", window_id=WIN, metric_id="CM-01", support_basis="detected_plus_inferred")
    assert len(set(_build("completeness_record", [a, b]))) == 2


@pytest.mark.determinism
def test_ct_nk_02_match_records_across_config_scenario_label_group():
    records = []
    for config in (C1, C2):
        for scenario in ("S_VIEW", "S_LINK"):
            for group in ("G1", "G2"):
                records.append(rows.row("match_record", window_id=WIN, config_id=config, scenario=scenario, label_group=group,
                                        ref_event_id="ref_" + "a" * 26, system_event_id="evt_" + "a" * 26))
    assert len(set(_build("match_record", records))) == 8


@pytest.mark.determinism
def test_ct_nk_03_weighted_and_estimand_results_distinct():
    records = [rows.row("metric_result", metric_id="EV-M1", definition_version="1", weighted=w, estimand=e)
               for w in (True, False) for e in ("frame_description", "new_session_performance")]
    assert len(set(_build("metric_result", records))) == 4


def _dataset(name):
    return rows.row("dataset_source", name=name, version="1")


@pytest.mark.determinism
def test_ct_nk_04_anchor_ids_stable_when_another_dataset_is_registered():
    spec = Spec("S0", "E-1.2.3", "f", "f", (), (), {})
    one = artifact.build_artifact(spec, {"dataset_source": [_dataset("A")]})
    two = artifact.build_artifact(spec, {"dataset_source": [_dataset("A"), _dataset("B")]})
    ids_one = {r["name"]: r["dsr_id"] for r in one.tables["dataset_source"]}
    ids_two = {r["name"]: r["dsr_id"] for r in two.tables["dataset_source"]}
    assert ids_one["A"] == ids_two["A"]
    assert one.artifact_id != two.artifact_id


@pytest.mark.determinism
def test_ct_nk_05_anchor_conflict():
    spec = Spec("S0", "E-1.2.3", "f", "f", (), (), {})
    first = artifact.build_artifact(spec, {"dataset_source": [_dataset("A")]})
    changed = _dataset("A")
    changed["source_url"] = "other"
    second = artifact.build_artifact(spec, {"dataset_source": [changed]})
    register = anchors.AnchorRegistry()
    register.add(first)
    register.add(first)  # identical payload is the same entity
    with pytest.raises(ContractError) as exc:
        register.add(second)
    assert exc.value.code == "ERR-ANCHOR-CONFLICT"


@pytest.mark.determinism
@pytest.mark.parametrize("stage,configs,inputs", [
    ("S5", (C1, C2), ()), ("S5", (), ()), ("S4", ("gcf_" + "a" * 26,), ()), ("S3", (), ()), ("S2", ("mdl_" + "a" * 26,), ()), ("S8", (EVC,), ()),
])
def test_ct_nk_06_art_iso(stage, configs, inputs):
    with pytest.raises(ContractError) as exc:
        artifact.spec_id(Spec(stage, "E-1.2.3", "f", "f", configs, inputs, {}))
    assert exc.value.code == "ERR-SPEC"


@pytest.mark.determinism
def test_art_iso_allows_several_band_schemes():
    configs = ("gcf_" + "a" * 26, "sbc_" + "a" * 26, "bsc_" + "a" * 26, "bsc_" + "b" * 26)
    assert artifact.spec_id(Spec("S4", "E-1.2.3", "f", "f", configs, (), {})).startswith("asp_")


@pytest.mark.determinism
@settings(max_examples=60, deadline=None)
@given(st.lists(st.tuples(st.integers(0, 3), st.integers(0, 3), st.floats(0, 1)), min_size=1, max_size=12))
def test_ct_nk_07_uniqueness_holds_iff_key_fields_differ(items):
    records = [rows.row("detection", recording_id=rows.REC, frame_index=f, det_index=d, score=s) for f, d, s in items]
    spec = Spec("S2", "E-1.2.3", "f", "f", ("mdl_" + "a" * 26, "inf_" + "a" * 26), (), {})
    keys = [(f, d) for f, d, _ in items]
    if len(set(keys)) == len(keys):
        first = artifact.build_artifact(spec, {"detection": records})
        again = artifact.build_artifact(spec, {"detection": list(reversed(records))})
        ids = [r["det_id"] for r in first.tables["detection"]]
        assert len(set(ids)) == len(ids) and sorted(ids) == sorted(r["det_id"] for r in again.tables["detection"])
    else:
        with pytest.raises(ContractError) as exc:
            artifact.build_artifact(spec, {"detection": records})
        assert exc.value.code == "ERR-NATURAL-KEY"


@pytest.mark.determinism
def test_ct_nk_08_references_resolve_across_identity_classes():
    recording = core.anchor_id("rec", "recording", ["x"])
    band = core.make_id("bsc", {"edges_m": [0.0]})
    profile_key = [rows.PERSON, rows.FORKLIFT, 0]
    p = rows.pow_row(0)
    p.update(recording_id=recording, timeline_id=recording, camera_id=recording)
    profile = rows.row("exposure_profile", subject_type="pow", subject_nk=profile_key, band_scheme_id=band)
    spec = Spec("S4", "E-1.2.3", "f", "f", ("gcf_" + "a" * 26, "sbc_" + "a" * 26, band), (), {})
    built = artifact.build_artifact(spec, {"pow": [p], "exposure_profile": [profile]})
    known = {recording, band, rows.PERSON, rows.FORKLIFT}
    assert artifact.unresolved_references(built, known) == []
    assert artifact.unresolved_references(built, known - {band}) == [band]
    assert built.tables["exposure_profile"][0]["subject_id"] == built.tables["pow"][0]["pow_id"]
