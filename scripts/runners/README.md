# runners

Command-line entry points for reproducing the OGC rider-burden experiments.

Run them from the repository root, for example:

```bash
python scripts/runners/run_all_scenarios.py \
  --problem 01_data/test/TEST_K50_1.json \
  --timelimit 60 \
  --population-size 40 \
  --generations 50 \
  --seed 0 \
  --metric gini
```

The frozen manuscript results under `05_results/frozen_stage1_16/` should not be overwritten by routine reruns.
