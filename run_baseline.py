"""Command-line runner for the supplied OGC baseline.

Examples
--------
Original mixed-mode baseline:
  python run_baseline.py --problem 01_data/test/TEST_K50_1.json --timelimit 60

BIKE-only with original BIKE availability:
  python run_baseline.py --problem 01_data/stage1/STAGE1_2.json --timelimit 100 --bike-only

BIKE-only with an explicit availability override:
  python run_baseline.py --problem 01_data/stage1/STAGE1_2.json --timelimit 100 --bike-only --bike-availability 100
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


def build_objects(prob: dict, bike_only: bool, bike_availability: int | None):
    orders = [Order(x) for x in prob["ORDERS"]]
    riders = [Rider(x) for x in prob["RIDERS"]]

    if bike_only:
        for r in riders:
            if r.type != "BIKE":
                r.available_number = 0
        if bike_availability is not None:
            for r in riders:
                if r.type == "BIKE":
                    r.available_number = bike_availability

    dist = np.asarray(prob["DIST"])
    for r in riders:
        r.T = np.round(dist / r.speed + r.service_time)
    return orders, riders, dist


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, help="Path to an OGC JSON instance")
    ap.add_argument("--timelimit", type=float, default=60.0)
    ap.add_argument("--solver", choices=["scipy","gurobi"], default="scipy",
                    help="Final set-partitioning backend. scipy is license-free.")
    ap.add_argument("--save", default=None, help="Optional JSON output path")
    ap.add_argument("--bike-only", action="store_true",
                    help="Set WALK/CAR availability to zero.")
    ap.add_argument("--bike-availability", type=int, default=None,
                    help="Optional BIKE availability override; use only when methodologically intended.")
    args = ap.parse_args()

    problem_path = Path(args.problem)
    with problem_path.open("r", encoding="utf-8") as f:
        prob = json.load(f)

    K = prob["K"]
    orders, riders, dist = build_objects(prob, args.bike_only, args.bike_availability)

    if args.solver == "scipy":
        from myalgorithm_scipy import algorithm
    else:
        from myalgorithm import algorithm

    t0 = time.time()
    solution = algorithm(K, orders, riders, dist, args.timelimit)
    elapsed = time.time() - t0

    # Independent re-evaluation with fresh objects, matching Yong_alg_test.py.
    orders, riders, dist = build_objects(prob, args.bike_only, args.bike_availability)
    checked = solution_check(K, orders, riders, dist, solution)
    checked["time"] = elapsed
    checked["timelimit_exception"] = elapsed > args.timelimit + 1
    checked["exception"] = None
    checked["prob_name"] = prob.get("name", problem_path.stem)
    checked["prob_file"] = str(problem_path)
    checked["analysis_scope"] = "BIKE-only" if args.bike_only else "original mixed-mode"
    checked["solver_backend"] = args.solver
    checked["bike_availability_override"] = args.bike_availability

    print(json.dumps(checked, ensure_ascii=False, indent=2))

    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(checked, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
