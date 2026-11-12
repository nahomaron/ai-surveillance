"""Appendix T T11.1 (contract E-1.2.9; D-12): provider-conditional borderline flags. CT-T11-01 and CT-T11-02.
Expected values are hand calculations written beside each case."""
import dataclasses

import pytest

from rq1.events import s5

from test_t10 import CLR, R1, RULES, build_s5, flags_for, s4_of, s5_config

NO_R3 = dataclasses.replace(RULES, conflict=())
PRED_1_0 = {"predicted": [{"motion_model_id": "constant_velocity", "horizon_s": 2.0, "pred_min_clearance_m": 1.0, "sigma_m": None}]}

# One case per T11.1 bullet: (data, provider enabled, provider disabled, flags when enabled, flags when disabled).
# Baseline frames (test_t10.synthetic_s4) set no flag; each case changes frame 5 only. k_sigma = 2.
CASES = {
    # |1.95 - d_p 2.0| = 0.05 <= 2 x 0.05: only if the P provider is R2.
    "d_p": (dict(pair={5: {"clearance_m": 1.95}}), RULES, R1, [CLR], []),
    # |0.05 - k_img 0.05| = 0 <= 0: only if the P provider is R1.
    "k_img": (dict(pair={5: {"image_gap_norm": 0.05}}), R1, RULES, [CLR], []),
    # |1.0 - d_pc 1.0| = 0 <= 2 x 0 (sigma_pred null): only if R3 is enabled.
    "d_pc": (dict(pair={5: PRED_1_0}), RULES, NO_R3, [CLR], []),
    # |0.35 - v_min 0.3| = 0.05 <= 2 x 0.05: only if R2 (the M provider) is enabled.
    "v_min": (dict(fork={5: (0.35, 0.05)}), RULES, R1, ["speed_near_v_min"], []),
}


@pytest.mark.determinism
@pytest.mark.parametrize("bullet", sorted(CASES))
def test_ct_t11_01_bullet_applies_only_with_its_provider(bullet):
    data, enabled, disabled, flags_on, flags_off = CASES[bullet]
    assert flags_for(rules=enabled, **data) == flags_on
    assert flags_for(rules=disabled, **data) == flags_off


@pytest.mark.determinism
@pytest.mark.parametrize("rules", [RULES, R1, NO_R3])
def test_ct_t11_01_minclr_and_ca_bullets_apply_in_every_configuration(rules):
    # Classification parameters (d_nm, k_sigma), so no provider condition (T11.1).
    # Minimum clearance 0.55: |0.55 - d_nm 0.5| = 0.05 <= 2 x 0.05.
    assert flags_for(pair={5: {"clearance_m": 0.55}}, rules=rules) == [CLR]
    # Clearance at CA 0.08: |0.08| <= 2 x 0.05; minclr 0.08 is 0.42 from d_nm, so only the CA bullet fires.
    assert flags_for(pair={5: {"clearance_m": 0.08}}, rules=rules) == [CLR]


@pytest.mark.determinism
@pytest.mark.parametrize("rules", [RULES, R1, NO_R3])
def test_ct_t11_01_footprint_flag_unchanged(rules):
    assert flags_for(pair={5: {"borderline_flags": ["footprint_orientation_unknown"]}}, rules=rules) == ["footprint_orientation_unknown"]


# CT-T11-02: configurations that differ only in a disabled provider's parameters. Each pair uses a parameter that belongs to
# the disabled provider alone. v_min and w_e are read outside their provider (T9.2, T9.6, T10.3(c)) and are left to CR-012.
PAIRS = {
    "R2 disabled, d_p": (R1, dict(d_p=1.5)),
    "R1 disabled, k_img": (RULES, dict(k_img=0.2)),
    "R3 disabled, d_pc and tau": (NO_R3, dict(d_pc=0.5, tau=3.0)),
    "R5 disabled, e_turn, e_acc, e_dec": (dataclasses.replace(RULES, r5=False), dict(e_turn=0.1, e_acc=0.1, e_dec=0.1)),
}


@pytest.mark.determinism
@pytest.mark.parametrize("name", sorted(PAIRS))
@pytest.mark.parametrize("scene", ["N2-G2", "N2-G3"])
def test_ct_t11_02_disabled_provider_parameters_do_not_change_the_payload(name, scene):
    rules, change = PAIRS[name]
    params = dataclasses.replace(s5_config().params, r5_enabled=rules.r5)
    a_cfg = s5_config(rules=rules, params=params)
    b_cfg = s5_config(rules=dataclasses.replace(rules, **change), params=params)
    s1, s4 = s4_of(scene)
    a, b = build_s5(s1, s4, a_cfg), build_s5(s1, s4, b_cfg)
    assert s5.config_id(a_cfg) != s5.config_id(b_cfg)  # recorded in the rule_configuration record (AR-40 item 3)
    assert a.artifact_id != b.artifact_id  # through the specification's configuration ID
    assert a.payload_sha256 == b.payload_sha256  # but no role in S5 output (T11.1)
