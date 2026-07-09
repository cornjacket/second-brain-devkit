---
tags: [seed, rust]
---

# Traits

A trait declares a set of method signatures and associated items that a type opts into with an `impl Trait for Type` block. Traits drive generics through trait bounds: `fn print<T: Display>(x: T)` or the `where` clause constrains a type parameter so the compiler can monomorphize a specialized copy per concrete type, giving static dispatch with no indirection. Default method bodies let implementors override selectively, and associated types (like `Iterator::Item`) plus associated constants keep signatures clean. `#[derive(Debug, Clone, PartialEq)]` auto-generates common impls. The coherence and orphan rules require that either the trait or the type be local, which is why the newtype pattern wraps a foreign type to add a foreign trait. When you need heterogeneous collections, `dyn Trait` behind a `Box` or `&` performs dynamic dispatch through a vtable. Marker traits `Send` and `Sync`, blanket impls, supertraits, and trait objects round out the system.
