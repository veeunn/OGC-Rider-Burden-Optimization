"""Command-line runner for the supplied OGC baseline.

The default SciPy backend reproduces the baseline set-partitioning model without
requiring a commercial solver license.

Research-specific options
-------------------------
--bike-only
    Disable WALK/CAR.
--bike-availability N
    Explicit BIKE availability upper bound.
--fixed-active-riders R
    Require exactly R selected bundles/active riders. This is intended for
    S1-S3 after R0 has been determined by S0.
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


def run_problem(
    problem_path: str | Path,
    *,
    timelimit: float = 60.0,
    solver: str = "scipy",
    bike_only: bool = False,
    bike_availability: int | None = None,
    fixed_active_riders: int | None = None,
) -> dict:
    problem_path = Path(problem_path)
    with problem_path.open("r", encoding="utf-8") as f:
        prob = json.load(f)

    K = int(prob["K"])
    orders, riders, dist = build_objects(prob, bike_only, bike_availability)

    if solver == "scipy":
        from myalgorithm_scipy import algorithm
    elif solver == "gurobi":
        if fixed_active_riders is not None:
            raise ValueError(
                "--fixed-active-riders is currently implemented in the SciPy backend. "
                "Use --solver scipy for S1-S3 workforce-fixed runs."
            )
        from myalgorithm import algorithm
    else:
        raise ValueError(f"Unsupported solver backend: {solver}")

    t0 = time.time()
    if solver == "scipy":
        solution = algorithm(
            K, orders, riders, dist, timelimit,
            fixed_num_riders=fixed_active_riders,
        )
    else:
        solution = algorithm(K, orders, riders, dist, timelimit)
    elapsed = time.time() - t0

    # Independent re-evaluation with fresh objects, matching Yong_alg_test.py.
    orders, riders, dist = build_objects(prob, bike_only, bike_availability)
    checked = solution_check(K, orders, riders, dist, solution)
    checked["time"] = elapsed
    checked["timelimit_exception"] = elapsed > timelimit + 1
    checked["exception"] = None
    checked["prob_name"] = prob.get("name", problem_path.stem)
    checked["prob_file"] = str(problem_path)
    checked["K"] = K
    checked["analysis_scope"] = "BIKE-only" if bike_only else "original mixed-mode"
    checked["solver_backend"] = solver
    checked["bike_availability_override"] = bike_availability
    checked["fixed_active_riders"] = fixed_active_riders
    return checked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, help="Path to an OGC JSON instance")
    ap.add_argument("--timelimit", type=float, default=60.0)
    ap.add_argument("--solver", choices=["scipy", "gurobi"], default="scipy")
    ap.add_argument("--save", default=None, help="Optional JSON output path")
    ap.add_argument("--bike-only", action="store_true")
    ap.add_argument("--bike-availability", type=int, default=None)
    ap.add_argument("--fixed-active-riders", type=int, default=None)
    args = ap.parse_args()

    checked = run_problem(
        args.problem,
        timelimit=args.timelimit,
        solver=args.solver,
        bike_only=args.bike_only,
        bike_availability=args.bike_availability,
        fixed_active_riders=args.fixed_active_riders,
    )

    print(json.dumps(checked, ensure_ascii=False, indent=2))
    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(checked, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
