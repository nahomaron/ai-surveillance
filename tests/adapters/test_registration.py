"""T-18 part C: S0 registration of SDG runs (E-1.2.1 section 3.1; T14.1 lineage; AR-52)."""
from datetime import datetime, timezone

import pytest

from rq1.adapters import registration as reg
from rq1.adapters import smartspaces
from rq1.ids.artifact import Spec
from rq1.registry.registrar import Registrar
from rq1.schema.errors import ContractError
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
