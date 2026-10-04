"""Command-line runner for the supplied OGC baseline.

Examples
--------
python run_baseline.py --problem 01_data/test/TEST_K50_1.json --timelimit 60
python run_baseline.py --problem 01_data/stage1/STAGE1_2.json --timelimit 100 --save 05_results/raw/STAGE1_2_baseline.json
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "02_baseline" / "runnable"
sys.path.insert(0, str(BASELINE))

import numpy as np
from util import Order, Rider, solution_check
from myalgorithm import algorithm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, help="Path to an OGC JSON instance")
    ap.add_argument("--timelimit", type=float, default=60.0)
    ap.add_argument("--save", default=None, help="Optional JSON output path")
    args = ap.parse_args()

    problem_path = Path(args.problem)
    with problem_path.open("r", encoding="utf-8") as f:
        prob = json.load(f)

    K = prob["K"]
    orders = [Order(x) for x in prob["ORDERS"]]
    riders = [Rider(x) for x in prob["RIDERS"]]
    dist = np.asarray(prob["DIST"])

    for r in riders:
        r.T = np.round(dist / r.speed + r.service_time)

    t0 = time.time()
    solution = algorithm(K, orders, riders, dist, args.timelimit)
    elapsed = time.time() - t0

    # Recreate clean objects before independent evaluation, matching Yong_alg_test.py.
    orders = [Order(x) for x in prob["ORDERS"]]
    riders = [Rider(x) for x in prob["RIDERS"]]
    for r in riders:
        r.T = np.round(dist / r.speed + r.service_time)

    checked = solution_check(K, orders, riders, dist, solution)
    checked["time"] = elapsed
    checked["timelimit_exception"] = elapsed > args.timelimit + 1
    checked["exception"] = None
    checked["prob_name"] = prob.get("name", problem_path.stem)
    checked["prob_file"] = str(problem_path)

    print(json.dumps(checked, ensure_ascii=False, indent=2))

    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(checked, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
