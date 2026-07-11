---
tags: [bench, distributed-systems]
---

# Replication Across Replicas

Replication keeps copies of the same data on multiple nodes so the cluster survives machine loss and serves reads from many replicas. Leader-based replication funnels every write through a primary that streams an ordered replication log to followers, which apply it to converge; synchronous replication blocks the commit until at least one follower acknowledges, trading latency for durability, while asynchronous replication risks losing recent writes if the leader fails before propagation. Multi-leader and leaderless schemes accept writes at several replicas and resolve concurrent updates with version vectors, last-writer-wins timestamps, or application merge functions. Replication lag creates read-your-writes and monotonic-read anomalies that clients mitigate by pinning to a replica or reading from the leader. Failover promotes a follower when the leader crashes, requiring careful handling of unreplicated tail writes, fencing of the old leader, and reconfiguration so the new primary owns the replication stream.
