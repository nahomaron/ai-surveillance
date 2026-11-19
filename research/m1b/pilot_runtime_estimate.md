# T-25p runtime estimate (D-45 item 3e), written before the pilot run

Measured on 19 Nov 2026 on one pilot camera (`rec_2lp5aamd7teaxdq4u3pkws5k6m`, 300 eligible frames, 1920 × 1080). The same laptop as the probe: Intel Core i7-5650U, 2 cores, CPU only. Nothing else was running.

- S2 (YOLO-World v2-s), including PyAV decoding in a separate process and the pipe:
  - 0.378 s per frame (median), P90 0.419 s;
  - 118.5 s wall time per camera;
  - model load about 15 s, once per run.
- Population: 206 cameras, 61,749 eligible frames (99 ceiling, 107 eye-level cameras).

| stage | estimate |
|---|---|
| S2 detection, 61,749 frames × 0.388 s | 6.7 h |
| S2 artifact, S3 ByteTrack, S4 full_camera, S5 BL-2..BL-6 (T-21 full_camera unit: median 2.5 s per camera) | about 0.3 h |
| S8 evaluation of columns B and C, aggregation | about 0.5 h |
| Frame-level check (item 3c): Grounding DINO 100 × 16.5 s, YOLO-World 100 × 0.35 s | about 0.5 h |
| **total** | **about 8 h** |

The total is below the 12 h limit, so the pilot goes ahead without a STOP. The S2 run is resumable per camera.
