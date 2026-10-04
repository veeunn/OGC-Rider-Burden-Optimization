"""Run S0 followed by S1-S3 for one OGC instance."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("+", " ".join(map(str,cmd)), flush=True)
    subprocess.run(cmd,check=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--problem",required=True)
    ap.add_argument("--timelimit",type=float,default=60.0)
    ap.add_argument("--population-size",type=int,default=40)
    ap.add_argument("--generations",type=int,default=50)
    ap.add_argument("--seed",type=int,default=0)
    ap.add_argument("--metric",default="gini")
    ap.add_argument("--output-dir",default="05_results")
    args=ap.parse_args()

    py=sys.executable
    stem=Path(args.problem).stem
    s0dir=Path(args.output_dir)/"S0"

    run([py,"run_s0.py",
         "--problem",args.problem,
         "--solver","scipy",
         "--timelimit",str(args.timelimit),
         "--output-dir",str(s0dir)])

    workforce=s0dir/f"{stem}_workforce.json"

    for scenario in ["S1","S2","S3"]:
        run([py,"run_equity.py",
             "--scenario",scenario,
             "--problem",args.problem,
             "--workforce",str(workforce),
             "--output-dir",args.output_dir,
             "--population-size",str(args.population_size),
             "--generations",str(args.generations),
             "--seed",str(args.seed),
             "--metric",args.metric])


if __name__=="__main__":
    main()
