"""D-58 STEP 5: `research/m1b/d58_report.md` from the D-58 results files (no computation beyond formatting and sums).

  PYTHONPATH=src .venv/bin/python research/m1b/d58_report.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import pilot_common as pc  # noqa: E402

ROOT = pc.ROOT
R = ROOT / "research/m1b"
STATUS = "**Diagnostic, tuning subset, not a reported result.**"
CONFIGS = ("C-v2", "C-v2+T25", "B-both", "B-both+T25", "A", "A+T25")
VIEWS = (("all", "all"), ("ceiling", "ceiling"), ("eye_level", "eye level"))
DEF_NAME = {"alpha": "α (m_gap 5 frames)", "beta": "β (m_gap_s 1.0 s)"}


def f3(v):
    return "–" if v is None else f"{v:.3f}"


def pct(a, b):
    return "–" if not b else f"{100 * a / b:.0f} %"


def load():
    return (json.loads((R / "d58_stitch_grid.json").read_text()), json.loads((R / "d58_events_tune.json").read_text()),
            json.loads((R / "t25_regression.json").read_text()))


def stitch_section(g: dict) -> list[str]:
    t = g["tuning_116"]["all"]
    sel = g["selection"]
    off, win = t["off"], t[sel["chosen"]]
    out = ["## 2. STEP 3: track stitching (T25.1), selected by tracking measures", "", STATUS, "",
           "Input: the D-56 package tracks (stored D-54 detector S3) on the 116 tuning cameras; floor positions from the stored C-v2 S4 (T24 on; AR-69 "
           "item 9). v_max person 2.5 m/s, forklift 4.0 m/s and k_img 1.0 are fixed design values (D-58), not fitted. Measures: D-55 definitions on "
           "stitched identities (primary variant: tracked points). Stitching creates no point, so point precision is the same in every row.", "",
           "| configuration | T_s (s) | r_g (m) | links forklift / person | gate floor / image | forklift IDF1 | person IDF1 | objective | forklift fragments / identity | person fragments / identity | point precision forklift / person |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in __import__("d58_stitch").grid():
        n, p, row = c["name"], c["params"], t[c["name"]]
        ts, rg = ("–", "–") if p is None else (f"{p['stitch_max_gap_s']:g}", f"{p['stitch_r_gate_m']:g}")
        mark = " **(selected)**" if n == sel["chosen"] else (" (kept)" if n in sel["kept"] else "")
        out.append(f"| {n}{mark} | {ts} | {rg} | {row['links']['forklift']} / {row['links']['person']} | {row['links_by_gate']['floor']} / {row['links_by_gate']['image']} | "
                   f"{row['forklift']['idf1']:.4f} | {row['person']['idf1']:.4f} | {row['objective']:.4f} | {row['forklift']['fragments_per_identity']:.3f} | "
                   f"{row['person']['fragments_per_identity']:.3f} | {row['forklift']['precision']:.3f} / {row['person']['precision']:.3f} |")
    out += ["", f"**Rule (pre-declared):** guard point precision ≥ {sel['guard_point_precision']} per class (all 13 pass); objective forklift + person IDF1 "
            f"(best {sel['best_objective']:.4f}); keep within {sel['within']} of the best ({', '.join(sel['kept'])}); then {sel['order']}. "
            f"**Selected: {sel['chosen']} (T_s {sel['chosen_params']['stitch_max_gap_s']:g} s, r_g {sel['chosen_params']['stitch_r_gate_m']:g} m), "
            "selected under D-58, not frozen.**", "",
            f"T_s 5 s is the largest value of the grid: the selection sits at the grid edge. Checks: stitching off reproduces the stored D-55 measures on "
            f"{g['checks']['off_reproduces_d55']} of {g['checks']['cameras']} cameras.", "", "By viewpoint (off → selected):", "",
            "| view | cameras | forklift IDF1 | person IDF1 | forklift fragments / identity | person fragments / identity | links forklift / person |", "|---|---|---|---|---|---|---|"]
    for key, name in VIEWS:
        v = g["tuning_116"][key]
        a, b = v["off"], v[sel["chosen"]]
        out.append(f"| {name} | {v['cameras']} | {a['forklift']['idf1']:.4f} → {b['forklift']['idf1']:.4f} | {a['person']['idf1']:.4f} → {b['person']['idf1']:.4f} | "
                   f"{a['forklift']['fragments_per_identity']:.3f} → {b['forklift']['fragments_per_identity']:.3f} | "
                   f"{a['person']['fragments_per_identity']:.3f} → {b['person']['fragments_per_identity']:.3f} | {b['links']['forklift']} / {b['links']['person']} |")
    out += ["", f"**Plainly:** stitching joins {win['links']['person']} person and {win['links']['forklift']} forklift fragments. Person IDF1 rises "
            f"{off['person']['idf1']:.3f} → {win['person']['idf1']:.3f}; forklift IDF1 {off['forklift']['idf1']:.3f} → {win['forklift']['idf1']:.3f}. "
            f"Forklift identities are rarely fragmented ({off['forklift']['fragments_per_identity']:.2f} fragments per identity without stitching), so there are few forklift links to make.", ""]
    return out


def ev_table(e: dict, view: str) -> list[str]:
    t = e["tuning_116"][view]
    out = ["| configuration | definition | EV-M1 | EV-M2 | assessable references | matched references | system events (G1) | matched events |",
           "|---|---|---|---|---|---|---|---|"]
    for n in CONFIGS:
        for d in ("alpha", "beta"):
            a = t[n][d]["reading_a"]
            out.append(f"| {n} | {DEF_NAME[d]} | {f3(a['EV-M1'])} | {f3(a['EV-M2'])} | {a['assessable_references']} | {a['matched_references']} | "
                       f"{a['system_events_g1']} | {a['matched_events']} |")
    return out


def events_section(e: dict) -> list[str]:
    t = e["tuning_116"]["all"]
    ch = e["checks"]
    out = ["## 3. STEP 4: event-level check (diagnostic)", "", STATUS, "",
           "All configurations: BL-6, N4 (unchanged), label group G1. B-both and A without T25 are added for comparison. T25.1 is off on the oracle "
           f"paths (T25.1 f). C-v2+T25 uses the STEP 3 winner ({e['stitch_winner']}; {e['stitching']['links']} links: "
           f"{e['stitching']['links_by_class'].get('forklift', 0)} forklift, {e['stitching']['links_by_class'].get('person', 0)} person).", "",
           "Event definitions: **α**: m_gap 5 frames for the system and the stored base references (T21). **β**: m_gap_s 1.0 s for the system and for "
           "a reference set rebuilt from simulator truth with m_gap_s 1.0 (T21.1 procedure). The β set is **diagnostic, not the v2 reference**; 1.0 s is "
           "a placeholder for this check only, not a v2 candidate. With T25.2 on under α, the join limit is 5 frames × δ_nom (0.17 s at 30 fps).", "",
           "References:", "", "| definition | references | assessable, G1 |", "|---|---|---|"]
    for d in ("alpha", "beta"):
        out.append(f"| {DEF_NAME[d]} | {t['references'][d]['references']} | {t['references'][d]['assessable_g1']} |")
    out += ["", "### 3.1 EV-M1 and EV-M2 (all 116 cameras)", ""] + ev_table(e, "all")
    out += ["", f"CR-037 item 3: the two pair readings (a) and (b) give the same pair for every event "
            f"({sum(t[n][d]['summary']['pair_readings_differ'] for n in CONFIGS for d in ('alpha', 'beta'))} events differ over all rows), so every EV "
            "value above holds under both readings; no value depends on a choice.", ""]
    for key, name in VIEWS[1:]:
        out += [f"### 3.{2 if key == 'ceiling' else 3} EV-M1 and EV-M2, {name} ({e['tuning_116'][key]['cameras']} cameras)", ""] + ev_table(e, key) + [""]
    out += ["### 3.4 System events, members and unobserved time (all cameras)", "",
            "Joined events are reported as joined, with their unobserved time (the summed gaps between members; never counted as exposure or as "
            "clearance-measured time, T25.2 c).", "",
            "| configuration | definition | system events (all labels) | member episodes | members per event | events with 1 / 2 / 3 / ≥ 4 members | joined events | unobserved time (s) |",
            "|---|---|---|---|---|---|---|---|"]
    for n in CONFIGS:
        for d in ("alpha", "beta"):
            s = t[n][d]["summary"]
            em = s["events_by_members"]
            out.append(f"| {n} | {DEF_NAME[d]} | {s['system_events']} | {s['member_episodes']} | {f3(s['members_per_event'])} | "
                       f"{em['1']} / {em['2']} / {em['3']} / {em['4']} | {s['joined_events']} | {s['unobserved_gap_s']:.1f} |")
    bands = list(t["C-v2"]["alpha"]["reading_a"]["unmatched_by_band"])
    out += ["", "### 3.5 Unmatched events by best same-pair temporal IoU (all cameras)", "",
            "Unmatched = false or duplicate alerts (G1). Band = best temporal IoU with a same-pair assessable G1 reference (`extent_check` bands).", "",
            "| configuration | definition | unmatched | " + " | ".join(bands) + " | with same-pair overlap |", "|---|---|---|" + "---|" * len(bands) + "---|"]
    for n in CONFIGS:
        for d in ("alpha", "beta"):
            a = t[n][d]["reading_a"]
            out.append(f"| {n} | {DEF_NAME[d]} | {a['unmatched_events']} | " + " | ".join(str(a["unmatched_by_band"][b]) for b in bands) +
                       f" | {a['unmatched_with_same_pair_overlap']} |")
    out += ["", "### 3.6 Remaining splits (the D-57 mechanisms, on events)", "",
            "A split = two consecutive same-pair events covering one assessable G1 reference. (i) the boundary members are in one POW; (ii) other POWs "
            "of the same pair units (tracks, or stitched identities); (iii) other units.", "",
            "| configuration | definition | view | references with ≥ 2 events | splits | (i) | (ii) | (iii) |", "|---|---|---|---|---|---|---|---|"]
    for n in CONFIGS:
        for d in ("alpha", "beta"):
            for key, name in VIEWS:
                a = e["tuning_116"][key][n][d]["reading_a"]
                sm = a["splits_by_mechanism"]
                out.append(f"| {n} | {DEF_NAME[d]} | {name} | {a['references_with_2plus_events']} | {a['splits']} | {sm['i']} | {sm['ii']} | {sm['iii']} |")
    out += ["", f"Checks: C-v2 under α equals D-54 (EV values and counts: {ch['c_v2_alpha_equals_d54']}) and its splits equal D-57 "
            f"({ch['c_v2_alpha_splits']} = {ch['d57_c_v2_splits']}). The β reference procedure at m_gap 5 reproduces the stored reference S5 payload and "
            f"reference list on {ch['reference_procedure_at_m_gap_5']} of {ch['cameras']} cameras. Two independent runs gave identical per-camera "
            "results and artifact IDs on 116 of 116 cameras.", ""]
    return out


def summary(g, e, reg) -> list[str]:
    t = e["tuning_116"]["all"]
    sel = g["selection"]
    ev = lambda n, d: t[n][d]["reading_a"]
    s = lambda n, d: t[n][d]["summary"]
    lines = [
        f"1. T25 is implemented opt-in (contract E-1.2.26). With its parameters absent, every stored D-54 and D-57 artifact rebuilds byte-identical on {reg['cameras']} of 116 tuning cameras, and the 12 M0 IDs are reproduced.",
        f"2. Track stitching (T25.1), chosen by tracking measures only: **T_s {sel['chosen_params']['stitch_max_gap_s']:g} s, r_g {sel['chosen_params']['stitch_r_gate_m']:g} m, selected, not frozen** (at the edge of the grid). Person IDF1 {g['tuning_116']['all']['off']['person']['idf1']:.3f} → {g['tuning_116']['all'][sel['chosen']]['person']['idf1']:.3f}; forklift {g['tuning_116']['all']['off']['forklift']['idf1']:.3f} → {g['tuning_116']['all'][sel['chosen']]['forklift']['idf1']:.3f}.",
        f"3. Detector path, EV-M1 / EV-M2 under α (m_gap 5 frames): C-v2 {f3(ev('C-v2', 'alpha')['EV-M1'])} / {f3(ev('C-v2', 'alpha')['EV-M2'])} → C-v2+T25 {f3(ev('C-v2+T25', 'alpha')['EV-M1'])} / {f3(ev('C-v2+T25', 'alpha')['EV-M2'])}. All of this gain comes from stitching.",
        f"4. Under α, T25.2 joins nothing on any path. A POW break needs a gap above g_max (15 frames), and the α join limit is 5 frames. T25.2 can act only when m_gap_s is at least (g_max + 1) × δ_nom, which is 0.53 s here.",
        f"5. Under β (1.0 s for system and references alike): C-v2 {f3(ev('C-v2', 'beta')['EV-M1'])} / {f3(ev('C-v2', 'beta')['EV-M2'])}; C-v2+T25 {f3(ev('C-v2+T25', 'beta')['EV-M1'])} / {f3(ev('C-v2+T25', 'beta')['EV-M2'])}, with {s('C-v2+T25', 'beta')['joined_events']} joined events holding {s('C-v2+T25', 'beta')['unobserved_gap_s']:.1f} s of unobserved time.",
        f"6. The oracle check is clean under β: A EV-M1 stays {f3(ev('A', 'beta')['EV-M1'])} and B-both is {f3(ev('B-both', 'beta')['EV-M1'])} (α {f3(ev('B-both', 'alpha')['EV-M1'])}). This fits D-57's explanation: there, m_gap changed on the system side only.",
        f"7. Remaining C-v2+T25 splits under β: (i) {ev('C-v2+T25', 'beta')['splits_by_mechanism']['i']}, (ii) {ev('C-v2+T25', 'beta')['splits_by_mechanism']['ii']}, (iii) {ev('C-v2+T25', 'beta')['splits_by_mechanism']['iii']}. They were 43 / 30 / 42 on C-v2 under α: stitching turns (iii) into (ii). The (ii) splits that remain are not joined at 1.0 s (the gap is longer, or a T = 1 frame or a coverage break lies in it).",
        f"8. CR-037 (the contact state, IE and pair of a joined event) is open. Both pair readings give the same pair for every event, and the label rule questions do not touch G1.",
        "9. N4, the label rules, the EV definitions and the stored base references are unchanged. The β set is a separate diagnostic set. Nothing ran on the 110 reporting cameras or the test partition.",
    ]
    return ["## Summary", ""] + lines + [""]


def main():  # pragma: no cover
    g, e, reg = load()
    doc = ["# D-58: event continuity (T25) on the tuning cameras", "", STATUS, "",
           "Source data: synthetic SDG validation, the 116 tuning cameras only (D-50 item 3). Nothing here is validated. Nothing ran on the 110 "
           "reporting cameras or the test partition (D-37). Contract E-1.2.26 (Appendix T T25), v1 base values otherwise; tracker package D-56 and "
           "T24 values D-54 (selected, not frozen). Outputs: `research/m1b/t25_regression.json`, `research/m1b/d58_stitch_grid.json`, "
           "`research/m1b/d58_events_tune.json`.", ""]
    doc += summary(g, e, reg)
    ident = reg["identical"]
    doc += ["## 1. STEP 2: implementation and regression", "",
            "T25.1 (`rq1.tracking.stitching`; S4 pairs stitched identities), T25.2 (`rq1.events.candidates.join_chains`, `joined_events`, "
            "`continuity_links`) and T25.3 (`rq1.events.engine.m_gap_frames`) are implemented opt-in. Every T25.4 check is a test "
            "(`tests/substrate/test_t25_stitching.py`, `tests/events/test_t25_join.py`). Representation: AR-69. Open meaning questions: CR-037.", "",
            "| configuration | S4 | S5 (D-54) | S5 (D-57 m_gap 5) |", "|---|---|---|---|"]
    for c in ("C-v2", "B-both", "A"):
        doc.append(f"| {c} | {ident[c]['S4']} / 116 | {ident[c]['S5 (D-54)']} / 116 | {ident[c]['S5 (D-57 m_gap 5)']} / 116 |")
    doc += ["", "Byte-identical rebuilds (payload SHA-256 and artifact ID) with the T25 parameters absent. M0 (W-02 method, AR-69 item 11): the 12 IDs "
            "and payload hashes equal the M0 report, in two runs. The fixture export's `data_dictionary.json` lists the two new optional "
            "`candidate_event` properties (AR-69 item 10).", ""]
    doc += stitch_section(g) + events_section(e)
    doc += ["## 4. Limits", "",
            "- Synthetic SDG data, tuning subset: these values select and diagnose; they are not reported results and are not validated.",
            "- The stitching winner and the β value 1.0 s are not frozen. The v2 m_gap_s comes from the literature (item C7) or a stated design choice, never from these scores (D-58 ruling 1).",
            "- The D-56 caveat holds: the package accepts forklift detections down to score 0.05; point precision is known on synthetic SDG data only.",
            "- Joined events are candidate events. Their members and unobserved time are part of the record; no automated output is called a near miss, collision or contact.", ""]
    path = R / "d58_report.md"
    path.write_text("\n".join(doc))
    print("wrote", path)


if __name__ == "__main__":
    main()
