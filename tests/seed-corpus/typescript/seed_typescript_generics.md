---
tags: [seed, typescript]
---

# Generics

Generics introduce type parameters — `function identity<T>(x: T): T` — so a signature preserves the caller's exact type from argument through return instead of collapsing to `any`. The compiler performs type-argument inference at each call site, so `identity(42)` binds `T` to the literal without an explicit `<number>`. Constraints written with `extends` bound a parameter, as in `<T extends { length: number }>`, and `keyof` constraints like `<K extends keyof T>` power type-safe property access. Default type parameters (`<T = string>`) and multiple parameters (`Map<K, V>`) round out the vocabulary. Generic classes and interfaces build reusable containers, while conditional types add `T extends U ? X : Y` and `infer` to destructure types positionally. Variance is structural, and the `const` type-parameter modifier preserves literal narrowing across generic boundaries.
