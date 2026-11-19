"""D-47 item 3: N9 rule tests on the unmatched BL-6 events (false and duplicate alerts) of columns C and C'.

Rules as applied to an unmatched system event (F.1 N9; F.1 A5.2 line "Event matching"; FX-ID-8 as tested in
`tests/evaluation/test_t14_attribution.py`; AR-42 items 1, 2 and 4, accepted):
  1 evidence_unavailable: coverage at the event's closest-approach (CA) frame is not usable (reference observability is
    not applicable to an event with no reference and is passed as observable, as in the FX-ID-8 test);
  2 perception: one of the event's two tracks has no reference object of its class with IoU >= iou_cm within +-n_miss frames
    of the event's CA frame (AR-42 item 1);
  3 tracking: the event's two tracks are not both `matched` at the event's CA frame (FX-ID-8);
  4 geometry, 5 event_reasoning: not evaluated (CR-029: no definition of their inputs on the detector path);
  6 linkage: M2 only; 7 reference_ambiguity: not applicable (no reference): not evaluated.
Hand-built cases (iou_cm 0.5, n_miss 5, CA frame 10; person track "A", forklift track "B"; reference identities p, f):
  a. coverage `unusable` at frame 10                                        -> evidence_unavailable
  b. A's boxes overlap no reference person within frames 5..15             -> perception (tracking also fails: secondary)
  c. A and B overlap p and f at frame 10 (IoU 1), but B is not matched there -> tracking
  d. A and B overlap p and f and both are matched at frame 10              -> unresolved; 4 and 5 not_evaluated
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/m1b"))
import n9_pilot as n9  # noqa: E402

P, F = (0.0, 0.0, 10.0, 20.0), (50.0, 0.0, 90.0, 30.0)
FAR = (500.0, 500.0, 510.0, 520.0)


def boxes(person_box, forklift_box):
    return {10: [("A", "person", person_box), ("B", "forklift", forklift_box)]}


REF = {10: [("p", "person", P), ("f", "forklift", F)]}


def row(track, status):
    return {"track_id": track, "frame_index": 10, "status": status, "physical_identity_id": None}


def test_a_evidence_unavailable():
    got = n9.diagnose_unmatched(("A", "B"), 10, "unusable", REF, boxes(P, F), [row("A", "matched"), row("B", "matched")])
    assert got["primary_stage"] == "evidence_unavailable"


def test_b_perception():
    got = n9.diagnose_unmatched(("A", "B"), 10, "usable", REF, boxes(FAR, F), [row("A", "unmatched_system"), row("B", "matched")])
    assert (got["primary_stage"], got["secondary_factors"]) == ("perception", ["tracking"])


def test_c_tracking():
    got = n9.diagnose_unmatched(("A", "B"), 10, "usable", REF, boxes(P, F), [row("A", "matched"), row("B", "ambiguous")])
    assert (got["primary_stage"], got["secondary_factors"]) == ("tracking", [])


def test_d_unresolved_with_rules_4_and_5_not_evaluated():
    got = n9.diagnose_unmatched(("A", "B"), 10, "usable_degraded", REF, boxes(P, F), [row("A", "matched"), row("B", "matched")])
    assert got["primary_stage"] == "unresolved"
    r = got["rule_test_results"]
    assert (r["evidence_unavailable"], r["perception"], r["tracking"]) == ("pass", "pass", "pass")
    assert r["geometry"] == r["event_reasoning"] == "not_evaluated"


def test_n_miss_is_the_preregistered_value():
    assert (n9.N_MISS, n9.IOU_CM) == (5, 0.5)  # docs/preregistration_FROZEN.md: iou_cm / n_miss = 0.5 / 5 frames
