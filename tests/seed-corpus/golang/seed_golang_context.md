---
tags: [seed, golang]
---

# The context package

context.Context carries deadlines, cancellation signals, and request-scoped values across API boundaries and goroutines. Passing it as the first argument lets callers cancel in-flight work. Never store a Context in a struct; pass it explicitly.
