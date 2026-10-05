# Frozen Stage 1 primary results (16 instances)

Status: **FROZEN for Results use on 2026-10-05 after QA**.

This folder is the numeric source of truth for the locked primary Stage 1 analysis: 16 instances × S1/S2/S3 × seeds 0–4 = 240 seed-level scenario results.

Use these files for all manuscript tables, figures, and reported numbers. Do not copy values from older workflow artifacts after this freeze.

Key files:

- qa_report.md — human-readable QA verdict, S0 solver audit, baseline corrections, and anomaly review.
- qa_checks.csv — machine-readable PASS/REVIEW checklist.
- final_stage1_summary_frozen.md — human-readable final pooled-knee and lowest-Gini summary.
- instance_scenario_results_frozen.csv — machine-readable 48-row instance × scenario frozen result table.
- scenario_overall_summary_frozen.csv — final across-instance descriptive aggregates.
- s0_solver_status.csv — original MILP status and frozen best-known baseline cost for each instance.
- freeze_manifest.json — locked sample, seeds, baseline policy, and changed baseline provenance.

Baseline policy:

- 12 instances have solver-proven optimal S0 solutions.
- STAGE1_5, STAGE1_10, STAGE1_11, and STAGE1_18 reached the S0 solver time limit with feasible incumbents.
- For time-limited cases, the frozen baseline is the best-known feasible fixed-R0 cost solution found across the S0 incumbent and final NSGA-II feasible solutions.
- This changes the baseline for STAGE1_5, STAGE1_10, and STAGE1_18; STAGE1_11 remains unchanged.

Any future change to model logic, candidate pools, burden definitions, R0 policy, or baseline construction requires a new freeze version rather than overwriting this folder.
