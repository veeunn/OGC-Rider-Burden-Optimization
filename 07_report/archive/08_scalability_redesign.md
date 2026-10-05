# 08. Scalability redesign for Stage 2 and Stage 3

## Why the current engine cannot simply be scaled up

The original OGC-derived bundle generator constructs full third-order arrays during size-3 bundle generation:

```python
i, j, k = np.indices((K, K, K))
```

This is practical for the small K=50 smoke instance but not for the competition-scale instances used in this study.

Observed problem sizes:

| Stage | Instances | K |
|---|---:|---:|
| Stage 1 | 18 | small benchmark scale |
| Stage 2 | 1, 3, 5 | 500 |
| Stage 2 | 2, 4, 6 | 1000 |
| Stage 3 | 1-3 | 2000 |

For K=500, one float64 K^3 array contains 125,000,000 elements, approximately 1 GB. The original implementation holds several K^3 arrays simultaneously. Two independent GitHub Actions runs on STAGE2_1 were terminated by the hosted runner during S0 candidate generation before the MILP time limit was reached.

Data restoration and validation succeeded in both runs, so the failure is computational rather than a split-file or SHA-256 problem.

## Memory-safe size 1-3 refactor

`03_src/memory_safe_bundling.py` implements an alternative generator that:

1. preserves the original size-1 and size-2 calculations;
2. identifies feasible-pair triangles without allocating K^3 index tensors;
3. evaluates triplets in bounded batches;
4. preserves the baseline route feasibility rules and first-minimum tie-breaking order.

The implementation is intentionally separate from the production candidate pool until equivalence is established.

### Exact small-instance equivalence checks

`scripts/compare_bundling_implementations.py` compares the ordered candidate signatures
`(shop_seq, dlv_seq, total_dist)` produced by the original tensor implementation and the memory-safe implementation.

Results:

| Instance | Size 1 | Size 2 | Size 3 | Feasible-triplet set |
|---|---:|---:|---:|---:|
| TEST_K50_1 | exact match (50) | exact match (362) | exact match (380) | exact match |
| TEST_K50_2 | exact match (50) | exact match (254) | exact match (180) | exact match |

Thus, for the verified small instances, the memory-safe refactor changes implementation only, not the candidate routes.

## A deeper scalability issue: candidate count

Removing K^3 tensors is necessary but not sufficient.

For STAGE2_1 (K=500), a direct diagnostic found:

- feasible unordered BIKE pairs: **61,172**;
- pair-feasible triangles: **4,115,657**;
- fully route-feasible BIKE triplets: **2,176,589**.

Therefore, an exhaustive route-column pool would contain more than two million size-3 candidates before size-4 routes are considered. A set-partition model with millions of binary route variables is unsuitable as the repeated repair operator inside NSGA-II, especially because the current NSGA-II calls an exact-cover MILP for many offspring.

This means the large-instance limitation is structural, not only a memory bug.

## Size-4 sensitivity on the two K=50 tests

As a diagnostic only, S0 was solved with maximum bundle size 3 and then with maximum bundle size 4.

| Instance | max size 3 S0 | max size 4 S0 | Cost gap | R0 (size 3 / size 4) |
|---|---:|---:|---:|---:|
| TEST_K50_1 | 3316.892 | 3285.584 | +0.953% | 20 / 20 |
| TEST_K50_2 | 3658.660 | 3658.660 | 0.000% | 22 / 22 |

This is useful evidence that omitting size-4 routes may have a modest effect on these two small instances, but it is **not sufficient evidence** to make max bundle size 3 the final research design for Stage 2/3.

## Recommended production redesign

The production solver should move away from exhaustive route-column enumeration plus MILP repair for K=500-2000.

A more scalable architecture is:

1. **Permutation / giant-tour representation** of orders.
2. **Split/decoder step** that partitions a permutation into feasible rider routes.
3. Route feasibility and cost still use the verified OGC clock, capacity, deadline, distance, and cost formulas.
4. **S0**: cost-only evolutionary search; its best solution determines R0.
5. **S1-S3**: keep R0 fixed and use a multi-objective evolutionary search over route memberships/orderings.
6. The three burden dimensions remain separate:
   - S1: order count;
   - S2: active route duration;
   - S3: waiting time.
7. Gini remains the primary inequality measure; PoF is still computed against S0.

This preserves the substantive research design (cost-equity trade-off under a fixed workforce) while replacing the non-scalable representation/repair mechanism.

## Literature basis for the redesign

Giant-tour representations combined with Split decoders are a standard vehicle-routing metaheuristic architecture. Split converts a customer permutation into a set of routes, commonly through dynamic programming / shortest-path logic, and is widely used inside modern genetic-search frameworks. Vidal et al. develop unified hybrid genetic-search frameworks for multi-attribute VRPs, and subsequent work continues to combine evolutionary search with Split-type decoding for large routing problems.

For the equity side, Matl, Hartl, and Vidal (2019) explicitly study bi-objective vehicle-routing trade-offs between transportation cost and alternative workload-equity resources. Their results also support keeping workload resources separate rather than assuming that a solution balanced under one resource is balanced under another.

## Validation plan for the new engine

Before Stage 2/3 results are accepted:

1. reproduce the current K=50 S0 solution closely or exactly where the same route space is used;
2. verify every decoded route with the original OGC feasibility checker;
3. confirm cost calculations against the supplied evaluator;
4. verify fixed-R0 enforcement in S1-S3;
5. compare the new and existing engines on TEST_K50_1 and TEST_K50_2;
6. only then run STAGE2_1 as the first large-instance pilot.

The current Stage 2/3 workflow should therefore be treated as a pipeline/data-restoration test, not yet as the final computational engine.
