---
tags: [seed, rust]
---

# Async and futures

Rust async functions return futures that do nothing until polled by an executor such as Tokio. .await yields control while waiting, enabling many concurrent tasks on few threads. There is no built-in runtime; you choose one.
