---
tags: [seed, rust]
---

# Unsafe Rust

The unsafe keyword unlocks operations the compiler cannot verify — raw pointer dereferences, FFI, and mutable statics. It does not disable the borrow checker elsewhere; it scopes responsibility to the author. Keep unsafe blocks small and well-audited.
