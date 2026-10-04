# Baseline Verification Status

## What is already source-verified

From the supplied OGC problem description:

- RIDERS rows contain rider type, speed, capacity, variable cost, fixed cost, service time, and availability.
- ORDERS rows contain order id, order time, pickup coordinates, delivery coordinates, preparation time, volume, and deadline.
- ready time is order time + preparation time.
- DIST is a 2K × 2K distance matrix.
- movement/service time is documented using distance, rider speed, and service time.
- bundle capacity must not exceed rider capacity.
- deliveries must satisfy deadlines.
- all pickups in a bundle must be completed before any delivery visit.
- all orders must be served.
- one rider can operate at most one bundled route.
- rider-type route counts cannot exceed rider availability.
- the competition objective is average delivery cost.
- the research scope restricts the analysis to BIKE riders.

## What remains to be verified from source code

The supplied baseline archive itself still needs source-level inspection before final S2/S3 implementation.

Critical checks:

1. exact route-start convention,
2. exact first-pickup time handling,
3. exact waiting-time representation,
4. exact placement/counting of service time,
5. objective rounding and comparison precision,
6. solution representation,
7. bundle-generation heuristic,
8. rider assignment bookkeeping,
9. search/improvement operators,
10. any implicit repair logic not spelled out in the PDF.

## Implementation policy

The repository currently implements only details that are directly supported by the supplied documentation.

Anything dependent on the original baseline's internal route clock or search representation is left explicit as `NotImplementedError` rather than guessed.

This file should be updated as each baseline-code item is verified.
