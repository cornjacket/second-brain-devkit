---
tags: [bench, distributed-systems]
---

# Fault Tolerance and Failure Detection

Fault tolerance is a cluster's ability to keep serving correct results while individual nodes crash, links drop, or processes pause, and it rests on redundancy plus a failure detector. Because a network cannot distinguish a slow node from a dead one, detectors use heartbeats with tuned timeouts and phi-accrual suspicion levels, accepting that any bound risks false positives that eject healthy replicas. Redundant replicas across independent failure domains, racks, and availability zones prevent correlated outages, while N-plus-one and N-plus-two provisioning absorbs concurrent losses. Systems degrade gracefully by shedding load, serving stale caches, or falling back to reduced functionality rather than cascading. Byzantine fault tolerance further tolerates nodes that lie or send conflicting messages, requiring larger quorums of three-f-plus-one. Bulkheads isolate blast radius, circuit breakers stop hammering a failing dependency, and periodic chaos experiments verify that failover actually works before a real outage exercises it.
