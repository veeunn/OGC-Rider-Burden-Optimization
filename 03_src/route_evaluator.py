"""OGC route evaluation reproduced from the supplied baseline util.py.

The clock here follows get_pd_times() in the supplied OGC baseline:
- the route clock starts at the first pickup's ready time;
- no travel time to the first pickup is counted;
- every later transition uses rider.T = round(DIST / speed + service_time);
- at later pickups, early arrival creates waiting until ready_time;
- after the final pickup, deliveries are visited without additional ready-time waits.

This module keeps the original source untouched under 02_baseline/original/.
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
    pickup_times: dict[int, float]
    delivery_times: dict[int, float]
    travel_service_time_sec: float
    waiting_time_sec: float

    @property
    def active_route_duration_sec(self) -> float:
        """Travel + service time, excluding waiting."""
        return self.travel_service_time_sec

    @property
    def elapsed_route_time_sec(self) -> float:
        """Clock time from first pickup-ready instant to final delivery."""
        if not self.delivery_times:
            return 0.0
        first = min(self.pickup_times.values())
        last = max(self.delivery_times.values())
        return float(last - first)


def rider_time_matrix(instance: OGCInstance, rider: RiderType) -> np.ndarray:
    return np.round(instance.dist_m / rider.speed_mps + rider.service_time_sec)


def route_distance_m(instance: OGCInstance, route: Route) -> float:
    """Exact get_total_distance() structure from the supplied util.py."""
    p = list(route.pickup_order_ids)
    d = list(route.delivery_order_ids)
    if not p or not d:
        raise ValueError("A route must contain at least one pickup and delivery.")
    if set(p) != set(d):
        raise ValueError("Pickup and delivery order sets must be identical.")

    k = instance.k
    return float(
        sum(instance.dist_m[i, j] for i, j in zip(p[:-1], p[1:]))
        + instance.dist_m[p[-1], d[0] + k]
        + sum(instance.dist_m[i + k, j + k] for i, j in zip(d[:-1], d[1:]))
    )


def bundle_volume(instance: OGCInstance, route: Route) -> int:
    return int(sum(instance.orders[i].volume for i in route.pickup_order_ids))


def capacity_feasible(instance: OGCInstance, route: Route, rider: RiderType) -> bool:
    return bundle_volume(instance, route) <= rider.capacity


def visit_structure_feasible(route: Route) -> bool:
    p = tuple(route.pickup_order_ids)
    d = tuple(route.delivery_order_ids)
    return (
        len(p) == len(d)
        and len(set(p)) == len(p)
        and len(set(d)) == len(d)
        and set(p) == set(d)
    )


def build_route_timeline(
    instance: OGCInstance,
    route: Route,
    rider: RiderType,
) -> RouteTimeline:
    """Reproduce baseline get_pd_times() and expose S2/S3 components."""
    if not visit_structure_feasible(route):
        raise ValueError("Pickup/delivery sequences are structurally invalid.")

    p = list(route.pickup_order_ids)
    d = list(route.delivery_order_ids)
    k_total = instance.k
    T = rider_time_matrix(instance, rider)

    pickup_times: dict[int, float] = {}
    delivery_times: dict[int, float] = {}

    # Baseline starts at first pickup ready time; there is no pre-route travel.
    current = p[0]
    t = float(instance.orders[current].ready_time_sec)
    pickup_times[current] = t

    active = 0.0
    waiting = 0.0

    # Subsequent pickups.
    for nxt in p[1:]:
        transition = float(T[current, nxt])
        active += transition
        arrival = t + transition
        ready = float(instance.orders[nxt].ready_time_sec)
        wait = max(0.0, ready - arrival)
        waiting += wait
        t = max(arrival, ready)
        pickup_times[nxt] = t
        current = nxt

    # Final pickup -> first delivery.
    first_d = d[0]
    transition = float(T[p[-1], first_d + k_total])
    active += transition
    t += transition
    delivery_times[first_d] = t
    current = first_d

    # Remaining deliveries.
    for nxt in d[1:]:
        transition = float(T[current + k_total, nxt + k_total])
        active += transition
        t += transition
        delivery_times[nxt] = t
        current = nxt

    return RouteTimeline(
        pickup_times=pickup_times,
        delivery_times=delivery_times,
        travel_service_time_sec=active,
        waiting_time_sec=waiting,
    )


def deadline_feasible(
    instance: OGCInstance,
    route: Route,
    rider: RiderType,
) -> bool:
    timeline = build_route_timeline(instance, route, rider)
    return all(
        timeline.delivery_times[i] <= instance.orders[i].deadline_sec
        for i in route.delivery_order_ids
    )


def route_feasible(
    instance: OGCInstance,
    route: Route,
    rider: RiderType,
) -> bool:
    return (
        visit_structure_feasible(route)
        and capacity_feasible(instance, route, rider)
        and deadline_feasible(instance, route, rider)
    )


def documented_bundle_cost(distance_m: float, rider: RiderType) -> float:
    return rider.fixed_cost + rider.variable_cost_per_100m * (distance_m / 100.0)


def average_delivery_cost(bundle_costs: Sequence[float], k_orders: int) -> float:
    if k_orders <= 0:
        raise ValueError("k_orders must be positive.")
    return float(sum(bundle_costs) / k_orders)
