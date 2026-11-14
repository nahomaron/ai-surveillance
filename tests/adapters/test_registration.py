"""T-18 part C: S0 registration of SDG runs (E-1.2.1 section 3.1; T14.1 lineage; AR-52)."""
from datetime import datetime, timezone

import pytest

from rq1.adapters import registration as reg
from rq1.adapters import smartspaces
from rq1.ids.artifact import Spec
from rq1.registry.registrar import Registrar
from rq1.schema.errors import ContractError
from rq1.splits import builder as splits
from rq1.splits import leakage

T = datetime(2026, 11, 13, 1, 52, 54, tzinfo=timezone.utc)
CAL = smartspaces.calibration({"type": "camera", "id": "c", "intrinsicMatrix": [[1000.0, 0.0, 960.0], [0.0, 1000.0, 540.0], [0.0, 0.0, 1.0]],
                               "extrinsicMatrix": [[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, 0.0, -1.0, 10.0]],
                               "attributes": [{"name": "frameWidth", "value": "1920"}, {"name": "frameHeight", "value": "1080"}]})


def run(n=46, seed=1402403531, head="0f6d585a0f0f0a8ed2c8", rgb="04573755960a76f10119", views=("ceiling_00", "eye_01"), cal_views=("ceiling_00",), row=None):
    ext = f"{rgb}_run_{n}_seed_{seed}"
    index = {"run_id": ext, "scenario": "nearmiss", "source_kind": "multi_camera_run", "seed": float(seed),
             "source_run_s3": f"s3://cosmos_generation/warehouse_osmos_2/nearmiss/shard-15/run_{n}_seed_{seed}/", **(row or {})}
    cams = {v: (reg.Video(f"raw/sdg/members/x/{head}_{ext}.{v}.rgb.mp4", f"{n:02d}{i:02d}".ljust(64, "a"), 1000 + i, "mp4", "h264"),
                CAL if v in cal_views else None) for i, v in enumerate(views)}
    return reg.SdgRun(f"{head}_{ext}", index, cams)


def register(runs):
    return Registrar().register(reg.sdg_metadata(runs, T), Spec("S0", "E-1.2.13", "test", "env", (), (), {}))


def test_rgb_run_id_suffix_rule():
    assert reg.rgb_run_id("0f6d585a0f0f0a8ed2c8_04573755960a76f10119_run_46_seed_1402403531") == "04573755960a76f10119_run_46_seed_1402403531"
    with pytest.raises(ContractError):
        reg.rgb_run_id("run_46_seed_1")


def test_session_lineage_t14_1():
    s = reg.sdg_session(run())
    assert s["session_label"] == "04573755960a76f10119_run_46_seed_1402403531" and s["scripted"] is True and s["scenario_ref"] == "nearmiss"
    lin = s["lineage"]
    assert lin["ext_run_id"] == lin["scene_id"] == s["session_label"]  # T14.1: the run is the scene instance
    assert lin["seed"] == 1402403531 and isinstance(lin["seed"], int)
    assert lin["generation_batch"] == "warehouse_osmos_2/nearmiss/shard-15"
    assert lin["layout_id"] == reg.SDG_LAYOUT
    assert lin["render_parent"] is None and lin["render_parent_null_reason"] == "not_applicable"


@pytest.mark.parametrize("change", [{"run_id": "other"}, {"source_kind": "extras_single_view"}, {"seed": 5.0}, {"seed": None},
                                    {"source_run_s3": "s3://b/x/run_9_seed_9/"}, {"source_run_s3": "https://x/run_46_seed_1402403531/"}])
def test_index_row_must_agree_with_the_run(change):
    with pytest.raises(ContractError):
        reg.sdg_session(run(row=change))


def test_viewpoints():
    assert (reg.viewpoint("ceiling_03"), reg.viewpoint("eye_00")) == ("ceiling", "eye_level")
    with pytest.raises(ContractError):
        reg.viewpoint("drone_00")


@pytest.mark.determinism
def test_s0_tables():
    built = register([run(), run(n=13, seed=851910160, head="aaaaaaaaaaaaaaaaaaaa", rgb="72a9270c9daa123ace61")])
    t = built.tables
    assert len(t["dataset_source"]) == 1 and t["dataset_source"][0]["data_origin"] == "synthetic_rendered"
    assert t["dataset_source"][0]["version"] == reg.SDG_VERSION and t["dataset_source"][0]["unit_status"] == "verified"
    assert [s["site_label"] for s in t["site"]] == [reg.SDG_LAYOUT] and t["site"][0]["site_kind"] == "synthetic_scene"
    assert len(t["session"]) == 2 and len(t["camera"]) == 4 and len(t["recording"]) == 4
    labels = sorted(c["camera_label"] for c in t["camera"])
    assert labels[0] == "04573755960a76f10119_run_46_seed_1402403531.ceiling_00"  # a camera is one view of one run
    assert {c["viewpoint_class"] for c in t["camera"]} == {"ceiling", "eye_level"}
    assert len(t["calibration"]) == 2 and {c["calibration_tier"] for c in t["calibration"]} == {"full_camera"}  # eye_01 has none
    assert all(f["retention_policy_id"] == reg.retention_policy_id() and f["privacy_state"] == "synthetic_no_persons" for f in t["source_file"])
    assert all(tl["kind"] == "recording_local" for tl in t["timeline"])  # AR-52 item 5
    assert all(s["lineage"]["render_parent"] is None and s["lineage"]["render_parent_null_reason"] == "not_applicable" for s in t["session"])  # stored, not only built
    assert register([run(), run(n=13, seed=851910160, head="aaaaaaaaaaaaaaaaaaaa", rgb="72a9270c9daa123ace61")]).artifact_id == built.artifact_id


def test_leakage_one_group_per_run_layout_shares_nothing():
    built = register([run(), run(n=13, seed=851910160, head="aaaaaaaaaaaaaaaaaaaa", rgb="72a9270c9daa123ace61")])
    sessions = {s["ses_id"]: s for s in built.tables["session"]}
    recs = [{"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": built.tables["dataset_source"][0]["dsr_id"],
             "lineage": sessions[r["session_id"]]["lineage"]} for r in built.tables["recording"]]
    groups = leakage.components([r["recording_id"] for r in recs], leakage.metadata_edges(recs))
    assert len(groups) == 2 and all(kinds == ["same_session"] for _, kinds in groups)  # the shared layout family adds no edge


def test_identical_bytes_refused():
    a = run()
    b = run(n=13, seed=851910160, head="aaaaaaaaaaaaaaaaaaaa", rgb="72a9270c9daa123ace61")
    b = reg.SdgRun(b.artifact_run, b.index_row, {"ceiling_00": a.cameras["ceiling_00"]})
    with pytest.raises(ContractError):
        reg.sdg_metadata([a, b], T)


def scene(name="Warehouse_000", origin="synthetic_rendered", parent=None, tag="b"):
    cams = {c: (reg.Video(f"raw/smartspaces/MTMC_Tracking_2026/train/{name}/videos/{c}.mp4", f"{i:02d}".ljust(64, tag), 5000 + i, "mp4", "h264"), CAL)
            for i, c in enumerate(("Camera_0000", "Camera_0001"))}
    return reg.SmartSpacesScene(name, origin, parent, cams)


def register_scene(s):
    return Registrar().register(reg.smartspaces_metadata(s, T), Spec("S0", "E-1.2.15", "test", "env", (), (), {}))


@pytest.mark.determinism
def test_smartspaces_version_label_per_origin_cr_020():
    assert reg.smartspaces_version("synthetic_transferred") == "MTMC_Tracking_2026@d38193be60906679124732a4be9a6516821e2bed/synthetic_transferred"
    a, b = register_scene(scene()), register_scene(scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="c"))
    da, db = a.tables["dataset_source"][0], b.tables["dataset_source"][0]
    assert (da["data_origin"], db["data_origin"]) == ("synthetic_rendered", "synthetic_transferred")
    assert da["version"].endswith("/synthetic_rendered") and db["version"].endswith("/synthetic_transferred") and da["dsr_id"] != db["dsr_id"]
    assert a.tables["site"][0]["data_origin"] == "synthetic_rendered" and b.tables["site"][0]["data_origin"] == "synthetic_transferred"  # one origin per file
    assert a.tables["license_component"] == b.tables["license_component"]  # one licence row for the release
    assert len(a.tables["recording"]) == 2 and len(a.tables["calibration"]) == 2


def test_smartspaces_lineage_render_parent():
    la = register_scene(scene()).tables["session"][0]["lineage"]
    lb = register_scene(scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="c")).tables["session"][0]["lineage"]
    assert (la["ext_run_id"], la["scene_id"], la["render_parent"], la["render_parent_null_reason"]) == ("Warehouse_000", "Warehouse_000", None, "not_applicable")
    assert (lb["ext_run_id"], lb["scene_id"], lb["render_parent"]) == ("Warehouse_001", "Warehouse_000", "Warehouse_000")  # T14.1: asset + re-renders
    assert la["seed"] is None and la["seed_null_reason"] == "not_supplied"


def test_smartspaces_refusals():
    with pytest.raises(ContractError):
        reg.smartspaces_metadata(scene("Warehouse_026", "real_staged"), T)
    with pytest.raises(ContractError):
        reg.smartspaces_metadata(scene("Warehouse_001", "synthetic_transferred", None), T)
    with pytest.raises(ContractError):
        reg.smartspaces_metadata(scene("Warehouse_000", "synthetic_rendered", "Warehouse_000"), T)


def _split_rows(*built_partition):
    """Recordings as `SplitBuilder.freeze` takes them, with the dataset name (T16.2)."""
    rows = []
    for built, partition in built_partition:
        d, s = built.tables["dataset_source"][0], built.tables["session"][0]
        rows += [{"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": d["dsr_id"], "dataset_name": d["name"],
                  "lineage": s["lineage"], "partition": partition} for r in built.tables["recording"]]
    return rows


def test_t16_scene_and_its_re_render_are_one_leakage_group():
    """T16 test: Warehouse_000 and Warehouse_001 register in different rows and fall in ONE leakage group; declaring them in
    different partitions raises ERR-LEAKAGE."""
    a, b = register_scene(scene()), register_scene(scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="c"))
    assert a.tables["dataset_source"][0]["dsr_id"] != b.tables["dataset_source"][0]["dsr_id"]  # different rows (T16.1)
    assert a.tables["dataset_source"][0]["name"] == b.tables["dataset_source"][0]["name"]
    assert a.tables["dataset_source"][0]["license_component_id"] == b.tables["dataset_source"][0]["license_component_id"]  # shared licence component
    rows = _split_rows((a, "test"), (b, "test"))
    groups = leakage.components([r["recording_id"] for r in rows], leakage.metadata_edges(rows))
    assert len(groups) == 1 and len(groups[0][0]) == 4 and "same_scene_or_run" in groups[0][1]
    frozen = splits.freeze(rows, "t16", "1", "T1", T)
    assert len(frozen["leakage_groups"]) == 1
    with pytest.raises(ContractError) as e:
        splits.freeze(_split_rows((a, "train"), (b, "test")), "t16", "1", "T1", T)
    assert e.value.code == "ERR-LEAKAGE"


def test_t16_2_edges_do_not_cross_dataset_names():
    a, b = register_scene(scene()), register_scene(scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="c"))
    rows = _split_rows((a, "train"), (b, "test"))
    for r in rows[2:]:
        r["dataset_name"] = "another/dataset"  # the same scene label in an unrelated dataset is not the same scene (AR-31)
    assert len(splits.freeze(rows, "t16", "1", "T1", T)["leakage_groups"]) == 2
    for r in rows:
        del r["dataset_name"]  # without names, rows are compared by dataset row, as before T16
    assert len(splits.freeze(rows, "t16", "1", "T1", T)["leakage_groups"]) == 2


def test_t16_1_file_listed_under_two_rows_is_refused():
    registrar = Registrar()
    spec = Spec("S0", "E-1.2.15", "test", "env", (), (), {})
    registrar.register(reg.smartspaces_metadata(scene(), T), spec)
    same_files = scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="b")  # tag b: the bytes of Warehouse_000's videos
    with pytest.raises(ContractError) as e:
        registrar.register(reg.smartspaces_metadata(same_files, T), spec)
    assert e.value.code == "ERR-INVARIANT"
    registrar.register(reg.smartspaces_metadata(scene("Warehouse_001", "synthetic_transferred", "Warehouse_000", tag="c"), T), spec)  # other bytes: accepted
    registrar.register(reg.smartspaces_metadata(scene(), T), spec)  # the same file under its own row again: accepted


def real_scene(name="Warehouse_026", tag="d"):
    return {c: reg.Video(f"raw/real/smartspaces/test/{name}/videos/{c}.mp4", f"{i:02d}".ljust(64, tag), 7000 + i, "mp4", "h264")
            for i, c in enumerate(("Camera_0000", "Camera_0001"))}


def test_real_scenes_register_under_the_real_row_with_d24_d26_conditions():
    from rq1.schema import vr_rules

    registrar, spec = Registrar(), Spec("S0", "E-1.2.15", "test", "env", (), (), {})
    built = registrar.register(reg.smartspaces_real_metadata("Warehouse_026", real_scene(), T), spec)
    t = built.tables
    d, site = t["dataset_source"][0], t["site"][0]
    assert d["version"].endswith("/real_staged") and d["data_origin"] == "real_staged" and d["annotation_levels"] == ["none"]  # D-24 b: no annotation
    assert (site["data_origin"], site["site_kind"], site["approvals_ref"]) == ("real_staged", "staged_facility", "PENDING-ADVISOR (exploratory, D-26)")
    assert all(f["privacy_state"] == "contains_identifiable_persons" and f["retention_policy_id"] == reg.retention_policy_id(reg.RETENTION_REAL) for f in t["source_file"])
    assert reg.retention_policy_id(reg.RETENTION_REAL) != reg.retention_policy_id()  # not the synthetic policy
    assert "calibration" not in t and "world_frame" not in t  # AR-54: uncalibrated, reference-free checks only
    real_ids = {f["src_id"] for f in t["source_file"]}
    assert vr_rules.check_retention(t["source_file"], real_ids, {reg.retention_policy_id(reg.RETENTION_REAL)}, []) == []  # VR-E-070
    assert vr_rules.check_retention(t["source_file"], real_ids, {reg.retention_policy_id()}, []) != []
    # T16: the real row is a third row of the same release; no leakage edge to the synthetic scenes (different scenes)
    syn = registrar.register(reg.smartspaces_metadata(scene(), T), spec)
    assert syn.tables["dataset_source"][0]["dsr_id"] != d["dsr_id"] and syn.tables["dataset_source"][0]["name"] == d["name"]
    rows = _split_rows((built, "test"), (syn, "test"))
    assert len(splits.freeze(rows, "t16", "1", "T1", T)["leakage_groups"]) == 2
