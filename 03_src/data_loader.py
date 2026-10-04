"""OGC 2024 JSON instance loader.

The field layout follows the supplied OGC problem description.
This module does not alter feasibility or optimization logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import numpy as np


@dataclass(frozen=True)
class RiderType:
    name: str
    speed_mps: float
    capacity: int
    variable_cost_per_100m: float
    fixed_cost: float
    service_time_sec: int
    availability: int


@dataclass(frozen=True)
class Order:
    order_id: int
    order_time_sec: int
    pickup_lat: float
    pickup_lon: float
    delivery_lat: float
    delivery_lon: float
    preparation_time_sec: int
    volume: int
    deadline_sec: int

    @property
    def ready_time_sec(self) -> int:
        return self.order_time_sec + self.preparation_time_sec


@dataclass(frozen=True)
class OGCInstance:
    name: str
    k: int
    riders: tuple[RiderType, ...]
    orders: tuple[Order, ...]
    dist_m: np.ndarray

    def bike(self) -> RiderType:
        matches = [r for r in self.riders if r.name.upper() == "BIKE"]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one BIKE rider type, found {len(matches)}")
        return matches[0]


def _parse_rider(row: list[Any]) -> RiderType:
    if len(row) != 7:
        raise ValueError(f"Unexpected RIDERS row length: {len(row)}")
    return RiderType(
        name=str(row[0]),
        speed_mps=float(row[1]),
        capacity=int(row[2]),
        variable_cost_per_100m=float(row[3]),
        fixed_cost=float(row[4]),
        service_time_sec=int(row[5]),
        availability=int(row[6]),
    )


def _parse_order(row: list[Any]) -> Order:
    if len(row) != 9:
        raise ValueError(f"Unexpected ORDERS row length: {len(row)}")
    return Order(
        order_id=int(row[0]),
        order_time_sec=int(row[1]),
        pickup_lat=float(row[2]),
        pickup_lon=float(row[3]),
        delivery_lat=float(row[4]),
        delivery_lon=float(row[5]),
        preparation_time_sec=int(row[6]),
        volume=int(row[7]),
        deadline_sec=int(row[8]),
    )


def load_instance(path: str | Path) -> OGCInstance:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    k = int(raw["K"])
    orders = tuple(_parse_order(row) for row in raw["ORDERS"])
    riders = tuple(_parse_rider(row) for row in raw["RIDERS"])
    dist = np.asarray(raw["DIST"], dtype=float)

    if len(orders) != k:
        raise ValueError(f"K={k}, but {len(orders)} orders were loaded.")
    if dist.shape != (2 * k, 2 * k):
        raise ValueError(
            f"DIST must be 2K x 2K = {(2*k, 2*k)}, got {dist.shape}."
        )

    return OGCInstance(
        name=str(raw.get("name", path.stem)),
        k=k,
        riders=riders,
        orders=orders,
        dist_m=dist,
    )
