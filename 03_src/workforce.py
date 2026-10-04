"""Helpers for enforcing the S0-fixed workforce policy."""
from __future__ import annotations

import json
from pathlib import Path


def load_workforce_manifest(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    required = {"problem", "K", "R0", "baseline_avg_cost", "workforce_policy"}
    missing = required.difference(manifest)
    if missing:
        raise ValueError(f"Workforce manifest is missing fields: {sorted(missing)}")
    if manifest["workforce_policy"] != "S0-fixed":
        raise ValueError("Expected workforce_policy='S0-fixed'.")
    if int(manifest["R0"]) <= 0:
        raise ValueError("R0 must be positive.")
    return manifest


def fixed_rider_count(path: str | Path) -> int:
    return int(load_workforce_manifest(path)["R0"])
