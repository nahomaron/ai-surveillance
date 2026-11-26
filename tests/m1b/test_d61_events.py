"""D-61: the pre-registration v2 base values (section 1.3, Owner decision of 26 Nov 2026, typed here by hand from the
decision text) and the STEP 4 measures (IE share and its g_max attribution, hand-made inputs)."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "../../research/m1b"))
sys.path.insert(0, os.path.join(HERE, "../../research/preregistration"))
import d61_events as de  # noqa: E402
import pilot_common as pc  # noqa: E402
import v2_values as v2  # noqa: E402

ROOT = Path(HERE).resolve().parents[1]


def test_v2_values_equal_d61_section_1_3():
    # S4: tau 2.0 s, v_min 0.3 m/s, w_v 0.5 s, g_max 45 frames, person r 0.30 m, footprints unchanged (scale 1.0)
    assert v2.S4_V2 == {"g_max": 45, "v_min": 0.3, "w_v": 0.5, "tau": 2.0, "person_radius_m": 0.30, "fork_length_scale": 1.0, "fork_width_scale": 1.0}
    # S5: ttc_max 1.5, pet_max 1.5, d_p 3.0, d_pc 1.0, w_e 1.0, e_turn 1.5, e_acc 1.0, e_dec 1.0, t_min 0.2, w_post 1.5,
    # d_nm 0.5, k_sigma 2.0, o_max 0.5, k_c 1.5, k_c_turn 3.0, k_img 0.05; m_gap 45 = floor(1.5 / (1/30) + 1e-9) (AR-71 item 1)
    assert v2.S5_V2 == {"k_img": 0.05, "d_p": 3.0, "d_pc": 1.0, "ttc_max": 1.5, "pet_max": 1.5, "w_e": 1.0, "e_turn": 1.5, "e_acc": 1.0,
                        "e_dec": 1.0, "m_gap": 45, "t_min": 0.2, "w_post": 1.5, "d_nm": 0.5, "k_sigma": 2.0, "o_max": 0.5, "k_c": 1.5, "k_c_turn": 3.0}
    assert v2.M_GAP_S == 1.5 and v2.BAND_EDGES_V2 == [0.0, 0.5, 1.0, 2.0, 3.0, 4.0] and v2.JOIN_ACROSS_POW is True
    assert v2.IOU_M == 0.3 and v2.IOU_M_REPORTED == (0.3, 0.5, 0.7)
    assert v2.TRACKER_PACKAGE == "trc_7flfpx52d2siiljxkqwcorr7nz"
    assert v2.DETECTOR["thresholds"] == {"person": 0.20, "forklift": 0.05}
    assert v2.T24 == {"anchor": "box_bottom_centre", "anchor_offset_m": 1.00, "anchor_taper_m": 2.0, "smartspaces_offset_scale": 0.923, "s_max_m_per_px": 0.1}


def test_m_gap_frames_at_30_fps_is_45():
    from rq1.events import engine
    assert engine.m_gap_frames(v2.M_GAP_S, v2.DELTA_NOM_S) == 45 == v2.S5_V2["m_gap"]  # 1.5 / (1/30) = 45


def test_changed_from_v1_is_exactly_the_d61_changes():
    assert v2.changed_from_v1() == {"g_max": (15, 45), "pet_max": (1.0, 1.5), "d_p": (2.0, 3.0), "w_post": (1.0, 1.5), "e_dec": (2.0, 1.0),
                                    "k_c": (3.0, 1.5), "m_gap": (5, 45), "band_edges_m": ([0.0, 0.5, 1.0, 2.0, 4.0], [0.0, 0.5, 1.0, 2.0, 3.0, 4.0])}


def test_t15_5_horizon_covers_ttc_and_pet_for_base_and_grid():
    assert v2.S5_V2["ttc_max"] <= v2.S4_V2["tau"] and v2.S5_V2["pet_max"] <= v2.S4_V2["tau"]
    for value in (1.0, 1.5, 2.0):  # section 1.4 grids of ttc_max and pet_max, at the smallest tau of its grid (2.0)
        assert value <= 2.0


def test_v2_s5_configuration():
    ctx = pc.m.Context("sdg")
    cfg = v2.s5_config(ctx, "BL-6", "label-x", True)
    assert cfg.m_gap_s == 1.5 and cfg.join_across_pow is True and cfg.version_label == "label-x"
    assert cfg.rules.d_p == 3.0 and cfg.rules.pet_max == 1.5 and cfg.rules.e_dec == 1.0 and cfg.rules.ttc_max == 1.5
    assert cfg.params.m_gap == 45 and cfg.params.w_post == 1.5 and cfg.params.k_c == 1.5 and cfg.params.g_max == 45 and cfg.params.e_dec == 1.0
    assert [b for b in cfg.params.bands] == [(None, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, None)]
    assert cfg.substrate_config["g_max"] == 45 and cfg.substrate_config["version_label"] == "label-x"
    assert v2.s5_config(ctx, "BL-6", "label-x", False).join_across_pow is None  # references: T25.2 off (T25.2 d)
    cf = v2.s5_config(ctx, "BL-6", "label-y", True, g_max=15)
    assert cf.params.g_max == 15 and cf.substrate_config["g_max"] == 15 and cf.rules.d_p == 3.0  # counterfactual: only g_max differs


def test_v1_defaults_unchanged():
    """The keyword extensions of m1a_common keep every v1 configuration ID (the stored T-21 BL-6 S5 configuration)."""
    from rq1.events import s5
    ctx = pc.m.Context("sdg")
    cfg = pc.m.s5_config(ctx, "BL-6", pc.m.S4_BASE, pc.m.S5_BASE)
    assert cfg.version_label == "preregistration-v1" and cfg.m_gap_s is None and cfg.join_across_pow is None
    unit = ROOT / "out/m1a/run1/sdg"
    recs = sorted(p for p in (unit).iterdir() if p.is_dir() and p.name.startswith("rec_")) if unit.exists() else []
    if not recs:
        pytest.skip("stored T-21 run not present")
    base = json.loads((recs[0] / "base.json").read_text())
    man = json.loads((unit / "artifacts" / base["s5"]["BL-6"] / "manifest.json").read_text())
    assert man["spec"]["config_ids"] == [s5.config_id(cfg)]


def test_ie_share_and_attribution():
    ev = lambda *labels: {"labels": frozenset(labels)}
    at45 = de.ie_share([ev("O", "IE"), ev("H"), ev("H", "IE"), ev("PC")])
    assert at45 == {"events": 4, "ie_events": 2, "ie_share": 0.5}  # 2 of 4
    at15 = de.ie_share([ev("O"), ev("H"), ev("H", "IE"), ev("PC"), ev("O")])
    assert at15 == {"events": 5, "ie_events": 1, "ie_share": 0.2}  # 1 of 5
    att = de.ie_attribution(at45, at15)
    assert att["difference"] == pytest.approx(0.3) and att["ie_events_difference"] == 1  # 0.5 - 0.2; 2 - 1
    assert de.ie_share([]) == {"events": 0, "ie_events": 0, "ie_share": None}
    assert de.ie_attribution(de.ie_share([]), at15)["difference"] is None
    assert de.pool_ie([at45, at15]) == {"events": 9, "ie_events": 3, "ie_share": 3 / 9}


def test_labels_are_diagnostic():
    assert "not the v2 reference" in de.LABEL_REF and "not frozen" in de.LABEL_SYS and "not frozen" in de.LABEL_CF
    assert "diagnostic" in de.STATUS and "not a reported result" in de.STATUS


def test_sensitivity_grids_equal_d61_section_1_4():
    g = v2.GRIDS
    assert g["tau"] == [2.0, 3.0, 4.0] and g["ttc_max"] == [1.0, 1.5, 2.0] and g["pet_max"] == [1.0, 1.5, 2.0]
    assert g["d_p"] == [2.0, 3.0, 4.0] and g["d_pc"] == [0.5, 1.0, 1.5] and g["v_min"] == [0.2, 0.3, 0.4] and g["w_v"] == [0.33, 0.5, 1.0]
    assert g["m_gap_s"] == [1.0, 1.5, 2.0] and g["t_min"] == [0.1, 0.2, 0.5] and g["w_post"] == [1.0, 1.5, 2.0] and g["w_e"] == [0.5, 1.0]
    assert g["e_turn"] == g["e_acc"] == g["e_dec"] == ["x0.5", "x1", "x2"] and g["d_nm"] == [0.3, 0.5, 1.0] and g["g_max"] == [15, 30, 45, 60]
    assert g["person_radius_m"] == [0.25, 0.30, 0.35] and g["forklift_footprint"] == ["-10%", "+10%"]
    assert g["iou_m_report_columns"] == [0.3, 0.5, 0.7] and g["e_fturn_deg_s"] == [2.0, 5.0, 10.0]
    # T15.5: every one-at-a-time grid value keeps ttc_max and pet_max <= tau (base tau 2.0; the tau grid only grows)
    assert max(g["ttc_max"]) <= v2.S4_V2["tau"] and max(g["pet_max"]) <= v2.S4_V2["tau"] and min(g["tau"]) >= max(v2.S5_V2["ttc_max"], v2.S5_V2["pet_max"])


def test_t24_config_equals_d54_for_sdg_and_scales_smartspaces():
    import d54_b_v2 as b
    ctx = pc.m.Context("sdg")
    _, cfg, _, _ = v2.substrate_config(ctx, "x")
    mine, gcf, rec = v2.t24_config(cfg, "sdg")
    theirs, gcf_b, rec_b = b.run_config(cfg, gate=True, shift=True)
    assert (gcf, rec) == (gcf_b, rec_b) and mine == theirs  # AR-71 item 4: one T24 configuration for SDG
    ss, gcf_ss, _ = v2.t24_config(cfg, "smartspaces")
    assert ss.priors["forklift"]["anchor_offset_m"] == pytest.approx(0.923) and gcf_ss != gcf  # d x 0.923 (D-54)
    assert ss.s_max == 0.1 and ss.priors["forklift"]["anchor_taper_m"] == 2.0
