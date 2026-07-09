---
tags: [seed, web-architecture]
---

# Microservices

A microservices architecture decomposes an application into independently deployable services drawn along bounded-context service boundaries, each owning its own datastore to enforce loose coupling and avoid a shared schema. Services communicate through an API gateway that fronts the mesh, handling routing, authentication, and request aggregation, while inter-service calls run over REST or gRPC synchronously or over an event bus and message queue for asynchronous, choreographed workflows. Service discovery and a registry let callers resolve healthy instances; a service mesh sidecar adds retries, circuit breakers, timeouts, and mutual-TLS between services. The trade-off is distributed-system complexity: eventual consistency across service databases, the saga pattern for cross-service transactions, distributed tracing to follow a request across hops, and cascading-failure isolation through bulkheads. A monolith is often the right start, and teams extract services only when independent deployability and team autonomy justify the operational overhead.
