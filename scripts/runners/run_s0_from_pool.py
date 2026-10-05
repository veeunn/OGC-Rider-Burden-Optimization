"""Solve S0 from an already generated BIKE candidate pool.

Used for computational rescue of Stage 1 instances whose candidate generation
finished successfully but whose exact-cover MILP exceeded the short smoke-test
limit. This avoids regenerating the candidate pool.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "03_src"
sys.path.insert(0, str(SRC))

from candidate_pool import load_candidate_pool
from set_partition import cost_optimal_selection


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-pool", required=True)
    ap.add_argument("--problem", required=True)
    ap.add_argument("--timelimit", type=float, default=600.0)
    ap.add_argument("--output-dir", default="05_results/S0")
    args = ap.parse_args()

    pool_path = Path(args.candidate_pool)
    problem_path = Path(args.problem)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = load_candidate_pool(pool_path)
    stem = problem_path.stem

    t0 = time.time()
    x, res = cost_optimal_selection(pool, time_limit=args.timelimit)
    solve_time = time.time() - t0

    selected = np.flatnonzero(x > 0)
    r0 = int(selected.size)
    total_cost = float(sum(pool["candidates"][int(i)]["cost"] for i in selected))
    avg_cost = total_cost / float(pool["K"])

    bundles = [
        ["BIKE", pool["candidates"][int(i)]["shop_seq"], pool["candidates"][int(i)]["dlv_seq"]]
        for i in selected
    ]

    solution = {
        "scenario": "S0",
        "problem": pool["problem"],
        "problem_file": str(problem_path),
        "K": int(pool["K"]),
        "R0": r0,
        "workforce_policy": "S0-fixed",
        "analysis_scope": "BIKE-only",
        "equity_population": "active riders only",
        "total_cost": total_cost,
        "avg_cost": avg_cost,
        "num_drivers": r0,
        "selected_candidate_ids": [int(i) for i in selected],
        "bundles": bundles,
        "candidate_pool_file": str(pool_path),
        "n_candidates": int(pool["n_candidates"]),
        "candidate_counts_by_bundle_size": pool["candidate_counts_by_bundle_size"],
        "pool_generation_sec": float(pool.get("pool_generation_sec", 0.0)),
        "solve_time_sec": float(solve_time),
        "milp_status": int(res.status),
        "milp_message": str(res.message),
        "feasible": True,
        "rescue_run": True,
    }

    manifest = {
        "problem": pool["problem"],
        "problem_file": str(problem_path),
        "K": int(pool["K"]),
        "scenario": "S0",
        "R0": r0,
        "baseline_avg_cost": avg_cost,
        "baseline_total_cost": total_cost,
        "selected_candidate_ids": [int(i) for i in selected],
        "s0_bike_availability": "non-binding",
        "candidate_pool_file": str(pool_path),
        "n_candidates": int(pool["n_candidates"]),
        "solver_backend": "scipy-milp",
        "solve_time_sec": float(solve_time),
        "pool_generation_sec": float(pool.get("pool_generation_sec", 0.0)),
        "workforce_policy": "S0-fixed",
        "equity_population": "active riders only",
        "rescue_run": True,
    }

    solution_path = out_dir / f"{stem}_S0.json"
    manifest_path = out_dir / f"{stem}_workforce.json"
    solution_path.write_text(json.dumps(solution, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"S0 solution: {solution_path}")
    print(f"Workforce manifest: {manifest_path}")


if __name__ == "__main__":
    main()
