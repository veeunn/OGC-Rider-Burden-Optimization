# 10. Results — Frozen Stage 1 Primary Analysis

## 10.1 Analysis set and QA status

The primary Stage 1 analysis uses 16 locked OGC instances. For each instance, three equity scenarios (S1-S3) were evaluated across five random seeds, yielding 240 seed-level scenario results in total. All expected rows were present, no seed was missing, and the fixed-workforce constraint R0 was consistent across scenarios. Formula recomputation, corrected baseline consistency, and pooled Pareto dominance checks all passed.

The S0 cost baseline was solver-proven optimal for 12 instances. Four instances (STAGE1_5, STAGE1_10, STAGE1_11, and STAGE1_18) reached the MILP time limit with feasible incumbents. For these cases, the analysis therefore uses the best-known feasible fixed-R0 baseline rather than claiming a globally optimal S0. The best-known baseline improved the original S0 cost for STAGE1_5, STAGE1_10, and STAGE1_18, while STAGE1_11 remained unchanged.

## 10.2 Cost-equity trade-off at the pooled knee

Across the 16-instance primary set, all three burden definitions show that rider-burden inequality can be reduced through reassignment while keeping the number of active BIKE riders fixed.

For S1 (Order Count), the mean pooled-knee equity improvement is **12.45% (SD 13.94%)**, with a mean Price of Fairness of **1.19% (SD 2.24%)**. S1 therefore provides the smallest average equity gain among the three burden dimensions, but it also requires the smallest average cost increase.

For S2 (Route Duration), the mean pooled-knee equity improvement rises to **27.58% (SD 8.35%)**, with a mean Price of Fairness of **2.62% (SD 1.67%)**. This indicates that substantial reductions in time-burden inequality are attainable without changing workforce size and with a relatively moderate increase in delivery cost.

For S3 (Waiting Time), the mean pooled-knee equity improvement is **26.70% (SD 7.77%)**, with a mean Price of Fairness of **3.28% (SD 1.57%)**. The achievable improvement is therefore comparable to S2, although the average cost premium is slightly higher.

Taken together, the pooled-knee results show a clear burden-definition effect. Time-based burdens (route duration and waiting time) exhibit considerably larger attainable equity improvements than order count. This implies that balancing the number of assigned orders is not equivalent to balancing the temporal burden experienced by riders.

## 10.3 Fixed-workforce interpretation

All S1-S3 solutions inherit the S0-derived active-rider count R0. Accordingly, the observed equity improvements do not result from activating additional riders. They arise from reallocating feasible delivery bundles among the same number of active BIKE riders.

This feature is important for interpreting the Price of Fairness. The reported cost increases represent the operational cost of selecting a more equitable assignment within a fixed workforce, rather than the cost of expanding workforce capacity.

## 10.4 Lowest-Gini solutions versus pooled-knee solutions

The lowest-Gini solutions generally achieve larger reductions in burden inequality than the pooled-knee solutions, but at a noticeably higher cost premium. This confirms that the relationship is a genuine cost-equity trade-off rather than a case in which one solution simultaneously dominates both the baseline cost and the equity objective.

The pooled-knee point is therefore used as the main descriptive compromise solution because it captures a substantial portion of the attainable equity improvement without moving to the more expensive extreme of the frontier.

## 10.5 Heterogeneity across instances

The magnitude of the cost-equity trade-off varies meaningfully across Stage 1 instances. The most prominent case is **STAGE1_10-S1**, where the corrected pooled-knee solution improves order-count equity by **62.46%** at a **9.54%** Price of Fairness. This value remains high even after correcting the time-limited S0 baseline, indicating that it is not an artifact of the original baseline cost.

At the other extreme, STAGE1_5-S1 has a pooled-knee improvement of approximately 0% after baseline correction. This illustrates that equity gains are not mechanically guaranteed by the optimization framework and depend on the feasible assignment structure of each instance.

## 10.6 Main empirical implications

Three empirical implications emerge from the frozen Stage 1 results.

First, rider-burden equity can be improved without increasing the number of active riders. This supports the view that assignment structure itself is a meaningful source of rider-burden inequality.

Second, the average Price of Fairness at the pooled knee remains in the low-single-digit range across all three burden definitions. The results therefore suggest that meaningful equity improvements can often be obtained without a proportionally large sacrifice in operational cost.

Third, burden definition materially affects the apparent equity opportunity. Order Count, Route Duration, and Waiting Time should therefore be analyzed separately rather than collapsed into a single composite burden index.

## 10.7 Scope of inference

The across-instance mean and standard deviation reported above are descriptive summaries of the locked 16-instance Stage 1 sample. They are not treated as population-level inferential estimates. STAGE1_6 and STAGE1_12 remain computational extension cases and are not retroactively added to the primary sample.

All numerical values in this section are frozen and should be taken only from `05_results/frozen_stage1_16/`.
