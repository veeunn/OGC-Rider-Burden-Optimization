# 04_experiments

Experiment definitions and run scripts.

## Scenarios

### S0 — Cost-only baseline
Minimize OGC delivery cost with the original feasibility rules.

### S1 — Order Count
Two-objective optimization:
1. minimize delivery cost,
2. minimize inequality in rider Order Count.

### S2 — Active Route Duration
Two-objective optimization:
1. minimize delivery cost,
2. minimize inequality in Active Route Duration.

Active Route Duration is defined as **travel + service time, excluding waiting time**.

### S3 — Waiting Time
Two-objective optimization:
1. minimize delivery cost,
2. minimize inequality in Waiting Time.

Waiting Time is the idle time at pickup locations before an assigned order is ready.

## Important

The three burden dimensions are currently analyzed **separately**.
No composite rider-burden score is used.
