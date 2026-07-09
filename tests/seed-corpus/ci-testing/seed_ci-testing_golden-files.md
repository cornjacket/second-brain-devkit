---
tags: [seed, ci-testing]
---

# Golden-file testing

A golden test compares output against a committed known-good file, failing on any diff. It suits complex output that is tedious to assert field by field. Regenerate the golden intentionally, and review the diff before accepting it.
