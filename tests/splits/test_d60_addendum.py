"""D-60 STEP 3: the split addendum X0b-A1 (one leakage group per layout; tier 1 `test_layout_holdout`, tier 2 `reserve`;
X0b unchanged). Hand-made rows; expected groups counted by hand beside each assertion. The data test reads the stored
artifacts and is skipped when they are not present."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rq1.ids import artifact as artifacts
from rq1.pipeline import d60
from rq1.schema import files
from rq1.schema.errors import ContractError
from rq1.splits import builder

ROOT = Path(__file__).resolve().parents[2]
T = datetime(2026, 11, 25, 12, 0, 0, tzinfo=timezone.utc)
L0, L1, L2 = "0" * 64, "1" * 64, "2" * 64


def rows(spec):
    """spec: [(scene, layout, n_cameras)] -> addendum rows (one session per scene, as the D-59 S0)."""
    out = []
    for scene, layout, n in spec:
        lin = {"ext_run_id": scene, "scene_id": scene, "generation_batch": "MTMC_Tracking_2026/train@d38193b", "layout_id": layout,
               "render_parent": None, "seed": None}
        out += [{"recording_id": f"rec_{scene[-3:]}_{i}", "session_id": f"ses_{scene[-3:]}", "dataset_id": "dsr_x", "dataset_name": "nvidia/PhysicalAI-SmartSpaces",
                 "lineage": lin, "partition": d60.PARTITION[d60.tier(scene)]} for i in range(n)]
    return sorted(out, key=lambda r: r["recording_id"])


def groups_by_partition(split):
    part = {a["leakage_group_id"]: a["partition"] for a in split["assignments"]}
    return sorted((part[g["leakage_group_id"]], len(g["member_recording_ids"]), tuple(g["edge_types"])) for g in split["leakage_groups"])


def test_one_group_per_layout():
    # 017 and 018 share L1 -> one group of 3 + 2 = 5; 019 alone in L2; 002 and 020 share L0 (tier 2) -> one group of 4.
    # The layout chain runs over every recording of a layout, so the 2 cameras of 019 are also joined by a same_layout edge
    # (each addendum group is one layout and lists it; first draft of this line omitted that edge type: a slip in the hand count).
    r = rows([("Warehouse_017", L1, 3), ("Warehouse_018", L1, 2), ("Warehouse_019", L2, 2), ("Warehouse_002", L0, 2), ("Warehouse_020", L0, 2)])
    split = d60.freeze_addendum(r, T)
    assert groups_by_partition(split) == [("reserve", 4, ("same_layout", "same_session")), ("test_layout_holdout", 2, ("same_layout", "same_session")),
                                          ("test_layout_holdout", 5, ("same_layout", "same_session"))]
    assert (split["split_label"], split["version"], split["tier"], split["basis"]) == ("X0b-A1", "1", "T1", "metadata_only")
    assert split["frozen_utc"] == T and split["parent_version_id"] is None and split["revision"] is None


def test_without_layout_edges_scenes_stay_apart_t14_1():
    r = rows([("Warehouse_017", L1, 3), ("Warehouse_018", L1, 2)])
    assert builder.freeze(r, "x", "1", "T1", T) == builder.freeze(r, "x", "1", "T1", T, extra_edges=())
    assert len(builder.freeze(r, "x", "1", "T1", T)["leakage_groups"]) == 2  # T14.1: a shared layout alone is no edge
    assert len(d60.freeze_addendum(r, T)["leakage_groups"]) == 1


def test_a_layout_in_both_tiers_is_refused():
    r = rows([("Warehouse_010", L0, 2), ("Warehouse_002", L0, 2)])  # a held-out layout shared with a reserve scene
    with pytest.raises(ContractError) as e:
        d60.freeze_addendum(r, T)
    assert e.value.code == "ERR-LEAKAGE"


def test_x0c_audit_passes_and_pr01_refuses_new_partitions():
    r = rows([("Warehouse_017", L1, 3), ("Warehouse_018", L1, 2), ("Warehouse_002", L0, 2)])
    split = d60.freeze_addendum(r, T)
    edges = d60.audit_edges(r)
    assert sum(1 for e in edges if e["edge_type"] == "same_layout") == 4 + 1  # chains: 5 recordings of L1, 2 of L0
    audit = builder.audit(split, "spm_x", edges, "metadata", 1, r)
    assert audit["violations"] == [] and audit["audit_complete"] and len(audit["edges_added"]) == len(edges)
    bad = {**audit, "violations": [{"leakage_group_id": "lkg_x", "partitions": ["reserve", "test_layout_holdout"]}]}
    with pytest.raises(ContractError) as e:
        builder.revise(split, "spm_x", bad, "lka_x", T, r)
    assert e.value.code == "ERR-SPEC"


def test_disjoint_check():
    a = d60.freeze_addendum(rows([("Warehouse_017", L1, 2)]), T)
    b = builder.freeze([{**x, "partition": "validation"} for x in rows([("Warehouse_019", L2, 1)])], "m1a", "1", "T1", T)
    assert d60.check_disjoint_from_x0b(a, b, {"s1", "s2"}, {"s3"}) == {"recordings_in_both": [], "source_files_in_both": [], "addendum_recordings": 2, "x0b_recordings": 1}
    assert d60.check_disjoint_from_x0b(a, a, {"s1"}, {"s1"})["recordings_in_both"] == sorted(m for g in a["leakage_groups"] for m in g["member_recording_ids"])


RECORD = ROOT / "docs/preregistration/freeze_record_X0b-A1.json"
X0B_DIR = ROOT / "out/prereg" / d60.X0B_ARTIFACT_ID


@pytest.mark.skipif(not (RECORD.exists() and X0B_DIR.exists()), reason="local split artifacts not present")
def test_stored_x0b_unchanged_and_addendum_as_recorded():
    rec = json.load(open(RECORD))
    x0b_manifest = json.load(open(X0B_DIR / "manifest.json"))
    assert artifacts.verify(str(X0B_DIR)) == d60.X0B_ARTIFACT_ID and x0b_manifest["payload_sha256"] == d60.X0B_PAYLOAD_SHA256
    x0b = files.read_table(str(X0B_DIR / "split_manifest.parquet"), "split_manifest", artifacts.SCHEMA_VERSION)[0]
    parts = builder.recording_partitions(x0b)
    assert len(parts) == 739 and len(x0b["leakage_groups"]) == 73  # docs/preregistration/freeze_record.json
    assert sorted(set(parts.values())) == ["test", "validation"]
    a_dir = ROOT / "out/prereg" / rec["artifact_id"]
    assert artifacts.verify(str(a_dir)) == rec["artifact_id"]
    a = files.read_table(str(a_dir / "split_manifest.parquet"), "split_manifest", artifacts.SCHEMA_VERSION)[0]
    a_parts = builder.recording_partitions(a)
    assert not set(a_parts) & set(parts) and len(a_parts) == 118
    assert sorted(set(a_parts.values())) == ["reserve", "test_layout_holdout"]
    assert rec["leakage_groups_by_partition"] == {"reserve": 1, "test_layout_holdout": 6}
    assert d60.X0B_ARTIFACT_ID in json.load(open(a_dir / "manifest.json"))["spec"]["input_artifact_ids"]
