---
tags: [seed, golang]
---

# Slices and arrays

A slice is a view over a backing array with a length and capacity; appending may reallocate when capacity is exceeded. Slices share storage, so a subslice can alias its parent. Copy explicitly when you need independent data.
