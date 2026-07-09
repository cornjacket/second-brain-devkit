---
tags: [seed, sqlite]
---

# Transactions

A transaction bundles statements into one atomic unit that upholds the ACID guarantees of atomicity, consistency, isolation, and durability. `BEGIN` opens it, `COMMIT` makes its writes durable, and `ROLLBACK` discards them by replaying the rollback journal or truncating the WAL back to the last commit frame. Outside an explicit BEGIN, SQLite runs in autocommit mode, wrapping every statement in its own implicit transaction, so wrapping thousands of INSERTs in a single BEGIN/COMMIT collapses that many fsyncs into one and is far quicker. SQLite offers `DEFERRED`, `IMMEDIATE`, and `EXCLUSIVE` begin modes that control when the write lock is acquired; a naive DEFERRED writer can hit SQLITE_BUSY when it upgrades from a read lock. SAVEPOINT and RELEASE create nestable, named subtransactions you can partially roll back. Because the database uses serializable isolation, a committed transaction never exposes a torn intermediate view to concurrent readers.
