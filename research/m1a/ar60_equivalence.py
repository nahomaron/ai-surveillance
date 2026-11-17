"""AR-60 real-data check: re-evaluate cameras already evaluated with the pre-AR-60 code and compare the outputs.

  python research/m1a/ar60_equivalence.py <scratch_dir> <ds> <label> <rec_id> [<rec_id> ...]

The current code writes each camera's evaluation to <scratch_dir>/<ds>_<rec_id>.pkl.gz (the existing
out/m1a/<label>/<ds>/<rec_id>/eval.pkl.gz, written by the pre-AR-60 code, is only read), and the two pickled outputs are
compared by repr (floats bit-identical). One summary line per camera is appended to research/m1a/ar60_equivalence.jsonl.
"""
import gzip
import json
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import evaluate_m1a as ev  # noqa: E402


def load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def main(scratch, ds, label, recs):
    log = ev.ROOT / "research/m1a/ar60_equivalence.jsonl"
    for rec in recs:
        old_p = ev.out_dir(label, ds) / rec / "eval.pkl.gz"
        new_p = Path(scratch) / f"{ds}_{rec}.pkl.gz"
        if new_p.exists():
            new_p.unlink()
        t0 = time.time()
        ev.evaluate_camera((ds, label, rec, str(new_p)))
        line = {"ds": ds, "label": label, "rec_id": rec, "identical": repr(load(new_p)) == repr(load(old_p)), "eval_s_ar60": round(time.time() - t0, 1)}
        print(json.dumps(line), flush=True)
        with open(log, "a") as f:
            f.write(json.dumps(line) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
