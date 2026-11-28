"""Terminal D-66 controls for the packaged Colab runner and arrival verifier."""
from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

CLOSED_JOBS = frozenset({"test", "reporting_test"})


@lru_cache(maxsize=1)
def identifiers():
    rows = json.loads(files(__package__).joinpath("closed_sdg.json").read_text(encoding="utf-8"))
    uris, hashes = zip(*rows.values())
    return frozenset(rows), frozenset(Path(uri).name for uri in uris), frozenset(hashes)


def refuse_job(job: str | None) -> None:
    if job in CLOSED_JOBS:
        raise ValueError("D-66 permanently closed the SDG final test")


def refuse_path(path: Path) -> None:
    names = identifiers()[1]
    if path.name in names or path.resolve().name in names:
        raise ValueError("D-66 permanently closed the SDG final test")


def refuse_camera(camera: dict, data_root: Path | None = None) -> None:
    recs, _, hashes = identifiers()
    uri = camera.get("uri")
    if camera.get("set") == "test" or camera["rec_id"] in recs or camera.get("sha256") in hashes:
        raise ValueError("D-66 permanently closed the SDG final test")
    if uri is not None:
        refuse_path((data_root or Path()) / uri)


def refuse_manifest(job: dict, data_root: Path | None = None) -> None:
    refuse_job(job.get("job"))
    for camera in job["cameras"]:
        refuse_camera(camera, data_root)
