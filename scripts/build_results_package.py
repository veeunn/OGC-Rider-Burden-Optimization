"""Build paper-ready tables and figures from the completed Stage 1 final experiment.

Input
-----
A directory containing the artifact produced by run-stage1-final.yml:
- instance_scenario_summary.csv
- scenario_overall_summary.csv
- STAGE1_*_S*_pooled_pareto.json

Output
------
CSV tables, PNG figures, and a concise Markdown results brief.

Raw numerical outputs are never altered. For presentation only, PoF values with
absolute magnitude < 0.01 percentage points are displayed as 0.00 to avoid
showing solver/rounding noise as substantive cost savings.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIO_LABELS = {
    "S1": "Order Count",
    "S2": "Route Duration",
    "S3": "Waiting Time",
}

def display_pof(x: float) -> float:
    x = float(x)
    return 0.0 if abs(x) < 0.01 else x

def instance_number(name: str) -> int:
    return int(str(name).split("_")[-1])

def load_k(repo_root: Path, instance: str) -> int | None:
    p = repo_root / "01_data" / "stage1" / f"{instance}.json"
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            return int(json.load(f)["K"])
    except Exception:
        return None

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-dir", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    src = Path(args.summary_dir)
    repo = Path(args.repo_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    inst = pd.read_csv(src / "instance_scenario_summary.csv")
    scen = pd.read_csv(src / "scenario_overall_summary.csv")

    inst["instance_no"] = inst["instance"].map(instance_number)
    inst["K"] = inst["instance"].map(lambda x: load_k(repo, x))
    inst = inst.sort_values(["instance_no", "scenario"]).reset_index(drop=True)

    # Preserve raw fields and add presentation-safe PoF fields.
    inst["pooled_knee_pof_display"] = inst["pooled_knee_pof_pct"].map(display_pof)
    inst["pooled_lowest_pof_display"] = inst["pooled_lowest_pof_pct"].map(display_pof)

    table1_cols = [
        "instance", "K", "R0", "scenario", "baseline_gini",
        "pooled_knee_improvement_pct", "pooled_knee_pof_display",
        "pooled_lowest_improvement_pct", "pooled_lowest_pof_display",
        "pooled_n_pareto",
    ]
    table1 = inst[table1_cols].rename(columns={
        "pooled_knee_pof_display": "pooled_knee_pof_pct",
        "pooled_lowest_pof_display": "pooled_lowest_pof_pct",
    })
    table1.to_csv(out / "table1_instance_scenario_results.csv", index=False)

    table2 = scen.copy()
    table2.to_csv(out / "table2_scenario_aggregate.csv", index=False)

    # Figure 1: pooled-knee cost-equity trade-off across all 13 instances.
    fig, ax = plt.subplots(figsize=(8.5, 6))
    for scenario, g in inst.groupby("scenario"):
        ax.scatter(
            g["pooled_knee_pof_display"],
            g["pooled_knee_improvement_pct"],
            label=f"{scenario}: {SCENARIO_LABELS[scenario]}",
            alpha=0.8,
        )
    ax.set_xlabel("Price of Fairness at pooled knee (%)")
    ax.set_ylabel("Equity improvement at pooled knee (%)")
    ax.set_title("Stage 1 pooled-knee cost–equity trade-off")
    ax.axvline(0, linewidth=0.8)
    ax.axhline(0, linewidth=0.8)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig1_pooled_knee_tradeoff.png", dpi=220)
    plt.close(fig)

    # Figure 2: instance-wise pooled-knee equity improvement.
    pivot = inst.pivot(index="instance_no", columns="scenario", values="pooled_knee_improvement_pct")
    pivot = pivot.sort_index()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for scenario in ["S1", "S2", "S3"]:
        if scenario in pivot.columns:
            ax.plot(pivot.index, pivot[scenario], marker="o", label=f"{scenario}: {SCENARIO_LABELS[scenario]}")
    ax.set_xlabel("Stage 1 instance")
    ax.set_ylabel("Pooled-knee equity improvement (%)")
    ax.set_title("Equity improvement by instance and burden definition")
    ax.set_xticks(pivot.index)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig2_instance_knee_improvement.png", dpi=220)
    plt.close(fig)

    # Figure 3: scenario aggregate comparison.
    x = np.arange(len(scen))
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.bar(x, scen["pooled_knee_improvement_mean"], yerr=scen["pooled_knee_improvement_sd"], capsize=4)
    ax.set_xticks(x, [f"{s}\n{SCENARIO_LABELS[s]}" for s in scen["scenario"]])
    ax.set_ylabel("Mean pooled-knee equity improvement (%)")
    ax.set_title("Scenario-level equity improvement across 13 instances")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "fig3_scenario_improvement.png", dpi=220)
    plt.close(fig)

    # Representative pooled Pareto frontiers: one small, one medium, one large instance.
    representatives = ["STAGE1_1", "STAGE1_3", "STAGE1_11"]
    for instance in representatives:
        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        plotted = False
        for scenario in ["S1", "S2", "S3"]:
            p = src / f"{instance}_{scenario}_pooled_pareto.json"
            if not p.exists():
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            pts = d.get("pooled_pareto", [])
            if not pts:
                continue
            xs = [display_pof(q["price_of_fairness_pct"]) for q in pts]
            ys = [q["equity_improvement_pct_vs_s0"] for q in pts]
            ax.plot(xs, ys, marker=".", linewidth=1, label=f"{scenario}: {SCENARIO_LABELS[scenario]}")
            plotted = True
        if plotted:
            ax.set_xlabel("Price of Fairness (%)")
            ax.set_ylabel("Equity improvement vs S0 (%)")
            ax.set_title(f"Pooled Pareto frontier: {instance}")
            ax.legend()
            ax.grid(alpha=0.2)
            fig.tight_layout()
            fig.savefig(out / f"fig4_pareto_{instance}.png", dpi=220)
        plt.close(fig)

    # Markdown results brief.
    s = scen.set_index("scenario")
    lines = [
        "# Stage 1 Final Results Package — 13 computationally completed instances",
        "",
        "## Experiment status",
        "",
        "Final NSGA-II settings are population = 80, generations = 100, five random seeds (0–4), and Gini as the primary inequality metric. The current final set contains 13 Stage 1 instances that completed the S0 baseline and all three equity scenarios. The remaining five Stage 1 instances are not silently discarded; they remain a separate computational-rescue task.",
        "",
        "## Main descriptive result",
        "",
        f"- S1 (Order Count): mean pooled-knee equity improvement = **{s.loc['S1','pooled_knee_improvement_mean']:.2f}%** with mean PoF = **{s.loc['S1','pooled_knee_pof_mean']:.2f}%**.",
        f"- S2 (Route Duration): mean pooled-knee equity improvement = **{s.loc['S2','pooled_knee_improvement_mean']:.2f}%** with mean PoF = **{s.loc['S2','pooled_knee_pof_mean']:.2f}%**.",
        f"- S3 (Waiting Time): mean pooled-knee equity improvement = **{s.loc['S3','pooled_knee_improvement_mean']:.2f}%** with mean PoF = **{s.loc['S3','pooled_knee_pof_mean']:.2f}%**.",
        "",
        "Across the current 13-instance set, S2 and S3 show substantially larger reductions in rider-burden inequality than S1, while their average cost penalties at the pooled knee remain in the low-single-digit range. S1 shows a smaller equity gain but the lowest average Price of Fairness.",
        "",
        "## Interpretation by research question",
        "",
        "**RQ1 — Baseline inequality.** The cost-minimizing S0 solution produces non-zero burden inequality under all three burden definitions in the completed instances. Baseline Gini differs materially by burden definition, so the three measures should remain separate rather than be collapsed into a composite burden score.",
        "",
        "**RQ2 — Can equity improve with the same workforce?** Yes. Because S1–S3 retain the S0-derived R0, improvements come from reassignment among the same number of active BIKE riders rather than activating additional riders.",
        "",
        "**RQ3 — What is the Price of Fairness?** At the pooled knee, the average PoF is lowest for S1 and remains moderate for S2/S3. Moving further to the lowest-Gini solution yields larger equity gains but a visibly larger cost premium, supporting a genuine cost–equity frontier rather than a single dominant solution.",
        "",
        "**RQ4 — Does the burden definition matter?** Yes. Order-count equity behaves differently from route-duration and waiting-time equity. The time-based measures show much larger attainable improvements, which suggests that equalizing the number of orders is not equivalent to equalizing temporal burden.",
        "",
        "## Numerical note",
        "",
        "STAGE1_5–S1 contains a pooled-knee PoF of approximately -0.006%. This package reports it as 0.00% for presentation because its magnitude is below 0.01 percentage points; the raw result remains unchanged in the source artifacts.",
        "",
        "## What is still provisional",
        "",
        "The 13-instance aggregate is descriptive, not the final population-wide claim until the five unresolved Stage 1 instances are either computationally recovered or excluded under a pre-specified, defensible computational-feasibility rule. No inferential significance claim should be attached to the across-instance mean±SD at this stage.",
        "",
    ]
    (out / "results_brief_13instances.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote results package to {out}")

if __name__ == "__main__":
    main()
