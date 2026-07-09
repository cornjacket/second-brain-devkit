---
tags: [seed, rust]
---

# Error handling with Result

Recoverable errors use Result<T, E>, and the ? operator propagates them concisely up the call stack. panic! is reserved for unrecoverable bugs. Crates like anyhow and thiserror streamline error types.
