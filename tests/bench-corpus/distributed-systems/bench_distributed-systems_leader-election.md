---
tags: [bench, distributed-systems]
---

# Leader Election

Leader election lets a cluster designate exactly one coordinator to serialize decisions, even as nodes crash and messages are lost. A candidate campaigns by incrementing a term or epoch number and soliciting votes from peers; a node grants at most one vote per term, so majority quorum overlap guarantees at most one winner. Raft randomizes election timeouts to break symmetry and avoid perpetual split votes, while the Bully algorithm elects the highest-identifier reachable node. Election requires a failure detector, typically heartbeats whose absence triggers a new campaign, but an unlucky timeout can depose a live leader and cause churn. Fencing tokens stamped with the monotonically rising epoch let downstream services reject a deposed leader that wakes from a pause, preventing two leaders from both acting. Coordination services like ZooKeeper expose ephemeral znodes and leases so clients elect and detect leaders without building the protocol themselves.
