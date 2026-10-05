# OGC Rider Burden Optimization

Multi-objective last-mile delivery optimization research based on the **Optimization Grand Challenge 2024 (OGC 2024)** food-delivery problem.

## Research goal

This project studies whether a cost-minimizing delivery allocation can concentrate operational burden on particular riders, and how much additional delivery cost is required to improve burden equity.

> **Main-study scope (current): OGC Stage 1 only.** The primary empirical analysis is locked to **16 Stage 1 instances**. STAGE1_6 and STAGE1_12 are retained as unresolved computational extension cases. Stage 2/3 files and scalability prototypes are preserved for reproducibility and future extension, but they are **not part of the current main empirical study**.

The current study design uses **BIKE riders only** to control for transport-mode heterogeneity and evaluates three burden dimensions separately:

- **S1 — Order Count:** number of orders assigned to each rider
- **S2 — Active Route Duration:** travel and service time, excluding waiting time
- **S3 — Waiting Time:** idle time at pickup locations before orders are ready

A cost-only solution is retained as the **S0 baseline**. Each burden scenario is compared against S0 using a cost–equity Pareto analysis with NSGA-II.

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
├── 07_report/                # Primary research design, methods, QA, and Results
└── scripts/                  # Runners, validation, summaries, result builders
```

## Experimental scenarios

| Scenario | Cost objective | Burden/equity dimension | Status |
|---|---|---|---|
| S0 | Minimize OGC delivery cost | None | Completed baseline |
| S1 | Minimize OGC delivery cost | Order Count | Frozen primary results |
| S2 | Minimize OGC delivery cost | Active Route Duration | Frozen primary results |
| S3 | Minimize OGC delivery cost | Waiting Time | Frozen primary results |

The primary inequality objective is **Gini**. Final Stage 1 settings are population = 80, generations = 100, and seeds = 0–4. The locked 16-instance primary results and QA outputs are stored under `05_results/frozen_stage1_16/`.

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

The main Stage 1 analysis is complete and the primary results are **frozen**. The locked sample contains 16 Stage 1 instances × 3 burden scenarios × 5 seeds = 240 seed-level scenario results. QA checks passed after correcting the best-known feasible baseline for three time-limited S0 cases.

Frozen numeric outputs are under `05_results/frozen_stage1_16/`, manuscript-ready figures are under `06_figures/frozen_stage1_16/`, and the primary document index is under `07_report/README.md`. Completed one-off GitHub Actions workflows are preserved under `.github/workflow_archive/`.

Stage 2/3 scalability work is archived as an experimental extension and is not required for the current paper.


## Quick start

Clone the repository and create the Python environment:

```bash
git clone https://github.com/veeunn/OGC-Rider-Burden-Optimization.git
cd OGC-Rider-Burden-Optimization
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Validate the committed OGC data

```bash
python scripts/validate_data.py \
  01_data/test/TEST_K50_1.json \
  01_data/test/TEST_K50_2.json \
  01_data/stage1/STAGE1_1.json \
  01_data/stage1/STAGE1_2.json
```

### 2. Run the supplied baseline

The default runner uses a **license-free SciPy MILP backend** for the final set-partitioning step while preserving the supplied bundle-generation logic and mathematical model.

```bash
python scripts/runners/run_baseline.py \
  --problem 01_data/test/TEST_K50_1.json \
  --solver scipy \
  --timelimit 60 \
  --save 05_results/raw/TEST_K50_1_baseline.json
```

To reproduce the original Gurobi backend instead:

```bash
pip install -r requirements-gurobi.txt
python scripts/runners/run_baseline.py --problem 01_data/test/TEST_K50_1.json --solver gurobi --timelimit 60
```

A valid Gurobi license is required for the Gurobi backend.

### 3. Calculate S1-S3 burden statistics

```bash
python scripts/runners/run_burden_report.py \
  --problem 01_data/test/TEST_K50_1.json \
  --solution 05_results/raw/TEST_K50_1_baseline.json \
  --rider-type BIKE \
  --save 05_results/raw/TEST_K50_1_burden.json
```

This produces separate rider-level and distributional results for:

- S1 Order Count,
- S2 Active Route Duration,
- S3 Waiting Time.

### BIKE-only runs

```bash
python scripts/runners/run_baseline.py \
  --problem 01_data/stage1/STAGE1_2.json \
  --solver scipy \
  --timelimit 100 \
  --bike-only
```

`--bike-only` preserves the original BIKE availability while setting WALK/CAR availability to zero.

If a methodological experiment intentionally changes BIKE availability, it must be explicit:

```bash
python scripts/runners/run_baseline.py ... --bike-only --bike-availability 100
```

Availability overrides must never be silently mixed with the original OGC constraints.

## Original vs runnable baseline

The exact supplied files are preserved under:

```text
02_baseline/original/
```

Runnable copies are under:

```text
02_baseline/runnable/
```

The original `util.py` contains two evaluator/plotting call sites that pass `rider.T` to a function whose definition expects the Rider object. The runnable copy fixes only those call sites. The source-level audit is documented in `07_report/06_baseline_code_audit.md`.

The SciPy backend is stored separately as `myalgorithm_scipy.py`; the original Gurobi algorithm is not overwritten.

## Manual validation

`.github/workflows/ci.yml` is intentionally **manual-only** after the Stage 1 results freeze. When explicitly dispatched, it checks Python syntax, validates committed OGC instances, runs a license-free baseline smoke test, and generates an S1-S3 burden report on a small test instance.

Routine documentation or repository-cleanup commits do not automatically consume GitHub Actions runner time.


## Fixed-workforce research workflow

The main study workflow is now:

```text
S0 cost minimization
   ↓
save R0 = active BIKE riders
   ↓
S1 / S2 / S3 all inherit exactly R0 riders
```

Run S0:

```bash
python scripts/runners/run_s0.py \
  --problem 01_data/test/TEST_K50_1.json \
  --solver scipy \
  --timelimit 60
```

This writes:

```text
05_results/S0/TEST_K50_1_S0.json
05_results/S0/TEST_K50_1_workforce.json
```

The workforce manifest contains the baseline cost and `R0`.

Check the inherited scenario configuration:

```bash
python scripts/runners/run_equity_config.py --scenario S1 --workforce 05_results/S0/TEST_K50_1_workforce.json
python scripts/runners/run_equity_config.py --scenario S2 --workforce 05_results/S0/TEST_K50_1_workforce.json
python scripts/runners/run_equity_config.py --scenario S3 --workforce 05_results/S0/TEST_K50_1_workforce.json
```

The S1-S3 optimizer enforces:

```text
number of selected bundles = R0
```

so equity improvements cannot be produced merely by changing workforce size.


## S1-S3 NSGA-II implementation

The repository now contains a complete fixed-workforce NSGA-II pipeline:

```text
03_src/candidate_pool.py
03_src/set_partition.py
03_src/nsga2_solver.py
scripts/runners/run_s0.py
scripts/runners/run_equity.py
scripts/runners/run_all_scenarios.py
```

The key design is that **S0 and S1-S3 use the identical BIKE candidate route pool**. S0 solves cost-minimizing exact cover on that pool and saves `R0`; S1-S3 then optimize cost and one burden inequality objective while enforcing both exact order coverage and exactly `R0` selected routes.

Run the whole pipeline for one instance:

```bash
python scripts/runners/run_all_scenarios.py \
  --problem 01_data/test/TEST_K50_1.json \
  --timelimit 60 \
  --population-size 40 \
  --generations 50 \
  --seed 0 \
  --metric gini
```

The default second objective is **Gini**, while `std`, `range`, `max`, and `cv` remain available for sensitivity analysis.

NSGA-II chromosomes are binary selections over candidate BIKE bundles. Every offspring is repaired through an exact-cover MILP before evaluation, guaranteeing:

- every order is covered exactly once;
- exactly `R0` active riders are used;
- only feasible candidate routes generated from the verified OGC timing/capacity logic are selected.

Each scenario output includes its Pareto set, rider-level burden values, Price of Fairness relative to S0, and a computed knee-point candidate.
