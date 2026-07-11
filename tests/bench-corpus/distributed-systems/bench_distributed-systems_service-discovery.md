---
tags: [bench, distributed-systems]
---

# Service Discovery

Service discovery lets clients in a dynamic cluster find the current network locations of backend instances that scale, restart, and reschedule with ephemeral addresses. Instances register themselves in a registry such as Consul, etcd, or ZooKeeper on startup and renew a lease with periodic heartbeats, so the registry evicts an instance whose lease expires after a crash. Clients resolve a logical service name to a live endpoint set either by querying the registry directly in client-side discovery or by routing through a server-side proxy or virtual IP that hides the lookup. DNS-based discovery with short time-to-live records and SRV entries offers a ubiquitous but coarse mechanism, while a service mesh sidecar watches the registry and load-balances locally with health awareness. The registry itself must be a consistent, replicated, fault-tolerant coordination store, because a stale or partitioned view routes traffic to dead instances or hides healthy ones from the cluster.
