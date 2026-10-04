# 01_data

This directory documents the OGC 2024 problem instances used in the study.

## Supplied source archives

The research materials supplied for this project include:

- `stage1_problems`
- `stage2_problems`
- `stage3_problems`

The original archives are intentionally **not committed yet**. Before public release, the redistribution conditions for the OGC dataset must be checked. In addition, the Stage 3 archive is large enough that normal GitHub file storage may be inappropriate.

## Planned layout

```text
01_data/
├── README.md
├── stage1/
├── stage2/
└── stage3/
```

## Analysis scope

The study uses **BIKE riders only** to control for transport-mode heterogeneity.

## Relevant instance fields

Based on the supplied OGC problem description, the instances contain:

- rider type and rider attributes,
- rider speed,
- capacity,
- fixed and variable cost,
- service time,
- rider availability,
- order pickup and delivery coordinates,
- ready time,
- order volume,
- deadline,
- and a 2K × 2K distance matrix.

The exact mapping from raw fields to code variables will be documented after the original baseline parser is verified.
