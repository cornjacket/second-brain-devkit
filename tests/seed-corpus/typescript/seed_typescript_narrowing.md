---
tags: [seed, typescript]
---

# Type narrowing

Control-flow analysis narrows a variable's type within branches — typeof, instanceof, truthiness, and custom type guards all refine it. After a null check the compiler knows the value is non-null. Narrowing is what makes unions ergonomic.
