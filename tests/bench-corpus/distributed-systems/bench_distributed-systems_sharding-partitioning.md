---
tags: [bench, distributed-systems]
---

# Sharding and Partitioning

Partitioning splits a dataset across nodes so no single machine holds the whole keyspace, letting the cluster scale storage and throughput horizontally. Hash partitioning maps each key through a hash into a ring or bucket, spreading load evenly but destroying range locality, while range partitioning keeps ordered keys together for efficient scans at the cost of hotspots on sequential inserts. Consistent hashing places nodes and keys on a ring so adding or removing a node relocates only a fraction of keys, and virtual nodes smooth skew across heterogeneous hardware. A hot partition caused by a skewed key demands splitting or salting the key. Rebalancing must move partitions without dropping requests, so a routing tier or coordination service tracks the partition-to-node mapping and redirects clients. Secondary indexes are either local per partition, requiring scatter-gather reads, or global, requiring their own partitioning scheme.
