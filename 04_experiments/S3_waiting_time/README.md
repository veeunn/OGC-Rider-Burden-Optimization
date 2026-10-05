# S3 — Waiting Time equity

Objectives:

1. minimize OGC average delivery cost;
2. minimize inequality in rider Waiting Time.

Waiting Time is pickup-location idle time before an assigned order is ready. The waiting-time extraction is implemented and used in the frozen primary analysis.

The active-rider count is fixed to the S0-derived `R0`.

Implemented through `scripts/runners/run_equity.py --scenario S3`.
