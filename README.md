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
python run_baseline.py \
  --problem 01_data/test/TEST_K50_1.json \
  --solver scipy \
  --timelimit 60 \
  --save 05_results/raw/TEST_K50_1_baseline.json
```

To reproduce the original Gurobi backend instead:

```bash
pip install -r requirements-gurobi.txt
python run_baseline.py --problem 01_data/test/TEST_K50_1.json --solver gurobi --timelimit 60
```

A valid Gurobi license is required for the Gurobi backend.

### 3. Calculate S1-S3 burden statistics

```bash
python run_burden_report.py \
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
python run_baseline.py \
  --problem 01_data/stage1/STAGE1_2.json \
  --solver scipy \
  --timelimit 100 \
  --bike-only
```

`--bike-only` preserves the original BIKE availability while setting WALK/CAR availability to zero.

If a methodological experiment intentionally changes BIKE availability, it must be explicit:

```bash
python run_baseline.py ... --bike-only --bike-availability 100
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

## Continuous integration

`.github/workflows/ci.yml` checks Python syntax, validates committed OGC instances, runs a license-free baseline smoke test, and generates an S1-S3 burden report on a small test instance.
