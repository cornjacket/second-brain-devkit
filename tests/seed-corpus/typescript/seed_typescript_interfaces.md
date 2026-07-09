---
tags: [seed, typescript]
---

# Interfaces vs type aliases

An `interface` declares an object shape and supports declaration merging — two interfaces with the same name in a scope fuse their members — plus `extends` clauses that can inherit from several interfaces at once, making them the idiomatic choice for open, extensible public contracts. A `type` alias binds a name to any type expression, so it alone can name union and intersection types, tuples, primitives, template literal types, and mapped types like `{ [K in keyof T]: ... }`; aliases compose with `&` where interfaces reach for `extends`. Interfaces cannot express a bare union, and type aliases cannot be reopened through merging. Both describe call signatures, index signatures, construct signatures, and optional or `readonly` members, and both participate identically in structural compatibility checks. Convention leans on interfaces for object contracts and aliases for everything else.
