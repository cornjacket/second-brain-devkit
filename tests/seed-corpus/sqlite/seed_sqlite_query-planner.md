---
tags: [seed, sqlite]
---

# The query planner

The planner chooses how to satisfy a query — which indexes to use and join order — based on collected statistics. EXPLAIN QUERY PLAN shows its decisions so you can spot full scans. Well-chosen indexes and up-to-date statistics guide it.
