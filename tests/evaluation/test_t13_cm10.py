"""CT-T13-01: Appendix T T13.1 (contract E-1.2.11). CM-10 is basis-independent. Expected value is the T13.1 check."""
import pytest

from rq1.evaluation import completeness as cm
from rq1.export import report
from rq1.schema import validate


def t13_window():
    # T13.1 check: pair (p1, f1) co-visible on 20 frames (2.0 s); its POW (A, F) has insufficient pair-frames on 5 of them (0.5 s).
    rows = [{"frame_index": f, "track_id": t, "physical_identity_id": i, "status": "matched"} for f in range(20) for t, i in (("A", "p1"), ("F", "f1"))]
    frames = {f: ("insufficient" if f >= 15 else "detected") for f in range(20)}
    return cm.WindowFrames(support={f: 0.1 for f in range(20)}, ref_visible={f: {"p1": "person", "f1": "forklift"} for f in range(20)},
                           ref_present={f: {"p1", "f1"} for f in range(20)}, assoc=rows, track_class={f: {"A": "detected", "F": "detected"} for f in range(20)},
                           pows=[{"person_track": "A", "forklift_track": "F", "frames": frames}])


@pytest.mark.determinism
@pytest.mark.parametrize("basis_label", ["detected", "detected_plus_inferred"])
def test_ct_t13_01_cm_10_basis_independent(basis_label):
    got = cm.cm10(t13_window())[("p1", "f1")]
    assert (got["numerator"], got["denominator"], got["value"]) == (pytest.approx(0.5), pytest.approx(2.0), pytest.approx(0.25))  # 0.5 / 2.0
    stored = cm.record("rwn_" + "a" * 26, "CM-10", basis_label, {}, got, "none", 0.5, 1.0)
    assert stored["value"] == pytest.approx(0.25)  # the same value under either basis label


@pytest.mark.determinism
def test_cm_10_stored_with_detected_placeholder_and_reported_basis_independent():
    records = cm.cm10_records(t13_window(), "rwn_" + "a" * 26, "none", 0.5, 1.0)
    assert [r["support_basis"] for r in records] == ["detected"] and validate.validate_rows("completeness_record", records) == []
    _, body = report.completeness_section(records, visibility_assumed=False)
    assert "CM-10 (basis-independent" in body[0]


def test_t13_3_cm_06_and_cm_07_are_sum_and_count():
    recs = [{"metric_id": "CM-06", "support_basis": "detected", "stratum": {"pair": "p1|f1"}, "value": 5.0},
            {"metric_id": "CM-07", "support_basis": "detected", "stratum": {"pair": "p1|f1", "start_frame": "0"}, "value": 2},
            {"metric_id": "CM-01", "support_basis": "detected", "stratum": {}, "value": 0.6}]
    _, body = report.completeness_section(recs, visibility_assumed=False)
    text = "\n".join(body)
    assert "CM-06 (detected, {'pair': 'p1|f1'}): sum (s) 5.0" in text and "CM-07 (detected, {'pair': 'p1|f1', 'start_frame': '0'}): count 2" in text
    assert "proportion" not in text
