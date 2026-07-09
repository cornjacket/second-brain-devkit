---
tags: [seed, rust]
---

# Ownership

Ownership is Rust's central discipline: every value has exactly one owning binding, and when that owner leaves scope the compiler inserts a call to the `Drop` trait's `drop`, giving deterministic, RAII-style cleanup with no garbage collector. Assigning or passing a non-`Copy` value performs a move that transfers ownership and invalidates the source binding, so using it afterward is a compile error rather than a double-free or use-after-free. Small `Copy` types like integers are duplicated bitwise instead of moved, and `clone` makes an explicit deep copy when you truly need one. Shared ownership is opt-in through reference-counted `Rc<T>` for single-threaded graphs or atomic `Arc<T>` across threads, often paired with `RefCell` or `Mutex` for interior mutability. Because move semantics and drop order are resolved entirely at compile time, Rust guarantees memory and thread safety without a runtime tracing collector.
