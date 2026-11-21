"""T23 rules (pure functions) and the T23.15 schema tables."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rq1.schema import registry, validate
from rq1.schema.errors import ContractError
from rq1.workflow import rules as R
from rq1.workflow.store import HashLog

U = "2026-11-19T10:00:00.000000Z"


def ep(k, onset, dur=1.0, g2="lbl_nm", kind="aligned_session"):
    return {"ep_id": f"ep_{k}", "t_start_tl_s": onset, "t_end_tl_s": onset + dur, "g2_label": g2, "camera_id": f"c{k}",
            "timeline_id": "tl_x", "timeline_kind": kind}


def test_t23_14_defaults():
    assert R.PARAMS == {"wf_source_config": "BL-6", "t_group_s": 2.0, "t_pending_days": 7.0, "theta_rej": 0.5, "theta_over": 0.3,
                        "n_flag_min": 10, "n_flag_min_sm": 5, "t_link_s": 60.0, "k_miss": 2}


def test_t23_4_transition_table():
    t = R.TRANSITIONS
    assert t["am_approve"][1:] == (("pending_am",), "recorded") and t["am_reject"][1:] == (("pending_am",), "pending_sm")
    assert t["am_duplicate"][2] == "closed_duplicate" and t["sm_uphold"][1:] == (("pending_sm",), "closed_rejected")
    assert t["sm_overturn"][1:] == (("pending_sm",), "recorded") and t["sm_reclassify"][1:] == (("recorded",), "closed_rejected")
    assert t["sm_reopen"][1:] == (("closed_rejected", "closed_duplicate"), "pending_sm") and t["sm_note"][1:] == (None, None)


def test_e1223_new_actions_and_state():
    """T23.19 (c), T23.20 (c), (e); D-49.1 section 4.1."""
    t = R.TRANSITIONS
    assert t["sm_confirm_duplicate"] == ("safety_manager", ("pending_sm",), "closed_duplicate")
    # T23.28 (a) (D-51 item 1): am_split became `split`, by the area manager or the safety manager
    assert t["split"] == ("area_manager|safety_manager", ("pending_am", "pending_sm"), "closed_split")
    assert t["withdraw_recordability"] == ("safety_manager", None, None)
    assert "closed_split" in R.STATES and R.WITHDRAW_REASONS == ("classification_changed", "entered_in_error",
                                                                 "event_not_work_related", "other")
    assert R.GROUP_RESOLUTIONS == ("one_interaction", "cannot_tell")
    enum = {f.name: f for f in registry.TABLES["wf_report_log"].fields}["action"].type.values
    assert {"sm_confirm_duplicate", "am_split", "split", "withdraw_recordability"} <= set(enum)


def test_t23_5_b_reject_labels():
    assert R.REJECT_REASONS == {"not_hazardous": "not_hazardous", "no_person_or_no_forklift": "not_hazardous",
                                "cannot_tell_from_video": "ud", "other": "unsure"}


def test_grouping_transitive_fx14e_and_separate():
    groups = [g for g, _ in R.group_episodes([ep(1, 0.0), ep(2, 1.5), ep(3, 3.2)], 2.0)]
    assert [[e["ep_id"] for e in g] for g in groups] == [["ep_1", "ep_2", "ep_3"]]
    # gap of 4.1 s > 2 x 2.0 s: two groups
    assert len(R.group_episodes([ep(1, 0.0), ep(2, 5.1)], 2.0)) == 2


def test_grouping_exact_touch_merges_t23_21_b():
    """T23.21 (b) (E-1.2.23): closed intervals; widened intervals that only touch are merged (was refused under CR-030 item 7)."""
    assert len(R.group_episodes([ep(1, 0.0), ep(2, 5.0)], 2.0)) == 1  # 1.0 + 2.0 == 5.0 - 2.0


def test_grouping_without_a_common_axis_is_per_camera():
    groups = R.group_episodes([ep(1, 0.0, kind="recording_local"), ep(2, 0.5, kind="recording_local")], 2.0)
    assert [len(g) for g, _ in groups] == [1, 1] and {b for _, b in groups} == {R.PER_CAMERA}


def test_kind_and_ai_label():
    assert R.report_kind([ep(1, 0, g2="lbl_nm"), ep(2, 0, g2="lbl_ct")]) == "incident_draft"
    assert R.report_kind([ep(1, 0, g2="lbl_ud")]) == "near_miss"
    assert R.group_ai_label([ep(1, 0, g2="lbl_ud")]) == "candidate, undetermined"
    assert R.group_ai_label([ep(1, 0, g2="lbl_ud"), ep(2, 0, g2="lbl_nm")]) == "candidate near miss and candidate, undetermined"


def test_description_template():
    """T23.2 (d) as changed by T23.24 (e): "Smallest estimated separation <x> m (<method>, <sigma status>)"."""
    m = {"ep_id": "ep_1", "camera_id": "c1", "minclr_m": 0.4, "geometry_method": "full_camera", "calibration_tier": "full_camera",
         "sigma_status": "uncalibrated_model"}
    d = R.description("candidate near miss", "Area 1", "2026-11-16T08:01:40.000000Z", R.combined([m]), False)
    assert d == ("The system flagged a candidate near miss between a person and a forklift in Area 1 at 2026-11-16 08:01:40 UTC. "
                 "Smallest estimated separation 0.40 m (full_camera, uncalibrated_model). Review the clip before deciding.")
    none = {**m, "minclr_m": None, "minclr_m_null_reason": "not_observable"}
    d = R.description("candidate, undetermined", "Area 1", "2026-11-16T08:01:40.000000Z", R.combined([none]), True)
    assert "a candidate, undetermined between" in d and "not available (not_observable)" in d and "(simulated calendar)" in d
    assert R.lint_workflow(d, html_page=False) == []


def test_iso_week_and_bounds():
    assert R.iso_week("2026-11-16T08:00:00.000000Z") == "2026-W47"
    lo, hi = R.week_bounds("2026-W47")
    assert lo == datetime(2026, 11, 16, tzinfo=timezone.utc) and (hi - lo).days == 7


def test_incidence_rate_bls_formula():
    # I9: cases x 200,000 / hours; 3 cases over 150,000 h -> 4.0
    assert 3 * 200_000 / 150_000 == 4.0


def test_cell_prints_its_value_and_notes():
    """CR-030 is ruled (D-49): every indicator has one reading; notes print beside the value (T23.18 c, d)."""
    c = R.Cell(R.Share(1, 2), {"undecided": 3})
    assert c.text(lambda v: v.text()).endswith("; undecided: 3") and c.determined


def test_share_text_has_n_and_wilson():
    assert R.Share(1, 1).text().startswith("1/1 = 1.000 (n = 1; Wilson 95 % interval ")


def test_schema_tables_present_and_rows_validate():
    for t in ("wf_config", "wf_establishment", "wf_area", "wf_user", "wf_report", "wf_report_log", "wf_hours", "demo_manifest"):
        assert t in registry.TABLES
    assert validate.validate_row("wf_establishment", {"est_id": "est_" + "a" * 26, "name": "X", "demo": True}) == []
    assert validate.validate_row("wf_establishment", {"est_id": "est_" + "a" * 26, "name": "X", "demo": "yes"})
    bad_user = {"user_id": "usr_" + "a" * 26, "pseudonym": "P", "roles": ["boss"], "est_id": None, "est_id_null_reason": "not_applicable", "area_ids": []}
    assert validate.validate_row("wf_user", bad_user)
    rep = {"report_id": "rpt_" + "a" * 26, "kind_initial": "incident_draft", "origin": "ai", "est_id": "est_" + "a" * 26,
           "area_id": "area_" + "a" * 26, "member_episode_ids": ["ep_" + "b" * 26], "member_episode_ids_null_reason": None, "created_utc": U}
    assert validate.validate_row("wf_report", rep) == []
    assert validate.validate_row("wf_report", {**rep, "origin": "robot"})


def test_report_log_chain(tmp_path):
    log = HashLog(tmp_path / "log.jsonl", "wf_report_log")
    row = {"entry_id": "wfe_" + "a" * 26, "report_id": "rpt_" + "a" * 26, "action": "create_human", "actor_user_id": "system",
           "actor_role": None, "actor_role_null_reason": "not_applicable",  # T23.28 (a) column (AR-65)
           "state_before": None, "state_before_null_reason": "not_applicable", "state_after": "pending_am", "field_changes": {},
           "label": None, "label_null_reason": "not_applicable", "reason": None, "reason_null_reason": "not_applicable",
           "note": None, "note_null_reason": "not_applicable", "linked_record_ids": [], "created_utc": U}
    log.append(row)
    log.append({**row, "entry_id": "wfe_" + "b" * 26, "action": "sm_note", "note": "n", "note_null_reason": None,
                "state_before": "pending_am", "state_before_null_reason": None})
    assert log.verify() == [] and log.head()[0] == 2
    with pytest.raises(ContractError):
        log.append({**row, "action": "delete"})  # not a T23.4 action
    lines = (tmp_path / "log.jsonl").read_bytes().splitlines()
    (tmp_path / "log.jsonl").write_bytes(b"\n".join([lines[1], lines[0]]) + b"\n")
    assert log.verify()
