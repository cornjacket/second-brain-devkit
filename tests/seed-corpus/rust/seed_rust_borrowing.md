---
tags: [seed, rust]
---

# Borrowing

Rather than moving a value, you can borrow it by taking a reference. Rust's aliasing rule permits any number of shared `&T` borrows or exactly one exclusive `&mut T` borrow within a given scope, never both at once. The borrow checker enforces this statically, which is how Rust rules out data races and iterator invalidation without a garbage collector or runtime checks. Non-lexical lifetimes (NLL) end a borrow at its last use rather than at the closing brace, so code that reborrows sequentially compiles cleanly. A `&mut` reference can be reborrowed and passed down a call chain, and `*` dereferences to reach the underlying place. When the checker complains that something "does not live long enough" or is "already borrowed as mutable," the fix is usually to narrow a scope, split a struct's fields, or reach for interior mutability such as `RefCell` or `Cell`.
