"""Summarize final Stage 1 multi-seed NSGA-II experiments."""
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np

def dominates(a,b):
    return (a[0] <= b[0] and a[1] <= b[1]) and (a[0] < b[0] or a[1] < b[1])

def nondominated(points):
    keep=[]
    for i,p in enumerate(points):
        obj=(float(p["avg_cost"]),float(p["inequality"]))
        if not any(j!=i and dominates((float(q["avg_cost"]),float(q["inequality"])),obj) for j,q in enumerate(points)):
            keep.append(p)
    out=[]; seen=set()
    for p in sorted(keep,key=lambda x:(float(x["avg_cost"]),float(x["inequality"]))):
        key=(round(float(p["avg_cost"]),12),round(float(p["inequality"]),12))
        if key not in seen:
            seen.add(key); out.append(p)
    return out

def knee_index(points):
    if not points: return None
    if len(points)<=2: return 0
    arr=np.asarray([(p["avg_cost"],p["inequality"]) for p in points],dtype=float)
    mins=arr.min(axis=0); maxs=arr.max(axis=0)
    span=np.where(maxs>mins,maxs-mins,1.0)
    z=(arr-mins)/span
    a=z[np.argmin(z[:,0])]; b=z[np.argmin(z[:,1])]
    ab=b-a; denom=float(np.linalg.norm(ab))
    if denom==0: return int(np.argmin(z.sum(axis=1)))
    d=[abs(ab[0]*(p-a)[1]-ab[1]*(p-a)[0])/denom for p in z]
    return int(np.argmax(d))

def mean_sd(xs):
    xs=[float(x) for x in xs if x is not None]
    if not xs: return (None,None)
    return float(np.mean(xs)), float(np.std(xs,ddof=0))

def pct(x):
    return "" if x is None else f"{float(x):.2f}%"

def pm(m,s):
    return "" if m is None else f"{m:.2f}% ± {s:.2f}%"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    root=Path(a.root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    files=[]
    for p in root.rglob("*_S[123]_seed*.json"):
        try:
            d=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        files.append((p,d))

    per_seed=[]
    grouped=defaultdict(list)
    for p,d in files:
        knee=d.get("knee_point") or {}
        low=d.get("lowest_inequality_point") or {}
        row={
            "instance":d["problem"],"scenario":d["scenario"],"seed":d["seed"],
            "K":d.get("K"),"R0":d["R0"],"baseline_avg_cost":d["baseline_avg_cost"],
            "baseline_gini":d["baseline_inequality"],"n_candidates":d.get("n_candidates"),
            "n_pareto":d["n_pareto"],"repair_failures":d.get("repair_failures"),
            "variation_failures":d.get("variation_failures"),
            "knee_improvement_pct":knee.get("equity_improvement_pct_vs_s0"),
            "knee_pof_pct":knee.get("price_of_fairness_pct"),
            "lowest_improvement_pct":low.get("equity_improvement_pct_vs_s0"),
            "lowest_pof_pct":low.get("price_of_fairness_pct"),
        }
        per_seed.append(row)
        for pt in d.get("pareto",[]):
            q=dict(pt); q["seed"]=d["seed"]
            grouped[(d["problem"],d["scenario"])].append(q)

    per_seed.sort(key=lambda r:(r["instance"],r["scenario"],r["seed"]))
    if per_seed:
        with (out/"seed_level_results.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(per_seed[0].keys())); w.writeheader(); w.writerows(per_seed)

    summary=[]
    for (inst,scen),pts in sorted(grouped.items()):
        rows=[r for r in per_seed if r["instance"]==inst and r["scenario"]==scen]
        pooled=nondominated(pts)
        ki=knee_index(pooled)
        knee=pooled[ki] if ki is not None else {}
        low=min(pooled,key=lambda x:(x["inequality"],x["avg_cost"])) if pooled else {}
        kim,kis=mean_sd([r["knee_improvement_pct"] for r in rows])
        kpm,kps=mean_sd([r["knee_pof_pct"] for r in rows])
        lim,lis=mean_sd([r["lowest_improvement_pct"] for r in rows])
        lpm,lps=mean_sd([r["lowest_pof_pct"] for r in rows])
        summary.append({
            "instance":inst,"scenario":scen,"n_seeds":len(rows),
            "K":rows[0].get("K") if rows else None,"R0":rows[0]["R0"] if rows else None,
            "baseline_gini":rows[0]["baseline_gini"] if rows else None,
            "knee_improvement_mean":kim,"knee_improvement_sd":kis,
            "knee_pof_mean":kpm,"knee_pof_sd":kps,
            "lowest_improvement_mean":lim,"lowest_improvement_sd":lis,
            "lowest_pof_mean":lpm,"lowest_pof_sd":lps,
            "pooled_n_pareto":len(pooled),
            "pooled_knee_improvement_pct":knee.get("equity_improvement_pct_vs_s0"),
            "pooled_knee_pof_pct":knee.get("price_of_fairness_pct"),
            "pooled_lowest_improvement_pct":low.get("equity_improvement_pct_vs_s0"),
            "pooled_lowest_pof_pct":low.get("price_of_fairness_pct"),
        })
        (out/f"{inst}_{scen}_pooled_pareto.json").write_text(
            json.dumps({"instance":inst,"scenario":scen,"pooled_pareto":pooled},ensure_ascii=False,indent=2),
            encoding="utf-8")

    if summary:
        with (out/"instance_scenario_summary.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

    scenario_summary=[]
    for scen in ["S1","S2","S3"]:
        rows=[r for r in summary if r["scenario"]==scen]
        if not rows: continue
        kim,kis=mean_sd([r["pooled_knee_improvement_pct"] for r in rows])
        kpm,kps=mean_sd([r["pooled_knee_pof_pct"] for r in rows])
        lim,lis=mean_sd([r["pooled_lowest_improvement_pct"] for r in rows])
        lpm,lps=mean_sd([r["pooled_lowest_pof_pct"] for r in rows])
        scenario_summary.append({
            "scenario":scen,"n_instances":len(rows),
            "pooled_knee_improvement_mean":kim,"pooled_knee_improvement_sd":kis,
            "pooled_knee_pof_mean":kpm,"pooled_knee_pof_sd":kps,
            "pooled_lowest_improvement_mean":lim,"pooled_lowest_improvement_sd":lis,
            "pooled_lowest_pof_mean":lpm,"pooled_lowest_pof_sd":lps,
        })
    if scenario_summary:
        with (out/"scenario_overall_summary.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(scenario_summary[0].keys())); w.writeheader(); w.writerows(scenario_summary)

    instances=sorted(set(r["instance"] for r in per_seed))
    seeds=sorted(set(int(r["seed"]) for r in per_seed))
    expected=len(instances)*3*len(seeds)
    md=[
        "# Stage 1 final experiment summary",
        "",
        "- Population: 80",
        "- Generations: 100",
        f"- Instances collected: {len(instances)}",
        f"- Seeds collected: {len(seeds)} ({', '.join(map(str,seeds))})",
        f"- Seed-level scenario rows: {len(per_seed)} / expected {expected}",
        "",
        "## Instance × scenario results",
        "",
        "| Instance | Scenario | Knee improvement mean±SD | Knee PoF mean±SD | Pooled knee improvement | Pooled knee PoF | Pooled lowest-Gini improvement |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        md.append(
            f"| {r['instance']} | {r['scenario']} | "
            f"{pm(r['knee_improvement_mean'],r['knee_improvement_sd'])} | "
            f"{pm(r['knee_pof_mean'],r['knee_pof_sd'])} | "
            f"{pct(r['pooled_knee_improvement_pct'])} | {pct(r['pooled_knee_pof_pct'])} | "
            f"{pct(r['pooled_lowest_improvement_pct'])} |"
        )
    md += ["","## Scenario-level aggregate","","| Scenario | N instances | Pooled-knee improvement mean±SD | Pooled-knee PoF mean±SD | Lowest-Gini improvement mean±SD | Lowest-Gini PoF mean±SD |","|---|---:|---:|---:|---:|---:|"]
    for r in scenario_summary:
        md.append(
            f"| {r['scenario']} | {r['n_instances']} | "
            f"{pm(r['pooled_knee_improvement_mean'],r['pooled_knee_improvement_sd'])} | "
            f"{pm(r['pooled_knee_pof_mean'],r['pooled_knee_pof_sd'])} | "
            f"{pm(r['pooled_lowest_improvement_mean'],r['pooled_lowest_improvement_sd'])} | "
            f"{pm(r['pooled_lowest_pof_mean'],r['pooled_lowest_pof_sd'])} |"
        )

    (out/"final_stage1_summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))

if __name__=="__main__":
    main()
