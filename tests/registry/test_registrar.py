"""T-05: S0 registration. FX-A3/A4, FX-B1-B3 from Appendix T T4; CT-I-05/06; CT-NK-04/05."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rq1.ids import core
from rq1.ids.artifact import Spec
from rq1.registry.registrar import Registrar, check_calibration, check_load_state, check_not_recorded
from rq1.schema.errors import ContractError

ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "records"
SPEC = Spec("S0", "E-1.2.3", "fixture", "fixture", (), (), {})
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
SHA_A, SHA_B = "ab" * 32, "cd" * 32
RET = "rtp_018f3a2e-7b1c-7def-8a12-3456789abcde"


def record(name):
    return json.loads((ROOT / f"{name}.json").read_text())["record"]


def registration(alignment=None, extent=None, origin="synthetic_rendered"):
    def rec(label, sha, cam):
        return {"dataset": ["ds", "1"], "site": "s1", "session": "run1", "camera": cam, "sha256": sha, "registration_label": label, "alignment": alignment}
    return {
        "licenses": [{"component": "ds", "version": "1", "component_type": "dataset", "license_label": "test", "terms_location": "unknown", "obligations": [], "license_status": "not_read"}],
        "datasets": [{"name": "ds", "version": "1", "data_origin": origin, "dataset_kind": "fixture", "source_url": "local", "retrieved_utc": T0, "license": ["ds", "1"],
                      "annotation_levels": ["none"], "unit_status": "verified",
                      "sites": [{"site_label": "s1", "data_origin": origin, "site_kind": "synthetic_scene", "independent_of_development": False,
                                 "cameras": [{"camera_label": "c1", "viewpoint_class": "ceiling", "declared_overlap_camera_ids": []},
                                             {"camera_label": "c2", "viewpoint_class": "eye_level", "declared_overlap_camera_ids": []}],
                                 "sessions": [{"session_label": "run1", "scripted": True, "extent": extent, "lineage": {"seed": 7}}]}]}],
        "source_files": [{"sha256": SHA_A, "size_bytes": 10, "container": "mkv", "codec": "mpeg4", "uri": "a", "privacy_state": "synthetic_no_persons", "retention_policy_id": RET},
                         {"sha256": SHA_B, "size_bytes": 10, "container": "mkv", "codec": "mpeg4", "uri": "b", "privacy_state": "synthetic_no_persons", "retention_policy_id": RET}],
        "recordings": [rec("r1", SHA_A, "c1"), rec("r2", SHA_B, "c2")],
    }


ALIGN = {"method": "dataset_supplied_sync", "version": "1", "offset_s": 0.0, "drift_ppm": 0.0, "sigma_s": 0.001, "evidence_ref": "doc", "prov_class": "dataset_supplied"}


@pytest.mark.determinism
def test_recordings_use_anchor_parent_ids():
    built = Registrar().register(registration(), SPEC)
    site = built.tables["site"][0]
    dataset = built.tables["dataset_source"][0]
    assert site["dataset_id"] == dataset["dsr_id"] and site["sit_id"] == core.anchor_id("sit", "site", [dataset["dsr_id"], "s1"])
    cameras = {c["camera_label"]: c["cam_id"] for c in built.tables["camera"]}
    recording = next(r for r in built.tables["recording"] if r["registration_label"] == "r1")
    assert recording["src_id"] == core.source_id(SHA_A) and recording["camera_id"] == cameras["c1"]


@pytest.mark.determinism
def test_unaligned_recordings_get_local_timelines_fx_a3_ct_t_11():
    built = Registrar().register(registration(), SPEC)
    timelines = built.tables["timeline"]
    assert len(timelines) == 2 and {t["kind"] for t in timelines} == {"recording_local"}
    assert all(t["extent_start_tl_s"] is None and t["extent_start_tl_s_null_reason"] == "not_applicable" and t["extent_source"] == "recording_extent" for t in timelines)
    assert "clock_alignment" not in built.tables or built.tables["clock_alignment"] == []
    fixture = record("FX-A3")
    assert fixture["timeline_kind"] == "recording_local" and fixture["clock_alignment_id"] is None


@pytest.mark.determinism
def test_aligned_recordings_share_one_session_timeline():
    built = Registrar().register(registration(ALIGN, [0.0, 120.0]), SPEC)
    timelines = built.tables["timeline"]
    assert len(timelines) == 1 and timelines[0]["kind"] == "aligned_session" and timelines[0]["extent_source"] == "session_metadata"
    assert timelines[0]["extent_end_tl_s"] == 120.0
    assert len(built.tables["clock_alignment"]) == 2
    assert {r["timeline_id"] for r in built.tables["recording"]} == {timelines[0]["tl_id"]}


@pytest.mark.determinism
def test_alignment_without_declared_extent_is_rejected():
    with pytest.raises(ContractError) as exc:
        Registrar().register(registration(ALIGN, None), SPEC)
    assert exc.value.code == "ERR-INVARIANT"


@pytest.mark.determinism
def test_assumed_zero_clock_method_does_not_exist():
    with pytest.raises(ContractError) as exc:
        Registrar().register(registration({**ALIGN, "method": "assumed_zero"}, [0.0, 10.0]), SPEC)
    assert exc.value.code == "ERR-UNKNOWN-ENUM"


@pytest.mark.determinism
def test_ar22_one_whole_session_camera_group_per_timeline():
    local = Registrar().register(registration(), SPEC).tables["camera_group"]
    assert len(local) == 2 and all(len(g["camera_ids"]) == 1 and g["grouping_basis"] == "whole_session" for g in local)
    aligned = Registrar().register(registration(ALIGN, [0.0, 120.0]), SPEC).tables["camera_group"]
    assert len(aligned) == 1 and len(aligned[0]["camera_ids"]) == 2


@pytest.mark.determinism
def test_fx_a4_not_recorded_on_local_timeline_is_rejected():
    fixture = record("FX-A4")
    timeline = {"kind": fixture["timeline_kind"], "extent_start_tl_s": None, "extent_end_tl_s": None}
    segment = {"coverage_state": fixture["coverage_state"], "t_start_tl_s": fixture["t_start_s"], "t_end_tl_s": fixture["t_end_s"]}
    assert [i.rule for i in check_not_recorded(segment, timeline)] == ["TI-11"]


@pytest.mark.determinism
def test_ti_11_not_recorded_allowed_only_inside_declared_extent():
    aligned = {"kind": "aligned_session", "extent_start_tl_s": 0.0, "extent_end_tl_s": 100.0}
    assert check_not_recorded({"coverage_state": "not_recorded", "t_start_tl_s": 10.0, "t_end_tl_s": 20.0}, aligned) == []
    assert check_not_recorded({"coverage_state": "not_recorded", "t_start_tl_s": 90.0, "t_end_tl_s": 110.0}, aligned)


def _calibration(name):
    data = {k: v for k, v in record(name).items() if k not in ("fixture", "calibration_id", "camera_id", "world_frame_id")}
    data.setdefault("valid_from_us", 0)
    data.setdefault("version", "1")
    return data


@pytest.mark.determinism
@pytest.mark.parametrize("name", ["FX-B1", "FX-B3"])
def test_fx_b_valid_calibrations(name):
    assert check_calibration(_calibration(name)) == []


@pytest.mark.determinism
def test_calibration_is_registered_with_tier_fields():
    data = registration()
    data["datasets"][0]["sites"][0]["world_frames"] = [{"label": "w", "version": "1", "origin_description": "o", "unit_status": "verified", "prov_class": "simulator_truth"}]
    data["calibrations"] = [{"dataset": ["ds", "1"], "site": "s1", "camera": "c1", "world_frame": ["w", "1"], **_calibration("FX-B1")}]
    row = Registrar().register(data, SPEC).tables["calibration"][0]
    assert row["calibration_tier"] == "ground_plane_homography" and row["intrinsics_K"] is None and row["intrinsics_K_null_reason"] == "not_applicable"


@pytest.mark.determinism
@pytest.mark.parametrize("change", [
    {"intrinsics_K": [1.0] * 9, "intrinsics_K_null_reason": None},  # tier-excluded field present
    {"homography_img_to_floor": None, "homography_img_to_floor_null_reason": "not_supplied"},  # tier-required field absent
    {"intrinsics_K_null_reason": "not_supplied"},  # excluded field null for the wrong reason
])
def test_cb_01_ground_plane_tier_fields(change):
    issues = check_calibration({**_calibration("FX-B1"), **change})
    assert issues and issues[0].rule == "CB-01" and issues[0].code == "ERR-CALIB-TIER"


@pytest.mark.determinism
def test_cb_01_full_camera_requires_intrinsics():
    issues = check_calibration({**_calibration("FX-B3"), "intrinsics_K": None, "intrinsics_K_null_reason": "not_supplied"})
    assert issues and issues[0].rule == "CB-01"


@pytest.mark.determinism
def test_cb_02_singular_homography_rejected():
    issues = check_calibration({**_calibration("FX-B1"), "homography_img_to_floor": [1.0, 2.0, 3.0, 2.0, 4.0, 6.0, 0.0, 0.0, 1.0]})
    assert [i.rule for i in issues] == ["CB-02"]


@pytest.mark.determinism
def test_fx_b2_height_from_homography_rejected():
    fixture = record("FX-B2")
    calibration = {"calibration_tier": "ground_plane_homography", "height_reference_ids": []}
    issues = check_load_state({"method": fixture["method"], "height_m": fixture["height_m"]}, calibration)
    assert [i.rule for i in issues] == ["CB-03"] and issues[0].code == "ERR-CALIB-TIER"


@pytest.mark.parametrize("state,calibration,multi_view,ok", [
    ({"method": "simulator_truth", "height_m": 2.0}, None, False, True),
    ({"method": "height_reference_plane", "height_m": 2.0}, {"calibration_tier": "full_camera", "height_reference_ids": ["h"]}, False, True),
    ({"method": "height_reference_plane", "height_m": 2.0}, {"calibration_tier": "full_camera", "height_reference_ids": []}, True, True),
    ({"method": "height_reference_plane", "height_m": 2.0}, {"calibration_tier": "full_camera", "height_reference_ids": []}, False, False),
    ({"method": "image_heuristic", "height_m": None}, None, False, True),
])
def test_cb_03_conditions(state, calibration, multi_view, ok):
    assert (check_load_state(state, calibration, multi_view=multi_view) == []) is ok


@pytest.mark.determinism
def test_failed_calibration_cannot_be_registered_as_valid_tier_mismatch():
    assert check_calibration({**_calibration("FX-B3"), "homography_assumes_undistorted": True})[0].rule == "CB-01"


@pytest.mark.determinism
def test_ct_i_05_same_file_two_cameras():
    data = registration()
    data["recordings"][1]["sha256"] = SHA_A
    data["source_files"] = data["source_files"][:1]
    built = Registrar().register(data, SPEC)
    assert len(built.tables["source_file"]) == 1 and len({r["rec_id"] for r in built.tables["recording"]}) == 2


@pytest.mark.determinism
def test_ct_i_06_duplicate_registration_rejected():
    data = registration()
    data["recordings"].append(copy.deepcopy(data["recordings"][0]))
    with pytest.raises(ContractError) as exc:
        Registrar().register(data, SPEC)
    assert exc.value.code == "ERR-NATURAL-KEY"


@pytest.mark.determinism
def test_ct_nk_04_anchors_stable_across_s0_artifacts():
    registrar = Registrar()
    first = registrar.register(registration(), SPEC)
    data = registration()
    extra = copy.deepcopy(data["datasets"][0])
    extra["name"] = "other"
    extra["sites"] = []
    data["datasets"].append(extra)
    second = registrar.register(data, SPEC)
    for table, prefix in (("dataset_source", "dsr"), ("site", "sit"), ("recording", "rec"), ("timeline", "tl")):
        assert {r[f"{prefix}_id"] for r in first.tables[table]} <= {r[f"{prefix}_id"] for r in second.tables[table]}, table
    assert first.artifact_id != second.artifact_id


@pytest.mark.determinism
def test_ct_nk_05_anchor_conflict_on_changed_payload():
    registrar = Registrar()
    registrar.register(registration(), SPEC)
    data = registration()
    data["datasets"][0]["source_url"] = "elsewhere"
    with pytest.raises(ContractError) as exc:
        registrar.register(data, SPEC)
    assert exc.value.code == "ERR-ANCHOR-CONFLICT"


@pytest.mark.determinism
def test_real_origin_site_needs_approvals():
    with pytest.raises(ContractError) as exc:
        Registrar().register(registration(origin="real_staged"), SPEC)
    assert exc.value.code == "ERR-INVARIANT"


@pytest.mark.determinism
def test_registration_is_deterministic():
    assert Registrar().register(registration(), SPEC).artifact_id == Registrar().register(registration(), SPEC).artifact_id


@pytest.mark.determinism
def test_artifact_ids_recompute_vr_e_004():
    from rq1.schema import vr_rules
    built = Registrar().register(registration(ALIGN, [0.0, 120.0]), SPEC)
    for table, rows in built.tables.items():
        assert vr_rules.check_ids(table, rows, built.artifact_id) == [], table
