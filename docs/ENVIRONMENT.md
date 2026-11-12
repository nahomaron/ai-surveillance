# Environment record (WORKPLAN S-01)

Recorded 2026-11-09.

| Item | Value |
|---|---|
| Hardware | Intel Core i7-5650U, 4 logical CPUs, 8 GB RAM, x86_64, no GPU assumed |
| OS | macOS 12.7.6 (21H1320), Darwin 21.6.0 |
| Free disk | 141 GiB on the data volume |
| Python | CPython 3.15.2, uv-managed (`~/.local/bin/python3`), in `.venv` |
| FFmpeg CLI | Not installed and not needed: PyAV wheels bundle FFmpeg libraries |

## Wheel check

Checked with `pip install --dry-run --only-binary=:all:` on CPython 3.15.2 and 3.14.3. Every package has a binary or pure-Python wheel on both.

| Package | Version | Wheel tag on 3.15 |
|---|---|---|
| numpy | 2.5.4 | cp315 macosx_10_15_x86_64 |
| scipy | 1.18.1 | cp315 macosx_10_15_x86_64 |
| pyarrow | 26.0.1 | cp315 macosx_12_0_x86_64 |
| av (PyAV) | 19.0.2 | cp312-abi3 macosx_11_0_x86_64 |
| opencv-python-headless | 4.10.0.84 | cp37-abi3 macosx_12_0_x86_64 |
| jsonschema | 4.26.0 | pure Python |
| hypothesis | 6.170.15 | cp315-abi3 macosx_10_12_x86_64 |
| pytest | 9.2.0 | pure Python |
| rfc8785 (RFC 8785 JCS) | 0.1.4 | pure Python |

opencv-python-headless resolves to 4.10.0.84 because that is the newest release with a wheel for macOS 12 x86_64. Pinning it through `requirements.lock` keeps S1 and geometry behaviour stable.

PyAV bundled library versions: libavcodec 63.1.102, libavformat 63.1.102, libavutil 61.1.102, libswscale 10.1.102. S1 is exact only for this decoder build (contract §2.6).

Direct dependencies are in `requirements.in`; the full pinned set is in `requirements.lock`.

Recreate with:

    ~/.local/bin/python3 -m venv .venv
    .venv/bin/python -m pip install --only-binary=:all: -r requirements.lock
