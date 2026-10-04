"""NSGA-II over feasible bundle selections with S0-fixed workforce.

Representation
--------------
A chromosome is a binary vector over a shared BIKE candidate bundle pool.
Every evaluated individual is repaired by an exact-cover MILP so that:

1. every order is covered exactly once; and
2. exactly R0 bundles / active riders are selected.

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

    def safe_repair(target: np.ndarray, fallback: np.ndarray | None = None) -> np.ndarray:
        nonlocal repair_failures
        try:
            return repair(pool, target, r0, rng, repair_time_limit)
        except RuntimeError as exc:
            # A HiGHS time limit with no primal solution should not terminate a
            # smoke run.  Preserve a known feasible parent/seed and record the
            # event so final experiments can reject under-explored settings.
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

    # Diversify around S0 first.  Large candidate pools can make a global
    # random exact-cover repair expensive, so failed repairs fall back to S0
    # rather than aborting the whole scenario.
    base_seed = population[0].copy()
    attempts = 0
    max_attempts = max(population_size * 2, 8)
    while len(population) < population_size and attempts < max_attempts:
        attempts += 1
        raw = base_seed.copy()
        flip_probability = min(0.02, max(2.0 / max(n, 1), 0.001))
        flips = rng.random(n) < flip_probability
        raw[flips] = 1 - raw[flips]
        population.append(safe_repair(raw, fallback=base_seed))
        population = deduplicate(population)

    # A smoke test is allowed to continue with duplicate feasible seeds.  The
    # repair_failures diagnostic tells us whether the settings are adequate
    # for a final experiment.
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
            c1, c2 = crossover(rng, p1, p2, crossover_probability)
            c1 = mutate(rng, c1, mutation_probability)
            c2 = mutate(rng, c2, mutation_probability)
            offspring.append(safe_repair(c1, fallback=p1))
            if len(offspring) < population_size:
                offspring.append(safe_repair(c2, fallback=p2))

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
    )
