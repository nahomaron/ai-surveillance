"""T-09: E-1.2.1 section 6 with Appendix N1 (flag level) and N2 (every frame, Appendix T T9.1); contract E-1.2.7."""
import copy
import dataclasses
import json
import random
from pathlib import Path

import pytest

from rq1.events import engine, kleene, labels, providers
from rq1.fixtures import synthetic_s1
from rq1.ids.artifact import Spec
from rq1.schema import vr_rules
from rq1.substrate import builder, oracle

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "records"
V = json.loads((FIX / "TEST-ONLY-PARAMETERS.json").read_text())["parameters"]  # Package F section 3 TEST-ONLY values
PARAMS = engine.Params(m_gap=V["m_gap"], t_min=V["t_min"], w_post=V["w_post"], d_nm=V["d_nm"], k_sigma=V["k_sigma"], o_max=V["o_max"], g_max=V["g_max"],
                       w_e=V["w_e"], k_c=V["k_c"], k_c_turn=V["k_c_turn"], r5_enabled=True, e_turn=V["e_turn"], e_acc=V["e_acc"], e_dec=V["e_dec"],
                       bands=tuple(zip([None] + V["band_edges_m"], V["band_edges_m"] + [None])))  # (None,0), (0,0.5), ..., (4,None)


def n1(row):
    return json.loads((FIX / f"N1-{row}.json").read_text())


def tri(word):
    return {"yes": 1, "no": 0, "unknown": 2}[word]


def n1_frames(inputs):
    exp = lambda key: engine.expand(inputs[key])
    p, m, c, e, q = exp("P"), exp("M"), exp("C_any"), exp("E"), exp("Q")
    frames = []
    for i in range(inputs["n_frames"]):
        lo, hi = inputs.get("clearance_frames", [0, inputs["n_frames"]])
        measured = inputs.get("minclr_m") is not None and lo <= i < hi  # T10: frames 0-11 (Appendix T T9.9); T11: frames 0-9
        frames.append(engine.FrameFlags(frame_index=i, t=i / 10, support=0.1, P=p[i], M=m[i], C_by={"R3": c[i]}, E=e[i], Q=q[i],
                                        clearance=inputs["minclr_m"] if measured else None, sigma=inputs.get("minclr_sigma_m") if measured else None))
    return frames


def run_n1(row):
    fixture = n1(row)
    inputs = fixture["inputs"]
    frames = n1_frames(inputs)
    # The N1 row states its CA frame (T10, T11), overlap and cue at CA (AR-37). Where no CA frame is stated, T9.5 picks it.
    # Usable frames around CA are not an input: T9.6 derives them from Q over W_CA.
    ca = None
    if inputs.get("ca_frame") is not None:
        ca = labels.CaInputs(frame_index=inputs["ca_frame"], overlap=tri(inputs["overlap_at_ca"]), cue=inputs["contact_cue"] == "yes")
    elif "overlap_at_ca" in inputs:
        ca = labels.CaInputs(frame_index=engine.closest_approach(frames)[0].frame_index, overlap=tri(inputs["overlap_at_ca"]), cue=inputs["contact_cue"] == "yes")
    return engine.run_pow(frames, PARAMS, ca_inputs=ca), fixture["expected"]


@pytest.mark.determinism
@pytest.mark.parametrize("row", [f"T{i}" for i in range(1, 12)])
def test_ct_e_09_n1_truth_table(row):
    (episodes, discarded), expected = run_n1(row)
    assert len(episodes) == 1 and discarded == []
    ep = episodes[0]
    got = [name for name in ("O", "H", "PC", "NM", "UD", "CT", "IE") if ep[f"lbl_{name}"]]
    assert (ep["contact_state"], ep["K"], got, ep["summary_label"], ep["review_route"]) == (
        expected["contact_state"], expected["K"], expected["labels"], expected["summary_label"], expected["review_route"])
    assert vr_rules.check_episode_labels(ep) == []  # CL-INV-01 to 11


@pytest.mark.determinism
def test_ct_e_09_n1_t12_two_episodes():
    (episodes, discarded), expected = run_n1("T12")
    got = [(e["start_frame"], e["end_frame_excl"], round(e["span_s"], 9), [n for n in ("O", "H", "PC") if e[f"lbl_{n}"]]) for e in episodes]
    assert got == [(x["start_frame"], x["end_frame_excl"], x["span_s"], x["labels"]) for x in expected["episodes"]] and discarded == []


@pytest.mark.determinism
def test_ct_e_09_n1_t13_discarded():
    (episodes, discarded), expected = run_n1("T13")
    assert episodes == []
    assert [{"start_frame": d["start_frame"], "end_frame_excl": d["end_frame_excl"], "span_s": round(d["span_s"], 9), "discard_reason": d["discard_reason"]}
            for d in discarded] == expected["discarded"]


def test_kleene_logic():
    assert [kleene.k_and(a, b) for a, b in ((1, 1), (1, 2), (0, 2), (2, 2))] == [1, 2, 0, 2]
    assert [kleene.k_or(a, b) for a, b in ((0, 0), (0, 2), (1, 2), (2, 2))] == [0, 2, 1, 2]
    assert kleene.any_of([0, 2, 0]) == 2 and kleene.any_of([0, 1, 2]) == 1 and kleene.any_of([]) == 0


def test_providers_section_6_0():
    assert providers.r1_p(0.04, k_img=0.05) == 1 and providers.r1_p(0.05, 0.05) == 0 and providers.r1_p(None, 0.05) == 2
    assert providers.r2_p(1.99, d_p=2.0) == 1 and providers.r2_p(2.0, 2.0) == 0 and providers.r2_p(None, 2.0) == 2
    assert providers.r2_m(0.31, v_min=0.3) == 1 and providers.r2_m(0.3, 0.3) == 0 and providers.r2_m(None, 0.3) == 2
    pred = [{"motion_model_id": "constant_velocity", "horizon_s": 2.0, "pred_min_clearance_m": 0.9}]
    assert providers.r3_c(pred, d_pc=1.0, tau=2.0) == 1 and providers.r3_c([], 1.0, 2.0) == 2 and providers.r3_c(pred, 1.0, 1.0) == 2
    assert [providers.g(s) for s in ("measured", "unmeasurable_uncalibrated", "unmeasurable_occluded")] == [1, 0, 2]
    assert providers.q("sufficient") == 1 and providers.q("insufficient") == 0


@pytest.mark.determinism
def test_lifecycle_w_post_extends_attributes_only():
    frames = [engine.FrameFlags(i, i / 10, 0.1, P=1 if i < 5 else 0, M=0, C_by={"R3": 0}, E=1 if i == 12 else 0, Q=1, clearance=1.0, sigma=0.05) for i in range(30)]
    (episodes, _), = [engine.run_pow(frames, PARAMS)]
    ep = episodes[0]
    assert (ep["start_frame"], ep["end_frame_excl"], ep["attr_end_frame_excl"]) == (0, 5, 15)  # I+ ends at 0.5 + w_post 1.0 = 1.5 s
    assert ep["E_ep"] == 1  # the evasive frame 12 lies in I+, outside I


@pytest.mark.determinism
@pytest.mark.parametrize("seed", range(300))
def test_ct_e_10_cl_inv_property(seed):
    rng = random.Random(seed)
    n = rng.randint(3, 25)
    pick = lambda: rng.choice([0, 1, 2])
    frames = [engine.FrameFlags(i, i / 10, 0.1, P=pick(), M=pick(), C_by={"R3": pick(), "R4": pick()}, E=pick(), Q=rng.choice([0, 1]),
                                clearance=rng.choice([None, rng.uniform(-0.3, 3.0)]), sigma=rng.choice([None, 0.05])) for i in range(n)]
    ca = labels.CaInputs(frame_index=rng.randrange(n), overlap=pick(), cue=rng.random() < 0.5)
    episodes, _ = engine.run_pow(frames, PARAMS, ca_inputs=ca if rng.random() < 0.5 else None)
    for ep in episodes:
        assert vr_rules.check_episode_labels(ep) == [], ep


@pytest.mark.determinism
def test_ct_e_13_one_episode_two_provider_columns():
    inputs = n1("T5")["inputs"]
    frames = n1_frames(inputs)
    for f in frames:
        f.C_by["R4"] = 1 if 5 <= f.frame_index < 8 else 0  # stub R4 provider (Package F WP-06)
    episodes, _ = engine.run_pow(frames, PARAMS)
    assert len(episodes) == 1 and episodes[0]["C_ep_by_provider"] == {"R3": False, "R4": True}


# Pipeline flags from S4 (N2): interior frames; the first and last frame are CR-008 item 7.
PERSON = {"class": "person", "shape": "disc", "radius_m": 0.30, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}
FORK = {"class": "forklift", "shape": "oriented_rect", "length_m": 2.0, "width_m": 1.0, "sigma_length_m": 0.0, "sigma_width_m": 0.0, "anchor": "centre"}


def s4_for(name):
    fixture = json.loads((FIX / f"{name}.json").read_text())
    n = len(fixture["expected"]["clearance_m"])
    person = fixture["inputs"]["person_xy"]
    fx = {"N2-G1": lambda t: 0.0, "N2-G2": lambda t: -2.5 + t, "N2-G3": lambda t: 1.5 * t}[name]
    positions = {**{(1, i): {"xy": person, "cov": [0.0025, 0.0, 0.0025]} for i in range(n)},
                 **{(2, i): {"xy": [fx(i / 10), 0.0], "cov": [0.0025, 0.0, 0.0025], "yaw": 0.0} for i in range(n)}}
    s1 = synthetic_s1.build(n)
    truth = [{"local_id": 1, "class": "person", "points": [{"frame_index": i, "bbox": [100.0, 100.0, 140.0, 200.0], "state": "tracked"} for i in range(n)]},
             {"local_id": 2, "class": "forklift", "points": [{"frame_index": i, "bbox": [300.0, 100.0, 500.0, 220.0], "state": "tracked"} for i in range(n)]}]
    s3 = oracle.OracleTrackSource().tracks(s1["frame"][0]["recording_id"], truth, s1["frame"], Spec("S3", "E-1.2.6", "f", "f", ("orc_" + "a" * 26,), (), {}))
    cfg = builder.SubstrateConfig(15, 0.3, 0.5, 2.0, {"forklift"}, {"person": PERSON, "forklift": FORK}, {"person": "fpp_" + "p" * 26, "forklift": "fpp_" + "f" * 26},
                                  {"bsc_" + "a" * 26: [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, None)]}, 0.5)
    s4 = builder.SubstrateBuilder().build(s1, s3, positions, None, cfg, Spec("S4", "E-1.2.6", "f", "f", ("gcf_" + "a" * 26, "sbc_" + "a" * 26), (s3.artifact_id,), {}))
    return fixture["expected"], s4, n, s1


RULES = providers.RuleParams(p_provider="R2", k_img=V["k_img"], d_p=V["d_p"], v_min=V["v_min"], d_pc=V["d_pc"], ttc_max=V["ttc_max"], pet_max=V["pet_max"], tau=V["tau"], conflict=("R3",),
                             r5=True, w_e=V["w_e"], e_turn=V["e_turn"], e_acc=V["e_acc"], e_dec=V["e_dec"], k_sigma=V["k_sigma"])
R1_RULES = dataclasses.replace(RULES, p_provider="R1")


@pytest.mark.determinism
@pytest.mark.parametrize("name", ["N2-G1", "N2-G2", "N2-G3"])
def test_n2_flags_every_frame(name):
    # Appendix T T9.1 (E-1.2.7): with the shifted velocity window, N2 holds as written on every frame, ends included.
    expected, s4, n, s1 = s4_for(name)
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    for key in ("P", "M", "C_by_R3"):
        got = [(f.C_by["R3"] if key == "C_by_R3" else getattr(f, key)) for f in flags]
        assert got == expected[key], (name, key)


@pytest.mark.determinism
def test_ct_e_14_early_trigger_g3():
    _, s4, _, s1 = s4_for("N2-G3")
    flags = providers.flag_frames(s4.tables, RULES, s1["frame"], s1["coverage_segment"])
    episodes, _ = engine.run_pow(flags, PARAMS)
    assert not any(f.P == 1 for f in flags) and episodes[0]["lbl_PC"]  # opens on the conflict, before any P frame
    # T9.1 check (E-1.2.7): G3 has a velocity on every frame, so N2 holds as written: episode frames 0-9, minclr 2.35 m.
    assert (episodes[0]["start_frame"], episodes[0]["end_frame_excl"], episodes[0]["minclr_m"]) == (0, 10, pytest.approx(2.35, abs=1e-6))


@pytest.mark.determinism
def test_ct_e_12_substrate_unchanged_by_events():
    _, s4, _, s1 = s4_for("N2-G2")
    before = copy.deepcopy(s4.tables)
    for rules in (RULES, R1_RULES):
        flags = providers.flag_frames(s4.tables, rules, s1["frame"], s1["coverage_segment"])
        engine.run_pow(flags, PARAMS)
    assert s4.tables == before
    for table, rows in s4.tables.items():
        assert vr_rules.check_ids(table, rows, s4.artifact_id) == []


@pytest.mark.determinism
def test_r1_only_configuration_never_has_motion():
    _, s4, _, s1 = s4_for("N2-G2")
    flags = providers.flag_frames(s4.tables, dataclasses.replace(R1_RULES, conflict=()), s1["frame"], s1["coverage_segment"])
    assert {f.M for f in flags} == {2}  # section 6.0: M unknown in every R1-only configuration, so no H (BL-2)
