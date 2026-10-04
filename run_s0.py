"""Run S0 on the same BIKE candidate pool used by S1-S3.

S0 policy
---------
1. Generate the BIKE-only candidate bundle pool.
2. Make BIKE availability non-binding.
3. Solve the exact-cover cost-minimization problem.
4. Save R0 = number of selected bundles / active riders.
5. Persist the candidate pool so S1-S3 use the identical feasible route set.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"03_src"
sys.path.insert(0,str(SRC))

from candidate_pool import generate_bike_candidate_pool, save_candidate_pool
from set_partition import cost_optimal_selection


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--problem",required=True)
    ap.add_argument("--timelimit",type=float,default=60.0,
                    help="MILP time limit after candidate generation.")
    ap.add_argument("--pool-time-limit",type=float,default=None,
                    help="Optional candidate-generation time limit.")
    ap.add_argument("--output-dir",default="05_results/S0")
    args=ap.parse_args()

    problem_path=Path(args.problem)
    out_dir=Path(args.output_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    stem=problem_path.stem

    pool_path=out_dir/f"{stem}_bike_pool.json"
    solution_path=out_dir/f"{stem}_S0.json"
    manifest_path=out_dir/f"{stem}_workforce.json"

    pool=generate_bike_candidate_pool(
        problem_path,
        include_size4=True,
        generation_time_limit=args.pool_time_limit,
    )
    save_candidate_pool(pool,pool_path)

    t0=time.time()
    x,res=cost_optimal_selection(pool,time_limit=args.timelimit)
    solve_time=time.time()-t0

    selected=np.flatnonzero(x>0)
    r0=int(selected.size)
    total_cost=float(sum(pool["candidates"][int(i)]["cost"] for i in selected))
    avg_cost=total_cost/float(pool["K"])

    bundles=[
        ["BIKE",
         pool["candidates"][int(i)]["shop_seq"],
         pool["candidates"][int(i)]["dlv_seq"]]
        for i in selected
    ]

    solution={
        "scenario":"S0",
        "problem":pool["problem"],
        "problem_file":str(problem_path),
        "K":int(pool["K"]),
        "R0":r0,
        "workforce_policy":"S0-fixed",
        "analysis_scope":"BIKE-only",
        "equity_population":"active riders only",
        "total_cost":total_cost,
        "avg_cost":avg_cost,
        "num_drivers":r0,
        "selected_candidate_ids":[int(i) for i in selected],
        "bundles":bundles,
        "candidate_pool_file":str(pool_path),
        "n_candidates":int(pool["n_candidates"]),
        "candidate_counts_by_bundle_size":pool["candidate_counts_by_bundle_size"],
        "pool_generation_sec":float(pool["pool_generation_sec"]),
        "solve_time_sec":float(solve_time),
        "milp_status":int(res.status),
        "milp_message":str(res.message),
        "feasible":True,
    }
    with solution_path.open("w",encoding="utf-8") as fp:
        json.dump(solution,fp,ensure_ascii=False,indent=2)

    manifest={
        "problem":pool["problem"],
        "problem_file":str(problem_path),
        "K":int(pool["K"]),
        "scenario":"S0",
        "R0":r0,
        "baseline_avg_cost":avg_cost,
        "baseline_total_cost":total_cost,
        "selected_candidate_ids":[int(i) for i in selected],
        "s0_bike_availability":"non-binding",
        "candidate_pool_file":str(pool_path),
        "n_candidates":int(pool["n_candidates"]),
        "solver_backend":"scipy-milp",
        "solve_time_sec":float(solve_time),
        "pool_generation_sec":float(pool["pool_generation_sec"]),
        "workforce_policy":"S0-fixed",
        "equity_population":"active riders only",
    }
    with manifest_path.open("w",encoding="utf-8") as fp:
        json.dump(manifest,fp,ensure_ascii=False,indent=2)

    print(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(f"S0 solution: {solution_path}")
    print(f"Workforce manifest: {manifest_path}")
    print(f"Candidate pool: {pool_path}")


if __name__=="__main__":
    main()
