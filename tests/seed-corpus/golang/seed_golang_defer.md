---
tags: [seed, golang]
---

# defer, panic, recover

defer schedules a call to run when the surrounding function returns, commonly to release resources like files or locks. Deferred calls run last-in-first-out. panic and recover exist for truly exceptional cases, not routine errors.
