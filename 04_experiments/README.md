# 04_experiments

Scenario definitions and fixed-workforce experiment policy.

Executable command-line runners are maintained separately under `scripts/runners/`.

## Scenarios

### S0 — Cost-only baseline
Minimize OGC delivery cost and save the active BIKE rider count as `R0`.

### S1 — Order Count
Minimize delivery cost and inequality in rider Order Count.

### S2 — Active Route Duration
Minimize delivery cost and inequality in Active Route Duration, defined as travel + service time excluding waiting time.

### S3 — Waiting Time
Minimize delivery cost and inequality in pickup-location waiting time before assigned orders are ready.

## Fixed-workforce rule

S1-S3 inherit exactly the S0-derived `R0`. Equity improvements therefore come from reassignment rather than increasing the number of active riders.

The three burden dimensions are analyzed separately; no composite rider-burden score is used.

See `WORKFORCE_POLICY.md` and `07_report/02_objective_functions_and_constraints.md` for the formal design.
