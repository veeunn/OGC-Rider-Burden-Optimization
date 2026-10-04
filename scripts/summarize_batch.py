"""Aggregate S0-S3 batch outputs for any OGC stage."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SCENARIOS = ("S1", "S2", "S3")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def point_fields(point: dict | None, prefix: str) -> dict:
    point = point or {}
    return {
        f"{prefix}_cost": point.get("avg_cost"),
        f"{prefix}_inequality": point.get("inequality"),
        f"{prefix}_equity_improvement_pct": point.get("equity_improvement_pct_vs_s0"),
        f"{prefix}_pof_pct": point.get("price_of_fairness_pct"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="collected")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stage-label", required=True)
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    missing = []

    for wf_path in sorted(root.rglob("*_workforce.json")):
        wf = load_json(wf_path)
        problem = str(wf["problem"])
        instance = Path(wf.get("problem_file", problem)).stem

        for scenario in SCENARIOS:
            matches = sorted(root.rglob(f"{instance}_{scenario}_seed*.json"))
            if not matches:
                missing.append({"instance": instance, "scenario": scenario})
                continue

            for path in matches:
                d = load_json(path)
                baseline_summary = d.get("baseline_burden_summary", {})
                row = {
                    "instance": instance,
                    "problem": problem,
                    "K": wf.get("K"),
                    "R0": wf.get("R0"),
                    "baseline_avg_cost": wf.get("baseline_avg_cost"),
                    "scenario": scenario,
                    "burden_field": d.get("burden_field"),
                    "inequality_metric": d.get("inequality_metric"),
                    "baseline_inequality": d.get("baseline_inequality"),
                    "baseline_zero_burden_share": baseline_summary.get("zero_burden_share"),
                    "n_candidates": d.get("n_candidates"),
                    "n_pareto": d.get("n_pareto"),
                    "population_size": d.get("population_size"),
                    "generations": d.get("generations"),
                    "seed": d.get("seed"),
                }
                row.update(point_fields(d.get("lowest_cost_point"), "lowest_cost"))
                row.update(point_fields(d.get("knee_point"), "knee"))
                row.update(point_fields(d.get("lowest_inequality_point"), "lowest_inequality"))
                rows.append(row)

    rows.sort(key=lambda r: (r["instance"], r["scenario"], r.get("seed") or 0))

    stem = args.stage_label.lower().replace(" ", "_")
    csv_path = out_dir / f"{stem}_summary.csv"
    json_path = out_dir / f"{stem}_summary.json"
    md_path = out_dir / f"{stem}_summary.md"

    fieldnames = list(rows[0].keys()) if rows else ["instance", "scenario", "status"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps({"rows": rows, "missing": missing}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    def fmt(value, digits=3):
        if value is None:
            return "—"
        return f"{float(value):.{digits}f}"

    lines = [
        f"# {args.stage_label} experiment summary",
        "",
        f"- Completed scenario rows: {len(rows)}",
        f"- Missing scenario rows: {len(missing)}",
        "",
        "| Instance | Scenario | K | R0 | S0 inequality | Knee inequality | Equity improvement | PoF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['instance']} | {r['scenario']} | {r.get('K')} | {r.get('R0')} | "
            f"{fmt(r.get('baseline_inequality'))} | {fmt(r.get('knee_inequality'))} | "
            f"{fmt(r.get('knee_equity_improvement_pct'), 1)}% | "
            f"{fmt(r.get('knee_pof_pct'), 1)}% |"
        )

    if missing:
        lines += ["", "## Missing", ""]
        lines += [f"- {m['instance']} / {m['scenario']}" for m in missing]

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
