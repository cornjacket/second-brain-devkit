---
tags: [seed, golang]
---

# Slices and arrays

A slice is a three-word descriptor, a pointer to a backing array plus a length and a capacity, distinct from a fixed-size array like [4]int whose length is part of its type. len(s) reports the elements in view and cap(s) how far the slice can grow into its backing array before append must allocate a new, larger array and copy. The slice expression s[low:high] reslices the same storage, and the full three-index form s[low:high:max] caps the result so a later append cannot clobber the parent. Because subslices alias shared storage, mutating one is visible through another; use the built-in copy(dst, src) when you need independent elements. The zero value of a slice is nil, which append handles seamlessly, and idiomatic growth is s = append(s, x). Removing an element splices with append(s[:i], s[i+1:]...), and beware retaining a small subslice that pins a large array from garbage collection.
