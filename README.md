# OGC Rider Burden Optimization

Multi-objective last-mile delivery optimization research based on the **Optimization Grand Challenge 2024 (OGC 2024)** food-delivery problem.

## Research goal

This project studies whether a cost-minimizing delivery allocation can concentrate operational burden on particular riders, and how much additional delivery cost is required to improve burden equity.

The current study design uses **BIKE riders only** to control for transport-mode heterogeneity and evaluates three burden dimensions separately:

- **S1 — Order Count:** number of orders assigned to each rider
- **S2 — Active Route Duration:** travel and service time, excluding waiting time
- **S3 — Waiting Time:** idle time at pickup locations before orders are ready

A cost-only solution is retained as the **S0 baseline**. Each burden scenario will be compared against S0 using a cost–equity Pareto analysis with NSGA-II.

> Current rule: **do not combine the three burden measures into a composite index.** S1, S2, and S3 are analyzed independently.

## Repository map

```text
.
├── 01_data/                  # OGC problem instances and data notes
├── 02_baseline/              # Original OGC baseline code (preserved)
├── 03_src/                   # Research implementation
├── 04_experiments/           # S0-S3 experiment configurations/runners
├── 05_results/               # Raw and summarized outputs
├── 06_figures/               # Pareto and burden-distribution figures
├── 07_report/                # Research design, objectives, constraints, results
└── docs/                     # Supporting documentation
```

## Experimental scenarios

| Scenario | Cost objective | Burden/equity dimension | Status |
|---|---|---|---|
| S0 | Minimize OGC delivery cost | None | Baseline |
| S1 | Minimize OGC delivery cost | Order Count | Planned |
| S2 | Minimize OGC delivery cost | Active Route Duration | Planned |
| S3 | Minimize OGC delivery cost | Waiting Time | Planned |

The exact **inequality function** used as the second objective (for example, Gini or another equity function) will be documented explicitly before the final runs rather than being silently assumed.

## Reproducibility principles

1. Preserve the original OGC baseline separately from research modifications.
2. Use the same feasibility logic across S0-S3.
3. Apply the same BIKE-only analysis scope across scenarios.
4. Change only the burden/equity objective when comparing S1-S3.
5. Save optimization settings, random seeds, raw Pareto solutions, summary metrics, and figures.
6. Document every objective function and constraint in `07_report/02_objective_functions_and_constraints.md`.

## Data

The project uses OGC 2024 problem instances containing order, rider, temporal, spatial, and distance-matrix information. Large raw files are handled separately from source code; see `01_data/README.md` for the repository data policy.

## Research output

The intended output is a transparent comparison of:

- baseline cost efficiency,
- burden inequality by dimension,
- Pareto-optimal cost–equity trade-offs,
- and the **Price of Fairness** required to improve equity.

## Project status

Repository scaffold initialized. Next steps are:

1. import and preserve the supplied OGC baseline,
2. verify the original objective and feasibility checks from code,
3. implement burden extraction,
4. finalize the equity function,
5. run S0-S3,
6. populate `05_results/`, `06_figures/`, and `07_report/`.
