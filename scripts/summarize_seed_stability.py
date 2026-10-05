"""Summarize Stage 1 NSGA-II seed stability and pooled Pareto frontiers."""
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
        obj=(p["avg_cost"],p["inequality"])
        if not any(j!=i and dominates((q["avg_cost"],q["inequality"]),obj) for j,q in enumerate(points)):
            keep.append(p)
    # de-duplicate identical objective pairs
    out=[]
    seen=set()
    for p in sorted(keep,key=lambda x:(x["avg_cost"],x["inequality"])):
        key=(round(float(p["avg_cost"]),12),round(float(p["inequality"]),12))
        if key not in seen:
            seen.add(key); out.append(p)
    return out

def knee_index(points):
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
    return (float(np.mean(xs)),float(np.std(xs,ddof=0)))

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
            "R0":d["R0"],"baseline_gini":d["baseline_inequality"],
            "n_pareto":d["n_pareto"],"repair_failures":d.get("repair_failures"),
            "variation_failures":d.get("variation_failures"),
            "knee_improvement_pct":knee.get("equity_improvement_pct_vs_s0"),
            "knee_pof_pct":knee.get("price_of_fairness_pct"),
            "lowest_improvement_pct":low.get("equity_improvement_pct_vs_s0"),
            "lowest_pof_pct":low.get("price_of_fairness_pct"),
        }
        per_seed.append(row)
        for pt in d.get("pareto",[]):
            q=dict(pt)
            q["seed"]=d["seed"]
            grouped[(d["problem"],d["scenario"])].append(q)

    per_seed.sort(key=lambda r:(r["instance"],r["scenario"],r["seed"]))
    fields=list(per_seed[0].keys()) if per_seed else []
    if per_seed:
        with (out/"seed_level_results.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(per_seed)

    summary=[]
    for key,pts in sorted(grouped.items()):
        inst,scen=key
        rows=[r for r in per_seed if r["instance"]==inst and r["scenario"]==scen]
        pooled=nondominated(pts)
        knee=pooled[knee_index(pooled)] if pooled else {}
        low=min(pooled,key=lambda x:(x["inequality"],x["avg_cost"])) if pooled else {}
        kim,kis=mean_sd([r["knee_improvement_pct"] for r in rows])
        kpm,kps=mean_sd([r["knee_pof_pct"] for r in rows])
        lim,lis=mean_sd([r["lowest_improvement_pct"] for r in rows])
        lpm,lps=mean_sd([r["lowest_pof_pct"] for r in rows])
        summary.append({
            "instance":inst,"scenario":scen,"n_seeds":len(rows),
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
        sf=list(summary[0].keys())
        with (out/"seed_stability_summary.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=sf); w.writeheader(); w.writerows(summary)

    md=["# Stage 1 seed stability (population=80, generations=100)","",
        f"- Seed-level scenario rows: {len(per_seed)}",
        f"- Expected rows for 3 instances × 3 scenarios × 5 seeds: 45","",
        "| Instance | Scenario | Knee improvement mean±SD | Knee PoF mean±SD | Pooled knee improvement | Pooled knee PoF | Pooled lowest-Gini improvement |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    def pm(m,s):
        return "" if m is None else f"{m:.2f}% ± {s:.2f}%"
    def pct(x):
        return "" if x is None else f"{x:.2f}%"
    for r in summary:
        md.append(f"| {r['instance']} | {r['scenario']} | {pm(r['knee_improvement_mean'],r['knee_improvement_sd'])} | {pm(r['knee_pof_mean'],r['knee_pof_sd'])} | {pct(r['pooled_knee_improvement_pct'])} | {pct(r['pooled_knee_pof_pct'])} | {pct(r['pooled_lowest_improvement_pct'])} |")
    (out/"seed_stability_summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))

if __name__=="__main__": main()
