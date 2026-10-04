# 03_src

Research implementation for the rider-burden study.

Planned modules:

- `data_loader.py` — load OGC problem instances
- `route_evaluator.py` — reproduce the original OGC feasibility and cost logic
- `burden_metrics.py` — calculate rider-level burden and inequality metrics
- `nsga2_solver.py` — multi-objective optimization
- `result_exporter.py` — export raw solutions, summaries, and metadata

## Design rule

All S0-S3 scenarios must use the **same feasibility logic**.

Only the second objective changes between S1, S2, and S3.
