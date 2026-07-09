---
tags: [seed, golang]
---

# Error handling

Go treats errors as ordinary values returned alongside results, checked explicitly with if err != nil. Wrapping with fmt.Errorf and %w preserves a chain that errors.Is and errors.As can inspect. There are no exceptions for ordinary control flow.
