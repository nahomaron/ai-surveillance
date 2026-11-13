"""Appendix T section T14 (E-1.2.12, D-20): a synthetic "scene" is a rendered scene instance; a shared layout family is
shared_scene_content metadata and creates no leakage edge; reports scope Target B intervals and count leakage groups."""
from datetime import datetime, timezone

import pytest

from rq1.export import report
from rq1.schema.errors import ContractError
from rq1.splits import builder, leakage

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def rec(rid, run, partition, dataset="sdg", **lineage):
    return {"recording_id": f"rec_{rid}", "session_id": f"ses_{run}", "dataset_id": dataset, "partition": partition, "lineage": lineage}


def sdg_run(run, partition, seed, cams=("ceiling_00", "eye_00")):
    # Two runs of one SDG layout family: different run, different seed, same layout family and batch.
    return [rec(f"{run}_{c}", run, partition, ext_run_id=run, seed=seed, layout_id="sdg_warehouse_family", generation_batch="nearmiss")
            for c in cams]


@pytest.mark.determinism
def test_ct_t14_1_shared_layout_family_creates_no_edge():
    recs = sdg_run("r1", "train", 11) + sdg_run("r2", "test", 22)
    kinds = {(a, b): k for a, b, k in leakage.metadata_edges(recs)}
    assert ("rec_r1_ceiling_00", "rec_r1_eye_00") in kinds  # views of one run: one scene instance
    assert not [k for k in kinds if "r1" in k[0] and "r2" in k[1]]  # same layout family, different runs: no edge
    split = builder.freeze(recs, split_label="s", version="1", tier="T1", frozen_utc=T0, shared_scene_content=True)
    assert len(split["leakage_groups"]) == 2 and split["shared_scene_content"] is True


@pytest.mark.determinism
def test_ct_t14_1_run_seed_and_render_lineage_edges_unchanged():
    same_seed = [rec("a", "1", "train", ext_run_id="r1", seed=5), rec("b", "2", "train", ext_run_id="r2", seed=5)]
    rerender = [rec("w0", "w0", "train", dataset="ss", scene_id="Warehouse_000"),
                rec("w1", "w1", "train", dataset="ss", scene_id="Warehouse_001", render_parent="Warehouse_000")]
    assert [k for _, _, k in leakage.metadata_edges(same_seed)] == ["same_scene_or_run"]
    assert [k for _, _, k in leakage.metadata_edges(rerender)] == ["same_scene_or_run"]
    with pytest.raises(ContractError):  # a scene and its re-render cannot be split across partitions
        builder.freeze([rerender[0], {**rerender[1], "partition": "test"}], split_label="s", version="1", tier="T1", frozen_utc=T0)


def _split():
    recs = sdg_run("r1", "train", 1) + sdg_run("r2", "train", 2) + sdg_run("r3", "test", 3) + \
        [rec("w0", "w0", "test", dataset="ss", scene_id="Warehouse_000"),
         rec("w1", "w1", "test", dataset="ss", scene_id="Warehouse_001", render_parent="Warehouse_000")]
    origin = {r["recording_id"]: ("synthetic_transferred" if r["recording_id"] == "rec_w1" else "synthetic_rendered") for r in recs}
    return builder.freeze(recs, split_label="s", version="1", tier="T1", frozen_utc=T0, shared_scene_content=True), origin


ROW = {"metric_id": "EV-M1", "interval_method": "cluster_bootstrap", "value": 0.8, "ci_low": 0.7, "ci_high": 0.9, "ci_level": 0.95,
       "slice": {"partition": "test"}}


@pytest.mark.determinism
def test_ct_t14_2_t14_3_target_b_line_scope_and_group_counts():
    split, origin = _split()
    heading, body = report.target_b_section([ROW, {**ROW, "metric_id": "EV-M9", "interval_method": "wilson"}], split, origin)
    assert body[0] == f"Scope: {report.T14_SCOPE}."
    lines = [b for b in body if b.startswith("- ")]
    assert len(lines) == 1  # only Target B (cluster bootstrap) intervals
    # Hand count: train {r1}, {r2} → 2 synthetic_rendered; test {r3} → 1 synthetic_rendered, {w0, w1} → 1 mixed group.
    assert lines[0] == ("- EV-M1 (test): 0.8 [0.7, 0.9] (95 % cluster bootstrap); leakage groups by partition and data origin: "
                        "train: synthetic_rendered 2; test: synthetic_rendered 1, synthetic_rendered+synthetic_transferred 1")


@pytest.mark.determinism
def test_ct_t14_3_missing_origin_is_refused():
    split, origin = _split()
    del origin["rec_w1"]
    with pytest.raises(ContractError):
        report.target_b_section([ROW], split, origin)


@pytest.mark.determinism
@pytest.mark.parametrize("claim", ["generalises to an unseen layout", "unseen-camera performance", "results on unseen sites"])
def test_ct_t14_2_no_unseen_claims_beside_t14_scope(claim):
    split, origin = _split()
    manifest = {"export_class": "research", "contract": "E-1.2.12"}
    section = report.target_b_section([ROW], split, origin)
    report.render(manifest, "research", "R", [section])  # the scoped section itself passes
    with pytest.raises(ContractError):
        report.render(manifest, "research", "R", [section, ("Discussion", [claim])])
