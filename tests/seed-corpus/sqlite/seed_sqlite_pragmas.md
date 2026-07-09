---
tags: [seed, sqlite]
---

# PRAGMA statements

A PRAGMA is SQLite's out-of-band statement for reading or setting engine parameters that ordinary SQL cannot reach. `PRAGMA journal_mode=WAL` switches the rollback journal to write-ahead logging, while `PRAGMA synchronous=NORMAL` relaxes how aggressively fsync is called at commit and checkpoint boundaries, trading durability against write throughput. `PRAGMA foreign_keys=ON` enables referential-integrity enforcement, which is off by default per connection. `PRAGMA busy_timeout=5000` sets how long a blocked connection sleeps and retries before returning SQLITE_BUSY. Introspection PRAGMAs like `table_info`, `index_list`, `foreign_key_list`, and `integrity_check` report schema and corruption details, while `cache_size`, `mmap_size`, `page_size`, and `wal_autocheckpoint` tune memory and file layout. Many PRAGMAs are per-connection and reset on close, so an application must reissue them on every fresh open rather than assuming they persist in the database header.
