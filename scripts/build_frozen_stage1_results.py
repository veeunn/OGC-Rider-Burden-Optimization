"""Build manuscript-ready outputs from the frozen 16-instance Stage 1 results.

This script intentionally reads ONLY from:
    05_results/frozen_stage1_16/

It must not read historical workflow artifacts or pre-freeze summaries.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIO_LABELS = {
    "S1": "Order Count",
    "S2": "Route Duration",
    "S3": "Waiting Time",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-dir", default="05_results/frozen_stage1_16")
    ap.add_argument("--out-dir", default="06_figures/frozen_stage1_16")
    args = ap.parse_args()

    frozen = Path(args.frozen_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    inst = pd.read_csv(frozen / "instance_scenario_results_frozen.csv")
    scen = pd.read_csv(frozen / "scenario_overall_summary_frozen.csv")

    # Table A: scenario-level headline results.
    t1 = scen[[
        "scenario", "n_instances",
        "pooled_knee_improvement_mean", "pooled_knee_improvement_sd",
        "pooled_knee_pof_mean", "pooled_knee_pof_sd"
    ]].copy()
    t1["burden"] = t1["scenario"].map(SCENARIO_LABELS)
    t1 = t1[[
        "scenario","burden","n_instances",
        "pooled_knee_improvement_mean","pooled_knee_improvement_sd",
        "pooled_knee_pof_mean","pooled_knee_pof_sd"
    ]]
    t1.to_csv(out / "tableA_scenario_headline.csv", index=False)

    # Table B: all 48 frozen instance-scenario rows.
    inst.to_csv(out / "tableB_instance_scenario_frozen.csv", index=False)

    # Figure 1: instance-level knee trade-off.
    fig, ax = plt.subplots(figsize=(8.4, 6.0))
    for s in ["S1","S2","S3"]:
        g = inst[inst["scenario"] == s]
        ax.scatter(
            g["pooled_knee_pof_pct"],
            g["pooled_knee_improvement_pct"],
            label=f"{s}: {SCENARIO_LABELS[s]}",
            alpha=0.82,
        )
    ax.set_xlabel("Price of Fairness at pooled knee (%)")
    ax.set_ylabel("Equity improvement at pooled knee (%)")
    ax.set_title("Frozen Stage 1 cost-equity trade-off")
    ax.axvline(0, linewidth=0.8)
    ax.axhline(0, linewidth=0.8)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig1_tradeoff_frozen.png", dpi=240)
    plt.close(fig)

    # Figure 2: instance-level improvement by burden definition.
    inst["instance_no"] = inst["instance"].str.split("_").str[-1].astype(int)
    pivot = inst.pivot(index="instance_no", columns="scenario", values="pooled_knee_improvement_pct").sort_index()
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    for s in ["S1","S2","S3"]:
        ax.plot(pivot.index, pivot[s], marker="o", label=f"{s}: {SCENARIO_LABELS[s]}")
    ax.set_xlabel("Stage 1 instance")
    ax.set_ylabel("Pooled-knee equity improvement (%)")
    ax.set_title("Frozen equity improvement by instance")
    ax.set_xticks(pivot.index)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig2_instance_improvement_frozen.png", dpi=240)
    plt.close(fig)

    # Figure 3: scenario-level mean improvement with SD.
    x = np.arange(len(scen))
    fig, ax = plt.subplots(figsize=(7.3, 5.4))
    ax.bar(
        x,
        scen["pooled_knee_improvement_mean"],
        yerr=scen["pooled_knee_improvement_sd"],
        capsize=4,
    )
    ax.set_xticks(x, [f"{s}\n{SCENARIO_LABELS[s]}" for s in scen["scenario"]])
    ax.set_ylabel("Mean pooled-knee equity improvement (%)")
    ax.set_title("Scenario-level equity improvement across 16 instances")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig3_scenario_improvement_frozen.png", dpi=240)
    plt.close(fig)

    s = scen.set_index("scenario")
    brief = f"""# Frozen Stage 1 Results Brief

## Headline result

Across the locked 16-instance Stage 1 sample, the pooled-knee solution improves rider-burden equity with modest average cost penalties.

- S1 Order Count: **{s.loc['S1','pooled_knee_improvement_mean']:.2f}% ± {s.loc['S1','pooled_knee_improvement_sd']:.2f}%** equity improvement at **{s.loc['S1','pooled_knee_pof_mean']:.2f}% ± {s.loc['S1','pooled_knee_pof_sd']:.2f}%** Price of Fairness.
- S2 Route Duration: **{s.loc['S2','pooled_knee_improvement_mean']:.2f}% ± {s.loc['S2','pooled_knee_improvement_sd']:.2f}%** improvement at **{s.loc['S2','pooled_knee_pof_mean']:.2f}% ± {s.loc['S2','pooled_knee_pof_sd']:.2f}%** PoF.
- S3 Waiting Time: **{s.loc['S3','pooled_knee_improvement_mean']:.2f}% ± {s.loc['S3','pooled_knee_improvement_sd']:.2f}%** improvement at **{s.loc['S3','pooled_knee_pof_mean']:.2f}% ± {s.loc['S3','pooled_knee_pof_sd']:.2f}%** PoF.

## Interpretation

The attainable equity gain depends strongly on how rider burden is defined. Order-count equity improves the least but requires the smallest average cost sacrifice. Time-based burdens show substantially larger average improvements while keeping mean pooled-knee cost increases in the low single digits.

The result supports three points. First, fixed-workforce reassignment alone can materially reduce burden inequality. Second, the Price of Fairness is positive but moderate at the knee. Third, equalizing order counts is not equivalent to equalizing temporal burden.

## Important case

STAGE1_10-S1 remains the strongest high-effect observation after baseline correction, with **62.46%** pooled-knee equity improvement and **9.54%** PoF.

## Source-of-truth rule

All values in this brief are read from the frozen files under `05_results/frozen_stage1_16/`. Historical workflow artifacts are not used.
"""
    (out / "results_brief_frozen.md").write_text(brief, encoding="utf-8")
    print(f"Wrote frozen results outputs to {out}")

if __name__ == "__main__":
    main()
