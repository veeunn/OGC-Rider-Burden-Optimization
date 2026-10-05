# 02_baseline

Preserved OGC baseline implementation and the minimally adjusted runnable copy used for verification.

## Layout

- `original/` — supplied baseline files preserved for provenance
- `runnable/` — runnable copy used by the research workflow
- `runnable/myalgorithm_scipy.py` — license-free SciPy MILP backend

Research-specific optimization logic belongs in `03_src/`; command-line entry points belong in `scripts/runners/`.

## Baseline verification

The project verified solution representation, route feasibility, capacity, ready times and deadlines, pickup/delivery sequencing, delivery cost, average cost, and bundle construction logic.

The verified mathematical formulation and constraints are documented in:

- `07_report/02_objective_functions_and_constraints.md`
- `07_report/05_baseline_verification_status.md`
- `07_report/06_baseline_code_audit.md`

The original baseline is not overwritten by the research modifications.
