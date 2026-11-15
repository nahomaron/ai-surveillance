"""V-01 item 5b (D-36 follow-up, Owner, 14 Nov 2026): Owner marks, one per clip (recording page).

The file `out/viewer/owner_marks.json` (git-ignored) holds the Owner's answer to "Would you send this clip for review?
yes / no / unsure" and a free-text note, per validation-partition recording. It is labelled "exploratory, Owner impression,
not a reference label" and is read by no stage: no module of rq1 other than this one names it, and nothing here feeds a
reference, label, metric or configuration.

A page opened from disk cannot write a file by itself. It either writes the merged file directly where the browser allows
the Owner to pick it (File System Access, Chromium-based browsers), or saves a one-clip mark file that
`python -m rq1.viewer --import-marks <file> ...` merges into `out/viewer/owner_marks.json` with the checks below.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rq1.schema.errors import ContractError

from . import guard

Row = dict[str, Any]
QUESTION = "Would you send this clip for review? yes / no / unsure"
LABEL = "exploratory, Owner impression, not a reference label"
READ_BY = "no stage"
SCHEMA = "rq1-viewer-owner-marks/1"
ANSWERS = ("yes", "no", "unsure")
FILE = Path("out") / "viewer" / "owner_marks.json"
_FIELDS = {"answer", "note", "run", "camera", "dataset_row", "page_code_commit"}


def empty() -> Row:
    return {"label": LABEL, "question": QUESTION, "read_by": READ_BY, "schema": SCHEMA, "marks": {}}


def page_block() -> Row:
    """What a page needs to show and save marks."""
    return {"label": LABEL, "question": QUESTION, "read_by": READ_BY, "schema": SCHEMA, "answers": list(ANSWERS), "file": FILE.as_posix()}


def _check(doc: Row, split: Row, source: str) -> None:
    for key, value in (("label", LABEL), ("question", QUESTION), ("read_by", READ_BY), ("schema", SCHEMA)):
        if doc.get(key) != value:
            raise ContractError("ERR-SPEC", f"{source}: {key} must be {value!r}")
    if not isinstance(doc.get("marks"), dict):
        raise ContractError("ERR-SPEC", f"{source}: no marks")
    for rec, mark in doc["marks"].items():
        guard.require_validation(split, rec)  # validation-partition clips only (D-37)
        if not isinstance(mark, dict) or set(mark) - _FIELDS or mark.get("answer") not in ANSWERS:
            raise ContractError("ERR-SPEC", f"{source}: {rec}: the answer must be one of {ANSWERS}")
        if not all(isinstance(mark.get(k, ""), str) for k in _FIELDS):
            raise ContractError("ERR-SPEC", f"{source}: {rec}: every field is text")


def merge(existing: Row, paths: list[str | Path], split: Row) -> Row:
    """`existing` plus the marks of each file, in order; a later mark of the same clip replaces the earlier one."""
    _check(existing, split, "existing marks file")
    out = {**existing, "marks": dict(existing["marks"])}
    for path in paths:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        _check(doc, split, str(path))
        out["marks"].update(doc["marks"])
    return out


def write(doc: Row, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def import_files(root: str | Path, paths: list[str | Path], split: Row) -> tuple[Path, int]:
    """Merge mark files into <root>/out/viewer/owner_marks.json. Returns the path and the number of clips marked."""
    target = Path(root) / FILE
    existing = json.loads(target.read_text(encoding="utf-8")) if target.exists() else empty()
    doc = merge(existing, paths, split)
    write(doc, target)
    return target, len(doc["marks"])
