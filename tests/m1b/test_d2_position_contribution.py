"""D-53 step 2: the diagnostic position substitution (hand-made inputs)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../research/m1b"))
import d2_position_contribution as d2  # noqa: E402

POS = {(1, 0): {"xy": [1.0, 2.0], "cov": [0.0, 0.0, 0.0], "yaw": 0.3}, (1, 1): {"xy": [1.5, 2.0], "cov": [0.0, 0.0, 0.0], "yaw": 0.3},
       (2, 0): {"xy": [5.0, 5.0], "cov": [0.0, 0.0, 0.0]}}
CLS = {1: "forklift", 2: "person"}


def test_b_tune_supplies_no_position():
    assert d2.substitute(POS, CLS, None) == {}


def test_forklift_substitution_keeps_position_and_covariance_and_drops_yaw():
    out = d2.substitute(POS, CLS, "forklift")
    assert out == {(1, 0): {"xy": [1.0, 2.0], "cov": [0.0, 0.0, 0.0]}, (1, 1): {"xy": [1.5, 2.0], "cov": [0.0, 0.0, 0.0]}}
    assert "yaw" in POS[(1, 0)]  # the input is not modified


def test_person_substitution():
    assert d2.substitute(POS, CLS, "person") == {(2, 0): {"xy": [5.0, 5.0], "cov": [0.0, 0.0, 0.0]}}


def test_summary_sums_counts():
    z = {"f": 0, "c": 0, "abstained_miss": 0, "duplicate": 0, "u": 1.0}
    cams = [{"viewpoint": "ceiling", "ev": {"X": {"a": 4, "m": 2, "s": 5, "m_s": 2, **z}}},
            {"viewpoint": "eye_level", "ev": {"X": {"a": 6, "m": 1, "s": 1, "m_s": 1, **z}}}]
    s = d2.summarize(cams)
    # summed: recall 3/10, precision 3/6
    assert s["all"]["X"]["EV-M1"] == 0.3 and s["all"]["X"]["EV-M2"] == 0.5
    assert s["all"]["X"]["missed_references"] == 7 and s["all"]["X"]["unmatched_events"] == 3
    assert s["ceiling"]["X"]["EV-M1"] == 0.5
