"""Compare original tensor bundle generation with memory-safe generation.

Use on small instances only. The script checks bundle counts and the selected
(shop_seq, dlv_seq, distance) candidate for sizes 1-3.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "02_baseline" / "runnable"
SRC = ROOT / "03_src"
sys.path.insert(0, str(BASELINE))
sys.path.insert(0, str(SRC))

from util import Order, Rider
from myalgorithm_scipy import bundling_123 as original_bundling_123
from memory_safe_bundling import bundling_123_bike_memory_safe


def signature(bundle):
    return (
        tuple(map(int, bundle.shop_seq)),
        tuple(map(int, bundle.dlv_seq)),
        float(bundle.total_dist),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True)
    ap.add_argument("--batch-size", type=int, default=100_000)
    args = ap.parse_args()

    path = Path(args.problem)
    data = json.loads(path.read_text(encoding="utf-8"))
    K = int(data["K"])
    orders = [Order(x) for x in data["ORDERS"]]
    bike_info = next(x for x in data["RIDERS"] if x[0] == "BIKE")
    bike = Rider(list(bike_info))
    dist = np.asarray(data["DIST"])
    bike.T = np.round(dist / bike.speed + bike.service_time)

    ready = np.asarray([o.ready_time for o in orders])
    deadline = np.asarray([o.deadline for o in orders])
    volume = np.asarray([o.volume for o in orders])

    original, original_triplets = original_bundling_123(
        K, orders, [bike], ready, deadline, volume, dist
    )
    safe, safe_triplets, diagnostics = bundling_123_bike_memory_safe(
        K,
        orders,
        bike,
        ready,
        deadline,
        volume,
        dist,
        batch_size=args.batch_size,
    )

    report = {"problem": data.get("name", path.stem), "K": K, "diagnostics": diagnostics}
    ok = True

    for size_idx, size in enumerate((1, 2, 3)):
        old = [signature(b) for b in original[size_idx]["BIKE"]]
        new = [signature(b) for b in safe[size_idx]["BIKE"]]
        same = old == new
        report[f"size{size}"] = {
            "original_count": len(old),
            "memory_safe_count": len(new),
            "exact_ordered_match": same,
        }
        ok &= same

    triplet_sets_match = original_triplets["BIKE"] == safe_triplets["BIKE"]
    report["triplet_sets_match"] = triplet_sets_match
    ok &= triplet_sets_match
    report["all_checks_passed"] = ok

    print(json.dumps(report, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
