"""Generate the BIKE-only candidate route pool used by S0-S3.

This reproduces the supplied baseline's active candidate-generation logic:
- all feasible bundles of size 1-3 from bundling_123();
- feasible size-4 BIKE bundles obtained by merging a size-3 bundle and a
  disjoint singleton using the baseline triplet-screening logic;
- size-5 generation remains excluded because it is commented out in the
  supplied baseline algorithm.

The resulting pool is serialized so S0 and S1-S3 use exactly the same route set.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
import time
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "02_baseline" / "runnable"
if str(BASELINE) not in sys.path:
    sys.path.insert(0, str(BASELINE))

from util import Order, Rider
from myalgorithm_scipy import bundling_123, try_merging_bundles


@dataclass(frozen=True)
class CandidateBundle:
    candidate_id: int
    shop_seq: list[int]
    dlv_seq: list[int]
    total_volume: float
    total_dist: float
    cost: float
    order_count: int
    active_route_duration_sec: float
    waiting_time_sec: float


def _timeline_metrics(all_orders, rider, shop_seq, dlv_seq) -> tuple[float, float]:
    """Return (active duration, waiting) using the verified baseline clock."""
    K = len(all_orders)
    k = shop_seq[0]
    t = float(all_orders[k].ready_time)
    active = 0.0
    waiting = 0.0

    for next_k in shop_seq[1:]:
        transition = float(rider.T[k, next_k])
        active += transition
        arrival = t + transition
        wait = max(0.0, float(all_orders[next_k].ready_time) - arrival)
        waiting += wait
        t = max(arrival, float(all_orders[next_k].ready_time))
        k = next_k

    first_d = dlv_seq[0]
    transition = float(rider.T[shop_seq[-1], first_d + K])
    active += transition
    t += transition
    k = first_d

    for next_k in dlv_seq[1:]:
        transition = float(rider.T[k + K, next_k + K])
        active += transition
        t += transition
        k = next_k

    return active, waiting


def load_problem(problem_path: str | Path):
    problem_path = Path(problem_path)
    with problem_path.open("r", encoding="utf-8") as f:
        prob = json.load(f)
    K = int(prob["K"])
    all_orders = [Order(x) for x in prob["ORDERS"]]
    bike_info = next((x for x in prob["RIDERS"] if x[0] == "BIKE"), None)
    if bike_info is None:
        raise ValueError("Problem has no BIKE rider type.")
    bike = Rider(list(bike_info))
    dist = np.asarray(prob["DIST"])
    bike.T = np.round(dist / bike.speed + bike.service_time)
    return prob, K, all_orders, bike, dist


def generate_bike_candidate_pool(
    problem_path: str | Path,
    *,
    include_size4: bool = True,
    generation_time_limit: float | None = None,
) -> dict:
    prob, K, all_orders, bike, dist = load_problem(problem_path)
    ready = np.asarray([o.ready_time for o in all_orders])
    deadline = np.asarray([o.deadline for o in all_orders])
    volume = np.asarray([o.volume for o in all_orders])

    started = time.time()
    best, feasible_triplets_by_rider = bundling_123(
        K, all_orders, [bike], ready, deadline, volume, dist
    )

    bundles = []
    bundles.extend(best[0]["BIKE"])
    bundles.extend(best[1]["BIKE"])
    bundles.extend(best[2]["BIKE"])

    n_size4 = 0
    if include_size4:
        singles = best[0]["BIKE"]
        triples = best[2]["BIKE"]
        triplet_set = feasible_triplets_by_rider["BIKE"]

        def triplet_screen(i, j, k, l):
            return (
                frozenset([i, j, l]) in triplet_set
                and frozenset([i, k, l]) in triplet_set
                and frozenset([j, k, l]) in triplet_set
            )

        for b3 in triples:
            if generation_time_limit is not None and time.time() - started >= generation_time_limit:
                break
            sorted_seq = sorted(b3.shop_seq)
            for b1 in singles:
                if generation_time_limit is not None and time.time() - started >= generation_time_limit:
                    break
                order_id = b1.shop_seq[0]
                if b1.total_volume + b3.total_volume > bike.capa:
                    continue
                # Same non-overlap / canonical-order condition as the supplied baseline.
                if order_id <= sorted_seq[2]:
                    continue
                if not triplet_screen(sorted_seq[0], sorted_seq[1], sorted_seq[2], order_id):
                    continue
                merged = try_merging_bundles(K, dist, all_orders, b1, b3)
                if merged is not None:
                    bundles.append(merged)
                    n_size4 += 1

    # De-duplicate identical route candidates while preserving deterministic order.
    unique = {}
    for b in bundles:
        key = (tuple(b.shop_seq), tuple(b.dlv_seq))
        if key not in unique:
            unique[key] = b

    records = []
    counts = {}
    for cid, b in enumerate(unique.values()):
        active, waiting = _timeline_metrics(all_orders, bike, b.shop_seq, b.dlv_seq)
        m = len(b.shop_seq)
        counts[m] = counts.get(m, 0) + 1
        records.append(asdict(CandidateBundle(
            candidate_id=cid,
            shop_seq=list(map(int, b.shop_seq)),
            dlv_seq=list(map(int, b.dlv_seq)),
            total_volume=float(b.total_volume),
            total_dist=float(b.total_dist),
            cost=float(b.cost),
            order_count=m,
            active_route_duration_sec=float(active),
            waiting_time_sec=float(waiting),
        )))

    return {
        "problem": prob.get("name", Path(problem_path).stem),
        "problem_file": str(problem_path),
        "K": K,
        "rider_type": "BIKE",
        "original_bike_availability": int(bike.available_number),
        "pool_generation_sec": time.time() - started,
        "include_size4": include_size4,
        "generation_time_limit_sec": generation_time_limit,
        "candidate_counts_by_bundle_size": {str(k): v for k, v in sorted(counts.items())},
        "n_candidates": len(records),
        "candidates": records,
    }


def save_candidate_pool(pool: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def load_candidate_pool(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
