---
tags: [seed, rust]
---

# Borrowing

Instead of moving, you can borrow a reference: many shared &T borrows or exactly one mutable &mut T at a time. The borrow checker enforces this, ruling out data races. References must never outlive the data they point to.
