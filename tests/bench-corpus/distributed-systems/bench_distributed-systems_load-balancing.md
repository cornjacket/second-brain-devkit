---
tags: [bench, distributed-systems]
---

# Load Balancing Across Nodes

Load balancing spreads incoming requests across a fleet of interchangeable backend replicas so no single node saturates while others sit idle. A layer-four balancer forwards packets by connection tuple, while a layer-seven balancer parses the request and can route by path, consistent-hash the session key for cache affinity, or steer traffic during a rolling deploy. Selection policies range from round-robin and random to least-connections and latency-weighted, with the power-of-two-choices heuristic sampling two backends and picking the less loaded to avoid herd effects. Active health checks eject a replica that fails probes, and passive checks trip on error rates, draining connections gracefully before removal. Client-side balancing pushes the decision into the caller using a service registry, eliminating a central hop. Autoscaling adds replicas under rising load, but the balancer must weight new nodes gradually with slow-start so cold caches and connection pools warm before absorbing full share.
