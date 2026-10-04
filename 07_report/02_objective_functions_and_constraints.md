# Objective Functions and Constraints

> Canonical methods record for the optimization study.  
> **Source-verified** items below come from the supplied OGC problem description and the submitted abstract.  
> Items marked **BASELINE-CODE CHECK REQUIRED** are intentionally not treated as final until the supplied baseline source archive is inspected.

## 1. Analysis scope

The research analysis is restricted to **BIKE** riders to control transport-mode heterogeneity.

The three burden dimensions are analyzed **separately**:

- S1: Order Count
- S2: Active Route Duration
- S3: Waiting Time

No composite burden score is used in the current design.

---

## 2. Original OGC cost objective

For a bundled route assigned to rider type \(v\), the supplied OGC description defines delivery cost as the sum of:

1. a rider-type fixed cost, and
2. a distance-dependent variable cost.

The rider data specify the variable cost on a **per-100-meter** basis.

Conceptually,

[
C_b = FC_v + VC_v \times \frac{D_b}{100}
]

where:

- \(C_b\): cost of bundle \(b\),
- \(FC_v\): fixed cost for the selected rider type,
- \(VC_v\): variable cost per 100 meters,
- \(D_b\): route distance in meters.

The competition objective is **average delivery cost**:

[
f_{cost}(x)=\frac{\sum_b C_b}{K}
]

where \(K\) is the number of orders in the instance.

### BASELINE-CODE CHECK REQUIRED

Before final analysis, verify the supplied code for:

- exact distance aggregation,
- cost rounding,
- any integer conversion,
- whether fixed cost is applied exactly once per bundle/rider,
- final objective rounding/comparison behavior.

The competition documentation notes that numerical comparison is performed after rounding objective values to a stated precision, so reporting and internal optimization precision must be separated carefully.

---

## 3. S0 — Cost-only baseline

[
\min f_{cost}(x)
]

S0 reproduces the original OGC feasibility rules and cost objective under the study's BIKE-only scope.

Its role is to provide the reference solution for all cost–equity comparisons and Price of Fairness calculations.

---

## 4. S1 — Order Count

For active rider \(r\),

[
OC_r = |O_r|
]

where \(O_r\) is the set of orders assigned to that rider.

The multi-objective problem is:

[
\min \left(f_{cost}(x),\ I(OC_1,\ldots,OC_R)\right)
]

where \(I(\cdot)\) is the selected inequality function.

### Current status

The inequality function has **not yet been frozen**. Candidate metrics implemented for comparison should include:

- Gini coefficient,
- standard deviation,
- range,
- maximum burden,
- coefficient of variation where meaningful.

The final optimization metric must be selected explicitly and documented before final runs.

---

## 5. S2 — Active Route Duration

The submitted abstract defines Active Route Duration as **travel time + service time, excluding waiting time**.

For rider \(r\),

[
ARD_r = TT_r + ST_r
]

and the multi-objective problem is:

[
\min \left(f_{cost}(x),\ I(ARD_1,\ldots,ARD_R)\right)
]

### OGC time conversion

The supplied OGC description gives the travel/service time matrix logic as:

[
T = \operatorname{round}\left(\frac{DIST}{speed}+service\_time\right)
]

with:

- distance in meters,
- speed in meters/second,
- resulting time in seconds,
- service time added to movement time.

### BASELINE-CODE CHECK REQUIRED

Verify exactly when service time is added in the route simulation so that Active Route Duration is not double-counted.

---

## 6. S3 — Waiting Time

The submitted abstract defines Waiting Time as idle time at pickup locations before the corresponding order is ready.

Conceptually, when a rider reaches pickup \(i\) before its ready time,

[
wait_{ri}=\max(0,RT_i-AT_{ri})
]

and

[
WT_r=\sum_i wait_{ri}
]

The multi-objective problem is:

[
\min \left(f_{cost}(x),\ I(WT_1,\ldots,WT_R)\right)
]

### Important timing issue

The OGC description allows waiting to satisfy ready-time feasibility and states that, for the **first visited pickup**, travel time to that first location is not considered; the rider may depart after the order's ready time.

Therefore, Waiting Time must be reconstructed from the **exact baseline route clock**, not from an independent timing approximation.

### BASELINE-CODE CHECK REQUIRED

Verify:

- route start-time convention,
- first-pickup timing,
- arrival/departure timestamps,
- how waiting is represented internally,
- whether the baseline shifts route start time to avoid unnecessary waiting.

S3 should not be finalized until these points are confirmed from source code.

---

# 7. Common OGC feasibility constraints

These constraints are source-verified from the supplied problem description.

## C1. Capacity constraint

For each bundled route assigned to rider \(r\),

[
\sum_{i\in O_r} volume_i \le capacity_r
]

---

## C2. Ready-time constraint

At a pickup location, the rider may leave for the next location only after the corresponding order is ready.

The documentation defines:

[
readytime_i = ordertime_i + preparationtime_i
]

Waiting at pickup is permitted when needed.

---

## C3. Delivery-deadline constraint

The rider must arrive at a delivery location sufficiently early to complete service by the order deadline.

The supplied documentation states the arrival requirement using:

[
arrival_i \le deadline_i-service\_time
]

---

## C4. Visit-order constraint

For a bundled delivery, **all pickup locations must be completed before any delivery location is visited**.

This is stronger than ordinary pairwise pickup-before-delivery precedence.

A feasible route therefore has the structural form:

[
P_{\pi(1)} \rightarrow \cdots \rightarrow P_{\pi(m)}
\rightarrow
D_{\sigma(1)} \rightarrow \cdots \rightarrow D_{\sigma(m)}
]

---

## C5. Order-satisfaction constraint

Every order must be included in a bundled delivery and completed by exactly one rider assignment.

---

## C6. Rider-assignment constraint

One rider may be assigned to at most one bundled delivery route.

---

## C7. Rider-availability constraint

For each rider type, the number of assigned bundled routes cannot exceed the available rider count provided in the instance.

---

## C8. Study transport-mode restriction

For this research,

[
rider\_type = BIKE
]

for every eligible route.

This is a research-scope restriction, not an original OGC competition constraint.

---

# 8. Route-time rules that must be preserved

The supplied OGC description provides two implementation details that are especially important for S2 and S3:

1. Travel time to the **first visited location** is not counted.
2. After all pickups are completed, delivery locations may be visited in any feasible order.

These rules must be reproduced exactly in the research evaluator.

---

# 9. Reporting metrics

For each scenario and each selected Pareto solution, save:

- average delivery cost,
- total delivery cost if recoverable,
- rider-level burden values,
- mean burden,
- maximum burden,
- minimum burden,
- standard deviation,
- range,
- Gini coefficient,
- coefficient of variation where defined,
- number of active riders,
- feasibility status,
- runtime,
- random seed,
- NSGA-II settings,
- Price of Fairness relative to S0.

Reporting several inequality statistics does **not** mean they are all optimization objectives. The final objective metric will be identified separately.

---

# 10. Price of Fairness

For an equity-improved solution \(x_f\) relative to the cost baseline \(x_0\),

[
PoF =
\frac{f_{cost}(x_f)-f_{cost}(x_0)}
     {f_{cost}(x_0)}
\times 100\%
]

The rule used to select a representative point from the Pareto frontier—e.g., knee point or a fixed equity-improvement target—must be documented alongside each reported PoF value.

---

# 11. Verification status

| Item | Source document | Baseline code |
|---|---:|---:|
| BIKE-only study scope | Verified | N/A |
| Order Count definition | Verified | To implement |
| Active Route Duration definition | Verified | Check timing implementation |
| Waiting Time definition | Verified | **Must verify route clock** |
| Average delivery cost objective | Verified | Check exact arithmetic |
| Capacity constraint | Verified | Check implementation |
| Ready-time constraint | Verified | Check implementation |
| Deadline constraint | Verified | Check implementation |
| All-pickups-before-deliveries rule | Verified | Check implementation |
| Order satisfaction | Verified | Check implementation |
| One bundle per rider | Verified | Check implementation |
| Rider availability | Verified | Check implementation |
