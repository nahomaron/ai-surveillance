"""D-53 step 5: render `research/m1b/v2_diagnostics_report.md` from the stored step outputs (no computation of new results).

  PYTHONPATH=src .venv/bin/python research/m1b/v2_diagnostics_report.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

R = pc.ROOT / "research/m1b"
VIEWS = (("all", "All"), ("ceiling", "Ceiling"), ("eye_level", "Eye-level"))


def f(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def pct(x):
    return "–" if x is None else f"{100 * x:.1f} %"


def load(name):
    return json.loads((R / name).read_text())


def render() -> str:
    sets, d1, d2, d4, d5 = (load(n) for n in ("v2_camera_sets.json", "d1_anchor_angle.json", "d2_position_contribution.json",
                                               "d4_detector_offset.json", "d5_sensitivity_split.json"))
    L = []
    w = L.append
    w("# Pre-registration v2 diagnostics D1, D2, D4, D5 (D-53)")
    w("")
    w("**Status: diagnostic, tuning subset, not a reported result.** Synthetic SDG validation data only; nothing is validated. "
      "Contract E-1.2.24 unchanged; no rule, parameter or pipeline code changed; Fix 1 (anchor offset) and Fix 2 (resolution gate) are not implemented. "
      "No test-partition data; the 110 reporting cameras enter only the descriptive D5 table. "
      "These numbers never appear in a report table beside columns A, B, C or C'.")
    w("")
    w("Sources: `v2_camera_sets.json`, `d1_anchor_angle.json`, `d2_position_contribution.json`, `d4_detector_offset.json`, "
      "`d5_sensitivity_split.json` (each written twice, byte-identical). Percentiles: linear interpolation. "
      "\"Along\" = error component on the line of sight from the camera's floor point to the true centre; negative = toward the camera.")
    w("")
    # ---------------------------------------------------------------- summary
    a2 = d2["ev"]["all"]
    A, B, F, P = (a2[k] for k in ("A (stored)", "B-tune", "B-sim-F", "B-sim-P"))
    loss = A["matched_references"] - B["matched_references"]
    rec_f, rec_p = F["matched_references"] - B["matched_references"], P["matched_references"] - B["matched_references"]
    gap = A["EV-M2"] - B["EV-M2"]
    bins1 = d1["along_by_theta"]["all"]
    res = d1["residual_after_d"]
    rb = [res[k] for k in bins1]
    pd_all = d4["result"]["all"]["paired_same_frames"]
    pbt = [r["median_difference_detector_minus_oracle_m"] for v, _ in VIEWS for r in d4["result"][v]["paired_by_theta"].values()]
    w("## Summary (plain language)")
    w("")
    w(f"1. **(a) Angle.** Yes. With oracle boxes, the forklift estimate falls short toward the camera by a median of {f(-bins1['0-15']['along_signed_median_m'])} m when the "
      f"forklift is seen end-on (0–15°) and {f(-bins1['75-90']['along_signed_median_m'])} m when seen side-on (75–90°); the footprint half-extent h(θ) falls from "
      f"{f(bins1['0-15']['h_theta_median_m'])} to {f(bins1['75-90']['h_theta_median_m'])} m over the same bins.")
    w(f"2. A constant shift by the candidate d = {f(d1['candidate_d_m'])} m leaves a median residual of {f(min(r['median_m'] for r in rb))}–{f(max(r['median_m'] for r in rb))} m "
      f"and a P95 of {f(min(r['p95_m'] for r in rb))}–{f(max(r['p95_m'] for r in rb))} m across the angle bins (all frames: median {f(res['all']['median_m'])}, P95 {f(res['all']['p95_m'])} m).")
    w(f"3. D3: {pct(d1['d3_share_r_lt_2m']['eye_level']['share'])} of eye-level forklift frames and {pct(d1['d3_share_r_lt_2m']['ceiling']['share'])} of ceiling frames have the estimate within 2 m of the camera.")
    w(f"4. **(b) Position substitution.** Column B loses {loss} of {A['assessable_references']} G1 references against A (BL-6 recall {f(B['EV-M1'])} vs {f(A['EV-M1'])}). "
      f"Simulator forklift positions (B-sim-F) recover {rec_f} of the {loss} ({pct(rec_f / loss)}); simulator person positions (B-sim-P) recover {rec_p} ({pct(rec_p / loss)}).")
    w(f"5. Precision: B {f(B['EV-M2'])}, A {f(A['EV-M2'])}. B-sim-F {f(F['EV-M2'])} ({pct((F['EV-M2'] - B['EV-M2']) / gap)} of the gap), "
      f"B-sim-P {f(P['EV-M2'])} ({pct((P['EV-M2'] - B['EV-M2']) / gap)}); unmatched events {B['unmatched_events']} → {F['unmatched_events']} (F) and {P['unmatched_events']} (P).")
    w(f"6. Neither substitution alone reaches A, so the person and forklift positions both contribute; forklift position contributes more to recall, person position more to precision.")
    w(f"7. **(c) Detector vs oracle boxes.** No, not by more than 0.2 m. On the same {pd_all['n']:,} forklift identity-frames (96 tuning cameras with stored S2), the median paired difference "
      f"(detector − oracle) is {f(pd_all['median_difference_detector_minus_oracle_m'])} m overall and lies between {f(min(pbt))} and {f(max(pbt))} m in every viewpoint × angle bin.")
    w(f"8. The two sides' separate medians differ by more in one bin (eye-level 15–30°: {f(d4['result']['eye_level']['paired_by_theta']['15-30']['detector_signed_median_m'])} vs "
      f"{f(d4['result']['eye_level']['paired_by_theta']['15-30']['oracle_signed_median_m'])} m), where the frame distributions are spread; the paired difference there is "
      f"{f(d4['result']['eye_level']['paired_by_theta']['15-30']['median_difference_detector_minus_oracle_m'])} m.")
    w(f"9. D4 does not cover the 20 T-22 probe cameras (no stored S2 run; the detector was not re-run).")
    w("10. No value or rule form is recommended here; the Architect and the Owner choose.")
    w("")
    # ---------------------------------------------------------------- step 0
    w("## Step 0: camera sets")
    w("")
    w("| Set | Runs | Cameras | Ceiling | Eye-level |")
    w("|---|---|---|---|---|")
    for k, name in (("tuning", "Tuning (runs with a T-22 probe camera)"), ("reporting", "Reporting (other validation runs)")):
        s = sets[k]
        w(f"| {name} | {s['n_runs']} | {s['n_cameras']} | {s['by_viewpoint']['ceiling']} | {s['by_viewpoint']['eye_level']} |")
    w("")
    w(f"Disjoint; population = the {sets['population_cameras']} SDG validation cameras with an ORACLE-S3. Check: {sets['check']}.")
    w("")
    # ---------------------------------------------------------------- step 1
    w("## Step 1 (D1, D3): forklift along-sight error by viewing angle, oracle boxes (column B S4, 116 tuning cameras)")
    w("")
    w(f"{d1['forklift_object_frames']:,} forklift object-frames with a position; θ = angle between the simulator yaw axis (box long axis) and the line of sight, folded to [0°, 90°]; "
      f"h(θ) = 1.515 |cos θ| + 0.565 |sin θ| m (L = 3.03 m, W = 1.13 m).")
    w("")
    for v, name in VIEWS:
        w(f"**{name}**")
        w("")
        w("| θ bin | n | Signed median (m) | P05 (m) | P95 (m) | Median h(θ) (m) |")
        w("|---|---|---|---|---|---|")
        for k, r in d1["along_by_theta"][v].items():
            w(f"| {k}° | {r['n']:,} | {f(r['along_signed_median_m'])} | {f(r['along_signed_p05_m'])} | {f(r['along_signed_p95_m'])} | {f(r['h_theta_median_m'])} |")
        w("")
    w("**D3: estimate within 2 m of the camera (floor distance r)**")
    w("")
    w("| Viewpoint | Frames | r < 2 m | Share |")
    w("|---|---|---|---|")
    for v, name in VIEWS:
        r = d1["d3_share_r_lt_2m"][v]
        w(f"| {name} | {r['n']:,} | {r['r_lt_2m']:,} | {pct(r['share'])} |")
    w("")
    w(f"**Candidate d** = median |along| over all tuning frames = {d1['along_abs_median_m_unrounded']:.3f} m, rounded to 0.05 m: **{f(d1['candidate_d_m'])} m**.")
    w("")
    w("Residual after a constant shift by d: |along − (−d)|")
    w("")
    w("| θ bin | n | Median (m) | P95 (m) |")
    w("|---|---|---|---|")
    for k, r in d1["residual_after_d"].items():
        w(f"| {k if k == 'all' else k + '°'} | {r['n']:,} | {f(r['median_m'])} | {f(r['p95_m'])} |")
    w("")
    # ---------------------------------------------------------------- step 2
    w("## Step 2 (D2): position contribution to the oracle-box loss (BL-6, G1, N4; 116 tuning cameras)")
    w("")
    w("Oracle boxes and BL-6 under the frozen v1 values, evaluated against the stored T-21 BL-6 references; EV-M1 and EV-M2 from summed counts. "
      "B-tune is column B re-run through the diagnostic adapter; its S4 equals the stored column B S4 on all "
      f"{d2['checks']['b_tune_s4_payload_equals_stored_B']} cameras (payload hash), and the rebuilt ORACLE-S3 equals the stored one on all {d2['checks']['s3_rebuilt_equals_stored']}. "
      "Only position and covariance were substituted (the simulator yaw was not). Column A: stored T-21 `base` unit, same cameras. "
      f"Code commit {', '.join(c[:7] for c in d2['code_commit'])}; execution records beside every artifact under `out/m1b/v2diag/`.")
    w("")
    for v, name in VIEWS:
        x = d2["ev"][v]
        w(f"**{name}** ({x['cameras']} cameras)")
        w("")
        w("| Run | EV-M1 | EV-M2 | Assessable | Matched | Missed | Events | Unmatched events |")
        w("|---|---|---|---|---|---|---|---|")
        for k, name2 in (("B-tune", "B-tune (column B)"), ("B-sim-F", "B-sim-F (simulator forklift)"), ("B-sim-P", "B-sim-P (simulator person)"),
                         ("A (stored)", "A (simulator both; stored)")):
            r = x[k]
            w(f"| {name2} | {f(r['EV-M1'], 3)} | {f(r['EV-M2'], 3)} | {r['assessable_references']} | {r['matched_references']} | {r['missed_references']} | "
              f"{r['system_events']} | {r['unmatched_events']} |")
        w("")
    # ---------------------------------------------------------------- step 3
    w("## Step 3 (D4): forklift offset with detector boxes (stored YOLO-World S2, frame level)")
    w("")
    w(f"{d4['cameras_used']} tuning cameras with a stored S2 ({d4['cameras_used_by_viewpoint']['ceiling']} ceiling, {d4['cameras_used_by_viewpoint']['eye_level']} eye-level); "
      f"**{d4['cameras_missing_stored_s2']} cameras missing** (the T-22 probe cameras: not in the pilot, no stored S2 run; the detector was not re-run). "
      f"Forklift detections matched to a reference-visible forklift box as in the pilot frame metrics (IoU ≥ 0.3, one-to-one): {d4['match_counts']['matched']:,}. "
      "Position = box bottom-centre through `full_camera`. Before tracking, so no tracker setting enters.")
    w("")
    w("| Viewpoint | n | Signed median (m) | P95 (m) | Median |along| (m) | P95 |along| (m) |")
    w("|---|---|---|---|---|---|")
    for v, name in VIEWS:
        r = d4["result"][v]["detector_box"]
        w(f"| {name} | {r['n']:,} | {f(r['along_signed_median_m'])} | {f(r['along_signed_p95_m'])} | {f(r['along_abs_median_m'])} | {f(r['along_abs_p95_m'])} |")
    w("")
    w("By θ bin, with the oracle box (stored column B S4) on the same identity-frames:")
    w("")
    for v, name in VIEWS:
        w(f"**{name}**")
        w("")
        w("| θ bin | n | Detector signed median (m) | Detector P95 (m) | Oracle signed median, same frames (m) | Median paired difference, detector − oracle (m) |")
        w("|---|---|---|---|---|---|")
        for k, r in d4["result"][v]["by_theta"].items():
            p = d4["result"][v]["paired_by_theta"][k]
            w(f"| {k}° | {r['n']:,} | {f(r['along_signed_median_m'])} | {f(r['along_signed_p95_m'])} | {f(p['oracle_signed_median_m'])} | "
              f"{f(p['median_difference_detector_minus_oracle_m'])} |")
        w("")
    # ---------------------------------------------------------------- step 4
    w("## Step 4 (D5): pixel-sensitivity table by camera set (descriptive; stored outputs)")
    w("")
    w("Definitions of `research/m1a/position_sensitivity.py` (CR-026 evidence, D-40 item 6), column B, persons and forklifts. "
      f"Check: on all 226 cameras the split function reproduces the stored SDG table exactly ({d5['check_all_226_reproduce_stored_sdg_table']}). "
      "\"Good\" = error < 1 m (stored definition); the share with error ≤ 1 m is identical to three decimals in every row and is kept in the JSON.")
    w("")
    for k, name in (("tuning", "SDG tuning cameras"), ("reporting", "SDG reporting cameras")):
        x = d5["sdg"][k]
        w(f"**{name}** ({x['cameras']} cameras, {x['gv01_points']:,} GV-01 points)")
        w("")
        w("| s_max (m/px) | Share flagged | Errors > 10 m caught | Good points lost | P99 of kept (m) |")
        w("|---|---|---|---|---|")
        for s, r in x["sensitivity_limits"].items():
            w(f"| {s} | {pct(r['flagged_share'])} | {pct(r['caught_share_of_err_gt_10m'])} | {pct(r['lost_share_of_good_lt_1m'])} | {f(r['kept']['p99_m'])} |")
        w("")
    x = d5["smartspaces"]
    w(f"**SmartSpaces** ({x['gv01_points']:,} GV-01 points): no tuning split is defined; the stored table is copied unchanged.")
    w("")
    w("| s_max (m/px) | Share flagged | Errors > 10 m caught | Good points lost | P99 of kept (m) |")
    w("|---|---|---|---|---|")
    for s, r in x["sensitivity_limits"].items():
        w(f"| {s} | {pct(r['flagged_share'])} | {pct(r['caught_share_of_err_gt_10m'])} | {pct(r['lost_share_of_good_lt_1m'])} | {f(r['kept']['p99_m'])} |")
    w("")
    return "\n".join(L)


if __name__ == "__main__":  # pragma: no cover
    p = R / "v2_diagnostics_report.md"
    p.write_text(render())
    print("wrote", p)
