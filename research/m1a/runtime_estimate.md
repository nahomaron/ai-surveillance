# T-21 runtime and memory estimate (D-36 step 1), 14 Nov 2026

Machine: MacBook Air, 4 CPU cores, 8 GB RAM. Code: the S3/S4/S5 stages at commit 566fe76; pre-registration v1 base values. Validation recordings only (D-37): the probe refuses any other recording.

## Measured

`research/m1a/runtime_probe.py`, one SDG validation camera (`run_20_seed_139404633.ceiling_00`; 300 frames, 2 tracks, 1 POW, 300 pair-frames):

| Stage | Seconds |
|---|---|
| S3 oracle tracks from truth | 0.9 |
| S4, simulator_truth positions | 15.4 |
| S4, full_camera positions (GV run) | 11.1 |
| S5 BL-2 / BL-3 / BL-4 / BL-5 / BL-6 | 0.44 / 0.41 / 0.71 / 0.53 / 0.68 |
| Peak resident memory | about 100 MB |

Profile (cProfile): about 70 % of S4 time is R4 `pet_pred` (`surrogate.occupancy` → `polygon_distance`), about 50 ms per pair-frame in total for S4.

`research/m1a/smartspaces_pair_frames.py`: person–forklift pair-frames with both oracle points present (an upper bound for POW pair-frames), SmartSpaces Warehouse_000, g_max 15: **3,193,789** over 19 cameras (largest: Camera_0003 723,949; Camera_0015 659,550; Camera_0001 377,949; Camera_0008 has no forklift). SDG validation: 226 cameras × at most 300 = about 68,000.

## Estimate (extrapolated linearly from the measurements; S8 not included because it is not yet built)

| Part | Serial | Wall clock with 3 workers |
|---|---|---|
| (a) SDG validation: S3, S4, S5 × 5 BL, full_camera S4 (226 cameras × about 30 s) | 1.9 h | about 0.7 h |
| (a) SmartSpaces Warehouse_000: S4 simulator_truth (3.19 M pair-frames × 51 ms) | 45 h | memory-bound (below) |
| (a) SmartSpaces: full_camera S4 | about 33 h | — |
| (a) SmartSpaces: S5 × 5 BL (about 1.8 ms per pair-frame per configuration) | about 8 h | — |
| **(a) total** | **about 88 h** | **far above 4 h** |
| (b) SDG sweeps: 15 S4-level variants (g_max 3, v_min 2, w_v 2, τ 2, person radius 2, footprint length/width ±10 % 4) × 226 cameras | about 15 h | about 5 h |
| (b) SDG sweeps: 23 S5-only variants × 226 cameras | about 1 h | about 0.3 h |
| (b) SmartSpaces sweeps (15 S4 variants × 45 h, plus S5) | about 700 h | infeasible |

τ = 3 and 4 s lengthen the R4 search, so those two variants cost more than the base.

**Memory.** S4 holds every pair_series row in memory and canonicalises the tables to hash them. The largest SmartSpaces camera has about 724,000 pair-frames: an estimated 1–2 GB for one S4 build. With 8 GB, SmartSpaces cameras must run one at a time. SDG is not at risk.
