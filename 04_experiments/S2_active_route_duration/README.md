# S2 — Active Route Duration equity

Objectives:

1. minimize OGC average delivery cost;
2. minimize inequality in Active Route Duration.

Active Route Duration is travel time + service time, excluding waiting time. The route-clock implementation has been verified and is used in the frozen primary analysis.

The active-rider count is fixed to the S0-derived `R0`.

Implemented through `scripts/runners/run_equity.py --scenario S2`.
