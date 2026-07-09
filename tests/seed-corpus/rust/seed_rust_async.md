---
tags: [seed, rust]
---

# Async and futures

An `async fn` in Rust desugars to a state machine implementing the `Future` trait, whose `poll` method returns `Poll::Pending` or `Poll::Ready`. Futures are lazy and inert until an executor drives them; Rust ships no runtime, so you add a crate like Tokio or async-std in `Cargo.toml` and annotate `main` with `#[tokio::main]`. Writing `.await` on a future suspends the current task at that point, returning control to the executor's cooperative scheduler until the awaited future resolves. The compiler stores locals held across an await point inside the generated future, which is why `Send` bounds and lifetimes surface loudly there. A `Waker` is registered so the reactor can re-poll the task once its I/O is ready. `tokio::spawn`, `select!`, and `join!` let you multiplex many tasks over a small thread pool, and pinning via `Pin<&mut Self>` guarantees self-referential futures never move.
