"""X0b partition draw (D-34 item B.2, D-35 option (b); AR-57 item 1)."""
import numpy as np
import pytest

from rq1.schema.errors import ContractError
from rq1.splits import draw


def test_batch_family_is_the_first_path_element():
    assert draw.batch_family("warehouse_osmos_2/nearmiss/shard-15") == "warehouse_osmos_2"
    assert draw.batch_family("warehouse_osmos/nearmiss-1") == "warehouse_osmos"
    assert draw.batch_family("warehouse_osmos_1/nearmiss") == "warehouse_osmos_1"
    assert draw.batch_family("single") == "single"
    for bad in ("", "/x"):
        with pytest.raises(ContractError):
            draw.batch_family(bad)


RUNS = [(f"r{i:02d}", "a/x" if i < 6 else ("b/y/shard-1" if i < 9 else "b/y/shard-2")) for i in range(12)]  # family a: 6 runs, b: 6 runs


def test_counts_per_family_and_procedure():
    """Hand procedure: one PCG64(seed) generator; family a (sorted first) draws 2 of its 6 sorted runs, then family b draws 3 of 6."""
    out = draw.draw_validation(list(reversed(RUNS)), {"a": 2, "b": 3}, seed=2026111401)
    rng = np.random.Generator(np.random.PCG64(2026111401))
    a = [f"r{i:02d}" for i in range(6)]
    b = [f"r{i:02d}" for i in range(6, 12)]
    expected = {a[int(i)] for i in rng.choice(6, 2, replace=False)} | {b[int(i)] for i in rng.choice(6, 3, replace=False)}
    assert {r for r, p in out.items() if p == "validation"} == expected
    assert sum(p == "test" for p in out.values()) == 7
    assert draw.family_table(RUNS, out) == [{"family": "a", "runs": 6, "validation": 2, "test": 4}, {"family": "b", "runs": 6, "validation": 3, "test": 3}]


def test_input_order_does_not_matter_and_seed_does():
    assert draw.draw_validation(RUNS, {"a": 2, "b": 3}, 1) == draw.draw_validation(list(reversed(RUNS)), {"a": 2, "b": 3}, 1)
    assert any(draw.draw_validation(RUNS, {"a": 2, "b": 3}, s) != draw.draw_validation(RUNS, {"a": 2, "b": 3}, 1) for s in range(2, 6))


@pytest.mark.parametrize("counts", [{"a": 7, "b": 3}, {"a": 2}, {"a": 2, "b": 3, "c": 1}, {"a": -1, "b": 3}])
def test_bad_counts_are_refused(counts):
    with pytest.raises(ContractError) as e:
        draw.draw_validation(RUNS, counts, 1)
    assert e.value.code == "ERR-SPEC"


def test_duplicate_runs_are_refused():
    with pytest.raises(ContractError):
        draw.draw_validation(RUNS + [RUNS[0]], {"a": 2, "b": 3}, 1)
