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

**Card discrepancy (release-level, from `runs.parquet`):** the card says near-miss runs have 10 cameras. The index says otherwise. Of 13,410 near-miss runs, 11,768 are `extras_single_view` (one clip, no source-run path), and 1,642 are `multi_camera_run`, of which 1,566 (95.4 %) have 10 cameras and 76 have between 1 and 9. *(Corrected 12 Nov 2026 in Part 3: this line first read 1,640 and 74, an arithmetic slip; 11,768 + 1,642 = 13,410.)* The P0 census holds for the multi-camera runs; the single-view extras have no run lineage. M1a sampling must state which kind it draws from.

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

## Part 3 — extension under D-20, D-21, D-22 (12 Nov 2026), recorded before download

**Authority:** Owner decisions of 12 Nov 2026. D-21 amends D-3: the cap is 30 GB in total, and real-world footage is permitted **for testing only** (no training or fine-tuning). D-22 excludes SmartSpaces pallet trucks from the E1 pair class (recorded as present, not evaluated). D-20 defines a leakage "scene" as the rendered scene instance (a run, or a scene plus its re-renders); a shared layout family is recorded as `shared_scene_content` with no edge; claims are limited to held-out runs of the same synthetic layout. No split is frozen until the Architect's E-1.2.12 text is committed.
**Nothing listed in this Part has been downloaded.** The only file fetched while writing it is one SDG index file (3.1, deviation) and the dataset cards and licence pages needed for 3.2 to 3.4. Machine-readable selection lists with every file's size and SHA-256: `research/datasets/part3/selection_*.json`.

### 3.1 SDG-Warehouse: multi-camera runs per near-miss artifacts shard

**Deviation from the instruction "from runs.parquet / clips.parquet only".** Neither index names an artifacts shard: both map runs and clips to **RGB** shards (`rgb/…/nearmiss-rgb-*.tar`) only. Two steps were therefore added, both metadata only:
1. `metadata/manifests/manifest_nearmiss_artifacts.json` (3,267,475 bytes; git blob `5902cb67…7716` verified, not an LFS file) was fetched into `data/raw/sdg/metadata/manifests/`. It lists the 1,642 runs that have an artifact folder. They are exactly the 1,642 `multi_camera_run` near-miss runs in `runs.parquet`. The 11,768 `extras_single_view` runs have no artifacts.
2. The first 512-byte tar header of each of the 547 artifacts shards was read by HTTP range request (547 requests, about 280 kB). Each header names the shard's first run.

Result: the first runs increase strictly with shard number in the sorted run list, so shard *k* holds the sorted runs from its own first run up to the next shard's first run. This was checked against the shard already held: 00538 contains exactly the predicted three runs (sorted positions 1,616 to 1,618). Map: `research/datasets/part3/sdg_artifacts_shard_map.json`; scripts `probe.py`, `map.py`, `draw.py` beside it.

| Fact | Value |
|---|---|
| Artifacts shards | 547; 2,637 GB in total |
| Runs per shard | 3 in 544 shards, 4 in 2, 2 in 1 |
| Run kind | all 1,642 are `multi_camera_run` (every artifacts shard is multi-camera only) |
| Cameras per run | 10 in 1,566 runs; 1 to 9 in 76 runs (1: 2, 2: 3, 3: 3, 4: 7, 5: 9, 6: 3, 7: 11, 8: 16, 9: 22) |
| Shards in which every run has 10 cameras | 477 |
| Shard size | min 2.78 GB, median 4.77 GB, max 79.18 GB (`00000`, 73.7 GiB) |
| Byte share inside a shard (00538) | `instance_id_segmentation_mapping.jsonl` 61.2 %; `rgb.mp4` 10.0 %; other render passes (edges, shaded_seg, segmentation, depth, npz) 27.2 %; `object_detection.jsonl` 1.3 %; `camera_params.jsonl` 0.2 % |

**Proposed draw (declared here; computed deterministically from the map):**
- Eligible: shards in which every run is a 10-camera `multi_camera_run` (the P0 census), size ≤ 6 GiB (as in Part 1), excluding the held shard 00538: **475 shards**. (If "multi-camera" is read as ≥ 2 cameras, 543 shards are eligible; the 10-camera reading is proposed so that every run satisfies the census.)
- Draw: numpy PCG64, seed **`2026111203`**, a permutation of the eligible shards sorted by name. Shards are taken in permutation order and the draw stops at the first shard that does not fit the SDG budget (3.6). Skipping to smaller shards is not allowed, so the size rule cannot bias the draw towards small shards.
- Result at the 3.6 budget (13.26 GB): **2 shards, 6 runs, 9.66 GB**. Next in order, not taken: `00354` (4.88 GB).

| Shard | Size (bytes) | LFS SHA-256 | Runs |
|---|---|---|---|
| `nearmiss-artifacts-00336.tar` | 4,854,691,840 | `86b916260f6c1a24410176023c038a191fef9036d9442e9532068fc2cb8ca763` | `9cb5e1621ee475146fcd_run_10_seed_1087475235`, `9cb8e8b90aac0e419ea4_run_29_seed_2071889816`, `9ceb0327c127ac4b2f93_run_1_seed_1315993226` |
| `nearmiss-artifacts-00243.tar` | 4,807,434,240 | `a73ebbab6665be804629672e58e375d6d95a7c4a797f06567293e021f4d9c93b` | `72a9270c9daa123ace61_run_13_seed_851910160`, `72c2e190ff811e2fcd9d_run_42_seed_648376005`, `72cdf064afe3ed619660_run_14_seed_495532104` |

With 00538, SDG would contribute 9 runs (9 leakage groups under D-20, all sharing one layout family → `shared_scene_content`).

**Option for the Owner (not proposed by default).** About 88 % of each shard is render passes RQ1 does not use. Range-reading only `rgb.mp4`, `object_detection.jsonl`, `camera_params.jsonl` and `meta.json` would cost about 0.19 GB per run, so the same 13 GB would hold about 70 runs instead of 6. The cost: no published hash exists for individual members, only for whole shards, so the "SHA check" would become a weaker check (tar header checksums, member sizes, and decoding plus a frame count match). It needs a per-shard header walk (about 276 range requests per shard). Not proposed without the Owner's agreement, because the instruction requires SHA checks.

### 3.2 PhysicalAI-SmartSpaces real-world scenes `Warehouse_026`, `Warehouse_027`

Same repository and pinned revision as Part 1 (`d38193be…`); published `test` split.

| Scene | Files | Bytes | Contents |
|---|---|---|---|
| `Warehouse_026` | 6 | 105,751,218 | `videos/Camera_0000–0003.mp4` (4), `calibration.json`, `vggt_reprojection_error.txt` |
| `Warehouse_027` | 9 | 184,188,642 | `videos/Camera_0000–0006.mp4` (7), `calibration.json`, `vggt_reprojection_error.txt` |
| **Total** | **15** | **289,939,860 (0.29 GB)** | every file has a Git-LFS SHA-256 (`selection_smartspaces_real.json`) |

**"Videos + calibration only": confirmed, with one addition.** The card says "the first 60 s (1800 frames) per camera is provided — videos + calibration only". The folders also hold `vggt_reprojection_error.txt` (about 1 kB, a calibration-quality report added 2026-07-27, per the changelog). There is no ground truth, no depth map and no map image. So these scenes have **no reference annotation**; any evaluation needs D-23.

**Card consent and privacy statements** (card `README.md` SHA-256 `cdba2b67…0ab`; `croissant.json` SHA-256 `fe6adeeb…bbdb`, both at the pinned revision):
- The README has no consent or privacy statement. Its "Ethical Considerations" section is NVIDIA's generic Trustworthy-AI text.
- `croissant.json`, `rai:personalSensitiveInformation`: "Every individual appearing in this real footage has provided a signed, written consent agreement authorizing the capture … no person appears in the real data without explicit individual consent on file with NVIDIA." It implicitly contains gender, age and location of capture.
- **Conflict for the Owner.** The same field says: "The hidden target is treated as an evaluation-only resource: raw video is not publicly redistributed, access is mediated solely through the AI City Challenge online evaluation server, **manual labeling of the test set by participants is prohibited by the challenge rules**, and the target is excluded from training use." It also says the dataset "is not authorized for use in biometric, facial recognition, demographic profiling, or surveillance systems targeting real individuals". Yet the README changelog (2026-06-04) says these two scenes' videos are released, and they are in the public tree under CC BY 4.0. Possible reading: Croissant describes the hidden, labelled target, and the 60 s public videos are a released part of it. That reading is not certain. Consequences:
  1. Training use is excluded by both the card and D-21. Consistent.
  2. **Manual reference annotation of these scenes (D-23) may conflict with the challenge rule.** RQ1 is not a challenge participant, but the statement is the publisher's stated use condition. The Owner should decide whether to annotate them, use them unannotated (for example, frame-interval and decode checks only), or exclude them.
  3. RQ1 measures pair exposure without identifying anyone. It is still a workplace-monitoring instrument, and the card lists "workplace and labor surveillance" as a misuse risk. Recorded for the ethics record (`approvals_ref`, 3.5).
- Proposed labels (to be confirmed by the Owner): `data_origin = real_staged`. Evidence: capture "by NVIDIA in real smart-space environments" with signed individual consent, which points to staged capture rather than routine operations. `site_kind = staged_facility`, `privacy_state = contains_identifiable_persons`.
- After download (only if approved): view the videos to check whether forklifts and people appear together. If they do not, report it and stop for this source. D-22: pallet trucks, if present, are recorded as present, not evaluated.

### 3.3 Video Dataset for Safe and Unsafe Behaviours (Mendeley Data `xjmtb22pff`)

| Item | Value |
|---|---|
| Pinned version | **v1**, DOI `10.17632/xjmtb22pff.1`, published 2024-06-11. The public API lists v1 as the only version |
| Publisher | Mendeley Data; owner and contributors at Bilecik Şeyh Edebali University (ROR `00dzfx204`); related article Springer *Multimedia Tools and Applications*, doi 10.1007/s11042-024-19276-8 |
| Licence | **CC BY 4.0** (Mendeley `data_licence`: "Creative Commons Attribution 4.0 International", `http://creativecommons.org/licenses/by/4.0`). Legal code is the same text pinned in Part 1 (SHA-256 `9ba9550a…429411`). Mendeley adds: "further permission may be required for any content within the dataset that is identified as belonging to a third party" |
| Content | 691 MP4 clips (1–20 s each), 8 classes (4 safe, 4 unsafe), publisher's `train`/`test` folders. Two IP cameras (UNV IPC2122CR3-PF40-A), 1920 × 1080, 24 fps, H.264 (Mendeley "method" field) |
| Integrity | Mendeley gives a SHA-256 for every file. Both HF mirrors (`Voxel51/Safe_and_Unsafe_Behaviours` @ `7369ff18…`, `yangyayaa/Safe_and_Unsafe_Behaviours` @ `672abfaf…`; identical cards, SHA-256 `5221b4c5…7730`) hold the same 691 MP4s, and **all 691 SHA-256 values equal Mendeley's**. Download from Mendeley; the mirrors corroborate. The mirrors add FiftyOne JSON and a GIF, which are not needed |
| Consent statement | Mendeley description: collected from the security cameras of a production facility in an organised industrial zone in Eskişehir, Turkey, 5 Nov to 13 Dec 2022, "after obtaining the necessary permissions from company officials and employees". Mirror card: "Proper permissions were obtained from company officials and employees for the use of video recordings and images **in academic studies**. The permission documentation is maintained at the Department of Computer Engineering, Faculty of Engineering, Bilecik Şeyh Edebali University." The record names the company; it is not copied into RQ1 records (the `site` table has no establishment field; `site_label` is pseudonymous) |
| Faces | **Not blurred.** Mirror card: "Workers' faces and bodies are visible in the footage." The Mendeley record makes no redaction claim. `privacy_state = contains_identifiable_persons`; `redaction_state = none` |
| Use limits stated | permission for academic studies; mirror card lists "worker surveillance or performance monitoring without proper consent and ethical oversight" as out of scope |
| Proposed labels | `data_origin = real_natural` (to be confirmed: the cards describe workers "performing normal production activities" filmed by fixed security cameras; clip selection by domain experts does not make it staged); `site_kind = operational_facility`; domain = **production facility, not a warehouse** (to be stated next to every result from this source) |

**Selection: four classes only, both publisher folders** (the publisher's train/test split has no meaning for RQ1, which uses the data for testing only):

| Class (folder) | Files (train + test) | Bytes |
|---|---|---|
| `0_safe_walkway_violation` | 178 + 32 = 210 | 3,500,705,686 |
| `3_carrying_overload_with_forklift` | 48 + 8 = 56 | 959,641,943 |
| `4_safe_walkway` | 50 + 25 = 75 | 1,182,485,682 |
| `7_safe_carrying` | 22 + 8 = 30 | 132,062,224 |
| **Total** | **371** | **5,774,895,535 (5.77 GB)** |

The class labels are the publisher's behaviour labels. They are not RQ1 labels and are not used as a reference for E1 (a "violation" label is not an exposure, a candidate or a near miss). Whether a forklift and a person appear together in each clip is checked by viewing after download, as for SmartSpaces.

### 3.4 FieldWorkArena: excluded

`Fujitsu/FieldWorkArena_Dataset` (HF, revision `aa9199c8…`, card SHA-256 `499d7e37…6197`): gated (manual approval), `license: other`, `license_name: terms-of-use`, with the terms on a Fujitsu research-portal page. **Excluded** (Owner, 12 Nov 2026): a custom non-commercial, no-redistribution licence, restricted to Fujitsu services. The terms page itself was not re-read for this record; the exclusion rests on the Owner's reading and the card metadata above. Nothing was requested or downloaded.

### 3.5 Real-data rules (D-21; VR-E-070)

- Storage: `data/raw/real/<source>/…` (inside `/data/`, which is git-ignored). Derived files from real footage go under `data/derived/real/` only.
- No frames, crops, thumbnails or faces from real footage in git, reports, exports, issues or chat. Reports carry numbers and file hashes only. `evidence_clip` rows for real footage carry `access_class = restricted_research` and `redaction_state = none` (no blurring is applied by RQ1 at this stage). OBX research exports exclude real-origin evidence clips.
- Testing only: real-origin recordings are never assigned to a training role and never enter `training_manifest_hashes`.
- VR-E-070 requires, for each real-origin `source_file`, a `retention_policy_id`, and, for each real-origin `site`, an `approvals_ref`. **Proposed retention policy** `rp_real_test_v1`: applies_to = real-origin source files and their derivatives; `retain_days` = **Owner to set** (agent suggestion: until the end of RQ1, at most 365 days); `deletion_method` = delete the files and their derived copies and record the action in `access_log`; `legal_basis_ref` = Owner to supply. **`approvals_ref` must be supplied by the Owner** (for example an ethics-office reference or a recorded Owner determination that public consented datasets need no further approval). The agent does not create these values.
- Access log: every read, export and delete of real-origin files is appended to the `access_log` hash chain once adapters exist (T-18 onward).
- No processing of real footage (decode, detection, quality flags) before G-FQ is approved. Viewing for the co-occurrence check (3.2, 3.3) is done by a person or by playing the video. Nothing is extracted or stored.

### 3.6 Budget (30 GB = 30 × 10⁹ bytes in total)

| Item | Bytes | Status |
|---|---|---|
| Held (Part 2 download, plus the 3.1 manifest) | 10,180,095,362 | downloaded |
| SmartSpaces `Warehouse_026` + `027` (15 files) | 289,939,860 | proposed |
| Safe and Unsafe Behaviours, 4 classes (371 files) | 5,774,895,535 | proposed |
| Reserve (re-downloads after a failed hash, card or index refreshes) | 500,000,000 | held back |
| SDG budget = the remainder | 13,255,069,243 | — |
| SDG extra shards 00336 + 00243 (3.1) | 9,662,126,080 | proposed |
| **Total if approved** | **25,907,056,837 (25.9 GB)** | 4.1 GB unused; the next drawn shard (4.88 GB) does not fit |

Order of download after approval: real sources first (SmartSpaces, then Mendeley), then SDG. Each file is checked against the SHA-256 in `research/datasets/part3/selection_*.json`. A mismatch is re-fetched once, then reported and the file deleted.

### 3.7 Open for the Owner (STOP: D-24 selection; D-23 annotation; D-25 G-FQ)

1. Approve or amend the selection and the budget (3.1, 3.2, 3.3, 3.6), including the 10-camera eligibility reading and whether to allow the member-level SDG option.
2. SmartSpaces real scenes: decide in light of the Croissant statement (3.2) whether they may be annotated, used unannotated, or excluded.
3. Confirm `data_origin` and `site_kind` for both real sources.
4. Supply `approvals_ref`, `retain_days` and `legal_basis_ref` (3.5).

### 3.8 SDG member-level plan (D-24 a), recorded before download (12 Nov 2026)

**Approval:** D-24 a replaces the whole-shard selection of 3.1. The draw is the one declared in 3.1: the same 475 eligible shards (every run a 10-camera `multi_camera_run`), numpy PCG64 seed `2026111203`, the same permutation. Only the cost per shard changes, so more shards fit the same 13,255,069,243-byte SDG budget (3.6).
**Members per run:** `<run>.<camera>.rgb.mp4`, `<run>.<camera>.object_detection.jsonl` and `<run>.<camera>.camera_params.jsonl` for every camera present, plus `<run>.meta.json` and `<run>.metadata.txt`. Not fetched: depth, edges, segmentation, shaded segmentation, instance-segmentation npz and mapping.
**Method (metadata only, accepted under D-24 item 1):** `walk.py` reads every tar header of a shard by HTTP range request and verifies each header checksum. On the held shard 00538 it reproduced Python `tarfile`'s (name, data offset, size) for all 276 members. Shards were walked in permutation order. Taken in order; the draw stops at the first shard whose selected bytes do not fit.

| Result | Value |
|---|---|
| Shards walked | first 30 in permutation order; 8,210 headers; 0 checksum failures; all regular files |
| Shards taken | **23**: 00336, 00243, 00354, 00359, 00152, 00383, 00486, 00498, 00514, 00506, 00412, 00255, 00529, 00454, 00060, 00358, 00357, 00256, 00007, 00289, 00144, 00308, 00350 |
| Runs | **69** (each with 10 RGB cameras) |
| Members | 2,185 |
| Bytes | **12,997,484,238** (budget 13,255,069,243). First misfit, not taken: 00094 (563,721,722 bytes) |
| Annotation coverage | 67 runs have `object_detection` and `camera_params` on all 10 cameras. **2 runs are partly annotated**: `a83b120d6daa8f2db3e2_run_3_seed_2069582642` (shard 00359; eye_00–02 only) and `77b0d9589e791edd2cc0_run_5_seed_177568880` (shard 00255; ceiling_01, eye_00–04). Both are kept: the draw rule is per shard and pre-declared. The adapter creates truth only for annotated cameras, and their unannotated cameras are not used for evaluation |

**Integrity:** `self_hashed_unverified_by_publisher`. No publisher hash exists per member; only the whole-shard LFS SHA-256 does (recorded in the plan, not checkable without the whole shard). At download, each member is fetched as exactly `[data_offset, data_offset + size)`; its length must equal the header size; the agent's SHA-256 is recorded. Plan with every byte range and the header data (mode, mtime, typeflag, header offset, checksum result): `research/datasets/part3/sdg_member_plan.json`. Download log with the self-hashes: `research/datasets/part3/sdg_member_hashes.json` (written at download).
**Storage:** `data/raw/sdg/members/<shard>/<member name>`.
**Budget after this plan:** held 10,180,095,362 + SmartSpaces real 289,939,860 + Mendeley 5,774,895,535 + SDG members 12,997,484,238 = **29,242,415,000 bytes (29.24 GB)** of 30 GB.
**Leakage (T14, E-1.2.12):** 69 + 3 held = 72 SDG runs, i.e. 72 scene instances, all in one layout family (`shared_scene_content`). No split is frozen until this download is complete and verified (D-24 / Owner).

### 3.9 D-23 second-annotator subset (Safe and Unsafe Behaviours only)

Declared before any annotation: per class, n_h = ceil(0.25 · N_h); numpy PCG64 seed `2026111223` over the class's clips sorted by path. Result: 53 / 210, 14 / 56, 19 / 75, 8 / 30, i.e. **94 of 371 clips (25.3 %)**. List: `research/datasets/part3/annotation_subset_d23.json`; script `annotation_subset.py`. The second annotator labels these before seeing the Owner's labels. SmartSpaces 026/027 get no annotation of any kind (D-24 b).

### 3.10 Real-source status (D-24, D-26)

- SmartSpaces `Warehouse_026/027`: downloaded to `data/raw/real/smartspaces/`; 15 / 15 files equal the publisher's SHA-256. Labels: `real_staged`, `staged_facility`, `contains_identifiable_persons`. Reference-free checks only; no annotation, no reference, no accuracy metric.
- Safe and Unsafe Behaviours: Mendeley v1, 4 classes, 371 clips, each checked against Mendeley's SHA-256 (download log `data/raw/real/safe_unsafe_behaviours/fetch_log.json`). Labels: `real_natural` (D-24 c), `operational_facility`, production facility (not a warehouse), `contains_identifiable_persons`, `redaction_state = none`. Academic and testing use only; estimand `conditional_on_selection`; no frequency, duration or per-hour aggregates.
- Both: `access_class = restricted_research`; VR-E-070 values pending the advisor (D-26); every artifact and report "exploratory; frame-quality rules provisional"; frame-quality rules `rv2-provisional`.
- Co-occurrence check (forklifts and people together): requires viewing; done only as reference-free statistics or by a person. Not yet done.

### 3.11 SDG member download: verification (12 Nov 2026)

- **2,185 / 2,185 members fetched**, each exactly its planned length (12,997,484,238 bytes). Agent SHA-256 per member: `research/datasets/part3/sdg_member_hashes.json`. Integrity label `self_hashed_unverified_by_publisher`. No `.part` files remain.
- Every `meta.json` parses; every line of every `.jsonl` member parses as JSON (a range that started or ended off a member boundary would not).
- **All 690 `rgb.mp4` have 300 video packets** (10 s at 30 fps). The containers do not state a frame count; packets were counted by demuxing.
- **Annotation length finding:** 19 annotation files have fewer than 300 lines (131 to 298). `object_detection.jsonl` lines carry no frame index; frame = line number. In a short file, therefore, the missing frames cannot be located, and the frame alignment of every later line is unknown. Affected: 5 runs. Runs with 300-line `object_detection` and `camera_params` on all 10 cameras: **64 of 69**. The 5 others have 9, 9, 5, 2 and 2 such cameras (`a610…run_15`, `91fb…run_1`, `77b0…run_5`, `a83b…run_3`, `a3cc…run_3`).
- Rule proposed for T-18 (to be pinned as an AR or raised as a CR there): a camera's annotation is used as truth only when both its annotation files have exactly as many lines as its video has frames. Otherwise the camera has no simulator truth. Its RGB is still usable for reference-free checks.
- Total held after D-24: **29,242,415,000 bytes (29.24 GB) of 30 GB.** The SDG download is complete and verified. A split may be frozen from here on (Owner condition of D-24 met), under T14.

### 3.12 rv2-provisional synthetic check (D-25 step 1)

- 68 synthetic recordings (the set held when D-25 was written: 30 SDG sample, 38 SmartSpaces synthetic Warehouse_001): **0 flags; 351,000 / 351,000 frames eligible**; luma P99 62–235. Per-recording counts: `research/datasets/part3/rv2_synthetic_check.json` (statistics only, no pixels).
- The 690 SDG member videos (3.11): 57 recordings flagged (41 runs), 4,361 `black` and 40 `frozen` frames (all frozen frames are also black), 0 `overexposed`; 202,639 / 207,000 frames eligible. Two runs are lit so darkly that every frame of 13 recordings falls under P99 ≤ 32 although content is visible (false positives); other flags are short dark or occluded stretches. Details and the Architect question: D-25. Counts: `research/datasets/part3/rv2_synthetic_check_members.json`.
