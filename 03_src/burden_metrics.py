"""Rider burden and inequality metrics for S1-S3.

This module intentionally keeps the three burden dimensions separate.
No composite rider-burden index is constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping
import numpy as np


@dataclass(frozen=True)
class RiderBurden:
    rider_id: str
    order_count: int
    active_route_duration_sec: float
    waiting_time_sec: float


def gini(values: Iterable[float]) -> float:
    """Return the Gini coefficient for non-negative burden values.

    If all values are zero, equity is perfect and 0.0 is returned.
    """
    x = np.asarray(list(values), dtype=float)
    if x.size == 0:
        raise ValueError("At least one value is required.")
    if np.any(x < 0):
        raise ValueError("Gini requires non-negative burden values.")
    total = float(x.sum())
    if total == 0.0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1, dtype=float)
    return float((2.0 * np.sum(idx * x) / (n * total)) - (n + 1.0) / n)


def summary(values: Iterable[float]) -> dict[str, float]:
    x = np.asarray(list(values), dtype=float)
    if x.size == 0:
        raise ValueError("At least one value is required.")
    mean = float(x.mean())
    sd = float(x.std(ddof=0))
    return {
        "n_riders": float(x.size),
        "mean": mean,
        "min": float(x.min()),
        "max": float(x.max()),
        "std": sd,
        "range": float(x.max() - x.min()),
        "gini": gini(x),
        "cv": float(sd / mean) if mean != 0.0 else 0.0,
    }


def metric_vector(
    burdens: Iterable[RiderBurden],
    scenario: str,
) -> np.ndarray:
    """Extract the rider-level burden vector for S1, S2, or S3."""
    b = list(burdens)
    s = scenario.upper()
    if s == "S1":
        return np.asarray([x.order_count for x in b], dtype=float)
    if s == "S2":
        return np.asarray([x.active_route_duration_sec for x in b], dtype=float)
    if s == "S3":
        return np.asarray([x.waiting_time_sec for x in b], dtype=float)
    raise ValueError("scenario must be one of S1, S2, S3")


def equity_metrics(
    burdens: Iterable[RiderBurden],
    scenario: str,
) -> dict[str, float]:
    return summary(metric_vector(burdens, scenario))


def objective_value(
    burdens: Iterable[RiderBurden],
    scenario: str,
    inequality: str = "gini",
) -> float:
    """Return a candidate second-objective value.

    The research has not yet frozen the final inequality function.
    This helper supports transparent comparison before that decision.
    """
    stats = equity_metrics(burdens, scenario)
    key = inequality.lower()
    aliases = {
        "sd": "std",
        "standard_deviation": "std",
        "max": "max",
        "range": "range",
        "gini": "gini",
        "cv": "cv",
    }
    if key not in aliases:
        raise ValueError(f"Unsupported inequality metric: {inequality}")
    return float(stats[aliases[key]])
