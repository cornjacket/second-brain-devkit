---
tags: [seed, rust]
---

# Enums and pattern matching

Rust enums are true algebraic sum types: each variant can be a unit, a tuple, or a struct-like variant carrying its own fields, so one type models a closed set of shapes. A `match` expression destructures a variant and binds its payload, and the compiler enforces exhaustiveness, rejecting the code until every variant is covered or a `_` wildcard catches the rest. Match arms support guards (`if x > 0`), `|` or-patterns, range patterns, and binding with `@`. `if let` and `while let` offer terse single-pattern matching, and `let ... else` diverges when a pattern fails. The standard library's `Option<T>` and `Result<T, E>` are themselves enums encoding absence and fallibility in the type system, so a `None` or `Err` can never be ignored by accident. Enums are laid out with a discriminant tag, and niche optimization lets `Option<&T>` occupy the same width as a bare reference.
