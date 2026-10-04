"""Run S0 and persist the baseline workforce size R0.

S0 policy
---------
1. BIKE only.
2. Set BIKE availability to K so the availability constraint is non-binding.
3. Minimize delivery cost.
4. Save R0 = number of selected BIKE bundles / active riders.

Example
-------
python run_s0.py \
  --problem 01_data/test/TEST_K50_1.json \
  --timelimit 60
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_baseline import run_problem


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True)
    ap.add_argument("--timelimit", type=float, default=60.0)
    ap.add_argument("--solver", choices=["scipy", "gurobi"], default="scipy")
    ap.add_argument(
        "--output-dir",
        default="05_results/S0",
        help="Directory for S0 solution and workforce manifest.",
    )
    args = ap.parse_args()

    problem_path = Path(args.problem)
    with problem_path.open("r", encoding="utf-8") as f:
        prob = json.load(f)

    K = int(prob["K"])
    result = run_problem(
        problem_path,
        timelimit=args.timelimit,
        solver=args.solver,
        bike_only=True,
        bike_availability=K,
        fixed_active_riders=None,
    )

    if not result.get("feasible", False):
        raise RuntimeError(
            f"S0 BIKE-only problem is infeasible for {problem_path}: "
            f"{result.get('infeasibility')}"
        )

    bike_bundles = [b for b in result["bundles"] if b[0] == "BIKE"]
    if len(bike_bundles) != result["num_drivers"]:
        raise RuntimeError(
            "S0 is intended to be BIKE-only, but a non-BIKE bundle was selected."
        )

    r0 = len(bike_bundles)
    result["scenario"] = "S0"
    result["R0"] = r0
    result["workforce_policy"] = "S0-fixed"
    result["s0_bike_availability"] = K

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = problem_path.stem

    solution_path = out_dir / f"{stem}_S0.json"
    manifest_path = out_dir / f"{stem}_workforce.json"

    with solution_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    manifest = {
        "problem": result["prob_name"],
        "problem_file": str(problem_path),
        "K": K,
        "scenario": "S0",
        "R0": r0,
        "baseline_avg_cost": result["avg_cost"],
        "baseline_total_cost": result["total_cost"],
        "s0_bike_availability": K,
        "solver_backend": result["solver_backend"],
        "runtime_sec": result["time"],
        "workforce_policy": "S0-fixed",
        "equity_population": "active riders only",
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"S0 solution: {solution_path}")
    print(f"Workforce manifest: {manifest_path}")


if __name__ == "__main__":
    main()
