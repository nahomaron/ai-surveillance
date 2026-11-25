"""D-59 tier-2 draw (qualification Part 5, 5.5): a numpy PCG64 permutation of the tier-2 scenes sorted by name.

Usage: python -I draw.py <candidates.json>
Prints the permutation. Scenes are taken in this order after the ground-truth screen; the draw stops at the first
qualifying scene that does not fit the budget (no skipping to a smaller scene), as in Part 3 (3.1)."""
import json
import sys

import numpy as np

SEED = 2026112459


def main():
    d = json.load(open(sys.argv[1]))
    tier2 = sorted(k for k, v in d["scenes"].items() if v["tier"] == 2)
    perm = np.random.Generator(np.random.PCG64(SEED)).permutation(len(tier2))
    print(json.dumps({"seed": SEED, "sorted": tier2, "order": [tier2[i] for i in perm]}))


if __name__ == "__main__":
    main()
