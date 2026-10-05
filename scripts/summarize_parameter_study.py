"""Summarize Stage 1 NSGA-II parameter-study artifacts."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def pf(point):
    if not point:
        return {"knee_gini":None,"knee_improvement_pct":None,"knee_pof_pct":None}
    return {
        "knee_gini":point.get("inequality"),
        "knee_improvement_pct":point.get("equity_improvement_pct_vs_s0"),
        "knee_pof_pct":point.get("price_of_fairness_pct"),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    root=Path(a.root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for p in root.rglob("*_S[123]_seed*.json"):
        d=json.loads(p.read_text(encoding="utf-8"))
        r={
            "instance":d["problem"],"scenario":d["scenario"],
            "population_size":d["population_size"],"generations":d["generations"],
            "seed":d["seed"],"R0":d["R0"],"baseline_gini":d["baseline_inequality"],
            "n_pareto":d["n_pareto"],"repair_failures":d.get("repair_failures"),
            "variation_failures":d.get("variation_failures"),
        }
        r.update(pf(d.get("knee_point")))
        low=d.get("lowest_inequality_point") or {}
        r["lowest_gini"]=low.get("inequality")
        r["lowest_improvement_pct"]=low.get("equity_improvement_pct_vs_s0")
        r["lowest_pof_pct"]=low.get("price_of_fairness_pct")
        rows.append(r)
    rows.sort(key=lambda r:(r["instance"],r["scenario"],r["population_size"],r["generations"],r["seed"]))
    fields=["instance","scenario","population_size","generations","seed","R0","baseline_gini","n_pareto","repair_failures","variation_failures","knee_gini","knee_improvement_pct","knee_pof_pct","lowest_gini","lowest_improvement_pct","lowest_pof_pct"]
    with (out/"parameter_study.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    md=["# Stage 1 NSGA-II parameter study","",f"- Completed scenario rows: {len(rows)}","",
        "| Instance | Scenario | Pop | Gen | Pareto | Knee improvement | Knee PoF | Lowest-Gini improvement | Lowest-Gini PoF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        fmt=lambda x:"" if x is None else f"{x:.2f}%"
        md.append(f"| {r['instance']} | {r['scenario']} | {r['population_size']} | {r['generations']} | {r['n_pareto']} | {fmt(r['knee_improvement_pct'])} | {fmt(r['knee_pof_pct'])} | {fmt(r['lowest_improvement_pct'])} | {fmt(r['lowest_pof_pct'])} |")
    (out/"parameter_study.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))
if __name__=="__main__": main()
