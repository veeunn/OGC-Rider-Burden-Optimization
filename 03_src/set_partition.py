"""Exact-cover MILP helpers shared by S0 and NSGA-II repair.

All models use the same BIKE candidate pool.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix


def exact_cover_constraints(pool: dict, fixed_num_riders: int | None = None):
    K = int(pool["K"])
    candidates = pool["candidates"]
    n = len(candidates)

    A = lil_matrix((K, n), dtype=float)
    for j, b in enumerate(candidates):
        for order_id in b["shop_seq"]:
            A[int(order_id), j] = 1.0

    constraints = [
        LinearConstraint(A.tocsr(), np.ones(K), np.ones(K))
    ]

    if fixed_num_riders is not None:
        if fixed_num_riders <= 0:
            raise ValueError("fixed_num_riders must be positive.")
        constraints.append(
            LinearConstraint(
                np.ones((1, n), dtype=float),
                np.array([float(fixed_num_riders)]),
                np.array([float(fixed_num_riders)]),
            )
        )
    return constraints


def solve_exact_cover(
    pool: dict,
    objective_coefficients,
    *,
    fixed_num_riders: int | None = None,
    time_limit: float | None = None,
):
    c = np.asarray(objective_coefficients, dtype=float)
    n = len(pool["candidates"])
    if c.shape != (n,):
        raise ValueError(f"Expected {n} objective coefficients, got {c.shape}.")

    options = {}
    if time_limit is not None:
        options["time_limit"] = float(time_limit)

    res = milp(
        c=c,
        integrality=np.ones(n, dtype=int),
        bounds=Bounds(np.zeros(n), np.ones(n)),
        constraints=exact_cover_constraints(pool, fixed_num_riders),
        options=options or None,
    )
    if res.x is None:
        raise RuntimeError(
            f"Exact-cover MILP failed: status={res.status}, message={res.message}"
        )
    x = np.asarray(res.x > 0.5, dtype=np.int8)
    return x, res


def cost_optimal_selection(
    pool: dict,
    *,
    fixed_num_riders: int | None = None,
    time_limit: float | None = None,
):
    costs = np.asarray([b["cost"] for b in pool["candidates"]], dtype=float)
    return solve_exact_cover(
        pool, costs,
        fixed_num_riders=fixed_num_riders,
        time_limit=time_limit,
    )


def nearest_feasible_selection(
    pool: dict,
    target,
    *,
    fixed_num_riders: int,
    rng=None,
    time_limit: float | None = None,
):
    """Repair a binary genotype to the nearest exact-cover solution.

    Hamming distance to target is linear up to an additive constant:
    selecting a target-1 variable receives coefficient -1 and selecting a
    target-0 variable receives +1. Tiny jitter breaks ties reproducibly.
    """
    z = np.asarray(target, dtype=np.int8)
    n = len(pool["candidates"])
    if z.shape != (n,):
        raise ValueError(f"Expected target shape {(n,)}, got {z.shape}.")

    c = np.where(z > 0, -1.0, 1.0)
    if rng is not None:
        c = c + rng.uniform(-1e-6, 1e-6, size=n)

    return solve_exact_cover(
        pool, c,
        fixed_num_riders=fixed_num_riders,
        time_limit=time_limit,
    )
