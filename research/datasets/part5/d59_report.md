# D-59 report — additional non-duplicate data, and a proposed testing and tuning plan

**For:** the Owner and the Research Architect. **Date:** 24 Nov 2026. **Branch:** `m0-implementation`.
**Authority:** Owner instruction D-59 (24 Nov 2026): cap raised to 60 GB; download whatever unique data can be obtained; propose how it enters testing and tuning.
**Status words:** everything below is *implemented* (downloaded, hash-checked, screened). Nothing is *empirically validated*. No system output exists on the new data. The plan in section 6 is a **proposal**; nothing in it is applied.
**Records:** `research/datasets/qualification.md` Part 5 (written before download), `research/datasets/part5/` (scripts and JSON), CR-036, D-59, D-60.

---

## 1. Summary

- **Downloaded:** 11 synthetic `PhysicalAI-SmartSpaces` `MTMC_Tracking_2026` scenes, **118 cameras (one video each), all 300 s at 30 fps** (one scene 309 s), with ground truth and calibration. Every file equals the publisher's SHA-256.
- **Why it is not a duplicate:**
  - No re-render was taken. The card names 001, 003, 005, 007, 021 and 024 as Cosmos Transfer re-renders, and each has byte-identical ground truth to its source.
  - **7 scenes are in 6 warehouse layouts that RQ1 has never seen.** Until now every held recording, SDG and SmartSpaces alike, came from a single layout (`Warehouse_000`'s, plus the single SDG layout family).
  - The other **4 scenes are new scenarios in `Warehouse_000`'s layout**, with 8 to 9 forklifts and 52 to 60 people each.
- **Rejected by the pre-declared screen:** 6 candidate new-layout scenes (008, 009, 012, 013, 014, 015). They contain people with humanoids and transporters but **no forklift**, so they can give no E1 pair. Only their small ground-truth files were downloaded.
- **Budget:** held 51.45 GB of 60 GB (was 30.62 GB). 8.05 GB of the cap is unused.
- **What it changes:** the new layouts make a **held-out-layout** result possible for the first time. Today's claims are limited to "held-out runs of the same synthetic layout" (D-20).
- **What it does not change:** X0b (the frozen split), the 116 tuning and 110 reporting cameras, the D-37 test reservation and the D-58 stop are untouched.

## 2. What was done, in order

| Step | Commit | What |
|---|---|---|
| 1 | `699836e` | §0 row D-59 (60 GB). Qualification Part 5 written **before any download**: source, licence, uniqueness evidence, candidate list with every SHA-256, screen rule, tier-2 draw (seed 2026112459). CR-036 opened. |
| 2 | `0b98265` | Screen files of all 17 candidates (51 files, 2.64 GB, 0 mismatches). Screen result and the final selection recorded **before any video download**. |
| 3 | this report's commit | 118 videos (18,198,933,567 bytes), 0 mismatches. Held total measured afterwards: 51,454,367,313 bytes (plan + 34 KB of fetch logs). Frame-interval and frame-count checks; this report; D-60. |

- **Source:** `nvidia/PhysicalAI-SmartSpaces`, revision `d38193b`. This is the revision pinned in Part 1 and still the Hub head.
- **Licence:** CC BY 4.0, the same licence row as Part 1.
- **Data held:** outside git under `data/raw/smartspaces/MTMC_Tracking_2026/`.

## 3. Selection

### 3.1 Uniqueness (evidence: Git-LFS SHA-256 of `map.png` and `ground_truth.json`)

| Group | Scenes | Decision |
|---|---|---|
| Re-renders (identical ground truth to a source scene) | 001, 003, 005, 007, 021, 024 | not taken (001 was already held) |
| Same layout as the held `Warehouse_000` | 002, 004, 006, 020 (sources) | tier 2 |
| Other layouts | 008, 009, 010, 011, 012, 013, 014, 015, 016, 017, 018, 019, 022 | tier 1 |
| Test split, no ground truth | 023, 025 | not taken |
| Real scenes | 026, 027 | already held under D-24 b |

### 3.2 Ground-truth screen

**Rule (declared before download):** a scene qualifies when at least one frame holds a Forklift and a Person. PalletTruck does not count as a forklift (D-22).

| Scene | Tier | Layout | Cameras | Forklifts | People | Frames with both (of 9,000) | Cameras seeing both |
|---|---|---|---|---|---|---|---|
| 010 | 1 | L-010 | 11 | 3 | 25 | 9,000 | 7 |
| 011 | 1 | L-011 | 10 | 3 | 20 | 9,000 | 5 |
| 016 | 1 | L-016 | 11 | 2 | 18 | 9,000 | 7 |
| 017 | 1 | L-017/018 | 3 | 2 | 2 | 9,000 | 3 |
| 018 | 1 | L-017/018 | 3 | 2 | 1 | 9,000 | 3 |
| 019 | 1 | L-019 | 3 | 1 | 3 | 9,000 (8,598 in one camera) | 3 |
| 022 | 1 | L-022 | 4 | 1 | 24 | 1,638 of 9,270 | **1** |
| 002 | 2 | L-000 | 20 | 9 | 60 | 9,000 | 15 |
| 004 | 2 | L-000 | 19 | 9 | 60 | 9,000 | 17 |
| 006 | 2 | L-000 | 18 | 8 | 52 | 9,000 | 9 |
| 020 | 2 | L-000 | 16 | 9 | 60 | 9,000 | 16 |
| **Total** | | **6 new + 1 held** | **118** | | | | |

Rejected (no forklift): 008, 009 (one layout), 012, 013, 014, 015. Counts are distinct ids from ground truth. "Layout" is the `map.png` identity. The tier-2 draw did not bind, because all four scenes fit.

## 4. Verification after download

| Check | Result |
|---|---|
| SHA-256 of every file against the publisher | 51 screen files + 118 videos, **0 mismatches** |
| Frame count of every video = ground-truth frame count | **118 of 118** (9,000 each; 022: 9,270) |
| Frame intervals (packet timestamps; VFR if any interval differs from the median by > 1 ms, as 2.5) | **constant 33.333 ms** on all 118 (min = median = P99 = max); **0 VFR** |
| Calibration entry for every camera | **118 of 118**; no camera without calibration |
| Format | 1920 × 1080, H.264, every video |

Per-video statistics: `research/datasets/part5/intervals.json`. The checks use demux only, with no pixels decoded. Frame-quality flags (rv2) have not been computed on the new recordings (section 6, T-26q).

## 5. What the new data adds, and its limits

**Adds:**
- **Layout diversity:** from 1 to 7 layouts with forklift–person interaction. This is the first chance to test whether results transfer to a layout that no parameter was chosen on.
- **Dense same-layout scenarios:** tier 2 has 8 to 9 forklifts and 52 to 60 people per scene and 16 to 20 cameras. That makes it a strong stress case for tracker identity and for episode splitting, the D-57/D-58 lever.
- **Volume:**

  | | Held SmartSpaces synthetic (000 + 001 re-render) | Tier 1 | Tier 2 |
  |---|---|---|---|
  | Cameras | 19 distinct | 45 | 73 |
  | Camera-hours | 1.6 | 3.8 | 6.1 |

**Limits (to state with any result):**
- **Still one generator.** Every scene is rendered by the same publisher's Omniverse pipeline. A new layout is not a new visual domain, and nothing here says anything about real footage.
- **Small populations.**
  - Tier 1 has 7 scenes in 6 layouts. Scenes 017, 018 and 019 have 3 cameras and 1 to 3 people each.
  - Scene 022 has forklift and person together on only 1,638 frames, in one camera.
  - A layout-level result would rest on 6 clusters. That is descriptive, not an inferential claim about layouts in general.
- **Tier 2 shares `Warehouse_000`'s layout.** It cannot support a held-out-layout claim. Whether it is `shared_scene_content` with 000 depends on CR-036 item 1.
- **Pallet trucks** are present in tier 2 (9 to 10 per scene) and stay not evaluated (D-22).
- **Synchronisation** rests on the shared frame index, as for 000 (qualification 2.7). Calibration exists for every camera, but its accuracy on these scenes has not been checked.

## 6. Proposed testing and tuning plan (agent's proposal; not applied; for the Architect and the Owner)

**Principles:**
1. **The current v2 work is not disturbed.** D-58 → v2 freeze → the 110 reporting cameras once → test (D-37) runs exactly as planned. The new data must not enter v2 tuning after the fact. Reopening tuning now would undermine the v2 pre-registration.
2. **The new data is assigned before any system output exists on it** (R-4: metadata only), by a seeded rule, in a split version recorded like X0b.

**Proposal:**

| Data | Proposed role | Why |
|---|---|---|
| **Tier 1** (7 scenes, 6 new layouts, 45 cameras) | **Held-out-layout test addendum.** Never used for tuning. Evaluated once with the frozen v2 package, after the v2 reporting run. Reported per scene and per layout, descriptively, beside the X0b test result | the only data that can show whether parameters chosen on one layout transfer; using any of it for tuning would remove that |
| **Tier 2** (4 scenes, held layout, 73 cameras) | **Option T2-a:** tuning reserve for a later package (v3): SmartSpaces-specific parameters such as the forklift prior (d × 0.923 was scaled, not fitted), tracker identity in dense scenes, and episode splitting / m_gap. **Option T2-b:** split by a seeded draw, 2 scenes for tuning and 2 for a same-layout test. **Option T2-c:** test-only (replication in the held layout) | T2-a gives the most tuning data where it is scarce; T2-b keeps a same-layout check of any v3 tuning; T2-c gives no tuning gain |

The agent leans to **tier 1 test-only plus T2-b**, so that any later tuning keeps an untouched same-layout check. This is a scientific choice, so the Architect and the Owner decide (D-60).

**Order of work once decided:**

| ID (proposed) | Task | Needs |
|---|---|---|
| T-26r | S0 registration of the 11 scenes (one S0 per scene, `synthetic_rendered`) | CR-036 items 1–2 (`layout_id`, `generation_batch`) |
| T-26s | New split version or addendum: tier 1 test; tier 2 per the chosen option; Warehouse_001 joins with Warehouse_000 as already planned (X0b note) | CR-036 main question; D-60 |
| T-26q | rv2 frame-quality statistics on the 118 recordings (statistics only, as 3.12) | none (can run now; about 1–2 h) |
| T-26o | Oracle-path runs (A, B columns) on the tuning share only | T-26s |
| T-26e | Detector-path runs (column C) | T-26s; v2 frozen; compute decision below |

**Compute (needs a decision):**
- **Detection rate:** the selected detector (YOLO-World v2-s) ran at about **0.35 s per frame** on this laptop's CPU (T-22).
- **Full detection:** every frame of the new cameras is about **1.06 M frames, about 100 h**. Tier 1 alone is 406 k frames, about 40 h. Tier 2 is 657 k frames, about 64 h.
- **Oracle path:** cheap by comparison. 13 SmartSpaces cameras took about 1 h after AR-60.
- **Options:**
  - (i) run in full, unattended, over several nights;
  - (ii) evaluate a seeded subset of windows under the existing RES/ECS sampling plan. This is a sampling decision for the Architect;
  - (iii) tier 1 in full (about 40 h) and tier 2 later.

## 7. Cap headroom and other unique sources (not downloaded)

8.05 GB of the 60 GB cap is unused. D-59's recorded scope (2026 edition, synthetic, with ground truth) is exhausted: every other 2026 scene is a re-render, has no ground truth, has no forklift, or is real. Candidates for a further decision, none qualified yet:

| Source | What it would add | Caveat |
|---|---|---|
| SmartSpaces `MTMC_Tracking_2025` (same repository, CC BY 4.0) | card: 23 scenes, 13 forklifts in total, about 70 GB without depth for the whole edition | only some scenes can fit; layout overlap with 2026 and forklift presence must be screened first; a second edition is a new dataset row |
| More SDG near-miss shards (same seeded permutation as 3.1) | more 10 s near-miss runs with one worker and one forklift each | same single layout family: more of the same distribution |
| Other public real datasets | real visual domain | needs a new D-24-style qualification and approval; testing only (D-21) |

## 8. Decisions needed (D-60)

1. **CR-036, main question:** how the 11 scenes join, or stay beside, the frozen split. Readings (a) separate frozen addendum, (b) test-only, (c) tuning-only, (d) re-freeze.
2. **CR-036 item 1, `layout_id`:** scene asset, or map identity. Item 2, `generation_batch` for the `val` folder scenes.
3. **Roles:** tier 1 (proposed: held-out-layout test only); tier 2 (T2-a, T2-b or T2-c).
4. **Compute:** full detection (about 100 h), sampled windows, or tier 1 first.
5. **Headroom:** whether to qualify a further source within the remaining 8.05 GB (section 7), or leave the cap unused.
