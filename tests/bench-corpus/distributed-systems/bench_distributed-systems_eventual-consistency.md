---
tags: [bench, distributed-systems]
---

# Eventual Consistency

Eventual consistency guarantees only that if writes stop, all replicas will converge to the same value given enough time, making it the availability-favoring choice for geo-distributed, partition-tolerant stores. Between writes, replicas may temporarily diverge and clients can read stale data, so the model trades strong ordering for low latency and always-writable availability even during a partition. Convergence is driven by background mechanisms: read repair fixes stale replicas detected on a quorum read, anti-entropy compares Merkle trees to find and reconcile divergent ranges, and hinted handoff stashes writes for an unreachable replica to replay on recovery. Conflicts from concurrent writes are resolved by last-writer-wins timestamps, version vectors surfacing siblings, or conflict-free merge functions. Stronger session guarantees like read-your-writes and monotonic reads layer atop the eventual base to tame the worst anomalies for a single client, giving a practical middle ground between raw eventual and expensive linearizable coordination.
