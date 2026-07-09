---
tags: [seed, sqlite]
---

# VACUUM and maintenance

VACUUM rebuilds the entire database by copying its live content into a fresh file, which reclaims free pages left behind by deleted rows, defragments the b-trees so pages sit in scan order, and shrinks the file back to its minimal page count. It runs in a transaction, needs temporary space up to the database size, and resets the rowids of any WITHOUT ROWID-less tables that relied on implicit ordering, so it is a maintenance operation rather than a hot-path one. `PRAGMA auto_vacuum=FULL` or `INCREMENTAL` instead keeps a pointer-map page tracking free pages and trims the file at each commit, or on demand via `PRAGMA incremental_vacuum(N)`, avoiding the full rewrite. `PRAGMA freelist_count` reports how many pages sit on the freelist awaiting reuse. Pair VACUUM with ANALYZE, which repopulates the `sqlite_stat1` statistics the query planner consults, and `VACUUM INTO 'backup.db'` writes a compacted copy without touching the original.
