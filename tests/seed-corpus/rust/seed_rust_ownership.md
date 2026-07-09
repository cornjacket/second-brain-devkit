---
tags: [seed, rust]
---

# Ownership

Every value in Rust has a single owner, and when the owner goes out of scope the value is dropped, giving deterministic cleanup without a garbage collector. Moving a value transfers ownership. This model prevents double-frees at compile time.
