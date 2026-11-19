"""Appendix T T22 (contract E-1.2.20), V-02 part A: the pure protocol rules in `rq1.review.protocol`.

Expected values are hand calculations recorded beside each test, or text retyped from T22.
"""
import pytest

from rq1.review import protocol as P
from rq1.schema.errors import ContractError


# --- T22.12 parameters and T22.5 value sets -------------------------------------------------------------------------

def test_parameters_are_the_t22_12_values():
    assert P.PARAMS == {"c_pad_s": 3.0, "n_batch": 60, "n_pilot": 20, "a_audit": 0.10}


def test_labels_and_confidence_scale():
    assert P.LABELS == ("ct", "nm", "ud", "not_hazardous", "unsure")
    assert P.CONFIDENCE == {1.0: "low", 2.0: "medium", 3.0: "high"}
    assert P.METHODS == ("agreement", "adjudicator", "consensus_meeting")
    assert P.STRATA == ("CT", "UD", "NM", "PC", "H", "O")


@pytest.mark.parametrize("value", [0.0, 1.5, 4.0, 2, "2.0", None, float("nan")])
def test_confidence_outside_the_scale_is_refused(value):
    with pytest.raises(ContractError) as e:
        P.check_confidence(value)
    assert e.value.code == "ERR-SPEC"


@pytest.mark.parametrize("value", [1.0, 2.0, 3.0])
def test_confidence_on_the_scale_is_accepted(value):
    assert P.check_confidence(value) == value


@pytest.mark.parametrize("text", ["", "   ", "\n", "...", "- -"])
def test_rationale_is_required(text):
    with pytest.raises(ContractError):
        P.check_rationale(text)


def test_label_outside_the_five_is_refused():
    with pytest.raises(ContractError):
        P.check_label("near_miss")


# --- T22.8 (b) mapping and status ----------------------------------------------------------------------------------

@pytest.mark.parametrize("g2,mapped", [("lbl_nm", "nm"), ("lbl_ud", "ud"), ("lbl_ct", "ct"), (None, "not_hazardous")])
def test_g2_mapping(g2, mapped):
    assert P.map_g2(g2) == mapped


@pytest.mark.parametrize("final,mapped,status", [
    ("unsure", "nm", "disputed"), ("unsure", "not_hazardous", "disputed"),
    ("nm", "nm", "confirmed"), ("not_hazardous", "not_hazardous", "confirmed"),
    ("ud", "nm", "rejected"), ("nm", "not_hazardous", "rejected"), ("ct", "ud", "rejected"),
])
def test_status_rule(final, mapped, status):
    assert P.status_for(final, mapped) == status


def test_g2_label_from_episode_flags():
    assert P.g2_from_flags(lbl_NM=True, lbl_UD=False, lbl_CT=False) == "lbl_nm"
    assert P.g2_from_flags(lbl_NM=False, lbl_UD=False, lbl_CT=False) is None
    with pytest.raises(ContractError):  # the three G2 labels are exclusive (section 6); two at once is not mapped
        P.g2_from_flags(lbl_NM=True, lbl_UD=True, lbl_CT=False)


# --- T22.7 (a) tier rule -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("a,b,tier1", [("nm", "nm", True), ("not_hazardous", "not_hazardous", True), ("unsure", "unsure", False),
                                       ("nm", "ud", False), ("unsure", "nm", False)])
def test_tier1_iff_same_label_and_neither_unsure(a, b, tier1):
    assert P.is_tier1(a, b) is tier1


# --- T22.4 clip window -------------------------------------------------------------------------------------------------

def test_clip_window_pads_and_clamps():
    # onset 5.0, I+ end 8.0, recording [0, 10]: [max(0, 5 - 3), min(10, 8 + 3)] = [2.0, 10.0]
    assert P.clip_window(5.0, 8.0, 0.0, 10.0, 3.0) == (2.0, 10.0)
    # onset 1.0: start clamps to 0.0; end 4.0 + 3.0 = 7.0
    assert P.clip_window(1.0, 4.0, 0.0, 10.0, 3.0) == (0.0, 7.0)


# --- T22.6 (a) allocation, hand calculations -------------------------------------------------------------------------

def test_allocation_no_ties_with_capping():
    # Strata of the T-21 SDG validation BL-6 frame: CT 7, UD 44, NM 30, PC 212, H 17, O 9; n = 60.
    # Equal share 60 / 6 = 10. CT (7) and O (9) are below it -> capped at size. Remaining 60 - 16 = 44 over 4 strata
    # = 11 each; no stratum is below 11 (H 17) -> UD, NM, PC, H get 11. Integral, so no remainder and no tie.
    sizes = {"CT": 7, "UD": 44, "NM": 30, "PC": 212, "H": 17, "O": 9}
    assert P.allocate(sizes, 60, seed=1) == {"CT": 7, "UD": 11, "NM": 11, "PC": 11, "H": 11, "O": 9}


def test_allocation_largest_remainder_with_seeded_ties():
    # Hand-made table: CT 2, UD 5, NM 9, PC 40, O 4 (H absent: size 0, not present); n = 20.
    # Share 20 / 5 = 4. CT (2) <= 4 -> 2; O (4) <= 4 -> 4. Remaining 14 over UD, NM, PC: share 14 / 3 = 4.667;
    # UD (5) > 4.667, so none capped. Floors 4, 4, 4 = 12; remainder 2. The three remainders are equal (0.667), so the
    # batch seed breaks the tie: two of UD, NM, PC get 5 and one gets 4.
    sizes = {"CT": 2, "UD": 5, "NM": 9, "PC": 40, "H": 0, "O": 4}
    outcomes = set()
    for seed in range(40):
        a = P.allocate(sizes, 20, seed=seed)
        assert a["CT"] == 2 and a["O"] == 4 and "H" not in a and sum(a.values()) == 20
        assert sorted((a["UD"], a["NM"], a["PC"])) == [4, 5, 5]
        assert a == P.allocate(sizes, 20, seed=seed)  # reproducible from the seed
        outcomes.add((a["UD"], a["NM"], a["PC"]))
    assert outcomes == {(4, 5, 5), (5, 4, 5), (5, 5, 4)}  # the tie really is broken by the seed


def test_allocation_capped_after_a_second_round():
    # CT 1, UD 3, NM 50; n = 30. Share 10: CT 1 capped; remaining 29 over UD, NM: 14.5: UD 3 capped;
    # remaining 26 for NM (50 > 26) -> NM 26. Total 30.
    assert P.allocate({"CT": 1, "UD": 3, "NM": 50}, 30, seed=7) == {"CT": 1, "UD": 3, "NM": 26}


def test_allocation_when_the_frame_is_smaller_than_the_batch():
    assert P.allocate({"CT": 1, "NM": 2}, 60, seed=3) == {"CT": 1, "NM": 2}


def _frame(sizes):
    return [{"target_id": f"ep_{s.lower()}{k:024d}", "stratum": s} for s, n in sizes.items() for k in range(n)]


def test_draw_is_without_replacement_sorted_and_reproducible():
    frame = _frame({"CT": 2, "UD": 5, "NM": 9, "PC": 40, "O": 4})
    alloc, ids = P.draw(frame, 20, seed=11)
    assert len(ids) == len(set(ids)) == 20 and ids == sorted(ids)
    by = {t["target_id"]: t["stratum"] for t in frame}
    assert {s: sum(1 for i in ids if by[i] == s) for s in alloc} == alloc
    assert P.draw(frame, 20, seed=11) == (alloc, ids)
    assert P.draw(frame, 20, seed=12)[1] != ids


def test_draw_excludes_given_targets():
    frame = _frame({"NM": 5, "PC": 5})
    excluded = {frame[0]["target_id"], frame[5]["target_id"]}
    _, ids = P.draw(frame, 60, seed=1, exclude=excluded)
    assert len(ids) == 8 and not excluded & set(ids)


# --- T22.6 (b) per-reviewer order --------------------------------------------------------------------------------------

def test_per_reviewer_order_differs_and_is_reproducible():
    ids = [f"ep_{k:026d}" for k in range(20)]
    a = P.reviewer_order(ids, 2026111901, "anr_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a01")
    b = P.reviewer_order(ids, 2026111901, "anr_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a02")
    assert sorted(a) == sorted(b) == ids
    assert a != b
    assert a == P.reviewer_order(list(reversed(ids)), 2026111901, "anr_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a01")  # input order irrelevant
    assert a != P.reviewer_order(ids, 2026111902, "anr_0193a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a01")


# --- T22.7 (d) audit sample size -------------------------------------------------------------------------------------

@pytest.mark.parametrize("n_tier1,n_audit", [(0, 0), (1, 1), (9, 1), (10, 1), (11, 2), (40, 4), (41, 5)])
def test_audit_count_is_ceiling_of_share(n_tier1, n_audit):
    # T22.14 (a): ceil(a_audit x n_tier1); FX-13e needs a 1-target tier1 set to be audited.
    ids = [f"ep_{k:026d}" for k in range(n_tier1)]
    sample = P.audit_sample(ids, 0.10, seed=5)
    assert len(sample) == n_audit and set(sample) <= set(ids) and sample == sorted(sample)
    assert sample == P.audit_sample(list(reversed(ids)), 0.10, seed=5)


# --- T22.10 (a) agreement --------------------------------------------------------------------------------------------

def test_agreement_statistics_hand_values():
    # Five targets. Reviewer 1: nm, nm, ud, not_hazardous, unsure. Reviewer 2: nm, ud, ud, not_hazardous, nm.
    # Five labels: p_o = 3/5 = 0.6. Marginals r1: nm 2, ud 1, nh 1, unsure 1; r2: nm 2, ud 2, nh 1.
    # p_e = (2*2 + 1*2 + 1*1 + 1*0) / 25 = 7/25 = 0.28. kappa = (0.6 - 0.28) / 0.72 = 0.4444...
    # Four labels (drop target 5, unsure): r1 nm nm ud nh, r2 nm ud ud nh. p_o = 3/4.
    # p_e = (2*1 + 1*2 + 1*1)/16 = 5/16. kappa = (0.75 - 0.3125) / 0.6875 = 0.63636...
    r1 = ["nm", "nm", "ud", "not_hazardous", "unsure"]
    r2 = ["nm", "ud", "ud", "not_hazardous", "nm"]
    k5, k4 = P.kappas(r1, r2)
    assert k5 == pytest.approx(0.32 / 0.72, abs=1e-12)
    assert k4 == pytest.approx(0.4375 / 0.6875, abs=1e-12)


def test_percentiles_of_review_time():
    # Linear interpolation (numpy default). Times 10, 20, 30, 40: median 25; P90 = 30 + 0.7 * 10 = 37.
    assert P.median_p90([40.0, 10.0, 30.0, 20.0]) == (25.0, 37.0)
    assert P.median_p90([None, None]) == (None, None)
    assert P.median_p90([None, 12.0]) == (12.0, 12.0)
