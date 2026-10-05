# 01_data

OGC 2024 problem instances used in this study.

## Layout

```text
01_data/
├── README.md
├── test/          # small validation instances
├── stage1/        # Stage 1 instances used for the study
├── stage2_parts/  # split Stage 2 files retained for extension work
└── stage3_parts/  # split Stage 3 files retained for extension work
```

The **frozen primary empirical analysis uses 16 Stage 1 instances**. STAGE1_6 and STAGE1_12 remain unresolved computational extension cases. Stage 2/3 data are retained for reproducibility and future scalability work, not for the current frozen Results.

Stage 2 and Stage 3 use split binary parts because some original JSON files exceed GitHub's browser-upload size limit. Each split-data directory contains a `manifest.json` recording the original filename, byte size, SHA-256 digest, and ordered part list.

## Restore split Stage 2 / Stage 3 data

```bash
python scripts/restore_split_data.py \
  --parts-dir 01_data/stage2_parts \
  --output-dir restored/stage2 \
  --file STAGE2_2.json
```

Omit `--file` to restore all instances in a stage. The former Stage 2/3 batch workflows are preserved under `.github/workflow_archive/` for provenance but are not active.

## Schema

`RIDERS` rows:

```text
[type, speed, capacity, variable_cost_per_100m, fixed_cost, service_time, availability]
```

`ORDERS` rows:

```text
[order_id, order_time, pickup_lat, pickup_lon,
 delivery_lat, delivery_lon, preparation_time, volume, deadline]
```

`ready_time = order_time + preparation_time`.

`DIST` is a `2K × 2K` distance matrix for `K` orders.

## Validation

```bash
python scripts/validate_data.py 01_data/test/TEST_K50_1.json
```

For split Stage 2/3 data, restore the original JSON first and then validate the restored file.
