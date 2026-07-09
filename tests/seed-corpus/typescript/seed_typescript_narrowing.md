---
tags: [seed, typescript]
---

# Type narrowing

Control-flow analysis tracks how each branch refines a variable, so within a block the compiler substitutes a narrower type than the declared one. Built-in narrowing primitives include `typeof x === "string"`, `instanceof`, the `in` operator, truthiness and equality checks, and `Array.isArray`. User-defined type guards return a type predicate `x is Cat`, and assertion functions declare `asserts x is Foo` to narrow by throwing. Discriminated unions narrow on a common literal `kind` field inside a `switch`, letting the `default` case bind to `never` for exhaustiveness. The non-null assertion `!` and optional chaining `?.` interact with `strictNullChecks` to strip `null | undefined`. Narrowing is reset when a closure could mutate the binding, and `const` versus `let` affects how durable the narrowed type is. This machinery is what makes `unknown` and union types ergonomic to consume safely.
