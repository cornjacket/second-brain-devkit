---
tags: [seed, web-architecture]
---

# Caching

Caching interposes fast lookup layers between clients and the origin: browser caches governed by Cache-Control and ETag validators, a shared CDN edge tier, a reverse-proxy cache like Varnish, and an in-memory store such as Redis or Memcached fronting the database. Each entry is addressed by a cache key and expires on its TTL, after which a revalidation or a fresh origin fetch repopulates it. The hard problem is cache invalidation: write-through, write-behind, and cache-aside patterns trade freshness against origin load, while stale-while-revalidate serves an aging entry as it refreshes in the background. A cache miss falls through to the next layer; a thundering herd of concurrent misses can stampede the origin, so request coalescing and jittered TTLs spread the reload. Conditional requests with If-None-Match let the origin answer 304 Not Modified instead of resending the body.
