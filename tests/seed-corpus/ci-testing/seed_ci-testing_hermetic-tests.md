---
tags: [seed, ci-testing]
---

# Hermetic tests

A hermetic test depends only on its declared inputs — no network, clock, or ambient state — so it runs identically anywhere. Determinism makes CI trustworthy and reproducible. Inject time and randomness rather than reading them directly.
