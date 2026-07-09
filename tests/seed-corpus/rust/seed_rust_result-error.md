---
tags: [seed, rust]
---

# Error handling with Result

Rust splits failure into two channels. Recoverable errors are values of the `Result<T, E>` enum, with an `Ok(T)` success arm and an `Err(E)` failure arm that the type system forces the caller to acknowledge. The `?` operator makes propagation ergonomic: on `Ok` it unwraps the inner value, and on `Err` it returns early after applying a `From` conversion to widen the error into the function's declared error type. Unrecoverable bugs use `panic!`, which unwinds the stack (or aborts) and is what `unwrap` and `expect` trigger on a bad `Result` or `Option`. Idiomatic crates layer on top: `thiserror` derives `std::error::Error` implementations for structured, per-variant enums in libraries, while `anyhow` offers a boxed `anyhow::Error` with `.context()` for application code. Combinators like `map_err`, `ok_or`, and `and_then` transform results without matching by hand.
