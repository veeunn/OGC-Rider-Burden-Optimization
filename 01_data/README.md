# 01_data

OGC 2024 problem instances used in this study.

The user has confirmed that the supplied competition data may be included in this research repository.

## Layout

```text
01_data/
├── README.md
├── test/
├── stage1/
├── stage2_parts/
└── stage3_parts/
```

Stage 1 instances are stored as original JSON files. Stage 2 and Stage 3 use split binary parts because some original JSON files exceed GitHub's browser-upload size limit. Split parts are byte-for-byte fragments of the original files; they are not independently valid JSON documents.

Each split-data directory contains a `manifest.json` with the original filename, original byte size, SHA-256 digest, and ordered part list.

## Restore Stage 2 / Stage 3

Restore one instance and verify its byte size and SHA-256 digest:

```bash
python scripts/restore_split_data.py \
  --parts-dir 01_data/stage2_parts \
  --output-dir restored/stage2 \
  --file STAGE2_2.json
```

Restore every instance in a stage by omitting `--file`.

GitHub Actions workflows `Run Stage 2 batch` and `Run Stage 3 batch` perform restoration and verification automatically before validation and optimization.

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

For a normal JSON instance:

```bash
python scripts/validate_data.py 01_data/test/TEST_K50_1.json
```

For split Stage 2/3 data, restore it first and then run the same validator on the restored JSON.
