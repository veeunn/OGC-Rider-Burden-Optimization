"""Validate OGC JSON files without running the optimizer."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def validate(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        p = json.load(f)
    k = int(p["K"])
    assert len(p["ORDERS"]) == k, (path, "ORDERS length", len(p["ORDERS"]), k)
    assert len(p["RIDERS"]) >= 1, (path, "RIDERS empty")
    dist = np.asarray(p["DIST"])
    assert dist.shape == (2*k, 2*k), (path, "DIST shape", dist.shape, (2*k,2*k))
    rider_types = {r[0] for r in p["RIDERS"]}
    assert "BIKE" in rider_types, (path, "BIKE missing")
    return {"name": p.get("name", path.stem), "K": k, "riders": sorted(rider_types)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    args=ap.parse_args()
    for raw in args.paths:
        path=Path(raw)
        info=validate(path)
        print(f"OK {path}: {info}")


if __name__=="__main__":
    main()
