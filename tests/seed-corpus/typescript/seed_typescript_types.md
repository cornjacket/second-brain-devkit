---
tags: [seed, typescript]
---

# Structural typing

TypeScript's type system is structural rather than nominal: assignability is decided by comparing members, so any object bearing the required properties with compatible types is accepted regardless of its declared class or interface name. This turns JavaScript's duck typing into a compile-time check — a `{ name: string }` literal satisfies any parameter typed to that shape. Excess-property checks add a targeted exception for fresh object literals to catch typos. Compatibility of function types follows parameter bivariance rules (tightened by `strictFunctionTypes`), and `private`/`protected` members introduce a nominal-like brand that blocks otherwise-identical shapes. Because types are fully erased during emit, there is no reflection and no runtime footprint from annotations; developers reintroduce nominal distinctions with branded types or discriminant tags when structural matching is too permissive. Enums and classes are the rare constructs that also emit runtime code.
