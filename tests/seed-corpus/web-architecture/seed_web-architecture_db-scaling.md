---
tags: [seed, web-architecture]
---

# Database scaling

A database tier scales reads by fanning queries out to read replicas kept current through asynchronous replication from a single primary, accepting replication lag and the eventual consistency that read-your-writes routing must work around. Write throughput scales horizontally through sharding: rows are partitioned across independent nodes by a shard key, using hash or range partitioning, with a routing layer or directory mapping each key to its shard. Cross-shard joins and distributed transactions grow expensive, so denormalization and a chosen partition key that avoids hot shards matter. A connection pool such as PgBouncer multiplexes client connections so the backend is not overwhelmed by per-request connects. Failover promotes a replica to primary when health checks trip, and rebalancing or resharding redistributes partitions as nodes are added. Leader-follower topologies, quorum writes, and read-write splitting at the application or proxy layer round out the pattern.
