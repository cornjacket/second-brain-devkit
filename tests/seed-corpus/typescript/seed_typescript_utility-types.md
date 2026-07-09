---
tags: [seed, typescript]
---

# Utility types

The standard library ships utility types that derive new types from existing ones so definitions stay in sync with their source. `Partial<T>` makes every property optional and `Required<T>` reverses it; `Readonly<T>` freezes them; `Pick<T, K>` and `Omit<T, K>` project or drop a subset of keys; `Record<K, V>` builds a dictionary type from a key union. `Exclude`, `Extract`, and `NonNullable` filter union members, while `ReturnType`, `Parameters`, `InstanceType`, and `Awaited` extract types from functions, constructors, and Promises using the `infer` keyword. Under the hood these are homomorphic mapped types — `{ [K in keyof T]?: T[K] }` — combined with conditional types and key remapping via `as`. Because they compose, you can nest them like `Partial<Pick<User, "email">>`, and they respect `keyof`, index access `T[K]`, and modifier operators `+`/`-readonly`/`-?`.
