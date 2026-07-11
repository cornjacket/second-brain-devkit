---
tags: [bench, distributed-systems]
---

# Idempotency Under Retries

Idempotency ensures that applying the same operation more than once leaves the system in the same state as applying it once, which is essential because unreliable networks force clients and brokers to retry after ambiguous timeouts. A caller attaches an idempotency key or deduplication token to a request so the receiver can recognize a retried operation and return the original outcome instead of double-applying it. At-least-once delivery from queues and replication streams guarantees duplicates, so consumers persist processed message identifiers or fold updates through commutative, idempotent merges. Idempotent receivers pair naturally with exactly-once effective semantics: the transport may deliver twice, but the effect lands once. Designing writes as upserts keyed by a natural identifier, or guarding state transitions with conditional compare-and-set on a version, converts otherwise dangerous retries into safe no-ops. Without idempotency, retry storms after a partition heal can corrupt balances and duplicate side effects across the cluster.
