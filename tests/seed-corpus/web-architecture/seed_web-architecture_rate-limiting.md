---
tags: [seed, web-architecture]
---

# Rate limiting

Rate limiting caps how many requests a client may make in a window, protecting a service from abuse and overload. Token-bucket and sliding-window are common algorithms. Return 429 with a retry hint so clients back off.
