"""X0b partition draw for the M1a split (Owner decisions D-34 item B.2 and D-35, 14 Nov 2026).

Strata: the batch family of a run = the first path element of its session lineage `generation_batch` (T14.1; e.g.
`warehouse_osmos_2/nearmiss/shard-15` -> `warehouse_osmos_2`). Validation counts per family are given (D-35: warehouse_osmos
12 of 36, warehouse_osmos_2 7 of 20, warehouse_osmos_1 5 of 16); the other runs are test. Inside each family: a simple
random draw without replacement, runs sorted by ext_run_id, numpy PCG64 seeded once with the draw seed; families are drawn
in sorted family order from that one generator (AR-57 item 1). Inputs are pre-system metadata only (R-4).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from rq1.schema.errors import ContractError

DERIVATION = ("batch family = first path element of session.lineage.generation_batch (split at '/'); validation runs per family "
              "drawn by simple random sampling without replacement, runs sorted by ext_run_id, one numpy PCG64 generator seeded with "
              "the draw seed, families drawn in sorted family order; all other runs are test")


def batch_family(generation_batch: str) -> str:
    if not generation_batch or generation_batch.startswith("/"):
        raise ContractError("ERR-SPEC", f"generation_batch without a first path element: {generation_batch!r}")
    return generation_batch.split("/", 1)[0]


def draw_validation(runs: list[tuple[str, str]], n_validation: dict[str, int], seed: int) -> dict[str, str]:
    """`runs`: (ext_run_id, generation_batch). Returns ext_run_id -> 'validation' | 'test'."""
    ids = [r for r, _ in runs]
    if len(set(ids)) != len(ids):
        raise ContractError("ERR-SPEC", "duplicate ext_run_id in the draw input")
    family = {r: batch_family(b) for r, b in runs}
    families = sorted(set(family.values()))
    if sorted(n_validation) != families:
        raise ContractError("ERR-SPEC", f"validation counts given for {sorted(n_validation)}, families present {families}")
    rng = np.random.Generator(np.random.PCG64(seed))
    out = {r: "test" for r in ids}
    for f in families:
        members = sorted(r for r in ids if family[r] == f)
        n = n_validation[f]
        if not 0 <= n <= len(members):
            raise ContractError("ERR-SPEC", f"family {f}: n_validation {n} outside 0..{len(members)}")
        for i in rng.choice(len(members), n, replace=False):
            out[members[int(i)]] = "validation"
    return out


def family_table(runs: list[tuple[str, str]], partition: dict[str, str]) -> list[dict[str, Any]]:
    """Per family: N, validation, test (for the frozen document and the freeze record)."""
    fam = {r: batch_family(b) for r, b in runs}
    return [{"family": f, "runs": sum(1 for r in fam if fam[r] == f), "validation": sum(1 for r in fam if fam[r] == f and partition[r] == "validation"),
             "test": sum(1 for r in fam if fam[r] == f and partition[r] == "test")} for f in sorted(set(fam.values()))]
