# 02_baseline

This directory is reserved for the **original OGC baseline implementation** supplied with the project.

## Rule

The original baseline should be preserved as faithfully as possible and separated from all research modifications.

Research code belongs in `03_src/`.

## Verification checklist

Before using the baseline as S0, verify from the supplied code:

1. how a solution is represented,
2. how route feasibility is checked,
3. how rider capacity is enforced,
4. how ready times and deadlines are evaluated,
5. how pickup/delivery sequencing is handled,
6. how delivery cost is calculated,
7. how average delivery cost is reported,
8. how the baseline search heuristic constructs and improves bundles.

The verified implementation details will be copied into `07_report/02_objective_functions_and_constraints.md`.
