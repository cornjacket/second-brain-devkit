---
tags: [seed, typescript]
---

# Union and intersection types

A union type `A | B` holds a value that is one of several members, and until narrowed you may only touch properties common to every member. An intersection `A & B` combines shapes so the result carries every member of both, which is how mixins and `extends`-style composition are modeled at the type level. Discriminated (tagged) unions give each member a shared singleton literal field — `type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number }` — so a `switch (shape.kind)` narrows to exactly one variant per branch. Assigning the fall-through `default` case to a `never`-typed variable forces exhaustiveness: adding a new variant becomes a compile error until handled. Unions distribute over conditional and mapped types, and literal unions like `"sm" | "md" | "lg"` model finite string domains without an enum.
