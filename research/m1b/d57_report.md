# D-57: why episodes split, and an m_gap sweep (tuning cameras)

**Diagnostic, tuning subset, not a reported result.**

Source data: synthetic SDG validation, the 116 tuning cameras only (D-50 item 3, D-57 ruling 8). Nothing here is validated; nothing runs on the 110 reporting cameras or the test partition (D-37). Contract E-1.2.25, v1 base values except lifecycle.m_gap_frames in STEP 3. Outputs: `research/m1b/d57_split_diagnosis.json`, `research/m1b/d57_mgap_sweep.json`.

## Summary

1. On C-v2, most splits are **not** lifecycle splits: of 115 splits, 30 are POW breaks (ii) and 42 are track fragmentation (iii), 72 together (63 %); 43 are inside one POW (i). m_gap cannot join (ii) or (iii); that would need a contract rule (not drafted here; the Architect drafts).
2. On B-both (oracle boxes), 81 of 87 splits are lifecycle splits (i); (ii) 6, (iii) 0.
3. Lifecycle splits (i) are short: median 10 frames (0.33 s) on C-v2, 14 frames on B-both, at 30 fps. In the gap T is 0 on 97 % of frames (C-v2): the clearance rises to d_p or above (P false), it is not unknown.
4. m_gap sweep, C-v2: EV-M1 / EV-M2 0.578 / 0.329 at 5; 0.630 / 0.459 at 30; 0.622 / 0.462 at 60.
5. The pre-declared rule selects **m_gap = 30 frames** (about 1.0 s at 30 fps): **selected under D-57, not frozen**; it is to be checked against the literature value (item C7) before the v2 freeze.
6. The oracle check is **not** clean. At m_gap 30, B-both EV-M1 falls 0.926 → 0.867 (EV-M2 0.571 → 0.848), and A EV-M1 falls 1.000 → 0.933.
7. Why: the references are built once with m_gap 5 (T21.1, T21.4). A joined episode spans references that the base lifecycle keeps apart and matches at most one. On A at m_gap 30, all 9 lost references share an episode with another reference (9 N4-unmatched references share one).
8. Checks: at m_gap 5 the rebuilt S5 equals the stored S5 payload on 116 of 116 cameras for each configuration, and EV values equal D-54. C-v2 references with 2+ episodes = 69 (= D-54).
9. N4, the label rules, the tracker and every contract value are unchanged. Nothing ran on the 110 reporting cameras or the test partition.

## 1. STEP 2: why do episodes split?

**Diagnostic, tuning subset, not a reported result.**

Stored D-54 outputs only (no new run), BL-6, G1, 116 tuning cameras. Definitions in `research/m1b/d57_split.py` and AR-68 item 4: an episode covers a reference if it has the same resolved identity pair and temporal IoU > 0 (the D-50 definition); for each reference covered by two or more episodes, each consecutive pair of covering episodes (in start-time order) is one split.

### 1.1 Splits by mechanism

| configuration | view | references with ≥ 2 episodes | splits | (i) same POW | (ii) other POW, same tracks | (iii) other tracks | (ii) + (iii) share |
|---|---|---|---|---|---|---|---|
| C-v2 | all | 69 | 115 | 43 | 30 | 42 | 63 % |
| C-v2 | ceiling |  | 73 | 31 | 18 | 24 | 58 % |
| C-v2 | eye level |  | 42 | 12 | 12 | 18 | 71 % |
| B-both | all | 64 | 87 | 81 | 6 | 0 | 7 % |
| B-both | ceiling |  | 40 | 40 | 0 | 0 | 0 % |
| B-both | eye level |  | 47 | 41 | 6 | 0 | 13 % |

**Plainly:** on C-v2 (the detector path), mechanisms (ii) and (iii) cause most splits (72 of 115). m_gap acts only inside one POW, so it cannot fix those. Joining across POWs or across tracks would need a contract rule; nothing is drafted here. On B-both (oracle boxes), lifecycle splits (i) dominate.

### 1.2 Gap between consecutive episodes (all views)

Gap = start of the later episode − end of the earlier one. Frame rate: 30 fps on every camera (1 / delta_nom_s). A negative gap means the episodes overlap (5 C-v2 splits, all (iii)).

| configuration | mechanism | n | median frames | P75 | P90 | max | median s | P75 s | P90 s | max s |
|---|---|---|---|---|---|---|---|---|---|---|
| C-v2 | (i) same POW (lifecycle split) | 43 | 10.0 | 15.0 | 26.8 | 41 | 0.33 | 0.50 | 0.89 | 1.37 |
| C-v2 | (ii) other POW, same tracks (POW break) | 30 | 27.0 | 41.2 | 48.8 | 83 | 0.90 | 1.38 | 1.63 | 2.77 |
| C-v2 | (iii) other tracks (track fragmentation) | 42 | 37.0 | 54.8 | 80.4 | 140 | 1.23 | 1.82 | 2.68 | 4.67 |
| B-both | (i) same POW (lifecycle split) | 81 | 14.0 | 27.0 | 41.0 | 63 | 0.47 | 0.90 | 1.37 | 2.10 |
| B-both | (ii) other POW, same tracks (POW break) | 6 | 53.5 | 99.8 | 127.0 | 139 | 1.78 | 3.32 | 4.23 | 4.63 |
| B-both | (iii) other tracks (track fragmentation) | 0 | – | – | – | – | – | – | – | – |

Mechanism (i) gap by view (frames: median, P75, P90, max):

| configuration | view | n | median | P75 | P90 | max | ≤ 15 | ≤ 30 | ≤ 60 |
|---|---|---|---|---|---|---|---|---|---|
| C-v2 | all | 43 | 10.0 | 15.0 | 26.8 | 41 | 32 | 40 | 43 |
| C-v2 | ceiling | 31 | 10.0 | 15.5 | 28.0 | 41 | 23 | 29 | 31 |
| C-v2 | eye level | 12 | 9.0 | 13.0 | 18.7 | 40 | 9 | 11 | 12 |
| B-both | all | 81 | 14.0 | 27.0 | 41.0 | 63 | 43 | 64 | 80 |
| B-both | ceiling | 40 | 14.5 | 28.8 | 45.1 | 63 | 21 | 30 | 39 |
| B-both | eye level | 41 | 13.0 | 23.0 | 34.0 | 46 | 22 | 34 | 41 |

(≤ n: gaps of at most n frames. A gap is bridged under T9.7 (a) when each maximal non-true run in it is ≤ m_gap; a gap that contains a discarded short window (T = 1 frames) can be joined at a smaller m_gap than its length.)

### 1.3 Inside the gap, mechanism (i)

| measure | C-v2 | B-both |
|---|---|---|
| splits (i) | 43 | 81 |
| mean share of gap frames with T = 0 | 97.4 % | 93.1 % |
| mean share with T unknown | 1.9 % | 5.7 % |
| mean share with T = 1 (discarded window shorter than t_min) | 0.7 % | 1.1 % |
| gaps with any T = 0 frame | 43 | 80 |
| mean share of gap frames with Q sufficient | 52.9 % | 30.9 % |
| gaps with Q insufficient on all gap frames | 7 | 56 |
| gaps with Q mixed | 25 | 0 |
| gaps with Q sufficient on all gap frames | 11 | 25 |
| flags true on the last frame before the gap: C | 0 | 1 |
| flags true on the last frame before the gap: P | 2 | 10 |
| flags true on the last frame before the gap: P+C | 0 | 3 |
| flags true on the last frame before the gap: P+X | 39 | 59 |
| flags true on the last frame before the gap: P+X+C | 2 | 8 |
| clearance before the gap < d_pc (1.0 m) | 0 | 11 |
| clearance before the gap d_pc to < d_p (1.0–2.0 m) | 43 | 69 |
| clearance before the gap ≥ d_p (2.0 m) | 0 | 1 |
| clearance before the gap null | 0 | 0 |
| clearance after the gap < d_pc (1.0 m) | 0 | 6 |
| clearance after the gap d_pc to < d_p (1.0–2.0 m) | 40 | 61 |
| clearance after the gap ≥ d_p (2.0 m) | 3 | 14 |
| clearance after the gap null | 0 | 0 |

Reading: the typical lifecycle split is P (with X) true at a clearance between d_pc and d_p, then a short run where the clearance is at or above d_p (T = 0, not unknown), then P again. On B-both, Q is insufficient on every gap frame in 56 of 81 gaps.

## 2. STEP 3: m_gap sweep

**Diagnostic, tuning subset, not a reported result.**

S5 onward only, on the stored D-54 S4 artifacts (C-v2, B-both) and the stored T-21 base S4 (A). Grid m_gap_frames ∈ {5 (v1), 15, 30, 60} (about 0.17, 0.5, 1.0, 2.0 s at 30 fps). Every other rule_configuration value is the v1 base value. N4, G1, the stored T-21 BL-6 references, as the pilot. The rule_configuration IDs (one per value, shared by the three configurations because their rule values are identical; they differ by S4):

- m_gap 5: `rcf_l2jqmbmovogf6zvgwcxyrs6qvx` (= the stored v1 BL-6 ID)
- m_gap 15: `rcf_vchrhfs6dpndfhacer3nwbr4zt`
- m_gap 30: `rcf_eyfmdco2airk7xmfkuq77vkdlm`
- m_gap 60: `rcf_olwdd3bvytmg6gf45fefwo76wh`

### 2.1 Event metrics

| configuration | view | m_gap | EV-M1 | matched / assessable references | EV-M2 | matched / system events | unmatched events | references with ≥ 2 episodes |
|---|---|---|---|---|---|---|---|---|
| C-v2 | all | 5 | 0.578 | 78 / 135 | 0.329 | 78 / 237 | 159 | 69 |
| C-v2 | all | 15 | 0.607 | 82 / 135 | 0.410 | 82 / 200 | 118 | 56 |
| C-v2 | all | 30 | 0.630 | 85 / 135 | 0.459 | 85 / 185 | 100 | 52 |
| C-v2 | all | 60 | 0.622 | 84 / 135 | 0.462 | 84 / 182 | 98 | 52 |
| C-v2 | ceiling | 5 | 0.781 | 50 / 64 | 0.368 | 50 / 136 | 86 | 42 |
| C-v2 | ceiling | 15 | 0.797 | 51 / 64 | 0.464 | 51 / 110 | 59 | 32 |
| C-v2 | ceiling | 30 | 0.828 | 53 / 64 | 0.535 | 53 / 99 | 46 | 30 |
| C-v2 | ceiling | 60 | 0.812 | 52 / 64 | 0.542 | 52 / 96 | 44 | 30 |
| C-v2 | eye level | 5 | 0.394 | 28 / 71 | 0.277 | 28 / 101 | 73 | 27 |
| C-v2 | eye level | 15 | 0.437 | 31 / 71 | 0.344 | 31 / 90 | 59 | 24 |
| C-v2 | eye level | 30 | 0.451 | 32 / 71 | 0.372 | 32 / 86 | 54 | 22 |
| C-v2 | eye level | 60 | 0.451 | 32 / 71 | 0.372 | 32 / 86 | 54 | 22 |
| B-both | all | 5 | 0.926 | 125 / 135 | 0.571 | 125 / 219 | 94 | 64 |
| B-both | all | 15 | 0.889 | 120 / 135 | 0.702 | 120 / 171 | 51 | 36 |
| B-both | all | 30 | 0.867 | 117 / 135 | 0.848 | 117 / 138 | 21 | 15 |
| B-both | all | 60 | 0.859 | 116 / 135 | 0.943 | 116 / 123 | 7 | 6 |
| B-both | ceiling | 5 | 0.953 | 61 / 64 | 0.587 | 61 / 104 | 43 | 33 |
| B-both | ceiling | 15 | 0.906 | 58 / 64 | 0.725 | 58 / 80 | 22 | 16 |
| B-both | ceiling | 30 | 0.859 | 55 / 64 | 0.887 | 55 / 62 | 7 | 4 |
| B-both | ceiling | 60 | 0.844 | 54 / 64 | 1.000 | 54 / 54 | 0 | 0 |
| B-both | eye level | 5 | 0.901 | 64 / 71 | 0.557 | 64 / 115 | 51 | 31 |
| B-both | eye level | 15 | 0.873 | 62 / 71 | 0.681 | 62 / 91 | 29 | 20 |
| B-both | eye level | 30 | 0.873 | 62 / 71 | 0.816 | 62 / 76 | 14 | 11 |
| B-both | eye level | 60 | 0.873 | 62 / 71 | 0.899 | 62 / 69 | 7 | 6 |
| A | all | 5 | 1.000 | 135 / 135 | 0.944 | 135 / 143 | 8 | 8 |
| A | all | 15 | 0.933 | 126 / 135 | 0.947 | 126 / 133 | 7 | 8 |
| A | all | 30 | 0.933 | 126 / 135 | 0.947 | 126 / 133 | 7 | 8 |
| A | all | 60 | 0.874 | 118 / 135 | 0.944 | 118 / 125 | 7 | 8 |
| A | ceiling | 5 | 1.000 | 64 / 64 | 1.000 | 64 / 64 | 0 | 0 |
| A | ceiling | 15 | 0.922 | 59 / 64 | 1.000 | 59 / 59 | 0 | 0 |
| A | ceiling | 30 | 0.922 | 59 / 64 | 1.000 | 59 / 59 | 0 | 0 |
| A | ceiling | 60 | 0.844 | 54 / 64 | 1.000 | 54 / 54 | 0 | 0 |
| A | eye level | 5 | 1.000 | 71 / 71 | 0.899 | 71 / 79 | 8 | 8 |
| A | eye level | 15 | 0.944 | 67 / 71 | 0.905 | 67 / 74 | 7 | 8 |
| A | eye level | 30 | 0.944 | 67 / 71 | 0.905 | 67 / 74 | 7 | 8 |
| A | eye level | 60 | 0.901 | 64 / 71 | 0.901 | 64 / 71 | 7 | 8 |

### 2.2 Unmatched events by best same-pair temporal IoU (D-50 bands), all views

| configuration | m_gap | unmatched | 0 | (0, 0.1] | (0.1, 0.2] | (0.2, 0.3) | >= 0.3 | with same-pair overlap |
|---|---|---|---|---|---|---|---|---|
| C-v2 | 5 | 159 | 10 | 66 | 47 | 34 | 2 | 149 |
| C-v2 | 15 | 118 | 6 | 42 | 41 | 27 | 2 | 112 |
| C-v2 | 30 | 100 | 3 | 37 | 31 | 24 | 5 | 97 |
| C-v2 | 60 | 98 | 2 | 36 | 30 | 24 | 6 | 96 |
| B-both | 5 | 94 | 7 | 44 | 21 | 17 | 5 | 87 |
| B-both | 15 | 51 | 6 | 21 | 6 | 13 | 5 | 45 |
| B-both | 30 | 21 | 3 | 4 | 4 | 6 | 4 | 18 |
| B-both | 60 | 7 | 0 | 1 | 2 | 2 | 2 | 7 |
| A | 5 | 8 | 0 | 0 | 3 | 2 | 3 | 8 |
| A | 15 | 7 | 0 | 0 | 2 | 2 | 3 | 7 |
| A | 30 | 7 | 0 | 0 | 2 | 2 | 3 | 7 |
| A | 60 | 7 | 0 | 0 | 2 | 2 | 3 | 7 |

### 2.3 Candidate-event counts per label (T10.6, S_VIEW, recording scope, summed), all views

Labels overlap; `all` counts every event. S_POSS and S_LINK are equal to S_VIEW on these single-camera runs.

| configuration | m_gap | all | O | H | PC | NM | UD | CT | IE |
|---|---|---|---|---|---|---|---|---|---|
| C-v2 | 5 | 237 | 9 | 224 | 192 | 52 | 89 | 5 | 155 |
| C-v2 | 15 | 200 | 9 | 187 | 173 | 39 | 81 | 5 | 132 |
| C-v2 | 30 | 185 | 9 | 173 | 160 | 39 | 78 | 5 | 124 |
| C-v2 | 60 | 182 | 9 | 170 | 160 | 39 | 78 | 5 | 123 |
| B-both | 5 | 219 | 1 | 214 | 181 | 31 | 20 | 3 | 168 |
| B-both | 15 | 171 | 1 | 168 | 154 | 22 | 19 | 2 | 131 |
| B-both | 30 | 138 | 0 | 137 | 133 | 16 | 19 | 2 | 109 |
| B-both | 60 | 123 | 0 | 123 | 122 | 14 | 19 | 2 | 100 |
| A | 5 | 143 | 0 | 143 | 141 | 7 | 25 | 7 | 109 |
| A | 15 | 133 | 0 | 133 | 132 | 7 | 25 | 7 | 102 |
| A | 30 | 133 | 0 | 133 | 132 | 7 | 25 | 7 | 102 |
| A | 60 | 125 | 0 | 125 | 125 | 7 | 25 | 7 | 97 |

### 2.4 Selection (pre-declared, C-v2, all 116 cameras)

1. Keep EV-M1 ≥ EV-M1(5) − 0.02 = 0.5578: kept 5, 15, 30, 60.
2. Highest EV-M2 among them: 0.4615.
3. Within 0.005 of it: 30, 60; the smaller m_gap is chosen.

**Chosen: m_gap = 30 frames. Selected under D-57, not frozen.** It is checked against the literature value (item C7) before the v2 freeze.

### 2.5 Oracle-path check at the chosen value

| configuration | EV-M1 at 5 | EV-M1 at chosen | EV-M2 at 5 | EV-M2 at chosen | matched references at 5 → at chosen | references sharing an episode (N4-unmatched) at 5 | at chosen |
|---|---|---|---|---|---|---|---|
| C-v2 | 0.578 | 0.630 | 0.329 | 0.459 | 78 → 85 | 8 (3) | 14 (4) |
| B-both | 0.926 | 0.867 | 0.571 | 0.848 | 125 → 117 | 12 (3) | 24 (12) |
| A | 1.000 | 0.933 | 0.944 | 0.947 | 135 → 126 | 0 (0) | 20 (9) |

Joining **does** lower EV-M1 on the oracle paths (B-both, A), while EV-M2 rises. A reference "shares an episode" when an episode that covers it (same pair, IoU > 0) also covers another reference. The references are built once at the base values, m_gap 5 included (T21.1), and stay fixed in sweeps (T21.4). So a system episode joined at a larger m_gap can span two references that the base lifecycle keeps apart, and it matches at most one of them under N4. On A every lost reference is such a case. This is reported, not resolved: N4 and the reference definition are unchanged.

## 3. Checks

- At m_gap 5 the rebuilt S5 payload equals the stored S5 payload: C-v2 116, B-both 116, A 116 of 116 cameras; the rule_configuration ID equals the stored one on all of them.
- At m_gap 5 EV-M1, EV-M2 and their counts equal D-54 (`d54_c_v2_tune.json`, `d54_b_v2_tune.json`): A yes, B-both yes, C-v2 yes.
- STEP 2: C-v2 references with two or more episodes = 69, as in D-54.
- Runtime: STEP 3 estimate on 2 cameras 0.06 h serial (limit 2 h); the sweep took 5.5 min of camera time (3 workers).
- Code commit of the sweep: fd2e3e8df421303673de8752e482605a03cd1830.
