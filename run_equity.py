"""Run S1-S3 fixed-workforce NSGA-II experiments.

Workflow
--------
1. Read S0 workforce manifest and inherit R0.
2. Generate/load the same BIKE candidate bundle pool.
3. Run NSGA-II with exact-cover + exact-R0 repair.
4. Save full population, Pareto set, and selected summary points.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"03_src"
sys.path.insert(0,str(SRC))

from candidate_pool import generate_bike_candidate_pool, load_candidate_pool, save_candidate_pool
from workforce import load_workforce_manifest
from nsga2_solver import solve


def _solution_from_x(pool: dict, x: np.ndarray):
    bundles=[]
    for idx in np.flatnonzero(x > 0):
        b=pool["candidates"][int(idx)]
        bundles.append(["BIKE", b["shop_seq"], b["dlv_seq"]])
    return bundles


def _burdens(pool: dict, x: np.ndarray, scenario: str):
    field={
        "S1":"order_count",
        "S2":"active_route_duration_sec",
        "S3":"waiting_time_sec",
    }[scenario]
    return [float(pool["candidates"][int(i)][field]) for i in np.flatnonzero(x > 0)]


def _knee_index(points):
    if len(points) <= 2:
        return 0
    arr=np.asarray(points,dtype=float)
    mins=arr.min(axis=0)
    maxs=arr.max(axis=0)
    span=np.where(maxs>mins,maxs-mins,1.0)
    z=(arr-mins)/span
    a=z[np.argmin(z[:,0])]
    b=z[np.argmin(z[:,1])]
    ab=b-a
    denom=np.linalg.norm(ab)
    if denom==0:
        return int(np.argmin(z.sum(axis=1)))
    d=[]
    for p in z:
        d.append(abs(np.cross(ab,p-a))/denom)
    return int(np.argmax(d))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario",required=True,choices=["S1","S2","S3"])
    ap.add_argument("--problem",required=True)
    ap.add_argument("--workforce",required=True)
    ap.add_argument("--candidate-pool",default=None)
    ap.add_argument("--output-dir",default="05_results")
    ap.add_argument("--metric",default="gini",choices=["gini","std","range","max","cv"])
    ap.add_argument("--population-size",type=int,default=40)
    ap.add_argument("--generations",type=int,default=50)
    ap.add_argument("--seed",type=int,default=0)
    ap.add_argument("--repair-time-limit",type=float,default=10.0)
    ap.add_argument("--pool-time-limit",type=float,default=None)
    args=ap.parse_args()

    scenario=args.scenario.upper()
    manifest=load_workforce_manifest(args.workforce)
    r0=int(manifest["R0"])

    if args.candidate_pool:
        pool=load_candidate_pool(args.candidate_pool)
        pool_path=Path(args.candidate_pool)
    else:
        pool=generate_bike_candidate_pool(
            args.problem,
            include_size4=True,
            generation_time_limit=args.pool_time_limit,
        )
        pool_dir=Path(args.output_dir)/"candidate_pools"
        pool_dir.mkdir(parents=True,exist_ok=True)
        pool_path=pool_dir/f"{Path(args.problem).stem}_bike_pool.json"
        save_candidate_pool(pool,pool_path)

    if int(pool["K"]) != int(manifest["K"]):
        raise ValueError("Candidate pool K and workforce manifest K do not match.")
    if str(pool["problem"]) != str(manifest["problem"]):
        raise ValueError("Candidate pool problem and workforce manifest problem do not match.")

    result=solve(
        pool,
        scenario=scenario,
        r0=r0,
        metric=args.metric,
        population_size=args.population_size,
        generations=args.generations,
        seed=args.seed,
        repair_time_limit=args.repair_time_limit,
    )

    pareto=[]
    for i in result.pareto_indices:
        x=result.population[i]
        cost,ineq=result.objectives[i]
        pareto.append({
            "population_index":int(i),
            "avg_cost":float(cost),
            "inequality":float(ineq),
            "selected_riders":int(x.sum()),
            "selected_candidate_ids":[int(j) for j in np.flatnonzero(x > 0)],
            "burdens":_burdens(pool,x,scenario),
            "bundles":_solution_from_x(pool,x),
        })

    pareto=sorted(pareto,key=lambda d:(d["avg_cost"],d["inequality"]))
    knee=None
    if pareto:
        k=_knee_index([(p["avg_cost"],p["inequality"]) for p in pareto])
        knee=pareto[k]

    baseline_cost=float(manifest["baseline_avg_cost"])
    for p in pareto:
        p["price_of_fairness_pct"]=(
            (p["avg_cost"]-baseline_cost)/baseline_cost*100.0
            if baseline_cost != 0 else None
        )

    out={
        "scenario":scenario,
        "problem":pool["problem"],
        "problem_file":args.problem,
        "candidate_pool_file":str(pool_path),
        "R0":r0,
        "workforce_policy":"S0-fixed",
        "equity_population":"active riders only",
        "inequality_metric":args.metric,
        "population_size":args.population_size,
        "generations":args.generations,
        "seed":args.seed,
        "baseline_avg_cost":baseline_cost,
        "n_candidates":pool["n_candidates"],
        "candidate_counts_by_bundle_size":pool["candidate_counts_by_bundle_size"],
        "n_pareto":len(pareto),
        "pareto":pareto,
        "knee_point":knee,
    }

    out_dir=Path(args.output_dir)/scenario
    out_dir.mkdir(parents=True,exist_ok=True)
    out_path=out_dir/f"{Path(args.problem).stem}_{scenario}_seed{args.seed}.json"
    with out_path.open("w",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)

    print(json.dumps({
        "scenario":scenario,
        "problem":pool["problem"],
        "R0":r0,
        "n_candidates":pool["n_candidates"],
        "n_pareto":len(pareto),
        "knee_point":None if knee is None else {
            "avg_cost":knee["avg_cost"],
            "inequality":knee["inequality"],
            "price_of_fairness_pct":knee["price_of_fairness_pct"],
        },
        "output":str(out_path),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
