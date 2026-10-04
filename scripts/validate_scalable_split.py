from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"03_src"))
from candidate_pool import generate_bike_candidate_pool
from set_partition import cost_optimal_selection
from scalable_split_solver import BikeSplitProblem,solve_s0_ga

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--problem",required=True); ap.add_argument("--population-size",type=int,default=24); ap.add_argument("--generations",type=int,default=30); ap.add_argument("--seed",type=int,default=0); a=ap.parse_args()
    p=Path(a.problem); pool=generate_bike_candidate_pool(p,include_size4=True); x,res=cost_optimal_selection(pool,time_limit=60)
    sel=np.flatnonzero(x>0); exact=sum(pool["candidates"][int(i)]["cost"] for i in sel)/pool["K"]
    exact_perm=np.asarray([oid for i in sel for oid in pool["candidates"][int(i)]["shop_seq"]],dtype=np.int32)
    prob=BikeSplitProblem(p,max_route_size=4); seeded=prob.decode_cost(exact_perm); seeded_check=prob.validate_decoded(seeded)
    ga,diag=solve_s0_ga(prob,population_size=a.population_size,generations=a.generations,seed=a.seed); ga_check=prob.validate_decoded(ga)
    report={"problem":p.stem,"K":pool["K"],"exact":{"avg_cost":exact,"R0":int(len(sel))},"split_seeded":{"avg_cost":seeded.avg_cost,"R0":seeded.R0,"gap_pct":(seeded.avg_cost-exact)/exact*100,"validated":seeded_check},"split_ga":{"avg_cost":ga.avg_cost,"R0":ga.R0,"gap_pct":(ga.avg_cost-exact)/exact*100,"validated":ga_check,"diagnostics":diag}}
    print(json.dumps(report,indent=2))
    if not seeded_check.get("feasible") or seeded.avg_cost>exact+1e-6: raise SystemExit(1)
if __name__=="__main__": main()
