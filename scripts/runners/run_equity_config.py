"""Shared loader for S1-S3 experiment configuration.

This script does not yet perform NSGA-II optimization. It guarantees that every
equity-aware scenario inherits exactly the S0 workforce size R0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "03_src"
sys.path.insert(0, str(SRC))

from workforce import load_workforce_manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=["S1", "S2", "S3"])
    ap.add_argument("--workforce", required=True, help="S0 workforce manifest JSON")
    args = ap.parse_args()

    manifest = load_workforce_manifest(args.workforce)
    metric = {
        "S1": "order_count",
        "S2": "active_route_duration",
        "S3": "waiting_time",
    }[args.scenario]

    config = {
        "scenario": args.scenario,
        "problem": manifest["problem"],
        "K": manifest["K"],
        "R0": manifest["R0"],
        "fixed_active_riders": manifest["R0"],
        "burden_metric": metric,
        "workforce_policy": "S0-fixed",
        "baseline_avg_cost": manifest["baseline_avg_cost"],
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
