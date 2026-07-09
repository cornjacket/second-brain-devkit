---
tags: [seed, sqlite]
---

# Transactions

A transaction groups statements so they commit all-or-nothing, giving atomicity and consistency. BEGIN and COMMIT bound it; ROLLBACK undoes it. Wrapping many inserts in one transaction is far faster than autocommitting each.
