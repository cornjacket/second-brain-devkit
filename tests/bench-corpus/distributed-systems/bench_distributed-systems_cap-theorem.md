---
tags: [bench, distributed-systems]
---

# The CAP Theorem and Partition Trade-offs

The CAP theorem states that a replicated system facing a network partition must sacrifice either linearizable consistency or availability, since nodes on opposite sides of the split cannot coordinate to agree on the latest write. When a partition severs replicas, a CP system refuses reads or writes on the minority side to avoid returning stale or divergent state, while an AP system keeps serving every replica and reconciles conflicting versions after the partition heals. PACELC extends this by noting that even without a partition, systems trade latency against consistency, because synchronous cross-replica coordination costs round trips. Practical designs pick a point on this spectrum per operation: quorum reads and writes tune the R plus W overlap against N replicas, and hinted handoff or read repair restore convergence. The theorem is fundamentally about coordination limits under unreliable networks, not about single-machine failure.
