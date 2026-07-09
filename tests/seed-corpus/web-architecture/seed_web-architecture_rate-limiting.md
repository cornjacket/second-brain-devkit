---
tags: [seed, web-architecture]
---

# Rate limiting

Rate limiting caps how many requests a client may issue within a window, shielding an endpoint from abuse, scraping, and accidental overload. The token-bucket algorithm refills tokens at a fixed rate and permits bursts up to the bucket capacity, while the leaky-bucket smooths output to a steady drain; fixed-window counters are simplest but spike at window edges, and sliding-window-log or sliding-window-counter variants smooth those boundaries. Limits are keyed by API key, client IP, or authenticated user, and are usually enforced at the API gateway or reverse proxy backed by an atomic Redis counter with INCR and expiry so distributed nodes share one tally. When a client exceeds its quota the server throttles with HTTP 429 Too Many Requests and advertises X-RateLimit-Limit, X-RateLimit-Remaining, and a Retry-After header so clients back off with exponential retry. Tiered quotas and per-route budgets let premium callers burst higher.
