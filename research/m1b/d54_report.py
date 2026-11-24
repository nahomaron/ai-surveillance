"""D-54 STEP 5: the D-54 diagnostics report, built from the stored STEP 3, 3b and 4 results (no computation of its own).

  PYTHONPATH=src .venv/bin/python research/m1b/d54_report.py   -> research/m1b/d54_report.md
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(__file__)
B = json.load(open(os.path.join(HERE, "d54_b_v2_tune.json")))
C = json.load(open(os.path.join(HERE, "d54_c_v2_tune.json")))
P = json.load(open(os.path.join(HERE, "d54_person_position.json")))
VIEWS = (("all", "all"), ("ceiling", "ceiling"), ("eye_level", "eye level"))
LABEL = "**Diagnostic, tuning subset, not a reported result.**"


def f(x, n=3):
    return "–" if x is None else f"{x:.{n}f}"


def pct(x, n=1):
    return "–" if x is None else f"{100 * x:.{n}f} %"


def ev_table(ev: dict, cols: list[tuple[str, str]]) -> list[str]:
    L = ["| column | view | cameras | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events |",
         "|---|---|---|---|---|---|---|---|"]
    for key, name in cols:
        for v, vn in VIEWS:
            x = ev[v][key]
            L.append(f"| {name} | {vn} | {ev[v]['cameras']} | {f(x['EV-M1'])} | {x['matched_references']} / {x['assessable_references']} | {f(x['EV-M2'])} | "
                     f"{x['matched_events']} / {x['system_events']} | {x['unmatched_events']} |")
    return L


def step3() -> list[str]:
    cols = [("A (stored)", "A (stored, D-53)"), ("B-tune (stored B)", "B-tune (= stored B, D-53)"), ("B-T24.2", "B-T24.2"), ("B-T24.1", "B-T24.1"), ("B-both", "B-both")]
    t = B["t24_values"]
    L = ["## 1. STEP 3: column B with T24 on (oracle boxes, BL-6)", "", LABEL, "",
         f"116 tuning cameras; oracle boxes; `full_camera`; S5 BL-6; N4 against the stored T-21 BL-6 references, label group G1, summed counts. "
         f"T24 values (D-54 v2 candidates, selected, not frozen): s_max {t['s_max_m_per_px']} m/px; forklift prior `anchor = box_bottom_centre`, "
         f"d {t['anchor_offset_m']:.2f} m, r_taper {t['anchor_taper_m']} m. The person prior is unchanged. The ORACLE-S3 was rebuilt and equals the stored one on "
         f"{B['checks']['s3_rebuilt_equals_stored']} of 116 cameras. Output: `research/m1b/d54_b_v2_tune.json`.", "",
         "### 1.1 EV-M1 and EV-M2", ""] + ev_table(B["ev"], cols)
    L += ["", "### 1.2 Forklift position error", "",
          "|Estimate − simulator footprint centre| of the oracle track's identity (D1 definitions); median and P95 by linear interpolation. "
          "This is the Euclidean error. It is not D1's along-sight residual (median 0.33 m, P95 0.64 m), which T24.1 (e) asks reports to state.", "",
          "| column | view | object-frames | median | P95 | > 1 m | > 2 m | > 10 m |", "|---|---|---|---|---|---|---|---|"]
    for key in ("B-tune (stored B)", "B-T24.2", "B-T24.1", "B-both"):
        for v, vn in VIEWS:
            e = B["forklift_position_error"][v][key]
            L.append(f"| {key} | {vn} | {e['n']} | {f(e['median_m'])} m | {f(e['p95_m'])} m | {pct(e['share_gt_1m'])} | {pct(e['share_gt_2m'])} | {pct(e['share_gt_10m'], 2)} |")
    L += ["", "### 1.3 Availability by null reason (T24.2 (e), (f))", "",
          f"Data origin: synthetic_rendered (SDG) for every camera. s_max = {t['s_max_m_per_px']} m/px. Gated positions are *unresolved*, not *wrong* (T24.2 (f)).", "",
          "| column | view | class | object-frames | position | resolution limit (s > s_max) | no floor intersection | lost point | other null |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key in ("B-tune (stored B)", "B-T24.2", "B-T24.1", "B-both"):
        for v, vn in VIEWS:
            for cls in ("forklift", "person"):
                a = B["availability"][v][key][cls]
                cell = lambda k: f"{a.get(k, 0)} ({pct(a.get('share_' + k, 0.0))})"
                L.append(f"| {key} | {vn} | {cls} | {a['object_frames']} | {cell('position')} | {cell('resolution_limit')} | {cell('no_floor_intersection')} | "
                         f"{cell('lost')} | {cell('other_null')} |")
    cr = B["cr034_size"]["B-both"]
    L += ["", "With the gate off, a ray with no floor intersection is \"other null\" (`not_observable`, as in E-1.2.24). With the gate on it is the separate row "
          "\"no floor intersection\", so the 383 person frames move between rows. The gate nulls no forklift frame on the oracle path.",
          f"CR-034 (lost points): ORACLE-S3 has {cr['lost_object_frames']} lost object-frames on these cameras. Readings (a) and (b) give identical results here "
          f"({cr['pair_frames_occluded_to_geometry_failure_under_b']} pair-frames would change).", ""]
    return L


def step3b() -> list[str]:
    t = C["t24_values_c_v2"]
    L = ["## 2. STEP 3b: detector path with the D-56 package, T24 off (C-pkg) and on (C-v2)", "", LABEL,
         "These runs never enter a report table beside the pilot columns.", "",
         f"116 tuning cameras. S2: the stored YOLO-World detections ({C['s2']['pilot']} pilot S2, {C['s2']['probe_d55']} probe-camera S2 from D-55); no new detection. "
         f"S3: the D-56 package `{C['tracker_package']}`. Its tracker run reproduced the stored D-55 grid measures on {C['checks']['tracker_reproduces_d55_grid']} of "
         f"{C['checks']['cameras']} cameras. S4 `full_camera`. C-v2 uses the T24 values s_max {t['s_max_m_per_px']} m/px, d {t['anchor_offset_m']:.2f} m and r_taper "
         f"{t['anchor_taper_m']} m (selected, not frozen). S5 BL-6. S8 N4 against the T-21 BL-6 references, G1, A5.2 association of the detector tracks, as in the pilot. "
         "Runtime: estimated 0.22 h on 2 cameras (limit 3 h); the run took 12 min, plus 5 min of evaluation. Output: `research/m1b/d54_c_v2_tune.json`.", "",
         f"Standing caveat (D-56): {C['caveat_d56']}", "",
         "Column C exists only on the 96 tuning cameras that are pilot cameras. Section 2.2 therefore restricts every column to those 96 cameras; it is stated as such.", ""]
    for pop, title, cols in (
            ("tuning_116", "### 2.1 All 116 tuning cameras", [("A (stored)", "A (stored)"), ("B-tune (stored B)", "B-tune (= stored B)"), ("C-pkg", "C-pkg"), ("C-v2", "C-v2")]),
            ("pilot_96", "### 2.2 The 96 tuning cameras that are pilot cameras (column C restricted to them)",
             [("A (stored)", "A (stored)"), ("B-tune (stored B)", "B-tune (= stored B)"), ("C (pilot, stored)", "C (pilot, stored)"), ("C-pkg", "C-pkg"), ("C-v2", "C-v2")])):
        ev = C[pop]
        L += [title, "", "#### EV-M1, EV-M2 and CM-03", ""] + ev_table(ev, cols)
        L += ["", "CM-03: pair coverage, pooled as sum of numerators over sum of denominators (the pilot's point value).", "",
              "| column | view | CM-03 detected | CM-03 detected_plus_inferred |", "|---|---|---|---|"]
        for key, name in cols:
            for v, vn in VIEWS:
                c3 = ev[v][key]["CM-03"]
                L.append(f"| {name} | {vn} | {f(c3['detected']['value'])} | {f(c3['detected_plus_inferred']['value'])} |")
        L += ["", "#### Extent and fragmentation (D-50 item 2 definitions, `extent_check.py`; BL-6, G1)", "",
              "| column | view | unmatched events | with same-pair overlap (IoU > 0) | IoU 0 / (0, 0.1] / (0.1, 0.2] / (0.2, 0.3) / ≥ 0.3 | references matched or overlapped | "
              "covered by ≥ 2 episodes | episodes | episodes with `continuation_of_nk` | overlapping episodes linked / overlapping |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for key, name in cols:
            for v, vn in VIEWS:
                x = ev[v][key]["extent"]
                bands = " / ".join(str(n) for n in x["unmatched_by_band"].values())
                L.append(f"| {name} | {vn} | {x['unmatched_events']} | {x['unmatched_with_same_pair_overlap']} | {bands} | {x['references_matched_or_overlapped']} | "
                         f"{x['references_with_2plus_episodes']} | {x['episodes']} | {x['episodes_with_continuation_of_nk']} | {x['of_which_linked']} / "
                         f"{x['episodes_overlapping_references']} |")
        L.append("")
    L += ["### 2.3 Position error (detector path, D-41 definitions as the pilot)", "",
          "|Estimate − simulator position| of the A5.2-matched identity on the frame (B: the oracle track's identity). Shares above 1, 2 and 5 m, as in the pilot. 116 cameras.", "",
          "| column | view | class | object-frames | median | P95 | > 1 m | > 2 m | > 5 m |", "|---|---|---|---|---|---|---|---|---|"]
    for key in ("B-tune (stored B)", "C-pkg", "C-v2"):
        for v, vn in VIEWS:
            for cls in ("forklift", "person"):
                e = C["tuning_116"][v][key]["position"][cls]["error"]
                L.append(f"| {key} | {vn} | {cls} | {e['n']} | {f(e['median_m'])} m | {f(e['p95_m'])} m | {pct(e['share_gt_1m'])} | {pct(e['share_gt_2m'])} | {pct(e['share_gt_5m'])} |")
    L += ["", "### 2.4 Availability by null reason, C-pkg and C-v2 (T24.2 (e), (f))", "",
          "Data origin: synthetic_rendered (SDG). s_max = 0.1 m/px. Gated positions are *unresolved*, not *wrong*.", "",
          "| column | view | class | object-frames | position | resolution limit (s > s_max) | no floor intersection | other null |", "|---|---|---|---|---|---|---|---|"]
    for key in ("C-pkg", "C-v2"):
        for v, vn in VIEWS:
            for cls in ("forklift", "person"):
                a = C["availability_t24"][v][key]["synthetic_rendered"][cls]
                cell = lambda k: f"{a.get(k, 0)} ({pct(a.get('share_' + k, 0.0))})"
                L.append(f"| {key} | {vn} | {cls} | {a['object_frames']} | {cell('position')} | {cell('resolution_limit')} | {cell('no_floor_intersection')} | {cell('other_null')} |")
    cr = C["cr034_size_c_v2"]
    L += ["", f"CR-034 (lost points): the detector S3 stores no lost points ({cr['lost_object_frames']} lost object-frames). Readings (a) and (b) give identical results here too.", ""]
    return L


def _stats_row(name, s):
    return (f"| {name} | {s['n']} | {f(s['along_signed_median_m'])} | {f(s['along_signed_p05_m'])} | {f(s['along_signed_p95_m'])} | {f(s['along_abs_median_m'])} | "
            f"{f(s['across_abs_median_m'])} | {f(s['error_median_m'])} | {f(s['error_p95_m'])} |")


CROSS = {"clearance_crosses_d_p": "clearance crosses d_p", "clearance_crosses_d_pc": "clearance crosses d_pc",
         "pred_min_crosses_d_pc": "predicted minimum crosses d_pc"}


def _events(x: dict, provider_note: str) -> list[str]:
    L = [f"- Events: **{x['n']}** (by viewpoint: " + ", ".join(f"{k} {v}" for k, v in x["by_viewpoint"].items()) + ").",
         "- Cause class at the closest-approach frame: " + "; ".join(f"{k}: {v}" for k, v in x["by_cause"].items()) + ".",
         f"- Providers fired ({provider_note}): " + "; ".join(f"{k}: {v}" for k, v in x["providers_fired"].items()) + ". R1 is not in BL-6.",
         "- Episode start: " + ", ".join(f"{CROSS[k]} {v}" for k, v in x["start_crossings"].items()) + f"; no neighbouring pair-frame {x['start_no_neighbour_pair_frame']}.",
         "- Episode end: " + ", ".join(f"{CROSS[k]} {v}" for k, v in x["end_crossings"].items()) + f"; no neighbouring pair-frame {x['end_no_neighbour_pair_frame']}.",
         f"- Person error at the closest-approach frame: along median {f(x['person_along_at_ca']['median_m'])} m (P05 {f(x['person_along_at_ca']['p05_m'])}, "
         f"P95 {f(x['person_along_at_ca']['p95_m'])}); |across| median {f(x['person_across_at_ca']['median_m'])} m.",
         f"- Clearance at that frame, median: B {f(x['clearance_B_at_ca']['median_m'])} m, B-sim-P {f(x['clearance_P_at_ca']['median_m'])} m, "
         f"A {f(x['clearance_A_at_ca']['median_m'])} m; B − B-sim-P median {f(x['clearance_B_minus_B_sim_P_at_ca']['median_m'])} m "
         f"(P05 {f(x['clearance_B_minus_B_sim_P_at_ca']['p05_m'])}, P95 {f(x['clearance_B_minus_B_sim_P_at_ca']['p95_m'])})."]
    return L


def step4() -> list[str]:
    a = P["a_person_error_column_b"]
    hdr = ["| group | object-frames | along median (signed) | along P05 | along P95 | |along| median | |across| median | error median | error P95 |",
           "|---|---|---|---|---|---|---|---|---|"]
    L = ["## 3. STEP 4: person-position diagnostic", "", LABEL, "",
         "116 tuning cameras; stored outputs: column B (oracle boxes, `full_camera`), column A, and the D-53 step 2 runs B-tune and B-sim-P. "
         "Classified only; no rule is recommended. Output: `research/m1b/d54_person_position.json`. Units: metres. Along: negative = toward the camera. "
         "Across is unsigned (D1).", "", "### 3.1 (a) Person position error in column B", ""] + hdr + [_stats_row("all", a["all"])]
    for key, title in (("by_r", "r"), ("by_viewpoint", "viewpoint"), ("by_evidence_state", "evidence state"), ("by_bottom_clipped", "box clipped at bottom")):
        for g, s in a[key].items():
            L.append(_stats_row(f"{title}: {g}", s))
    L += ["", "r = floor distance from the camera's floor point to the estimate. \"Clipped at bottom\" = oracle box bottom edge on the last pixel row (y2 ≥ H − 1).", "",
          "### 3.2 (b) Along-sight error against the simulator person box", ""]
    b = P["b_half_depth"]
    L += [f"- Median signed along-sight error {f(b['along_signed_median_m'])} m; median |along| {f(b['along_abs_median_m'])} m ({b['n']} object-frames).",
          f"- Simulator person box half-depth along the line of sight (half the projected extent of the 3D box's floor face): median {f(b['person_box_half_depth_median_m'])} m "
          f"(P05 {f(b['p05_m'])}, P95 {f(b['p95_m'])}). Half floor length median {f(b['half_length_median_m'])} m; half floor width median {f(b['half_width_median_m'])} m. "
          f"Frames without a 3D box: {b['frames_without_3d_box']}.", ""]
    c = P["c_b_tune_unmatched_without_b_sim_p_counterpart"]
    L += ["### 3.3 (c) B-tune unmatched events with no counterpart in B-sim-P", "",
          f"B-tune unmatched {c['b_tune_unmatched_total']}, B-sim-P unmatched {c['b_sim_p_unmatched_total']}. D-54 does not define \"counterpart\" (**CR-035**), so both readings "
          "are given and neither is chosen. Neither reading gives 42, because B-sim-P also has unmatched events with no B-tune counterpart. "
          "Cause class: the BL-6 threshold the B value is below at the closest-approach frame while the B-sim-P value is not "
          "(d_p 2.0 m for the clearance, R2; d_pc 1.0 m for the predicted minimum clearance, R3).", "",
          f"**Reading 1** ({c['reading_1']['counterpart']}):", ""] + _events(c["reading_1"], "B-tune episode")
    L += ["", f"**Reading 2** ({c['reading_2']['counterpart']}):", ""] + _events(c["reading_2"], "B-tune episode")
    d = P["d_references_recovered_by_b_sim_p"]
    L += ["", "### 3.4 (d) References B-sim-P matches and B-tune does not", "",
          "At the closest-approach frame of the B-sim-P event. Cause class: the threshold the B-sim-P value is below while the B value is not.", ""] + _events(d, "B-sim-P episode")
    L += [f"- B-tune events of the same pair overlapping these references: " + ", ".join(str(x["b_tune_same_pair_overlapping_events"]) for x in d["references"]) + ".", ""]
    return L


def summary() -> list[str]:
    bb, bt = B["ev"]["all"]["B-both"], B["ev"]["all"]["B-tune (stored B)"]
    cp, cv = C["tuning_116"]["all"]["C-pkg"], C["tuning_116"]["all"]["C-v2"]
    c96 = C["pilot_96"]["all"]["C (pilot, stored)"]
    fe = B["forklift_position_error"]["all"]
    return ["## Summary (plain language)", "",
            f"1. With oracle boxes, the forklift centre shift (T24.1) raises EV-M1 from {f(bt['EV-M1'], 2)} to {f(bb['EV-M1'], 2)} and EV-M2 from {f(bt['EV-M2'], 2)} to {f(bb['EV-M2'], 2)} (116 tuning cameras).",
            f"2. It lowers the median forklift position error from {f(fe['B-tune (stored B)']['median_m'], 2)} m to {f(fe['B-T24.1']['median_m'], 2)} m. The share above 2 m rises from "
            f"{pct(fe['B-tune (stored B)']['share_gt_2m'])} to {pct(fe['B-T24.1']['share_gt_2m'])}.",
            f"3. With oracle boxes, the resolution gate (T24.2) leaves EV-M1 at {f(bt['EV-M1'], 3)} and moves EV-M2 from {f(bt['EV-M2'], 3)} to {f(B['ev']['all']['B-T24.2']['EV-M2'], 3)}. "
            "It nulls 366 person frames (all eye level) and no forklift frame.",
            f"4. The D-56 tracker package alone (C-pkg) gives EV-M1 {f(cp['EV-M1'], 2)}, EV-M2 {f(cp['EV-M2'], 2)} and CM-03 {f(cp['CM-03']['detected']['value'], 2)}. "
            f"On the 96 cameras where column C exists, C gives {f(c96['EV-M1'], 2)}, {f(c96['EV-M2'], 2)} and {f(c96['CM-03']['detected']['value'], 2)}.",
            f"5. With T24 on as well (C-v2): EV-M1 {f(cv['EV-M1'], 2)}, EV-M2 {f(cv['EV-M2'], 2)}. The system raises more events ({cv['system_events']} against {cp['system_events']}), and "
            f"{cv['unmatched_events']} of them are unmatched.",
            "6. On the detector path the eye-level cameras lag far behind the ceiling cameras (C-v2 EV-M1 0.39 against 0.78).",
            f"7. Fragmentation remains: with C-v2, {cv['extent']['references_with_2plus_episodes']} references are covered by two or more episodes, and "
            f"{cv['extent']['episodes_with_continuation_of_nk']} of {cv['extent']['episodes']} episodes carry `continuation_of_nk`.",
            f"8. Person positions with oracle boxes: median error {f(P['a_person_error_column_b']['all']['error_median_m'], 2)} m. The median along-sight error is "
            f"{f(P['b_half_depth']['along_signed_median_m'], 2)} m, about a third of the person box's half-depth ({f(P['b_half_depth']['person_box_half_depth_median_m'], 2)} m).",
            "9. The large person errors are in estimates 20 m or more from the camera (296 frames, median error 76 m); below 20 m the error P95 is at most 5.4 m.",
            "10. Among the B-tune unmatched events that B-sim-P lacks, B alone is below d_pc (R3) more often than below d_p (reading 1: 8 against 4 of 15; "
            "reading 2: 20 against 4 of 50, with 25 on the same side of both). The count depends on CR-035.",
            "11. Lost points (CR-034) do not occur on either path here, so CR-034's two readings give identical results.",
            "12. All of this is synthetic SDG data on the tuning cameras only: diagnostic, not a reported result, and nothing here is validated."]


def build() -> str:
    head = ["# D-54 diagnostics: T24 on the tuning cameras, and person positions", "",
            "Decision: D-54 (23 Nov 2026), with D-56. Contract E-1.2.25 (Appendix T T24). Branch `m0-implementation`.", "",
            LABEL + " Synthetic SDG validation data; 116 tuning cameras only (D-54 ruling 5). Nothing was run on the 110 reporting cameras or "
            "on the test partition (D-37). Pilot columns A, B, C and C′ are unchanged and their stored artifacts were not overwritten. "
            "The T24 values and the tracker package are **selected, not frozen**. Status words: implemented / verified (fixtures) only. Nothing is empirically validated.", ""]
    return "\n".join(head + summary() + [""] + step3() + step3b() + step4()) + "\n"


if __name__ == "__main__":
    p = os.path.join(HERE, "d54_report.md")
    with open(p, "w") as fh:
        fh.write(build())
    print("wrote", p)
