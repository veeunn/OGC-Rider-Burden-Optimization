# 08. Main-study scope decision: Stage 1 S0-S3

## Decision

The current paper will use the **18 OGC Stage 1 problem instances** as its empirical basis.

Stage 2 and Stage 3 data remain in the repository for reproducibility and possible future scalability work, but they are **outside the current main study**.

## Research design retained

The substantive design does not change:

- **S0:** minimize delivery cost.
- **S1:** minimize cost and inequality in rider Order Count.
- **S2:** minimize cost and inequality in Active Route Duration.
- **S3:** minimize cost and inequality in Waiting Time.
- **R0:** number of active BIKE riders selected by S0.
- **Fixed workforce:** S1-S3 must use exactly R0 active riders.
- **Primary equity measure:** Gini coefficient.
- **Trade-off outputs:** Pareto frontier, knee point, equity improvement, and Price of Fairness.

Price of Fairness is

```text
PoF (%) = (Cost_fair - Cost_S0) / Cost_S0 * 100
```

Equity improvement within each burden dimension is

```text
Equity improvement (%) = (Gini_S0 - Gini_fair) / Gini_S0 * 100
```

The three burden dimensions are **not combined into a composite index**.

## Why Stage 1 is sufficient for the current paper

The goal is not to develop a new large-scale vehicle-routing algorithm. The goal is to quantify the **cost-equity trade-off** produced by introducing rider-burden equity into an OGC-based delivery allocation problem.

Using 18 Stage 1 instances permits repeated, instance-level comparison of S0-S3 while keeping the same verified OGC feasibility, timing, cost, and BIKE-only scope.

## Stage 2/3 status

The repository contains Stage 2/3 split data, reconstruction utilities, and experimental scalability prototypes. Those components document why the original exhaustive candidate-generation engine does not scale directly to K=500-2000. They should be treated as future-extension material, not as required evidence for the current Stage 1 paper.

## Execution plan

The main study proceeds in four computational phases:

1. **Pilot smoke test** — representative Stage 1 instances with very small NSGA-II settings.
2. **All-instance smoke test** — all 18 Stage 1 instances, still using small settings, to confirm feasibility and pipeline stability.
3. **Parameter/seed stability** — larger populations/generations and repeated seeds on selected representative instances.
4. **Final experiment** — frozen settings, all 18 instances, repeated seeds, followed by aggregate Pareto/Gini/PoF reporting.

Small smoke-test settings are never interpreted as final empirical results.
