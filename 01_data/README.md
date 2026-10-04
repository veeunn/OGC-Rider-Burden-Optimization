# 01_data

OGC 2024 problem instances used in this study.

The user has confirmed that the supplied competition data may be included in this research repository.

## Layout

```text
01_data/
├── README.md
├── test/
└── stage1/
```

## Committed reproducibility set

At minimum, the repository contains small test instances and Stage 1 instances required for the baseline smoke/reproduction workflow.

All JSON files use the original OGC schema and are not transformed before optimization.

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

Run:

```bash
python scripts/validate_data.py 01_data/test/TEST_K50_1.json
```

The validator checks order count, distance-matrix shape, and the presence of BIKE rider data.
