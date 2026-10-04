"""Memory-safe BIKE bundle generation for bundle sizes 1-3.

This module preserves the baseline route semantics without allocating K x K x K
NumPy tensors. Pair candidates are generated with K x K arrays. Triplet
candidates are generated from feasible-pair triangles and evaluated in batches.

It is intentionally separate from candidate_pool.py until equivalence against
the original tensor implementation is verified on small instances.
"""
from __future__ import annotations

from itertools import permutations
import time

import numpy as np

from util import Bundle, get_total_distance


SHOP_PERMS = np.asarray(list(permutations(range(3))), dtype=np.int8)
# Matches the original bundled-tensor delivery-axis lookup order.
DLV_PERMS = np.asarray(
    [
        (1, 2, 0),
        (1, 0, 2),
        (2, 1, 0),
        (2, 0, 1),
        (0, 1, 2),
        (0, 2, 1),
    ],
    dtype=np.int8,
)


def _generate_singles_pairs(K, all_orders, rider, ready, deadline, volume, dist):
    capa = rider.capa
    pickup = rider.T[:K, :K]
    delivery = rider.T[K:, K:]
    pdp = rider.T[:K, K:]

    # Singles: exact baseline logic.
    single_dist = np.diag(pdp)
    single_ok = (ready + single_dist <= deadline) & (volume <= capa)
    singles = [
        Bundle(
            all_orders,
            rider,
            [int(i)],
            [int(i)],
            float(volume[i]),
            float(dist[i, i + K]),
        )
        for i in np.flatnonzero(single_ok)
    ]

    # Pairs: exact same four route-pattern comparison as the baseline.
    cap_ok = capa >= (volume[:, None] + volume[None, :])
    pdp_t = pdp.T
    pdp_same = np.broadcast_to(np.diag(pdp)[:, None], pdp.shape).T

    different_distance = pickup + pdp_t + delivery
    same_distance = pickup + pdp_same + delivery

    ready_matrix = np.tile(ready, (K, 1))
    deadline_matrix = np.tile(deadline, (K, 1))
    start_time_1 = ready_matrix.T + pickup

    start_time_2 = np.maximum(start_time_1 + pdp_t, ready_matrix + pdp_t)
    start_time_2_2 = np.maximum(start_time_1 + pdp_same, ready_matrix + pdp_same)
    end_time_1 = start_time_2 + delivery
    end_time_1_2 = start_time_2_2 + delivery

    time_ok_1 = (start_time_2 <= deadline_matrix.T) & (end_time_1 <= deadline_matrix)
    time_ok_2 = (start_time_2_2 <= deadline_matrix) & (end_time_1_2 <= deadline_matrix.T)

    d1 = np.where(cap_ok & time_ok_1, different_distance, np.inf)
    d2 = np.where(cap_ok & time_ok_2, same_distance, np.inf)
    np.fill_diagonal(d1, np.inf)
    np.fill_diagonal(d2, np.inf)

    stacked = np.stack((d1, d2, d1.T, d2.T), axis=2)
    iu = np.triu_indices(K, 1)
    best_index = np.argmin(stacked[iu], axis=1)

    pairs = []
    feasible_pairs = set()
    adjacency = np.zeros((K, K), dtype=bool)

    for pos, (i, j) in enumerate(zip(*iu)):
        if np.all(np.isinf(stacked[i, j])):
            continue
        which = int(best_index[pos])
        if which == 0:
            shop_seq, dlv_seq = [int(i), int(j)], [int(i), int(j)]
        elif which == 1:
            shop_seq, dlv_seq = [int(i), int(j)], [int(j), int(i)]
        elif which == 2:
            shop_seq, dlv_seq = [int(j), int(i)], [int(j), int(i)]
        else:
            shop_seq, dlv_seq = [int(j), int(i)], [int(i), int(j)]

        b = Bundle(
            all_orders,
            rider,
            shop_seq,
            dlv_seq,
            float(volume[i] + volume[j]),
            float(get_total_distance(K, dist, shop_seq, dlv_seq)),
        )
        pairs.append(b)
        feasible_pairs.add(frozenset((int(i), int(j))))
        adjacency[i, j] = adjacency[j, i] = True

    return singles, pairs, feasible_pairs, adjacency


def _iter_pair_triangles(adjacency, batch_size):
    """Yield arrays of i<j<k where all three unordered pairs are feasible."""
    K = adjacency.shape[0]
    pending = []
    pending_n = 0

    for i in range(K - 2):
        nbr = np.flatnonzero(adjacency[i, i + 1 :]) + i + 1
        if nbr.size < 2:
            continue
        sub = adjacency[np.ix_(nbr, nbr)]
        a, b = np.where(np.triu(sub, 1))
        if a.size == 0:
            continue
        tri = np.column_stack(
            (
                np.full(a.size, i, dtype=np.int32),
                nbr[a].astype(np.int32, copy=False),
                nbr[b].astype(np.int32, copy=False),
            )
        )
        pending.append(tri)
        pending_n += len(tri)

        if pending_n >= batch_size:
            yield np.vstack(pending)
            pending = []
            pending_n = 0

    if pending:
        yield np.vstack(pending)


def _evaluate_triplet_batch(
    K,
    all_orders,
    rider,
    ready,
    deadline,
    volume,
    dist,
    triangles,
):
    """Return the baseline-best feasible Bundle for each unordered triplet."""
    tri = np.asarray(triangles, dtype=np.int32)
    n = len(tri)
    if n == 0:
        return []

    cap_ok = volume[tri].sum(axis=1) <= rider.capa
    best_dist = np.full(n, np.inf, dtype=float)
    best_shop = np.full(n, -1, dtype=np.int8)
    best_dlv = np.full(n, -1, dtype=np.int8)

    T = rider.T

    # Same pickup-permutation order as the baseline's distances list.
    # Same delivery-axis order as dlv_seq_lookup in the baseline.
    for s_idx, sp in enumerate(SHOP_PERMS):
        p1 = tri[:, sp[0]]
        p2 = tri[:, sp[1]]
        p3 = tri[:, sp[2]]

        t1 = ready[p1]
        t2 = np.maximum(t1 + T[p1, p2], ready[p2])
        t3 = np.maximum(t2 + T[p2, p3], ready[p3])

        for d_idx, dp in enumerate(DLV_PERMS):
            q1 = tri[:, sp[dp[0]]]
            q2 = tri[:, sp[dp[1]]]
            q3 = tri[:, sp[dp[2]]]

            td1 = t3 + T[p3, q1 + K]
            td2 = td1 + T[q1 + K, q2 + K]
            td3 = td2 + T[q2 + K, q3 + K]

            feasible = (
                cap_ok
                & (td1 <= deadline[q1])
                & (td2 <= deadline[q2])
                & (td3 <= deadline[q3])
            )
            if not np.any(feasible):
                continue

            route_dist = (
                dist[p1, p2]
                + dist[p2, p3]
                + dist[p3, q1 + K]
                + dist[q1 + K, q2 + K]
                + dist[q2 + K, q3 + K]
            )

            # Strictly-less preserves the original first-minimum tie breaking.
            improve = feasible & (route_dist < best_dist)
            best_dist[improve] = route_dist[improve]
            best_shop[improve] = s_idx
            best_dlv[improve] = d_idx

    good = np.flatnonzero(np.isfinite(best_dist))
    bundles = []
    for row in good:
        base = tri[row]
        sp = SHOP_PERMS[int(best_shop[row])]
        dp = DLV_PERMS[int(best_dlv[row])]
        shop = [int(base[x]) for x in sp]
        dlv = [int(base[sp[x]]) for x in dp]
        bundles.append(
            Bundle(
                all_orders,
                rider,
                shop,
                dlv,
                float(volume[base].sum()),
                float(best_dist[row]),
            )
        )
    return bundles


def bundling_123_bike_memory_safe(
    K,
    all_orders,
    rider,
    ready,
    deadline,
    volume,
    dist,
    *,
    batch_size=100_000,
):
    """Generate BIKE bundle sizes 1-3 without K^3 tensor allocation."""
    started = time.time()

    singles, pairs, feasible_pairs, adjacency = _generate_singles_pairs(
        K, all_orders, rider, ready, deadline, volume, dist
    )

    triples = []
    feasible_triplets = set()
    raw_pair_triangles = 0

    for batch in _iter_pair_triangles(adjacency, batch_size):
        raw_pair_triangles += len(batch)
        batch_bundles = _evaluate_triplet_batch(
            K,
            all_orders,
            rider,
            ready,
            deadline,
            volume,
            dist,
            batch,
        )
        triples.extend(batch_bundles)
        feasible_triplets.update(frozenset(b.shop_seq) for b in batch_bundles)

    diagnostics = {
        "raw_pair_triangles": int(raw_pair_triangles),
        "feasible_triplets": int(len(triples)),
        "elapsed_sec": float(time.time() - started),
    }

    best = {
        0: {"BIKE": singles},
        1: {"BIKE": pairs},
        2: {"BIKE": triples},
    }
    return best, {"BIKE": feasible_triplets}, diagnostics
