---
tags: [seed, sqlite]
---

# Virtual tables

A virtual table is a `CREATE VIRTUAL TABLE ... USING module(...)` object whose rows are produced on demand by a registered module rather than stored in a native b-tree. The module is a `sqlite3_module` struct of callbacks that SQLite invokes as it executes a query: `xCreate` and `xConnect` bind the table, `xBestIndex` negotiates with the query planner by reporting which WHERE constraints and ORDER BY terms the module can handle and at what estimated cost, and `xFilter`, `xNext`, `xColumn`, `xEof`, and `xRowid` drive a cursor across the result rows. The planner passes the chosen plan back through `idxNum` and `idxStr`. This module interface is how FTS5, the R-tree spatial index, the `dbstat` and `generate_series` table-valued functions, and sqlite-vec's vec0 all plug in. Eponymous modules need no CREATE statement, and shadow tables let a module persist its own backing storage in ordinary b-trees behind the virtual facade.
