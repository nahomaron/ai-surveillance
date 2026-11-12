"""Process guard for the `determinism` marker (CLAUDE.md work-loop step 4; Owner process change, not a contract change).

A test module is guarded when it imports the artifact builder or a stage that calls it, the ID library or the fixture
package, reads `fixtures/records`, or imports helpers from a guarded test module. Every test in a guarded module must
carry `@pytest.mark.determinism` unless it is listed in EXCEPTIONS with a reason. Exceptions are pure-formula tests:
they build, hash, serialize or load nothing and use no seed. This module itself is static analysis and stays unmarked."""
import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIGGERS = ("rq1.ids", "rq1.fixtures", "rq1.substrate.builder", "rq1.substrate.oracle", "rq1.decode.stage", "rq1.registry.registrar", "rq1.events.s5")
EXCEPTIONS: dict[str, str] = {
    "tests/evaluation/test_t14_completeness.py::test_ct_f_03_cm_09": "pure formula: CM ratio on hand-built frame tables; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_completeness.py::test_cm_bases_and_cm_02_moving_restriction": "pure formula: CM ratio on hand-built frame tables; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_n9_pipeline_order_and_unresolved": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_rule_1_evidence_unavailable": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_rule_3_tracking": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_rule_4_geometry_and_rule_5_event_reasoning_and_rule_7": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_oracle_runner_covers_the_2_cubed_sets": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/evaluation/test_t14_attribution.py::test_vr_e_061_verified_only_on_synthetic_with_oracle_runs": "pure formula: N9 rule or VR-E-061 check on hand-built inputs; no fixture file, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_23_at_or_below_f_sub_no_degradation": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_23_above_f_sub_exactly_substituted_frames_degrade": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_t7_median_all_timed_when_no_adjacent_pair": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_t7_even_count_uses_mean_of_middle_values": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_t7_fewer_than_two_timed_frames": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_09_support_split_across_window_boundary": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_10_interval_ending_mid_support": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_12_linked_edges_need_one_aligned_timeline": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_ct_t_13_cross_timeline_window_rejected": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/decode/test_s1.py::test_t7_1_pairs_overlapping_an_uncertainty_region_are_excluded": "pure formula: T7 interval and support rules on hand-built timestamp lists; no clip, artifact or seed",
    "tests/evaluation/test_t12.py::test_headline_metrics_hand_calculation": "pure formula: EV-M ratios on hand-built counts; no matching, artifact or seed",
    "tests/evaluation/test_t12.py::test_window_counts_from_records": "pure formula: EV-M ratios on hand-built counts; no matching, artifact or seed",
    "tests/evaluation/test_t12.py::test_ev_m8_localization": "pure formula: EV-M ratios on hand-built counts; no matching, artifact or seed",
    "tests/evaluation/test_t12.py::test_ev_m3_abstention_rate": "pure formula: EV-M ratios on hand-built counts; no matching, artifact or seed",
    "tests/evaluation/test_t13.py::test_wilson": "pure formula: N5 closed-form estimator on literal numbers; no fixture file or seed",
    "tests/evaluation/test_t13.py::test_bland_altman": "pure formula: N5 closed-form estimator on literal numbers; no fixture file or seed",
    "tests/evaluation/test_t13.py::test_icc_2_1_shrout_fleiss_example": "pure formula: N5 closed-form estimator on literal numbers; no fixture file or seed",
    "tests/evaluation/test_t13.py::test_cohen_kappa": "pure formula: N5 closed-form estimator on literal numbers; no fixture file or seed",
    "tests/evaluation/test_t13.py::test_krippendorff_alpha_nominal": "pure formula: N5 closed-form estimator on literal numbers; no fixture file or seed",
    "tests/events/test_engine_part_a.py::test_kleene_logic": "pure formula: section 6.0 truth tables on literals",
    "tests/events/test_engine_part_a.py::test_providers_section_6_0": "pure formula: section 6.0 truth tables on literals",
    "tests/events/test_t10.py::test_ct_t10_01_order": "pure formula: contact order and E_ep on hand-built flags; no S4, artifact or seed",
    "tests/events/test_t10.py::test_ct_t10_04_e_ep_true_if_any_true_frame_in_i_plus": "pure formula: contact order and E_ep on hand-built flags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_2_e_in_kleene_logic": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_2_exp_evasive_score_is_max_over_i_plus": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_3_cue_units": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_3_cue_at_ca_gives_suspected": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_4_r5_disabled": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_observed_ca": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_unobserved_continuation_with_ttca": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_unobserved_continuation_without_ttca_uses_end_of_i": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_diverging_at_last_measured_frame_stays_observed": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_minimum_not_at_last_measured_frame_stays_observed": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_no_measured_clearance_uses_image_gap": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_5_no_boxes_gives_null_ca_and_not_assessable": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_6_w_ca_reaches_into_i_plus": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_6_q_insufficient_at_ca_comes_before_suspected": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_section_6_0_borderline_frames_from_providers": "pure formula: T9 engine rules on hand-built FrameFlags; no S4, artifact or seed",
    "tests/events/test_t9.py::test_t9_schema_fields": "schema-shape check: reads field definitions, serializes nothing",
    "tests/registry/test_registrar.py::test_cb_03_conditions": "pure formula: CB-03 conditions on literals; no registration",
    "tests/schema/test_vr_rules.py::test_ar8_sentinel_applies_only_to_non_negative_columns": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_unknown_enum_is_fatal_err_unknown_enum": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_tri_only_accepts_0_1_2": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_unknown_column_rejected": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_frac_suffix_is_bounded_section_1_2": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_bbox_requires_x1_lt_x2_section_4_1": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_validate_table_raises_fatal_contract_error": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/schema/test_vr_rules.py::test_schema_major_uses_package_f_section_9": "pure check: one validation rule on a literal row; nothing serialized",
    "tests/substrate/test_part_a.py::test_section_3_4_pair_class_rules": "pure formula: geometry or class rule on literals; no S4 artifact",
    "tests/substrate/test_part_a.py::test_n2_g2_predicted_minimum_never_below_d_pc": "pure formula: geometry or class rule on literals; no S4 artifact",
    "tests/substrate/test_part_a.py::test_signed_distance_inside_rectangle": "pure formula: geometry or class rule on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t9_1_window_is_shifted_not_shrunk": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t9_1_runs_split_at_unusable_frames_and_coverage_breaks": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_2_ols_standard_errors": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_2_yaw_rules": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_4_dimension_term_and_null_covariance": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_4_gradient_inside_uses_nearest_edge_normal": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_5_image_gap": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_6_evidence_state_precedence": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/substrate/test_part_b.py::test_t8_7_q_state_and_reasons": "pure formula: T8/T9.1 helper on literals; no S4 artifact",
    "tests/validation/test_store.py::test_rc_05_and_vr_e_040_no_reference_state_in_observation_store": "pure check: namespace or reference-class guard on a literal record",
    "tests/validation/test_store.py::test_rv_02_rule_conformance_results_carry_no_claim": "pure check: namespace or reference-class guard on a literal record",
    "tests/validation/test_store.py::test_ct_e_25_candidate_review_label_as_reference": "pure check: namespace or reference-class guard on a literal record",
    "tests/validation/test_store.py::test_vr_e_053_reference_records_are_blind": "pure check: namespace or reference-class guard on a literal record",
}


def _imports(tree: ast.Module) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
            out += [f"{node.module}.{a.name}" for a in node.names]
    return out


def _modules() -> dict[str, tuple[ast.Module, str]]:
    here = Path(__file__).resolve()
    return {str(p.relative_to(ROOT)): (ast.parse(p.read_text()), p.read_text()) for p in sorted((ROOT / "tests").rglob("test_*.py")) if p.resolve() != here}


def guarded_modules() -> set[str]:
    mods = _modules()
    guarded = {path for path, (tree, text) in mods.items()
               if any(name == t or name.startswith(t + ".") for name in _imports(tree) for t in TRIGGERS) or '"fixtures" / "records"' in text}
    changed = True
    while changed:  # a module importing helpers from a guarded test module is guarded too
        changed = False
        for path, (tree, _) in mods.items():
            if path in guarded:
                continue
            helpers = {n.split(".")[0] for n in _imports(tree) if n.split(".")[0].startswith("test_")}
            if any(Path(g).stem in helpers for g in guarded):
                guarded.add(path)
                changed = True
    return guarded


def _marked(fn: ast.FunctionDef, module_marked: bool) -> bool:
    return module_marked or any("determinism" in ast.unparse(d) for d in fn.decorator_list)


def unmarked_tests() -> dict[str, list[str]]:
    out = {}
    for path, (tree, _) in _modules().items():
        module_marked = any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "pytestmark" for t in n.targets) and "determinism" in ast.unparse(n.value)
                            for n in tree.body)
        out[path] = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_") and not _marked(n, module_marked)]
    return out


def test_marker_is_registered_with_strict_markers():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["pytest"]["ini_options"]
    assert "--strict-markers" in config["addopts"]
    assert any(m.startswith("determinism:") for m in config["markers"])


def test_every_test_in_a_guarded_module_is_marked_or_excepted():
    guarded = guarded_modules()
    missing = [f"{path}::{name}" for path, names in unmarked_tests().items() if path in guarded for name in names
               if f"{path}::{name}" not in EXCEPTIONS]
    assert missing == [], "mark these with @pytest.mark.determinism, or list them in EXCEPTIONS with a reason:\n" + "\n".join(missing)


def test_exceptions_are_current_and_reasoned():
    unmarked = {f"{path}::{name}" for path, names in unmarked_tests().items() for name in names}
    guarded = guarded_modules()
    stale = [key for key in EXCEPTIONS if key not in unmarked or key.split("::")[0] not in guarded]
    assert stale == [], f"exceptions that are marked, missing or outside guarded modules: {stale}"
    assert all(reason.strip() for reason in EXCEPTIONS.values())
