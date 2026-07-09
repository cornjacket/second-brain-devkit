---
tags: [seed, golang]
---

# defer, panic, recover

defer schedules a function call to run when the surrounding function returns, whether it returns normally or unwinds through a panic, making it the idiomatic way to pair acquisition with release: defer f.Close(), defer mu.Unlock(), defer wg.Done(). Deferred calls stack and execute last-in-first-out, and their arguments are evaluated at the point the defer statement runs, not when the call fires. A deferred closure can read and mutate named return values, enabling patterns that rewrite the result during cleanup. panic unwinds the goroutine's stack, running deferred calls along the way, and recover, valid only inside a deferred function, stops that unwinding and returns the panic value. Idiomatic Go reserves panic and recover for truly exceptional conditions, such as unrecoverable invariants, while ordinary failures flow back as error values checked with if err != nil rather than through panic.
