---
tags: [seed, golang]
---

# Interfaces

A Go interface is satisfied implicitly: any type that implements its method set counts, with no explicit declaration. Small interfaces like io.Reader compose well and keep dependencies loose. Accept interfaces, return concrete types is a common guideline.
