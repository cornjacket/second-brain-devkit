---
tags: [seed, sqlite]
---

# Virtual tables

A virtual table presents a module's data through the SQL interface without storing rows in the usual b-tree, backing features like full-text search and R-trees. Extensions implement the xBestIndex and xFilter callbacks. They make SQLite extensible without changing the core.
