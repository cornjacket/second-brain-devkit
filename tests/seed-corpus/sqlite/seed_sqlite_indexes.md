---
tags: [seed, sqlite]
---

# Indexes

An index is a sorted structure that lets SQLite find rows without scanning the whole table, dramatically speeding lookups and joins on the indexed columns. Indexes cost storage and slow writes, so add them for real query patterns. A covering index answers a query from the index alone.
