---
tags: [bench, distributed-systems]
---

# Backpressure and Flow Control

Backpressure is the mechanism by which an overloaded downstream service signals upstream producers to slow down, preventing unbounded queues that turn a transient overload into cascading failure across the cluster. Without it, a fast producer overwhelms a slow consumer, memory balloons with in-flight requests, latency climbs, and timeouts trigger retries that amplify the load in a feedback spiral. Bounded queues and finite connection pools impose natural limits, blocking or rejecting once full, while reactive streams propagate demand so a consumer explicitly requests only as many items as it can handle. Load shedding drops or defers low-priority work early, admission control caps concurrent requests, and rate limiters throttle at the edge. Credit-based flow control grants a sender a budget of outstanding messages replenished on acknowledgement. Circuit breakers open under sustained failure to stop hammering a struggling dependency, and deadline propagation lets a saturated node abandon work whose caller has already given up.
