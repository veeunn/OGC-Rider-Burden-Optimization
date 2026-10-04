"""NSGA-II over feasible bundle selections with S0-fixed workforce.

Representation
--------------
A chromosome is a binary vector over a shared BIKE candidate bundle pool.
Individuals are maintained as exact-cover selections so that:

1. every order is covered exactly once; and
2. exactly R0 bundles / active riders are selected.

The current Stage 1 implementation uses feasibility-preserving two-route
exchange moves as the primary variation operator. This avoids repeatedly
solving an exact-cover repair MILP for large candidate pools while keeping
the NSGA-II non-dominated sorting and crowding-distance selection framework.

Objectives
----------
f1 = average delivery cost
f2 = inequality of the selected rider burdens

S1 burden = order count
S2 burden = active route duration
S3 burden = waiting time

The default inequality objective is Gini. Other implemented metrics can be
selected explicitly for sensitivity analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from typing import Iterable

import numpy as np

from set_partition import nearest_feasible_selection


def gini(values: Iterable[float]) -> float:
    x = np.asarray(list(values), dtype=float)
    if x.size == 0:
        raise ValueError("At least one burden value is required.")
    if np.any(x < 0):
        raise ValueError("Burden values must be non-negative.")
    total = float(x.sum())
    if total == 0.0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1, dtype=float)
    return float((2.0 * np.sum(idx * x) / (n * total)) - (n + 1.0) / n)


def inequality(values: np.ndarray, metric: str) -> float:
    metric = metric.lower()
    if metric == "gini":
        return gini(values)
    if metric in {"std", "sd"}:
        return float(np.std(values, ddof=0))
    if metric == "range":
        return float(np.max(values) - np.min(values))
    if metric == "max":
        return float(np.max(values))
    if metric == "cv":
        mean = float(np.mean(values))
        return float(np.std(values, ddof=0) / mean) if mean != 0 else 0.0
    raise ValueError(f"Unsupported inequality metric: {metric}")


def _metric_field(scenario: str) -> str:
    return {
        "S1": "order_count",
        "S2": "active_route_duration_sec",
        "S3": "waiting_time_sec",
    }[scenario.upper()]


def evaluate(pool: dict, x: np.ndarray, scenario: str, metric: str = "gini") -> tuple[float, float]:
    chosen = np.flatnonzero(x > 0)
    if chosen.size == 0:
        raise ValueError("No bundles selected.")

    candidates = pool["candidates"]
    total_cost = float(sum(candidates[i]["cost"] for i in chosen))
    avg_cost = total_cost / float(pool["K"])

    field = _metric_field(scenario)
    burdens = np.asarray([candidates[i][field] for i in chosen], dtype=float)
    return avg_cost, inequality(burdens, metric)


def dominates(a, b) -> bool:
    return (a[0] <= b[0] and a[1] <= b[1]) and (a[0] < b[0] or a[1] < b[1])


def fast_non_dominated_sort(objectives: list[tuple[float, float]]) -> list[list[int]]:
    n = len(objectives)
    dominates_set = [set() for _ in range(n)]
    dominated_count = [0] * n
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(objectives[p], objectives[q]):
                dominates_set[p].add(q)
            elif dominates(objectives[q], objectives[p]):
                dominated_count[p] += 1
        if dominated_count[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in dominates_set[p]:
                dominated_count[q] -= 1
                if dominated_count[q] == 0:
                    nxt.append(q)
        i += 1
        fronts.append(nxt)

    return fronts[:-1]


def crowding_distance(front: list[int], objectives: list[tuple[float, float]]) -> dict[int, float]:
    if not front:
        return {}
    d = {i: 0.0 for i in front}
    if len(front) <= 2:
        return {i: math.inf for i in front}

    for m in range(2):
        ordered = sorted(front, key=lambda i: objectives[i][m])
        d[ordered[0]] = math.inf
        d[ordered[-1]] = math.inf
        lo = objectives[ordered[0]][m]
        hi = objectives[ordered[-1]][m]
        if hi == lo:
            continue
        for pos in range(1, len(ordered) - 1):
            prev_v = objectives[ordered[pos - 1]][m]
            next_v = objectives[ordered[pos + 1]][m]
            d[ordered[pos]] += (next_v - prev_v) / (hi - lo)
    return d


def rank_and_crowding(objectives):
    fronts = fast_non_dominated_sort(objectives)
    rank = {}
    crowd = {}
    for r, front in enumerate(fronts):
        for i in front:
            rank[i] = r
        crowd.update(crowding_distance(front, objectives))
    return fronts, rank, crowd


def tournament(rng, rank, crowd):
    a, b = rng.integers(0, len(rank), size=2)
    if rank[a] < rank[b]:
        return a
    if rank[b] < rank[a]:
        return b
    if crowd[a] > crowd[b]:
        return a
    if crowd[b] > crowd[a]:
        return b
    return int(a if rng.random() < 0.5 else b)


def crossover(rng, a: np.ndarray, b: np.ndarray, probability: float):
    if rng.random() >= probability:
        return a.copy(), b.copy()
    mask = rng.random(a.size) < 0.5
    c1 = np.where(mask, a, b).astype(np.int8)
    c2 = np.where(mask, b, a).astype(np.int8)
    return c1, c2


def mutate(rng, x: np.ndarray, probability: float):
    y = x.copy()
    flips = rng.random(y.size) < probability
    y[flips] = 1 - y[flips]
    return y

def _subset_candidate_index(pool: dict) -> dict[frozenset[int], list[int]]:
    """Map each unordered order subset to candidate-route ids."""
    out: dict[frozenset[int], list[int]] = {}
    for cid, candidate in enumerate(pool["candidates"]):
        key = frozenset(int(i) for i in candidate["shop_seq"])
        out.setdefault(key, []).append(cid)
    return out


def feasible_route_exchange(
    pool: dict,
    x: np.ndarray,
    rng,
    subset_index: dict[frozenset[int], list[int]],
    *,
    max_tries: int = 50,
) -> np.ndarray:
    """Return a feasible fixed-R0 neighbor using a 2-route exchange.

    Two selected routes are removed. Their union of orders is repartitioned
    into two feasible candidate routes from the same candidate pool. Because
    the union is preserved and two routes replace two routes, exact coverage
    and R0 are preserved without solving a repair MILP.
    """
    y0 = np.asarray(x, dtype=np.int8)
    selected = np.flatnonzero(y0 > 0)
    if selected.size < 2:
        return y0.copy()

    candidates = pool["candidates"]
    max_bundle_size = max(
        (len(candidate["shop_seq"]) for candidate in candidates),
        default=1,
    )

    for _ in range(max_tries):
        old_ids = rng.choice(selected, size=2, replace=False)
        old_a, old_b = int(old_ids[0]), int(old_ids[1])
        union = frozenset(
            list(candidates[old_a]["shop_seq"]) + list(candidates[old_b]["shop_seq"])
        )
        if len(union) < 2 or len(union) > 2 * max_bundle_size:
            continue

        anchor = min(union)
        others = sorted(union - {anchor})
        alternatives: list[tuple[int, int]] = []

        max_left = min(max_bundle_size, len(union) - 1)
        for left_size in range(1, max_left + 1):
            for rest in combinations(others, left_size - 1):
                left = frozenset((anchor, *rest))
                right = union - left
                if not right or len(right) > max_bundle_size:
                    continue
                left_ids = subset_index.get(left)
                right_ids = subset_index.get(right)
                if not left_ids or not right_ids:
                    continue

                # Usually each subset has one candidate. Size-4 generation can
                # leave multiple route sequences for the same order subset.
                for new_a in left_ids:
                    for new_b in right_ids:
                        if new_a == new_b:
                            continue
                        if {int(new_a), int(new_b)} == {old_a, old_b}:
                            continue
                        alternatives.append((int(new_a), int(new_b)))

        if not alternatives:
            continue

        new_a, new_b = alternatives[int(rng.integers(0, len(alternatives)))]
        y = y0.copy()
        y[old_a] = 0
        y[old_b] = 0
        y[new_a] = 1
        y[new_b] = 1
        return y

    return y0.copy()


def diversify_feasible(
    pool: dict,
    x: np.ndarray,
    rng,
    subset_index: dict[frozenset[int], list[int]],
    *,
    exchanges: int = 1,
) -> np.ndarray:
    """Apply one or more feasibility-preserving route exchanges."""
    y = np.asarray(x, dtype=np.int8).copy()
    for _ in range(max(1, int(exchanges))):
        z = feasible_route_exchange(pool, y, rng, subset_index)
        if not np.array_equal(z, y):
            y = z
    return y



def selection_is_feasible(pool: dict, x: np.ndarray, r0: int) -> bool:
    """Check exact order coverage and the fixed-R0 workforce constraint."""
    z = np.asarray(x, dtype=np.int8)
    n = len(pool["candidates"])
    if z.shape != (n,) or int(z.sum()) != int(r0):
        return False

    coverage = np.zeros(int(pool["K"]), dtype=np.int16)
    for idx in np.flatnonzero(z > 0):
        for order_id in pool["candidates"][int(idx)]["shop_seq"]:
            coverage[int(order_id)] += 1
    return bool(np.all(coverage == 1))


def repair(pool: dict, x: np.ndarray, r0: int, rng, repair_time_limit: float | None):
    # Do not solve another MILP when the target is already feasible.  This is
    # especially important for the exact S0 seed supplied to S1-S3.
    z = np.asarray(x, dtype=np.int8)
    if selection_is_feasible(pool, z, r0):
        return z.copy()

    repaired, _ = nearest_feasible_selection(
        pool,
        z,
        fixed_num_riders=r0,
        rng=rng,
        time_limit=repair_time_limit,
    )
    return repaired


def deduplicate(population: list[np.ndarray]) -> list[np.ndarray]:
    seen = set()
    out = []
    for x in population:
        key = x.tobytes()
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


@dataclass
class NSGA2Result:
    population: list[np.ndarray]
    objectives: list[tuple[float, float]]
    pareto_indices: list[int]
    generations: int
    seed: int
    repair_failures: int
    variation_failures: int


def solve(
    pool: dict,
    *,
    scenario: str,
    r0: int,
    metric: str = "gini",
    population_size: int = 40,
    generations: int = 50,
    crossover_probability: float = 0.9,
    mutation_probability: float | None = None,
    seed: int = 0,
    repair_time_limit: float | None = 10.0,
    initial_solutions: list[np.ndarray] | None = None,
) -> NSGA2Result:
    scenario = scenario.upper()
    if scenario not in {"S1", "S2", "S3"}:
        raise ValueError("scenario must be S1, S2, or S3")
    if population_size < 4:
        raise ValueError("population_size must be >= 4")
    n = len(pool["candidates"])
    if mutation_probability is None:
        mutation_probability = min(0.05, max(1.0 / max(n, 1), 0.001))

    rng = np.random.default_rng(seed)

    population = []
    repair_failures = 0
    variation_failures = 0
    subset_index = _subset_candidate_index(pool)

    def safe_repair(target: np.ndarray, fallback: np.ndarray | None = None) -> np.ndarray:
        nonlocal repair_failures
        try:
            return repair(pool, target, r0, rng, repair_time_limit)
        except RuntimeError as exc:
            if fallback is not None and selection_is_feasible(pool, fallback, r0):
                repair_failures += 1
                return np.asarray(fallback, dtype=np.int8).copy()
            raise exc

    if initial_solutions:
        for x in initial_solutions:
            population.append(
                safe_repair(np.asarray(x, dtype=np.int8), fallback=None)
            )

    if not population:
        raise ValueError("At least one feasible initial solution is required.")

    # Build the starting population with feasibility-preserving route
    # exchanges around S0. This avoids expensive exact-cover repair while
    # creating genuinely different fixed-R0 solutions.
    base_seed = population[0].copy()
    attempts = 0
    max_attempts = max(population_size * 20, 40)
    while len(population) < population_size and attempts < max_attempts:
        attempts += 1
        exchanges = 1 + (attempts % 4)
        neighbor = diversify_feasible(
            pool,
            base_seed,
            rng,
            subset_index,
            exchanges=exchanges,
        )
        if np.array_equal(neighbor, base_seed):
            variation_failures += 1
        population.append(neighbor)
        population = deduplicate(population)

    while len(population) < population_size:
        population.append(base_seed.copy())

    population = population[:population_size]

    for _gen in range(generations):
        objectives = [evaluate(pool, x, scenario, metric) for x in population]
        _, rank, crowd = rank_and_crowding(objectives)

        offspring = []
        while len(offspring) < population_size:
            p1 = population[tournament(rng, rank, crowd)]
            p2 = population[tournament(rng, rank, crowd)]

            # Uniform crossover over route-selection bits is usually
            # infeasible and requires an expensive exact-cover repair.
            # Instead, use feasibility-preserving 2-route exchanges. The
            # NSGA-II ranking/crowding selection remains unchanged.
            c1 = diversify_feasible(
                pool,
                p1,
                rng,
                subset_index,
                exchanges=1 + int(rng.integers(0, 3)),
            )
            c2 = diversify_feasible(
                pool,
                p2,
                rng,
                subset_index,
                exchanges=1 + int(rng.integers(0, 3)),
            )
            if np.array_equal(c1, p1):
                variation_failures += 1
            if np.array_equal(c2, p2):
                variation_failures += 1

            offspring.append(c1)
            if len(offspring) < population_size:
                offspring.append(c2)

        combined = deduplicate(population + offspring)
        combined_obj = [evaluate(pool, x, scenario, metric) for x in combined]
        fronts = fast_non_dominated_sort(combined_obj)

        new_population = []
        for front in fronts:
            if len(new_population) + len(front) <= population_size:
                new_population.extend(combined[i] for i in front)
            else:
                cd = crowding_distance(front, combined_obj)
                ordered = sorted(front, key=lambda i: cd[i], reverse=True)
                remaining = population_size - len(new_population)
                new_population.extend(combined[i] for i in ordered[:remaining])
                break

        while len(new_population) < population_size:
            new_population.append(new_population[rng.integers(0, len(new_population))].copy())
        population = new_population

    objectives = [evaluate(pool, x, scenario, metric) for x in population]
    fronts = fast_non_dominated_sort(objectives)
    pareto = fronts[0] if fronts else []

    return NSGA2Result(
        population=population,
        objectives=objectives,
        pareto_indices=pareto,
        generations=generations,
        seed=seed,
        repair_failures=repair_failures,
        variation_failures=variation_failures,
    )
