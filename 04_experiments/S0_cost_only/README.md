# S0 — Cost-only baseline

Objective:

```text
minimize delivery cost
```

S0 uses the BIKE candidate-route pool shared with S1-S3 and saves the selected active-rider count as `R0`.

The implemented runner is:

`scripts/runners/run_s0.py`

For the frozen primary analysis, 12 S0 instances were solver-proven optimal and four reached the time limit with feasible incumbents. The final baseline policy and corrections are documented in `05_results/frozen_stage1_16/qa_report.md`.
