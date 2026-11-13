"""D-23: the declared, seeded subset of Safe and Unsafe Behaviours clips for the second, independent annotator.

Rule: per class (stratum), n_h = ceil(0.25 * N_h); clips of the class sorted by path; numpy PCG64 permutation with seed
2026111223; the first n_h of the permutation. Usage: python -I annotation_subset.py <selection_mendeley.json> <out.json>"""
import json
import math
import sys

import numpy as np

SEED, FRACTION = 2026111223, 0.25
sel = json.load(open(sys.argv[1]))
classes = {}
for f in sel["files"]:
    classes.setdefault(f["path"].split("/")[1], []).append(f["path"])
rng = np.random.Generator(np.random.PCG64(SEED))
out = {"seed": SEED, "fraction_per_class": FRACTION, "rule": __doc__.split("\n\n")[1], "strata": []}
for cls in sorted(classes):
    paths = sorted(classes[cls])
    n = math.ceil(FRACTION * len(paths))
    out["strata"].append({"class": cls, "N_h": len(paths), "n_h": n, "clips": sorted(paths[i] for i in rng.permutation(len(paths))[:n])})
json.dump(out, open(sys.argv[2], "w"), indent=1)
print([(s["class"], s["N_h"], s["n_h"]) for s in out["strata"]], sum(s["n_h"] for s in out["strata"]))
