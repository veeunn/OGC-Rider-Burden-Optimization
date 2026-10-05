# Stage 1 16-instance QA and freeze report

## Final verdict

**PASS — suitable to freeze for Results use**

The locked primary sample contains 16 Stage 1 instances × 3 equity scenarios × 5 seeds = **240 seed-level scenario results**.

## Critical QA table

| Check | Result | Detail |
|---|---|---|
| Expected rows | PASS | 240/240 |
| Missing seeds | PASS | 0 missing |
| R0 consistency | PASS | consistent across all 16 instances |
| Baseline-cost consistency | PASS | corrected best-known baseline consistent across all seed/scenario rows |
| Baseline-Gini recomputation | PASS | recomputed from selected candidate IDs and the original candidate pool |
| Best-known baseline feasibility | PASS | fixed R0 plus exact pickup/delivery cover for all 16 |
| Formula recomputation | PASS | PoF and equity improvement match corrected baseline formulas |
| Negative PoF after correction | PASS | none below numerical tolerance |
| Pareto dominance | PASS | no dominated points in corrected pooled frontiers |
| S0 solver status | PASS | 12 Optimal; 4 time-limit feasible incumbents |
| Numerical anomalies | REVIEW | retained below for interpretation |
| Final verdict | PASS | suitable to freeze for Results use |

## S0 solver verification

**Proven optimal (12):** STAGE1_1, STAGE1_2, STAGE1_3, STAGE1_4, STAGE1_7, STAGE1_8, STAGE1_9, STAGE1_13, STAGE1_14, STAGE1_15, STAGE1_16, STAGE1_17.

**Time-limit feasible incumbent (4):** STAGE1_5, STAGE1_10, STAGE1_11, STAGE1_18.

Publication wording must distinguish proven-optimal cases from time-limited cases. For the latter, use **best-known feasible S0 baseline**, not global cost-optimal S0.

## Baseline corrections

- **STAGE1_5:** 2005.523333 → 2005.403333 (**0.0060% lower**), source S1 seed 2.
- **STAGE1_10:** 3599.757000 → 3586.557000 (**0.3667% lower**), source S3 seed 4.
- **STAGE1_18:** 3768.252000 → 3766.050000 (**0.0584% lower**), source S1 seed 4.
- **STAGE1_11:** time-limited S0 retained because no lower-cost feasible solution was found.

Each corrected assignment keeps the same R0 and exactly covers all pickups and deliveries. For corrected instances, the new baseline assignment was evaluated under S1/S2/S3, inserted into each frontier, and the nondominated set and knee were recomputed. This removes the artificial negative PoF values.

## Frozen scenario-level results

| Scenario | N | Pooled-knee equity improvement mean ± SD | Pooled-knee PoF mean ± SD |
|---|---:|---:|---:|
| S1 | 16 | **12.45% ± 13.94%** | **1.19% ± 2.24%** |
| S2 | 16 | **27.58% ± 8.35%** | **2.62% ± 1.67%** |
| S3 | 16 | **26.70% ± 7.77%** | **3.28% ± 1.57%** |

## Anomalies retained for interpretation

- STAGE1_10-S1 remains a genuine high-effect case: pooled-knee improvement **62.46%**, PoF **9.54%** after baseline correction.
- STAGE1_14-S2-seed2 had one historical same-cost/worse-Gini point in a per-seed Pareto file; the pooled nondominated filter removes it, so the aggregate results are unaffected.
- Baseline improvements in STAGE1_5 and STAGE1_18 are small but are retained at full precision rather than manually clipped.

## Freeze policy

The files in `05_results/frozen_stage1_16/` are now the numeric source of truth for manuscript Results, tables, and figures. Do not hand-recalculate values from older workflow artifacts. Any change to model logic, candidate pools, burden definitions, R0 policy, or baseline construction requires a new freeze version.
