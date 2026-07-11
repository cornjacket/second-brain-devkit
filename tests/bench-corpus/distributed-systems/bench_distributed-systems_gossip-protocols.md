---
tags: [bench, distributed-systems]
---

# Gossip Protocols

Gossip protocols disseminate state across a large cluster the way rumors spread, with each node periodically picking a few random peers and exchanging updates, so information reaches every member in a logarithmic number of rounds without any central coordinator. Epidemic anti-entropy has nodes compare and reconcile their datasets so divergent replicas converge, while rumor-mongering push-pull rounds propagate fresh writes and hinted handoffs. Membership and failure detection ride on the same substrate: SWIM pings a random peer, asks intermediaries to ping on its behalf before declaring a suspect dead, and piggybacks membership changes on regular gossip to bound false positives. Because gossip is decentralized and randomized it tolerates node churn and partial partitions gracefully, trading immediate consistency for eventual convergence and scalability to thousands of nodes. Systems like Cassandra and Consul use it to spread ring topology, node liveness, and schema versions without a bottleneck or single point of failure.
