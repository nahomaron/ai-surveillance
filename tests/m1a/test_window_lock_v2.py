"""D-63 STEP 3: the v2 window lock (AR-71 item 11, accepted under D-63 ruling 1; AR-72 for its representation).
Hand-made inputs; expected values by hand beside each assertion."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/preregistration"))
import lock_v2 as lk  # noqa: E402
import readiness_v2 as rd  # noqa: E402

T_LOCK = datetime(2026, 11, 26, 15, 47, 13, tzinfo=timezone.utc)


def _id(prefix):
    from rq1.ids import core
    return core.make_id(prefix, ["fixture", prefix])


SPM, CGP, TL, ART_V0 = _id("spm"), _id("cgp"), _id("tl"), _id("art")


def _window(index=0, t0=0.0, t1=10.0, guard=10.0):
    return {"plan_nk": ["m1a-sdg-test", "1"], "camera_group_id": CGP, "timeline_id": TL, "window_index": index, "t_start_tl_s": t0,
            "t_end_tl_s": t1, "window_length_s": t1 - t0, "t_guard_end_tl_s": guard, "stratum_id": "sdg:ceiling", "sample_type": "RES",
            "inclusion_prob": 1.0, "inclusion_prob_null_reason": None, "weight": 1.0, "weight_null_reason": None, "exhaustive": True,
            "annotation_status": "planned", "locked_utc": None, "locked_utc_null_reason": "pending_review", "lock_sha256": None,
            "lock_sha256_null_reason": "pending_review", "split_version_id": SPM, "partition_at_sampling": "test", "leakage_group_id": "lkg_x"}


def _ref_row(refs):
    return {"s5": "art_ref", "s5_payload_sha256": "ab" * 32, "references": refs}


def test_lock_hash_is_the_ar71_item11_definition_by_hand():
    # The JCS body written out by hand: natural key, bounds, set label, reference S5 (ID, payload hash), overlapping entries.
    w = _window()
    inside = {"t_start_tl_s": 2.0, "t_end_tl_s": 3.0, "ref": "r1"}
    outside = {"t_start_tl_s": 10.0, "t_end_tl_s": 11.0, "ref": "r2"}  # starts at t_guard_end: [t_start, t_guard_end) excludes it
    body = {"plan_nk": ["m1a-sdg-test", "1"], "camera_group_id": CGP, "window_index": 0, "t_start_tl_s": 0.0, "t_end_tl_s": 10.0,
            "t_guard_end_tl_s": 10.0, "reference_set": rd.vr.LABEL, "rec_id": "rec_a", "reference_s5": "art_ref",
            "reference_s5_payload_sha256": "ab" * 32, "references": [inside]}
    expected = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert lk.lock_hash(w, "rec_a", _ref_row([inside, outside])) == expected


def test_lock_changes_only_the_three_lock_fields():
    w = _window()
    out = lk.locked_window(w, "f" * 64, T_LOCK)
    assert out["annotation_status"] == "locked" and out["lock_sha256"] == "f" * 64 and out["locked_utc"] == T_LOCK
    assert out["locked_utc_null_reason"] is None and out["lock_sha256_null_reason"] is None
    changed = {k for k in w if w[k] != out[k]}
    assert changed == {"annotation_status", "locked_utc", "locked_utc_null_reason", "lock_sha256", "lock_sha256_null_reason"}
    assert w["annotation_status"] == "planned"  # the input row (V0) is not modified


def test_lock_refuses_a_window_that_is_not_planned():
    from rq1.schema.errors import ContractError
    w = {**_window(), "annotation_status": "locked"}
    with pytest.raises(ContractError):
        lk.locked_window(w, "f" * 64, T_LOCK)


def test_lock_artifact_builds_identically_and_differs_from_v0_only_in_lock_fields():
    from rq1.ids.artifact import Spec, build_artifact
    plan = lk.strip_derived("sampling_plan", {"spl_id": "spl_x", "plan_label": "m1a-sdg-test", "version": "1", "sample_type": "RES",
                                              "split_version_id": SPM, "population_definition_ref": "p", "supersedes_plan_id": None,
                                              "supersedes_plan_id_null_reason": "not_applicable", "frame_definition": {"camera_group_ids": [CGP], "w_ref_s": 10.0, "w_guard_s": 0.0, "tiling_origin_tl_s": 0.0},
                                              "frame_sha256": "00" * 32, "strata": [{"stratum_id": "sdg:ceiling", "definition": "d", "N_h": 1, "n_h": 1}],
                                              "stratifier_inputs": ["stratum_id"], "seed": 1, "frozen_utc": T_LOCK, "ecs_selection_basis": None,
                                              "ecs_selection_basis_null_reason": "not_applicable"})
    assert "spl_id" not in plan
    w = lk.strip_derived("reference_window", {"rwn_id": "rwn_x", "plan_id": "spl_x", **_window()})
    assert "rwn_id" not in w and "plan_id" not in w
    spec = Spec("V0", "E-1.2.26", "c" * 40, "e" * 64, (), (ART_V0,), {})
    tables = {"sampling_plan": [plan], "reference_window": [lk.locked_window(w, "f" * 64, T_LOCK)]}
    a, b = build_artifact(spec, tables), build_artifact(spec, tables)
    assert a.artifact_id == b.artifact_id and a.payload_sha256 == b.payload_sha256
    later = {**tables, "reference_window": [lk.locked_window(w, "f" * 64, datetime(2026, 11, 27, tzinfo=timezone.utc))]}
    assert build_artifact(spec, later).payload_sha256 == a.payload_sha256  # locked_utc is an event column, outside the hash (AR-7)


def test_vr_e_054_accepts_the_locked_rows_before_s8():
    from rq1.schema import vr_rules
    w = lk.locked_window(_window(), "f" * 64, T_LOCK)
    assert vr_rules.check_windows_locked([w], datetime(2026, 11, 27, tzinfo=timezone.utc)) == []
    assert vr_rules.check_windows_locked([_window()], datetime(2026, 11, 27, tzinfo=timezone.utc))  # V0 as stored: not locked
