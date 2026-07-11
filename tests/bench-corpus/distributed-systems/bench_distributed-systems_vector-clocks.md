---
tags: [bench, distributed-systems]
---

# Vector Clocks and Causality

Vector clocks capture the happens-before relation between events on different nodes without relying on synchronized physical time. Each node keeps a vector of counters, one entry per node, incrementing its own on every local event and attaching the vector to outgoing messages; on receipt a node takes the element-wise maximum then bumps its own slot. Comparing two vectors reveals whether one causally precedes the other, whether they are equal, or whether they are concurrent because neither dominates. Replicated stores use this to detect conflicting writes made without knowledge of each other, surfacing sibling versions the application must merge instead of silently overwriting under last-writer-wins. A simpler Lamport clock gives a total order consistent with causality but cannot distinguish concurrency from ordering. Version vectors, a close cousin keyed per replica rather than per event, track object lineage so read repair and anti-entropy know which replica holds the strictly newer value versus a genuine divergence.
