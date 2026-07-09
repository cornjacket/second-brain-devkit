---
tags: [seed, rust]
---

# Unsafe Rust

The `unsafe` keyword unlocks five superpowers the compiler cannot verify: dereferencing raw pointers `*const T` and `*mut T`, calling other `unsafe` functions, implementing `unsafe` traits, accessing or mutating `static mut` items, and reading union fields. It does not switch off the borrow checker or type checker elsewhere; it merely shifts the obligation for upholding Rust's aliasing and validity invariants onto the author of that block. This is the escape hatch for FFI declared in `extern "C"` blocks, for `std::mem::transmute`, and for building sound abstractions like `Vec` on top of raw allocation. The convention is to wrap a small, well-audited `unsafe` block inside a safe API and document the `// SAFETY:` reasoning that justifies it. Violating the invariants is undefined behavior, so tools like Miri interpret code to catch out-of-bounds pointer arithmetic, use-after-free, and data races that slip past compilation.
