# Objective Functions and Constraints

> This file is the canonical methods record for the optimization model.  
> Items marked **TO VERIFY FROM BASELINE CODE** must be checked against the supplied OGC implementation before they are treated as final.

## 1. Common scope

All scenarios use BIKE riders only.

All scenarios must use the same feasibility evaluator. The burden objective changes, but feasibility rules do not.

---

## 2. Cost objective

### S0-S3 Objective 1

[
\min f_{cost}(x)
]

The study retains the original OGC delivery-cost definition.

The supplied problem description indicates that rider cost depends on rider fixed cost, variable cost, and route distance, and that the competition evaluates average delivery cost.

**TO VERIFY FROM BASELINE CODE:** exact cost formula, scaling, rounding, and reporting convention.

---

## 3. S1 — Order Count equity

For rider \(r\):

[
OC_r = \text{number of orders assigned to rider } r
]

Two-objective problem:

[
\min \left(f_{cost}(x),\; I(OC_1,\dots,OC_R)\right)
]

where \(I(\cdot)\) is the inequality function.

**Inequality function is not yet frozen.**  
Candidate primary metric: Gini coefficient.  
Reporting metrics should also include mean, maximum, standard deviation, and range.

---

## 4. S2 — Active Route Duration equity

For rider \(r\):

[
ARD_r = \text{travel time}_r + \text{service time}_r
]

Waiting time is excluded.

Two-objective problem:

[
\min \left(f_{cost}(x),\; I(ARD_1,\dots,ARD_R)\right)
]

Travel and service times must be extracted from the same route-time simulation used for feasibility.

---

## 5. S3 — Waiting Time equity

For rider \(r\), waiting occurs when the rider reaches a pickup before the corresponding order is ready.

Conceptually:

[
WT_r = \sum_i \max(0, ready_i-arrival_{ri})
]

Two-objective problem:

[
\min \left(f_{cost}(x),\; I(WT_1,\dots,WT_R)\right)
]

**TO VERIFY FROM BASELINE CODE:** exact event timing and whether waiting is already represented explicitly or must be reconstructed from arrival/departure times.

---

## 6. Common constraints

The following constraints reflect the supplied OGC problem description and must be matched exactly to the original evaluator.

### C1. Order fulfillment
Every order must be served exactly once.

### C2. Rider capacity
The total order volume assigned to a route must not exceed the selected BIKE rider capacity.

### C3. Ready-time feasibility
Pickup timing must respect order ready times.

### C4. Delivery deadline
Each order must be delivered no later than its deadline.

### C5. Pickup–delivery precedence
Pickup operations must occur before the corresponding deliveries.

### C6. Rider assignment
A rider resource cannot be assigned beyond its allowed usage in the original formulation.

### C7. Rider availability
The number of routes assigned to a rider type cannot exceed available riders.

### C8. Transport-mode restriction
Only BIKE riders are eligible in this study.

---

## 7. Reporting metrics

For every scenario and selected Pareto solution, report:

- total/average delivery cost,
- mean rider burden,
- maximum rider burden,
- standard deviation,
- range,
- Gini coefficient,
- feasibility status,
- runtime,
- random seed,
- Price of Fairness relative to S0.

---

## 8. Price of Fairness

For a selected equity-improved solution:

[
PoF = \frac{Cost_{fair}-Cost_{baseline}}{Cost_{baseline}}\times 100\%
]

The exact baseline reference and solution-selection rule must be recorded for every reported PoF value.
