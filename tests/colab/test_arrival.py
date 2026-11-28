"""D-63 STEP 6 / T-29h: arrival check of sealed Colab S2 outputs (hashes only; outputs are never decompressed)."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/colab"))
import arrival as A  # noqa: E402

W = {"yolov8s-worldv2.pt": {"sha256": "a" * 64}, "clip/ViT-B-32.pt": {"sha256": "b" * 64}}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def make(tmp: Path, n=2):
    cams = [{"rec_id": f"rec_{k}", "sha256": f"{k}" * 64, "n_eligible": 3 + k} for k in range(n)]
    job = {"format": "rq1-colab-job-1", "job": "fixture", "decision": "D-64", "cameras": cams,
           "detector": {"weights": W}}
    jp = tmp / "job.json"
    jp.write_text(json.dumps(job))
    out = tmp / "out"
    out.mkdir()
    files = []
    for c in cams:
        payload = gzip.compress(b"opaque-" + c["rec_id"].encode(), mtime=0)
        gz = out / f"{c['rec_id']}.json.gz"
        gz.write_bytes(payload)
        side = {"rec_id": c["rec_id"], "file": gz.name, "sha256": sha(payload), "bytes": len(payload),
                "frames": c["n_eligible"], "n_eligible": c["n_eligible"], "input_sha256": c["sha256"]}
        (out / f"{c['rec_id']}.done.json").write_text(json.dumps(side))
        files.append(side)
    m = {"job": "fixture", "job_manifest_sha256": sha(jp.read_bytes()), "complete": True, "cameras_in_job": n,
         "cameras_finished": n, "weights_sha256": {k: v["sha256"] for k, v in W.items()},
         "environment": {"runner_commit": "c0ffee"}, "files": files}
    (out / "colab_manifest.json").write_text(json.dumps(m))
    (out / "pip_freeze_c0ffee.txt").write_text("x==1\n")
    return jp, out


def test_clean_arrival_passes(tmp_path):
    jp, out = make(tmp_path)
    r = A.verify(jp, out)
    assert r["pass"] is True and r["problems"] == []
    assert r["cameras_verified"] == 2 and len(r["files"]) == 2  # 2 cameras made by hand
    assert r["files"][0]["sha256"] == sha((out / "rec_0.json.gz").read_bytes())


def test_never_decompresses(tmp_path, monkeypatch):
    jp, out = make(tmp_path)

    def boom(*a, **k):
        raise AssertionError("sealed output opened")
    monkeypatch.setattr(gzip, "open", boom)
    monkeypatch.setattr(gzip, "decompress", boom)
    monkeypatch.setattr(gzip, "GzipFile", boom)
    assert A.verify(jp, out)["pass"] is True


@pytest.mark.parametrize("breakage", ["tamper", "missing", "extra", "jobsha", "frames", "input", "weights", "incomplete"])
def test_each_defect_fails(tmp_path, breakage):
    jp, out = make(tmp_path)
    m = json.loads((out / "colab_manifest.json").read_text())
    if breakage == "tamper":
        (out / "rec_1.json.gz").write_bytes(b"changed")
    elif breakage == "missing":
        (out / "rec_1.json.gz").unlink()
    elif breakage == "extra":
        (out / "rec_9.json.gz").write_bytes(b"x")
    elif breakage == "jobsha":
        m["job_manifest_sha256"] = "0" * 64
    elif breakage == "frames":
        side = json.loads((out / "rec_0.done.json").read_text())
        side["frames"] = 99
        (out / "rec_0.done.json").write_text(json.dumps(side))
    elif breakage == "input":
        m["files"][0]["input_sha256"] = "f" * 64
    elif breakage == "weights":
        m["weights_sha256"]["yolov8s-worldv2.pt"] = "c" * 64
    elif breakage == "incomplete":
        m["complete"] = False
    (out / "colab_manifest.json").write_text(json.dumps(m))
    r = A.verify(jp, out)
    assert r["pass"] is False and r["problems"]
