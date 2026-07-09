---
tags: [seed, web-architecture]
---

# Load balancing

A load balancer sits in front of a pool of backend instances and distributes inbound requests across them, operating either at layer 4 on TCP connections or at layer 7 as a reverse proxy that inspects HTTP paths and headers. Scheduling algorithms include round-robin, weighted round-robin, least-connections, and consistent hashing on a client attribute. Active and passive health checks probe each upstream and eject an instance that fails, draining it from rotation so failed nodes stop receiving traffic; connection draining lets in-flight requests finish before a deregister. For stateful flows, sticky sessions pin a client to one backend via a cookie or source-IP affinity, though a shared session store or stateless JWTs let any instance serve any request. Deployed in redundant pairs behind a virtual IP with failover, the balancer also terminates TLS, enforces timeouts, and supports blue-green and canary rollouts by shifting weight between upstream pools.
