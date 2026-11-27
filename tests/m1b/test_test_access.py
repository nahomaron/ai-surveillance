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


def test_loader_refuses_without_gate():
    import pytest
    sys.path.insert(0, str(ROOT / "research/m1a"))
    import m1a_common as m
    from rq1.schema.errors import ContractError
    with pytest.raises(ContractError, match="gate does not hold"):
        m.load_for_test_run(None, "rec_x", {"items": {"x0c_complete": True}})
