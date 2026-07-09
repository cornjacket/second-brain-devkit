---
tags: [seed, sqlite]
---

# Write-ahead logging

Write-ahead logging, enabled with `PRAGMA journal_mode=WAL`, appends modified pages as frames to a sidecar `-wal` file instead of overwriting the main database in place. A shared-memory `-shm` file holds the wal-index, a hash map that lets each reader find the most recent frame for any page, so readers see a consistent snapshot against the last committed frame while a single writer keeps appending, giving multiple concurrent readers alongside one writer. A checkpoint copies committed frames back into the main database b-tree and, in TRUNCATE or RESTART mode, resets the wal file; `PRAGMA wal_autocheckpoint=1000` triggers this automatically once the wal grows past that many pages, and `PRAGMA wal_checkpoint(TRUNCATE)` forces it. Because the wal and shm live beside the database, WAL requires all connections to share a filesystem and does not work over many network mounts. The `-wal` file is not durable until checkpointed unless synchronous is FULL.
