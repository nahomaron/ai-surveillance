"""CT-T12-01: Appendix T T12.1 (contract E-1.2.10) shared parameters. Expected values are hand calculations written here."""
import dataclasses

import pytest

from rq1.events import engine, providers, s5
from rq1.events.engine import FrameFlags
from rq1.schema import validate
from rq1.schema.errors import ContractError

from test_t10 import PARAMS, RULES, SUBSTRATE, build_s5, s4_of, s5_config, synthetic_s4

OFF = dataclasses.replace(RULES, r5=False)
OFF_PARAMS = dataclasses.replace(PARAMS, r5_enabled=False)


def test_rule_configuration_holds_only_exclusive_parameters():
    record = s5.rule_configuration(s5_config())
    assert {p["provider_id"]: sorted(p["params"]) for p in record["providers"]} == {
        "R1": ["k_img"], "R2": ["d_p"], "R3": ["d_pc"], "R5": ["e_acc", "e_dec", "e_turn"]}
    assert record["classification"]["w_e_s"] == PARAMS.w_e == 1.0  # w_e: classification block
    assert record["substrate_config_id"] == s5.substrate_config_id(SUBSTRATE)  # v_min and tau: substrate_config
    assert validate.validate_row("rule_configuration", record) == []
    assert validate.validate_row("substrate_config", SUBSTRATE) == []


@pytest.mark.determinism
@pytest.mark.parametrize("scene", ["N2-G2", "N2-G3"])
def test_ct_t12_01_r5_exclusive_parameters_with_r5_disabled_leave_the_payload(scene):
    s1, s4 = s4_of(scene)
    a_cfg = s5_config(rules=OFF, params=OFF_PARAMS)
    b_cfg = s5_config(rules=dataclasses.replace(OFF, e_turn=0.1, e_acc=0.1, e_dec=0.1), params=OFF_PARAMS)
    a, b = build_s5(s1, s4, a_cfg), build_s5(s1, s4, b_cfg)
    assert s5.config_id(a_cfg) != s5.config_id(b_cfg) and a.payload_sha256 == b.payload_sha256


def test_ct_t12_01_w_e_changes_output_even_with_r5_disabled():
    # T9.6 W_CA: I = [0, 10) ends at CA = frame 9 (minimum clearance); Q = 0 on frames 4-9 and 1 on 10-14 (in I+).
    # w_e = 1.0: W_CA = frames with |t - 0.9| <= 0.5 = 4-14, which holds sufficient frames -> undetermined (Q = 0 at CA).
    # w_e = 0.15: W_CA = frames with |t - 0.9| <= 0.075 = frame 9 only (frames 8 and 10 are 0.1 s away), and Q = 0 there
    # -> not_assessable. R5 is disabled throughout, so the change comes from w_e in the classification block (T12.1).
    def run(w_e):
        frames = [FrameFlags(i, i / 10, 0.1, P=1 if i < 10 else 0, M=1 if i < 10 else 0, C_by={"R3": 0}, Q=0 if 4 <= i < 10 else 1,
                             clearance=1.0 - 0.05 * min(i, 9) + (0.2 if i > 9 else 0), sigma=0.05, overlap=0, closing_rate=-0.1) for i in range(20)]
        (ep,), _ = engine.run_pow(frames, dataclasses.replace(OFF_PARAMS, w_e=w_e))
        return ep["contact_state"]
    assert (run(1.0), run(0.15)) == ("undetermined", "not_assessable")


def test_ct_t12_01_v_min_changes_output():
    # Forklift speed 0.35 on every frame (synthetic S4, sigma 0): with v_min 0.3, M = 1 (0.35 > 0.3) and P = 1, so H;
    # with v_min 0.4, M = 0, so O. v_min is read through its single source, substrate_config.v_min.
    s4, frames, coverage = synthetic_s4(fork={i: (0.35, 0.0) for i in range(20)})
    labels = []
    for v_min in (0.3, 0.4):
        flags = providers.flag_frames(s4, dataclasses.replace(RULES, v_min=v_min), frames, coverage)
        (ep,), _ = engine.run_pow(flags, PARAMS)
        labels.append((ep["lbl_H"], ep["lbl_O"]))
    assert labels == [(True, False), (False, True)]


@pytest.mark.determinism
def test_t12_1_runtime_value_must_match_its_single_source():
    s1, s4 = s4_of("N2-G2")
    for change in (dict(v_min=0.4), dict(tau=3.0), dict(w_e=0.5)):
        with pytest.raises(ContractError) as exc:
            build_s5(s1, s4, s5_config(rules=dataclasses.replace(RULES, **change)))
        assert exc.value.code == "ERR-SPEC" and "T12.1" in str(exc.value)
    other = {**SUBSTRATE, "g_max": 10}  # S4 was built with SUBSTRATE, not this record
    with pytest.raises(ContractError):
        build_s5(s1, s4, s5_config(substrate=other))
