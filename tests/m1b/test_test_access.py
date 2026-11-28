"""D-63 STEP 7 (T-29t): the test-run gate items (hand-made records)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/v2"))
import test_access as ta  # noqa: E402

READY = {"items": [{"item": "X0c complete (R-2)", "result": "pass", "evidence": {"violations": 0}}]}
LOCK = {"lock_artifact": "art_lock"}
REP = {"cameras": 110, "MR-01": {"value": 1.0}}
ARR = {"pass": True, "cameras_verified": 471}


def test_gate_holds_only_when_every_item_holds():
    assert all(ta.gate_items(READY, LOCK, "art_lock", 471, REP, ARR).values())
    assert not ta.gate_items(READY, LOCK, "art_other", 471, REP, ARR)["window_lock_applied"]
    assert not ta.gate_items(READY, LOCK, "art_lock", 470, REP, ARR)["window_lock_applied"]
    assert not ta.gate_items(READY, LOCK, "art_lock", 471, None, ARR)["reporting_run_finished"]
    assert not ta.gate_items(READY, LOCK, "art_lock", 471, {"cameras": 110, "MR-01": {"value": 0.0}}, ARR)["reporting_run_finished"]
    assert not ta.gate_items(READY, LOCK, "art_lock", 471, REP, {"pass": False, "cameras_verified": 471})["test_s2_arrived"]
    bad = {"items": [{"item": "X0c complete (R-2)", "result": "pass", "evidence": {"violations": 1}}]}
    assert not ta.gate_items(bad, LOCK, "art_lock", 471, REP, ARR)["x0c_complete"]


def test_terminal_gate_refuses_before_open(monkeypatch):
    import pytest
    monkeypatch.setattr(Path, "read_text", lambda *a, **k: pytest.fail("opened historical readiness records"))
    with pytest.raises(SystemExit, match="D-66"):
        ta.gate()


def test_loaders_refuse_closed_lineage_before_open(monkeypatch):
    import pytest
    from types import SimpleNamespace
    sys.path.insert(0, str(ROOT / "research/m1a"))
    import m1a_common as m
    from rq1.schema.errors import ContractError

    ctx = SimpleNamespace(ds="sdg", freeze={"split": {"sdg_test_runs": ["closed"], "sdg_validation_runs": ["development", "closed"]}},
                          counts={"cameras": [{"rec_id": "rec_fixture", "run": "closed"}]})
    monkeypatch.setattr(m.files, "read_table", lambda *a, **k: pytest.fail("opened a closed artifact"))
    monkeypatch.setattr(m, "_load", lambda *a, **k: pytest.fail("entered the payload loader"))
    for load in (m.load, m.load_for_reference):
        with pytest.raises(ContractError, match="D-66"):
            load(ctx, "rec_fixture")
    with pytest.raises(ContractError, match="D-66"):
        m.load_for_test_run(None, "rec_fixture", {"items": ta.gate_items(READY, LOCK, "art_lock", 471, REP, ARR)})
