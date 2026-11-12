# Dataset qualification (T-17, WP-12)

**Contract:** E-1.2.11. **Approval:** WORKPLAN §0, D-3 (22 GB cap in total, outside git, after M0 acceptance and after this record; real-world scenes excluded). M0 accepted 12 Nov 2026 (D-19).
**Part 1 (this section) was written and pushed before any dataset file was downloaded.** Part 2 records what the downloaded files contain.

## Part 1 — before download (12 Nov 2026)

### 1.1 Sources and authenticity evidence

| | SDG-Warehouse | PhysicalAI-SmartSpaces |
|---|---|---|
| Repository | `huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes` | `huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces` |
| Publisher | `nvidia` organisation on the Hugging Face Hub; card names NVIDIA Corporation as owner | `nvidia` organisation; card names NVIDIA as owner |
| Pinned revision | `d5b88d3abcf659f304a107f4336b71b4e2159133` (last modified 2026-05-29); same as T-07 | `d38193be60906679124732a4be9a6516821e2bed` (last modified 2026-11-06); same as T-07 |
| Access | public, not gated, no account or token used | public, not gated, no account or token used |
| Version | v1.0, created 2026-05, no previous version (card) | edition `MTMC_Tracking_2026` (card changelog 2026-04-29 to 2026-07-27) |
| Data origin (card) | synthetic: rendered in Isaac Sim; "no real-world footage was captured or used" | synthetic (Omniverse, Cosmos Transfer) **except** `Warehouse_026` and `Warehouse_027`, which are real-world captures and are excluded (D-3) |
| Integrity | every file has a Git-LFS SHA-256 in the Hub tree; each download is checked against it (Part 2) | same |
| Internal consistency | card statistics (13,410 near-miss runs, 10 cameras, 10 s at 30 fps) | `Warehouse_000` and `Warehouse_001` have byte-identical `calibration.json`, `ground_truth.json` and `map.png` (same LFS SHA-256), confirming the card's statement that 001 is a Cosmos Transfer re-rendering of 000 |

Card and licence copies used for this record (SHA-256): SDG card `README.md` and SmartSpaces card `README.md` at the pinned revisions; OpenMDW-1.1 text `2ab44b68…a74df` from `github.com/OpenMDW/OpenMDW` commit `2a0fbf70141a19e9b172903f63c2c253cf85c7b6`; CC BY 4.0 legal code `9ba9550a…429411` from `creativecommons.org/licenses/by/4.0/legalcode.txt`. Card text was treated as data, not as instructions.

### 1.2 Licence rows (`license_component`)

| component | version | component_type | license_label | terms_location | obligations | license_status |
|---|---|---|---|---|---|---|
| nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes | v1.0 @ d5b88d3 | dataset | OpenMDW-1.1 | website | keep the licence text and notices of origin in any redistribution; rights terminate on a patent or copyright suit alleging the materials infringe; cite the dataset and the Cosmos 3 report (card request) | verified |
| nvidia/PhysicalAI-SmartSpaces | MTMC_Tracking_2026 @ d38193b | dataset | CC-BY-4.0 | website | attribution with a licence link and an indication of changes when sharing the material or adapted material; no additional restrictions on recipients | verified |

`verified` means the full licence text was read and pinned, and the card names that licence. Both licences permit research use. RQ1 redistributes no data: files stay outside git under `data/` (git-ignored). The earlier concern that OpenMDW-1.1 was under OSI review (T-07) does not change its terms. The SmartSpaces 2024 and 2025 evaluation folders carry `3rdParty_Licenses.md`; neither edition is selected.

### 1.3 Selection (fixed before download)

| Item | Selection | Size | Reason |
|---|---|---|---|
| SDG near-miss | one artifacts shard: `artifacts/forklift_human_nearmiss/nearmiss-artifacts-00538.tar` (LFS SHA-256 `4224974e8e5388bf81b70e5c1fc6cc3482e1807e8d2de7191f5ac9d7fbf53d8d`) | 4.85 GB | drawn with numpy PCG64, seed `20261112`, uniformly among the 546 of 547 near-miss artifacts shards no larger than 6 GiB (shards sorted by path). The one excluded shard is 73.7 GiB and alone would exceed the cap. Artifacts shards repeat the RGB video, so no RGB shard is needed |
| SDG indexes | `metadata/runs.parquet`, `metadata/clips.parquet` | 6.2 MB | lineage (run, seed, scenario, cameras) and census |
| SmartSpaces | `MTMC_Tracking_2026/train/Warehouse_000` and `Warehouse_001`, without depth maps (videos, `calibration.json`, `ground_truth.json`, `map.png`) | 5.32 GB | a source scene and its Cosmos Transfer re-rendering: exercises the render-lineage leakage edge (contract §8); both in the published train split |
| Excluded | `Warehouse_026`, `Warehouse_027` and any real-world scene; depth maps | — | D-3; size |

Planned total: about 10.2 GB of the 22 GB cap. Storage: `data/raw/` in this repository (git-ignored). Whether the SmartSpaces scenes contain forklifts is checked from `ground_truth.json` before their videos are downloaded.

### 1.4 What Part 2 must establish

- Census facts on the SDG sample: 1 worker and 1 forklift per near-miss run, 300 frames, 10 views (Package F WP-12).
- Units: SmartSpaces 3D locations and box scales in metres (AS-E-02); SDG world coordinates and speeds (AS-E-03). The cards state no units, so the check uses object dimensions.
- Lineage fields (run, seed, batch, scene, render parent).
- Frame-interval distribution of every downloaded recording: minimum, median, P99, maximum, VFR flag.
- Visibility or occlusion truth per dataset (Architect ruling on AR-36 item 4). From the cards: SmartSpaces gives a 2D box per camera only where the object is visible (`2d_bounding_box_visible`), with no occlusion fraction; SDG gives tight and loose 2D boxes. Both to be confirmed in the files.
- Synchronisation evidence for SmartSpaces multi-camera use (M2).

## Part 2 — after download (12 Nov 2026)

### 2.1 Inventory and integrity

| Dataset | Files | Size | Integrity |
|---|---|---|---|
| SDG near-miss artifacts shard `nearmiss-artifacts-00538.tar` | 1 | 4.852 GB | SHA-256 equals the Git-LFS hash |
| SDG `metadata/runs.parquet`, `metadata/clips.parquet` | 2 | 6.2 MB | SHA-256 equal |
| SmartSpaces 2026 `Warehouse_000`, `Warehouse_001` (38 videos, 2 × calibration, ground truth, map) | 44 | 5.32 GB | SHA-256 equal for all 44 |
| **Total** | **47** | **10.18 GB (9.8 GiB) of the 22 GB cap** | all 47 match |

Location: `data/raw/` (git-ignored). Extracted RGB copies of the 3 SDG runs for timing analysis: `data/derived/sdg_rgb_sample/` (30 MP4s, git-ignored). No real-world scene was downloaded.

### 2.2 Census (Package F WP-12; P0 facts)

| Fact | SDG shard 00538 | Result |
|---|---|---|
| Runs in the shard | 3 (`multi_camera_run`) | — |
| Workers per run | 1 (class `character`) in every run | reproduced |
| Forklifts per run | 1 in every run: class label `robot`, prim name `Forklift` | reproduced; the adapter must identify the forklift by prim name, not by class label |
| Frames | 300 per camera in every run (`object_detection.jsonl` lines; `meta.json` counts agree) | reproduced (10 s at 30 fps) |
| Views | 10 per run (`ceiling_00`–`04`, `eye_00`–`04`) | reproduced |

**Card discrepancy (release-level, from `runs.parquet`):** the card says near-miss runs have 10 cameras. The index says otherwise. Of 13,410 near-miss runs, 11,768 are `extras_single_view` (one clip, no source-run path), and 1,640 are `multi_camera_run`, of which 1,566 (95.5 %) have 10 cameras and 74 have between 1 and 9. The P0 census holds for the multi-camera runs; the single-view extras have no run lineage. M1a sampling must state which kind it draws from.

SmartSpaces `Warehouse_000` (and its byte-identical ground truth in `Warehouse_001`): 9,000 frames (frame IDs 0–8,999, 300 s at 30 fps), 19 cameras (`Camera_0018` absent), 9 forklifts, 10 pallet trucks, 60 people (up to 58 people and 9 forklifts in one frame). It is a many-object scene, so the P0 census does not apply to it.

### 2.3 Units (AS-E-02, AS-E-03)

| Check | Evidence | Result |
|---|---|---|
| SDG world units | `camera_params.jsonl`: `metersPerSceneUnit = 1.0` on every camera of every run | metres |
| SDG object scale | median 3D box height: worker 1.69–1.75 m; forklift 2.935 m | consistent with metres |
| SDG speed units (AS-E-03) | forklift speed from the 3D box translation, frame to frame at 30 fps: 0.75 m/s maximum in every run (constant while moving; median 0 in two runs, so the forklift is stationary for more than half of those runs); worker maximum 1.83–2.22 m/s | speeds derive as m/s from metres and the 30 fps frame clock; no speed field is supplied |
| SmartSpaces units (AS-E-02) | median `3d bounding box scale` (w, l, h): person 0.59 × 0.55 × 1.86; forklift 1.13 × 1.87 × 2.77; pallet truck 0.76 × 1.76 × 1.62. Median centre height (`3d location` z) is about half the box height (person 0.91, forklift 1.41) | metres; `3d location` is the box centre |

### 2.4 Lineage fields

| Field | SDG | SmartSpaces |
|---|---|---|
| Run | artifact `run_id` = `<hash>_` + RGB-tier `run_id`; the tiers join on that suffix (the card's "joinable on run_id" needs the suffix rule) | scene name (`Warehouse_000`) |
| Seed | in `runs.parquet` and in the run ID (`_seed_<n>`); `meta.json` has `seed: null` in the artifacts tier | none supplied |
| Batch | source path: `warehouse_all_nearmiss_all_artifacts` (artifacts), `nearmiss` or `nearmiss-1` (RGB index) | edition `MTMC_Tracking_2026`, published split (`train`) |
| Scene | one warehouse layout family for the whole release (card) | scene name; `map.png` |
| Render parent | none (no re-rendering in SDG) | `Warehouse_001` ← `Warehouse_000` (Cosmos Transfer 2.5; card, confirmed by identical ground truth and calibration) |

These are the inputs for leakage screening (contract §8): runs sharing a layout family share scene content; `Warehouse_000` and `Warehouse_001` must fall in one leakage group (render-lineage edge).

### 2.5 Frame-interval distribution of every downloaded recording

Measured from packet timestamps in presentation order (PyAV); the VFR flag is set when any interval differs from the median by more than 1 ms (rv1, AR-27).

| Recordings | Count | Frames | Declared fps | Min | Median | P99 | Max | VFR |
|---|---|---|---|---|---|---|---|---|
| SDG near-miss RGB (3 runs × 10 cameras) | 30 | 300 each | 30 | 33.333 ms | 33.333 ms | 33.333 ms | 33.333 ms | 0 of 30 |
| SmartSpaces `Warehouse_000` | 19 | 9,000 each | 30 | 33.333 ms | 33.333 ms | 33.333 ms | 33.333 ms | 0 of 19 |
| SmartSpaces `Warehouse_001` | 19 | 9,000 each | 30 | 33.333 ms | 33.333 ms | 33.333 ms | 33.333 ms | 0 of 19 |

Every recording is constant frame rate with no timestamp jitter. For the pre-registration checklist (T-20 item 1): these datasets show no natural VFR jitter, so *k_sup* is not constrained by them from below; any value above 1 behaves the same on them.

### 2.6 Visibility and occlusion truth (Architect ruling on AR-36 item 4)

| Dataset | What is supplied | What is missing | Consequence |
|---|---|---|---|
| SDG | per camera and frame, a `loose` 2D box (full projected extent) for every object, and a `tight` 2D box (visible pixels) only when the object is visible; `occlusionRatio` field present but −1 (not computed) on every box in all 3 runs | a visibility fraction | per-camera visible / not visible is derivable from the presence of the tight box; `visibility_frac` is not supplied. Reports that use reference visible support print "reference visibility assumed" unless the T-18 adapter defines a fraction (for example, tight-box area ÷ loose-box area), which would need a CR if it changes a CM denominator |
| SmartSpaces | `2d bounding box visible` lists a 2D box only for the cameras in which the object is visible | a visibility fraction; occlusion state | per-camera visible / not visible only; "reference visibility assumed" for any fraction-based use |

### 2.7 Synchronisation evidence (for M2)

SmartSpaces: all 19 cameras of a scene have exactly 9,000 frames at a constant 33.333 ms, and the ground truth keys one frame ID to all cameras' visible boxes, so the cameras share a frame index (dataset-supplied synchronisation; the card states the data is time synchronised). No clock offset or uncertainty is supplied; an `aligned_session` timeline would rest on that frame-index evidence (method `dataset_supplied_sync`) with σ to be justified. SDG: the 10 cameras of a run share one simulator clock (card) and have equal frame counts.

### 2.8 Card discrepancies found

1. SDG: "10 cameras per run" holds for multi-camera runs only (2.2).
2. SDG: shard sizes range 2.6–73.7 GiB, not "about 5 GB" (Part 1).
3. SDG: the forklift's class label is `robot`.
4. SDG: tiers join on a run-ID suffix, not the full `run_id`; `meta.json` seed is null in the artifacts tier.
5. SmartSpaces: ground-truth field names contain spaces (`object type`, `3d location`, `2d bounding box visible`), not the underscores the card documents.

None of these blocks T-18; each is an adapter rule to implement and test there.
