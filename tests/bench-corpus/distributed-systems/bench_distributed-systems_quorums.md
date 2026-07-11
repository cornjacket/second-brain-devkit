---
tags: [bench, distributed-systems]
---

# Quorums and Overlap

A quorum is the minimum number of replicas that must participate in an operation for it to count, and quorum systems exploit the guarantee that any two quorums intersect on at least one node. In a leaderless store with N replicas, requiring W acknowledgements on writes and R responses on reads makes reads observe the newest write whenever R plus W exceeds N, because the read set and write set must overlap on a replica holding it. Tuning these knobs trades durability and consistency against latency and availability: a sloppy quorum accepts writes on any reachable node during a partition then hands them off later, favoring availability. Consensus protocols rely on majority quorums so competing leaders cannot both assemble one, which is why odd cluster sizes maximize fault tolerance per node. Witness or flexible-quorum schemes lower the write cost while preserving the intersection property that keeps replicas from silently diverging.
