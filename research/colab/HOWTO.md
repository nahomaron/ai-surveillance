# Colab GPU detection: how to run it (Owner, D-60)

What this does: runs the frozen D-45 detector on Google Colab's GPU for the 45 tier-1 videos, after a 2-camera check that the GPU output equals the laptop's CPU output. Only detection (S2) runs on Colab. The agent does everything after that on the laptop.

**Rules (D-60).** Upload only the files listed below: synthetic CC BY 4.0 videos, no real footage. For tier 1, do not open, plot or count the output files. Send the folder back as it is.

**Sizes.**
- Equivalence check: 2 videos, 34,708,143 bytes (**0.03 GB**). List: `research/colab/equivalence_manifest.json`.
- Tier 1: 45 videos, 5,908,702,565 bytes (**5.91 GB**). List: `research/colab/tier1_manifest.json`.
- Total upload: **5.94 GB**. The notebook also downloads the two weight files once (0.38 GB) into the same Drive folder. Outputs are small (estimated well under 1 GB).

---

## 1. Upload the videos to Google Drive, keeping the folder layout

1. On the laptop, in the repository folder, build the upload folder (hard links, so no extra disk space is used):
   ```
   PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py stage equivalence
   PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py stage tier1
   ```
   This creates `out/colab_upload/rq1_colab/data/raw/...`.
2. Open drive.google.com and go to **My Drive**.
3. Drag the folder `out/colab_upload/rq1_colab` into **My Drive**, or use *New → Folder upload*. The result must be `My Drive/rq1_colab/data/raw/...`, with the same sub-folders as on the laptop.
   - You can upload the 2 equivalence videos first (`data/raw/sdg/...`), and the tier-1 videos (`data/raw/smartspaces/...`) later. Tier 1 is only needed from step 4 on.
4. Wait until Drive shows that the upload is complete. The notebook checks the SHA-256 of every file, so an incomplete upload is caught.

## 2. Open the notebook in Colab, choose a GPU, and mount Drive

1. Go to colab.research.google.com → *File → Open notebook → GitHub*. Enter `nahomaron/ai-surveillance`, choose branch `m0-implementation`, and open `research/colab/s2_detect.ipynb`.
2. *Runtime → Change runtime type → Hardware accelerator: GPU* (T4 is enough) → *Save*.
3. In cell 1, leave `JOB = "equivalence"`.
4. *Runtime → Run all*. When asked, allow Colab to access your Google Drive (this is cell 2).
   - Cell 2 stops if no GPU is selected, or if `My Drive/rq1_colab/data` is missing.
   - Cell 3 installs Ultralytics 8.4.215, PyAV 19.0.2 and the pinned CLIP. If it fails, send me the error text and stop.
   - Cell 4 checks every video and the weights. A line starting with `STOPPED:` means a file differs: send me that line.

## 3. Run the 2-camera check, then send the output folder back

1. The equivalence job takes a few minutes. Cell 6 should print `equivalence complete - 2 of 2 cameras, 600 frames`.
2. In Drive, download the folder `My Drive/rq1_colab/out/equivalence` (right-click → *Download*; Drive makes a zip).
3. On the laptop, unzip it so that the files are in `out/colab/equivalence/` in the repository folder: `colab_manifest.json`, two `rec_….json.gz` files, two `rec_….done.json` files and a `pip_freeze_….txt`.
4. Tell the agent: "Colab equivalence outputs are in out/colab/equivalence". The agent compares them with the CPU results and reports pass or fail. **Do not start tier 1 before the agent reports a pass.**

## 4. Run tier 1, and re-run after any disconnect

1. Make sure the tier-1 videos are uploaded (step 1).
2. Open the notebook again (step 2), set `JOB = "tier1"` in cell 1, and choose *Runtime → Run all*.
3. Each camera takes several minutes, and all 45 cameras may take a few hours. This is an estimate only: GPU speed on Colab has not been measured.
4. **If Colab disconnects or the session ends**, open the notebook again, keep `JOB = "tier1"`, and choose *Run all* again. Finished cameras are skipped (`already finished: skipped`). Repeat until cell 6 prints `tier1 complete - 45 of 45 cameras`.
5. Do not open or inspect the `.json.gz` files.

## 5. Download the tier-1 output folder to the laptop

1. In Drive, download `My Drive/rq1_colab/out/tier1`.
2. Unzip it so that the files are in `out/colab/tier1/` in the repository folder: `colab_manifest.json`, 45 `.json.gz` files, 45 `.done.json` files and the `pip_freeze_….txt` file(s).
3. Tell the agent: "Colab tier-1 outputs are in out/colab/tier1". The agent checks every file hash, builds the S2 artifacts and runs the integrity checks (totals only, D-60 STEP 5).

After that, the videos in Drive can be deleted, if you wish. The laptop keeps its own copies.

---

# D-63: the `reporting_test` job (110 reporting + 471 test cameras)

**Replaced by the `test` job (D-64 option a, next section). Do not run `reporting_test`.** It is kept as the record of the D-63 STEP 4 job.

**Status (26 Nov 2026).** The 2-camera equivalence check **passed** (D-62; result in `research/colab/equivalence_result.json`). D-63 rulings 7–8 allow S2 on the reporting and test cameras on Colab, in one session.

**Tier 1 is skipped.** D-63 ruling 5 defers tier 1 past 1 Dec 2026 (CR-039). **Do not run `JOB = "tier1"`**, and you do not need to upload the tier-1 videos. If they are already in Drive, they may stay there or be removed. The laptop keeps its own copies, and the tier-1 manifest stays frozen.

**Rules (D-63).** Upload only the files listed in `research/colab/reporting_test_manifest.json`. They are synthetic SDG videos, not real footage. **Do not open, plot or count the output files**, test cameras especially: the test outputs are sealed until the reporting run is finished (D-63 ruling 8). Send the folder back as it is.

**Sizes and time.**
- Upload: **581 videos, 9,509,264,335 bytes (9.51 GB)**:
  - reporting: 110 videos, 1.81 GB, 32,950 frames;
  - test: 471 videos, 7.70 GB, 141,190 frames.
- **Drive space needed:** about **9.9 GB**, which is 9.51 GB of videos, 0.38 GB of weights (already in Drive from the equivalence run), the 0.03 GB equivalence videos, and outputs of about 10 MB.
  - If the 5.91 GB of tier-1 videos are also in Drive, the total is about 15.8 GB. That is more than the free 15 GB Drive plan. In that case, remove the tier-1 videos from Drive first (step 1 above, `data/raw/smartspaces/...`).
- **Expected runtime on a T4:** about **2.3 hours** for the 174,140 frames. This is based on the equivalence timing (27.9 s for 600 frames = 0.047 s per frame, including decoding): about 0.4 h for reporting and 1.8 h for test.
  - Reading the videos from Drive can add time.
  - A free Colab session may disconnect before it finishes. Re-run as in step 4 above: finished cameras are skipped.

## Steps

1. On the laptop, build the upload folder (hard links, no extra disk space):
   ```
   PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py stage reporting_test
   ```
   The agent has already run this (26 Nov 2026), so the links are in place. The videos are in two folders:
   - `out/colab_upload/rq1_colab/data/raw/sdg/...` (551 videos);
   - `out/colab_upload/rq1_colab/data/derived/sdg_rgb_sample/...` (30 test videos: extracted copies of 3 SDG runs, registered in S0 under this path).
2. Upload **only these two folders**, keeping the layout:
   - `data/raw/sdg` to `My Drive/rq1_colab/data/raw/sdg`;
   - `data/derived` to `My Drive/rq1_colab/data/derived`.

   **Do not upload `data/raw/smartspaces`**: that is tier 1, which is skipped. The two equivalence videos are already in Drive; files already there can be skipped. The notebook checks the SHA-256 of every one of the 581 files.
3. Open the notebook as in step 2 above, with a GPU runtime. In cell 1 set **`JOB = "reporting_test"`**, then *Runtime → Run all*.
4. Cell 6 should end with `reporting_test complete - 581 of 581 cameras`. If not, run again (finished cameras are skipped).
5. Download `My Drive/rq1_colab/out/reporting_test`. Unzip it so that the files are in **`out/colab/reporting_test/`** in the repository folder: `colab_manifest.json`, 581 `.json.gz` files, 581 `.done.json` files and the `pip_freeze_….txt` file(s).
6. Tell the agent: "Colab reporting_test outputs are in out/colab/reporting_test".
   - The agent checks every hash.
   - It runs the reporting cameras (D-63 STEP 5).
   - It records the test hashes without opening the test files (STEP 6).
   - Only after that does it run test (STEP 7).

---

# D-64: the `test` job (471 test cameras only) — run this one

**Status (26 Nov 2026).** D-64 option (a): the reporting run uses the stored CPU S2 of the 110 reporting cameras (frozen v2 S2 IDs), so **Colab runs the test cameras only**. Manifest: `research/colab/test_manifest.json`. Its 471 cameras are exactly the test cameras of `reporting_test_manifest.json`, entry for entry, with the same detector settings.

**Rules (D-63, unchanged).** Upload only the files listed in `test_manifest.json`. They are synthetic SDG videos, not real footage. **Do not open, plot or count the output files**: the test outputs are sealed until the reporting run is finished (D-63 ruling 8). Send the folder back as it is. Tier 1 stays skipped (do not run `JOB = "tier1"`).

**Sizes and time.**
- Upload: **471 videos, 7,703,586,524 bytes (7.70 GB), 141,190 frames.**
- **Drive space needed:** about **8.1 GB**: 7.70 GB of videos, 0.38 GB of weights (already in Drive from the equivalence run), the 0.03 GB equivalence videos, and outputs of about 10 MB.
  - If the 5.91 GB of tier-1 videos are also in Drive, the total is about 14.0 GB. That fits a free 15 GB plan only just; removing the tier-1 videos (`data/raw/smartspaces/...`) first is safer.
- **Expected runtime on a T4:** about **1.8 hours** (141,190 frames at 0.047 s per frame, the equivalence timing). Reading from Drive can add time; after a disconnect, re-run as in step 4: finished cameras are skipped.

## Steps

1. The upload folder is built (hard links, no extra disk space; the agent ran this on 26 Nov 2026):
   ```
   PYTHONPATH=src .venv/bin/python research/colab/make_manifests.py stage test
   ```
   It is a **new folder, `out/colab_upload_test/rq1_colab/data/`**, holding the test videos only:
   - `raw/sdg/...` (441 videos);
   - `derived/sdg_rgb_sample/...` (30 videos: extracted copies of 3 SDG runs, registered in S0 under this path).

   Do not upload from the older `out/colab_upload/` folder: it also holds the 110 reporting videos, which are not needed.
2. Upload these two folders, keeping the layout:
   - `out/colab_upload_test/rq1_colab/data/raw/sdg` to `My Drive/rq1_colab/data/raw/sdg`;
   - `out/colab_upload_test/rq1_colab/data/derived` to `My Drive/rq1_colab/data/derived`.

   Files already in Drive (the two equivalence videos) can be skipped. The notebook checks the SHA-256 of every one of the 471 files.
3. Open the notebook as in step 2 at the top of this file, with a GPU runtime. In cell 1 set **`JOB = "test"`**, then *Runtime → Run all*.
4. Cell 6 should end with `test complete - 471 of 471 cameras`. If not, run again (finished cameras are skipped).
5. Download `My Drive/rq1_colab/out/test`. Unzip it so that the files are in **`out/colab/test/`** in the repository folder: `colab_manifest.json`, 471 `.json.gz` files, 471 `.done.json` files and the `pip_freeze_….txt` file(s).
6. Tell the agent: "Colab test outputs are in out/colab/test".
   - The agent checks every hash and records them without opening the test files (D-63 STEP 6).
   - It runs test (STEP 7) only after the reporting run (STEP 5, from the stored CPU S2) is finished.
