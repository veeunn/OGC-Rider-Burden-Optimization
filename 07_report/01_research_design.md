# Research Design

## Research question

Does a cost-minimizing last-mile delivery allocation concentrate operational burden on particular riders, and what additional cost is required to improve rider-burden equity?

## Scope

- Dataset: OGC 2024 food-delivery instances
- Transport mode: BIKE only
- Optimization framework: NSGA-II for multi-objective scenarios
- Baseline: cost-minimizing BIKE-only allocation
- Burden dimensions are analyzed separately
- Workforce size is fixed across S1-S3 using the S0 baseline

## Scenario structure

| Scenario | Objective 1 | Objective 2 | Active rider count |
|---|---|---|---:|
| S0 | Delivery cost | — | Determines \(R_0\) |
| S1 | Delivery cost | Order Count inequality | \(R_0\) fixed |
| S2 | Delivery cost | Active Route Duration inequality | \(R_0\) fixed |
| S3 | Delivery cost | Waiting Time inequality | \(R_0\) fixed |

## Workforce policy

The original OGC instances were designed for a mixed fleet. Because this study removes WALK and CAR, the original BIKE availability is not treated as the study workforce size.

For S0, BIKE availability is made non-binding by setting the upper bound to the number of orders \(K\). The cost-minimizing BIKE-only solution then determines the number of active riders:

\[
R_0 = \text{number of selected BIKE bundles in S0}.
\]

For S1-S3, the number of selected BIKE bundles is fixed exactly at \(R_0\):

\[
\sum_b x_b = R_0.
\]

Therefore, differences between S0 and S1-S3 reflect reallocation of orders/routes among the same number of active riders, not workforce expansion or contraction.

## Burden definitions

### Order Count
Number of orders assigned to an active rider.

### Active Route Duration
Travel time plus service time, excluding waiting time.

### Waiting Time
Idle time incurred at pickup locations before assigned orders become ready.

## Current methodological decisions

1. No composite burden score is used.
2. S1, S2, and S3 are analyzed separately.
3. S0 determines the baseline active workforce \(R_0\).
4. S1-S3 use exactly the same active rider count \(R_0\).
5. Equity is calculated across the \(R_0\) active riders only.
