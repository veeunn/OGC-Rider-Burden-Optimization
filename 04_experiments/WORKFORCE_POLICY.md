# Workforce Policy

## Decision

The study uses **S0-fixed workforce size**.

### Step 1 — S0
- Restrict the fleet to BIKE.
- Set BIKE availability to \(K\) so availability is non-binding.
- Minimize delivery cost.
- Record the number of selected BIKE bundles as \(R_0\).

### Step 2 — S1-S3
Use the same number of active riders in every equity-aware scenario:

\[
\sum_b x_b = R_0
\]

- S1 redistributes Order Count.
- S2 redistributes Active Route Duration.
- S3 redistributes Waiting Time.

## Interpretation

This design measures whether burden can be redistributed more equitably **without changing the number of active riders**.

A reduction in inequality therefore cannot be attributed simply to hiring/activating more riders.

## Equity population

Equity statistics are calculated over the \(R_0\) active riders only. Unused hypothetical BIKE capacity is not entered as zero-burden riders.

## Reproducibility record

Each S0 output must save:
- instance name,
- S0 average cost,
- S0 total cost,
- \(R_0\),
- BIKE availability used for S0 (= \(K\)),
- solver backend,
- runtime and seed.

Each S1-S3 run must record the inherited \(R_0\).
