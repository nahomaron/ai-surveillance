"""T-10: splits, leakage audit and sampling. Texts: E-1.2.1 section 8; Appendix T CT-S, SP, FX-A3.1 (T3)."""
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from rq1.evaluation import estimators
from rq1.sampling import plan as sampling
from rq1.schema import vr_rules
from rq1.schema.errors import ContractError
from rq1.splits import builder, leakage

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"


def rec(rid, session, partition, dataset="ds", **lineage):
    return {"recording_id": f"rec_{rid}", "session_id": f"ses_{session}", "dataset_id": dataset, "partition": partition, "lineage": lineage}


def freeze(recs, tier="T1", **kw):
    return builder.freeze(recs, split_label="s", version="1", tier=tier, frozen_utc=T0, **kw)


def partition_of(split, recording_id):
    group = next(g for g in split["leakage_groups"] if recording_id in g["member_recording_ids"])
    return next(a["partition"] for a in split["assignments"] if a["leakage_group_id"] == group["leakage_group_id"])


def test_metadata_edges_ar_31():
    recs = [rec("a", "1", "train", scene_id="sc1"), rec("b", "2", "train", scene_id="sc1"), rec("c", "3", "train", render_parent="sc1"),
            rec("d", "4", "train", actor_roster_ref="r", layout_id="l", script_id="s", collection_day="d1"),
            rec("e", "5", "train", actor_roster_ref="r", layout_id="l", script_id="s", collection_day="d1"),
            rec("f", "6", "train", actor_roster_ref="r", layout_id="l", script_id="s", collection_day="d2"), rec("g", "6", "train"),
            rec("h", "7", "train", scene_id="sc1", dataset="other")]
    kinds = {(a, b): k for a, b, k in leakage.metadata_edges(recs)}
    assert kinds[("rec_a", "rec_b")] == kinds[("rec_a", "rec_c")] == "same_scene_or_run"
    assert kinds[("rec_d", "rec_e")] == "same_scripted_instance" and ("rec_d", "rec_f") not in kinds
    assert kinds[("rec_f", "rec_g")] == "same_session"
    assert not [k for k in kinds if "rec_h" in k]  # lineage edges stay within one dataset


def test_ct_s_01_clean_run():
    split = freeze([rec(x, x, p, ext_run_id=x) for x, p in (("r1", "train"), ("r2", "validation"), ("r3", "test"))])
    assert len(split["leakage_groups"]) == 3 and split["revision"] is None
    audit = builder.audit(split, "spm_1", identities=[], discovery_basis="sampled_annotation", audit_seq=1)
    assert audit["violations"] == [] and audit["audit_complete"] is True
    with pytest.raises(ContractError):  # CT-S-04 and SP-03: no revision without a violation
        builder.revise(split, "spm_1", audit, "lka_1", frozen_utc=T1)


def test_ct_e_23_two_cameras_of_one_interaction_across_partitions():
    with pytest.raises(ContractError) as exc:  # FX-14: same session, train and test
        freeze([rec("c1", "s", "train"), rec("c2", "s", "test")])
    assert exc.value.code == "ERR-LEAKAGE"


def _two_unrelated():
    return freeze([rec("a", "1", "train"), rec("b", "2", "test"), rec("c", "3", "validation")])


def test_ct_s_02_annotation_discovers_leakage():
    split = _two_unrelated()
    edge = {"recording_a": "rec_a", "recording_b": "rec_b", "edge_type": "same_physical_interaction", "evidence_ref": "ann-1"}
    audit = builder.audit(split, "spm_1", identities=[edge], discovery_basis="sampled_annotation", audit_seq=1)
    assert len(audit["violations"]) == 1 and audit["discovery_basis"] == "sampled_annotation"
    v2 = builder.revise(split, "spm_1", audit, "lka_1", frozen_utc=T1)
    assert partition_of(v2, "rec_b") == "train" and v2["parent_version_id"] == "spm_1"  # PR-01
    assert v2["revision"]["rule"] == "PR-01" and v2["revision"]["audit_id"] == "lka_1"
    windows = [{"window_index": 0, "stratum_id": "h1", "recording_ids": ["rec_b"]}, {"window_index": 1, "stratum_id": "h2", "recording_ids": ["rec_x"]}]
    assert builder.affected_strata(windows, split, v2, audit) == {"h1"}  # R-3: requires_resample
    results = [{"metric_id": "EV-M1", "slice": {"partition": "test"}, "validity": "valid"}, {"metric_id": "EV-M1", "slice": {"partition": "train"}, "validity": "valid"}]
    marked = builder.invalidate_results(results, split, v2)
    assert [r["validity"] for r in marked] == ["invalidated_leakage", "valid"]


def test_ct_s_03_monotone_move_to_validation():
    split = _two_unrelated()
    edge = {"recording_a": "rec_c", "recording_b": "rec_b", "edge_type": "same_physical_interaction", "evidence_ref": "ann-2"}
    audit = builder.audit(split, "spm_1", [edge], "sampled_annotation", 1)
    v2 = builder.revise(split, "spm_1", audit, "lka_1", frozen_utc=T1)
    assert partition_of(v2, "rec_b") == "validation"
    windows = [{"window_index": 0, "stratum_id": "h1", "recording_ids": ["rec_b"], "partition_at_sampling": "test"}]
    assert sampling.test_domain(windows, v2) == []  # test windows from the moved group leave the test domain


def test_sp_04_revision_never_moves_into_test():
    split = _two_unrelated()
    edge = {"recording_a": "rec_a", "recording_b": "rec_b", "edge_type": "same_physical_interaction", "evidence_ref": "x"}
    v2 = builder.revise(split, "spm_1", builder.audit(split, "spm_1", [edge], "sampled_annotation", 1), "lka_1", frozen_utc=T1)
    before = {r: partition_of(split, r) for r in ("rec_a", "rec_b", "rec_c")}
    after = {r: partition_of(v2, r) for r in before}
    assert all(not (after[r] == "test" and before[r] != "test") for r in before)


def test_sp_07_revision_takes_no_metric_or_label_inputs():
    params = set(inspect.signature(builder.revise).parameters)
    assert params == {"split", "split_id", "audit", "audit_id", "frozen_utc", "recordings"}  # recordings: metadata only (AR-34)


def _t2b(extra=None):
    recs = [rec("s1c1", "s1", "train"), rec("s1c2", "s1", "test"), rec("s2c1", "s2", "train")]
    if extra:
        recs.append(extra)
    return recs


def test_ct_s_05_t2b_declared_share():
    split = freeze(_t2b(), tier="T2b", t2b_shared_sessions=["ses_s1"], shared_scene_content=True)
    edge = {"recording_a": "rec_s1c1", "recording_b": "rec_s1c2", "edge_type": "same_physical_interaction", "evidence_ref": "x"}
    audit = builder.audit(split, "spm_1", [edge], "sampled_annotation", 1, recordings=_t2b())
    # AR-34 as changed by the Architect (12 Nov 2026): recorded in edges_added, not a violation.
    assert audit["violations"] == [] and audit["edges_added"] == [edge]
    with pytest.raises(ContractError):  # nothing to revise
        builder.revise(split, "spm_1", audit, "lka_1", frozen_utc=T1, recordings=_t2b())
    with pytest.raises(ContractError) as exc:
        freeze(_t2b(), tier="T2b", t2b_shared_sessions=["ses_s1"], shared_scene_content=False)
    assert exc.value.code == "ERR-LEAKAGE"


def test_ct_s_06_t2b_undeclared_share():
    with pytest.raises(ContractError) as exc:
        freeze(_t2b(rec("s2c2", "s2", "test")), tier="T2b", t2b_shared_sessions=["ses_s1"], shared_scene_content=True)
    assert exc.value.code == "ERR-LEAKAGE"


def test_ct_s_07_sp_08_test_run_before_audit_is_blocked():
    split = _two_unrelated()
    with pytest.raises(ContractError) as exc:
        builder.check_s8_allowed("test", split, audits=[], run_start=T2)
    assert exc.value.code == "ERR-AUDIT-PENDING"
    pending = {**builder.audit(split, "spm_1", [], "sampled_annotation", 1), "audit_complete": False}
    with pytest.raises(ContractError):
        builder.check_s8_allowed("test", split, audits=[pending], run_start=T2)
    done = builder.audit(split, "spm_1", [], "sampled_annotation", 2)
    builder.check_s8_allowed("test", split, audits=[pending, done], run_start=T2)
    builder.check_s8_allowed("validation", split, audits=[], run_start=T2)  # R-2 applies to test only
    with pytest.raises(ContractError):  # SP-08 reads the event time: the split must be frozen before the run
        builder.check_s8_allowed("test", {**split, "frozen_utc": T2}, audits=[done], run_start=T1)


def test_sp_01_split_has_no_validation_inputs():
    assert builder.check_sp_01([{"stage": "S0"}], validation_times=[T1], frozen_utc=T0) == []
    assert [i.rule for i in builder.check_sp_01([{"stage": "V0"}], [], T0)] == ["SP-01"]
    assert [i.rule for i in builder.check_sp_01([{"stage": "S0"}], [T0], T1)] == ["SP-01"]  # validation record before the freeze


def test_ct_s_10_sp_11_roster_leak_screened_before_split():
    recs = [rec("d", "4", "test", actor_roster_ref="r", layout_id="l", script_id="s", collection_day="d1"),
            rec("e", "5", "test", actor_roster_ref="r", layout_id="l", script_id="s", collection_day="d1")]
    split = freeze(recs)
    assert len(split["leakage_groups"]) == 1 and split["leakage_groups"][0]["edge_types"] == ["same_scripted_instance"]
    audit = builder.audit(split, "spm_1", [], "metadata", 1)
    assert audit["violations"] == [] and sampling.estimand_validity([audit]) == "design_valid"


# Sampling frame and RES draw
def test_tiling_and_guard():
    windows = sampling.tile_windows("cgp_1", "tl_1", (0.0, 90.0), w_ref=30.0, w_guard=5.0, origin=0.0)
    assert [(w["window_index"], w["t_start_tl_s"], w["t_end_tl_s"], w["t_guard_end_tl_s"]) for w in windows] == [
        (0, 0.0, 30.0, 35.0), (1, 30.0, 60.0, 65.0), (2, 60.0, 90.0, 90.0)]


def test_d7_short_timeline_gives_one_short_window():
    # Owner decision D-7 (b), 12 Nov 2026: a 10 s timeline with w_ref = 30 s gives exactly one 10 s window.
    windows = sampling.tile_windows("cgp_1", "tl_1", (0.0, 10.0), w_ref=30.0, w_guard=5.0, origin=0.0)
    assert [(w["t_start_tl_s"], w["t_end_tl_s"], w["window_length_s"], w["t_guard_end_tl_s"]) for w in windows] == [(0.0, 10.0, 10.0, 10.0)]


def test_d7_last_window_shorter_and_guard_clipped():
    windows = sampling.tile_windows("cgp_1", "tl_1", (0.0, 70.0), w_ref=30.0, w_guard=5.0, origin=0.0)
    assert [(w["t_start_tl_s"], w["t_end_tl_s"], w["window_length_s"], w["t_guard_end_tl_s"]) for w in windows] == [
        (0.0, 30.0, 30.0, 35.0), (30.0, 60.0, 30.0, 65.0), (60.0, 70.0, 10.0, 70.0)]


def test_d7_weights_stay_inverse_pi_with_a_short_window():
    population = [{**w, "stratum_id": "h", "recording_ids": ["rec_x"], "partition_at_sampling": "test", "leakage_group_id": "lkg_x"}
                  for w in sampling.tile_windows("cgp_" + "a" * 26, "tl_" + "a" * 26, (0.0, 70.0), 30.0, 5.0, 0.0)]
    drawn = sampling.draw_res(population, {"h": 3}, seed=1)
    assert [w["weight"] for w in drawn] == [1.0, 1.0, 1.0]


def _population(n_per=10, strata=("h1", "h2")):
    return [{"camera_group_id": "cgp_" + s * 13, "timeline_id": "tl_" + s * 13, "window_index": i, "t_start_tl_s": 30.0 * i, "t_end_tl_s": 30.0 * (i + 1),
             "t_guard_end_tl_s": 30.0 * (i + 1) + 5.0, "stratum_id": s, "recording_ids": [f"rec_{s}"], "partition_at_sampling": "test",
             "leakage_group_id": f"lkg_{s}"} for s in strata for i in range(n_per)]  # IDs: 26 characters after the prefix


def test_res_draw_is_seeded_and_reproducible():
    a = sampling.draw_res(_population(), {"h1": 2, "h2": 4}, seed=7)
    b = sampling.draw_res(_population(), {"h1": 2, "h2": 4}, seed=7)
    assert [(w["stratum_id"], w["window_index"]) for w in a] == [(w["stratum_id"], w["window_index"]) for w in b]
    assert sorted({w["stratum_id"]: w["inclusion_prob"] for w in a}.items()) == [("h1", 0.2), ("h2", 0.4)]  # pi = n_h / N_h
    assert all(w["weight"] == pytest.approx(1 / w["inclusion_prob"]) and w["sample_type"] == "RES" for w in a)
    c = sampling.draw_res(_population(), {"h1": 2, "h2": 4}, seed=8)
    assert [w["window_index"] for w in a] != [w["window_index"] for w in c]


def test_plan_rows_validate_and_hash_frame():
    rows = sampling.plan_rows(plan_label="p", version="1", sample_type="RES", split_version_id="spm_" + "a" * 26, population=_population(),
                              selected=sampling.draw_res(_population(), {"h1": 2, "h2": 2}, seed=1), strata_n={"h1": 2, "h2": 2}, seed=1,
                              frame=dict(camera_group_ids=["cgp_" + "h1" * 13, "cgp_" + "h2" * 13], w_ref_s=30.0, w_guard_s=5.0, tiling_origin_tl_s=0.0), frozen_utc=T0)
    plan, windows = rows["sampling_plan"][0], rows["reference_window"]
    assert {s["stratum_id"]: (s["N_h"], s["n_h"]) for s in plan["strata"]} == {"h1": (10, 2), "h2": (10, 2)}
    assert len(plan["frame_sha256"]) == 64 and len(windows) == 4
    from rq1.ids.artifact import Spec, build_artifact
    built = build_artifact(Spec("V0", "E-1.2.5", "f", "f", (), ("spm_" + "a" * 26,), {}), rows)
    assert all(w["plan_id"] == built.tables["sampling_plan"][0]["spl_id"] for w in built.tables["reference_window"])


def test_ct_e_18_sampler_isolation():
    assert vr_rules.check_v0_inputs([{"stage": "S1", "table": "coverage_segment"}, {"stage": "X0b", "table": "split_manifest"}]) == []
    with pytest.raises(ContractError):
        sampling.check_inputs([{"stage": "S5", "table": "episode"}])
    assert not {"episodes", "detections", "events"} & set(inspect.signature(sampling.draw_res).parameters)


def test_ct_e_19_ecs_excluded_and_weights_inverse_pi():
    res = sampling.draw_res(_population(), {"h1": 2, "h2": 2}, seed=3)
    ecs = sampling.ecs_windows(_population()[:1], basis="FX-15: chosen from system alerts")
    assert ecs[0]["inclusion_prob"] is None and ecs[0]["weight"] is None and ecs[0]["sample_type"] == "ECS"
    assert sampling.headline_windows(res + ecs) == res
    rows = [{"metric_id": "EV-M1", "sample_type": "ECS"}]
    assert [i.code for i in vr_rules.check_headline_sample_type(rows)] == ["ERR-ECS-AGGREGATE"]


def test_ct_s_09_sp_10_conditional_results_carry_no_rates():
    rows = [{"metric_id": "EV-M7", "estimand": "conditional_on_selection"}, {"metric_id": "EV-M8", "estimand": "conditional_on_selection"}]
    assert [i.rule for i in sampling.check_sp_10(rows)] == ["SP-10"]


def test_sp_02_windows_reference_current_split():
    assert sampling.check_sp_02([{"split_version_id": "spm_2"}], current_split_id="spm_2") == []
    assert [i.rule for i in sampling.check_sp_02([{"split_version_id": "spm_1"}], current_split_id="spm_2")] == ["SP-02"]


def test_ct_s_08_fx_a3_1_counterexample():
    fixture = json.loads((FIX / "FX-A3.1.json").read_text())["inputs"]
    recs = [rec(r, r, "test") for r in fixture["recordings"]] + [rec("train", "t", "train")]
    split = freeze(recs)
    population = [{"camera_group_id": f"cgp_{r}", "timeline_id": f"tl_{r}", "window_index": i, "t_start_tl_s": 30.0 * i, "t_end_tl_s": 30.0 * (i + 1),
                   "t_guard_end_tl_s": 30.0 * (i + 1), "stratum_id": r, "recording_ids": [f"rec_{r}"], "partition_at_sampling": "test",
                   "leakage_group_id": partition_of(split, f"rec_{r}")} for r in fixture["recordings"] for i in range(fixture["windows_per_recording"])]
    shared = {(r, i) for r in fixture["shared_recordings"] for i in range(fixture["shared_windows"])}
    seed = next(s for s in range(100) if any((w["stratum_id"], w["window_index"]) in shared for w in sampling.draw_res(population, {r: 2 for r in fixture["recordings"]}, seed=s)))
    selected = sampling.draw_res(population, {r: fixture["res_windows_per_recording"] for r in fixture["recordings"]}, seed=seed)
    assert {w["inclusion_prob"] for w in selected} == {fixture["pi"]}
    found = sorted({w["stratum_id"] for w in selected if (w["stratum_id"], w["window_index"]) in shared})
    edges = [{"recording_a": f"rec_{r}", "recording_b": "rec_train", "edge_type": fixture["edge"], "evidence_ref": "window"} for r in found]
    audit = builder.audit(split, "spm_1", edges, fixture["discovery_basis"], 1)
    v2 = builder.revise(split, "spm_1", audit, "lka_1", frozen_utc=T1)
    assert all(partition_of(v2, f"rec_{r}") == "train" for r in found)  # moved_to train
    assert builder.affected_strata(selected, split, v2, audit) == set(found)  # requires_resample
    assert sampling.estimand_validity([audit]) == "requires_resample"
    assert [i.rule for i in sampling.check_sp_09(plan_frozen=T0, audits=[{**audit, "frozen_after": T1}])] == ["SP-09"]  # old-plan headline refused
    fresh = sampling.test_domain(population, v2)
    assert {w["stratum_id"] for w in fresh} == set(fixture["recordings"]) - set(found)
    assert sampling.estimand_validity([], fresh_plan=True) == "design_valid"


def test_d1_ac_09_estimator_simulation():
    """Weighted ratio with the stratified window bootstrap covers the known population ratio near the nominal rate."""
    rng = np.random.Generator(np.random.PCG64(2026))
    strata = {"h1": 40, "h2": 20}
    population = {h: [(int(rng.integers(1, 6)), 0) for _ in range(n)] for h, n in strata.items()}
    population = {h: [(a, int(rng.binomial(a, 0.8 if h == "h1" else 0.5))) for a, _ in rows] for h, rows in population.items()}
    truth = sum(m for rows in population.values() for _, m in rows) / sum(a for rows in population.values() for a, _ in rows)
    n_h = {"h1": 10, "h2": 8}
    covered, reps = 0, 200
    for rep in range(reps):
        sample = {h: [population[h][i] for i in rng.choice(strata[h], n_h[h], replace=False)] for h in strata}
        weights = {h: strata[h] / n_h[h] for h in strata}
        low, high = estimators.stratified_bootstrap_ratio(sample, weights, B=200, seed=rep)
        covered += low <= truth <= high
    assert 0.85 <= covered / reps <= 0.995
