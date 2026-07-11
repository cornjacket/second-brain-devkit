---
tags: [bench, distributed-systems]
---

# Conflict-Free Replicated Data Types

CRDTs are replicated data structures engineered so that concurrent updates on different nodes always merge into the same result without coordination, giving strong eventual consistency. State-based convergent types define a merge that is commutative, associative, and idempotent, forming a join-semilattice so replicas that exchange and least-upper-bound their states inevitably converge regardless of message order or duplication. Operation-based commutative types instead broadcast operations that commute, requiring reliable causal delivery but smaller payloads. Canonical designs include grow-only and PN counters, observed-remove sets that track unique tags to make add and remove commute, and sequence types like RGA or Logoot for collaborative text editing. Because merges need no locks, leader, or quorum round trip, CRDTs power offline-first apps, multi-leader replication, and geo-replicated caches that stay available under partition. The cost is metadata overhead from tombstones and version tags and the constraint that application semantics must fit a lattice.
