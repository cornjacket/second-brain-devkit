---
tags: [seed, sqlite]
---

# The query planner

The query planner, also called the query optimizer, translates a SELECT into a bytecode program for the VDBE, deciding which b-tree indexes to open, the join order across tables, and whether to materialize subqueries or push them down. It uses the Next-Generation Query Planner cost model, weighting estimated row counts drawn from the `sqlite_stat1` and `sqlite_stat4` tables that ANALYZE populates. `EXPLAIN QUERY PLAN` prints a human-readable tree showing SEARCH versus SCAN steps, which index each table uses, USING COVERING INDEX notes, and any TEMP B-TREE built for ORDER BY or GROUP BY, letting you spot an accidental full scan. A skip-scan can exploit a leading index column with low cardinality. When the planner picks poorly you can nudge it with `+` unary operators to disqualify an index, a CROSS JOIN to pin join order, or `INDEXED BY` and `NOT INDEXED` hints.
