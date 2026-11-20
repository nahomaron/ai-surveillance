"""T23 command line. `python -m rq1.workflow demo|summary` from the repository root (PYTHONPATH=src).

  demo     run the T23.11 demo draw on a NEW store (refused if the store already has a demo manifest)
  summary  print the demo manifest summary and the log verification of a store

The application itself is served by `python -m rq1.review serve --store <store>` (one server, one sign-in).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rq1.workflow.demo import SdgDemoSource, draw_demo
from rq1.workflow.store import WorkflowStore


def summary(store: WorkflowStore) -> dict:
    m = store.demo_manifest()
    reports = store.reports()
    ests, areas = store.establishments(), store.areas()
    out = {"demo_id": m["demo_id"] if m else None, "seed": m["seed"] if m else None, "source_path": m["source_path"] if m else None,
           "source_root": m["source_root"] if m else None, "runs": [], "reports": len(reports),
           "verification": {k: ("intact" if not v else v[0].message) for k, v in store.verify().items()},
           "report_log_length": store.report_log.head()[0]}
    for run in (m or {}).get("runs", []):
        rs = [r for r in reports if r.fields.get("area_id") == run["area_id"]]
        out["runs"].append({"run": run["run"], "family": run["family"], "establishment": ests[run["est_id"]]["name"],
                            "area": areas[run["area_id"]]["name"], "cameras": len(run["camera_rec_ids"]),
                            "cameras_with_source_output": len(run["s5_artifact_ids"]), "calendar_offset_s": run["calendar_offset_s"],
                            "reports": len(rs), "members": sum(len(r.header["member_episode_ids"] or []) for r in rs),
                            "kinds": sorted(r.header["kind_initial"] for r in rs)})
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m rq1.workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="run the T23.11 demo draw on a new store")
    demo.add_argument("--store", required=True)
    demo.add_argument("--root", default=".")
    demo.add_argument("--seed", type=int, required=True)
    summ = sub.add_parser("summary", help="print the demo manifest summary")
    summ.add_argument("--store", required=True)
    args = parser.parse_args(argv)
    if args.command == "demo":
        if Path(args.store).exists() and any(Path(args.store).iterdir()):
            raise SystemExit("The demo runs on a NEW store; this folder is not empty.")
        store = WorkflowStore(Path(args.store))
        draw_demo(store, SdgDemoSource(args.root), args.seed)
    else:
        store = WorkflowStore(Path(args.store))
    print(json.dumps(summary(store), indent=1))


if __name__ == "__main__":
    main()
