"""Shared route evaluation primitives.

Important:
- Cost/capacity formulas below are grounded in the supplied OGC documentation.
- Full route-clock reproduction is intentionally not guessed here.
- S2/S3 timing must be finalized only after the original baseline source code is verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

from data_loader import OGCInstance, RiderType


@dataclass(frozen=True)
class Route:
    pickup_order_ids: tuple[int, ...]
    delivery_order_ids: tuple[int, ...]


@dataclass(frozen=True)
class RouteTimeline:
    travel_time_sec: float
    service_time_sec: float
    waiting_time_sec: float

    @property
    def active_route_duration_sec(self) -> float:
        return self.travel_time_sec + self.service_time_sec


def route_distance_m(
    instance: OGCInstance,
    route: Route,
) -> float:
    """Calculate distance along P...P -> D...D route nodes.

    OGC node indexing:
      pickup i  -> i
      delivery i -> i + K

    The supplied documentation says movement to the first visited node is not counted.
    """
    k = instance.k
    nodes = list(route.pickup_order_ids) + [i + k for i in route.delivery_order_ids]
    if len(nodes) <= 1:
        return 0.0
    return float(sum(instance.dist_m[a, b] for a, b in zip(nodes[:-1], nodes[1:])))


def bundle_volume(instance: OGCInstance, route: Route) -> int:
    return int(sum(instance.orders[i].volume for i in route.pickup_order_ids))


def capacity_feasible(
    instance: OGCInstance,
    route: Route,
    rider: RiderType,
) -> bool:
    return bundle_volume(instance, route) <= rider.capacity


def visit_structure_feasible(route: Route) -> bool:
    """Check that each bundled order is picked up and delivered exactly once."""
    p = tuple(route.pickup_order_ids)
    d = tuple(route.delivery_order_ids)
    return (
        len(p) == len(d)
        and len(set(p)) == len(p)
        and len(set(d)) == len(d)
        and set(p) == set(d)
    )


def documented_bundle_cost(
    distance_m: float,
    rider: RiderType,
) -> float:
    """Documented OGC bundle cost before any code-specific rounding.

    variable_cost_per_100m is applied to distance / 100.
    """
    return rider.fixed_cost + rider.variable_cost_per_100m * (distance_m / 100.0)


def average_delivery_cost(bundle_costs: Sequence[float], k_orders: int) -> float:
    if k_orders <= 0:
        raise ValueError("k_orders must be positive.")
    return float(sum(bundle_costs) / k_orders)


def build_route_timeline(*args, **kwargs) -> RouteTimeline:
    """Placeholder for exact OGC route-clock reproduction.

    Do not replace this with a generic VRP clock. The supplied documentation has
    OGC-specific timing rules (including first-location treatment), and the
    original baseline source must be checked before S2/S3 final runs.
    """
    raise NotImplementedError(
        "Exact route timing is pending verification of the supplied OGC baseline code."
    )
