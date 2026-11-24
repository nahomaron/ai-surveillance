# Notes for pre-registration v2

Pre-registration v1 (`docs/preregistration_FROZEN.md`) and its frozen criteria are unchanged. This file collects what the Owner has recorded for v2, with its source. It is a record, not a pre-registration.

## Position accuracy (D-41, 17 Nov 2026)
- State position accuracy as **median, P95 and outlier share** (the share above stated distances). GV-01 RMSE is dominated by outliers.
- Report **position availability** separately: the share of object-frames with a numeric position, by null reason.

## Licence rows in the S2 artifact (D-47 item 5, 19 Nov 2026)
- The next S2 build carries the `license_component` rows of every weight file it loads inside the artifact: the CLIP ViT-B/32 text encoder (`lic_ym5owzhkkwvjzayaewgzuzhpyc`) and, if it is used, Grounding DINO tiny (`lic_bim7wazyo5z6kh4iiks4hvky2q`). They sit beside the YOLO-World row. The rows are in `research/m1b/pilot_license_components.json`.

## Detector and tracker as one package (D-50 item 3, 19 Nov 2026)
- The detector thresholds and **all** tracker parameters, `fuse_score` included, are fixed as **one package**.
- **Tuning subset:** the package is chosen only on all cameras of the runs that contain a T-22 probe camera. That is 13 of the 24 SDG validation runs: 116 cameras (54 ceiling, 62 eye-level), counted on 19 Nov 2026.
- **Reporting:** v2 results are reported on the other validation runs (11 runs, 110 cameras: 55 ceiling, 55 eye-level) and on test (D-37 still reserves the test partition).
- **Why** (T-25p pilot, `reports/M1b_pilot_report.md`):
  - D-45 fixed the forklift detector threshold at 0.05, while ByteTrack's defaults start tracks at 0.25. That cost most forklift tracks (column C).
  - Aligning the start thresholds alone (C') made it worse, because `fuse_score` needs IoU × score ≥ 0.2 to continue a track.
  - The parameters interact, so they cannot be chosen one at a time.

## Questions for the Architect
- **Episode extent and fragmentation** (D-50 item 2; `research/m1b/pilot_extent.json`). On the detector path (C, BL-6), 141 of 142 events overlap a reference interaction of the same pair, but only 31 match under N4 (temporal IoU ≥ 0.3).
  - 55 of the 111 unmatched events overlap with IoU ≤ 0.1.
  - 38 of the 100 references found by overlap are covered by two or more separate episodes, and only 4 of those 145 episodes are linked by `continuation_of_nk`.
  - Should v2 define how fragmented episodes of one pair are joined, or how an event's extent is compared, on the detector path? This is a question only; N4 is unchanged.
- **Inputs for v2, for the Architect** (D-50 item 4; no rule is implemented now):
  - CR-007: the footprint anchor. The evidence is now sufficient: the forklift error lies along the line of sight, −1.01 m, against 0.09 m across.
  - CR-029: N9 rules 4 and 5 on the detector path.
  - CR-026: a range condition for full_camera foot rays.

## Tracker package selected (D-55, 23 Nov 2026)
- Selected package `trc_7flfpx52d2siiljxkqwcorr7nz`: person ByteTrack at the installed defaults (column C); forklift ByteTrack with track_high_thresh 0.05, new_track_thresh 0.05, track_low_thresh 0.05, fuse_score false, track_buffer 90, match_thresh 0.8 (`research/m1b/v2_tracker_report.md`). **Selected under D-55, not frozen.**
