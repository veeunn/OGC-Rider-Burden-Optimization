# Research Design

## Research question

Does a cost-minimizing last-mile delivery allocation concentrate operational burden on particular riders, and what additional cost is required to improve rider-burden equity?

## Scope

- Dataset: OGC 2024 food-delivery instances
- Transport mode: BIKE only
- Optimization framework: NSGA-II for multi-objective scenarios
- Baseline: original cost-minimizing OGC formulation
- Burden dimensions are analyzed separately

## Scenario structure

| Scenario | Objective 1 | Objective 2 |
|---|---|---|
| S0 | Delivery cost | — |
| S1 | Delivery cost | Order Count inequality |
| S2 | Delivery cost | Active Route Duration inequality |
| S3 | Delivery cost | Waiting Time inequality |

## Burden definitions

### Order Count
Number of orders assigned to a rider.

### Active Route Duration
Travel time plus service time, excluding waiting time.

### Waiting Time
Idle time incurred at pickup locations before assigned orders become ready.

## Current methodological decision

No composite burden score is used at this stage. The three dimensions remain separate so that their distinct cost–equity trade-offs can be observed directly.
