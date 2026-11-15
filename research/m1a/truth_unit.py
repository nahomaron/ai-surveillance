"""T-21: the per-camera truth table and T20.1 visible frames (GV and CM inputs) for cameras without a T21 reference unit
(SmartSpaces, D-39). Same content as the `truth.pkl.gz` that `run_m1a.unit_reference` writes on SDG.
  python research/m1a/truth_unit.py <ds> <label> <rec_id,...>     (one camera at a time; finished cameras are skipped)"""
import gzip, os, pickle, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import m1a_common as m

ds, label, recs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
ctx = m.Context(ds)
for rec in recs:
    ctx.camera(rec)  # ERR-LEAKAGE unless validation (D-37)
    path = m.ROOT / "out/m1a" / label / ds / rec / "truth.pkl.gz"
    if path.exists():
        print(rec, "skipped", flush=True)
        continue
    t0 = time.time()
    data = m.load(ctx, rec)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as f:
        pickle.dump({"truth_table": m.truth_table(data), "visible_frames": m.visible_frames(data)}, f)
    os.replace(tmp, path)
    print(rec, "done", round(time.time() - t0, 1), flush=True)
