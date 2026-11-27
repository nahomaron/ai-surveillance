"""D-66 diagnostic (post hoc, tuning cameras only, selects nothing): which rule input was undetermined on each IE event.
Hand-made frames; expected values by hand from the engine's IE rule (engine._episode):
IE = Q at the CA frame not 1, or insufficient-Q time > o_max * span, or contact not_assessable, or (K = 2 and H or PC)."""
import sys
from pathlib import Path

import pytest

from rq1.events import engine

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/v2"))
import ie_inputs_diag as d  # noqa: E402

PARAMS = engine.Params(m_gap=3, t_min=0.3, w_post=1.5, d_nm=0.5, k_sigma=2.0, o_max=0.25, g_max=45, w_e=1.0, k_c=1.5,
                       k_c_turn=1.5, r5_enabled=True, e_turn=1.5, e_acc=1.0, e_dec=1.0, bands=())
CALM = engine.Rates(person_speed_change=0.1, forklift_decel=0.1, person_turn_rate=0.1)


def frames(Q, M, R4, E, rates):
    out = []
    for i in range(5):
        c_by = {"R3": 0} if R4 is None else {"R3": 0, "R4": R4[i]}
        out.append(engine.FrameFlags(i, 0.1 * i, 0.1, P=1, M=M[i], C_by=c_by, E=E[i], Q=Q[i], rates=rates[i]))
    return out


def ep(ca, k, contact, ie, x=True, c=False, e_ep=1, minclr=0.2):
    return {"start_frame": 0, "end_frame_excl": 5, "attr_end_frame_excl": 5, "span_s": 0.5, "closest_approach_frame": ca,
            "K": k, "X_ep": x, "C_ep": c, "E_ep": e_ep, "minclr_m": minclr, "contact_state": contact, "lbl_IE": ie}


def test_k_undetermined_with_every_input_unknown_somewhere():
    f = frames(Q=[1, 0, 1, 1, 1], M=[1, 2, 1, 1, 1], R4=[0, 0, 0, 2, 0], E=[0, 0, 2, 0, 0], rates=[CALM, CALM, None, CALM, CALM])
    a = d.attribute(f, ep(ca=2, k=2, contact="undetermined", ie=True, e_ep=2, minclr=None), PARAMS)
    # CA frame 2 has Q 1; insufficient time 0.1 s <= 0.25 * 0.5 = 0.125 s; contact assessable; K 2 with H: only the K clause
    assert a["clauses"] == {"coverage_at_ca": False, "coverage_share": False, "contact_not_assessable": False, "k_undetermined": True}
    assert a["k_parts"] == {"r5_unknown": True, "clearance_unknown": True}  # E_ep 2, minclr null
    # M 2 on frame 1, R4 2 on frame 3, E 2 on frame 2, rates None at CA (cue 2), Q 0 on frame 1
    assert a["undetermined"] == {"M": True, "R4": True, "R5": True, "contact_cue": True, "coverage": True}


def test_coverage_at_ca_and_inputs_not_enabled():
    f = frames(Q=[1, 0, 0, 1, 1], M=[1] * 5, R4=None, E=[0] * 5, rates=[CALM] * 5)
    p = engine.Params(**{**PARAMS.__dict__, "r5_enabled": False})
    a = d.attribute(f, ep(ca=1, k=1, contact="undetermined", ie=True, e_ep=0), p)
    # CA frame 1 has Q 0; insufficient time 0.2 s > 0.125 s; K 1: coverage clauses only
    assert a["clauses"] == {"coverage_at_ca": True, "coverage_share": True, "contact_not_assessable": False, "k_undetermined": False}
    assert a["k_parts"] is None
    # R4 not in the configuration, R5 off: not enabled (None); calm rates at CA: cue 0 (determined)
    assert a["undetermined"] == {"M": False, "R4": None, "R5": None, "contact_cue": False, "coverage": True}


def test_no_ca_frame_is_coverage_and_cue_unknown():
    f = frames(Q=[1] * 5, M=[1] * 5, R4=[0] * 5, E=[0] * 5, rates=[CALM] * 5)
    a = d.attribute(f, ep(ca=None, k=1, contact="not_assessable", ie=True), PARAMS)
    assert a["clauses"]["coverage_at_ca"] and a["clauses"]["contact_not_assessable"]
    assert a["undetermined"]["contact_cue"] is True and a["undetermined"]["coverage"] is False


def test_disagreement_with_the_stored_label_stops():
    f = frames(Q=[1] * 5, M=[1] * 5, R4=[0] * 5, E=[0] * 5, rates=[CALM] * 5)
    with pytest.raises(SystemExit, match="STOP"):
        d.attribute(f, ep(ca=2, k=1, contact="none_observed", ie=True), PARAMS)  # no clause holds, yet stored IE


def test_summary_counts():
    rows = [{"clauses": {"coverage_at_ca": True, "k_undetermined": False}, "undetermined": {"M": True, "R4": None}},
            {"clauses": {"coverage_at_ca": True, "k_undetermined": True}, "undetermined": {"M": False, "R4": None}}]
    s = d.summarise(rows)
    assert s["ie_events"] == 2
    assert s["clauses"] == {"coverage_at_ca": 2, "k_undetermined": 1}
    assert s["undetermined"] == {"M": 1, "R4": "not enabled"}
    assert s["clause_combinations"] == {"coverage_at_ca": 1, "coverage_at_ca + k_undetermined": 1}
