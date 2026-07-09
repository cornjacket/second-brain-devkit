---
tags: [seed, ci-testing]
---

# Hermetic tests

A hermetic test depends only on its explicitly declared inputs and touches no ambient state — no live network calls, no system clock, no environment variables, no files outside a sandboxed temp directory — so it produces the identical result on a laptop, a fresh container, and a CI runner alike. Hermeticity is what makes a test deterministic and reproducible, and it is the property that lets you trust a red build as a real regression rather than environmental noise. Achieve it by injecting the clock and the random seed instead of reading time.time or an unseeded generator directly, by stubbing outbound HTTP behind a fake, by pinning dependency versions, and by running each case in isolation so no leaked state crosses the boundary. Sandbox filesystem writes to tmp_path. Hermetic suites parallelize safely and cache cleanly, because nothing hidden can perturb the outcome.
