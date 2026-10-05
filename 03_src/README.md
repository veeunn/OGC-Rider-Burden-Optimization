# 03_src

Core research implementation for the rider-burden optimization study.

## Modules

- `data_loader.py` — load OGC problem instances
- `route_evaluator.py` — route timing and burden evaluation
- `burden_metrics.py` — rider-level burden and inequality metrics
- `candidate_pool.py` — BIKE candidate-route generation
- `set_partition.py` — fixed-workforce exact-cover optimization
- `nsga2_solver.py` — multi-objective NSGA-II search
- `workforce.py` — S0-derived fixed-workforce manifest handling
- `result_exporter.py` — result export helpers
- `memory_safe_bundling.py` — memory-aware bundle generation support
- `scalable_split_solver.py` — scalability/extension solver support

Command-line runners are under `scripts/runners/`.

## Design rule

S0-S3 use the same feasibility logic and candidate-route structure. S1, S2, and S3 differ only in the rider-burden equity objective being evaluated.

The frozen manuscript numbers are not stored here; their source of truth is `05_results/frozen_stage1_16/`.
