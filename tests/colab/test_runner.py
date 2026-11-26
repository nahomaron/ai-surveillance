"""D-60 STEP 4 (a): the Colab runner, with a fake detector (Ultralytics is not in `.venv`). A clip is encoded in the test."""
import gzip
import json
import sys
from pathlib import Path

import av
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/colab"))
from rq1_colab import runner as R  # noqa: E402

# research/m1b/s2_yolo_world.py writes these keys; the Colab file must carry every one of them (same format)
CPU_KEYS = {"rec_id", "model", "weights_sha256", "classes", "score_floor", "predict", "width", "height", "frames", "seconds",
            "first_frame_includes_warmup", "wall_s", "torch", "torch_threads", "ultralytics", "python", "code_commit"}


def clip(path: Path, n=8, w=32, h=16):
    with av.open(str(path), "w") as c:
        s = c.add_stream("mpeg4", rate=10)
        s.width, s.height, s.pix_fmt = w, h, "yuv420p"
        for k in range(n):
            img = np.full((h, w, 3), 20 * k, dtype=np.uint8)
            for p in s.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
                c.mux(p)
        for p in s.encode():
            c.mux(p)


def job(tmp: Path, eligible: dict[int, int], n=8):
    video = tmp / "data/raw/x/videos/Camera_0000.mp4"
    video.parent.mkdir(parents=True)
    clip(video, n)
    cam = {"rec_id": "rec_a", "uri": "raw/x/videos/Camera_0000.mp4", "sha256": R.sha256(video), "size_bytes": video.stat().st_size,
           "n_eligible": len(eligible), "eligible_runs": R.compress(eligible)}
    j = {"format": "rq1-colab-job-1", "job": "test", "decision": "D-60", "cameras": [cam]}
    (tmp / "job.json").write_text(json.dumps(j))
    return j


def fake(img):
    return [{"class": "person", "box": [1.0, 2.0, 3.0, 4.0], "score": round(float(img.mean()) / 255, 6)}]


def weights(tmp: Path, monkeypatch):
    blobs = {name: name.encode() * 3 for name in R.WEIGHTS}
    monkeypatch.setattr(R, "WEIGHTS", {n: {"url": f"u/{n}", "bytes": len(b), "sha256": __import__("hashlib").sha256(b).hexdigest()} for n, b in blobs.items()})
    for n, b in blobs.items():
        (tmp / "w" / n).parent.mkdir(parents=True, exist_ok=True)
        (tmp / "w" / n).write_bytes(b)


def args(tmp):
    return ["--job", str(tmp / "job.json"), "--data-root", str(tmp / "data"), "--out", str(tmp / "out"), "--weights-dir", str(tmp / "w"), "--device", "cpu"]


def test_compress_expand():
    m = {0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 9: 9}
    assert R.compress(m) == [[0, 3, 0], [4, 2, 3], [9, 1, 9]]  # hand-written runs
    assert R.expand(R.compress(m)) == m
    with pytest.raises(R.RunnerError):
        R.expand([[0, 2, 0], [1, 1, 5]])  # decode_seq 1 twice


def test_frames_are_the_eligible_ones_in_decode_order(tmp_path):
    clip(tmp_path / "c.mp4")
    got = [(k, i) for k, i, _ in R.frames(tmp_path / "c.mp4", {1: 0, 2: 1, 6: 2})]
    assert got == [(1, 0), (2, 1), (6, 2)]
    with av.open(str(tmp_path / "c.mp4")) as c:
        direct = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    assert all(np.array_equal(img, direct[k]) for k, _, img in R.frames(tmp_path / "c.mp4", {1: 0, 6: 1}))
    with pytest.raises(R.RunnerError):
        list(R.frames(tmp_path / "c.mp4", {1: 0, 50: 1}))  # a listed frame the video does not have


def test_run_writes_the_s2raw_format_and_resumes(tmp_path, monkeypatch):
    weights(tmp_path, monkeypatch)
    job(tmp_path, {k: k for k in range(8) if k != 3})
    m = R.main(args(tmp_path), detector=fake)
    assert m["complete"] and m["cameras_finished"] == 1 and m["frames_total"] == 7 and len(m["job_manifest_sha256"]) == 64
    raw = json.load(gzip.open(tmp_path / "out/rec_a.json.gz", "rt"))
    assert CPU_KEYS <= set(raw)
    assert [f["decode_seq"] for f in raw["frames"]] == [0, 1, 2, 4, 5, 6, 7] and raw["frames"][0]["detections"][0]["class"] == "person"
    assert (raw["width"], raw["height"], raw["score_floor"], raw["predict"]) == (32, 16, 0.05, {"imgsz": 640, "iou": 0.7, "max_det": 300, "device": "cpu"})
    side = json.loads((tmp_path / "out/rec_a.done.json").read_text())
    assert side["sha256"] == R.sha256(tmp_path / "out/rec_a.json.gz") == m["files"][0]["sha256"]
    calls = []
    R.main(args(tmp_path), detector=lambda img: calls.append(1) or [])
    assert calls == []  # finished camera skipped
    (tmp_path / "out/rec_a.json.gz").write_bytes(b"broken")  # an output that no longer matches its sidecar is redone
    R.main(args(tmp_path), detector=lambda img: calls.append(1) or [])
    assert len(calls) == 7


def test_input_and_weight_checks(tmp_path, monkeypatch):
    weights(tmp_path, monkeypatch)
    j = job(tmp_path, {0: 0})
    j["cameras"][0]["sha256"] = "0" * 64
    (tmp_path / "job.json").write_text(json.dumps(j))
    with pytest.raises(R.RunnerError, match="input check failed"):
        R.main(args(tmp_path), detector=fake)
    job_ok = job(tmp_path / "b", {0: 0})
    (tmp_path / "b/w").mkdir()
    name = next(iter(R.WEIGHTS))
    (tmp_path / "b/w" / name).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "b/w" / name).write_bytes(b"other weights")
    with pytest.raises(R.RunnerError, match="differs from the D-45 weights"):
        R.fetch_weights(tmp_path / "b/w", download=lambda url, p: p.write_bytes(b"x"))
    assert job_ok["cameras"][0]["n_eligible"] == 1


def test_missing_weights_are_downloaded_then_checked(tmp_path, monkeypatch):
    weights(tmp_path, monkeypatch)
    blobs = {n: (tmp_path / "w" / n).read_bytes() for n in R.WEIGHTS}
    urls = []
    got = R.fetch_weights(tmp_path / "w2", download=lambda url, p: (urls.append(url), p.write_bytes(blobs[url[2:]])))
    assert sorted(urls) == sorted(f"u/{n}" for n in R.WEIGHTS) and got == {n: w["sha256"] for n, w in R.WEIGHTS.items()}
