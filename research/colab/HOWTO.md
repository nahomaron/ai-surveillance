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
