---
tags: [seed, rust]
---

# Lifetimes

Lifetimes are named regions, written `'a`, that the borrow checker uses to prove every reference outlives the data it points at, statically rejecting dangling references. Most are inferred through lifetime elision: the compiler's three elision rules assign fresh lifetimes to input references and tie the output to `&self` when a method borrows the receiver, so you rarely annotate. Explicit parameters appear on a signature like `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str` when the relationship between inputs and the returned borrow is otherwise ambiguous. Structs that hold references carry a lifetime parameter so instances cannot outlive their borrowed fields. The special `'static` lifetime marks data that lives for the whole program, such as string literals. Higher-ranked trait bounds (`for<'a>`) generalize over all lifetimes for closures. Lifetimes are purely a compile-time proof and are erased before codegen, so they add no runtime overhead.
