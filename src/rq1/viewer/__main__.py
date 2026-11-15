"""V-01 CLI. One self-contained HTML page per validation-partition recording, written under <root>/out/viewer/ (git-ignored).

  PYTHONPATH=src python -m rq1.viewer --rec <rec_id> [--rec <rec_id> ...]
  PYTHONPATH=src python -m rq1.viewer --all-validation [--dataset sdg|smartspaces]
  PYTHONPATH=src python -m rq1.viewer --import-marks <owner_mark_*.json> ...   (merge Owner marks; item 5b)

A recording outside the validation partition of the frozen X0b split, or any recording when no frozen split exists, is
refused with ERR-SPEC. The page records the code commit it was generated from (with "+uncommitted" when the working tree
has changes) and the SHA-256 of docs/preregistration_FROZEN.md.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rq1.schema.errors import ContractError

from . import guard, marks, page
from .recordings import Source


def code_commit(root: Path) -> str:
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
    return head + ("+uncommitted" if dirty else "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m rq1.viewer", description="V-01 truth replay pages (validation partition only)")
    ap.add_argument("--root", default=".", help="repository root (default: current directory)")
    ap.add_argument("--out", default="out/viewer", help="output directory under <root>/out (default: out/viewer)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--rec", action="append", help="recording ID (rec_...); may be repeated")
    group.add_argument("--all-validation", action="store_true", help="every validation-partition recording held")
    group.add_argument("--import-marks", nargs="+", metavar="FILE", help="merge mark files saved by the pages into the Owner marks file")
    ap.add_argument("--dataset", choices=("sdg", "smartspaces"), help="with --all-validation: one dataset only")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    out = (root / args.out).resolve()
    if root / "out" not in out.parents and out != root / "out":
        ap.error("--out must lie under <root>/out (git-ignored)")
    if args.import_marks:
        try:
            split, _ = guard.load_frozen_split(root)
            target, n = marks.import_files(root, args.import_marks, split)
        except (ContractError, ValueError) as e:
            print(f"refused: {e}", file=sys.stderr)
            return 2
        print(f"{target}: {n} clips marked ({marks.LABEL})")
        return 0
    try:
        source = Source(root)
    except ContractError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    commit = code_commit(root)
    recordings = args.rec or [r for r in source.validation_recordings() if not args.dataset or source.entries[r][0] == args.dataset]
    out.mkdir(parents=True, exist_ok=True)
    written, refused = [], 0
    for rec in recordings:
        try:
            data = source.build(rec, commit)
        except ContractError as e:
            print(f"refused {rec}: {e}", file=sys.stderr)
            refused += 1
            continue
        name = source.file_name(rec)
        (out / name).write_text(page.render(data), encoding="utf-8")
        h = data["header"]
        written.append({"file": name, "run": h["run"], "camera": h["camera"], "viewpoint_class": h["viewpoint_class"], "low_light": h["low_light"],
                        "dataset_row": h["dataset_row"]})
        print(f"wrote {out / name}", flush=True)
    if args.all_validation:
        (out / "index.html").write_text(page.render_index(written), encoding="utf-8")
    print(f"{len(written)} written, {refused} refused", flush=True)
    return 0 if not refused else 2


if __name__ == "__main__":
    sys.exit(main())
