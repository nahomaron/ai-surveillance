"""V-02 command line. `python -m rq1.review init|serve` from the repository root (PYTHONPATH=src).

  init   create the Owner profile of a validation store (asks for the passphrase on the terminal)
  serve  run the review application on http://127.0.0.1:<port>/ (SDG validation episodes of the T-21 run)
"""
from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from rq1.review.frame import SdgFrame
from rq1.review.server import make_server
from rq1.review.store import Store


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m rq1.review")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create the Owner profile")
    init.add_argument("--store", default="out/review/main")
    init.add_argument("--owner", required=True, help="the Owner's pseudonym")
    serve = sub.add_parser("serve", help="run the review application on 127.0.0.1")
    serve.add_argument("--store", default="out/review/main")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--root", default=".", help="repository root holding out/ and data/")
    serve.add_argument("--configuration", default="BL-6")
    args = parser.parse_args(argv)
    store = Store(Path(args.store))
    if args.command == "init":
        first = getpass.getpass("Owner passphrase: ")
        if first != getpass.getpass("Repeat: "):
            raise SystemExit("The passphrases differ.")
        store.create_owner(args.owner, first)
        print(f"Owner profile created in {args.store}.")
        return
    frames = {args.configuration: SdgFrame(args.root, args.configuration)}
    server = make_server(store, frames, port=args.port)
    print(f"Review application on http://127.0.0.1:{server.server_address[1]}/  (Ctrl-C stops it)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
