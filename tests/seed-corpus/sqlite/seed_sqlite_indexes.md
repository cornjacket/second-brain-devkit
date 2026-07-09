---
tags: [seed, sqlite]
---

# Indexes

An index in SQLite is a separate b-tree keyed on one or more columns, letting the engine seek to matching rows instead of doing a full table scan. `CREATE INDEX idx ON t(a, b)` builds it; each entry stores the key columns plus the rowid that points back into the table b-tree. A covering index that includes every referenced column lets the planner satisfy a query from the index b-tree alone, avoiding the extra rowid lookup into the table. Partial indexes with a WHERE clause index only qualifying rows, and expression indexes key on a computed value. WITHOUT ROWID tables store the payload directly in the primary-key b-tree, making the PK clustered. Each index adds write amplification, since every INSERT, UPDATE, and DELETE must maintain its b-tree, so index the actual WHERE, JOIN, and ORDER BY columns rather than speculatively.
