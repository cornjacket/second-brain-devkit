---
tags: [seed, ci-testing]
---

# Golden-file testing

Golden-file testing, also called snapshot testing, serializes a function's output and compares it byte-for-byte against a committed known-good file — the golden or snapshot — failing the assertion on any diff. It shines for large, structured output that is tedious to assert field by field: rendered HTML, a serialized AST, formatter output, or a CLI's stdout. Frameworks like Jest with toMatchSnapshot, or an UPDATE_SNAPSHOTS environment flag, regenerate the baseline on demand. The discipline is to normalize nondeterministic content first — timestamps, random IDs, absolute paths — so the golden stays stable across runs and machines, otherwise every run reports a spurious diff. Treat an updated golden like source code: regenerate it intentionally, then scrutinize the diff in review before accepting it, because a blindly refreshed snapshot silently blesses a regression and turns the assertion into a rubber stamp.
