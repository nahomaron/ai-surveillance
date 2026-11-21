"""Appendix T T23.25 (contract E-1.2.23; D-49): the store registry, global demo exclusion and per-person exposure across
stores (FX-14o, FX-14p). Expected values are retyped from the D-49.1 section 6.1 table (fixtures FX-14o, FX-14p)."""
from __future__ import annotations

import json

import pytest

from conftest import Clock, ROOT
from rq1.review.frame import FixtureFrame
from rq1.review.registry import StoreRegistry, exposure_reasons
from rq1.review.store import Store
from rq1.schema.errors import ContractError
from rq1.workflow.demo import draw_demo
from rq1.workflow.store import WorkflowStore
from test_t23_demo import CONFIG, FakeSource, _id

QUAL = "completed T22 handbook training and pilot batch, 2026-11-19"
WHY = "The forklift stops abruptly as the person steps out."


def _exp(fid):
    return json.loads((ROOT / f"fixtures/records/{fid}.json").read_text())["expected"]


def _targets(recordings, tag="t", config=CONFIG, g2=None, stratum="PC"):
    return [{"target_type": "system_episode", "target_id": _id("ep", f"{tag}{k:03d}"), "recording_id": r, "config_id": config,
             "g2_label": g2, "stratum": stratum} for k, r in enumerate(recordings)]


def _v02(reg, path, people=("R-A", "R-B")):
    reg.register(path)
    s = Store(path, clock=Clock(), kdf_iterations=1000, registry=reg)
    s.create_owner("Owner-2", "pw")
    ids = [s.add_annotator(p, "c_layer_reviewer", QUAL, True, f"pw-{p}")["anr_id"] for p in people]
    return s, ids


def _pilot(store, ids, config=CONFIG):
    store.create_batch(FixtureFrame(_targets([_id("rec", f"pil{k}") for k in range(3)], "pil", config), config_id=config), 5, ids, None, pilot=True)


def test_unregistered_store_refuses_to_open(tmp_path):
    reg = StoreRegistry(tmp_path / "registry.json")
    with pytest.raises(ContractError) as err:
        Store(tmp_path / "s", kdf_iterations=1000, registry=reg)
    assert err.value.code == "ERR-SPEC" and "T23.25 (a)" in str(err.value)
    assert not (tmp_path / "s").exists()  # nothing created
    reg.register(tmp_path / "s")
    Store(tmp_path / "s", kdf_iterations=1000, registry=reg)
    assert reg.roots() == [(tmp_path / "s").resolve()]
    reg.register(tmp_path / "s")  # idempotent
    assert reg.roots() == [(tmp_path / "s").resolve()]
    assert (tmp_path / "registry.json").read_bytes().startswith(b'{"')  # JCS


def test_fx14o_batch_in_main_store_excludes_demo_runs_of_other_stores(tmp_path, video):
    exp = _exp("FX-14o")
    reg = StoreRegistry(tmp_path / "registry.json")
    reg.register(tmp_path / "s1")
    s1 = WorkflowStore(tmp_path / "s1", clock=Clock(), kdf_iterations=1000, registry=reg)
    src = FakeSource(video)
    m = draw_demo(s1, src, 2026111903)
    demo_recs = {r for run in m["runs"] for r in run["camera_rec_ids"]}
    s2, ids = _v02(reg, tmp_path / "s2")
    _pilot(s2, ids)
    all_recs = [r for runs in src.runs_by_family().values() for run in runs for r in src.recordings(run)]
    frame = _targets(all_recs)
    b = s2.create_batch(FixtureFrame(frame, config_id=CONFIG), 7, ids, None, pilot=False)
    rec_of = {t["target_id"]: t["recording_id"] for t in frame}
    assert sum(1 for t in b["target_ids"] if rec_of[t] in demo_recs) == exp["targets_of_R_in_S2_batch"]
    assert b["excluded_demo_targets"] == sum(1 for t in frame if t["recording_id"] in demo_recs) > 0


def test_fx14o_demo_draw_refused_after_a_batch_in_another_store(tmp_path, video):
    exp = _exp("FX-14o")
    reg = StoreRegistry(tmp_path / "registry.json")
    src = FakeSource(video)
    all_recs = [r for runs in src.runs_by_family().values() for run in runs for r in src.recordings(run)]
    s2, ids = _v02(reg, tmp_path / "s2")
    _pilot(s2, ids)
    s2.create_batch(FixtureFrame(_targets(all_recs), config_id=CONFIG), 7, ids, None, pilot=False)
    reg.register(tmp_path / "s1")
    s1 = WorkflowStore(tmp_path / "s1", clock=Clock(), kdf_iterations=1000, registry=reg)
    before = sorted(p.name for p in s1.root.iterdir())
    with pytest.raises(ContractError) as err:
        draw_demo(s1, src, 2026111903)
    assert exp["demo_draw_in_S1_after_S2_batch"] == f"refused ({err.value.code})" and "T23.25 (b)" in str(err.value)
    assert sorted(p.name for p in s1.root.iterdir()) == before


def test_fx14p_exposure_across_stores(make_wf, tmp_path, video):
    exp = _exp("FX-14p")
    reg = StoreRegistry(tmp_path / "registry.json")
    app = make_wf("FX-14", registry=reg)  # S1
    [rid] = app.intake()
    rec = app.fixture["inputs"]["episodes"][0]["recording_id"]
    app.ids["AM-2"] = app.store.add_user("AM-2", ["area_manager"], None, [app.area_id], "pw-AM-2")["user_id"]
    assert app.act("AM-1", rid, "am_approve", label="nm", rationale=WHY)[0] == 303  # P approves
    assert app.client("AM-2").text(f"/wf/report/{rid}")[0] == 200  # only a first-display record
    s2, ids = _v02(reg, tmp_path / "s2", people=("AM-1", "AM-2", "R-C"))
    assert exposure_reasons(reg, "AM-1", rec) and exposure_reasons(reg, "AM-2", rec) == ["wf_displays"]
    assert exposure_reasons(reg, "R-C", rec) == [] and exp["unexposed_person"] == "accepted"
    _pilot(s2, ids[:2], config=app.fixture["inputs"]["episodes"][0]["config_id"])
    cfg = app.fixture["inputs"]["episodes"][0]["config_id"]
    b = s2.create_batch(FixtureFrame(_targets([rec], "p", cfg), config_id=cfg), 7, ids[:2], None, pilot=False)
    [target] = b["target_ids"]
    for anr, key in ((ids[0], "approved_then_reference"), (ids[1], "display_only_then_reference")):
        with pytest.raises(ContractError) as err:
            s2.submit(b["batch_id"], target, anr, "nm", 2.0, WHY)
        assert exp[key] == "refused (T22.2 b)" and "T22.2 (b)" in str(err.value)
    assert not s2.exposed(ids[2], rec)


def test_fx14p_owner_of_a_demo_store_is_exposed(tmp_path, video):
    exp = _exp("FX-14p")
    reg = StoreRegistry(tmp_path / "registry.json")
    reg.register(tmp_path / "s3")
    s3 = WorkflowStore(tmp_path / "s3", clock=Clock(), kdf_iterations=1000, registry=reg)
    s3.create_owner("Owner-3", "pw")
    m = draw_demo(s3, FakeSource(video), 2026111903)
    rec = m["runs"][0]["camera_rec_ids"][0]
    s2, ids = _v02(reg, tmp_path / "s2", people=("Owner-3", "R-D"))
    assert exposure_reasons(reg, "Owner-3", rec) == ["owner of a demo store"]
    assert s2.exposed(ids[0], rec) and not s2.exposed(ids[1], rec)
    assert exp["owner_of_s1_then_reference"] == "refused (T22.2 b)"


def test_default_registry_lists_the_two_stores():
    """D-49 step 2 c: out/review/registry.json lists out/review/main and out/review/demo_20261119 (when present here)."""
    path = ROOT / "out/review/registry.json"
    if not path.exists():
        pytest.skip("no registry on this computer")
    roots = StoreRegistry(path).roots()
    assert {(ROOT / "out/review/main").resolve(), (ROOT / "out/review/demo_20261119").resolve()} <= set(roots)
