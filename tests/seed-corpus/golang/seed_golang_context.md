---
tags: [seed, golang]
---

# The context package

context.Context propagates deadlines, cancellation signals, and request-scoped values down a call tree and across goroutine boundaries. You derive children from context.Background() or context.TODO() with context.WithCancel, context.WithTimeout, and context.WithDeadline, each returning a cancel function you must defer to release resources. A goroutine watches ctx.Done(), a channel that closes on cancellation, and consults ctx.Err() to distinguish context.Canceled from context.DeadlineExceeded. By convention Context is the first parameter, named ctx, of any blocking or I/O-bound function; it is never stored in a struct. context.WithValue attaches request-scoped data keyed by an unexported type to avoid collisions, though it is reserved for cross-cutting concerns like trace IDs rather than optional parameters. Cancellation cascades: cancelling a parent closes every derived Done channel, so select statements listening on ctx.Done() unwind in-flight work promptly.
