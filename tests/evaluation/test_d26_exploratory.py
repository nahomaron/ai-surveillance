"""D-26 (exploratory phase for real footage): real-origin results are reported as experimental, never technically_validated,
applied through the section 9.6 downgrade-only override (no contract change); reports carry the fixed exploratory line."""
import pytest

from rq1.decode.quality import EXPLORATORY_NOTE
from rq1.evaluation import fitness
from rq1.export import report
from rq1.schema.errors import ContractError


def decided(status):
    return {"criterion_decisions": {"c1": "met"}, "measurement_status": status, "failing_interval": None, "failing_interval_null_reason": "not_applicable"}


def row(origin, status):
    return fitness.exploratory_fitness_row({"data_origin": origin}, decided(status), "CV0", {}, False)


@pytest.mark.determinism
@pytest.mark.parametrize("origin", ["real_natural", "real_staged"])
def test_real_technically_validated_is_downgraded_to_experimental(origin):
    r = row(origin, "technically_validated")
    assert r["measurement_status"] == "experimental"
    assert r["override"] == {"downgrade_only": True, "rationale": fitness.D26_RATIONALE, "actor": "Owner"}
    fitness.check_record(r, decided("technically_validated"))  # FT-01 / FT-08: a permitted downgrade


@pytest.mark.determinism
@pytest.mark.parametrize("origin,status", [("real_natural", "experimental"), ("real_natural", "unsuitable_under_tested_conditions"),
                                           ("real_staged", "not_yet_assessable"), ("synthetic_rendered", "experimental")])
def test_other_statuses_and_synthetic_rows_are_unchanged(origin, status):
    r = row(origin, status)
    assert r["measurement_status"] == status and r["override"] is None  # downgrade-only: nothing is raised


@pytest.mark.determinism
def test_exploratory_report_line():
    manifest = {"export_class": "research", "contract": "E-1.2.12", "exploratory": True}
    text = report.render(manifest, "research", "R", [])
    assert text.splitlines()[0] == EXPLORATORY_NOTE == "exploratory; frame-quality rules provisional"
    assert EXPLORATORY_NOTE not in report.render({**manifest, "exploratory": False}, "research", "R", [])


@pytest.mark.determinism
def test_real_origin_report_requires_the_exploratory_flag():
    manifest = {"export_class": "research", "contract": "E-1.2.12", "data_origins": ["real_natural"]}
    with pytest.raises(ContractError):
        report.render(manifest, "research", "R", [])
