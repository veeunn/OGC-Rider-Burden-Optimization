# Primary Stage 1 analysis sample lock

## Decision

The primary empirical analysis is fixed at 16 OGC Stage 1 instances:

STAGE1_1, STAGE1_2, STAGE1_3, STAGE1_4, STAGE1_5, STAGE1_7, STAGE1_8, STAGE1_9, STAGE1_10, STAGE1_11, STAGE1_13, STAGE1_14, STAGE1_15, STAGE1_16, STAGE1_17, and STAGE1_18.

STAGE1_6 and STAGE1_12 are excluded from the primary result set because the common exhaustive candidate-generation pipeline did not complete within the computational rescue window. Their S1-S3 equity outcomes were not observed before this primary-sample decision.

## Analysis policy

- S0 is the cost-only BIKE baseline.
- S1, S2, and S3 use the same candidate route universe and exactly the S0-derived active rider count R0.
- Final NSGA-II settings are population = 80, generations = 100, seeds = 0-4.
- Gini is the primary inequality objective.
- Main outputs are pooled Pareto frontiers, pooled-knee equity improvement, lowest-Gini improvement, and Price of Fairness.
- Across-instance mean and standard deviation are descriptive summaries, not population-level inferential estimates.

## Treatment of STAGE1_6 and STAGE1_12

These instances remain computational extension cases. Any later successful runs will be reported as robustness or scalability evidence and will not retroactively redefine the locked 16-instance primary analysis.

## Rationale

Fixing the sample before observing the unresolved instances' equity outcomes prevents outcome-dependent inclusion or exclusion.
