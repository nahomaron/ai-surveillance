"""D-57 STEP 4: the D-57 report, built from the stored STEP 2 and STEP 3 results (no computation of its own).

  PYTHONPATH=src .venv/bin/python research/m1b/d57_report.py   -> research/m1b/d57_report.md
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(__file__)
S = json.load(open(os.path.join(HERE, "d57_split_diagnosis.json")))
W = json.load(open(os.path.join(HERE, "d57_mgap_sweep.json")))
VIEWS = (("all", "all"), ("ceiling", "ceiling"), ("eye_level", "eye level"))
GRID = ("5", "15", "30", "60")
LABEL = "**Diagnostic, tuning subset, not a reported result.**"
MECH = {"i": "(i) same POW (lifecycle split)", "ii": "(ii) other POW, same tracks (POW break)", "iii": "(iii) other tracks (track fragmentation)"}
BANDS = ("0", "(0, 0.1]", "(0.1, 0.2]", "(0.2, 0.3)", ">= 0.3")
LABELS = ("all", "O", "H", "PC", "NM", "UD", "CT", "IE")


def f(x, n=3):
    return "–" if x is None else f"{x:.{n}f}"


def pct(x, n=0):
    return "–" if x is None else f"{100 * x:.{n}f} %"


def summary() -> list[str]:
    c, b = S["configs"]["C-v2"]["all"], S["configs"]["B-both"]["all"]
    cm, bm = c["by_mechanism"], b["by_mechanism"]
    r = W["results"]["all"]
    sel = W["selection"]["chosen"]
    sh = W["references_sharing_an_episode"]["all"]
    x = lambda cfg, g: r[cfg][str(g)]
    return [
        "## Summary", "",
        f"1. On C-v2, most splits are **not** lifecycle splits: of {c['splits']} splits, {cm['ii']} are POW breaks (ii) and {cm['iii']} are track "
        f"fragmentation (iii), {cm['ii'] + cm['iii']} together ({pct((cm['ii'] + cm['iii']) / c['splits'])}); {cm['i']} are inside one POW (i). "
        "m_gap cannot join (ii) or (iii); that would need a contract rule (not drafted here; the Architect drafts).",
        f"2. On B-both (oracle boxes), {bm['i']} of {b['splits']} splits are lifecycle splits (i); (ii) {bm['ii']}, (iii) {bm['iii']}.",
        f"3. Lifecycle splits (i) are short: median {f(c['gap']['i']['frames']['median'], 0)} frames ({f(c['gap']['i']['seconds']['median'], 2)} s) on C-v2, "
        f"{f(b['gap']['i']['frames']['median'], 0)} frames on B-both, at 30 fps. In the gap T is 0 on {pct(c['mechanism_i']['mean_share_T0'])} of frames "
        f"(C-v2): the clearance rises to d_p or above (P false), it is not unknown.",
        f"4. m_gap sweep, C-v2: EV-M1 / EV-M2 {f(x('C-v2', 5)['EV-M1'])} / {f(x('C-v2', 5)['EV-M2'])} at 5; {f(x('C-v2', 30)['EV-M1'])} / "
        f"{f(x('C-v2', 30)['EV-M2'])} at 30; {f(x('C-v2', 60)['EV-M1'])} / {f(x('C-v2', 60)['EV-M2'])} at 60.",
        f"5. The pre-declared rule selects **m_gap = {sel} frames** (about {W['grid_seconds_at_30fps'][str(sel)]} s at 30 fps): **selected under D-57, not frozen**; "
        "it is to be checked against the literature value (item C7) before the v2 freeze.",
        f"6. The oracle check is **not** clean. At m_gap {sel}, B-both EV-M1 falls {f(x('B-both', 5)['EV-M1'])} → {f(x('B-both', sel)['EV-M1'])} "
        f"(EV-M2 {f(x('B-both', 5)['EV-M2'])} → {f(x('B-both', sel)['EV-M2'])}), and A EV-M1 falls {f(x('A', 5)['EV-M1'])} → {f(x('A', sel)['EV-M1'])}.",
        f"7. Why: the references are built once with m_gap 5 (T21.1, T21.4). A joined episode spans references that the base lifecycle keeps apart "
        f"and matches at most one. On A at m_gap {sel}, all {x('A', 5)['matched_references'] - x('A', sel)['matched_references']} lost references share "
        f"an episode with another reference ({sh['A'][str(sel)]['of_which_n4_unmatched']} N4-unmatched references share one).",
        f"8. Checks: at m_gap 5 the rebuilt S5 equals the stored S5 payload on 116 of 116 cameras for each configuration, and EV values equal D-54. "
        f"C-v2 references with 2+ episodes = {S['checks']['d54_value']} (= D-54).",
        "9. N4, the label rules, the tracker and every contract value are unchanged. Nothing ran on the 110 reporting cameras or the test partition.",
        ""]


def step2() -> list[str]:
    L = ["## 1. STEP 2: why do episodes split?", "", LABEL, "",
         "Stored D-54 outputs only (no new run), BL-6, G1, 116 tuning cameras. Definitions in `research/m1b/d57_split.py` and AR-68 item 4: "
         "an episode covers a reference if it has the same resolved identity pair and temporal IoU > 0 (the D-50 definition); "
         "for each reference covered by two or more episodes, each consecutive pair of covering episodes (in start-time order) is one split.", "",
         "### 1.1 Splits by mechanism", "",
         "| configuration | view | references with ≥ 2 episodes | splits | (i) same POW | (ii) other POW, same tracks | (iii) other tracks | (ii) + (iii) share |",
         "|---|---|---|---|---|---|---|---|"]
    for cfg in ("C-v2", "B-both"):
        for v, vn in VIEWS:
            x = S["configs"][cfg][v]
            m = x["by_mechanism"]
            refs = S["configs"][cfg]["references_with_2plus_episodes"] if v == "all" else ""
            L.append(f"| {cfg} | {vn} | {refs} | {x['splits']} | {m['i']} | {m['ii']} | {m['iii']} | "
                     f"{pct((m['ii'] + m['iii']) / x['splits']) if x['splits'] else '–'} |")
    c = S["configs"]["C-v2"]["all"]["by_mechanism"]
    L += ["", f"**Plainly:** on C-v2 (the detector path), mechanisms (ii) and (iii) cause most splits ({c['ii'] + c['iii']} of "
          f"{sum(c.values())}). m_gap acts only inside one POW, so it cannot fix those. Joining across POWs or across tracks would need a contract rule; "
          "nothing is drafted here. On B-both (oracle boxes), lifecycle splits (i) dominate.", "",
          "### 1.2 Gap between consecutive episodes (all views)", "",
          "Gap = start of the later episode − end of the earlier one. Frame rate: 30 fps on every camera (1 / delta_nom_s). A negative gap means "
          "the episodes overlap (5 C-v2 splits, all (iii)).", "",
          "| configuration | mechanism | n | median frames | P75 | P90 | max | median s | P75 s | P90 s | max s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for cfg in ("C-v2", "B-both"):
        for k in ("i", "ii", "iii"):
            g = S["configs"][cfg]["all"]["gap"][k]
            fr, se = g["frames"], g["seconds"]
            L.append(f"| {cfg} | {MECH[k]} | {fr['n']} | {f(fr['median'], 1)} | {f(fr['p75'], 1)} | {f(fr['p90'], 1)} | {f(fr['max'], 0)} | "
                     f"{f(se['median'], 2)} | {f(se['p75'], 2)} | {f(se['p90'], 2)} | {f(se['max'], 2)} |")
    L += ["", "Mechanism (i) gap by view (frames: median, P75, P90, max):", "", "| configuration | view | n | median | P75 | P90 | max | ≤ 15 | ≤ 30 | ≤ 60 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for cfg in ("C-v2", "B-both"):
        for v, vn in VIEWS:
            x = S["configs"][cfg][v]
            fr = x["gap"]["i"]["frames"]
            at = x["mechanism_i"]["gap_frames_at_most"]
            L.append(f"| {cfg} | {vn} | {fr['n']} | {f(fr['median'], 1)} | {f(fr['p75'], 1)} | {f(fr['p90'], 1)} | {f(fr['max'], 0)} | {at['15']} | {at['30']} | {at['60']} |")
    L += ["", "(≤ n: gaps of at most n frames. A gap is bridged under T9.7 (a) when each maximal non-true run in it is ≤ m_gap; a gap that "
          "contains a discarded short window (T = 1 frames) can be joined at a smaller m_gap than its length.)", "",
          "### 1.3 Inside the gap, mechanism (i)", "",
          "| measure | C-v2 | B-both |", "|---|---|---|"]
    ci, bi = S["configs"]["C-v2"]["all"]["mechanism_i"], S["configs"]["B-both"]["all"]["mechanism_i"]
    rows = [("splits (i)", S["configs"]["C-v2"]["all"]["by_mechanism"]["i"], S["configs"]["B-both"]["all"]["by_mechanism"]["i"]),
            ("mean share of gap frames with T = 0", pct(ci["mean_share_T0"], 1), pct(bi["mean_share_T0"], 1)),
            ("mean share with T unknown", pct(ci["mean_share_T_unknown"], 1), pct(bi["mean_share_T_unknown"], 1)),
            ("mean share with T = 1 (discarded window shorter than t_min)", pct(ci["mean_share_T1"], 1), pct(bi["mean_share_T1"], 1)),
            ("gaps with any T = 0 frame", ci["gaps_with_any_T0"], bi["gaps_with_any_T0"]),
            ("mean share of gap frames with Q sufficient", pct(ci["mean_share_q_sufficient"], 1), pct(bi["mean_share_q_sufficient"], 1))]
    for k in sorted(set(ci["q_state_in_gap"]) | set(bi["q_state_in_gap"])):
        rows.append((f"gaps with Q {k} on all gap frames" if k != "mixed" else "gaps with Q mixed", ci["q_state_in_gap"].get(k, 0), bi["q_state_in_gap"].get(k, 0)))
    for k in sorted(set(ci["flags_true_before"]) | set(bi["flags_true_before"])):
        rows.append((f"flags true on the last frame before the gap: {k}", ci["flags_true_before"].get(k, 0), bi["flags_true_before"].get(k, 0)))
    for side in ("before", "after"):
        for k, name in (("below_d_pc", "< d_pc (1.0 m)"), ("d_pc_to_d_p", "d_pc to < d_p (1.0–2.0 m)"), ("at_or_above_d_p", "≥ d_p (2.0 m)"), ("null", "null")):
            rows.append((f"clearance {side} the gap {name}", ci[f"clearance_{side}"][k], bi[f"clearance_{side}"][k]))
    L += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    nb = S["configs"]["B-both"]["all"]["by_mechanism"]["i"]
    L += ["", "Reading: the typical lifecycle split is P (with X) true at a clearance between d_pc and d_p, then a short run where the clearance is at "
          f"or above d_p (T = 0, not unknown), then P again. On B-both, Q is insufficient on every gap frame in {bi['q_state_in_gap'].get('insufficient', 0)} "
          f"of {nb} gaps.", ""]
    return L


def step3() -> list[str]:
    sel = W["selection"]
    L = ["## 2. STEP 3: m_gap sweep", "", LABEL, "",
         "S5 onward only, on the stored D-54 S4 artifacts (C-v2, B-both) and the stored T-21 base S4 (A). Grid m_gap_frames ∈ {5 (v1), 15, 30, 60} "
         "(about 0.17, 0.5, 1.0, 2.0 s at 30 fps). Every other rule_configuration value is the v1 base value. N4, G1, the stored T-21 BL-6 references, "
         "as the pilot. The rule_configuration IDs (one per value, shared by the three configurations because their rule values are identical; "
         "they differ by S4):", ""]
    for g in GRID:
        L.append(f"- m_gap {g}: `{W['rule_configuration_ids']['C-v2'][g][0]}`" + (" (= the stored v1 BL-6 ID)" if g == "5" else ""))
    L += ["", "### 2.1 Event metrics", "",
          "| configuration | view | m_gap | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events | references with ≥ 2 episodes |",
          "|---|---|---|---|---|---|---|---|---|"]
    for cfg in ("C-v2", "B-both", "A"):
        for v, vn in VIEWS:
            for g in GRID:
                x = W["results"][v][cfg][g]
                L.append(f"| {cfg} | {vn} | {g} | {f(x['EV-M1'])} | {x['matched_references']} / {x['assessable_references']} | {f(x['EV-M2'])} | "
                         f"{x['matched_events']} / {x['system_events']} | {x['unmatched_events']} | {x['references_with_2plus_episodes']} |")
    L += ["", "### 2.2 Unmatched events by best same-pair temporal IoU (D-50 bands), all views", "",
          "| configuration | m_gap | unmatched | " + " | ".join(BANDS) + " | with same-pair overlap |", "|---|---|---|" + "---|" * len(BANDS) + "---|"]
    for cfg in ("C-v2", "B-both", "A"):
        for g in GRID:
            x = W["results"]["all"][cfg][g]
            L.append(f"| {cfg} | {g} | {x['unmatched_events']} | " + " | ".join(str(x["unmatched_by_band"][b]) for b in BANDS) +
                     f" | {x['unmatched_with_same_pair_overlap']} |")
    L += ["", "### 2.3 Candidate-event counts per label (T10.6, S_VIEW, recording scope, summed), all views", "",
          "Labels overlap; `all` counts every event. S_POSS and S_LINK are equal to S_VIEW on these single-camera runs.", "",
          "| configuration | m_gap | " + " | ".join(LABELS) + " |", "|---|---|" + "---|" * len(LABELS)]
    for cfg in ("C-v2", "B-both", "A"):
        for g in GRID:
            x = W["results"]["all"][cfg][g]["candidate_event_counts"]
            L.append(f"| {cfg} | {g} | " + " | ".join(str(x.get(f"S_VIEW|{k}", 0)) for k in LABELS) + " |")
    L += ["", "### 2.4 Selection (pre-declared, C-v2, all 116 cameras)", "",
          f"1. Keep EV-M1 ≥ EV-M1(5) − 0.02 = {f(sel['ev_m1_floor'], 4)}: kept {', '.join(map(str, sel['kept']))}.",
          f"2. Highest EV-M2 among them: {f(sel['best_ev_m2'], 4)}.",
          f"3. Within 0.005 of it: {', '.join(map(str, sel['tied']))}; the smaller m_gap is chosen.", "",
          f"**Chosen: m_gap = {sel['chosen']} frames. Selected under D-57, not frozen.** It is checked against the literature value (item C7) before the v2 freeze.",
          "", "### 2.5 Oracle-path check at the chosen value", ""]
    c = sel["chosen"]
    sh = W["references_sharing_an_episode"]
    L += ["| configuration | EV-M1 at 5 | EV-M1 at chosen | EV-M2 at 5 | EV-M2 at chosen | matched references at 5 → at chosen | references sharing an episode (N4-unmatched) at 5 | at chosen |",
          "|---|---|---|---|---|---|---|---|"]
    for cfg in ("C-v2", "B-both", "A"):
        a, b = W["results"]["all"][cfg]["5"], W["results"]["all"][cfg][str(c)]
        L.append(f"| {cfg} | {f(a['EV-M1'])} | {f(b['EV-M1'])} | {f(a['EV-M2'])} | {f(b['EV-M2'])} | {a['matched_references']} → {b['matched_references']} | "
                 f"{sh['all'][cfg]['5']['references_sharing_an_episode']} ({sh['all'][cfg]['5']['of_which_n4_unmatched']}) | "
                 f"{sh['all'][cfg][str(c)]['references_sharing_an_episode']} ({sh['all'][cfg][str(c)]['of_which_n4_unmatched']}) |")
    L += ["", "Joining **does** lower EV-M1 on the oracle paths (B-both, A), while EV-M2 rises. A reference \"shares an episode\" when an episode that "
          "covers it (same pair, IoU > 0) also covers another reference. The references are built once at the base values, m_gap 5 included "
          "(T21.1), and stay fixed in sweeps (T21.4). So a system episode joined at a larger m_gap can span two references that the base lifecycle keeps "
          "apart, and it matches at most one of them under N4. On A every lost reference is such a case. This is reported, not resolved: N4 and the "
          "reference definition are unchanged.", ""]
    ch = W["checks"]
    L += ["## 3. Checks", "",
          f"- At m_gap 5 the rebuilt S5 payload equals the stored S5 payload: C-v2 {ch['m_gap5_payload_equals_stored_s5']['C-v2']}, "
          f"B-both {ch['m_gap5_payload_equals_stored_s5']['B-both']}, A {ch['m_gap5_payload_equals_stored_s5']['A']} of 116 cameras; "
          "the rule_configuration ID equals the stored one on all of them.",
          f"- At m_gap 5 EV-M1, EV-M2 and their counts equal D-54 (`d54_c_v2_tune.json`, `d54_b_v2_tune.json`): "
          + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in ch["m_gap5_ev_equals_d54"].items()) + ".",
          f"- STEP 2: C-v2 references with two or more episodes = {S['checks']['d54_value']}, as in D-54.",
          f"- Runtime: STEP 3 estimate on 2 cameras 0.06 h serial (limit 2 h); the sweep took {round(W['runtime_s'] / 60, 1)} min of camera time "
          "(3 workers).",
          f"- Code commit of the sweep: {', '.join(W['code_commit'])}.", ""]
    return L


def main():
    L = ["# D-57: why episodes split, and an m_gap sweep (tuning cameras)", "", LABEL, "",
         "Source data: synthetic SDG validation, the 116 tuning cameras only (D-50 item 3, D-57 ruling 8). Nothing here is validated; nothing runs on "
         "the 110 reporting cameras or the test partition (D-37). Contract E-1.2.25, v1 base values except lifecycle.m_gap_frames in STEP 3. "
         "Outputs: `research/m1b/d57_split_diagnosis.json`, `research/m1b/d57_mgap_sweep.json`.", ""]
    L += summary() + step2() + step3()
    p = os.path.join(HERE, "d57_report.md")
    with open(p, "w") as fh:
        fh.write("\n".join(L).rstrip() + "\n")
    print("wrote", p)


if __name__ == "__main__":
    main()
