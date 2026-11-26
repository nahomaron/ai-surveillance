"""D-60 STEP 4: the Colab package agrees with the CPU detector environment, and the job manifests are consistent."""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/colab"))
from rq1_colab import runner as R  # noqa: E402

NB = json.loads((ROOT / "research/colab/s2_detect.ipynb").read_text())
NB_TEXT = "".join("".join(c["source"]) for c in NB["cells"])
REQ = (ROOT / "research/m1b/requirements_detector.txt").read_text()


def test_pins_equal_the_cpu_detector_environment():
    assert f"ultralytics=={R.PINNED['ultralytics']}" in REQ  # the .venv-det version (D-42)
    assert f'"ultralytics=={R.PINNED["ultralytics"]}"' in NB_TEXT and f'"av=={R.PINNED["av"]}"' in NB_TEXT
    clip = re.search(r"CLIP\.git@([0-9a-f]{40})", REQ).group(1)
    assert f"CLIP.git@{clip}" in NB_TEXT
    import av
    assert av.__version__ == R.PINNED["av"]  # the PyAV of .venv, which decoded the CPU S2 frames


def test_weights_and_detector_settings_equal_d45():
    w = json.loads((ROOT / "research/m1b/zero_shot_weights.json").read_text())
    assert R.WEIGHTS[R.MODEL]["sha256"] == w["yolov8s-worldv2.pt"]["sha256"] and R.WEIGHTS[R.MODEL]["bytes"] == w["yolov8s-worldv2.pt"]["bytes"]
    assert R.WEIGHTS["clip/ViT-B-32.pt"]["sha256"] == w["ViT-B-32.pt (CLIP text encoder)"]["sha256"]
    sys.path.insert(0, str(ROOT / "research/m1b"))
    src = (ROOT / "research/m1b/zero_shot_probe.py").read_text()
    assert 'CLASSES = ("person", "forklift")' in src and "SCORE_MIN = 0.05" in src
    assert R.CLASSES == ("person", "forklift") and R.SCORE_FLOOR == 0.05 and R.PREDICT == {"imgsz": 640, "iou": 0.7, "max_det": 300}
    assert "img[:, :, ::-1]" in src and "img[:, :, ::-1]" in Path(R.__file__).read_text()  # RGB -> BGR in both


@pytest.mark.parametrize("job", ["equivalence", "tier1", "reporting_test"])
def test_manifest_consistent(job):
    p = ROOT / f"research/colab/{job}_manifest.json"
    if not p.exists():
        pytest.skip("manifest not built")
    m = json.loads(p.read_text())
    assert m["format"] == "rq1-colab-job-1" and m["job"] == job and m["decision"] == ("D-63" if job == "reporting_test" else "D-60")
    assert m["videos"] == len(m["cameras"]) and m["total_bytes"] == sum(c["size_bytes"] for c in m["cameras"])
    assert len({c["rec_id"] for c in m["cameras"]}) == len(m["cameras"]) and len({c["uri"] for c in m["cameras"]}) == len(m["cameras"])
    for c in m["cameras"]:
        assert len(R.expand(c["eligible_runs"])) == c["n_eligible"] <= c["n_decoded"] and len(c["sha256"]) == 64
    if job == "equivalence":
        assert [c["rec_id"] for c in m["cameras"]] == ["rec_67do32mc4zwrtblayv5nixp4c2", "rec_4vmkmof7sgq7fbjqm6zb64xpko"]  # AR-70 item 7
    elif job == "reporting_test":
        # D-63 STEP 4: the 110 reporting and 471 test cameras, the v2 reference sets, SDG only, every frame of each
        sys.path.insert(0, str(ROOT / "research/preregistration"))
        import v2_references as vr
        assert m["sets"] == {"reporting": 110, "test": 471} and m["videos"] == 581
        for name in ("reporting", "test"):
            assert sorted(c["rec_id"] for c in m["cameras"] if c["set"] == name) == sorted(vr.cameras(name))
        # SDG files as registered in S0: the dataset members, or the extracted copies of 3 runs (qualification.md, 30 test cameras)
        assert all(c["uri"].startswith(("raw/sdg/", "derived/sdg_rgb_sample/")) for c in m["cameras"])
    else:
        assert m["videos"] == 45 and all("smartspaces" in c["uri"] for c in m["cameras"])
        rec = json.loads((ROOT / "docs/preregistration/freeze_record_X0b-A1.json").read_text())
        assert m["split"]["artifact_id"] == rec["artifact_id"]
        tier1 = {s["scene"] for s in rec["scenes"] if s["partition"] == ["test_layout_holdout"]}
        assert {c["label"].split(".")[0] for c in m["cameras"]} == tier1
