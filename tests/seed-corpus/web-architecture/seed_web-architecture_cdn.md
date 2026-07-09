---
tags: [seed, web-architecture]
---

# Content delivery networks

A content delivery network distributes static assets and cached responses across a fleet of edge nodes in points of presence near the requester, so a stylesheet or image is served from a nearby edge cache instead of a round trip to the origin server. DNS-based or anycast routing steers each client to the closest healthy edge, and on a cache miss the edge does an origin pull and stores the object per its Cache-Control and TTL. Cache-busting via fingerprinted filenames and explicit purge or soft-purge APIs handle invalidation across the whole network. CDNs also terminate TLS at the edge, offer origin shielding to collapse many edge misses into one origin fetch, and front the origin as a shield against traffic spikes and volumetric DDoS floods. Modern providers push compute to the edge with functions that rewrite requests, sign URLs, and vary responses by geography.
