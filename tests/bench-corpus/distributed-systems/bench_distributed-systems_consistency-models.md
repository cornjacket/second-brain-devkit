---
tags: [bench, distributed-systems]
---

# Consistency Models

A consistency model is the contract defining which orderings of reads and writes a replicated store may expose to concurrent clients. Linearizability is the strongest single-object guarantee, making every operation appear to take effect atomically at some instant between its invocation and response, so all nodes observe one real-time order. Sequential consistency preserves each client's program order but allows a single global interleaving without real-time constraints. Causal consistency only orders operations linked by happens-before, letting concurrent writes be seen in different orders on different replicas. Weaker still, read-your-writes, monotonic-reads, and monotonic-writes are session guarantees clients demand from an otherwise eventually consistent store. Strengthening the model forces more cross-replica coordination and quorum round trips, raising latency and lowering availability under partition, which is why designers deliberately pick the weakest model that still satisfies application invariants.
