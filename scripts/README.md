# scripts

Utilities and reproducibility scripts.

## Current structure

- `runners/` — command-line entry points for S0-S3 and baseline runs
- `build_frozen_stage1_results.py` — current frozen-result table/figure builder
- `validate_data.py` — dataset validation
- `restore_split_data.py` — restore split Stage 2/3 JSON files
- `summarize_*.py` — experiment summary utilities
- `compare_bundling_implementations.py` — implementation comparison helper
- `validate_scalable_split.py` — scalability/split-data validation

`build_results_package.py` is retained as a **pre-freeze historical builder**. For manuscript outputs, use `build_frozen_stage1_results.py` and the frozen files under `05_results/frozen_stage1_16/`.

See `scripts/runners/README.md` for reproduction commands.
