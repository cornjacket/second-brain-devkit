---
tags: [bench, distributed-systems]
---

# Consensus with Raft and Paxos

Consensus protocols let a cluster of replicas agree on a single ordered log of commands despite crashes and network delays. Paxos frames agreement as proposers, acceptors, and learners exchanging prepare and accept rounds keyed by monotonically increasing ballot numbers, guaranteeing that once a value is chosen no conflicting value can be chosen. Raft decomposes the same problem into leader election, log replication, and safety, electing a leader per term who alone appends entries and replicates them to followers until a majority acknowledges, at which point the entry commits. Both rely on quorum overlap so any two majorities intersect, preventing split-brain divergence. Multi-Paxos amortizes the prepare phase across a stable leader, mirroring Raft's steady state. Correctness hinges on durable term and vote persistence across reboots, and on the leader completeness property ensuring committed entries survive every subsequent leader term.
