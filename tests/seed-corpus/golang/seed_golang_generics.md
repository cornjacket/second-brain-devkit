---
tags: [seed, golang]
---

# Generics

Go generics, added in 1.18, let functions and types declare type parameters in square brackets, as in func Map[T, U any](s []T, f func(T) U) []U, constrained by interfaces that describe what a type must support. A constraint is an interface listing method sets or, using type sets with the | union and the ~ underlying-type approximation, permissible concrete types; comparable is a built-in constraint for types usable with == and as map keys. The compiler infers type arguments at the call site so you rarely spell them out. Generics eliminate the interface{} casts and reflection that reusable containers, ordered maps, and algorithms like Min, Max, and Filter once required, while keeping static type checking. The golang.org/x/exp/constraints package supplies constraints.Ordered for the comparison operators. Idiom still favors concrete types and plain interfaces until real duplication across type parameters justifies the abstraction, since overuse obscures signatures.
