"""T-15 part B: reports (F.1 A2 CT-X-04; A5.1 RV-02, RV-04; Appendix T T12.2, T12.4, CT-E-28; CLAUDE.md wording rules)."""
import pytest

from rq1.evaluation import event_metrics as em
from rq1.export import obx, report
from rq1.fixtures import identity_rows as rows
from rq1.ids import artifact
from rq1.ids.artifact import Spec
from rq1.schema.errors import ContractError

FIXTURE = {"export_class": "fixture_verification", "contract": "E-1.2.10"}
RESEARCH = {"export_class": "research", "contract": "E-1.2.10"}


def test_ct_x_04_banner_and_templates():
    text = report.render(FIXTURE, "fixture", "M0 fixture report", [])
    assert text.splitlines()[0] == "FIXTURE VERIFICATION — NOT RESEARCH RESULTS"  # EXP-4 fixed banner
    with pytest.raises(ContractError) as exc:
        report.render(FIXTURE, "research", "M0", [])  # research template on a fixture export
    assert exc.value.code == "ERR-EXPORT-CLASS"
    with pytest.raises(ContractError):
        report.render(RESEARCH, "fixture", "M1a", [])  # and the reverse (EXP-3)
    assert "FIXTURE VERIFICATION" not in report.render(RESEARCH, "research", "M1a report", [])


@pytest.mark.parametrize("line", [
    "Two collisions were found.", "The system found a near miss.", "Observed contact at frame 12.", "Contact occurred at CA.",
    "The detector was validated on SDG.", "There were 3 interactions.", "One physical interaction per episode.",
    "Site safety score 0.4.", "OSHA log linkage.",
    "Near misses were observed in window 3.", "A near-miss occurred.", "The system validated the event.",
])
def test_wording_rules_flag(line):
    assert report.lint(line) != []


@pytest.mark.parametrize("line", [
    "One candidate near miss (NM, candidate).", "Contact state: suspected; contact cue true.", "contact_state = undetermined",
    "Status: technically_validated in scope X.", "| Empirically validated (scope) |", "4 candidate events (scenario_count).",
    # Pass cases required by the Architect's ruling on AR-46 item 4:
    "No near misses were observed.", "no near miss was found in this window", "candidate near miss", "technically_validated",
])
def test_wording_rules_allow(line):
    assert report.lint(line) == []


def test_render_refuses_a_wording_violation():
    with pytest.raises(ContractError) as exc:
        report.render(FIXTURE, "fixture", "M0", [("Results", ["The pipeline detected a collision."])])
    assert exc.value.code == "ERR-INVARIANT"


def test_rv_02_and_rv_04_conformance_section():
    rows_ok = [{"metric_id": "EV-M1", "reference_class": "rule_conformance", "claim_level": "none", "value": 1.0},
               {"metric_id": "GV-01", "reference_class": "independent_perceptual_geometric", "claim_level": "L1", "value": 0.1}]
    title, body = report.conformance_section(rows_ok)
    assert title == "Implementation conformance" and body[0] == report.RV04_CAVEAT
    assert body[2:] == ["- EV-M1: 1.0 (claim level none)"]  # only rule-conformance rows
    text = report.render(FIXTURE, "fixture", "M0", [(title, body)])  # the fixed caveat is allowed
    assert "Implementation conformance" in text
    with pytest.raises(ContractError):
        report.conformance_section([{**rows_ok[0], "claim_level": "L2"}])  # RV-02
    assert any(i.startswith("RV-04") for i in report.lint("## Implementation conformance\nThis demonstrates hazard identification."))


def test_ev_m10_section_labels():
    title, body = report.ev_m10_section({"EV-M2": 1 / 3, "EV-M7": 2.0}, {"label": em.SENSITIVITY_LABEL, "EV-M2": 0.5, "EV-M7": 1.0},
                                        {"weighted": {"non_abstained": 1.0, "abstained": 1.0}})
    text = "\n".join(body)
    assert "sensitivity_excluding_unobservable_overlap: EV-M2 0.5" in text and "Headline EV-M2" in text
    assert body[-1] == "These events are neither confirmed nor refuted by the reference."
    report.render(FIXTURE, "fixture", "M0", [(title, body)])


def test_reference_visibility_assumed_is_printed():
    rec = {"metric_id": "CM-01", "support_basis": "detected", "stratum": {"physical_identity_id": "p1"}, "value": 0.6}
    _, body = report.completeness_section([rec], visibility_assumed=True)
    assert body[0] == "Note: reference visibility assumed."
    _, body = report.completeness_section([rec], visibility_assumed=False)
    assert "reference visibility assumed" not in "\n".join(body)
    _, body = report.completeness_section([{**rec, "metric_id": "CM-08"}], visibility_assumed=True)
    assert "reference visibility assumed" not in "\n".join(body)  # CM-08 needs no reference


def test_status_board():
    title, body = report.status_board([{"item": "S5 event engine", "status": "verified"}, {"item": "OBX export", "status": "implemented"}])
    assert title == "Status board" and "| S5 event engine | Verified | — |" in body
    with pytest.raises(ContractError):
        report.status_board([{"item": "x", "status": "empirically_validated", "scope": None, "data_origin": "real_natural"}])
    with pytest.raises(ContractError):
        report.status_board([{"item": "x", "status": "empirically_validated", "scope": "E1 SDG", "data_origin": "synthetic_rendered"}])
    _, body = report.status_board([{"item": "x", "status": "empirically_validated", "scope": "site A, calibrated", "data_origin": "real_natural"}])
    report.render(RESEARCH, "research", "M2", [("Status board", body)])


def test_counts_are_scenario_counts_not_interactions():
    rows_ = [{"scope_type": "recording", "scope_id": "rec_x", "scenario": "S_VIEW", "label": "all", "n_events": 2, "wording": "scenario_count",
              "assumptions": [{"assumption": a, "status": "unverified"} for a in ("A1", "A2", "A3")]}]
    title, body = report.counts_section(rows_)
    assert "2 candidate events (scenario_count; A1 unverified, A2 unverified, A3 unverified)" in body[-1]
    report.render(FIXTURE, "fixture", "M0", [(title, body)])


@pytest.mark.determinism
def test_ct_e_28_lineage_to_source_file():
    sha = "ab" * 32
    spec = lambda stage, cfg, inputs: Spec(stage, "E-1.2.10", "f", "f", cfg, inputs, {})
    s0 = artifact.build_artifact(spec("S0", (), ()), {"source_file": [rows.row("source_file", sha256=sha)]})
    s5 = artifact.build_artifact(spec("S5", ("rcf_" + "a" * 26,), (s0.artifact_id,)), {"episode": [rows.episode("pow_" + "a" * 26, 0)]})
    s8 = artifact.build_artifact(spec("S8", ("evc_" + "a" * 26, "spm_" + "a" * 26), (s5.artifact_id,)), {"completeness_record": [rows.row("completeness_record")]})
    store = {a.artifact_id: a for a in (s0, s5, s8)}
    assert obx.check_lineage([s8.artifact_id, s5.artifact_id], store) == []  # every metric row's artifact reaches src_
    orphan = artifact.build_artifact(spec("S8", ("evc_" + "b" * 26, "spm_" + "a" * 26), ()), {"completeness_record": [rows.row("completeness_record")]})
    assert obx.check_lineage([orphan.artifact_id], {**store, orphan.artifact_id: orphan}) == [orphan.artifact_id]
