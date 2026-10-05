"""Run S1-S3 fixed-workforce NSGA-II experiments.

Each equity scenario inherits the exact S0 route selection as an initial
solution. This guarantees that the cost-optimal baseline is present in the
search population and provides the correct within-dimension equity reference.
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
from nsga2_solver import solve, inequality


def _solution_from_x(pool: dict, x: np.ndarray):
    bundles=[]
    for idx in np.flatnonzero(x > 0):
        b=pool["candidates"][int(idx)]
        bundles.append(["BIKE", b["shop_seq"], b["dlv_seq"]])
    return bundles


def _metric_field(scenario: str) -> str:
    return {
        "S1":"order_count",
        "S2":"active_route_duration_sec",
        "S3":"waiting_time_sec",
    }[scenario]


def _burdens(pool: dict, x: np.ndarray, scenario: str):
    field=_metric_field(scenario)
    return np.asarray(
        [float(pool["candidates"][int(i)][field]) for i in np.flatnonzero(x > 0)],
        dtype=float,
    )


def _burden_summary(values: np.ndarray) -> dict:
    if values.size == 0:
        raise ValueError("No active-rider burdens.")
    mean=float(np.mean(values))
    std=float(np.std(values,ddof=0))
    zeros=int(np.sum(values == 0))
    return {
        "n_riders":int(values.size),
        "mean":mean,
        "min":float(np.min(values)),
        "max":float(np.max(values)),
        "std":std,
        "range":float(np.max(values)-np.min(values)),
        "gini":float(inequality(values,"gini")),
        "cv":float(std/mean) if mean != 0 else 0.0,
        "zero_burden_riders":zeros,
        "zero_burden_share":float(zeros/values.size),
    }


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
    denom=float(np.linalg.norm(ab))
    if denom==0:
        return int(np.argmin(z.sum(axis=1)))
    # Perpendicular distance to the line joining the two normalized extremes.
    d=[abs(ab[0]*(p-a)[1]-ab[1]*(p-a)[0])/denom for p in z]
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

    selected_ids=manifest.get("selected_candidate_ids")
    if not selected_ids:
        raise ValueError(
            "Workforce manifest lacks S0 selected_candidate_ids. "
            "Re-run S0 with the current code before S1-S3."
        )

    x0=np.zeros(len(pool["candidates"]),dtype=np.int8)
    x0[np.asarray(selected_ids,dtype=int)]=1
    if int(x0.sum()) != r0:
        raise ValueError("S0 selected route count does not equal R0.")

    baseline_burdens=_burdens(pool,x0,scenario)
    baseline_ineq=float(inequality(baseline_burdens,args.metric))
    baseline_burden_summary=_burden_summary(baseline_burdens)

    result=solve(
        pool,
        scenario=scenario,
        r0=r0,
        metric=args.metric,
        population_size=args.population_size,
        generations=args.generations,
        seed=args.seed,
        repair_time_limit=args.repair_time_limit,
        initial_solutions=[x0],
    )

    baseline_cost=float(manifest["baseline_avg_cost"])
    pareto=[]
    for i in result.pareto_indices:
        x=result.population[i]
        cost,ineq=result.objectives[i]
        burdens=_burdens(pool,x,scenario)
        pof=((float(cost)-baseline_cost)/baseline_cost*100.0) if baseline_cost != 0 else None
        improvement=((baseline_ineq-float(ineq))/baseline_ineq*100.0) if baseline_ineq != 0 else None
        pareto.append({
            "population_index":int(i),
            "avg_cost":float(cost),
            "inequality":float(ineq),
            "price_of_fairness_pct":pof,
            "equity_improvement_pct_vs_s0":improvement,
            "is_s0_baseline":bool(np.array_equal(x,x0)),
            "selected_riders":int(x.sum()),
            "selected_candidate_ids":[int(j) for j in np.flatnonzero(x > 0)],
            "burdens":[float(v) for v in burdens],
            "burden_summary":_burden_summary(burdens),
            "bundles":_solution_from_x(pool,x),
        })

    pareto=sorted(pareto,key=lambda d:(d["avg_cost"],d["inequality"]))
    knee=None
    lowest_cost=None
    lowest_inequality=None
    if pareto:
        lowest_cost=min(pareto,key=lambda d:(d["avg_cost"],d["inequality"]))
        lowest_inequality=min(pareto,key=lambda d:(d["inequality"],d["avg_cost"]))
        k=_knee_index([(p["avg_cost"],p["inequality"]) for p in pareto])
        knee=pareto[k]

    out={
        "scenario":scenario,
        "problem":pool["problem"],
        "problem_file":args.problem,
        "candidate_pool_file":str(pool_path),
        "R0":r0,
        "workforce_policy":"S0-fixed",
        "equity_population":"active riders only",
        "burden_field":_metric_field(scenario),
        "inequality_metric":args.metric,
        "population_size":args.population_size,
        "generations":args.generations,
        "seed":args.seed,
        "baseline_avg_cost":baseline_cost,
        "baseline_inequality":baseline_ineq,
        "baseline_burden_summary":baseline_burden_summary,
        "n_candidates":pool["n_candidates"],
        "candidate_counts_by_bundle_size":pool["candidate_counts_by_bundle_size"],
        "n_pareto":len(pareto),
        "repair_failures":int(result.repair_failures),
        "variation_failures":int(result.variation_failures),
        "pareto":pareto,
        "lowest_cost_point":lowest_cost,
        "knee_point":knee,
        "lowest_inequality_point":lowest_inequality,
    }

    out_dir=Path(args.output_dir)/scenario
    out_dir.mkdir(parents=True,exist_ok=True)
    out_path=out_dir/f"{Path(args.problem).stem}_{scenario}_seed{args.seed}.json"
    with out_path.open("w",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)

    def compact(p):
        if p is None:
            return None
        return {
            "avg_cost":p["avg_cost"],
            "inequality":p["inequality"],
            "equity_improvement_pct_vs_s0":p["equity_improvement_pct_vs_s0"],
            "price_of_fairness_pct":p["price_of_fairness_pct"],
            "is_s0_baseline":p["is_s0_baseline"],
        }

    print(json.dumps({
        "scenario":scenario,
        "problem":pool["problem"],
        "R0":r0,
        "n_candidates":pool["n_candidates"],
        "baseline_inequality":baseline_ineq,
        "baseline_zero_burden_share":baseline_burden_summary["zero_burden_share"],
        "n_pareto":len(pareto),
        "repair_failures":int(result.repair_failures),
        "variation_failures":int(result.variation_failures),
        "lowest_cost_point":compact(lowest_cost),
        "knee_point":compact(knee),
        "lowest_inequality_point":compact(lowest_inequality),
        "output":str(out_path),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
