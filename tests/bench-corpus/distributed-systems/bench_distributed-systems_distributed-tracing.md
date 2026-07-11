---
tags: [bench, distributed-systems]
---

# Distributed Tracing

Distributed tracing reconstructs the path of a single request as it fans out across many services in a cluster, stitching together the causally related work into one end-to-end view. Each request carries a propagated trace identifier plus a span identifier, and every service emits a span recording its start, duration, parent link, and tags, so a collector assembles the spans into a directed tree revealing where latency accumulates and which downstream hop failed. Context propagation injects these identifiers into request headers across process and network boundaries, following standards like W3C Trace Context and OpenTelemetry so heterogeneous services interoperate. Because tracing every request is expensive at scale, head-based or tail-based sampling keeps a representative or anomaly-biased subset. Traces expose fan-out amplification, sequential calls that should be parallel, and retries storms, complementing metrics and logs. Correlating a trace with per-span logs and service dependency graphs turns an opaque multi-hop timeout into a pinpointed root cause.
