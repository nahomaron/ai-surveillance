"""D-60 STEP 2: S0 lineage of the D-59 scenes (ruling 4; AR-70). Expected values are the ruling's words or hand-written."""
from datetime import datetime, timezone

import pytest

from rq1.adapters import registration as reg
from rq1.adapters import smartspaces
from rq1.ids.artifact import Spec
from rq1.pipeline import d60
from rq1.registry.registrar import Registrar
from rq1.schema.errors import ContractError
from rq1.splits import draw, leakage

T = datetime(2026, 11, 25, 3, 28, 56, tzinfo=timezone.utc)
CAL = smartspaces.calibration({"type": "camera", "id": "c", "intrinsicMatrix": [[1000.0, 0.0, 960.0], [0.0, 1000.0, 540.0], [0.0, 0.0, 1.0]],
                               "extrinsicMatrix": [[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0], [0.0, 0.0, -1.0, 10.0]],
                               "attributes": [{"name": "frameWidth", "value": "1920"}, {"name": "frameHeight", "value": "1080"}]})
MAP_A = "0bb7fd5915654b6fa4a1e984d9ed4d83eec41a7ebab8a045badf16a40348890a"  # Warehouse_002 map.png (candidates.json)
MAP_B = "b" * 64


def scene(name, folder="train", tag="d"):
    cams = {c: (reg.Video(f"raw/smartspaces/MTMC_Tracking_2026/{folder}/{name}/videos/{c}.mp4", f"{name[-3:]}{i:02d}".ljust(64, tag), 7000 + i, "mp4", "h264"), CAL)
            for i, c in enumerate(("Camera_0000", "Camera_0001"))}
    return reg.SmartSpacesScene(name, "synthetic_rendered", None, cams)


def register(s, layout, folder):
    return Registrar().register(reg.smartspaces_metadata(s, T, layout_id=layout, generation_batch=reg.d59_generation_batch(folder)),
                                Spec("S0", "E-1.2.26", "test", "env", (), (), {}))


def test_generation_batch_folder_and_revision():
    assert reg.d59_generation_batch("val") == "MTMC_Tracking_2026/val@d38193b"
    assert reg.d59_generation_batch("train") == "MTMC_Tracking_2026/train@d38193b"
    assert draw.batch_family(reg.d59_generation_batch("val")) == draw.batch_family(reg.d59_generation_batch("train")) == "MTMC_Tracking_2026"
    with pytest.raises(ContractError):
        reg.d59_generation_batch("test")


def test_layout_id_is_the_map_sha256():
    assert reg.map_layout_id(MAP_A) == MAP_A
    for bad in (MAP_A.upper(), MAP_A[:-1], "Warehouse_002"):
        with pytest.raises(ContractError):
            reg.map_layout_id(bad)


def test_d59_lineage_in_s0():
    built = register(scene("Warehouse_020", "val"), MAP_A, "val")
    lin = built.tables["session"][0]["lineage"]
    assert lin["layout_id"] == MAP_A and lin["generation_batch"] == "MTMC_Tracking_2026/val@d38193b"
    assert (lin["ext_run_id"], lin["scene_id"], lin["render_parent"], lin["render_parent_null_reason"]) == ("Warehouse_020", "Warehouse_020", None, "not_applicable")
    assert built.tables["dataset_source"][0]["data_origin"] == "synthetic_rendered" and len(built.tables["calibration"]) == 2


def test_defaults_keep_the_t18_lineage():
    """Without the D-60 arguments the input is the T-18 one (Warehouse_000 / 001 stay reproducible)."""
    s = scene("Warehouse_000")
    assert reg.smartspaces_metadata(s, T) == reg.smartspaces_metadata(s, T, None, None)
    lin = reg.smartspaces_metadata(s, T)["datasets"][0]["sites"][0]["sessions"][0]["lineage"]
    assert lin["layout_id"] == "Warehouse_000" and lin["generation_batch"] == "MTMC_Tracking_2026/train"


def test_layout_alone_creates_no_metadata_edge_t14_1():
    """T14.1: a shared layout is shared_scene_content and creates no leakage edge by itself (the X0b rule). The D-60 layout
    grouping of the addendum is applied by the addendum builder, not by `metadata_edges`."""
    a, b = register(scene("Warehouse_017"), MAP_B, "train"), register(scene("Warehouse_018", tag="e"), MAP_B, "train")
    rows = []
    for built in (a, b):
        d, ses = built.tables["dataset_source"][0], built.tables["session"][0]
        rows += [{"recording_id": r["rec_id"], "session_id": r["session_id"], "dataset_id": d["dsr_id"], "dataset_name": d["name"], "lineage": ses["lineage"]}
                 for r in built.tables["recording"]]
    kinds = {k for _, _, k in leakage.metadata_edges(rows)}
    assert kinds == {"same_session"}
    assert len(leakage.components([r["recording_id"] for r in rows], leakage.metadata_edges(rows))) == 2


def test_d60_tiers():
    assert sorted(d60.TIER1 + d60.TIER2) == sorted(d60.SCENES) and not set(d60.TIER1) & set(d60.TIER2)
    assert [d60.tier(s) for s in ("Warehouse_010", "Warehouse_022", "Warehouse_002", "Warehouse_020")] == [1, 1, 2, 2]
    assert d60.SCENES["Warehouse_020"] == d60.SCENES["Warehouse_022"] == "val"
    with pytest.raises(KeyError):
        d60.tier("Warehouse_000")
