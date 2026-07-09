---
tags: [seed, rust]
---

# Iterators

The `Iterator` trait revolves around one required method, `next`, returning `Option<Self::Item>` that yields `Some` until it produces `None`. Adapters like `map`, `filter`, `take`, `skip`, `zip`, `enumerate`, and `flat_map` are lazy: they wrap the source iterator and do no work until a consuming adapter such as `collect`, `sum`, `fold`, `for_each`, or `find` drives the chain. Because adapters compose without intermediate allocation, a pipeline fuses into a single pass that the optimizer typically lowers to a tight loop rivaling a hand-written `for`. Implementing `Iterator` for your own type grants `for x in it` support via `IntoIterator`. The distinction between `iter`, `iter_mut`, and `into_iter` controls whether items are borrowed as `&T`, `&mut T`, or moved by value. `collect` is generic over the target through `FromIterator`, so a turbofish like `collect::<Vec<_>>()` names the output, and `?` inside a map can even collect into `Result`.
