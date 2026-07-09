---
tags: [seed, ci-testing]
---

# Unit tests

A unit test exercises one small unit — a single function, method, or class — in strict isolation from its collaborators, so a failure pinpoints the exact code at fault instead of leaving you bisecting a whole call graph. Following the arrange-act-assert pattern, the test sets up inputs, invokes the unit once, and checks the outcome with assertions like assertEqual or pytest's plain assert, often parametrized to sweep many cases and edge conditions through one body. Units run in milliseconds because they stub or fake anything slow or external — no live database, no network, no clock — which keeps them deterministic and repeatable on every run. They form the broad base of the test pyramid, the fastest and most numerous layer, so CI executes thousands of them on each push for near-instant feedback. Keep each case independent so ordering never changes the result.
