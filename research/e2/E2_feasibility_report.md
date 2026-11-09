# E2 data feasibility report (T-07)

**Date:** 2026-11-09. **Scope:** read-only review of public dataset cards and repository metadata. No dataset file was downloaded or opened. Package F section 6 defines the data needs.

**Status labels**
- **verified:** stated in the dataset's primary card or repository metadata. This confirms what the publisher says, not what the files contain.
- **unverified:** a lead that was not confirmed from a primary source.
- **missing:** the primary card describes the content and this item is absent from it.
- **needs collection:** no reviewed source can supply it, so new data would be needed.

## Conclusion

No reviewed dataset documents a worker and a forklift-elevated load in the same scene with a height reference. SDG-Warehouse may support the synthetic load and height work (E2-W1, E2-W2), but only if inspection of a sample shows raised loads exist. The worker-and-load relationship (E2-W3) **needs collection**, which agrees with the data gap already recorded in Package F section 6.

## Requirement matrix

| Requirement | SDG-Warehouse | SmartSpaces MTMC 2025 and 2026 |
|---|---|---|
| Workers present | **verified** for near-miss, fire and box-pickup scenarios. **verified** as "optional" in forklift–shelf collision; how often is **unverified** | **verified** (Person class) |
| Forklift present | **verified** in near-miss and collision scenarios | **verified** (Forklift: 13 objects in 2025, 121 in 2026) |
| Load carried or raised by a forklift | **missing** from the card. Whether any forklift carries a load is **unverified** | **missing**. No load, pallet or fork class is listed |
| Worker and elevated load in one scene | **missing**. The forklift–shelf scenario with its optional character is the only possible case, and it depends on the row above | **missing** |
| Height reference | Per-frame oriented 3D boxes in world coordinates are **verified** on the card for "agents and props". No rack-beam or marker registry is listed (**missing**) | 3D location and box scale are **verified** for listed classes only. No height registry (**missing**) |
| Calibration | Per-frame intrinsics and extrinsics, **verified**. Simulator-supplied | Intrinsics, extrinsics, camera matrix and homography, **verified** for 2025 and 2026 formats. The 2024 release lacks some fields |
| Temporal coverage | 10 s runs for near-miss and fire, 15 s for collision and box pickup, 30 fps, 5–10 synchronized cameras, **verified** | 30 fps, time synchronized, **verified**. 28.7 hours in 2026 and 42 hours in 2025 |
| Licence | OpenMDW-1.1 per the card, **verified** as the label. Licence obligations are **unverified**: the full text was not read, and the licence was still under OSI review in August 2026 | CC-BY-4.0, **verified** as the label on the card |

## Details to carry into T-17

**SDG-Warehouse** (`nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes`, revision `d5b88d3abcf659f304a107f4336b71b4e2159133`, v1.0, May 2026, not gated)
- The card supports the census facts expected by T-17: one worker, one forklift, 10 cameras (5 ceiling, 5 eye-level) and 10 s at 30 fps, which is 300 frames. The per-run object count still has to be measured.
- Near-miss runs have a configurable dodge distance, and the card says the same composition can give near-miss or direct-contact events. Run-level field names and units are **unverified**.
- A seed is recorded per run, and `metadata/runs.parquet` and `clips.parquet` index the runs. These provide lineage inputs for leakage screening.
- The card says future work will add "dropped pallets", so that incident type is not in this release (**verified**).
- All content is one warehouse layout family (**verified**), which limits any generalization claim.

**SmartSpaces** (`nvidia/PhysicalAI-SmartSpaces`, revision `d38193be60906679124732a4be9a6516821e2bed`, not gated)
- `Warehouse_026` and `Warehouse_027` in MTMC 2026 are **real-world** captures. They must stay out of any selection, because CLAUDE.md forbids real worker footage.
- Six scenes (`Warehouse_001`, `003`, `005`, `007`, `021`, `024`) are Cosmos Transfer re-renderings of `000`, `002`, `004`, `006`, `020`, `023`, with the same scene, cameras and ground truth. They need render-lineage leakage edges under contract section 8.
- The published train, validation and test partitions differ between the 2025 and 2026 editions, so the editions cannot be mixed without a new split.

**Download size.** SDG shards are published as roughly 5 GB tar files, and near-miss artifacts total 2.46 TiB over 547 shards, about 4.6 GiB each. The WORKPLAN section 0 figure of about 1.5 GB cannot cover even one artifacts shard if whole shards are fetched. An artifacts shard repeats the RGB video, so one artifacts shard is enough for a first sample. See `DECISIONS_NEEDED.md` D-3.

## Other sources checked (leads only, all unverified)

| Source | Note |
|---|---|
| SynthSite (arXiv 2607.16351) | Synthetic worker-under-suspended-load benchmark, 55 clips. A construction or crane context, with no confirmed height annotation. Worth reading if E2 scope extends past forklifts |
| LOCO (TUM) | Real still images of logistics objects with forklift and pallet classes. Images only, with no worker-and-load relationship and no height. Licence not read |
| `yangyayaa/Safe_and_Unsafe_Behaviours` | Real workplace clips, with classes such as forklift carrying blocks. Excluded because real worker footage is forbidden |
| Roboflow forklift projects | Community image projects with no height or calibration information found |

## What this implies for later gates

| Work item | Finding | Next evidence needed |
|---|---|---|
| E2-W1, E2-W2 | Possible on SDG forklift–shelf runs if raised loads exist | Inspect one approved artifacts shard during T-17: class labels, prop heights, any load on forks |
| E2-W3 | **needs collection** | Staged protocol in the RD track (E2-W4), using proxies or markers and no person under a real suspended load |
| E2-W5 | Not a data question | Owner decision |

## Sources

- [SDG-Warehouse dataset card](https://huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes)
- [PhysicalAI-SmartSpaces dataset card](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces)
- [Cosmos 3 technical report](https://arxiv.org/pdf/2606.02800)
- [OpenMDW repository](https://github.com/OpenMDW/openmdw)
- [OSI license-review thread on OpenMDW-1.1](https://lists.opensource.org/pipermail/license-review_lists.opensource.org/2026-August/006147.html)
- [SynthSite paper](https://arxiv.org/pdf/2607.16351)
- [LOCO announcement](https://www.mec.ed.tum.de/en/fml/news/article/we-have-just-released-the-first-scene-understanding-dataset-for-logistics/)
- [Safe and Unsafe Behaviours card](https://huggingface.co/datasets/yangyayaa/Safe_and_Unsafe_Behaviours)
