---
tags: [seed, golang]
---

# Interfaces

A Go interface declares a method set, and any type whose methods cover that set satisfies it implicitly, with no implements keyword or explicit declaration linking the two. This structural, duck-typed satisfaction means io.Reader, io.Writer, and fmt.Stringer are satisfied simply by defining Read, Write, or String with the right signatures. Small single-method interfaces compose through embedding, as io.ReadWriteCloser combines three, keeping dependencies loose. An interface value is a two-word pair of a dynamic type and a value; a type assertion x.(T) or a type switch switch v := x.(type) recovers the concrete type at runtime. The empty interface interface{}, now spelled any, holds any value. A common nil pitfall arises when a typed nil pointer is stored in an interface, making the interface itself non-nil. Idiom advises accepting interfaces as parameters while returning concrete types.
