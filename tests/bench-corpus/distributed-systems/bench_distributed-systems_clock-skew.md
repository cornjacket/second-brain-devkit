---
tags: [bench, distributed-systems]
---

# Clock Skew and Time in Distributed Systems

Clock skew is the divergence between the physical clocks of separate nodes, an unavoidable reality that makes wall-clock timestamps a dangerous basis for ordering events across a cluster. NTP disciplines clocks to within milliseconds but drift, leap seconds, and asymmetric network delay leave residual uncertainty, so a receiver's timestamp may legitimately precede a sender's despite the true causal order being the reverse. Last-writer-wins conflict resolution keyed on such timestamps can silently discard the newer write when a lagging clock stamps a higher value. Logical clocks and vector clocks sidestep physical time by ordering events through causality instead. Google's Spanner confronts skew head-on with TrueTime, exposing a bounded uncertainty interval from GPS and atomic clocks and deliberately waiting out that interval before committing so external consistency holds. Hybrid logical clocks combine physical time with a logical counter to stay close to real time while still respecting happens-before across the network.
