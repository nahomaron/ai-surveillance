"""Appendix T T23.16 (e) (contract E-1.2.23; D-49): evaluation code reads adjudications only through
`reference_adjudications(...)`, and a static test refuses any other read in the A-workstream modules (FX-14m).

The accessor is tested here on a hand-made store folder (the V-02 layout of AR-61 item 5: JSONL envelopes
{batch_id, recording_id, row}; batch manifests under batches/<id>/manifest.json)."""
from pathlib import Path

import pytest

from rq1.schema.canonical import canonical_json
from rq1.schema.errors import ContractError
from rq1.validation import reference as REF

SRC = Path(__file__).resolve().parents[2] / "src"


def _adj(tag, namespace="reference", cls="independent_expert_judgment", reason=None, drop_reason=False):
    row = {"adj_id": f"adj_{tag.ljust(26, '0')}", "target_type": "system_episode", "target_id": f"ep_{tag.ljust(26, '0')}",
           "namespace": namespace, "final_label": "nm", "tier": "tier1", "method": "agreement",
           "assessment_ids": [f"rva_{tag.ljust(26, '0')}"], "agreement_stat_ref": "rvb_x", "agreement_stat_ref_null_reason": None,
           "prov_class": "human_adjudicated", "reference_class": cls, "reference_class_null_reason": reason}
    if drop_reason:
        del row["reference_class_null_reason"]
    return row


def _store(tmp_path, rows, pilot_targets=()):
    root = tmp_path / "store"
    (root / "batches" / "rvb_pilot").mkdir(parents=True)
    (root / "batches" / "rvb_pilot" / "manifest.json").write_bytes(canonical_json({"batch_id": "rvb_pilot", "pilot": True,
                                                                                  "target_ids": list(pilot_targets)}))
    with open(root / "adjudication.jsonl", "wb") as h:
        for batch, row in rows:
            h.write(canonical_json({"batch_id": batch, "recording_id": "rec_x", "row": row}) + b"\n")
    return root


def test_accessor_returns_reference_expert_rows_only(tmp_path):
    rows = [("rvb_a", _adj("ref1")), ("rvb_a", _adj("ref2", drop_reason=True)),  # stored before E-1.2.23 (T23.16 f)
            (None, _adj("cr1", "candidate_review", None, "not_applicable")),
            ("rvb_a", _adj("rc1", cls="rule_conformance")),
            ("rvb_pilot", _adj("pil1"))]
    root = _store(tmp_path, rows, pilot_targets=[_adj("pil1")["target_id"]])
    got = REF.reference_adjudications(root)
    assert [r["adj_id"][:8] for r in got] == ["adj_ref1", "adj_ref2"]
    assert all(r["reference_class_null_reason"] is None for r in got)


def test_accessor_refuses_a_stored_candidate_review_row_without_reason(tmp_path):
    root = _store(tmp_path, [(None, _adj("cr1", "candidate_review", None, drop_reason=True))])
    with pytest.raises(ContractError) as err:
        REF.reference_adjudications(root)
    assert err.value.code == "ERR-INVARIANT"


def test_accessor_on_a_missing_store_is_empty(tmp_path):
    assert REF.reference_adjudications(tmp_path / "nothing") == []


def test_fx14m_planted_direct_read_is_found(tmp_path):
    """FX-14m (D-49.1 section 6.1, retyped): an evaluation module that opens adjudication.jsonl directly -> the test fails."""
    planted = tmp_path / "src/rq1/evaluation/_planted.py"
    planted.parent.mkdir(parents=True)
    planted.write_text('rows = open(root / "adjudication.jsonl").read()\n')
    found = REF.direct_read_violations(tmp_path / "src")
    assert found and found[0][0].endswith("_planted.py")


def test_fx14l_accessor_part_on_a_hand_made_store(tmp_path):
    """FX-14l (D-49.1 section 6.1, retyped), the part that needs no V-02 or workflow code: a store holding 1 reference
    adjudication (agreement) and 3 candidate_review adjudications -> reference_adjudications() returns 1 row and the EV-M12
    population has 1 target. (The kappa and batch-draw parts run in tests/review/test_t23_16_isolation.py.)"""
    rows = [("rvb_a", _adj("ref1"))] + [(None, _adj(f"cr{k}", "candidate_review", None, "not_applicable")) for k in (1, 2, 3)]
    root = _store(tmp_path, rows)
    assert len(REF.reference_adjudications(root)) == 1
    assert len(REF.ev_m12_population(root)["pairs"]) == 1


@pytest.mark.parametrize("text", ['p = root / "reviewer_assessment.jsonl"\n', "x = store.adjudications()\n",
                                  'json.loads(Path("adjudication.jsonl").read_text())\n', "rows = s.assessments()\n"])
def test_other_direct_reads_are_found(tmp_path, text):
    (tmp_path / "src/rq1/pipeline").mkdir(parents=True)
    (tmp_path / "src/rq1/pipeline/m.py").write_text(text)
    assert REF.direct_read_violations(tmp_path / "src")


def test_fx14m_the_real_tree_is_clean():
    """T23.16 (e): src/rq1/evaluation/, src/rq1/pipeline/ and src/rq1/review/protocol.py read no adjudication or assessment
    file except through the accessor (paths that do not exist on a branch are skipped)."""
    assert REF.direct_read_violations(SRC) == []
