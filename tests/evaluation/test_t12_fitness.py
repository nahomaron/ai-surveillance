"""CT-T12-05: Appendix T T12.5 (contract E-1.2.10) fitness gaps; and the evaluation_config record (Architect ruling on
AR-42 item 3). Expected decisions are derived by hand from section 9.6 as amended by T12.5."""
import json
from pathlib import Path

import pytest

from rq1.evaluation import fitness as ft
from rq1.evaluation import matching as mt
from rq1.ids import artifact, core
from rq1.schema import validate

from test_t14_fitness import FIRST_TEST, TYPES, crit, res, scope

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"


def test_ct_t12_05_repeatability_not_met_alone_is_experimental():
    cs = [crit(1, "repeatability"), crit(2, "technical_accuracy")]
    got = ft.decide(scope(cs), cs, {cs[0]["acc_id"]: res(0.60, 0.70)}, FIRST_TEST)  # 0.70 < 0.8: not_met; accuracy not_assessable
    assert got["measurement_status"] == "experimental" and got["failing_interval"] == {"low": 0.60, "high": 0.70}


def test_ct_t12_05_failing_interval_is_first_not_met_of_any_type():
    # Criterion IDs 1 (repeatability) and 2 (accuracy) both not_met: unsuitable (accuracy), failing interval from ID 1.
    cs = [crit(1, "repeatability"), crit(2, "technical_accuracy")]
    got = ft.decide(scope(cs), cs, {cs[0]["acc_id"]: res(0.50, 0.60), cs[1]["acc_id"]: res(0.60, 0.70)}, FIRST_TEST)
    assert (got["measurement_status"], got["failing_interval"]) == ("unsuitable_under_tested_conditions", {"low": 0.50, "high": 0.60})


def test_ct_t12_05_real_staged_validates_and_stays_scoped():
    cs = [crit(i, t) for i, t in enumerate(TYPES)]
    results = {c["acc_id"]: res(0.82, 0.90) for c in cs}
    assert ft.decide(scope(cs, "real_staged"), cs, results, FIRST_TEST)["measurement_status"] == "technically_validated"
    # A real_natural scope has its own results; with none it is not_yet_assessable: nothing carries over.
    assert ft.decide(scope(cs, "real_natural"), cs, {}, FIRST_TEST)["measurement_status"] == "not_yet_assessable"
    assert ft.decide(scope(cs, "synthetic_rendered"), cs, results, FIRST_TEST)["measurement_status"] == "experimental"


def test_ct_t12_05_comparability_characterized():
    cs = [crit(i, t) for i, t in enumerate(TYPES)]
    comparability = cs[4]["acc_id"]
    results = {c["acc_id"]: res(0.82, 0.90) for c in cs}
    decided = {**results, comparability: res(0.50, 0.60)}  # comparability not_met, but decided: characterized
    got = ft.decide(scope(cs, "real_natural"), cs, decided, FIRST_TEST)
    assert got["measurement_status"] == "technically_validated" and got["criterion_decisions"][comparability] == "not_met"
    undecided = {k: v for k, v in results.items() if k != comparability}  # comparability not_assessable: not characterized
    assert ft.decide(scope(cs, "real_natural"), cs, undecided, FIRST_TEST)["measurement_status"] == "experimental"


@pytest.mark.determinism
def test_evaluation_config_record_carries_the_mapping():
    v = json.loads((FIX / "TEST-ONLY-PARAMETERS.json").read_text())["parameters"]
    groups = {"r1": frozenset({"G1", "G2"}), "r2": frozenset({"G1"})}
    make = lambda g: mt.evaluation_config(v["iou_m"], v["iou_cm"], v["eps_amb"], v["n_miss"], v["bootstrap_B"], 7, "rule_conformance", g, "TEST-ONLY")
    record = make(groups)
    assert validate.validate_row("evaluation_config", record) == []
    a, b = core.make_id("evc", record), core.make_id("evc", make({**groups, "r2": frozenset({"G1", "G2"})}))
    assert a.startswith("evc_") and a != b  # a changed mapping changes the evc ID, and so the S8 specification
    spec = artifact.Spec("S8", "E-1.2.10", "f", "f", (a, "spm_" + "a" * 26), (), {})
    artifact.check_art_iso(spec)  # ART-ISO for S8: exactly one evc and one spm
    assert artifact.spec_id(spec) != artifact.spec_id(artifact.Spec("S8", "E-1.2.10", "f", "f", (b, "spm_" + "a" * 26), (), {}))
