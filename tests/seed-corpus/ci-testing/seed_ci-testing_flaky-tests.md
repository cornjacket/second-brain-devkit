---
tags: [seed, ci-testing]
---

# Flaky tests

A flaky test passes on one run and fails on the next with no code change, producing nondeterministic red builds that erode trust in the whole suite. Common causes are race conditions, reliance on wall-clock timing or sleep-based waits, unseeded randomness, test-ordering dependencies that leak mutable setup between cases, and hidden coupling to an external service. Teams often paper over flakiness with automatic retries — rerun-failures or a retry annotation — but blind retries only hide the defect and mask real regressions. The disciplined move is to quarantine the offending test into a separate lane so it stops blocking merges, then reproduce it by shuffling test order and hammering it under load until it fails deterministically. Fix the root cause: inject the clock, await explicit conditions instead of sleeping, and enforce isolation. Determinism is the only durable cure.
