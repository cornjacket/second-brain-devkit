---
tags: [seed, golang]
---

# Testing in Go

The testing package runs functions named TestXxx that take a *testing.T, with table-driven tests idiomatic for many cases. go test runs them, and subtests via t.Run give granular reporting. Benchmarks and fuzzing live in the same framework.
