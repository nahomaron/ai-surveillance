"""AR-58 (D-38 A.1): the faster R4 pet_pred search and the speed-only changes in S4 and S5.

Acceptance (D-38 A.1): against the AR-49 method (kept unchanged in `surrogate_ar49.py`), ttc_s and pet_pred_s within
1e-6 s, nulls identical; every flag identical. The expected values here are the AR-49 method's own outputs, computed in the
test, not edited numbers. The golden-section fixed-point exit is pinned to be bit-identical to the full 200 iterations."""
import math
import random

import pytest

from rq1.events import providers
from rq1.substrate import geometry, surrogate, surrogate_ar49

TOL_S = 1e-6


def _cases(n, seed):
    rng = random.Random(seed)
    for _ in range(n):
        yaw = rng.choice([None, 0.0, math.pi / 2, rng.uniform(-math.pi, math.pi)])
        pv = (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5)) if rng.random() > 0.1 else (0.0, 0.0)
        fv = (rng.uniform(-3, 3), rng.uniform(-3, 3)) if rng.random() > 0.1 else (0.0, 0.0)
        yield ((rng.uniform(-7, 7), rng.uniform(-7, 7)), rng.choice([0.25, 0.30, 0.35]), pv, yaw, fv,
               rng.choice([3.03, 2.68, 2.0]), rng.choice([1.13, 1.16, 1.0]), rng.choice([2.0, 3.0, 4.0]))


def _pet(mod, pc, r, pv, yaw, fv, length, width, tau):
    return mod.pet_pred(mod.person_shape(pc, r), pv, mod.forklift_shape((0.0, 0.0), yaw, length, width), fv, tau)


@pytest.mark.determinism
def test_pet_pred_matches_the_ar49_method_on_random_cases():
    # 2,000 seeded cases over the three priors, the three person radii and tau in {2, 3, 4} s; unknown yaw included.
    n_values = 0
    for case in _cases(2000, 2026111501):
        old, new = _pet(surrogate_ar49, *case), _pet(surrogate, *case)
        assert (old is None) == (new is None), case
        if old is not None:
            n_values += 1
            assert abs(old - new) <= TOL_S, (case, old, new)
    assert n_values > 300  # the sample exercises the non-null branch


@pytest.mark.determinism
def test_pet_pred_matches_the_ar49_method_on_the_t15_fixtures():
    # The T15 fixture geometries (tests/events/test_t15.py): person r 0.30 m, forklift 2.0 x 1.0 m, tau 2.0 s.
    fixtures = [((-3.0, 0.0), (1.5, 0.0), (0.0, 0.0), (0.0, 0.0), 0.0),   # head-on
                ((-6.0, 0.0), (1.5, 0.0), (0.0, 0.0), (0.0, 0.0), 0.0),   # crossing beyond tau
                ((0.0, -3.0), (0.0, 1.5), (-1.0, 0.0), (1.5, 0.0), 0.0),  # crossing paths with a time gap
                ((0.0, -2.0), (0.0, 1.0), (-2.0, 0.0), (1.0, 0.0), 0.0),  # simultaneous occupancy
                ((0.0, 3.0), (1.0, 0.0), (0.0, 0.0), (1.0, 0.0), 0.0),    # parallel paths
                ((0.5, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), 0.0),    # overlap at the frame
                ((-3.0, 0.0), (1.5, 0.0), (0.0, 0.0), (0.0, 0.0), None)]  # unknown yaw
    for pc, pv, fc, fv, yaw in fixtures:
        p_old, f_old = surrogate_ar49.person_shape(pc, 0.30), surrogate_ar49.forklift_shape(fc, yaw, 2.0, 1.0)
        p_new, f_new = surrogate.person_shape(pc, 0.30), surrogate.forklift_shape(fc, yaw, 2.0, 1.0)
        old, new = surrogate_ar49.pet_pred(p_old, pv, f_old, fv, 2.0), surrogate.pet_pred(p_new, pv, f_new, fv, 2.0)
        assert (old is None) == (new is None) and (old is None or abs(old - new) <= TOL_S), (pc, pv, fc, fv, yaw, old, new)


@pytest.mark.determinism
def test_r4_flag_identical_on_random_cases():
    # C_by_R4 from the same row with the AR-49 and the new pet_pred: identical on every case (pet_max on the T15 grid).
    for case in _cases(1000, 2026111502):
        pc, r, pv, yaw, fv, length, width, tau = case
        args = (pc, pv, r, (0.0, 0.0), fv, yaw, length, width)
        _, t_min = geometry.predict_min_clearance(*args, tau)
        t_c = surrogate.ttc(lambda t: geometry.predicted_clearance(*args, t), t_min)
        for pet_max in (0.5, 1.0, 1.5):
            got = []
            for mod in (surrogate_ar49, surrogate):
                pet = _pet(mod, *case)
                row = {"ttc_s": t_c, "pet_pred_s": pet, "ttc_s_null_reason": None if t_c is not None else "not_applicable",
                       "pet_pred_s_null_reason": None if pet is not None else "not_applicable", "clearance_state": "measured"}
                got.append(providers.r4_c(row, 1.0, 1.0, min(1.5, tau), pet_max))
            assert got[0] == got[1], (case, pet_max)


def _argmin_200(f, lo, hi):
    """The AR-49 golden-section loop without the fixed-point exit (all 200 iterations)."""
    ratio = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    for _ in range(200):
        m1, m2 = b - ratio * (b - a), a + ratio * (b - a)
        if f(m1) <= f(m2):
            b = m2
        else:
            a = m1
    return min((f(t), t) for t in (lo, (a + b) / 2, hi))[1]


@pytest.mark.determinism
def test_golden_section_fixed_point_exit_is_bit_identical():
    # Same function, with and without the exit: the same float, bit for bit (flat minima, kinks and smooth minima).
    rng = random.Random(2026111503)
    funcs = [lambda t: abs(t - 0.7), lambda t: max(0.0, abs(t - 1.3) - 0.4) - 0.3, lambda t: (t - 1.9) ** 2, lambda t: math.hypot(t - 0.2, 0.5), lambda t: -1.0]
    for _ in range(200):
        c, w = rng.uniform(-1, 5), rng.uniform(0, 1)
        funcs.append(lambda t, c=c, w=w: max(0.0, abs(t - c) - w))
    for f in funcs:
        for tau in (2.0, 3.0, 4.0):
            assert surrogate._argmin(f, 0.0, tau) == _argmin_200(f, 0.0, tau)


@pytest.mark.determinism
def test_predict_min_clearance_fixed_point_exit_is_bit_identical():
    # The AR-49 predict_min_clearance loop (200 iterations, written out here) against the code with the exit: identical.
    ratio = (math.sqrt(5) - 1) / 2
    for pc, r, pv, yaw, fv, length, width, tau in _cases(300, 2026111504):
        args = (pc, pv, r, (0.0, 0.0), fv, yaw, length, width)
        at = lambda t: geometry.predicted_clearance(*args, t)
        lo, hi = 0.0, tau
        for _ in range(200):
            m1, m2 = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
            if at(m1) <= at(m2):
                hi = m2
            else:
                lo = m1
        assert geometry.predict_min_clearance(*args, tau) == min((at(t), t) for t in (0.0, (lo + hi) / 2, tau))


@pytest.mark.determinism
def test_minkowski_gap_equals_the_polygon_gap():
    # gap(F + v t, G) computed both ways: equal to 1e-12 m on random shapes and times.
    rng = random.Random(2026111505)
    for _ in range(300):
        fork = surrogate.forklift_shape((rng.uniform(-3, 3), rng.uniform(-3, 3)), rng.uniform(-3, 3), 3.03, 1.13)
        person = surrogate.person_shape((rng.uniform(-3, 3), rng.uniform(-3, 3)), 0.3)
        v = (rng.uniform(-2, 2), rng.uniform(-2, 2))
        region = surrogate.swept(fork, (rng.uniform(-2, 2), rng.uniform(-2, 2)), 2.0)
        f = surrogate._path_gap(person, v, region)
        for t in (0.0, rng.uniform(0, 2), 2.0):
            ref = surrogate.gap(person.moved((v[0] * t, v[1] * t)), region)
            assert abs(f(t) - ref) <= 1e-12
