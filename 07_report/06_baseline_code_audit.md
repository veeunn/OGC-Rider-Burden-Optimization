# Baseline code audit

This note records what was verified directly from the supplied `util.py`, `myalgorithm.py`, and `Yong_alg_test.py`.

## Exact cost implementation

`Rider.calculate_cost(dist)` returns:

```python
fixed_cost + dist / 100.0 * var_cost
```

`Bundle.update_cost()` applies this to the bundle's total route distance.

The reported baseline objective is:

```python
sum(bundle.cost for bundle in bundles) / K
```

## Exact route distance

The original `get_total_distance()` sums:

1. pickup-to-pickup arcs,
2. last pickup to first delivery,
3. delivery-to-delivery arcs.

There is no depot or pre-route arc.

## Exact route clock

The original `get_pd_times()`:

1. initializes time at the **first pickup's ready time**;
2. does not count travel to the first pickup;
3. for later pickups uses `max(previous_time + rider.T, next_ready_time)`;
4. after the last pickup, visits deliveries continuously using `rider.T`;
5. defines `rider.T = round(DIST / speed + service_time)`.

This is now reproduced in `03_src/route_evaluator.py`, which additionally separates active travel/service time from pickup waiting time.

## Final baseline optimization model

The supplied `myalgorithm.py` creates candidate bundles and then solves a binary set-partitioning model with Gurobi.

Decision variable:
- one binary variable per candidate bundle.

Objective:
- minimize total selected bundle cost.

Constraints:
- each order is covered exactly once;
- selected bundles of each rider type do not exceed that type's availability.

Because K is fixed, minimizing total selected cost is equivalent to minimizing average delivery cost.

## Reproducibility patch

The supplied `util.py` defines:

```python
get_pd_times(all_orders, rider, shop_seq, dlv_seq)
```

but two downstream calls in `solution_check()` / plotting pass `rider.T` instead of the rider object.

The original file is preserved unchanged in `02_baseline/original/`.

The runnable copy in `02_baseline/runnable/util.py` changes only those call sites to pass `rider`, so that the function matches its own definition and the algorithm's other uses.

No optimization logic is changed by this patch.

## Gurobi

The final set-partitioning step requires `gurobipy` and a valid Gurobi license. CI therefore performs syntax and data checks but does not execute the full optimizer.
